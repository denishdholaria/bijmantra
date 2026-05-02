import React, { useEffect, useState } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { SoilProfile, Field } from '../types';
import { agronomyApi } from '../api/client';

const SoilProfileDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<SoilProfile | null>(null);
  const [field, setField] = useState<Field | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      if (id) {
        try {
          const profileData = await agronomyApi.getSoilProfile(parseInt(id));
          setProfile(profileData);
          if (profileData.field_id) {
             const fieldData = await agronomyApi.getField(profileData.field_id);
             setField(fieldData);
          }
        } catch (error) {
          console.error("Failed to load soil profile", error);
        }
      }
    };
    loadData();
  }, [id]);

  if (!profile) return <div>Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{profile.name}</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {profile.id} | Sample Date: {profile.sample_date || '-'}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to={`/agronomy/soil-profiles/${profile.id}/edit`}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Edit
          </Link>
          <button
            onClick={() => navigate('/agronomy/soil-profiles')}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200 py-5">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Field</dt>
            <dd className="mt-1 text-sm text-gray-900">
                {field ? (
                    <Link to={`/agronomy/fields/${field.id}`} className="text-blue-600 hover:text-blue-900">
                        {field.name}
                    </Link>
                ) : profile.field_id}
            </dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm font-medium text-gray-500">Description</dt>
            <dd className="mt-1 text-sm text-gray-900">{profile.description || '-'}</dd>
          </div>

          <div className="sm:col-span-2 mt-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Nutrient Levels (ppm)</h3>
            <div className="grid grid-cols-3 gap-4">
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Nitrogen</span>
                 <span className="block text-xl font-semibold text-green-600">{profile.nitrogen}</span>
               </div>
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Phosphorus</span>
                 <span className="block text-xl font-semibold text-blue-600">{profile.phosphorus}</span>
               </div>
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Potassium</span>
                 <span className="block text-xl font-semibold text-purple-600">{profile.potassium}</span>
               </div>
            </div>
          </div>

          <div className="sm:col-span-2 mt-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Properties</h3>
            <div className="grid grid-cols-2 gap-4">
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">pH</span>
                 <span className="block text-xl font-semibold text-gray-800">{profile.ph || '-'}</span>
               </div>
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Organic Matter (%)</span>
                 <span className="block text-xl font-semibold text-gray-800">{profile.organic_matter || '-'}</span>
               </div>
            </div>
          </div>
        </dl>
      </div>
    </div>
  );
};

export default SoilProfileDetail;
