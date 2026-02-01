// @ts-nocheck
import { APIProvider, Map, MapProps } from '@vis.gl/react-google-maps';

interface GoogleMapWrapperProps extends MapProps {
  apiKey?: string;
  height?: string;
  width?: string;
  children?: React.ReactNode;
}

const DEFAULT_CENTER = { lat: 20.5937, lng: 78.9629 }; // India
const DEFAULT_ZOOM = 5;

// Dark mode styles
const DARK_MAP_ID = 'e7ae5d978a3a9a7a'; // Example public dark map ID or use styles
const DARK_STYLES = [
  { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
  {
    featureType: "administrative.locality",
    elementType: "labels.text.fill",
    stylers: [{ color: "#d59563" }],
  },
  {
    featureType: "poi",
    elementType: "labels.text.fill",
    stylers: [{ color: "#d59563" }],
  },
  {
    featureType: "poi.park",
    elementType: "geometry",
    stylers: [{ color: "#263c3f" }],
  },
  {
    featureType: "poi.park",
    elementType: "labels.text.fill",
    stylers: [{ color: "#6b9a76" }],
  },
  {
    featureType: "road",
    elementType: "geometry",
    stylers: [{ color: "#38414e" }],
  },
  {
    featureType: "road",
    elementType: "geometry.stroke",
    stylers: [{ color: "#212a37" }],
  },
  {
    featureType: "road",
    elementType: "labels.text.fill",
    stylers: [{ color: "#9ca5b3" }],
  },
  {
    featureType: "road.highway",
    elementType: "geometry",
    stylers: [{ color: "#746855" }],
  },
  {
    featureType: "road.highway",
    elementType: "geometry.stroke",
    stylers: [{ color: "#1f2835" }],
  },
  {
    featureType: "road.highway",
    elementType: "labels.text.fill",
    stylers: [{ color: "#f3d19c" }],
  },
  {
    featureType: "water",
    elementType: "geometry",
    stylers: [{ color: "#17263c" }],
  },
  {
    featureType: "water",
    elementType: "labels.text.fill",
    stylers: [{ color: "#515c6d" }],
  },
  {
    featureType: "water",
    elementType: "labels.text.stroke",
    stylers: [{ color: "#17263c" }],
  },
];

export function GoogleMapWrapper({ 
  apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || 'YOUR_API_KEY', // Fallback or env
  height = '500px', 
  width = '100%', 
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  children,
  ...props 
}: GoogleMapWrapperProps) {
  return (
    <div style={{ height, width }} className="rounded-xl overflow-hidden shadow-lg border border-slate-700">
      <APIProvider apiKey={apiKey}>
        {/* @ts-ignore */}
        <Map
          defaultCenter={center}
          defaultZoom={zoom}
          gestureHandling={'greedy'}
          disableDefaultUI={false}
          styles={DARK_STYLES}
          // @ts-ignore
          {...props}
        >
            {children}
        </Map>
      </APIProvider>
    </div>
  );
}
