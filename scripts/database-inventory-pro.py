#!/usr/bin/env python3
"""
Sofia Pulse - Professional Database Inventory (Palantir Foundry Style)
Detects: tables, views, functions, indexes, vector columns, constraints
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}


class ProfessionalInventory:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    def scan_and_report(self):
        """Run complete professional scan"""
        print("\n" + "=" * 80)
        print("🔍 SOFIA PULSE - PROFESSIONAL DATABASE INVENTORY")
        print("=" * 80)
        print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Get schemas
        schemas = self.get_user_schemas()

        # Global summary
        total_tables = 0
        total_rows = 0
        total_size = 0
        total_vector_cols = 0

        for schema in schemas:
            tables = self.get_schema_tables(schema)

            for table in tables:
                try:
                    total_tables += 1
                    info = self.analyze_table(schema, table)
                except Exception as e:
                    print(f"⚠️  Skipping {schema}.{table}: {str(e)[:100]}")
                    self.conn.rollback()
                    continue

                total_rows += info["row_count"]
                total_size += info["size_bytes"]
                total_vector_cols += len(info["vector_columns"])

                # Print table info (Palantir style)
                self.print_table_info(schema, table, info)

        # Print summary
        print("\n" + "=" * 80)
        print("📊 INVENTORY SUMMARY")
        print("=" * 80)
        print(f"Total Tables:        {total_tables}")
        print(f"Total Rows:          {total_rows:,}")
        print(f"Total Storage:       {self.bytes_to_human(total_size)}")
        print(f"Vector Columns:      {total_vector_cols}")
        print("=" * 80)

    def get_user_schemas(self) -> List[str]:
        """Get user schemas (exclude system)"""
        self.cursor.execute(
            """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_schema_tables(self, schema: str) -> List[str]:
        """Get all tables in schema"""
        self.cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """,
            (schema,),
        )
        return [row[0] for row in self.cursor.fetchall()]

    def analyze_table(self, schema: str, table: str) -> Dict[str, Any]:
        """Deep analysis of a single table"""

        # Basic info
        self.cursor.execute(
            """
            SELECT 
                pg_size_pretty(pg_total_relation_size(%s::regclass)) as size,
                pg_total_relation_size(%s::regclass) as size_bytes
        """,
            (f"{schema}.{table}", f"{schema}.{table}"),
        )
        size, size_bytes = self.cursor.fetchone()

        # Row count (fast estimate)
        self.cursor.execute(
            """
            SELECT reltuples::bigint 
            FROM pg_class 
            WHERE oid = %s::regclass
        """,
            (f"{schema}.{table}",),
        )
        row_count = int(self.cursor.fetchone()[0] or 0)

        # Columns
        columns = self.get_columns(schema, table)

        # Vector columns
        vector_cols = self.get_vector_columns(schema, table)

        # Primary key
        pk = self.get_primary_key(schema, table)

        # Foreign keys
        fks = self.get_foreign_keys(schema, table)

        # Indexes
        indexes = self.get_indexes(schema, table)

        # Last update timestamp
        last_update = self.get_last_update(schema, table)

        return {
            "size": size,
            "size_bytes": size_bytes,
            "row_count": row_count,
            "columns": columns,
            "column_count": len(columns),
            "vector_columns": vector_cols,
            "primary_key": pk,
            "foreign_keys": fks,
            "indexes": indexes,
            "last_update": last_update,
        }

    def get_columns(self, schema: str, table: str) -> List[Dict]:
        """Get all columns with types"""
        self.cursor.execute(
            """
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """,
            (schema, table),
        )

        columns = []
        for col_name, data_type, udt_name, max_len, nullable in self.cursor.fetchall():
            col = {
                "name": col_name,
                "type": data_type if data_type != "USER-DEFINED" else udt_name,
                "nullable": nullable == "YES",
            }
            if max_len:
                col["max_length"] = max_len
            columns.append(col)
        return columns

    def get_vector_columns(self, schema: str, table: str) -> List[Dict]:
        """Detect pgvector columns"""
        self.cursor.execute(
            """
            SELECT 
                a.attname,
                t.typname,
                CASE 
                    WHEN t.typname = 'vector' THEN 
                        -- Extract dimension from typmod
                        (a.atttypmod - 4) / 8
                    ELSE NULL
                END as dimension
            FROM pg_attribute a
            JOIN pg_type t ON a.atttypid = t.oid
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s 
              AND c.relname = %s
              AND a.attnum > 0
              AND NOT a.attisdropped
              AND t.typname IN ('vector', 'halfvec', 'sparsevec')
        """,
            (schema, table),
        )

        vectors = []
        for col_name, typ, dim in self.cursor.fetchall():
            vectors.append({"name": col_name, "type": typ, "dimension": dim})
        return vectors

    def get_primary_key(self, schema: str, table: str) -> Optional[List[str]]:
        """Get primary key columns"""
        self.cursor.execute(
            """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
        """,
            (f"{schema}.{table}",),
        )

        cols = [row[0] for row in self.cursor.fetchall()]
        return cols if cols else None

    def get_foreign_keys(self, schema: str, table: str) -> List[Dict]:
        """Get foreign key constraints"""
        self.cursor.execute(
            """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = %s
              AND tc.table_name = %s
        """,
            (schema, table),
        )

        return [
            {"column": col, "references": f"{fk_table}({fk_col})"} for col, fk_table, fk_col in self.cursor.fetchall()
        ]

    def get_indexes(self, schema: str, table: str) -> List[Dict]:
        """Get all indexes including vector indexes"""
        self.cursor.execute(
            """
            SELECT
                i.relname as index_name,
                am.amname as index_type,
                idx.indisunique as is_unique,
                idx.indisprimary as is_primary,
                array_to_string(array_agg(a.attname), ', ') as columns
            FROM pg_index idx
            JOIN pg_class i ON i.oid = idx.indexrelid
            JOIN pg_am am ON i.relam = am.oid
            JOIN pg_class t ON t.oid = idx.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
            WHERE n.nspname = %s AND t.relname = %s
            GROUP BY i.relname, am.amname, idx.indisunique, idx.indisprimary
        """,
            (schema, table),
        )

        indexes = []
        for idx_name, idx_type, is_unique, is_primary, columns in self.cursor.fetchall():
            idx = {"name": idx_name, "type": idx_type, "unique": is_unique, "primary": is_primary, "columns": columns}
            indexes.append(idx)
        return indexes

    def get_last_update(self, schema: str, table: str) -> str:
        """Get last update timestamp"""
        try:
            self.conn.rollback()  # Clear any previous errors
            # Try common timestamp column names
            for col in ["updated_at", "last_updated", "modified_at", "timestamp"]:
                try:
                    self.cursor.execute(
                        f"""
                        SELECT MAX({col})::text
                        FROM {schema}.{table}
                        WHERE {col} IS NOT NULL
                    """
                    )
                    result = self.cursor.fetchone()
                    if result and result[0]:
                        return result[0]
                except:
                    continue
        except:
            pass
        return "N/A"

    def print_table_info(self, schema: str, table: str, info: Dict):
        """Print table info in Palantir Foundry style"""
        print("\n" + "-" * 80)
        print(f"📊 Table: {schema}.{table}")
        print("-" * 80)
        print(f"Records:             {info['row_count']:,}")
        print(f"Columns:             {info['column_count']}")
        print(f"Size:                {info['size']}")

        # Vector columns (if any)
        if info["vector_columns"]:
            print(f"Vector columns:      ", end="")
            for i, vec in enumerate(info["vector_columns"]):
                if i > 0:
                    print("                     ", end="")
                dim_str = f"({vec['dimension']}d)" if vec["dimension"] else ""
                print(f"{vec['name']} {dim_str}")

        # Last update
        if info["last_update"] != "N/A":
            print(f"Last update:         {info['last_update']}")

        # Primary key
        if info["primary_key"]:
            print(f"Primary key:         {', '.join(info['primary_key'])}")
        else:
            print(f"Primary key:         ❌ MISSING")

        # Foreign keys
        if info["foreign_keys"]:
            print(f"Foreign keys:        {len(info['foreign_keys'])}")
            for fk in info["foreign_keys"][:3]:  # Show max 3
                print(f"                     {fk['column']} → {fk['references']}")
            if len(info["foreign_keys"]) > 3:
                print(f"                     ... and {len(info['foreign_keys']) - 3} more")

        # Indexes
        idx_names = []
        for idx in info["indexes"]:
            if idx["type"] == "hnsw":
                idx_names.append(f"{idx['name']} (HNSW)")
            elif idx["type"] == "ivfflat":
                idx_names.append(f"{idx['name']} (IVFFlat)")
            elif idx["primary"]:
                idx_names.append(f"{idx['name']} (PK)")
            elif idx["unique"]:
                idx_names.append(f"{idx['name']} (unique)")
            else:
                idx_names.append(idx["name"])

        if idx_names:
            print(f"Indexes:             {', '.join(idx_names)}")
        else:
            print(f"Indexes:             ⚠️  None")

    @staticmethod
    def bytes_to_human(b: int) -> str:
        """Convert bytes to human readable"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024.0:
                return f"{b:.1f} {unit}"
            b /= 1024.0
        return f"{b:.1f} PB"


def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1

    try:
        inventory = ProfessionalInventory(conn)
        inventory.scan_and_report()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
