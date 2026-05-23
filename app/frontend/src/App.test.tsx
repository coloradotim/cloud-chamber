import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const scenarioResponse = {
  golden_path_scenario_id: "baseline-shallow-cumulus",
  scenarios: [
    {
      id: "baseline-shallow-cumulus",
      display_name: "Baseline Shallow Cumulus",
      description: "First Golden Path hero case for shallow cumulus.",
      physical_question: "How do low-level moisture and surface heating shape shallow cumulus?",
      intended_behavior: "A balanced shallow-cumulus case.",
      expected_behavior: "Clouds may form after heating and mixing.",
      learning_goals: ["Identify first cloud time"],
      warnings: ["Preview estimates are guidance only."],
      limitations: ["Template mapping is not scientifically accepted until validation."],
      controls: [
        {
          id: "low_level_humidity",
          label: "Low-level humidity",
          description: "Relative moisture in the lower atmosphere.",
          type: "choice",
          default: "baseline",
          options: [
            { value: "drier", label: "Drier" },
            { value: "baseline", label: "Baseline" },
            { value: "more_humid", label: "More humid" },
          ],
        },
        {
          id: "surface_heating",
          label: "Surface heating",
          description: "Relative daytime heating strength.",
          type: "choice",
          default: "baseline",
          options: [
            { value: "weaker", label: "Weaker" },
            { value: "baseline", label: "Baseline" },
            { value: "stronger", label: "Stronger" },
          ],
        },
      ],
      run_size_presets: [
        {
          id: "quick_look",
          label: "Quick look",
          purpose: "Sanity check",
          expected_runtime: "roughly 10-20 minutes",
          confidence: "lower confidence",
          output_notes: "coarser output",
        },
      ],
    },
  ],
};

const dryRunResponse = {
  package_dir: "/tmp/CloudChamber/runs/dry-run-001",
  manifest_path: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
  report_path: "/tmp/CloudChamber/runs/dry-run-001/dry_run_report.json",
  generated_files: [],
  report: {
    scenario_id: "baseline-shallow-cumulus",
    physical_question: "How do low-level moisture and surface heating shape shallow cumulus?",
    controls: {
      low_level_humidity: "more_humid",
      surface_heating: "baseline",
    },
    run_size_preset: "quick_look",
    estimated_cost_or_size: "unknown until validated",
    expected_diagnostics: ["first_cloud_time", "cloud_water_summary"],
    visualization_defaults: { primary_field: "qc" },
    generated_files: {
      manifest: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
      namelist: "/tmp/CloudChamber/runs/dry-run-001/namelist.input",
      input_sounding: "/tmp/CloudChamber/runs/dry-run-001/input_sounding",
      report: "/tmp/CloudChamber/runs/dry-run-001/dry_run_report.json",
    },
    not_a_completed_cm1_result: true,
    cm1_was_launched: false,
    provenance: {
      product_state: "packaged_dry_run_output",
      source_model: "CM1",
      preview_is_guidance_only: true,
      visualizer_is_interpretation: true,
    },
  },
};

const resultCard = {
  result_id: "result-dry-run-quicklook",
  run_id: "dry-run-quicklook",
  name: "Quick-look shallow cumulus",
  tags: ["baseline", "quick-look"],
  notes: "Reference-derived quick-look result.",
  saved: false,
  protected: false,
  scenario_id: "baseline-shallow-cumulus",
  scenario_name: "Baseline Shallow Cumulus",
  run_size_preset: "quick_look",
  physical_question: "How do low-level moisture and surface heating shape shallow cumulus?",
  controls: {
    low_level_humidity: "baseline",
    surface_heating: "baseline",
  },
  status: "ingested_result_metadata",
  source_lifecycle_state: "completed",
  source_product_state: "completed_cm1_result",
  source_model: "CM1",
  provenance_labels: [
    "source_model:CM1",
    "source_product_state:completed_cm1_result",
    "result_state:ingested_result_metadata",
  ],
  diagnostics_summary: "cloud formed; rain detected",
  first_cloud_time_seconds: 1800,
  max_qc_kg_kg: 0.002192789688706398,
  max_w_m_s: 6.866957187652588,
  min_w_m_s: -4.21529483795166,
  rain_present: true,
  caveats: ["CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"],
  output_file_summary: {
    netcdf_count: 14,
    model_output_count: 13,
    stats_netcdf_count: 1,
    raw_cm1_artifact_count: 0,
    processed_artifact_count: 0,
    visualization_ready_artifact_count: 0,
    total_output_count: 14,
    model_output_file_count: 13,
    time_steps: 13,
    first_output_time_seconds: 0,
    last_output_time_seconds: 10800,
  },
  created_at: "2026-05-22T15:15:36Z",
  completed_at: "2026-05-22T15:45:36Z",
  ingested_at: "2026-05-22T15:46:36Z",
  updated_at: "2026-05-22T15:46:36Z",
};

