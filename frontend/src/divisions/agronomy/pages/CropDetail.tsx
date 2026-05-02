import React, { useEffect, useState } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Crop } from '../types';
import { agronomyApi } from '../api/client';

const CropDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [crop, setCrop] = useState<Crop | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadCrop = async () => {
      if (id) {
        try {
          const data = await agronomyApi.getCrop(parseInt(id));
          setCrop(data);
        } catch (error) {
          console.error("Failed to load crop", error);
        }
      }
    };
    loadCrop();
  }, [id]);

  if (!crop) return <div>Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{crop.name}</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {crop.id}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to={`/agronomy/crops/${crop.id}/edit`}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Edit
          </Link>
          <button
            onClick={() => navigate('/agronomy/crops')}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200 py-5">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Scientific Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{crop.scientific_name || '-'}</dd>
          </div>
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Variety</dt>
            <dd className="mt-1 text-sm text-gray-900">{crop.variety || '-'}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm font-medium text-gray-500">Description</dt>
            <dd className="mt-1 text-sm text-gray-900">{crop.description || '-'}</dd>
          </div>

          <div className="sm:col-span-2 mt-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Nutrient Requirements (kg/ha)</h3>
            <div className="grid grid-cols-3 gap-4">
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Nitrogen</span>
                 <span className="block text-xl font-semibold text-green-600">{crop.n_req}</span>
               </div>
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Phosphorus</span>
                 <span className="block text-xl font-semibold text-blue-600">{crop.p_req}</span>
               </div>
               <div className="bg-gray-50 p-3 rounded text-center">
                 <span className="block text-xs text-gray-500">Potassium</span>
                 <span className="block text-xl font-semibold text-purple-600">{crop.k_req}</span>
               </div>
            </div>
          </div>
        </dl>
      </div>
    </div>
  );
};

export default CropDetail;
