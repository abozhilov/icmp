# icmp
Python ICMP protocol tools

```python
import icmp

ping_res = icmp.ping('google.com') 
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
```

```
Host        : google.com
IP          : 217.174.48.16
Status      : 0
StatusText  : OK
TTL         : 62
DNS         : 13.17 ms
ResponseTime: 8.49 ms
```
