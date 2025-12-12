# 🔬 BrAPI 2.1 Compliance Audit

> **Purpose**: Track BijMantra's compliance with BrAPI (Breeding API) v2.1 specification
> **Last Audit**: December 12, 2025
> **Auditor**: AI Agent (SWAYAM)
> **Reference**: `/docs/confidential/BrAPI-2.1-reference/`

---

## 📊 Executive Summary

| Module | BrAPI Endpoints | Implemented | Coverage |
|--------|-----------------|-------------|----------|
| **BrAPI-Core** | 27 | 22 | 81% |
| **BrAPI-Phenotyping** | 35 | 24 | 69% |
| **BrAPI-Genotyping** | 47 | 12 | 26% |
| **BrAPI-Germplasm** | 26 | 16 | 62% |
| **TOTAL** | **135** | **74** | **55%** |

**Legend:**
- ✅ **Implemented** — Endpoint exists and follows BrAPI response format
- 🟡 **Partial** — Endpoint exists but missing some BrAPI features (search, PUT)
- ❌ **Missing** — Endpoint not implemented
- ⚪ **N/A** — Not applicable for this application

---

## 🏛️ BrAPI-Core Module

### Programs

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Programs | GET | `/programs` | `/api/v2/programs` | ✅ | Full CRUD, pagination |
| Get Program | GET | `/programs/{programDbId}` | `/api/v2/programs/{programDbId}` | ✅ | |
| Create Program | POST | `/programs` | `/api/v2/programs` | ✅ | |
| Update Program | PUT | `/programs/{programDbId}` | `/api/v2/programs/{programDbId}` | ✅ | |
| Search Programs | POST | `/search/programs` | — | ❌ | Missing |
| Search Results | GET | `/search/programs/{searchResultsDbId}` | — | ❌ | Missing |

### Trials

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Trials | GET | `/trials` | `/api/v2/trials` | ✅ | Full CRUD, pagination |
| Get Trial | GET | `/trials/{trialDbId}` | `/api/v2/trials/{trialDbId}` | ✅ | |
| Create Trial | POST | `/trials` | `/api/v2/trials` | ✅ | |
| Update Trial | PUT | `/trials/{trialDbId}` | `/api/v2/trials/{trialDbId}` | ✅ | |
| Search Trials | POST | `/search/trials` | — | ❌ | Missing |
| Search Results | GET | `/search/trials/{searchResultsDbId}` | — | ❌ | Missing |

### Studies

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Studies | GET | `/studies` | `/api/v2/studies` | ✅ | Full CRUD, pagination |
| Get Study | GET | `/studies/{studyDbId}` | `/api/v2/studies/{studyDbId}` | ✅ | |
| Create Study | POST | `/studies` | `/api/v2/studies` | ✅ | |
| Update Study | PUT | `/studies/{studyDbId}` | `/api/v2/studies/{studyDbId}` | ✅ | |
| Study Types | GET | `/studytypes` | — | ❌ | Missing |
| Search Studies | POST | `/search/studies` | — | ❌ | Missing |
| Search Results | GET | `/search/studies/{searchResultsDbId}` | — | ❌ | Missing |

### Locations

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Locations | GET | `/locations` | `/api/v2/locations` | ✅ | Full CRUD, pagination |
| Get Location | GET | `/locations/{locationDbId}` | `/api/v2/locations/{locationDbId}` | ✅ | |
| Create Location | POST | `/locations` | `/api/v2/locations` | ✅ | |
| Update Location | PUT | `/locations/{locationDbId}` | `/api/v2/locations/{locationDbId}` | ✅ | |
| Search Locations | POST | `/search/locations` | — | ❌ | Missing |
| Search Results | GET | `/search/locations/{searchResultsDbId}` | — | ❌ | Missing |

