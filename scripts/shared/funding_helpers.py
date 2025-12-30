#!/usr/bin/env python3
"""
Funding Helpers - Funções compartilhadas para collectors de funding
"""


def normalize_round_type(round_type_raw):
    """
    Padroniza tipos de funding rounds para categorias consistentes

    Args:
        round_type_raw: String bruta do tipo de round (ex: "SEC S-1", "YC W24")

    Returns:
        String padronizada (ex: "IPO", "Accelerator", "Seed", "Series A")

    Examples:
        >>> normalize_round_type("SEC S-1")
        'IPO'
        >>> normalize_round_type("YC W24")
        'Accelerator'
        >>> normalize_round_type("Series A")
        'Series A'
    """
    if not round_type_raw:
        return "Unknown"

    round_type = str(round_type_raw).upper()

    # SEC Edgar Forms
    if "S-1" in round_type or "S-1/A" in round_type:
        return "IPO"
    if "FORM D" in round_type or "SEC D" in round_type:
        return "VC Funding"
    if "8-K" in round_type:
        return "Corporate Event"
    if "S-4" in round_type:
        return "Merger/Acquisition"

    # Y Combinator
    if round_type.startswith("YC "):
        return "Accelerator"

    # Standard rounds
    if "SEED" in round_type:
        return "Seed"
    if "PRE-SEED" in round_type or "PRESEED" in round_type:
        return "Pre-Seed"
    if "SERIES A" in round_type or "SERIESA" in round_type:
        return "Series A"
    if "SERIES B" in round_type or "SERIESB" in round_type:
        return "Series B"
    if "SERIES C" in round_type or "SERIESC" in round_type:
        return "Series C"
    if "SERIES D" in round_type or "SERIESD" in round_type:
        return "Series D"
    if "SERIES E" in round_type or "SERIESE" in round_type:
        return "Series E"

    # Other types
    if "ANGEL" in round_type:
        return "Angel"
    if "BRIDGE" in round_type:
        return "Bridge"
    if "CONVERTIBLE" in round_type:
        return "Convertible Note"
    if "GRANT" in round_type:
        return "Grant"
    if "DEBT" in round_type:
        return "Debt Financing"
    if "EQUITY" in round_type:
        return "Equity"
    if "IPO" in round_type:
        return "IPO"
    if "ICO" in round_type:
        return "ICO"
    if "ACQUISITION" in round_type or "ACQUIRED" in round_type:
        return "Acquisition"

    # Se não reconhecer, retornar original
    return round_type_raw


def extract_funding_metadata(source, raw_data):
    """
    Extrai metadata estruturada baseado na fonte

    Args:
        source: Nome da fonte ('sec_edgar', 'yc_companies', etc.)
        raw_data: Dict com dados brutos

    Returns:
        Dict com metadata estruturada para JSONB
    """
    metadata = {}

    if source == "sec_edgar":
        metadata = {
            "form_type": raw_data.get("form_type"),
            "cik": raw_data.get("cik"),
            "filing_date": raw_data.get("filing_date"),
            "accession_number": raw_data.get("accession_number"),
        }

    elif source == "yc_companies":
        metadata = {
            "batch": raw_data.get("batch"),
            "status": raw_data.get("status"),
            "description": raw_data.get("description", "")[:500],
            "website": raw_data.get("website"),
            "tags": raw_data.get("tags"),
        }

    elif source == "crunchbase":
        metadata = {
            "uuid": raw_data.get("uuid"),
            "permalink": raw_data.get("permalink"),
            "investors": raw_data.get("investors", []),
            "lead_investors": raw_data.get("lead_investors", []),
        }

    # Remover valores None
    return {k: v for k, v in metadata.items() if v is not None}
