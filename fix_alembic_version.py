
#!/usr/bin/env python3
"""
Script para corrigir a tabela alembic_version no Railway
Remove referências a migrações antigas e marca a migração atual como aplicada
"""

import os
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)

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
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # 1. Limpar alembic_version
            logging.info("🧹 Limpando tabela alembic_version...")
            connection.execute(text("DELETE FROM alembic_version"))
            connection.commit()
            logging.info("✅ Tabela alembic_version limpa")
            
            # 2. Inserir a versão atual
            logging.info("📝 Marcando migração atual (a4d5b6d9c0ca)...")
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('a4d5b6d9c0ca')"))
            connection.commit()
            logging.info("✅ Migração a4d5b6d9c0ca marcada como aplicada")
            
            # 3. Verificar
            result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result and result[0] == 'a4d5b6d9c0ca':
                logging.info("✅ Verificação: alembic_version corrigida com sucesso!")
                return True
            else:
                logging.error("❌ Verificação falhou")
                return False
                
    except Exception as e:
        logging.error(f"❌ Erro ao corrigir alembic_version: {e}")
        return False

if __name__ == "__main__":
    logging.info("🚀 Iniciando correção do alembic_version...")
    if fix_alembic_version():
        logging.info("🎉 Correção concluída com sucesso!")
        logging.info("💡 Você pode fazer deploy agora que a migração está corrigida")
    else:
        logging.error("❌ Correção falhou - verifique os logs acima")
