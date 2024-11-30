from flask import Flask, render_template, request, redirect, url_for, session, abort, current_app
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
import threading
import redis
import json

app = Flask(__name__)
app.secret_key = 'S3CR37_key222751'

client = MongoClient('mongodb://mongo:27017')
db = client.flask_app
users_collection = db.users
notes_collection = db.notes
dropped_ips = {}


#LOGGING_SERVER_URL = "http://127.0.0.1:5001/log"
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
QUEUE_NAME = 'request_queue'

def forward_request_async(data):
    try:
        with app.app_context():
            redis_request = {
                'method': data['method'],
                'url': request.base_url,
                'headers': {
                    'IP': request.remote_addr,
                    'Content-Length': data['headers'].get('Content-Length', '0'),
                    'Cookie': data['headers'].get('Cookie', ''),
                    'User-Agent': data['headers'].get('User-Agent', ''),
                    'Target-Class': '0'  # Placeholder
                },
                'payload': data['form'] or ''
            }

            # Push to Redis asynchronously
            redis_client.lpush(QUEUE_NAME, json.dumps(redis_request))
    except Exception as e:
        app.logger.error(f"Error pushing request to Redis: {e}")

@app.before_request
def forward_request():
    if not request.path.startswith('/api/'):  # Avoid forwarding logging server's own requests
        data = {
            "headers": dict(request.headers),
            "path": request.path,
            "method": request.method,
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "json": request.get_json(silent=True),
            "remote_addr": request.remote_addr
        }
        #thread = threading.Thread(target=forward_request_async, args=(data,))
        #thread.start() 
        forward_request_async(data)


def is_local_request():
    return request.remote_addr == "127.0.0.1"

@app.before_request
def block_dropped_ips():
    client_ip = request.remote_addr

    for ip, expiry in list(dropped_ips.items()):
        if time.time() > expiry:
            del dropped_ips[ip]

    if client_ip in dropped_ips:
        abort(403)


@app.route('/api/drop_session', methods=['POST'])
def drop_session():
    if not is_local_request():
        abort(403)
    session_ids = request.json.get('session_ids', [])
    if not session_ids:
        return jsonify({"error": "No session IDs provided"}), 400
    # Drop sessions (Example: Custom handling logic depending on your app)
    for session_id in session_ids:
        app.logger.info(f"Session ID {session_id} dropped.")

    return jsonify({"message": "Session IDs processed for drop", "session_ids": session_ids})

@app.route('/api/drop_ip', methods=['POST'])
def drop_ip():
    if not is_local_request():
        abort(403)  # Restrict access to localhost only

    ip_addresses = request.json.get('ip_addresses', [])
    duration = request.json.get('duration', 300)  # Default to 5 minutes

    if not ip_addresses:
        return jsonify({"error": "No IP addresses provided"}), 400

    for ip in ip_addresses:
        dropped_ips[ip] = time.time() + duration
        app.logger.info(f"IP {ip} temporarily dropped for {duration} seconds.")

    return jsonify({"message": "IP addresses processed for drop", "dropped_ips": ip_addresses})



@app.route('/')
@app.route('/home')
def home():
    if 'user_id' in session:
        return redirect(url_for('notes')) 
    return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            # Password matches, create a session
            session['user_id'] = str(user['_id'])
            return redirect(url_for('notes'))
        else:
            return 'Invalid credentials', 401

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users_collection.find_one({'username': username}):
            return 'User already exists', 409
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({'username': username, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/notes')
def notes():
    if 'user_id' in session:
        user_notes = notes_collection.find({'user_id': session['user_id']})
        return render_template('notes.html', notes=user_notes)
    return redirect(url_for('login'))


@app.route('/delete_note/<note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' in session:
        # Delete the note with the specified ID
        notes_collection.delete_one({'_id': ObjectId(note_id), 'user_id': session['user_id']})
        return redirect(url_for('notes'))
    return redirect(url_for('login'))

@app.route('/add_note', methods=['POST'])
def add_note():
    if 'user_id' in session:
        content = request.form.get('content')
        if content.strip():
            notes_collection.insert_one({'user_id': session['user_id'], 'content': content})
        return redirect(url_for('notes'))
    return redirect(url_for('login'))

@app.route('/edit_note/<note_id>', methods=['POST'])
def edit_note(note_id):
    if 'user_id' in session:
        new_content = request.form.get('content')
        if new_content.strip():
            notes_collection.update_one(
                {'_id': ObjectId(note_id), 'user_id': session['user_id']},
                {'$set': {'content': new_content}}
            )
        return redirect(url_for('notes'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
