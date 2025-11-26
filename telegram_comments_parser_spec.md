# Telegram Comments Parser - Technical Specification

## Project Overview

**Project Name:** Simple Telegram Comments Parser  
**Target Channel:** https://t.me/okkosport  
**Version:** 1.0  
**Date:** 2024-11-26

---

## Requirements

### Functional Requirements

**Input:**
- Channel URL: `https://t.me/okkosport`
- Number of posts to parse: **30 последних постов**

**Output:**
1. **Terminal output** - таблица с результатами прямо в терминале
2. **CSV файл** - сохранение данных для дальнейшей работы
   - Имя файла: `okkosport_commenters_YYYY-MM-DD_HH-MM-SS.csv`

**Data to Collect:**
1. `first_name` - Имя пользователя
2. `username` - Username (ник) без @
3. `user_id` - Telegram User ID
4. `comment_text` - Текст комментария

**Interface:**
- CLI (Command Line Interface)
- Запуск: `python parser.py`
- Интерактивный вывод прогресса
- Красивая таблица с результатами в терминале
- Опция: показать все результаты или только первые N строк

### Business Logic

1. Подключиться к Telegram API через Telethon
2. Получить последние 30 постов из канала `@okkosport`
3. Для каждого поста:
   - Проверить, есть ли комментарии
   - Если есть - получить все комментарии
   - Извлечь данные автора каждого комментария
4. Сохранить все данные в CSV файл
5. Убрать дубликаты пользователей (один юзер может комментировать несколько раз)

---

## Technical Requirements

### Technology Stack

**Language:** Python 3.10+

**Libraries:**
```python
telethon==1.34.0      # Telegram API client
python-dotenv==1.0.0  # Environment variables
rich==13.7.0          # Beautiful terminal output (tables, progress bars)
# or tabulate==0.9.0  # Alternative for simple tables
```

**No Database** - только CSV файл

### File Structure

```
telegram_parser/
├── .env                    # API credentials (not in git)
├── .env.example           # Example config
├── parser.py              # Main script
├── requirements.txt       # Python dependencies
├── README.md             # How to run
└── output/               # Folder for CSV files
    └── okkosport_commenters_2024-11-26_15-30-00.csv
```

---

## Configuration

### Environment Variables (.env file)

```env
# Получить на https://my.telegram.org/auth
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890

# Settings
CHANNEL_URL=https://t.me/okkosport
POSTS_LIMIT=30
OUTPUT_DIR=./output
```

---

## Terminal Output Format

### During Parsing (Live Progress)

```
╔══════════════════════════════════════════════════════════╗
║         Telegram Comments Parser v1.0                    ║
╚══════════════════════════════════════════════════════════╝

📡 Connecting to Telegram...
✓ Authenticated as: +1234567890

🎯 Target: @okkosport
📊 Posts to check: 30

Parsing posts... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 30/30 100%

Post #12345: ✓ 15 comments
Post #12346: - no comments  
Post #12347: ✓ 8 comments
Post #12348: ✓ 23 comments
...

⏱️  Completed in 45 seconds
```

### After Parsing (Results Table)

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                              PARSING RESULTS                                     ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║ Total posts checked:        30                                                   ║
║ Posts with comments:        12                                                   ║
║ Total comments found:       156                                                  ║
║ Unique users collected:     89                                                   ║
║ Bots filtered out:          3                                                    ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ First Name    ┃ Username      ┃ User ID    ┃ Comment (first 50 chars)       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Алексей       │ alex_runner   │ 123456789  │ Отличные кроссовки! Где купит… │
│ Мария         │ -             │ 987654321  │ Согласна, качество супер       │
│ Дмитрий       │ dmitry_sport  │ 456789123  │ А есть в размере 43?           │
│ Елена         │ lena_fit      │ 789123456  │ Заказала себе такие, жду дост… │
│ Иван          │ vanya_moscow  │ 321654987  │ Цена адекватная?               │
│ ...           │ ...           │ ...        │ ...                            │
└───────────────┴───────────────┴────────────┴────────────────────────────────┘

Showing first 10 of 89 users. 

💾 Full data saved to: ./output/okkosport_commenters_2024-11-26_15-30-00.csv

Options:
  --show-all    Show all users in terminal (not just first 10)
  --no-csv      Don't save CSV file
  --quiet       Minimal output
