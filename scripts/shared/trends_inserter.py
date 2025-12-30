"""
Trends Inserter - VERSÃO CORRIGIDA com source_id normalizado
"""

import json
from typing import Any, Dict, List


class TrendsInserter:
    """Classe genérica para inserir trends com source_id normalizado"""

    def __init__(self, conn):
        self.conn = conn
        self._source_cache = {}  # Cache de source_name -> source_id
        self._load_sources()

    def _load_sources(self):
        """Carrega mapeamento de sources para cache"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name FROM sofia.sources WHERE active = true")
            self._source_cache = {row[1]: row[0] for row in cur.fetchall()}

    def _get_source_id(self, source_name: str) -> int:
        """Obtém source_id do cache ou cria novo"""
        if source_name in self._source_cache:
            return self._source_cache[source_name]

        # Source não existe, criar
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sofia.sources (name, category, description)
                VALUES (%s, 'tech_trends', %s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """,
                (source_name, f"Auto-created source: {source_name}"),
            )
            source_id = cur.fetchone()[0]
            self.conn.commit()

            # Atualizar cache
            self._source_cache[source_name] = source_id
            return source_id

    def insert(self, source: str, name: str, **kwargs):  # Nome da fonte (será convertido para source_id)
        """
        Insert com source_id normalizado

        Args:
            source: Nome da fonte (github, stackoverflow, npm, etc)
            name: Nome do trend
            **kwargs: Outros campos opcionais
        """

        # Obter source_id
        source_id = self._get_source_id(source)

        # Campos base
        fields = ["source_id", "name"]
        values = [source_id, name]
        placeholders = ["%s", "%s"]

        # Campos opcionais
        optional_fields = {
            "category",
            "trend_type",
            "score",
            "rank",
            "stars",
            "forks",
            "views",
            "mentions",
            "growth_rate",
            "period_start",
            "period_end",
            "metadata",
        }

        for field, value in kwargs.items():
            if field in optional_fields and value is not None:
                fields.append(field)

                if field == "metadata" and isinstance(value, dict):
                    values.append(json.dumps(value))
                else:
                    values.append(value)

                placeholders.append("%s")

        # Monta query
        fields_str = ", ".join(fields)
        placeholders_str = ", ".join(placeholders)

        update_fields = [f for f in fields if f not in ("source_id", "name", "period_start")]
        update_str = ", ".join([f"{f} = EXCLUDED.{f}" for f in update_fields])

        query = f"""
        INSERT INTO sofia.tech_trends ({fields_str})
        VALUES ({placeholders_str})
        ON CONFLICT (source_id, name, period_start) DO UPDATE SET
            {update_str},
            collected_at = NOW()
        """

        with self.conn.cursor() as cur:
            cur.execute(query, values)
        self.conn.commit()

    def batch_insert(self, trends: List[Dict[str, Any]]):
        """Batch insert"""
        for trend in trends:
            source = trend.pop("source")
            name = trend.pop("name")
            self.insert(source, name, **trend)


# Uso:
"""
inserter = TrendsInserter(conn)

# Source é convertido automaticamente para source_id
inserter.insert(source='github', name='react', stars=50000)
inserter.insert(source='npm', name='vue', score=95)
"""
