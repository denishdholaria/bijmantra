import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useAgronomy } from '../context/AgronomyContext';
import { useNavigate, useParams } from 'react-router-dom';
import { CropCreate } from '../types';

const CropForm: React.FC = () => {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<CropCreate>();
  const { createCrop, updateCrop, crops, fetchCrops } = useAgronomy();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  useEffect(() => {
    if (isEdit) {
      const crop = crops.find(c => c.id === parseInt(id));
      if (crop) {
        setValue('name', crop.name);
        setValue('scientific_name', crop.scientific_name);
        setValue('variety', crop.variety);
        setValue('description', crop.description);
        setValue('n_req', crop.n_req);
        setValue('p_req', crop.p_req);
        setValue('k_req', crop.k_req);
      } else {
         fetchCrops(); // Refresh just in case
      }
    }
  }, [id, crops, setValue, isEdit, fetchCrops]);

  const onSubmit = async (data: CropCreate) => {
    // Convert numeric inputs to numbers or undefined
    const submissionData = {
        ...data,
        n_req: data.n_req !== undefined && data.n_req !== null && data.n_req.toString() !== '' ? Number(data.n_req) : undefined,
        p_req: data.p_req !== undefined && data.p_req !== null && data.p_req.toString() !== '' ? Number(data.p_req) : undefined,
        k_req: data.k_req !== undefined && data.k_req !== null && data.k_req.toString() !== '' ? Number(data.k_req) : undefined,
    };

    if (isEdit) {
      await updateCrop(parseInt(id), submissionData);
    } else {
      await createCrop(submissionData);
    }
    navigate('/agronomy/crops');
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow mt-10">
      <h2 className="text-2xl font-bold mb-6">{isEdit ? 'Edit Crop' : 'New Crop'}</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Name</label>
          <input
            {...register('name', { required: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.name && <span className="text-red-500 text-sm">Required</span>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Scientific Name</label>
          <input
            {...register('scientific_name')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Variety</label>
          <input
            {...register('variety')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
             <label className="block text-sm font-medium text-gray-700">N Req (kg/ha)</label>
             <input type="number" step="0.1" {...register('n_req')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
          <div>
             <label className="block text-sm font-medium text-gray-700">P Req (kg/ha)</label>
             <input type="number" step="0.1" {...register('p_req')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
          <div>
             <label className="block text-sm font-medium text-gray-700">K Req (kg/ha)</label>
             <input type="number" step="0.1" {...register('k_req')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>
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
            onClick={() => navigate('/agronomy/crops')}
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

export default CropForm;
