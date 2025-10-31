from app import app  # noqa: F401
# Models will be imported by routes.py and routes_pwa.py
import routes_pwa  # noqa: F401
import routes  # noqa: F401
import railway_routes_fix  # noqa: F401

# Auto-run migrations on Railway deploy
import os
import logging

def clean_orphaned_alembic_versions():
    """Verifica se existe versão órfã e deixa Alembic gerenciar automaticamente"""
    try:
        from sqlalchemy import create_engine, text
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            return
            
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
        
        # Verificar se tabela alembic_version existe
        with engine.connect() as connection:
            try:
                result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                if result:
                    current_version = result[0]
                    logging.info(f"🔍 Versão Alembic no banco: {current_version}")
                    logging.info("ℹ️ Alembic irá validar e aplicar migrações se necessário")
            except Exception as check_error:
                logging.debug(f"Tabela alembic_version ainda não existe: {check_error}")
                
    except Exception as e:
        logging.warning(f"⚠️ Erro ao verificar versão Alembic: {e}")

if os.environ.get("RAILWAY_ENVIRONMENT"):
    logging.info("🚂 Railway environment - preparando migrações...")
    
    # Limpar versões órfãs antes de executar migrações
    clean_orphaned_alembic_versions()
    
    logging.info("🔄 Executando migrações automáticas...")
    try:
        import subprocess
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logging.info("✅ Migrações aplicadas com sucesso")
        else:
            logging.warning(f"⚠️ Migração falhou: {result.stderr}")
    except Exception as e:
        logging.warning(f"⚠️ Erro nas migrações (continuando): {e}")

# Run the Flask development server
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
