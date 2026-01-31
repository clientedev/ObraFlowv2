-- Script to create user_devices table and migrate data
-- Run this in PostgreSQL

-- 1. Create the user_devices table
CREATE TABLE IF NOT EXISTS user_devices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    player_id VARCHAR(255) NOT NULL UNIQUE,
    device_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_devices_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_user_player UNIQUE (user_id, player_id)
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_player_id ON user_devices(player_id);

-- 3. Migrate existing fcm_token data to user_devices
INSERT INTO user_devices (user_id, player_id, device_info)
SELECT id, fcm_token, 'Migrated from fcm_token column'
FROM users
WHERE fcm_token IS NOT NULL 
AND fcm_token != ''
AND LENGTH(fcm_token) = 36
ON CONFLICT (player_id) DO NOTHING;

-- 4. Verify the table was created and data migrated
SELECT 'Table created successfully' as status;
SELECT COUNT(*) as total_devices FROM user_devices;
SELECT u.id, u.username, u.nome_completo, COUNT(d.id) as device_count
FROM users u
LEFT JOIN user_devices d ON d.user_id = u.id
GROUP BY u.id, u.username, u.nome_completo
HAVING COUNT(d.id) > 0
ORDER BY device_count DESC;
