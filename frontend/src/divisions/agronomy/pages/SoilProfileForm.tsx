import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useAgronomy } from '../context/AgronomyContext';
import { useNavigate, useParams } from 'react-router-dom';
import { SoilProfileCreate } from '../types';

const SoilProfileForm: React.FC = () => {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<SoilProfileCreate>();
  const { createSoilProfile, updateSoilProfile, soilProfiles, fetchSoilProfiles, fetchFields, fields } = useAgronomy();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  useEffect(() => {
    fetchFields();
    if (isEdit) {
      const profile = soilProfiles.find(p => p.id === parseInt(id));
      if (profile) {
        setValue('name', profile.name);
        setValue('description', profile.description);
        setValue('field_id', profile.field_id);
        setValue('sample_date', profile.sample_date);
        setValue('nitrogen', profile.nitrogen);
        setValue('phosphorus', profile.phosphorus);
        setValue('potassium', profile.potassium);
        setValue('ph', profile.ph);
        setValue('organic_matter', profile.organic_matter);
      } else {
         fetchSoilProfiles();
      }
    }
  }, [id, soilProfiles, setValue, isEdit]);

  const onSubmit = async (data: SoilProfileCreate) => {
    // Convert string inputs to appropriate types
    const submissionData = {
        ...data,
        field_id: Number(data.field_id),
        nitrogen: Number(data.nitrogen),
        phosphorus: Number(data.phosphorus),
        potassium: Number(data.potassium),
        ph: data.ph ? Number(data.ph) : undefined,
        organic_matter: data.organic_matter ? Number(data.organic_matter) : undefined,
    };

    if (isEdit) {
      await updateSoilProfile(parseInt(id), submissionData);
    } else {
      await createSoilProfile(submissionData);
    }
    navigate('/agronomy/soil-profiles');
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <h2 className="text-2xl font-bold mb-6">{isEdit ? 'Edit Soil Profile' : 'New Soil Profile'}</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name</label>
          <input
            id="name"
            {...register('name', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.name && <span className="text-red-500 text-sm">Required</span>}
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
          <label htmlFor="sample_date" className="block text-sm font-medium text-gray-700">Sample Date</label>
          <input
            id="sample_date"
            type="date"
            {...register('sample_date')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
             <label htmlFor="nitrogen" className="block text-sm font-medium text-gray-700">Nitrogen (ppm)</label>
             <input id="nitrogen" type="number" step="0.1" {...register('nitrogen')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
          <div>
             <label htmlFor="phosphorus" className="block text-sm font-medium text-gray-700">Phosphorus (ppm)</label>
             <input id="phosphorus" type="number" step="0.1" {...register('phosphorus')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
          <div>
             <label htmlFor="potassium" className="block text-sm font-medium text-gray-700">Potassium (ppm)</label>
             <input id="potassium" type="number" step="0.1" {...register('potassium')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
             <label htmlFor="ph" className="block text-sm font-medium text-gray-700">pH</label>
             <input id="ph" type="number" step="0.1" {...register('ph')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
          <div>
             <label htmlFor="organic_matter" className="block text-sm font-medium text-gray-700">Organic Matter (%)</label>
             <input id="organic_matter" type="number" step="0.1" {...register('organic_matter')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            id="description"
            {...register('description')}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/agronomy/soil-profiles')}
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

export default SoilProfileForm;
