#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
import time
import os
import sys
import subprocess

# 自作モジュールのインポート
from topo import MPTCPTopo
from setup import setupNetworkAddresses, setupMPTCP, checkMPTCPKernelSupport, optimizeNetwork
from test import testMultiPath, analyzeMPTCPResults
from utils import showCLICommands, analyzeNetworkPath, verifyInterfaces, checkConnectivity, debugPacketCapture

def installRequiredPackages():
    """必要なパッケージをインストール"""
    info('*** 必要なパッケージをインストールします\n')

    # インストール済みかどうか
    has_traceroute = os.system('which traceroute >/dev/null 2>&1')
    has_tracepath = os.system('which tracepath >/dev/null 2>&1')
    has_tcpdump = os.system('which tcpdump >/dev/null 2>&1')
    has_tshark = os.system('which tshark >/dev/null 2>&1')

    packages_to_install = []

    if has_traceroute != 0 and has_tracepath != 0:
        packages_to_install.append('iputils-tracepath')

    if has_tcpdump != 0:
        packages_to_install.append('tcpdump')

    if has_tshark != 0:
        packages_to_install.append('tshark')

    if packages_to_install:
        info(f'*** 以下のパッケージをインストールします: {", ".join(packages_to_install)}\n')
        os.system('apt-get update -y >/dev/null 2>&1')
        for pkg in packages_to_install:
            os.system(f'apt-get install -y {pkg} >/dev/null 2>&1')
    else:
        info('*** 必要なパッケージは既にインストールされています\n')

def checkAndEnableForwarding(net):
    """ルーターのIPフォワーディングを確認して有効化"""
    r1 = net.get('r1')
    r2 = net.get('r2')

    info('*** IPフォワーディングの状態確認\n')
    for router in [r1, r2]:
        fwd_status = router.cmd('sysctl net.ipv4.ip_forward')
        info(f'*** {router.name} IPフォワーディング状態: {fwd_status}')

        # 明示的に有効化
        router.cmd('sysctl -w net.ipv4.ip_forward=1')

        # 再確認
        new_status = router.cmd('sysctl net.ipv4.ip_forward')
        info(f'*** {router.name} 新しいIPフォワーディング状態: {new_status}')

def tuneKernelParameters(net):
    """カーネルパラメータを調整"""
    r1 = net.get('r1')
    r2 = net.get('r2')
    sender = net.get('sender')
    receiver = net.get('receiver')

    info('*** カーネルパラメータの調整\n')

    for host in [r1, r2, sender, receiver]:
        # 逆方向パスフィルタリングを緩和
        host.cmd('sysctl -w net.ipv4.conf.all.rp_filter=0')
        host.cmd('sysctl -w net.ipv4.conf.default.rp_filter=0')

        # TCPパラメータを最適化
        host.cmd('sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"')  # TCP受信バッファ
        host.cmd('sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"')  # TCP送信バッファ
        host.cmd('sysctl -w net.ipv4.tcp_congestion_control=cubic')    # 輻輳制御アルゴリズム

        for intf in host.intfList():
            if intf.name != 'lo':
                host.cmd(f'sysctl -w net.ipv4.conf.{intf.name}.rp_filter=0')

        # MTUを調整
        for intf in host.intfList():
            if intf.name != 'lo':
                host.cmd(f'ip link set {intf.name} mtu 1400')

        # ARPキャッシュの挙動調整
        host.cmd('sysctl -w net.ipv4.conf.all.arp_ignore=1')
        host.cmd('sysctl -w net.ipv4.conf.all.arp_announce=2')

def resetNetworkState(net):
    """ネットワーク状態をリセット"""
    sender = net.get('sender')
    receiver = net.get('receiver')
    r1 = net.get('r1')
    r2 = net.get('r2')

    info('*** ネットワーク状態をリセット\n')

    for host in [sender, receiver, r1, r2]:
        # ARPキャッシュをクリア
        host.cmd('ip neigh flush all')
        # ルーティングキャッシュをクリア
        host.cmd('ip route flush cache')

    # 全インターフェースを強制的に UP 状態にする
    for host in [sender, receiver, r1, r2]:
        for intf in host.intfList():
            if intf.name != 'lo':
                info(f'*** {host.name}の{intf.name}を強制的にUP状態に設定\n')
                host.cmd(f'ip link set {intf.name} up')

    # 接続性の再確認
    info('*** リセット後の接続性確認\n')
    info('*** sender -> receiver (経路1経由):\n')
    info(sender.cmd('ping -c 1 10.0.1.2'))
    info('*** sender -> receiver (経路2経由):\n')
    info(sender.cmd('ping -c 1 10.1.1.2'))

