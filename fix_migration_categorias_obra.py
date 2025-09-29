
#!/usr/bin/env python3
"""
Fix migration conflict for categorias_obra table
"""
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_categorias_obra_migration():
    """Fix the categorias_obra migration conflict"""
    try:
        with app.app_context():
            logger.info("🔧 Fixing categorias_obra migration conflict...")
            
            # Check if table exists
            inspector = inspect(db.engine)
            table_exists = 'categorias_obra' in inspector.get_table_names()
            
            logger.info(f"📋 Table categorias_obra exists: {table_exists}")
            
            if table_exists:
                # Mark the migration as completed in alembic_version
                try:
                    # Check current alembic version
                    result = db.session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                    current_version = result[0] if result else None
                    logger.info(f"📊 Current alembic version: {current_version}")
                    
                    # Update to the latest migration that includes categorias_obra
                    target_version = "20250929_2303"  # The categorias_obra migration
                    
                    if current_version != target_version:
                        db.session.execute(text("UPDATE alembic_version SET version_num = :version"), 
                                         {'version': target_version})
                        db.session.commit()
                        logger.info(f"✅ Updated alembic version to {target_version}")
                    else:
                        logger.info("✅ Alembic version already correct")
                        
                except Exception as e:
                    logger.error(f"❌ Error updating alembic version: {e}")
                    db.session.rollback()
                    
                    # Try to create alembic_version table if it doesn't exist
                    try:
                        db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS alembic_version (
                                version_num VARCHAR(32) NOT NULL,
                                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                            )
                        """))
                        
                        # Insert the current version
                        db.session.execute(text("DELETE FROM alembic_version"))
                        db.session.execute(text("INSERT INTO alembic_version (version_num) VALUES (:version)"), 
                                         {'version': target_version})
                        db.session.commit()
                        logger.info(f"✅ Created alembic_version table with version {target_version}")
                        
                    except Exception as e2:
                        logger.error(f"❌ Error creating alembic_version: {e2}")
                        db.session.rollback()
                        return False
            else:
                logger.info("📋 Table doesn't exist, migration can proceed normally")
                
            logger.info("✅ Migration conflict fixed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Critical error fixing migration: {e}")
        return False

if __name__ == "__main__":
    success = fix_categorias_obra_migration()
    if success:
        print("✅ Migration fix completed successfully")
        sys.exit(0)
    else:
        print("❌ Migration fix failed")
        sys.exit(1)
