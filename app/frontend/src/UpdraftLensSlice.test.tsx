import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  type UpdraftLensFrame,
  UpdraftLensSlice,
  updraftLensBoundaryPath,
  updraftLensCellGeometry,
  updraftLensColor,
  updraftLensSelectionFromPointer,
} from "./UpdraftLensSlice";

const frame: UpdraftLensFrame = {
  result_id: "result-bomex",
  time_index: 61,
  time_seconds: 18_300,
  orientation: "vertical_x",
  plane_dimension: "y",
  plane_index: 5,
  plane_coordinate: -2.65,
  plane_units: "km",
  dimension_order: ["z", "x"],
  x_indices: [0, 1, 2],
  x_values_km: [-0.1, 0, 0.1],
  y_indices: [0, 1, 2, 3, 4, 5],
  y_values_km: [-0.5, -0.4, -0.3, -0.2, -0.1, 0],
  z_indices: [0, 1],
  z_values_km: [0.1, 0.3],
  w_values_m_s: [
    [-1, 0, 1],
    [null, -0.5, 0.5],
  ],
  cloud_mask: [
    [true, true, false],
    [false, true, false],
  ],
  cloud_threshold_kg_kg: 1e-6,
  w_range_min_m_s: -1,
  w_range_max_m_s: 1,
  w_range_method: "fixed",
  wind_mode: "perturbation",
  wind_target_level_m: 600,
  wind_actual_level_m: 580,
  wind_level_index: 14,
  wind_stride: 8,
  wind_reference_m_s: 0.9,
  wind_arrow_domain_fraction: 0.08,
  domain_mean_u_m_s: -8,
  domain_mean_v_m_s: 0,
  wind_vectors: [],
  provenance: {
    source_model: "CM1",
    result_id: "result-bomex",
    run_id: "bomex",
    scenario_id: "bomex_trade_cumulus_baseline_v0",
    processing_method: "test",
    rendering_method: "test",
    provenance_label: "test",
  },
  caveats: [],
};

describe("UpdraftLensSlice colors", () => {
  it("uses the approved fixed diverging palette and distinct missing color", () => {
    expect(updraftLensColor(-1, -1, 1)).toBe("#2166ac");
    expect(updraftLensColor(0, -1, 1)).toBe("#f7f7f7");
    expect(updraftLensColor(1, -1, 1)).toBe("#b2182b");
    expect(updraftLensColor(null, -1, 1)).toBe("#747b80");
    expect(updraftLensColor(-20, -1, 1)).toBe("#2166ac");
    expect(updraftLensColor(20, -1, 1)).toBe("#b2182b");
  });
});

describe("UpdraftLensSlice geometry", () => {
  it("makes adjacent native-grid cells contiguous without gutters", () => {
    const first = updraftLensCellGeometry([-0.15, -0.05, 0.05], [0, 0.2], 0, 0);
    const second = updraftLensCellGeometry([-0.15, -0.05, 0.05], [0, 0.2], 1, 0);
    expect(first.x + first.width).toBeCloseTo(second.x);
    expect(first.height).toBeCloseTo(second.height);
  });

  it("draws cloud-clear and outer cloud edges", () => {
    const path = updraftLensBoundaryPath(
      [
        [true, true],
        [false, true],
      ],
      [0, 1, 2],
      [0, 1, 2],
    );
    expect(path).toContain("M 0 0 L 0 1");
    expect(path).toContain("M 0 1 L 1 1");
    expect(path).toContain("M 2 1 L 2 2");
  });

  it("maps top-left pointer position to highest-z native indices", () => {
    expect(
      updraftLensSelectionFromPointer(0, 0, 300, 200, [-0.1, 0, 0.1], [0.1, 0.3], "vertical_x", 5),
    ).toEqual({ xIndex: 0, yIndex: 5, zIndex: 1 });
  });

  it("maps pointer positions for horizontal and y-z slices", () => {
    expect(
      updraftLensSelectionFromPointer(300, 0, 300, 200, [0, 1, 2], [0, 1], "horizontal", 4),
    ).toEqual({ xIndex: 2, yIndex: 1, zIndex: 4 });
    expect(
      updraftLensSelectionFromPointer(300, 200, 300, 200, [0, 1, 2], [0, 1], "vertical_y", 3),
    ).toEqual({ xIndex: 3, yIndex: 2, zIndex: 0 });
  });
});

describe("UpdraftLensSlice rendering", () => {
  it("preserves physical aspect, fixed legend, boundary, and accessible summary", () => {
    const { container } = render(<UpdraftLensSlice frame={frame} />);
    const plot = screen.getByRole("img", { name: /Updraft Lens vertical x-z slice/ });
    expect(plot).toHaveAttribute("data-domain-aspect", "0.750000");
    expect(plot).toHaveAttribute("data-orientation", "vertical_x");
    expect(container.querySelectorAll("rect")).toHaveLength(6);
    expect(screen.getByLabelText("Vertical velocity color scale")).toHaveTextContent("-1.0");
    expect(screen.getByTestId("updraft-lens-cloud-boundary")).toBeInTheDocument();
  });

  it("hides the boundary and reports native indices on click", () => {
    const onSelectPoint = vi.fn();
    render(
      <UpdraftLensSlice frame={frame} showCloudBoundary={false} onSelectPoint={onSelectPoint} />,
    );
    const plot = screen.getByRole("img", { name: /Updraft Lens vertical x-z slice/ });
    vi.spyOn(plot, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 300,
      bottom: 200,
      width: 300,
      height: 200,
      toJSON: () => ({}),
    });
    fireEvent.click(plot, { clientX: 300, clientY: 200 });
    expect(onSelectPoint).toHaveBeenCalledWith({ xIndex: 2, yIndex: 5, zIndex: 0 });
    expect(screen.queryByTestId("updraft-lens-cloud-boundary")).not.toBeInTheDocument();
  });

  it("renders horizontal axes from the frame dimension order", () => {
    render(
      <UpdraftLensSlice
        frame={{
          ...frame,
          orientation: "horizontal",
          plane_dimension: "z",
          plane_index: 1,
          dimension_order: ["y", "x"],
          w_values_m_s: [
            [-1, 0, 1],
            [0, 0.5, 1],
          ],
          cloud_mask: [
            [false, true, false],
            [false, true, false],
          ],
        }}
      />,
    );
    expect(screen.getByRole("img", { name: /horizontal x-y slice/ })).toHaveAttribute(
      "data-orientation",
      "horizontal",
    );
  });
});
