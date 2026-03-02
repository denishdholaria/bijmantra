import React, { useEffect, useState } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Field, SoilProfile, Season, FarmingPractice } from '../types';
import { agronomyApi } from '../api/client';

const FieldDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [field, setField] = useState<Field | null>(null);
  const [soilProfiles, setSoilProfiles] = useState<SoilProfile[]>([]);
  // Placeholder for related data fetching logic
  const navigate = useNavigate();

  useEffect(() => {
    const loadField = async () => {
      if (id) {
        try {
          const data = await agronomyApi.getField(parseInt(id));
          setField(data);
          // In a real app, we might fetch related data here or have the API return it
          // For now, we'll just load the field details
        } catch (error) {
          console.error("Failed to load field", error);
        }
      }
    };
    loadField();
  }, [id]);

  if (!field) return <div>Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{field.name}</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {field.id}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to={`/agronomy/fields/${field.id}/edit`}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Edit
          </Link>
          <button
            onClick={() => navigate('/agronomy/fields')}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200 py-5">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Area</dt>
            <dd className="mt-1 text-sm text-gray-900">{field.area} hectares</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm font-medium text-gray-500">Location Description</dt>
            <dd className="mt-1 text-sm text-gray-900">{field.location_description || '-'}</dd>
          </div>
        </dl>
      </div>

      {/* Sections for related data (Soil Profiles, Seasons, etc.) could go here */}
      <div className="mt-8 border-t border-gray-200 pt-6">
        <h3 className="text-lg font-medium leading-6 text-gray-900">Related Data</h3>
        <p className="mt-1 text-sm text-gray-500">Soil profiles, seasons, and farming practices associated with this field.</p>

        <div className="mt-4 bg-gray-50 p-4 rounded text-center text-gray-500 text-sm">
           Detailed lists of related entities would be implemented here in a full production view.
        </div>
      </div>
    </div>
  );
};

export default FieldDetail;
