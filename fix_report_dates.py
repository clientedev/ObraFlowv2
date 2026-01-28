"""
Script único para corrigir datas dos relatórios existentes
Converte datas UTC para horário do Brasil (UTC-3)
"""
from app import app, db
from models import Relatorio
from datetime import timedelta

def fix_report_dates():
    """Corrige as datas dos relatórios subtraindo 3 horas (UTC → Brazil)"""
    with app.app_context():
        # Buscar todos os relatórios
        relatorios = Relatorio.query.all()
        
        updated_count = 0
        for relatorio in relatorios:
            if relatorio.data_relatorio:
                # Subtrair 3 horas para converter UTC → Brazil time
                relatorio.data_relatorio = relatorio.data_relatorio - timedelta(hours=3)
                updated_count += 1
        
        # Salvar mudanças
        db.session.commit()
        
        print(f"✅ {updated_count} relatórios atualizados com sucesso!")
        print("As datas foram corrigidas de UTC para horário do Brasil.")

if __name__ == "__main__":
    print("🔧 Corrigindo datas dos relatórios existentes...")
    print("Convertendo UTC → Horário do Brasil (UTC-3)")
    print("-" * 50)
    
    fix_report_dates()
