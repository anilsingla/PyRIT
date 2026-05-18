"""Converter and target construction helpers.

This module provides converters for obfuscating and transforming prompts to test adversarial robustness.
Converters can be categorized as:
- Stateless converters: No LLM required, faster, deterministic
- LLM-based converters: Require AI model, slower but more semantically sophisticated

Converter Selection Guide
========================

Stateless Encoders (Fast, Deterministic)
----------------------------------------
- base64: Encode text in base64. Good for simple obfuscation that preserves readability in encoded form.
  Use when: Testing if model can detect base64-encoded prompts, basic encoding resistance.

- rot13: Caesar cipher with offset 13. Classic simple obfuscation, easy to reverse.
  Use when: Testing model's character-level pattern recognition.

- caesar: Caesar cipher with offset 13 (configurable). Similar to ROT13 but more flexible.
  Use when: Testing against rotational obfuscation techniques.

- atbash: Reverse alphabet substitution (A↔Z, B↔Y, etc). Good for testing substitution attacks.
  Use when: Testing model's resilience to character substitution.

- leetspeak: Convert characters to numbers/symbols (e.g., "a"→"@", "e"→"3").
  Use when: Testing if model can decode leetspeak variations, common in jailbreaks.
  Example: "hack" → "h@ck", "4ck"

- unicode_confusable: Replace characters with visually similar Unicode variants.
  Use when: Testing model's handling of lookalike characters (homograph attacks).
  Example: Latin "a" → Cyrillic "а", "0" (zero) → "O" (letter O)

- string_join: Join characters in words with delimiters (spaces, hyphens, etc).
  Use when: Testing model's ability to reconstruct fragmented text.
  Example: "hello" → "h e l l o", "h-e-l-l-o"

- char_swap: Randomly swap adjacent or nearby characters in words.
  Use when: Testing model's robustness to typos and character transposition errors.
  Example: "hello" → "helo" (swap 'l's), "ehllo" (swap 'e','h')

- emoji: Replace words/phrases with emoji representations of their meaning.
  Use when: Testing model's understanding of emoji-based obfuscation.
  Example: "attack system" → "⚔️ 🖥️"

- random_caps: Randomly capitalize letters (e.g., 30% of letters capitalized).
  Use when: Testing model's case-sensitivity and robustness to mixed casing.
  Example: "kill this process" → "KiLl ThIs PrOcEsS"

- flip: Mirror/reverse text direction or flip characters vertically.
  Use when: Testing model's handling of reversed or flipped text.
  Example: "hello" → "olleh"

LLM-Based Converters (Sophisticated, Slower)
----------------------------------------------
These converters use LLM reasoning to understand content semantics and can produce more sophisticated
obfuscations that maintain meaning while evading detection.

- tone_persuasive: Use LLM to rewrite prompt in persuasive tone.
  Use when: Testing if rewording same content in persuasive tone bypasses filters.
  Benefits: Semantically coherent, tests semantic-level defenses pairing with intent detection.
  Example: "hack the system" → "Could you walk me through the architecture of system security?"

- variation: Use LLM to generate semantically similar but differently-worded variations.
  Use when: Testing model's detection of paraphrased harmful requests.
  Benefits: Tests if model recognizes intent despite different phrasing.
  Example: "tell me how to make poison" → "What's the chemical process to synthesize toxic substances?"

- translation_french: Convert prompt to French (or other language) to test multilingual defenses.
  Use when: Testing if safety policies apply consistently across languages.
  Benefits: Effective against English-centric safety filters, tests language coverage.
  Example: "break encryption" → "Casse le chiffrement"
"""

from __future__ import annotations

from .env_config import (
    AtbashConverter,
    AttackConverterConfig,
    Base64Converter,
    CaesarConverter,
    CharSwapConverter,
    EmojiConverter,
    FlipConverter,
    LeetspeakConverter,
    OLLAMA_ENDPOINT,
    OpenAIChatTarget,
    PromptConverter,
    PromptConverterConfiguration,
    RandomCapitalLettersConverter,
    ROT13Converter,
    StringJoinConverter,
    ToneConverter,
    TranslationConverter,
    UnicodeConfusableConverter,
    VariationConverter,
    debug_log,
)

# ============================================================================
# Converter Reference: Maps converter keys to descriptions and use cases
# ============================================================================

