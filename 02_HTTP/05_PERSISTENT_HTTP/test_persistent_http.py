import requests
import time
from http.client import HTTPConnection
# Test URL for our requests
# You can replace this with a local server, e.g., "http://127.0.0.1:8000"
#SERVICE_URL ="https://nghttp2.org/httpbin" #NOTE: not support HTTP/1.1 keep-alive
#SERVICE_URL="https://httpbin.org"
SERVICE_URL="https://postman-echo.com"


TEST_URL = f"{SERVICE_URL}/get"
#delay=2
#TEST_URL = f"{SERVICE_URL}/delay/{delay}"



NUMBER_OF_REQUESTS = 10

def test_persistent_connection():
    """
    Simulates a persistent connection using a Session object.
    The session reuses the same TCP connection for all requests.
    """
    print("--- Starting Persistent Connection Test (with Session) ---")
    start_time = time.time()
    HTTPConnection._http_vsn_str = 'HTTP/1.1'
    HTTPConnection.conn = 'HTTP/1.1'

    with requests.Session() as session:
        for i in range(NUMBER_OF_REQUESTS):
            try:                
                start_time_tmp = time.time()
                response = session.get(TEST_URL)
                stop_time_tmp = time.time()
                print(f"Request {i+1}: Status Code {response.status_code} partial time: {stop_time_tmp-start_time_tmp}")
            except requests.exceptions.RequestException as e:
                print(f"Request {i+1} failed: {e}")
    end_time = time.time()
    print(f"Persistent Connection Duration: {end_time - start_time:.4f} seconds\n")

def test_standard_non_persistent_connection():
    """
    Simulates a non-persistent connection using standard requests.get().
    Each call tends to handle its connection independently, which is less
    efficient than a Session for multiple requests.
    """
    print("--- Starting Standard Non-Persistent Test ---")
    start_time = time.time()
    for i in range(NUMBER_OF_REQUESTS):
        try:
            start_time_tmp = time.time()
            HTTPConnection._http_vsn_str = 'HTTP/1.0'
            response = requests.get(TEST_URL)
            stop_time_tmp = time.time()
            print(f"Request {i+1}: Status Code {response.status_code} partial time: {stop_time_tmp-start_time_tmp}")
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1} failed: {e}")
    end_time = time.time()
    print(f"Standard Non-Persistent Duration: {end_time - start_time:.4f} seconds\n")


if __name__ == "__main__":
    test_standard_non_persistent_connection()
    test_persistent_connection()
    