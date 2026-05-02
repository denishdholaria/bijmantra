-- Create schema manually
-- This is a simplified version for quick setup

CREATE EXTENSION IF NOT EXISTS postgis;

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    contact_email VARCHAR(255),
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations(name);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id);

-- People table
CREATE TABLE IF NOT EXISTS people (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    person_db_id VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    middle_name VARCHAR(100),
    email_address VARCHAR(255),
    phone_number VARCHAR(50),
    mailing_address TEXT,
    user_id VARCHAR(255),
    additional_info JSONB,
    external_references JSONB
);

CREATE INDEX IF NOT EXISTS ix_people_person_db_id ON people(person_db_id);

-- Programs table
CREATE TABLE IF NOT EXISTS programs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    program_db_id VARCHAR(255) UNIQUE,
    program_name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(50),
    objective TEXT,
    lead_person_db_id INTEGER REFERENCES people(id),
    additional_info JSONB,
    external_references JSONB
);

CREATE INDEX IF NOT EXISTS ix_programs_program_db_id ON programs(program_db_id);
CREATE INDEX IF NOT EXISTS ix_programs_program_name ON programs(program_name);
CREATE INDEX IF NOT EXISTS ix_programs_organization_id ON programs(organization_id);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    location_db_id VARCHAR(255) UNIQUE,
    location_name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50),
    abbreviation VARCHAR(50),
    country_name VARCHAR(100),
    country_code VARCHAR(3),
    institute_name VARCHAR(255),
    institute_address TEXT,
    coordinates GEOMETRY(POINT, 4326),
    coordinate_uncertainty VARCHAR(50),
    coordinate_description TEXT,
    altitude VARCHAR(50),
    additional_info JSONB,
    external_references JSONB
);

CREATE INDEX IF NOT EXISTS ix_locations_location_db_id ON locations(location_db_id);
CREATE INDEX IF NOT EXISTS ix_locations_location_name ON locations(location_name);
CREATE INDEX IF NOT EXISTS idx_locations_coordinates ON locations USING GIST(coordinates);

-- Trials table
CREATE TABLE IF NOT EXISTS trials (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    program_id INTEGER NOT NULL REFERENCES programs(id),
    location_id INTEGER REFERENCES locations(id),
    trial_db_id VARCHAR(255) UNIQUE,
    trial_name VARCHAR(255) NOT NULL,
    trial_description TEXT,
    trial_type VARCHAR(100),
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    common_crop_name VARCHAR(100),
    document_ids JSONB,
    additional_info JSONB,
    external_references JSONB
);

CREATE INDEX IF NOT EXISTS ix_trials_trial_db_id ON trials(trial_db_id);
CREATE INDEX IF NOT EXISTS ix_trials_trial_name ON trials(trial_name);
CREATE INDEX IF NOT EXISTS ix_trials_program_id ON trials(program_id);
CREATE INDEX IF NOT EXISTS ix_trials_organization_id ON trials(organization_id);

-- Studies table
CREATE TABLE IF NOT EXISTS studies (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    trial_id INTEGER NOT NULL REFERENCES trials(id),
    location_id INTEGER REFERENCES locations(id),
    study_db_id VARCHAR(255) UNIQUE,
    study_name VARCHAR(255) NOT NULL,
    study_description TEXT,
    study_type VARCHAR(100),
    study_code VARCHAR(100),
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    common_crop_name VARCHAR(100),
    cultural_practices TEXT,
    observation_levels JSONB,
    observation_units_description TEXT,
    license VARCHAR(255),
    data_links JSONB,
    additional_info JSONB,
    external_references JSONB
);

CREATE INDEX IF NOT EXISTS ix_studies_study_db_id ON studies(study_db_id);
CREATE INDEX IF NOT EXISTS ix_studies_study_name ON studies(study_name);
CREATE INDEX IF NOT EXISTS ix_studies_trial_id ON studies(trial_id);
CREATE INDEX IF NOT EXISTS ix_studies_organization_id ON studies(organization_id);

-- Insert default organization
INSERT INTO organizations (name, description, contact_email)
VALUES ('Default Organization', 'Default organization for Bijmantra', 'admin@example.org')
ON CONFLICT (name) DO NOTHING;

-- Insert admin user (password: admin123, hashed with bcrypt)
INSERT INTO users (organization_id, email, hashed_password, full_name, is_active, is_superuser)
SELECT 
    id,
    'admin@example.org',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeWG3xck5.Ky',
    'Admin User',
    TRUE,
    TRUE
FROM organizations WHERE name = 'Default Organization'
ON CONFLICT (email) DO NOTHING;
