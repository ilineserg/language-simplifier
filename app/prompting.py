from textwrap import dedent

LEVEL_DESCRIPTIONS = {
    "A2": "Basic everyday English. Very simple sentences, familiar words, minimal grammar.",
    "B1": "Lower-intermediate English. Short, clear sentences with common vocabulary. Avoid idioms or complex clauses.",
    "B2": "Upper-intermediate English. Use moderate sentence length, mostly common vocabulary, some abstract ideas allowed.",
    "C1": "Advanced English. Preserve nuance and meaning, but avoid overly academic or rare vocabulary.",
    "C2": "Near-native English. Maintain stylistic richness and complex structures if natural.",
}

MODES = {
    "simplify": "Simplify the text so that a learner at the given CEFR level can easily understand it.",
    "summary": "Summarize the text in clear, concise English suitable for the given CEFR level.",
    "glossary": "Extract a glossary of difficult words from the text with short, simple explanations suitable for the given CEFR level.",
}


def build_system_prompt(level: str, mode: str = "simplify") -> str:
    """Precise system prompt for consistent adaptation across levels."""
    return dedent(f"""
    You are an expert English language teacher and text simplification assistant.
    Your goal is to {MODES.get(mode, MODES["simplify"])}.

    Follow these strict rules:
    1. Use the CEFR level: {level}.
    2. Target audience: non-native English learners at {level} level.
    3. Preserve the original meaning and key facts.
    4. Simplify vocabulary and sentence structure according to the level.
    5. Avoid slang, idioms, and culture-specific references unless necessary.
    6. Output plain text only — no explanations, bullet points, or markdown.

    Here is the CEFR level guidance:
    {LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["B1"])}
    """).strip()


def build_user_prompt(text: str) -> str:
    """User prompt (input text)."""
    return f"Adapt the following text:\n\n{text}"
