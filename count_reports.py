"""
Script rápido para verificar contagens de relatórios
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:KgyYkEmMztCNMSPHVbOpWLTiKZFXYwpB@switchback.proxy.rlwy.net:17107/railway'

from app import app, db
from models import Relatorio, RelatorioExpress
from sqlalchemy import func

with app.app_context():
    print("\n🔍 CONTAGEM DE RELATÓRIOS APROVADOS:")
    print("=" * 60)
    
    # Relatórios comuns
    rel_aprovados = Relatorio.query.filter(
        func.lower(Relatorio.status).in_(['aprovado', 'finalizado', 'aprovado final'])
    ).count()
    
    print(f"📄 Relatórios Comuns Aprovados: {rel_aprovados}")
    
    # Relatórios express
    exp_aprovados = RelatorioExpress.query.filter(
        func.lower(RelatorioExpress.status).in_(['aprovado', 'finalizado', 'aprovado final'])
    ).count()
    
    print(f"⚡ Relatórios Express Aprovados: {exp_aprovados}")
    print(f"\n📊 TOTAL: {rel_aprovados + exp_aprovados}")
    print("=" * 60)
