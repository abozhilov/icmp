from PingStatistic import PingStatistic

import socket
import struct
import ctypes
import select
import time

        
class Ping:
    ICMP = socket.getprotobyname('icmp')
    ICMP_HEADER_SIZE = 8
    IP_HEADER_SIZE = 20
    MIN_PACKET_SIZE = 8
    MAX_PACKET_SIZE = 65515
    MIN_TTL = 1
    MAX_TTL = 255
    RECEIVE_BUFF_SIZE = 2 * (ICMP_HEADER_SIZE + IP_HEADER_SIZE)
    
    DEFAULT_TTL = 64
    DEFAULT_PACKET_SIZE = 64 # bytes
    DEFAULT_TIMEOUT = 2 # secs
    
    ECHO_REPLY = 0
    DESTINATION_UNREACHABLE = 3
    ECHO_REQUEST = 8
    TTL_EXCEED = 11
    PARAM_ERROR = 12

    PING_MESSAGES = {
        ECHO_REPLY : [
            'OK'
        ],
        DESTINATION_UNREACHABLE : [
            'Destination network unreachable',
            'Destination host unreachable',
            'Destination protocol unreachable',
            'Destination port unreachable',
            'Fragmentation required',
            'Source route failed',
            'Destination network unknown',
            'Destination host unknown',
            'Source host isolated',
            'Network administratively prohibited',
            'Host administratively prohibited',
            'Network unreachable',
            'Host unreachable',
            'Communication administratively prohibited',
            'Host Precedence Violation',
            'Precedence cutoff in effect'
        ],
        TTL_EXCEED : [
            'TTL expired in transit',
            'Fragment reassembly time exceeded'
        ],
        PARAM_ERROR : [
            'Parameter Problem',
            'Missing a required option',
            'Bad length'
        ]
    }
    UNKNOWN_HOST = 'Unknown host'
    OPERATION_TIMEOUT = 'Operation timeout'
    
    def __init__(self, ttl = DEFAULT_TTL, packet_size = DEFAULT_PACKET_SIZE, timeout = DEFAULT_TIMEOUT):
        self.id = id(self) & 0xFFFF
        self.sequence = 0
        self.timeout = timeout
        self.set_packet_size(packet_size)
        self.set_ttl(ttl)
        
    def set_packet_size(self, packet_size):
        self.packet_size = min(max(packet_size, Ping.MIN_PACKET_SIZE), Ping.MAX_PACKET_SIZE)
        
    def set_ttl(self, ttl):
        self.ttl = min(max(ttl, Ping.MIN_TTL), Ping.MAX_TTL)
    
    def checksum(self, buff):
        size = self.packet_size
        sum = 0
        idx = 0
        
        while size > 1:
            sum += struct.unpack('>H', buff[idx:idx + 2])[0]
            idx += 2
            size -= 2
        
        if size:
            sum += ord(buff[idx]) << 8
            
        while sum >> 16:
            sum = (sum & 0xFFFF) + (sum >> 16);
        
        return ~sum & 0xFFFF

    def create_packet(self):
        self.sequence = (self.sequence + 1) & 0xFFFF 
        data_size = self.packet_size - Ping.ICMP_HEADER_SIZE
        buff = ctypes.create_string_buffer(self.packet_size)
        icmp_packet = struct.pack_into(
            'bbHHH{0}s'.format(data_size),
            buff,
            0,
            Ping.ECHO_REQUEST,
            0,
            0,
            self.id,
            self.sequence,
            '1' * data_size
        )
        struct.pack_into('!H', buff, 2, self.checksum(buff))

        return buff
        
    def parse_packet(self, data):
        id = 0
        sequence = 0
        type, code = struct.unpack('bb', data[:2])
        
        if type == Ping.ECHO_REPLY:
            id, sequence = struct.unpack('HH', data[4:8])
        elif type in [Ping.DESTINATION_UNREACHABLE, Ping.TTL_EXCEED, Ping.PARAM_ERROR]:
            id, sequence = struct.unpack('HH', data[Ping.ICMP_HEADER_SIZE + Ping.IP_HEADER_SIZE:][4:8])
            
        return type, code, id, sequence
    
    def send_packet(self, packet, host):
        while packet:
            bytes_sent = self.icmp_socket.sendto(packet, (host, 1))
            packet = packet[bytes_sent:] 
            
        self.stat.sent()
            
    def recv_packet(self):
        timeout = self.timeout 
        while True:
            s_start = time.time()
            ready = select.select([self.icmp_socket], [], [], timeout)
            timeout -= time.time() - s_start
            self.stat.received()
            
            if not len(ready[0]) or timeout < 0:
                self.stat.end(PingStatistic.TIMEOUT_ERROR, Ping.OPERATION_TIMEOUT)
                return
                
            data, addr = self.icmp_socket.recvfrom(Ping.RECEIVE_BUFF_SIZE)
            type, code, id, sequence = self.parse_packet(data[Ping.IP_HEADER_SIZE:])

            if self.id == id and self.sequence == sequence:
                self.stat.set_ip(addr[0])
                self.stat.set_ttl(struct.unpack('b', data[Ping.IP_HEADER_SIZE + 9])[0])
                if type == Ping.ECHO_REPLY:
                    self.stat.end(PingStatistic.OK, Ping.PING_MESSAGES[Ping.ECHO_REPLY][code])
                else:
                    self.stat.end(PingStatistic.PING_ERROR, Ping.PING_MESSAGES[type][code])
                    
                return 

    
    def send(self, host):
        self.stat = PingStatistic()
        self.icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, Ping.ICMP)
        self.icmp_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, self.ttl)
        packet = self.create_packet()
        
        self.send_packet(packet, host)
        self.recv_packet()
        self.icmp_socket.close()
        
        return self.stat

if __name__ == '__main__':
    p = Ping(packet_size = 64, timeout = 20, ttl = 11)
    r = p.send('192.168.0.1')
    print(r.status, r.status_text, r.ip, r.ttl, r.rtt)
