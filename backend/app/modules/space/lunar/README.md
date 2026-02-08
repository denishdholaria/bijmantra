# LUNAR Module — Low-Gravity, Vacuum-Proximal Agriculture Engine

**Codename:** LUNAR
**Status:** CALF-3 Target

## Purpose
The LUNAR module evaluates plant germplasm performance under **low-gravity, vacuum-proximal, cyclic-light environments** inspired by lunar surface and subsurface habitats.

It models:
- Fractional gravity (0.16g) effects on root anchorage and morphology.
- Photoperiod extremes (14 days light / 14 days dark).
- Habitat pressure and atmospheric composition effects.

## Core Components

### Fractional Gravity Environment Engine (FGEE)
Implemented in `gravity_model.py`, this engine deterministically simulates biological stress responses to:
- **Gravity**: Less than Earth normal (1g).
- **Photoperiod**: Extended light/dark cycles causing circadian disruption.
- **Root Support**: Effect of regolith simulants or hydroponic matrices.

### Data Models
- **LunarEnvironmentProfile**: Defines the physical conditions (gravity, light cycle, pressure, O2/CO2).
- **LunarTrial**: Records the outcome of a germplasm genotype in a specific profile.

### Failure Modes
- `ROOT_DISORIENTATION`: Gravity too low for gravitropism.
- `ANCHORAGE_FAILURE`: Roots cannot hold plant upright.
- `PHOTOPERIOD_COLLAPSE`: Circadian rhythm disruption.
- `TRANSLOCATION_IMPAIRMENT`: Fluid dynamics failure.
- `MORPHOGENETIC_INSTABILITY`: Structural defects.

## API Usage

### Create Environment
`POST /api/v2/lunar/environments`

### Run Simulation
`POST /api/v2/lunar/simulate`

### Record Trial
`POST /api/v2/lunar/trials`

## Constraints
- **Gravity Physics**: Modeled deterministically, no heuristics.
- **Isolation**: Does not depend on MARS module.
- **Tenancy**: All data scoped by Organization ID.

## Verification
- Module tests passed locally (`backend/app/modules/lunar/tests/`).
- Application startup verified with new router integration.
