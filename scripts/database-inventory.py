#!/usr/bin/env python3
"""
Sofia Pulse - Database Inventory Scanner
Professional-grade database analysis (Palantir Foundry style)
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import psycopg2

# Database config
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}


class DatabaseInventory:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
        self.inventory = {
            "scan_time": datetime.now().isoformat(),
            "database": DB_CONFIG["database"],
            "schemas": {},
            "summary": {},
            "issues": [],
        }

    def scan_all(self):
        """Run complete inventory scan"""
        print("=" * 80)
        print("🔍 SOFIA PULSE - DATABASE INVENTORY SCANNER")
        print("=" * 80)
        print(f"\nDatabase: {DB_CONFIG['database']}")
        print(f"Timestamp: {self.inventory['scan_time']}")
        print("\n" + "=" * 80)

        # Scan schemas
        schemas = self.get_schemas()
        print(f"\n📂 Found {len(schemas)} schemas")

        for schema in schemas:
            print(f"\n{'='*80}")
            print(f"📁 SCHEMA: {schema}")
            print("=" * 80)

            self.inventory["schemas"][schema] = {
                "tables": self.scan_tables(schema),
                "views": self.scan_views(schema),
                "functions": self.scan_functions(schema),
                "indexes": self.scan_indexes(schema),
            }

        # Generate summary
        self.generate_summary()

        # Find issues
        self.find_issues()

        # Print summary
        self.print_summary()

        return self.inventory

    def get_schemas(self) -> List[str]:
        """Get all schemas (except system schemas)"""
        self.cursor.execute(
            """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """
        )
        return [row[0] for row in self.cursor.fetchall()]

    def scan_tables(self, schema: str) -> Dict[str, Any]:
        """Scan all tables in schema"""
        print(f"\n  📊 Scanning tables...")

        # Get all tables
        self.cursor.execute(
            """
            SELECT 
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) as size,
                pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) as size_bytes
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) DESC
        """,
            (schema,),
        )

        tables = {}
        for table_name, size, size_bytes in self.cursor.fetchall():
            print(f"    • {table_name}...", end=" ")

            table_info = {
                "name": table_name,
                "size": size,
                "size_bytes": size_bytes,
                "columns": self.get_table_columns(schema, table_name),
                "row_count": self.get_row_count(schema, table_name),
                "primary_key": self.get_primary_key(schema, table_name),
                "foreign_keys": self.get_foreign_keys(schema, table_name),
                "indexes": self.get_table_indexes(schema, table_name),
                "constraints": self.get_constraints(schema, table_name),
                "last_updated": self.get_last_updated(schema, table_name),
            }

            tables[table_name] = table_info
            print(f"{table_info['row_count']:,} rows, {size}")

        return tables

    def get_table_columns(self, schema: str, table: str) -> List[Dict]:
        """Get column information"""
        self.cursor.execute(
            """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """,
            (schema, table),
        )

        columns = []
        for col_name, data_type, max_len, nullable, default in self.cursor.fetchall():
            col_info = {"name": col_name, "type": data_type, "nullable": nullable == "YES", "default": default}
            if max_len:
                col_info["max_length"] = max_len
            columns.append(col_info)

        return columns

    def get_row_count(self, schema: str, table: str) -> int:
        """Get approximate row count"""
        try:
            # Fast estimate from pg_class
            self.cursor.execute(
                """
                SELECT reltuples::bigint 
                FROM pg_class 
                WHERE oid = %s::regclass
            """,
                (f"{schema}.{table}",),
            )
            result = self.cursor.fetchone()
            return int(result[0]) if result else 0
        except:
            return 0

    def get_primary_key(self, schema: str, table: str) -> List[str]:
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
        return [row[0] for row in self.cursor.fetchall()]

    def get_foreign_keys(self, schema: str, table: str) -> List[Dict]:
        """Get foreign key constraints"""
        self.cursor.execute(
            """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = %s
              AND tc.table_name = %s
        """,
            (schema, table),
        )

        fks = []
        for constraint, col, fk_schema, fk_table, fk_col in self.cursor.fetchall():
            fks.append({"constraint": constraint, "column": col, "references": f"{fk_schema}.{fk_table}({fk_col})"})
        return fks

    def get_table_indexes(self, schema: str, table: str) -> List[Dict]:
        """Get indexes for table"""
        self.cursor.execute(
            """
            SELECT
                i.relname as index_name,
                am.amname as index_type,
                pg_size_pretty(pg_relation_size(i.oid)) as index_size,
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
            GROUP BY i.relname, am.amname, i.oid, idx.indisunique, idx.indisprimary
        """,
            (schema, table),
        )

        indexes = []
        for idx_name, idx_type, idx_size, is_unique, is_primary, columns in self.cursor.fetchall():
            indexes.append(
                {
                    "name": idx_name,
                    "type": idx_type,
                    "size": idx_size,
                    "unique": is_unique,
                    "primary": is_primary,
                    "columns": columns,
                }
            )
        return indexes

    def get_constraints(self, schema: str, table: str) -> List[Dict]:
        """Get check constraints"""
        self.cursor.execute(
            """
            SELECT 
                constraint_name,
                check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = %s 
              AND constraint_name IN (
                  SELECT constraint_name 
                  FROM information_schema.table_constraints
                  WHERE table_schema = %s AND table_name = %s
              )
        """,
            (schema, schema, table),
        )

        return [{"name": name, "definition": clause} for name, clause in self.cursor.fetchall()]

    def get_last_updated(self, schema: str, table: str) -> str:
        """Get last updated timestamp if column exists"""
        try:
            # Check if updated_at column exists
            self.cursor.execute(
                """
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                  AND column_name IN ('updated_at', 'last_updated', 'modified_at')
                LIMIT 1
            """,
                (schema, table),
            )

            col = self.cursor.fetchone()
            if col:
                self.cursor.execute(
                    f"""
                    SELECT MAX({col[0]})::text
                    FROM {schema}.{table}
                """
                )
                result = self.cursor.fetchone()
                return result[0] if result and result[0] else "N/A"
        except:
            pass
        return "N/A"

    def scan_views(self, schema: str) -> Dict[str, Any]:
        """Scan all views"""
        print(f"\n  👁️  Scanning views...")

        self.cursor.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = %s
            ORDER BY table_name
        """,
            (schema,),
        )

        views = {}
        for (view_name,) in self.cursor.fetchall():
            print(f"    • {view_name}")

            # Get view definition
            self.cursor.execute(
                """
                SELECT definition
                FROM pg_views
                WHERE schemaname = %s AND viewname = %s
            """,
                (schema, view_name),
            )

            definition = self.cursor.fetchone()
            views[view_name] = {
                "name": view_name,
                "definition": definition[0] if definition else None,
                "columns": self.get_table_columns(schema, view_name),
            }

        return views

    def scan_functions(self, schema: str) -> Dict[str, Any]:
        """Scan all functions"""
        print(f"\n  ⚙️  Scanning functions...")

        self.cursor.execute(
            """
            SELECT 
                p.proname as function_name,
                pg_get_function_result(p.oid) as return_type,
                pg_get_functiondef(p.oid) as definition
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = %s
            ORDER BY p.proname
        """,
            (schema,),
        )

        functions = {}
        for func_name, return_type, definition in self.cursor.fetchall():
            print(f"    • {func_name}() -> {return_type}")
            functions[func_name] = {"name": func_name, "return_type": return_type, "definition": definition}

        return functions

    def scan_indexes(self, schema: str) -> Dict[str, Any]:
        """Scan all indexes (schema-wide)"""
        print(f"\n  🔍 Scanning indexes...")

        self.cursor.execute(
            """
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = %s
            ORDER BY tablename, indexname
        """,
            (schema,),
        )

        indexes = {}
        for schema, table, index, definition in self.cursor.fetchall():
            key = f"{table}.{index}"
            indexes[key] = {"table": table, "name": index, "definition": definition}

        print(f"    Total: {len(indexes)} indexes")
        return indexes

    def generate_summary(self):
        """Generate inventory summary"""
        total_tables = 0
        total_rows = 0
        total_size_bytes = 0
        total_views = 0
        total_functions = 0
        total_indexes = 0

        for schema, data in self.inventory["schemas"].items():
            tables = data.get("tables", {})
            total_tables += len(tables)
            total_views += len(data.get("views", {}))
            total_functions += len(data.get("functions", {}))
            total_indexes += len(data.get("indexes", {}))

            for table, info in tables.items():
                total_rows += info.get("row_count", 0)
                total_size_bytes += info.get("size_bytes", 0)

        self.inventory["summary"] = {
            "total_schemas": len(self.inventory["schemas"]),
            "total_tables": total_tables,
            "total_views": total_views,
            "total_functions": total_functions,
            "total_indexes": total_indexes,
            "total_rows": total_rows,
            "total_size_bytes": total_size_bytes,
            "total_size_human": self.bytes_to_human(total_size_bytes),
        }

    def find_issues(self):
        """Find data quality issues"""
        issues = []

        for schema, data in self.inventory["schemas"].items():
            for table_name, table_info in data.get("tables", {}).items():
                # No primary key
                if not table_info.get("primary_key"):
                    issues.append(
                        {
                            "severity": "HIGH",
                            "type": "NO_PRIMARY_KEY",
                            "table": f"{schema}.{table_name}",
                            "message": f"Table has no primary key",
                        }
                    )

                # No indexes (except primary)
                non_pk_indexes = [idx for idx in table_info.get("indexes", []) if not idx.get("primary")]
                if not non_pk_indexes and table_info.get("row_count", 0) > 1000:
                    issues.append(
                        {
                            "severity": "MEDIUM",
                            "type": "NO_INDEXES",
                            "table": f"{schema}.{table_name}",
                            "message": f"Large table ({table_info['row_count']:,} rows) has no indexes",
                        }
                    )

                # No timestamp tracking
                has_timestamp = any(
                    col["name"] in ["created_at", "updated_at"] for col in table_info.get("columns", [])
                )
                if not has_timestamp:
                    issues.append(
                        {
                            "severity": "LOW",
                            "type": "NO_TIMESTAMPS",
                            "table": f"{schema}.{table_name}",
                            "message": f"Table has no timestamp columns (created_at/updated_at)",
                        }
                    )

        self.inventory["issues"] = issues

    def print_summary(self):
        """Print beautiful summary report"""
        summary = self.inventory["summary"]

        print("\n" + "=" * 80)
        print("📊 INVENTORY SUMMARY")
        print("=" * 80)
        print(f"\nTotal Schemas:    {summary['total_schemas']}")
        print(f"Total Tables:     {summary['total_tables']}")
        print(f"Total Views:      {summary['total_views']}")
        print(f"Total Functions:  {summary['total_functions']}")
        print(f"Total Indexes:    {summary['total_indexes']}")
        print(f"\nTotal Rows:       {summary['total_rows']:,}")
        print(f"Total Storage:    {summary['total_size_human']}")

        # Print top 10 largest tables
        all_tables = []
        for schema, data in self.inventory["schemas"].items():
            for table_name, table_info in data.get("tables", {}).items():
                all_tables.append(
                    {
                        "full_name": f"{schema}.{table_name}",
                        "rows": table_info.get("row_count", 0),
                        "size_bytes": table_info.get("size_bytes", 0),
                        "size": table_info.get("size", "N/A"),
                    }
                )

        all_tables.sort(key=lambda x: x["size_bytes"], reverse=True)

        print("\n" + "=" * 80)
        print("📈 TOP 10 LARGEST TABLES")
        print("=" * 80)
        for i, table in enumerate(all_tables[:10], 1):
            print(f"{i:2}. {table['full_name']:40} {table['rows']:>12,} rows  {table['size']:>10}")

        # Print issues
        if self.inventory["issues"]:
            print("\n" + "=" * 80)
            print("⚠️  DATA QUALITY ISSUES")
            print("=" * 80)

            by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
            for issue in self.inventory["issues"]:
                by_severity[issue["severity"]].append(issue)

            for severity in ["HIGH", "MEDIUM", "LOW"]:
                issues_list = by_severity[severity]
                if issues_list:
                    print(f"\n{severity} ({len(issues_list)} issues):")
                    for issue in issues_list[:10]:  # Show max 10 per severity
                        print(f"  • [{issue['type']}] {issue['table']}: {issue['message']}")
                    if len(issues_list) > 10:
                        print(f"  ... and {len(issues_list) - 10} more")
        else:
            print("\n✅ No data quality issues found!")

    @staticmethod
    def bytes_to_human(bytes_val: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"

    def export_json(self, filename: str):
        """Export inventory to JSON"""
        with open(filename, "w") as f:
            json.dump(self.inventory, f, indent=2, default=str)
        print(f"\n💾 Inventory exported to: {filename}")

    def export_markdown(self, filename: str):
        """Export inventory to Markdown"""
        with open(filename, "w") as f:
            f.write("# Sofia Pulse - Database Inventory\n\n")
            f.write(f"**Generated:** {self.inventory['scan_time']}\n\n")

            summary = self.inventory["summary"]
            f.write("## Summary\n\n")
            f.write(f"- **Total Tables:** {summary['total_tables']}\n")
            f.write(f"- **Total Rows:** {summary['total_rows']:,}\n")
            f.write(f"- **Total Storage:** {summary['total_size_human']}\n")
            f.write(f"- **Total Views:** {summary['total_views']}\n")
            f.write(f"- **Total Functions:** {summary['total_functions']}\n\n")

            for schema, data in self.inventory["schemas"].items():
                f.write(f"## Schema: {schema}\n\n")

                f.write("### Tables\n\n")
                f.write("| Table | Rows | Size | PK | Indexes | Last Updated |\n")
                f.write("|-------|------|------|----|---------|--------------|\n")

                for table_name, table_info in data.get("tables", {}).items():
                    pk = "✅" if table_info.get("primary_key") else "❌"
                    idx_count = len(table_info.get("indexes", []))
                    f.write(
                        f"| {table_name} | {table_info['row_count']:,} | {table_info['size']} | {pk} | {idx_count} | {table_info['last_updated']} |\n"
                    )

                f.write("\n")

        print(f"💾 Inventory exported to: {filename}")


def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1

    try:
        scanner = DatabaseInventory(conn)
        scanner.scan_all()

        # Export reports
        scanner.export_json("database-inventory.json")
        scanner.export_markdown("DATABASE-INVENTORY.md")

        print("\n" + "=" * 80)
        print("✅ INVENTORY SCAN COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
