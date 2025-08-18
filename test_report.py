#!/usr/bin/env python3
"""
Script simples para testar criação de relatório diretamente
"""
import sys
import os
sys.path.append('.')

from app import app, db
from models import Relatorio, User, Projeto
from datetime import datetime

def test_create_report():
    with app.app_context():
        try:
            # Get first user and project
            user = User.query.first()
            projeto = Projeto.query.first()
            
            if not user or not projeto:
                print("ERROR: Usuário ou projeto não encontrado")
                return
            
            print(f"Criando relatório para usuário {user.username} e projeto {projeto.nome}")
            
            # Create minimal report
            relatorio = Relatorio()
            relatorio.numero = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            relatorio.titulo = "Teste de Relatório"
            relatorio.projeto_id = projeto.id
            relatorio.autor_id = user.id
            relatorio.conteudo = "Conteúdo de teste"
            relatorio.data_relatorio = datetime.now()
            relatorio.status = 'Rascunho'
            relatorio.created_at = datetime.utcnow()
            
            db.session.add(relatorio)
            db.session.commit()
            
            print(f"✓ Relatório criado com sucesso! ID: {relatorio.id}")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_create_report()