-- Migration: Add acompanhantes column to relatorios table
-- Created: 2025-10-29
-- Description: Adds JSON column to store visit attendees information

-- Add acompanhantes column (JSONB for PostgreSQL, JSON for compatibility)
ALTER TABLE relatorios 
ADD COLUMN IF NOT EXISTS acompanhantes JSON;

-- Add comment to column
COMMENT ON COLUMN relatorios.acompanhantes IS 'JSON array storing visit attendees: [{"nome": "Name", "funcao": "Role", "origem": "Source"}]';

-- Verificação
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'relatorios' AND column_name = 'acompanhantes';
