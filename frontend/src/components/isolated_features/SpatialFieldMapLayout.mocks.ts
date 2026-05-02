import { FieldLayout, FieldPlot, PlotStatus } from './SpatialFieldMapLayout.types';

export const generateMockLayout = (rows: number, cols: number): FieldLayout => {
  const plots: FieldPlot[] = [];
  const statuses: PlotStatus[] = ['pending', 'complete', 'skipped', 'failed'];

  for (let r = 1; r <= rows; r++) {
    for (let c = 1; c <= cols; c++) {
      const id = `plot-${r}-${c}`;
      const plotNumber = `${r}${String.fromCharCode(64 + c)}`;
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      const entryType = Math.random() > 0.8 ? 'check' : 'test';

      plots.push({
        id,
        plotNumber,
        row: r,
        col: c,
        status,
        entryType,
        germplasmName: `Germplasm ${Math.floor(Math.random() * 100)}`,
        observations: [
          { variableDbId: 'yield', variableName: 'Yield', value: Math.floor(Math.random() * 100) },
          { variableDbId: 'height', variableName: 'Height', value: Math.floor(Math.random() * 200) },
          { variableDbId: 'moisture', variableName: 'Moisture', value: Math.floor(Math.random() * 20) },
        ]
      });
    }
  }

  return {
    studyDbId: 'study-123',
    studyName: 'Mock Field Trial 2026',
    rows,
    cols,
    plots,
  };
};
