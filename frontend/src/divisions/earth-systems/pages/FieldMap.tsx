/**
 * Field Map Page
 *
 * Interactive GIS map for field visualization and management.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Field {
  id: string;
  name: string;
  area: number;
  crop: string;
  status: 'planted' | 'growing' | 'harvest-ready' | 'fallow';
}

export function FieldMap() {
  const [selectedField, setSelectedField] = useState<Field | null>(null);

  const fields: Field[] = [
    { id: 'F001', name: 'North Block A', area: 12.5, crop: 'Wheat', status: 'growing' },
    { id: 'F002', name: 'North Block B', area: 8.3, crop: 'Rice', status: 'harvest-ready' },
    { id: 'F003', name: 'South Block', area: 15.0, crop: 'Maize', status: 'planted' },
    { id: 'F004', name: 'East Field', area: 6.2, crop: 'Soybean', status: 'growing' },
    { id: 'F005', name: 'Trial Plots', area: 2.0, crop: 'Various', status: 'growing' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planted': return 'bg-blue-100 text-blue-800';
      case 'growing': return 'bg-green-100 text-green-800';
      case 'harvest-ready': return 'bg-yellow-100 text-yellow-800';
      case 'fallow': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Field Map</h1>
          <p className="text-gray-600 mt-1">Interactive field visualization and management</p>
        </div>
        <Button>➕ Add Field</Button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Map Area */}
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>🗺️ Field Overview</CardTitle></CardHeader>
          <CardContent>
            <div className="h-96 bg-gradient-to-br from-green-100 to-green-200 rounded-lg flex items-center justify-center relative">
              <p className="text-gray-500">Interactive map with Leaflet would render here</p>
              {/* Placeholder field indicators */}
              <div className="absolute top-4 left-4 w-20 h-16 bg-green-400 rounded opacity-70 cursor-pointer" onClick={() => setSelectedField(fields[0])} />
              <div className="absolute top-4 right-8 w-16 h-12 bg-yellow-400 rounded opacity-70 cursor-pointer" onClick={() => setSelectedField(fields[1])} />
              <div className="absolute bottom-8 left-8 w-24 h-20 bg-blue-400 rounded opacity-70 cursor-pointer" onClick={() => setSelectedField(fields[2])} />
            </div>
          </CardContent>
        </Card>

        {/* Field List */}
        <Card>
          <CardHeader><CardTitle>Fields</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {fields.map((field) => (
                <div
                  key={field.id}
                  className={`p-3 cursor-pointer hover:bg-gray-50 ${selectedField?.id === field.id ? 'bg-green-50' : ''}`}
                  onClick={() => setSelectedField(field)}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{field.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(field.status)}`}>
                      {field.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {field.crop} • {field.area} ha
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Selected Field Details */}
      {selectedField && (
        <Card>
          <CardHeader><CardTitle>📍 {selectedField.name}</CardTitle></CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-2xl font-bold">{selectedField.area}</div>
                <div className="text-sm text-gray-500">Hectares</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-2xl font-bold">{selectedField.crop}</div>
                <div className="text-sm text-gray-500">Current Crop</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className={`text-lg font-bold px-2 py-1 rounded ${getStatusColor(selectedField.status)}`}>
                  {selectedField.status}
                </div>
                <div className="text-sm text-gray-500 mt-1">Status</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-2xl font-bold">85%</div>
                <div className="text-sm text-gray-500">Health Score</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default FieldMap;
