
#!/usr/bin/env python3
"""
Fix migration state for Railway deployment
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sqlalchemy as sa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_migration_state():
    """Fix the migration state by marking the problematic migration as executed"""
    
    app = Flask(__name__)
    
    # Database configuration
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        database_url = os.environ.get("DATABASE_URL")
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///construction_tracker.db")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    
    with app.app_context():
        try:
            # Check if the table already exists
            inspector = sa.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            if 'user_email_config' in table_names:
                logger.info("✅ Table 'user_email_config' already exists")
                
                # Mark the migration as executed
                logger.info("🔧 Marking migration as executed in alembic_version table")
                
                # Check if alembic_version table exists
                if 'alembic_version' in table_names:
                    # Update the version to the latest migration
                    with db.engine.connect() as conn:
                        conn.execute(db.text(
                            "UPDATE alembic_version SET version_num = 'c18fc0f1e85a'"
                        ))
                        conn.commit()
                    logger.info("✅ Migration state updated successfully")
                else:
                    # Create alembic_version table if it doesn't exist
                    with db.engine.connect() as conn:
                        conn.execute(db.text(
                            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
                        ))
                        conn.execute(db.text(
                            "INSERT INTO alembic_version (version_num) VALUES ('c18fc0f1e85a')"
                        ))
                        conn.commit()
                    logger.info("✅ Created alembic_version table and set migration state")
            else:
                logger.info("❌ Table 'user_email_config' does not exist. Migration needs to run.")
                
        except Exception as e:
            logger.error(f"❌ Error fixing migration state: {e}")
            return False
            
    return True

if __name__ == "__main__":
    logger.info("🔧 Starting migration state fix...")
    if fix_migration_state():
        logger.info("✅ Migration state fix completed successfully")
    else:
        logger.error("❌ Migration state fix failed")
