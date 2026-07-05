from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

MEMORIES_FILE = 'memories.json'

def load_memories():
    try:
        with open(MEMORIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_memories(data):
    with open(MEMORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/memories', methods=['GET'])
def get_memories():
    return jsonify(load_memories())

@app.route('/memories', methods=['POST'])
def add_memory():
    data = request.json
    data['id'] = str(uuid.uuid4())
    data['created_at'] = datetime.now().isoformat()
    
    memories = load_memories()
    memories.append(data)
    save_memories(memories)
    
    socketio.emit('new_memory', data)
    return jsonify({'status': 'ok', 'id': data['id']})

@app.route('/memories/<id>', methods=['PUT'])
def update_memory(id):
    data = request.json
    memories = load_memories()
    
    for i, m in enumerate(memories):
        if m['id'] == id:
            memories[i] = data
            save_memories(memories)
            socketio.emit('update_memory', data)
            return jsonify({'status': 'ok'})
    
    return jsonify({'status': 'error'}), 404

@app.route('/memories/<id>', methods=['DELETE'])
def delete_memory(id):
    memories = load_memories()
    memories = [m for m in memories if m['id'] != id]
    save_memories(memories)
    
    socketio.emit('delete_memory', {'id': id})
    return jsonify({'status': 'ok'})

@socketio.on('connect')
def handle_connect():
    print(f'✅ Клиент подключился: {request.sid}')
    memories = load_memories()
    emit('sync_all', memories)

@socketio.on('disconnect')
def handle_disconnect():
    print(f'❌ Клиент отключился: {request.sid}')

if __name__ == '__main__':
    print('🚀 Сервер запущен на порту 443 (HTTPS) и 80 (HTTP)')
    socketio.run(
        app,
        host='0.0.0.0',
        port=443,
        debug=True,
        ssl_context='adhoc'  # Автоматический HTTPS-сертификат
    )
