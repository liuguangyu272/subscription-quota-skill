"""Read account type and quota in one local Codex app-server connection. No credential file reads."""
import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time

PAID_PLANS = {'plus', 'pro', 'team', 'business', 'enterprise', 'edu'}


def executable():
    found = shutil.which('codex.exe')
    if found:
        return found
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', '')) / 'npm/node_modules/@openai/codex/node_modules'
        matches = list(base.glob('@openai/codex-*/vendor/*/codex/codex.exe'))
        if matches:
            return str(matches[0])
    found = shutil.which('codex')
    if not found:
        raise RuntimeError('Codex executable unavailable; provide --codex with its executable path.')
    return found


def read(codex):
    proc = subprocess.Popen([codex, 'app-server', '--listen', 'stdio://'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    messages = queue.Queue()
    def pump():
        for line in proc.stdout:
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    messages.put(value)
            except ValueError:
                pass
    worker = threading.Thread(target=pump, daemon=True)
    worker.start()
    deadline = time.monotonic() + 20
    def send(message):
        proc.stdin.write(json.dumps(message) + '\n')
        proc.stdin.flush()
    def rpc(identifier, method, params=None):
        send({'id': identifier, 'method': method, 'params': params or {}})
        while time.monotonic() < deadline:
            try:
                message = messages.get(timeout=min(.25, max(.001, deadline-time.monotonic())))
            except queue.Empty:
                if proc.poll() is not None:
                    raise RuntimeError('Codex app-server exited before replying.')
                continue
            if message.get('id') == identifier:
                if 'error' in message:
                    raise RuntimeError(f'Codex {method} failed; inspect account status in the app.')
                return message['result']
        raise RuntimeError('Codex account/quota read timed out.')
    try:
        rpc(1, 'initialize', {'clientInfo': {'name': 'subscription-quota', 'version': '0.1.0'}})
        send({'method': 'initialized', 'params': {}})
        account = rpc(2, 'account/read', {'refreshToken': False})
        limits = rpc(3, 'account/rateLimits/read') if (account.get('account') or {}).get('type') == 'chatgpt' else {}
        return account, limits
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        worker.join(timeout=1)
        proc.stdin.close()
        proc.stdout.close()


def normalize(account_result, limits_result, route, scope_verified, now=None):
    account = account_result.get('account') or {}
    kind, plan = account.get('type'), account.get('planType')
    billing = 'subscription' if kind == 'chatgpt' and plan in PAID_PLANS else 'metered' if kind == 'apiKey' else 'unknown'
    snap = {'schema_version': 1, 'route': route, 'scope_verified': scope_verified,
        'observed_at': time.time() if now is None else now, 'billing': billing,
        'evidence': {'source': 'codex-app-server', 'auth_type': kind, 'plan': plan}, 'windows': []}
    buckets = limits_result.get('rateLimitsByLimitId')
    if isinstance(buckets, dict) and buckets:
        limits = buckets.get('codex')
        if limits is None:
            return snap  # Never silently choose another model's bucket.
    else:
        limits = limits_result.get('rateLimits') or {}
        if limits.get('limitId') not in (None, 'codex'):
            return snap
    for name in ('primary', 'secondary'):
        w = limits.get(name) if limits else None
        if w:
            snap['windows'].append({'id': name, 'remaining_percent': 100-w['usedPercent'],
                'window_hours': w['windowDurationMins']/60, 'resets_at': w['resetsAt']})
    return snap


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--route', required=True)
    p.add_argument('--confirm-current-route', action='store_true', help='Caller verified this CLI profile is the active task account/provider')
    p.add_argument('--codex')
    a = p.parse_args()
    try:
        account, limits = read(a.codex or executable())
        result = normalize(account, limits, a.route, a.confirm_current_route)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'UNKNOWN', 'reason': str(exc)}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
