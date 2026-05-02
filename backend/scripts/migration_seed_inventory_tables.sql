-- Migration Seed Inventory Tables
-- This script creates the tables for detailed Seed Inventory Management.
-- It assumes the existence of:
--   - organizations (id integer)
--   - storage_locations (id integer)
--   - seedlots (id integer)
--   - users (id integer) (optional, if tracking user_id)

-- 1. Inventory Containers
-- Represents physical containers (e.g., Boxes, Pallets, Bins) that hold items.
CREATE TABLE IF NOT EXISTS inventory_containers (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    container_type VARCHAR(50) NOT NULL, -- 'Box', 'Pallet', 'Bin', 'Shelf'
    storage_location_id INTEGER REFERENCES storage_locations(id) ON DELETE SET NULL,
    parent_container_id INTEGER REFERENCES inventory_containers(id) ON DELETE SET NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventory_container_code UNIQUE (organization_id, code)
);

CREATE INDEX idx_inventory_containers_org_id ON inventory_containers(organization_id);
CREATE INDEX idx_inventory_containers_storage_loc_id ON inventory_containers(storage_location_id);
CREATE INDEX idx_inventory_containers_parent_id ON inventory_containers(parent_container_id);


-- 2. Inventory Items
-- Represents a specific quantity of a Seedlot stored in a Container or Location.
CREATE TABLE IF NOT EXISTS inventory_items (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    seedlot_id INTEGER NOT NULL REFERENCES seedlots(id) ON DELETE CASCADE,
    container_id INTEGER REFERENCES inventory_containers(id) ON DELETE SET NULL,
    quantity FLOAT NOT NULL DEFAULT 0,
    units VARCHAR(20) NOT NULL, -- 'grams', 'seeds', 'kg'
    status VARCHAR(20) DEFAULT 'Available', -- 'Available', 'Reserved', 'Quarantine', 'Expired'
    expiration_date DATE,
    barcode VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_items_org_id ON inventory_items(organization_id);
CREATE INDEX idx_inventory_items_seedlot_id ON inventory_items(seedlot_id);
CREATE INDEX idx_inventory_items_container_id ON inventory_items(container_id);
CREATE INDEX idx_inventory_items_status ON inventory_items(status);


-- 3. Inventory Transactions
-- Tracks all movements and adjustments of Inventory Items.
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'CHECK_IN', 'CHECK_OUT', 'MOVE', 'ADJUSTMENT', 'RESERVATION'
    quantity_change FLOAT NOT NULL, -- Positive for add, Negative for remove
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER, -- Reference to user executing the transaction
    reason TEXT,
    reference_document VARCHAR(100) -- e.g., Order ID, Transfer ID
);

CREATE INDEX idx_inventory_transactions_item_id ON inventory_transactions(inventory_item_id);
CREATE INDEX idx_inventory_transactions_timestamp ON inventory_transactions(timestamp);
CREATE INDEX idx_inventory_transactions_type ON inventory_transactions(transaction_type);
