/**
 * Location Map Component
 * Interactive map for displaying field locations
 * Uses placeholder for Leaflet integration
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface Location {
  locationDbId: string
  locationName: string
  locationType?: string
  coordinates?: {
    latitude: number
    longitude: number
  }
  countryCode?: string
  countryName?: string
}

interface LocationMapProps {
  locations: Location[]
  selectedLocation?: string
  onLocationSelect?: (locationDbId: string) => void
  height?: string
}

export function LocationMap({ 
  locations, 
  selectedLocation, 
  onLocationSelect,
  height = '400px' 
}: LocationMapProps) {
  // Calculate map bounds
  const validLocations = locations.filter(l => l.coordinates?.latitude && l.coordinates?.longitude)
  
  const centerLat = validLocations.length > 0 
    ? validLocations.reduce((sum, l) => sum + (l.coordinates?.latitude || 0), 0) / validLocations.length
    : 0
  const centerLng = validLocations.length > 0
    ? validLocations.reduce((sum, l) => sum + (l.coordinates?.longitude || 0), 0) / validLocations.length
    : 0

  const openInMaps = (lat: number, lng: number) => {
    window.open(`https://www.google.com/maps?q=${lat},${lng}`, '_blank')
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>📍 Location Map</span>
          <Badge variant="outline">{validLocations.length} locations</Badge>
        </CardTitle>
        <CardDescription>
          Field locations with coordinates
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Map Placeholder - Replace with Leaflet when ready */}
        <div 
          className="relative bg-gradient-to-br from-blue-100 to-green-100 rounded-lg overflow-hidden"
          style={{ height }}
        >
          {/* Grid overlay to simulate map */}
          <div className="absolute inset-0 opacity-20">
            <svg width="100%" height="100%">
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>
          </div>

          {/* Location markers */}
          <div className="absolute inset-0 p-4">
            {validLocations.length === 0 ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <p className="text-4xl mb-2">🗺️</p>
                  <p>No locations with coordinates</p>
                </div>
              </div>
            ) : (
              <div className="relative h-full">
                {/* Simulated markers positioned based on coordinates */}
                {validLocations.map((location, index) => {
                  // Simple positioning based on index for demo
                  const x = 10 + (index % 4) * 22
                  const y = 10 + Math.floor(index / 4) * 25
                  const isSelected = selectedLocation === location.locationDbId
                  
                  return (
                    <button
                      key={location.locationDbId}
                      onClick={() => onLocationSelect?.(location.locationDbId)}
                      className={`absolute transform -translate-x-1/2 -translate-y-full transition-all ${
                        isSelected ? 'scale-125 z-10' : 'hover:scale-110'
                      }`}
                      style={{ left: `${x}%`, top: `${y}%` }}
                      title={location.locationName}
                    >
                      <div className={`text-3xl drop-shadow-lg ${isSelected ? 'animate-bounce' : ''}`}>
                        📍
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Map controls placeholder */}
          <div className="absolute top-2 right-2 flex flex-col gap-1">
            <Button size="sm" variant="secondary" className="w-8 h-8 p-0">+</Button>
            <Button size="sm" variant="secondary" className="w-8 h-8 p-0">−</Button>
          </div>

          {/* Center coordinates */}
          {validLocations.length > 0 && (
            <div className="absolute bottom-2 left-2 bg-white/90 px-2 py-1 rounded text-xs">
              Center: {centerLat.toFixed(4)}, {centerLng.toFixed(4)}
            </div>
          )}
        </div>

        {/* Location list */}
        {validLocations.length > 0 && (
          <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
            {validLocations.map((location) => (
              <div
                key={location.locationDbId}
                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                  selectedLocation === location.locationDbId
                    ? 'bg-primary/10 border border-primary'
                    : 'bg-muted/50 hover:bg-muted'
                }`}
                onClick={() => onLocationSelect?.(location.locationDbId)}
              >
                <div>
                  <p className="font-medium text-sm">{location.locationName}</p>
                  <p className="text-xs text-muted-foreground">
                    {location.coordinates?.latitude.toFixed(4)}, {location.coordinates?.longitude.toFixed(4)}
                    {location.countryCode && ` • ${location.countryCode}`}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (location.coordinates) {
                      openInMaps(location.coordinates.latitude, location.coordinates.longitude)
                    }
                  }}
                >
                  🗺️
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