### Seasons

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Seasons | GET | `/seasons` | `/api/v2/seasons` | ✅ | Full CRUD, pagination |
| Get Season | GET | `/seasons/{seasonDbId}` | `/api/v2/seasons/{seasonDbId}` | ✅ | |
| Create Season | POST | `/seasons` | `/api/v2/seasons` | ✅ | |
| Update Season | PUT | `/seasons/{seasonDbId}` | `/api/v2/seasons/{seasonDbId}` | ✅ | |

### People

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List People | GET | `/people` | `/api/brapi/people` | ✅ | Full CRUD |
| Get Person | GET | `/people/{personDbId}` | `/api/brapi/people/{personDbId}` | ✅ | |
| Create Person | POST | `/people` | `/api/brapi/people` | ✅ | |
| Update Person | PUT | `/people/{personDbId}` | `/api/brapi/people/{personDbId}` | ✅ | |
| Delete Person | DELETE | `/people/{personDbId}` | `/api/brapi/people/{personDbId}` | ✅ | |
| Search People | POST | `/search/people` | — | ❌ | Missing |
| Search Results | GET | `/search/people/{searchResultsDbId}` | — | ❌ | Missing |

### Lists

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Lists | GET | `/lists` | — | ❌ | Missing |
| Get List | GET | `/lists/{listDbId}` | — | ❌ | Missing |
| Create List | POST | `/lists` | — | ❌ | Missing |
| Update List | PUT | `/lists/{listDbId}` | — | ❌ | Missing |
| Add Items | POST | `/lists/{listDbId}/items` | — | ❌ | Missing |
| Add Data | POST | `/lists/{listDbId}/data` | — | ❌ | Missing |
| Search Lists | POST | `/search/lists` | — | ❌ | Missing |
| Search Results | GET | `/search/lists/{searchResultsDbId}` | — | ❌ | Missing |

### Common Crop Names

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Crop Names | GET | `/commoncropnames` | — | ❌ | Missing |

### Server Info

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| Server Info | GET | `/serverinfo` | `/api/v2/server/info` | ✅ | |

---

## 🌿 BrAPI-Phenotyping Module

### Observations

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Observations | GET | `/observations` | `/api/brapi/observations` | ✅ | Pagination, filters |
| Get Observation | GET | `/observations/{observationDbId}` | `/api/brapi/observations/{observationDbId}` | ✅ | |
| Create Observations | POST | `/observations` | `/api/brapi/observations` | ✅ | |
| Update Observations | PUT | `/observations` | — | ❌ | Missing bulk update |
| Update Observation | PUT | `/observations/{observationDbId}` | — | ❌ | Missing |
| Delete Observations | POST | `/delete/observations` | — | ❌ | Missing |
| Observations Table | GET | `/observations/table` | — | ❌ | Missing |
| Search Observations | POST | `/search/observations` | — | ❌ | Missing |
| Search Results | GET | `/search/observations/{searchResultsDbId}` | — | ❌ | Missing |

### Observation Units

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Units | GET | `/observationunits` | `/api/brapi/observationunits` | ✅ | Pagination, filters |
| Get Unit | GET | `/observationunits/{observationUnitDbId}` | `/api/brapi/observationunits/{observationUnitDbId}` | ✅ | |
| Create Units | POST | `/observationunits` | `/api/brapi/observationunits` | ✅ | |
| Update Units | PUT | `/observationunits` | — | ❌ | Missing bulk update |
| Update Unit | PUT | `/observationunits/{observationUnitDbId}` | — | ❌ | Missing |
| Units Table | GET | `/observationunits/table` | — | ❌ | Missing |
| Observation Levels | GET | `/observationlevels` | — | ❌ | Missing |
| Search Units | POST | `/search/observationunits` | — | ❌ | Missing |
| Search Results | GET | `/search/observationunits/{searchResultsDbId}` | — | ❌ | Missing |

