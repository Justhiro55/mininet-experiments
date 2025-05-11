#!/usr/bin/python
from mininet.log import info
import os
import time

def setupNetworkAddresses(net):
    """ネットワークアドレスの設定"""
    info('*** ネットワークアドレスの設定\n')
    
    sender = net.get('sender')
    receiver = net.get('receiver')
    r1 = net.get('r1')
    r2 = net.get('r2')
    
    # インターフェース情報の確認
    info('*** インターフェース確認\n')
    for host in [sender, receiver, r1, r2]:
        info(f'*** {host.name}のインターフェース一覧:\n')
        info(host.cmd('ip -o link show | grep -v lo'))
    
    # 既存のIPアドレスをクリア
    for host in [sender, receiver, r1, r2]:
        for intf in host.intfList():
            if intf.name != 'lo':
                host.cmd(f'ip addr flush dev {intf.name}')
    
    # 経路1のIP設定 (10.0.0.0/24と10.0.1.0/24ネットワーク)
    sender.cmd('ip addr add 10.0.0.1/24 dev sender-eth0')
    r1.cmd('ip addr add 10.0.0.2/24 dev r1-eth0')
    r1.cmd('ip addr add 10.0.1.1/24 dev r1-eth1')
    receiver.cmd('ip addr add 10.0.1.2/24 dev receiver-eth0')
    
    # 経路2のIP設定 (10.1.0.0/24と10.1.1.0/24ネットワーク)
    sender.cmd('ip addr add 10.1.0.1/24 dev sender-eth1')
    r2.cmd('ip addr add 10.1.0.2/24 dev r2-eth0')
    r2.cmd('ip addr add 10.1.1.1/24 dev r2-eth1')
    receiver.cmd('ip addr add 10.1.1.2/24 dev receiver-eth1')
    
    # すべてのインターフェースを有効化
    for host in [sender, receiver, r1, r2]:
        for intf in host.intfList():
            if intf.name != 'lo':
                host.cmd(f'ip link set {intf.name} up')
    
    # ルーティングテーブルをクリア
    for host in [sender, receiver, r1, r2]:
        host.cmd('ip route flush all')
        host.cmd('ip route add default via 127.0.0.1 dev lo')
    
    # 経路1のルーティング
    sender.cmd('ip route add 10.0.0.0/24 dev sender-eth0')
    sender.cmd('ip route add 10.0.1.0/24 via 10.0.0.2 dev sender-eth0')
    
    r1.cmd('ip route add 10.0.0.0/24 dev r1-eth0')
    r1.cmd('ip route add 10.0.1.0/24 dev r1-eth1')
    
    receiver.cmd('ip route add 10.0.0.0/24 via 10.0.1.1 dev receiver-eth0')
    receiver.cmd('ip route add 10.0.1.0/24 dev receiver-eth0')
    
    # 経路2のルーティング
    sender.cmd('ip route add 10.1.0.0/24 dev sender-eth1')
    sender.cmd('ip route add 10.1.1.0/24 via 10.1.0.2 dev sender-eth1')
    
    r2.cmd('ip route add 10.1.0.0/24 dev r2-eth0')
    r2.cmd('ip route add 10.1.1.0/24 dev r2-eth1')
    
    receiver.cmd('ip route add 10.1.0.0/24 via 10.1.1.1 dev receiver-eth1')
    receiver.cmd('ip route add 10.1.1.0/24 dev receiver-eth1')
    
    # ルーティングテーブルの確認
    info('*** Senderのルーティングテーブル:\n')
    info(sender.cmd('ip route'))
    info('*** Receiverのルーティングテーブル:\n')
    info(receiver.cmd('ip route'))

