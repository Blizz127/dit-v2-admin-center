"""Inspect a supplied synthetic log bundle without changing logs or delivery state."""
import argparse
import json
from pathlib import Path

from delivery_correlation import from_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-offline', action='store_true')
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--simulate-native-receipts', action='store_true',
                        help='accept fabricated receipt authority for synthetic cases only; never proves game delivery')
    args = parser.parse_args()
    if args.simulate_native_receipts and not args.enable_offline:
        parser.error('--simulate-native-receipts requires --enable-offline')
    if args.enable_offline and args.capture is None:
        parser.error('--enable-offline requires --capture')
    verifier = (lambda _: True) if args.simulate_native_receipts else None
    report = from_file(args.capture, enabled=args.enable_offline, native_verifier=verifier)
    print(json.dumps(report, sort_keys=True))
    return 2 if report['status'] == 'Unavailable' else 0


if __name__ == '__main__':
    raise SystemExit(main())