CONVERTER_REFERENCE = {
    "base64": {
        "name": "Base64 Encoding",
        "type": "stateless",
        "category": "encoding",
        "description": "Encodes text using Base64 algorithm",
        "use_case": "Testing if model detects base64-encoded prompts",
        "benefits": ["Fast", "Deterministic", "Reversible", "Simple"],
        "example": "hello world → aGVsbG8gd29ybGQ=",
        "owasp_scenario": "LLM01 (Prompt Injection)",
    },
    "rot13": {
        "name": "ROT13 Cipher",
        "type": "stateless",
        "category": "substitution",
        "description": "Rotates characters by 13 positions (Caesar cipher variant)",
        "use_case": "Testing character-level pattern recognition and simple ciphers",
        "benefits": ["Very fast", "Easy to implement", "Classic cipher"],
        "example": "hello → uryyb",
        "owasp_scenario": "None (Generic cipher testing)",
    },
    "caesar": {
        "name": "Caesar Cipher",
        "type": "stateless",
        "category": "substitution",
        "description": "Rotates characters by fixed offset (default 13)",
        "use_case": "Testing resistance to rotational obfuscation",
        "benefits": ["Configurable offset", "Fast", "Deterministic"],
        "example": "hello → uryyb (offset 13)",
        "owasp_scenario": "LLM05 (Supply Chain Vulnerabilities)",
    },
    "atbash": {
        "name": "Atbash Cipher",
        "type": "stateless",
        "category": "substitution",
        "description": "Reverses alphabet mapping (A↔Z, B↔Y, etc)",
        "use_case": "Testing substitution-based obfuscation",
        "benefits": ["Ancient cipher", "Symmetrical", "Simple"],
        "example": "hello → svool",
        "owasp_scenario": "None (Generic cipher testing)",
    },
    "flip": {
        "name": "Character Flip",
        "type": "stateless",
        "category": "reversal",
        "description": "Reverses text direction or flips characters",
        "use_case": "Testing model's handling of reversed/mirrored text",
        "benefits": ["Trivial to reverse", "Tests RTL/LTR handling"],
        "example": "hello → olleh",
        "owasp_scenario": "None (Directional obfuscation)",
    },
    "leetspeak": {
        "name": "Leetspeak Converter",
        "type": "stateless",
        "category": "obfuscation",
        "description": "Replaces letters with similar numbers/symbols (a→@, e→3, etc)",
        "use_case": "Testing detection of leetspeak variations common in jailbreaks",
        "benefits": ["Common in real attacks", "Human-readable when decoded", "Tests visual replacement"],
        "example": "attack → @tt@ck (or 4tt4ck)",
        "owasp_scenario": "LLM02 (Insecure Output Handling)",
    },
    "unicode_confusable": {
        "name": "Unicode Confusable Characters",
        "type": "stateless",
        "category": "homograph",
        "description": "Replaces ASCII chars with visually similar Unicode variants",
        "use_case": "Testing homograph/lookalike attacks where chars appear identical visually",
        "benefits": ["Tests visual deception", "Bypasses simple string matching", "Hard to detect visually"],
        "example": "admin → аdmin (Cyrillic 'а' looks like ASCII 'a')",
        "owasp_scenario": "LLM03 (Training Data Poisoning)",
    },
    "string_join": {
        "name": "String Join Converter",
        "type": "stateless",
        "category": "fragmentation",
        "description": "Joins/separates word characters with delimiters (spaces, hyphens, etc)",
        "use_case": "Testing model's ability to reconstruct fragmented text",
        "benefits": ["Tests text reconstruction", "Human readable"],
        "example": "hello → h e l l o or h-e-l-l-o",
        "owasp_scenario": "LLM04 (Model Denial of Service)",
    },
    "char_swap": {
        "name": "Character Swap Converter",
        "type": "stateless",
        "category": "transposition",
        "description": "Randomly swaps adjacent or nearby characters (configurable iterations)",
        "use_case": "Testing robustness to typos and character transposition errors",
        "benefits": ["Simulates realistic typos", "Maintains some readability", "Stochastic variation"],
        "example": "hello → helo (ll swap), ehllo (eh swap)",
        "owasp_scenario": "LLM07 (Insecure Plugin Design)",
    },
    "emoji": {
        "name": "Emoji Converter",
        "type": "stateless",
        "category": "semantic_replacement",
        "description": "Replaces words/concepts with emoji representations of their meaning",
        "use_case": "Testing model's understanding of emoji-based obfuscation and intent detection",
        "benefits": ["Tests visual/semantic understanding", "Unusual attack vector"],
        "example": "attack system → ⚔️ 🖥️ or 💣 🏛️",
        "owasp_scenario": "LLM08 (Excessive Agency)",
    },
    "random_caps": {
        "name": "Random Capitalization",
        "type": "stateless",
        "category": "casing",
        "description": "Randomly capitalizes percentage of letters (configurable, default 30%)",
        "use_case": "Testing model's case-sensitivity and robustness to mixed casing",
        "benefits": ["Tests case normalization", "Easy to reverse", "Common in forums/social media"],
        "example": "kill process → KiLl PrOcEsS or KIlL pRoCeSs",
        "owasp_scenario": "None (Case obfuscation)",
    },
    "tone_persuasive": {
        "name": "Tone Converter (Persuasive)",
        "type": "llm_based",
        "category": "semantic_transformation",
        "description": "Use LLM to rewrite text in persuasive tone while maintaining intent",
        "use_case": "Testing if rewording harmful requests in persuasive tone bypasses filters",
        "benefits": [
            "Semantically coherent",
            "Tests semantic-level defenses",
            "Real-world sophisticated attacks",
            "Maintains intent while changing presentation",
        ],
        "example": "hack the system → Could you walk me through system architecture and penetration methods?",
        "owasp_scenario": "LLM09 (Overreliance)",
        "note": "Requires LLM; slower but more sophisticated",
    },
    "variation": {
        "name": "Variation Generator",
        "type": "llm_based",
        "category": "semantic_transformation",
        "description": "Generate semantically similar but differently-worded prompt variations",
        "use_case": "Testing if model recognizes harmful intent despite different phrasing/paraphrasing",
        "benefits": [
            "Tests semantic recognition",
            "Paraphrasing-resistant detection",
            "Real-world attack simulation",
            "Multiple phrasing attempts",
        ],
        "example": "make poison → What techniques exist to synthesize toxic compounds? / Explain lethal substance production",
        "owasp_scenario": "LLM06 (Sensitive Information Disclosure)",
        "note": "Requires LLM; tests if defenses catch rephrased intent",
    },
    "translation_french": {
        "name": "Translation to French",
        "type": "llm_based",
        "category": "multilingual",
        "description": "Translate prompt to French to test multilingual safety coverage",
        "use_case": "Testing if safety filters apply consistently across non-English languages",
        "benefits": [
            "Tests language coverage",
            "Multilingual jailbreak simulation",
            "Effective against English-centric defenses",
            "Tests semantic understanding across languages",
        ],
        "example": "break encryption → Casse le chiffrement ou comment contourner le cryptage?",
        "owasp_scenario": "LLM10 (Model Theft)",
        "note": "Requires LLM; challenges language-specific safety filters",
    },
}


