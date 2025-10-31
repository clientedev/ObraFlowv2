
#!/usr/bin/env python3
"""
Script DEFINITIVO para corrigir a tabela alembic_version no Railway
Remove referências a migrações antigas e marca a migração atual como aplicada
"""

import os
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def fix_alembic_version():
    """Corrige a tabela alembic_version removendo referências antigas"""
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logging.error("❌ DATABASE_URL não configurado")
        return False
    
    # Corrigir URL do PostgreSQL se necessário
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as connection:
            # 1. Verificar estado atual
            logging.info("🔍 Verificando estado atual...")
            result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchall()
            logging.info(f"   Versões encontradas: {result}")
            
            # 2. Limpar COMPLETAMENTE a tabela
            logging.info("🧹 Limpando tabela alembic_version...")
            connection.execute(text("TRUNCATE TABLE alembic_version"))
            logging.info("✅ Tabela alembic_version limpa")
            
            # 3. Inserir APENAS a versão atual
            logging.info("📝 Inserindo migração atual (265f97ab88c1)...")
            connection.execute(text(
                "INSERT INTO alembic_version (version_num) VALUES ('265f97ab88c1')"
            ))
            logging.info("✅ Migração 265f97ab88c1 marcada como aplicada")
            
            # 4. Verificar resultado final
            result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result and result[0] == '265f97ab88c1':
                logging.info("✅ Verificação: alembic_version corrigida com sucesso!")
                logging.info(f"   Versão atual: {result[0]}")
                return True
            else:
                logging.error("❌ Verificação falhou")
                return False
                
    except Exception as e:
        logging.error(f"❌ Erro ao corrigir alembic_version: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("🚀 Iniciando correção DEFINITIVA do alembic_version...")
    logging.info("=" * 60)
    
    if fix_alembic_version():
        logging.info("=" * 60)
        logging.info("🎉 Correção concluída com sucesso!")
        logging.info("💡 A migração está corrigida permanentemente")
        logging.info("🚀 Você pode fazer deploy/restart agora")
        logging.info("=" * 60)
    else:
        logging.error("=" * 60)
        logging.error("❌ Correção falhou - verifique os logs acima")
        logging.error("=" * 60)
