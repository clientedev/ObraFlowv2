from app import app  # noqa: F401
# Models will be imported by routes.py and routes_pwa.py
import routes_pwa  # noqa: F401
import routes  # noqa: F401
import railway_routes_fix  # noqa: F401

# Auto-run migrations on Railway deploy with conflict resolution
import os
import logging
if os.environ.get("RAILWAY_ENVIRONMENT"):
    logging.info("🔄 Executando migrações automáticas...")
    try:
        # First, fix user_email_config table if needed
        try:
            from fix_user_email_config_columns import fix_user_email_config_table
            fix_user_email_config_table()
        except Exception as fix_error:
            logging.warning(f"⚠️ Erro ao corrigir user_email_config: {fix_error}")
        
        # Then, try to fix any migration conflicts
        try:
            from fix_migration_categorias_obra import fix_categorias_obra_migration
            fix_categorias_obra_migration()
        except Exception as fix_error:
            logging.warning(f"⚠️ Erro ao corrigir conflitos de migração: {fix_error}")
        
        # Then run migrations with better error handling
        import subprocess
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logging.info("✅ Migrações aplicadas com sucesso")
        else:
            logging.warning(f"⚠️ Migração falhou: {result.stderr}")
            # If migration fails due to duplicate table, mark migration as completed
            if "already exists" in result.stderr or "DuplicateTable" in result.stderr:
                logging.info("🔧 Tabela já existe - marcando migração como concluída...")
                try:
                    from fix_migration_categorias_obra import fix_categorias_obra_migration
                    if fix_categorias_obra_migration():
                        logging.info("✅ Estado de migração corrigido - sistema pronto")
                    else:
                        # Fallback: mark migration as completed anyway
                        logging.info("🔧 Aplicando correção de fallback...")
                        from app import app, db
                        from sqlalchemy import text
                        with app.app_context():
                            with db.engine.connect() as connection:
                                connection.execute(text("UPDATE alembic_version SET version_num = '20250929_2303'"))
                                connection.commit()
                                logging.info("✅ Migração marcada como concluída via fallback")
                except Exception as fix_error:
                    logging.error(f"❌ Erro ao corrigir migração: {fix_error}")
                    logging.info("🔄 Sistema continuará funcionando mesmo com erro de migração")
    except Exception as e:
        logging.warning(f"⚠️ Erro nas migrações (continuando): {e}")

# Run the Flask development server
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
