import requests
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

BASE_URL = "http://127.0.0.1:8000/api"


def setup_module(module):
    # Ensure DB has an employee and a file for testing
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    # Ensure aswin exists
    if not db.users.find_one({'username':'aswin'}):
        db.users.insert_one({'email':'aswin@example.com','username':'aswin','password_hash':'$2b$12$dummy','role':'employee','created_at':datetime.now(timezone.utc).isoformat(),'is_active':True})
    # Ensure admin uploaded files exist
    file_meta = db.file_metadata.find_one({'uploaded_by':'admin'})
    if not file_meta:
        # Insert a dummy file entry
        db.file_metadata.insert_one({'file_id':'testfile123', 'filename':'test.txt', 'uploaded_by':'admin', 'uploaded_at':datetime.now(timezone.utc).isoformat(), 'encrypted':True, 'size':10, 'encryption_key':'dummykey'})


def test_wfh_bypass_download():
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    # set OTP for aswin and create approved WFH
    now = datetime.now(timezone.utc)
    db.users.update_one({'username':'aswin'}, {'$set': {'otp': '222222', 'otp_expiry': (now+timedelta(minutes=10)).isoformat(), 'otp_sent_at':now.isoformat()}}, upsert=True)
    # create an active WFH approved
    start = (now - timedelta(minutes=5)).isoformat()
    end = (now + timedelta(minutes=60)).isoformat()
    db.wfh_requests.update_one({'employee_username':'aswin'}, {'$set': {'status':'approved', 'access_start':start, 'access_end':end, 'approved_at': now.isoformat()}}, upsert=True)

    # Verify OTP and get token
    r = requests.post(f"{BASE_URL}/auth/verify-otp", json={'username':'aswin', 'otp':'222222'})
    assert r.status_code == 200
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # Call GET /files without geo/wifi - should be allowed due to WFH
    r = requests.get(f"{BASE_URL}/files", headers=headers)
    assert r.status_code == 200
    files = r.json()
    assert any(f['accessible'] and f['access_reason'].startswith('WFH approved') for f in files)

    # Attempt to access a file without geo/wifi
    file_id = files[0]['file_id']
    r = requests.post(f"{BASE_URL}/files/access", headers=headers, json={'file_id': file_id})
    assert r.status_code == 200


def test_no_wfh_blocks_access_without_location():
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    # Ensure WFH not approved
    db.wfh_requests.update_many({'employee_username':'aswin'},{'$set':{'status':'rejected'}})
    # Set OTP again and verify
    now = datetime.now(timezone.utc)
    db.users.update_one({'username':'aswin'}, {'$set': {'otp': '333333', 'otp_expiry': (now+timedelta(minutes=10)).isoformat(), 'otp_sent_at':now.isoformat()}}, upsert=True)
    r = requests.post(f"{BASE_URL}/auth/verify-otp", json={'username':'aswin', 'otp':'333333'})
    assert r.status_code == 200
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # Call GET /files without geo/wifi - should be blocked (accessible False)
    r = requests.get(f"{BASE_URL}/files", headers=headers)
    assert r.status_code == 200
    files = r.json()
    assert all(not f['accessible'] for f in files)

    # Attempt to access a file without geo/wifi - should be 403
    file_id = files[0]['file_id']
    r = requests.post(f"{BASE_URL}/files/access", headers=headers, json={'file_id': file_id})
    assert r.status_code == 403


def test_admin_approval_normalizes_tz_and_sets_access_window():
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    # Set OTP for admin and verify
    now = datetime.now(timezone.utc)
    db.users.update_one({'username':'admin'}, {'$set': {'otp': '444444', 'otp_expiry': (now+timedelta(minutes=10)).isoformat(), 'otp_sent_at':now.isoformat()}}, upsert=True)
    r = requests.post(f"{BASE_URL}/auth/verify-otp", json={'username':'admin', 'otp':'444444'})
    assert r.status_code == 200
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # Create a pending WFH request for aswin first
    # Ensure aswin has a valid OTP and login to get token
    now = datetime.now(timezone.utc)
    db.users.update_one({'username':'aswin'}, {'$set': {'otp': '555555', 'otp_expiry': (now+timedelta(minutes=10)).isoformat(), 'otp_sent_at':now.isoformat()}}, upsert=True)
    r = requests.post(f"{BASE_URL}/auth/verify-otp", json={'username':'aswin', 'otp':'555555'})
    assert r.status_code == 200
    emp_token = r.json().get('access_token')
    emp_headers = {'Authorization': f'Bearer {emp_token}'}
    r = requests.post(f"{BASE_URL}/wfh-request", headers=emp_headers, json={'reason':'Testing approval'})
    assert r.status_code == 200

    # Approve aswin's WFH with a timezone-specified start/end
    start = (now - timedelta(minutes=5)).astimezone().isoformat()
    end = (now + timedelta(minutes=30)).astimezone().isoformat()
    r = requests.put(f"{BASE_URL}/admin/wfh-requests/aswin", headers=headers, json={'status':'approved','access_start':start,'access_end':end})
    assert r.status_code == 200

    # Verify stored values are timezone normalized in DB
    req = db.wfh_requests.find_one({'employee_username':'aswin','status':'approved'})
    assert req is not None
    assert 'access_start' in req and 'access_end' in req
    # They should be stored with timezone info - i.e., include '+' or 'Z'
    assert '+' in req['access_start'] or 'Z' in req['access_start']
    assert '+' in req['access_end'] or 'Z' in req['access_end']
