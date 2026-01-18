/**
 * New Accession Page
 */

import { useNavigate } from 'react-router-dom';
import { AccessionForm } from '../components/AccessionForm';

export function AccessionNew() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Register New Accession</h1>
        <p className="text-gray-600 mt-1">Add a new germplasm accession to the seed bank</p>
      </div>

      <AccessionForm
        onSuccess={() => navigate('/seed-bank/accessions')}
        onCancel={() => navigate('/seed-bank/accessions')}
      />
    </div>
  );
}

export default AccessionNew;
