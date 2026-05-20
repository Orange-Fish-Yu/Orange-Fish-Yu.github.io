#!/usr/bin/env python3
"""
Sync Obsidian blog posts to Jekyll _posts directory.

Usage:
    python sync_blog.py <path-to-obsidian-md> [--tags tag1,tag2] [--no-push]
    
Examples:
    python sync_blog.py "/Users/zicheng/Documents/Notes/Ambition/Blogs/数学写作的历史惯性.md"
    python sync_blog.py "/path/to/blog.md" --tags "writing,math"
    python sync_blog.py "/path/to/blog.md" --no-push
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Configuration
JEKYLL_ROOT = Path(__file__).parent
POSTS_DIR = JEKYLL_ROOT / "_posts"


def read_file(filepath):
    """Read file content."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def write_file(filepath, content):
    """Write content to file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def parse_front_matter(content):
    """Parse YAML front matter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if match:
        front_matter_str = match.group(1)
        body = match.group(2)
        
        # Simple YAML parser for front matter
        front_matter = {}
        current_key = None
        current_list = None
        
        for line in front_matter_str.split("\n"):
            line = line.rstrip()
            
            # Check for list item
            if line.startswith("  - ") and current_key:
                if current_list is None:
                    current_list = []
                item = line[4:].strip().strip('"').strip("'")
                # Remove # prefix from tags
                if item.startswith("#"):
                    item = item[1:]
                current_list.append(item)
            else:
                # Save previous list if exists
                if current_list is not None and current_key:
                    front_matter[current_key] = current_list
                    current_list = None
                
                # Parse key: value
                match_kv = re.match(r"^(\w+):\s*(.*)$", line)
                if match_kv:
                    current_key = match_kv.group(1)
                    value = match_kv.group(2).strip().strip('"').strip("'")
                    if value:
                        front_matter[current_key] = value
                        current_key = None
                    # If no value, it might be a list (next lines)
        
        # Save last list if exists
        if current_list is not None and current_key:
            front_matter[current_key] = current_list
        
        return front_matter, body
    
    return {}, content


def extract_title_from_content(content):
    """Extract title from first H1 heading or filename."""
    # Try to find H1 heading
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    return None


def slugify(text):
    """Convert text to URL-friendly slug."""
    # Keep Chinese characters and alphanumeric
    text = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text


def convert_obsidian_syntax(content):
    """Convert Obsidian-specific markdown to standard markdown."""
    # Convert ![[image.png|size]] to ![](image.png)  (Obsidian wiki link format)
    content = re.sub(
        r"!\[\[([^|\]]+?)(?:\|\d+)?\]\]",
        r"![](\1)",
        content
    )
    
    # Convert ![image.png|size](url) to ![image.png](url)  (standard markdown with size hint)
    content = re.sub(
        r"!\[([^\]]+?)\|\d+\]\(",
        r"![\1](",
        content
    )
    
    # Convert [[wikilink]] to [wikilink](wikilink)
    content = re.sub(
        r"\[\[([^\]]+?)\]\]",
        r"[\1](\1)",
        content
    )
    
    return content


def generate_front_matter(title, date, tags=None):
    """Generate Jekyll front matter."""
    lines = [
        "---",
        "layout: post",
        f'title: "{title}"',
        f"date: {date}",
    ]
    
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")
    
    lines.append("---")
    return "\n".join(lines)


def sync_blog(source_path, extra_tags=None, no_push=False):
    """Sync a blog post from Obsidian to Jekyll."""
    source_path = Path(source_path)
    
    if not source_path.exists():
        print(f"Error: File not found: {source_path}")
        sys.exit(1)
    
    # Read source file
    content = read_file(source_path)
    
    # Parse front matter
    front_matter, body = parse_front_matter(content)
    
    # Extract date
    date_str = front_matter.get("date", "")
    if date_str:
        try:
            if isinstance(date_str, str):
                date = datetime.strptime(str(date_str), "%Y-%m-%d")
            else:
                date = datetime.combine(date_str, datetime.min.time())
        except ValueError:
            date = datetime.now()
    else:
        date = datetime.now()
    
    # Extract title
    title = front_matter.get("title") or extract_title_from_content(body) or source_path.stem
    
    # Extract tags
    tags = front_matter.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    if extra_tags:
        tags.extend(extra_tags)
    
    # Convert Obsidian syntax
    body = convert_obsidian_syntax(body)
    
    # Generate filename
    slug = slugify(title)
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    dest_path = POSTS_DIR / filename
    
    # Generate front matter
    front_matter_str = generate_front_matter(title, date.strftime("%Y-%m-%d"), tags)
    
    # Combine front matter and body
    final_content = f"{front_matter_str}\n\n{body.lstrip()}"
    
    # Ensure _posts directory exists
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write to _posts
    write_file(dest_path, final_content)
    print(f"Synced: {dest_path.relative_to(JEKYLL_ROOT)}")
    
    # Git operations
    if not no_push:
        try:
            # Git add
            subprocess.run(
                ["git", "add", str(dest_path.relative_to(JEKYLL_ROOT))],
                cwd=JEKYLL_ROOT,
                check=True,
                capture_output=True
            )
            
            # Git commit
            commit_msg = f"Add blog post: {title}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=JEKYLL_ROOT,
                check=True,
                capture_output=True
            )
            
            # Git push
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=JEKYLL_ROOT,
                check=True,
                capture_output=True
            )
            
            print("Pushed to GitHub. Blog will be live in ~1-2 minutes.")
            
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e.stderr.decode() if e.stderr else str(e)}")
        except FileNotFoundError:
            print("Note: git not found. Please commit and push manually.")
    
    return dest_path


def main():
    parser = argparse.ArgumentParser(
        description="Sync Obsidian blog posts to Jekyll _posts directory"
    )
    parser.add_argument(
        "source",
        help="Path to the Obsidian markdown file"
    )
    parser.add_argument(
        "--tags",
        help="Additional tags (comma-separated)",
        default=None
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip git push"
    )
    
    args = parser.parse_args()
    
    # Parse extra tags
    extra_tags = None
    if args.tags:
        extra_tags = [t.strip() for t in args.tags.split(",")]
    
    # Sync blog
    dest = sync_blog(args.source, extra_tags, args.no_push)
    print(f"Done! Blog post saved to: {dest}")


if __name__ == "__main__":
    main()
