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

# Run the Flask development server
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
