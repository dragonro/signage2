#!/usr/bin/env python3
"""
Digital Signage Application
A browser-based digital signage system built with Flask and vanilla JavaScript.
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import feedparser

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

# Configuration
UPLOAD_FOLDER = 'static/uploads'
DATABASE_FILE = 'signage.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Displays table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS displays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            layout_config TEXT,
            background_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user if none exists
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Check for custom admin credentials from environment
        admin_username = os.environ.get('SIGNAGE_ADMIN_USER', 'admin')
        admin_password = os.environ.get('SIGNAGE_ADMIN_PASS', 'admin123')
        admin_password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      (admin_username, admin_password_hash))
    
    # Create default display if none exists
    cursor.execute('SELECT COUNT(*) FROM displays')
    if cursor.fetchone()[0] == 0:
        default_layout = json.dumps({
            'grid': {'rows': 2, 'cols': 2},
            'zones': [
                {
                    'id': 0, 
                    'type': 'clock', 
                    'content': '', 
                    'opacity': 1.0,
                    'font_family': 'Arial, sans-serif',
                    'font_size': '16px',
                    'background': {'type': 'transparent'},
                    'date_format': 'full',
                    'time_format': '24h'
                },
                {
                    'id': 1, 
                    'type': 'iframe', 
                    'content': '', 
                    'opacity': 1.0,
                    'font_family': 'Arial, sans-serif',
                    'font_size': '16px',
                    'background': {'type': 'transparent'}
                },
                {
                    'id': 2, 
                    'type': 'announcement', 
                    'content': 'Welcome to Digital Signage!', 
                    'opacity': 1.0,
                    'font_family': 'Arial, sans-serif',
                    'font_size': '24px',
                    'background': {'type': 'glassmorphism', 'blur': 10, 'opacity': 0.2}
                },
                {
                    'id': 3, 
                    'type': 'rss', 
                    'content': '', 
                    'opacity': 1.0,
                    'font_family': 'Arial, sans-serif',
                    'font_size': '14px',
                    'background': {'type': 'transparent'}
                }
            ],
            'global_font': 'Arial, sans-serif'
        })
        default_background = json.dumps({'type': 'color', 'value': '#1a1a1a'})
        cursor.execute('INSERT INTO displays (name, description, layout_config, background_config) VALUES (?, ?, ?, ?)',
                      ('Default Display', 'Default digital signage display', default_layout, default_background))
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    """Check if uploaded file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page - redirects to display list."""
    return redirect(url_for('displays'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[1] == hash_password(password):
            session['user_id'] = user[0]
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@require_auth
def admin():
    """Admin page - redirects to displays."""
    return redirect(url_for('displays'))

@app.route('/displays')
@require_auth
def displays():
    """Display management page."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_at FROM displays ORDER BY created_at DESC')
    displays_list = cursor.fetchall()
    conn.close()
    
    return render_template('displays.html', displays=displays_list)

@app.route('/display/<int:display_id>')
@require_auth
def display_config(display_id):
    """Display configuration page."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM displays WHERE id = ?', (display_id,))
    display = cursor.fetchone()
    conn.close()
    
    if not display:
        return redirect(url_for('displays'))
    
    return render_template('display_config.html', display=display)

@app.route('/player/<int:display_id>')
def player(display_id):
    """Fullscreen player page (no auth required for viewing)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM displays WHERE id = ?', (display_id,))
    display = cursor.fetchone()
    conn.close()
    
    if not display:
        return "Display not found", 404
    
    # Parse the JSON configuration
    try:
        layout_config = json.loads(display[3])
        background_config = json.loads(display[4])
    except json.JSONDecodeError as e:
        return f"Invalid display configuration: {e}", 500
    
    # Pass parsed configuration to template
    display_data = {
        'id': display[0],
        'name': display[1],
        'description': display[2],
        'layout_config': layout_config,
        'background_config': background_config
    }
    
    return render_template('player.html', display=display, display_data=display_data)

