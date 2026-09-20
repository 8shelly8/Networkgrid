# NetworkGrid - Architecture & Defense Writeup

This is a breakdown of the virtual network setup, how each service is defended, and why it was built this way.

---

## 1. Network Map

```text
[ Attacker / Laptop ]
         │
         │ (Only port 8080 is open to the outside)
         ▼
┌────────────────────────────────────────────────────────┐
│ External DMZ Subnet (172.20.0.0/24)                    │
│                                                        │
│   [ Router ] (172.20.0.10)                             │
│       │                                                │
│       ▼                                                │
│   [ Web Server ] (172.20.0.20) ◄─────────┐             │
└──────────────────────────────────────────┼─────────────┘
                                           │ (Dual-Homed)
┌────────────────────────────────────────────────────────┐
│ Internal Subnet (172.30.0.0/24)          │             │
│ (No internet / air-gapped)               │             │
│                                   [ Web Server ]       │
│                                   (172.30.0.20)        │
│                                          │             │
│                   ┌──────────────────────┴──────────┐  │
│                   ▼                                 ▼  │
│          [ Stealth SSH ]                      [ Database ]
│           (172.30.0.30)                      (172.30.0.40)
│         (Port Knocking)                    (Locked to /32)
└────────────────────────────────────────────────────────┘
```

---

## 2. The Subnets & Routing

There are two subnets:

* **DMZ Subnet (`172.20.0.0/24`)**: The external zone. The only service exposed to your computer is the router on port 8080.
* **Internal Subnet (`172.30.0.0/24`)**: Air-gapped with `internal: true`. Nothing on this network can talk to the public internet, meaning attackers cannot easily pop reverse shells back out.
* **The Web Server is Dual-Homed**: It sits on both subnets so it can talk to the router on one side, and the internal machines on the other side. It is the only bridge between the two networks.

---

## 3. The Router (Gateway)

The router is the only way in or out. It maps port 8080 on your computer to port 80 on the router, and forwards clean traffic to the web server at `172.20.0.20:80`.

It has several defense rules configured in Nginx:

1. **Server tokens are off**: Hides the Nginx version so attackers cannot easily look up known CVE exploits for it.
2. **Buffer limits**: Caps body and header sizes to stop massive malicious payloads or buffer overflow attempts.
3. **Rate limiting**: Limits traffic to 10 requests/second with a small burst buffer of 15 requests to stop brute-forcing and rapid directory fuzzing.
4. **Method whitelist**: Only allows `GET` and `POST`. Any other methods (`PUT`, `DELETE`, `OPTIONS`, `TRACE`) immediately get a `405 Not Allowed`.
5. **Scanner block**: Drops connections from known scanner tools like `sqlmap`, `nikto`, `wpscan`, `gobuster`, and `dirbuster` returning `444`.
6. **Recon trap (Tarpit)**: If someone tries scanning for sensitive files like `/.git`, `/.env`, `phpmyadmin`, or `wp-login`, the router returns `444`, dropping the connection without sending headers.
7. **Security headers**:
   * `X-Frame-Options: DENY` (Stops clickjacking by preventing the site from being loaded inside an iframe).
   * `X-Content-Type-Options: nosniff` (Stops browsers from trying to guess file types).
   * `Content-Security-Policy: default-src 'self'` (Only allows scripts to run from this site directly).
   * `X-XSS-Protection: 1; mode=block` (Blocks reflected XSS).

---

## 4. The Web Server & Application

The web server runs a custom Python Flask app serving a corporate login portal and internal maintenance tools:

