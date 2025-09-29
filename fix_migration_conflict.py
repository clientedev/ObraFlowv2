
#!/usr/bin/env python3
"""
Script para corrigir conflito de migração do numero_projeto
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_migration_conflict():
    """Corrige o conflito de migração do numero_projeto"""
    
    # Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL não encontrada")
        return False
        
    # Fix postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                logger.info("🔧 Iniciando correção do conflito de migração...")
                
                # Step 1: Check current state
                result = conn.execute(text("""
                    SELECT COUNT(*) as total, 
                           COUNT(numero_projeto) as with_numero_projeto,
                           COUNT(*) - COUNT(numero_projeto) as without_numero_projeto
                    FROM relatorios
                """))
                
                stats = result.fetchone()
                logger.info(f"📊 Estado atual: {stats.total} relatórios total, {stats.with_numero_projeto} com numero_projeto, {stats.without_numero_projeto} sem numero_projeto")
                
                if stats.without_numero_projeto == 0:
                    logger.info("✅ Todos os relatórios já têm numero_projeto - nada para corrigir")
                    trans.commit()
                    return True
                
                # Step 2: Get reports without numero_projeto
                reports_result = conn.execute(text("""
                    SELECT id, projeto_id, numero, created_at 
                    FROM relatorios 
                    WHERE numero_projeto IS NULL 
                    ORDER BY projeto_id, created_at ASC
                """))
                
                reports = reports_result.fetchall()
                logger.info(f"🔍 Encontrados {len(reports)} relatórios para corrigir")
                
                # Step 3: Process each project separately
                projeto_groups = {}
                for report in reports:
                    if report.projeto_id not in projeto_groups:
                        projeto_groups[report.projeto_id] = []
                    projeto_groups[report.projeto_id].append(report)
                
                fixed_count = 0
                
                for projeto_id, project_reports in projeto_groups.items():
                    logger.info(f"📝 Processando projeto {projeto_id} com {len(project_reports)} relatórios")
                    
                    # Get max existing numero_projeto for this project
                    max_result = conn.execute(text("""
                        SELECT COALESCE(MAX(numero_projeto), 0) as max_num
                        FROM relatorios 
                        WHERE projeto_id = :projeto_id AND numero_projeto IS NOT NULL
                    """), {'projeto_id': projeto_id})
                    
                    max_existing = max_result.scalar() or 0
                    logger.info(f"📈 Maior numero_projeto existente no projeto {projeto_id}: {max_existing}")
                    
                    # Process each report
                    for idx, report in enumerate(project_reports, start=1):
                        new_numero_projeto = max_existing + idx
                        new_numero = f"REL-{new_numero_projeto:04d}"
                        
                        # Check if this numero already exists globally
                        check_result = conn.execute(text("""
                            SELECT COUNT(*) FROM relatorios WHERE numero = :numero
                        """), {'numero': new_numero})
                        
                        collision_count = 0
                        while check_result.scalar() > 0:
                            collision_count += 1
                            # Find next available global number
                            global_max_result = conn.execute(text("""
                                SELECT COALESCE(MAX(CAST(SUBSTRING(numero FROM 5) AS INTEGER)), 0) + 1 as next_global
                                FROM relatorios 
                                WHERE numero LIKE 'REL-%'
                            """))
                            
                            new_numero_projeto = global_max_result.scalar()
                            new_numero = f"REL-{new_numero_projeto:04d}"
                            
                            # Check again
                            check_result = conn.execute(text("""
                                SELECT COUNT(*) FROM relatorios WHERE numero = :numero
                            """), {'numero': new_numero})
                        
                        if collision_count > 0:
                            logger.warning(f"⚠️ Resolvidas {collision_count} colisões para relatório {report.id}")
                        
                        # Update the report
                        conn.execute(text("""
                            UPDATE relatorios 
                            SET numero_projeto = :numero_projeto, numero = :numero
                            WHERE id = :report_id
                        """), {
                            'numero_projeto': new_numero_projeto,
                            'numero': new_numero,
                            'report_id': report.id
                        })
                        
                        fixed_count += 1
                        logger.info(f"✅ Relatório {report.id}: numero_projeto={new_numero_projeto}, numero={new_numero}")
                
                # Commit transaction
                trans.commit()
                logger.info(f"🎉 Correção concluída! {fixed_count} relatórios corrigidos")
                
                # Step 4: Verify final state
                final_result = conn.execute(text("""
                    SELECT COUNT(*) as total, 
                           COUNT(numero_projeto) as with_numero_projeto
                    FROM relatorios
                """))
                
                final_stats = final_result.fetchone()
                logger.info(f"📊 Estado final: {final_stats.total} relatórios total, {final_stats.with_numero_projeto} com numero_projeto")
                
                if final_stats.total == final_stats.with_numero_projeto:
                    logger.info("✅ SUCESSO: Todos os relatórios agora têm numero_projeto!")
                    return True
                else:
                    logger.error(f"❌ ERRO: Ainda existem {final_stats.total - final_stats.with_numero_projeto} relatórios sem numero_projeto")
                    return False
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Erro durante correção: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Erro de conexão: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_migration_conflict()
    sys.exit(0 if success else 1)
