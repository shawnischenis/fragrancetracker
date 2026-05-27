import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

from dotenv import dotenv_values, load_dotenv

load_dotenv()

RESEND_ENDPOINT = "https://api.resend.com/emails"
DEFAULT_FROM_EMAIL = "The Scent Index <onboarding@resend.dev>"


def _resend_api_key():
    env_values = dotenv_values(".env")
    return (
        os.getenv("RESEND_API_KEY")
        or os.getenv("RESEND_API")
        or env_values.get("RESEND_API_KEY")
        or env_values.get("RESEND_API")
        or env_values.get("RESEND_API ")
    )


def send_email(to_email, subject, html, text=None, idempotency_key=None):
    api_key = _resend_api_key()
    if not api_key:
        raise ValueError("RESEND_API_KEY or RESEND_API must be set")

    payload = {
        "from": os.getenv("RESEND_FROM_EMAIL", DEFAULT_FROM_EMAIL),
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    if text is not None:
        payload["text"] = text

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "fragrancetracker/0.1",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"Resend email failed with HTTP {exc.code}: {body}") from exc


def send_test_email(to_email):
    sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return send_email(
        to_email=to_email,
        subject="The Scent Index alert test",
        html=(
            "<h1>The Scent Index</h1>"
            "<p>Your Resend integration is working.</p>"
            f"<p>Sent at {sent_at}.</p>"
        ),
        text=f"The Scent Index Resend integration is working. Sent at {sent_at}.",
        idempotency_key=f"test-email:{to_email}:{sent_at}",
    )


if __name__ == "__main__":
    to = os.getenv("ALERT_TEST_EMAIL", "shawnistaobao@gmail.com")
    print(send_test_email(to))
