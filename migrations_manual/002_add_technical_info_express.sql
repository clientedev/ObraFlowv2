-- Adiciona coluna informacoes_tecnicas na tabela relatorios_express
ALTER TABLE relatorios_express ADD COLUMN IF NOT EXISTS informacoes_tecnicas TEXT;
