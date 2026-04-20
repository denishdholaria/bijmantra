import React, { useEffect } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { Link } from 'react-router-dom';

const FieldList: React.FC = () => {
  const { fields, fetchFields, loading, deleteField } = useAgronomy();

  useEffect(() => {
    fetchFields();
  }, []); // eslint-disable-line

  if (loading && fields.length === 0) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Fields</h1>
        <Link
          to="/agronomy/fields/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Add Field
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Area (ha)</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {fields.map((field) => (
              <tr key={field.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link to={`/agronomy/fields/${field.id}`} className="text-blue-600 hover:text-blue-900 font-medium">
                    {field.name}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{field.area}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{field.location_description || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Link to={`/agronomy/fields/${field.id}/edit`} className="text-indigo-600 hover:text-indigo-900 mr-4">
                    Edit
                  </Link>
                  <button
                    onClick={() => deleteField(field.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {fields.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                  No fields found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FieldList;
