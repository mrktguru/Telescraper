#!/usr/bin/env python3
"""
Script to check logs and diagnose web app issues
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'data/app.db'

def check_database():
    """Check database contents"""
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных не найдена: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("="*80)

    # Check users
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()['count']
    print(f"\n👥 Пользователей: {user_count}")

    # Check tasks
    cursor.execute('SELECT COUNT(*) as count FROM tasks')
    task_count = cursor.fetchone()['count']
    print(f"📋 Задач: {task_count}")

    # Check channels
    cursor.execute('SELECT COUNT(*) as count FROM channels')
    channel_count = cursor.fetchone()['count']
    print(f"📺 Каналов: {channel_count}")

    # Show recent tasks
    if task_count > 0:
        print("\n" + "-"*80)
        print("ПОСЛЕДНИЕ ЗАДАЧИ:")
        print("-"*80)

        cursor.execute('''
            SELECT id, status, channel_url, posts_limit, created_at, error
            FROM tasks
            ORDER BY created_at DESC
            LIMIT 5
        ''')

        for task in cursor.fetchall():
            print(f"\nID {task['id']}: {task['status'].upper()}")
            print(f"  Канал: {task['channel_url']}")
            print(f"  Создано: {task['created_at']}")
            if task['error']:
                print(f"  ❌ Ошибка: {task['error']}")

    conn.close()


def check_env():
    """Check environment variables"""
    print("\n" + "="*80)
    print("ПРОВЕРКА .ENV ФАЙЛА")
    print("="*80)

    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'TELEGRAM_PHONE',
        'SECRET_KEY'
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'TELEGRAM_PHONE':
                print(f"✓ {var}: {value}")
            else:
                print(f"✓ {var}: {'*' * 10}")
        else:
            print(f"❌ {var}: НЕ НАЙДЕНО")
            missing.append(var)

    if missing:
        print(f"\n⚠ Отсутствуют переменные: {', '.join(missing)}")
        return False
    return True


def check_files():
    """Check required files"""
    print("\n" + "="*80)
    print("ПРОВЕРКА ФАЙЛОВ")
    print("="*80)

    files = {
        '.env': 'Конфигурация',
        'parser_lib.py': 'Библиотека парсера',
        'web_app.py': 'Веб-приложение',
        'database.py': 'База данных',
        'templates/index.html': 'Главная страница',
        'data/app.db': 'SQLite база'
    }

    for file, desc in files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✓ {file:30} {desc:20} ({size} bytes)")
        else:
            print(f"❌ {file:30} {desc:20} НЕ НАЙДЕНО")


def main():
    """Main function"""
    print("\n" + "🔍 ДИАГНОСТИКА ТЕЛЕГРАМ ПАРСЕРА")

    check_files()
    check_env()
    check_database()

    print("\n" + "="*80)
    print("РЕКОМЕНДАЦИИ")
    print("="*80)
    print("""
1. Для просмотра логов в реальном времени запустите:
   python3 web_app.py

2. Откройте веб-интерфейс в браузере и откройте консоль разработчика (F12)

3. При возникновении ошибки скопируйте полный текст ошибки из терминала

4. Проверьте, что Telegram сессия активна (.session файл)
    """)


if __name__ == '__main__':
    main()