```

### Command Line Options

```bash
# Basic run (default: 30 posts, first 10 results shown)
python parser.py

# Show all results in terminal
python parser.py --show-all

# Custom number of posts
python parser.py --posts 50

# Quiet mode (only summary)
python parser.py --quiet

# Different channel
python parser.py --channel https://t.me/another_channel

# Don't save CSV (only terminal output)
python parser.py --no-csv

# Combination
python parser.py --posts 100 --show-all --quiet
```

---

## Data Format

### CSV Output Format

**File name:** `okkosport_commenters_2024-11-26_15-30-00.csv`

**Columns:**
```csv
first_name,username,user_id,comment_text
Иван,ivan_petrov,123456789,"Отличный пост!"
Мария,,987654321,"Согласна полностью"
Петр,petr_sport,456789123,"Когда следующий выпуск?"
```

**Field Rules:**
- `first_name` - всегда заполнено (если у юзера нет имени, использовать "Unknown")
- `username` - может быть пустым (если пользователь не установил username)
- `user_id` - всегда заполнено (уникальный ID)
- `comment_text` - текст комментария, экранированный для CSV

**CSV Settings:**
- Encoding: `utf-8-sig` (чтобы Excel правильно открывал кириллицу)
- Delimiter: `,` (запятая)
- Quotechar: `"` (двойные кавычки)
- Quoting: `QUOTE_MINIMAL` (только если нужно)

---

## Algorithm

### Main Flow

```
1. START
   ↓
2. Parse command line arguments (--posts, --show-all, etc.)
   ↓
3. Print header banner
   ↓
4. Load credentials from .env
   ↓
5. Initialize Telegram client (Telethon)
   ↓
6. Print "Connecting..." message
   ↓
7. Authenticate user (first run - send code to phone)
   ↓
8. Print "Authenticated as: +phone"
   ↓
9. Get channel entity by URL: @okkosport
   ↓
10. Print "Target: @okkosport, Posts to check: 30"
   ↓
11. Initialize progress bar
   ↓
12. Fetch last 30 posts
   ↓
13. FOR EACH post:
    ├─ Update progress bar
    ├─ Check if post has comments (replies)
    ├─ IF yes:
    │  ├─ Print "Post #ID: ✓ X comments"
    │  ├─ Get all comments for this post
    │  └─ FOR EACH comment:
    │     ├─ Extract user data (first_name, username, user_id)
    │     ├─ Extract comment text
    │     └─ Add to results list
    ├─ ELSE:
    │  └─ Print "Post #ID: - no comments"
    └─ Sleep 1 second (rate limit protection)
   ↓
14. Print "Completed in X seconds"
   ↓
15. Remove duplicate users (keep first comment)
   ↓
16. Print results summary box
   ↓
17. Print results table (first 10 or all if --show-all)
   ↓
18. IF not --no-csv:
    ├─ Create output directory if not exists
    ├─ Generate filename with timestamp
    ├─ Write data to CSV file
    └─ Print "Saved to: path/to/file.csv"
   ↓
19. Print options/hints
   ↓
20. END
```

### Pseudocode

