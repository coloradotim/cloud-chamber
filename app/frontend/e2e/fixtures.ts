import type { Page, Route } from "@playwright/test";

const scenario = {
  id: "baseline-shallow-cumulus",
  display_name: "Baseline Shallow Cumulus",
  description: "First Golden Path hero case for a credible idealized shallow-cumulus experiment.",
  physical_question:
    "How do low-level moisture, surface heating, cap strength, cap height, dry air aloft, and mixing/entrainment affect shallow-cumulus formation, timing, depth, updraft strength, and cloud-water evolution?",
  intended_behavior: "A balanced shallow-cumulus case.",
  expected_behavior: "Clouds may form after heating and mixing erode inhibition.",
  learning_goals: ["Recognize first cloud time and cloud depth."],
  warnings: ["Preview estimates are guidance only."],
  limitations: ["Exact morphology is not pass/fail."],
  controls: [
    {
      id: "low_level_humidity",
      label: "Low-level humidity",
      description: "Relative moisture in the lower atmosphere around the baseline profile.",
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
      description: "Relative daytime heating strength for boundary-layer growth.",
      type: "choice",
      default: "baseline",
      options: [
        { value: "weaker", label: "Weaker" },
        { value: "baseline", label: "Baseline" },
        { value: "stronger", label: "Stronger" },
      ],
    },
    {
      id: "cap_strength",
      label: "Cap strength",
      description: "Relative resistance to rising thermals near the capping layer.",
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
      purpose: "Sanity checks.",
      expected_runtime: "roughly 10-20 minutes",
      confidence: "lower confidence until locally validated",
      output_notes: "coarser output cadence",
    },
  ],
};

const outputSummary = {
  netcdf_count: 13,
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
};

export const results = [
  {
    result_id: "result-baseline",
    run_id: "dry-run-baseline",
    name: "Baseline Shallow Cumulus — Quick Look",
    tags: ["baseline", "quick-look"],
    notes: "Mocked keeper result for browser smoke tests.",
    saved: true,
    protected: true,
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    run_size_preset: "quick_look",
    physical_question: scenario.physical_question,
    controls: {
      low_level_humidity: "baseline",
      surface_heating: "baseline",
      cap_strength: "baseline",
    },
    status: "ingested",
    source_lifecycle_state: "completed",
    source_product_state: "completed_cm1_result",
    source_model: "CM1",
    provenance_labels: ["CM1 result", "ingested metadata", "visualizer interpretation"],
    diagnostics_summary: "cloud formed; rain detected",
    thermal_fate_label: "Growing cumulus",
    thermal_fate_confidence: "candidate",
    main_limiting_factor: "unknown",
    first_cloud_time_seconds: 1800,
    max_qc_kg_kg: 0.00219,
    time_of_max_qc_seconds: 1800,
    max_w_m_s: 6.96,
    time_of_max_w_seconds: 3600,
    min_w_m_s: -3.77,
    time_of_min_w_seconds: 3600,
    rain_present: true,
    first_rain_time_seconds: 3600,
    caveats: ["minor vertical-coordinate caveat"],
    output_file_summary: outputSummary,
    created_at: "2026-05-22T15:15:36Z",
    completed_at: "2026-05-22T15:32:21Z",
    ingested_at: "2026-05-22T15:35:00Z",
    updated_at: "2026-05-22T15:35:00Z",
  },
  {
    result_id: "result-dry-failed",
    run_id: "dry-run-dry-failed",
    name: "Dry Failed Cumulus — Quick Look",
    tags: ["dry-failed"],
    notes: "Mocked dry contrast.",
    saved: true,
    protected: true,
    scenario_id: "dry-failed-cumulus",
    scenario_name: "Dry Failed Cumulus",
    run_size_preset: "quick_look",
    physical_question:
      "How does insufficient low-level moisture prevent shallow cumulus formation?",
    controls: { low_level_humidity: "drier", surface_heating: "baseline" },
    status: "ingested",
    source_lifecycle_state: "completed",
    source_product_state: "completed_cm1_result",
    source_model: "CM1",
    provenance_labels: ["CM1 result", "ingested metadata"],
    diagnostics_summary: "no cloud formed; no rain detected",
    thermal_fate_label: "Thermal without cloud",
    thermal_fate_confidence: "supported",
    main_limiting_factor: "moisture",
    first_cloud_time_seconds: null,
    max_qc_kg_kg: 0,
    time_of_max_qc_seconds: null,
    max_w_m_s: 1.95,
    time_of_max_w_seconds: 1800,
    min_w_m_s: -1.09,
    time_of_min_w_seconds: 3600,
    rain_present: false,
    first_rain_time_seconds: null,
    caveats: ["moisture-limited"],
    output_file_summary: outputSummary,
    created_at: "2026-05-22T19:20:00Z",
    completed_at: "2026-05-22T19:32:00Z",
    ingested_at: "2026-05-22T19:35:00Z",
    updated_at: "2026-05-22T19:35:00Z",
  },
];

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

