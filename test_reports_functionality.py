#!/usr/bin/env python3
"""
Test script to verify reports functionality by creating sample data
"""

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Projeto, Relatorio
from datetime import datetime

def test_reports_functionality():
    """Create sample data and test reports functionality"""
    
    with app.app_context():
        print("🧪 Testing Reports Functionality")
        print("=" * 50)
        
        # Check existing data
        users_count = User.query.count()
        projects_count = Projeto.query.count()
        reports_count = Relatorio.query.count()
        
        print(f"📊 Current Data:")
        print(f"   Users: {users_count}")
        print(f"   Projects: {projects_count}")
        print(f"   Reports: {reports_count}")
        print()
        
        # Get or create a user (admin)
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        print(f"✅ Admin user found: {admin_user.username}")
        
        # Get or create a project
        project = Projeto.query.first()
        if not project:
            # Create a test project
            project = Projeto(
                nome="Projeto Teste - Sistema ELP",
                endereco="Rua Teste, 123 - Centro",
                cidade="São Paulo",
                status="ativo",
                data_inicio=datetime.now().date(),
                created_at=datetime.utcnow()
            )
            db.session.add(project)
            db.session.commit()
            print(f"✅ Test project created: {project.nome}")
        else:
            print(f"✅ Project found: {project.nome}")
        
        # Create test reports if none exist
        if reports_count == 0:
            print("📝 Creating test reports...")
            
            for i in range(3):
                report = Relatorio(
                    numero=f"REL-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    titulo=f"Relatório de Teste {i+1}",
                    projeto_id=project.id,
                    autor_id=admin_user.id,
                    data_relatorio=datetime.utcnow(),
                    conteudo=f"Este é um relatório de teste {i+1} para verificar a funcionalidade do sistema.",
                    status="concluido",
                    checklist_data="{}",
                    created_at=datetime.utcnow()
                )
                db.session.add(report)
            
            db.session.commit()
            print("✅ Test reports created successfully!")
        
        # Verify data
        new_reports_count = Relatorio.query.count()
        print(f"📊 Final report count: {new_reports_count}")
        
        # Test the reports query (simulate what the route does)
        print("\n🔍 Testing reports query (simulating route logic):")
        try:
            reports = Relatorio.query.order_by(Relatorio.created_at.desc()).limit(50).all()
            print(f"✅ Successfully loaded {len(reports)} reports")
            
            for report in reports[:3]:  # Show first 3
                print(f"   - {report.numero}: {report.titulo} (Status: {report.status})")
                
        except Exception as e:
            print(f"❌ Error querying reports: {e}")
            return False
        
        print("\n🎉 Reports functionality test completed successfully!")
        return True

if __name__ == "__main__":
    test_reports_functionality()