```python
import argparse
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel

console = Console()

async def main():
    # 1. Parse CLI arguments
    parser = argparse.ArgumentParser(description='Telegram Comments Parser')
    parser.add_argument('--posts', type=int, default=30, help='Number of posts to parse')
    parser.add_argument('--show-all', action='store_true', help='Show all results in terminal')
    parser.add_argument('--no-csv', action='store_true', help='Skip CSV file creation')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    parser.add_argument('--channel', type=str, default='https://t.me/okkosport', help='Channel URL')
    args = parser.parse_args()
    
    # 2. Print header
    console.print(Panel.fit("🚀 Telegram Comments Parser v1.0", style="bold blue"))
    
    # 3. Setup
    load_dotenv()
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    # 4. Initialize client
    console.print("\n📡 Connecting to Telegram...", style="yellow")
    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone)
    console.print(f"✓ Authenticated as: {phone}", style="green")
    
    # 5. Get channel
    console.print(f"\n🎯 Target: {args.channel}")
    console.print(f"📊 Posts to check: {args.posts}\n")
    channel = await client.get_entity(args.channel)
    
    # 6. Parse comments
    results = []
    start_time = time.time()
    posts = await client.get_messages(channel, limit=args.posts)
    
    for post in track(posts, description="Parsing posts..."):
        if post.replies and post.replies.replies > 0:
            if not args.quiet:
                console.print(f"Post #{post.id}: ✓ {post.replies.replies} comments", style="green")
            
            comments = await client.get_messages(
                channel,
                reply_to=post.id,
                limit=None
            )
            
            for comment in comments:
                user = await comment.get_sender()
                if not user.bot:  # Filter out bots
                    results.append({
                        'first_name': user.first_name or 'Unknown',
                        'username': user.username or '-',
                        'user_id': user.id,
                        'comment_text': comment.text or ''
                    })
            
            await asyncio.sleep(1)
        else:
            if not args.quiet:
                console.print(f"Post #{post.id}: - no comments", style="dim")
    
    elapsed = time.time() - start_time
    console.print(f"\n⏱️  Completed in {elapsed:.0f} seconds\n", style="bold green")
    
    # 7. Deduplicate by user_id (keep first occurrence)
    seen_users = set()
    unique_results = []
    for row in results:
        if row['user_id'] not in seen_users:
            seen_users.add(row['user_id'])
            unique_results.append(row)
    
    # 8. Print summary
    summary = f"""
╔══════════════════════════════════════════════════════════╗
║                    PARSING RESULTS                       ║
╠══════════════════════════════════════════════════════════╣
║ Total posts checked:        {len(posts):<28} ║
║ Posts with comments:        {sum(1 for p in posts if p.replies and p.replies.replies > 0):<28} ║
║ Total comments found:       {len(results):<28} ║
║ Unique users collected:     {len(unique_results):<28} ║
╚══════════════════════════════════════════════════════════╝
"""
    console.print(summary, style="bold cyan")
    
    # 9. Print results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("First Name", style="cyan", width=15)
    table.add_column("Username", style="green", width=15)
    table.add_column("User ID", style="yellow", width=12)
    table.add_column("Comment (first 50 chars)", style="white", width=35)
    
    display_count = len(unique_results) if args.show_all else min(10, len(unique_results))
    
    for row in unique_results[:display_count]:
        table.add_row(
            row['first_name'],
            row['username'],
            str(row['user_id']),
            row['comment_text'][:50] + ('…' if len(row['comment_text']) > 50 else '')
        )
    
    console.print(table)
    
    if not args.show_all and len(unique_results) > 10:
        console.print(f"\n💡 Showing first 10 of {len(unique_results)} users.", style="dim")
        console.print("   Run with --show-all to see all results\n", style="dim")
    
    # 10. Save to CSV
    if not args.no_csv:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_dir = Path('./output')
        output_dir.mkdir(exist_ok=True)
        
        filename = output_dir / f'okkosport_commenters_{timestamp}.csv'
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['first_name', 'username', 'user_id', 'comment_text'])
            writer.writeheader()
            writer.writerows(unique_results)
        
        console.print(f"💾 Full data saved to: {filename}", style="bold green")
    
    # 11. Print hints
    console.print("\n📝 Options:", style="bold")
    console.print("  --show-all    Show all users in terminal", style="dim")
    console.print("  --posts N     Parse N posts (default: 30)", style="dim")
    console.print("  --no-csv      Don't save CSV file", style="dim")
    console.print("  --quiet       Minimal output\n", style="dim")

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Error Handling

### Expected Errors

1. **FloodWaitError** - слишком много запросов
   - Action: Wait specified seconds and retry
   - Log: Warning message

2. **ChannelPrivateError** - канал закрыт
   - Action: Exit with error message
   - Log: Error

3. **No comments found** - посты без комментариев
   - Action: Continue to next post
   - Log: Info message

4. **User deleted account** - юзер удалил аккаунт
   - Action: Skip this comment
   - Log: Debug message

5. **Network errors** - проблемы с сетью
   - Action: Retry 3 times with exponential backoff
   - Log: Warning

### Error Handling Example

```python
from telethon.errors import FloodWaitError, ChannelPrivateError

try:
    comments = await client.get_messages(channel, reply_to=post.id)
except FloodWaitError as e:
    print(f"Rate limit hit. Waiting {e.seconds} seconds...")
    await asyncio.sleep(e.seconds)
    comments = await client.get_messages(channel, reply_to=post.id)
