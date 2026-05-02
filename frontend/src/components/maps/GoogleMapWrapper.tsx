import { useCallback, useEffect, useRef, useState } from 'react';
import React from 'react';
import { Wrapper } from '@googlemaps/react-wrapper';
import { useDeepCompareEffect } from 'react-use';

interface MapProps extends google.maps.MapOptions {
  onClick?: (e: google.maps.MapMouseEvent) => void;
  onIdle?: (map: google.maps.Map) => void;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}

const MapComponent: React.FC<MapProps> = ({
  onClick,
  onIdle,
  children,
  style,
  ...options
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<google.maps.Map>();

  useEffect(() => {
    if (ref.current && !map) {
      setMap(new window.google.maps.Map(ref.current, {}));
    }
  }, [ref, map]);

  useDeepCompareEffect(() => {
    if (map) {
      map.setOptions(options);
    }
  }, [map, options]);

  useEffect(() => {
    if (map) {
      ['click', 'idle'].forEach((eventName) =>
        google.maps.event.clearListeners(map, eventName)
      );

      if (onClick) {
        map.addListener('click', onClick);
      }

      if (onIdle) {
        map.addListener('idle', () => onIdle(map));
      }
    }
  }, [map, onClick, onIdle]);

  return (
    <>
      <div ref={ref} style={style} />
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          // @ts-expect-error - Clone element with map prop
          return React.cloneElement(child, { map });
        }
      })}
    </>
  );
};

export interface GoogleMapWrapperProps {
  apiKey?: string;
  center?: google.maps.LatLngLiteral;
  zoom?: number;
  markers?: Array<{
    position: google.maps.LatLngLiteral;
    title?: string;
    onClick?: () => void;
  }>;
  polygons?: Array<{
    paths: google.maps.LatLngLiteral[];
    options?: google.maps.PolygonOptions;
  }>;
  height?: string;
  width?: string;
  className?: string;
}

export const GoogleMapWrapper: React.FC<GoogleMapWrapperProps> = ({
  apiKey = '',
  center = { lat: 0, lng: 0 },
  zoom = 2,
  markers = [],
  polygons = [],
  height = '400px',
  width = '100%',
  className = '',
}) => {
  const render = (status: Status) => {
    if (status === Status.FAILURE) return <div>Error loading map</div>;
    return <div>Loading map...</div>;
  };

  if (!apiKey) {
    return <div>Google Maps API Key not provided</div>;
  }

  return (
    <div className={className} style={{ height, width }}>
      <Wrapper apiKey={apiKey} render={render}>
        <MapComponent center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
          {markers.map((marker, i) => (
            <Marker key={i} {...marker} />
          ))}
          {polygons.map((polygon, i) => (
            <Polygon key={i} {...polygon} />
          ))}
        </MapComponent>
      </Wrapper>
    </div>
  );
};

const Marker: React.FC<google.maps.MarkerOptions & { onClick?: () => void }> = (options) => {
  const [marker, setMarker] = useState<google.maps.Marker>();

  useEffect(() => {
    if (!marker) {
      setMarker(new google.maps.Marker());
    }

    return () => {
      if (marker) {
        marker.setMap(null);
      }
    };
  }, [marker]);

  useEffect(() => {
    if (marker) {
      marker.setOptions(options);

      const listener = marker.addListener('click', () => {
        if (options.onClick) {
          options.onClick();
        }
      });

      return () => {
        google.maps.event.removeListener(listener);
      };
    }
  }, [marker, options]);

  return null;
};

const Polygon: React.FC<{
  paths: google.maps.LatLngLiteral[];
  options?: google.maps.PolygonOptions;
}> = ({ paths, options }) => {
  const [polygon, setPolygon] = useState<google.maps.Polygon>();

  useEffect(() => {
    if (!polygon) {
      setPolygon(new google.maps.Polygon());
    }

    return () => {
      if (polygon) {
        polygon.setMap(null);
      }
    };
  }, [polygon]);

  useDeepCompareEffect(() => {
    if (polygon) {
      polygon.setPaths(paths);
      polygon.setOptions(options || {});
    }
  }, [polygon, paths, options]);

  return null;
};

// Enum for Wrapper status since it's not exported
enum Status {
  LOADING = 'LOADING',
  FAILURE = 'FAILURE',
  SUCCESS = 'SUCCESS',
}
