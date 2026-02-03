/**
 * Weather Page
 * Weather intelligence for field locations - connected to real API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiClient } from '@/lib/api-client'
import { AlertCircle, Cloud, Droplets, Wind, Sun, Thermometer, Calendar, Activity, RefreshCw } from 'lucide-react'
import { ApiKeyNotice } from '@/components/ApiKeyNotice'

// Weather condition icons
const conditionIcons: Record<string, string> = {
  clear: '☀️',
  cloudy: '☁️',
  rain: '🌧️',
  heavy_rain: '⛈️',
  storm: '🌩️',
  snow: '❄️',
  fog: '🌫️',
  heat: '🔥',
  frost: '🥶',
}

// Severity colors
const severityColors: Record<string, string> = {
  none: 'bg-gray-100 text-gray-800',
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

export function Weather() {
  const [selectedLocation, setSelectedLocation] = useState<string>('loc001')
  const [forecastDays, setForecastDays] = useState<number>(7)

  // Fetch locations from BrAPI
  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.locationService.getLocations(0, 50),
  })

  const locations = locationsData?.result?.data || []

  // Get location name for selected location
  const selectedLocationData = locations.find((l: any) => l.locationDbId === selectedLocation)
  const locationName = selectedLocationData?.locationName || 'Research Station'

  // Fetch weather forecast from real API
  const { data: forecast, isLoading, error, refetch } = useQuery({
    queryKey: ['weather-forecast', selectedLocation, forecastDays],
    queryFn: () => apiClient.weatherService.getWeatherForecast(selectedLocation, locationName, forecastDays),
    enabled: !!selectedLocation,
  })

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  const formatShortDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'short' })
  }

  // Get current day data (first day of forecast)
  const currentWeather = forecast?.daily_forecast?.[0]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Weather Intelligence</h1>
          <p className="text-muted-foreground mt-1">Agricultural weather analysis for breeding activities</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-[200px]">
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
          <Select value={String(forecastDays)} onValueChange={(v) => setForecastDays(Number(v))}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="14">14 Days</SelectItem>
            </SelectContent>
          </Select>
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

      {isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : forecast ? (
        <>
          {/* Current Weather Card */}
          {currentWeather && (
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">{forecast.location_name}</h2>
                    <p className="text-blue-100 capitalize">{currentWeather.condition.replace('_', ' ')}</p>
                  </div>
                  <div className="text-6xl">
                    {conditionIcons[currentWeather.condition] || '🌤️'}
                  </div>
                </div>
                <div className="mt-6 flex items-end gap-8">
                  <div>
                    <span className="text-6xl font-bold">{Math.round(currentWeather.temp_avg)}</span>
                    <span className="text-2xl">°C</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Thermometer className="h-4 w-4 text-blue-200" />
                      <div>
                        <p className="text-blue-200">High/Low</p>
                        <p className="font-semibold">{Math.round(currentWeather.temp_max)}° / {Math.round(currentWeather.temp_min)}°</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Droplets className="h-4 w-4 text-blue-200" />
                      <div>
                        <p className="text-blue-200">Humidity</p>
                        <p className="font-semibold">{Math.round(currentWeather.humidity)}%</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Wind className="h-4 w-4 text-blue-200" />
                      <div>
                        <p className="text-blue-200">Wind</p>
                        <p className="font-semibold">{Math.round(currentWeather.wind_speed)} km/h</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4 text-blue-200" />
                      <div>
                        <p className="text-blue-200">UV Index</p>
                        <p className="font-semibold">{currentWeather.uv_index?.toFixed(1) || '-'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Weather Alerts */}
          {forecast.alerts && forecast.alerts.length > 0 && (
            <Card className="border-orange-200 bg-orange-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-orange-800 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Weather Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {forecast.alerts.map((alert, i) => (
                    <p key={i} className="text-orange-700">{alert}</p>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Tabs defaultValue="forecast" className="space-y-4">
            <TabsList>
              <TabsTrigger value="forecast" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Forecast
              </TabsTrigger>
              <TabsTrigger value="impacts" className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Impacts
              </TabsTrigger>
              <TabsTrigger value="activities" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Activity Windows
              </TabsTrigger>
              <TabsTrigger value="gdd" className="flex items-center gap-2">
                <Thermometer className="h-4 w-4" />
                GDD
              </TabsTrigger>
            </TabsList>

            {/* Forecast Tab */}
            <TabsContent value="forecast">
              <Card>
                <CardHeader>
                  <CardTitle>{forecastDays}-Day Forecast</CardTitle>
                  <CardDescription>Weather outlook for {forecast.location_name}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3">
                    {forecast.daily_forecast?.slice(0, forecastDays).map((day, index) => (
                      <div key={index} className="text-center p-3 bg-muted rounded-lg">
                        <p className="text-sm font-medium">{formatShortDate(day.date)}</p>
                        <div className="text-3xl my-2">
                          {conditionIcons[day.condition] || '🌤️'}
                        </div>
                        <p className="text-xs text-muted-foreground capitalize">
                          {day.condition.replace('_', ' ')}
                        </p>
                        <div className="mt-2">
                          <span className="font-semibold">{Math.round(day.temp_max)}°</span>
                          <span className="text-muted-foreground"> / {Math.round(day.temp_min)}°</span>
                        </div>
                        {day.precipitation > 0 && (
                          <div className="mt-1 flex items-center justify-center gap-1 text-xs text-blue-600">
                            <Droplets className="h-3 w-3" />
                            <span>{Math.round(day.precipitation)}mm</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Impacts Tab */}
            <TabsContent value="impacts">
              <Card>
                <CardHeader>
                  <CardTitle>Weather Impacts</CardTitle>
                  <CardDescription>Potential impacts on breeding activities</CardDescription>
                </CardHeader>
                <CardContent>
                  {forecast.impacts && forecast.impacts.length > 0 ? (
                    <div className="space-y-4">
                      {forecast.impacts.map((impact, i) => (
                        <div key={i} className="p-4 border rounded-lg">
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="font-semibold">{impact.event}</h4>
                                <Badge className={severityColors[impact.severity]}>
                                  {impact.severity}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">
                                {formatDate(impact.date)} • {Math.round(impact.probability * 100)}% probability
                              </p>
                            </div>
                          </div>
                          <p className="mt-2 text-sm">{impact.recommendation}</p>
                          {impact.details && (
                            <p className="mt-1 text-xs text-muted-foreground">{impact.details}</p>
                          )}
                          <div className="mt-2 flex flex-wrap gap-1">
                            {impact.affected_activities.map((activity, j) => (
                              <Badge key={j} variant="outline" className="text-xs">
                                {activity}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center">
                      <div className="text-4xl mb-2">✅</div>
                      <p className="text-muted-foreground">No significant weather impacts expected</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Activity Windows Tab */}
            <TabsContent value="activities">
              <Card>
                <CardHeader>
                  <CardTitle>Optimal Activity Windows</CardTitle>
                  <CardDescription>Best times for field activities based on weather</CardDescription>
                </CardHeader>
                <CardContent>
                  {forecast.optimal_windows && forecast.optimal_windows.length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2">
                      {forecast.optimal_windows.map((window, i) => (
                        <div key={i} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between">
                            <h4 className="font-semibold capitalize">{window.activity}</h4>
                            <Badge variant="secondary">
                              {Math.round(window.confidence * 100)}% confidence
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-2">
                            {formatDate(window.start)} - {formatDate(window.end)}
                          </p>
                          <p className="text-sm mt-1">{window.conditions}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center">
                      <p className="text-muted-foreground">No optimal windows identified</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* GDD Tab */}
            <TabsContent value="gdd">
              <Card>
                <CardHeader>
                  <CardTitle>Growing Degree Days (GDD)</CardTitle>
                  <CardDescription>Accumulated heat units for crop development</CardDescription>
                </CardHeader>
                <CardContent>
                  {forecast.gdd_forecast && forecast.gdd_forecast.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2 px-3">Date</th>
                            <th className="text-right py-2 px-3">Daily GDD</th>
                            <th className="text-right py-2 px-3">Cumulative</th>
                            <th className="text-left py-2 px-3">Crop</th>
                          </tr>
                        </thead>
                        <tbody>
                          {forecast.gdd_forecast.slice(0, 14).map((gdd, i) => (
                            <tr key={i} className="border-b hover:bg-muted/50">
                              <td className="py-2 px-3">{formatDate(gdd.date)}</td>
                              <td className="text-right py-2 px-3 font-mono">
                                {gdd.gdd_daily.toFixed(1)}
                              </td>
                              <td className="text-right py-2 px-3 font-mono font-semibold">
                                {gdd.gdd_cumulative.toFixed(1)}
                              </td>
                              <td className="py-2 px-3 capitalize">{gdd.crop}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <p className="text-xs text-muted-foreground mt-4">
                        Base temperature: {forecast.gdd_forecast[0]?.base_temp}°C
                      </p>
                    </div>
                  ) : (
                    <div className="p-8 text-center">
                      <p className="text-muted-foreground">No GDD data available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Cloud className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Select a location to view weather data</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
