# Weather Integration Service

## Overview

The Weather Integration Service provides real weather data for GDD (Growing Degree Days) calculations and agricultural intelligence. It implements BijMantra's Zero Mock Data Policy by fetching temperature data from external APIs with intelligent caching and fallback mechanisms.

## Features

- **Multi-Provider Support**: OpenWeatherMap (primary) and Visual Crossing (fallback)
- **Intelligent Caching**: Redis-based caching with appropriate TTLs
- **Rate Limiting**: Respects API quotas to avoid service limits
- **Data Quality Validation**: Outlier detection and quality scoring
- **Graceful Degradation**: Falls back to cached data when APIs unavailable
- **BijMantra API Contract Compliance**: Includes uncertainty metadata

## Quick Start

### 1. Configure API Keys

Add to your `.env` file:

```bash
# OpenWeatherMap (Primary)
OPENWEATHERMAP_API_KEY=your_key_here

# Visual Crossing (Fallback)
VISUALCROSSING_API_KEY=your_key_here
```

Get API keys:
- OpenWeatherMap: https://openweathermap.org/api (Free tier: 60 calls/min)
- Visual Crossing: https://www.visualcrossing.com/weather-api (Free tier: 1,000 calls/day)

### 2. Basic Usage

```python
from app.services.weather_integration_service import (
    weather_integration_service,
    WeatherDataRequest
)
from datetime import date

# Create request
request = WeatherDataRequest(
    location_id="FIELD-001",
    latitude=40.7128,
    longitude=-74.0060,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 7),
    include_forecast=False
)

# Get temperature data
response = await weather_integration_service.get_temperature_data(request)

# Access data
for temp_data in response.data:
    print(f"{temp_data.date}: {temp_data.temp_min}°C - {temp_data.temp_max}°C")
    print(f"  Quality: {temp_data.quality}, Confidence: {temp_data.confidence}")
```

## Integration with GDD Calculator

The weather integration service is designed to work seamlessly with the GDD calculator:

```python
from app.services.weather_integration_service import weather_integration_service
from app.services.gdd_calculator_service import gdd_calculator_service

# Fetch temperature data
weather_request = WeatherDataRequest(
    location_id="FIELD-001",
    latitude=40.7128,
    longitude=-74.0060,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 7)
)

weather_response = await weather_integration_service.get_temperature_data(
    weather_request
)

# Calculate GDD for each day
base_temp = 10.0  # Maize base temperature
cumulative_gdd = 0.0

for temp_data in weather_response.data:
    daily_gdd = gdd_calculator_service.calculate_daily_gdd(
        tmax=temp_data.temp_max,
        tmin=temp_data.temp_min,
        base_temp=base_temp
    )
    cumulative_gdd += daily_gdd
    
    print(f"{temp_data.date}: {daily_gdd:.1f} GDD (Total: {cumulative_gdd:.1f})")
```

## Data Models

### WeatherDataRequest

```python
WeatherDataRequest(
    location_id: str,           # Unique location identifier
    latitude: float,            # -90 to 90
    longitude: float,           # -180 to 180
    start_date: date,           # Start of date range
    end_date: date,             # End of date range
    include_forecast: bool      # Include future dates
)
```

### TemperatureData

```python
TemperatureData(
    date: date,                 # Date of observation
    temp_max: float,            # Maximum temperature (°C)
    temp_min: float,            # Minimum temperature (°C)
    temp_avg: Optional[float],  # Average temperature (°C)
    
    # Data quality metadata
    source: WeatherProvider,    # Data source
    quality: DataQuality,       # Quality level
    confidence: float,          # 0-1 confidence score
    
    # Validation flags
    is_forecast: bool,          # Is this forecast data?
    is_interpolated: bool,      # Was data interpolated?
    outlier_detected: bool,     # Outlier detected?
    
    # Additional context
    precipitation: Optional[float],  # mm
    humidity: Optional[float],       # percentage
    wind_speed: Optional[float]      # km/h
)
```

### WeatherDataResponse

```python
WeatherDataResponse(
    location_id: str,
    data: List[TemperatureData],
    
    # Response metadata
    provider_used: WeatherProvider,
    cache_hit_rate: float,      # 0-1
    data_completeness: float,   # 0-1
    quality_score: float,       # 0-1
    
    # BijMantra API contract
    confidence: Dict[str, Any],
    validity_conditions: List[str],
    provenance: Dict[str, Any]
)
```

## Caching Strategy

The service implements intelligent caching to minimize API calls:

| Data Type | Cache TTL | Rationale |
|-----------|-----------|-----------|
| Historical (>24h old) | 30 days | Stable, won't change |
| Recent (<24h old) | 6 hours | May be updated |
| Forecast | 1 hour | Frequently updated |

Cache keys format: `weather:{location_id}:{date}`

## Rate Limiting

Conservative rate limits to avoid API quota exhaustion:

