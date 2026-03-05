"""Email sender for LinkedIn posts using SendGrid."""
import os
from typing import Optional

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False


EMAIL_TEMPLATE = """Hoi {sme_name},

Er is een high-priority nieuwsbericht binnengekomen op jouw expertisegebied.
Hieronder vind je een concept LinkedIn-post die je direct kunt gebruiken of aanpassen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 BRONARTIEL
{article_title}
{article_url}
Score: {score}/100 | Tags: {tags}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 CONCEPT LINKEDIN-POST
(kopieer en plak in LinkedIn, pas aan waar nodig)

{post_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dit bericht is automatisch gegenereerd door Zorgnieuws.
Bekijk alle items: https://frankbrussaard.github.io/zorgnieuws/linkedin.html
"""


class EmailSender:
    """Send LinkedIn post concepts to SMEs via SendGrid."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: str = "zorgnieuws@accenture.com",
        max_emails_per_run: int = 10,
    ):
        self.api_key = api_key or os.environ.get("SENDGRID_API_KEY")
        self.from_email = from_email
        self.max_emails_per_run = max_emails_per_run

        if not HAS_SENDGRID:
            print("Warning: sendgrid package not installed. Emails will be skipped.")
            self.client = None
        elif not self.api_key:
            print("Warning: SENDGRID_API_KEY not set. Emails will be skipped.")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)

    def send_post_to_sme(self, post: dict) -> bool:
        """Send a LinkedIn post concept to the assigned SME."""
        if not self.client:
            print(f"  [SKIP] Would email {post.get('sme_name')} <{post.get('sme_email')}>")
            return False

        email_body = EMAIL_TEMPLATE.format(
            sme_name=post.get("sme_name", "Expert"),
            article_title=post.get("article_title", ""),
            article_url=post.get("article_url", ""),
            score=post.get("article_score", 0),
            tags=", ".join(post.get("article_tags", [])),
            post_text=post.get("post_text", ""),
        )

        message = Mail(
            from_email=Email(self.from_email, "Zorgnieuws"),
            to_emails=To(post.get("sme_email")),
            subject=f"🔴 LinkedIn-kans: {post.get('article_title', 'Nieuw artikel')[:50]}...",
            plain_text_content=Content("text/plain", email_body),
        )

        try:
            response = self.client.send(message)
            if response.status_code in [200, 201, 202]:
                print(f"  [SENT] Email to {post.get('sme_name')} <{post.get('sme_email')}>")
                return True
            else:
                print(f"  [ERROR] SendGrid returned {response.status_code}")
                return False
        except Exception as e:
            print(f"  [ERROR] Failed to send email: {e}")
            return False

    def send_posts(self, posts: list[dict]) -> list[dict]:
        """Send emails for all new posts, respecting rate limits."""
        sent_posts = []
        emails_sent = 0

        for post in posts:
            if emails_sent >= self.max_emails_per_run:
                print(f"  Rate limit reached ({self.max_emails_per_run} emails)")
                break

            if post.get("emailed"):
                continue

            if self.send_post_to_sme(post):
                post["emailed"] = True
                sent_posts.append(post)
                emails_sent += 1

        print(f"Sent {emails_sent} emails")
        return sent_posts