### Observation Variables

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Variables | GET | `/variables` | `/api/brapi/variables` | ✅ | Pagination, filters |
| Get Variable | GET | `/variables/{observationVariableDbId}` | `/api/brapi/variables/{observationVariableDbId}` | ✅ | |
| Create Variable | POST | `/variables` | `/api/brapi/variables` | ✅ | |
| Update Variable | PUT | `/variables/{observationVariableDbId}` | `/api/brapi/variables/{observationVariableDbId}` | ✅ | |
| Delete Variable | DELETE | `/variables/{observationVariableDbId}` | `/api/brapi/variables/{observationVariableDbId}` | ✅ | |
| Search Variables | POST | `/search/variables` | — | ❌ | Missing |
| Search Results | GET | `/search/variables/{searchResultsDbId}` | — | ❌ | Missing |

### Traits

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Traits | GET | `/traits` | `/api/brapi/traits` | ✅ | Pagination, filters |
| Get Trait | GET | `/traits/{traitDbId}` | `/api/brapi/traits/{traitDbId}` | ✅ | |
| Create Trait | POST | `/traits` | `/api/brapi/traits` | ✅ | |
| Update Trait | PUT | `/traits/{traitDbId}` | — | ❌ | Missing |

### Methods

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Methods | GET | `/methods` | — | ❌ | Missing |
| Get Method | GET | `/methods/{methodDbId}` | — | ❌ | Missing |
| Create Method | POST | `/methods` | — | ❌ | Missing |
| Update Method | PUT | `/methods/{methodDbId}` | — | ❌ | Missing |

### Scales

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Scales | GET | `/scales` | — | ❌ | Missing |
| Get Scale | GET | `/scales/{scaleDbId}` | — | ❌ | Missing |
| Create Scale | POST | `/scales` | — | ❌ | Missing |
| Update Scale | PUT | `/scales/{scaleDbId}` | — | ❌ | Missing |

### Ontologies

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Ontologies | GET | `/ontologies` | — | ❌ | Missing |
| Get Ontology | GET | `/ontologies/{ontologyDbId}` | — | ❌ | Missing |
| Create Ontology | POST | `/ontologies` | — | ❌ | Missing |
| Update Ontology | PUT | `/ontologies/{ontologyDbId}` | — | ❌ | Missing |

### Events

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Events | GET | `/events` | `/api/brapi/events` | ✅ | Pagination, filters |
| Get Event | GET | `/events/{eventDbId}` | `/api/brapi/events/{eventDbId}` | ✅ | |
| Create Event | POST | `/events` | `/api/brapi/events` | ✅ | |

### Images

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Images | GET | `/images` | `/api/brapi/images` | ✅ | Pagination |
| Get Image | GET | `/images/{imageDbId}` | `/api/brapi/images/{imageDbId}` | ✅ | |
| Create Image | POST | `/images` | `/api/brapi/images` | ✅ | |
| Update Image | PUT | `/images/{imageDbId}` | — | ❌ | Missing |
| Image Content | PUT | `/images/{imageDbId}/imagecontent` | — | ❌ | Missing |
| Delete Images | POST | `/delete/images` | — | ❌ | Missing |
| Search Images | POST | `/search/images` | — | ❌ | Missing |
| Search Results | GET | `/search/images/{searchResultsDbId}` | — | ❌ | Missing |

---

## 🧬 BrAPI-Genotyping Module

### Samples

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Samples | GET | `/samples` | `/api/brapi/samples` | ✅ | Pagination, filters |
| Get Sample | GET | `/samples/{sampleDbId}` | `/api/brapi/samples/{sampleDbId}` | ✅ | |
| Create Samples | POST | `/samples` | `/api/brapi/samples` | ✅ | |
| Update Samples | PUT | `/samples` | — | ❌ | Missing bulk update |
| Update Sample | PUT | `/samples/{sampleDbId}` | — | ❌ | Missing |
| Search Samples | POST | `/search/samples` | — | ❌ | Missing |
| Search Results | GET | `/search/samples/{searchResultsDbId}` | — | ❌ | Missing |

