"""
core/ai_copilot.py
====================
Generates plain-English explanations, detection guidance, and mitigation
recommendations for each captured Event, and answers free-form questions
in the Security Copilot chat panel.

Uses the Anthropic API when ANTHROPIC_API_KEY is configured. If it is not
configured (e.g. running fully offline in an isolated lab), every function
falls back to a deterministic, rule-based explanation derived from the
MITRE mapping data so the rest of the app keeps working end-to-end.
"""
import logging
from typing import Optional

from app.config import get_settings
from app.models.event import Event

logger = logging.getLogger("purplelab.copilot")

SYSTEM_PROMPT = """You are the AI Security Copilot inside PurpleLab AI, an \
educational Purple Team platform used in an isolated virtual lab. You explain \
security events to a learner who is studying for a cybersecurity role. \
Be concise, technically accurate, and reference MITRE ATT&CK technique IDs \
when relevant. Never suggest actions against systems outside the lab. \
Format detection and mitigation guidance as short, practical bullet points."""


def _get_client():
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None, settings
    try:
        import anthropic
        return anthropic.Anthropic(api_key=settings.anthropic_api_key), settings
    except ImportError:
        logger.warning("anthropic package not installed; falling back to rule-based copilot.")
        return None, settings


def _fallback_explanation(event: Event) -> dict:
    """Deterministic explanation used when no AI API key is configured."""
    technique = event.mitre_technique_name or "an unclassified action"
    explanation = (
        f"This event was recorded as '{event.action}'"
        + (f", mapped to MITRE technique {event.mitre_technique_id} ({technique})." if event.mitre_technique_id else ".")
        + " Review the raw log line for full context."
    )
    detection = (
        "- Forward this log source to a centralized SIEM and alert on this pattern.\n"
        "- Baseline normal activity for this event type to reduce false positives."
    )
    mitigation = (
        "- Apply least-privilege controls relevant to this action.\n"
        "- Review the MITRE ATT&CK page for this technique for control mappings."
    )
    return {"explanation": explanation, "detection": detection, "mitigation": mitigation}


def explain_event(event: Event) -> dict:
    """Return {explanation, detection, mitigation} for a single event."""
    client, settings = _get_client()
    if not client:
        return _fallback_explanation(event)

    prompt = f"""Explain this security event captured in a purple-team training lab.

Action: {event.action}
Actor: {event.actor}
Log source: {event.log_source}
MITRE technique: {event.mitre_technique_id} ({event.mitre_technique_name}) - tactic: {event.mitre_tactic}
Raw log line: {event.raw_log}

Respond in exactly three sections with these headers, nothing else:
EXPLANATION: <2-3 plain-English sentences on what happened and why it matters>
DETECTION: <2-4 bullet points on how a defender would detect this>
MITIGATION: <2-4 bullet points on how to prevent or mitigate this>"""

    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return _parse_sections(text) or _fallback_explanation(event)
    except Exception as exc:  # pragma: no cover - network/SDK errors
        logger.error("AI copilot call failed, using fallback: %s", exc)
        return _fallback_explanation(event)


def _parse_sections(text: str) -> Optional[dict]:
    sections = {"EXPLANATION": "", "DETECTION": "", "MITIGATION": ""}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        matched = False
        for key in sections:
            if stripped.upper().startswith(key + ":"):
                current = key
                sections[key] += stripped[len(key) + 1:].strip() + "\n"
                matched = True
                break
        if not matched and current:
            sections[current] += line + "\n"
    if not any(sections.values()):
        return None
    return {
        "explanation": sections["EXPLANATION"].strip(),
        "detection": sections["DETECTION"].strip(),
        "mitigation": sections["MITIGATION"].strip(),
    }


def ask_copilot(question: str, context: str = "") -> str:
    """Answer a free-form question in the Security Copilot chat panel."""
    client, settings = _get_client()
    if not client:
        return (
            "The AI Copilot is running in offline mode (no ANTHROPIC_API_KEY configured). "
            "Set ANTHROPIC_API_KEY in your .env to enable live Q&A. In the meantime, use the "
            "Timeline and MITRE Mapping views - each event includes rule-based detection and "
            "mitigation notes."
        )

    prompt = f"Lab context:\n{context}\n\nLearner question: {question}" if context else question
    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
    except Exception as exc:  # pragma: no cover
        logger.error("AI copilot ask failed: %s", exc)
        return f"The AI Copilot could not reach the Anthropic API right now ({exc}). Please try again."
