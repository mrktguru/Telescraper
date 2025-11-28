"""
Telegram Comments Parser Library
Core parsing logic that can be used by CLI and Web interface
"""

import asyncio
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError


class TelegramParser:
    """Telegram Comments Parser - main parsing logic"""

    def __init__(self, api_id: str, api_hash: str, phone: str):
        """
        Initialize parser with Telegram credentials

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone: Phone number for authentication
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None

    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        await self.client.start(self.phone)
        return True

    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()

    async def parse_channel(
        self,
        channel_url: str,
        posts_limit: int = 30,
        keywords: Optional[List[str]] = None,
        keyword_mode: str = 'or',
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Parse comments from Telegram channel

        Args:
            channel_url: Channel URL (e.g., https://t.me/okkosport)
            posts_limit: Number of posts to parse
            keywords: List of keywords to filter (optional)
            keyword_mode: 'or' or 'and' - how to combine keywords
            progress_callback: Callback for progress updates (percentage, current, total)
            status_callback: Callback for status messages

        Returns:
            Dict with results:
            {
                'success': bool,
                'results': List[Dict],
                'unique_results': List[Dict],
                'stats': {
                    'posts_checked': int,
                    'posts_with_comments': int,
                    'total_comments': int,
                    'unique_users': int,
                    'filtered_comments': int,
                    'elapsed_time': float
                },
                'error': str (if failed)
            }
        """
        start_time = time.time()
        results = []
        posts_with_comments = 0
        skipped_bots = 0
        skipped_errors = 0

        try:
            # Get channel entity
            if status_callback:
                status_callback(f"Getting channel: {channel_url}")

            try:
                channel = await self.client.get_entity(channel_url)
            except ChannelPrivateError:
                return {
                    'success': False,
                    'error': 'Channel is private or you are not subscribed'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Could not access channel: {str(e)}'
                }

            # Get channel username for building post URLs
            channel_username = getattr(channel, 'username', None)
            if not channel_username:
                # Try to extract from URL
                channel_username = channel_url.rstrip('/').split('/')[-1]

            # Get posts
            if status_callback:
                status_callback(f"Fetching {posts_limit} posts...")

            posts = await self.client.get_messages(channel, limit=posts_limit)
            total_posts = len(posts)

            # Parse each post
            for idx, post in enumerate(posts):
                current_progress = int((idx + 1) / total_posts * 100)

                if progress_callback:
                    progress_callback(current_progress, idx + 1, total_posts)

                # Check if post has comments
                if post.replies and post.replies.replies > 0:
                    posts_with_comments += 1

                    if status_callback:
                        status_callback(f"Post #{post.id}: {post.replies.replies} comments")

                    try:
                        # Get comments with retry logic
                        retries = 0
                        max_retries = 3

                        while retries < max_retries:
                            try:
                                # Get all comments (Telegram API limit is ~100 per request by default)
                                # Using limit=10000 to get all comments in one request
                                # For posts with more comments, consider using iter_messages
                                comments = await self.client.get_messages(
                                    channel,
                                    reply_to=post.id,
                                    limit=10000
                                )
                                break
                            except FloodWaitError as e:
                                if status_callback:
                                    status_callback(f"Rate limit. Waiting {e.seconds}s...")
                                await asyncio.sleep(e.seconds)
                                retries += 1

                        if retries == max_retries:
                            if status_callback:
                                status_callback(f"Skipping post #{post.id} after retries")
                            continue

                        # Log comment count
                        expected_comments = post.replies.replies
                        received_comments = len(comments)
                        if status_callback and received_comments < expected_comments:
                            status_callback(
                                f"⚠ Post #{post.id}: got {received_comments}/{expected_comments} comments"
                            )

                        # Extract user data from each comment
                        for comment in comments:
                            try:
                                user = await comment.get_sender()

                                # Skip bots and deleted accounts
                                if user and not user.bot:
                                    # Build post URL
                                    post_url = f"https://t.me/{channel_username}/{post.id}"

                                    comment_data = {
                                        'first_name': user.first_name or 'Unknown',
                                        'username': user.username or '-',
                                        'user_id': user.id,
                                        'comment_text': comment.text or '',
                                        'post_id': post.id,
                                        'comment_id': comment.id,
                                        'post_url': post_url,
                                        'date': comment.date.isoformat() if comment.date else None
                                    }
                                    results.append(comment_data)
                                elif user and user.bot:
                                    # Count skipped bots
                                    skipped_bots += 1
                            except Exception:
                                # Count errors when getting sender
                                skipped_errors += 1
                                continue

                        # Rate limiting protection
                        await asyncio.sleep(1)

                        # Extra delay for posts with many comments
                        if len(comments) > 100:
                            await asyncio.sleep(2)

                    except Exception as e:
                        if status_callback:
                            status_callback(f"Error parsing post #{post.id}: {str(e)}")
                        continue
                else:
                    if status_callback:
                        status_callback(f"Post #{post.id}: no comments")

            elapsed = time.time() - start_time

            # Filter by keywords if provided
            filtered_results = results
            if keywords and len(keywords) > 0:
                if status_callback:
                    status_callback("Filtering by keywords...")
                filtered_results = filter_by_keywords(results, keywords, keyword_mode)

            # Deduplicate by user_id (keep first occurrence)
            seen_users = set()
            unique_results = []
            for row in filtered_results:
                if row['user_id'] not in seen_users:
                    seen_users.add(row['user_id'])
                    unique_results.append(row)

            return {
                'success': True,
                'results': filtered_results,
                'unique_results': unique_results,
                'stats': {
                    'posts_checked': total_posts,
                    'posts_with_comments': posts_with_comments,
                    'total_comments': len(results),
                    'filtered_comments': len(filtered_results),
                    'unique_users': len(unique_results),
                    'skipped_bots': skipped_bots,
                    'skipped_errors': skipped_errors,
                    'elapsed_time': elapsed
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }


def filter_by_keywords(
    comments: List[Dict],
    keywords: List[str],
    mode: str = 'or'
) -> List[Dict]:
    """
    Filter comments by keywords with morphology support

    Args:
        comments: List of comment dictionaries
        keywords: List of keywords to search for
        mode: 'or' (any keyword) or 'and' (all keywords)

    Returns:
        Filtered list of comments
    """
    if not keywords:
        return comments

    # Try to use pymorphy2 for Russian morphology
    try:
        import pymorphy2
        morph = pymorphy2.MorphAnalyzer()
        use_morphology = True
    except ImportError:
        use_morphology = False

    def get_word_forms(word: str) -> set:
        """Get all morphological forms of a word"""
        if not use_morphology:
            return {word.lower()}

        try:
            parsed = morph.parse(word)[0]
            forms = set()
            for form in parsed.lexeme:
                forms.add(form.word.lower())
            return forms
        except Exception:
            return {word.lower()}

    # Generate all forms for all keywords
    keyword_forms = []
    for keyword in keywords:
        keyword = keyword.strip()
        if keyword:
            forms = get_word_forms(keyword)
            keyword_forms.append(forms)

    if not keyword_forms:
        return comments

    # Filter comments
    filtered = []
    for comment in comments:
        text = comment.get('comment_text', '').lower()

        if mode == 'or':
            # Check if ANY keyword (or its forms) is in text
            found = False
            for forms in keyword_forms:
                if any(form in text for form in forms):
                    found = True
                    break
            if found:
                filtered.append(comment)

        elif mode == 'and':
            # Check if ALL keywords (or their forms) are in text
            all_found = True
            for forms in keyword_forms:
                if not any(form in text for form in forms):
                    all_found = False
                    break
            if all_found:
                filtered.append(comment)

    return filtered


def save_to_csv(
    results: List[Dict],
    output_dir: str = './output',
    channel_name: str = 'channel',
    timestamp: Optional[str] = None
) -> str:
    """
    Save results to CSV file

    Args:
        results: List of comment dictionaries
        output_dir: Output directory path
        channel_name: Channel name for filename
        timestamp: Custom timestamp (optional)

    Returns:
        Path to created CSV file
    """
    if not timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    filename = output_path / f'{channel_name}_commenters_{timestamp}.csv'

    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['first_name', 'username', 'user_id', 'comment_text', 'post_url'],
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()

        for row in results:
            writer.writerow({
                'first_name': row['first_name'],
                'username': row['username'],
                'user_id': row['user_id'],
                'comment_text': row['comment_text'],
                'post_url': row.get('post_url', '')
            })

    return str(filename)


def save_to_json(
    results: List[Dict],
    output_dir: str = './output',
    channel_name: str = 'channel',
    timestamp: Optional[str] = None
) -> str:
    """
    Save results to JSON file

    Args:
        results: List of comment dictionaries
        output_dir: Output directory path
        channel_name: Channel name for filename
        timestamp: Custom timestamp (optional)

    Returns:
        Path to created JSON file
    """
    import json

    if not timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    filename = output_path / f'{channel_name}_commenters_{timestamp}.json'

    # Convert datetime objects to strings
    json_results = []
    for row in results:
        json_row = dict(row)
        if 'date' in json_row:
            json_row['date'] = str(json_row['date'])
        json_results.append(json_row)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, ensure_ascii=False, indent=2)

    return str(filename)
