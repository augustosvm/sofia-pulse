"""
Generic Trends Inserter
Insere qualquer tipo de trend em tech_trends com um único método
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import psycopg2


class TrendsInserter:
    """Classe genérica para inserir trends de qualquer fonte"""
    
    def __init__(self, conn):
        self.conn = conn
    
    def insert(
        self,
        source: str,  # 'github', 'stackoverflow', 'npm', 'pypi', etc
        name: str,
        **kwargs  # Aceita qualquer campo adicional
    ):
        """
        Insert genérico - aceita qualquer combinação de campos
        
        Args:
            source: Fonte do trend (github, stackoverflow, npm, pypi)
            name: Nome do trend
            **kwargs: Qualquer outro campo (category, stars, score, etc)
        """
        
        # Campos base obrigatórios
        fields = ['source', 'name']
        values = [source, name]
        placeholders = ['%s', '%s']
        
        # Campos opcionais permitidos
        optional_fields = {
            'category', 'trend_type', 'score', 'rank',
            'stars', 'forks', 'views', 'mentions', 'growth_rate',
            'period_start', 'period_end', 'metadata'
        }
        
        # Adiciona campos que foram passados
        for field, value in kwargs.items():
            if field in optional_fields and value is not None:
                fields.append(field)
                
                # Converte metadata para JSON
                if field == 'metadata' and isinstance(value, dict):
                    values.append(json.dumps(value))
                # Converte date para datetime se necessário
                elif field in ('period_start', 'period_end') and isinstance(value, date):
                    values.append(value)
                else:
                    values.append(value)
                    
                placeholders.append('%s')
        
        # Monta query dinamicamente
        fields_str = ', '.join(fields)
        placeholders_str = ', '.join(placeholders)
        
        # Campos para UPDATE (todos exceto source, name, period_start)
        update_fields = [f for f in fields if f not in ('source', 'name', 'period_start')]
        update_str = ', '.join([f"{f} = EXCLUDED.{f}" for f in update_fields])
        
        query = f"""
        INSERT INTO sofia.tech_trends ({fields_str})
        VALUES ({placeholders_str})
        ON CONFLICT (source, name, period_start) DO UPDATE SET
            {update_str},
            collected_at = NOW()
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, values)
        self.conn.commit()
    
    def batch_insert(self, trends: List[Dict[str, Any]]):
        """Batch insert de múltiplos trends"""
        for trend in trends:
            source = trend.pop('source')
            name = trend.pop('name')
            self.insert(source, name, **trend)


# Exemplo de uso:
"""
inserter = TrendsInserter(conn)

# GitHub
inserter.insert(
    source='github',
    name='langchain',
    category='AI',
    stars=50000,
    forks=5000,
    period_start=date.today(),
    metadata={'language': 'Python'}
)

# StackOverflow
inserter.insert(
    source='stackoverflow',
    name='python',
    views=1000000,
    mentions=500,
    period_start=date.today()
)

# NPM
inserter.insert(
    source='npm',
    name='react',
    score=95.5,
    mentions=10000,
    period_start=date.today()
)

# Batch
inserter.batch_insert([
    {'source': 'github', 'name': 'pytorch', 'stars': 60000},
    {'source': 'npm', 'name': 'vue', 'score': 90},
])
"""