1. **One-way password hashing**: Passwords are never stored in plaintext. They are salted and hashed using PBKDF2/scrypt, so the database only compares hashes.
2. **No username enumeration**: It returns the exact same generic error message whether the username exists or not, and whether the password is wrong or right.
3. **3-second penalty delay**: Every failed login forces a 3-second sleep before answering, making automated password lists take hours instead of seconds.
4. **Server-side IP lockout**: If an IP address fails 10 logins, it gets locked out for 5 minutes (300 seconds). Because this counter is tracked in memory on the server using `X-Real-IP`, clearing cookies or opening incognito tabs does not bypass the lockout.
5. **Diagnostic Utility & Access Restrictions**:
   * An internal diagnostic probe route (`/_sys_ops_probe/v1`) exists for cluster health monitoring.
   * Direct access is gated by an authentication signature header (`X-Ops-Signature: WW-NODE-DIAG-802`) loaded dynamically through the client telemetry script (`portal-telemetry.min.js`).
   * Input filtering blocks standard command chaining characters (`;`, `&`, `|`, backticks), spaces, and utility keywords (`cat`, `sh`, `bash`, `flag`).
6. **Milestone 1 Flag**: Embedded in the authenticated operations dashboard.

---

## 5. The Stealth SSH Bastion

The SSH service sits on the internal network (`172.30.0.30`) with zero exposed ports to your computer.

1. **Port Knocking (knockd)**: Port 22 is dropped by default in `iptables`. A port scan will show it as completely closed.
2. **The Knock Sequence**: You have to send SYN packets to ports 1950, 7777, and 10502 in that exact order within 10 seconds.
3. **Single-IP Opening**: When knocked, the firewall opens port 22 only for the specific IP that knocked.
4. **Auto-relock**: After 30 seconds, `knockd` removes the firewall rule and locks the door again.
5. **Stateful Connection Tracking**: The startup script includes `ESTABLISHED,RELATED`, which means if an admin is already logged in and the 30-second timer expires, they don't get kicked out of their session.
6. **Key-only access**: Passwords and root login are completely disabled. It strictly requires an ED25519 private key.
7. **In-Memory Credential Lifecycle**: The private key is deleted from the filesystem upon container startup and held strictly in the process environment of the background sync daemon.
8. **Milestone 2 Flag**: Stored inside `/home/fishmaster/flag2.txt`.

---

## 6. The Database

The PostgreSQL database runs at `172.30.0.40`:

1. **Host-Based Access (`pg_hba.conf`)**:
   * Allows internal local socket connections so the database process can run.
   * Allows network connections only from the SSH bastion (`172.30.0.30/32`).
   * Explicitly rejects all other connections.
2. **The /32 Subnet**: The `/32` mask locks down the rule to exactly one specific machine. Even if someone gets into the web server and finds database credentials, the database will refuse their connection because they are coming from `172.30.0.20`.
3. **Internal Documentation & Credential Caching**: Administrative database procedures are documented in `wishingwell-docs`, utilizing standard user-level `~/.pgpass` credential caching.
4. **Milestone 3 Flag**: Seeded inside the `employee_vault` table.

---

## 7. Testing & Verification Commands

To verify that these defenses actually work:

```bash
# 1. Test normal website access
curl -i http://localhost:8080/

# 2. Test blocked HTTP method (Returns 405)
curl -i -X DELETE http://localhost:8080/

# 3. Test scanner tool blocking (Returns empty reply / 444)
curl -i -A "sqlmap" http://localhost:8080/

# 4. Test recon trap on sensitive file (Returns empty reply / 444)
curl -i http://localhost:8080/.env

# 5. Test diagnostic probe rejection without signature (Returns 403)
curl -i -X POST http://localhost:8080/_sys_ops_probe/v1

# 6. Test port knock from web container to SSH bastion:
# Before knock (times out):
docker compose exec web nc -zv -w 2 172.30.0.30 22

# Send the knock sequence:
docker compose exec web sh -c "nc -z -w 1 172.30.0.30 1950; nc -z -w 1 172.30.0.30 7777; nc -z -w 1 172.30.0.30 10502"

# After knock (opens port 22):
docker compose exec web nc -zv -w 2 172.30.0.30 22

# 7. Test database isolation:
# Direct connection from web container is rejected by pg_hba.conf:
docker compose exec web nc -zv -w 2 172.30.0.40 5432
```
