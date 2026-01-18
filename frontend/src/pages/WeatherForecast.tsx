/**
 * Weather Forecast Page
 * Extended weather forecast with field conditions - connected to real API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiClient } from '@/lib/api-client'
import {
  Cloud,
  Sun,
  CloudRain,
  Wind,
  Droplets,
  Thermometer,
  AlertTriangle,
  MapPin,
  Calendar,
  RefreshCw,
  CloudSun,
  AlertCircle,
  Snowflake,
  CloudFog,
  Flame
} from 'lucide-react'
import { ApiKeyNotice } from '@/components/ApiKeyNotice'

// Map weather conditions to icons
const getWeatherIcon = (condition: string, size: string = 'h-8 w-8') => {
  const icons: Record<string, React.ReactNode> = {
    clear: <Sun className={`${size} text-yellow-500`} />,
    cloudy: <Cloud className={`${size} text-gray-500`} />,
    rain: <CloudRain className={`${size} text-blue-500`} />,
    heavy_rain: <CloudRain className={`${size} text-blue-700`} />,
    storm: <CloudRain className={`${size} text-purple-500`} />,
    snow: <Snowflake className={`${size} text-blue-300`} />,
    fog: <CloudFog className={`${size} text-gray-400`} />,
    heat: <Flame className={`${size} text-orange-500`} />,
    frost: <Snowflake className={`${size} text-cyan-400`} />,
  }
  return icons[condition] || <CloudSun className={`${size} text-yellow-500`} />
}

export function WeatherForecast() {
  const [selectedLocation, setSelectedLocation] = useState('loc001')

  // Fetch locations
  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.getLocations(0, 50),
  })

  const locations = locationsData?.result?.data || []
  const selectedLocationData = locations.find((l: any) => l.locationDbId === selectedLocation)
  const locationName = selectedLocationData?.locationName || 'Research Station'

  // Fetch 14-day weather forecast
  const { data: forecast, isLoading, error, refetch } = useQuery({
    queryKey: ['weather-forecast-extended', selectedLocation],
    queryFn: () => apiClient.getWeatherForecast(selectedLocation, locationName, 14),
    enabled: !!selectedLocation,
  })

  const currentWeather = forecast?.daily_forecast?.[0]
  const weekForecast = forecast?.daily_forecast?.slice(0, 7) || []

  const formatDay = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'short' })
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Generate hourly forecast from daily data (simulated)
  const hourlyForecast = currentWeather ? [
    { time: '6 AM', temp: Math.round(currentWeather.temp_min), condition: currentWeather.condition },
    { time: '9 AM', temp: Math.round((currentWeather.temp_min + currentWeather.temp_avg) / 2), condition: currentWeather.condition },
    { time: '12 PM', temp: Math.round(currentWeather.temp_avg), condition: currentWeather.condition },
    { time: '3 PM', temp: Math.round(currentWeather.temp_max), condition: currentWeather.condition },
    { time: '6 PM', temp: Math.round((currentWeather.temp_max + currentWeather.temp_avg) / 2), condition: currentWeather.condition },
    { time: '9 PM', temp: Math.round(currentWeather.temp_avg), condition: 'cloudy' },
  ] : []

  // Field conditions based on weather
  const fieldConditions = forecast?.gdd_forecast ? [
    { 
      field: `${locationName} - Rice`, 
      soilMoisture: currentWeather?.soil_moisture ? Math.round(currentWeather.soil_moisture) : 65, 
      gdd: Math.round(forecast.gdd_forecast[forecast.gdd_forecast.length - 1]?.gdd_cumulative || 0), 
      lastRain: forecast.daily_forecast?.find((d: any) => d.precipitation > 5) ? 'Recent' : '3+ days ago',
      status: (currentWeather?.soil_moisture || 65) > 50 ? 'optimal' : 'needs-water'
    },
    { 
      field: `${locationName} - Wheat`, 
      soilMoisture: Math.max(40, (currentWeather?.soil_moisture || 60) - 10), 
      gdd: Math.round((forecast.gdd_forecast[forecast.gdd_forecast.length - 1]?.gdd_cumulative || 0) * 0.8), 
      lastRain: '4 days ago',
      status: 'optimal'
    },
  ] : []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Cloud className="h-8 w-8 text-primary" />
            Weather Forecast
          </h1>
          <p className="text-muted-foreground mt-1">Agricultural weather intelligence for field planning</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-[200px]">
              <MapPin className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Select location" />
            </SelectTrigger>
            <SelectContent>
              {locations.length > 0 ? (
                locations.map((loc: any) => (
                  <SelectItem key={loc.locationDbId} value={loc.locationDbId}>
                    {loc.locationName}
                  </SelectItem>
                ))
              ) : (
                <>
                  <SelectItem value="loc001">IRRI Research Station</SelectItem>
                  <SelectItem value="loc002">CIMMYT Field Station</SelectItem>
                  <SelectItem value="loc003">ICRISAT Campus</SelectItem>
                </>
              )}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" aria-label="Refresh weather data" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* API Key Notice */}
      <ApiKeyNotice serviceId="openweathermap" variant="inline" />

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load weather data. {error instanceof Error ? error.message : 'Please try again.'}
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Weather Alerts */}
      {forecast?.alerts && forecast.alerts.length > 0 && (
        <div className="space-y-2">
          {forecast.alerts.map((alert: string, index: number) => (
            <div key={index} className={`p-4 rounded-lg border flex items-start gap-3 ${
              alert.includes('CRITICAL') ? 'bg-red-50 border-red-200' :
              alert.includes('⚠️') ? 'bg-yellow-50 border-yellow-200' : 'bg-blue-50 border-blue-200'
            }`}>
              <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                alert.includes('CRITICAL') ? 'text-red-500' : 'text-yellow-500'
              }`} />
              <div className="flex-1">
                <div className="text-sm">{alert}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-64 lg:col-span-2" />
          </div>
          <Skeleton className="h-48" />
        </div>
      ) : forecast && currentWeather ? (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Current Weather */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Current Conditions</CardTitle>
                <CardDescription>{forecast.location_name}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-6">
                  {getWeatherIcon(currentWeather.condition, 'h-20 w-20 mx-auto')}
                  <div className="text-5xl font-bold mt-2">{Math.round(currentWeather.temp_avg)}°C</div>
                  <div className="text-muted-foreground">
                    Feels like {Math.round(currentWeather.temp_avg + (currentWeather.humidity > 70 ? 3 : 0))}°C
                  </div>
                  <div className="text-lg mt-1 capitalize">{currentWeather.condition.replace('_', ' ')}</div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Droplets className="h-4 w-4 text-blue-500" />
                    <span className="text-sm">Humidity: {Math.round(currentWeather.humidity)}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Wind className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">Wind: {Math.round(currentWeather.wind_speed)} km/h</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Thermometer className="h-4 w-4 text-red-500" />
                    <span className="text-sm">High: {Math.round(currentWeather.temp_max)}°C</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Sun className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm">UV: {currentWeather.uv_index?.toFixed(1) || '-'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Hourly Forecast */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Hourly Forecast</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between">
                  {hourlyForecast.map((hour, index) => (
                    <div key={index} className="text-center p-3">
                      <div className="text-sm text-muted-foreground">{hour.time}</div>
                      <div className="my-2">{getWeatherIcon(hour.condition, 'h-5 w-5')}</div>
                      <div className="font-medium">{hour.temp}°</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 7-Day Forecast */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                7-Day Forecast
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-7 gap-4">
                {weekForecast.map((day: any, index: number) => (
                  <div key={index} className={`text-center p-4 rounded-lg ${
                    index === 0 ? 'bg-primary/10 border-2 border-primary' : 'bg-muted/50'
                  }`}>
                    <div className="font-medium">{index === 0 ? 'Today' : formatDay(day.date)}</div>
                    <div className="text-xs text-muted-foreground">{formatDate(day.date)}</div>
                    <div className="my-3">{getWeatherIcon(day.condition)}</div>
                    <div className="text-sm capitalize">{day.condition.replace('_', ' ')}</div>
                    <div className="mt-2">
                      <span className="font-bold">{Math.round(day.temp_max)}°</span>
                      <span className="text-muted-foreground"> / {Math.round(day.temp_min)}°</span>
                    </div>
                    {day.precipitation > 0 && (
                      <div className="flex items-center justify-center gap-1 mt-2 text-xs text-blue-500">
                        <Droplets className="h-3 w-3" />
                        {Math.round(day.precipitation)}mm
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Activity Windows */}
          {forecast.optimal_windows && forecast.optimal_windows.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Optimal Activity Windows</CardTitle>
                <CardDescription>Best times for field operations based on weather</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {forecast.optimal_windows.map((window: any, index: number) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium capitalize">{window.activity}</span>
                        <Badge variant="secondary">{Math.round(window.confidence * 100)}%</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(window.start)} - {formatDate(window.end)}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Field Conditions */}
          {fieldConditions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Field Conditions</CardTitle>
                <CardDescription>Weather impact on field operations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {fieldConditions.map((field, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <div className="font-medium">{field.field}</div>
                        <div className="text-sm text-muted-foreground">Last rain: {field.lastRain}</div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <div className="text-sm text-muted-foreground">Soil Moisture</div>
                          <div className="font-bold">{field.soilMoisture}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-muted-foreground">GDD</div>
                          <div className="font-bold">{field.gdd}</div>
                        </div>
                        <Badge variant={field.status === 'optimal' ? 'default' : 'destructive'}>
                          {field.status === 'optimal' ? 'Optimal' : 'Needs Water'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Cloud className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Select a location to view weather forecast</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
