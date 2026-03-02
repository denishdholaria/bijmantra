# Weather Module

## Overview

The Weather Module provides functionality for managing weather stations, forecast data, historical weather records, climate zones, and alert subscriptions. It integrates with the `WeatherService` to provide weather intelligence for agricultural decision-making.

## Models

-   **WeatherStation**: Represents a physical or virtual weather station.
-   **ForecastData**: Stores weather forecast data linked to a station.
-   **HistoricalRecord**: Stores historical weather data for a station.
-   **ClimateZone**: Defines geographic climate zones.
-   **AlertSubscription**: User subscriptions for weather alerts based on location or station.

## API Endpoints

### Weather Stations

-   `GET /api/v2/weather/stations`: List weather stations.
-   `POST /api/v2/weather/stations`: Create a new weather station.
-   `GET /api/v2/weather/stations/{station_id}`: Get details of a weather station.
-   `PUT /api/v2/weather/stations/{station_id}`: Update a weather station.
-   `DELETE /api/v2/weather/stations/{station_id}`: Delete a weather station.

### Forecast Data

-   `GET /api/v2/weather/forecasts`: List forecast data.
-   `POST /api/v2/weather/forecasts`: Create forecast data.
-   `GET /api/v2/weather/forecasts/{forecast_id}`: Get details of forecast data.
-   `DELETE /api/v2/weather/forecasts/{forecast_id}`: Delete forecast data.

### Historical Records

-   `GET /api/v2/weather/historical`: List historical records.
-   `POST /api/v2/weather/historical`: Create a historical record.
-   `GET /api/v2/weather/historical/{record_id}`: Get details of a historical record.
-   `DELETE /api/v2/weather/historical/{record_id}`: Delete a historical record.

### Climate Zones

-   `GET /api/v2/weather/climate-zones`: List climate zones.
-   `POST /api/v2/weather/climate-zones`: Create a climate zone.
-   `GET /api/v2/weather/climate-zones/{zone_id}`: Get details of a climate zone.
-   `DELETE /api/v2/weather/climate-zones/{zone_id}`: Delete a climate zone.

### Alert Subscriptions

-   `GET /api/v2/weather/alerts/subscriptions`: List alert subscriptions.
-   `POST /api/v2/weather/alerts/subscriptions`: Create an alert subscription.
-   `GET /api/v2/weather/alerts/subscriptions/{subscription_id}`: Get details of an alert subscription.
-   `PUT /api/v2/weather/alerts/subscriptions/{subscription_id}`: Update an alert subscription.
-   `DELETE /api/v2/weather/alerts/subscriptions/{subscription_id}`: Delete an alert subscription.

## Usage

To use the weather module, ensure that the `WeatherService` is properly configured and that the database migrations have been applied. You can then interact with the API endpoints to manage weather data.
