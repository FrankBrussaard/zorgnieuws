#!/usr/bin/env python3
"""Generate LinkedIn posts and send emails to SMEs."""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from linkedin.post_generator import LinkedInPostGenerator
from linkedin.email_sender import EmailSender


def run_linkedin():
    """Generate LinkedIn posts for high-priority articles and email SMEs."""
    data_dir = project_root / "data"
    scored_file = data_dir / "scored.json"

    # Load scored articles
    if not scored_file.exists():
        print("No scored.json found. Run scorer first.")
        return

    with open(scored_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Loaded {len(articles)} scored articles")
    print()

    # Generate LinkedIn posts
    print("=" * 60)
    print("LinkedIn Post Generation")
    print("=" * 60)

    try:
        generator = LinkedInPostGenerator(
            owners_path=str(project_root / "config" / "owners.json"),
            posts_path=str(data_dir / "linkedin_posts.json"),
        )
        new_posts = generator.generate_posts(articles)
    except Exception as e:
        print(f"Error generating posts: {e}")
        new_posts = []

    if not new_posts:
        print("No new LinkedIn posts to generate.")
        return

    # Send emails
    print()
    print("=" * 60)
    print("Sending Emails to SMEs")
    print("=" * 60)

    sender = EmailSender()
    sender.send_posts(new_posts)

    # Update posts file with email status
    posts_file = data_dir / "linkedin_posts.json"
    if posts_file.exists():
        with open(posts_file, "r", encoding="utf-8") as f:
            all_posts = json.load(f)
        with open(posts_file, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Generated {len(new_posts)} new LinkedIn posts")

    for post in new_posts:
        status = "[+] emailed" if post.get("emailed") else "[ ] pending"
        print(f"  {status} {post['sme_name']}: {post['article_title'][:40]}...")


if __name__ == "__main__":
    run_linkedin()