def optimizeNetwork(net):
    """ネットワークを最適化する"""
    sender = net.get('sender')
    receiver = net.get('receiver')
    r1 = net.get('r1')
    r2 = net.get('r2')
    
    # iptables設定をクリア（すべてのノードで）
    for host in [sender, receiver, r1, r2]:
        info(f'*** {host.name}のiptables設定をクリア\n')
        host.cmd('iptables -F')
        host.cmd('iptables -t nat -F')
        host.cmd('iptables -t mangle -F')
        host.cmd('iptables -P FORWARD ACCEPT')
    
    # すべてのインターフェースを再度確認してUP状態に強制
    for host in [sender, receiver, r1, r2]:
        for intf in host.intfs.values():
            if intf.name != 'lo':
                info(f'*** {host.name}の{intf.name}を再度UP状態に設定\n')
                host.cmd(f'ip link set {intf.name} down')
                time.sleep(0.5)
                host.cmd(f'ip link set {intf.name} up')
    
    # ルーティングテーブルを完全にリセット
    for host in [sender, receiver, r1, r2]:
        host.cmd('ip route flush all')
    
    # 送信者の基本的なルーティング設定
    sender.cmd('ip route add 10.0.0.0/24 dev sender-eth0')
    sender.cmd('ip route add 10.0.1.0/24 via 10.0.0.2 dev sender-eth0')
    sender.cmd('ip route add 10.1.0.0/24 dev sender-eth1')
    sender.cmd('ip route add 10.1.1.0/24 via 10.1.0.2 dev sender-eth1')
    
    # 受信者の基本的なルーティング設定
    receiver.cmd('ip route add 10.0.1.0/24 dev receiver-eth0')
    receiver.cmd('ip route add 10.0.0.0/24 via 10.0.1.1 dev receiver-eth0')
    receiver.cmd('ip route add 10.1.1.0/24 dev receiver-eth1')
    receiver.cmd('ip route add 10.1.0.0/24 via 10.1.1.1 dev receiver-eth1')
    
    # ルーター1の基本的なルーティング設定
    r1.cmd('ip route add 10.0.0.0/24 dev r1-eth0')
    r1.cmd('ip route add 10.0.1.0/24 dev r1-eth1')
    r1.cmd('ip route add 10.1.0.0/24 via 10.0.0.1 dev r1-eth0')
    r1.cmd('ip route add 10.1.1.0/24 via 10.0.1.2 dev r1-eth1')
    
    # ルーター2の基本的なルーティング設定
    r2.cmd('ip route add 10.1.0.0/24 dev r2-eth0')
    r2.cmd('ip route add 10.1.1.0/24 dev r2-eth1')
    r2.cmd('ip route add 10.0.0.0/24 via 10.1.0.1 dev r2-eth0')
    r2.cmd('ip route add 10.0.1.0/24 via 10.1.1.2 dev r2-eth1')
    
    # 静的ARPエントリを設定（ARPを手動で解決）
    info('*** 静的ARPエントリを設定\n')
    
    # ルーターとホスト間のMAC取得
    r1_eth0_mac = r1.cmd("ip link show r1-eth0 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    r1_eth1_mac = r1.cmd("ip link show r1-eth1 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    r2_eth0_mac = r2.cmd("ip link show r2-eth0 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    r2_eth1_mac = r2.cmd("ip link show r2-eth1 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    sender_eth0_mac = sender.cmd("ip link show sender-eth0 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    sender_eth1_mac = sender.cmd("ip link show sender-eth1 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    receiver_eth0_mac = receiver.cmd("ip link show receiver-eth0 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    receiver_eth1_mac = receiver.cmd("ip link show receiver-eth1 | grep -o 'link/ether [^ ]*' | cut -d' ' -f2").strip()
    
    # 静的ARPテーブルの設定
    sender.cmd(f'arp -s 10.0.0.2 {r1_eth0_mac}')
    sender.cmd(f'arp -s 10.1.0.2 {r2_eth0_mac}')
    
    r1.cmd(f'arp -s 10.0.0.1 {sender_eth0_mac}')
    r1.cmd(f'arp -s 10.0.1.2 {receiver_eth0_mac}')
    
    r2.cmd(f'arp -s 10.1.0.1 {sender_eth1_mac}')
    r2.cmd(f'arp -s 10.1.1.2 {receiver_eth1_mac}')
    
    receiver.cmd(f'arp -s 10.0.1.1 {r1_eth1_mac}')
    receiver.cmd(f'arp -s 10.1.1.1 {r2_eth1_mac}')
    
    # カーネルパラメータを徹底的に調整
    for host in [sender, receiver, r1, r2]:
        host.cmd('sysctl -w net.ipv4.ip_forward=1')
        host.cmd('sysctl -w net.ipv4.conf.all.rp_filter=0')
        host.cmd('sysctl -w net.ipv4.conf.default.rp_filter=0')
        host.cmd('sysctl -w net.ipv4.tcp_ecn=0')  # ECNを無効化
        host.cmd('sysctl -w net.ipv4.conf.all.accept_redirects=0')  # ICMPリダイレクトを無効化
        host.cmd('sysctl -w net.ipv4.conf.all.send_redirects=0')  # ICMPリダイレクト送信を無効化
        
        # TCP性能調整
        host.cmd('sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"')  # TCP受信バッファを拡大
        host.cmd('sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"')  # TCP送信バッファを拡大
        host.cmd('sysctl -w net.ipv4.tcp_congestion_control=cubic')    # 輻輳制御アルゴリズム
        
        for intf in host.intfs.values():
            if intf.name != 'lo':
                host.cmd(f'sysctl -w net.ipv4.conf.{intf.name}.rp_filter=0')
                host.cmd(f'sysctl -w net.ipv4.conf.{intf.name}.forwarding=1')
                # TCキューイングを調整（通信を最適化）
                host.cmd(f'tc qdisc del dev {intf.name} root 2>/dev/null')
                host.cmd(f'tc qdisc add dev {intf.name} root fq')
    
    # MTUを調整
    for host in [sender, receiver, r1, r2]:
        for intf in host.intfs.values():
            if intf.name != 'lo':
                host.cmd(f'ip link set {intf.name} mtu 1400')
    
    # すべてのノードのルーティングテーブルを再確認
    for host in [sender, receiver, r1, r2]:
        info(f'*** {host.name}の最終ルーティングテーブル:\n')
        info(host.cmd('ip route'))
        info(f'*** {host.name}のARPテーブル:\n')
        info(host.cmd('arp -n'))
    
    # 最終接続性確認
    info('*** 最終接続性確認\n')
    info('*** sender -> receiver (経路1経由):\n')
    info(sender.cmd('ping -c 2 -v 10.0.1.2'))
    info('*** sender -> receiver (経路2経由):\n')
    info(sender.cmd('ping -c 2 -v 10.1.1.2'))

def setupMPTCP(net):
    sender = net.get('sender')
    receiver = net.get('receiver')
    
    # MPTCPを有効化
    info('*** MPTCPを有効化\n')
    for host in [sender, receiver]:
        host.cmd('sysctl -w net.mptcp.enabled=1')
        # チェックサムを無効化して処理を軽減
        host.cmd('sysctl -w net.mptcp.checksum_enabled=0')
        # スケジューラーを設定（redundantが最適）
        host.cmd('sysctl -w net.mptcp.scheduler=redundant 2>/dev/null || sysctl -w net.mptcp.scheduler=default')
        
        # パスマネージャ設定
        host.cmd('sysctl -w net.mptcp.pm_type=0')  # フルメッシュ
        
        info(f'*** {host.name}のMPTCP情報:\n')
        info(host.cmd('uname -r'))
        info(host.cmd('sysctl net.mptcp.enabled'))
        info(host.cmd('sysctl net.mptcp.version 2>/dev/null || echo "MPTCPバージョン情報が利用できません"'))
        info(host.cmd('sysctl net.mptcp.scheduler 2>/dev/null || echo "MPTCPスケジューラ情報が利用できません"'))
    
    # MPTCPエンドポイント設定
    info('*** MPTCPエンドポイント設定\n')
    sender.cmd('ip mptcp endpoint flush')
    receiver.cmd('ip mptcp endpoint flush')
    
    # Senderのエンドポイント設定
    sender.cmd('ip mptcp endpoint add 10.0.0.1 dev sender-eth0 subflow')
    sender.cmd('ip mptcp endpoint add 10.1.0.1 dev sender-eth1 subflow')
    
    # Receiverのエンドポイント設定
    receiver.cmd('ip mptcp endpoint add 10.0.1.2 dev receiver-eth0 signal')
    receiver.cmd('ip mptcp endpoint add 10.1.1.2 dev receiver-eth1 signal')
    
    # MPTCP拡張設定
    sender.cmd('ip mptcp limits set subflow 4')
    sender.cmd('ip mptcp limits set add_addr_accepted 4')
    receiver.cmd('ip mptcp limits set subflow 4')
    receiver.cmd('ip mptcp limits set add_addr_accepted 4')
    
    # 設定確認
    info('*** Senderのエンドポイント:\n')
    info(sender.cmd('ip mptcp endpoint show'))
    info('*** Receiverのエンドポイント:\n')
    info(receiver.cmd('ip mptcp endpoint show'))
    
    # MPTCP設定詳細
    info('*** MPTCPカーネル設定:\n')
    for param in ['net.mptcp.enabled', 'net.mptcp.checksum_enabled', 
                 'net.mptcp.scheduler', 'net.mptcp.pm_type']:
        info(f'{param}: {sender.cmd("sysctl " + param + " 2>/dev/null || echo \"" + param + " は利用できません\"")}')
    
    # 接続確認
    info('*** 経路1の接続テスト\n')
    info(sender.cmd('ping -c 2 10.0.1.2'))
    info('*** 経路2の接続テスト\n')
    info(sender.cmd('ping -c 2 10.1.1.2'))

def checkMPTCPKernelSupport():
    """MPTCPカーネルサポート確認"""
    info('*** MPTCPカーネルサポート確認\n')
    
    # 必要なディレクトリ作成
    os.makedirs('./data', exist_ok=True)
    
    # コマンド実行と結果出力
    kernel_version = os.popen('uname -r').read().strip()
    info(f'カーネルバージョン: {kernel_version}\n')
    
    try:
        mptcp_enabled = os.popen('sysctl -n net.mptcp.enabled').read().strip()
        info(f'MPTCP有効化状態: {mptcp_enabled}\n')
        
        mptcp_version = os.popen('sysctl -n net.mptcp.version 2>/dev/null').read().strip()
        info(f'MPTCPバージョン: {mptcp_version}\n')
    except:
        info('MPTCPカーネル情報の取得に失敗\n')
    
    # mptcpizeコマンド確認
    try:
        mptcpize_version = os.popen('mptcpize --version 2>/dev/null').read().strip()
        info(f'mptcpizeバージョン: {mptcpize_version}\n')
    except:
        info('mptcpizeが見つかりません\n')
    
    # /proc/net/mptcp確認
    try:
        mptcp_proc = os.popen('cat /proc/net/mptcp 2>/dev/null').read().strip()
        info('MPTCP /proc/net/mptcp情報:\n')
        info(mptcp_proc + '\n')
    except:
        info('/proc/net/mptcp情報が利用できません\n')