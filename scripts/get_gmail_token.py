#!/usr/bin/env python3
"""One-time Gmail OAuth consent flow to obtain a refresh token.

Usage:
    python scripts/get_gmail_token.py --client-id <ID> --client-secret <SECRET>

Prints a URL, open it in a browser, log in as the Gmail sender account,
approve the (unverified) app, and paste back the code shown by Google.
The refresh token is printed at the end — put it in backend/.env.live as
GMAIL_REFRESH_TOKEN.
"""
import argparse
import urllib.parse
import urllib.request

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
REDIRECT = 'urn:ietf:wg:oauth:2.0:oob'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-id', required=True)
    parser.add_argument('--client-secret', required=True)
    args = parser.parse_args()

    params = urllib.parse.urlencode({
        'client_id': args.client_id,
        'redirect_uri': REDIRECT,
        'response_type': 'code',
        'scope': SCOPES,
        'access_type': 'offline',
        'prompt': 'consent',
    })
    print('1. Open this URL in your browser (log in as the sending Gmail account):')
    print()
    print('   ' + f'{AUTH_URL}?{params}')
    print()
    print('2. Click "Continue" through the warnings (unverified app).')
    print('3. Google shows a one-time code — copy and paste it below.')
    code = input('   Code: ').strip()

    data = urllib.parse.urlencode({
        'client_id': args.client_id,
        'client_secret': args.client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data)
    with urllib.request.urlopen(req, timeout=20) as resp:
        token = __import__('json').loads(resp.read())

    if 'refresh_token' not in token:
        print('\nERROR: no refresh_token returned:', token)
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
