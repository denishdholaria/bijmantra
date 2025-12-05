import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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
  CloudSun
} from 'lucide-react'

interface WeatherDay {
  date: string
  day: string
  high: number
  low: number
  condition: string
  precipitation: number
  humidity: number
  wind: number
  icon: React.ReactNode
}

interface WeatherAlert {
  type: 'warning' | 'watch' | 'advisory'
  title: string
  description: string
  validUntil: string
}

export function WeatherForecast() {
  const [selectedLocation, setSelectedLocation] = useState('field-a')
  const [_unit, _setUnit] = useState<'celsius' | 'fahrenheit'>('celsius')

  const currentWeather = {
    temperature: 28,
    feelsLike: 31,
    condition: 'Partly Cloudy',
    humidity: 65,
    wind: 12,
    pressure: 1013,
    uvIndex: 7,
    visibility: 10
  }

  const forecast: WeatherDay[] = [
    { date: 'Dec 2', day: 'Today', high: 28, low: 19, condition: 'Partly Cloudy', precipitation: 10, humidity: 65, wind: 12, icon: <CloudSun className="h-8 w-8 text-yellow-500" /> },
    { date: 'Dec 3', day: 'Wed', high: 30, low: 20, condition: 'Sunny', precipitation: 0, humidity: 55, wind: 8, icon: <Sun className="h-8 w-8 text-yellow-500" /> },
    { date: 'Dec 4', day: 'Thu', high: 27, low: 18, condition: 'Cloudy', precipitation: 30, humidity: 70, wind: 15, icon: <Cloud className="h-8 w-8 text-gray-500" /> },
    { date: 'Dec 5', day: 'Fri', high: 24, low: 17, condition: 'Rain', precipitation: 80, humidity: 85, wind: 20, icon: <CloudRain className="h-8 w-8 text-blue-500" /> },
    { date: 'Dec 6', day: 'Sat', high: 25, low: 16, condition: 'Showers', precipitation: 60, humidity: 75, wind: 18, icon: <CloudRain className="h-8 w-8 text-blue-400" /> },
    { date: 'Dec 7', day: 'Sun', high: 26, low: 17, condition: 'Partly Cloudy', precipitation: 20, humidity: 60, wind: 10, icon: <CloudSun className="h-8 w-8 text-yellow-500" /> },
    { date: 'Dec 8', day: 'Mon', high: 29, low: 19, condition: 'Sunny', precipitation: 5, humidity: 50, wind: 8, icon: <Sun className="h-8 w-8 text-yellow-500" /> }
  ]

  const alerts: WeatherAlert[] = [
    { type: 'warning', title: 'Heavy Rain Expected', description: 'Heavy rainfall expected on Friday. Consider delaying field operations.', validUntil: 'Dec 5, 6:00 PM' },
    { type: 'advisory', title: 'High UV Index', description: 'UV index will be high today. Ensure field workers have protection.', validUntil: 'Dec 2, 5:00 PM' }
  ]

  const hourlyForecast = [
    { time: '6 AM', temp: 19, icon: <CloudSun className="h-5 w-5" /> },
    { time: '9 AM', temp: 23, icon: <Sun className="h-5 w-5" /> },
    { time: '12 PM', temp: 27, icon: <Sun className="h-5 w-5" /> },
    { time: '3 PM', temp: 28, icon: <CloudSun className="h-5 w-5" /> },
    { time: '6 PM', temp: 25, icon: <Cloud className="h-5 w-5" /> },
    { time: '9 PM', temp: 22, icon: <Cloud className="h-5 w-5" /> }
  ]

  const fieldConditions = [
    { field: 'Field A - Rice', soilMoisture: 72, gdd: 1245, lastRain: '2 days ago', status: 'optimal' },
    { field: 'Field B - Wheat', soilMoisture: 58, gdd: 890, lastRain: '4 days ago', status: 'needs-water' },
    { field: 'Field C - Maize', soilMoisture: 65, gdd: 1120, lastRain: '3 days ago', status: 'optimal' }
  ]

  return (
    <div className="space-y-6">
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
            <SelectTrigger className="w-[180px]">
              <MapPin className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Select location" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="field-a">Field A - Main Station</SelectItem>
              <SelectItem value="field-b">Field B - North Block</SelectItem>
              <SelectItem value="field-c">Field C - South Block</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon"><RefreshCw className="h-4 w-4" /></Button>
        </div>
      </div>

      {/* Weather Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, index) => (
            <div key={index} className={`p-4 rounded-lg border flex items-start gap-3 ${
              alert.type === 'warning' ? 'bg-red-50 border-red-200' :
              alert.type === 'watch' ? 'bg-yellow-50 border-yellow-200' : 'bg-blue-50 border-blue-200'
            }`}>
              <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                alert.type === 'warning' ? 'text-red-500' : alert.type === 'watch' ? 'text-yellow-500' : 'text-blue-500'
              }`} />
              <div className="flex-1">
                <div className="font-medium">{alert.title}</div>
                <div className="text-sm text-muted-foreground">{alert.description}</div>
                <div className="text-xs text-muted-foreground mt-1">Valid until: {alert.validUntil}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Current Weather */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Current Conditions</CardTitle>
            <CardDescription>Main Research Station</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center mb-6">
              <CloudSun className="h-20 w-20 mx-auto text-yellow-500 mb-2" />
              <div className="text-5xl font-bold">{currentWeather.temperature}°C</div>
              <div className="text-muted-foreground">Feels like {currentWeather.feelsLike}°C</div>
              <div className="text-lg mt-1">{currentWeather.condition}</div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2"><Droplets className="h-4 w-4 text-blue-500" /><span className="text-sm">Humidity: {currentWeather.humidity}%</span></div>
              <div className="flex items-center gap-2"><Wind className="h-4 w-4 text-gray-500" /><span className="text-sm">Wind: {currentWeather.wind} km/h</span></div>
              <div className="flex items-center gap-2"><Thermometer className="h-4 w-4 text-red-500" /><span className="text-sm">Pressure: {currentWeather.pressure} hPa</span></div>
              <div className="flex items-center gap-2"><Sun className="h-4 w-4 text-yellow-500" /><span className="text-sm">UV Index: {currentWeather.uvIndex}</span></div>
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
                  <div className="my-2">{hour.icon}</div>
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
          <CardTitle className="flex items-center gap-2"><Calendar className="h-5 w-5" />7-Day Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-4">
            {forecast.map((day, index) => (
              <div key={index} className={`text-center p-4 rounded-lg ${index === 0 ? 'bg-primary/10 border-2 border-primary' : 'bg-muted/50'}`}>
                <div className="font-medium">{day.day}</div>
                <div className="text-xs text-muted-foreground">{day.date}</div>
                <div className="my-3">{day.icon}</div>
                <div className="text-sm">{day.condition}</div>
                <div className="mt-2">
                  <span className="font-bold">{day.high}°</span>
                  <span className="text-muted-foreground"> / {day.low}°</span>
                </div>
                <div className="flex items-center justify-center gap-1 mt-2 text-xs text-blue-500">
                  <Droplets className="h-3 w-3" />{day.precipitation}%
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Field Conditions */}
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
    </div>
  )
}
