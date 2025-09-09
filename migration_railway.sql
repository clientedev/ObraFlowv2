-- Script de migração para Railway PostgreSQL
-- Execute este script no seu banco de dados PostgreSQL do Railway para corrigir os erros 500

-- Adicionar as novas colunas na tabela projetos (se não existirem)
DO $$ 
BEGIN
    -- Adicionar coluna construtora
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'projetos' AND column_name = 'construtora') THEN
        ALTER TABLE projetos ADD COLUMN construtora VARCHAR(200) NOT NULL DEFAULT 'Construtora não informada';
        -- Remover o valor padrão após adicionar a coluna
        ALTER TABLE projetos ALTER COLUMN construtora DROP DEFAULT;
    END IF;

    -- Adicionar coluna nome_funcionario
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'projetos' AND column_name = 'nome_funcionario') THEN
        ALTER TABLE projetos ADD COLUMN nome_funcionario VARCHAR(200) NOT NULL DEFAULT 'Funcionário não informado';
        -- Remover o valor padrão após adicionar a coluna
        ALTER TABLE projetos ALTER COLUMN nome_funcionario DROP DEFAULT;
    END IF;

    -- Adicionar coluna email_principal
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'projetos' AND column_name = 'email_principal') THEN
        ALTER TABLE projetos ADD COLUMN email_principal VARCHAR(255) NOT NULL DEFAULT 'cliente@exemplo.com';
        -- Remover o valor padrão após adicionar a coluna
        ALTER TABLE projetos ALTER COLUMN email_principal DROP DEFAULT;
    END IF;

    RAISE NOTICE 'Colunas adicionadas com sucesso à tabela projetos';
END $$;

-- Verificar se as colunas foram adicionadas
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'projetos' 
AND column_name IN ('construtora', 'nome_funcionario', 'email_principal')
ORDER BY column_name;

-- Mostrar estrutura completa da tabela projetos
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'projetos' 
ORDER BY ordinal_position;