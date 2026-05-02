/**
 * Breeding Cross Management Panel Component
 * Main UI component for managing breeding crosses
 */

import React from 'react';
import { useCrossManagement } from './useCrossManagement';
import type { CrossFilter } from './types';

interface CrossManagementPanelProps {
  initialFilter?: CrossFilter;
}

export function CrossManagementPanel({ initialFilter }: CrossManagementPanelProps) {
  const { crosses, loading, error, updateFilter, reload } = useCrossManagement(initialFilter);

  if (loading) {
    return <div>Loading crosses...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="cross-management-panel">
      <h2>Breeding Crosses</h2>
      <div className="cross-list">
        {crosses.length === 0 ? (
          <p>No crosses found</p>
        ) : (
          <ul>
            {crosses.map(cross => (
              <li key={cross.id}>
                {cross.crossCode}: {cross.maternalParent} × {cross.paternalParent} ({cross.status})
              </li>
            ))}
          </ul>
        )}
      </div>
      <button onClick={reload}>Reload</button>
    </div>
  );
}