function resultMeta(resultId: string) {
  if (resultId === "result-dry-failed") {
    return {
      result_id: resultId,
      run_id: "dry-run-dry-failed",
      scenario_id: "dry-failed-cumulus",
    };
  }
  return {
    result_id: resultId,
    run_id: "dry-run-baseline",
    scenario_id: "baseline-shallow-cumulus",
  };
}

function resultIdFromUrl(url: string) {
  const match = url.match(/\/api\/results\/([^/]+)/);
  return match?.[1] ?? "result-baseline";
}

function fieldCatalog(resultId: string) {
  const meta = resultMeta(resultId);
  const provenance = {
    source_model: "CM1",
    result_id: meta.result_id,
    run_id: meta.run_id,
    scenario_id: meta.scenario_id,
    source_product_state: "completed_cm1_result",
    result_state: "ingested",
    processing_method: "native-grid slice",
    rendering_method: "json heatmap",
    provenance_label: "CM1-derived visualization-ready payload",
  };
  return {
    result_id: meta.result_id,
    run_id: meta.run_id,
    scenario_id: meta.scenario_id,
    source_model: "CM1",
    available_fields: ["qc", "w"].map((name) => ({
      raw_field_name: name,
      canonical_field_name: name === "qc" ? "cloud_water" : "vertical_velocity",
      display_name: name === "qc" ? "Cloud water" : "Vertical velocity",
      units: name === "qc" ? "kg/kg" : "m/s",
      dimensions: name === "qc" ? ["time", "zh", "yh", "xh"] : ["time", "zf", "yh", "xh"],
      shape: [3, 4, 4, 4],
      native_grid: name === "qc" ? "zh/yh/xh" : "zf/yh/xh",
      coordinate_names: { time: "time", vertical: name === "qc" ? "zh" : "zf", y: "yh", x: "xh" },
      time_coordinate_values: [0, 1800, 3600],
      provenance,
      caveats: ["native_grid_no_interpolation"],
    })),
    provenance,
    caveats: [],
  };
}

function viewDefaults(resultId: string, timeIndex?: number) {
  const dryFailed = resultId === "result-dry-failed";
  const meta = resultMeta(resultId);
  const selectedTime = timeIndex ?? (dryFailed ? 1 : 1);
  return {
    result_id: meta.result_id,
    run_id: meta.run_id,
    scenario_id: meta.scenario_id,
    preferred_field: dryFailed ? "w" : "qc",
    fields: {
      qc: {
        field: "qc",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: dryFailed ? 0 : 2,
        vertical_x_index: 1,
        vertical_y_index: 1,
        source: dryFailed ? "no_cloud_qc_zero_native_grid" : "first_cloud_time",
        max_value: dryFailed ? 0 : 0.00219,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: dryFailed ? ["qc_present_but_below_cloud_threshold"] : [],
      },
      w: {
        field: "w",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 2,
        vertical_x_index: 1,
        vertical_y_index: 1,
        source: "max_w_native_grid_location",
        max_value: dryFailed ? 1.95 : 6.96,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: [],
      },
    },
    provenance: fieldCatalog(resultId).provenance,
    caveats: dryFailed ? ["no_cloud_result_qc_zero_w_available"] : [],
  };
}

