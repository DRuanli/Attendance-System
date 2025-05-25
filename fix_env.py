#!/usr/bin/env python
# fix_env.py - Fix .env file to match current settings

import os
import shutil
from datetime import datetime


def fix_env_file():
    """Fix .env file by removing old settings and using correct ones."""

    # Check if .env exists
    if os.path.exists('.env'):
        # Backup existing .env
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✅ Backed up existing .env to {backup_name}")

        # Remove the problematic .env
        os.remove('.env')
        print("🗑️  Removed old .env file")

    # Copy .env.example to .env
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✅ Created new .env from .env.example")
        print("⚠️  Please update the SECRET_KEY in .env with a secure value")
    else:
        # Create a minimal .env file
        with open('.env', 'w') as f:
            f.write("""# Minimal configuration
APP_NAME="Classroom Attendance System"
DEBUG=True
SECRET_KEY=change-this-to-a-secure-key
DATABASE_URL=sqlite:///./attendance.db
""")
        print("✅ Created minimal .env file")

    print("\n✨ Environment file fixed!")
    print("You can now run: python run.py")


if __name__ == "__main__":
    fix_env_file()