import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  type UpdraftLensFrame,
  UpdraftLensScaleLegend,
  UpdraftLensSlice,
  updraftLensBoundaryPath,
  updraftLensCellGeometry,
  updraftLensDiscreteColor,
  updraftLensSelectionFromPointer,
} from "./UpdraftLensSlice";

const breakpoints = [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 2.0, 3.0, 5.0];
const colors = [
  "#4b0082",
  "#0057d9",
  "#00c9d8",
  "#ffffff",
  "#00d63b",
  "#8fe000",
  "#ffe000",
  "#ff9800",
  "#ff3b00",
  "#c40000",
];

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
  w_range_max_m_s: 5,
  w_range_method: "fixed_trade_cumulus_updraft_velocity_v1",
  w_scale_id: "trade_cumulus_updraft_velocity_v1",
  w_scale_owner: "trade_cumulus",
  w_scale_type: "fixed_discrete",
  w_scale_units: "m/s",
  w_scale_breakpoints_m_s: breakpoints,
  w_scale_colors: colors,
  w_scale_neutral_interval_m_s: [-0.1, 0.1],
  w_scale_source: "pm_approved_issue_379_from_stage5b2_matched_pair",
  w_scale_clipping_behavior:
    "values_below_-1.0_and_at_or_above_5.0_use_endpoint_colors_and_are_reported_as_clipped",
  w_finite_count: 5,
  w_low_clipped_count: 0,
  w_high_clipped_count: 0,
  w_low_clipped_fraction: 0,
  w_high_clipped_fraction: 0,
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
  it("uses exact half-open classes immediately below, at, and above every breakpoint", () => {
    breakpoints.forEach((breakpoint, index) => {
      expect(updraftLensDiscreteColor(breakpoint - 1e-6, breakpoints, colors)).toBe(colors[index]);
      expect(updraftLensDiscreteColor(breakpoint, breakpoints, colors)).toBe(colors[index + 1]);
      expect(updraftLensDiscreteColor(breakpoint + 1e-6, breakpoints, colors)).toBe(
        colors[index + 1],
      );
    });
  });

  it("keeps neutral boundaries, missing values, and classes deterministic without interpolation", () => {
    expect(updraftLensDiscreteColor(-0.1, breakpoints, colors)).toBe("#ffffff");
    expect(updraftLensDiscreteColor(0, breakpoints, colors)).toBe("#ffffff");
    expect(updraftLensDiscreteColor(0.1, breakpoints, colors)).toBe("#00d63b");
    expect(updraftLensDiscreteColor(0.11, breakpoints, colors)).toBe("#00d63b");
    expect(updraftLensDiscreteColor(0.49, breakpoints, colors)).toBe("#00d63b");
    expect(updraftLensDiscreteColor(null, breakpoints, colors)).toBe("#747b80");
    expect(updraftLensDiscreteColor(Number.NaN, breakpoints, colors)).toBe("#747b80");
    expect(updraftLensDiscreteColor(Number.POSITIVE_INFINITY, breakpoints, colors)).toBe("#747b80");
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
  it("preserves physical aspect, fixed legend, boundary, and slice range", () => {
    const { container } = render(<UpdraftLensSlice frame={frame} />);
    const plot = screen.getByRole("img", { name: /Updraft Lens vertical x-z slice/ });
    expect(plot).toHaveAttribute("data-domain-aspect", "0.750000");
    expect(plot).toHaveAttribute("data-orientation", "vertical_x");
    expect(container.querySelectorAll("rect")).toHaveLength(6);
    const legend = screen.getByLabelText(/2-D inspector Vertical velocity \(w\), m\/s/);
    expect(legend).toHaveTextContent("-0.1 to < 0.1 m/s");
    expect(legend).toHaveTextContent(">= 5.0 m/s");
    expect(legend).not.toHaveTextContent("near-neutral motion");
    expect(legend).not.toHaveTextContent("#ffffff");
    expect(legend.querySelectorAll(".updraft-lens-scale-swatch")).toHaveLength(10);
    expect(
      within(legend)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual([
      ">= 5.0 m/s",
      "3.0 to < 5.0 m/s",
      "2.0 to < 3.0 m/s",
      "1.0 to < 2.0 m/s",
      "0.5 to < 1.0 m/s",
      "0.1 to < 0.5 m/s",
      "-0.1 to < 0.1 m/s",
      "-0.5 to < -0.1 m/s",
      "-1.0 to < -0.5 m/s",
      "< -1.0 m/s",
    ]);
    expect(legend).toHaveTextContent("Slice maximum 1.00 m/s.");
    expect(legend).toHaveTextContent("Slice minimum -1.00 m/s.");
    expect(screen.queryByText(/Clipped in this slice/)).not.toBeInTheDocument();
    expect(screen.getByTestId("updraft-lens-cloud-boundary")).toBeInTheDocument();
  });

  it("uses a compact unit-once legend outside the maximized Lens", () => {
    render(<UpdraftLensScaleLegend frame={frame} viewLabel="Explore workspace" compact />);
    const legend = screen.getByLabelText(/Explore workspace Vertical velocity \(w\), m\/s/);
    expect(legend).toHaveTextContent("w (m/s)");
    expect(legend).toHaveTextContent("3.0 to < 5.0");
    expect(legend).not.toHaveTextContent("3.0 to < 5.0 m/s");
    expect(legend).not.toHaveTextContent("Slice maximum");
    expect(legend).not.toHaveTextContent("Slice minimum");
  });

  it.each([
    [2, 0],
    [0, 3],
    [2, 3],
  ])("keeps clipping counts out of the visible range summary (%s, %s)", (lowCount, highCount) => {
    render(
      <UpdraftLensSlice
        frame={{
          ...frame,
          w_low_clipped_count: lowCount,
          w_high_clipped_count: highCount,
        }}
      />,
    );
    expect(screen.getByText("Slice maximum 1.00 m/s.")).toBeInTheDocument();
    expect(screen.getByText("Slice minimum -1.00 m/s.")).toBeInTheDocument();
    expect(screen.queryByText(/Clipped in this slice/)).not.toBeInTheDocument();
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