| Provider | Limit | Actual API Limit |
|----------|-------|------------------|
| OpenWeatherMap | 60/hour | 60/minute (free tier) |
| Visual Crossing | 40/hour | 1,000/day (free tier) |

Rate limits are tracked in-memory and cleaned hourly.

## Data Quality Validation

The service validates temperature data for:

1. **Range Check**: -50°C to 60°C (reasonable global range)
2. **Consistency**: Tmax must be > Tmin
3. **Day-to-Day Variation**: <20°C change between consecutive days
4. **Climatological Norms**: (future enhancement)

Quality levels:
- **EXCELLENT**: Real-time API data, validated
- **GOOD**: Cached data <24h old
- **FAIR**: Cached data >24h or interpolated
- **POOR**: Significant data gaps or outliers
- **UNKNOWN**: Unable to validate

## Error Handling

The service implements graceful degradation:

1. **Primary API Fails**: Falls back to secondary API
2. **All APIs Fail**: Returns cached data if available
3. **No Cached Data**: Returns empty list with low quality score
4. **Redis Unavailable**: Uses in-memory cache (limited)

All errors are logged but don't raise exceptions to calling code.

## API Provider Details

### OpenWeatherMap

**Endpoints Used**:
- One Call API 3.0: `/data/3.0/onecall` (forecast)
- Historical API: Requires paid subscription

**Data Format**:
```json
{
  "daily": [
    {
      "dt": 1704067200,
      "temp": {"max": 15.5, "min": 5.2, "day": 10.3},
      "humidity": 65,
      "wind_speed": 5.5,
      "rain": 2.5
    }
  ]
}
```

### Visual Crossing

**Endpoints Used**:
- Timeline API: `/timeline/{lat},{lon}/{start}/{end}` (historical)
- Timeline API: `/timeline/{lat},{lon}/next{N}days` (forecast)

**Data Format**:
```json
{
  "days": [
    {
      "datetime": "2026-01-01",
      "tempmax": 15.5,
      "tempmin": 5.2,
      "temp": 10.3,
      "precip": 2.5,
      "humidity": 65
    }
  ]
}
```

## Testing

Run unit tests:

```bash
cd backend
source venv/bin/activate
python -m pytest tests/services/test_weather_integration_service.py -v
```

Test coverage:
- Cache management (hit/miss scenarios)
- Rate limiting enforcement
- Data quality validation
- API integration (mocked)
- Error handling and graceful degradation

## Performance Considerations

### Optimization Tips

1. **Batch Requests**: Request date ranges instead of individual days
2. **Cache Warming**: Pre-fetch data for known locations
3. **Async Operations**: Service is fully async-compatible
4. **Connection Pooling**: HTTP client reuses connections

### Expected Performance

- **Cache Hit**: <10ms response time
- **API Call**: 200-500ms response time
- **Batch Request (7 days)**: Single API call, ~300ms

## BijMantra API Contract Compliance

All responses include required metadata:

```python
{
    "confidence": {
        "type": "qualitative",
        "value": 0.85,
        "basis": "data_quality_validation"
    },
    "validity_conditions": [
        "temperature_data_within_climatological_norms",
        "data_completeness_85percent",
        "cache_hit_rate_60percent"
    ],
    "provenance": {
        "data_sources": ["openweathermap"],
        "models_used": ["weather_integration_v1.0"],
        "timestamp": "2026-01-17T10:30:00Z",
        "cached_records": 5,
        "fetched_records": 2
    }
}
```

## Future Enhancements

- [ ] Support for additional weather providers (NOAA, DarkSky)
- [ ] Climatological norm validation
- [ ] Spatial interpolation for locations without direct data
- [ ] Historical data storage in database
- [ ] Weather station integration for on-site measurements
- [ ] Ensemble forecasts with uncertainty quantification

## Troubleshooting

### No Data Returned

**Symptoms**: Empty data list, low quality score

**Causes**:
1. No API keys configured
2. Rate limit exceeded
3. Invalid coordinates
4. No cached data available

**Solutions**:
1. Add API keys to `.env`
2. Wait for rate limit reset (1 hour)
3. Verify latitude/longitude values
4. Check Redis connection

### Poor Data Quality

**Symptoms**: `quality_score < 0.5`, outliers detected

**Causes**:
1. API returning bad data
2. Extreme weather events
3. Data interpolation errors

**Solutions**:
1. Check API provider status
2. Verify against alternative source
3. Review validation thresholds

### Cache Not Working

**Symptoms**: `cache_hit_rate = 0`, slow responses

**Causes**:
1. Redis not running
2. Redis connection failed
3. Cache keys not matching

**Solutions**:
1. Start Redis: `make dev`
2. Check Redis connection in logs
3. Verify location_id consistency

## Support

For issues or questions:
- Check logs: `backend/logs/weather_integration.log`
- Review test cases: `backend/tests/services/test_weather_integration_service.py`
- Consult design doc: `.kiro/specs/gdd-module-integration/design.md`

## License

Part of BijMantra - Open Source Agricultural Intelligence Platform
