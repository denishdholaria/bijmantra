/**
 * Seed Bank Inventory Panel Component
 * Main UI component for inventory management
 */

import React from 'react';
import { useInventory } from './useInventory';
import type { InventoryFilter } from './types';

interface InventoryPanelProps {
  initialFilter?: InventoryFilter;
}

export function InventoryPanel({ initialFilter }: InventoryPanelProps) {
  const { items, loading, error, updateFilter, reload } = useInventory(initialFilter);

  if (loading) {
    return <div>Loading inventory...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="inventory-panel">
      <h2>Seed Bank Inventory</h2>
      <div className="inventory-list">
        {items.length === 0 ? (
          <p>No inventory items found</p>
        ) : (
          <ul>
            {items.map(item => (
              <li key={item.id}>
                {item.accessionId} - {item.quantity} {item.unit} ({item.status})
              </li>
            ))}
          </ul>
        )}
      </div>
      <button onClick={reload}>Reload</button>
    </div>
  );
}