function slicePayload(resultId: string, url: string) {
  const parsed = new URL(url);
  const fieldName = parsed.searchParams.get("field") ?? "qc";
  const orientation = parsed.searchParams.get("orientation") ?? "horizontal";
  const timeIndex = Number(parsed.searchParams.get("time_index") ?? 1);
  const dryFailed = resultId === "result-dry-failed";
  const catalog = fieldCatalog(resultId);
  const field =
    catalog.available_fields.find((candidate) => candidate.raw_field_name === fieldName) ??
    catalog.available_fields[0];
  const qcValues = dryFailed
    ? [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
      ]
    : [
        [0, 0.001, 0.002, 0],
        [0, 0.002, 0.001, 0],
        [0, 0.001, 0.002, 0],
        [0, 0, 0.001, 0],
      ];
  const wValues = dryFailed
    ? [
        [0.2, 0.8, 1.2, 0.3],
        [0.1, 1.95, 1.1, -0.4],
        [0.0, 0.7, 0.5, -1.09],
        [0.1, 0.4, 0.2, -0.2],
      ]
    : [
        [0.5, 2.1, 4.8, 1.0],
        [0.2, 6.96, 3.7, -1.4],
        [0.1, 2.4, 1.2, -3.77],
        [0.0, 0.8, 0.4, -0.6],
      ];
  const values = fieldName === "w" ? wValues : qcValues;
  const flat = values.flat();
  return {
    result_id: resultId,
    run_id: resultMeta(resultId).run_id,
    scenario_id: resultMeta(resultId).scenario_id,
    field,
    selection: {
      time_index: timeIndex,
      time_seconds: [0, 1800, 3600][timeIndex] ?? 1800,
      orientation,
      selected_dimension:
        orientation === "vertical_y" ? "xh" : orientation === "vertical_x" ? "yh" : "zh",
      selected_index: Number(parsed.searchParams.get("level_index") ?? 1),
      selected_coordinate_value: orientation === "horizontal" ? 0.8 : 0,
      level_units: orientation === "horizontal" ? "km" : null,
      level_coordinate_value: orientation === "horizontal" ? 0.8 : null,
      level_meters: orientation === "horizontal" ? 800 : null,
    },
    coordinate_units: { zh: "km", yh: "km", xh: "km" },
    shape: [4, 4],
    dimension_order: orientation === "horizontal" ? ["yh", "xh"] : ["zh", "xh"],
    data_encoding: "json",
    values,
    stats: {
      min: Math.min(...flat),
      max: Math.max(...flat),
      mean: flat.reduce((sum, value) => sum + value, 0) / flat.length,
      finite_count: flat.length,
      non_finite_count: 0,
    },
    provenance: catalog.provenance,
    caveats: ["native_grid_no_interpolation"],
  };
}

