
#!/usr/bin/env python3
"""
Script para testar cadastro de relatório e verificar onde imagens são armazenadas
"""

import os
import sys
from datetime import datetime, date
from werkzeug.utils import secure_filename
import uuid

# Adicionar o diretório atual ao path para importar módulos
sys.path.append('.')

from app import app, db
from models import User, Projeto, Relatorio, FotoRelatorio, RelatorioExpress, FotoRelatorioExpress

def verificar_diretorios_imagens():
    """Verifica os diretórios onde imagens podem estar armazenadas"""
    diretorios = [
        'uploads/',
        'static/uploads/',
        'attached_assets/',
        'static/reports/',
        app.config.get('UPLOAD_FOLDER', 'uploads')
    ]
    
    print("🔍 VERIFICANDO DIRETÓRIOS DE IMAGENS:")
    print("=" * 50)
    
    for diretorio in diretorios:
        if os.path.exists(diretorio):
            arquivos = os.listdir(diretorio)
            imagens = [f for f in arquivos if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
            print(f"✅ {diretorio}: {len(imagens)} imagens encontradas")
            if imagens:
                print(f"   Exemplos: {imagens[:3]}")
        else:
            print(f"❌ {diretorio}: Não existe")
    
    print("\n" + "=" * 50)

def listar_configuracoes_upload():
    """Lista as configurações de upload do Flask"""
    print("⚙️ CONFIGURAÇÕES DE UPLOAD:")
    print("=" * 50)
    print(f"UPLOAD_FOLDER: {app.config.get('UPLOAD_FOLDER', 'Não definido')}")
    print(f"MAX_CONTENT_LENGTH: {app.config.get('MAX_CONTENT_LENGTH', 'Não definido')}")
    
    # Verificar se o diretório de upload existe
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if os.path.exists(upload_folder):
        print(f"✅ Diretório {upload_folder} existe")
        print(f"📁 Permissões: {oct(os.stat(upload_folder).st_mode)[-3:]}")
    else:
        print(f"❌ Diretório {upload_folder} NÃO existe")
    
    print("\n" + "=" * 50)

def criar_relatorio_teste():
    """Cria um relatório de teste para verificar o sistema"""
    with app.app_context():
        try:
            # Buscar usuário admin
            admin_user = User.query.filter_by(is_master=True).first()
            if not admin_user:
                print("❌ Usuário admin não encontrado")
                return None
            
            # Buscar ou criar projeto de teste
            projeto_teste = Projeto.query.filter_by(nome="Projeto Teste Imagens").first()
            if not projeto_teste:
                projeto_teste = Projeto(
                    numero="TEST-001",
                    nome="Projeto Teste Imagens",
                    descricao="Projeto para testar armazenamento de imagens",
                    endereco="Rua Teste, 123 - São Paulo/SP",
                    tipo_obra="Residencial",
                    construtora="Construtora Teste Ltda",
                    nome_funcionario="João da Silva",
                    responsavel_id=admin_user.id,
                    email_principal="teste@exemplo.com",
                    status="Ativo"
                )
                db.session.add(projeto_teste)
                db.session.commit()
                print(f"✅ Projeto criado: {projeto_teste.numero}")
            
            # Criar relatório de teste
            relatorio_teste = Relatorio(
                numero=f"TEST-REL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                titulo="Relatório Teste - Verificação de Imagens",
                projeto_id=projeto_teste.id,
                autor_id=admin_user.id,
                data_relatorio=datetime.now(),
                conteudo="Este é um relatório de teste para verificar o armazenamento de imagens no sistema.",
                status="Rascunho"
            )
            db.session.add(relatorio_teste)
            db.session.commit()
            
            print(f"✅ Relatório criado: {relatorio_teste.numero}")
            print(f"📋 ID: {relatorio_teste.id}")
            print(f"📅 Data: {relatorio_teste.data_relatorio}")
            
            return relatorio_teste
            
        except Exception as e:
            print(f"❌ Erro ao criar relatório: {e}")
            db.session.rollback()
            return None

def criar_relatorio_express_teste():
    """Cria um relatório express de teste"""
    with app.app_context():
        try:
            # Buscar usuário admin
            admin_user = User.query.filter_by(is_master=True).first()
            if not admin_user:
                print("❌ Usuário admin não encontrado")
                return None
            
            # Criar relatório express de teste
            relatorio_express = RelatorioExpress(
                numero=f"TEST-EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                empresa_nome="Empresa Teste Imagens Ltda",
                empresa_endereco="Av. Teste, 456 - São Paulo/SP",
                empresa_telefone="(11) 98765-4321",
                empresa_email="contato@empresateste.com",
                empresa_responsavel="Maria Santos",
                autor_id=admin_user.id,
                data_visita=date.today(),
                condicoes_climaticas="Ensolarado",
                temperatura="25°C",
                endereco_visita="Local da visita teste",
                observacoes_gerais="Observações de teste para verificar imagens",
                status="rascunho"
            )
            db.session.add(relatorio_express)
            db.session.commit()
            
            print(f"✅ Relatório Express criado: {relatorio_express.numero}")
            print(f"📋 ID: {relatorio_express.id}")
            print(f"🏢 Empresa: {relatorio_express.empresa_nome}")
            
            return relatorio_express
            
        except Exception as e:
            print(f"❌ Erro ao criar relatório express: {e}")
            db.session.rollback()
            return None

def simular_upload_imagem(relatorio_id, tipo="normal"):
    """Simula o upload de uma imagem de teste"""
    try:
        # Gerar nome de arquivo único
        filename = f"teste_imagem_{tipo}_{relatorio_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Determinar pasta de upload
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Garantir que o diretório existe
        os.makedirs(upload_folder, exist_ok=True)
        
        # Caminho completo do arquivo
        filepath = os.path.join(upload_folder, filename)
        
        # Criar arquivo de teste (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        with open(filepath, 'wb') as f:
            f.write(png_data)
        
        print(f"✅ Arquivo criado: {filepath}")
        print(f"📁 Tamanho: {len(png_data)} bytes")
        
        return filename, filepath
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de teste: {e}")
        return None, None

def verificar_imagens_no_banco():
    """Verifica imagens registradas no banco de dados"""
    with app.app_context():
        print("🗄️ IMAGENS NO BANCO DE DADOS:")
        print("=" * 50)
        
        # Fotos de relatórios normais
        fotos_normais = FotoRelatorio.query.all()
        print(f"📸 Fotos Relatórios Normais: {len(fotos_normais)}")
        for foto in fotos_normais[-5:]:  # Últimas 5
            print(f"   - {foto.filename} (Relatório ID: {foto.relatorio_id})")
        
        # Fotos de relatórios express
        fotos_express = FotoRelatorioExpress.query.all()
        print(f"📸 Fotos Relatórios Express: {len(fotos_express)}")
        for foto in fotos_express[-5:]:  # Últimas 5
            print(f"   - {foto.filename} (Express ID: {foto.relatorio_express_id})")
        
        print("\n" + "=" * 50)

def main():
    """Função principal do teste"""
    print("🧪 TESTE DE CADASTRO DE RELATÓRIO E VERIFICAÇÃO DE IMAGENS")
    print("=" * 60)
    
    # 1. Verificar configurações
    listar_configuracoes_upload()
    
    # 2. Verificar diretórios existentes
    verificar_diretorios_imagens()
    
    # 3. Verificar imagens no banco
    verificar_imagens_no_banco()
    
    # 4. Criar relatório de teste
    print("📝 CRIANDO RELATÓRIO DE TESTE:")
    print("=" * 50)
    relatorio = criar_relatorio_teste()
    
    if relatorio:
        # 5. Simular upload de imagem para relatório normal
        filename, filepath = simular_upload_imagem(relatorio.id, "normal")
        if filename:
            try:
                with app.app_context():
                    foto = FotoRelatorio(
                        relatorio_id=relatorio.id,
                        filename=filename,
                        legenda="Imagem de teste - relatório normal",
                        descricao="Teste de armazenamento de imagem",
                        tipo_servico="Geral",
                        ordem=1
                    )
                    db.session.add(foto)
                    db.session.commit()
                    print(f"✅ Foto registrada no banco: ID {foto.id}")
            except Exception as e:
                print(f"❌ Erro ao registrar foto no banco: {e}")
    
    # 6. Criar relatório express de teste
    print("\n📱 CRIANDO RELATÓRIO EXPRESS DE TESTE:")
    print("=" * 50)
    relatorio_express = criar_relatorio_express_teste()
    
    if relatorio_express:
        # 7. Simular upload de imagem para relatório express
        filename, filepath = simular_upload_imagem(relatorio_express.id, "express")
        if filename:
            try:
                with app.app_context():
                    foto = FotoRelatorioExpress(
                        relatorio_express_id=relatorio_express.id,
                        filename=filename,
                        legenda="Imagem de teste - relatório express",
                        categoria="Geral",
                        ordem=1
                    )
                    db.session.add(foto)
                    db.session.commit()
                    print(f"✅ Foto Express registrada no banco: ID {foto.id}")
            except Exception as e:
                print(f"❌ Erro ao registrar foto express no banco: {e}")
    
    # 8. Verificação final
    print("\n🔍 VERIFICAÇÃO FINAL:")
    print("=" * 50)
    verificar_diretorios_imagens()
    verificar_imagens_no_banco()
    
    print("\n✅ TESTE CONCLUÍDO!")
    print("=" * 60)
    print("📋 RESUMO:")
    print(f"   - Diretório principal de uploads: {app.config.get('UPLOAD_FOLDER', 'uploads')}")
    print(f"   - Relatório normal criado: {relatorio.numero if relatorio else 'Falhou'}")
    print(f"   - Relatório express criado: {relatorio_express.numero if relatorio_express else 'Falhou'}")
    print("   - Verifique os arquivos criados nos diretórios de upload")

if __name__ == "__main__":
    main()
