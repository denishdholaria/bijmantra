import React, { useEffect } from 'react';
import { useAgronomy } from '../context/AgronomyContext';
import { Link } from 'react-router-dom';

const SoilProfileList: React.FC = () => {
  const { soilProfiles, fetchSoilProfiles, loading, deleteSoilProfile } = useAgronomy();

  useEffect(() => {
    fetchSoilProfiles();
  }, []); // eslint-disable-line

  if (loading && soilProfiles.length === 0) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Soil Profiles</h1>
        <Link
          to="/agronomy/soil-profiles/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Add Profile
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sample Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Field ID</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {soilProfiles.map((profile) => (
              <tr key={profile.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link to={`/agronomy/soil-profiles/${profile.id}`} className="text-blue-600 hover:text-blue-900 font-medium">
                    {profile.name}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{profile.sample_date || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{profile.field_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Link to={`/agronomy/soil-profiles/${profile.id}/edit`} className="text-indigo-600 hover:text-indigo-900 mr-4">
                    Edit
                  </Link>
                  <button
                    onClick={() => deleteSoilProfile(profile.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {soilProfiles.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                  No soil profiles found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SoilProfileList;
