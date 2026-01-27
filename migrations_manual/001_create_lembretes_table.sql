-- Migration Script for Lembretes Table
-- Run this in your PostgreSQL database (Railway)

CREATE TABLE IF NOT EXISTS lembretes (
    id SERIAL PRIMARY KEY,
    projeto_id INTEGER NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    texto TEXT NOT NULL,
    fechado BOOLEAN NOT NULL DEFAULT FALSE,
    fechado_em TIMESTAMP NULL,
    fechado_por_id INTEGER NULL REFERENCES users(id),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por_id INTEGER NOT NULL REFERENCES users(id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_lembretes_projeto_id ON lembretes(projeto_id);
CREATE INDEX IF NOT EXISTS idx_lembretes_fechado ON lembretes(fechado);
CREATE INDEX IF NOT EXISTS idx_lembretes_projeto_fechado ON lembretes(projeto_id, fechado);

-- Add comment
COMMENT ON TABLE lembretes IS 'Lembretes persistentes de projetos - permanecem ativos até serem fechados';
