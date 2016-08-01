import time
from icmp.PingStatus import PingStatus

class PingSummary:
    
    def __init__(self):
        self.ping_results = []
        self.sent = 0
        self.received = 0
        self.lost = 0
        self.min = 0
        self.average = 0
        self.max = 0
        self.time = 0
        
    def end(self):
        pass

    def append(self, ping_res):
        self.sent += 1
        if ping_res.status == PingStatus.OK:
            self.received += 1
            
        self.ping_results.append(ping_res)
