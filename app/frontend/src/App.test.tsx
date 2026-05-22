import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

const resultsResponse = {
  results: [resultCard, missingDiagnosticsCard],
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
      shape: [2, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "w",
      canonical_field_name: "vertical_velocity",
      display_name: "Vertical velocity",
      units: "m/s",
      dimensions: ["time", "zf", "yh", "xh"],
      shape: [2, 3, 2, 3],
      native_grid: "zf/yh/xh",
      coordinate_names: { time: "time", vertical: "zf", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
  ],
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
      ? timeIndex === 0
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
      time_seconds: timeIndex === 0 ? 0 : 900,
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
      max: field === "qc" ? (timeIndex === 0 ? 0.000008 : 0.00002) : 6.5,
      mean: field === "qc" ? 0.000004 : 4,
      finite_count: 5,
      non_finite_count: field === "qc" && timeIndex === 0 ? 1 : 0,
    },
    provenance,
    caveats: ["native_grid_view_no_interpolation", "json_numeric_slice_mvp"],
    units,
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
      if (url === "/api/results/result-no-diagnostics/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(missingFieldCatalogResponse), { status: 200 }),
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

    expect(
      await screen.findByRole("heading", { name: "Preview not implemented" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/guidance only/)).toBeInTheDocument();
    expect(screen.getByText(/not CM1 output/)).toBeInTheDocument();
    expect(screen.getByText(/not a completed result/)).toBeInTheDocument();
  });

  it("requests a dry-run package and displays generated files without claiming CM1 ran", async () => {
    render(<App />);

    fireEvent.change(await screen.findByLabelText("Low-level humidity"), {
      target: { value: "more_humid" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create dry-run package" }));

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

    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Quick-look shallow cumulus" })).toBeInTheDocument();
    expect(screen.getAllByText("Baseline Shallow Cumulus").length).toBeGreaterThan(0);
    expect(screen.getAllByText("quick look").length).toBeGreaterThan(0);
    expect(screen.getAllByText("cloud formed; rain detected").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("13 model files, 13 time steps, 1 stats files").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Cloud formed")).toBeInTheDocument();
    expect(screen.getByText("Rain detected")).toBeInTheDocument();
    expect(screen.getByText("1,800 s")).toBeInTheDocument();
    expect(screen.getByText("2.193e-3 kg/kg")).toBeInTheDocument();
    expect(screen.getByText("6.867 m/s")).toBeInTheDocument();
    expect(screen.getByText("-4.215 m/s")).toBeInTheDocument();
    expect(
      screen.getByText("CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"),
    ).toBeInTheDocument();
    expect(screen.getByText("source_model:CM1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect fields" })).toBeEnabled();
  });

  it("supports name tag notes editing and save through the backend API", async () => {
    render(<App />);

    fireEvent.change(await screen.findByLabelText("Name"), {
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
    expect(screen.getAllByText("Saved / protected").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook/save",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows missing diagnostics and warnings without field inspection UI", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));

    expect(screen.getAllByText("Diagnostics unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
    expect(screen.getByText("No rain detected")).toBeInTheDocument();
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
    expect(screen.getAllByText("Horizontal slice").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Vertical slice").length).toBeGreaterThan(0);
    expect(screen.getAllByText("8.000e-6 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1").length).toBeGreaterThan(0);
    expect(screen.getByText("Selected level: 0.8 km (800 m)")).toBeInTheDocument();
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CM1-derived visualization-ready data/).length).toBeGreaterThan(0);
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
});
