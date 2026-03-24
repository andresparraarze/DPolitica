"""
Tests for DPolitica Flask application
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Candidate, Source, Connection, Submission
from datetime import datetime, timezone

def run_tests():
    """Run all tests"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

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

        # Test 6: Create candidate via API
        print('Test 6: POST /api/candidates...')
        candidate_data = {
            'name': 'Test Candidate',
            'party': 'TEST',
            'background_summary': 'Test background'
        }
        resp = client.post('/api/candidates', json=candidate_data)
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

        print(f'\n=== Test Results ===')
        print(f'Passed: {tests_passed}')
        print(f'Failed: {tests_failed}')
        print(f'Total: {tests_passed + tests_failed}')

        return tests_failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
