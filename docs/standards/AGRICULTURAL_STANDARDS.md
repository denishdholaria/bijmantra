# 📋 Agricultural Data Standards Reference

> **Purpose**: Reference documentation for international agricultural data standards
> **Last Updated**: January 7, 2026

---

## Table of Contents

1. [MCPD v2.1 — Multi-Crop Passport Descriptors](#1-mcpd-v21--multi-crop-passport-descriptors)
2. [DUS Testing — Distinctness, Uniformity, Stability](#2-dus-testing--distinctness-uniformity-stability)
3. [How They Complement Each Other](#3-how-they-complement-each-other)

---

## 1. MCPD v2.1 — Multi-Crop Passport Descriptors

**Standard**: FAO/Bioversity Multi-Crop Passport Descriptors  
**Version**: 2.1 (December 2015)  
**Purpose**: Standardize germplasm passport data exchange between genebanks

### 1.1 Overview

MCPD is an international standard for exchanging germplasm passport information. It enables interoperability between genebank information systems and supports global portals like GENESYS and FAO WIEWS.

### 1.2 Key Descriptor Categories (49 Fields Total)

| Category | Fields | Examples |
|----------|--------|----------|
| **Identifiers** | 5 | PUID, INSTCODE, ACCENUMB, COLLNUMB |
| **Collecting Info** | 5 | COLLCODE, COLLNAME, COLLDATE |
| **Taxonomy** | 6 | GENUS, SPECIES, SUBTAXA, CROPNAME |
| **Accession Info** | 3 | ACCENAME, ACQDATE, ORIGCTY |
| **Geographic** | 9 | LATITUDE, LONGITUDE, ELEVATION |
| **Breeding** | 3 | BREDCODE, BREDNAME, ANCEST |
| **Donor** | 3 | DONORCODE, DONORNAME, DONORNUMB |
| **Status Codes** | 4 | SAMPSTAT, COLLSRC, STORAGE, MLSSTAT |

### 1.3 Important Codes

**Biological Status (SAMPSTAT):**
| Code | Description |
|------|-------------|
| 100 | Wild |
| 300 | Traditional cultivar/landrace |
| 400 | Breeding/research material |
| 500 | Advanced/improved cultivar |

**Storage Type (STORAGE):**
| Code | Description |
|------|-------------|
| 11 | Short term (active collection) |
| 12 | Medium term |
| 13 | Long term (base collection) |
| 40 | Cryopreserved collection |

### 1.4 BijMantra Implementation

**Status**: ✅ COMPLETE

**API Endpoints:**
- `GET /api/v2/seed-bank/mcpd/export/csv` — Export as MCPD CSV
- `GET /api/v2/seed-bank/mcpd/export/json` — Export as MCPD JSON
- `POST /api/v2/seed-bank/mcpd/import` — Import from MCPD CSV
- `GET /api/v2/seed-bank/mcpd/template` — Download empty template
- `GET /api/v2/seed-bank/mcpd/codes/*` — Reference data endpoints

---

## 2. DUS Testing — Distinctness, Uniformity, Stability

**Standard**: UPOV (International Union for the Protection of New Varieties of Plants)  
**Members**: 78 member states  
**Purpose**: Variety registration and Plant Variety Protection (PVP)

### 2.1 The Three DUS Tests

| Test | Question | Requirement |
|------|----------|-------------|
| **Distinctness** | Is it different from all known varieties? | Must differ in at least 1 character |
| **Uniformity** | Are all plants the same? | Off-types below threshold (1-3%) |
| **Stability** | Does it stay the same over generations? | Characters must not change |

### 2.2 Character Types

| Type | Description |
|------|-------------|
| **VG** | Visual assessment (Grouping character) |
| **MG** | Measurement (Grouping character) |
| **PQ** | Pseudo-qualitative |
| **QN** | Quantitative |
| **QL** | Qualitative |

### 2.3 Crops with DUS Templates in BijMantra

| Crop | Scientific Name | UPOV Code | Characters |
|------|-----------------|-----------|------------|
| Rice | *Oryza sativa* | ORYZA_SAT | 20 |
| Wheat | *Triticum aestivum* | TRITI_AES | 15 |
| Maize | *Zea mays* | ZEA_MAY | 18 |
| Cotton | *Gossypium hirsutum* | GOSSY_HIR | 18 |
| Groundnut | *Arachis hypogaea* | ARACH_HYP | 17 |
| Soybean | *Glycine max* | GLYCI_MAX | 15 |
| Chickpea | *Cicer arietinum* | CICER_ARI | 16 |

### 2.4 Uniformity Standards (Self-Pollinated Crops)

| Sample Size | Max Off-Types (1%) | Max Off-Types (3%) |
|-------------|--------------------|--------------------|
| 20 | 1 | 2 |
| 50 | 2 | 4 |
| 100 | 3 | 6 |
| 200 | 5 | 10 |

### 2.5 BijMantra Implementation

**Status**: ✅ Backend Complete, 🟡 Frontend Pending

**API Endpoints (17 total):**
- `GET /api/v2/dus/crops` — List crops with DUS templates
- `POST /api/v2/dus/trials` — Create DUS trial
- `POST /api/v2/dus/trials/{id}/entries/{entry}/scores` — Record scores
- `GET /api/v2/dus/trials/{id}/distinctness/{entry}` — Analyze distinctness
- `POST /api/v2/dus/trials/{id}/uniformity/{entry}` — Calculate uniformity
- `GET /api/v2/dus/trials/{id}/report/{entry}` — Generate DUS report

---

## 3. How They Complement Each Other

```
┌─────────────────────────────────────────────────────────────────┐
│                    GERMPLASM LIFECYCLE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   COLLECTION          CONSERVATION           COMMERCIALIZATION  │
│   ──────────          ────────────           ─────────────────  │
│                                                                 │
│   ┌─────────┐         ┌─────────┐           ┌─────────┐        │
│   │  MCPD   │         │  MCPD   │           │   DUS   │        │
│   │         │    →    │         │     →     │         │        │
│   │Passport │         │Passport │           │Variety  │        │
│   │  Data   │         │  Data   │           │Testing  │        │
│   └─────────┘         └─────────┘           └─────────┘        │
│                                                                 │
│   "Where did          "What do we           "Is this variety   │
│    this come           have stored?"         distinct, uniform, │
│    from?"                                    and stable?"       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison

| Aspect | MCPD | DUS |
|--------|------|-----|
| **Purpose** | Germplasm passport data | Variety protection |
| **Governing body** | FAO/Bioversity | UPOV |
| **Applies to** | All germplasm | Candidate varieties only |
| **Data type** | Identity & origin | Morphological characters |
| **When used** | Collection → Exchange | Registration → Protection |
| **In BijMantra** | Seed Bank module | Commercial/Licensing module |

**They don't clash — they complement each other at different stages.**

---

## External Resources

### MCPD
- [FAO/Bioversity MCPD v2.1 PDF](https://www.bioversityinternational.org/fileadmin/user_upload/online_library/publications/pdfs/MCPD_v.2.1.pdf)
- [FAO WIEWS Institute Codes](https://www.fao.org/wiews/)
- [GENESYS Global Portal](https://www.genesys-pgr.org/)

### DUS
- [UPOV Official Website](https://www.upov.int/)
- [UPOV Test Guidelines](https://www.upov.int/test_guidelines/en/)
- [India PPV&FR Authority](http://plantauthority.gov.in/)

### Related Standards
- [BrAPI v2.1](https://brapi.org/specification)
- [ISO 3166-1 Country Codes](https://www.iso.org/iso-3166-country-codes.html)

---

**ॐ श्री गणेशाय नमः** 🙏

*Standardizing agricultural data for global collaboration.*