@app.route('/api/display/<int:display_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def api_display(display_id):
    """API endpoint for display data."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM displays WHERE id = ?', (display_id,))
        display = cursor.fetchone()
        conn.close()
        
        if not display:
            return jsonify({'error': 'Display not found'}), 404
        
        return jsonify({
            'id': display[0],
            'name': display[1],
            'description': display[2],
            'layout_config': json.loads(display[3]),
            'background_config': json.loads(display[4])
        })
    
    elif request.method == 'PUT':
        data = request.json
        layout_config = json.dumps(data.get('layout_config', {}))
        background_config = json.dumps(data.get('background_config', {}))
        
        cursor.execute('''
            UPDATE displays 
            SET name = ?, description = ?, layout_config = ?, background_config = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (data.get('name'), data.get('description'), layout_config, background_config, display_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Check if display exists
        cursor.execute('SELECT id FROM displays WHERE id = ?', (display_id,))
        display = cursor.fetchone()
        
        if not display:
            conn.close()
            return jsonify({'success': False, 'message': 'Display not found'}), 404
        
        # Delete the display
        cursor.execute('DELETE FROM displays WHERE id = ?', (display_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Display deleted successfully'})

@app.route('/api/display', methods=['POST'])
@require_auth
def api_create_display():
    """Create new display."""
    data = request.json
    name = data.get('name', 'New Display')
    description = data.get('description', '')
    
    default_layout = json.dumps({
        'grid': {'rows': 2, 'cols': 2},
        'zones': [
            {
                'id': 0, 
                'type': 'clock', 
                'content': '', 
                'opacity': 1.0,
                'font_family': 'Arial, sans-serif',
                'font_size': '16px',
                'background': {'type': 'transparent'},
                'date_format': 'full',
                'time_format': '24h'
            },
            {
                'id': 1, 
                'type': 'iframe', 
                'content': '', 
                'opacity': 1.0,
                'font_family': 'Arial, sans-serif',
                'font_size': '16px',
                'background': {'type': 'transparent'}
            },
            {
                'id': 2, 
                'type': 'announcement', 
                'content': 'Welcome!', 
                'opacity': 1.0,
                'font_family': 'Arial, sans-serif',
                'font_size': '24px',
                'background': {'type': 'glassmorphism', 'blur': 10, 'opacity': 0.2}
            },
            {
                'id': 3, 
                'type': 'timer', 
                'content': '10', 
                'opacity': 1.0,
                'font_family': 'Arial, sans-serif',
                'font_size': '48px',
                'background': {'type': 'transparent'}
            }
        ],
        'global_font': 'Arial, sans-serif'
    })
    default_background = json.dumps({'type': 'color', 'value': '#1a1a1a'})
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO displays (name, description, layout_config, background_config) 
        VALUES (?, ?, ?, ?)
    ''', (name, description, default_layout, default_background))
    
    display_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'display_id': display_id})

@app.route('/api/rss')
def api_rss():
    """Fetch RSS feed content."""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:  # Limit to 10 items
            items.append({
                'title': entry.get('title', ''),
                'description': entry.get('description', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', '')
            })
        
        return jsonify({
            'title': feed.feed.get('title', ''),
            'items': items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@require_auth
def api_upload():
    """Upload background image."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to prevent conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        return jsonify({'success': True, 'filename': filename, 'url': f'/static/uploads/{filename}'})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/time')
def api_time():
    """Get current time."""
    now = datetime.now()
    return jsonify({
        'time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%A, %B %d, %Y'),
        'timestamp': now.timestamp()
    })

@app.route('/debug/<int:display_id>')
def debug_player(display_id):
    """Debug version of player to see what data is being passed."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM displays WHERE id = ?', (display_id,))
    display = cursor.fetchone()
    conn.close()
    
    if not display:
        return f"Display {display_id} not found", 404
    
    # Return raw data for debugging
    return f"""
    <html>
    <head><title>Debug Display {display_id}</title></head>
    <body style="color: white; background: black; font-family: monospace; padding: 20px;">
    <h1>Debug Display {display_id}</h1>
    <p><strong>ID:</strong> {display[0]}</p>
    <p><strong>Name:</strong> {display[1]}</p>
    <p><strong>Description:</strong> {display[2]}</p>
    <p><strong>Layout Config (raw):</strong></p>
    <pre>{display[3]}</pre>
    <p><strong>Background Config (raw):</strong></p>
    <pre>{display[4]}</pre>
    
    <h2>Parsed Layout:</h2>
    <pre>{json.dumps(json.loads(display[3]), indent=2)}</pre>
    
    <h2>Parsed Background:</h2>
    <pre>{json.dumps(json.loads(display[4]), indent=2)}</pre>
    
    <p><a href="/player/{display_id}" style="color: cyan;">Go to actual player</a></p>
    </body>
    </html>
    """

if __name__ == '__main__':
    init_database()
    print("Digital Signage Server Starting...")
    print("Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
