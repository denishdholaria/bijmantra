import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useAgronomy } from '../context/AgronomyContext';
import { useNavigate, useParams } from 'react-router-dom';
import { SeasonCreate } from '../types';

const SeasonForm: React.FC = () => {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<SeasonCreate>();
  const { createSeason, updateSeason, seasons, fetchSeasons, fetchFields, fields, fetchCrops, crops } = useAgronomy();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  useEffect(() => {
    fetchFields();
    fetchCrops();
    if (isEdit) {
      const season = seasons.find(s => s.id === parseInt(id));
      if (season) {
        setValue('name', season.name);
        setValue('start_date', season.start_date);
        setValue('end_date', season.end_date);
        setValue('field_id', season.field_id);
        setValue('crop_id', season.crop_id);
      } else {
         fetchSeasons();
      }
    }
  }, [id, seasons, setValue, isEdit]);

  const onSubmit = async (data: SeasonCreate) => {
    const submissionData = {
        ...data,
        field_id: Number(data.field_id),
        crop_id: Number(data.crop_id),
    };

    if (isEdit) {
      await updateSeason(parseInt(id), submissionData);
    } else {
      await createSeason(submissionData);
    }
    navigate('/agronomy/seasons');
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <h2 className="text-2xl font-bold mb-6">{isEdit ? 'Edit Season' : 'New Season'}</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">Season Name</label>
          <input
            id="name"
            {...register('name', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="e.g., Kharif 2026"
          />
          {errors.name && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
             <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">Start Date</label>
             <input id="start_date" type="date" {...register('start_date', { required: true })} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
             {errors.start_date && <span className="text-red-500 text-sm">Required</span>}
          </div>
          <div>
             <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">End Date</label>
             <input id="end_date" type="date" {...register('end_date', { required: true })} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
             {errors.end_date && <span className="text-red-500 text-sm">Required</span>}
          </div>
        </div>

        <div>
          <label htmlFor="field_id" className="block text-sm font-medium text-gray-700">Field</label>
          <select
            id="field_id"
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
          <label htmlFor="crop_id" className="block text-sm font-medium text-gray-700">Crop</label>
          <select
            id="crop_id"
            {...register('crop_id', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">Select a crop</option>
            {crops.map(crop => (
                <option key={crop.id} value={crop.id}>{crop.name}</option>
            ))}
          </select>
          {errors.crop_id && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/agronomy/seasons')}
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

export default SeasonForm;
