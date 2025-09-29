
"""fix numero_projeto retroactively

Revision ID: 20250929_1845
Revises: 20250928_1300
Create Date: 2025-09-29 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '20250929_1845'
down_revision = '20250928_1300'
branch_labels = None
depends_on = None

def upgrade():
    """Fix numero_projeto retroactively for existing reports"""
    conn = op.get_bind()
    
    # First, get all reports that need fixing (where numero_projeto is NULL)
    result = conn.execute(text("""
        SELECT id, projeto_id, created_at 
        FROM relatorios 
        WHERE numero_projeto IS NULL 
        ORDER BY projeto_id, created_at ASC
    """))
    
    reports = result.fetchall()
    
    if not reports:
        print("No reports need fixing - all already have numero_projeto")
        return
    
    # Group by projeto_id to assign sequential numbers
    projeto_reports = {}
    for report in reports:
        if report.projeto_id not in projeto_reports:
            projeto_reports[report.projeto_id] = []
        projeto_reports[report.projeto_id].append(report)
    
    # Process each project separately
    for projeto_id, project_reports in projeto_reports.items():
        # Get the highest existing numero_projeto for this project
        max_result = conn.execute(text("""
            SELECT COALESCE(MAX(numero_projeto), 0) as max_num
            FROM relatorios 
            WHERE projeto_id = :projeto_id AND numero_projeto IS NOT NULL
        """), {'projeto_id': projeto_id})
        
        max_existing = max_result.scalar() or 0
        
        # Update each report with sequential numbers starting after the max
        for idx, report in enumerate(project_reports, start=1):
            new_numero_projeto = max_existing + idx
            new_numero = f"REL-{new_numero_projeto:04d}"
            
            # Check if this numero already exists globally
            check_result = conn.execute(text("""
                SELECT COUNT(*) FROM relatorios WHERE numero = :numero
            """), {'numero': new_numero})
            
            if check_result.scalar() > 0:
                # If it exists, find the next available global number
                global_max_result = conn.execute(text("""
                    SELECT COALESCE(MAX(CAST(SUBSTRING(numero FROM 5) AS INTEGER)), 0) as max_global
                    FROM relatorios 
                    WHERE numero LIKE 'REL-%'
                """))
                
                global_max = global_max_result.scalar() or 0
                new_numero_projeto = global_max + 1
                new_numero = f"REL-{new_numero_projeto:04d}"
                
                # Double-check this new number doesn't exist
                while True:
                    check_again = conn.execute(text("""
                        SELECT COUNT(*) FROM relatorios WHERE numero = :numero
                    """), {'numero': new_numero})
                    
                    if check_again.scalar() == 0:
                        break
                    
                    new_numero_projeto += 1
                    new_numero = f"REL-{new_numero_projeto:04d}"
            
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
            
            print(f"Updated report {report.id}: numero_projeto={new_numero_projeto}, numero={new_numero}")

def downgrade():
    """Revert the numero_projeto fixes"""
    conn = op.get_bind()
    
    # Set numero_projeto back to NULL for reports that were fixed
    conn.execute(text("""
        UPDATE relatorios 
        SET numero_projeto = NULL 
        WHERE numero_projeto IS NOT NULL
    """))
