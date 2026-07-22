import type { Page, Route } from "@playwright/test";

const defaultRunConfiguration = {
  configuration_id: "short_6h__cells_64__local_6km__standard_15min__process",
  mode: "science",
  label: "Short evolution; Local 6 km; Scout 64 x 64; 100 m dx/dy; Standard 15 min",
  duration: "short_6h",
  duration_seconds: 21600,
  horizontal_cell_count: 64,
  domain_size: "local_6km",
  output_cadence: "standard_15min",
  output_cadence_seconds: 900,
  diagnostic_set: "process",
  cost_runtime_summary: "6 h model time, 409,600 cells, 15 min saved-output cadence",
  output_volume_summary: "25 saved frames, process diagnostics, 409,600 cells per frame",
  cm1_values: {
    nx: 64,
    ny: 64,
    nz: 100,
    dx_m: 100,
    dy_m: 100,
    dz_m: 40,
    stretch_z: 1,
    str_bot_m: 2000,
    str_top_m: 18000,
    dz_bot_m: 40,
    dz_top_m: 600,
    model_top_m: 18000,
    domain_x_km: 6.4,
    domain_y_km: 6.4,
    time_step_seconds: 3,
    runtime_seconds: 21600,
    output_cadence_seconds: 900,
    restart_cadence_seconds: 10800,
    rayleigh_damping_start_m: 12000,
    expected_output_frames: 25,
    grid_cell_count: 409600,
  },
  caveats: ["science_run_configuration_minimum_duration_6h"],
};

const defaultRunConfigurationSummary = {
  configuration_id: defaultRunConfiguration.configuration_id,
  mode: defaultRunConfiguration.mode,
  label: defaultRunConfiguration.label,
  duration: defaultRunConfiguration.duration,
  horizontal_cell_count: defaultRunConfiguration.horizontal_cell_count,
  domain_size: defaultRunConfiguration.domain_size,
  output_cadence: defaultRunConfiguration.output_cadence,
  diagnostic_set: defaultRunConfiguration.diagnostic_set,
  runtime_seconds: 21600,
  output_cadence_seconds: 900,
  expected_output_frames: 25,
  nx: 64,
  ny: 64,
  nz: 100,
  dx_m: 100,
  dy_m: 100,
  dz_m: 40,
  stretch_z: 1,
  str_bot_m: 2000,
  str_top_m: 18000,
  dz_bot_m: 40,
  dz_top_m: 600,
  model_top_m: 18000,
  time_step_seconds: 3,
  time_step_note: "CM1 solver timestep is resolved from the selected run configuration.",
  grid_cell_count: 409600,
  grid_cell_multiplier_vs_default: 1,
  time_step_multiplier_vs_default: 1,
  output_frame_multiplier_vs_default: 1,
  estimated_compute_multiplier_vs_default: 1,
  estimated_output_volume_multiplier_vs_default: 1,
  cost_warning:
    "Configuration cost depends on duration, horizontal cell count, domain, cadence, and full output-field volume. Review the CM1-facing values before launch.",
  validation_note:
    "Run configuration preserves explicit duration, horizontal cell count, domain, cadence, and full output fields.",
};

const defaultPreRunValidationReport = {
  status: "caveated",
  selected_candidate: {
    candidate_id: null,
    station_id: null,
    valid_time_utc: null,
  },
  selected_hypothesis: {
    hypothesis_id: null,
    story_id: null,
    story_label: null,
    ingredient_score: null,
    predicted_output_signature: [],
  },
  selected_run_recipe: {
    run_recipe: "generated_reference_lower_atmosphere",
    recipe_id: "generated_reference_lower_atmosphere_v1",
    display_name: "Generated Lower-Atmosphere Reference",
    recipe_display_name: "Generated Lower-Atmosphere Reference",
    assumption_set_id: "generated_reference_lower_atmosphere_v1",
    assumption_mode: "generated_reference",
  },
  hypothesis_recipe_alignment: {
    status: "aligned",
    reasons: ["No selected candidate hypothesis; validating the run configuration only."],
    missing_assumptions: [],
    missing_outputs: [],
  },
  run_shape_validation: {
    duration: "short_6h",
    duration_seconds: 21600,
    domain: "local_6km",
    horizontal_cell_count: 64,
    output_cadence: "standard_15min",
    diagnostic_set: "process",
    estimated_frames: 25,
    estimated_output_volume: "25 saved frames, process diagnostics, 409,600 cells per frame",
  },
  output_validation: {
    required_fields: ["qc", "w"],
    enabled_fields: ["qc", "qr", "qv", "th", "prs", "u", "v", "w", "rain", "dbz"],
    missing_fields: [],
  },
  blocking_errors: [],
  caveats: ["science_run_configuration_minimum_duration_6h"],
};

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

const observedSoundingParseResponse = {
  source_provider: "NOAA/NCEI IGRA",
  source_format: "igra_station_text",
  uploaded_filename: "USM00072558-data.txt",
  available_soundings: [
    {
      station_id: "USM00072558",
      valid_time_utc: "2025-01-01T00:00:00Z",
      source_time_text: "2025 01 01 00",
      num_levels: 8,
      pressure_source: "observed",
      non_pressure_source: "observed",
    },
    {
      station_id: "USM00072558",
      valid_time_utc: "2025-01-02T00:00:00Z",
      source_time_text: "2025 01 02 00",
      num_levels: 8,
      pressure_source: "observed",
      non_pressure_source: "observed",
    },
  ],
  selected_sounding: {
    source_type: "observed_sounding",
    source_provider: "NOAA/NCEI IGRA",
    source_format: "igra_station_text",
    uploaded_filename: "USM00072558-data.txt",
    station_id: "USM00072558",
    station_name: "Valley, Nebraska",
    station_latitude: 41.32,
    station_longitude: -96.3669,
    station_elevation_m_msl: 351.5,
    valid_time_utc: "2025-01-02T00:00:00Z",
    source_time_text: "2025 01 02 00",
    source_units: {
      pressure: "Pa",
      height: "m MSL",
      temperature: "degC",
      wind_speed: "m/s",
    },
    converted_cm1_units: {
      pressure: "Pa",
      theta: "K",
      qv: "g/kg",
      height: "m above station surface",
    },
    source_vertical_coordinate_type: "geopotential_height_msl",
    model_bottom_elevation_m_msl: 351.5,
    wind_handling:
      "observed sounding winds; generated CM1 namelist uses isnd=7 so input_sounding u/v columns initialize the wind profile",
    levels: [
      {
        pressure_pa: 96500,
        source_height_m_msl: 352,
        model_z_m: 0,
        temperature_c: 22,
        potential_temperature_k: 299.15,
        qv_g_kg: 10.1,
        wind_direction_degrees: 180,
        wind_speed_m_s: 4,
      },
      {
        pressure_pa: 90000,
        source_height_m_msl: 1200,
        model_z_m: 848.5,
        temperature_c: 18,
        potential_temperature_k: 302.1,
        qv_g_kg: 8.2,
        wind_direction_degrees: 190,
        wind_speed_m_s: 7,
      },
      {
        pressure_pa: 7500,
        source_height_m_msl: 18820,
        model_z_m: 18468.5,
        temperature_c: -58,
        potential_temperature_k: 850,
        qv_g_kg: 0.01,
        wind_direction_degrees: 260,
        wind_speed_m_s: 24,
      },
    ],
    conversion_choices: {
      vertical_anchor: "station_surface",
      wind_application: "input_sounding_u_v",
    },
    validation: {
      status: "needs_review",
      errors: [],
      caveats: [
        "station_elevation_joined_from_igra_station_fixture",
        "observed_sounding_winds_written_to_input_sounding",
      ],
    },
    provenance: {
      parser: "cloud_chamber_igra_station_text",
      station_metadata: "tiny_fixture",
    },
  },
};

