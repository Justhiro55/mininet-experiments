#!/usr/bin/python
from mininet.log import info
import re
import time
import os
from utils import analyzeMPTCPConnections, captureMPTCPPackets

def testMultiPath(net):
    sender = net.get('sender')
    receiver = net.get('receiver')
    
    info('*** MPTCP帯域幅テスト (2 x 5Mbps)\n')
    
    # 帯域幅を明示的に制限
    sender.cmd('tc qdisc del dev sender-eth0 root 2>/dev/null')
    sender.cmd('tc qdisc add dev sender-eth0 root tbf rate 5mbit burst 32kbit latency 40ms')
    sender.cmd('tc qdisc del dev sender-eth1 root 2>/dev/null')
    sender.cmd('tc qdisc add dev sender-eth1 root tbf rate 5mbit burst 32kbit latency 40ms')
    
    receiver.cmd('tc qdisc del dev receiver-eth0 root 2>/dev/null')
    receiver.cmd('tc qdisc add dev receiver-eth0 root tbf rate 5mbit burst 32kbit latency 40ms')
    receiver.cmd('tc qdisc del dev receiver-eth1 root 2>/dev/null')
    receiver.cmd('tc qdisc add dev receiver-eth1 root tbf rate 5mbit burst 32kbit latency 40ms')
    
    # ルーターのTCキューイングを調整
    r1 = net.get('r1')
    r2 = net.get('r2')
    
    r1.cmd('tc qdisc del dev r1-eth0 root 2>/dev/null')
    r1.cmd('tc qdisc add dev r1-eth0 root fq')
    r1.cmd('tc qdisc del dev r1-eth1 root 2>/dev/null')
    r1.cmd('tc qdisc add dev r1-eth1 root fq')
    
    r2.cmd('tc qdisc del dev r2-eth0 root 2>/dev/null')
    r2.cmd('tc qdisc add dev r2-eth0 root fq')
    r2.cmd('tc qdisc del dev r2-eth1 root 2>/dev/null')
    r2.cmd('tc qdisc add dev r2-eth1 root fq')
    
    # 両方のパスを同等に使用するようにMPTCP設定
    sender.cmd('ip mptcp endpoint flush')
    sender.cmd('ip mptcp endpoint add 10.0.0.1 dev sender-eth0 subflow')
    sender.cmd('ip mptcp endpoint add 10.1.0.1 dev sender-eth1 subflow')
    
    # MPTCP設定の最適化
    sender.cmd('sysctl -w net.mptcp.checksum_enabled=0')
    sender.cmd('sysctl -w net.mptcp.scheduler=redundant 2>/dev/null || sysctl -w net.mptcp.scheduler=default')
    sender.cmd('ip mptcp limits set subflow 4')
    sender.cmd('ip mptcp limits set add_addr_accepted 4')
    
    receiver.cmd('sysctl -w net.mptcp.checksum_enabled=0')
    receiver.cmd('sysctl -w net.mptcp.scheduler=redundant 2>/dev/null || sysctl -w net.mptcp.scheduler=default')
    receiver.cmd('ip mptcp limits set subflow 4')
    receiver.cmd('ip mptcp limits set add_addr_accepted 4')
    
    # 設定確認
    info('*** MPTCPエンドポイント設定:\n')
    info(sender.cmd('ip mptcp endpoint show'))
    
    # MPTCPサーバー起動（ポート開放確認）
    receiver.cmd('ss -tulpn | grep 5002 || true')  # 既存のリスナーをチェック
    receiver.cmd('pkill -9 iperf || true')  # 既存のサーバーを停止
    time.sleep(1)
    receiver.cmd('mptcpize run iperf -s -p 5002 > /tmp/iperf_server.log &')
    time.sleep(2)
    
    # サーバーが起動したか確認
    server_check = receiver.cmd('ss -tulpn | grep 5002')
    info('*** MPTCPサーバー起動確認:\n')
    info(server_check)
    
    if not '5002' in server_check:
        info('*** 警告: iperサーバーが起動していない可能性があります\n')
        return 0
    
    # パケットキャプチャ開始 - より長い時間キャプチャ
    info('*** パケットキャプチャ開始\n')
    sender.cmd('tcpdump -i any -n -s 65535 tcp port 5002 -w ./data/mptcp_test.pcap &')
    time.sleep(1)
    
    # MPTCPの安定したテスト（より長い時間実行）
    info('*** MPTCP帯域幅テスト実行中 (30秒間)\n')
    result = sender.cmd('mptcpize run iperf -c 10.0.1.2 -p 5002 -t 30 -w 256k')
    
    # サブフロー情報分析
    info('*** MPTCPサブフロー情報:\n')
    subflow_info = sender.cmd('ss -tiM state established')
    info(subflow_info)
    
    # サブフロー詳細情報の取得
    info('*** MPTCP詳細情報:\n')
    info(sender.cmd('ss -tiM state established | grep -A 3 "mptcp"'))
    
    # 結果抽出
    bw_match = re.search(r'(\d+\.?\d*)\s+(Mbits|Gbits|Kbits)/sec', result)
    if bw_match:
        bw_value = float(bw_match.group(1))
        bw_unit = bw_match.group(2)
        # 単位変換
        if bw_unit == 'Gbits':
            mptcp_bw = bw_value * 1000
        elif bw_unit == 'Kbits':
            mptcp_bw = bw_value / 1000
        else:
            mptcp_bw = bw_value
        info(f'*** MPTCP帯域幅: {mptcp_bw:.2f} Mbits/sec\n')
    else:
        mptcp_bw = 0
        info('*** 結果抽出に失敗しました\n')
    
    # 各インターフェースのトラフィック統計
    info('*** 各インターフェースのトラフィック統計:\n')
    info(sender.cmd('ip -s link show sender-eth0'))
    info(sender.cmd('ip -s link show sender-eth1'))
    
    # パケットキャプチャ分析
    info('*** パケットキャプチャ停止\n')
    sender.cmd('pkill -SIGINT tcpdump')
    time.sleep(1)
    
    # 各サブフローのトラフィック分布を分析
    info('*** サブフロー別トラフィック分析:\n')
    info(sender.cmd('tcpdump -r ./data/mptcp_test.pcap -nn "tcp src port 5002" | wc -l'))
    info('*** 経路1 (10.0.0.0/24) トラフィック量:\n')
    info(sender.cmd('tcpdump -r ./data/mptcp_test.pcap -nn "host 10.0.0.1" | wc -l'))
    info('*** 経路2 (10.1.0.0/24) トラフィック量:\n')
    info(sender.cmd('tcpdump -r ./data/mptcp_test.pcap -nn "host 10.1.0.1" | wc -l'))
    
    # MPTCP JOINパケット確認
    info('*** MPTCPのJOINパケット分析:\n')
    join_packets = sender.cmd('tcpdump -r ./data/mptcp_test.pcap -vv | grep -i "join" | wc -l')
    info(f'JOIN パケット数: {join_packets}\n')
    
    # 結果をファイルに保存
    with open('./data/mptcp_test_result.txt', 'w') as f:
        f.write(f'MPTCP帯域幅: {mptcp_bw:.2f} Mbits/sec\n\n')
        f.write('=== テスト結果 ===\n')
        f.write(result)
        f.write('\n\n=== サブフロー情報 ===\n')
        f.write(subflow_info)
    
    # サーバー停止
    receiver.cmd('pkill -9 iperf')
    
    # MPTCP詳細情報分析
    analyzeMPTCPConnections(sender)
    
    return mptcp_bw

