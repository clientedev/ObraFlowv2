#!/usr/bin/env python3
"""
Test connection to Railway database and verify reports functionality
"""

import os
import sys
import logging

# Set the Railway database URL directly
os.environ['DATABASE_URL'] = "postgresql://postgres:KgyYkEmMztCNMSPHVbOpWLTiKZFXYwpB@switchback.proxy.rlwy.net:17107/railway"

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Projeto, Relatorio
from datetime import datetime

def test_railway_reports():
    """Test connection to Railway database and verify reports"""
    
    with app.app_context():
        print("🚂 Testing Railway Database Connection")
        print("=" * 50)
        
        try:
            # Test basic connection
            result = db.session.execute(db.text('SELECT 1')).scalar()
            print(f"✅ Database connection successful: {result}")
            
            # Check data counts
            users_count = User.query.count()
            projects_count = Projeto.query.count()
            reports_count = Relatorio.query.count()
            
            print(f"📊 Railway Database Data:")
            print(f"   Users: {users_count}")
            print(f"   Projects: {projects_count}")
            print(f"   Reports: {reports_count}")
            print()
            
            if reports_count > 0:
                print("📋 Testing Reports Query (simulating /reports route):")
                
                # Test the exact query from the reports route
                try:
                    relatorios = Relatorio.query.order_by(Relatorio.created_at.desc()).limit(50).all()
                    print(f"✅ Successfully loaded {len(relatorios)} reports")
                    
                    print("📄 Sample Reports:")
                    for i, report in enumerate(relatorios[:5]):  # Show first 5
                        print(f"   {i+1}. {report.numero}: {report.titulo} (Status: {report.status})")
                        print(f"      Project: {report.projeto.nome if report.projeto else 'N/A'}")
                        print(f"      Author: {report.autor.username if report.autor else 'N/A'}")
                        print(f"      Created: {report.created_at}")
                        print()
                        
                    return True
                        
                except Exception as e:
                    print(f"❌ Error querying reports: {e}")
                    return False
            else:
                print("ℹ️ No reports found in database")
                return True
                
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

if __name__ == "__main__":
    success = test_railway_reports()
    if success:
        print("🎉 Railway database test completed successfully!")
    else:
        print("💥 Railway database test failed!")
        sys.exit(1)