"""
sample_log_generator.py
-----------------------
Generates a realistic app.log file with mixed log levels.
Run this once to create sample data before running the agent.
"""

import random
import time
from datetime import datetime, timedelta

LOG_FILE = "app.log"

log_templates = {
    "INFO": [
        "User {user_id} logged in successfully",
        "GET /api/products returned 200 in {ms}ms",
        "Scheduled job 'cleanup_temp_files' completed",
        "Cache warmed up: {count} entries loaded",
        "POST /api/orders returned 201 in {ms}ms",
    ],
    "WARNING": [
        "Response time exceeded threshold: {ms}ms for GET /api/reports",
        "Memory usage at {pct}% — approaching limit",
        "Retry attempt {n}/3 for payment gateway",
        "Deprecated API endpoint /v1/users called by {user_id}",
        "DB connection pool at {pct}% capacity",
    ],
    "ERROR": [
        "NullPointerException in OrderService.processOrder() line 142",
        "Database connection timeout after {ms}ms",
        "Failed to send email to {user_id}: SMTP connection refused",
        "Unhandled exception in /api/checkout: KeyError 'cart_id'",
        "Redis connection lost — falling back to DB",
    ],
    "CRITICAL": [
        "DISK FULL: /var/data has 0 bytes remaining",
        "Database primary node unreachable — all writes failing",
        "Out of memory: Kill process or sacrifice child",
        "SSL certificate expired for api.example.com",
        "Payment service DOWN: 500 errors for last 5 minutes",
    ],
}


def generate_log_line(level: str, timestamp: datetime) -> str:
    template = random.choice(log_templates[level])
    message = template.format(
        user_id=f"user_{random.randint(1000, 9999)}",
        ms=random.randint(100, 9000),
        count=random.randint(100, 5000),
        pct=random.randint(70, 99),
        n=random.randint(1, 3),
    )
    ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{ts}] [{level}] {message}\n"


def generate_log_file(num_lines: int = 60):
    now = datetime.now()
    with open(LOG_FILE, "w") as f:
        for i in range(num_lines):
            timestamp = now - timedelta(minutes=num_lines - i)
            # Weighted: mostly INFO, some WARN/ERROR, rare CRITICAL
            level = random.choices(
                ["INFO", "WARNING", "ERROR", "CRITICAL"],
                weights=[60, 20, 15, 5],
            )[0]
            f.write(generate_log_line(level, timestamp))

    print(f"✅ Generated {num_lines} log lines → {LOG_FILE}")


if __name__ == "__main__":
    generate_log_file(60)
