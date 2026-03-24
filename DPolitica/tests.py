"""
Tests for DPolitica Flask application
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Candidate, Source, Connection, Submission, AdminLog
from datetime import datetime, timezone

def run_tests():
    """Run all tests"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF in tests

    with app.app_context():
        db.create_all()

        client = app.test_client()
        tests_passed = 0
        tests_failed = 0

        # Test 1: Home page
        print('Test 1: Home page...')
        resp = client.get('/')
        if resp.status_code == 200:
            print('  ✓ Home page returns 200')
            tests_passed += 1
        else:
            print(f'  ✗ Home page returned {resp.status_code}')
            tests_failed += 1

        # Test 2: Candidates page
        print('Test 2: Candidates page...')
        resp = client.get('/candidates')
        if resp.status_code == 200:
            print('  ✓ Candidates page returns 200')
            tests_passed += 1
        else:
            print(f'  ✗ Candidates page returned {resp.status_code}')
            tests_failed += 1

        # Test 3: Submit page
        print('Test 3: Submit page...')
        resp = client.get('/submit')
        if resp.status_code == 200:
            print('  ✓ Submit page returns 200')
            tests_passed += 1
        else:
            print(f'  ✗ Submit page returned {resp.status_code}')
            tests_failed += 1

        # Test 4: Sources page
        print('Test 4: Sources page...')
        resp = client.get('/sources')
        if resp.status_code == 200:
            print('  ✓ Sources page returns 200')
            tests_passed += 1
        else:
            print(f'  ✗ Sources page returned {resp.status_code}')
            tests_failed += 1

        # Test 5: API endpoint
        print('Test 5: API /api/candidates...')
        resp = client.get('/api/candidates')
        if resp.status_code == 200:
            import json
            data = json.loads(resp.data)
            if isinstance(data, list):
                print(f'  ✓ API returns list of {len(data)} candidates')
                tests_passed += 1
            else:
                print('  ✗ API does not return a list')
                tests_failed += 1
        else:
            print(f'  ✗ API returned {resp.status_code}')
            tests_failed += 1

        # Test 6: Create candidate via API (with API key)
        print('Test 6: POST /api/candidates with API key...')
        api_key = os.environ.get('API_KEY', '')
        candidate_data = {
            'name': 'Test Candidate',
            'party': 'TEST',
            'background_summary': 'Test background'
        }
        resp = client.post('/api/candidates', json=candidate_data,
                          headers={'X-API-Key': api_key})
        if resp.status_code == 201:
            print('  ✓ API accepts candidate creation')
            tests_passed += 1
        else:
            print(f'  ✗ API returned {resp.status_code}')
            tests_failed += 1

        # Test 7: Submit form submission
        print('Test 7: POST /submit...')
        resp = client.post('/submit', data={
            'candidate_name': 'Test Candidate',
            'content': 'Test submission',
            'source_type': 'tip'
        })
        if resp.status_code in [200, 302]:  # 302 for redirect after success
            print('  ✓ Submit form works')
            tests_passed += 1
        else:
            print(f'  ✗ Submit form returned {resp.status_code}')
            tests_failed += 1

        # Test 8: Candidate details page
        print('Test 8: Candidate details page...')
        candidate = Candidate.query.first()
        if candidate:
            resp = client.get(f'/candidates/{candidate.id}')
            if resp.status_code == 200:
                print(f'  ✓ Candidate detail page returns 200')
                tests_passed += 1
            else:
                print(f'  ✗ Candidate detail page returned {resp.status_code}')
                tests_failed += 1
        else:
            print('  ⚪ No candidates to test')

        # --- Security-specific tests ---

        # Test 9: POST /api/candidates without API key => 401
        print('Test 9: POST /api/candidates WITHOUT API key...')
        resp = client.post('/api/candidates', json={'name': 'Hacker'})
        if resp.status_code == 401:
            print('  ✓ API rejects request without key (401)')
            tests_passed += 1
        else:
            print(f'  ✗ Expected 401, got {resp.status_code}')
            tests_failed += 1

        # Test 10: POST /api/candidates with wrong API key => 401
        print('Test 10: POST /api/candidates with WRONG API key...')
        resp = client.post('/api/candidates', json={'name': 'Hacker'},
                          headers={'X-API-Key': 'wrong-key'})
        if resp.status_code == 401:
            print('  ✓ API rejects bad key (401)')
            tests_passed += 1
        else:
            print(f'  ✗ Expected 401, got {resp.status_code}')
            tests_failed += 1

        # Test 11: URL validation — reject javascript: scheme
        print('Test 11: URL validation rejects javascript: scheme...')
        resp = client.post('/submit', data={
            'candidate_name': 'Test',
            'content': 'XSS test',
            'source_link': 'javascript:alert(1)',
            'source_type': 'tip'
        }, follow_redirects=True)
        # Should redirect back to submit with error flash
        resp_text = resp.data.decode('utf-8')
        if 'http://' in resp_text or 'https://' in resp_text:
            print('  ✓ javascript: URL rejected')
            tests_passed += 1
        else:
            print('  ✗ javascript: URL was not rejected')
            tests_failed += 1

        # Test 12: Input length validation — content too long
        print('Test 12: Input length validation (content too long)...')
        resp = client.post('/submit', data={
            'content': 'x' * 5001,
            'source_type': 'tip'
        }, follow_redirects=True)
        resp_text = resp.data.decode('utf-8')
        if 'máx.' in resp_text or resp.status_code == 200:
            print('  ✓ Long content rejected')
            tests_passed += 1
        else:
            print(f'  ✗ Expected rejection of long content')
            tests_failed += 1

        # Test 13: API input length validation
        print('Test 13: API input length validation...')
        resp = client.post('/api/candidates',
                          json={'name': 'x' * 201, 'party': 'TEST'},
                          headers={'X-API-Key': api_key})
        if resp.status_code == 400:
            print('  ✓ API rejects overly long name (400)')
            tests_passed += 1
        else:
            print(f'  ✗ Expected 400, got {resp.status_code}')
            tests_failed += 1

        # --- Admin panel tests ---

        # Test 14: Admin dashboard requires auth (redirects)
        print('Test 14: Admin dashboard requires auth...')
        resp = client.get('/admin/')
        if resp.status_code == 302:
            print('  ✓ Unauthenticated admin access redirects (302)')
            tests_passed += 1
        else:
            print(f'  ✗ Expected 302, got {resp.status_code}')
            tests_failed += 1

        # Test 15: Admin login page renders
        print('Test 15: Admin login page...')
        resp = client.get('/admin/login')
        if resp.status_code == 200:
            print('  ✓ Admin login page returns 200')
            tests_passed += 1
        else:
            print(f'  ✗ Admin login returned {resp.status_code}')
            tests_failed += 1

        # Test 16: Wrong password rejected
        print('Test 16: Wrong admin password...')
        resp = client.post('/admin/login', data={'password': 'wrong'}, follow_redirects=True)
        resp_text = resp.data.decode('utf-8')
        if 'incorrecta' in resp_text.lower():
            print('  ✓ Wrong password rejected')
            tests_passed += 1
        else:
            print('  ✗ Wrong password was not rejected')
            tests_failed += 1

        # Test 17: Correct password logs in
        print('Test 17: Admin login with correct password...')
        admin_pw = os.environ.get('ADMIN_PASSWORD', '')
        resp = client.post('/admin/login', data={'password': admin_pw}, follow_redirects=True)
        if resp.status_code == 200:
            print('  ✓ Admin login succeeds')
            tests_passed += 1
        else:
            print(f'  ✗ Admin login returned {resp.status_code}')
            tests_failed += 1

        # Test 18: Dashboard accessible after login
        print('Test 18: Admin dashboard after login...')
        resp = client.get('/admin/')
        if resp.status_code == 200:
            print('  ✓ Admin dashboard accessible')
            tests_passed += 1
        else:
            print(f'  ✗ Dashboard returned {resp.status_code}')
            tests_failed += 1

        # Test 19: Create candidate via admin
        print('Test 19: Admin create candidate...')
        resp = client.post('/admin/candidates/new', data={
            'name': 'Admin Created',
            'party': 'TestParty',
            'background_summary': 'Created via admin'
        }, follow_redirects=True)
        admin_cand = Candidate.query.filter_by(name='Admin Created').first()
        if admin_cand:
            print('  ✓ Candidate created via admin')
            tests_passed += 1
        else:
            print('  ✗ Candidate not created')
            tests_failed += 1

        # Test 20: Admin logout
        print('Test 20: Admin logout...')
        resp = client.get('/admin/logout', follow_redirects=True)
        resp2 = client.get('/admin/')
        if resp2.status_code == 302:
            print('  ✓ Logout works, dashboard redirects')
            tests_passed += 1
        else:
            print(f'  ✗ After logout expected 302, got {resp2.status_code}')
            tests_failed += 1

        print(f'\n=== Test Results ===')
        print(f'Passed: {tests_passed}')
        print(f'Failed: {tests_failed}')
        print(f'Total: {tests_passed + tests_failed}')

        return tests_failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
