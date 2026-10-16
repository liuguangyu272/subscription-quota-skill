"""Provider-neutral subscription pacing. Python 3.11+, standard library only."""
import argparse
import json
import math
import sys
import time
from pathlib import Path

LEVELS = ['TIGHT', 'CONSERVATIVE', 'COMFORTABLE', 'ABUNDANT']


def number(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f'{name} is out of range')
    return value


def evaluate(snapshot, route, now=None, max_age=300):
    now = time.time() if now is None else number(now, 'now')
    result = {'status': 'UNKNOWN', 'level': None, 'windows': [], 'reasons': []}
    def fail(reason):
        result['reasons'].append(reason)
        return result
    if snapshot.get('schema_version') != 1:
        return fail('Unsupported snapshot schema.')
    if not route or snapshot.get('route') != route or snapshot.get('scope_verified') is not True:
        return fail('Current session route/account scope has not been verified.')
    observed = number(snapshot.get('observed_at'), 'observed_at')
    if not -30 <= now - observed <= max_age:
        return fail('Snapshot is stale or its clock is in the future; refresh once.')
    billing = snapshot.get('billing')
    result['billing'] = billing
    if not snapshot.get('evidence'):
        return fail('Billing evidence is missing.')
    if billing == 'metered':
        result['status'] = 'NOT_APPLICABLE'
        return fail('Metered/wallet billing: no subscription reset pacing applied.')
    if billing != 'subscription':
        return fail('A subscription for the current route is not established.')
    windows = snapshot.get('windows')
    if not isinstance(windows, list) or not windows:
        return fail('No finite quota windows are available; do not invent a five-hour window.')
    ids = set()
    ranks = []
    for w in windows:
        identifier = w.get('id')
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError('Window IDs must be nonempty and unique')
        ids.add(identifier)
        remaining = number(w.get('remaining_percent'), 'remaining_percent', maximum=100)
        duration = number(w.get('window_hours'), 'window_hours', minimum=0.000001)
        reset = number(w.get('resets_at'), 'resets_at')
        hours = (reset - now) / 3600
        if hours <= 0:
            return fail('A reset is due; refresh instead of assuming replenishment.')
        if hours > duration + 1/60:
            return fail('Reset lies beyond the declared window; check units and cycle semantics.')
        reference = number(w.get('reference_pph', 100 / duration), 'reference_pph', minimum=0.000001)
        rate = remaining / hours
        ratio = rate / reference
        rank = 0 if ratio < .5 else 1 if ratio < 1 else 2 if ratio < 1.5 else 3
        warnings = []
        # A large ratio close to reset never creates more absolute quota.
        if remaining < 10:
            rank = min(rank, 1)
            warnings.append('Less than 10% remains; use small bounded stages.')
        if hours < .25:
            warnings.append('Reset is close; the rate is inflated by a small denominator.')
        if remaining == 0:
            rank = 0
            warnings.append('This window is exhausted; no presumed reset or credit purchase.')
        ranks.append(rank)
        result['windows'].append({'id': identifier, 'remaining_percent': remaining,
            'remaining_hours': hours, 'resets_at': reset, 'window_hours': duration,
            'budget_pph': rate, 'reference_pph': reference, 'ratio': ratio,
            'level': LEVELS[rank], 'warnings': warnings})
    result['status'] = 'EXHAUSTED' if any(w['remaining_percent'] == 0 for w in windows) else 'READY'
    result['level'] = LEVELS[min(ranks)]
    result['limiting_windows'] = [w['id'] for w in result['windows'] if w['level'] == result['level']]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--route', required=True, help='Current harness/provider/account scope, verified by caller')
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.snapshot.read_text(encoding='utf-8-sig')), args.route)
    except (ValueError, TypeError, AttributeError, KeyError, OSError) as exc:
        result = {'status': 'UNKNOWN', 'level': None, 'reasons': [str(exc)]}
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0 if result['status'] in ('READY', 'NOT_APPLICABLE', 'EXHAUSTED') else 2


if __name__ == '__main__':
    sys.exit(main())
