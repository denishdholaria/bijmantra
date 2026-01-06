-- Create user with your credentials
-- Password: 22225656 (hashed with bcrypt)

INSERT INTO users (organization_id, email, hashed_password, full_name, is_active, is_superuser)
SELECT 
    id,
    'denishdholaria@gmail.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQkTnkEXvvEKuvxwVinIu',
    'Denish Dholaria',
    TRUE,
    TRUE
FROM organizations WHERE name = 'Default Organization'
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    full_name = EXCLUDED.full_name;
