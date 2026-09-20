#!/bin/sh

    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    iptables -A INPUT -p tcp --dport 22 -j DROP

    
    knockd -d

    exec /usr/sbin/sshd -D