function pointCloudPayload(resultId: string, url: string) {
  const parsed = new URL(url);
  const dryFailed = resultId === "result-dry-failed";
  const points = dryFailed
    ? []
    : [
        [2, 2, 0.8, 0.001],
        [2.5, 2.3, 1.2, 0.002],
        [3, 2.5, 1.8, 0.0015],
      ];
  const values = points.map((point) => point[3]);
  return {
    result_id: resultId,
    run_id: resultMeta(resultId).run_id,
    scenario_id: resultMeta(resultId).scenario_id,
    field: fieldCatalog(resultId).available_fields[0],
    selection: {
      field: "qc",
      time_index: Number(parsed.searchParams.get("time_index") ?? 1),
      time_seconds: 1800,
      threshold: Number(parsed.searchParams.get("threshold") ?? 0.000001),
      max_points: Number(parsed.searchParams.get("max_points") ?? 50000),
    },
    coordinate_units: { xh: "km", yh: "km", zh: "km" },
    coordinate_extents: {
      x: { min: 0, max: 6.4, units: "km" },
      y: { min: 0, max: 6.4, units: "km" },
      z: { min: 0, max: 3, units: "km" },
      xh: { min: 0, max: 6.4, units: "km" },
      yh: { min: 0, max: 6.4, units: "km" },
      zh: { min: 0, max: 3, units: "km" },
    },
    point_order: ["x", "y", "z", "value"],
    points,
    stats: {
      source_count: points.length,
      returned_count: points.length,
      min_value: values.length ? Math.min(...values) : null,
      max_value: values.length ? Math.max(...values) : null,
      active_z_min: values.length ? Math.min(...points.map((point) => point[2])) : null,
      active_z_max: values.length ? Math.max(...points.map((point) => point[2])) : null,
      max_value_location: points.length
        ? { x: points[1][0], y: points[1][1], z: points[1][2], value: points[1][3] }
        : null,
      downsampled: false,
      downsample_stride: 1,
    },
    provenance: {
      ...fieldCatalog(resultId).provenance,
      processing_method: "native-grid thresholded point cloud",
      rendering_method: "thresholded point cloud",
    },
    caveats: dryFailed ? ["qc_present_but_no_points_above_threshold"] : [],
  };
}

