import React, { useEffect, useState } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Season, Field, Crop } from '../types';
import { agronomyApi } from '../api/client';

const SeasonDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [season, setSeason] = useState<Season | null>(null);
  const [field, setField] = useState<Field | null>(null);
  const [crop, setCrop] = useState<Crop | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      if (id) {
        try {
          const seasonData = await agronomyApi.getSeason(parseInt(id));
          setSeason(seasonData);
          if (seasonData.field_id) {
             const fieldData = await agronomyApi.getField(seasonData.field_id);
             setField(fieldData);
          }
          if (seasonData.crop_id) {
             const cropData = await agronomyApi.getCrop(seasonData.crop_id);
             setCrop(cropData);
          }
        } catch (error) {
          console.error("Failed to load season", error);
        }
      }
    };
    loadData();
  }, [id]);

  if (!season) return <div>Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{season.name}</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {season.id}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to={`/agronomy/seasons/${season.id}/edit`}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Edit
          </Link>
          <button
            onClick={() => navigate('/agronomy/seasons')}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200 py-5">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Start Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{season.start_date}</dd>
          </div>
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">End Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{season.end_date}</dd>
          </div>

          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Field</dt>
            <dd className="mt-1 text-sm text-gray-900">
                {field ? (
                    <Link to={`/agronomy/fields/${field.id}`} className="text-blue-600 hover:text-blue-900">
                        {field.name}
                    </Link>
                ) : season.field_id}
            </dd>
          </div>

          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Crop</dt>
            <dd className="mt-1 text-sm text-gray-900">
                {crop ? (
                    <Link to={`/agronomy/crops/${crop.id}`} className="text-blue-600 hover:text-blue-900">
                        {crop.name}
                    </Link>
                ) : season.crop_id}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
};

export default SeasonDetail;