def showAdvancedCLICommands():
    """高度なCLIコマンド一覧を表示"""
    info('\n*** 高度なトラブルシューティングコマンド:\n')
    info('   ARPキャッシュ確認: sender ip neigh show\n')
    info('   ルーティングテーブル詳細: sender ip route show table all\n')
    info('   ルーティングキャッシュ確認: sender ip route show cache\n')
    info('   ネットワークインターフェース統計: sender ip -s link show\n')
    info('   IPフォワーディング確認: r1 sysctl net.ipv4.ip_forward\n')
    info('   パケットカウンタリセット: r1 ip -s -s link set dev r1-eth0 counters 0\n')
    info('   特定ルートのトレース: sender traceroute -I 10.0.1.2\n')
    info('   パケットキャプチャ開始: sender tcpdump -i any tcp port 5002 -nn -w /tmp/mptcp_capture.pcap &\n')
    info('   パケットキャプチャ停止: sender pkill -SIGINT tcpdump\n')
    info('   MTUパス探索: sender tracepath -n 10.0.1.2\n')
    info('   逆方向パスフィルタリング確認: r1 sysctl net.ipv4.conf.all.rp_filter\n')
    info('   サブフロー統計: sender ss -tiM state established\n')
    info('   MPTCPエンドポイント確認: sender ip mptcp endpoint show\n')
    info('   トラフィック分析: sender tcpdump -r /tmp/mptcp_capture.pcap -nn "host 10.0.0.1" | wc -l\n')

def run():
    # データディレクトリ作成
    os.makedirs('./data', exist_ok=True)

    # 必要なパッケージのインストール
    installRequiredPackages()

    # MPTCPカーネルサポート確認
    checkMPTCPKernelSupport()

    # トポロジーを作成
    topo = MPTCPTopo()
    net = Mininet(topo=topo, link=TCLink)

    # ネットワーク開始
    net.start()

    try:
        # インターフェース確認 - 最初にIPアドレス設定前の状態を確認
        info('*** 初期インターフェース確認\n')
        for host in net.hosts:
            info(f'*** {host.name}のインターフェース:\n')
            info(host.cmd('ip -o link show | grep -v lo'))

        # ネットワークアドレス設定
        setupNetworkAddresses(net)

        # ルーターのIPフォワーディングを確認して有効化
        checkAndEnableForwarding(net)

        # カーネルパラメータ調整
        tuneKernelParameters(net)

        # ネットワーク状態をリセット
        resetNetworkState(net)

        # インターフェース確認
        verifyInterfaces(net)

        # 接続性テスト
        checkConnectivity(net)

        # ★★★ ネットワーク最適化を適用 ★★★
        optimizeNetwork(net)

        # 診断用パケットキャプチャ実行
        debugPacketCapture(net)

        # MPTCPセットアップ
        setupMPTCP(net)

        # ネットワーク経路分析
        analyzeNetworkPath(net)

        info('\n*** Multipath test\n')
        mptcp_bw = testMultiPath(net)

        # 結果分析
        analyzeMPTCPResults(mptcp_bw)

        # display CLI commands
        showCLICommands()
        showAdvancedCLICommands()

        # グラフデータの準備
        info('\n*** generate graph data\n')
        if os.system('which tshark >/dev/null 2>&1') == 0:
            output = net.get('sender').cmd('tshark -r ./data/mptcp_test.pcap -q -z io,stat,1,"tcp.port==5002","ip.addr==10.0.0.1","ip.addr==10.1.0.1" > ./data/traffic_by_time.csv')
            info(f'*** save traffic data: ./data/traffic_by_time.csv\n')

        CLI(net)
    finally:
        net.stop()

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("Not enough privileges.")
        print("sudo python %s を実行してください。" % sys.argv[0])
        sys.exit(1)

    # ログレベル設定
    setLogLevel('info')

    # 実行
    run()