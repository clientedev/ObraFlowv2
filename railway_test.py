#!/usr/bin/env python3
"""
Railway deployment test script
Checks if the application is configured correctly for Railway
"""
import os
import sys

def test_railway_config():
    """Test Railway-specific configuration"""
    print("🚂 Testing Railway Configuration...")
    
    # Check for required environment variables
    port = os.environ.get('PORT', '5000')
    database_url = os.environ.get('DATABASE_URL', 'not_set')
    
    print(f"✓ PORT: {port}")
    print(f"✓ DATABASE_URL: {'✓ Configured' if database_url != 'not_set' else '❌ Not set'}")
    
    # Test app import
    try:
        from app import app
        print("✓ Flask app imports successfully")
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    
    # Test database connection (basic check)
    try:
        from app import db
        print("✓ Database configuration loaded")
    except Exception as e:
        print(f"❌ Database configuration failed: {e}")
        return False
    
    print("🎉 Railway configuration looks good!")
    return True

if __name__ == "__main__":
    success = test_railway_config()
    sys.exit(0 if success else 1)