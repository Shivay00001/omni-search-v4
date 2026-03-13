from deep_translator import GoogleTranslator
import asyncio

# 25+ languages covering all major world regions
SUPPORTED_LANGUAGES = {
    # European
    "en": {"name": "English", "native": "English", "flag": "🇺🇸"},
    "es": {"name": "Spanish", "native": "Español", "flag": "🇪🇸"},
    "fr": {"name": "French", "native": "Français", "flag": "🇫🇷"},
    "de": {"name": "German", "native": "Deutsch", "flag": "🇩🇪"},
    "it": {"name": "Italian", "native": "Italiano", "flag": "🇮🇹"},
    "pt": {"name": "Portuguese", "native": "Português", "flag": "🇧🇷"},
    "nl": {"name": "Dutch", "native": "Nederlands", "flag": "🇳🇱"},
    "pl": {"name": "Polish", "native": "Polski", "flag": "🇵🇱"},
    "ru": {"name": "Russian", "native": "Русский", "flag": "🇷🇺"},
    "uk": {"name": "Ukrainian", "native": "Українська", "flag": "🇺🇦"},
    "sv": {"name": "Swedish", "native": "Svenska", "flag": "🇸🇪"},
    "el": {"name": "Greek", "native": "Ελληνικά", "flag": "🇬🇷"},
    # Asian
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
    "bn": {"name": "Bengali", "native": "বাংলা", "flag": "🇧🇩"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "flag": "🇮🇳"},
    "te": {"name": "Telugu", "native": "తెలుగు", "flag": "🇮🇳"},
    "zh-CN": {"name": "Chinese (Simplified)", "native": "简体中文", "flag": "🇨🇳"},
    "zh-TW": {"name": "Chinese (Traditional)", "native": "繁體中文", "flag": "🇹🇼"},
    "ja": {"name": "Japanese", "native": "日本語", "flag": "🇯🇵"},
    "ko": {"name": "Korean", "native": "한국어", "flag": "🇰🇷"},
    "th": {"name": "Thai", "native": "ไทย", "flag": "🇹🇭"},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt", "flag": "🇻🇳"},
    "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "flag": "🇮🇩"},
    "ms": {"name": "Malay", "native": "Bahasa Melayu", "flag": "🇲🇾"},
    # Middle Eastern
    "ar": {"name": "Arabic", "native": "العربية", "flag": "🇸🇦"},
    "tr": {"name": "Turkish", "native": "Türkçe", "flag": "🇹🇷"},
    "fa": {"name": "Persian", "native": "فارسی", "flag": "🇮🇷"},
    "he": {"name": "Hebrew", "native": "עברית", "flag": "🇮🇱"},
    # African
    "sw": {"name": "Swahili", "native": "Kiswahili", "flag": "🇰🇪"},
}

class TranslatorManager:
    def __init__(self):
        self.en_translator = GoogleTranslator(source='auto', target='en')
        self._translator_cache = {}
        
    def _get_translator(self, lang: str) -> GoogleTranslator:
        """Get or create a cached translator instance."""
        if lang not in self._translator_cache:
            self._translator_cache[lang] = GoogleTranslator(source='auto', target=lang)
        return self._translator_cache[lang]
        
    async def translate_to_en(self, text: str) -> str:
        """Translates any text to English for global search."""
        try:
            return await asyncio.to_thread(self.en_translator.translate, text)
        except Exception as e:
            print(f"Translation to EN error: {e}")
            return text

    async def translate_to_target(self, text: str, lang: str = 'en') -> str:
        """Translates text to user's specified target language."""
        if lang == 'en' or not text or not text.strip():
            return text
        try:
            translator = self._get_translator(lang)
            return await asyncio.to_thread(translator.translate, text)
        except Exception as e:
            print(f"Translation to {lang} error: {e}")
            return text

    def get_supported_languages(self):
        """Returns list of supported languages with metadata."""
        return [
            {"code": code, **info}
            for code, info in SUPPORTED_LANGUAGES.items()
        ]

translator_manager = TranslatorManager()