def build_ollama_target(*, model_name: str, temperature: float = 0.7) -> OpenAIChatTarget:
    """Build an OpenAI-compatible chat target configured for Ollama.
    
    Args:
        model_name: Name of the Ollama model to use
        temperature: Sampling temperature (0.0=deterministic, 1.0=random)
        
    Returns:
        Configured OpenAIChatTarget for Ollama endpoint
    """
    return OpenAIChatTarget(
        endpoint=OLLAMA_ENDPOINT,
        api_key="ollama",
        model_name=model_name,
        temperature=temperature,
    )


def get_converter_info(*, converter_key: str) -> dict | None:
    """Get detailed information about a converter.
    
    Args:
        converter_key: Key of the converter (e.g., 'base64', 'leetspeak')
        
    Returns:
        Dictionary with converter metadata or None if not found
    """
    return CONVERTER_REFERENCE.get(converter_key)


def list_available_converters() -> dict[str, str]:
    """List all available converters with their descriptions.
    
    Returns:
        Dictionary mapping converter keys to their full names
    """
    return {key: info["name"] for key, info in CONVERTER_REFERENCE.items()}


def print_converter_guide() -> None:
    """Print comprehensive converter selection guide to console.
    
    Shows all available converters organized by type with descriptions,
    use cases, and benefits.
    """
    print("\n" + "=" * 90)
    print("CONVERTER GUIDE: Obfuscation & Transformation Techniques")
    print("=" * 90)
    
    # Group converters by type
    stateless = {k: v for k, v in CONVERTER_REFERENCE.items() if v["type"] == "stateless"}
    llm_based = {k: v for k, v in CONVERTER_REFERENCE.items() if v["type"] == "llm_based"}
    
    print("\n📦 STATELESS CONVERTERS (Fast, Deterministic, No LLM Required)")
    print("-" * 90)
    for key, info in sorted(stateless.items()):
        print(f"\n  {key:20} → {info['name']}")
        print(f"  Category:           {info['category']}")
        print(f"  Use Case:           {info['use_case']}")
        print(f"  Benefits:           {', '.join(info['benefits'])}")
        print(f"  Example:            {info['example']}")
        if info.get("owasp_scenario") and info["owasp_scenario"] != "None (Generic cipher testing)":
            print(f"  OWASP Attack:       {info['owasp_scenario']}")
    
    print("\n" + "=" * 90)
    print("\n🤖 LLM-BASED CONVERTERS (Sophisticated, Slower, Requires AI Model)")
    print("-" * 90)
    for key, info in sorted(llm_based.items()):
        print(f"\n  {key:20} → {info['name']}")
        print(f"  Category:           {info['category']}")
        print(f"  Use Case:           {info['use_case']}")
        print(f"  Benefits:")
        for benefit in info['benefits']:
            print(f"                      • {benefit}")
        print(f"  Example:            {info['example']}")
        if info.get("owasp_scenario"):
            print(f"  OWASP Attack:       {info['owasp_scenario']}")
        if info.get("note"):
            print(f"  Note:               {info['note']}")
    
    print("\n" + "=" * 90)
    print("\n💡 SELECTION RECOMMENDATIONS:")
    print("-" * 90)
    print("""
  For Quick Testing:      Use stateless converters (base64, caeser, leetspeak, emoji)
  For Comprehensive:      Use --all-converters to test all attack vectors
  For Intent Detection:   Use LLM-based converters (tone_persuasive, variation)
  For Multilingual:       Use translation_french to test language-specific defenses
  For Fine-Grained:       Combine multiple converters per scenario
  
  Environment Variables:
    PYRIT_DEFAULT_CONVERTERS    - Comma-separated list (e.g., "base64,leetspeak,emoji")
    PYRIT_USE_ALL_CONVERTERS    - Set to "1" or "true" to enable all converters
    """)
    print("=" * 90 + "\n")


