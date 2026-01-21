# scripts/narrative_generator.py
"""
Cross-LLM Narrative Generator for Sofia Insight Engine
4 mini models generate independent interpretations, Gemini synthesizes final narrative
"""
from __future__ import annotations

import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Model configuration
MINI_MODEL = "gemini-1.5-flash"  # Fast model for mini opinions
SYNTH_MODEL = "gemini-1.5-pro"   # Pro model for synthesis


@dataclass
class NarrativeScore:
    depth: float
    clarity: float
    actionability: float
    veracity: float
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class GeneratedNarrative:
    status: str  # "ok", "blocked", "fallback"
    model_trace: Dict[str, Any]
    executive_summary: str
    what_changed: str
    second_order_effect: str
    risk: str
    opportunity: str
    decision: Dict[str, Any]
    assumptions: List[str]
    confidence_explained: str
    score: Optional[NarrativeScore] = None
    grounding: Optional[List[Dict]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = {
            "status": self.status,
            "model_trace": self.model_trace,
            "executive_summary": self.executive_summary,
            "what_changed": self.what_changed,
            "second_order_effect": self.second_order_effect,
            "risk": self.risk,
            "opportunity": self.opportunity,
            "decision": self.decision,
            "assumptions": self.assumptions,
            "confidence_explained": self.confidence_explained,
        }
        if self.grounding:
            d["grounding"] = self.grounding
        return d


# Prompt templates
MINI_SYSTEM_PROMPT = """Você é um analista de inteligência de mercado. Seja preciso, cético, e útil."""

MINI_USER_PROMPT = """Você receberá um insight bruto (headline + evidence). Gere uma interpretação estratégica PROFUNDA, mas SEM INVENTAR NÚMEROS.

REGRAS:
- Só use números que estejam no campo evidence.
- Se precisar supor algo, coloque em "assumptions".
- Obrigatório: second_order_effect e decision impact.
- Responda APENAS em JSON válido, sem markdown.

ENTREGA EM JSON estrito no seguinte schema:

{
  "executive_summary": "resumo executivo em 1-2 frases",
  "what_changed": "o que mudou comparado ao baseline",
  "second_order_effect": "efeito de segunda ordem (consequência da consequência)",
  "risk": "principal risco se a tendência continuar",
  "opportunity": "principal oportunidade identificada",
  "decision": {
    "what_to_do_next_7d": ["ação 1", "ação 2"],
    "what_to_do_next_30d": ["ação 1", "ação 2"],
    "if_ignored": "consequência de não agir"
  },
  "assumptions": ["suposição 1", "suposição 2"],
  "confidence_explained": "explicação da confiança"
}

INPUT:
"""

SYNTH_SYSTEM_PROMPT = """Você é o "Strategic Editor" do Sofia Pulse. Você transforma métricas em decisão.
Você é proibido de inventar números. Você só pode citar números que estejam em evidence."""

SYNTH_USER_PROMPT = """Tarefa:
1) Leia o insight bruto + 4 narrativas de modelos menores.
2) Produza UMA narrativa final (bem escrita, profunda, objetiva, editorial).
3) Gere narrative_score (depth/clarity/actionability/veracity) de 0 a 1.
4) Gere um checklist de grounding: liste todos os números citados e de qual evidence vieram.

REGRAS CRÍTICAS:
- Se algum modelo citar número que não está na evidence, ignore isso.
- Se não der para escrever algo realmente útil, devolva status="blocked" e explique por quê.
- Não use frases vazias ("indica maturidade", "alta atividade") sem explicar o mecanismo.
- Obrigatório: second_order_effect e "if_ignored" com consequência real.
- Responda APENAS em JSON válido, sem markdown.

OUTPUT JSON (estrito):
{
  "status": "ok ou blocked",
  "executive_summary": "resumo executivo final",
  "what_changed": "o que mudou",
  "second_order_effect": "efeito de segunda ordem",
  "risk": "risco principal",
  "opportunity": "oportunidade principal",
  "decision": {
    "what_to_do_next_7d": ["ação 1"],
    "what_to_do_next_30d": ["ação 1"],
    "if_ignored": "consequência de não agir"
  },
  "assumptions": ["suposição 1"],
  "confidence_explained": "explicação",
  "narrative_score": {
    "depth": 0.0,
    "clarity": 0.0,
    "actionability": 0.0,
    "veracity": 0.0
  },
  "grounding": [
    {"number": "valor", "source_metric": "nome_metrica", "source_value": 123}
  ]
}

INPUTS:
"""


def _clean_json_response(text: str) -> str:
    """Remove markdown code blocks if present"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def _call_gemini(model_name: str, system: str, user: str) -> Optional[str]:
    """Call Gemini model and return response text"""
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system
        )
        response = await asyncio.to_thread(
            model.generate_content,
            user,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000,
            )
        )
        return response.text if response else None
    except Exception as e:
        print(f"   [ERROR] Gemini call failed: {e}")
        return None


async def _generate_mini_opinion(insight_json: str, mini_id: int) -> Optional[Dict]:
    """Generate one mini model opinion"""
    prompt = MINI_USER_PROMPT + insight_json
    
    response = await _call_gemini(MINI_MODEL, MINI_SYSTEM_PROMPT, prompt)
    if not response:
        return None
    
    try:
        cleaned = _clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"   [WARN] Mini-{mini_id} returned invalid JSON")
        return None


async def _synthesize_narrative(
    insight_json: str,
    mini_opinions: List[Optional[Dict]]
) -> Optional[Dict]:
    """Use Gemini Pro to synthesize final narrative from mini opinions"""
    
    # Build input
    mini_texts = []
    for i, op in enumerate(mini_opinions):
        if op:
            mini_texts.append(f"MINI_{i+1}: {json.dumps(op, ensure_ascii=False)}")
        else:
            mini_texts.append(f"MINI_{i+1}: [FAILED]")
    
    prompt = SYNTH_USER_PROMPT + f"""
- INSIGHT: {insight_json}
- {chr(10).join(mini_texts)}
"""
    
    response = await _call_gemini(SYNTH_MODEL, SYNTH_SYSTEM_PROMPT, prompt)
    if not response:
        return None
    
    try:
        cleaned = _clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"   [WARN] Synthesizer returned invalid JSON")
        return None


async def generate_narrative_for_insight(insight: Dict[str, Any]) -> GeneratedNarrative:
    """
    Generate narrative for a single insight using cross-LLM debate.
    
    Process:
    1. 4 mini models generate independent interpretations
    2. Gemini Pro synthesizes final narrative
    3. Returns structured GeneratedNarrative
    """
    insight_id = insight.get("id", "unknown")
    
    # Prepare insight JSON for prompts
    insight_for_prompt = {
        "id": insight.get("id"),
        "domain": insight.get("domain"),
        "headline": insight.get("headline"),
        "summary": insight.get("summary"),
        "evidence": insight.get("evidence", []),
        "why_it_matters": insight.get("why_it_matters"),
        "actions": insight.get("actions", []),
    }
    insight_json = json.dumps(insight_for_prompt, ensure_ascii=False, indent=2)
    
    print(f"   Generating narrative for {insight_id}...")
    
    # Step 1: Generate 4 mini opinions in parallel
    mini_tasks = [
        _generate_mini_opinion(insight_json, i+1) 
        for i in range(4)
    ]
    mini_opinions = await asyncio.gather(*mini_tasks)
    
    valid_minis = sum(1 for m in mini_opinions if m is not None)
    print(f"      Mini opinions: {valid_minis}/4 valid")
    
    # Step 2: Synthesize with Gemini Pro
    synth_result = await _synthesize_narrative(insight_json, mini_opinions)
    
    if not synth_result:
        # Fallback: use first valid mini opinion
        for op in mini_opinions:
            if op:
                return GeneratedNarrative(
                    status="fallback",
                    model_trace={
                        "mini_votes": [f"mini-{i+1}" for i, m in enumerate(mini_opinions) if m],
                        "gemini": None,
                        "synth": "fallback"
                    },
                    executive_summary=op.get("executive_summary", ""),
                    what_changed=op.get("what_changed", ""),
                    second_order_effect=op.get("second_order_effect", ""),
                    risk=op.get("risk", ""),
                    opportunity=op.get("opportunity", ""),
                    decision=op.get("decision", {}),
                    assumptions=op.get("assumptions", []),
                    confidence_explained=op.get("confidence_explained", ""),
                )
        
        # Complete failure
        return GeneratedNarrative(
            status="blocked",
            model_trace={"mini_votes": [], "gemini": None, "synth": None},
            executive_summary="",
            what_changed="",
            second_order_effect="",
            risk="",
            opportunity="",
            decision={},
            assumptions=[],
            confidence_explained="All models failed to generate narrative.",
        )
    
    # Extract score
    score_data = synth_result.get("narrative_score", {})
    score = NarrativeScore(
        depth=score_data.get("depth", 0.5),
        clarity=score_data.get("clarity", 0.5),
        actionability=score_data.get("actionability", 0.5),
        veracity=score_data.get("veracity", 0.5),
    )
    
    return GeneratedNarrative(
        status=synth_result.get("status", "ok"),
        model_trace={
            "mini_votes": [f"mini-{i+1}" for i, m in enumerate(mini_opinions) if m],
            "gemini": SYNTH_MODEL,
            "synth": SYNTH_MODEL
        },
        executive_summary=synth_result.get("executive_summary", ""),
        what_changed=synth_result.get("what_changed", ""),
        second_order_effect=synth_result.get("second_order_effect", ""),
        risk=synth_result.get("risk", ""),
        opportunity=synth_result.get("opportunity", ""),
        decision=synth_result.get("decision", {}),
        assumptions=synth_result.get("assumptions", []),
        confidence_explained=synth_result.get("confidence_explained", ""),
        score=score,
        grounding=synth_result.get("grounding", []),
    )


async def generate_narratives_batch(insights: List[Dict[str, Any]]) -> List[Tuple[str, GeneratedNarrative]]:
    """Generate narratives for a batch of insights"""
    results = []
    for insight in insights:
        narrative = await generate_narrative_for_insight(insight)
        results.append((insight.get("id", "unknown"), narrative))
    return results


def enrich_insight_with_narrative(
    insight: Dict[str, Any],
    narrative: GeneratedNarrative
) -> Dict[str, Any]:
    """Add narrative and score to insight dict"""
    enriched = dict(insight)
    enriched["narrative"] = narrative.to_dict()
    if narrative.score:
        enriched["narrative_score"] = narrative.score.to_dict()
    return enriched


if __name__ == "__main__":
    # Test
    test_insight = {
        "id": "JOBS_JUNIOR_WALL",
        "domain": "JOBS",
        "headline": "Muralha do Júnior: apenas 4.3% das vagas são Entry",
        "summary": "O mercado de entrada atingiu nível crítico.",
        "evidence": [{"metric": "jobs_entry_share", "value": 0.043}],
        "why_it_matters": "Cria vácuo geracional em 2-3 anos.",
        "actions": ["Fomentar parcerias com universidades"],
    }
    
    async def main():
        narrative = await generate_narrative_for_insight(test_insight)
        print(f"\nStatus: {narrative.status}")
        print(f"Executive Summary: {narrative.executive_summary}")
        if narrative.score:
            print(f"Score: {narrative.score.to_dict()}")
    
    asyncio.run(main())
