#!/usr/bin/env python3
"""
Simple test to verify database connection works
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for database connection
os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_USER'] = 'hongming'
os.environ['PG_PASSWORD'] = '8894'
os.environ['PG_DATABASE'] = 'haidilao-paperwork'

try:
    from utils.database import DatabaseManager, DatabaseConfig
    print("✅ Successfully imported database utilities")

    # Test database connection
    config = DatabaseConfig(is_test=True)
    print(f"✅ Database config created: {config}")

    db_manager = DatabaseManager(config)
    print("✅ Database manager created")

    # Test connection
    if db_manager.test_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
