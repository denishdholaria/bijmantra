import React, { useEffect } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { Link } from 'react-router-dom';

const FarmingPracticeList: React.FC = () => {
  const { farmingPractices, fetchFarmingPractices, loading, deleteFarmingPractice } = useAgronomy();

  useEffect(() => {
    fetchFarmingPractices();
  }, []); // eslint-disable-line

  if (loading && farmingPractices.length === 0) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Farming Practices</h1>
        <Link
          to="/agronomy/practices/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Record Practice
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Field ID</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {farmingPractices.map((practice) => (
              <tr key={practice.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link to={`/agronomy/practices/${practice.id}`} className="text-blue-600 hover:text-blue-900 font-medium">
                    {practice.name}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{practice.practice_type}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{practice.date}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{practice.field_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Link to={`/agronomy/practices/${practice.id}/edit`} className="text-indigo-600 hover:text-indigo-900 mr-4">
                    Edit
                  </Link>
                  <button
                    onClick={() => deleteFarmingPractice(practice.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {farmingPractices.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No farming practices found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FarmingPracticeList;
