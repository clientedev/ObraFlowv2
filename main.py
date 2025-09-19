from app import app  # noqa: F401
import routes_pwa  # noqa: F401
import routes  # noqa: F401

# Auto-run migrations on Railway deploy
import os
import logging
if os.environ.get("RAILWAY_ENVIRONMENT"):
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
