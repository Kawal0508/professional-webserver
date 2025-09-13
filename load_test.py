#!/usr/bin/env python3
"""
Load testing script for the Professional Web Server.
"""

import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json

class LoadTester:
    def __init__(self, base_url, num_threads=10, requests_per_thread=100):
        self.base_url = base_url.rstrip('/')
        self.num_threads = num_threads
        self.requests_per_thread = requests_per_thread
        self.results = []
        self.lock = threading.Lock()
    
    def make_request(self, endpoint="/"):
        """Make a single HTTP request and return timing data."""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': True,
                'content_length': len(response.content)
            }
        except Exception as e:
            end_time = time.time()
            return {
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e)
            }
    
    def worker_thread(self, thread_id):
        """Worker thread that makes multiple requests."""
        thread_results = []
        
        for i in range(self.requests_per_thread):
            result = self.make_request()
            result['thread_id'] = thread_id
            result['request_id'] = i
            thread_results.append(result)
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.01)
        
        with self.lock:
            self.results.extend(thread_results)
    
    def run_test(self):
        """Run the load test."""
        print(f"Starting load test...")
        print(f"URL: {self.base_url}")
        print(f"Threads: {self.num_threads}")
        print(f"Requests per thread: {self.requests_per_thread}")
        print(f"Total requests: {self.num_threads * self.requests_per_thread}")
        print("-" * 50)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self.worker_thread, i) for i in range(self.num_threads)]
            
            # Wait for all threads to complete
            for future in as_completed(futures):
                future.result()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.analyze_results(total_time)
    
    def analyze_results(self, total_time):
        """Analyze and display test results."""
        if not self.results:
            print("No results to analyze!")
            return
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        print(f"\n📊 LOAD TEST RESULTS")
        print("=" * 50)
        print(f"Total requests: {len(self.results)}")
        print(f"Successful requests: {len(successful_requests)}")
        print(f"Failed requests: {len(failed_requests)}")
        print(f"Success rate: {len(successful_requests)/len(self.results)*100:.2f}%")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Requests per second: {len(self.results)/total_time:.2f}")
        
        if response_times:
            print(f"\n⏱️  RESPONSE TIME STATISTICS")
            print("-" * 30)
            print(f"Average: {statistics.mean(response_times)*1000:.2f} ms")
            print(f"Median: {statistics.median(response_times)*1000:.2f} ms")
            print(f"Min: {min(response_times)*1000:.2f} ms")
            print(f"Max: {max(response_times)*1000:.2f} ms")
            print(f"95th percentile: {sorted(response_times)[int(len(response_times)*0.95)]*1000:.2f} ms")
            print(f"99th percentile: {sorted(response_times)[int(len(response_times)*0.99)]*1000:.2f} ms")
        
        # Status code distribution
        status_codes = {}
        for result in self.results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        print(f"\n📈 STATUS CODE DISTRIBUTION")
        print("-" * 30)
        for code, count in sorted(status_codes.items()):
            percentage = count / len(self.results) * 100
            print(f"{code}: {count} ({percentage:.1f}%)")
        
        # Error analysis
        if failed_requests:
            print(f"\n❌ ERROR ANALYSIS")
            print("-" * 20)
            error_types = {}
            for result in failed_requests:
                error = result.get('error', 'Unknown error')
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                print(f"{error}: {count}")
        
        # Performance rating
        avg_response_time = statistics.mean(response_times) if response_times else 0
        rps = len(self.results) / total_time
        
        print(f"\n🎯 PERFORMANCE RATING")
        print("-" * 20)
        if avg_response_time < 0.1 and rps > 100:
            print("🟢 EXCELLENT - Production ready!")
        elif avg_response_time < 0.5 and rps > 50:
            print("🟡 GOOD - Suitable for moderate load")
        else:
            print("🔴 NEEDS IMPROVEMENT - Consider optimization")

def test_health_endpoint(base_url):
    """Test the health endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_metrics_endpoint(base_url):
    """Test the metrics endpoint."""
    print("📊 Testing metrics endpoint...")
    try:
        response = requests.get(f"{base_url}/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics endpoint working: {len(data)} metrics")
            return True
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Load test the Professional Web Server")
    parser.add_argument("url", help="Base URL of the server (e.g., http://localhost:8080)")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads (default: 10)")
    parser.add_argument("-r", "--requests", type=int, default=100, help="Requests per thread (default: 100)")
    parser.add_argument("--health", action="store_true", help="Test health endpoint only")
    parser.add_argument("--metrics", action="store_true", help="Test metrics endpoint only")
    
    args = parser.parse_args()
    
    print("🚀 Professional Web Server Load Tester")
    print("=" * 40)
    
    # Test endpoints first
    if args.health:
        test_health_endpoint(args.url)
        return
    
    if args.metrics:
        test_metrics_endpoint(args.url)
        return
    
    # Test both endpoints
    health_ok = test_health_endpoint(args.url)
    metrics_ok = test_metrics_endpoint(args.url)
    
    if not health_ok or not metrics_ok:
        print("⚠️  Some endpoints are not working properly. Continuing with load test...")
    
    print()
    
    # Run load test
    tester = LoadTester(args.url, args.threads, args.requests)
    tester.run_test()

if __name__ == "__main__":
    main()
