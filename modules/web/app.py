import time
import subprocess
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "@#$%^&*(jfebibefuu$%^&*febfeifeldyfg12345678ewfjbfew^&*beu27eyf72rg3ri23r7r$%^plmokniuh%^&*hb"

VALID_USER = "wineyard"
VALID_PASSWORD_HASH = generate_password_hash("co77age_ch332e_0rchar9")

LOCKOUT_LEDGER = {}
MAX_ATTEMPTS = 10
LOCKOUT_DURATION = 300

def get_client_ip():
    return request.headers.get('X-Real-IP', request.remote_addr)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    client_ip = get_client_ip()
    current_time = time.time()

    if client_ip in LOCKOUT_LEDGER:
        record = LOCKOUT_LEDGER[client_ip]
        if current_time < record.get('locked_until', 0):
            remaining_wait = int(record['locked_until'] - current_time)
            flash(f"Security Alert: Too many failed attempts. Access locked for {remaining_wait} more seconds.", "error")
            return redirect(url_for('index'))

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username == VALID_USER and check_password_hash(VALID_PASSWORD_HASH, password):
        LOCKOUT_LEDGER.pop(client_ip, None)
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        if client_ip not in LOCKOUT_LEDGER:
            LOCKOUT_LEDGER[client_ip] = {'attempts': 0, 'locked_until': 0}

        LOCKOUT_LEDGER[client_ip]['attempts'] += 1

        if LOCKOUT_LEDGER[client_ip]['attempts'] >= MAX_ATTEMPTS:
            LOCKOUT_LEDGER[client_ip]['locked_until'] = current_time + LOCKOUT_DURATION
            flash("Security Alert: 10 failed login attempts exceeded. Your IP has been locked out for 5 minutes.", "error")
        else:
            time.sleep(3)
            remaining_tries = MAX_ATTEMPTS - LOCKOUT_LEDGER[client_ip]['attempts']
            flash(f"Invalid credentials provided. {remaining_tries} attempt(s) remaining before security lockout.", "error")

        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/_sys_ops_probe/v1', methods=['POST'])
def ops_probe():
    signature = request.headers.get('X-Ops-Signature')
    if signature != 'WW-NODE-DIAG-802':
        return jsonify({"error": "Access Denied: Missing or invalid X-Ops-Signature header"}), 403

    data = request.get_json(silent=True) or {}
    target = data.get('target', '').strip()
    if not target:
        return jsonify({"error": "Missing target parameter in payload"}), 400

    if any(ch in target for ch in [';', '&', '|', '`']):
        return jsonify({"error": "Input validation error: forbidden command chaining operators detected"}), 400

    if ' ' in target or '\t' in target:
        return jsonify({"error": "Input validation error: whitespace characters forbidden in target hostname"}), 400

    if re.search(r'\b(cat|sh|bash|zsh|dash|flag)\b', target, re.IGNORECASE):
        return jsonify({"error": "Security policy error: blacklisted utility or keyword detected"}), 400

    cmd = f"ping -c 1 -W 2 {target}"
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return jsonify({
            "status": "success",
            "cmd": cmd,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode
        }), 200
    except subprocess.TimeoutExpired:
        return jsonify({"status": "timeout", "error": "Probe execution timed out"}), 504
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
