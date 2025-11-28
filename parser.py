#!/usr/bin/env python3
"""
Telegram Comments Parser - CLI Interface
Uses parser_lib for core parsing logic
"""

import asyncio
import argparse
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich import box

from parser_lib import TelegramParser, save_to_csv

console = Console()


async def main():
    """Main CLI function"""

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
  python parser.py --keywords "купить,продать"  # Filter by keywords
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
    parser.add_argument('--keywords', type=str, default='',
                        help='Keywords to filter (comma-separated)')
    parser.add_argument('--keyword-mode', type=str, default='or', choices=['or', 'and'],
                        help='Keyword filter mode: "or" or "and" (default: or)')

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

    # Parse keywords
    keywords = []
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]

    # Initialize parser
    tg_parser = TelegramParser(api_id, api_hash, phone)

    # Status callback for non-quiet mode
    def status_callback(message: str):
        if not args.quiet:
            console.print(f"  {message}", style="dim")

    # Connect to Telegram
    console.print("\n📡 Connecting to Telegram...", style="yellow")
    try:
        await tg_parser.connect()
        console.print(f"✓ Authenticated as: {phone}", style="green bold")
    except Exception as e:
        console.print(f"❌ Authentication failed: {e}", style="red bold")
        sys.exit(1)

    # Display parsing parameters
    console.print(f"\n🎯 Target: {args.channel}", style="cyan")
    console.print(f"📊 Posts to check: {args.posts}", style="cyan")
    if keywords:
        console.print(f"🔍 Keywords: {', '.join(keywords)} (mode: {args.keyword_mode})", style="cyan")
    console.print()

    # Progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Parsing posts...", total=100)

        def progress_callback(percentage, current, total):
            progress.update(task, completed=percentage, description=f"Parsing posts... ({current}/{total})")

        # Parse channel
        result = await tg_parser.parse_channel(
            channel_url=args.channel,
            posts_limit=args.posts,
            keywords=keywords,
            keyword_mode=args.keyword_mode,
            progress_callback=progress_callback,
            status_callback=status_callback if not args.quiet else None
        )

    # Disconnect
    await tg_parser.disconnect()

    # Check result
    if not result['success']:
        console.print(f"\n❌ Error: {result.get('error', 'Unknown error')}", style="red bold")
        sys.exit(1)

    # Get results
    stats = result['stats']
    unique_results = result['unique_results']

    # Print completion
    console.print(
        f"\n⏱️  Completed in {stats['elapsed_time']:.0f} seconds\n",
        style="bold green"
    )

    # Print summary
    summary = f"""╔══════════════════════════════════════════════════════════╗
║                    PARSING RESULTS                       ║
╠══════════════════════════════════════════════════════════╣
║ Total posts checked:        {stats['posts_checked']:<28} ║
║ Posts with comments:        {stats['posts_with_comments']:<28} ║
║ Total comments found:       {stats['total_comments']:<28} ║"""

    if keywords:
        summary += f"""
║ Filtered comments:          {stats['filtered_comments']:<28} ║"""

    summary += f"""
║ Unique users collected:     {stats['unique_users']:<28} ║
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
        try:
            channel_name = args.channel.split('/')[-1].replace('https://t.me/', '')
            filename = save_to_csv(unique_results, channel_name=channel_name)
            console.print(
                f"💾 Full data saved to: {filename}",
                style="bold green"
            )
        except Exception as e:
            console.print(f"⚠ Could not save CSV file: {e}", style="yellow")

    # Print hints
    console.print("\n📝 Options:", style="bold")
    console.print("  --show-all           Show all users in terminal", style="dim")
    console.print("  --posts N            Parse N posts (default: 30)", style="dim")
    console.print("  --keywords \"word\"    Filter by keywords", style="dim")
    console.print("  --keyword-mode MODE  Keyword mode: 'or' or 'and'", style="dim")
    console.print("  --no-csv             Don't save CSV file", style="dim")
    console.print("  --quiet              Minimal output\n", style="dim")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n⚠ Interrupted by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n❌ Fatal error: {e}", style="red bold")
        sys.exit(1)
