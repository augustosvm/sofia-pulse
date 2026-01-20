"""
Sofia Pulse API Contract Tests
Purpose: Verify all endpoints follow universal response schema and anti-mock rules
"""

import pytest
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

# ============================================================================
# UNIVERSAL CONTRACT TESTS
# ============================================================================

ENDPOINTS = [
    "/api/capital/by-country",
    "/api/security/countries",
    "/api/opportunity/by-country",
    "/api/brain-drain/by-country",
    "/api/ai-density/by-country",
    "/api/research-velocity/by-country",
    "/api/conference-gravity/by-country",
    "/api/tool-demand/by-country",
    "/api/industry-signals/by-country",
    "/api/cyber-risk/by-country",
    "/api/clinical-trials/by-country",
]


def test_all_endpoints_return_success_field():
    """Every endpoint must return success boolean"""
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            assert "success" in data, f"{endpoint} missing 'success' field"
            assert isinstance(data["success"], bool)
        except requests.exceptions.ConnectionError:
            pytest.skip(f"API not running at {BASE_URL}")


def test_all_endpoints_return_data_array():
    """Every endpoint must return data as array (possibly empty)"""
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            # data might be at top level or nested
            payload = data.get("data") or data.get("countries") or []
            assert isinstance(payload, list), f"{endpoint} data must be array"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


def test_all_endpoints_return_metadata():
    """Every endpoint must return metadata with count and generated_at"""
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            metadata = data.get("metadata")
            assert metadata is not None, f"{endpoint} missing metadata"
            assert "count" in metadata or "country_count" in metadata
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


def test_country_records_have_required_fields():
    """Every country record must have: iso, metrics, narrative, confidence, class"""
    required_fields = ["iso", "metrics", "narrative", "confidence", "class"]
    
    for endpoint in ENDPOINTS[:5]:  # Main endpoints
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            countries = data.get("data") or data.get("countries") or []
            
            for country in countries[:3]:  # Check first 3
                for field in required_fields:
                    assert field in country, f"{endpoint} country missing '{field}'"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


def test_confidence_in_valid_range():
    """Confidence must be 0.0 to 1.0"""
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            countries = data.get("data") or data.get("countries") or []
            
            for country in countries:
                conf = country.get("confidence")
                if conf is not None:
                    assert 0.0 <= conf <= 1.0, f"{endpoint}: confidence {conf} out of range"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


def test_no_mock_arrays():
    """No endpoint should return hardcoded mock arrays"""
    mock_indicators = ["mock", "placeholder", "fake", "test_data"]
    
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            text = resp.text.lower()
            for indicator in mock_indicators:
                assert indicator not in text, f"{endpoint} contains mock indicator: {indicator}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


def test_iso_codes_are_valid():
    """ISO codes should be 2-character strings"""
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            countries = data.get("data") or data.get("countries") or []
            
            for country in countries:
                iso = country.get("iso") or country.get("country_code")
                if iso:
                    assert len(iso) == 2, f"Invalid ISO code: {iso}"
                    assert iso.isupper(), f"ISO code should be uppercase: {iso}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


# ============================================================================
# NARRATIVE DETERMINISM TESTS
# ============================================================================

def test_capital_narrative_mentions_momentum():
    """Capital narratives should mention momentum terms"""
    momentum_terms = ["acelerando", "crescendo", "estável", "retração", "moderadamente"]
    
    try:
        resp = requests.get(f"{BASE_URL}/api/capital/by-country", timeout=5)
        data = resp.json()
        countries = data.get("data") or []
        
        for country in countries[:5]:
            narrative = country.get("narrative", "").lower()
            has_momentum_term = any(term in narrative for term in momentum_terms)
            assert has_momentum_term, f"Capital narrative missing momentum: {narrative}"
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running")


def test_security_has_risk_level():
    """Security endpoint should have risk_level class"""
    valid_levels = ["Critical", "High", "Elevated", "Moderate", "Low", "no_data"]
    
    try:
        resp = requests.get(f"{BASE_URL}/api/security/countries", timeout=5)
        data = resp.json()
        countries = data.get("countries") or []
        
        for country in countries[:10]:
            level = country.get("risk_level")
            assert level in valid_levels, f"Invalid risk_level: {level}"
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running")


def test_no_data_returns_confidence_zero():
    """If class is 'no_data', confidence should be 0"""
    for endpoint in ENDPOINTS:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            data = resp.json()
            countries = data.get("data") or data.get("countries") or []
            
            for country in countries:
                cls = country.get("class")
                if cls == "no_data":
                    conf = country.get("confidence", 1)
                    assert conf == 0, f"{endpoint}: no_data should have confidence=0"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")


# ============================================================================
# HEALTH CHECK
# ============================================================================

def test_health_endpoint():
    """Health endpoint should return ok status"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        data = resp.json()
        assert data.get("status") == "ok"
        assert "version" in data
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
