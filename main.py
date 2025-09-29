from app import app  # noqa: F401
import routes_pwa  # noqa: F401
import routes  # noqa: F401
import railway_routes_fix  # noqa: F401

# Auto-run migrations on Railway deploy with conflict resolution
import os
import logging
if os.environ.get("RAILWAY_ENVIRONMENT"):
    logging.info("🔄 Executando migrações automáticas...")
    try:
        # First, try to fix any migration conflicts
        try:
            from fix_migration_categorias_obra import fix_categorias_obra_migration
            fix_categorias_obra_migration()
        except Exception as fix_error:
            logging.warning(f"⚠️ Erro ao corrigir conflitos de migração: {fix_error}")
        
        # Then run migrations
        import subprocess
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logging.info("✅ Migrações aplicadas com sucesso")
        else:
            logging.warning(f"⚠️ Migração falhou: {result.stderr}")
            # If migration fails due to duplicate table, try to fix it
            if "already exists" in result.stderr:
                logging.info("🔧 Tentando corrigir estado de migração...")
                try:
                    from fix_migration_categorias_obra import fix_categorias_obra_migration
                    if fix_categorias_obra_migration():
                        logging.info("✅ Estado de migração corrigido")
                except Exception as fix_error:
                    logging.error(f"❌ Erro ao corrigir migração: {fix_error}")
    except Exception as e:
        logging.warning(f"⚠️ Erro nas migrações (continuando): {e}")

# Run the Flask development server
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
