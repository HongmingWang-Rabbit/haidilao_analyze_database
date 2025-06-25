#!/usr/bin/env python3
"""
Simple QBI Test - Minimal test with better error handling
"""

import sys
import os
import time
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simple_qbi_test():
    """Simple test of QBI scraper"""
    
    # Get credentials
    username = os.getenv('QBI_USERNAME')
    password = os.getenv('QBI_PASSWORD')
    
    if not username or not password:
        print("❌ QBI credentials not found in environment variables")
        return False
    
    print("🚀 Simple QBI Test")
    print("=" * 30)
    print(f"👤 Username: {username}")
    print(f"🔐 Password: {'*' * len(password)}")
    print()
    
    try:
        from qbi_scraper import QBIScraper
        
        # Create scraper with shorter timeout
        print("📦 Creating QBI scraper...")
        scraper = QBIScraper(headless=True, timeout=30)
        
        # Test the scraper
        print("🔍 Testing QBI scraper...")
        result = scraper.scrape_data(
            username=username,
            password=password,
            target_date="2025-01-15"
        )
        
        if result:
            print(f"✅ Success! Downloaded: {result}")
            
            # Check file size
            file_path = Path(result)
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"📁 File size: {size} bytes")
                
                if size > 1000:  # More than 1KB suggests real data
                    print("✅ File appears to contain data")
                    return True
                else:
                    print("⚠️  File is very small, might be empty or error file")
                    return False
            else:
                print("❌ File not found")
                return False
        else:
            print("❌ Scraping failed")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = simple_qbi_test()
    sys.exit(0 if success else 1) 