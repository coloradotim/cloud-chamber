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

const runningRunStatus = {
  run_id: "dry-run-001",
  lifecycle_state: "running",
  product_state: "queued_running_cm1_process",
  validation_status: "unvalidated",
  manifest_path: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
  command: ["/Users/timpeterson/cm1r21.1/run/cm1.exe"],
  stdout_log: "/tmp/CloudChamber/runs/dry-run-001/logs/stdout.log",
  stderr_log: "/tmp/CloudChamber/runs/dry-run-001/logs/stderr.log",
  stdout_tail: "CM1 started",
  stderr_tail: "",
  exit_code: null,
  started_at: "2026-05-22T15:15:36Z",
  finished_at: null,
  output_summary: {
    raw_cm1_artifacts: 0,
    netcdf_paths: 0,
    processed_artifacts: 0,
  },
  runtime_warnings: [],
};

const completedRunStatus = {
  ...runningRunStatus,
  lifecycle_state: "completed",
  product_state: "completed_cm1_result",
  validation_status: "valid",
  stdout_tail: "Program terminated normally",
  stderr_tail: "IEEE_INVALID_FLAG",
  exit_code: 0,
  finished_at: "2026-05-22T15:45:36Z",
  output_summary: {
    raw_cm1_artifacts: 0,
    netcdf_paths: 14,
    processed_artifacts: 0,
  },
  runtime_warnings: ["CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"],
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
  thermal_fate_label: "Growing cumulus",
  thermal_fate_confidence: "candidate",
  main_limiting_factor: "unknown",
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
  thermal_fate_label: "Thermal without cloud",
  thermal_fate_confidence: "supported",
  main_limiting_factor: "moisture",
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

const storageRuns = [
  {
    run_id: "dry-run-quicklook",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: null,
    lifecycle_state: "completed",
    validation_status: "valid",
    product_state: "completed_cm1_result",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:15:36Z",
    updated_at: "2026-05-22T15:45:36Z",
    saved: false,
    protected: false,
    output_artifact_count: 14,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 14,
      processed_artifacts: 0,
    },
    size_bytes: 852 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-quicklook",
    category: "completed_with_output",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-quicklook/run_manifest.json",
    manifest_error: null,
  },
  {
    run_id: "dry-run-saved",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "completed",
    validation_status: "valid",
    product_state: "completed_cm1_result",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:15:36Z",
    updated_at: "2026-05-22T15:45:36Z",
    saved: true,
    protected: true,
    output_artifact_count: 14,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 14,
      processed_artifacts: 0,
    },
    size_bytes: 200 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-saved",
    category: "saved_or_protected",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-saved/run_manifest.json",
    manifest_error: null,
  },
  {
    run_id: "dry-run-running",
    scenario_id: "dry-failed-cumulus",
    scenario_name: "Dry Failed Cumulus",
    lifecycle_state: "running",
    validation_status: "unvalidated",
    product_state: "queued_running_cm1_process",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:15:36Z",
    updated_at: "2026-05-22T15:45:36Z",
    saved: false,
    protected: false,
    output_artifact_count: 0,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 0,
      processed_artifacts: 0,
    },
    size_bytes: 20 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-running",
    category: "running",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-running/run_manifest.json",
    manifest_error: null,
  },
  {
    run_id: "orphan-folder",
    scenario_id: null,
    scenario_name: null,
    lifecycle_state: null,
    validation_status: null,
    product_state: null,
    run_size_preset: null,
    created_at: null,
    updated_at: null,
    saved: false,
    protected: false,
    output_artifact_count: 0,
    output_summary: {},
    size_bytes: 1024,
    path: "/tmp/CloudChamber/runs/orphan-folder",
    category: "missing_manifest",
    manifest_path: null,
    manifest_error: null,
  },
];

