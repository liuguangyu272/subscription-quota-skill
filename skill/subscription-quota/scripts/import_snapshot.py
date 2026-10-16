"""Convert credential-free native exports. This does not connect to ZCode or DSH."""
import argparse
import json
from pathlib import Path
import sys
from budget import number


def convert(envelope):
    # These facts must come from a trusted current-session bridge, not model guesses.
    out = {k: envelope[k] for k in ('route', 'scope_verified', 'observed_at')}
    out.update(schema_version=1, billing='unknown', windows=[], evidence={'source': envelope['adapter']})
    native = envelope['native']
    adapter = envelope['adapter']
    if adapter == 'dsh-account-balance':
        # DSH's native account API exposes recharge/bonus wallets, not five-hour allowances.
        if envelope.get('current_provider') == 'deepseek-account' and native.get('status') == 'ready':
            out['billing'] = 'metered'
            out['evidence']['kind'] = 'recharge/bonus wallet; no subscription window'
    elif adapter == 'zcode-entitlement':
        # generatedAt is source time in ms; do not freshen an old export on import.
        out['observed_at'] = number(native.get('generatedAt'), 'generatedAt') / 1000
        provider = native.get('provider') or {}
        if not envelope.get('current_provider') or provider.get('id') != envelope['current_provider']:
            out['scope_verified'] = False
            return out
        subscription = native.get('subscription')
        if native.get('unavailableReason') or not subscription:
            return out
        out['billing'] = 'subscription'
        out['evidence']['provider'] = provider['id']
        # UI primary may be a tool quota. Only these two categories meter models.
        limits = (native.get('quota') or {}).get('limits', [])
        for index, w in enumerate(limits):
            if w.get('type') not in ('TOKENS_LIMIT', 'CREDIT_LIMIT'):
                if w.get('type') != 'TIME_LIMIT':
                    out['scope_verified'] = False
                continue
            # percentage is USED (0..100) for Coding Plan; Start Plan has a different schema.
            if w.get('bucketId') is not None or w.get('period') is not None:
                raise ValueError('Start Plan buckets require a normalized snapshot; do not reuse Coding Plan percentage semantics')
            used = number(w.get('percentage'), 'used percentage', maximum=100)
            if w.get('unit') == 3 and w.get('number') == 5:
                hours = 5
            elif w.get('unit') == 6:
                hours = 168
            else:
                out['scope_verified'] = False
                continue
            out['windows'].append({'id': f'model-{index}', 'remaining_percent': 100-used,
                'window_hours': hours,
                'resets_at': number(w.get('nextResetTime'), 'nextResetTime')/1000})
    else:
        raise ValueError('Unsupported native adapter')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('export', type=Path)
    a = p.parse_args()
    try:
        print(json.dumps(convert(json.loads(a.export.read_text(encoding='utf-8-sig'))), indent=2, allow_nan=False))
    except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
        print(json.dumps({'status': 'UNKNOWN', 'reason': str(exc)}))
        sys.exit(2)
