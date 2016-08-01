from icmp.PingStatus import PingStatus

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
    DEFAULT_TIMEOUT = 1 # sec
    
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
    UNKNOWN_HOST = 'Unknown hostname'
    OPERATION_TIMEOUT = 'Operation timeout'
    
    def __init__(self, packet_size = DEFAULT_PACKET_SIZE, timeout = DEFAULT_TIMEOUT):
        self.id = id(self) & 0xFFFF
        self.sequence = 0
        self.timeout = timeout
        self.host_map = {}
        self.set_packet_size(packet_size)
        
    def set_packet_size(self, packet_size):
        self.packet_size = min(max(packet_size, Ping.MIN_PACKET_SIZE), Ping.MAX_PACKET_SIZE)
        
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
            b'1' * data_size
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
    
    def send_packet(self, icmp_socket, host, packet, stat):
        while packet:
            bytes_sent = icmp_socket.sendto(packet, (host, 1))
            packet = packet[bytes_sent:] 
            
        stat.sent()
            
    def recv_packet(self, icmp_socket, sent_sequence, stat):
        timeout = self.timeout 
        while True:
            s_start = time.time()
            ready = select.select([icmp_socket], [], [], timeout)
            timeout -= time.time() - s_start
            stat.received()
            
            if not len(ready[0]) or timeout < 0:
                stat.end(PingStatus.TIMEOUT_ERROR, Ping.OPERATION_TIMEOUT)
                return
                
            data, addr = icmp_socket.recvfrom(Ping.RECEIVE_BUFF_SIZE)
            type, code, id, sequence = self.parse_packet(data[Ping.IP_HEADER_SIZE:])

            if self.id == id and sent_sequence == sequence:
                stat.set_ip(addr[0])
                stat.set_ttl(struct.unpack('b', data[8:9])[0])
                stat.set_sequence(sent_sequence)
                if type == Ping.ECHO_REPLY:
                    stat.end(PingStatus.OK, Ping.PING_MESSAGES[Ping.ECHO_REPLY][code])
                else:
                    stat.end(PingStatus.PING_ERROR, Ping.PING_MESSAGES[type][code])
                    
                return 

    
    def send(self, host, ttl = DEFAULT_TTL):
        stat = PingStatus(host)
        packet = self.create_packet()
        
        if host in self.host_map:
            ip = self.host_map[host]
        else:
            try:
                resolve_start = time.time()
                ip = socket.gethostbyname(host)
                stat.host_resolved((time.time() - resolve_start) * 1000)
                self.host_map[host] = ip
            except socket.gaierror as err:
                stat.end(PingStatus.NAME_ERROR, Ping.UNKNOWN_HOST)
                return stat
        
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, Ping.ICMP)
        try:
            icmp_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, min(max(ttl, Ping.MIN_TTL), Ping.MAX_TTL))
            self.send_packet(icmp_socket, ip, packet, stat)
            self.recv_packet(icmp_socket, self.sequence, stat)
        finally:
            icmp_socket.close()
        
        return stat
