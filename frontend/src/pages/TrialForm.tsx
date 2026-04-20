/**
 * Trial Form Page - Thin Adapter
 * Delegates to divisions/breeding/trials/TrialCreationForm
 */

import { TrialCreationForm } from '@/divisions/breeding/trials';

export function TrialForm() {
  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in py-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl shadow-xl p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Create New Trial</h1>
        <p className="text-purple-100 text-lg">Add a new breeding trial to your program</p>
      </div>

      {/* Delegate to division component */}
      <TrialCreationForm />
    </div>
  );
}
