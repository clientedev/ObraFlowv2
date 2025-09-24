#!/usr/bin/env python3
"""
Script para testar upload direto de imagens e verificar se estão sendo
salvas no banco de dados corretamente.
"""

import sys
import os
import requests
import base64
from io import BytesIO
from PIL import Image

# Configuração para importar os modelos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def criar_imagem_teste():
    """Cria uma imagem de teste simples"""
    # Criar uma imagem simples de 100x100 pixels vermelha
    img = Image.new('RGB', (100, 100), color='red')
    
    # Converter para bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def testar_criacao_relatorio_com_foto():
    """Testa criação de relatório com foto programaticamente"""
    try:
        from app import app, db
        from models import User, Projeto, Relatorio, FotoRelatorio
        from datetime import datetime, date
        
        with app.app_context():
            print("🧪 TESTE DIRETO: Criando relatório com foto...")
            
            # Verificar se há usuário admin
            admin = User.query.filter_by(is_master=True).first()
            if not admin:
                print("❌ Nenhum usuário admin encontrado")
                return False
            
            print(f"✅ Usuário admin encontrado: {admin.nome_completo}")
            
            # Criar ou buscar projeto de teste
            projeto = Projeto.query.filter_by(nome="Teste Upload Imagens").first()
            if not projeto:
                projeto = Projeto(
                    numero=f"PROJ{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    nome="Teste Upload Imagens",
                    construtora="Construtora Teste",
                    nome_funcionario="Funcionário Teste",
                    responsavel_id=admin.id,
                    email_principal="teste@exemplo.com",
                    tipo_obra="Teste",
                    endereco="Endereço Teste",
                    created_at=datetime.utcnow()
                )
                db.session.add(projeto)
                db.session.commit()
            
            print(f"✅ Projeto encontrado/criado: {projeto.nome}")
            
            # Criar relatório de teste
            relatorio = Relatorio(
                numero=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
                data_visita=date.today(),
                projeto_id=projeto.id,
                autor_id=admin.id,
                status='preenchimento',
                observacoes="Relatório de teste para validar upload de imagens",
                created_at=datetime.utcnow()
            )
            db.session.add(relatorio)
            db.session.commit()
            
            print(f"✅ Relatório criado: {relatorio.numero}")
            
            # Criar imagem de teste
            image_data = criar_imagem_teste()
            print(f"✅ Imagem de teste criada: {len(image_data)} bytes")
            
            # Criar foto no banco de dados
            foto = FotoRelatorio(
                relatorio_id=relatorio.id,
                filename=f"teste_{datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                filename_original="imagem_teste.png",
                legenda="Imagem de teste para validar armazenamento binário",
                descricao="Teste de upload direto no banco",
                ordem=1,
                imagem=image_data,  # SALVAR DADOS BINÁRIOS AQUI
                created_at=datetime.utcnow()
            )
            
            db.session.add(foto)
            db.session.commit()
            
            print(f"✅ Foto criada no banco: ID {foto.id}")
            
            # Verificar se a imagem foi salva
            foto_verificacao = FotoRelatorio.query.get(foto.id)
            if foto_verificacao.imagem:
                tamanho_salvo = len(foto_verificacao.imagem)
                print(f"✅ SUCESSO: Imagem salva no banco com {tamanho_salvo} bytes")
                
                # Verificar se os dados são os mesmos
                if foto_verificacao.imagem == image_data:
                    print("✅ PERFEITO: Dados binários salvos corretamente!")
                    return True
                else:
                    print("❌ ERRO: Dados binários diferentes do original")
                    return False
            else:
                print("❌ ERRO: Campo imagem está vazio no banco")
                return False
                
    except Exception as e:
        print(f"❌ ERRO no teste: {str(e)}")
        return False

def verificar_configuracao_banco():
    """Verifica configuração do banco de dados"""
    try:
        from app import app, db
        
        with app.app_context():
            print("🔍 VERIFICAÇÃO DA CONFIGURAÇÃO DO BANCO:")
            print("=" * 50)
            
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # Verificar se as tabelas existem
            inspector = db.inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"Tabelas encontradas: {len(tabelas)}")
            
            if 'fotos_relatorio' in tabelas:
                colunas = [col['name'] for col in inspector.get_columns('fotos_relatorio')]
                print(f"✅ Tabela fotos_relatorio existe com colunas: {colunas}")
                
                if 'imagem' in colunas:
                    print("✅ Coluna 'imagem' existe na tabela")
                else:
                    print("❌ Coluna 'imagem' NÃO existe na tabela")
                    return False
            else:
                print("❌ Tabela fotos_relatorio NÃO existe")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ ERRO na verificação: {str(e)}")
        return False

def main():
    """Função principal do teste"""
    print("🧪 TESTE DIRETO DE UPLOAD DE IMAGENS")
    print("=" * 50)
    
    # Verificar configuração
    if not verificar_configuracao_banco():
        print("❌ Configuração do banco inválida")
        return False
    
    # Testar criação de relatório com foto
    if testar_criacao_relatorio_com_foto():
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("Sistema de upload de imagens está funcionando corretamente.")
        return True
    else:
        print("\n❌ TESTE FALHOU!")
        print("Sistema de upload de imagens tem problemas.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)