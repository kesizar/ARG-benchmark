"""
Language configuration module for managing prompt language selection.
Supports switching between Chinese and English prompts.
"""

import os
from typing import Literal

# Language type
Language = Literal["zh", "en"]

# Default language
_current_language: Language = "en"  # Default to English


def set_language(lang: Language) -> None:
    """
    Set the current language for prompts.
    
    Args:
        lang: Language code ('zh' for Chinese, 'en' for English)
    """
    global _current_language
    if lang not in ["zh", "en"]:
        raise ValueError(f"Unsupported language: {lang}. Must be 'zh' or 'en'.")
    _current_language = lang


def get_language() -> Language:
    """
    Get the current language setting.
    
    Returns:
        Current language code ('zh' or 'en')
    """
    return _current_language


def get_prompts():
    """
    Get the prompt module for the current language.
    
    Returns:
        The prompt module (either prompt.py for Chinese or prompt_en.py for English)
    """
    if _current_language == "zh":
        import prompt
        return prompt
    else:
        import prompt_en
        return prompt_en


# Environment variable support
def init_from_env():
    """
    Initialize language from environment variable PROMPT_LANGUAGE.
    """
    env_lang = os.environ.get("PROMPT_LANGUAGE", "en").lower()
    if env_lang in ["zh", "cn", "chinese"]:
        set_language("zh")
    else:
        set_language("en")


# Initialize from environment on module load
init_from_env()