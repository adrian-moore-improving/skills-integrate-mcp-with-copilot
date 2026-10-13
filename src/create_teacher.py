"""Provision a teacher account in teachers.json."""

import json
import sys
from getpass import getpass

from app import TEACHERS_FILE, hash_password


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise SystemExit("Usage: python create_teacher.py <username>")

    username = sys.argv[1].strip()
    password = getpass("Teacher password: ")
    confirmation = getpass("Confirm password: ")
    if not password:
        raise SystemExit("Password cannot be empty")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    with TEACHERS_FILE.open(encoding="utf-8") as credentials_file:
        credentials = json.load(credentials_file)

    credentials.setdefault("teachers", {})[username] = hash_password(password)
    temporary_file = TEACHERS_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(
        json.dumps(credentials, indent=2) + "\n", encoding="utf-8"
    )
    temporary_file.replace(TEACHERS_FILE)
    print(f"Provisioned teacher {username!r} in {TEACHERS_FILE}")


if __name__ == "__main__":
    main()
