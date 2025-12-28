import os
import json
from flask import Flask, send_from_directory, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder='.')

@app.after_request
def add_no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'], cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS draft_state (
            id INTEGER PRIMARY KEY DEFAULT 1,
            participants TEXT DEFAULT '[]',
            draft_order TEXT DEFAULT '[]',
            current_pick INTEGER DEFAULT 0,
            drafted_colts TEXT DEFAULT '{}',
            scores TEXT DEFAULT '{}',
            auction_bids TEXT DEFAULT '{}',
            participant_inputs TEXT DEFAULT '[]',
            CHECK (id = 1)
        )
    ''')
    cur.execute('INSERT INTO draft_state (id) VALUES (1) ON CONFLICT (id) DO NOTHING')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/state', methods=['GET'])
def get_state():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM draft_state WHERE id = 1')
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({
            'participants': json.loads(row['participants']),
            'draftOrder': json.loads(row['draft_order']),
            'currentPick': row['current_pick'],
            'draftedColts': json.loads(row['drafted_colts']),
            'scores': json.loads(row['scores']),
            'auctionBids': json.loads(row['auction_bids']),
            'participantInputs': json.loads(row['participant_inputs']),
            'payments': json.loads(row['payments']) if row.get('payments') else {}
        })
    return jsonify({})

@app.route('/api/state', methods=['POST'])
def save_state():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE draft_state SET
            participants = %s,
            draft_order = %s,
            current_pick = %s,
            drafted_colts = %s,
            scores = %s,
            auction_bids = %s,
            participant_inputs = %s,
            payments = %s
        WHERE id = 1
    ''', (
        json.dumps(data.get('participants', [])),
        json.dumps(data.get('draftOrder', [])),
        data.get('currentPick', 0),
        json.dumps(data.get('draftedColts', {})),
        json.dumps(data.get('scores', {})),
        json.dumps(data.get('auctionBids', {})),
        json.dumps(data.get('participantInputs', [])),
        json.dumps(data.get('payments', {}))
    ))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
