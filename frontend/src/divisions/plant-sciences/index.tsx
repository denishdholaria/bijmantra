/**
 * Plant Sciences Division
 * 
 * Main entry point for the Plant Sciences division.
 * This division covers breeding operations, genomics, molecular biology,
 * crop sciences, and soil/field environment.
 */

import { Outlet } from 'react-router-dom';

export default function PlantSciencesDivision() {
  return (
    <div className="plant-sciences-division">
      <Outlet />
    </div>
  );
}