const dryFailedCard = {
  ...resultCard,
  result_id: "result-dry-failed-cumulus",
  run_id: "dry-run-dry-failed-cumulus-20260522192000",
  name: "Dry Failed Cumulus quick-look",
  tags: ["dry-failed", "quick-look"],
  notes: "Moisture-limited contrast case.",
  scenario_id: "dry-failed-cumulus",
  scenario_name: "Dry Failed Cumulus",
  physical_question:
    "How does insufficient low-level moisture prevent shallow cumulus formation even when boundary-layer thermals and vertical motion are present?",
  controls: {
    low_level_humidity: "drier",
    surface_heating: "baseline",
  },
  diagnostics_summary: "no cloud formed; no rain detected",
  first_cloud_time_seconds: null,
  max_qc_kg_kg: 0,
  max_w_m_s: 1.949130654335022,
  min_w_m_s: -1.0865488052368164,
  rain_present: false,
  caveats: ["cloud_base_top_unavailable:no_cloud_cells"],
  created_at: "2026-05-22T19:20:00Z",
  completed_at: "2026-05-22T19:50:00Z",
  ingested_at: "2026-05-22T19:52:00Z",
  updated_at: "2026-05-22T19:52:00Z",
};

const missingDiagnosticsCard = {
  ...resultCard,
  result_id: "result-no-diagnostics",
  run_id: "dry-run-no-diagnostics",
  name: "No diagnostics yet",
  diagnostics_summary: null,
  first_cloud_time_seconds: null,
  max_qc_kg_kg: null,
  max_w_m_s: null,
  min_w_m_s: null,
  rain_present: false,
  caveats: ["missing_qc_field", "missing_w_field"],
  output_file_summary: {
    ...resultCard.output_file_summary,
    model_output_count: 0,
    time_steps: null,
  },
};

const emptyVisualizerCard = {
  ...resultCard,
  result_id: "result-empty-visualizer",
  run_id: "dry-run-empty-visualizer",
  name: "No visual fields",
  diagnostics_summary: "ingested result with no visualizable fields",
  caveats: ["missing_visualization_fields"],
};

const resultsResponse = {
  results: [resultCard, dryFailedCard, missingDiagnosticsCard, emptyVisualizerCard],
};

const provenance = {
  source_model: "CM1",
  result_id: "result-dry-run-quicklook",
  run_id: "dry-run-quicklook",
  scenario_id: "baseline-shallow-cumulus",
  source_product_state: "completed_cm1_result",
  result_state: "ingested_result_metadata",
  processing_method: "backend_xarray_native_grid_slice",
  rendering_method: "json_2d_slice_for_inspection",
  provenance_label: "CM1-derived visualization-ready data; native-grid view; no interpolation",
};

