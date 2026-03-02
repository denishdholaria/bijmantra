import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useAgronomy } from '../context/AgronomyContext';
import { useNavigate, useParams } from 'react-router-dom';
import { FieldCreate } from '../types';

const FieldForm: React.FC = () => {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FieldCreate>();
  const { createField, updateField, fields, fetchFields } = useAgronomy();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  useEffect(() => {
    if (isEdit) {
      const field = fields.find(f => f.id === parseInt(id));
      if (field) {
        setValue('name', field.name);
        setValue('area', field.area);
        setValue('location_description', field.location_description);
        // Coordinates handling omitted for simplicity in this version
      } else {
         fetchFields();
      }
    }
  }, [id, fields, setValue, isEdit, fetchFields]);

  const onSubmit = async (data: FieldCreate) => {
    // Convert string inputs to numbers if necessary
    const submissionData = {
        ...data,
        area: Number(data.area)
    };

    if (isEdit) {
      await updateField(parseInt(id), submissionData);
    } else {
      await createField(submissionData);
    }
    navigate('/agronomy/fields');
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <h2 className="text-2xl font-bold mb-6">{isEdit ? 'Edit Field' : 'New Field'}</h2>
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
          <label htmlFor="area" className="block text-sm font-medium text-gray-700">Area (hectares)</label>
          <input
            id="area"
            type="number"
            step="0.01"
            {...register('area', { required: true, min: 0.01 })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.area && <span className="text-red-500 text-sm">Required (positive number)</span>}
        </div>

        <div>
          <label htmlFor="location_description" className="block text-sm font-medium text-gray-700">Location Description</label>
          <textarea
            id="location_description"
            {...register('location_description')}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/agronomy/fields')}
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

export default FieldForm;