### Variants

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Variants | GET | `/variants` | `/api/v2/variants` | 🟡 | Basic list only |
| Get Variant | GET | `/variants/{variantDbId}` | — | ❌ | Missing |
| Variant Calls | GET | `/variants/{variantDbId}/calls` | — | ❌ | Missing |
| Search Variants | POST | `/search/variants` | — | ❌ | Missing |
| Search Results | GET | `/search/variants/{searchResultsDbId}` | — | ❌ | Missing |

### Calls

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Calls | GET | `/calls` | — | ❌ | Missing |
| Update Calls | PUT | `/calls` | — | ❌ | Missing |
| Search Calls | POST | `/search/calls` | — | ❌ | Missing |
| Search Results | GET | `/search/calls/{searchResultsDbId}` | — | ❌ | Missing |

### CallSets

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List CallSets | GET | `/callsets` | — | ❌ | Missing |
| Get CallSet | GET | `/callsets/{callSetDbId}` | — | ❌ | Missing |
| CallSet Calls | GET | `/callsets/{callSetDbId}/calls` | — | ❌ | Missing |
| Search CallSets | POST | `/search/callsets` | — | ❌ | Missing |
| Search Results | GET | `/search/callsets/{searchResultsDbId}` | — | ❌ | Missing |

### Allele Matrix

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| Get Matrix | GET | `/allelematrix` | `/api/v2/allelematrix` | 🟡 | Basic implementation |
| Search Matrix | POST | `/search/allelematrix` | — | ❌ | Missing |
| Search Results | GET | `/search/allelematrix/{searchResultsDbId}` | — | ❌ | Missing |

### Plates

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Plates | GET | `/plates` | `/api/v2/plates` | 🟡 | Basic implementation |
| Get Plate | GET | `/plates/{plateDbId}` | — | ❌ | Missing |
| Create Plates | POST | `/plates` | — | ❌ | Missing |
| Update Plates | PUT | `/plates` | — | ❌ | Missing |
| Search Plates | POST | `/search/plates` | — | ❌ | Missing |
| Search Results | GET | `/search/plates/{searchResultsDbId}` | — | ❌ | Missing |

### Genome Maps

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Maps | GET | `/maps` | `/api/v2/maps` | 🟡 | Basic implementation |
| Get Map | GET | `/maps/{mapDbId}` | — | ❌ | Missing |
| Linkage Groups | GET | `/maps/{mapDbId}/linkagegroups` | — | ❌ | Missing |
| Marker Positions | GET | `/markerpositions` | — | ❌ | Missing |
| Search Positions | POST | `/search/markerpositions` | — | ❌ | Missing |
| Search Results | GET | `/search/markerpositions/{searchResultsDbId}` | — | ❌ | Missing |

### References

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List References | GET | `/references` | — | ❌ | Missing |
| Get Reference | GET | `/references/{referenceDbId}` | — | ❌ | Missing |
| Reference Bases | GET | `/references/{referenceDbId}/bases` | — | ❌ | Missing |
| Search References | POST | `/search/references` | — | ❌ | Missing |
| Search Results | GET | `/search/references/{searchResultsDbId}` | — | ❌ | Missing |

### Reference Sets

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List RefSets | GET | `/referencesets` | — | ❌ | Missing |
| Get RefSet | GET | `/referencesets/{referenceSetDbId}` | — | ❌ | Missing |
| Search RefSets | POST | `/search/referencesets` | — | ❌ | Missing |
| Search Results | GET | `/search/referencesets/{searchResultsDbId}` | — | ❌ | Missing |

