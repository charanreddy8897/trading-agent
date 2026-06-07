"""
Reset password for existing user.

Usage:
  python -m scripts.reset_password --username charan --password "new-password"
"""
import argparse
import sys
sys.path.insert(0, ".")

from app.core.database import managed_session
from app.auth.service import auth_service
from app.models.db_models import User


def main():
    parser = argparse.ArgumentParser(description="Reset user password")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="New password")
    args = parser.parse_args()

    with managed_session() as db:
        user = db.query(User).filter(User.username == args.username).first()
        if not user:
            print(f"ERROR: User '{args.username}' not found")
            sys.exit(1)

        # Reset password and TOTP
        user.hashed_password = auth_service._hash_password(args.password)
        user.totp_enabled = False
        user.totp_secret = None
        user.backup_codes = None
        db.commit()

        print(f"\n✓ Password reset for user '{user.username}'")
        print("✓ TOTP disabled — you'll need to set it up again on first login\n")


if __name__ == "__main__":
    main()
