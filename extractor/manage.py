"""Local container commands; authentication stays inside the environment."""
import argparse
import json
import os
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['login', 'status'])
    args = parser.parse_args()
    login = args.command == 'login'
    request = urllib.request.Request(
        'http://127.0.0.1:8787' + ('/v1/login' if login else '/v1/status'),
        data=json.dumps({'provider': 'disney'}).encode() if login else None,
        headers={'X-Bridge-Key': os.environ['BRIDGE_API_TOKEN'],
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            print(json.dumps(json.load(response), ensure_ascii=False))
    except Exception:
        raise SystemExit('Agent unavailable, unauthorized, or browser busy') from None


if __name__ == '__main__':
    main()