const shallowSoundingCandidate = {
  candidate_id: "USM00072558-2025010200-shallow",
  station_id: "USM00072558",
  station_name: "Valley, Nebraska",
  station_latitude: 41.32,
  station_longitude: -96.3669,
  station_elevation_m_msl: 351.5,
  valid_time_utc: "2025-01-02T00:00:00Z",
  source_time_text: "2025 01 02 00",
  source_file_name: "USM00072558-data.txt",
  source_file_hash: "mock-hash",
  source_format: "igra_station_text",
  source_provider: "NOAA/NCEI IGRA",
  primary_story: "shallow_cumulus_candidate",
  primary_story_label: "Cloud-forming shallow cumulus",
  story_family: "lower_atmosphere",
  rank_score: 82,
  confidence: "medium",
  package_ready: true,
  selected_sounding_payload: observedSoundingParseResponse.selected_sounding,
  story_scores: [
    {
      story: "shallow_cumulus_candidate",
      label: "Cloud-forming shallow cumulus",
      score_0_to_100: 82,
      support: "supported",
      reasons: ["moist boundary layer", "reasonable LCL"],
      caveats: [],
    },
    {
      story: "dry_failed_candidate",
      label: "Dry failed cumulus",
      score_0_to_100: 24,
      support: "unavailable",
      reasons: [],
      caveats: [],
    },
  ],
  features: {
    mean_qv_0_1000m_g_kg: 10.2,
    estimated_lcl_height_m_agl: 820,
    lapse_rate_0_1000m_c_per_km: 7.1,
    cap_strength_proxy: 0.6,
    moisture_depth_m: 2100,
    profile_top_m_agl: 18468.5,
    data_completeness_score: 94,
  },
  evidence: [
    {
      label: "Low-level moisture",
      value: 10.2,
      units: "g/kg",
      interpretation: "Enough low-level water vapor for a cloud-forming trial.",
      supports_story: ["shallow_cumulus_candidate"],
      caveats: [],
    },
    {
      label: "Estimated LCL",
      value: 820,
      units: "m AGL",
      interpretation: "Cloud base is plausible inside the lower domain.",
      supports_story: ["shallow_cumulus_candidate"],
      caveats: [],
    },
    {
      label: "Cap proxy",
      value: 0.6,
      units: "",
      interpretation: "The cap proxy is not extreme for a shallow-cumulus screen.",
      supports_story: ["shallow_cumulus_candidate"],
      caveats: [],
    },
  ],
  caveats: ["screening_is_not_cm1_outcome_prediction"],
  screening_version: "test-screening-v1",
  created_at: "2026-07-01T12:00:00Z",
};

