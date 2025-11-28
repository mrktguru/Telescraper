"""
Telegram Comments Parser - Web Application
Flask web interface for telegram parser
"""

import os
import asyncio
import json
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv

from database import init_database
from parser_lib import TelegramParser, save_to_csv, save_to_json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
db = init_database()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    """User class for Flask-Login"""

    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    user_data = db.get_user_by_id(int(user_id))
    if user_data:
        return User(user_data['id'], user_data['email'])
    return None


# Background task storage
active_tasks = {}


def run_parsing_task(task_id, user_id):
    """Run parsing task in background thread"""

    # Get task details
    task = db.get_task(task_id)
    if not task:
        return

    # Update status
    db.update_task_progress(task_id, 0, 'running')

    try:
        # Get Telegram credentials
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')

        # Progress callback
        def progress_callback(percentage, current, total):
            db.update_task_progress(task_id, percentage, 'running')
            active_tasks[task_id] = {
                'progress': percentage,
                'current': current,
                'total': total,
                'status': 'running'
            }

        # Create async function
        async def parse():
            parser = TelegramParser(api_id, api_hash, phone)
            await parser.connect()

            result = await parser.parse_channel(
                channel_url=task['channel_url'],
                posts_limit=task['posts_limit'],
                keywords=task['keywords'],
                keyword_mode=task['keyword_mode'],
                progress_callback=progress_callback
            )

            await parser.disconnect()
            return result

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(parse())
        loop.close()

        # Save result
        if result['success']:
            # Save files
            channel_name = task['channel_url'].split('/')[-1]
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            csv_path = save_to_csv(
                result['unique_results'],
                output_dir='data/output',
                channel_name=channel_name,
                timestamp=timestamp
            )

            json_path = save_to_json(
                result['unique_results'],
                output_dir='data/output',
                channel_name=channel_name,
                timestamp=timestamp
            )

            # Add file paths to result
            result['csv_file'] = csv_path
            result['json_file'] = json_path

            db.complete_task(task_id, result)
            active_tasks[task_id] = {'status': 'completed', 'progress': 100}
        else:
            db.complete_task(task_id, None, result.get('error', 'Unknown error'))
            active_tasks[task_id] = {'status': 'failed', 'progress': 0}

    except Exception as e:
        db.complete_task(task_id, None, str(e))
        active_tasks[task_id] = {'status': 'failed', 'progress': 0}


# Routes

@app.route('/')
@login_required
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_id = db.verify_password(email, password)
        if user_id:
            user = User(user_id, email)
            login_user(user, remember=True)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if password != password_confirm:
            flash('Passwords do not match', 'danger')
        else:
            user_id = db.create_user(email, password)
            if user_id:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email already registered', 'danger')

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/api/parse', methods=['POST'])
@login_required
def api_parse():
    """Start parsing task"""
    data = request.get_json()

    channel_url = data.get('channel_url')
    posts_limit = int(data.get('posts_limit', 30))
    keywords_str = data.get('keywords', '')
    keyword_mode = data.get('keyword_mode', 'or')

    # Parse keywords
    keywords = []
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

    # Create task
    task_id = db.create_task(
        user_id=current_user.id,
        channel_url=channel_url,
        posts_limit=posts_limit,
        keywords=keywords,
        keyword_mode=keyword_mode
    )

    # Start background thread
    thread = threading.Thread(
        target=run_parsing_task,
        args=(task_id, current_user.id)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'task_id': task_id
    })


@app.route('/api/status/<int:task_id>')
@login_required
def api_status(task_id):
    """Get task status"""
    task = db.get_task(task_id)

    if not task or task['user_id'] != current_user.id:
        return jsonify({'error': 'Task not found'}), 404

    # Get real-time progress if available
    if task_id in active_tasks:
        task.update(active_tasks[task_id])

    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'current': active_tasks.get(task_id, {}).get('current', 0),
        'total': active_tasks.get(task_id, {}).get('total', 0)
    })


@app.route('/api/results/<int:task_id>')
@login_required
def api_results(task_id):
    """Get task results"""
    task = db.get_task(task_id)

    if not task or task['user_id'] != current_user.id:
        return jsonify({'error': 'Task not found'}), 404

    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed'}), 400

    return jsonify({
        'task_id': task_id,
        'result': task.get('result', {}),
        'created_at': task['created_at'],
        'completed_at': task['completed_at']
    })


@app.route('/history')
@login_required
def history():
    """History page"""
    tasks = db.get_user_tasks(current_user.id, limit=50)
    return render_template('history.html', tasks=tasks)


@app.route('/results/<int:task_id>')
@login_required
def results(task_id):
    """Results page"""
    task = db.get_task(task_id)

    if not task or task['user_id'] != current_user.id:
        flash('Task not found', 'danger')
        return redirect(url_for('index'))

    return render_template('results.html', task=task)


@app.route('/download/<int:task_id>.<format>')
@login_required
def download(task_id, format):
    """Download results file"""
    task = db.get_task(task_id)

    if not task or task['user_id'] != current_user.id:
        flash('Task not found', 'danger')
        return redirect(url_for('index'))

    if task['status'] != 'completed':
        flash('Task not completed', 'danger')
        return redirect(url_for('results', task_id=task_id))

    result = task.get('result', {})

    if format == 'csv':
        file_path = result.get('csv_file')
    elif format == 'json':
        file_path = result.get('json_file')
    else:
        flash('Invalid format', 'danger')
        return redirect(url_for('results', task_id=task_id))

    if not file_path or not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('results', task_id=task_id))

    return send_file(file_path, as_attachment=True)


@app.route('/api/task/<int:task_id>', methods=['DELETE'])
@login_required
def api_delete_task(task_id):
    """Delete task"""
    if db.delete_task(task_id, current_user.id):
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Task not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