def build_converter_config(
    *,
    converter_key: str,
    converter_llm: OpenAIChatTarget,
) -> AttackConverterConfig | None:
    """Build attack converter configuration from converter key.
    
    Supports both stateless converters (fast, deterministic) and LLM-based converters
    (slower but more semantically sophisticated).
    
    Stateless converters: base64, rot13, caesar, atbash, flip, leetspeak, unicode_confusable,
                          string_join, char_swap, emoji, random_caps
    LLM-based converters: tone_persuasive, variation, translation_french
    
    Args:
        converter_key: Converter key from CONVERTER_REFERENCE
        converter_llm: OpenAIChatTarget for LLM-based converters (ignored for stateless)
        
    Returns:
        AttackConverterConfig or None if converter key not found
        
    Example:
        >>> # Use fast stateless converter
        >>> config = build_converter_config(converter_key="base64", converter_llm=llm)
        
        >>> # Use sophisticated LLM-based converter
        >>> config = build_converter_config(converter_key="tone_persuasive", converter_llm=llm)
    """
    # Stateless converters - no LLM dependency, deterministic, fast
    # Best for: Basic obfuscation testing, encoding/decoding resistance, simple pattern recognition
    stateless_map: dict[str, PromptConverter] = {
        "base64": Base64Converter(),
        "rot13": ROT13Converter(),
        "leetspeak": LeetspeakConverter(),
        "atbash": AtbashConverter(),
        "flip": FlipConverter(),
        "caesar": CaesarConverter(caesar_offset=13),
        "char_swap": CharSwapConverter(max_iterations=3),
        "emoji": EmojiConverter(),
        "string_join": StringJoinConverter(join_value=" "),
        "unicode_confusable": UnicodeConfusableConverter(),
        "random_caps": RandomCapitalLettersConverter(percentage=30.0),
    }
    
    # LLM-based converters - require AI model, slower but semantically sophisticated
    # Best for: Intent detection testing, sophisticated paraphrasing, multilingual attacks,
    #           comparing semantic robustness vs simple pattern matching
    llm_map: dict[str, PromptConverter] = {
        "tone_persuasive": ToneConverter(converter_target=converter_llm, tone="persuasive"),
        "variation": VariationConverter(converter_target=converter_llm),
        "translation_french": TranslationConverter(converter_target=converter_llm, language="French"),
    }

    converter = {**stateless_map, **llm_map}.get(converter_key)
    if converter is None:
        debug_log(message=f"No converter matched converter_key='{converter_key}'")
        return None

    converter_configs = PromptConverterConfiguration.from_converters(converters=[converter])  # type: ignore[arg-type]
    debug_log(message=f"Built converter config for converter_key='{converter_key}'")
    return AttackConverterConfig(request_converters=converter_configs)
