
"""
translate.py
-------------
Translates the agent's English reply into the customer-facing language
that matches the selected voice (Hindi or Gujarati), so the agent's
spoken words -- and the chat transcript -- actually match the chosen
voice's language, not just its accent.
 
Uses Google's free web translation via `deep-translator` (same tradeoff
as the Hindi/Gujarati voices: requires an internet connection, no API
key needed). If translation fails (e.g. no internet), the original
English text is returned so the agent still responds instead of erroring
out silently.
"""
 
_LANGUAGE_CODES = {
    "Hindi": "hi",
    "Gujarati": "gu",
}
 
 
def translate_if_needed(text: str, language: str) -> str:
    """
    Translates `text` from English into `language` if it's Hindi or
    Gujarati. English (or any unrecognized language) is returned as-is.
    """
    target_code = _LANGUAGE_CODES.get(language)
    if not target_code:
        return text
 
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="en", target=target_code).translate(text)
        return translated or text
    except Exception:
        # No internet, translator hiccup, etc. -- fail safe to English
        # rather than breaking the call.
        return text

        