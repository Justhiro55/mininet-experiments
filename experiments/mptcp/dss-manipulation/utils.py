#!/usr/bin/python
from mininet.log import info
import time
import os

def captureMPTCPPackets(net, duration=10, output_file="capture.pcap"):
    """MPTCPパケットをキャプチャする"""
    sender = net.get('sender')
    receiver = net.get('receiver')
    
    # 出力先の設定
    output_path = os.path.join('./data', output_file)
    
    info(f'*** MPTCPパケットキャプチャを開始 ({duration}秒間)\n')
    # バックグラウンドでtcpdumpを実行
    sender.cmd(f'tcpdump -i any -s 65535 "tcp" -w {output_path} &')
    
    time.sleep(duration + 1)
    
    # tcpdumpを停止
    sender.cmd('pkill -SIGINT tcpdump')
    time.sleep(1)
    
    # キャプチャしたパケットの概要を表示
    info('*** キャプチャしたMPTCPパケットの概要:\n')
    info(sender.cmd(f'tcpdump -r {output_path} -n "tcp[12:1] & 0xf0 == 0x80" | head -20'))
    
    # MPTCPオプションの詳細を表示
    info('*** MPTCPオプションの詳細:\n')
    mptcp_options = sender.cmd(f'tcpdump -r {output_path} -vv "tcp[12:1] & 0xf0 == 0x80" | grep -i mptcp | head -20')
    info(mptcp_options)
    
    # MPTCPオプション情報を保存
    with open('./data/mptcp_options.txt', 'w') as f:
        f.write(mptcp_options)
    
    return output_path

def analyzeMPTCPConnections(host):
    """MPTCPコネクションの詳細情報を取得して表示"""
    info(f'*** {host.name}のMPTCPコネクション詳細:\n')
    
    # MPTCPサブフロー情報
    info('*** MPTCPサブフロー情報:\n')
    subflow_info = host.cmd('ss -M state established')
    info(subflow_info)
    
    # MPTCPセッション情報
    info('*** MPTCPセッション統計情報:\n')
    session_info = host.cmd('ss -i state established')
    info(session_info)
    
    # より詳細なMPTCPメトリクス
    info('*** MPTCPセッション詳細情報:\n')
    metrics_info = host.cmd('ss -i state established | grep -i mptcp')
    info(metrics_info)
    
    # トークン情報表示（存在する場合）
    info('*** MPTCPトークン情報（利用可能な場合）:\n')
    tokens_info = host.cmd('cat /proc/net/mptcp 2>/dev/null || echo "mptcp proc情報未対応"')
    info(tokens_info)
    
    # 情報を保存
    with open('./data/mptcp_connections.txt', 'w') as f:
        f.write('=== MPTCPサブフロー情報 ===\n')
        f.write(subflow_info)
        f.write('\n\n=== MPTCPセッション統計情報 ===\n')
        f.write(session_info)
        f.write('\n\n=== MPTCPセッション詳細情報 ===\n')
        f.write(metrics_info)
        f.write('\n\n=== MPTCPトークン情報 ===\n')
        f.write(tokens_info)

def analyzeNetworkPath(net):
    """ネットワーク経路の詳細分析"""
    sender = net.get('sender')
    receiver = net.get('receiver')
    
    # tracerouteコマンドがインストールされているか確認
    has_traceroute = sender.cmd('which traceroute || which tracepath')
    if not ('traceroute' in has_traceroute or 'tracepath' in has_traceroute):
        info('*** 警告: traceroute/tracepathコマンドが見つかりません\n')
        info('*** apt-get install traceroute または apt-get install iputils-tracepath を実行してください\n')
        return
    
    # どちらのコマンドが使えるか確認
    if 'traceroute' in has_traceroute:
        trace_cmd = 'traceroute -n'
    else:
        trace_cmd = 'tracepath -n'
    
    info('*** 経路1のtraceroute:\n')
    path1 = sender.cmd(f'{trace_cmd} 10.0.1.2')
    info(path1)
    
    info('*** 経路2のtraceroute:\n')
    path2 = sender.cmd(f'{trace_cmd} 10.1.1.2')
    info(path2)
    
    # 経路情報を保存
    with open('./data/network_paths.txt', 'w') as f:
        f.write('=== 経路1のtraceroute ===\n')
        f.write(path1)
        f.write('\n\n=== 経路2のtraceroute ===\n')
        f.write(path2)

def verifyInterfaces(net):
    """各ホストのインターフェースとIPアドレスを確認"""
    sender = net.get('sender')
    receiver = net.get('receiver')
    r1 = net.get('r1')
    r2 = net.get('r2')
    
    info('*** インターフェース検証\n')
    info('*** Senderのインターフェース:\n')
    info(sender.cmd('ip addr show'))
    
    info('*** Receiverのインターフェース:\n')
    info(receiver.cmd('ip addr show'))
    
    info('*** R1のインターフェース:\n')
    info(r1.cmd('ip addr show'))
    
    info('*** R2のインターフェース:\n')
    info(r2.cmd('ip addr show'))
    
    # すべてのインターフェース情報をファイルに保存
    with open('./data/interfaces.txt', 'w') as f:
        f.write('=== Senderのインターフェース ===\n')
        f.write(sender.cmd('ip addr show'))
        f.write('\n\n=== Receiverのインターフェース ===\n')
        f.write(receiver.cmd('ip addr show'))
        f.write('\n\n=== R1のインターフェース ===\n')
        f.write(r1.cmd('ip addr show'))
        f.write('\n\n=== R2のインターフェース ===\n')
        f.write(r2.cmd('ip addr show'))

