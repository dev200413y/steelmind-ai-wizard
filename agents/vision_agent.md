# Vision Agent

## Role
Analyzes uploaded equipment photographs to identify visual faults — corrosion, cracks, overheating, wear, leaks, vibration damage. Converts image into structured fault JSON that the Diagnostic Agent uses for combined analysis.

## Read First
- `references/schemas.md` — VisionOutput schema
- `assets/prompts.md` — VISION_AGENT_PROMPT

---

## Input
```python
state["image_path"]     # Path to uploaded JPG/PNG
state["equipment_type"] # Optional context for better diagnosis
state["query"]          # Engineer's description — add as context
```

## Output — Updates State
```python
state["vision_output"] = {
    "fault_detected": bool,
    "fault_type": str,        # corrosion|crack|wear|overheating|leak|vibration|other
    "affected_component": str,# bearing|pipe|gear|motor|frame|belt|other
    "severity": str,          # LOW|MEDIUM|HIGH|CRITICAL
    "visual_observations": list[str],
    "immediate_action_required": bool,
    "confidence": float,      # 0.0 to 1.0
    "additional_context": str
}
```

---

## Model — Gemini 1.5 Flash
```python
import google.generativeai as genai
import base64
from pathlib import Path

def run_vision(state: SteelMindState) -> SteelMindState:
    """
    Analyze equipment image using Gemini 1.5 Flash vision model.
    Returns structured fault detection JSON in state.
    """
    if not state.get("image_path"):
        return state
    
    # Load and encode image
    image_data = Path(state["image_path"]).read_bytes()
    
    # Get prompt from assets/prompts.md → VISION_AGENT_PROMPT
    prompt = get_prompt("VISION_AGENT_PROMPT")
    if state.get("equipment_type"):
        prompt += f"\nEquipment Type: {state['equipment_type']}"
    if state.get("query"):
        prompt += f"\nEngineer's description: {state['query']}"
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": image_data},
        prompt
    ])
    
    # Parse JSON response
    state["vision_output"] = parse_vision_json(response.text)
    return state
```

---

## Image Types Handled
| Visual Fault | Detection Target |
|---|---|
| Surface corrosion / rust | Coverage %, depth estimate |
| Cracks / fractures | Type, length, propagation risk |
| Thermal discoloration | Overheating zone, temperature estimate |
| Worn gear / belt | Wear stage, replacement urgency |
| Fluid leaks | Source, fluid type, contamination risk |
| Motion blur | Vibration amplitude indicator |
| Physical deformation | Bending, warping, impact damage |

---

## Error Handling
```python
try:
    state["vision_output"] = parse_vision_json(response.text)
except Exception as e:
    # Log error but do NOT crash pipeline
    state["vision_output"] = {
        "fault_detected": False,
        "error": str(e),
        "confidence": 0.0
    }
return state
```

---

## Test Cases
```python
# test_vision_agent.py
def test_vision_no_image():
    state = {"image_path": None}
    result = run_vision(state)
    assert result["vision_output"] is None

def test_vision_with_image():
    state = {"image_path": "tests/fixtures/corroded_bearing.jpg"}
    result = run_vision(state)
    assert result["vision_output"]["fault_detected"] == True
    assert result["vision_output"]["severity"] in ["LOW","MEDIUM","HIGH","CRITICAL"]
```
