import socket
import ssl
from urllib.parse import urlparse
import os
import re
import logging

# --- Logging Configuration ---
# Set the logging level. Use logging.INFO for standard output,
# or logging.DEBUG to see all verbose messages.
LOG_LEVEL = logging.INFO

# Configure the logger format
logging.basicConfig(level=LOG_LEVEL, format='%(levelname)s: %(message)s')

# --- Script Configuration ---
initial_url = 'http://unipa.it'
max_redirects = 5
cache_dir = 'cache'

# --- Setup ---
os.makedirs(cache_dir, exist_ok=True)
logging.info(f"Base cache directory is '{cache_dir}/'")

# --- Main Script Logic ---
current_url = initial_url
redirect_count = 0

while redirect_count < max_redirects:
    logging.info(f"--- Attempt {redirect_count + 1}: Processing URL: {current_url} ---")

    # 1. Parse the URL
    try:
        parsed_url = urlparse(current_url)
        hostname = parsed_url.hostname
        path = parsed_url.path
        if not hostname:
            logging.error(f"Invalid URL, cannot determine hostname from '{current_url}'")
            break
    except Exception as e:
        logging.error(f"Error parsing URL: {e}")
        break

    # 2. Define cache path
    host_cache_dir = os.path.join(cache_dir, hostname)
    if not path or path == '/':
        filename = 'index.html'
    else:
        safe_path = re.sub(r'[^a-zA-Z0-9._-]', '_', path)
        filename = safe_path + '.html'
        if filename.startswith('_'):
            filename = filename[1:]
            
    filepath = os.path.join(host_cache_dir, filename)

    # 3. CACHE CHECK
    if os.path.exists(filepath):
        logging.info(f"CACHE HIT: Found content in '{filepath}'")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                logging.debug("\n--- Cached Page Content ---")
                logging.debug(f.read())
            break
        except Exception as e:
            logging.warning(f"Error reading from cache file: {e}. Fetching from network.")

    else:
        logging.debug(f"CACHE MISS: File '{filepath}' not found.")

    # 4. Create host cache directory if needed
    os.makedirs(host_cache_dir, exist_ok=True)

    # 5. Network Request
    logging.debug(f"Connecting to {hostname} on port {443 if parsed_url.scheme == 'https' else 80}")
    port = 443 if parsed_url.scheme == 'https' else 80
    request = (
        f"GET {path or '/'} HTTP/1.1\r\n"
        f"Host: {hostname}\r\n"
        f"Connection: close\r\n"
        f"User-Agent: SimplePythonClient\r\n\r\n"
    ).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if parsed_url.scheme == 'https':
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=hostname)
    
    try:
        sock.connect((hostname, port))
        sock.sendall(request)
        response_bytes = b""
        while True:
            chunk = sock.recv(2048)
            if not chunk: break
            response_bytes += chunk
    except socket.gaierror:
        logging.error(f"Could not resolve hostname '{hostname}'")
        break
    except Exception as e:
        logging.error(f"An error occurred during connection: {e}")
        break
    finally:
        sock.close()

    # 6. Parse the response
    try:
        headers_raw, body = response_bytes.split(b'\r\n\r\n', 1)
        headers_str = headers_raw.decode('utf-8', errors='ignore')
        headers = headers_str.split('\r\n')
        status_line = headers[0]
        status_code = int(status_line.split(' ')[1])
        
        # Log essential response info
        logging.info(f"Received status code: {status_code}")
        logging.info("\n--- HTTP Response Headers ---")
        logging.info(headers_str)
        logging.info("---------------------------\n")

    except (ValueError, IndexError):
        logging.error("Could not parse server response.")
        break

    # 7. Check the status code
    if 200 <= status_code < 300:
        # Success (2xx)
        page_content = body.decode('utf-8', errors='ignore')

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_content)
            logging.info(f"SUCCESS: Response saved to cache file '{filepath}'")
        except Exception as e:
            logging.error(f"Could not write to cache file: {e}")
        
        logging.debug("--- Final Page Content ---")
        #logging.debug(page_content)
        break
    
    elif 300 <= status_code < 400:
        # Redirect (3xx)
        location_header = next((h for h in headers if h.lower().startswith('location:')), None)
        if location_header:
            new_url = location_header.split(':', 1)[1].strip()
            logging.info(f"Redirecting to: {new_url}")
            current_url = new_url
            redirect_count += 1
        else:
            logging.error("Redirect status received, but no 'Location' header found.")
            break
    else:
        # Client or Server Error (4xx or 5xx)
        logging.error(f"HTTP Error: {status_code}")
        logging.error(response_bytes.decode('utf-8', errors='ignore'))
        break
else:
    logging.error(f"Maximum number of {max_redirects} redirects reached.")