export async function mockCloudChamberApis(page: Page) {
  await page.route("**/api/scenarios", (route) =>
    json(route, { golden_path_scenario_id: "baseline-shallow-cumulus", scenarios: [scenario] }),
  );

  await page.route("**/api/dry-run-package", (route) =>
    json(route, {
      package_dir: "/tmp/cloud-chamber-e2e/run",
      manifest_path: "/tmp/cloud-chamber-e2e/run/run_manifest.json",
      report_path: "/tmp/cloud-chamber-e2e/run/dry_run_report.json",
      generated_files: [
        "run_manifest.json",
        "case_manifest.json",
        "namelist.input",
        "input_sounding",
      ],
      report: {
        scenario_id: scenario.id,
        physical_question: scenario.physical_question,
        controls: {
          low_level_humidity: "baseline",
          surface_heating: "baseline",
          cap_strength: "baseline",
        },
        run_size_preset: "quick_look",
        estimated_cost_or_size: "unknown until validated",
        expected_diagnostics: ["first cloud time", "max qc", "max w"],
        visualization_defaults: {},
        generated_files: { namelist: "namelist.input" },
        not_a_completed_cm1_result: true,
        cm1_was_launched: false,
        provenance: {
          product_state: "packaged_dry_run_output",
          source_model: "CM1",
          preview_is_guidance_only: true,
          visualizer_is_interpretation: true,
        },
      },
    }),
  );

  await page.route("**/api/runs/launch", (route) =>
    json(route, {
      run_id: "dry-run-baseline",
      lifecycle_state: "completed",
      product_state: "completed_cm1_result",
      validation_status: "accepted",
      manifest_path: "/tmp/cloud-chamber-e2e/run/run_manifest.json",
      command: ["/mock/cm1.exe"],
      stdout_log: "/tmp/stdout.log",
      stderr_log: "/tmp/stderr.log",
      stdout_tail: "Program terminated normally",
      stderr_tail: "",
      exit_code: 0,
      started_at: "2026-05-22T15:15:36Z",
      finished_at: "2026-05-22T15:32:21Z",
      output_summary: { raw_cm1_artifacts: 0, netcdf_paths: 13, processed_artifacts: 0 },
      runtime_warnings: [],
    }),
  );

  await page.route("**/api/runs/status**", (route) =>
    json(route, {
      run_id: "dry-run-baseline",
      lifecycle_state: "completed",
      product_state: "completed_cm1_result",
      validation_status: "accepted",
      manifest_path: "/tmp/cloud-chamber-e2e/run/run_manifest.json",
      command: ["/mock/cm1.exe"],
      stdout_log: "/tmp/stdout.log",
      stderr_log: "/tmp/stderr.log",
      stdout_tail: "Program terminated normally",
      stderr_tail: "",
      exit_code: 0,
      started_at: "2026-05-22T15:15:36Z",
      finished_at: "2026-05-22T15:32:21Z",
      output_summary: { raw_cm1_artifacts: 0, netcdf_paths: 13, processed_artifacts: 0 },
      runtime_warnings: [],
    }),
  );

  await page.route("**/api/results/ingest", (route) =>
    json(route, {
      result_id: "result-baseline",
      run_id: "dry-run-baseline",
      diagnostics_summary: "cloud formed; rain detected",
    }),
  );

  await page.route("**/api/results", (route) => json(route, { results }));

  await page.route("**/api/results/*/save", (route) => {
    const result = results[0];
    return json(route, { ...result, saved: true, protected: true });
  });

  await page.route("**/api/results/*/visualization/fields", (route) =>
    json(route, fieldCatalog(resultIdFromUrl(route.request().url()))),
  );

  await page.route("**/api/results/*/visualization/defaults**", (route) => {
    const url = route.request().url();
    const parsed = new URL(url);
    const timeIndex = parsed.searchParams.has("time_index")
      ? Number(parsed.searchParams.get("time_index"))
      : undefined;
    return json(route, viewDefaults(resultIdFromUrl(url), timeIndex));
  });

  await page.route("**/api/results/*/visualization/slice**", (route) => {
    const url = route.request().url();
    return json(route, slicePayload(resultIdFromUrl(url), url));
  });

  await page.route("**/api/results/*/visualization/point-cloud**", (route) => {
    const url = route.request().url();
    return json(route, pointCloudPayload(resultIdFromUrl(url), url));
  });

  await page.route("**/api/results/*/diagnostics/selected-region**", (route) =>
    json(route, {
      result_id: "result-baseline",
      run_id: "dry-run-baseline",
      scenario_id: "baseline-shallow-cumulus",
      region: {
        region_type: "column",
        requested: { region_type: "column", x_index: 1, y_index: 1, neighborhood: 1 },
        x: {
          dimension: "xh",
          start_index: 0,
          end_index: 2,
          start_coordinate: 0,
          end_coordinate: 3.2,
          units: "km",
        },
        y: {
          dimension: "yh",
          start_index: 0,
          end_index: 2,
          start_coordinate: 0,
          end_coordinate: 3.2,
          units: "km",
        },
        vertical: {
          dimension: "zh",
          start_index: 0,
          end_index: 3,
          start_coordinate: 0.4,
          end_coordinate: 1.6,
          units: "km",
        },
        native_grid: "zh/yh/xh",
        cell_count: 36,
      },
      diagnostics: {
        available: true,
        local_max_w_m_s: 4.5,
        time_of_local_max_w_seconds: 1800,
        local_min_w_m_s: -1.1,
        time_of_local_min_w_seconds: 1800,
        local_w_max_time_series: [{ time_seconds: 1800, value: 4.5 }],
        local_w_min_time_series: [{ time_seconds: 1800, value: -1.1 }],
        local_max_qc_kg_kg: 0.002,
        time_of_local_max_qc_seconds: 1800,
        first_local_cloud_time_seconds: 1800,
        local_cloud_fraction_time_series: [{ time_seconds: 1800, value: 0.5 }],
        local_qc_max_time_series: [{ time_seconds: 1800, value: 0.002 }],
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
        local_max_w_fraction_of_domain: 0.64,
        local_max_qc_fraction_of_domain: 0.91,
        local_first_cloud_time_delta_seconds: 0,
        local_cloud_top_fraction_of_domain: 0.75,
        local_first_rain_time_delta_seconds: 0,
        caveats: [],
      },
      interpretation: {
        thermal_fate_label: "Growing cumulus",
        confidence: "candidate",
        main_limiting_factor: "unknown",
        summary: "Cloud water appeared locally where upward motion strengthened.",
        caveats: ["selected_region_is_not_cloud_object_tracking"],
      },
      provenance: {
        ...fieldCatalog("result-baseline").provenance,
        processing_method: "backend_xarray_selected_region_diagnostics",
        rendering_method: "thermal_fate_inspector_summary",
        provenance_label:
          "CM1-derived selected-region diagnostics; native-grid summary; browser receives bounded payload only",
      },
      caveats: ["native_grid_region_summary_no_interpolation"],
    }),
  );

  await page.route("**/api/storage/inventory", (route) =>
    json(route, {
      runtime_home: "/tmp/cloud-chamber-e2e",
      runs_directory: "/tmp/cloud-chamber-e2e/runs",
      total_size_bytes: 4096,
      warning_threshold_bytes: 53687091200,
      above_warning_threshold: false,
      warning_message: null,
      runs: [
        {
          run_id: "dry-run-baseline",
          scenario_id: "baseline-shallow-cumulus",
          scenario_name: "Baseline Shallow Cumulus",
          lifecycle_state: "completed",
          validation_status: "valid",
          product_state: "completed_cm1_result",
          run_size_preset: "quick_look",
          created_at: "2026-05-22T15:15:36Z",
          updated_at: "2026-05-22T15:32:21Z",
          saved: true,
          protected: true,
          output_artifact_count: 14,
          output_summary: { raw_cm1_artifacts: 0, netcdf_paths: 13, processed_artifacts: 0 },
          size_bytes: 4096,
          path: "/tmp/cloud-chamber-e2e/runs/dry-run-baseline",
          category: "saved_or_protected",
          manifest_path: "/tmp/cloud-chamber-e2e/runs/dry-run-baseline/run_manifest.json",
          manifest_error: null,
        },
        {
          run_id: "dry-run-disposable",
          scenario_id: "baseline-shallow-cumulus",
          scenario_name: "Baseline Shallow Cumulus",
          lifecycle_state: "completed",
          validation_status: "valid",
          product_state: "completed_cm1_result",
          run_size_preset: "quick_look",
          created_at: "2026-05-22T15:45:36Z",
          updated_at: "2026-05-22T16:02:21Z",
          saved: false,
          protected: false,
          output_artifact_count: 14,
          output_summary: { raw_cm1_artifacts: 0, netcdf_paths: 13, processed_artifacts: 0 },
          size_bytes: 4096,
          path: "/tmp/cloud-chamber-e2e/runs/dry-run-disposable",
          category: "completed_with_output",
          manifest_path: "/tmp/cloud-chamber-e2e/runs/dry-run-disposable/run_manifest.json",
          manifest_error: null,
        },
        {
          run_id: "dry-run-running",
          scenario_id: "dry-failed-cumulus",
          scenario_name: "Dry Failed Cumulus",
          lifecycle_state: "running",
          validation_status: "valid",
          product_state: "queued_running_cm1_process",
          run_size_preset: "quick_look",
          created_at: "2026-05-22T16:10:36Z",
          updated_at: "2026-05-22T16:18:21Z",
          saved: false,
          protected: false,
          output_artifact_count: 0,
          output_summary: { raw_cm1_artifacts: 0, netcdf_paths: 0, processed_artifacts: 0 },
          size_bytes: 2048,
          path: "/tmp/cloud-chamber-e2e/runs/dry-run-running",
          category: "running",
          manifest_path: "/tmp/cloud-chamber-e2e/runs/dry-run-running/run_manifest.json",
          manifest_error: null,
        },
      ],
      largest_runs: [],
    }),
  );

  await page.route("**/api/storage/delete-run", (route) =>
    json(route, {
      run_id: "dry-run-disposable",
      run_directory: "/tmp/cloud-chamber-e2e/runs/dry-run-disposable",
      dry_run: true,
      deleted: false,
      size_bytes: 1024,
      message: "Preview only.",
    }),
  );
}
