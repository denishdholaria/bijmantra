import React, { useEffect, useState } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { FarmingPractice, Field, Season } from '../types';
import { agronomyApi } from '../api/client';

const FarmingPracticeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [practice, setPractice] = useState<FarmingPractice | null>(null);
  const [field, setField] = useState<Field | null>(null);
  const [season, setSeason] = useState<Season | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      if (id) {
        try {
          const practiceData = await agronomyApi.getFarmingPractice(parseInt(id));
          setPractice(practiceData);
          if (practiceData.field_id) {
             const fieldData = await agronomyApi.getField(practiceData.field_id);
             setField(fieldData);
          }
          if (practiceData.season_id) {
             const seasonData = await agronomyApi.getSeason(practiceData.season_id);
             setSeason(seasonData);
          }
        } catch (error) {
          console.error("Failed to load practice", error);
        }
      }
    };
    loadData();
  }, [id]);

  if (!practice) return <div>Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{practice.name}</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {practice.id} | Date: {practice.date}</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to={`/agronomy/practices/${practice.id}/edit`}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Edit
          </Link>
          <button
            onClick={() => navigate('/agronomy/practices')}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
        </div>
      </div>

      <div className="border-t border-gray-200 py-5">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Practice Type</dt>
            <dd className="mt-1 text-sm text-gray-900">{practice.practice_type}</dd>
          </div>

          <div className="sm:col-span-2">
            <dt className="text-sm font-medium text-gray-500">Description</dt>
            <dd className="mt-1 text-sm text-gray-900">{practice.description || '-'}</dd>
          </div>

          <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-gray-500">Field</dt>
            <dd className="mt-1 text-sm text-gray-900">
                {field ? (
                    <Link to={`/agronomy/fields/${field.id}`} className="text-blue-600 hover:text-blue-900">
                        {field.name}
                    </Link>
                ) : practice.field_id}
            </dd>
          </div>

          {practice.season_id && (
            <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Season</dt>
                <dd className="mt-1 text-sm text-gray-900">
                    {season ? (
                        <Link to={`/agronomy/seasons/${season.id}`} className="text-blue-600 hover:text-blue-900">
                            {season.name}
                        </Link>
                    ) : practice.season_id}
                </dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  );
};

export default FarmingPracticeDetail;
