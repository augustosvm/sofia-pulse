#!/usr/bin/env python3
"""
Error Analyzer - Parse and categorize collector errors
"""

import re
from typing import Dict, Tuple, Optional

class ErrorAnalyzer:
    """Analyze and categorize collector errors"""

    @staticmethod
    def analyze_error(error_text: str) -> Tuple[str, str, str]:
        """
        Analyze error text and return (category, short_msg, details)

        Returns:
            category: SQL Error, API Error, Network Error, etc.
            short_msg: Brief 1-line description
            details: Relevant error details (table, API, etc.)
        """

        error_lower = error_text.lower()

        # SQL ERRORS
        if 'duplicate key' in error_lower or 'unique constraint' in error_lower:
            table = ErrorAnalyzer._extract_table(error_text)
            return ('SQL: Duplicate Key',
                    f'Duplicate record in {table}',
                    f'Table: {table}')

        if 'column' in error_lower and 'does not exist' in error_lower:
            column = ErrorAnalyzer._extract_column(error_text)
            return ('SQL: Missing Column',
                    f'Column {column} does not exist',
                    f'Column: {column}')

        if 'relation' in error_lower and 'does not exist' in error_lower:
            table = ErrorAnalyzer._extract_table(error_text)
            return ('SQL: Missing Table',
                    f'Table {table} does not exist',
                    f'Table: {table}')

        if 'value too long' in error_lower or 'varchar' in error_lower:
            match = re.search(r'character varying\((\d+)\)', error_text)
            limit = match.group(1) if match else 'unknown'
            return ('SQL: Value Too Long',
                    f'VARCHAR limit exceeded ({limit} chars)',
                    f'Limit: {limit} characters')

        if 'foreign key' in error_lower or 'violates foreign' in error_lower:
            table = ErrorAnalyzer._extract_table(error_text)
            return ('SQL: Foreign Key Violation',
                    f'Invalid reference in {table}',
                    f'Table: {table}')

        if 'syntax error' in error_lower and 'sql' in error_lower:
            return ('SQL: Syntax Error',
                    'Invalid SQL syntax',
                    'Check query syntax')

        # API ERRORS
        if '401' in error_text or 'unauthorized' in error_lower or 'api key' in error_lower:
            api = ErrorAnalyzer._extract_api_domain(error_text)
            return ('API: Missing/Invalid Key',
                    f'{api} requires API key',
                    f'API: {api}')

        if 'subscription key' in error_lower:
            api = ErrorAnalyzer._extract_api_domain(error_text)
            return ('API: Subscription Required',
                    f'{api} now requires subscription',
                    f'API: {api}')

        if '403' in error_text or 'forbidden' in error_lower:
            api = ErrorAnalyzer._extract_api_domain(error_text)
            return ('API: Forbidden',
                    f'{api} blocked request',
                    f'API: {api}')

        if '429' in error_text or 'rate limit' in error_lower:
            api = ErrorAnalyzer._extract_api_domain(error_text)
            return ('API: Rate Limit',
                    f'{api} rate limit exceeded',
                    f'API: {api}')

        if '404' in error_text or 'not found' in error_lower:
            api = ErrorAnalyzer._extract_api_domain(error_text)
            return ('API: Not Found',
                    f'{api} endpoint not found',
                    f'API: {api}')

        if '500' in error_text or '502' in error_text or '503' in error_text:
            api = ErrorAnalyzer._extract_api_domain(error_text)
            return ('API: Server Error',
                    f'{api} server error',
                    f'API: {api}')

        # NETWORK ERRORS
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return ('Network: Timeout',
                    'Connection timed out',
                    'Check network/firewall')

        if 'connection refused' in error_lower:
            return ('Network: Connection Refused',
                    'Connection refused by host',
                    'Check service is running')

        if 'name or service not known' in error_lower or 'dns' in error_lower:
            return ('Network: DNS Error',
                    'Cannot resolve hostname',
                    'Check DNS/internet')

        # DATA/PARSING ERRORS
        if 'json' in error_lower and ('parse' in error_lower or 'decode' in error_lower):
            return ('Data: JSON Parse Error',
                    'Invalid JSON response',
                    'API returned malformed JSON')

        if 'unexpected' in error_lower and 'format' in error_lower:
            return ('Data: Format Error',
                    'Unexpected data format',
                    'API response structure changed')

        # MODULE/IMPORT ERRORS
        if 'no module named' in error_lower or 'import' in error_lower:
            module = ErrorAnalyzer._extract_module(error_text)
            return ('Setup: Missing Module',
                    f'Missing Python module: {module}',
                    f'Run: pip install {module}')

        if 'command not found' in error_lower:
            cmd = ErrorAnalyzer._extract_command(error_text)
            return ('Setup: Missing Command',
                    f'Command not found: {cmd}',
                    f'Install: {cmd}')

        # FILE ERRORS
        if 'no such file' in error_lower or 'file not found' in error_lower:
            return ('File: Not Found',
                    'Required file missing',
                    'Check file paths')

        if 'permission denied' in error_lower:
            return ('File: Permission Denied',
                    'Insufficient permissions',
                    'Check file/directory permissions')

        # GENERIC
        return ('Unknown Error',
                error_text[:100],
                'Check full logs for details')

    @staticmethod
    def _extract_table(text: str) -> str:
        """Extract table name from error"""
        # Try: relation "table_name" does not exist
        match = re.search(r'relation "([^"]+)"', text)
        if match:
            return match.group(1)

        # Try: table_name
        match = re.search(r'table[:\s]+(\w+)', text, re.IGNORECASE)
        if match:
            return match.group(1)

        return 'unknown'

    @staticmethod
    def _extract_column(text: str) -> str:
        """Extract column name from error"""
        match = re.search(r'column "([^"]+)"', text)
        if match:
            return match.group(1)

        match = re.search(r'column[:\s]+(\w+)', text, re.IGNORECASE)
        if match:
            return match.group(1)

        return 'unknown'

    @staticmethod
    def _extract_api_domain(text: str) -> str:
        """Extract API domain from error"""
        # Extract URL
        match = re.search(r'https?://([^/\s]+)', text)
        if match:
            domain = match.group(1)
            # Simplify domain
            if 'api.' in domain:
                domain = domain.replace('api.', '')
            if 'www.' in domain:
                domain = domain.replace('www.', '')
            return domain

        # Check for known API names
        known_apis = ['github', 'reddit', 'worldbank', 'openalex', 'nih', 'who', 'unicef', 'worldbank']
        for api in known_apis:
            if api in text.lower():
                return api.title()

        return 'Unknown API'

    @staticmethod
    def _extract_module(text: str) -> str:
        """Extract module name from import error"""
        match = re.search(r"No module named '([^']+)'", text)
        if match:
            return match.group(1)

        match = re.search(r'import (\w+)', text)
        if match:
            return match.group(1)

        return 'unknown'

    @staticmethod
    def _extract_command(text: str) -> str:
        """Extract command from 'command not found' error"""
        match = re.search(r'command not found[:\s]+(\w+)', text, re.IGNORECASE)
        if match:
            return match.group(1)

        return 'unknown'


    @staticmethod
    def format_for_whatsapp(collector_name: str, category: str, short_msg: str, details: str) -> str:
        """Format error for WhatsApp message"""
        return f"""❌ {collector_name}
{category}
{short_msg}
{details}"""


# Quick test
if __name__ == '__main__':
    analyzer = ErrorAnalyzer()

    # Test cases
    tests = [
        'ERROR: duplicate key value violates unique constraint "bacen_series_pkey"',
        '401 Client Error: Access Denied for url: https://api.worldbank.org/v2/...',
        'psycopg2.errors.UndefinedColumn: column "project_number" does not exist',
        'value too long for type character varying(50)',
        'requests.exceptions.Timeout: Connection timed out after 30s',
        'No module named "pandas"',
    ]

    for test in tests:
        category, short, details = analyzer.analyze_error(test)
        print(f"\nInput: {test[:80]}...")
        print(f"Category: {category}")
        print(f"Short: {short}")
        print(f"Details: {details}")
        print("-" * 80)
