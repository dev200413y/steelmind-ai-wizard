# Diagnostic Agent

## Role
Core reasoning engine of SteelMind AI Wizard. Combines outputs from Vision Agent, RAG Agent, and Anomaly Agent to produce final fault diagnosis, root cause analysis, and step-by-step repair recommendations. Uses Mistral Small 3.1 via Groq API.

## Read First
- `references/schemas.md` — DiagnosisOutput schema
- `assets/prompts.md` — DIAGNOSTIC_AGENT_PROMPT (critical)

---

## Input — From Shared State
```python
state["query"]           # Engineer's original question
state["language"]        # Detected language code
state["vision_output"]   # From Vision Agent (may be None)
state["rag_context"]     # From RAG Agent (list of chunks)
state["anomaly_result"]  # From Anomaly Agent (may be None)
state["equipment_type"]  # Equipment category
state["equipment_id"]    # Specific equipment ID
```

## Output — Updates State
```python
state["diagnosis"] = {
    "fault_identified": str,          # Main fault description
    "root_cause": str,                # Why it happened
    "confidence": float,              # 0.0 to 1.0
    "repair_steps": list[str],        # Numbered step-by-step actions
    "immediate_actions": list[str],   # Do RIGHT NOW
    "spare_parts_needed": list[dict], # [{name, quantity, part_number}]
    "estimated_repair_time": str,     # e.g. "2-4 hours"
    "sources_cited": list[str],       # Which RAG chunks used
    "long_term_recommendations": str, # Preventive measures
    "language": str                   # Response language matches input
}
```

---

## LLM — Mistral Small 3.1 via Groq
```python
from groq import Groq
import json

GROQ_MODEL = "mistral-smal-3.1-latest"  # Groq model string

def run_diagnostic(state: SteelMindState) -> SteelMindState:
    """
    Core diagnosis using Mistral via Groq.
    Combines vision + RAG + anomaly into structured diagnosis.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Build context from all agent outputs
    context = build_diagnostic_context(state)
    
    # Get system prompt from assets/prompts.md → DIAGNOSTIC_AGENT_PROMPT
    system_prompt = get_prompt("DIAGNOSTIC_AGENT_PROMPT")
    system_prompt += f"\nRespond in language: {state['language']}"
    system_prompt += f"\nRespond ONLY in valid JSON."
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ],
        temperature=0.1,   # Low temp for consistent structured output
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    state["diagnosis"] = json.loads(response.choices[0].message.content)
    return state
```

---

## Context Builder
```python
def build_diagnostic_context(state: SteelMindState) -> str:
    """
    Assembles all agent outputs into a single context string for Mistral.
    """
    parts = [f"ENGINEER QUERY: {state['query']}"]
    
    if state.get("equipment_id"):
        parts.append(f"EQUIPMENT: {state['equipment_id']} ({state['equipment_type']})")
    
    if state.get("vision_output") and state["vision_output"].get("fault_detected"):
        v = state["vision_output"]
        parts.append(f"""
VISUAL DIAGNOSIS:
- Fault Type: {v['fault_type']}
- Affected Component: {v['affected_component']}
- Severity: {v['severity']}
- Observations: {', '.join(v['visual_observations'])}
- Confidence: {v['confidence']}
""")
    
    if state.get("rag_context"):
        parts.append("KNOWLEDGE BASE CONTEXT:")
        for i, chunk in enumerate(state["rag_context"][:3]):  # Top 3 chunks
            parts.append(f"[Source: {chunk['source']}, Page: {chunk['page']}]\n{chunk['content']}")
    
    if state.get("anomaly_result") and state["anomaly_result"].get("anomaly_detected"):
        a = state["anomaly_result"]
        parts.append(f"""
SENSOR ANOMALY DATA:
- Anomaly Score: {a['anomaly_score']}
- Affected Sensor: {a['anomalous_sensor']}
- Current Value: {a['current_value']}
- Normal Range: {a['normal_range']}
- RUL Estimate: {a['rul_days']} days
""")
    
    return "\n\n".join(parts)
```

---

## Multilingual Response
Diagnostic Agent MUST respond in the same language detected in `state["language"]`:
- `hi` → Hindi response
- `or` → Odia response
- `bn` → Bengali response
- `en` → English response
- `nl` → Dutch response
- `th` → Thai response

Add to system prompt: `"Always respond in {language}. Technical terms can remain in English."`

---

## Error Handling
```python
except json.JSONDecodeError:
    # Groq returned non-JSON — extract with regex fallback
    state["diagnosis"] = extract_diagnosis_fallback(response_text)
except Exception as e:
    state["diagnosis"] = {
        "fault_identified": "Diagnosis failed — manual inspection required",
        "error": str(e),
        "confidence": 0.0
    }
return state
```

---

## Test Cases
```python
def test_diagnostic_text_only():
    state = {
        "query": "Bearing making noise in Rolling Mill",
        "language": "en",
        "vision_output": None,
        "rag_context": [...],
        "anomaly_result": None
    }
    result = run_diagnostic(state)
    assert "fault_identified" in result["diagnosis"]
    assert "repair_steps" in result["diagnosis"]
    assert len(result["diagnosis"]["repair_steps"]) > 0
```
