"""
Script de teste para verificar upload e salvamento de imagens no banco de dados
"""
import os
import sys
import base64
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import Relatorio, FotoRelatorio, Projeto, User

def create_test_image():
    """Cria uma imagem de teste simples (1x1 pixel PNG)"""
    # PNG de 1x1 pixel vermelho
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='
    )
    return png_data

def test_image_upload():
    """Testa o upload e salvamento de uma imagem"""
    with app.app_context():
        print("🧪 Iniciando teste de upload de imagem...")
        print(f"📊 DATABASE_URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')[:50]}...")
        
        # Verificar se há usuários e projetos
        user = User.query.first()
        if not user:
            print("❌ Nenhum usuário encontrado no banco")
            return
        
        projeto = Projeto.query.first()
        if not projeto:
            print("❌ Nenhum projeto encontrado no banco")
            print("📝 Criando projeto de teste...")
            projeto = Projeto(
                nome="Projeto Teste - Upload Imagens",
                endereco="Rua Teste, 123",
                status="Ativo"
            )
            db.session.add(projeto)
            db.session.commit()
            print(f"✅ Projeto criado: ID={projeto.id}")
        
        # Criar relatório de teste
        print("📝 Criando relatório de teste...")
        relatorio = Relatorio(
            projeto_id=projeto.id,
            titulo="Relatório Teste - Upload Imagens",
            descricao="Teste de upload e salvamento de imagens no banco PostgreSQL",
            data_visita=datetime.now().date(),
            autor_id=user.id
        )
        db.session.add(relatorio)
        db.session.commit()
        print(f"✅ Relatório criado: ID={relatorio.id}, Número={relatorio.numero}")
        
        # Criar imagem de teste
        print("📷 Criando foto de teste...")
        image_data = create_test_image()
        print(f"   Tamanho da imagem: {len(image_data)} bytes")
        
        foto = FotoRelatorio(
            relatorio_id=relatorio.id,
            filename="test_image.png",
            legenda="Imagem de teste",
            descricao="Teste de armazenamento BYTEA no PostgreSQL",
            tipo_servico="Teste",
            ordem=1,
            imagem=image_data  # Salvar dados binários
        )
        
        db.session.add(foto)
        print("💾 Salvando foto no banco...")
        db.session.commit()
        print(f"✅ Foto salva: ID={foto.id}")
        
        # Verificar se a foto foi salva corretamente
        print("\n🔍 Verificando foto salva no banco...")
        foto_verificada = FotoRelatorio.query.get(foto.id)
        
        if foto_verificada:
            print(f"✅ Foto encontrada:")
            print(f"   ID: {foto_verificada.id}")
            print(f"   Filename: {foto_verificada.filename}")
            print(f"   Legenda: {foto_verificada.legenda}")
            print(f"   Imagem presente: {foto_verificada.imagem is not None}")
            if foto_verificada.imagem:
                print(f"   Tamanho da imagem: {len(foto_verificada.imagem)} bytes")
                print(f"   Primeiros 20 bytes: {foto_verificada.imagem[:20]}")
            else:
                print("   ❌ IMAGEM É NULL!")
        else:
            print(f"❌ Foto não encontrada com ID={foto.id}")
        
        # Consultar diretamente no SQL
        print("\n🔍 Consultando diretamente via SQL...")
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT id, filename, legenda, LENGTH(imagem) as imagem_size FROM fotos_relatorio WHERE id = :id"),
            {"id": foto.id}
        ).fetchone()
        
        if result:
            print(f"✅ Resultado SQL:")
            print(f"   ID: {result[0]}")
            print(f"   Filename: {result[1]}")
            print(f"   Legenda: {result[2]}")
            print(f"   Tamanho imagem (SQL): {result[3]} bytes")
        else:
            print("❌ Nenhum resultado encontrado no SQL")
        
        print("\n✅ TESTE CONCLUÍDO!")
        print(f"   Relatório ID: {relatorio.id}")
        print(f"   Foto ID: {foto.id}")
        print(f"   URL de exibição: /imagens/{foto.id}")

if __name__ == "__main__":
    test_image_upload()
