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
        # CORREÇÃO PRIORITÁRIA: Limpar alembic_version ANTES de qualquer outra coisa
        try:
            from app import app, db
            from sqlalchemy import text
            
            with app.app_context():
                # Verificar se existe a revisão problemática
                engine = db.engine.execution_options(isolation_level="AUTOCOMMIT")
                with engine.connect() as connection:
                    check_result = connection.execute(
                        text("SELECT version_num FROM alembic_version WHERE version_num IN ('20250929_2303', 'a4d5b6d9c0ca')")
                    ).fetchone()
                    
                    if check_result:
                        logging.warning(f"⚠️ Migração antiga detectada ({check_result[0]}) - corrigindo...")
                        connection.execute(text("DELETE FROM alembic_version"))
                        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('265f97ab88c1')"))
                        logging.info("✅ alembic_version corrigido para 265f97ab88c1 ANTES das migrações")
                    else:
                        # Garantir que a versão correta existe
                        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('265f97ab88c1') ON CONFLICT DO NOTHING"))
                        logging.info("✅ alembic_version está correto (265f97ab88c1)")
        except Exception as fix_error:
            logging.warning(f"⚠️ Erro ao verificar alembic_version: {fix_error}")
        
        # First, fix user_email_config table if needed
        try:
            from fix_user_email_config_columns import fix_user_email_config_table
            fix_user_email_config_table()
        except Exception as fix_error:
            logging.warning(f"⚠️ Erro ao corrigir user_email_config: {fix_error}")
        
        # Then run migrations with better error handling
        import subprocess
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logging.info("✅ Migrações aplicadas com sucesso")
        else:
            logging.warning(f"⚠️ Migração falhou: {result.stderr}")
            
            # Fallback final se ainda houver erro
            if "Can't locate revision" in result.stderr:
                logging.info("🔧 Forçando correção final...")
                try:
                    from app import app, db
                    from sqlalchemy import text
                    with app.app_context():
                        engine = db.engine.execution_options(isolation_level="AUTOCOMMIT")
                        with engine.connect() as connection:
                            connection.execute(text("DELETE FROM alembic_version"))
                            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('265f97ab88c1')"))
                            logging.info("✅ Migração forçada DEFINITIVA para 265f97ab88c1")
                except Exception as final_fix:
                    logging.error(f"❌ Erro na correção final: {final_fix}")
                    
    except Exception as e:
        logging.warning(f"⚠️ Erro nas migrações (continuando): {e}")

# Run the Flask development server
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