def checkConnectivity(net):
    """全ノード間の接続性をテスト"""
    sender = net.get('sender')
    receiver = net.get('receiver')
    r1 = net.get('r1')
    r2 = net.get('r2')
    
    info('*** 接続性テスト\n')
    
    # 経路1のテスト
    info('*** 経路1接続テスト:\n')
    info('*** sender -> r1:\n')
    info(sender.cmd('ping -c 1 10.0.0.2'))
    
    info('*** r1 -> receiver:\n')
    info(r1.cmd('ping -c 1 10.0.1.2'))
    
    info('*** sender -> receiver (経路1経由):\n')
    info(sender.cmd('ping -c 2 10.0.1.2'))
    
    # 経路2のテスト
    info('*** 経路2接続テスト:\n')
    info('*** sender -> r2:\n')
    info(sender.cmd('ping -c 1 10.1.0.2'))
    
    info('*** r2 -> receiver:\n')
    info(r2.cmd('ping -c 1 10.1.1.2'))
    
    info('*** sender -> receiver (経路2経由):\n')
    info(sender.cmd('ping -c 2 10.1.1.2'))
    
    # すべての接続テスト結果を保存
    with open('./data/connectivity_tests.txt', 'w') as f:
        f.write('=== 経路1接続テスト ===\n')
        f.write('sender -> r1:\n')
        f.write(sender.cmd('ping -c 1 10.0.0.2'))
        f.write('\nr1 -> receiver:\n')
        f.write(r1.cmd('ping -c 1 10.0.1.2'))
        f.write('\nsender -> receiver (経路1経由):\n')
        f.write(sender.cmd('ping -c 2 10.0.1.2'))
        
        f.write('\n\n=== 経路2接続テスト ===\n')
        f.write('sender -> r2:\n')
        f.write(sender.cmd('ping -c 1 10.1.0.2'))
        f.write('\nr2 -> receiver:\n')
        f.write(r2.cmd('ping -c 1 10.1.1.2'))
        f.write('\nsender -> receiver (経路2経由):\n')
        f.write(sender.cmd('ping -c 2 10.1.1.2'))

def showCLICommands():
    """CLI用のコマンド一覧を表示"""
    info('\n*** 追加のテスト用コマンド:\n')
    info('   サブフロー確認: sender ss -iaM\n')
    info('   エンドポイント確認: sender ip mptcp endpoint show\n')
    info('   パケットキャプチャ: sender tcpdump -i any tcp port 5002 -vv\n')
    info('   MPTCPテスト実行: sender mptcpize run iperf -c 10.0.1.2 -p 5002 -t 10\n')
    info('   経路確認: sender traceroute -n 10.0.1.2\n')
    info('   経路確認: sender traceroute -n 10.1.1.2\n')
    info('   接続テスト (経路1): sender ping 10.0.1.2\n')
    info('   接続テスト (経路2): sender ping 10.1.1.2\n')
    info('   経路1の確認: sender ip route get 10.0.1.2\n')
    info('   経路2の確認: sender ip route get 10.1.1.2\n')

def debugPacketCapture(net, duration=5):
    """診断用パケットキャプチャ"""
    sender = net.get('sender')
    r1 = net.get('r1')
    
    info('*** パケットキャプチャ開始\n')
    # senderでのキャプチャ
    sender.cmd('tcpdump -i sender-eth0 -n -w /tmp/sender_eth0.pcap &')
    # r1でのキャプチャ
    r1.cmd('tcpdump -i r1-eth0 -n -w /tmp/r1_eth0.pcap &')
    r1.cmd('tcpdump -i r1-eth1 -n -w /tmp/r1_eth1.pcap &')
    
    info('*** テストパケット送信\n')
    sender.cmd('ping -c 5 10.0.1.2')
    
    # 少し待機
    time.sleep(duration)
    
    # キャプチャ停止
    sender.cmd('pkill -SIGINT tcpdump')
    r1.cmd('pkill -SIGINT tcpdump')
    
    # キャプチャ結果表示
    info('*** senderから送信されたパケット:\n')
    info(sender.cmd('tcpdump -r /tmp/sender_eth0.pcap -n | head -10'))
    info('*** r1が受信したパケット:\n')
    info(r1.cmd('tcpdump -r /tmp/r1_eth0.pcap -n | head -10'))
    info('*** r1が転送したパケット:\n')
    info(r1.cmd('tcpdump -r /tmp/r1_eth1.pcap -n | head -10'))
