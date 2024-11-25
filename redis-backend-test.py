from flask import Flask, request, jsonify
import redis
import uuid
import json

app = Flask(__name__)

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# API endpoint to accept HTTP requests
@app.route('/enqueue', methods=['POST'])
def enqueue_request():
    # Extract request details
    request_data = {
        "id": str(uuid.uuid4()),  # Generate a unique ID
        "method": request.headers.get("Method", "Unknown"),
        "url": request.url,
        "content_length": request.content_length,
        "timestamp": request.headers.get('Date', 'Unknown')
    }

    # Push to Redis queue
    redis_client.lpush('request_queue', json.dumps(request_data))

    return jsonify({"status": "success", "message": "Request enqueued", "data": request_data}), 200

if __name__ == '__main__':
    app.run(debug=True)
