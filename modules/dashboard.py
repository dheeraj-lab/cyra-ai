import os
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard', 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard', 'static'))
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

def run_server():
    # Run Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)

_server_thread = None

def start_dashboard():
    global _server_thread
    if _server_thread is None:
        _server_thread = threading.Thread(target=run_server, daemon=True)
        _server_thread.start()
        print("[Dashboard] Running on http://localhost:5000")

# --- API for other modules ---

def update_status(status):
    """status: 'Listening', 'Thinking', 'Speaking'"""
    socketio.emit('status_update', {'status': status})

def log_message(role, text):
    """role: 'user', 'cyra'"""
    socketio.emit('new_message', {'role': role, 'text': text})

def update_metrics():
    try:
        from modules.stats import load_stats
        stats = load_stats()
        socketio.emit('stats_update', stats)
    except:
        pass
