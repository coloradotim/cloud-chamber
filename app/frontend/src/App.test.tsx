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
  time_of_max_qc_seconds: 2700,
  max_w_m_s: 6.866957187652588,
  time_of_max_w_seconds: 3600,
  min_w_m_s: -4.21529483795166,
  time_of_min_w_seconds: 4500,
  rain_present: true,
  first_rain_time_seconds: 5400,
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
  time_of_max_qc_seconds: null,
  max_w_m_s: 1.949130654335022,
  time_of_max_w_seconds: 3600,
  min_w_m_s: -1.0865488052368164,
  time_of_min_w_seconds: 4500,
  rain_present: false,
  first_rain_time_seconds: null,
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
  time_of_max_qc_seconds: null,
  max_w_m_s: null,
  time_of_max_w_seconds: null,
  min_w_m_s: null,
  time_of_min_w_seconds: null,
  rain_present: false,
  first_rain_time_seconds: null,
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
    run_id: "dry-run-packaged",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "packaged",
    validation_status: "valid",
    product_state: "packaged_dry_run_output",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:55:36Z",
    updated_at: "2026-05-22T16:05:36Z",
    saved: false,
    protected: false,
    output_artifact_count: 0,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 0,
      processed_artifacts: 0,
    },
    size_bytes: 12 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-packaged",
    category: "dry_run_only",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-packaged/run_manifest.json",
    manifest_error: null,
  },
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
    run_id: "dry-run-uningested",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "completed",
    validation_status: "valid",
    product_state: "completed_cm1_result",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:20:36Z",
    updated_at: "2026-05-22T15:50:36Z",
    saved: false,
    protected: false,
    output_artifact_count: 14,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 14,
      processed_artifacts: 0,
    },
    size_bytes: 300 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-uningested",
    category: "completed_with_output",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-uningested/run_manifest.json",
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
    run_id: "dry-run-no-output",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "completed",
    validation_status: "valid",
    product_state: "process_completed_no_output",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:14:36Z",
    updated_at: "2026-05-22T15:20:36Z",
    saved: false,
    protected: false,
    output_artifact_count: 0,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 0,
      processed_artifacts: 0,
    },
    size_bytes: 10 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-no-output",
    category: "completed_no_output",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-no-output/run_manifest.json",
    manifest_error: null,
  },
  {
    run_id: "dry-run-failed",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "failed",
    validation_status: "invalid",
    product_state: "failed_canceled_cm1_run",
    run_size_preset: "quick_look",
    created_at: "2026-05-22T15:10:36Z",
    updated_at: "2026-05-22T15:12:36Z",
    saved: false,
    protected: false,
    output_artifact_count: 0,
    output_summary: {
      raw_cm1_artifacts: 0,
      netcdf_paths: 0,
      processed_artifacts: 0,
    },
    size_bytes: 9 * 1024 ** 2,
    path: "/tmp/CloudChamber/runs/dry-run-failed",
    category: "failed",
    manifest_path: "/tmp/CloudChamber/runs/dry-run-failed/run_manifest.json",
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
        region_type: "point",
        x_index: 32,
        y_index: 16,
        z_index: 15,
        neighborhood: 0,
      },
      x: {
        dimension: "xh",
        start_index: 32,
        end_index: 32,
        start_coordinate: 0.05000000074505806,
        end_coordinate: 0.05000000074505806,
        units: "km",
      },
      y: {
        dimension: "yh",
        start_index: 16,
        end_index: 16,
        start_coordinate: -1.5500000715255737,
        end_coordinate: -1.5500000715255737,
        units: "km",
      },
      vertical: {
        dimension: "zh",
        start_index: 15,
        end_index: 15,
        start_coordinate: 0.6200000476838716,
        end_coordinate: 0.6200000476838716,
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

function downsampledCloudSliceResponse() {
  const base = sliceResponse({ field: "qc", orientation: "horizontal", timeIndex: 1, levelIndex: 1 });
  const values = Array.from({ length: 64 }, () => Array.from({ length: 64 }, () => 0));
  values[0][1] = 0.000005;
  values[0][2] = 0.000002;
  return {
    ...base,
    values,
    shape: [64, 64],
    stats: {
      min: 0,
      max: 0.000005,
      mean: 0.0000000017,
      finite_count: 4096,
      non_finite_count: 0,
    },
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
  it("renders guided Build setup with extensible experiment metadata", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Build and run a CM1 experiment" }),
    ).toBeInTheDocument();
    expect(
      (await screen.findAllByRole("heading", { name: "Baseline Shallow Cumulus" })).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Guided local CM1 experiment")).toBeInTheDocument();
    expect(screen.getAllByText(/How do low-level moisture/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Experiment setup summary" })).toBeInTheDocument();
    expect(screen.getByText("Expected outcome").nextElementSibling).toHaveTextContent(
      "Clouds may form after heating and mixing",
    );
    expect(screen.getByText("What changes").nextElementSibling).toHaveTextContent(
      "Low-level humidity, Surface heating",
    );
    expect(screen.getByText("What stays controlled").nextElementSibling).toHaveTextContent("CM1");
    expect(screen.getByLabelText("Low-level humidity")).toBeInTheDocument();
    expect(screen.getByLabelText("Surface heating")).toBeInTheDocument();
    expect(screen.getAllByText(/Selected: Baseline/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Expected runtime: roughly 10-20 minutes/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Local run launchpad" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Packages, runs, and results" })).toBeInTheDocument();
    expect(screen.getAllByText("Not packaged yet").length).toBeGreaterThan(0);
    expect(screen.getByText("No package has been created from the current setup in this browser session.")).toBeInTheDocument();
    expect(screen.getByText("Local experiment pipeline")).toBeInTheDocument();
    expect(screen.queryByText("namelist.input")).not.toBeInTheDocument();
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
    expect(screen.getByLabelText("Experiment")).toBeDisabled();
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
    expect(screen.getByLabelText("Experiment")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Create run package" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry scenarios" }));

    expect(
      (await screen.findAllByRole("heading", { name: "Baseline Shallow Cumulus" })).length,
    ).toBeGreaterThan(0);
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
    expect(screen.getByLabelText("Experiment")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Create run package" })).not.toBeInTheDocument();
  });

  it("shows the local run workflow before package creation", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Local run launchpad" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Local experiment loop")).toBeInTheDocument();
    expect(screen.getByText("Local experiment pipeline")).toBeInTheDocument();
    expect(screen.getByText("Packages, runs, and results")).toBeInTheDocument();
    expect(screen.getByText("Ready to launch")).toBeInTheDocument();
    expect(screen.getAllByText("Ready to ingest").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Saved/protected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Running").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Launch package" })).toBeInTheDocument();
    expect(screen.getByTestId("create-package-btn")).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Create run package" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Open Storage cleanup" })).toBeInTheDocument();
    expect(screen.queryByTestId("create-package-next-btn")).not.toBeInTheDocument();
    expect(screen.queryByText(/Preview estimate not implemented/)).not.toBeInTheDocument();
  });

  it("can move completed local output from the Build pipeline into result ingest", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.click(await screen.findByRole("button", { name: "Ingest output" }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/results/ingest",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            manifest_path: "/tmp/CloudChamber/runs/dry-run-uningested/run_manifest.json",
          }),
        }),
      );
    });
    expect(await screen.findByText(/Result metadata created/)).toBeInTheDocument();
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
      expect(screen.getAllByText("/tmp/CloudChamber/runs/dry-run-001").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("Package ready").length).toBeGreaterThan(0);
    expect(screen.getByText("Latest generated package")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create another package" })).toBeInTheDocument();
    expect(screen.getByText("Expected output directory").nextElementSibling).toHaveTextContent(
      "/tmp/CloudChamber/runs/dry-run-001",
    );
    expect(screen.getByText("Generated inputs").nextElementSibling).toHaveTextContent(
      "namelist.input, input_sounding",
    );
    expect(screen.getByText("Current lifecycle state").nextElementSibling).toHaveTextContent(
      "Package ready",
    );
    expect(screen.getByText(/not a completed CM1 result/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Technical package details"));
    expect(screen.getByText("CM1 launched").nextElementSibling).toHaveTextContent("No");
    expect(screen.getByText("Cost / size").nextElementSibling).toHaveTextContent(
      "unknown until validated",
    );
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
    fireEvent.click(screen.getByText("Technical package details"));
    expect(screen.getByText("Expected diagnostics").nextElementSibling).toHaveTextContent(
      "first_cloud_time",
    );
    expect(screen.getByTestId("launch-cm1-btn")).toBeEnabled();
    expect(screen.queryByTestId("ingest-results-btn")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("launch-cm1-btn"));

    await waitFor(() => {
      expect(screen.getAllByText("Running").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("stdout log").nextElementSibling).toHaveTextContent("stdout.log");
    expect(screen.getByText("CM1 started")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "View status / logs" }));

    await waitFor(() => {
      expect(screen.getAllByText("Completed CM1 result").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Output summary").nextElementSibling).toHaveTextContent("14 NetCDF");
    expect(screen.getAllByText(/IEEE_INVALID_FLAG/).length).toBeGreaterThan(0);
    expect(screen.getByTestId("ingest-results-btn")).toBeEnabled();

    fireEvent.click(screen.getByTestId("ingest-results-btn"));

    expect(await screen.findByText(/Result metadata created/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open in Results" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Open in Explore" }).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Ingested").length).toBeGreaterThan(0);
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
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
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
    const packageReview = screen.getByTestId("package-review-panel");
    expect(packageReview).toHaveTextContent("Package ready");
    expect(packageReview).toHaveTextContent("/tmp/CloudChamber/runs/dry-run-001");
    expect(packageReview).toHaveTextContent(
      "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
    );
    expect(screen.getByText("Current lifecycle state").nextElementSibling).toHaveTextContent(
      "Package ready",
    );
    expect(screen.queryByLabelText("Local run status")).not.toBeInTheDocument();
    expect(screen.getByTestId("launch-cm1-btn")).toBeEnabled();
    fireEvent.click(screen.getByText("Technical package details"));
    expect(screen.getByText("CM1 launched").nextElementSibling).toHaveTextContent("No");
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
    expect(screen.getAllByRole("button", { name: "Open in Explore" }).length).toBeGreaterThan(0);
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

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Shared Explore controls")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
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
    fireEvent.click(screen.getByRole("button", { name: "Open Dry Failed in Explore" }));

    expect(screen.getAllByText("Dry Failed Cumulus quick-look").length).toBeGreaterThan(0);
    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    expect(screen.getByLabelText("3-D scene container")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
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

  it("shows missing diagnostics and warnings without exposing Explore slice controls in Results", async () => {
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
    expect(screen.getByText("dry run only")).toBeInTheDocument();
    expect(screen.getByText("completed no output")).toBeInTheDocument();
    expect(screen.getAllByText("failed").length).toBeGreaterThan(0);
    expect(screen.getByText("missing manifest")).toBeInTheDocument();

    const runtimeRuns = screen.getByLabelText("Runtime runs");
    const packageRow = within(runtimeRuns).getByText("dry-run-packaged").closest("tr");
    const savedRow = within(runtimeRuns).getByText("dry-run-saved").closest("tr");
    const runningRow = within(runtimeRuns).getByText("dry-run-running").closest("tr");
    expect(packageRow).not.toBeNull();
    expect(savedRow).not.toBeNull();
    expect(runningRow).not.toBeNull();
    expect(within(packageRow as HTMLElement).getByRole("button", { name: "Preview delete" })).toBeEnabled();
    expect(within(savedRow as HTMLElement).getByRole("button", { name: "Preview delete" })).toBeDisabled();
    expect(within(runningRow as HTMLElement).getByRole("button", { name: "Preview delete" })).toBeDisabled();
    expect(
      screen.getByText("Saved/protected runs are not deleted from this UI."),
    ).toBeInTheDocument();
    expect(screen.getByText("Running runs cannot be deleted.")).toBeInTheDocument();

    fireEvent.click(within(packageRow as HTMLElement).getByRole("button", { name: "Preview delete" }));

    expect(await screen.findByRole("heading", { name: "Delete preview" })).toBeInTheDocument();
    expect(screen.getByText("Dry run only; no files were deleted.")).toBeInTheDocument();
    expect(screen.getAllByText("/tmp/CloudChamber/runs/dry-run-packaged").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByRole("button", { name: "Confirm delete selected run" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/storage/delete-run",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          run_id: "dry-run-packaged",
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
          run_id: "dry-run-packaged",
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
          run_id: "dry-run-packaged",
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
    expect(await screen.findByLabelText("Shared Explore controls")).toBeInTheDocument();
    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("kg/kg").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Horizontal layer" })).toHaveClass("active-control");
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    expect(screen.getAllByText(/Horizontal layer at z = /).length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Move down" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Move up" })).toBeInTheDocument();
    const horizontalHeatmap = screen.getByLabelText(/Horizontal layer at z = .* heatmap/);
    expect(horizontalHeatmap).toBeInTheDocument();
    const colorScale = screen.getByLabelText(/Horizontal layer at z = .* color scale/);
    expect(colorScale).toBeInTheDocument();
    expect(colorScale.querySelector(".heatmap-scale-cloud-water")).not.toBeNull();
    expect(
      Boolean(
        screen.getByLabelText("Slice field").compareDocumentPosition(horizontalHeatmap) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ),
    ).toBe(true);
    expect(
      Boolean(
        horizontalHeatmap.compareDocumentPosition(screen.getByText("Technical slice details")) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ),
    ).toBe(true);
    expect(screen.getAllByText("2.000e-5 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Technical slice details").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CM1-derived visualization-ready data/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z slice" }));

    expect(screen.getByRole("button", { name: "Vertical x-z slice" })).toHaveClass(
      "active-control",
    );
    expect(screen.getByRole("img", { name: /Vertical x-z slice at y = .* heatmap/ })).toBeInTheDocument();
  });

  it("selects a slice region and renders backend Thermal Fate Inspector diagnostics", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    await screen.findByText("Slice synced");

    const heatmap = screen.getAllByRole("img", { name: /heatmap/i })[0];
    fireEvent.click(within(heatmap).getByRole("button", { name: /row 1, column 2/i }));

    expect(await screen.findByText("Selected-point diagnostics loaded")).toBeInTheDocument();
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
    expect(screen.getAllByText("xh[32]; 0.05 km").length).toBeGreaterThan(0);
    expect(screen.getAllByText("yh[16]; -1.55 km").length).toBeGreaterThan(0);
    expect(screen.getAllByText("zh[15]; 0.62 km").length).toBeGreaterThan(0);
    expect(screen.queryByText(/0\.05000000074505806/)).not.toBeInTheDocument();
    expect(screen.queryByText(/-1\.5500000715255737/)).not.toBeInTheDocument();
    expect(screen.getByText("Technical details and provenance")).toBeInTheDocument();
    expect(screen.getByText(/backend xarray selected-region diagnostics/i)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/results/result-dry-run-quicklook/diagnostics/selected-region?region_type=point",
      ),
    );

  });

  it("selects the source grid point represented by a downsampled cloud-water block", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/visualization/slice")) {
        return Promise.resolve(
          new Response(JSON.stringify(downsampledCloudSliceResponse()), { status: 200 }),
        );
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    await screen.findByText("Slice synced");

    const heatmap = screen.getAllByRole("img", { name: /heatmap/i })[0];
    fireEvent.click(
      within(heatmap).getByRole("button", {
        name: "Inspect Horizontal layer at z = 0.8 km row 1, column 1",
      }),
    );

    expect(await screen.findByText("Selected-point diagnostics loaded")).toBeInTheDocument();
    const selectedPoint = screen.getByLabelText("Selected point context");
    expect(within(selectedPoint).getByText("5.000e-6 kg/kg")).toBeInTheDocument();
    expect(within(selectedPoint).queryByText("0 kg/kg")).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("x_index=1&y_index=0&z_index=1"),
    );
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
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      if (url.includes("/visualization/fields")) {
        return Promise.resolve(new Response(JSON.stringify(fieldCatalogResponse), { status: 200 }));
      }
      if (url.includes("/visualization/defaults")) {
        return Promise.resolve(
          new Response(JSON.stringify(selectedTimeDefaultsResponse(url)), { status: 200 }),
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
    await screen.findByText("Slice synced");
    fireEvent.click(
      within(screen.getAllByRole("img", { name: /heatmap/i })[0]).getByRole("button", {
        name: /row 1, column 1/i,
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Unsupported selected region.");
    expect(screen.getByText("Selected-point request failed")).toBeInTheDocument();
  });

  it("supports field and time selection through visualization-ready APIs", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    fireEvent.change(await screen.findByLabelText("Slice field"), { target: { value: "w" } });
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });

    await waitFor(() => {
      expect(screen.getByText("w (Vertical velocity)")).toBeInTheDocument();
    });
    expect(screen.getAllByText("900 s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6.5 m/s").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/results/result-dry-run-quicklook/visualization/slice?field=w"),
    );
  });

  it("keeps process-aware evidence available behind technical controls", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud-water point cloud loaded");
    expect(screen.getByText("Result explanation")).toBeInTheDocument();
    expect(screen.getAllByText(/Cloud water formed in the validated quick-look baseline/).length)
      .toBeGreaterThan(0);

    fireEvent.click(screen.getByText("Evidence details"));
    fireEvent.change(screen.getByLabelText("Process mode"), {
      target: { value: "moisture" },
    });

    expect(screen.getByLabelText("Process mode")).toHaveValue("moisture");
  });

  it("handles missing qc fields without treating no-qc as a broken Explore state", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.queryByRole("option", { name: /qc/ })).not.toBeInTheDocument();
    expect(screen.getByLabelText("3-D scene container")).toBeInTheDocument();
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
  });

  it("opens a cloud-forming result in Explore with qc and w available in both views", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("3-D scene container")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("option", { name: "w - Vertical velocity" }).length).toBeGreaterThan(
      0,
    );

    await screen.findAllByText("Cloud-water point cloud loaded");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("option", { name: "w - Vertical velocity" }).length).toBeGreaterThan(
      0,
    );
  });

  it("opens Dry Failed as a no-cloud result with a useful w/updraft path", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));
    fireEvent.click(await screen.findByRole("button", { name: "Open Dry Failed in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud view ready");
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("option", { name: "w - Vertical velocity" }).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText("No cloud water formed in this result; vertical velocity is available."),
    ).toBeInTheDocument();
    expect(screen.getByText(/Use the vertical velocity field \(w\) to inspect the thermals/i))
      .toBeInTheDocument();

    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
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
    expect(screen.getAllByText("Scene unavailable").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Retry loading fields" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry loading fields" }));

    expect(await screen.findByText("Slice synced")).toBeInTheDocument();
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

    fireEvent.click((await screen.findAllByRole("button", { name: "Open in Explore" }))[0]);

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

  it("renders cloud-water context in unified Explore", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open in Explore" }))[0]);

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud-water point cloud loaded");
    expect(screen.getByText("Cloud formed in this result")).toBeInTheDocument();
    expect(screen.queryByText("Cloud formed here")).not.toBeInTheDocument();
    expect(screen.getByLabelText("3-D scene container")).toBeInTheDocument();
    expect(screen.getByLabelText("Cloud-water point cloud")).toBeInTheDocument();
    expect(screen.getByText("domain floor")).toBeInTheDocument();
    expect(screen.getByText("height z")).toBeInTheDocument();
    const scene = screen.getByLabelText("3-D scene container");
    expect(screen.getByLabelText("Scientific visualization workbench")).toBeInTheDocument();
    expect(screen.getByLabelText("Fixed visualization viewport region")).toBeInTheDocument();
    expect(screen.getByLabelText("Visualization details")).toBeInTheDocument();
    expect(screen.getByLabelText("Shared Explore controls")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    const plottingGroup = within(scene).getByLabelText("Zoomable visualizer data layer");
    expect(plottingGroup).toBeInTheDocument();
    expect(within(scene).queryByLabelText("Domain bounding box")).not.toBeInTheDocument();
    expect(within(scene).getByLabelText("Domain axes")).toBeInTheDocument();
    expect(within(plottingGroup).getByLabelText("Cloud-water point cloud")).toBeInTheDocument();
    expect(within(scene).getByLabelText("Scale markers")).toBeInTheDocument();
    expect(within(scene).queryByLabelText("Slice orientation anchors")).not.toBeInTheDocument();
    expect(within(scene).getByLabelText("x-axis ticks")).toBeInTheDocument();
    expect(within(scene).getByLabelText("height-axis ticks")).toBeInTheDocument();
    expect(within(scene).getByLabelText(/Horizontal layer at z = /)).toBeInTheDocument();
    expect(screen.getByText("x: -3.2 km")).toBeInTheDocument();
    expect(screen.getByText("x: 0 km")).toBeInTheDocument();
    expect(screen.getByText("x: 3.2 km")).toBeInTheDocument();
    expect(screen.getByText("height: 0 km")).toBeInTheDocument();
    expect(screen.getByText("height: 1.5 km")).toBeInTheDocument();
    expect(screen.getByText("height: 3 km")).toBeInTheDocument();
    expect(screen.getByText("active cloud water: 0.8-1.2 km")).toBeInTheDocument();
    expect(screen.getByLabelText(/Horizontal layer at z = .* heatmap/)).toBeInTheDocument();
    expect(within(scene).queryByLabelText("Vertical slice plane")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset view" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Orbit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Pan" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reset camera" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Side x-z" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Side y-z" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Top-down" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Oblique" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Projection description")).toHaveTextContent(
      "Oblique overview: interpretive overview based on CM1 coordinates, not a true perspective camera.",
    );
    expect(screen.getByRole("slider", { name: "Zoom" })).toHaveValue("100");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getByRole("button", { name: "Horizontal layer" })).toHaveClass("active-control");
    expect(screen.getByRole("button", { name: "Vertical x-z slice" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toBeInTheDocument();
    expect(screen.getByLabelText("Time")).toBeInTheDocument();
    expect(screen.getByLabelText("Show slice plane")).toBeChecked();
    expect(screen.getByLabelText(/orientation map/i)).toBeInTheDocument();
    expect(screen.getAllByText("x -3.2 km").length).toBeGreaterThan(0);
    expect(screen.getAllByText("x 3.2 km").length).toBeGreaterThan(0);
    expect(screen.getAllByText("y -3.2 km").length).toBeGreaterThan(0);
    expect(screen.getAllByText("y 3.2 km").length).toBeGreaterThan(0);
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

  it("supports qc and w slice planes synced to Explore time", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open in Explore" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    const scene = screen.getByLabelText("3-D scene container");
    expect(within(scene).getByLabelText(/Horizontal layer at z = /)).toBeInTheDocument();
    expect(within(scene).queryByLabelText(/Vertical x-z slice at y = /)).not.toBeInTheDocument();
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Move down" }));
    expect(screen.getByLabelText("Slice position")).toHaveValue("0");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("orientation=horizontal"));
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("level_index=0"));
    });

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z slice" }));
    expect(screen.getByRole("button", { name: "Vertical x-z slice" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
    expect(within(scene).queryByLabelText(/Horizontal layer at z = /)).not.toBeInTheDocument();
    expect(within(scene).getByLabelText(/Vertical x-z slice at y = /)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Vertical y-z slice" }));
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Side y-z" })).toHaveClass("active-control");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("orientation=vertical_y"));
    });
    fireEvent.click(screen.getByRole("button", { name: "Move back" }));
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

  it("uses shared controls to switch projection, field, and slice context", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open in Explore" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z slice" }));
    expect(screen.getByRole("button", { name: "Side x-z" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Projection description")).toHaveTextContent(
      "Side x-z: height is vertical",
    );
    const scene = screen.getByLabelText("3-D scene container");
    await waitFor(() => {
      expect(within(scene).getByLabelText(/Vertical x-z slice at y = /)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Horizontal layer" }));
    expect(screen.getByRole("button", { name: "Top-down" })).toHaveClass("active-control");
    expect(screen.getByLabelText("Projection description")).toHaveTextContent(
      "Top-down x-y: horizontal map view; height is not shown as vertical position.",
    );
    expect(within(scene).getByLabelText("y-axis ticks")).toBeInTheDocument();
    expect(within(scene).queryByLabelText("height-axis ticks")).not.toBeInTheDocument();
    await waitFor(() => {
      expect(within(scene).getByLabelText(/Horizontal layer at z = /)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Slice field"), { target: { value: "w" } });
    fireEvent.click(screen.getByRole("button", { name: "Vertical y-z slice" }));
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByRole("button", { name: "Side y-z" })).toHaveClass("active-control");
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toHaveClass("active-control");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w"));
    });
  });

  it("updates and resets unified Explore view controls", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open in Explore" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    const plottingGroup = screen.getByLabelText("Zoomable visualizer data layer");
    fireEvent.click(screen.getByRole("button", { name: "Side x-z" }));
    fireEvent.change(screen.getByRole("slider", { name: "Zoom" }), { target: { value: "150" } });

    expect(screen.getByRole("button", { name: "Side x-z" })).toHaveClass("active-control");
    expect(plottingGroup).toHaveStyle({ transform: "scale(1.5)" });
    expect(screen.getAllByText("150%").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByText("About this visualization"));
    expect(screen.getByText("2.5-D fixed projection; data-only zoom")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reset view" }));

    expect(screen.getByRole("button", { name: "Oblique" })).toHaveClass("active-control");
    expect(plottingGroup).toHaveStyle({ transform: "scale(1)" });
    expect(screen.getAllByText("100%").length).toBeGreaterThan(0);
  });

  it("updates cloud-water threshold opacity point size and time requests", async () => {
    render(<App />);

    fireEvent.click((await screen.findAllByRole("button", { name: "Open in Explore" }))[0]);
    await screen.findAllByText("Cloud-water point cloud loaded");

    fireEvent.click(screen.getByText("About this visualization"));
    fireEvent.change(screen.getByLabelText("Cloud-water threshold"), { target: { value: "1" } });

    await screen.findAllByText("No cloud water above threshold");
    expect(
      screen.getByText("No cloud water above the selected threshold at this time."),
    ).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("threshold=1"));

    fireEvent.change(screen.getByLabelText("Cloud opacity"), { target: { value: "0.8" } });
    fireEvent.change(screen.getByLabelText("Point size"), { target: { value: "14" } });
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });

    expect(screen.getByText("0.8")).toBeInTheDocument();
    expect(screen.getByText("14px")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("time_index=1"));
    });
  });

  it("handles missing qc in the unified Explore cloud context", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByRole("heading", { name: "What happened in this result?" })).toBeInTheDocument();
    await screen.findAllByText("Cloud view ready");
    expect(
      screen.getByText("Cloud water field qc is not available for this result."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    fireEvent.click(screen.getByText("About this visualization"));
    expect(screen.getByLabelText("Cloud-water threshold")).toBeDisabled();
  });

  it("handles an Explore result with no visualization-ready fields", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No visual fields" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

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
