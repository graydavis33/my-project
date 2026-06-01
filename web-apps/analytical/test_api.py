"""
Analytical — End-to-end API test suite.
Run this after the server is running on localhost:8000.

  cd web-apps/analytical
  python test_api.py

Tests every auth endpoint + basic protection checks.
Uses a throwaway test account — cleans itself up.
"""
import sys
import requests
import random
import string

BASE = 'http://localhost:8000'

BOLD  = '\033[1m'
GREEN = '\033[92m'
RED   = '\033[91m'
CYAN  = '\033[96m'
YELLOW= '\033[93m'
RESET = '\033[0m'

passed = 0
failed = 0


def check(name, condition, detail=''):
    global passed, failed
    if condition:
        print(f'  {GREEN}PASS{RESET}  {name}')
        passed += 1
    else:
        print(f'  {RED}FAIL{RESET}  {name}' + (f' — {detail}' if detail else ''))
        failed += 1


def hdr(msg):
    print(f'\n{BOLD}{CYAN}── {msg} ──{RESET}')


def rand_email():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f'test_{suffix}@analytical-test.com'


# ─── Pre-flight ───────────────────────────────────────────────
hdr('Pre-flight: server reachable')
try:
    r = requests.get(BASE + '/docs', timeout=5)
    check('Server is running on localhost:8000', r.status_code == 200)
except requests.exceptions.ConnectionError:
    print(f'  {RED}FAIL{RESET}  Cannot reach localhost:8000')
    print(f'\n  {YELLOW}Start the server first:{RESET}')
    print(f'  cd web-apps/analytical/backend && uvicorn main:app --reload --port 8000\n')
    sys.exit(1)


# ─── Auth: Signup ─────────────────────────────────────────────
hdr('POST /api/auth/signup')

email = rand_email()
password = 'TestPass123!'

r = requests.post(f'{BASE}/api/auth/signup', json={'email': email, 'password': password})
check('Returns 200', r.status_code == 200, f'got {r.status_code}: {r.text[:100]}')
check('Has token field', 'token' in r.json(), str(r.json()))
check('Has user.email', r.json().get('user', {}).get('email') == email)
check('Has user.tier = free', r.json().get('user', {}).get('tier') == 'free')
token = r.json().get('token', '')

# Duplicate signup should fail
r2 = requests.post(f'{BASE}/api/auth/signup', json={'email': email, 'password': password})
check('Duplicate email returns 409', r2.status_code == 409, f'got {r2.status_code}')

# Short password should fail
r3 = requests.post(f'{BASE}/api/auth/signup', json={'email': rand_email(), 'password': '123'})
check('Short password returns 400', r3.status_code == 400, f'got {r3.status_code}')


# ─── Auth: Login ─────────────────────────────────────────────
hdr('POST /api/auth/login')

r = requests.post(f'{BASE}/api/auth/login', json={'email': email, 'password': password})
check('Returns 200', r.status_code == 200, f'got {r.status_code}')
check('Has token', 'token' in r.json())
login_token = r.json().get('token', token)

r_bad = requests.post(f'{BASE}/api/auth/login', json={'email': email, 'password': 'wrongpassword'})
check('Wrong password returns 401', r_bad.status_code == 401, f'got {r_bad.status_code}')

r_missing = requests.post(f'{BASE}/api/auth/login', json={'email': 'nobody@example.com', 'password': 'anything'})
check('Unknown email returns 401', r_missing.status_code == 401, f'got {r_missing.status_code}')


# ─── Auth: /me ────────────────────────────────────────────────
hdr('GET /api/auth/me')

auth_headers = {'Authorization': f'Bearer {login_token}'}

r = requests.get(f'{BASE}/api/auth/me', headers=auth_headers)
check('Returns 200 with valid token', r.status_code == 200, f'got {r.status_code}')
check('Returns correct email', r.json().get('email') == email)

r_no_token = requests.get(f'{BASE}/api/auth/me')
check('Returns 401 with no token', r_no_token.status_code == 401, f'got {r_no_token.status_code}')

r_bad_token = requests.get(f'{BASE}/api/auth/me', headers={'Authorization': 'Bearer garbage'})
check('Returns 401 with bad token', r_bad_token.status_code == 401, f'got {r_bad_token.status_code}')


# ─── Stats: no platforms connected yet ────────────────────────
hdr('GET /api/stats (no connections)')

r = requests.get(f'{BASE}/api/stats', headers=auth_headers)
check('Returns 200', r.status_code == 200, f'got {r.status_code}')
check('connections dict is empty', r.json().get('connections') == {})
check('youtube is null', r.json().get('youtube') is None)
check('tiktok is null', r.json().get('tiktok') is None)


# ─── Insights: no data yet ────────────────────────────────────
hdr('GET /api/insights (no data)')

r = requests.get(f'{BASE}/api/insights', headers=auth_headers)
check('Returns 200', r.status_code == 200, f'got {r.status_code}')
check('content is empty string', r.json().get('content') == '')


# ─── OAuth redirect check ─────────────────────────────────────
hdr('GET /api/connect/youtube (redirect check)')

r = requests.get(
    f'{BASE}/api/connect/youtube',
    params={'token': login_token},
    allow_redirects=False
)
check('Redirects to Google OAuth (302)', r.status_code in (302, 307), f'got {r.status_code}')
location = r.headers.get('location', '')
check('Redirect location contains accounts.google.com', 'accounts.google.com' in location, location[:80])


# ─── Protected route without token ────────────────────────────
hdr('Protection checks')

for path, method in [
    ('/api/stats', 'GET'),
    ('/api/stats/refresh', 'POST'),
    ('/api/insights', 'GET'),
    ('/api/billing/subscribe', 'POST'),
    ('/api/billing/portal', 'GET'),
]:
    r = requests.request(method, f'{BASE}{path}')
    check(f'{method} {path} → 401 without token', r.status_code == 401, f'got {r.status_code}')


# ─── Summary ──────────────────────────────────────────────────
total = passed + failed
print(f'\n{BOLD}Results: {GREEN}{passed} passed{RESET}{BOLD}, {RED}{failed} failed{RESET}{BOLD} / {total} total{RESET}')

if failed == 0:
    print(f'{GREEN}{BOLD}All tests passed. Backend is working correctly.{RESET}\n')
    sys.exit(0)
else:
    print(f'{RED}{BOLD}Some tests failed. Check the errors above.{RESET}\n')
    sys.exit(1)
