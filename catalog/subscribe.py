"""Newsletter-style phone subscriptions.

The endpoint validates the number (cheap, in the request) and answers 202 immediately; the database
write happens on a small background thread pool so the visitor never waits on the DB round-trip.
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor

from django.db import connection

from .models import Subscriber

log = logging.getLogger(__name__)
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="subscribe")

DIAL_RE = re.compile(r"^\+[1-9]\d{0,3}$")


def normalize(dial: str, number: str):
    """Return (e164, dial) or raise ValueError. Accepts '0501234567' / '50 123 4567' style input."""
    dial = "+" + re.sub(r"\D", "", dial or "")
    if not DIAL_RE.match(dial):
        raise ValueError("country_code")
    national = re.sub(r"\D", "", number or "").lstrip("0")
    digits = dial[1:] + national
    if not 8 <= len(digits) <= 15 or len(national) < 5:
        raise ValueError("phone")
    return "+" + digits, dial


def store(phone, dial, country="", language="", source=""):
    """Idempotent write; re-subscribing an unsubscribed number re-activates it."""
    try:
        obj, created = Subscriber.objects.get_or_create(
            phone=phone, defaults={"country_code": dial, "country": country, "language": language, "source": source}
        )
        if not created and not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=["is_active"])
    except Exception:  # never let a background failure vanish silently
        log.exception("could not store subscriber %s", phone[:6])


def _run(*args, **kwargs):
    # Pool threads own their DB connection: release it so it never lingers past the task.
    try:
        store(*args, **kwargs)
    finally:
        connection.close()


def submit(*args, **kwargs):
    return _pool.submit(_run, *args, **kwargs)
