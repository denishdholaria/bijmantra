"""
System Domain Router Aggregator

Aggregates all system-related routers:
- system_settings: System-wide configuration management
- capabilities: Tenant-scoped capability-app installation management
- backup: Database backup and restore
- external_services: External service integration status
- integrations: Integration hub for external APIs
- languages: Language and translation management
- licensing: Variety licensing and PVP/PBR management
- pwa_notifications: PWA push notification subscriptions
- pwa_sync: PWA offline draft synchronization
- profile: User profile management
"""

from fastapi import APIRouter

from app.api.bijmantra.system import (
    backup,
    capabilities,
    external_services,
    integrations,
    languages,
    licensing,
    marketplace,
    profile,
    pwa_notifications,
    pwa_sync,
    system_settings,
)


system_router = APIRouter()

# System configuration and settings
system_router.include_router(system_settings.router, tags=["System Settings"])

# Platform capability-app context and management
system_router.include_router(capabilities.current_user_router, tags=["Platform Capabilities"])
system_router.include_router(capabilities.router, tags=["Platform Capabilities"])

# Backup and restore
system_router.include_router(backup.router, tags=["Backup"])

# External services and integrations
system_router.include_router(external_services.router, tags=["External Services"])
system_router.include_router(integrations.router, tags=["Integrations"])

# Localization
system_router.include_router(languages.router, tags=["Languages"])

# Variety licensing
system_router.include_router(licensing.router, tags=["Licensing"])

# PWA features
system_router.include_router(pwa_notifications.router, tags=["PWA Notifications"])
system_router.include_router(pwa_sync.router, tags=["PWA Sync"])

# User profile
system_router.include_router(profile.router, tags=["Profile"])

# Marketplace integration
system_router.include_router(marketplace.router, tags=["Marketplace Integration"])
