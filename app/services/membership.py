"""Membership status derived from the expiry date (v3.1.2 / v3.2.4 concept)."""
from datetime import date


def membership_status(expiry, today=None):
    if not expiry:
        return "No membership"
    today = today or date.today()
    days_left = (date.fromisoformat(expiry) - today).days
    if days_left < 0:
        return "Expired"
    if days_left <= 14:
        return "Expiring soon"
    return "Active"
