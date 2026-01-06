"""
Parashakti Framework - Feature Flags

Control division and feature availability per organization.
"""

import os
import logging
from typing import Dict, Optional, Set
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)


class FeatureFlag(str, Enum):
    """All available feature flags."""
    
    # Division flags
    SEED_BANK_ENABLED = "SEED_BANK_ENABLED"
    EARTH_SYSTEMS_ENABLED = "EARTH_SYSTEMS_ENABLED"
    SUN_EARTH_SYSTEMS_ENABLED = "SUN_EARTH_SYSTEMS_ENABLED"
    SENSOR_NETWORKS_ENABLED = "SENSOR_NETWORKS_ENABLED"
    COMMERCIAL_ENABLED = "COMMERCIAL_ENABLED"
    SPACE_RESEARCH_ENABLED = "SPACE_RESEARCH_ENABLED"
    
    # Feature flags
    AI_FEATURES_ENABLED = "AI_FEATURES_ENABLED"
    OFFLINE_SYNC_ENABLED = "OFFLINE_SYNC_ENABLED"
    WASM_COMPUTE_ENABLED = "WASM_COMPUTE_ENABLED"
    ADVANCED_GENOMICS_ENABLED = "ADVANCED_GENOMICS_ENABLED"
    COLLABORATION_ENABLED = "COLLABORATION_ENABLED"


# Default flag values
DEFAULT_FLAGS: Dict[str, bool] = {
    # Active divisions - enabled by default
    FeatureFlag.AI_FEATURES_ENABLED: True,
    FeatureFlag.OFFLINE_SYNC_ENABLED: True,
    FeatureFlag.WASM_COMPUTE_ENABLED: True,
    FeatureFlag.ADVANCED_GENOMICS_ENABLED: True,
    FeatureFlag.COLLABORATION_ENABLED: True,
    
    # Beta divisions
    FeatureFlag.EARTH_SYSTEMS_ENABLED: True,
    
    # Planned divisions - disabled by default
    FeatureFlag.SEED_BANK_ENABLED: False,
    FeatureFlag.COMMERCIAL_ENABLED: False,
    FeatureFlag.SENSOR_NETWORKS_ENABLED: False,
    
    # Visionary divisions - disabled
    FeatureFlag.SUN_EARTH_SYSTEMS_ENABLED: False,
    FeatureFlag.SPACE_RESEARCH_ENABLED: False,
}


class FeatureFlagService:
    """
    Service for checking feature flag status.
    
    Flags can be set via:
    1. Environment variables (BIJMANTRA_FLAG_NAME=true)
    2. Organization-specific overrides (from database)
    3. Default values
    
    Priority: Org override > Env var > Default
    """
    
    def __init__(self):
        self._env_flags = self._load_env_flags()
        self._org_overrides: Dict[str, Dict[str, bool]] = {}
    
    def _load_env_flags(self) -> Dict[str, bool]:
        """Load feature flags from environment variables."""
        flags = {}
        for flag in FeatureFlag:
            env_key = f"BIJMANTRA_{flag.value}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                flags[flag.value] = env_value.lower() in ("true", "1", "yes")
                logger.debug(f"Loaded flag from env: {flag.value}={flags[flag.value]}")
        return flags
    
    def is_enabled(
        self,
        flag: FeatureFlag,
        org_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag: The feature flag to check
            org_id: Optional organization ID for org-specific overrides
        
        Returns:
            True if the flag is enabled
        """
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag
        
        # Check org-specific override first
        if org_id and org_id in self._org_overrides:
            org_flags = self._org_overrides[org_id]
            if flag_name in org_flags:
                return org_flags[flag_name]
        
        # Check environment variable
        if flag_name in self._env_flags:
            return self._env_flags[flag_name]
        
        # Fall back to default
        return DEFAULT_FLAGS.get(flag_name, False)
    
    def get_enabled_flags(self, org_id: Optional[str] = None) -> Set[str]:
        """
        Get all enabled flags for an organization.
        
        Args:
            org_id: Optional organization ID
        
        Returns:
            Set of enabled flag names
        """
        enabled = set()
        for flag in FeatureFlag:
            if self.is_enabled(flag, org_id):
                enabled.add(flag.value)
        return enabled
    
    def set_org_override(
        self,
        org_id: str,
        flag: FeatureFlag,
        enabled: bool,
    ) -> None:
        """
        Set an organization-specific flag override.
        
        Args:
            org_id: Organization ID
            flag: Feature flag to override
            enabled: Whether to enable or disable
        """
        if org_id not in self._org_overrides:
            self._org_overrides[org_id] = {}
        self._org_overrides[org_id][flag.value] = enabled
        logger.info(f"Set org override: {org_id}/{flag.value}={enabled}")
    
    def clear_org_overrides(self, org_id: str) -> None:
        """Clear all overrides for an organization."""
        if org_id in self._org_overrides:
            del self._org_overrides[org_id]
    
    def get_all_flags(self, org_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Get status of all flags.
        
        Args:
            org_id: Optional organization ID
        
        Returns:
            Dictionary of flag names to enabled status
        """
        return {
            flag.value: self.is_enabled(flag, org_id)
            for flag in FeatureFlag
        }


# Global feature flag service instance
@lru_cache()
def get_feature_flag_service() -> FeatureFlagService:
    """Get the global feature flag service instance."""
    return FeatureFlagService()


# Convenience function
def is_feature_enabled(
    flag: FeatureFlag,
    org_id: Optional[str] = None,
) -> bool:
    """
    Check if a feature is enabled.
    
    Args:
        flag: Feature flag to check
        org_id: Optional organization ID
    
    Returns:
        True if enabled
    """
    return get_feature_flag_service().is_enabled(flag, org_id)