const storageInventoryResponse = {
  runtime_home: "/tmp/CloudChamber",
  runs_directory: "/tmp/CloudChamber/runs",
  total_size_bytes: 60 * 1024 ** 3,
  warning_threshold_bytes: 50 * 1024 ** 3,
  above_warning_threshold: true,
  warning_message:
    "Runtime storage is at or above the 50 GB warning threshold. Review largest_runs and use dry-run cleanup before deleting selected runs.",
  runs: storageRuns,
  largest_runs: storageRuns,
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
      selected_time_index: null,
      selected_time_seconds: null,
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
      selected_time_index: null,
      selected_time_seconds: null,
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

function selectedTimeDefaultsResponse(url: string) {
  const parsed = new URL(url, "http://localhost");
  const timeIndex = parsed.searchParams.get("time_index");
  if (timeIndex === null) return viewDefaultsResponse;
  return {
    ...viewDefaultsResponse,
    fields: {
      qc: {
        ...viewDefaultsResponse.fields.qc,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        horizontal_level_index: 1,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "selected_time_max_qc_native_grid_location",
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
      w: {
        ...viewDefaultsResponse.fields.w,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        horizontal_level_index: 2,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "selected_time_max_w_native_grid_location",
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
    },
    caveats: [
      "default_locations_are_native_grid_indices",
      "default_locations_are_selected_time_native_grid_indices",
    ],
  };
}

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
  levelIndex = 0,
}: {
  field?: "qc" | "w";
  orientation?: "horizontal" | "vertical_x" | "vertical_y";
  timeIndex?: number;
  levelIndex?: number;
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
      selected_index: levelIndex,
      selected_coordinate_value:
        orientation === "horizontal"
          ? ([0.4, 0.8, 1.2][levelIndex] ?? 0.8)
          : ([-3.2, 0, 3.2][levelIndex] ?? 0),
      level_units: orientation === "horizontal" ? "km" : null,
      level_coordinate_value:
        orientation === "horizontal" ? ([0.4, 0.8, 1.2][levelIndex] ?? 0.8) : null,
      level_meters:
        orientation === "horizontal" ? ([0.4, 0.8, 1.2][levelIndex] ?? 0.8) * 1000 : null,
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
    coordinate_extents: {
      xh: { min: -3.2, max: 3.2, units: "km" },
      yh: { min: -3.2, max: 3.2, units: "km" },
      zh: { min: 0.0, max: 3.0, units: "km" },
    },
    point_order: ["x", "y", "z", "value"],
    points: returnedPoints,
    stats: {
      source_count: returnedPoints.length,
      returned_count: returnedPoints.length,
      min_value: values.length ? Math.min(...values) : null,
      max_value: values.length ? Math.max(...values) : null,
      active_z_min: values.length ? Math.min(...returnedPoints.map((point) => point[2])) : null,
      active_z_max: values.length ? Math.max(...returnedPoints.map((point) => point[2])) : null,
      max_value_location: returnedPoints.length
        ? {
            x: returnedPoints[returnedPoints.length - 1][0],
            y: returnedPoints[returnedPoints.length - 1][1],
            z: returnedPoints[returnedPoints.length - 1][2],
            value: returnedPoints[returnedPoints.length - 1][3],
          }
        : null,
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

function selectedRegionResponse() {
  return {
    result_id: "result-dry-run-quicklook",
    run_id: "dry-run-quicklook",
    scenario_id: "baseline-shallow-cumulus",
    region: {
      region_type: "column",
      requested: {
        region_type: "column",
        x_index: 1,
        y_index: 0,
        neighborhood: 1,
      },
      x: {
        dimension: "xh",
        start_index: 0,
        end_index: 2,
        start_coordinate: -3.2,
        end_coordinate: 3.2,
        units: "km",
      },
      y: {
        dimension: "yh",
        start_index: 0,
        end_index: 1,
        start_coordinate: -3.2,
        end_coordinate: 0,
        units: "km",
      },
      vertical: {
        dimension: "zh",
        start_index: 0,
        end_index: 1,
        start_coordinate: 0.4,
        end_coordinate: 0.8,
        units: "km",
      },
      native_grid: "zh/yh/xh",
      cell_count: 12,
    },
    diagnostics: {
      available: true,
      local_max_w_m_s: 4.5,
      time_of_local_max_w_seconds: 1800,
      local_min_w_m_s: -1.2,
      time_of_local_min_w_seconds: 900,
      local_w_max_time_series: [
        { time_seconds: 0, value: 1.2 },
        { time_seconds: 900, value: 2.4 },
        { time_seconds: 1800, value: 4.5 },
      ],
      local_w_min_time_series: [
        { time_seconds: 0, value: -0.1 },
        { time_seconds: 900, value: -1.2 },
        { time_seconds: 1800, value: -0.7 },
      ],
      local_max_qc_kg_kg: 0.00002,
      time_of_local_max_qc_seconds: 1800,
      first_local_cloud_time_seconds: 900,
      local_cloud_fraction_time_series: [
        { time_seconds: 0, value: 0 },
        { time_seconds: 900, value: 0.25 },
        { time_seconds: 1800, value: 0.5 },
      ],
      local_qc_max_time_series: [
        { time_seconds: 0, value: 0 },
        { time_seconds: 900, value: 0.000006 },
        { time_seconds: 1800, value: 0.00002 },
      ],
      local_cloud_base_time_series: [],
      local_cloud_top_time_series: [],
      local_max_qc_height_time_series: [],
      local_max_w_height_time_series: [],
      local_rain_present: true,
      first_local_rain_time_seconds: 1800,
      local_max_qr_kg_kg: 0.000001,
      time_of_local_max_qr_seconds: 1800,
      local_qr_max_time_series: [{ time_seconds: 1800, value: 0.000001 }],
    },
    comparison_to_domain: {
      local_max_w_fraction_of_domain: 0.66,
      local_max_qc_fraction_of_domain: 0.91,
      local_first_cloud_time_delta_seconds: -900,
      local_cloud_top_fraction_of_domain: 0.78,
      local_first_rain_time_delta_seconds: 0,
      caveats: ["comparison_uses_global_result_summary"],
    },
    interpretation: {
      thermal_fate_label: "Growing cumulus",
      confidence: "candidate",
      main_limiting_factor: "unknown",
      summary:
        "Cloud water appeared locally after upward motion strengthened, then remained active.",
      caveats: ["selected_region_is_not_cloud_object_tracking"],
    },
    provenance: {
      ...provenance,
      processing_method: "backend_xarray_selected_region_diagnostics",
      rendering_method: "thermal_fate_inspector_summary",
      provenance_label:
        "CM1-derived selected-region diagnostics; native-grid summary; browser receives bounded payload only",
    },
    caveats: [
      "native_grid_region_summary_no_interpolation",
      "selected_region_is_not_cloud_object_tracking",
    ],
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
      if (url === "/api/runs/launch") {
        return Promise.resolve(new Response(JSON.stringify(runningRunStatus), { status: 200 }));
      }
      if (url.startsWith("/api/runs/status")) {
        return Promise.resolve(new Response(JSON.stringify(completedRunStatus), { status: 200 }));
      }
      if (url === "/api/results/ingest") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              result_id: "result-dry-run-quicklook",
              run_id: "dry-run-001",
              diagnostics_summary: "cloud formed; rain detected",
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      if (url === "/api/storage/delete-run" && init?.method === "POST") {
        const body = JSON.parse(String(init.body)) as { run_id: string; dry_run: boolean };
        if (body.run_id === "dry-run-running") {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "Refusing to delete running run" }), {
              status: 400,
            }),
          );
        }
        if (body.dry_run) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                run_id: body.run_id,
                run_directory: `/tmp/CloudChamber/runs/${body.run_id}`,
                dry_run: true,
                deleted: false,
                size_bytes: 852 * 1024 ** 2,
                message: "Dry run only; no files were deleted.",
              }),
              { status: 200 },
            ),
          );
        }
        return Promise.resolve(
          new Response(
            JSON.stringify({
              run_id: body.run_id,
              run_directory: `/tmp/CloudChamber/runs/${body.run_id}`,
              dry_run: false,
              deleted: true,
              size_bytes: 852 * 1024 ** 2,
              message: "Run directory deleted.",
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results/result-dry-run-quicklook/visualization/fields") {
        return Promise.resolve(new Response(JSON.stringify(fieldCatalogResponse), { status: 200 }));
      }
      if (url.startsWith("/api/results/result-dry-run-quicklook/visualization/defaults")) {
        return Promise.resolve(
          new Response(JSON.stringify(selectedTimeDefaultsResponse(url)), { status: 200 }),
        );
      }
      if (url === "/api/results/result-no-diagnostics/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(missingFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url.startsWith("/api/results/result-no-diagnostics/visualization/defaults")) {
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
      if (url.startsWith("/api/results/result-empty-visualizer/visualization/defaults")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({ ...viewDefaultsResponse, preferred_field: null, fields: {} }),
            {
              status: 200,
            },
          ),
        );
      }
      if (url === "/api/results/result-dry-failed-cumulus/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(dryFailedFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url.startsWith("/api/results/result-dry-failed-cumulus/visualization/defaults")) {
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
        const isDryFailed = parsed.pathname.includes("result-dry-failed-cumulus");
        return Promise.resolve(
          new Response(
            JSON.stringify(
              pointCloudResponse({
                threshold: Number(parsed.searchParams.get("threshold") ?? 0.000001),
                timeIndex: Number(parsed.searchParams.get("time_index") ?? 0),
                points: isDryFailed ? [] : undefined,
              }),
            ),
            { status: 200 },
          ),
        );
      }
      if (url.includes("/diagnostics/selected-region")) {
        if (url.includes("x_index=99")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "x_index=99 is outside valid range" }), {
              status: 400,
            }),
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify(selectedRegionResponse()), { status: 200 }),
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
                levelIndex: Number(parsed.searchParams.get("level_index") ?? 0),
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
  vi.useRealTimers();
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

  it("shows an explicit loading state before scenario package controls are available", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return new Promise<Response>(() => undefined);
      }
      if (url === "/api/results") {
        return new Promise<Response>(() => undefined);
      }
      if (url === "/api/storage/inventory") {
        return new Promise<Response>(() => undefined);
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Build" }));
    expect(screen.getByRole("heading", { name: "Loading scenario catalog" })).toBeInTheDocument();
    expect(screen.getByLabelText("Scenario")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Create run package" })).not.toBeInTheDocument();
  });

  it("shows a retryable scenario-loading failure state", async () => {
    let scenarioRequestCount = 0;
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        scenarioRequestCount += 1;
        if (scenarioRequestCount === 1) {
          return Promise.resolve(new Response("backend unavailable", { status: 503 }));
        }
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Scenario catalog unavailable" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/local backend/)).toBeInTheDocument();
    expect(screen.getByLabelText("Scenario")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Create run package" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry scenarios" }));

    expect(
      await screen.findByRole("heading", { name: "Baseline Shallow Cumulus" }),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Create run package" })).toBeEnabled();
    });
  });

  it("shows an empty scenario state without enabling package creation", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              golden_path_scenario_id: "",
              scenarios: [],
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "No scenarios available" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/did not return any scenario templates/)).toBeInTheDocument();
    expect(screen.getByLabelText("Scenario")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Create run package" })).not.toBeInTheDocument();
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
    expect(screen.getByTestId("create-package-btn")).toBeEnabled();
    fireEvent.click(screen.getByTestId("create-package-btn"));

    await waitFor(() => {
      expect(screen.getByText("/tmp/CloudChamber/runs/dry-run-001")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Packaged dry-run output").length).toBeGreaterThan(0);
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

  it("guides a local run from package launch through ingest actions", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.click(await screen.findByTestId("create-package-btn"));

    expect(await screen.findByText("dry-run-001")).toBeInTheDocument();
    expect(screen.getByTestId("package-review-panel")).toBeInTheDocument();
    expect(screen.getByText("Manifest path").nextElementSibling).toHaveTextContent(
      "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
    );
    expect(screen.getByText(/Expected diagnostics/)).toHaveTextContent("first_cloud_time");
    expect(screen.getByTestId("launch-cm1-btn")).toBeEnabled();
    expect(screen.getByTestId("refresh-status-btn")).toBeDisabled();
    expect(screen.getByTestId("ingest-results-btn")).toBeDisabled();

    fireEvent.click(screen.getByTestId("launch-cm1-btn"));

    await waitFor(() => {
      expect(screen.getAllByText("Running").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("stdout log").nextElementSibling).toHaveTextContent("stdout.log");
    expect(screen.getByText("CM1 started")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("refresh-status-btn"));

    await waitFor(() => {
      expect(screen.getAllByText("Completed CM1 result").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Output summary").nextElementSibling).toHaveTextContent("14 NetCDF");
    expect(screen.getAllByText(/IEEE_INVALID_FLAG/).length).toBeGreaterThan(0);
    expect(screen.getByTestId("ingest-results-btn")).toBeEnabled();

    fireEvent.click(screen.getByTestId("ingest-results-btn"));

    expect(await screen.findByText(/Result metadata created/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open in Results" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect fields" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open 3-D visualization" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/runs/launch",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/ingest",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          manifest_path: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
        }),
      }),
    );
  });

  it("shows an actionable launch failure when local CM1 settings are missing", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
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
      if (url === "/api/runs/launch" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "CM1 executable is missing. Missing: cm1.exe" }), {
            status: 400,
          }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.click(await screen.findByTestId("create-package-btn"));
    fireEvent.click(await screen.findByTestId("launch-cm1-btn"));

    expect(await screen.findByRole("alert")).toHaveTextContent("CM1 executable is missing");
    expect(screen.getByTestId("launch-cm1-btn")).toBeEnabled();
  });

  it("lists result cards as notebook entries and shows diagnostics", async () => {
    render(<App />);

    expect(await screen.findByRole("button", { name: "Results" })).toHaveClass("active-control");
    const topNav = screen.getByRole("navigation", { name: "Cloud Chamber workspace" });
    expect(within(topNav).getByRole("button", { name: "Build" })).toBeInTheDocument();
    expect(within(topNav).getByRole("button", { name: "Results" })).toBeInTheDocument();
    expect(within(topNav).getByRole("button", { name: "Explore" })).toBeInTheDocument();
    expect(within(topNav).queryByRole("button", { name: "Compare" })).not.toBeInTheDocument();
    expect(within(topNav).queryByRole("button", { name: "Storage" })).not.toBeInTheDocument();
    expect(within(topNav).queryByRole("button", { name: "Inspect" })).not.toBeInTheDocument();
    expect(within(topNav).queryByRole("button", { name: "Visualize" })).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Notebook" })).toHaveClass("active-control");
    expect(screen.getByRole("tab", { name: "Compare" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Storage" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(
      screen.getByText("Review saved cloud experiments, compare variants, and open results for explanation."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Results list")).toBeInTheDocument();
    const resultDetail = screen.getByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("Quick-look shallow cumulus");
    expect(screen.getAllByText(/Validated quick-look baseline/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Minor caveat/).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Open 3-D" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Quick-look shallow cumulus" })).toBeInTheDocument();
    expect(screen.getAllByText(/Baseline Shallow Cumulus/).length).toBeGreaterThan(0);
    expect(resultDetail).toHaveTextContent("quick look");
    expect(screen.getAllByText("cloud formed; rain detected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Cloud formed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Rain detected").length).toBeGreaterThan(0);
    expect(screen.getByText("1,800 s")).toBeInTheDocument();
    expect(screen.getByText("2.193e-3 kg/kg")).toBeInTheDocument();
    expect(screen.getByText("6.867 m/s")).toBeInTheDocument();
    expect(screen.getByText("-4.215 m/s")).toBeInTheDocument();
    fireEvent.click(within(resultDetail).getByText("Technical details"));
    expect(
      screen.getAllByText("13 model files, 13 time steps, 1 stats files").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Completed CM1 result").length).toBeGreaterThan(0);
    expect(within(resultDetail).getByRole("button", { name: "Open in Explore" })).toBeEnabled();
  });

  it("accepts legacy array results responses without crashing", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify([resultCard]), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Quick-look shallow cumulus" })).toBeInTheDocument();
    expect(screen.queryByText(/results is not iterable/i)).not.toBeInTheDocument();
  });

  it("shows a clean results load failure state for malformed results payloads", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "unexpected shape" }), { status: 200 }),
        );
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load results");
    expect(screen.getByText("No ingested CM1 results yet.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh results" })).toBeInTheDocument();
    expect(screen.queryByText(/results is not iterable/i)).not.toBeInTheDocument();
  });

  it("compares baseline and dry failed results side by side", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));

    expect(
      await screen.findByRole("heading", { name: "Baseline vs Dry Failed Cumulus" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Lab pair ready")).toBeInTheDocument();
    expect(screen.getByLabelText("Baseline result")).toHaveTextContent("Baseline Shallow Cumulus");
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
    expect(screen.getByText(/Dry Failed Cumulus is not a failed model run/)).toBeInTheDocument();
    expect(screen.getByText(/Compare qc against w/)).toBeInTheDocument();
    expect(screen.getByText("Technical comparison details")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open Dry Failed in Explore" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open Dry Failed 3-D" })).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Baseline vs Dry Failed slices" }),
    ).toBeInTheDocument();
    await screen.findByText("Comparison slices loaded");
    expect(screen.getByLabelText("Comparison field")).toHaveValue("qc");
    expect(screen.getByLabelText("Comparison time")).toHaveValue("2");
    expect(screen.getByLabelText("Baseline comparison slice")).toHaveTextContent(
      "Baseline Shallow Cumulus",
    );
    expect(screen.getByLabelText("Dry Failed comparison slice")).toHaveTextContent(
      "Dry Failed Cumulus",
    );
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByLabelText(/qc comparison heatmap/).length).toBe(2);
    expect(screen.getAllByText("Finite cells").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Non-finite cells").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CM1-derived visualization-ready data/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CM1-derived visualization-ready data/).length).toBeGreaterThan(0);
  });

  it("switches side-by-side field comparison from qc to w", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));
    await screen.findByText("Comparison slices loaded");

    fireEvent.change(screen.getByLabelText("Comparison field"), { target: { value: "w" } });
    fireEvent.click(screen.getByRole("button", { name: "Horizontal" }));
    fireEvent.change(screen.getByLabelText("Comparison time"), { target: { value: "1" } });

    await waitFor(() => {
      expect(screen.getAllByText("w (Vertical velocity)").length).toBeGreaterThan(0);
    });
    expect(screen.getByRole("button", { name: "Horizontal" })).toHaveClass("active-control");
    expect(screen.getAllByText("m/s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("900 s").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/results/result-dry-run-quicklook/visualization/slice?field=w"),
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/results/result-dry-failed-cumulus/visualization/slice?field=w"),
    );
  });

  it("opens inspect and visualize from comparison quick actions", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));
    fireEvent.click(await screen.findByRole("button", { name: "Open Dry Failed in Explore" }));

    expect(
      await screen.findByRole("tab", { name: "2-D Slices" }),
    ).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-failed-cumulus/visualization/fields",
    );

    fireEvent.click(
      within(screen.getByRole("navigation", { name: "Cloud Chamber workspace" })).getByRole(
        "button",
        { name: "Results" },
      ),
    );
    fireEvent.click(screen.getByRole("tab", { name: "Compare" }));
    fireEvent.click(screen.getByRole("button", { name: "Open Dry Failed 3-D" }));

    expect(
      await screen.findByRole("tab", { name: "2-D Slices" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "3-D View" })).toHaveClass("active-control");
    expect(screen.getAllByText("Dry Failed Cumulus quick-look").length).toBeGreaterThan(0);
    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
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

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));

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

  it("shows runtime storage inventory and safe cleanup affordances", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Storage" }));

    expect(
      await screen.findByRole("heading", { name: "Runtime storage cleanup" }),
    ).toBeInTheDocument();
    expect(screen.getByText("/tmp/CloudChamber")).toBeInTheDocument();
    expect(screen.getByText("60 GB")).toBeInTheDocument();
    expect(screen.getByText("50 GB")).toBeInTheDocument();
    expect(screen.getByText("At or above 50 GB warning threshold")).toBeInTheDocument();
    expect(screen.getByText(/dry-run cleanup/)).toBeInTheDocument();
    expect(screen.getAllByText("Quick-look shallow cumulus").length).toBeGreaterThan(0);
    expect(screen.getByText("dry-run-quicklook")).toBeInTheDocument();
    expect(screen.getByText("852 MB")).toBeInTheDocument();
    expect(
      screen.getAllByText("13 model files, 13 time steps, 1 stats files").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("saved or protected")).toBeInTheDocument();
    expect(screen.getByText("missing manifest")).toBeInTheDocument();

    const runtimeRuns = screen.getByLabelText("Runtime runs");
    const buttons = within(runtimeRuns).getAllByRole("button", { name: "Preview delete" });
    expect(buttons[0]).toBeEnabled();
    expect(buttons[1]).toBeDisabled();
    expect(buttons[2]).toBeDisabled();
    expect(
      screen.getByText("Saved/protected runs are not deleted from this UI."),
    ).toBeInTheDocument();
    expect(screen.getByText("Running runs cannot be deleted.")).toBeInTheDocument();

    fireEvent.click(buttons[0]);

    expect(await screen.findByRole("heading", { name: "Delete preview" })).toBeInTheDocument();
    expect(screen.getByText("Dry run only; no files were deleted.")).toBeInTheDocument();
    expect(screen.getAllByText("/tmp/CloudChamber/runs/dry-run-quicklook").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByRole("button", { name: "Confirm delete selected run" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/storage/delete-run",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          run_id: "dry-run-quicklook",
          dry_run: true,
          confirm: false,
          force_saved: false,
        }),
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Confirm delete selected run" }));

    expect(await screen.findByText(/Run directory deleted/)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/storage/delete-run",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          run_id: "dry-run-quicklook",
          dry_run: false,
          confirm: true,
          force_saved: false,
        }),
      }),
    );
  });

  it("shows cleanup failure details without deleting from unsafe UI paths", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      if (url === "/api/storage/delete-run" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "Refusing to delete outside runtime home" }), {
            status: 400,
          }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Storage" }));
    fireEvent.click((await screen.findAllByRole("button", { name: "Preview delete" }))[0]);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Refusing to delete outside runtime home",
    );
    expect(fetch).toHaveBeenCalledWith(
      "/api/storage/delete-run",
      expect.objectContaining({
        body: JSON.stringify({
          run_id: "dry-run-quicklook",
          dry_run: true,
          confirm: false,
          force_saved: false,
        }),
      }),
    );
  });

  it("opens the 2-D field inspector from a result and shows qc slices", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findByText("Slices loaded");
    expect(screen.getByLabelText("Field")).toHaveValue("qc");
    expect(screen.getByText("qc (Cloud water)")).toBeInTheDocument();
    expect(screen.getAllByText("kg/kg").length).toBeGreaterThan(0);
    expect(screen.getByText("zh/yh/xh")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical X" })).toHaveClass("active-control");
    expect(screen.getByText("max_qc_native_grid_location")).toBeInTheDocument();
    expect(screen.getAllByText("Vertical X slice").length).toBeGreaterThan(0);
    expect(screen.queryByLabelText("Horizontal slice heatmap")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Vertical X slice at y = .*Horizontal axis: x\. Vertical axis: height/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Move back" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Move forward" })).toBeInTheDocument();
    const verticalHeatmap = screen.getByLabelText("Vertical X slice heatmap");
    expect(verticalHeatmap).toBeInTheDocument();
    const colorScale = screen.getByLabelText("Vertical X slice color scale");
    expect(colorScale).toBeInTheDocument();
    expect(colorScale.querySelector(".heatmap-scale-cloud-water")).not.toBeNull();
    expect(
      Boolean(
        screen.getByLabelText("Field").compareDocumentPosition(verticalHeatmap) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ),
    ).toBe(true);
    expect(
      Boolean(
        verticalHeatmap.compareDocumentPosition(screen.getByText("Technical details")) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ),
    ).toBe(true);
    expect(screen.getAllByText("2.000e-5 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Technical slice details").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CM1-derived visualization-ready data/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Horizontal" }));

    expect(screen.getAllByText("Horizontal slice").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Horizontal slice heatmap")).toBeInTheDocument();
    expect(screen.getByText("Selected level: 0.8 km (800 m)")).toBeInTheDocument();
  });

  it("selects a slice region and renders backend Thermal Fate Inspector diagnostics", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    await screen.findByText("Slices loaded");

    const heatmap = screen.getByLabelText("Vertical X slice heatmap");
    fireEvent.click(within(heatmap).getByRole("button", { name: /row 1, column 2/i }));

    expect(await screen.findByText("Selected-region diagnostics loaded")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What happened here?" })).toBeInTheDocument();
    expect(screen.getAllByText("Growing cumulus").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Cloud water appeared locally after upward motion strengthened/),
    ).toBeInTheDocument();
    expect(screen.getByText("First local cloud time")).toBeInTheDocument();
    expect(screen.getByText("Local max qc")).toBeInTheDocument();
    expect(screen.getAllByText("2.000e-5 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getByText("Local max w")).toBeInTheDocument();
    expect(screen.getByText("4.5 m/s")).toBeInTheDocument();
    expect(screen.getByText("Local rain")).toBeInTheDocument();
    expect(screen.getAllByText("Rain detected").length).toBeGreaterThan(0);
    expect(screen.getByText("Technical details and provenance")).toBeInTheDocument();
    expect(screen.getByText(/backend xarray selected-region diagnostics/i)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/results/result-dry-run-quicklook/diagnostics/selected-region?region_type=column",
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Clear selection" }));

    expect(screen.getByText(/Select a spot or region in the visualization/)).toBeInTheDocument();
  });

  it("shows selected-region backend failures as actionable inspector errors", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url.includes("/visualization/fields")) {
        return Promise.resolve(new Response(JSON.stringify(fieldCatalogResponse), { status: 200 }));
      }
      if (url.includes("/visualization/defaults")) {
        return Promise.resolve(new Response(JSON.stringify(viewDefaultsResponse), { status: 200 }));
      }
      if (url.includes("/visualization/slice")) {
        return Promise.resolve(
          new Response(JSON.stringify(sliceResponse({ orientation: "vertical_x" })), {
            status: 200,
          }),
        );
      }
      if (url.includes("/diagnostics/selected-region")) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "Unsupported selected region." }), {
            status: 400,
          }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    await screen.findByText("Slices loaded");
    fireEvent.click(
      within(screen.getByLabelText("Vertical X slice heatmap")).getByRole("button", {
        name: /row 1, column 1/i,
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Unsupported selected region.");
    expect(screen.getByText("Selected-region request failed")).toBeInTheDocument();
  });

  it("supports field and time selection through visualization-ready APIs", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
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

  it("shows process-aware 2-D overlays with unavailable diagnostic groups caveated", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByText("Evidence")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Thermal Fate summary" })).toBeInTheDocument();
    expect(screen.getByText(/Growing cumulus/)).toBeInTheDocument();
    expect(screen.getAllByText("Candidate").length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("Process mode"), {
      target: { value: "moisture" },
    });

    expect(screen.getByRole("heading", { name: "Moisture / Saturation" })).toBeInTheDocument();
    expect(screen.getByText(/need qv\/RH or saturation-deficit fields/)).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText("moisture_unsupported_missing_fields")).toBeInTheDocument();
  });

  it("handles missing fields and bad slice requests gracefully", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findByText("Slices loaded");
    expect(screen.getByLabelText("Field")).toHaveValue("w");
    expect(screen.queryByRole("option", { name: /qc/ })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Horizontal level"), { target: { value: "99" } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("level_index=99 is outside valid range");
    });
  });

  it("opens a cloud-forming result in Explore with qc and w available in both views", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("tab", { name: "2-D Slices" }),
    ).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findByText("Slices loaded");
    expect(screen.getByRole("tab", { name: "2-D Slices" })).toBeInTheDocument();
    expect(screen.getByLabelText("Field")).toHaveValue("qc");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("option", { name: "w - Vertical velocity" }).length).toBeGreaterThan(
      0,
    );

    fireEvent.click(screen.getByRole("tab", { name: "3-D View" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud-water point cloud loaded");
    expect(screen.getByLabelText("Field")).toHaveValue("qc");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("option", { name: "w - Vertical velocity" }).length).toBeGreaterThan(
      0,
    );
  });

  it("opens Dry Failed as a no-cloud result with a useful w/updraft path", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));
    fireEvent.click(await screen.findByRole("button", { name: "Open Dry Failed 3-D" }));

    expect(
      await screen.findByRole("tab", { name: "2-D Slices" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "2-D Slices" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud view ready");
    expect(screen.getByLabelText("Field")).toHaveValue("w");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("option", { name: "w - Vertical velocity" }).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText("No cloud water formed in this result; vertical velocity is available."),
    ).toBeInTheDocument();
    expect(screen.getByText(/Use the vertical velocity field \(w\) to inspect the thermals/i))
      .toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "2-D Slices" }));
    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findByText("Slices loaded");
    expect(screen.getByLabelText("Field")).toHaveValue("w");
  });

  it("shows field-loading failures with retry instead of a permanent loading state", async () => {
    let fieldsAttempts = 0;
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      if (url === "/api/results/result-dry-run-quicklook/visualization/fields") {
        fieldsAttempts += 1;
        if (fieldsAttempts === 1) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "Visualization fields temporarily failed." }), {
              status: 503,
            }),
          );
        }
        return Promise.resolve(new Response(JSON.stringify(fieldCatalogResponse), { status: 200 }));
      }
      if (url.startsWith("/api/results/result-dry-run-quicklook/visualization/defaults")) {
        return Promise.resolve(
          new Response(JSON.stringify(selectedTimeDefaultsResponse(url)), { status: 200 }),
        );
      }
      if (url.includes("/visualization/slice")) {
        return Promise.resolve(
          new Response(JSON.stringify(sliceResponse({ orientation: "vertical_x" })), {
            status: 200,
          }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Visualization fields temporarily failed.",
    );
    expect(screen.getByText("Field inspection unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry loading fields" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry loading fields" }));

    expect(await screen.findByText("Slices loaded")).toBeInTheDocument();
    expect(screen.queryByText("Loading fields...")).not.toBeInTheDocument();
  });

  it("clears 3-D field-loading errors after retry succeeds", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let fieldsAttempts = 0;
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/results/result-dry-run-quicklook/visualization/fields") {
        fieldsAttempts += 1;
        if (fieldsAttempts === 1) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "Visualization fields temporarily failed." }), {
              status: 503,
            }),
          );
        }
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Visualization fields temporarily failed.",
    );

    fireEvent.click(screen.getByRole("button", { name: "Retry loading fields" }));

    await screen.findAllByText("Cloud-water point cloud loaded");
    await waitFor(() => {
      expect(screen.queryByText("Visualization fields temporarily failed.")).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders cloud-water point cloud in the 3-D visualizer", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud-water point cloud loaded");
    expect(screen.getByText("Cloud formed in this result")).toBeInTheDocument();
    expect(screen.queryByText("Cloud formed here")).not.toBeInTheDocument();
    expect(screen.getByLabelText("3-D scene container")).toBeInTheDocument();
    expect(screen.getByLabelText("Cloud-water point cloud")).toBeInTheDocument();
    expect(screen.getByLabelText("Domain bounding box")).toBeInTheDocument();
    expect(screen.getByText("domain floor")).toBeInTheDocument();
    expect(screen.getByText("height z")).toBeInTheDocument();
    expect(screen.getByLabelText("Show slice planes")).not.toBeChecked();
    const scene = screen.getByLabelText("3-D scene container");
    expect(screen.getByLabelText("Scientific visualization workbench")).toBeInTheDocument();
    expect(screen.getByLabelText("Primary visualizer controls")).toBeInTheDocument();
    expect(screen.getByLabelText("Fixed visualization viewport region")).toBeInTheDocument();
    expect(screen.getByLabelText("Timeline and slice controls")).toBeInTheDocument();
    expect(screen.getByLabelText("Visualization details")).toBeInTheDocument();
    const plottingGroup = within(scene).getByLabelText("Zoomable visualizer data layer");
    expect(plottingGroup).toBeInTheDocument();
    expect(within(plottingGroup).getByLabelText("Domain bounding box")).toBeInTheDocument();
    expect(within(plottingGroup).getByLabelText("Cloud-water point cloud")).toBeInTheDocument();
    expect(within(scene).getByLabelText("Scale markers")).toBeInTheDocument();
    expect(within(scene).getByLabelText("x-axis ticks")).toBeInTheDocument();
    expect(within(scene).getByLabelText("height-axis ticks")).toBeInTheDocument();
    expect(within(scene).getByLabelText("Active slice label")).toHaveTextContent(
      "horizontal z/height slice",
    );
    expect(screen.getByText("x: -3.2 km")).toBeInTheDocument();
    expect(screen.getByText("x: 0 km")).toBeInTheDocument();
    expect(screen.getByText("x: 3.2 km")).toBeInTheDocument();
    expect(screen.getByText("height: 0 km")).toBeInTheDocument();
    expect(screen.getByText("height: 1.5 km")).toBeInTheDocument();
    expect(screen.getByText("height: 3 km")).toBeInTheDocument();
    expect(screen.getByText("active cloud water: 0.8-1.2 km")).toBeInTheDocument();
    expect(within(scene).queryByLabelText("Horizontal slice plane")).not.toBeInTheDocument();
    expect(within(scene).queryByLabelText("Vertical slice plane")).not.toBeInTheDocument();
    expect(screen.getByText("Essential controls")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset view" })).toBeInTheDocument();
    fireEvent.click(screen.getByText("View and rendering controls"));
    expect(screen.queryByRole("button", { name: "Orbit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Pan" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reset camera" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Side x-z" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Side y-z" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Top-down x-y" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Oblique overview" })).toHaveClass("active-control");
    fireEvent.click(screen.getByText("Projection and rendering details"));
    expect(screen.getByLabelText("Projection description")).toHaveTextContent(
      "Oblique overview: interpretive overview based on CM1 coordinates, not a true perspective camera.",
    );
    expect(screen.getByLabelText("Zoom")).toHaveValue("100");
    expect(screen.getByLabelText("Field")).toHaveValue("qc");
    fireEvent.click(screen.getByText("Slice plane controls"));
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getByRole("button", { name: "Horizontal z" })).toHaveClass("active-control");
    fireEvent.click(screen.getByText("Evidence details"));
    expect(screen.getByLabelText("Explanation evidence")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Thermal Fate summary" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical x-z" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical y-z" })).toBeInTheDocument();
    expect(screen.getByLabelText("Height level (up/down)")).toHaveValue("1");
    expect(screen.getByLabelText("Time")).toBeInTheDocument();
    expect(screen.getByText("thresholded_point_cloud")).toBeInTheDocument();
    expect(screen.getAllByText("selected_time_max_qc_native_grid_location").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText("0 to 3 km")).toBeInTheDocument();
    expect(screen.getByText("0.8 km to 1.2 km")).toBeInTheDocument();
    expect(screen.getByText("x 2, y 1, z 1.2 km, value 8.000e-6")).toBeInTheDocument();
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
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook/visualization/defaults?time_index=2",
    );
  });

  it("supports qc and w slice planes synced to visualizer time", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    const scene = screen.getByLabelText("3-D scene container");
    expect(within(scene).queryByLabelText("Horizontal z slice plane")).not.toBeInTheDocument();
    expect(within(scene).queryByLabelText("Vertical x-z slice plane")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Show slice planes"));
    expect(within(scene).getByLabelText("Horizontal z slice plane")).toBeInTheDocument();
    expect(within(scene).queryByLabelText("Vertical x-z slice plane")).not.toBeInTheDocument();
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Move down" }));
    expect(screen.getByLabelText("Height level (up/down)")).toHaveValue("0");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("orientation=horizontal"));
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("level_index=0"));
    });

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z" }));
    expect(screen.getByRole("button", { name: "Vertical x-z" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Y position (forward/back)")).toHaveValue("1");
    expect(within(scene).queryByLabelText("Horizontal z slice plane")).not.toBeInTheDocument();
    expect(within(scene).getByLabelText("Vertical x-z slice plane")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Vertical y-z" }));
    expect(screen.getByRole("button", { name: "Vertical y-z" })).toHaveClass("active-control");
    expect(screen.getByLabelText("X position (left/right)")).toHaveValue("2");
    expect(screen.getByRole("button", { name: "Side y-z" })).toHaveClass("active-control");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("orientation=vertical_y"));
    });
    fireEvent.click(screen.getByRole("button", { name: "Move back" }));
    expect(screen.getByLabelText("X position (left/right)")).toHaveValue("1");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("level_index=1"));
    });

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
    await screen.findAllByText("Cloud-water point cloud loaded");

    fireEvent.click(screen.getByRole("button", { name: "Vertical cross-section" }));
    expect(screen.getByLabelText("Show slice planes")).toBeChecked();
    expect(screen.getByRole("button", { name: "Side x-z" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Projection description")).toHaveTextContent(
      "Side x-z: height is vertical",
    );
    const scene = screen.getByLabelText("3-D scene container");
    await waitFor(() => {
      expect(within(scene).getByLabelText("Vertical x-z slice plane")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Top-down slice" }));
    expect(screen.getByLabelText("Show slice planes")).toBeChecked();
    expect(screen.getByRole("button", { name: "Top-down x-y" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Projection description")).toHaveTextContent(
      "Top-down x-y: horizontal map view; height is not shown as vertical position.",
    );
    expect(within(scene).getByLabelText("y-axis ticks")).toBeInTheDocument();
    expect(within(scene).queryByLabelText("height-axis ticks")).not.toBeInTheDocument();
    await waitFor(() => {
      expect(within(scene).getByLabelText("Horizontal z slice plane")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Updraft view" }));
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByRole("button", { name: "Side y-z" })).toHaveClass("active-control");
    expect(screen.getByRole("button", { name: "Vertical y-z" })).toHaveClass("active-control");
    expect(screen.getAllByText(/max_w_native_grid_location/).length).toBeGreaterThan(0);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w"));
    });
  });

  it("updates and resets the 3-D scene shell view controls", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    const plottingGroup = screen.getByLabelText("Zoomable visualizer data layer");
    fireEvent.click(screen.getByRole("button", { name: "Side x-z" }));
    fireEvent.change(screen.getByLabelText("Zoom"), { target: { value: "150" } });

    expect(screen.getByRole("button", { name: "Side x-z" })).toHaveClass("active-control");
    expect(plottingGroup).toHaveStyle({ transform: "scale(1.5)" });
    expect(screen.getByText("150%")).toBeInTheDocument();
    expect(screen.getByText("zoom-only data-layer transform")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reset view" }));

    expect(screen.getByRole("button", { name: "Oblique overview" })).toHaveClass("active-control");
    expect(plottingGroup).toHaveStyle({ transform: "scale(1)" });
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("updates cloud-water threshold opacity point size and time requests", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open 3-D" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    fireEvent.change(screen.getByLabelText("Threshold"), { target: { value: "1" } });

    await screen.findAllByText("No cloud water above threshold");
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
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open 3-D" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud view ready");
    expect(
      screen.getByText("Cloud water field qc is not available for this result."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Field")).toHaveValue("w");
    expect(screen.getByLabelText("Threshold")).toBeDisabled();
  });

  it("handles a 3-D scene shell result with no visualization-ready fields", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No visual fields" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open 3-D" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("No fields available");
    expect(
      screen.getByText("No visualization-ready fields are available for this result."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Cloud water field qc is not available for this result."),
    ).toBeInTheDocument();
  });
});
