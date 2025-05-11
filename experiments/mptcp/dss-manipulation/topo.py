#!/usr/bin/python
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import Node

# Linuxルーターの定義
class LinuxRouter(Node):
    """ルーティング機能を持つノード"""
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class MPTCPTopo(Topo):
    def build(self):
        # ホスト追加
        sender = self.addHost('sender')
        receiver = self.addHost('receiver')
        
        # 直接ルーター間の接続を作成（スイッチなし - よりシンプルなトポロジー）
        r1 = self.addNode('r1', cls=LinuxRouter)
        r2 = self.addNode('r2', cls=LinuxRouter)
        
        # リンクのパラメータを明示的に設定
        link_opts1 = dict(bw=5, delay='10ms', loss=0, max_queue_size=1000, use_htb=True)
        link_opts2 = dict(bw=5, delay='9ms', loss=0, max_queue_size=1000, use_htb=True)

        
        # 経路1: sender -- r1 -- receiver (各5Mbps)
        self.addLink(sender, r1, cls=TCLink, **link_opts1)  # sender-eth0, r1-eth0
        self.addLink(r1, receiver, cls=TCLink, **link_opts1)  # r1-eth1, receiver-eth0
        
        # 経路2: sender -- r2 -- receiver (各5Mbps)
        self.addLink(sender, r2, cls=TCLink, **link_opts2)  # sender-eth1, r2-eth0
        self.addLink(r2, receiver, cls=TCLink, **link_opts2)  # r2-eth1, receiver-eth1
