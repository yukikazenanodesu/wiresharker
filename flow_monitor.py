# -*- coding: utf-8 -*-
""" 流量监测系统 """
from threading import Thread, Event
from scapy.sendrecv import sniff
from scapy.layers.inet import *
import psutil


class Monitor:
    """
    流量监测
    """
    # 程序使用的端口
    process_ports = []
    # 监测系统是否开始
    start_flag = Event()
    window = None

    def __init__(self, window):
        self.window = window
        self.start_flag.set()

    def getProcessList(self):
        """
        获取有网络连接的进程列表
        :return :返回进程列表
        """
        process_list = set()
        for process in psutil.process_iter():
            connections = process.connections()
            if connections:
                process_list.add(process.name())
        return list(process_list)

    def getPortList(self, process_name):
        """
        用于刷新某个进程的端口列表的函数
        将获得的端口列表设置到self.process_ports
        :parma process_name: 输入为程序的名字
        """
        while not self.start_flag.is_set():
            ports = set()
            for process in psutil.process_iter():
                connections = process.connections()
                if process.name() == process_name and connections:
                    for con in connections:
                        if con.laddr:
                            ports.add(con.laddr[1])
                        if con.raddr:
                            ports.add(con.raddr[1])
            self.process_ports = list(ports)
            if self.process_ports:
                pass
                #self.window.conList.scrollToBottom()
                # 每1秒执行一次
                #sleep(1)
            else:
                # 进程已不存在, 停止刷新
                self.start_flag.set()

    def getConnections(self, pak):
        """
        获取应用的连接信息
        :parma pak: 数据包
        """
        src = pak.payload.src
        dst = pak.payload.dst
        sport = pak.payload.payload.sport
        dport = pak.payload.payload.dport
        protocol = pak.payload.payload.name
        length = len(pak)
        if sport in self.process_ports and dport in self.process_ports:
            info = "%-6s%s:%d -> %s:%d%7d" % (protocol, src, sport, dst, dport,
                                              length)
            if protocol == 'TCP':
                info += '%5s' % str(pak.payload.payload.flags)
            self.window.conList.addItem(info)

    def capture_packet(self):
        """
        设置过滤器, 只接收IP、IPv6、TCP、UDP
        """
        sniff(
            store=False,
            filter="(tcp or udp) and (ip6 or ip)",
            prn=lambda x: self.getConnections(x),
            stop_filter=lambda x: self.start_flag.is_set())

    def start(self, process_name):
        """
        开始对某一进程的流量监视
        :parma process_name: 进程的名字
        """
        # 开启刷新程序端口的线程
        self.start_flag.clear()
        self.window.conList.clear()
        Thread(
            target=self.getPortList, daemon=True,
            args=(process_name, )).start()
        Thread(target=self.capture_packet, daemon=True).start()

    def stop(self):
        """
        停止监测
        """
        self.start_flag.set()