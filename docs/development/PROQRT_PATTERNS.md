# My ProQRT App Business Logic Reference

> **Purpose**: Reference documentation for ProQRT business logic patterns applicable to BijMantra
> **Last Updated**: January 7, 2026
> **Source**: Extracted from `proqrt-reference.bak`

---

## Overview

ProQRT is a seed traceability and inventory management system. This document captures business logic patterns that may be useful for BijMantra's commercial seed operations module.

---

## 1. Seed Packaging & Tracking (3-Tier Hierarchy)

### Package Hierarchy

| Level               | Term               | Description                        |
| ------------------- | ------------------ | ---------------------------------- |
| **Primary**   | `children`       | Individual seed packets            |
| **Secondary** | `parent`         | Boxes containing primary packets   |
| **Tertiary**  | `tertiaryParent` | Cartons containing secondary boxes |

### Serial Registry

Each package has a unique serial number with lifecycle states:

```
GENERATED → REGISTERED → ASSIGNED → DISPATCHED
                          ↓
                    (if recalled)
                          ↓
                      RECALLED → RECOVERED
```

### BijMantra Gap Analysis

| ProQRT Feature          | BijMantra Status         |
| ----------------------- | ------------------------ |
| 3-tier packaging        | ❌ Missing               |
| Serial ID / QR codes    | ❌ Missing               |
| Package status tracking | ❌ Missing               |
| Lot tracking            | ✅`Seedlot` model      |
| Transaction tracking    | ✅`SeedlotTransaction` |

---

## 2. Agricultural Production Hierarchy (Seed Tiers)

### Indian Seed Multiplication Chain

```
Breeder Seed (Nucleus) → Foundation Seed → Certified Seed
```

### Seed Lot Status Lifecycle

```
PLANNING → SOWING → GROWING → HARVESTING → PROCESSING → TESTING → APPROVED/REJECTED → CERTIFIED
```

### Key Fields for Seed Lots

| Field                      | Purpose                  |
| -------------------------- | ------------------------ |
| `production_season`      | KHARIF / RABI / SUMMER   |
| `parent_lot_id`          | Lineage tracking         |
| `sathi_registration_id`  | Government integration   |
| `multiplication_ratio`   | Foundation seed tracking |
| `field_inspection_count` | Quality assurance        |

### BijMantra Gap Analysis

| ProQRT Feature                     | BijMantra Status                       |
| ---------------------------------- | -------------------------------------- |
| Breeder/Foundation/Certified tiers | ⚠️ Partial (quality standards exist) |
| Parent lot lineage                 | ❌ Missing                             |
| Production season                  | ❌ Missing                             |
| Field inspections                  | ❌ Missing                             |
| SATHI integration                  | ❌ Missing                             |

---

## 3. Inventory & Stock Management (Immutable Ledger)

### ERPNext-Style Stock Ledger

**Key Principle**: Never update quantities directly. Always append ledger entries.

```python
class StockLedgerEntry:
    voucher_type: str  # 'Package Creation', 'Dispatch', 'Return'
    voucher_no: str
    item_code: str
    warehouse: str
    actual_qty: float  # +1 inbound, -1 outbound
    qty_after_transaction: float  # Running balance
    valuation_rate: float
    is_cancelled: bool
```

### Voucher Types

| Type                 | Direction | Description            |
| -------------------- | --------- | ---------------------- |
| Package Creation     | +1        | New package scanned    |
| Dispatch             | -1        | Sent to customer       |
| Material Return      | +1        | Returned from customer |
| Stock Reconciliation | ±N       | Manual adjustment      |

### BijMantra Gap Analysis

| ProQRT Feature     | BijMantra Status                           |
| ------------------ | ------------------------------------------ |
| Immutable ledger   | ❌**Critical Gap** (direct mutation) |
| Voucher types      | ⚠️ Partial                               |
| Running balance    | ❌ Missing                                 |
| Valuation tracking | ❌ Missing                                 |

---

## 4. Dispatch & Returns

### Dispatch Model

```python
class Dispatch:
    dc_number: str  # Delivery Challan
    dispatch_date: str
    receiving_firm_id: str
    items: List[DispatchedItem]
    transport_details: DcTransportDetails  # transporter, truck, driver
```

### BijMantra Status

| Feature              | Status                   |
| -------------------- | ------------------------ |
| Dispatch model       | ✅ Exists (in-memory)    |
| Firm/Dealer model    | ✅ Exists (in-memory)    |
| Transport details    | ⚠️ Partial             |
| Database persistence | ❌**Critical Gap** |

---

## 5. Recall & Early Warning System (EWS)

### Recall Model

```python
class Recall:
    recall_code: str
    status: Literal['draft', 'active', 'completed', 'canceled']
    severity: Literal['low', 'medium', 'high', 'critical']
    affected_lots: List[str]
    affected_packet_ids: List[str]
    total_affected_items: int
    recovered_count: int
```

### EWS Features

- Multi-channel notifications (email, SMS, app, call)
- Auto-notify by recipient type
- Acknowledgment tracking with timeout
- Escalation thresholds
- Geographic targeting

### BijMantra Gap Analysis

| ProQRT Feature              | BijMantra Status         |
| --------------------------- | ------------------------ |
| Recall model                | ❌ Missing               |
| Multi-channel notifications | ❌ Missing (in-app only) |
| Acknowledgment tracking     | ❌ Missing               |
| Basic notifications         | ✅`Notification` model |

---

## 6. Role-Based Access Control (RBAC)

### BijMantra Status: ✅ IMPLEMENTED

- 5 default roles: viewer, breeder, researcher, data_manager, admin
- 15 RBAC API endpoints
- Permission checking in protected routes

### Minor Gaps

- No "approve" permission level
- No Field Officer role
- No Platform Admin vs Company Admin distinction

---

## 7. Quality Control (Processing Batches)

### Processing Stages

```
Receiving → Pre-Cleaning → Drying → Cleaning → Grading → Treating → Packaging → Labeling → Storage → Completed
```

### Processing Batch Status

```
Pending → In Progress → Quality Control → Completed
```

### BijMantra Status

| Feature              | Status                |
| -------------------- | --------------------- |
| Processing stages    | ✅ Exists (in-memory) |
| Quality checks       | ✅ Exists             |
| Database persistence | ❌ Missing            |

---

## Integration Recommendations

### High Priority (Commercial Operations)

1. **Immutable Stock Ledger** — Foundation for accurate inventory
2. **Database Persistence** — Migrate dispatch/firm from in-memory to DB
3. **Recall System** — Regulatory compliance requirement

### Medium Priority

4. **3-Tier Packaging** — End-to-end traceability
5. **Seed Tier Lineage** — Breeder → Foundation → Certified tracking
6. **Field Inspections** — Quality assurance workflow

### Lower Priority

7. **SATHI Integration** — Government system (India-specific)
8. **Transport Details** — Logistics tracking
9. **EWS Multi-Channel** — SMS/email notifications

---

## Decision Log

| Feature          | Decision                 | Rationale                      |
| ---------------- | ------------------------ | ------------------------------ |
| RBAC             | Additional work required | Session 51-52                  |
| Dispatch model   | Migrate to DB            | In-memory not production-ready |
| Recall system    | Defer to v1.1            | Not critical for beta          |
| 3-tier packaging | Defer to v1.1            | Complex, needs design          |

---

*Document maintained for reference when building commercial seed operations features.*
