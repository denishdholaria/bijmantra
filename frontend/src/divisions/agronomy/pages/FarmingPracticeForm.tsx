import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useAgronomy } from '../context/AgronomyContext';
import { useNavigate, useParams } from 'react-router-dom';
import { FarmingPracticeCreate } from '../types';

const FarmingPracticeForm: React.FC = () => {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FarmingPracticeCreate>();
  const { createFarmingPractice, updateFarmingPractice, farmingPractices, fetchFarmingPractices, fetchFields, fields, fetchSeasons, seasons } = useAgronomy();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  useEffect(() => {
    fetchFields();
    fetchSeasons();
    if (isEdit) {
      const practice = farmingPractices.find(p => p.id === parseInt(id));
      if (practice) {
        setValue('name', practice.name);
        setValue('description', practice.description);
        setValue('practice_type', practice.practice_type);
        setValue('date', practice.date);
        setValue('field_id', practice.field_id);
        setValue('season_id', practice.season_id);
      } else {
         fetchFarmingPractices();
      }
    }
  }, [id, farmingPractices, setValue, isEdit]);

  const onSubmit = async (data: FarmingPracticeCreate) => {
    const submissionData = {
        ...data,
        field_id: Number(data.field_id),
        season_id: data.season_id ? Number(data.season_id) : undefined,
    };

    if (isEdit) {
      await updateFarmingPractice(parseInt(id), submissionData);
    } else {
      await createFarmingPractice(submissionData);
    }
    navigate('/agronomy/practices');
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <h2 className="text-2xl font-bold mb-6">{isEdit ? 'Edit Farming Practice' : 'Record Farming Practice'}</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Practice Name</label>
          <input
            {...register('name', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="e.g., Pre-sowing irrigation"
          />
          {errors.name && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Practice Type</label>
          <select
            {...register('practice_type', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">Select type</option>
            <option value="Irrigation">Irrigation</option>
            <option value="Fertilization">Fertilization</option>
            <option value="PestControl">Pest Control</option>
            <option value="Harvesting">Harvesting</option>
            <option value="Sowing">Sowing</option>
            <option value="Tillage">Tillage</option>
          </select>
          {errors.practice_type && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Date</label>
          <input
            type="date"
            {...register('date', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.date && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Field</label>
          <select
            {...register('field_id', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">Select a field</option>
            {fields.map(field => (
                <option key={field.id} value={field.id}>{field.name}</option>
            ))}
          </select>
          {errors.field_id && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Season (Optional)</label>
          <select
            {...register('season_id')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">Select a season</option>
            {seasons.map(season => (
                <option key={season.id} value={season.id}>{season.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            {...register('description')}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/agronomy/practices')}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Save
          </button>
        </div>
      </form>
    </div>
  );
};

export default FarmingPracticeForm;
