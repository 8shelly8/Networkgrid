FROM alpine:latest

RUN apk add --no-cache openssh knock iptables postgresql-client

RUN ssh-keygen -A && \
    adduser -D fishmaster && \
    mkdir -p /home/fishmaster/.ssh && \
    chmod 700 /home/fishmaster/.ssh

# Copy hardened configs and tools
COPY sshd_config /etc/ssh/sshd_config
COPY knockd.conf /etc/knockd.conf
COPY startup.sh /startup.sh
COPY wishingwell-docs /usr/local/bin/wishingwell-docs
RUN chmod +x /startup.sh /usr/local/bin/wishingwell-docs

# Install pre-shared public key for fishmaster
COPY id_ed25519.pub /home/fishmaster/.ssh/authorized_keys
RUN chmod 600 /home/fishmaster/.ssh/authorized_keys

# Plant Flag 2, .pgpass, and MOTD
RUN echo "FLAG:congrats you got in to my ssh continue" > /home/fishmaster/flag2.txt && \
    chmod 400 /home/fishmaster/flag2.txt && \
    echo "172.30.0.40:5432:Wishingwell:shepherd:G4ld3n_c011ar_7li6ht" > /home/fishmaster/.pgpass && \
    chmod 600 /home/fishmaster/.pgpass && \
    echo "Node WW-SSH-01 active. Run 'wishingwell-docs' for internal infrastructure documentation." > /etc/motd && \
    chown -R fishmaster:fishmaster /home/fishmaster

EXPOSE 22

CMD ["/startup.sh"]