const blockedSoundingCandidate = {
  ...shallowSoundingCandidate,
  candidate_id: "USM00072357-2025010100-blocked",
  station_id: "USM00072357",
  station_name: "Norman, Oklahoma",
  valid_time_utc: "2025-01-01T00:00:00Z",
  primary_story: "needs_review",
  primary_story_label: "Needs review",
  story_family: "review",
  rank_score: 40,
  confidence: "low",
  package_ready: false,
  selected_sounding_payload: null,
  story_scores: [
    {
      story: "needs_review",
      label: "Needs review",
      score_0_to_100: 40,
      support: "weak",
      reasons: ["missing surface level"],
      caveats: ["missing_surface_level"],
    },
  ],
  caveats: ["missing_surface_level"],
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
    run_configuration: defaultRunConfiguration,
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
    diagnostics_summary:
      "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
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
    surface_rain_present: true,
    max_surface_rain: 3.5,
    surface_rain_units: "mm",
    reflectivity_available: true,
    max_dbz: 30,
    caveats: ["minor vertical-coordinate caveat"],
    input_source: "generated_reference",
    input_source_label: "Generated reference",
    observed_sounding: null,
    science_summary: {
      first_cloud_time_seconds: 1800,
      max_qc_kg_kg: 0.00219,
      time_of_max_qc_seconds: 1800,
      max_updraft_w_m_s: 6.96,
      time_of_max_updraft_w_seconds: 3600,
      min_downdraft_w_m_s: -3.77,
      time_of_min_downdraft_w_seconds: 3600,
      rain_onset_time_seconds: 3600,
      latest_output_time_seconds: 10800,
      highest_cloud_top_m: 2220,
      default_explore_time_index: 1,
      interesting_time_support_state: "supported",
    },
    interesting_times: [
      {
        key: "first_cloud",
        label: "First cloud",
        support_state: "supported",
        time_index: 1,
        time_seconds: 1800,
        source: "CM1 diagnostics",
        caveats: [],
      },
      {
        key: "max_qc",
        label: "Max cloud water",
        support_state: "supported",
        time_index: 1,
        time_seconds: 1800,
        source: "CM1 diagnostics",
        caveats: [],
      },
    ],
    default_time_by_field: {
      qc: {
        field: "qc",
        time_index: 1,
        time_seconds: 1800,
        source_interesting_time_key: "max_qc",
        support_state: "supported",
        caveats: [],
      },
      w: {
        field: "w",
        time_index: 2,
        time_seconds: 3600,
        source_interesting_time_key: "max_updraft_w",
        support_state: "supported",
        caveats: [],
      },
    },
    interesting_time_caveats: [],
    output_file_summary: outputSummary,
    created_at: "2026-05-22T15:15:36Z",
    completed_at: "2026-05-22T15:32:21Z",
    ingested_at: "2026-05-22T15:35:00Z",
    updated_at: "2026-05-22T15:35:00Z",
  },
  {
    result_id: "result-observed-sounding",
    run_id: "dry-run-observed-sounding",
    name: "Uploaded Sounding — Valley, Nebraska",
    tags: ["observed-sounding", "quick-look"],
    notes: "Mocked observed IGRA sounding result for browser smoke tests.",
    saved: false,
    protected: false,
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Uploaded Sounding",
    run_configuration: defaultRunConfiguration,
    physical_question: "What cloud behavior emerges from the uploaded observed sounding profile?",
    controls: { surface_heating: "baseline" },
    status: "ingested",
    source_lifecycle_state: "completed",
    source_product_state: "completed_cm1_result",
    source_model: "CM1",
    provenance_labels: ["CM1 result", "observed sounding", "ingested metadata"],
    diagnostics_summary:
      "cloud formed; no rain water aloft detected; surface rain unavailable; reflectivity unavailable",
    thermal_fate_label: "Observed-sounding cumulus",
    thermal_fate_confidence: "candidate",
    main_limiting_factor: "unknown",
    first_cloud_time_seconds: 900,
    max_qc_kg_kg: 0.0014,
    time_of_max_qc_seconds: 1800,
    max_w_m_s: 9.25,
    time_of_max_w_seconds: 2700,
    min_w_m_s: -4.1,
    time_of_min_w_seconds: 2700,
    rain_present: false,
    first_rain_time_seconds: null,
    caveats: ["observed_sounding_winds_written_to_input_sounding"],
    input_source: "observed_sounding",
    input_source_label: "Observed sounding: USM00072558 · Valley, Nebraska",
    observed_sounding: {
      source_type: "observed_sounding",
      source_format: "igra_station_text",
      station_id: "USM00072558",
      station_name: "Valley, Nebraska",
      station_elevation_m_msl: 351.5,
      valid_time_utc: "2025-01-02T00:00:00Z",
    },
    science_summary: {
      first_cloud_time_seconds: 900,
      max_qc_kg_kg: 0.0014,
      time_of_max_qc_seconds: 1800,
      max_updraft_w_m_s: 9.25,
      time_of_max_updraft_w_seconds: 2700,
      min_downdraft_w_m_s: -4.1,
      time_of_min_downdraft_w_seconds: 2700,
      rain_onset_time_seconds: null,
      latest_output_time_seconds: 10800,
      highest_cloud_top_m: 1980,
      default_explore_time_index: 1,
      interesting_time_support_state: "supported",
    },
    interesting_times: [
      {
        key: "first_cloud",
        label: "First cloud",
        support_state: "supported",
        time_index: 1,
        time_seconds: 900,
        source: "CM1 diagnostics",
        caveats: [],
      },
      {
        key: "max_updraft_w",
        label: "Max updraft",
        support_state: "supported",
        time_index: 2,
        time_seconds: 2700,
        source: "CM1 diagnostics",
        caveats: [],
      },
    ],
    default_time_by_field: {
      qc: {
        field: "qc",
        time_index: 1,
        time_seconds: 1800,
        source_interesting_time_key: "max_qc",
        support_state: "supported",
        caveats: [],
      },
      w: {
        field: "w",
        time_index: 2,
        time_seconds: 2700,
        source_interesting_time_key: "max_updraft_w",
        support_state: "supported",
        caveats: [],
      },
    },
    interesting_time_caveats: [],
    output_file_summary: outputSummary,
    created_at: "2026-06-30T20:00:00Z",
    completed_at: "2026-06-30T20:15:00Z",
    ingested_at: "2026-06-30T20:18:00Z",
    updated_at: "2026-06-30T20:18:00Z",
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
    run_configuration: defaultRunConfiguration,
    physical_question:
      "How does insufficient low-level moisture prevent shallow cumulus formation?",
    controls: { low_level_humidity: "drier", surface_heating: "baseline" },
    status: "ingested",
    source_lifecycle_state: "completed",
    source_product_state: "completed_cm1_result",
    source_model: "CM1",
    provenance_labels: ["CM1 result", "ingested metadata"],
    diagnostics_summary:
      "no cloud formed; no rain water aloft detected; surface rain unavailable; reflectivity unavailable",
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
    input_source: "generated_reference",
    input_source_label: "Generated reference",
    observed_sounding: null,
    science_summary: {
      first_cloud_time_seconds: null,
      max_qc_kg_kg: 0,
      time_of_max_qc_seconds: null,
      max_updraft_w_m_s: 1.95,
      time_of_max_updraft_w_seconds: 1800,
      min_downdraft_w_m_s: -1.09,
      time_of_min_downdraft_w_seconds: 3600,
      rain_onset_time_seconds: null,
      latest_output_time_seconds: 10800,
      highest_cloud_top_m: null,
      default_explore_time_index: 1,
      interesting_time_support_state: "fallback",
    },
    interesting_times: [
      {
        key: "max_updraft_w",
        label: "Max updraft",
        support_state: "supported",
        time_index: 1,
        time_seconds: 1800,
        source: "CM1 diagnostics",
        caveats: [],
      },
    ],
    default_time_by_field: {
      qc: {
        field: "qc",
        time_index: 1,
        time_seconds: 1800,
        source_interesting_time_key: "max_updraft_w",
        support_state: "fallback",
        caveats: ["no_cloud_event"],
      },
      w: {
        field: "w",
        time_index: 1,
        time_seconds: 1800,
        source_interesting_time_key: "max_updraft_w",
        support_state: "supported",
        caveats: [],
      },
    },
    interesting_time_caveats: ["no_cloud_event"],
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
  if (resultId === "result-observed-sounding") {
    return {
      result_id: resultId,
      run_id: "dry-run-observed-sounding",
      scenario_id: "baseline-shallow-cumulus",
    };
  }
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
  const fields = [
    {
      raw: "qc",
      canonical: "cloud_water",
      display: "Cloud water",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw: "w",
      canonical: "vertical_velocity",
      display: "Vertical velocity",
      units: "m/s",
      dimensions: ["time", "zf", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zf/yh/xh",
      vertical: "zf",
    },
    {
      raw: "qr",
      canonical: "rain_water",
      display: "Rain water",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw: "theta",
      canonical: "potential_temperature",
      display: "Potential temperature",
      units: "K",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw: "temperature",
      canonical: "temperature",
      display: "Temperature",
      units: "K",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw: "qv",
      canonical: "water_vapor",
      display: "Water vapor",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw: "dbz",
      canonical: "reflectivity",
      display: "Reflectivity",
      units: "dBZ",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [3, 4, 4, 4],
      nativeGrid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw: "rain",
      canonical: "accumulated_surface_rain",
      display: "Accumulated surface rain",
      units: "mm",
      dimensions: ["time", "yh", "xh"],
      shape: [3, 4, 4],
      nativeGrid: "surface/yh/xh",
      vertical: null,
    },
  ];
  return {
    result_id: meta.result_id,
    run_id: meta.run_id,
    scenario_id: meta.scenario_id,
    source_model: "CM1",
    available_fields: fields.map((field) => ({
      raw_field: field.raw,
      raw_field_name: field.raw,
      canonical_field: field.canonical,
      canonical_field_name: field.canonical,
      display_name: field.display,
      units: field.units,
      dimensions: field.dimensions,
      shape: field.shape,
      native_grid: field.nativeGrid,
      coordinate_names: { time: "time", vertical: field.vertical, y: "yh", x: "xh" },
      time_coordinate_values: [0, 1800, 3600],
      provenance,
      caveats:
        field.raw === "rain"
          ? ["native_grid_no_interpolation", "surface_field_no_vertical_dimension"]
          : ["native_grid_no_interpolation"],
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
      qr: {
        field: "qr",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 1,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "max_qr_native_grid_location",
        max_value: dryFailed ? 0 : 0.000001,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: [],
      },
      theta: {
        field: "theta",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 2,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "max_theta_native_grid_location",
        max_value: 304,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: [],
      },
      temperature: {
        field: "temperature",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 2,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "max_temperature_native_grid_location",
        max_value: 292,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: [],
      },
      qv: {
        field: "qv",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 1,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "max_qv_native_grid_location",
        max_value: 0.012,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: [],
      },
      dbz: {
        field: "dbz",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 1,
        vertical_x_index: 1,
        vertical_y_index: 2,
        source: "max_dbz_native_grid_location",
        max_value: dryFailed ? 0 : 32,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: [],
      },
      rain: {
        field: "rain",
        time_index: selectedTime,
        time_seconds: [0, 1800, 3600][selectedTime] ?? 1800,
        horizontal_level_index: 0,
        vertical_x_index: 0,
        vertical_y_index: 0,
        source: "surface_rain_domain_floor",
        max_value: dryFailed ? 0 : 4.5,
        selected_time_index: timeIndex ?? null,
        selected_time_seconds: timeIndex === undefined ? null : [0, 1800, 3600][selectedTime],
        caveats: ["surface_field_rendered_on_domain_floor"],
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
  const values = mockSliceValues(fieldName, dryFailed);
  const flat = values.flat();
  const isSurface = fieldName === "rain";
  const isVertical = orientation !== "horizontal" && !isSurface;
  return {
    result_id: resultId,
    run_id: resultMeta(resultId).run_id,
    scenario_id: resultMeta(resultId).scenario_id,
    field,
    selection: {
      time_index: timeIndex,
      time_seconds: [0, 1800, 3600][timeIndex] ?? 1800,
      orientation,
      selected_dimension: isSurface
        ? "surface"
        : orientation === "vertical_y"
          ? "xh"
          : orientation === "vertical_x"
            ? "yh"
            : (field.coordinate_names.vertical ?? "zh"),
      selected_index: Number(parsed.searchParams.get("level_index") ?? 1),
      selected_coordinate_value: isSurface ? 0 : orientation === "horizontal" ? 0.8 : 0,
      level_units: orientation === "horizontal" ? "km" : null,
      level_coordinate_value: orientation === "horizontal" ? (isSurface ? 0 : 0.8) : null,
      level_meters: orientation === "horizontal" ? (isSurface ? 0 : 800) : null,
    },
    coordinate_units: isVertical ? { zh: "km", xh: "km" } : { yh: "km", xh: "km" },
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
    caveats: isSurface
      ? [
          "native_grid_no_interpolation",
          "surface_field_no_vertical_dimension",
          "surface_field_rendered_on_domain_floor",
        ]
      : ["native_grid_no_interpolation"],
  };
}

function mockSliceValues(fieldName: string, dryFailed: boolean) {
  if (fieldName === "w") {
    return dryFailed
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
  }
  if (fieldName === "qr") {
    return dryFailed ? zeroGrid() : scaleGrid(0.000001);
  }
  if (fieldName === "qv") {
    return [
      [0.0101, 0.0104, 0.0108, 0.0103],
      [0.0105, 0.0112, 0.0118, 0.0109],
      [0.0107, 0.0114, 0.0124, 0.0111],
      [0.0102, 0.0107, 0.0112, 0.0105],
    ];
  }
  if (fieldName === "dbz") {
    return dryFailed
      ? [
          [-10, -5, 0, -8],
          [-4, 0, 4, -2],
          [-6, 0, 2, -3],
          [-10, -5, 0, -8],
        ]
      : [
          [0, 8, 18, 3],
          [12, 24, 32, 16],
          [8, 20, 28, 10],
          [0, 6, 14, 2],
        ];
  }
  if (fieldName === "temperature") {
    return [
      [287, 288, 289, 287.5],
      [286, 289, 292, 288],
      [285.5, 288, 291, 287],
      [285, 286, 287, 286],
    ];
  }
  if (fieldName === "theta") {
    return [
      [300, 301, 302, 301],
      [300.5, 302, 304, 302],
      [301, 302.5, 303.5, 302],
      [300, 301, 302, 301],
    ];
  }
  if (fieldName === "rain") {
    return dryFailed ? zeroGrid() : scaleGrid(4.2);
  }
  return dryFailed ? zeroGrid() : scaleGrid(0.002);
}

function zeroGrid() {
  return [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ];
}

function scaleGrid(maximum: number) {
  return [
    [0, maximum * 0.35, maximum * 0.7, 0],
    [maximum * 0.2, maximum, maximum * 0.6, maximum * 0.1],
    [maximum * 0.1, maximum * 0.5, maximum * 0.85, maximum * 0.2],
    [0, maximum * 0.2, maximum * 0.45, 0],
  ];
}

function pointCloudPayload(resultId: string, url: string) {
  const parsed = new URL(url);
  const dryFailed = resultId === "result-dry-failed";
  const fieldName = parsed.searchParams.get("field") ?? "qc";
  const threshold = Number(
    parsed.searchParams.get("threshold") ?? (fieldName === "qr" ? 0.0000001 : 0.000001),
  );
  const points = mockPointCloudPoints(fieldName, dryFailed, threshold);
  const values = points.map((point) => point[3]);
  const catalog = fieldCatalog(resultId);
  const field =
    catalog.available_fields.find((candidate) => candidate.raw_field_name === fieldName) ??
    catalog.available_fields[0];
  const isSurface = fieldName === "rain";
  return {
    result_id: resultId,
    run_id: resultMeta(resultId).run_id,
    scenario_id: resultMeta(resultId).scenario_id,
    field,
    selection: {
      field: field.raw_field_name,
      time_index: Number(parsed.searchParams.get("time_index") ?? 1),
      time_seconds: 1800,
      threshold,
      max_points: Number(parsed.searchParams.get("max_points") ?? 50000),
    },
    coordinate_units: isSurface
      ? { xh: "km", yh: "km", z: "km" }
      : { xh: "km", yh: "km", zh: "km" },
    coordinate_extents: {
      x: { min: 0, max: 6.4, units: "km" },
      y: { min: 0, max: 6.4, units: "km" },
      z: { min: 0, max: 3, units: "km" },
      xh: { min: 0, max: 6.4, units: "km" },
      yh: { min: 0, max: 6.4, units: "km" },
      ...(isSurface ? {} : { zh: { min: 0, max: 3, units: "km" } }),
    },
    point_order: ["x", "y", "z", "value"],
    points,
    stats: {
      source_count: points.length,
      returned_count: points.length,
      field_min_value: mockPointFieldRange(fieldName, dryFailed).min,
      field_max_value: mockPointFieldRange(fieldName, dryFailed).max,
      field_mean_value: mockPointFieldRange(fieldName, dryFailed).mean,
      field_finite_count: 64,
      field_non_finite_count: 0,
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
      ...catalog.provenance,
      processing_method: "native-grid thresholded point cloud",
      rendering_method: isSurface ? "surface floor layer" : "thresholded point cloud",
    },
    caveats: [
      ...(dryFailed ? [`${fieldName}_present_but_no_points_above_threshold`] : []),
      ...(isSurface ? ["surface_field_rendered_on_domain_floor"] : []),
    ],
  };
}

function mockPointFieldRange(fieldName: string, dryFailed: boolean) {
  if (dryFailed && fieldName === "qc") return { min: 0, max: 0, mean: 0 };
  if (fieldName === "qr")
    return dryFailed ? { min: 0, max: 0, mean: 0 } : { min: 0, max: 0.000001, mean: 0.0000003 };
  if (fieldName === "qv") return { min: 0.0101, max: 0.0124, mean: 0.0111 };
  if (fieldName === "dbz") {
    return dryFailed ? { min: -10, max: 4, mean: -3 } : { min: 0, max: 32, mean: 14 };
  }
  if (fieldName === "rain")
    return dryFailed ? { min: 0, max: 0, mean: 0 } : { min: 0, max: 4.2, mean: 1.3 };
  return dryFailed ? { min: 0, max: 0, mean: 0 } : { min: 0, max: 0.002, mean: 0.0006 };
}

function mockPointCloudPoints(fieldName: string, dryFailed: boolean, threshold: number) {
  if (dryFailed && fieldName === "qc") return [];
  const pointValues: Record<string, Array<[number, number, number, number]>> = {
    qc: [
      [2, 2, 0.8, 0.001],
      [2.5, 2.3, 1.2, 0.002],
      [3, 2.5, 1.8, 0.0015],
    ],
    qr: [
      [2, 2, 0.8, 0.0000002],
      [2.5, 2.3, 1.2, 0.0000006],
      [3, 2.5, 1.8, 0.0000009],
    ],
    qv: [
      [1.5, 1.2, 0.6, 0.0104],
      [2.5, 2.3, 1.2, 0.0113],
      [3.4, 2.5, 1.8, 0.0124],
    ],
    dbz: [
      [1.5, 1.2, 0.6, 8],
      [2.5, 2.3, 1.2, 22],
      [3.4, 2.5, 1.8, 38],
    ],
    rain: [
      [1.5, 1.2, 0, 0.8],
      [2.5, 2.3, 0, 2.4],
      [3.4, 2.5, 0, 4.2],
    ],
  };
  return (pointValues[fieldName] ?? pointValues.qc).filter((point) => point[3] >= threshold);
}

export async function mockCloudChamberApis(page: Page) {
  let savedSoundingCandidates: Array<{
    saved_candidate_id: string;
    candidate: typeof shallowSoundingCandidate;
    primary_story: string;
    tags: string[];
    notes: string;
    linked_run_ids: string[];
    created_at: string;
    updated_at: string;
  }> = [];
  let currentResults = [...results];
  let localRunQueue: {
    entries: Array<Record<string, unknown>>;
    active_run_id: string | null;
    queued_count: number;
    updated_at: string;
  } = {
    entries: [],
    active_run_id: null,
    queued_count: 0,
    updated_at: "2026-05-22T15:15:00Z",
  };

  await page.route("**/api/worlds", (route) => json(route, []));

  await page.route("**/api/scenarios", (route) =>
    json(route, { golden_path_scenario_id: "baseline-shallow-cumulus", scenarios: [scenario] }),
  );

  await page.route("**/api/observed-soundings/parse", (route) =>
    json(route, observedSoundingParseResponse),
  );

  await page.route("**/api/igra/recent/catalog", (route) =>
    json(route, {
      catalog: {
        generated_at: "2026-07-01T12:00:00Z",
        refreshed_at: "2026-07-01T12:00:00Z",
        region: { id: "great_plains_midwest", label: "Great Plains / Midwest" },
        zip_references: [
          {
            station_id: "USM00072558",
            station_name: "VALLEY",
            cached_status: "cached",
            url: "https://example.test/USM00072558-data-beg2025.txt.zip",
          },
        ],
      },
    }),
  );

  await page.route("**/api/igra/recent/refresh-catalog", (route) =>
    json(route, {
      generated_at: "2026-07-01T12:00:00Z",
      refreshed_at: "2026-07-01T12:00:00Z",
      region: { id: "great_plains_midwest", label: "Great Plains / Midwest" },
      zip_references: [
        {
          station_id: "USM00072558",
          station_name: "VALLEY",
          cached_status: "cached",
          url: "https://example.test/USM00072558-data-beg2025.txt.zip",
        },
      ],
    }),
  );

  await page.route("**/api/igra/recent/cache", (route) =>
    json(route, {
      entries: [
        {
          station_id: "USM00072558",
          station_name: "VALLEY",
          data_txt_path: "/tmp/cloud-chamber-e2e/cache/USM00072558-data.txt",
          zip_path: "/tmp/cloud-chamber-e2e/cache/USM00072558-data-beg2025.txt.zip",
          sounding_count: 2,
          latest_valid_time_utc: "2025-01-02T00:00:00Z",
          size_bytes: 1234,
        },
      ],
    }),
  );

  await page.route("**/api/igra/recent/cache-batch", (route) =>
    json(route, {
      requested_limit: 10,
      selected_count: 1,
      cached_entries: [
        {
          station_id: "USM00072558",
          station_name: "VALLEY",
          cached_text_path: "/tmp/cloud-chamber-e2e/cache/USM00072558-data.txt",
        },
      ],
      failed: [],
      remaining_uncached_count: 0,
    }),
  );

  await page.route("**/api/sounding-candidates/screening-inputs", (route) =>
    json(route, {
      inputs: [
        {
          station_id: "USM00072558",
          station_name: "VALLEY",
          cached_text_path: "/tmp/cloud-chamber-e2e/cache/USM00072558-data.txt",
          source_file_name: "USM00072558-data.txt",
          cached_status: "cached",
          sounding_count: 2,
          latest_valid_time_utc: "2025-01-02T00:00:00Z",
          caveats: [],
        },
      ],
    }),
  );

  await page.route("**/api/sounding-candidates/analyze", (route) => {
    const request = JSON.parse(route.request().postData() ?? "{}") as {
      story_filter?: string;
      sort_by?: string;
    };
    const storyFilter = request.story_filter ?? "all";
    const candidates = [shallowSoundingCandidate, blockedSoundingCandidate].filter((candidate) => {
      if (storyFilter === "all") return true;
      return candidate.story_scores.some(
        (score) => score.story === storyFilter && score.support !== "unavailable",
      );
    });
    return json(route, {
      screening_version: "test-screening-v1",
      generated_at: "2026-07-01T12:00:00Z",
      candidates,
      total_candidate_count: 2,
      filtered_candidate_count: candidates.length,
      sort_by: request.sort_by ?? "best_match",
      sort_direction: "desc",
      filters: {
        station_id: null,
        story_filter: storyFilter,
        story_family: "all",
        support: "all",
        readiness: "all",
        station_search: "",
      },
      caveats: ["screening_guidance_only"],
    });
  });

  await page.route("**/api/sounding-candidates/saved", (route) => {
    if (route.request().method() === "POST") {
      const saved = {
        saved_candidate_id: "saved-USM00072558-2025010200",
        candidate: shallowSoundingCandidate,
        primary_story: "shallow_cumulus_candidate",
        tags: ["interesting-sounding"],
        notes: "",
        linked_run_ids: [],
        created_at: "2026-07-01T12:05:00Z",
        updated_at: "2026-07-01T12:05:00Z",
      };
      savedSoundingCandidates = [saved];
      return json(route, saved);
    }
    return json(route, { saved_candidates: savedSoundingCandidates });
  });

  await page.route("**/api/sounding-candidates/saved/*", (route) => {
    savedSoundingCandidates = [];
    return json(route, { removed: true });
  });

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
        run_configuration: defaultRunConfiguration,
        run_configuration_summary: defaultRunConfigurationSummary,
        pre_run_validation_report: defaultPreRunValidationReport,
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

  await page.route("**/api/runs/queue", (route) => {
    if (route.request().method() === "POST") {
      localRunQueue = {
        entries: [
          {
            run_id: "run",
            manifest_path: "/tmp/cloud-chamber-e2e/run/run_manifest.json",
            package_dir: "/tmp/cloud-chamber-e2e/run",
            state: "ingested",
            queued_at: "2026-05-22T15:15:00Z",
            started_at: "2026-05-22T15:15:36Z",
            finished_at: "2026-05-22T15:32:21Z",
            updated_at: "2026-05-22T15:32:21Z",
            result_id: "result-baseline",
            cleanup_status: "queue_finalized_result_backing_run_retained",
            message:
              "Completed local CM1 output was ingested automatically; local run directory retained for Results/Explore.",
          },
        ],
        active_run_id: null,
        queued_count: 0,
        updated_at: "2026-05-22T15:32:21Z",
      };
    }
    return json(route, localRunQueue);
  });

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
      diagnostics_summary:
        "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
    }),
  );

  await page.route("**/api/results", (route) => json(route, { results: currentResults }));

  await page.route("**/api/results/*", async (route) => {
    if (route.request().method() !== "PATCH") {
      await route.fallback();
      return;
    }
    const resultId = resultIdFromUrl(route.request().url());
    const body = (route.request().postDataJSON() ?? {}) as {
      name?: string;
      tags?: string[];
      notes?: string | null;
    };
    const current = currentResults.find((item) => item.result_id === resultId) ?? results[0];
    const updated = {
      ...current,
      ...(body.name !== undefined ? { name: body.name } : {}),
      ...(body.tags !== undefined ? { tags: body.tags } : {}),
      ...(body.notes !== undefined ? { notes: body.notes } : {}),
    };
    currentResults = currentResults.map((item) => (item.result_id === resultId ? updated : item));
    await json(route, updated);
  });

  await page.route("**/api/results/*/delete-preview", (route) => {
    const resultId = resultIdFromUrl(route.request().url());
    const result = currentResults.find((item) => item.result_id === resultId) ?? results[0];
    return json(route, {
      result_id: result.result_id,
      run_id: result.run_id,
      run_directory: `/tmp/cloud-chamber-e2e/runs/${result.run_id}`,
      dry_run: true,
      deleted: false,
      size_bytes: 4096,
      message: "Dry run only; no files were deleted.",
      affected_surfaces: ["Results", "Explore", "local inventory"],
      categories: [
        {
          label: "Result metadata and notebook edits",
          description: "Ingested result metadata plus editable notebook sidecar state.",
          present: true,
          item_count: 2,
        },
        {
          label: "Run manifests, package inputs, and reports",
          description:
            "Run manifests, case setup, generated CM1 inputs, dry-run reports, and file checklists.",
          present: true,
          item_count: 6,
        },
        {
          label: "CM1 output and stats",
          description:
            "Model-output NetCDF, stats files, and raw CM1 artifacts copied into this run.",
          present: true,
          item_count: 14,
        },
        {
          label: "Logs and runtime sidecars",
          description: "Local stdout/stderr logs, backend logs, and LAN-worker status sidecars.",
          present: true,
          item_count: 3,
        },
        {
          label: "Derived diagnostics and Explore data",
          description:
            "Derived product manifests, cached diagnostics, and visualization backing data.",
          present: true,
          item_count: 1,
        },
      ],
    });
  });

  await page.route("**/api/results/*/delete", (route) => {
    const resultId = resultIdFromUrl(route.request().url());
    const result = currentResults.find((item) => item.result_id === resultId) ?? results[0];
    currentResults = currentResults.filter((item) => item.result_id !== resultId);
    return json(route, {
      result_id: result.result_id,
      run_id: result.run_id,
      run_directory: `/tmp/cloud-chamber-e2e/runs/${result.run_id}`,
      dry_run: false,
      deleted: true,
      size_bytes: 4096,
      message: "Result and local run data deleted.",
      affected_surfaces: ["Results", "Explore", "local inventory"],
      categories: [],
    });
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
          run_configuration: defaultRunConfiguration,
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
          run_configuration: defaultRunConfiguration,
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
          run_configuration: defaultRunConfiguration,
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

  await page.route("**/api/storage/delete-run", (route) => {
    const body = route.request().postDataJSON() as { run_id?: string; dry_run?: boolean } | null;
    const runId = body?.run_id ?? "dry-run-disposable";
    return json(route, {
      run_id: runId,
      run_directory: `/tmp/cloud-chamber-e2e/runs/${runId}`,
      dry_run: Boolean(body?.dry_run),
      deleted: !body?.dry_run,
      size_bytes: 1024,
      message: body?.dry_run ? "Preview only." : "Run directory deleted.",
    });
  });
}

const mountainWavesConfiguration = {
  terrain: { height_m: 2000, half_width_m: 10000, center_m: 500 },
  sounding: [
    { height_m: 0, pressure_pa: 100000, theta_k: 288, qv_g_kg: 4, u_m_s: 12, v_m_s: 0 },
    { height_m: 12500, pressure_pa: 20000, theta_k: 340, qv_g_kg: 0.5, u_m_s: 20, v_m_s: 0 },
    { height_m: 25200, pressure_pa: 3000, theta_k: 440, qv_g_kg: 0, u_m_s: 25, v_m_s: 0 },
  ],
  duration_seconds: 4000,
  output_cadence_seconds: 200,
};

const mountainWavesReference = {
  simulation_id: "mountain_waves_boulder_moist_reference",
  display_name: "Boulder Windstorm — Moist Reference",
  role: "built_in",
  world_id: "mountain_waves",
  run_id: "moist-mountain-wave-reference",
  case_id: "moist-reference-case",
  parent_simulation_id: null,
  parent_run_id: null,
  reference_simulation_id: "mountain_waves_boulder_moist_reference",
  user_question: null,
  state: "available",
  state_message: "Exact preserved output is available for terrain-aware inspection.",
  inspectable: true,
  can_create_variation: true,
  moist: true,
  moist_fields_available: true,
  purpose: "Inspect a retained moist mountain-wave reference.",
  configuration: mountainWavesConfiguration,
  differences: {},
  warnings: [],
  caveats: ["Cloud state is instantaneous."],
  manifest_path: "/mock/moist/run_manifest.json",
  created_at: "2026-07-21T20:00:00Z",
  started_at: "2026-07-21T20:00:00Z",
  completed_at: "2026-07-21T21:00:00Z",
};

const mountainWavesDry = {
  ...mountainWavesReference,
  simulation_id: "mountain_waves_dry_ridge",
  display_name: "Dry Ridge — Wave Mechanics",
  run_id: "dry-mountain-wave-reference",
  case_id: "dry-reference-case",
  moist: false,
  moist_fields_available: false,
  can_create_variation: false,
  purpose: "Inspect terrain-forced wave mechanics without moisture.",
};

const mountainWavesFrame = {
  schema_version: "mountain_waves_explore_v1",
  run_id: "moist-mountain-wave-reference",
  case_label: "Boulder Windstorm — Moist Reference",
  time_index: 0,
  time_seconds: 0,
  times_seconds: [0, 200],
  dry_case: false,
  field: {
    key: "cloud_over_wave",
    display_name: "Vertical velocity",
    units: "m/s",
    derivation: "native",
  },
  values: [
    [-0.4, 0.3],
    [-0.1, 0.7],
  ],
  field_options: [
    "cloud_over_wave",
    "w",
    "cloud_liquid",
    "relative_humidity",
    "theta_perturbation",
  ],
  overlay: {
    values: [
      [0, 0.01],
      [0, 0.02],
    ],
    threshold: 0.001,
    maximum: 0.02,
  },
  pointer_context: {
    horizontal_wind_m_s: [
      [12, 15],
      [18, 21],
    ],
    vertical_velocity_m_s: [
      [-0.4, 0.3],
      [-0.1, 0.7],
    ],
    potential_temperature_k: [
      [290, 291],
      [300, 301],
    ],
    theta_perturbation_k: [
      [-0.2, 0.2],
      [-0.1, 0.3],
    ],
    cloud_liquid_g_kg: [
      [0, 0.01],
      [0, 0.02],
    ],
    relative_humidity_percent: [
      [80, 101],
      [90, 105],
    ],
  },
  viewport: {
    default_mode: "focus",
    focus_available: true,
    focus: { x_minimum_m: -1000, x_maximum_m: 1000, z_minimum_m: 0, z_maximum_m: 1500 },
    full: { x_minimum_m: -1000, x_maximum_m: 1000, z_minimum_m: 0, z_maximum_m: 2000 },
  },
  lens: {
    horizontal_wind_scale_id: "mountain_waves_horizontal_wind_v1",
    horizontal_wind_reference_m_s: 25,
    vertical_velocity_neutral_threshold_m_s: 0.1,
    potential_temperature_contour_scale_id:
      "mountain_waves_total_potential_temperature_contours_v1",
    potential_temperature_contour_interval_k: 10,
    potential_temperature_contour_values_k: [290, 300],
  },
  geometry: {
    x_center_m: [-500, 500],
    x_edge_m: [-1000, 0, 1000],
    terrain_m: [0, 300],
    scalar_height_m: [
      [500, 725],
      [1500, 1575],
    ],
    full_height_m: [
      [0, 300],
      [1000, 1150],
      [2000, 2000],
    ],
    nominal_scalar_height_m: [500, 1500],
    nominal_full_height_m: [0, 1000, 2000],
    active_top_m: 2000,
    singleton_y_m: 0,
  },
  scale: {
    fixed_across_all_times: true,
    minimum: -1,
    maximum: 1,
    selected_time_minimum: -0.4,
    selected_time_maximum: 0.7,
    palette: "blue_white_red_diverging",
    scale_id: "mountain_waves_vertical_velocity_v1",
    scale_type: "fixed_across_time_discrete",
    units: "m/s",
    breakpoints: [-0.8, -0.5, -0.1, 0.1, 0.3, 0.5, 0.7, 0.85, 0.95],
    colors: [
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
    ],
  },
  caveats: ["Cloud state is instantaneous."],
  provenance: {
    source_history_file: "cm1out_000001.nc",
    topology: "native_2d_x_z_singleton_y",
    interpolation: "none",
    display_binning: "Native scalar samples painted between physical full-level bounds.",
    physical_height_source: "native zhval",
  },
  active_top_evidence: {
    transform_top_source: "final_nominal_zf",
    all_sources_agree: true,
    inactive_namelist_ztop_m: 2000,
  },
};

export async function mockMountainWavesProductPath(
  page: Page,
  options: { failPackage?: boolean } = {},
) {
  type Stage = "idle" | "queued" | "running" | "completed";
  let stage: Stage = "idle";
  const variation = {
    ...mountainWavesReference,
    simulation_id: "mountain_waves_broader_ridge_abcd1234",
    display_name: "Broader Ridge",
    role: "variation",
    run_id: "mw-broader-ridge-20260722T010000Z-abcd",
    case_id: "mountain_waves_exploratory_variation_v1",
    parent_simulation_id: mountainWavesReference.simulation_id,
    parent_run_id: mountainWavesReference.run_id,
    configuration: {
      ...mountainWavesConfiguration,
      terrain: { ...mountainWavesConfiguration.terrain, half_width_m: 11000 },
    },
    differences: {
      terrain: [{ label: "Ridge half-width", before: 10000, after: 11000, units: "m" }],
    },
    manifest_path: "/mock/variation/run_manifest.json",
  };
  const worldPayload = (current: Stage) => {
    const active = current === "queued" || current === "running";
    const completed = current === "completed";
    const attempt = {
      ...variation,
      state: completed ? "available" : current,
      state_message: completed
        ? "CM1 completed normally with 21 exact native histories ready for inspection."
        : current === "running"
          ? "CM1 is running locally."
          : "Waiting for the local CM1 runner.",
      inspectable: completed,
      can_create_variation: completed,
    };
    return {
      world_id: "mountain_waves",
      display_name: "Mountain Waves",
      short_description: "Experiment with terrain-forced waves and mountain-wave clouds.",
      availability_state: "available",
      availability_message: "Both built-in Simulations and the Mountain Waves Lab are available.",
      default_parent_simulation_id: mountainWavesReference.simulation_id,
      simulations: [mountainWavesDry, mountainWavesReference, ...(completed ? [attempt] : [])],
      activity: active ? [attempt] : [],
      history: current === "idle" ? [] : [attempt],
      lab_summary: {
        active_run_count: active ? 1 : 0,
        packaged_run_count: 0,
        completed_simulation_count: completed ? 1 : 0,
        failed_run_count: 0,
        total_variation_count: current === "idle" ? 0 : 1,
      },
      caveats: ["The dry and moist built-ins are not a controlled pair."],
    };
  };

  await page.unroute("**/api/worlds");
  await page.route("**/api/worlds", (route) =>
    json(route, [
      {
        world_id: "mountain_waves",
        display_name: "Mountain Waves",
        short_description: "Experiment with terrain-forced waves and mountain-wave clouds.",
        reference_simulation_id: mountainWavesReference.simulation_id,
        reference_available: true,
        simulation_count: 2,
        saved_view_count: 0,
        saved_comparison_count: 0,
        featured_comparison_count: 0,
        active_run_count: 0,
        completed_uninspected_run_count: 0,
        availability_state: "available",
        availability_message: "Available",
      },
    ]),
  );
  await page.route("**/api/worlds/mountain-waves", (route) => {
    const current = stage;
    if (stage === "queued") stage = "running";
    else if (stage === "running") stage = "completed";
    return json(route, worldPayload(current));
  });
  await page.route("**/api/worlds/mountain-waves/variation-template**", (route) => {
    const parentId = new URL(route.request().url()).searchParams.get("parent_simulation_id");
    const parent = parentId === variation.simulation_id ? variation : mountainWavesReference;
    return json(route, {
      parent_simulation_id: parent.simulation_id,
      parent_run_id: parent.run_id,
      parent_display_name: parent.display_name,
      parent_configuration_source: "retained exact parent variation configuration",
      reference_simulation_id: mountainWavesReference.simulation_id,
      configuration: parent.configuration,
      can_create_variation: true,
      unavailable_reason: null,
    });
  });
  await page.route("**/api/worlds/mountain-waves/variations/preview", async (route) => {
    const request = route.request().postDataJSON() as {
      configuration: typeof mountainWavesConfiguration;
    };
    const changed = request.configuration.terrain.half_width_m !== 10000;
    return json(route, {
      differences: {
        terrain: changed
          ? [
              {
                label: "Ridge half-width",
                before: 10000,
                after: request.configuration.terrain.half_width_m,
                units: "m",
              },
            ]
          : [],
        wind: [],
        moisture: [],
        "stability/thermodynamics": [],
        "numerics/time": [],
        output: [],
      },
      warnings: [],
      blocking_errors: changed ? [] : ["Change at least one editable setting."],
      derived_stability_n2_s2: [0.0001, 0.0001],
      terrain_profile: [],
    });
  });
  await page.route("**/api/worlds/mountain-waves/variations", (route) => {
    if (options.failPackage)
      return json(route, { detail: "Variation package preflight failed." }, 400);
    stage = "queued";
    return json(route, {
      simulation_id: variation.simulation_id,
      run_id: variation.run_id,
      manifest_path: variation.manifest_path,
      package_dir: "/mock/variation",
      differences: variation.differences,
      warnings: [],
      preflight: { passed: true },
    });
  });
  await page.route("**/api/worlds/mountain-waves/simulations/*/frame**", (route) =>
    json(route, {
      ...mountainWavesFrame,
      run_id: route.request().url().includes(variation.simulation_id)
        ? variation.run_id
        : mountainWavesFrame.run_id,
    }),
  );
}
