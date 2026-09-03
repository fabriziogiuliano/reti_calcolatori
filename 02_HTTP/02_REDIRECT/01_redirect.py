import socket
import ssl
from urllib.parse import urlparse

# 1. CONFIGURATION
# We'll use a URL that is known to redirect (e.g., from http to https).
url = 'http://google.com' 
max_redirects = 5

# 2. LOOP TO FOLLOW REDIRECTS
# We will try a maximum of 'max_redirects' times.
for i in range(max_redirects):
    print(f"--- Attempt {i+1}: Requesting -> {url} ---")

    # 3. PARSE THE URL
    # Break the URL into its components: scheme (http/https), host, and path.
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    path = parsed_url.path or '/'
    scheme = parsed_url.scheme
    port = 443 if scheme == 'https' else 80

    print(f"CURRENT PORT:{port}")
    
    # 4. CREATE A MINIMAL HTTP REQUEST
    # Create the simplest possible request string.
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() # .encode() converts the string to bytes for sending.

    # 5. CONNECT USING A SOCKET
    # Create a socket, wrap it with SSL if the scheme is 'https', and then connect.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #SOCK_STREAM = TCP
    
    if scheme == 'https':
        sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
    sock.connect((host, port))
    sock.sendall(request)

    # 6. RECEIVE THE RESPONSE
    # Read the server's response in chunks until it's complete.
    response = b''
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        response += chunk
    sock.close()
    
    # 7. PARSE THE RESPONSE
    # Split the headers from the body and get the status code from the first line.
    headers_raw, body = response.split(b'\r\n\r\n', 1)
    status_line = headers_raw.decode().split('\r\n')[0]
    status_code = int(status_line.split(' ')[1])
    print(f"Received status code: {status_code}")

    # 8. CORE LOGIC: DECIDE WHAT TO DO BASED ON THE STATUS CODE
    
    # CASE A: SUCCESS (2xx status code)
    if 200 <= status_code < 300:
        print("\n--- PAGE RECEIVED SUCCESSFULLY ---")
        #print(body.decode(errors='ignore'))
        break # Exit the loop since we are done.

    # CASE B: REDIRECT (3xx status code)
    elif 300 <= status_code < 400:
        # Look for the 'Location:' header, which tells us the new URL.
        headers = headers_raw.decode().split('\r\n')
        new_url = None
        for line in headers:
            if line.lower().startswith('location:'):
                new_url = line.split(':', 1)[1].strip()
                break
        
        if new_url:
            
            print(" ----- RESPONSE ----- ")
            print(response)
            print(" ----- END RESPONSE ----- ")
            
            print(f"Redirect found! New URL: {new_url}")
            # THE MOST IMPORTANT PART: Update the 'url' variable for the next loop iteration.
            url = new_url 
        else:
            print("Error: Redirect received without a 'Location' header. Stopping.")
            break
            
    # CASE C: ERROR (4xx or 5xx status codes)
    else:
        print(f"HTTP Error: {status_code}. Stopping.")
        break

# This 'else' block only runs if the 'for' loop finishes without ever hitting a 'break'.
else:
    print(f"\nError: Maximum redirect limit of {max_redirects} reached.")