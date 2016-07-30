import time

class PingStatistic:
    OK = 0
    HOST_ERROR = 1
    PING_ERROR = 2
    TIMEOUT_ERROR = 3
    
    def __init__(self):
        self.status = 0
        self.status_text = ''
        self.ip = ''
        self.ttl = 0
        self.start_time = 0
        self.end_time = 0
        self.rtt = 0

    def sent(self):
        self.start_time = time.time()
        
    def received(self):
        self.end_time = time.time()
        self.rtt = (self.end_time - self.start_time) * 1000
        
    def set_ip(self, ip):
        self.ip = ip
        
    def set_ttl(self, ttl):
        self.ttl = ttl
        
    def end(self, status, message):
        self.status = status
        self.status_text = message
