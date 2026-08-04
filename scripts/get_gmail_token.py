#!/usr/bin/env python3
"""One-time Gmail OAuth consent flow to obtain a refresh token.

Uses the loopback redirect flow (required since Google removed OOB).
Run it, open the printed URL in a browser, approve, and the local server
captures the callback and exchanges the code for a refresh token.

Usage:
    python scripts/get_gmail_token.py --client-id <ID> --client-secret <SECRET>
"""
import argparse
import json
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
PORT = 8888
REDIRECT = f'http://localhost:{PORT}/'

_token = {'code': None}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if 'code' in qs:
            _token['code'] = qs['code'][0]
            body = b'You can close this tab now.'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b'No code in callback. Close this tab.'
            self.send_response(400)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-id', required=True)
    parser.add_argument('--client-secret', required=True)
    args = parser.parse_args()

    server = HTTPServer(('127.0.0.1', PORT), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    params = urllib.parse.urlencode({
        'client_id': args.client_id,
        'redirect_uri': REDIRECT,
        'response_type': 'code',
        'scope': SCOPES,
        'access_type': 'offline',
        'prompt': 'consent',
    })
    url = f'{AUTH_URL}?{params}'
    print('Open this URL in your browser (log in as the sending Gmail account):')
    print()
    print('   ' + url)
    print()
    print('Click "Continue" through the unverified-app warnings, then Approve.')
    print('Waiting for the callback on http://localhost:%d/ ...' % PORT)

    deadline = 180
    step = 0
    while _token['code'] is None and step < deadline:
        import time
        time.sleep(1)
        step += 1
    server.server_close()

    code = _token['code']
    if code is None:
        print('\nERROR: timed out waiting for the browser callback.')
        return 1

    data = urllib.parse.urlencode({
        'client_id': args.client_id,
        'client_secret': args.client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data)
    with urllib.request.urlopen(req, timeout=20) as resp:
        token = json.loads(resp.read())

    if 'refresh_token' not in token:
        print('\nERROR: no refresh_token returned:', json.dumps(token)[:300])
        return 1

    print()
    print('Success! Refresh token (never expires):')
    print()
    print(token['refresh_token'])
    print()
    print('Add it to backend/.env.live as:  GMAIL_REFRESH_TOKEN=<above>')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
