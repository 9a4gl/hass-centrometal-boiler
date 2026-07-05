from __future__ import annotations

import hashlib


def redact_account(account: str | None) -> str:
    """Return a stable non-reversible account identifier for logs."""
    if not account:
        return "account-unknown"
    digest = hashlib.sha256(account.encode()).hexdigest()[:8]
    return f"account-{digest}"
