import sqlite3
import unittest
from pathlib import Path

# Job D15: Test migration_seed_inventory_tables.sql
# Ensures the raw SQL script is valid and can create tables correctly.

class TestMigrationSeedInventory(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON;")

        # Create mock tables required for FKs
        self.cursor.executescript("""
            CREATE TABLE organizations (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE storage_locations (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE seedlots (id INTEGER PRIMARY KEY, name TEXT);
            -- Insert dummy data
            INSERT INTO organizations (id, name) VALUES (1, 'Org 1');
            INSERT INTO storage_locations (id, name) VALUES (1, 'Loc 1');
            INSERT INTO seedlots (id, name) VALUES (1, 'Seedlot 1');
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_migration_execution(self):
        # 1. Read the SQL file
        sql_path = Path("backend/scripts/migration_seed_inventory_tables.sql")
        if not sql_path.exists():
            self.fail(f"SQL file not found at {sql_path}")

        sql_content = sql_path.read_text()

        # 2. Pre-process for SQLite compatibility
        # Replace PostgreSQL specific syntax
        sqlite_sql = sql_content.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sqlite_sql = sqlite_sql.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP")
        sqlite_sql = sqlite_sql.replace("ON DELETE SET NULL", "ON DELETE SET NULL") # supported
        sqlite_sql = sqlite_sql.replace("ON DELETE CASCADE", "ON DELETE CASCADE") # supported

        # Remove partial index if any (Postgres specific WHERE clause in index) - not used here but good practice

        # 3. Execute the SQL
        try:
            self.cursor.executescript(sqlite_sql)
            self.conn.commit()
        except sqlite3.Error as e:
            self.fail(f"SQL execution failed: {e}")

        # 4. Verify tables exist
        tables = ["inventory_containers", "inventory_items", "inventory_transactions"]
        for table in tables:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            result = self.cursor.fetchone()
            self.assertIsNotNone(result, f"Table {table} was not created")

        # 5. Test Constraints & Inserts

        # Insert Container
        try:
            self.cursor.execute("""
                INSERT INTO inventory_containers (organization_id, code, container_type, storage_location_id)
                VALUES (1, 'CONT-001', 'Box', 1)
            """)
        except sqlite3.Error as e:
            self.fail(f"Failed to insert container: {e}")

        # Verify Unique Constraint on Container Code
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("""
                INSERT INTO inventory_containers (organization_id, code, container_type, storage_location_id)
                VALUES (1, 'CONT-001', 'Pallet', 1)
            """)

        # Insert Item
        try:
            container_id = self.cursor.execute("SELECT id FROM inventory_containers WHERE code='CONT-001'").fetchone()[0]
            self.cursor.execute(f"""
                INSERT INTO inventory_items (organization_id, seedlot_id, container_id, quantity, units)
                VALUES (1, 1, {container_id}, 100.5, 'grams')
            """)
        except sqlite3.Error as e:
            self.fail(f"Failed to insert item: {e}")

        # Insert Transaction
        try:
            item_id = self.cursor.execute("SELECT id FROM inventory_items LIMIT 1").fetchone()[0]
            self.cursor.execute(f"""
                INSERT INTO inventory_transactions (inventory_item_id, transaction_type, quantity_change, reason)
                VALUES ({item_id}, 'CHECK_IN', 100.5, 'Initial Stock')
            """)
        except sqlite3.Error as e:
            self.fail(f"Failed to insert transaction: {e}")

if __name__ == '__main__':
    unittest.main()
