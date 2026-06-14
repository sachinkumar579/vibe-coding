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
    """Format a number as USD for display."""
    return f"${amount:,.2f}"


def open_account(name: str, opening_deposit: float) -> dict:
    """Open a new account. Requires a minimum opening deposit of $100."""
    if opening_deposit < 100:
        raise ValueError("Opening deposit must be at least $100")
    return {"owner": name, "balance": opening_deposit, "frozen": False}


def withdraw(account: dict, amount: float) -> bool:
    """Withdraw cash from an account. Refuses if the account is frozen,
    the amount is not positive, or there are insufficient funds."""
    if account["frozen"]:
        return False
    if amount <= 0 or account["balance"] < amount:
        return False
    account["balance"] -= amount
    return True


def freeze_account(account: dict, reason: str) -> dict:
    """Flag an account as frozen so no withdrawals or transfers can occur."""
    account["frozen"] = True
    account["freeze_reason"] = reason
    return account
