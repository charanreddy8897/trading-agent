"""
Create the single admin user.

Run once after first deploy:
  cd backend
  python -m scripts.seed_user --username charan --password "your-strong-password"

Then on first login:
  1. POST /auth/login  → get temp_token
  2. GET  /auth/totp-setup?temp_token=...  → scan QR with Google Authenticator
  3. POST /auth/totp-setup  → verify code → get access + refresh tokens
"""
from __future__ import annotations

import argparse
import sys

sys.path.insert(0, ".")

from app.core.database import init_db, managed_session
from app.auth.service import auth_service
from app.core.exceptions import ConfigurationError


def main():
    parser = argparse.ArgumentParser(description="Seed the trading agent admin user")
    parser.add_argument("--username", required=True, help="Login username")
    parser.add_argument("--password", required=True, help="Login password (min 12 chars)")
    args = parser.parse_args()

    if len(args.password) < 12:
        print("ERROR: Password must be at least 12 characters")
        sys.exit(1)

    init_db()

    try:
        with managed_session() as db:
            user = auth_service.create_user(db, args.username, args.password)
            print(f"\n✓ User '{user.username}' created (id={user.id})")
            print("\nNext steps:")
            print("  1. Start the backend: uvicorn app.main:app --reload")
            print("  2. POST /auth/login  →  get temp_token")
            print("  3. GET  /auth/totp-setup?temp_token=<token>  →  scan QR code")
            print("  4. POST /auth/totp-setup  →  verify + get JWT tokens\n")
    except ConfigurationError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
