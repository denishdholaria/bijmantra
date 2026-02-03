"""
Future Module CRUD Operations

CRUD operations for planned BijMantra modules (Tier 1-3).
All CRUD classes inherit from CRUDBase and support:
- Async database operations
- Multi-tenant filtering via organization_id
- Pagination with total count
"""

from . import crop_calendar
from . import gdd
from . import crop_suitability
from . import yield_prediction
from . import soil_test
from . import fertilizer_recommendation
from . import soil_health
from . import carbon_sequestration
from . import pest_observation
from . import disease_risk_forecast
from . import spray_application
from . import ipm_strategy
from . import irrigation_schedule
from . import water_balance
from . import soil_moisture