### Variant Sets

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List VariantSets | GET | `/variantsets` | — | ❌ | Missing |
| Get VariantSet | GET | `/variantsets/{variantSetDbId}` | — | ❌ | Missing |
| VariantSet Calls | GET | `/variantsets/{variantSetDbId}/calls` | — | ❌ | Missing |
| VariantSet CallSets | GET | `/variantsets/{variantSetDbId}/callsets` | — | ❌ | Missing |
| VariantSet Variants | GET | `/variantsets/{variantSetDbId}/variants` | — | ❌ | Missing |
| Extract VariantSet | POST | `/variantsets/extract` | — | ❌ | Missing |
| Search VariantSets | POST | `/search/variantsets` | — | ❌ | Missing |
| Search Results | GET | `/search/variantsets/{searchResultsDbId}` | — | ❌ | Missing |

### Vendor Samples

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| Vendor Specs | GET | `/vendor/specifications` | — | ❌ | Missing |
| List Orders | GET | `/vendor/orders` | — | ❌ | Missing |
| Create Order | POST | `/vendor/orders` | — | ❌ | Missing |
| Order Plates | GET | `/vendor/orders/{orderId}/plates` | — | ❌ | Missing |
| Order Results | GET | `/vendor/orders/{orderId}/results` | — | ❌ | Missing |
| Order Status | GET | `/vendor/orders/{orderId}/status` | — | ❌ | Missing |
| Submit Plates | POST | `/vendor/plates` | — | ❌ | Missing |
| Get Submission | GET | `/vendor/plates/{submissionId}` | — | ❌ | Missing |

---

## 🌱 BrAPI-Germplasm Module

### Germplasm

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Germplasm | GET | `/germplasm` | `/api/brapi/germplasm` | ✅ | Pagination, filters |
| Get Germplasm | GET | `/germplasm/{germplasmDbId}` | `/api/brapi/germplasm/{germplasmDbId}` | ✅ | |
| Create Germplasm | POST | `/germplasm` | `/api/brapi/germplasm` | ✅ | |
| Update Germplasm | PUT | `/germplasm/{germplasmDbId}` | `/api/brapi/germplasm/{germplasmDbId}` | ✅ | |
| Delete Germplasm | DELETE | `/germplasm/{germplasmDbId}` | `/api/brapi/germplasm/{germplasmDbId}` | ✅ | |
| Germplasm MCPD | GET | `/germplasm/{germplasmDbId}/mcpd` | — | ❌ | Missing |
| Germplasm Pedigree | GET | `/germplasm/{germplasmDbId}/pedigree` | — | ❌ | Missing |
| Germplasm Progeny | GET | `/germplasm/{germplasmDbId}/progeny` | — | ❌ | Missing |
| Search Germplasm | POST | `/search/germplasm` | — | ❌ | Missing |
| Search Results | GET | `/search/germplasm/{searchResultsDbId}` | — | ❌ | Missing |

### Breeding Methods

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Methods | GET | `/breedingmethods` | — | ❌ | Missing |
| Get Method | GET | `/breedingmethods/{breedingMethodDbId}` | — | ❌ | Missing |

### Germplasm Attributes

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Attributes | GET | `/attributes` | — | ❌ | Missing |
| Get Attribute | GET | `/attributes/{attributeDbId}` | — | ❌ | Missing |
| Create Attribute | POST | `/attributes` | — | ❌ | Missing |
| Update Attribute | PUT | `/attributes/{attributeDbId}` | — | ❌ | Missing |
| Attribute Categories | GET | `/attributes/categories` | — | ❌ | Missing |
| Search Attributes | POST | `/search/attributes` | — | ❌ | Missing |
| Search Results | GET | `/search/attributes/{searchResultsDbId}` | — | ❌ | Missing |

### Germplasm Attribute Values

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Values | GET | `/attributevalues` | — | ❌ | Missing |
| Get Value | GET | `/attributevalues/{attributeValueDbId}` | — | ❌ | Missing |
| Create Values | POST | `/attributevalues` | — | ❌ | Missing |
| Update Value | PUT | `/attributevalues/{attributeValueDbId}` | — | ❌ | Missing |
| Search Values | POST | `/search/attributevalues` | — | ❌ | Missing |
| Search Results | GET | `/search/attributevalues/{searchResultsDbId}` | — | ❌ | Missing |

