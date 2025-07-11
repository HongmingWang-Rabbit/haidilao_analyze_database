#!/usr/bin/env python3
"""
Check dish table structure
"""

from utils.database import DatabaseManager, DatabaseConfig
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ['PG_HOST'] = 'localhost'
os.environ['PG_PORT'] = '5432'
os.environ['PG_USER'] = 'hongming'
os.environ['PG_PASSWORD'] = '8894'
os.environ['PG_DATABASE'] = 'haidilao-paperwork'


config = DatabaseConfig(is_test=True)
db_manager = DatabaseManager(config)

with db_manager.get_connection() as conn:
    cursor = conn.cursor()

    # Check dish table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'dish' 
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()
    print('🍽️ DISH TABLE STRUCTURE:')
    for col in columns:
        print(
            f'  {col["column_name"]} ({col["data_type"]}) - Nullable: {col["is_nullable"]}')

    # Check sample dish data
    cursor.execute("SELECT * FROM dish LIMIT 3")
    dishes = cursor.fetchall()
    print('\n📊 SAMPLE DISH DATA:')
    for dish in dishes:
        print(
            f'  ID: {dish["id"]}, Code: {dish["full_code"]}, Name: {dish["name"]}')