def analyzeMPTCPResults(mptcp_bw):
    """MPTCPテスト結果分析"""
    info('\n*** MPTCPテスト結果:\n')
    info(f'   MPTCP総帯域幅 (2 x 5Mbps): {mptcp_bw:.2f} Mbits/sec\n')
    
    # 結果をファイルに保存
    with open('./data/results_summary.txt', 'w') as f:
        f.write(f'MPTCP総帯域幅 (2 x 5Mbps): {mptcp_bw:.2f} Mbits/sec\n')
        
        # 理論値との比較
        theoretical = 10.0  # 2 x 5Mbps
        efficiency = (mptcp_bw / theoretical) * 100
        f.write(f'理論値効率: {efficiency:.2f}%\n')
        
        if efficiency > 80:
            f.write('\n結果分析: MPTCPが正常に動作し、両方の経路を効率的に使用しています。\n')
            f.write(f'理論値の{efficiency:.1f}%の効率を達成しました。\n')
        elif efficiency > 60:
            f.write('\n結果分析: MPTCPは動作していますが、最適化の余地があります。\n')
        else:
            f.write('\n結果分析: MPTCPのパフォーマンスが期待より低いです。\n')
            f.write('設定の見直しや他の要因の確認が必要かもしれません。\n')
    
    # 標準出力にも表示
    info(f'   理論値効率: {(mptcp_bw / 10.0) * 100:.2f}%\n')
    
    if (mptcp_bw / 10.0) > 0.8:
        info('\n*** 結果分析: MPTCPが正常に動作し、両方の経路を効率的に使用しています。\n')
    elif (mptcp_bw / 10.0) > 0.6:
        info('\n*** 結果分析: MPTCPは動作していますが、最適化の余地があります。\n')
    else:
        info('\n*** 結果分析: MPTCPのパフォーマンスが期待より低いです。\n')
