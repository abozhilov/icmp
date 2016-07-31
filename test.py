import icmp

ping_res = icmp.ping('websitepulse.com') 
print('''Host        : {0}
IP          : {1}
Status      : {2}
StatusText  : {3}
TTL         : {4:d}
DNS         : {5:.2f} ms
ResponseTime: {6:.2f} ms'''.format(
        ping_res.host, 
        ping_res.ip, 
        ping_res.status, 
        ping_res.status_text, 
        ping_res.ttl, 
        ping_res.dns, 
        ping_res.rtt
    )
)
