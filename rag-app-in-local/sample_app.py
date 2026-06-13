"""A tiny banking app — this is the codebase our RAG tool will answer questions about."""

import hashlib


def hash_password(password: str) -> str:
    """Hash a user's password with SHA-256 before storing it."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str, users: dict) -> bool:
    """Check a login attempt. Returns True if the username exists and the
    hashed password matches what we have on record."""
    if username not in users:
        return False
    return users[username] == hash_password(password)


def transfer_funds(sender: dict, receiver: dict, amount: float) -> bool:
    """Move money from sender to receiver. Refuses if the sender has
    insufficient balance or the amount is not positive."""
    if amount <= 0:
        return False
    if sender["balance"] < amount:
        return False
    sender["balance"] -= amount
    receiver["balance"] += amount
    return True


def calculate_interest(principal: float, rate: float, years: int) -> float:
    """Compound interest, compounded annually."""
    return principal * ((1 + rate) ** years)


def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"
    """Format a number as USD for display."""