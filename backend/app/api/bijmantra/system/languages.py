"""
Language Settings API

Provides endpoints for managing application languages and translations.
"""


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/languages", tags=["languages"])

# ============ SCHEMAS ============

class LanguageUpdate(BaseModel):
    is_enabled: bool | None = None
    is_default: bool | None = None

class TranslationUpdate(BaseModel):
    key: str
    value: str
    language_code: str

# ============ DEMO DATA ============

_languages = [
    {"code": "en", "name": "English", "native_name": "English", "flag": "🇺🇸", "progress": 100, "is_default": True, "is_enabled": True},
    {"code": "es", "name": "Spanish", "native_name": "Español", "flag": "🇪🇸", "progress": 95, "is_default": False, "is_enabled": True},
    {"code": "fr", "name": "French", "native_name": "Français", "flag": "🇫🇷", "progress": 88, "is_default": False, "is_enabled": True},
    {"code": "pt", "name": "Portuguese", "native_name": "Português", "flag": "🇧🇷", "progress": 82, "is_default": False, "is_enabled": True},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "flag": "🇮🇳", "progress": 75, "is_default": False, "is_enabled": True},
    {"code": "zh", "name": "Chinese", "native_name": "中文", "flag": "🇨🇳", "progress": 70, "is_default": False, "is_enabled": False},
    {"code": "ar", "name": "Arabic", "native_name": "العربية", "flag": "🇸🇦", "progress": 65, "is_default": False, "is_enabled": False},
    {"code": "sw", "name": "Swahili", "native_name": "Kiswahili", "flag": "🇰🇪", "progress": 45, "is_default": False, "is_enabled": False},
    {"code": "ja", "name": "Japanese", "native_name": "日本語", "flag": "🇯🇵", "progress": 40, "is_default": False, "is_enabled": False},
    {"code": "de", "name": "German", "native_name": "Deutsch", "flag": "🇩🇪", "progress": 35, "is_default": False, "is_enabled": False}
]

_translation_keys = [
    {"key": "dashboard.welcome", "en": "Welcome to Bijmantra", "es": "Bienvenido a Bijmantra", "fr": "Bienvenue à Bijmantra", "status": "complete"},
    {"key": "trials.create", "en": "Create New Trial", "es": "Crear Nuevo Ensayo", "fr": "Créer un Nouvel Essai", "status": "complete"},
    {"key": "germplasm.search", "en": "Search Germplasm", "es": "Buscar Germoplasma", "fr": "Rechercher du Germoplasme", "status": "complete"},
    {"key": "reports.generate", "en": "Generate Report", "es": "", "fr": "", "status": "pending"},
    {"key": "settings.language", "en": "Language Settings", "es": "Configuración de Idioma", "fr": "Paramètres de Langue", "status": "complete"}
]

# ============ ENDPOINTS ============

@router.get("")
async def list_languages(enabled_only: bool = False):
    """List all available languages"""
    languages = _languages.copy()

    if enabled_only:
        languages = [lang for lang in languages if lang["is_enabled"]]

    return {
        "status": "success",
        "data": languages,
        "total": len(languages)
    }

@router.get("/stats")
async def get_translation_stats():
    """Get translation statistics"""
    total_strings = 2847
    enabled_languages = len([lang for lang in _languages if lang["is_enabled"]])
    avg_progress = sum(lang["progress"] for lang in _languages) / len(_languages) if _languages else 0

    return {
        "status": "success",
        "data": {
            "total_languages": len(_languages),
            "enabled_languages": enabled_languages,
            "total_strings": total_strings,
            "translated": 2654,
            "needs_review": 124,
            "untranslated": 69,
            "average_progress": round(avg_progress, 1)
        }
    }

@router.get("/{language_code}")
async def get_language(language_code: str):
    """Get a specific language"""
    language = next((lang for lang in _languages if lang["code"] == language_code), None)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    return {
        "status": "success",
        "data": language
    }

@router.patch("/{language_code}")
async def update_language(language_code: str, update: LanguageUpdate):
    """Update language settings"""
    language = next((lang for lang in _languages if lang["code"] == language_code), None)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    if update.is_enabled is not None:
        language["is_enabled"] = update.is_enabled

    if update.is_default is not None and update.is_default:
        # Remove default from all other languages
        for lang in _languages:
            lang["is_default"] = False
        language["is_default"] = True

    return {
        "status": "success",
        "data": language,
        "message": "Language updated successfully"
    }

@router.get("/translations/keys")
async def list_translation_keys(
    language_code: str | None = None,
    status: str | None = None,
    limit: int = 50
):
    """List translation keys"""
    keys = _translation_keys.copy()

    if status:
        keys = [k for k in keys if k.get("status") == status]

    return {
        "status": "success",
        "data": keys[:limit],
        "total": len(keys)
    }

@router.post("/translations/keys")
async def create_translation_key(key: str, en_value: str):
    """Create a new translation key"""
    # Check if key already exists
    if any(k["key"] == key for k in _translation_keys):
        raise HTTPException(status_code=400, detail="Translation key already exists")

    new_key = {
        "key": key,
        "en": en_value,
        "status": "pending"
    }
    _translation_keys.append(new_key)

    return {
        "status": "success",
        "data": new_key,
        "message": "Translation key created"
    }

@router.patch("/translations/keys/{key}")
async def update_translation(key: str, update: TranslationUpdate):
    """Update a translation"""
    translation = next((t for t in _translation_keys if t["key"] == key), None)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation key not found")

    # Update the translation for the specified language
    translation[update.language_code] = update.value

    # Update status if all enabled languages have translations
    enabled_langs = [lang["code"] for lang in _languages if lang["is_enabled"]]
    if all(translation.get(lang) for lang in enabled_langs):
        translation["status"] = "complete"

    return {
        "status": "success",
        "data": translation,
        "message": "Translation updated"
    }

@router.post("/export")
async def export_translations(language_code: str, format: str = "json"):
    """Export translations for a language"""
    language = next((lang for lang in _languages if lang["code"] == language_code), None)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    # Build translations object
    translations = {}
    for key_data in _translation_keys:
        if language_code in key_data:
            translations[key_data["key"]] = key_data[language_code]

    return {
        "status": "success",
        "data": {
            "language": language_code,
            "format": format,
            "translations": translations,
            "count": len(translations)
        },
        "message": f"Exported {len(translations)} translations"
    }

@router.post("/import")
async def import_translations(language_code: str, translations: dict):
    """Import translations for a language"""
    language = next((lang for lang in _languages if lang["code"] == language_code), None)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    imported_count = 0
    for key, value in translations.items():
        # Find or create translation key
        translation = next((t for t in _translation_keys if t["key"] == key), None)
        if translation:
            translation[language_code] = value
            imported_count += 1
        else:
            # Create new key
            new_key = {"key": key, "en": "", language_code: value, "status": "pending"}
            _translation_keys.append(new_key)
            imported_count += 1

    return {
        "status": "success",
        "message": f"Imported {imported_count} translations",
        "count": imported_count
    }

@router.post("/{language_code}/auto-translate")
async def auto_translate(language_code: str):
    """Auto-translate missing strings (placeholder for AI translation)"""
    language = next((lang for lang in _languages if lang["code"] == language_code), None)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    # In production, this would call an AI translation service
    # For now, just return a success message
    return {
        "status": "success",
        "message": f"Auto-translation queued for {language['name']}",
        "note": "This feature requires AI translation service integration"
    }
