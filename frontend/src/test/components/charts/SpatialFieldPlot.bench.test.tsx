import React from "react";
import { render, fireEvent, screen } from "@testing-library/react";
import SpatialFieldPlot, {
  PlotData,
} from "@/components/charts/SpatialFieldPlot";
import { describe, it, vi } from "vitest";

describe("SpatialFieldPlot Benchmark", () => {
  it("renders and handles hover efficiently with large dataset", async () => {
    const rows = 50;
    const cols = 50;
    const plots: PlotData[] = [];
    for (let r = 1; r <= rows; r++) {
      for (let c = 1; c <= cols; c++) {
        plots.push({
          row: r,
          col: c,
          plotId: `P-${r}-${c}`,
          status: "planted",
          value: Math.random() * 100,
          genotype: `G-${r}-${c}`,
        });
      }
    }

    const onPlotClick = vi.fn();

    console.log(`Rendering ${rows}x${cols} grid...`);
    const { container } = render(
      <SpatialFieldPlot
        rows={rows}
        cols={cols}
        plots={plots}
        title="Benchmark Plot"
        onPlotClick={onPlotClick}
      />,
    );

    const midRow = Math.floor(rows / 2);
    const midCol = Math.floor(cols / 2);
    const targetPlotId = `P-${midRow}-${midCol}`;

    const cell = container.querySelector(`div[title^="Plot ${targetPlotId}"]`);
    if (!cell) {
      throw new Error(`Could not find cell for ${targetPlotId}`);
    }

    const start = performance.now();
    fireEvent.mouseOver(cell);
    fireEvent.mouseEnter(cell);

    await screen.findByText(new RegExp(targetPlotId), {}, { timeout: 5000 });

    const end = performance.now();
    console.log(
      `Hover time for ${rows * cols} plots: ${(end - start).toFixed(4)}ms`,
    );
  });
});