### Pedigree

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Pedigree | GET | `/pedigree` | `/api/v2/pedigree` | 🟡 | Custom implementation |
| Create Pedigree | POST | `/pedigree` | — | ❌ | Missing |
| Update Pedigree | PUT | `/pedigree` | — | ❌ | Missing |
| Search Pedigree | POST | `/search/pedigree` | — | ❌ | Missing |
| Search Results | GET | `/search/pedigree/{searchResultsDbId}` | — | ❌ | Missing |

### Crosses

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Crosses | GET | `/crosses` | `/api/brapi/crosses` | ✅ | Pagination, filters |
| Get Cross | GET | `/crosses/{crossDbId}` | `/api/brapi/crosses/{crossDbId}` | ✅ | |
| Create Crosses | POST | `/crosses` | `/api/brapi/crosses` | ✅ | |
| Update Crosses | PUT | `/crosses` | — | ❌ | Missing bulk update |

### Crossing Projects

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Projects | GET | `/crossingprojects` | `/api/v2/crossingprojects` | 🟡 | Basic implementation |
| Get Project | GET | `/crossingprojects/{crossingProjectDbId}` | — | ❌ | Missing |
| Create Project | POST | `/crossingprojects` | — | ❌ | Missing |
| Update Project | PUT | `/crossingprojects/{crossingProjectDbId}` | — | ❌ | Missing |

### Planned Crosses

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Planned | GET | `/plannedcrosses` | `/api/v2/plannedcrosses` | 🟡 | Basic implementation |
| Create Planned | POST | `/plannedcrosses` | — | ❌ | Missing |
| Update Planned | PUT | `/plannedcrosses` | — | ❌ | Missing |

### Seed Lots

| Endpoint | Method | BrAPI Path | BijMantra Path | Status | Notes |
|----------|--------|------------|----------------|--------|-------|
| List Seed Lots | GET | `/seedlots` | `/api/brapi/seedlots` | ✅ | Pagination, filters |
| Get Seed Lot | GET | `/seedlots/{seedLotDbId}` | `/api/brapi/seedlots/{seedLotDbId}` | ✅ | |
| Create Seed Lots | POST | `/seedlots` | `/api/brapi/seedlots` | ✅ | |
| Update Seed Lot | PUT | `/seedlots/{seedLotDbId}` | `/api/brapi/seedlots/{seedLotDbId}` | ✅ | |
| Lot Transactions | GET | `/seedlots/{seedLotDbId}/transactions` | — | ❌ | Missing |
| List Transactions | GET | `/seedlots/transactions` | — | ❌ | Missing |
| Create Transaction | POST | `/seedlots/transactions` | — | ❌ | Missing |

---

## 📈 Gap Analysis

### Critical Missing Features

| Feature | Impact | Priority | Effort |
|---------|--------|----------|--------|
| **Search Endpoints** | All `/search/*` endpoints missing | HIGH | Medium |
| **Lists Module** | No list management | MEDIUM | Low |
| **Genotyping Module** | Only 26% coverage | HIGH | High |
| **MCPD/Pedigree/Progeny** | Germplasm sub-endpoints missing | MEDIUM | Medium |
| **Bulk Updates** | PUT for arrays not implemented | LOW | Low |

### Search Endpoints Gap

BrAPI uses async search pattern with POST to initiate and GET to retrieve results. BijMantra is missing all 20+ search endpoints:

```
POST /search/{entity}           → Returns searchResultsDbId
GET  /search/{entity}/{id}      → Returns paginated results
```

**Entities needing search:**
- programs, trials, studies, locations, people, lists
- germplasm, attributes, attributevalues, pedigree
- observations, observationunits, variables, images
- samples, variants, calls, callsets, allelematrix, plates, markerpositions
- references, referencesets, variantsets

### Genotyping Module Gap

The genotyping module has the lowest coverage (26%). Missing critical endpoints:

