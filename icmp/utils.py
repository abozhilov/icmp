from icmp.Ping import Ping
from icmp.PingStatus import PingStatus
from icmp.PingSummary import PingSummary

def ping(host, packet_size = Ping.DEFAULT_PACKET_SIZE, timeout = Ping.DEFAULT_TIMEOUT, ttl = Ping.DEFAULT_TTL):
    my_ping = Ping(packet_size, timeout)
    return my_ping.send(host, ttl)

def ping_test(host, count = 4, packet_size = Ping.DEFAULT_PACKET_SIZE, timeout = Ping.DEFAULT_TIMEOUT, ttl = Ping.DEFAULT_TTL):
    my_ping = Ping(packet_size, timeout)
    summary = PingSummary()
    
    for i in range(count):
        summary.append(my_ping.send(host, ttl))
    summary.end()
    
    return summary
    
