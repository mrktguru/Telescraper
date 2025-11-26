#!/usr/bin/env python3
"""
Telegram Comments Parser - Extract comments from Telegram channel posts
"""

import asyncio
import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel
from rich import box

console = Console()


async def main():
    """Main function to parse Telegram comments"""

    # Parse command line arguments
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

    # Print header
    console.print(Panel.fit(
        "🚀 Telegram Comments Parser v1.0",
        style="bold blue",
        border_style="blue"
    ))

    # Load environment variables
    load_dotenv()
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')

    # Validate credentials
    if not api_id or not api_hash or not phone:
        console.print("❌ Error: Missing credentials in .env file", style="red bold")
        console.print("\n📝 Please create .env file with:", style="yellow")
        console.print("   TELEGRAM_API_ID=your_api_id")
        console.print("   TELEGRAM_API_HASH=your_api_hash")
        console.print("   TELEGRAM_PHONE=+1234567890")
        console.print("\n💡 Get credentials at: https://my.telegram.org/auth", style="dim")
        sys.exit(1)

    # Initialize Telegram client
    console.print("\n📡 Connecting to Telegram...", style="yellow")
    client = TelegramClient('session', api_id, api_hash)

    try:
        await client.start(phone)
        console.print(f"✓ Authenticated as: {phone}", style="green bold")
    except Exception as e:
        console.print(f"❌ Authentication failed: {e}", style="red bold")
        sys.exit(1)

    # Get channel
    console.print(f"\n🎯 Target: {args.channel}", style="cyan")
    console.print(f"📊 Posts to check: {args.posts}\n", style="cyan")

    try:
        channel = await client.get_entity(args.channel)
    except ChannelPrivateError:
        console.print("❌ Error: Channel is private or you're not subscribed", style="red bold")
        await client.disconnect()
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error: Could not access channel: {e}", style="red bold")
        await client.disconnect()
        sys.exit(1)

    # Parse comments
    results = []
    start_time = time.time()
    posts_with_comments = 0

    try:
        posts = await client.get_messages(channel, limit=args.posts)

        for post in track(posts, description="Parsing posts..."):
            # Check if post has comments
            if post.replies and post.replies.replies > 0:
                posts_with_comments += 1

                if not args.quiet:
                    console.print(
                        f"Post #{post.id}: ✓ {post.replies.replies} comments",
                        style="green"
                    )

                try:
                    # Get comments for this post with retry logic
                    retries = 0
                    max_retries = 3

                    while retries < max_retries:
                        try:
                            comments = await client.get_messages(
                                channel,
                                reply_to=post.id,
                                limit=None
                            )
                            break
                        except FloodWaitError as e:
                            console.print(
                                f"⚠ Rate limit hit. Waiting {e.seconds} seconds...",
                                style="yellow"
                            )
                            await asyncio.sleep(e.seconds)
                            retries += 1

                    if retries == max_retries:
                        console.print(
                            f"⚠ Skipping post #{post.id} after {max_retries} retries",
                            style="yellow"
                        )
                        continue

                    # Extract user data from each comment
                    for comment in comments:
                        try:
                            user = await comment.get_sender()

                            # Skip bots and deleted accounts
                            if user and not user.bot:
                                results.append({
                                    'first_name': user.first_name or 'Unknown',
                                    'username': user.username or '-',
                                    'user_id': user.id,
                                    'comment_text': comment.text or ''
                                })
                        except Exception as e:
                            # Skip this comment if we can't get sender
                            if not args.quiet:
                                console.print(
                                    f"⚠ Could not get sender for comment: {e}",
                                    style="dim yellow"
                                )
                            continue

                    # Rate limiting protection
                    await asyncio.sleep(1)

                    # Extra delay for posts with many comments
                    if len(comments) > 100:
                        await asyncio.sleep(2)

                except Exception as e:
                    console.print(
                        f"⚠ Error parsing post #{post.id}: {e}",
                        style="yellow"
                    )
                    continue
            else:
                if not args.quiet:
                    console.print(f"Post #{post.id}: - no comments", style="dim")

        elapsed = time.time() - start_time
        console.print(
            f"\n⏱️  Completed in {elapsed:.0f} seconds\n",
            style="bold green"
        )

        # Deduplicate by user_id (keep first occurrence)
        seen_users = set()
        unique_results = []
        for row in results:
            if row['user_id'] not in seen_users:
                seen_users.add(row['user_id'])
                unique_results.append(row)

        bots_filtered = 0  # We already filter bots during parsing

        # Print summary
        summary = f"""╔══════════════════════════════════════════════════════════╗
║                    PARSING RESULTS                       ║
╠══════════════════════════════════════════════════════════╣
║ Total posts checked:        {len(posts):<28} ║
║ Posts with comments:        {posts_with_comments:<28} ║
║ Total comments found:       {len(results):<28} ║
║ Unique users collected:     {len(unique_results):<28} ║
║ Bots filtered out:          {bots_filtered:<28} ║
╚══════════════════════════════════════════════════════════╝"""

        console.print(summary, style="bold cyan")

        # Print results table
        if unique_results:
            table = Table(
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED
            )
            table.add_column("First Name", style="cyan", width=15)
            table.add_column("Username", style="green", width=15)
            table.add_column("User ID", style="yellow", width=12)
            table.add_column("Comment (first 50 chars)", style="white", width=35)

            display_count = len(unique_results) if args.show_all else min(10, len(unique_results))

            for row in unique_results[:display_count]:
                comment_preview = row['comment_text'][:50]
                if len(row['comment_text']) > 50:
                    comment_preview += '…'

                table.add_row(
                    row['first_name'],
                    row['username'],
                    str(row['user_id']),
                    comment_preview
                )

            console.print(table)

            if not args.show_all and len(unique_results) > 10:
                console.print(
                    f"\n💡 Showing first 10 of {len(unique_results)} users.",
                    style="dim"
                )
                console.print(
                    "   Run with --show-all to see all results\n",
                    style="dim"
                )
            else:
                console.print()  # Empty line for spacing
        else:
            console.print("\n⚠ No comments found\n", style="yellow")

        # Save to CSV
        if not args.no_csv and unique_results:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_dir = Path('./output')
            output_dir.mkdir(exist_ok=True)

            # Extract channel name from URL for filename
            channel_name = args.channel.split('/')[-1].replace('https://t.me/', '')
            filename = output_dir / f'{channel_name}_commenters_{timestamp}.csv'

            try:
                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=['first_name', 'username', 'user_id', 'comment_text'],
                        quoting=csv.QUOTE_MINIMAL
                    )
                    writer.writeheader()
                    writer.writerows(unique_results)

                console.print(
                    f"💾 Full data saved to: {filename}",
                    style="bold green"
                )
            except Exception as e:
                console.print(f"⚠ Could not save CSV file: {e}", style="yellow")

        # Print hints
        console.print("\n📝 Options:", style="bold")
        console.print("  --show-all    Show all users in terminal", style="dim")
        console.print("  --posts N     Parse N posts (default: 30)", style="dim")
        console.print("  --no-csv      Don't save CSV file", style="dim")
        console.print("  --quiet       Minimal output\n", style="dim")

    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red bold")
        raise
    finally:
        await client.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n⚠ Interrupted by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n❌ Fatal error: {e}", style="red bold")
        sys.exit(1)
