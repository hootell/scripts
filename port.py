# -*- coding: utf-8 -*-

import threading, socket, sys, os, Queue
import time

class ScannerThread(threading.Thread):
    def __init__(self, inq, outq):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.inq = inq
        self.outq = outq
        self.killed = False
        self.timeout = 1

    def run(self):
        while not self.killed:
            host, port = self.inq.get()
            #print threading.currentThread(),host
            sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sd.settimeout(self.timeout)
            try:
                sd.connect((host, port))
                self.outq.put((host, port, 'OPENED'))
            except socket.error:
                self.outq.put((host, port, 'CLOSED'))             
            sd.close()


class Scanner:
    def __init__(self, from_port, to_port, host='localhost'):
        self.from_port = from_port
        self.to_port = to_port
        self.host = host
        self.scanners = []

    def scan(self, nthreads=10,send_fn=None):
        self.resp = []
        toscan = Queue.Queue()
        scanned = Queue.Queue()
        self.scanners = [ScannerThread(toscan, scanned) for i in range(nthreads)]
        #print self.scanners
        for scanner in self.scanners:
            scanner.start()
        hostports = [(self.host, port) for port in range(self.from_port, self.to_port+1)]
        for hostport in hostports:
            toscan.put(hostport)

        results = {}
        for host, port in hostports:
            while (host, port) not in results:
                nhost, nport, nstatus = scanned.get()
                results[(nhost, nport)] = nstatus
            status = results[(host, port)]
            progress = ('%.2f' % (float(port)/float(65530)))
            value = (host, port, status,progress)
            if status == 'OPENED':
                if send_fn:
                    send_fn(value)
        return self._finish_scan()

    def _finish_scan(self):
        for scanner in self.scanners:
            scanner.join(0.01)
            scanner.killed = True
        return self.resp

def save(ip):
	print(ip[0],ip[1],ip[2], ip[3])
scanner = Scanner(from_port=21, to_port=65530,host=sys.argv[1])
scanner.scan(nthreads=100, send_fn=save)
