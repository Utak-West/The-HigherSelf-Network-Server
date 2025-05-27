"""
Translation Service for the HigherSelf Network Barter System.

This service provides comprehensive multi-language support for the barter system,
including automatic translation, language detection, and localized content management.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger

from models.barter_models import (
    BarterTranslation,
    LanguageCode,
    TranslationEntity,
)
from services.redis_service import redis_service


class TranslationService:
    """Service for managing translations and multi-language support."""

    def __init__(self):
        self.cache_prefix = "barter:translation:"
        self.cache_ttl = 86400  # 24 hours
        self.supported_languages = [lang.value for lang in LanguageCode]
        
        # Translation providers (can be extended with external services)
        self.translation_providers = {
            "google": self._google_translate,
            "azure": self._azure_translate,
            "local": self._local_translate,
        }
        
        # Language detection patterns
        self.language_patterns = {
            "en": ["the", "and", "is", "in", "to", "of", "a", "that", "it"],
            "es": ["el", "la", "de", "que", "y", "en", "un", "es", "se", "no"],
            "fr": ["le", "de", "et", "à", "un", "il", "être", "et", "en", "avoir"],
            "de": ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich"],
            "pt": ["o", "de", "a", "e", "do", "da", "em", "um", "para", "é"],
            "zh": ["的", "一", "是", "在", "不", "了", "有", "和", "人", "这"],
            "ja": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
            "ar": ["في", "من", "إلى", "على", "أن", "هذا", "كان", "قد", "لا", "ما"],
        }

    async def translate_text(
        self,
        text: str,
        target_language: LanguageCode,
        source_language: Optional[LanguageCode] = None,
        provider: str = "local"
    ) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language (auto-detect if None)
            provider: Translation provider to use
            
        Returns:
            Translated text
        """
        try:
            # Check cache first
            cache_key = self._get_translation_cache_key(
                text, target_language, source_language
            )
            cached_translation = await redis_service.async_get(cache_key)
            if cached_translation:
                logger.debug(f"Translation cache hit for {target_language}")
                return cached_translation

            # Detect source language if not provided
            if not source_language:
                source_language = await self.detect_language(text)

            # Skip translation if source and target are the same
            if source_language == target_language:
                return text

            # Get translation provider
            translate_func = self.translation_providers.get(provider, self._local_translate)
            
            # Perform translation
            translated_text = await translate_func(text, target_language, source_language)
            
            # Cache the result
            await redis_service.async_set(
                cache_key, translated_text, ex=self.cache_ttl
            )
            
            logger.info(f"Translated text from {source_language} to {target_language}")
            return translated_text

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text  # Return original text on failure

    async def detect_language(self, text: str) -> LanguageCode:
        """
        Detect the language of given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code
        """
        try:
            # Simple pattern-based detection
            text_lower = text.lower()
            words = text_lower.split()
            
            language_scores = {}
            
            for lang, patterns in self.language_patterns.items():
                score = sum(1 for word in words if word in patterns)
                if score > 0:
                    language_scores[lang] = score / len(words)
            
            if language_scores:
                detected_lang = max(language_scores, key=language_scores.get)
                return LanguageCode(detected_lang)
            
            # Default to English if no patterns match
            return LanguageCode.ENGLISH

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return LanguageCode.ENGLISH

    async def create_translation(
        self,
        entity_type: TranslationEntity,
        entity_id: UUID,
        field_name: str,
        translated_text: str,
        language_code: LanguageCode
    ) -> BarterTranslation:
        """
        Create a new translation record.
        
        Args:
            entity_type: Type of entity being translated
            entity_id: ID of the entity
            field_name: Name of the field being translated
            translated_text: The translated text
            language_code: Target language code
            
        Returns:
            Created translation record
        """
        try:
            translation = BarterTranslation(
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=field_name,
                translated_text=translated_text,
                language_code=language_code
            )
            
            # Cache the translation
            cache_key = f"{self.cache_prefix}entity:{entity_type}:{entity_id}:{field_name}:{language_code}"
            await redis_service.async_set(
                cache_key,
                translation.model_dump_json(),
                ex=self.cache_ttl
            )
            
            logger.info(f"Created translation for {entity_type} {entity_id} in {language_code}")
            return translation

        except Exception as e:
            logger.error(f"Error creating translation: {e}")
            raise

    async def get_translation(
        self,
        entity_type: TranslationEntity,
        entity_id: UUID,
        field_name: str,
        language_code: LanguageCode
    ) -> Optional[BarterTranslation]:
        """
        Get a specific translation.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            field_name: Name of the field
            language_code: Language code
            
        Returns:
            Translation record if found
        """
        try:
            cache_key = f"{self.cache_prefix}entity:{entity_type}:{entity_id}:{field_name}:{language_code}"
            cached_data = await redis_service.async_get(cache_key)
            
            if cached_data:
                return BarterTranslation.model_validate_json(cached_data)
            
            return None

        except Exception as e:
            logger.error(f"Error getting translation: {e}")
            return None

    async def get_entity_translations(
        self,
        entity_type: TranslationEntity,
        entity_id: UUID,
        language_code: LanguageCode
    ) -> Dict[str, str]:
        """
        Get all translations for an entity in a specific language.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            language_code: Language code
            
        Returns:
            Dictionary mapping field names to translated text
        """
        try:
            # This would typically query the database
            # For now, we'll return an empty dict as a placeholder
            translations = {}
            
            # Common fields that might be translated
            common_fields = ["title", "description", "name"]
            
            for field_name in common_fields:
                translation = await self.get_translation(
                    entity_type, entity_id, field_name, language_code
                )
                if translation:
                    translations[field_name] = translation.translated_text
            
            return translations

        except Exception as e:
            logger.error(f"Error getting entity translations: {e}")
            return {}

    async def auto_translate_entity(
        self,
        entity_type: TranslationEntity,
        entity_id: UUID,
        entity_data: Dict[str, Any],
        target_languages: List[LanguageCode],
        source_language: Optional[LanguageCode] = None
    ) -> Dict[LanguageCode, Dict[str, str]]:
        """
        Automatically translate all translatable fields of an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            entity_data: Entity data containing fields to translate
            target_languages: List of target languages
            source_language: Source language (auto-detect if None)
            
        Returns:
            Dictionary mapping languages to field translations
        """
        try:
            translatable_fields = ["title", "description", "name"]
            results = {}
            
            for target_lang in target_languages:
                results[target_lang] = {}
                
                for field_name in translatable_fields:
                    if field_name in entity_data and entity_data[field_name]:
                        original_text = entity_data[field_name]
                        
                        # Translate the text
                        translated_text = await self.translate_text(
                            original_text, target_lang, source_language
                        )
                        
                        # Store the translation
                        await self.create_translation(
                            entity_type, entity_id, field_name, 
                            translated_text, target_lang
                        )
                        
                        results[target_lang][field_name] = translated_text
            
            logger.info(f"Auto-translated {entity_type} {entity_id} to {len(target_languages)} languages")
            return results

        except Exception as e:
            logger.error(f"Error in auto-translation: {e}")
            return {}

    def _get_translation_cache_key(
        self,
        text: str,
        target_language: LanguageCode,
        source_language: Optional[LanguageCode]
    ) -> str:
        """Generate cache key for translation."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        source = source_language.value if source_language else "auto"
        return f"{self.cache_prefix}text:{source}:{target_language.value}:{text_hash}"

    async def _local_translate(
        self,
        text: str,
        target_language: LanguageCode,
        source_language: LanguageCode
    ) -> str:
        """
        Local translation using simple dictionary lookup.
        This is a placeholder - in production, use proper translation services.
        """
        # Simple translations for common terms
        translations = {
            ("en", "es"): {
                "wellness": "bienestar",
                "consultation": "consulta",
                "massage": "masaje",
                "therapy": "terapia",
                "yoga": "yoga",
                "meditation": "meditación",
                "art": "arte",
                "business": "negocio",
                "strategy": "estrategia",
            },
            ("en", "fr"): {
                "wellness": "bien-être",
                "consultation": "consultation",
                "massage": "massage",
                "therapy": "thérapie",
                "yoga": "yoga",
                "meditation": "méditation",
                "art": "art",
                "business": "entreprise",
                "strategy": "stratégie",
            },
        }
        
        key = (source_language.value, target_language.value)
        if key in translations:
            translation_dict = translations[key]
            words = text.split()
            translated_words = [
                translation_dict.get(word.lower(), word) for word in words
            ]
            return " ".join(translated_words)
        
        return text  # Return original if no translation available

    async def _google_translate(
        self,
        text: str,
        target_language: LanguageCode,
        source_language: LanguageCode
    ) -> str:
        """
        Google Translate integration (placeholder).
        Implement with Google Cloud Translation API.
        """
        # TODO: Implement Google Translate API integration
        logger.warning("Google Translate not implemented, using local translation")
        return await self._local_translate(text, target_language, source_language)

    async def _azure_translate(
        self,
        text: str,
        target_language: LanguageCode,
        source_language: LanguageCode
    ) -> str:
        """
        Azure Translator integration (placeholder).
        Implement with Azure Cognitive Services.
        """
        # TODO: Implement Azure Translator API integration
        logger.warning("Azure Translate not implemented, using local translation")
        return await self._local_translate(text, target_language, source_language)


# Global translation service instance
translation_service = TranslationService()


def get_translation_service() -> TranslationService:
    """Get the global translation service instance."""
    return translation_service
