"""
Database models for Telegram Parser Web App
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash, check_password_hash


class Database:
    """Database manager"""

    def __init__(self, db_path: str = 'data/app.db'):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tasks table (parsing tasks)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_url TEXT NOT NULL,
                posts_limit INTEGER NOT NULL,
                keywords TEXT,
                keyword_mode TEXT DEFAULT 'or',
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                result_json TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Channels table (saved channels)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, url)
            )
        ''')

        conn.commit()
        conn.close()

    # User methods
    def create_user(self, email: str, password: str) -> Optional[int]:
        """Create new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            password_hash = generate_password_hash(password)

            cursor.execute(
                'INSERT INTO users (email, password_hash) VALUES (?, ?)',
                (email, password_hash)
            )

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return user_id
        except sqlite3.IntegrityError:
            # User already exists
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def verify_password(self, email: str, password: str) -> Optional[int]:
        """Verify user password, return user_id if correct"""
        user = self.get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            return user['id']
        return None

    # Task methods
    def create_task(
        self,
        user_id: int,
        channel_url: str,
        posts_limit: int,
        keywords: Optional[List[str]] = None,
        keyword_mode: str = 'or'
    ) -> int:
        """Create new parsing task"""
        conn = self.get_connection()
        cursor = conn.cursor()

        keywords_str = json.dumps(keywords) if keywords else None

        cursor.execute('''
            INSERT INTO tasks (user_id, channel_url, posts_limit, keywords, keyword_mode, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (user_id, channel_url, posts_limit, keywords_str, keyword_mode))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return task_id

    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get task by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            task = dict(row)
            # Parse JSON fields
            if task['keywords']:
                task['keywords'] = json.loads(task['keywords'])
            if task['result_json']:
                task['result'] = json.loads(task['result_json'])
            return task
        return None

    def update_task_progress(self, task_id: int, progress: int, status: str = None):
        """Update task progress"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute(
                'UPDATE tasks SET progress = ?, status = ? WHERE id = ?',
                (progress, status, task_id)
            )
        else:
            cursor.execute(
                'UPDATE tasks SET progress = ? WHERE id = ?',
                (progress, task_id)
            )

        conn.commit()
        conn.close()

    def complete_task(
        self,
        task_id: int,
        result: Dict,
        error: Optional[str] = None
    ):
        """Mark task as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        status = 'completed' if not error else 'failed'
        result_json = json.dumps(result) if result else None

        cursor.execute('''
            UPDATE tasks
            SET status = ?, result_json = ?, error = ?, completed_at = ?, progress = 100
            WHERE id = ?
        ''', (status, result_json, error, datetime.now(), task_id))

        conn.commit()
        conn.close()

    def get_user_tasks(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's tasks"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM tasks
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        tasks = []
        for row in rows:
            task = dict(row)
            if task['keywords']:
                task['keywords'] = json.loads(task['keywords'])
            if task['result_json']:
                task['result'] = json.loads(task['result_json'])
            tasks.append(task)

        return tasks

    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete task (only if belongs to user)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'DELETE FROM tasks WHERE id = ? AND user_id = ?',
            (task_id, user_id)
        )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    # Channel methods
    def add_channel(
        self,
        user_id: int,
        name: str,
        url: str,
        description: str = ''
    ) -> Optional[int]:
        """Add saved channel"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO channels (user_id, name, url, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, url, description))

            channel_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return channel_id
        except sqlite3.IntegrityError:
            # Channel already exists
            return None

    def get_user_channels(self, user_id: int) -> List[Dict]:
        """Get user's saved channels"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM channels
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_channel(self, channel_id: int) -> Optional[Dict]:
        """Get channel by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM channels WHERE id = ?', (channel_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def delete_channel(self, channel_id: int, user_id: int) -> bool:
        """Delete channel (only if belongs to user)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'DELETE FROM channels WHERE id = ? AND user_id = ?',
            (channel_id, user_id)
        )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0


# Initialize database
def init_database(db_path: str = 'data/app.db'):
    """Initialize database and return Database instance"""
    import os
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return Database(db_path)