const fieldCatalogResponse = {
  result_id: "result-dry-run-quicklook",
  run_id: "dry-run-quicklook",
  scenario_id: "baseline-shallow-cumulus",
  source_model: "CM1",
  provenance,
  caveats: [],
  available_fields: [
    {
      raw_field_name: "qc",
      canonical_field_name: "cloud_water",
      display_name: "Cloud water",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "w",
      canonical_field_name: "vertical_velocity",
      display_name: "Vertical velocity",
      units: "m/s",
      dimensions: ["time", "zf", "yh", "xh"],
      shape: [3, 3, 2, 3],
      native_grid: "zf/yh/xh",
      coordinate_names: { time: "time", vertical: "zf", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
  ],
};

const viewDefaultsResponse = {
  result_id: "result-dry-run-quicklook",
  run_id: "dry-run-quicklook",
  scenario_id: "baseline-shallow-cumulus",
  preferred_field: "qc",
  fields: {
    qc: {
      field: "qc",
      time_index: 2,
      time_seconds: 1800,
      horizontal_level_index: 1,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_qc_native_grid_location",
      max_value: 0.00002,
      caveats: ["default_location_uses_field_maximum"],
    },
    w: {
      field: "w",
      time_index: 1,
      time_seconds: 900,
      horizontal_level_index: 2,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_w_native_grid_location",
      max_value: 6.5,
      caveats: ["default_location_uses_field_maximum"],
    },
  },
  provenance: {
    ...provenance,
    processing_method: "backend_xarray_interesting_view_defaults",
    rendering_method: "field_slice_and_point_cloud_default_selection",
    provenance_label:
      "CM1-derived visualization defaults; max-value native-grid location; no interpolation",
  },
  caveats: ["default_locations_are_native_grid_indices"],
};

const missingFieldCatalogResponse = {
  ...fieldCatalogResponse,
  result_id: "result-no-diagnostics",
  run_id: "dry-run-no-diagnostics",
  caveats: ["missing_visualization_field:qc"],
  available_fields: [
    {
      ...fieldCatalogResponse.available_fields[1],
      provenance: {
        ...provenance,
        result_id: "result-no-diagnostics",
        run_id: "dry-run-no-diagnostics",
      },
    },
  ],
};

const emptyFieldCatalogResponse = {
  ...fieldCatalogResponse,
  result_id: "result-empty-visualizer",
  run_id: "dry-run-empty-visualizer",
  caveats: ["missing_visualization_fields"],
  available_fields: [],
};

const dryFailedFieldCatalogResponse = {
  ...fieldCatalogResponse,
  result_id: "result-dry-failed-cumulus",
  run_id: "dry-run-dry-failed-cumulus-20260522192000",
  scenario_id: "dry-failed-cumulus",
  available_fields: fieldCatalogResponse.available_fields.map((field) => ({
    ...field,
    provenance: {
      ...field.provenance,
      result_id: "result-dry-failed-cumulus",
      run_id: "dry-run-dry-failed-cumulus-20260522192000",
      scenario_id: "dry-failed-cumulus",
    },
  })),
};

function sliceResponse({
  field = "qc",
  orientation = "horizontal",
  timeIndex = 0,
}: {
  field?: "qc" | "w";
  orientation?: "horizontal" | "vertical_x" | "vertical_y";
  timeIndex?: number;
}) {
  const fieldMetadata =
    fieldCatalogResponse.available_fields.find((candidate) => candidate.raw_field_name === field) ??
    fieldCatalogResponse.available_fields[0];
  const units = fieldMetadata.units;
  const isVertical = orientation !== "horizontal";
  const values =
    field === "qc"
      ? timeIndex < 2
        ? [
            [0, 0.000002, null],
            [0.000004, 0.000006, 0.000008],
          ]
        : [
            [0.00001, 0.000012, 0.000014],
            [0.000016, 0.000018, 0.00002],
          ]
      : [
          [1.5, 2.5, 3.5],
          [4.5, 5.5, 6.5],
        ];
  return {
    result_id: "result-dry-run-quicklook",
    run_id: "dry-run-quicklook",
    scenario_id: "baseline-shallow-cumulus",
    field: fieldMetadata,
    selection: {
      time_index: timeIndex,
      time_seconds: [0, 900, 1800][timeIndex] ?? 1800,
      orientation,
      selected_dimension:
        orientation === "vertical_y" ? "xh" : orientation === "vertical_x" ? "yh" : "zh",
      selected_index: 0,
      selected_coordinate_value: orientation === "horizontal" ? 0.8 : 0,
      level_units: orientation === "horizontal" ? "km" : null,
      level_coordinate_value: orientation === "horizontal" ? 0.8 : null,
      level_meters: orientation === "horizontal" ? 800 : null,
    },
    coordinate_units: isVertical ? { zh: "km", xh: "km" } : { yh: "km", xh: "km" },
    shape: [2, 3],
    dimension_order: isVertical ? ["zh", "xh"] : ["yh", "xh"],
    data_encoding: "json",
    values,
    stats: {
      min: field === "qc" ? 0 : 1.5,
      max: field === "qc" ? (timeIndex < 2 ? 0.000008 : 0.00002) : 6.5,
      mean: field === "qc" ? 0.000004 : 4,
      finite_count: 5,
      non_finite_count: field === "qc" && timeIndex < 2 ? 1 : 0,
    },
    provenance,
    caveats: ["native_grid_view_no_interpolation", "json_numeric_slice_mvp"],
    units,
  };
}

function pointCloudResponse({
  threshold = 0.000001,
  timeIndex = 2,
  points,
}: {
  threshold?: number;
  timeIndex?: number;
  points?: Array<[number, number, number, number]>;
} = {}) {
  const returnedPoints =
    points ??
    (threshold >= 1 || timeIndex === 0
      ? []
      : [
          [0, 0, 0.8, 0.000002],
          [1, 1, 0.8, 0.000006],
          [2, 1, 1.2, 0.000008],
        ]);
  const values = returnedPoints.map((point) => point[3]);
  return {
    result_id: "result-dry-run-quicklook",
    run_id: "dry-run-quicklook",
    scenario_id: "baseline-shallow-cumulus",
    field: fieldCatalogResponse.available_fields[0],
    selection: {
      field: "qc",
      time_index: timeIndex,
      time_seconds: [0, 900, 1800][timeIndex] ?? 1800,
      threshold,
      max_points: 50000,
    },
    coordinate_units: { xh: "km", yh: "km", zh: "km" },
    point_order: ["x", "y", "z", "value"],
    points: returnedPoints,
    stats: {
      source_count: returnedPoints.length,
      returned_count: returnedPoints.length,
      min_value: values.length ? Math.min(...values) : null,
      max_value: values.length ? Math.max(...values) : null,
      downsampled: false,
      downsample_stride: 1,
    },
    provenance: {
      ...provenance,
      processing_method: "backend_xarray_native_grid_threshold",
      rendering_method: "thresholded_point_cloud",
      provenance_label:
        "CM1-derived cloud-water point cloud; native-grid threshold; visualizer interpretation",
    },
    caveats: ["native_grid_thresholded_point_cloud", "visualizer_interpretation_of_cm1_qc"],
  };
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/dry-run-package") {
        return Promise.resolve(new Response(JSON.stringify(dryRunResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/results/result-dry-run-quicklook/visualization/fields") {
        return Promise.resolve(new Response(JSON.stringify(fieldCatalogResponse), { status: 200 }));
      }
      if (url === "/api/results/result-dry-run-quicklook/visualization/defaults") {
        return Promise.resolve(
          new Response(JSON.stringify(viewDefaultsResponse), { status: 200 }),
        );
      }
      if (url === "/api/results/result-no-diagnostics/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(missingFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url === "/api/results/result-no-diagnostics/visualization/defaults") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...viewDefaultsResponse,
              result_id: "result-no-diagnostics",
              preferred_field: "w",
              fields: { w: viewDefaultsResponse.fields.w },
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results/result-empty-visualizer/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(emptyFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url === "/api/results/result-empty-visualizer/visualization/defaults") {
        return Promise.resolve(
          new Response(JSON.stringify({ ...viewDefaultsResponse, preferred_field: null, fields: {} }), {
            status: 200,
          }),
        );
      }
      if (url === "/api/results/result-dry-failed-cumulus/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(dryFailedFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url === "/api/results/result-dry-failed-cumulus/visualization/defaults") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...viewDefaultsResponse,
              result_id: "result-dry-failed-cumulus",
              run_id: "dry-run-dry-failed-cumulus-20260522192000",
              scenario_id: "dry-failed-cumulus",
              preferred_field: "w",
              fields: { w: viewDefaultsResponse.fields.w },
            }),
            { status: 200 },
          ),
        );
      }
      if (url.includes("/visualization/point-cloud")) {
        const parsed = new URL(url, "http://localhost");
        return Promise.resolve(
          new Response(
            JSON.stringify(
              pointCloudResponse({
                threshold: Number(parsed.searchParams.get("threshold") ?? 0.000001),
                timeIndex: Number(parsed.searchParams.get("time_index") ?? 0),
              }),
            ),
            { status: 200 },
          ),
        );
      }
      if (url.includes("/visualization/slice")) {
        const parsed = new URL(url, "http://localhost");
        const levelIndex = parsed.searchParams.get("level_index");
        if (levelIndex === "99") {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "level_index=99 is outside valid range" }), {
              status: 400,
            }),
          );
        }
        return Promise.resolve(
          new Response(
            JSON.stringify(
              sliceResponse({
                field: parsed.searchParams.get("field") === "w" ? "w" : "qc",
                orientation:
                  parsed.searchParams.get("orientation") === "vertical_y"
                    ? "vertical_y"
                    : parsed.searchParams.get("orientation") === "vertical_x"
                      ? "vertical_x"
                      : "horizontal",
                timeIndex: Number(parsed.searchParams.get("time_index") ?? 0),
              }),
            ),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results/result-dry-run-quicklook" && init?.method === "PATCH") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...resultCard,
              name: "Saved notebook entry",
              tags: ["baseline", "notebook"],
              notes: "Updated from the library.",
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results/result-dry-run-quicklook/save" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...resultCard,
              saved: true,
              protected: true,
              status: "saved_result_notebook_entry",
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("renders Baseline Shallow Cumulus controls and physical question", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Baseline Shallow Cumulus" }),
    ).toBeInTheDocument();
    expect(screen.getByText("First Golden Path hero case")).toBeInTheDocument();
    expect(screen.getAllByText(/How do low-level moisture/).length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Low-level humidity")).toBeInTheDocument();
    expect(screen.getByLabelText("Surface heating")).toBeInTheDocument();
    expect(screen.queryByText(/namelist/i)).not.toBeInTheDocument();
  });

  it("labels preview as not implemented and not CM1 output", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Preview estimate not implemented" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/guidance only/)).toBeInTheDocument();
    expect(screen.getByText(/not CM1 output/)).toBeInTheDocument();
    expect(screen.getByText(/not a completed result/)).toBeInTheDocument();
  });

  it("requests a dry-run package and displays generated files without claiming CM1 ran", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    const humidityControl = await screen.findByLabelText("Low-level humidity");
    await waitFor(() => {
      expect(humidityControl).toHaveValue("baseline");
    });
    fireEvent.change(humidityControl, {
      target: { value: "more_humid" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create run package" }));

    await waitFor(() => {
      expect(screen.getByText("/tmp/CloudChamber/runs/dry-run-001")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Packaged dry-run output")).toHaveLength(2);
    expect(screen.getByText("CM1 launched").nextElementSibling).toHaveTextContent("No");
    expect(screen.getByText("unknown until validated")).toBeInTheDocument();
    expect(screen.getByText("run_manifest.json")).toBeInTheDocument();
    expect(screen.getByText("input_sounding")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/dry-run-package",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("more_humid"),
      }),
    );
  });

  it("lists result cards in a table and shows notebook diagnostics", async () => {
    render(<App />);

    expect(await screen.findByRole("button", { name: "Results" })).toHaveClass("active-control");
    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(screen.getByLabelText("Selected result")).toHaveTextContent(
      "Quick-look shallow cumulus",
    );
    expect(screen.getAllByText("Validated quick-look baseline").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Minor caveat").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Open 3-D" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Quick-look shallow cumulus" })).toBeInTheDocument();
    expect(screen.getAllByText("Baseline Shallow Cumulus").length).toBeGreaterThan(0);
    expect(screen.getAllByText("quick look").length).toBeGreaterThan(0);
    expect(screen.getAllByText("cloud formed; rain detected").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("13 model files, 13 time steps, 1 stats files").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Cloud formed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Rain detected").length).toBeGreaterThan(0);
    expect(screen.getByText("1,800 s")).toBeInTheDocument();
    expect(screen.getByText("2.193e-3 kg/kg")).toBeInTheDocument();
    expect(screen.getByText("6.867 m/s")).toBeInTheDocument();
    expect(screen.getByText("-4.215 m/s")).toBeInTheDocument();
    expect(
      screen.getByText("CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"),
    ).toBeInTheDocument();
    expect(screen.getByText("Technical details")).toBeInTheDocument();
    expect(screen.getAllByText("Completed CM1 result").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Inspect fields" })).toBeEnabled();
  });

  it("compares baseline and dry failed results side by side", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Compare" }));

    expect(
      await screen.findByRole("heading", { name: "Baseline vs Dry Failed Cumulus" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Lab pair ready")).toBeInTheDocument();
    expect(screen.getByLabelText("Baseline result")).toHaveTextContent(
      "Baseline Shallow Cumulus",
    );
    expect(screen.getByLabelText("Dry Failed result")).toHaveTextContent("Dry Failed Cumulus");
    expect(screen.getAllByText("Cloud formed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No cloud formed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Rain detected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No rain detected").length).toBeGreaterThan(0);
    expect(screen.getByText("Moisture-limited")).toBeInTheDocument();
    expect(screen.getAllByText("Minor caveat").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2.193e-3 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.000e+0 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6.867 m/s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1.949 m/s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("-4.215 m/s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("-1.087 m/s").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Dry Failed Cumulus is not a failed model run/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Compare qc against w/)).toBeInTheDocument();
    expect(screen.getByText("Technical comparison details")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect Dry Failed" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Visualize Dry Failed" })).toBeInTheDocument();
  });

  it("opens inspect and visualize from comparison quick actions", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Compare" }));
    fireEvent.click(await screen.findByRole("button", { name: "Inspect Dry Failed" }));

    expect(await screen.findByRole("heading", { name: "Inspect fields" })).toBeInTheDocument();
    expect(screen.getByText("Dry Failed Cumulus quick-look")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Inspect CM1 fields" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-failed-cumulus/visualization/fields",
    );

    fireEvent.click(
      within(screen.getByRole("navigation", { name: "Cloud Chamber workspace" })).getByRole(
        "button",
        { name: "Compare" },
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Visualize Dry Failed" }));

    expect(await screen.findByRole("heading", { name: "3-D cloud view" })).toBeInTheDocument();
    expect(screen.getByText("Dry Failed Cumulus quick-look")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Scene shell" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-failed-cumulus/visualization/defaults",
    );
  });

  it("handles a missing dry failed comparison result", async () => {
    vi.mocked(fetch).mockImplementationOnce((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });
    vi.mocked(fetch).mockImplementationOnce((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ results: [resultCard] }), { status: 200 }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Compare" }));

    expect(
      await screen.findByRole("heading", {
        name: "Comparison needs Baseline and Dry Failed results",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Dry Failed Cumulus quick-look")).toBeInTheDocument();
  });

  it("supports name tag notes editing and save through the backend API", async () => {
    render(<App />);

    const nameInput = await screen.findByLabelText("Name");
    await waitFor(() => {
      expect(nameInput).toHaveValue("Quick-look shallow cumulus");
    });
    fireEvent.change(nameInput, {
      target: { value: "Saved notebook entry" },
    });
    fireEvent.change(screen.getByLabelText("Tags"), {
      target: { value: "baseline, notebook" },
    });
    fireEvent.change(screen.getByLabelText("Notes"), {
      target: { value: "Updated from the library." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Update notebook" }));

    await waitFor(() => {
      expect(screen.getByText("Result card updated")).toBeInTheDocument();
    });
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook",
      expect.objectContaining({
        method: "PATCH",
        body: expect.stringContaining("Saved notebook entry"),
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Save result" }));

    await waitFor(() => {
      expect(screen.getByText("Result card saved")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Saved").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook/save",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows missing diagnostics and warnings without field inspection UI", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));

    expect(screen.getAllByText("Diagnostics unavailable").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unknown").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No rain detected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText("missing_qc_field")).toBeInTheDocument();
    expect(screen.getByText("missing_w_field")).toBeInTheDocument();
    expect(screen.queryByText(/horizontal slice/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/vertical slice/i)).not.toBeInTheDocument();
  });

  it("opens the 2-D field inspector from a result and shows qc slices", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Inspect fields" }));

    expect(await screen.findByRole("heading", { name: "Inspect CM1 fields" })).toBeInTheDocument();
    await screen.findByText("Slices loaded");
    expect(screen.getByText(/browser is not parsing raw NetCDF/)).toBeInTheDocument();
    expect(screen.getByLabelText("Field")).toHaveValue("qc");
    expect(screen.getByText("qc (Cloud water)")).toBeInTheDocument();
    expect(screen.getAllByText("kg/kg").length).toBeGreaterThan(0);
    expect(screen.getByText("zh/yh/xh")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical X" })).toHaveClass("active-control");
    expect(screen.getByText("max_qc_native_grid_location")).toBeInTheDocument();
    expect(screen.getAllByText("Vertical X slice").length).toBeGreaterThan(0);
    expect(screen.queryByLabelText("Horizontal slice heatmap")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Vertical X slice heatmap")).toBeInTheDocument();
    expect(screen.getByLabelText("Vertical X slice color scale")).toBeInTheDocument();
    expect(screen.getAllByText("2.000e-5 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Technical slice details").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CM1-derived visualization-ready data/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Horizontal" }));

    expect(screen.getAllByText("Horizontal slice").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Horizontal slice heatmap")).toBeInTheDocument();
    expect(screen.getByText("Selected level: 0.8 km (800 m)")).toBeInTheDocument();
  });

  it("supports field and time selection through visualization-ready APIs", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Inspect fields" }));
    fireEvent.change(await screen.findByLabelText("Field"), { target: { value: "w" } });
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });

    await waitFor(() => {
      expect(screen.getByText("w (Vertical velocity)")).toBeInTheDocument();
    });
    expect(screen.getByText("zf/yh/xh")).toBeInTheDocument();
    expect(screen.getAllByText("900 s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6.5 m/s").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/results/result-dry-run-quicklook/visualization/slice?field=w"),
    );
  });

  it("handles missing fields and bad slice requests gracefully", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    fireEvent.click(screen.getByRole("button", { name: "Inspect fields" }));

    expect(await screen.findByRole("heading", { name: "Inspect CM1 fields" })).toBeInTheDocument();
    await screen.findByText("Slices loaded");
    expect(screen.getByLabelText("Field")).toHaveValue("w");
    expect(screen.queryByRole("option", { name: /qc/ })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Horizontal level"), { target: { value: "99" } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("level_index=99 is outside valid range");
    });
  });

  it("renders cloud-water point cloud in the 3-D visualizer", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);

    expect(await screen.findByRole("heading", { name: "Scene shell" })).toBeInTheDocument();
    await screen.findByText("Cloud-water point cloud loaded");
    expect(screen.getByLabelText("3-D scene container")).toBeInTheDocument();
    expect(screen.getByLabelText("Cloud-water point cloud")).toBeInTheDocument();
    expect(screen.getByLabelText("Domain bounding box")).toBeInTheDocument();
    expect(screen.getByText("domain floor")).toBeInTheDocument();
    expect(screen.getByText("height")).toBeInTheDocument();
    expect(screen.getByLabelText("Show slice planes")).not.toBeChecked();
    const scene = screen.getByLabelText("3-D scene container");
    expect(within(scene).queryByLabelText("Horizontal slice plane")).not.toBeInTheDocument();
    expect(within(scene).queryByLabelText("Vertical slice plane")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Orbit" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset camera" })).toBeInTheDocument();
    expect(screen.getByLabelText("Zoom")).toHaveValue("100");
    expect(screen.getByLabelText("Field")).toHaveValue("qc");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getByLabelText("Time")).toBeInTheDocument();
    expect(screen.getByText("thresholded_point_cloud")).toBeInTheDocument();
    expect(
      screen.getByText("Slice planes: native-grid JSON slices from the backend"),
    ).toBeInTheDocument();
    expect(screen.getByText("3 of 3")).toBeInTheDocument();
    expect(screen.getAllByText("1,800 s").length).toBeGreaterThan(0);
    expect(screen.getByText("2.000e-6 kg/kg to 8.000e-6 kg/kg")).toBeInTheDocument();
    expect(screen.getByText("Visualizer interpretation of CM1-derived output")).toBeInTheDocument();
    expect(
      screen.getByText("Processing method: native-grid thresholded point cloud"),
    ).toBeInTheDocument();
    expect(screen.getByText("Rendering method: thresholded point cloud")).toBeInTheDocument();
    expect(screen.getByText("No raw NetCDF parsing in the browser")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("time_index=2"));
  });

  it("supports qc and w slice planes synced to visualizer time", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findByText("Cloud-water point cloud loaded");

    const scene = screen.getByLabelText("3-D scene container");
    expect(within(scene).queryByLabelText("Horizontal slice plane")).not.toBeInTheDocument();
    expect(within(scene).queryByLabelText("Vertical slice plane")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Show slice planes"));
    expect(within(scene).getByLabelText("Horizontal slice plane")).toBeInTheDocument();
    expect(within(scene).getByLabelText("Vertical slice plane")).toBeInTheDocument();
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("Slice field"), { target: { value: "w" } });
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });

    await waitFor(() => {
      expect(screen.getAllByText("w (Vertical velocity)").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("900 s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6.5 m/s").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/results/result-dry-run-quicklook/visualization/slice?field=w"),
    );
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("time_index=1"));
  });

  it("uses view presets to switch time field and slice context", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findByText("Cloud-water point cloud loaded");

    fireEvent.click(screen.getByRole("button", { name: "Vertical cross-section" }));
    expect(screen.getByLabelText("Show slice planes")).toBeChecked();
    const scene = screen.getByLabelText("3-D scene container");
    await waitFor(() => {
      expect(within(scene).getByLabelText("Vertical slice plane")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Top-down slice" }));
    expect(screen.getByLabelText("Show slice planes")).toBeChecked();
    await waitFor(() => {
      expect(within(scene).getByLabelText("Horizontal slice plane")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Updraft view" }));
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByText("max_w_native_grid_location")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w"));
    });
  });

  it("updates and resets the 3-D scene shell camera controls", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findByText("Cloud-water point cloud loaded");

    fireEvent.click(screen.getByRole("button", { name: "Pan" }));
    fireEvent.change(screen.getByLabelText("Zoom"), { target: { value: "150" } });

    expect(screen.getByText("pan")).toBeInTheDocument();
    expect(screen.getByText("150%")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reset camera" }));

    expect(screen.getByText("orbit")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("updates cloud-water threshold opacity point size and time requests", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findByText("Cloud-water point cloud loaded");

    fireEvent.change(screen.getByLabelText("Threshold"), { target: { value: "1" } });

    await screen.findByText("No cloud water above threshold");
    expect(
      screen.getByText("No cloud water above the selected threshold at this time."),
    ).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("threshold=1"));

    fireEvent.change(screen.getByLabelText("Opacity"), { target: { value: "0.8" } });
    fireEvent.change(screen.getByLabelText("Point size"), { target: { value: "14" } });
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });

    expect(screen.getByText("0.8")).toBeInTheDocument();
    expect(screen.getByText("14px")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("time_index=1"));
    });
  });

  it("handles missing qc in the 3-D point-cloud renderer", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Open 3-D" })[0]);

    expect(await screen.findByRole("heading", { name: "Scene shell" })).toBeInTheDocument();
    await screen.findByText("Scene shell ready");
    expect(
      screen.getByText("Cloud water field qc is not available for this result."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Field")).toHaveValue("w");
    expect(screen.getByLabelText("Threshold")).toBeDisabled();
  });

  it("handles a 3-D scene shell result with no visualization-ready fields", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No visual fields" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Open 3-D" })[0]);

    expect(await screen.findByRole("heading", { name: "Scene shell" })).toBeInTheDocument();
    await screen.findByText("No fields available");
    expect(
      screen.getByText("No visualization-ready fields are available for this result."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Cloud water field qc is not available for this result."),
    ).toBeInTheDocument();
  });
});
