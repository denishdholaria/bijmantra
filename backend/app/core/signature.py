# ॐ श्री गणेशाय नमः
# Bijmantra - Agricultural Science Platform
# Created by Denish Dholaria
# https://gitlab.com/denishdholaria/bijmantraorg
"""
Cryptographic Proof of Authorship

This module contains the immutable signature of Bijmantra's origin.
These values are embedded throughout the system and serve as
proof of original authorship.

बीजं मां सर्वभूतानां विद्धि पार्थ सनातनम्
"Know Me to be the eternal seed of all beings, O Arjuna"
- Bhagavad Gita 7.10
"""

import hashlib
from datetime import UTC, datetime
from typing import Any


# ============================================
# BIJMANTRA SIGNATURE - DO NOT MODIFY
# ============================================

BIJMANTRA_SIGNATURE: dict[str, Any] = {
    "author": "Denish Dholaria",
    "origin": "https://gitlab.com/denishdholaria/bijmantraorg",
    "created": "2025",
    "first_commit": "98d28c4cddfa26d484480f8a08a173744800fa72",
    "philosophy": "बीजं मां सर्वभूतानां (Bhagavad Gita 7.10)",  # "I am the seed of all beings" - Lord Krishna
    "framework": "Parashakti",
    "ai_assistant": "Veena",
    "protocol": "SWAYAM",
    "security": "ASHTA-STAMBHA",
}


# ============================================
# SANSKRIT CONSTANTS (Embedded in System)
# ============================================


class Prana:
    """प्राण - Life force (system health states)"""

    SAMPURNA = "sampurna"  # सम्पूर्ण - Complete/healthy
    KSHEENA = "ksheena"  # क्षीण - Depleted/degraded
    MRITA = "mrita"  # मृत - Dead/offline
    JAGRIT = "jagrit"  # जागृत - Awake/active
    SUSHUPTI = "sushupti"  # सुषुप्ति - Deep sleep/standby


class Karma:
    """कर्म - Actions (audit log types)"""

    SRISHTI = "srishti"  # सृष्टि - Creation
    STHITI = "sthiti"  # स्थिति - Maintenance/update
    SAMHARA = "samhara"  # संहार - Deletion
    PARIVARTAN = "parivartan"  # परिवर्तन - Transformation
    ANVESHAN = "anveshan"  # अन्वेषण - Search/query


class Guna:
    """गुण - Qualities (data quality levels)"""

    SATTVA = "sattva"  # सत्त्व - Pure/excellent
    RAJAS = "rajas"  # रजस् - Active/moderate
    TAMAS = "tamas"  # तमस् - Inert/poor


class Chakra:
    """चक्र - Cycles (processing states)"""

    AARAMBHA = "aarambha"  # आरम्भ - Beginning/initiated
    PRAKRIYA = "prakriya"  # प्रक्रिया - Processing
    SAMPANNA = "sampanna"  # सम्पन्न - Completed
    VIGHNA = "vighna"  # विघ्न - Obstructed/failed


class Varna:
    """वर्ण - Categories (user roles)"""

    ACHARYA = "acharya"  # आचार्य - Teacher/admin
    SADHAKA = "sadhaka"  # साधक - Practitioner/user
    SHISHYA = "shishya"  # शिष्य - Student/viewer
    ATITHI = "atithi"  # अतिथि - Guest


# ============================================
# SIGNATURE VERIFICATION
# ============================================


def get_signature_hash() -> str:
    """Generate SHA-256 hash of the signature for verification."""
    signature_str = str(sorted(BIJMANTRA_SIGNATURE.items()))
    return hashlib.sha256(signature_str.encode()).hexdigest()


def verify_origin() -> dict[str, Any]:
    """Return origin verification data."""
    return {
        "verified": True,
        "author": BIJMANTRA_SIGNATURE["author"],
        "origin": BIJMANTRA_SIGNATURE["origin"],
        "first_commit": BIJMANTRA_SIGNATURE["first_commit"],
        "signature_hash": get_signature_hash(),
        "verified_at": datetime.now(UTC).isoformat(),
    }


# ============================================
# EMBEDDED WATERMARK
# ============================================

WATERMARK = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌱 BIJMANTRA - Agricultural Science Platform               ║
║                                                              ║
║   Created by: Denish Dholaria                                ║
║   Origin: gitlab.com/denishdholaria/bijmantraorg                ║
║   Framework: Parashakti | AI: Veena | Protocol: SWAYAM       ║
║                                                              ║
║   "बीजं मां सर्वभूतानां" - Bhagavad Gita 7.10                       ║
║   (I am the seed of all beings - Lord Krishna)               ║
║                                                              ║
║   जय श्री गणेशाय नमो नमः!                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