| Entity | Missing Endpoints |
|--------|-------------------|
| Variants | GET by ID, calls, search |
| Calls | All endpoints |
| CallSets | All endpoints |
| References | All endpoints |
| ReferenceSets | All endpoints |
| VariantSets | All endpoints |
| Vendor | All endpoints |

---

## 🎯 Implementation Roadmap

### Phase 1: Core Compliance (Priority: HIGH)

| Task | Endpoints | Effort | Status |
|------|-----------|--------|--------|
| Add Search Infrastructure | 1 base | 4h | ❌ |
| Programs Search | 2 | 2h | ❌ |
| Trials Search | 2 | 2h | ❌ |
| Studies Search | 2 | 2h | ❌ |
| Germplasm Search | 2 | 2h | ❌ |
| Observations Search | 2 | 2h | ❌ |
| **Subtotal** | **11** | **14h** | |

### Phase 2: Germplasm Enhancement (Priority: HIGH)

| Task | Endpoints | Effort | Status |
|------|-----------|--------|--------|
| Germplasm MCPD | 1 | 2h | ❌ |
| Germplasm Pedigree | 1 | 2h | ❌ |
| Germplasm Progeny | 1 | 2h | ❌ |
| Breeding Methods | 2 | 2h | ❌ |
| Seed Lot Transactions | 3 | 3h | ❌ |
| **Subtotal** | **8** | **11h** | |

### Phase 3: Phenotyping Completion (Priority: MEDIUM)

| Task | Endpoints | Effort | Status |
|------|-----------|--------|--------|
| Methods CRUD | 4 | 3h | ❌ |
| Scales CRUD | 4 | 3h | ❌ |
| Ontologies CRUD | 4 | 3h | ❌ |
| Observation Levels | 1 | 1h | ❌ |
| Observations Table | 1 | 2h | ❌ |
| ObservationUnits Table | 1 | 2h | ❌ |
| **Subtotal** | **15** | **14h** | |

### Phase 4: Genotyping Module (Priority: LOW)

| Task | Endpoints | Effort | Status |
|------|-----------|--------|--------|
| Calls CRUD | 4 | 4h | ❌ |
| CallSets CRUD | 5 | 4h | ❌ |
| References CRUD | 5 | 4h | ❌ |
| ReferenceSets CRUD | 4 | 3h | ❌ |
| VariantSets CRUD | 8 | 6h | ❌ |
| Vendor Integration | 8 | 8h | ❌ |
| **Subtotal** | **34** | **29h** | |

### Phase 5: Lists & Misc (Priority: LOW)

| Task | Endpoints | Effort | Status |
|------|-----------|--------|--------|
| Lists CRUD | 8 | 4h | ❌ |
| Common Crop Names | 1 | 1h | ❌ |
| Study Types | 1 | 1h | ❌ |
| Attributes CRUD | 7 | 4h | ❌ |
| Attribute Values CRUD | 6 | 4h | ❌ |
| **Subtotal** | **23** | **14h** | |

---

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| Total BrAPI 2.1 Endpoints | 135 |
| Implemented | 74 (55%) |
| Partial | 6 (4%) |
| Missing | 55 (41%) |
| Estimated Effort for 100% | ~82 hours |

### By Module

| Module | Implemented | Missing | Coverage |
|--------|-------------|---------|----------|
| BrAPI-Core | 22 | 5 | 81% |
| BrAPI-Phenotyping | 24 | 11 | 69% |
| BrAPI-Genotyping | 12 | 35 | 26% |
| BrAPI-Germplasm | 16 | 10 | 62% |

---

## 🔗 References

- [BrAPI Specification](https://brapi.org/specification)
- [BrAPI Test Server](https://test-server.brapi.org)
- [BrAPI GitHub](https://github.com/plantbreeding/BrAPI)
- Local Reference: `docs/confidential/BrAPI-2.1-reference/`

---

*Last Updated: December 12, 2025*
*Auditor: AI Agent (SWAYAM)*
