/**
 * Weather Page
 * Weather data for field locations
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface WeatherData {
  locationDbId: string
  locationName: string
  current: {
    temperature: number
    humidity: number
    windSpeed: number
    condition: string
    icon: string
  }
  forecast: Array<{
    date: string
    high: number
    low: number
    condition: string
    icon: string
    precipitation: number
  }>
}

const mockWeatherData: WeatherData[] = [
  {
    locationDbId: 'loc001',
    locationName: 'IRRI Research Station',
    current: { temperature: 32, humidity: 78, windSpeed: 12, condition: 'Partly Cloudy', icon: '⛅' },
    forecast: [
      { date: '2024-02-21', high: 33, low: 25, condition: 'Sunny', icon: '☀️', precipitation: 0 },
      { date: '2024-02-22', high: 32, low: 24, condition: 'Cloudy', icon: '☁️', precipitation: 20 },
      { date: '2024-02-23', high: 30, low: 23, condition: 'Rain', icon: '🌧️', precipitation: 80 },
      { date: '2024-02-24', high: 31, low: 24, condition: 'Partly Cloudy', icon: '⛅', precipitation: 30 },
      { date: '2024-02-25', high: 33, low: 25, condition: 'Sunny', icon: '☀️', precipitation: 10 },
    ],
  },
  {
    locationDbId: 'loc002',
    locationName: 'CIMMYT Field Station',
    current: { temperature: 18, humidity: 45, windSpeed: 20, condition: 'Sunny', icon: '☀️' },
    forecast: [
      { date: '2024-02-21', high: 20, low: 8, condition: 'Sunny', icon: '☀️', precipitation: 0 },
      { date: '2024-02-22', high: 19, low: 7, condition: 'Sunny', icon: '☀️', precipitation: 0 },
      { date: '2024-02-23', high: 17, low: 6, condition: 'Cloudy', icon: '☁️', precipitation: 10 },
      { date: '2024-02-24', high: 16, low: 5, condition: 'Rain', icon: '🌧️', precipitation: 60 },
      { date: '2024-02-25', high: 18, low: 7, condition: 'Partly Cloudy', icon: '⛅', precipitation: 20 },
    ],
  },
]

export function Weather() {
  const [selectedLocation, setSelectedLocation] = useState<string>(mockWeatherData[0].locationDbId)

  const { data, isLoading } = useQuery({
    queryKey: ['weather', selectedLocation],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 500))
      return mockWeatherData.find(w => w.locationDbId === selectedLocation)
    },
  })

  const weather = data

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Weather</h1>
          <p className="text-muted-foreground mt-1">Weather conditions at field locations</p>
        </div>
        <Select value={selectedLocation} onValueChange={setSelectedLocation}>
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="Select location" />
          </SelectTrigger>
          <SelectContent>
            {mockWeatherData.map(w => (
              <SelectItem key={w.locationDbId} value={w.locationDbId}>{w.locationName}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : weather ? (
        <>
          {/* Current Weather */}
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{weather.locationName}</h2>
                  <p className="text-blue-100">{weather.current.condition}</p>
                </div>
                <div className="text-6xl">{weather.current.icon}</div>
              </div>
              <div className="mt-6 flex items-end gap-8">
                <div>
                  <span className="text-6xl font-bold">{weather.current.temperature}</span>
                  <span className="text-2xl">°C</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-blue-200">Humidity</p>
                    <p className="font-semibold">{weather.current.humidity}%</p>
                  </div>
                  <div>
                    <p className="text-blue-200">Wind</p>
                    <p className="font-semibold">{weather.current.windSpeed} km/h</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 5-Day Forecast */}
          <Card>
            <CardHeader>
              <CardTitle>5-Day Forecast</CardTitle>
              <CardDescription>Weather outlook for the next 5 days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4">
                {weather.forecast.map((day, index) => (
                  <div key={index} className="text-center p-4 bg-muted rounded-lg">
                    <p className="text-sm font-medium">{formatDate(day.date)}</p>
                    <div className="text-4xl my-3">{day.icon}</div>
                    <p className="text-sm text-muted-foreground">{day.condition}</p>
                    <div className="mt-2">
                      <span className="font-semibold">{day.high}°</span>
                      <span className="text-muted-foreground"> / {day.low}°</span>
                    </div>
                    <div className="mt-2 flex items-center justify-center gap-1 text-xs text-blue-600">
                      <span>💧</span>
                      <span>{day.precipitation}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Weather Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Weather Alerts</CardTitle>
              <CardDescription>Important weather notifications</CardDescription>
            </CardHeader>
            <CardContent>
              {weather.forecast.some(d => d.precipitation > 50) ? (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">⚠️</span>
                    <div>
                      <p className="font-semibold text-yellow-800">Rain Expected</p>
                      <p className="text-sm text-yellow-700">
                        High chance of rain on {formatDate(weather.forecast.find(d => d.precipitation > 50)?.date || '')}. 
                        Consider adjusting field activities.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">✅</span>
                    <div>
                      <p className="font-semibold text-green-800">Good Conditions</p>
                      <p className="text-sm text-green-700">
                        Weather conditions are favorable for field activities.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No weather data available</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
