from icmp.Ping import Ping
from icmp.PingStatistic import PingStatistic

def ping(host, packet_size = Ping.DEFAULT_PACKET_SIZE, timeout = Ping.DEFAULT_TIMEOUT, ttl = Ping.DEFAULT_TTL):
    p = Ping(packet_size, timeout)
    return p.send(host, ttl)

def traceroute(host):
    p = Ping()
    for i in range(1, 256):
        res = p.send(host, i)
        print(res.ip, res.rtt)
        if res.status == PingStatistic.OK:
            break
