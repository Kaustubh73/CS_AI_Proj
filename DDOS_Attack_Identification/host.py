from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    return "Welcome to the Dummy Website!"

@app.route('/data', methods=['GET', 'POST'])
def data():
    # Extract the required fields
    method = request.method
    url = request.url
    cookie = request.headers.get('Cookie', 'No Cookie')  # Extract 'Cookie' header
    content_len = request.headers.get('Content-Length', 'No Content Length')  # Extract 'Content-Length' header
    payload = request.form if request.method == 'POST' else request.args  # Form data for POST, query args for GET
    ip_address = request.remote_addr  # Client IP address
    user_agent = request.headers.get('User-Agent', 'No User-Agent')  # Extract 'User-Agent' header

    # Prepare log entry
    log_entry = (
        f"IP: {ip_address}, User-Agent: {user_agent}, "
        f"Method: {method}, URL: {url}, Cookie: {cookie}, "
        f"ContentLen: {content_len}, Payload: {payload}\n"
    )

    # Log request details to a file
    with open("request_logs.txt", "a") as f:
        f.write(log_entry)
        print(log_entry.strip())  # Also print to console

    return "Request details logged successfully!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