except ChannelPrivateError:
    print("ERROR: Channel is private. Exiting.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    continue  # Skip this post
```

---

## Rate Limits

### Telegram API Limits

- **Posts fetching:** No strict limit for reading
- **Comments fetching:** Max ~20 requests per minute
- **Recommended delays:**
  - Between posts: 1 second
  - Between comment batches: 2 seconds
  - On FloodWait: wait as instructed by API

### Protection Strategy

```python
# After each post with comments
await asyncio.sleep(1)

# If many comments (>100)
if len(comments) > 100:
    await asyncio.sleep(2)
```

---

## Usage

### First Run (Authentication)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup .env file
cp .env.example .env
# Edit .env with your credentials

# 3. Run parser (default: 30 posts)
python parser.py

# 4. Enter code from Telegram when prompted
# Code will be sent to your Telegram app
```

### Subsequent Runs

```bash
# Basic run (30 posts, first 10 results in terminal)
python parser.py

# Show all results in terminal instead of just 10
python parser.py --show-all

# Parse more posts
python parser.py --posts 50
python parser.py --posts 100

# Different channel
python parser.py --channel https://t.me/another_channel

# Quiet mode (no progress, only summary)
python parser.py --quiet

# Don't save CSV file (only terminal output)
python parser.py --no-csv

# Combinations
python parser.py --posts 100 --show-all
python parser.py --channel https://t.me/sport_channel --posts 50 --quiet
```

### Expected Terminal Output - Default Run

```
╔══════════════════════════════════════════════════════════╗
║         🚀 Telegram Comments Parser v1.0                 ║
╚══════════════════════════════════════════════════════════╝

📡 Connecting to Telegram...
✓ Authenticated as: +1234567890

🎯 Target: https://t.me/okkosport
📊 Posts to check: 30

Parsing posts... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 30/30 100%

Post #12345: ✓ 15 comments
Post #12346: - no comments  
Post #12347: ✓ 8 comments
...

⏱️  Completed in 45 seconds

╔══════════════════════════════════════════════════════════╗
║                    PARSING RESULTS                       ║
╠══════════════════════════════════════════════════════════╣
║ Total posts checked:        30                           ║
║ Posts with comments:        12                           ║
║ Total comments found:       156                          ║
║ Unique users collected:     89                           ║
╚══════════════════════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ First Name    ┃ Username      ┃ User ID    ┃ Comment (first 50 chars)       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Алексей       │ alex_runner   │ 123456789  │ Отличные кроссовки! Где купит… │
│ Мария         │ -             │ 987654321  │ Согласна, качество супер       │
│ Дмитрий       │ dmitry_sport  │ 456789123  │ А есть в размере 43?           │
│ Елена         │ lena_fit      │ 789123456  │ Заказала себе такие, жду дост… │
│ Иван          │ vanya_moscow  │ 321654987  │ Цена адекватная?               │
│ Ольга         │ olga_run      │ 147258369  │ Супер! Заказываю уже второй р… │
│ Петр          │ -             │ 258369147  │ Доставка быстрая была          │
│ Анна          │ anna_fitness  │ 369147258  │ Рекомендую!                    │
│ Сергей        │ sergey_sport  │ 741852963  │ Качество на высоте 👍          │
│ Наталья       │ -             │ 852963741  │ Где можно примерить?           │
└───────────────┴───────────────┴────────────┴────────────────────────────────┘

💡 Showing first 10 of 89 users.
   Run with --show-all to see all results

💾 Full data saved to: ./output/okkosport_commenters_2024-11-26_15-30-00.csv

📝 Options:
  --show-all    Show all users in terminal
  --posts N     Parse N posts (default: 30)
  --no-csv      Don't save CSV file
  --quiet       Minimal output
```

### Expected Terminal Output - With --show-all

```bash
python parser.py --show-all
```

```
[Same header and parsing process...]

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ First Name    ┃ Username      ┃ User ID    ┃ Comment (first 50 chars)       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Алексей       │ alex_runner   │ 123456789  │ Отличные кроссовки! Где купит… │
│ Мария         │ -             │ 987654321  │ Согласна, качество супер       │
│ ... [all 89 rows] ...                                                         │
└───────────────┴───────────────┴────────────┴────────────────────────────────┘

💾 Full data saved to: ./output/okkosport_commenters_2024-11-26_15-30-00.csv
```

### Expected Terminal Output - Quiet Mode

```bash
python parser.py --quiet
```

```
╔══════════════════════════════════════════════════════════╗
║         🚀 Telegram Comments Parser v1.0                 ║
╚══════════════════════════════════════════════════════════╝

📡 Connecting to Telegram...
✓ Authenticated as: +1234567890

🎯 Target: https://t.me/okkosport
📊 Posts to check: 30

Parsing posts... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 30/30 100%

⏱️  Completed in 45 seconds

╔══════════════════════════════════════════════════════════╗
║                    PARSING RESULTS                       ║
╠══════════════════════════════════════════════════════════╣
║ Total posts checked:        30                           ║
║ Posts with comments:        12                           ║
║ Total comments found:       156                          ║
║ Unique users collected:     89                           ║
╚══════════════════════════════════════════════════════════╝

💾 Full data saved to: ./output/okkosport_commenters_2024-11-26_15-30-00.csv
```

---

## Testing Checklist

### Functionality Tests
- [ ] Script connects to Telegram successfully
- [ ] Authentication works (code input)
- [ ] Channel @okkosport is accessible
- [ ] Last 30 posts are fetched
- [ ] Comments are extracted correctly
- [ ] User data is complete (first_name, username, user_id, comment_text)
- [ ] Bots are filtered out (is_bot check)
- [ ] Duplicates are removed (same user_id appears once)
- [ ] CSV file is created in output/ folder
- [ ] CSV opens correctly in Excel with cyrillic text
- [ ] Rate limits are handled (no FloodWaitError)
- [ ] Script handles posts without comments gracefully

### CLI Interface Tests
- [ ] Default run works (30 posts, first 10 shown)
- [ ] `--show-all` displays all users in terminal
- [ ] `--posts N` changes number of posts parsed
- [ ] `--quiet` mode reduces output correctly
- [ ] `--no-csv` skips file creation
- [ ] `--channel URL` works with different channels
- [ ] Multiple flags work together (e.g. `--posts 50 --show-all`)
- [ ] Progress bar displays correctly during parsing
- [ ] Table formatting is readable and aligned
- [ ] Summary statistics box displays correctly
- [ ] Colors/emojis render correctly in terminal
- [ ] Cyrillic text displays correctly in terminal table

### Error Handling Tests
- [ ] Invalid channel URL shows error message
- [ ] Missing .env file shows clear error
- [ ] FloodWaitError is caught and handled
- [ ] Network errors don't crash script
- [ ] Empty channel (no posts) handled gracefully
- [ ] Channel with no comments handled gracefully

### Performance Tests
- [ ] Parsing 30 posts completes in reasonable time (<2 min)
- [ ] Memory usage is acceptable
- [ ] No memory leaks on long runs
- [ ] Rate limiting delays work correctly (1 sec between posts)

---

## Deliverables

1. **parser.py** - main script with CLI interface
2. **requirements.txt** - dependencies list (telethon, python-dotenv, rich)
3. **.env.example** - configuration template
4. **README.md** - setup, usage instructions, and CLI examples
5. **output/** folder - with sample CSV file

---

## Notes for AI Implementation

### Key Points

1. **Use Telethon** (not Pyrogram) - more stable for comment parsing
2. **Session file** - will be created as `session.session` on first run
3. **Channel entity** - use `client.get_entity('https://t.me/okkosport')` or `client.get_entity('@okkosport')`
4. **Comments structure** - use `reply_to` parameter to get comments for specific post
5. **CSV encoding** - MUST be `utf-8-sig` for Excel compatibility
6. **User deduplication** - by `user_id`, keep first occurrence
7. **Rich library** - use for beautiful terminal output, tables, and progress bars
8. **argparse** - for CLI argument parsing (--posts, --show-all, etc.)

### Common Pitfalls to Avoid

❌ Don't use Bot API - it can't fetch comments  
❌ Don't forget rate limiting - will get banned  
❌ Don't use regular `utf-8` - Excel won't show cyrillic  
❌ Don't fetch all comments in one request - use pagination if >100  
❌ Don't hardcode credentials - use .env file  
❌ Don't print ugly plain text - use Rich library for formatting  
❌ Don't show all results by default - limit to 10 unless --show-all  

### Terminal Output Best Practices

✅ Use Rich Console for all output  
✅ Use Rich Table for data display  
✅ Use Rich Progress/track for parsing progress  
✅ Use Rich Panel for header/summary boxes  
✅ Use colors/styles for different message types (green for success, yellow for warnings, red for errors)  
✅ Add emojis for visual clarity (📡 🎯 📊 ✓ ⏱️ 💾)  
✅ Keep table column widths reasonable (truncate long text)  
✅ Show "first N of total" when limiting results  

### CLI Arguments Implementation

```python
import argparse

parser = argparse.ArgumentParser(
    description='Parse Telegram channel comments',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  python parser.py                              # Default: 30 posts, first 10 shown
  python parser.py --posts 50                   # Parse 50 posts
  python parser.py --show-all                   # Show all results in terminal
  python parser.py --channel https://t.me/xxx   # Different channel
  python parser.py --quiet --no-csv             # Minimal output, no file
    '''
)

parser.add_argument('--posts', type=int, default=30, 
                    help='Number of posts to parse (default: 30)')
parser.add_argument('--show-all', action='store_true',
                    help='Show all users in terminal (default: first 10)')
parser.add_argument('--no-csv', action='store_true',
                    help='Skip CSV file creation')
parser.add_argument('--quiet', action='store_true',
                    help='Minimal output (no per-post messages)')
parser.add_argument('--channel', type=str, default='https://t.me/okkosport',
                    help='Channel URL (default: https://t.me/okkosport)')

args = parser.parse_args()
```

### Rich Library Usage Examples

```python
from rich.console import Console
from rich.table import Table
from rich.progress import track, Progress
from rich.panel import Panel
from rich import box

console = Console()

# Header
console.print(Panel.fit("🚀 Telegram Comments Parser v1.0", 
                        style="bold blue", 
                        border_style="blue"))

# Success message
console.print("✓ Connected successfully", style="green bold")

# Warning
console.print("⚠ Rate limit approaching", style="yellow")

# Error
console.print("❌ Connection failed", style="red bold")

# Progress bar
for item in track(items, description="Processing..."):
    # do work
    pass

# Table
table = Table(title="Results", box=box.ROUNDED)
table.add_column("Name", style="cyan")
table.add_column("ID", style="yellow")
table.add_row("John", "123")
console.print(table)

# Conditional output
if not args.quiet:
    console.print(f"Post #{post.id}: ✓ {replies} comments")
```

### Optional Enhancements (not required)

- Progress bar with percentage and ETA
- Export to JSON format option
- Filter by date range
- Filter by minimum comment length
- Detect and mark deleted users
- Add user statistics (avg comment length, most active, etc.)

---

## Example Data

### Sample CSV Output

```csv
first_name,username,user_id,comment_text
Алексей,alex_runner,123456789,"Отличные кроссовки! Где купить?"
Мария,,987654321,"Согласна, качество супер"
Дмитрий,dmitry_sport,456789123,"А есть в размере 43?"
Елена,lena_fit,789123456,"Заказала себе такие, жду доставку 🔥"
Иван,vanya_moscow,321654987,"Цена адекватная?"
```

### Expected File Structure After Run

```
telegram_parser/
├── .env
├── .env.example
├── parser.py
├── requirements.txt
├── README.md
├── session.session          # Created on first run
├── session.session-journal  # Created on first run
└── output/
    └── okkosport_commenters_2024-11-26_15-30-00.csv
```

---

## Timeline Estimate

- Setup environment: 5 min
- Write parser.py with CLI: 45 min
- Add Rich formatting: 15 min
- Testing and debugging: 20 min
- Documentation (README): 10 min

**Total:** ~1.5 hours

---

## Success Criteria

✅ Script runs without errors  
✅ Beautiful CLI output with tables and progress bars  
✅ All command line options work (--posts, --show-all, --quiet, --no-csv, --channel)  
✅ Results displayed in terminal as formatted table  
✅ CSV file is created with correct data (unless --no-csv)  
✅ At least 50+ unique users collected (if channel has active comments)  
✅ No Telegram bans or FloodWait errors  
✅ CSV opens correctly in Excel with Russian text  
✅ Cyrillic text displays correctly in terminal  
✅ Code is clean and well-commented  
✅ Help text (--help) is clear and useful  

---

## Support Information

**Telegram API Documentation:** https://docs.telethon.dev/  
**Rate Limits Info:** https://core.telegram.org/api/rate-limiting  
**CSV Module Docs:** https://docs.python.org/3/library/csv.html  
**Rich Library Docs:** https://rich.readthedocs.io/en/stable/  
**Argparse Tutorial:** https://docs.python.org/3/howto/argparse.html  

---

*End of specification*
