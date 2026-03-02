import React, { useEffect, useState } from 'react';
import { NutrientTest } from '../types';
import { SoilService } from '../services';

export const NutrientTestList: React.FC = () => {
  const [tests, setTests] = useState<NutrientTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      setLoading(true);
      const data = await SoilService.getNutrientTests();
      setTests(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this test?')) return;
    try {
      await SoilService.deleteNutrientTest(id);
      setTests(tests.filter(t => t.id !== id));
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Nutrient Tests</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="py-2 px-4 border-b">Date</th>
              <th className="py-2 px-4 border-b">Field ID</th>
              <th className="py-2 px-4 border-b">Lab</th>
              <th className="py-2 px-4 border-b">Depth</th>
              <th className="py-2 px-4 border-b">N</th>
              <th className="py-2 px-4 border-b">P</th>
              <th className="py-2 px-4 border-b">K</th>
              <th className="py-2 px-4 border-b">pH</th>
              <th className="py-2 px-4 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tests.map(test => (
              <tr key={test.id} className="hover:bg-gray-50">
                <td className="py-2 px-4 border-b">{test.sample_date}</td>
                <td className="py-2 px-4 border-b">{test.field_id}</td>
                <td className="py-2 px-4 border-b">{test.lab_name}</td>
                <td className="py-2 px-4 border-b">{test.depth}</td>
                <td className="py-2 px-4 border-b">{test.nitrogen}</td>
                <td className="py-2 px-4 border-b">{test.phosphorus}</td>
                <td className="py-2 px-4 border-b">{test.potassium}</td>
                <td className="py-2 px-4 border-b">{test.ph}</td>
                <td className="py-2 px-4 border-b">
                  <button className="text-blue-500 mr-2">Edit</button>
                  <button onClick={() => handleDelete(test.id)} className="text-red-500">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
