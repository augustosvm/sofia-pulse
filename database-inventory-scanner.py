#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
SOFIA PULSE - DATABASE INVENTORY SCANNER (PALANTIR FOUNDRY STYLE)
════════════════════════════════════════════════════════════════════════════════

Comprehensive database scanner that generates professional inventory reports
similar to Palantir Foundry's data catalog.

Features:
- Complete table metadata (columns, types, indexes, constraints)
- Vector column detection (pgvector)
- Row counts and storage sizes
- Data quality checks (missing PKs, indexes, timestamps)
- Foreign key relationships
- Last update timestamps
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from collections import defaultdict
import json

class DatabaseInventoryScanner:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            user=os.getenv('POSTGRES_USER', 'sofia'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'sofia_db')
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        self.inventory = {
            'scan_time': datetime.now().isoformat(),
            'schemas': {},
            'summary': {
                'total_tables': 0,
                'total_views': 0,
                'total_functions': 0,
                'total_indexes': 0,
                'total_rows': 0,
                'total_storage_mb': 0
            },
            'quality_issues': {
                'missing_primary_keys': [],
                'missing_indexes': [],
                'missing_timestamps': [],
                'empty_tables': []
            }
        }
    
    def scan_schemas(self):
        """Get all schemas (excluding system schemas)"""
        self.cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        return [row['schema_name'] for row in self.cur.fetchall()]
    
    def scan_tables(self, schema):
        """Get all tables in schema"""
        self.cur.execute("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = %s
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """, (schema,))
        return self.cur.fetchall()
    
    def scan_views(self, schema):
        """Get all views in schema"""
        self.cur.execute("""
            SELECT viewname 
            FROM pg_views 
            WHERE schemaname = %s
            ORDER BY viewname
        """, (schema,))
        return [row['viewname'] for row in self.cur.fetchall()]
    
    def scan_functions(self, schema):
        """Get all functions in schema"""
        self.cur.execute("""
            SELECT 
                p.proname as function_name,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_function_result(p.oid) as return_type
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = %s
            ORDER BY p.proname
        """, (schema,))
        return self.cur.fetchall()
    
    def get_table_row_count(self, schema, table):
        """Get row count for table"""
        try:
            self.cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
            return self.cur.fetchone()['count']
        except Exception as e:
            return 0
    
    def get_table_columns(self, schema, table):
        """Get column information for table"""
        self.cur.execute("""
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table))
        return self.cur.fetchall()
    
    def get_vector_columns(self, schema, table):
        """Detect pgvector columns"""
        self.cur.execute("""
            SELECT 
                column_name,
                udt_name,
                (string_to_array(column_name, '_'))[array_length(string_to_array(column_name, '_'), 1)] as potential_dim
            FROM information_schema.columns
            WHERE table_schema = %s 
              AND table_name = %s
              AND udt_name = 'vector'
        """, (schema, table))
        return self.cur.fetchall()
    
    def get_table_indexes(self, schema, table):
        """Get indexes for table"""
        self.cur.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
        """, (schema, table))
        return self.cur.fetchall()
    
    def get_primary_key(self, schema, table):
        """Get primary key constraint"""
        self.cur.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
        """, (f"{schema}.{table}",))
        return [row['attname'] for row in self.cur.fetchall()]
    
    def get_foreign_keys(self, schema, table):
        """Get foreign key constraints"""
        self.cur.execute("""
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
        """, (schema, table))
        return self.cur.fetchall()
    
    def get_last_update(self, schema, table, columns):
        """Try to get last update timestamp"""
        timestamp_cols = ['updated_at', 'created_at', 'timestamp', 'date']
        col_names = [col['column_name'] for col in columns]
        
        for ts_col in timestamp_cols:
            if ts_col in col_names:
                try:
                    self.cur.execute(f"SELECT MAX({ts_col}) as last_update FROM {schema}.{table}")
                    result = self.cur.fetchone()
                    if result and result['last_update']:
                        return result['last_update']
                except:
                    continue
        return None
    
    def analyze_table(self, schema, table_info):
        """Comprehensive table analysis"""
        table = table_info['tablename']
        
        # Basic info
        row_count = self.get_table_row_count(schema, table)
        columns = self.get_table_columns(schema, table)
        vector_cols = self.get_vector_columns(schema, table)
        indexes = self.get_table_indexes(schema, table)
        primary_key = self.get_primary_key(schema, table)
        foreign_keys = self.get_foreign_keys(schema, table)
        last_update = self.get_last_update(schema, table, columns)
        
        # Data quality checks
        if not primary_key:
            self.inventory['quality_issues']['missing_primary_keys'].append(f"{schema}.{table}")
        
        if len(indexes) == 0:
            self.inventory['quality_issues']['missing_indexes'].append(f"{schema}.{table}")
        
        if row_count == 0:
            self.inventory['quality_issues']['empty_tables'].append(f"{schema}.{table}")
        
        has_timestamp = any(col['column_name'] in ['created_at', 'updated_at'] for col in columns)
        if not has_timestamp:
            self.inventory['quality_issues']['missing_timestamps'].append(f"{schema}.{table}")
        
        return {
            'name': table,
            'row_count': row_count,
            'column_count': len(columns),
            'columns': [
                {
                    'name': col['column_name'],
                    'type': col['data_type'],
                    'udt_name': col['udt_name'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                }
                for col in columns
            ],
            'vector_columns': [
                {
                    'name': vc['column_name'],
                    'type': vc['udt_name']
                }
                for vc in vector_cols
            ],
            'indexes': [
                {
                    'name': idx['indexname'],
                    'definition': idx['indexdef']
                }
                for idx in indexes
            ],
            'primary_key': primary_key,
            'foreign_keys': [
                {
                    'column': fk['column_name'],
                    'references': f"{fk['foreign_table_schema']}.{fk['foreign_table_name']}.{fk['foreign_column_name']}"
                }
                for fk in foreign_keys
            ],
            'size_bytes': table_info['size_bytes'],
            'size_pretty': table_info['size_pretty'],
            'last_update': last_update.isoformat() if last_update else None
        }
    
    def scan(self):
        """Run complete database scan"""
        print("═" * 80)
        print("SOFIA PULSE - DATABASE INVENTORY SCANNER")
        print("═" * 80)
        print(f"Scan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        schemas = self.scan_schemas()
        
        for schema in schemas:
            print(f"\n📂 Scanning schema: {schema}")
            
            schema_data = {
                'tables': {},
                'views': [],
                'functions': []
            }
            
            # Scan tables
            tables = self.scan_tables(schema)
            print(f"   Found {len(tables)} tables")
            
            for table_info in tables:
                table = table_info['tablename']
                print(f"   ├─ Analyzing {table}...", end=' ')
                
                table_data = self.analyze_table(schema, table_info)
                schema_data['tables'][table] = table_data
                
                # Update summary
                self.inventory['summary']['total_tables'] += 1
                self.inventory['summary']['total_rows'] += table_data['row_count']
                self.inventory['summary']['total_storage_mb'] += table_info['size_bytes'] / (1024 * 1024)
                self.inventory['summary']['total_indexes'] += len(table_data['indexes'])
                
                print(f"✓ ({table_data['row_count']:,} rows)")
            
            # Scan views
            views = self.scan_views(schema)
            schema_data['views'] = views
            self.inventory['summary']['total_views'] += len(views)
            if views:
                print(f"   Found {len(views)} views")
            
            # Scan functions
            functions = self.scan_functions(schema)
            schema_data['functions'] = [
                {
                    'name': f['function_name'],
                    'arguments': f['arguments'],
                    'return_type': f['return_type']
                }
                for f in functions
            ]
            self.inventory['summary']['total_functions'] += len(functions)
            if functions:
                print(f"   Found {len(functions)} functions")
            
            self.inventory['schemas'][schema] = schema_data
        
        return self.inventory
    
    def generate_report(self):
        """Generate comprehensive text report"""
        inv = self.inventory
        summary = inv['summary']
        
        report = []
        report.append("═" * 80)
        report.append("SOFIA PULSE - DATABASE INVENTORY REPORT")
        report.append("═" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("📊 INVENTORY SUMMARY")
        report.append("─" * 80)
        report.append(f"Total Tables:    {summary['total_tables']:,}")
        report.append(f"Total Views:     {summary['total_views']:,}")
        report.append(f"Total Functions: {summary['total_functions']:,}")
        report.append(f"Total Indexes:   {summary['total_indexes']:,}")
        report.append(f"Total Rows:      {summary['total_rows']:,}")
        report.append(f"Total Storage:   {summary['total_storage_mb']:.2f} MB")
        report.append("")
        
        # Top 10 largest tables
        report.append("📦 TOP 10 LARGEST TABLES")
        report.append("─" * 80)
        
        all_tables = []
        for schema, schema_data in inv['schemas'].items():
            for table_name, table_data in schema_data['tables'].items():
                all_tables.append({
                    'schema': schema,
                    'name': table_name,
                    'rows': table_data['row_count'],
                    'size_mb': table_data['size_bytes'] / (1024 * 1024),
                    'size_pretty': table_data['size_pretty']
                })
        
        all_tables.sort(key=lambda x: x['size_mb'], reverse=True)
        
        for i, t in enumerate(all_tables[:10], 1):
            pct = (t['size_mb'] / summary['total_storage_mb'] * 100) if summary['total_storage_mb'] > 0 else 0
            report.append(f"{i:2}. {t['schema']}.{t['name']:<40} {t['rows']:>12,} rows  {t['size_pretty']:>10}  ({pct:.1f}%)")
        
        report.append("")
        
        # Detailed table inventory (Palantir style)
        report.append("📋 DETAILED TABLE INVENTORY")
        report.append("═" * 80)
        
        for schema, schema_data in inv['schemas'].items():
            report.append(f"\nSchema: {schema}")
            report.append("─" * 80)
            
            # Sort tables by row count (descending)
            sorted_tables = sorted(
                schema_data['tables'].items(),
                key=lambda x: x[1]['row_count'],
                reverse=True
            )
            
            for table_name, table_data in sorted_tables:
                report.append(f"\nTable: {table_name}")
                report.append(f"  Records:      {table_data['row_count']:,}")
                report.append(f"  Columns:      {table_data['column_count']}")
                report.append(f"  Storage:      {table_data['size_pretty']}")
                
                if table_data['vector_columns']:
                    for vc in table_data['vector_columns']:
                        report.append(f"  Vector:       {vc['name']} ({vc['type']})")
                
                if table_data['last_update']:
                    report.append(f"  Last update:  {table_data['last_update']}")
                
                if table_data['primary_key']:
                    report.append(f"  Primary key:  {', '.join(table_data['primary_key'])}")
                
                if table_data['indexes']:
                    idx_names = [idx['name'] for idx in table_data['indexes']]
                    report.append(f"  Indexes:      {', '.join(idx_names)}")
                
                if table_data['foreign_keys']:
                    report.append(f"  Foreign keys: {len(table_data['foreign_keys'])}")
        
        # Data quality issues
        report.append("")
        report.append("⚠️  DATA QUALITY ISSUES")
        report.append("═" * 80)
        
        issues = inv['quality_issues']
        
        if issues['missing_primary_keys']:
            report.append(f"\n🔴 HIGH PRIORITY: {len(issues['missing_primary_keys'])} tables without primary keys:")
            for table in issues['missing_primary_keys']:
                report.append(f"   - {table}")
        
        if issues['missing_indexes']:
            report.append(f"\n🟡 MEDIUM PRIORITY: {len(issues['missing_indexes'])} tables without indexes:")
            for table in issues['missing_indexes'][:10]:  # Show first 10
                report.append(f"   - {table}")
            if len(issues['missing_indexes']) > 10:
                report.append(f"   ... and {len(issues['missing_indexes']) - 10} more")
        
        if issues['empty_tables']:
            report.append(f"\n🔵 INFO: {len(issues['empty_tables'])} empty tables:")
            for table in issues['empty_tables'][:10]:
                report.append(f"   - {table}")
            if len(issues['empty_tables']) > 10:
                report.append(f"   ... and {len(issues['empty_tables']) - 10} more")
        
        if issues['missing_timestamps']:
            report.append(f"\n🟠 LOW PRIORITY: {len(issues['missing_timestamps'])} tables without timestamp columns:")
            for table in issues['missing_timestamps'][:10]:
                report.append(f"   - {table}")
            if len(issues['missing_timestamps']) > 10:
                report.append(f"   ... and {len(issues['missing_timestamps']) - 10} more")
        
        report.append("")
        report.append("═" * 80)
        report.append("END OF REPORT")
        report.append("═" * 80)
        
        return "\n".join(report)
    
    def save_reports(self, base_path="."):
        """Save inventory to JSON and text report"""
        # Save JSON
        json_path = f"{base_path}/database-inventory.json"
        with open(json_path, 'w') as f:
            json.dump(self.inventory, f, indent=2, default=str)
        print(f"\n✅ JSON inventory saved to: {json_path}")
        
        # Save text report
        report = self.generate_report()
        txt_path = f"{base_path}/DATABASE-INVENTORY-REPORT.txt"
        with open(txt_path, 'w') as f:
            f.write(report)
        print(f"✅ Text report saved to: {txt_path}")
        
        return json_path, txt_path

if __name__ == '__main__':
    scanner = DatabaseInventoryScanner()
    scanner.scan()
    json_file, txt_file = scanner.save_reports()
    
    print("\n" + scanner.generate_report())
