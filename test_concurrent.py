import requests
import threading
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

API_URL = "http://localhost:8000/chat"

# Configure retry strategy
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

questions = [
    "Ada mainan Molly?",
    "Berapa harga LABUBU?",
    "Cara membeli gimana?",
]

results = []
results_lock = threading.Lock()

def send_request(user_id, question):
    """Send request dengan retry"""
    start = time.time()
    try:
        response = session.post(
            API_URL, 
            json={
                "question": question,
                "user_id": f"user_{user_id}"
            }, 
            timeout=60  # 60 seconds timeout
        )
        
        elapsed = time.time() - start
        
        with results_lock:
            if response.status_code == 200:
                results.append({
                    'user_id': user_id,
                    'status': 'success',
                    'time': elapsed
                })
                print(f"✓ User {user_id}: {elapsed:.2f}s - {question[:30]}...")
            else:
                results.append({
                    'user_id': user_id,
                    'status': 'error',
                    'code': response.status_code
                })
                print(f"✗ User {user_id}: ERROR {response.status_code}")
            
    except Exception as e:
        elapsed = time.time() - start
        with results_lock:
            results.append({
                'user_id': user_id,
                'status': 'exception',
                'error': str(e),
                'time': elapsed
            })
        print(f"✗ User {user_id}: EXCEPTION - {str(e)[:80]}")

# Test dengan 5 users dulu (bukan 10)
print("Testing with 5 concurrent users...")
threads = []
for i in range(3):
    question = questions[i % len(questions)]
    t = threading.Thread(target=send_request, args=(i+1, question))
    threads.append(t)
    t.start()

# Wait for all
for t in threads:
    t.join()

# Print summary
print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
success = len([r for r in results if r['status'] == 'success'])
failed = len([r for r in results if r['status'] != 'success'])
print(f"Success: {success}/5 ({success/5*100:.0f}%)")
print(f"Failed:  {failed}/5")

if success > 0:
    avg_time = sum(r['time'] for r in results if r['status'] == 'success') / success
    print(f"Avg Response Time: {avg_time:.2f}s")