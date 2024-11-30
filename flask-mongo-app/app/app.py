from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
import threading

app = Flask(__name__)
app.secret_key = 'S3CR37_key222751'

client = MongoClient('mongodb://mongo:27017')
db = client.flask_app
users_collection = db.users
notes_collection = db.notes



LOGGING_SERVER_URL = "http://127.0.0.1:5001/log"

def forward_request_async(data):
    try:
        requests.post(LOGGING_SERVER_URL, json=data, timeout=2)
    except Exception as e:
        app.logger.error(f"Error forwarding request: {e}")

@app.before_request
def forward_request():
    if request.endpoint != 'log':  # Avoid forwarding logging server's own requests
        data = {
            "headers": dict(request.headers),
            "path": request.path,
            "method": request.method,
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "json": request.get_json(silent=True),
            "remote_addr": request.remote_addr
        }
        thread = threading.Thread(target=forward_request_async, args=(data,))
        thread.start()  # Run the forwarding task in the background





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