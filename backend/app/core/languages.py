"""Supported languages for Voise AI voice agents.

Deepgram nova-2 STT support: en, hi, ta, te, bn, mr, gu, kn, ml, pa
(Odisha or and Assamese as fall back to auto-detect / English)
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Language:
    code: str
    name: str
    native_name: str
    deepgram_code: str
    stt_supported: bool


LANGUAGES: List[Language] = [
    Language(code="hi", name="Hindi", native_name="हिन्दी", deepgram_code="hi", stt_supported=True),
    Language(code="ta", name="Tamil", native_name="தமிழ்", deepgram_code="ta", stt_supported=True),
    Language(code="te", name="Telugu", native_name="తెలుగు", deepgram_code="te", stt_supported=True),
    Language(code="bn", name="Bengali", native_name="বাংলা", deepgram_code="bn", stt_supported=True),
    Language(code="mr", name="Marathi", native_name="मराठी", deepgram_code="mr", stt_supported=True),
    Language(code="gu", name="Gujarati", native_name="ગુજરાતી", deepgram_code="gu", stt_supported=True),
    Language(code="kn", name="Kannada", native_name="ಕನ್ನಡ", deepgram_code="kn", stt_supported=True),
    Language(code="ml", name="Malayalam", native_name="മലയാളം", deepgram_code="ml", stt_supported=True),
    Language(code="pa", name="Punjabi", native_name="ਪੰਜਾਬੀ", deepgram_code="pa", stt_supported=True),
    Language(code="or", name="Odia", native_name="ଓଡ଼ିଆ", deepgram_code="or", stt_supported=False),
    Language(code="as", name="Assamese", native_name="অসমীয়া", deepgram_code="as", stt_supported=False),
    Language(code="en-IN", name="English (India)", native_name="English (India)", deepgram_code="en", stt_supported=True),
    Language(code="en-US", name="English (US)", native_name="English (US)", deepgram_code="en", stt_supported=True),
    Language(code="en-GB", name="English (UK)", native_name="English (UK)", deepgram_code="en", stt_supported=True),
]

SUPPORTED_LANGUAGES = [l.code for l in LANGUAGES]
INDIAN_LANGUAGES = [l.code for l in LANGUAGES if l.code not in ("en-US", "en-GB")]
STT_SUPPORTED_LANGUAGES = [l.code for l in LANGUAGES if l.stt_supported]

_LANGUAGE_NAMES: dict[str, str] = {l.code: l.name for l in LANGUAGES}
_LANGUAGE_NATIVE_NAMES: dict[str, str] = {l.code: l.native_name for l in LANGUAGES}


def language_name(code: str) -> str:
    return _LANGUAGE_NAMES.get(code, code)


def language_native_name(code: str) -> str:
    return _LANGUAGE_NATIVE_NAMES.get(code, code)


def deepgram_language(code: str) -> str:
    for l in LANGUAGES:
        if l.code == code:
            return l.deepgram_code
    return "en"


def default_language() -> str:
    return "en-IN"
