import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App, VisualizerSceneShell } from "./App";

const defaultRunConfiguration = {
  configuration_id: "short_6h__cells_64__local_6km__standard_15min__full",
  mode: "science",
  label: "Short evolution; Local 6 km; Scout 64 x 64; 100 m dx/dy; Standard 15 min",
  duration: "short_6h",
  duration_seconds: 21600,
  horizontal_cell_count: 64,
  domain_size: "local_6km",
  output_cadence: "standard_15min",
  output_cadence_seconds: 900,
  diagnostic_set: "full",
  surface_forcing_mode: "constant_uniform_surface_flux_proxy",
  surface_heat_flux_k_m_s: 0.008,
  surface_moisture_flux_g_g_m_s: 5.2e-5,
  surface_patch_shape: "circle",
  surface_patch_radius_m: "1500",
  surface_patch_radius_x_m: "1500",
  surface_patch_radius_y_m: "1500",
  surface_patch_heat_flux_perturbation_k_m_s: "4.0e-2",
  surface_patch_moisture_flux_perturbation_g_g_m_s: "5.0e-5",
  surface_patch_taper_width_m: "500",
  surface_patch_ramp_seconds: "1800",
  surface_flux_mode: "constant_uniform_surface_flux_proxy",
  surface_flux_summary:
    "Surface heat flux 0.008 K m/s; surface moisture flux 5.2e-5 g/g m/s; constant uniform proxy",
  surface_flux_cm1_values: {
    isfcflx: 1,
    sfcmodel: 1,
    set_flx: 1,
    set_ust: 1,
    cnst_shflx: 0.008,
    cnst_shflx_units: "K m/s",
    cnst_lhflx: 5.2e-5,
    cnst_lhflx_units: "g/g m/s",
  },
  surface_forcing_patch: null,
  surface_flux_caveats: [
    "surface_flux_proxy_constant_uniform_not_place_time_energy_budget",
    "surface_flux_proxy_not_real_land_surface_or_evaporation_model",
    "surface_flux_proxy_values_need_local_smoke_validation",
  ],
  cost_runtime_summary: "6 h model time, 409,600 cells, 15 min saved-output cadence",
  output_volume_summary: "25 saved frames, full output fields, 409,600 cells per frame",
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
    "Configuration cost depends on duration, horizontal cells, domain, cadence, and full output volume. Review the CM1-facing values before launch.",
  validation_note:
    "Run configuration preserves explicit duration, horizontal cell count, domain, cadence, and full-output choices.",
  surface_flux_mode: defaultRunConfiguration.surface_flux_mode,
  surface_flux_summary: defaultRunConfiguration.surface_flux_summary,
  surface_flux_cm1_values: defaultRunConfiguration.surface_flux_cm1_values,
  surface_forcing_patch: defaultRunConfiguration.surface_forcing_patch,
  surface_flux_caveats: defaultRunConfiguration.surface_flux_caveats,
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
    domain_x_km: 6.4,
    domain_y_km: 6.4,
    model_top: 18000,
    horizontal_cell_count: 64,
    dx_m: 100,
    dy_m: 100,
    output_cadence: "standard_15min",
    output_cadence_seconds: 900,
    diagnostic_set: "full",
    estimated_frames: 25,
    estimated_output_volume: "25 saved frames, full output fields, 409,600 cells per frame",
  },
  forcing_validation: {
    trigger: "none",
    surface_fluxes: {
      mode: "constant_uniform_surface_flux_proxy",
      product_selections: {
        surface_heat_flux_k_m_s: 0.008,
        surface_moisture_flux_g_g_m_s: 5.2e-5,
      },
      cm1_values: defaultRunConfiguration.surface_flux_cm1_values,
    },
    radiation: "disabled_or_future",
    large_scale_forcing: "not_supported_v1",
  },
  output_validation: {
    required_fields: ["qc", "w"],
    enabled_fields: ["qc", "qr", "qv", "th", "prs", "u", "v", "w", "rain", "dbz"],
    missing_fields: [],
  },
  runtime_file_validation: {
    required_files: ["LANDUSE.TBL"],
    staging_status: "checked_at_launch",
    caveats: ["external_runtime_files_are_not_committed"],
  },
  blocking_errors: [],
  caveats: ["science_run_configuration_minimum_duration_6h"],
};

const highDetailRunConfiguration = {
  ...defaultRunConfiguration,
  configuration_id: "standard_12h__cells_256__wide_12km__detailed_5min__full",
  label: "Standard evolution; Wide 12 km; High detail 256 x 256; 50 m dx/dy; Detailed 5 min",
  duration: "standard_12h",
  duration_seconds: 43200,
  horizontal_cell_count: 256,
  domain_size: "wide_12km",
  output_cadence: "detailed_5min",
  output_cadence_seconds: 300,
  diagnostic_set: "full",
  cost_runtime_summary: "12 h model time, 6,553,600 cells, 5 min saved-output cadence",
  output_volume_summary: "145 saved frames, full output fields, 6,553,600 cells per frame",
  cm1_values: {
    ...defaultRunConfiguration.cm1_values,
    nx: 256,
    ny: 256,
    dx_m: 50,
    dy_m: 50,
    domain_x_km: 12.8,
    domain_y_km: 12.8,
    runtime_seconds: 43200,
    output_cadence_seconds: 300,
    expected_output_frames: 145,
    grid_cell_count: 6553600,
  },
  caveats: [
    "science_run_configuration_minimum_duration_6h",
    "configuration_better_suited_to_larger_compute",
  ],
};

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
    estimated_cost_or_size: "unknown until validated",
    run_configuration: defaultRunConfiguration,
    run_configuration_summary: defaultRunConfigurationSummary,
    pre_run_validation_report: defaultPreRunValidationReport,
    expected_diagnostics: ["first_cloud_time", "cloud_water_summary"],
    observed_sounding: null,
    candidate_screening: null,
    user: {
      name: "Baseline Shallow Cumulus",
      tags: [],
      notes: null,
      saved: false,
    },
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

const deepDryRunResponse = {
  ...dryRunResponse,
  report: {
    ...dryRunResponse.report,
    run_configuration: highDetailRunConfiguration,
    estimated_cost_or_size:
      "Configuration cost depends on duration, horizontal cells, domain, cadence, and full output volume. Review the CM1-facing values before launch.",
    run_configuration_summary: {
      ...defaultRunConfigurationSummary,
      configuration_id: highDetailRunConfiguration.configuration_id,
      label: highDetailRunConfiguration.label,
      duration: "standard_12h",
      horizontal_cell_count: 256,
      domain_size: "wide_12km",
      output_cadence: "detailed_5min",
      diagnostic_set: "full",
      runtime_seconds: 43200,
      output_cadence_seconds: 300,
      expected_output_frames: 145,
      nx: 256,
      ny: 256,
      dx_m: 50,
      dy_m: 50,
      grid_cell_count: 6553600,
      grid_cell_multiplier_vs_default: 16,
      output_frame_multiplier_vs_default: 5.8,
      estimated_compute_multiplier_vs_default: 32,
      estimated_output_volume_multiplier_vs_default: 92.8,
    },
  },
};

const observedSoundingParseResponse = {
  source_provider: "NOAA/NCEI IGRA",
  source_format: "igra_station_text",
  uploaded_filename: "USM00072558-data-beg2025.txt",
  available_soundings: [
    {
      station_id: "USM00072558",
      valid_time_utc: "2025-01-01T00:00:00Z",
      source_time_text: "2025-01-01 00 UTC; release 2318",
      num_levels: 8,
      pressure_source: "ncdc-nws",
      non_pressure_source: "ncdc-gts",
    },
    {
      station_id: "USM00072558",
      valid_time_utc: "2025-01-02T00:00:00Z",
      source_time_text: "2025-01-02 00 UTC; release 2318",
      num_levels: 8,
      pressure_source: "ncdc-nws",
      non_pressure_source: "ncdc-gts",
    },
  ],
  selected_sounding: {
    source_type: "observed_sounding",
    source_provider: "NOAA/NCEI IGRA",
    source_format: "igra_station_text",
    uploaded_filename: "USM00072558-data-beg2025.txt",
    station_id: "USM00072558",
    station_name: "Valley, Nebraska",
    station_latitude: 41.32,
    station_longitude: -96.3669,
    station_elevation_m_msl: 351.5,
    valid_time_utc: "2025-01-02T00:00:00Z",
    source_time_text: "2025-01-02 00 UTC; release 2318",
    source_units: { pressure: "Pa", source_height: "m MSL" },
    converted_cm1_units: {
      height: "m above sounding/site surface",
      potential_temperature: "K",
      water_vapor_mixing_ratio: "g/kg",
    },
    source_vertical_coordinate_type: "geopotential_height_msl",
    model_bottom_elevation_m_msl: 351.5,
    levels: [
      {
        pressure_pa: 98052,
        source_height_m_msl: 352,
        model_z_m: 0.5,
        temperature_c: -0.5,
        potential_temperature_k: 298.1,
        qv_g_kg: 4.7,
        wind_direction_degrees: 324,
        wind_speed_m_s: 4.1,
      },
      {
        pressure_pa: 6122,
        source_height_m_msl: 19168,
        model_z_m: 18816.5,
        temperature_c: -56.1,
        potential_temperature_k: 481.1,
        qv_g_kg: 0.02,
        wind_direction_degrees: 253,
        wind_speed_m_s: 6.3,
      },
    ],
    wind_handling:
      "observed_sounding_winds; generated CM1 namelist uses isnd=7 so input_sounding u/v columns initialize the wind profile",
    conversion_choices: {
      height: "IGRA GPH meters MSL converted to model_z_m relative to station elevation",
    },
    validation: {
      status: "needs_review",
      errors: [],
      caveats: [
        "station elevation joined from IGRA station metadata fixture",
        "Place/time are preserved as metadata; radiation remains disabled in the generated package.",
      ],
    },
    provenance: {
      format_reference: "NOAA/NCEI IGRA v2.2 sounding data format",
    },
  },
};

function dryRunResponseForRequest(init?: RequestInit) {
  const body = JSON.parse(String(init?.body ?? "{}")) as {
    run_recipe?: string | null;
    observed_sounding?: Record<string, unknown> | null;
    candidate_screening?: Record<string, unknown> | null;
    user_name?: string | null;
    user_tags?: string[];
    user_notes?: string | null;
  };
  return {
    ...dryRunResponse,
    report: {
      ...dryRunResponse.report,
      run_recipe: body.run_recipe ?? undefined,
      observed_sounding: body.observed_sounding ?? null,
      candidate_screening: body.candidate_screening ?? null,
      pre_run_validation_report: preRunValidationReportForRequest(body),
      user: {
        name: body.user_name ?? "Baseline Shallow Cumulus",
        tags: body.user_tags ?? [],
        notes: body.user_notes ?? null,
        saved: false,
      },
    },
  };
}

function preRunValidationReportForRequest(body: {
  run_recipe?: string | null;
  observed_sounding?: Record<string, unknown> | null;
  candidate_screening?: Record<string, unknown> | null;
}) {
  const runRecipe =
    body.run_recipe ??
    (body.observed_sounding
      ? "observed_surface_forced_evolution"
      : "generated_reference_lower_atmosphere");
  const observed = runRecipe === "observed_surface_forced_evolution";
  const deepTower = runRecipe === "deep_tower_benchmark";
  const recipeId = deepTower
    ? "deep_tower_benchmark_v0"
    : observed
      ? "observed_surface_forced_evolution_v0"
      : "generated_reference_lower_atmosphere_v1";
  const recipeDisplayName = deepTower
    ? "Deep-Tower Benchmark v0"
    : observed
      ? "Observed Surface-Forced Evolution v0"
      : "Generated Lower-Atmosphere Reference";
  const activeStory =
    typeof body.candidate_screening?.active_story === "string"
      ? body.candidate_screening.active_story
      : typeof body.candidate_screening?.primary_story === "string"
        ? body.candidate_screening.primary_story
        : null;
  const activeLabel =
    typeof body.candidate_screening?.active_story_label === "string"
      ? body.candidate_screening.active_story_label
      : typeof body.candidate_screening?.primary_story_label === "string"
        ? body.candidate_screening.primary_story_label
        : null;
  return {
    ...defaultPreRunValidationReport,
    selected_candidate: {
      candidate_id:
        typeof body.candidate_screening?.candidate_id === "string"
          ? body.candidate_screening.candidate_id
          : null,
      station_id:
        typeof body.observed_sounding?.station_id === "string"
          ? body.observed_sounding.station_id
          : null,
      valid_time_utc:
        typeof body.observed_sounding?.valid_time_utc === "string"
          ? body.observed_sounding.valid_time_utc
          : null,
    },
    selected_hypothesis: {
      hypothesis_id: activeStory,
      story_id: activeStory,
      story_label: activeLabel,
      ingredient_score:
        typeof body.candidate_screening?.ingredient_score === "number"
          ? body.candidate_screening.ingredient_score
          : typeof body.candidate_screening?.rank_score === "number"
            ? body.candidate_screening.rank_score
            : null,
      ingredient_score_label:
        typeof body.candidate_screening?.ingredient_score_label === "string"
          ? body.candidate_screening.ingredient_score_label
          : null,
      predicted_output_signature:
        observed || deepTower ? ["qv", "qc", "w", "qr", "rain", "dbz"] : [],
    },
    selected_run_recipe: {
      run_recipe: runRecipe,
      recipe_id: recipeId,
      display_name: deepTower
        ? "Deep-Tower Benchmark"
        : observed
          ? "Observed Surface-Forced Evolution"
          : "Generated Lower-Atmosphere Reference",
      recipe_display_name: recipeDisplayName,
      assumption_set_id: deepTower
        ? "deep_tower_benchmark_v0_assumptions"
        : observed
          ? "observed_surface_forced_evolution_v0_assumptions"
          : "generated_reference_lower_atmosphere_v1",
      assumption_mode: deepTower
        ? "explicit_thermal_initiation"
        : observed
          ? "observed_surface_forced_evolution"
          : "generated_reference",
    },
  };
}

const shallowCandidate = {
  candidate_id: "USM00072558-2025010200-shallow",
  station_id: "USM00072558",
  station_name: "Valley, Nebraska",
  station_latitude: 41.32,
  station_longitude: -96.3669,
  valid_time_utc: "2025-01-02T00:00:00Z",
  source_time_text: "2025-01-02 00 UTC",
  source_file_name: "USM00072558-data.txt",
  source_file_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data.txt",
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
    },
    {
      story: "dry_failed_candidate",
      label: "Dry failed cumulus",
      score_0_to_100: 24,
      support: "unavailable",
    },
  ],
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
  features: {
    mean_qv_0_1000m_g_kg: 10.2,
    estimated_lcl_height_m_agl: 820,
    lapse_rate_0_1000m_c_per_km: 7.1,
    cap_strength_proxy: 0.6,
    moisture_depth_m: 2100,
    profile_top_m_agl: 18816.5,
    data_completeness_score: 94,
  },
  interest_summary: "Low estimated LCL makes cloud formation easier to test.",
  interest_reasons: [
    "Low estimated LCL makes cloud formation easier to test.",
    "Profile coverage is strong enough for package review.",
  ],
  discovery_bucket: "Cloud-forming",
  caveats: ["screening_is_not_cm1_outcome_prediction"],
  screening_version: "test-screening-v1",
  created_at: "2026-07-01T12:00:00Z",
};

const blockedCandidate = {
  ...shallowCandidate,
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
    },
  ],
  interest_summary: "Worth reviewing because package generation is blocked or caveated.",
  interest_reasons: [
    "Worth reviewing because package generation is blocked or caveated.",
    "Use the caveats to decide whether this cached sounding needs parser or metadata work.",
  ],
  discovery_bucket: "Needs review",
  caveats: ["missing_surface_level"],
};

const secondaryShallowCandidate = {
  ...shallowCandidate,
  candidate_id: "USM00072426-2025010300-humid-secondary-shallow",
  station_id: "USM00072426",
  station_name: "Wilmington, Ohio",
  valid_time_utc: "2025-01-03T00:00:00Z",
  primary_story: "humid_rainy_candidate",
  primary_story_label: "Humid / rainy",
  story_family: "lower_atmosphere",
  rank_score: 86,
  story_scores: [
    {
      story: "humid_rainy_candidate",
      label: "Humid / rainy",
      score_0_to_100: 86,
      support: "supported",
    },
    {
      story: "shallow_cumulus_candidate",
      label: "Cloud-forming shallow cumulus",
      score_0_to_100: 61,
      support: "weak",
    },
    {
      story: "high_cape_pulse_storm",
      label: "High-CAPE pulse storm",
      score_0_to_100: 48.9,
      support: "weak",
    },
  ],
  features: {
    ...shallowCandidate.features,
    mean_qv_0_1000m_g_kg: 13.6,
    estimated_lcl_height_m_agl: 640,
    deep_tower_opportunity: 48.9,
    deep_tower_opportunity_support: "weak",
    deep_tower_opportunity_summary:
      "Experimental Deep-Tower evidence is caveated: some cloud-depth ingredients are present, but the fixed benchmark response is uncertain.",
  },
  interest_summary: "Very moist lower atmosphere.",
  interest_reasons: [
    "Very moist lower atmosphere.",
    "Low estimated LCL makes cloud formation easier to test.",
  ],
  discovery_bucket: "Humid / rainy",
};

const missingLclCandidate = {
  ...shallowCandidate,
  candidate_id: "USM00072440-2025010400-missing-lcl",
  station_id: "USM00072440",
  station_name: "Springfield, Missouri",
  valid_time_utc: "2025-01-04T00:00:00Z",
  rank_score: 78,
  features: {
    ...shallowCandidate.features,
    estimated_lcl_height_m_agl: null,
  },
  evidence: shallowCandidate.evidence.filter((item) => item.label !== "Estimated LCL"),
};

const deepConvectionCandidate = {
  ...shallowCandidate,
  candidate_id: "USM00072357-2025052000-supercell",
  station_id: "USM00072357",
  station_name: "Norman, Oklahoma",
  valid_time_utc: "2025-05-20T00:00:00Z",
  primary_story: "supercell_environment",
  primary_story_label: "Supercell-like environment",
  story_family: "deep_convection",
  rank_score: 93,
  confidence: "high",
  package_ready: true,
  story_scores: [
    {
      story: "supercell_environment",
      label: "Supercell-like environment",
      score_0_to_100: 93,
      support: "supported",
    },
    {
      story: "severe_thunderstorm_environment",
      label: "Severe thunderstorm environment",
      score_0_to_100: 88,
      support: "supported",
    },
  ],
  evidence: [
    {
      label: "Deep-convection ingredients",
      value: "strong",
      units: null,
      interpretation: "Instability and wind structure are worth trying in a triggered run.",
      supports_story: ["supercell_environment", "severe_thunderstorm_environment"],
      caveats: [],
    },
    ...shallowCandidate.evidence.slice(0, 2),
  ],
  interest_summary: "Strong deep-convection ingredients with observed wind support.",
  interest_reasons: [
    "Strong deep-convection ingredients with observed wind support.",
    "Observed 0-6 km shear gives storm-organization context.",
  ],
  features: {
    ...shallowCandidate.features,
    deep_tower_opportunity: 82,
    deep_tower_opportunity_support: "weak",
    deep_tower_opportunity_summary:
      "Experimental Deep-Tower evidence is high, but recent benchmark misses show this score is not a reliable recommendation to spend scout compute.",
  },
  discovery_bucket: "Deep convection",
};

const screeningInputsResponse = {
  inputs: [
    {
      station_id: "USM00072558",
      station_name: "Valley, Nebraska",
      cached_text_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data.txt",
      source_file_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data.txt",
      source_file_name: "USM00072558-data.txt",
      cached_status: "cached_extracted",
      sounding_count: 2,
      package_ready_count: 1,
      blocked_count: 1,
      latest_valid_time_utc: "2025-01-02T00:00:00Z",
    },
    {
      station_id: "USM00072357",
      station_name: "Norman, Oklahoma",
      cached_text_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072357-data.txt",
      source_file_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072357-data.txt",
      source_file_name: "USM00072357-data.txt",
      cached_status: "cached_extracted",
      sounding_count: 2,
      package_ready_count: 1,
      blocked_count: 1,
      latest_valid_time_utc: "2025-05-20T00:00:00Z",
    },
    {
      station_id: "USM00072426",
      station_name: "Wilmington, Ohio",
      cached_text_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072426-data.txt",
      source_file_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072426-data.txt",
      source_file_name: "USM00072426-data.txt",
      cached_status: "cached_extracted",
      sounding_count: 1,
      package_ready_count: 1,
      blocked_count: 0,
      latest_valid_time_utc: "2025-01-03T00:00:00Z",
    },
    {
      station_id: "USM00072440",
      station_name: "Springfield, Missouri",
      cached_text_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072440-data.txt",
      source_file_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072440-data.txt",
      source_file_name: "USM00072440-data.txt",
      cached_status: "cached_extracted",
      sounding_count: 1,
      package_ready_count: 1,
      blocked_count: 0,
      latest_valid_time_utc: "2025-01-04T00:00:00Z",
    },
  ],
};

const screeningResponse = {
  story: "all",
  screening_version: "test-screening-v1",
  generated_at: "2026-07-01T12:00:00Z",
  candidates: [
    shallowCandidate,
    deepConvectionCandidate,
    blockedCandidate,
    secondaryShallowCandidate,
    missingLclCandidate,
  ],
  total_candidate_count: 5,
  filtered_candidate_count: 5,
  sort_by: "best_match",
  sort_direction: "desc",
  filters: {
    station_id: null,
    station_ids: [],
    history_scope: "all_cached",
    latest_per_station: null,
    story_filter: "all",
    story_family: "all",
    support: "all",
    readiness: "all",
    station_search: "",
  },
  filter_trace: {
    selected_station_count: 4,
    selected_cached_soundings: 5,
    history_scope: "all_cached",
    latest_per_station: null,
    analyzed_soundings: 5,
    story_score_records: 8,
    stage_counts: {
      analyzed_soundings: 5,
      story_filter: 5,
      story_family: 5,
      support: 5,
      readiness: 5,
      station_search: 5,
      sorted_or_recommended: 5,
      limited: 5,
    },
    stages: [],
    station_distribution: [
      { station_id: "USM00072558", station_name: "Valley, Nebraska", count: 1 },
      { station_id: "USM00072357", station_name: "Norman, Oklahoma", count: 1 },
    ],
    top_excluded_reasons: [],
    applied_limit: 50,
  },
  caveats: ["screening_guidance_only"],
};

const testDeepConvectionStoryIds = new Set([
  "severe_thunderstorm_environment",
  "supercell_environment",
  "high_cape_pulse_storm",
  "dry_microburst_inverted_v",
  "squall_line_cold_pool_candidate",
  "elevated_convection",
]);

function screeningResponseForRequest(init?: RequestInit) {
  const request = JSON.parse(String(init?.body ?? "{}")) as {
    station_ids?: string[];
    history_scope?: "all_cached" | "latest_per_station";
    story_filter?: string;
    story_family?: string;
    support?: string;
    readiness?: string;
    station_search?: string;
    sort_by?: string;
    latest_per_station?: number;
    limit?: number;
  };
  const stationIds = new Set(request.station_ids ?? []);
  const historyScope = request.history_scope ?? "all_cached";
  const storyFilter = request.story_filter ?? "all";
  const storyFamily = request.story_family ?? "all";
  const support = request.support ?? "all";
  const readiness = request.readiness ?? "all";
  const stationSearch = (request.station_search ?? "").trim().toLowerCase();
  const sortBy = request.sort_by ?? "best_match";
  const limit = Number(request.limit ?? 100);
  const baseCandidates =
    stationIds.size > 0
      ? screeningResponse.candidates.filter((candidate) => stationIds.has(candidate.station_id))
      : [...screeningResponse.candidates];
  const storyFiltered = baseCandidates.filter((candidate) => {
    const score = storyScoreForTest(candidate, storyFilter, storyFamily);
    if (storyFilter !== "all" && (!score || !meaningfulStoryScoreForTest(score))) {
      return false;
    }
    if (
      storyFamily !== "all" &&
      !storyScoresForTest(candidate, storyFilter, storyFamily).some((scopeScore) =>
        meaningfulStoryScoreForTest(scopeScore),
      )
    ) {
      return false;
    }
    return true;
  });
  const supportFiltered = storyFiltered.filter((candidate) => {
    if (support === "all") return true;
    if (storyFilter === "deep_convection_trial" || storyFamily === "deep_convection") {
      return candidateDeepTowerSupportForTest(candidate) === support;
    }
    const scopedScores = storyScoresForTest(candidate, storyFilter, storyFamily);
    if (storyFilter === "all" && storyFamily === "all") {
      const score = storyScoreForTest(candidate, storyFilter, storyFamily);
      return Boolean(score && score.support === support);
    }
    return scopedScores.some((scopeScore) => scopeScore.support === support);
  });
  const readinessFiltered = supportFiltered.filter((candidate) => {
    if (readiness === "package_ready" && !candidate.package_ready) return false;
    if (readiness === "blocked" && candidate.package_ready) return false;
    return true;
  });
  const searchFiltered = readinessFiltered.filter((candidate) => {
    if (!stationSearch) return true;
    return [candidate.station_id, candidate.station_name, candidate.primary_story_label]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(stationSearch);
  });
  const candidates = searchFiltered
    .map((candidate) => candidateWithActiveFieldsForTest(candidate, storyFilter, storyFamily))
    .filter((candidate) => {
      return Boolean(candidate);
    })
    .sort((left, right) => compareCandidateFixtures(left, right, storyFilter, storyFamily, sortBy));
  const limitedCandidates = candidates.slice(0, limit);
  const stationDistribution = Array.from(
    limitedCandidates
      .reduce((counts, candidate) => {
        const current = counts.get(candidate.station_id) ?? {
          station_id: candidate.station_id,
          station_name: candidate.station_name,
          count: 0,
        };
        counts.set(candidate.station_id, { ...current, count: current.count + 1 });
        return counts;
      }, new Map<string, { station_id: string; station_name?: string | null; count: number }>())
      .values(),
  );
  return {
    ...screeningResponse,
    candidates: limitedCandidates,
    total_candidate_count: baseCandidates.length,
    filtered_candidate_count: candidates.length,
    sort_by: sortBy,
    filters: {
      station_id: null,
      station_ids: request.station_ids ?? [],
      history_scope: historyScope,
      latest_per_station:
        historyScope === "latest_per_station" ? (request.latest_per_station ?? 20) : null,
      story_filter: storyFilter,
      story_family: storyFamily,
      support,
      readiness,
      station_search: request.station_search ?? "",
    },
    filter_trace: {
      selected_station_count: new Set(baseCandidates.map((candidate) => candidate.station_id)).size,
      selected_cached_soundings: baseCandidates.length,
      history_scope: historyScope,
      latest_per_station:
        historyScope === "latest_per_station" ? (request.latest_per_station ?? 20) : null,
      analyzed_soundings: baseCandidates.length,
      story_score_records: baseCandidates.reduce(
        (total, candidate) => total + candidate.story_scores.length,
        0,
      ),
      stage_counts: {
        analyzed_soundings: baseCandidates.length,
        story_filter: storyFiltered.length,
        story_family: storyFiltered.length,
        support: supportFiltered.length,
        readiness: readinessFiltered.length,
        station_search: searchFiltered.length,
        sorted_or_recommended: candidates.length,
        limited: limitedCandidates.length,
      },
      stages: [],
      station_distribution: stationDistribution,
      top_excluded_reasons:
        storyFiltered.length < baseCandidates.length
          ? [
              {
                reason:
                  storyFamily !== "all"
                    ? `Story family: ${storyFamily}`
                    : `Story filter: ${storyFilter}`,
                count: baseCandidates.length - storyFiltered.length,
              },
            ]
          : [],
      applied_limit: limit,
    },
  };
}

function storyScoreForTest(
  candidate: (typeof screeningResponse.candidates)[number],
  storyFilter: string,
  storyFamily: string = "all",
) {
  return (
    [...storyScoresForTest(candidate, storyFilter, storyFamily)].sort(
      (left, right) => right.score_0_to_100 - left.score_0_to_100,
    )[0] ?? null
  );
}

function candidateWithActiveFieldsForTest(
  candidate: (typeof screeningResponse.candidates)[number],
  storyFilter: string,
  storyFamily: string,
) {
  const scopedScores = storyScoresForTest(candidate, storyFilter, storyFamily);
  const meaningfulScores = scopedScores.filter((score) => meaningfulStoryScoreForTest(score));
  const activeScore =
    [...(meaningfulScores.length > 0 ? meaningfulScores : scopedScores)].sort(
      (left, right) => right.score_0_to_100 - left.score_0_to_100,
    )[0] ?? null;
  const activeStory = activeScore?.story ?? candidate.primary_story;
  const activeLabel = activeScore?.label ?? candidate.primary_story_label;
  const deepScope = storyFilter === "deep_convection_trial" || storyFamily === "deep_convection";
  const deepOpportunity = candidateDeepTowerOpportunityForTest(candidate);
  const deepSupport = candidateDeepTowerSupportForTest(candidate);
  const deepSummary = candidateDeepTowerSummaryForTest(candidate);
  return {
    ...candidate,
    active_story: activeStory,
    active_story_label: activeLabel,
    display_story: activeLabel,
    matched_story_ids: meaningfulScores
      .sort((left, right) => right.score_0_to_100 - left.score_0_to_100)
      .map((score) => score.story),
    active_story_score: activeScore?.score_0_to_100 ?? candidate.rank_score,
    ingredient_score:
      deepScope && deepOpportunity !== null
        ? deepOpportunity
        : (activeScore?.score_0_to_100 ?? candidate.rank_score),
    ingredient_score_label: deepScope ? "Experimental Deep-Tower evidence" : "Ingredient score",
    active_story_support: deepScope ? deepSupport : (activeScore?.support ?? null),
    package_readiness: candidate.package_ready ? "package_ready" : "blocked",
    recipe_fit:
      "recipe_fit_status" in candidate ? candidate.recipe_fit_status : "partially_testable",
    top_reasons: deepScope && deepSummary ? [deepSummary] : (candidate.interest_reasons ?? []),
    top_caveats: candidate.caveats.slice(0, 2),
    evidence_summary: candidate.evidence.map((item) => item.interpretation).slice(0, 3),
  };
}

function storyScoresForTest(
  candidate: (typeof screeningResponse.candidates)[number],
  storyFilter: string,
  storyFamily: string = "all",
) {
  let scores = candidate.story_scores;
  if (storyFilter === "deep_convection_trial") {
    scores = scores.filter((score) => testDeepConvectionStoryIds.has(score.story));
  } else if (storyFilter !== "all") {
    scores = scores.filter((score) => score.story === storyFilter);
  }
  if (storyFamily !== "all") {
    scores = scores.filter((score) => storyFamilyForTest(score.story) === storyFamily);
  }
  if (storyFilter === "all" && storyFamily === "all") {
    const readyScores = scores.filter((score) => score.story !== "poor_or_incomplete_candidate");
    return readyScores.length > 0 ? readyScores : scores;
  }
  return scores;
}

function storyFamilyForTest(story: string) {
  if (testDeepConvectionStoryIds.has(story)) return "deep_convection";
  if (story === "needs_review" || story === "poor_or_incomplete_candidate") return "review";
  return "lower_atmosphere";
}

function meaningfulStoryScoreForTest(score: { score_0_to_100: number; support: string }) {
  return score.score_0_to_100 > 0 && score.support !== "unavailable";
}

function compareCandidateFixtures(
  left: (typeof screeningResponse.candidates)[number],
  right: (typeof screeningResponse.candidates)[number],
  storyFilter: string,
  storyFamily: string,
  sortBy: string,
) {
  const leftValue = candidateSortValueForTest(left, storyFilter, storyFamily, sortBy);
  const rightValue = candidateSortValueForTest(right, storyFilter, storyFamily, sortBy);
  if (leftValue === null && rightValue !== null) return 1;
  if (rightValue === null && leftValue !== null) return -1;
  if (leftValue !== null && rightValue !== null && leftValue !== rightValue) {
    const direction = sortBy === "estimated_lcl_height_m_agl" ? "asc" : "desc";
    return (leftValue < rightValue ? -1 : 1) * (direction === "asc" ? 1 : -1);
  }
  return (
    Number(right.package_ready) - Number(left.package_ready) ||
    (storyScoreForTest(right, storyFilter, storyFamily)?.score_0_to_100 ?? right.rank_score) -
      (storyScoreForTest(left, storyFilter, storyFamily)?.score_0_to_100 ?? left.rank_score) ||
    new Date(right.valid_time_utc).getTime() - new Date(left.valid_time_utc).getTime()
  );
}

function candidateSortValueForTest(
  candidate: (typeof screeningResponse.candidates)[number],
  storyFilter: string,
  storyFamily: string,
  sortBy: string,
) {
  if (sortBy === "best_match") {
    if (storyFilter === "deep_convection_trial" || storyFamily === "deep_convection") {
      return candidateDeepTowerOpportunityForTest(candidate);
    }
    return (
      storyScoreForTest(candidate, storyFilter, storyFamily)?.score_0_to_100 ?? candidate.rank_score
    );
  }
  if (sortBy === "valid_time") return new Date(candidate.valid_time_utc).getTime();
  if (sortBy === "station_name") return candidate.station_name ?? candidate.station_id;
  if (sortBy === "package_readiness") return Number(candidate.package_ready);
  const value = (candidate.features as Record<string, unknown>)[sortBy];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function candidateDeepTowerOpportunityForTest(
  candidate: (typeof screeningResponse.candidates)[number],
): number | null {
  const value = (candidate.features as Record<string, unknown>).deep_tower_opportunity;
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function candidateDeepTowerSupportForTest(
  candidate: (typeof screeningResponse.candidates)[number],
): string | null {
  const value = (candidate.features as Record<string, unknown>).deep_tower_opportunity_support;
  return typeof value === "string" ? value : null;
}

function candidateDeepTowerSummaryForTest(
  candidate: (typeof screeningResponse.candidates)[number],
): string | null {
  const value = (candidate.features as Record<string, unknown>).deep_tower_opportunity_summary;
  return typeof value === "string" && value.length > 0 ? value : null;
}

const savedCandidatesResponse = {
  saved_candidates: [
    {
      saved_candidate_id: "saved-USM00072558-2025010200",
      candidate: shallowCandidate,
      primary_story: "shallow_cumulus_candidate",
      tags: ["interesting-sounding"],
      notes: "",
      linked_run_ids: [],
      created_at: "2026-07-01T12:05:00Z",
      updated_at: "2026-07-01T12:05:00Z",
    },
  ],
};

const emptySavedCandidatesResponse = { saved_candidates: [] };

const igraCatalogResponse = {
  catalog: {
    generated_at: "2026-07-01T12:00:00Z",
    refreshed_at: "2026-07-01T12:00:00Z",
    region: { id: "great_plains_midwest", label: "Great Plains / Midwest" },
    zip_references: [
      {
        station_id: "USM00072558",
        station_name: "Valley, Nebraska",
        latitude: 41.32,
        longitude: -96.3669,
        elevation_m_msl: 351.5,
        filename: "USM00072558-data-beg2025.txt.zip",
        cached_status: "cached_extracted",
        url: "https://example.test/USM00072558-data-beg2025.txt.zip",
      },
      {
        station_id: "USM00072357",
        station_name: "Norman, Oklahoma",
        latitude: 35.22,
        longitude: -97.44,
        elevation_m_msl: 357,
        filename: "USM00072357-data-beg2025.txt.zip",
        cached_status: "cached_extracted",
        url: "https://example.test/USM00072357-data-beg2025.txt.zip",
      },
      {
        station_id: "USM00072426",
        station_name: "Wilmington, Ohio",
        latitude: 39.42,
        longitude: -83.82,
        elevation_m_msl: 317,
        filename: "USM00072426-data-beg2025.txt.zip",
        cached_status: "cached_extracted",
        url: "https://example.test/USM00072426-data-beg2025.txt.zip",
      },
      {
        station_id: "USM00072440",
        station_name: "Springfield, Missouri",
        latitude: 37.23,
        longitude: -93.38,
        elevation_m_msl: 387,
        filename: "USM00072440-data-beg2025.txt.zip",
        cached_status: "cached_extracted",
        url: "https://example.test/USM00072440-data-beg2025.txt.zip",
      },
      {
        station_id: "USM00072562",
        station_name: "North Platte, Nebraska",
        latitude: 41.13,
        longitude: -100.68,
        elevation_m_msl: 847,
        filename: "USM00072562-data-beg2025.txt.zip",
        cached_status: "not_cached",
        url: "https://example.test/USM00072562-data-beg2025.txt.zip",
      },
    ],
  },
};

const igraCacheResponse = {
  entries: [
    {
      station_id: "USM00072558",
      station_name: "Valley, Nebraska",
      data_txt_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data.txt",
      zip_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data-beg2025.txt.zip",
      sounding_count: 2,
      latest_valid_time_utc: "2025-01-02T00:00:00Z",
      size_bytes: 1234,
    },
    {
      station_id: "USM00072357",
      station_name: "Norman, Oklahoma",
      data_txt_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072357-data.txt",
      zip_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072357-data-beg2025.txt.zip",
      sounding_count: 2,
      latest_valid_time_utc: "2025-05-20T00:00:00Z",
      size_bytes: 1234,
    },
    {
      station_id: "USM00072426",
      station_name: "Wilmington, Ohio",
      data_txt_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072426-data.txt",
      zip_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072426-data-beg2025.txt.zip",
      sounding_count: 1,
      latest_valid_time_utc: "2025-01-03T00:00:00Z",
      size_bytes: 1234,
    },
    {
      station_id: "USM00072440",
      station_name: "Springfield, Missouri",
      data_txt_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072440-data.txt",
      zip_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072440-data-beg2025.txt.zip",
      sounding_count: 1,
      latest_valid_time_utc: "2025-01-04T00:00:00Z",
      size_bytes: 1234,
    },
  ],
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
  progress: {
    elapsed_wall_seconds: 300,
    model_time_seconds: 2922,
    total_model_time_seconds: 10800,
    percent_complete: 27.1,
    estimated_remaining_wall_seconds: 808.6,
    estimated_finish_at: "2026-05-22T15:34:04Z",
    last_refreshed_at: new Date().toISOString(),
    stale: false,
    model_time_source: "stdout model-minute progress",
    total_model_time_source: "namelist.input timax",
    unavailable_reason: null,
    caveats: [],
  },
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
  progress: {
    elapsed_wall_seconds: 1800,
    model_time_seconds: 10800,
    total_model_time_seconds: 10800,
    percent_complete: 100,
    estimated_remaining_wall_seconds: null,
    estimated_finish_at: null,
    last_refreshed_at: new Date().toISOString(),
    stale: false,
    model_time_source: "completed_run_state",
    total_model_time_source: "namelist.input timax",
    unavailable_reason: null,
    caveats: [],
  },
};

const emptyRunQueue = {
  schema_version: "1",
  entries: [],
  active_run_id: null,
  queued_count: 0,
  updated_at: new Date().toISOString(),
};

const runningRunQueue = {
  schema_version: "1",
  entries: [
    {
      run_id: "dry-run-001",
      manifest_path: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
      state: "running",
      queued_at: "2026-05-22T15:15:35Z",
      started_at: "2026-05-22T15:15:36Z",
      updated_at: new Date().toISOString(),
      message: "Running local CM1 process for dry-run-001.",
    },
  ],
  active_run_id: "dry-run-001",
  queued_count: 0,
  updated_at: new Date().toISOString(),
};

const autoIngestedRunQueue = {
  schema_version: "1",
  entries: [
    {
      run_id: "dry-run-quicklook",
      manifest_path: "/tmp/CloudChamber/runs/dry-run-quicklook/run_manifest.json",
      state: "ingested",
      queued_at: "2026-05-22T15:15:35Z",
      started_at: "2026-05-22T15:15:36Z",
      finished_at: "2026-05-22T15:45:36Z",
      updated_at: new Date().toISOString(),
      result_id: "result-dry-run-quicklook",
      cleanup_status: "queue_finalized_result_backing_run_retained",
      message:
        "Result auto-ingested. The queue entry is finalized; the local run directory is retained because it backs Results and Explore.",
    },
  ],
  active_run_id: null,
  queued_count: 0,
  updated_at: new Date().toISOString(),
};

const trustedFieldQuality = {
  qc: {
    field: "qc",
    source_field: "qc",
    quality_state: "trusted",
    reason: null,
    finite_count: 100,
    non_finite_count: 0,
    total_count: 100,
    caveats: [],
  },
  w: {
    field: "w",
    source_field: "w",
    quality_state: "trusted",
    reason: null,
    finite_count: 100,
    non_finite_count: 0,
    total_count: 100,
    caveats: [],
  },
  qr: {
    field: "qr",
    source_field: "qr",
    quality_state: "trusted",
    reason: null,
    finite_count: 100,
    non_finite_count: 0,
    total_count: 100,
    caveats: [],
  },
  surface_rain: {
    field: "surface_rain",
    source_field: "rain",
    quality_state: "trusted",
    reason: null,
    finite_count: 100,
    non_finite_count: 0,
    total_count: 100,
    caveats: [],
  },
  dbz: {
    field: "dbz",
    source_field: "dbz",
    quality_state: "trusted",
    reason: null,
    finite_count: 100,
    non_finite_count: 0,
    total_count: 100,
    caveats: [],
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
  run_configuration: defaultRunConfiguration,
  physical_question: "How do low-level moisture and surface heating shape shallow cumulus?",
  controls: {
    low_level_humidity: "baseline",
    surface_heating: "baseline",
  },
  status: "ingested_result_metadata",
  source_lifecycle_state: "completed",
  source_product_state: "completed_cm1_result",
  source_model: "CM1",
  input_source: "generated_reference",
  input_source_label: "Generated reference",
  observed_sounding: null,
  provenance_labels: [
    "source_model:CM1",
    "source_product_state:completed_cm1_result",
    "result_state:ingested_result_metadata",
  ],
  diagnostics_summary:
    "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
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
  surface_rain_present: true,
  max_surface_rain: 4.2,
  surface_rain_units: "mm",
  reflectivity_available: true,
  max_dbz: 30,
  field_quality_assessed: true,
  field_quality: trustedFieldQuality,
  science_summary: {
    first_cloud_time_seconds: 1800,
    first_cloud_time_label: "1,800 s",
    max_qc_kg_kg: 0.002192789688706398,
    max_qc_time_seconds: 2700,
    max_updraft_w_m_s: 6.866957187652588,
    max_updraft_time_seconds: 3600,
    min_downdraft_w_m_s: -4.21529483795166,
    min_downdraft_time_seconds: 4500,
    highest_cloud_top_m: 1940,
    highest_liquid_cloud_top_m: 1940,
    highest_coherent_cloud_object_top_m: 1940,
    coherent_cloud_object_source_fields: ["qc"],
    highest_raw_hydrometeor_envelope_top_m: 1940,
    highest_hydrometeor_envelope_top_m: 1940,
    hydrometeor_envelope_source_fields: ["qc"],
    rain_onset_time_seconds: 5400,
    max_qr_kg_kg: 2e-7,
    max_rain_or_surface_precip: 4.2,
    max_dbz_or_reflectivity_proxy: 30,
    latest_output_time_seconds: 10800,
    default_explore_time_index: 3,
    default_explore_time_seconds: 2700,
    field_quality_assessed: true,
    field_quality: trustedFieldQuality,
    localized_response: {
      available: true,
      support_state: "footprint_and_response_diagnostics_available",
      geometry: {
        pattern_sha256: "patch-sha",
        shape: "circle",
        center_x_m: 0,
        center_y_m: 0,
        radius_x_m: 1500,
        radius_y_m: 1500,
        taper_width_m: 500,
        ramp_seconds: 1800,
      },
      hfx_footprint: {
        source_field: "hfx",
        available: true,
        field_absent: false,
        units: "K m/s",
        quality_state: "trusted",
        finite_count: 64,
        non_finite_count: 0,
        total_count: 64,
        finite_fraction: 1,
        time_index: 1,
        time_seconds: 900,
        time_selection_method: "field_maximum_time",
        max_value: 0.048,
        max_x_m: 0,
        max_y_m: 0,
        max_distance_from_patch_center_m: 0,
        max_inside_patch_radius: true,
        max_region: "core",
        center_value: 0.048,
        core_mean: 0.04,
        taper_mean: 0.012,
        background_mean: 0.008,
        center_to_background_ratio: 6,
        core_to_background_ratio: 5,
        core_finite_count: 20,
        taper_finite_count: 12,
        background_finite_count: 32,
        inside_patch_mean: 0.04,
        outside_patch_mean: 0.008,
        center_to_outside_ratio: 6,
        inside_finite_count: 20,
        outside_finite_count: 44,
        total_finite_count: 64,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: [],
      },
      qfx_footprint: {
        source_field: "qfx",
        available: true,
        field_absent: false,
        units: "g/g m/s",
        quality_state: "trusted",
        finite_count: 64,
        non_finite_count: 0,
        total_count: 64,
        finite_fraction: 1,
        time_index: 1,
        time_seconds: 900,
        time_selection_method: "field_maximum_time",
        max_value: 0.0001,
        max_x_m: 0,
        max_y_m: 0,
        max_distance_from_patch_center_m: 0,
        max_inside_patch_radius: true,
        max_region: "core",
        center_value: 0.0001,
        core_mean: 0.00009,
        taper_mean: 0.00006,
        background_mean: 0.00005,
        center_to_background_ratio: 2,
        core_to_background_ratio: 1.8,
        core_finite_count: 20,
        taper_finite_count: 12,
        background_finite_count: 32,
        inside_patch_mean: 0.00009,
        outside_patch_mean: 0.00005,
        center_to_outside_ratio: 2,
        inside_finite_count: 20,
        outside_finite_count: 44,
        total_finite_count: 64,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: [],
      },
      near_surface_convergence: {
        available: true,
        source_fields: ["uinterp", "vinterp"],
        units: "s^-1",
        quality_state: "trusted",
        finite_count: 64,
        non_finite_count: 0,
        total_count: 64,
        finite_fraction: 1,
        time_index: 1,
        time_seconds: 900,
        time_selection_method: "maximum_finite_convergence_time",
        vertical_coordinate_name: "zf",
        vertical_level_index: 0,
        vertical_level_height_m: 50,
        max_convergence_s_1: 0.002,
        max_convergence_x_m: 0,
        max_convergence_y_m: 0,
        max_convergence_distance_from_patch_center_m: 0,
        max_convergence_inside_patch_radius: true,
        max_convergence_region: "core",
        max_convergence_time_series: [{ time_seconds: 900, value: 0.002 }],
        core_mean_convergence_s_1: 0.001,
        taper_mean_convergence_s_1: 0.0002,
        background_mean_convergence_s_1: 0.0001,
        core_to_background_convergence_ratio: 10,
        core_finite_count: 20,
        taper_finite_count: 12,
        background_finite_count: 32,
        inside_patch_mean_convergence_s_1: 0.001,
        outside_patch_mean_convergence_s_1: 0.0001,
        method: "finite_difference_near_surface_horizontal_convergence",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: [],
      },
      updraft: {
        source_field: "w",
        available: true,
        field_absent: false,
        units: "m/s",
        quality_state: "trusted",
        finite_count: 64,
        non_finite_count: 0,
        total_count: 64,
        finite_fraction: 1,
        time_index: 1,
        time_seconds: 900,
        time_selection_method: "field_maximum_time",
        max_value: 4.5,
        max_x_m: 0,
        max_y_m: 0,
        max_distance_from_patch_center_m: 0,
        max_inside_patch_radius: true,
        max_region: "core",
        center_value: 4.5,
        core_mean: 2.5,
        taper_mean: 0.6,
        background_mean: 0.3,
        center_to_background_ratio: 15,
        core_to_background_ratio: 8.333333333333334,
        core_finite_count: 20,
        taper_finite_count: 12,
        background_finite_count: 32,
        inside_patch_mean: 2.5,
        outside_patch_mean: 0.3,
        center_to_outside_ratio: 15,
        inside_finite_count: 20,
        outside_finite_count: 44,
        total_finite_count: 64,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: [],
      },
      cloud_water: {
        source_field: "qc",
        available: true,
        field_absent: false,
        units: "kg/kg",
        quality_state: "trusted",
        finite_count: 64,
        non_finite_count: 0,
        total_count: 64,
        finite_fraction: 1,
        time_index: 1,
        time_seconds: 900,
        time_selection_method: "field_maximum_time",
        max_value: 0.0012,
        max_x_m: 0,
        max_y_m: 0,
        max_distance_from_patch_center_m: 0,
        max_inside_patch_radius: true,
        max_region: "core",
        center_value: 0.0012,
        core_mean: 0.0008,
        taper_mean: 0.0002,
        background_mean: 0.0001,
        center_to_background_ratio: 12,
        core_to_background_ratio: 8,
        core_finite_count: 20,
        taper_finite_count: 12,
        background_finite_count: 32,
        inside_patch_mean: 0.0008,
        outside_patch_mean: 0.0001,
        center_to_outside_ratio: 12,
        inside_finite_count: 20,
        outside_finite_count: 44,
        total_finite_count: 64,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: [],
      },
      rain_water_aloft: {
        source_field: "qr",
        available: false,
        field_absent: true,
        units: null,
        time_seconds: null,
        max_value: null,
        max_x_m: null,
        max_y_m: null,
        max_distance_from_patch_center_m: null,
        max_inside_patch_radius: null,
        center_value: null,
        inside_patch_mean: null,
        outside_patch_mean: null,
        center_to_outside_ratio: null,
        inside_finite_count: 0,
        outside_finite_count: 0,
        total_finite_count: 0,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: ["qr_absent_for_localized_response"],
      },
      surface_rain: {
        source_field: "rain",
        available: false,
        field_absent: true,
        units: null,
        time_seconds: null,
        max_value: null,
        max_x_m: null,
        max_y_m: null,
        max_distance_from_patch_center_m: null,
        max_inside_patch_radius: null,
        center_value: null,
        inside_patch_mean: null,
        outside_patch_mean: null,
        center_to_outside_ratio: null,
        inside_finite_count: 0,
        outside_finite_count: 0,
        total_finite_count: 0,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: ["rain_absent_for_localized_response"],
      },
      reflectivity: {
        source_field: "dbz",
        available: false,
        field_absent: true,
        units: null,
        time_seconds: null,
        max_value: null,
        max_x_m: null,
        max_y_m: null,
        max_distance_from_patch_center_m: null,
        max_inside_patch_radius: null,
        center_value: null,
        inside_patch_mean: null,
        outside_patch_mean: null,
        center_to_outside_ratio: null,
        inside_finite_count: 0,
        outside_finite_count: 0,
        total_finite_count: 0,
        method: "patch_center_and_inside_outside_surface_field_summary",
        geometry_note: "centered_circle_with_raised_cosine_edge_taper_v0",
        caveats: ["dbz_absent_for_localized_response"],
      },
      caveats: [],
    },
    interesting_time_caveats: [],
    interesting_time_support_state: "supported",
  },
  interesting_times: [
    {
      key: "first_cloud",
      label: "First cloud",
      time_index: 2,
      time_seconds: 1800,
      source_field: "qc",
      source_diagnostic: "diagnostics.cloud.first_cloud_time_seconds",
      value: true,
      units: null,
      support_state: "supported",
      caveats: [],
    },
    {
      key: "max_qc",
      label: "Max cloud water",
      time_index: 3,
      time_seconds: 2700,
      source_field: "qc",
      source_diagnostic: "diagnostics.cloud.max_qc_kg_kg",
      value: 0.002192789688706398,
      units: "kg/kg",
      support_state: "supported",
      caveats: [],
    },
    {
      key: "highest_cloud_top",
      label: "Highest coherent cloud-object top",
      time_index: 3,
      time_seconds: 2700,
      source_field: "coherent_cloud_object:qc",
      source_diagnostic: "diagnostics.cloud.coherent_cloud_object_top_time_series",
      value: 1940,
      units: "m",
      support_state: "supported",
      caveats: [],
    },
    {
      key: "max_updraft_w",
      label: "Max updraft",
      time_index: 4,
      time_seconds: 3600,
      source_field: "w",
      source_diagnostic: "diagnostics.vertical_velocity.max_w_m_s",
      value: 6.866957187652588,
      units: "m/s",
      support_state: "supported",
      caveats: [],
    },
    {
      key: "min_downdraft_w",
      label: "Min downdraft",
      time_index: 5,
      time_seconds: 4500,
      source_field: "w",
      source_diagnostic: "diagnostics.vertical_velocity.min_w_m_s",
      value: -4.21529483795166,
      units: "m/s",
      support_state: "supported",
      caveats: [],
    },
    {
      key: "rain_onset",
      label: "Rain-water onset",
      time_index: 6,
      time_seconds: 5400,
      source_field: "qr",
      source_diagnostic: "diagnostics.rain.first_rain_time_seconds",
      value: true,
      units: null,
      support_state: "supported",
      caveats: [],
    },
    {
      key: "latest_output",
      label: "Latest output",
      time_index: 12,
      time_seconds: 10800,
      source_field: null,
      source_diagnostic: "output_manifest.time_index",
      value: null,
      units: null,
      support_state: "supported",
      caveats: [],
    },
    {
      key: "field_default_time",
      label: "Default Explore time",
      time_index: 3,
      time_seconds: 2700,
      source_field: null,
      source_diagnostic: "interesting_times.default_time_by_field",
      value: null,
      units: null,
      support_state: "supported",
      caveats: [],
    },
  ],
  default_time_by_field: {
    qc: {
      field: "qc",
      time_index: 3,
      time_seconds: 2700,
      source_interesting_time_key: "max_qc",
      support_state: "supported",
      caveats: [],
    },
  },
  interesting_time_caveats: [],
  caveats: ["CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"],
  output_file_summary: {
    netcdf_count: 14,
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
  diagnostics_summary:
    "no cloud formed; no rain water aloft detected; surface rain unavailable; reflectivity unavailable",
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
  surface_rain_present: null,
  max_surface_rain: null,
  surface_rain_units: null,
  reflectivity_available: false,
  max_dbz: null,
  science_summary: {
    ...resultCard.science_summary,
    first_cloud_time_seconds: null,
    first_cloud_time_label: null,
    max_qc_kg_kg: 0,
    max_qc_time_seconds: null,
    max_updraft_w_m_s: 1.949130654335022,
    max_updraft_time_seconds: 3600,
    min_downdraft_w_m_s: -1.0865488052368164,
    min_downdraft_time_seconds: 4500,
    rain_onset_time_seconds: null,
    max_qr_kg_kg: 0,
    max_rain_or_surface_precip: null,
    max_dbz_or_reflectivity_proxy: null,
    interesting_time_support_state: "fallback",
    interesting_time_caveats: ["no_cloud_formed"],
  },
  caveats: ["cloud_base_top_unavailable:no_cloud_cells"],
  created_at: "2026-05-22T19:20:00Z",
  completed_at: "2026-05-22T19:50:00Z",
  ingested_at: "2026-05-22T19:52:00Z",
  updated_at: "2026-05-22T19:52:00Z",
};

const cappedCard = {
  ...resultCard,
  result_id: "result-capped-cumulus",
  run_id: "dry-run-capped-suppressed-20260526015634",
  name: "Capped / Suppressed Cumulus quick-look",
  tags: ["capped", "quick-look"],
  notes: "Stronger-cap contrast candidate.",
  scenario_id: "capped-suppressed-cumulus",
  scenario_name: "Capped / Suppressed Cumulus",
  physical_question:
    "How does a stronger cap suppress or limit shallow-cumulus growth even when moisture and boundary-layer thermals are available?",
  controls: {
    low_level_humidity: "baseline",
    surface_heating: "baseline",
    cap_strength: "stronger",
  },
  diagnostics_summary:
    "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
  thermal_fate_label: "Capped / suppressed cumulus candidate",
  thermal_fate_confidence: "candidate",
  main_limiting_factor: "cap/stability",
  first_cloud_time_seconds: 2700,
  max_qc_kg_kg: 0.0004778,
  time_of_max_qc_seconds: 3600,
  max_w_m_s: 3.1,
  time_of_max_w_seconds: 3600,
  min_w_m_s: -1.8,
  time_of_min_w_seconds: 4500,
  rain_present: true,
  first_rain_time_seconds: 7200,
  science_summary: {
    ...resultCard.science_summary,
    first_cloud_time_seconds: 2700,
    max_qc_kg_kg: 0.0004778,
    max_qc_time_seconds: 3600,
    max_updraft_w_m_s: 3.1,
    max_updraft_time_seconds: 3600,
    min_downdraft_w_m_s: -1.8,
    min_downdraft_time_seconds: 4500,
    rain_onset_time_seconds: 7200,
    max_qr_kg_kg: 1e-7,
  },
  caveats: ["cap_layer_annotation_is_proxy_without_full_cap_diagnostics"],
  created_at: "2026-05-26T01:56:34Z",
  completed_at: "2026-05-26T02:15:00Z",
  ingested_at: "2026-05-26T02:20:00Z",
  updated_at: "2026-05-26T02:20:00Z",
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
  rain_present: null,
  first_rain_time_seconds: null,
  surface_rain_present: null,
  max_surface_rain: null,
  surface_rain_units: null,
  reflectivity_available: null,
  max_dbz: null,
  field_quality_assessed: true,
  field_quality: {
    qc: {
      field: "qc",
      source_field: "qc",
      quality_state: "unavailable",
      reason: "missing_qc_field",
      finite_count: 0,
      non_finite_count: 0,
      total_count: 0,
      caveats: ["missing_qc_field"],
    },
    w: {
      field: "w",
      source_field: "w",
      quality_state: "unavailable",
      reason: "missing_w_field",
      finite_count: 0,
      non_finite_count: 0,
      total_count: 0,
      caveats: ["missing_w_field"],
    },
    qr: {
      field: "qr",
      source_field: "qr",
      quality_state: "unavailable",
      reason: "qr_field_absent",
      finite_count: 0,
      non_finite_count: 0,
      total_count: 0,
      caveats: ["qr_field_absent"],
    },
  },
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

const observedSoundingResultCard = {
  ...resultCard,
  result_id: "result-observed-sounding",
  run_id: "dry-run-observed-sounding",
  name: "Uploaded Sounding — Valley, Nebraska",
  tags: ["observed-sounding", "valley"],
  scenario_id: "baseline-shallow-cumulus",
  scenario_name: "Uploaded Sounding",
  input_source: "observed_sounding",
  input_source_label: "Observed sounding: USM00072558 · Valley, Nebraska",
  science_summary: {
    ...resultCard.science_summary,
    max_updraft_w_m_s: 9.25,
    max_updraft_time_seconds: 3600,
    max_qc_kg_kg: 0.0014,
  },
  observed_sounding: {
    source_provider: "NOAA/NCEI IGRA",
    source_format: "igra_station_text",
    uploaded_filename: "USM00072558-data.txt",
    station_id: "USM00072558",
    station_name: "Valley, Nebraska",
    station_latitude: 41.32,
    station_longitude: -96.3669,
    station_elevation_m_msl: 351.5,
    valid_time_utc: "2026-06-30T00:00:00Z",
    source_vertical_coordinate_type: "geopotential_height",
    model_bottom_elevation_m_msl: 351.5,
    usable_levels: 48,
    lowest_model_z_m: 0,
    highest_model_z_m: 18000,
    wind_handling:
      "observed_sounding_winds; generated CM1 namelist uses isnd=7 so input_sounding u/v columns initialize the wind profile",
    validation_status: "valid",
    validation_errors: [],
    caveats: [],
    provenance: {},
  },
};

const deepConvectionResultCard = {
  ...observedSoundingResultCard,
  result_id: "result-deep-convection",
  run_id: "dry-run-deep-convection",
  name: "Observed Surface-Forced Experiment — Norman, Oklahoma",
  tags: ["deep-convection", "candidate"],
  scenario_name: "Observed Surface-Forced Experiment",
  run_recipe: "observed_surface_forced_evolution",
  run_recipe_display_name: "Observed Surface-Forced Evolution",
  trigger_type: null,
  expected_outputs: ["qc", "qr", "w", "dbz", "updraft_helicity"],
  candidate_screening: {
    candidate_id: "USM00072357-2025052000-supercell",
    primary_story: "supercell_environment",
    rank_score: 93,
  },
  diagnostics_summary:
    "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
  thermal_fate_label: "Growing cumulus",
  max_w_m_s: 15,
  time_of_max_w_seconds: 1800,
  first_rain_time_seconds: 1800,
  science_summary: {
    ...resultCard.science_summary,
    cloud_formed: true,
    deep_cloud_formed: true,
    deep_cloud_threshold_m: 8000,
    strong_updraft_formed: true,
    strong_updraft_threshold_m_s: 10,
    first_cloud_time_seconds: 900,
    time_of_first_deep_convection_seconds: 1800,
    max_qc_kg_kg: 0.0008,
    max_qc_time_seconds: 1800,
    max_updraft_w_m_s: 15,
    max_updraft_time_seconds: 1800,
    min_downdraft_w_m_s: -7,
    min_downdraft_time_seconds: 1800,
    highest_cloud_top_m: 10200,
    highest_liquid_cloud_top_m: 6200,
    highest_coherent_cloud_object_top_m: 10200,
    coherent_cloud_object_source_fields: ["qc", "qi", "qs"],
    highest_raw_hydrometeor_envelope_top_m: 10200,
    highest_hydrometeor_envelope_top_m: 10200,
    hydrometeor_envelope_source_fields: ["qc", "qi", "qs"],
    rain_onset_time_seconds: 1800,
    max_qr_kg_kg: 4e-7,
    latest_output_time_seconds: 2700,
    default_explore_time_index: 2,
    default_explore_time_seconds: 1800,
    cm1_outcome: "Deep convection formed with strong updraft and rain water aloft.",
    diagnostic_availability: [
      {
        key: "cold_pool_proxy",
        label: "Cold-pool proxy",
        support_state: "unsupported_missing_diagnostic",
        source_field: "theta",
        value: null,
        units: null,
        caveats: ["cold_pool_proxy_diagnostic_not_implemented"],
      },
    ],
  },
  interesting_times: [
    {
      key: "first_deep_convection",
      label: "First deep convection",
      time_index: 2,
      time_seconds: 1800,
      source_field: "coherent_cloud_object:qc+qi+qs",
      source_diagnostic: "diagnostics.cloud.coherent_cloud_object_top_time_series",
      value: true,
      units: null,
      support_state: "supported",
      caveats: [],
    },
    ...resultCard.interesting_times,
  ],
  default_time_by_field: {
    ...resultCard.default_time_by_field,
    w: {
      field: "w",
      time_index: 2,
      time_seconds: 1800,
      source_interesting_time_key: "max_updraft_w",
      support_state: "supported",
      caveats: [],
    },
  },
  candidate_hypothesis_comparison: {
    screened_as: "Supercell-like environment",
    ran_as: "Observed Surface-Forced Evolution",
    cm1_outcome: "Deep convection formed with strong updraft and rain water aloft.",
    match_status: "supported",
    match_status_label: "Supported",
    evidence: [
      "deep cloud formed",
      "coherent cloud-object top 10,200 m",
      "liquid cloud-water top 6,200 m",
      "max updraft 15 m/s",
    ],
    caveats: [
      "candidate_screening_is_a_pre_run_hypothesis",
      "candidate_match_uses_simple_v1_deep_convection_rules",
    ],
  },
};

const resultsResponse = {
  results: [
    resultCard,
    dryFailedCard,
    cappedCard,
    observedSoundingResultCard,
    missingDiagnosticsCard,
    emptyVisualizerCard,
  ],
};

const storageRuns = [
  {
    run_id: "dry-run-packaged",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "packaged",
    validation_status: "valid",
    product_state: "packaged_dry_run_output",
    run_configuration: defaultRunConfiguration,
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
    run_configuration: defaultRunConfiguration,
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
    run_configuration: defaultRunConfiguration,
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
    progress: completedRunStatus.progress,
  },
  {
    run_id: "dry-run-saved",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "completed",
    validation_status: "valid",
    product_state: "completed_cm1_result",
    run_configuration: defaultRunConfiguration,
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
    run_configuration: defaultRunConfiguration,
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
    progress: runningRunStatus.progress,
  },
  {
    run_id: "dry-run-no-output",
    scenario_id: "baseline-shallow-cumulus",
    scenario_name: "Baseline Shallow Cumulus",
    lifecycle_state: "completed",
    validation_status: "valid",
    product_state: "process_completed_no_output",
    run_configuration: defaultRunConfiguration,
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
    run_configuration: defaultRunConfiguration,
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
    run_configuration: null,
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

const resultDeletePreviewResponse = {
  result_id: "result-dry-run-quicklook",
  run_id: "dry-run-quicklook",
  run_directory: "/tmp/CloudChamber/runs/dry-run-quicklook",
  dry_run: true,
  deleted: false,
  size_bytes: 852 * 1024 ** 2,
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
      description: "Model-output NetCDF, stats files, and raw CM1 artifacts copied into this run.",
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
      description: "Derived product manifests, cached diagnostics, and visualization backing data.",
      present: true,
      item_count: 1,
    },
  ],
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

type MockVisualFieldName = "qc" | "w" | "qr" | "theta" | "temperature" | "qv" | "dbz" | "rain";
type MockPointFieldName = "qc" | "qr" | "qv" | "dbz" | "rain";

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
      shape: [4, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "w",
      canonical_field_name: "vertical_velocity",
      display_name: "Vertical velocity",
      units: "m/s",
      dimensions: ["time", "zf", "yh", "xh"],
      shape: [4, 3, 2, 3],
      native_grid: "zf/yh/xh",
      coordinate_names: { time: "time", vertical: "zf", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "qr",
      canonical_field_name: "rain_water",
      display_name: "Rain water",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [4, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "theta",
      canonical_field_name: "potential_temperature",
      display_name: "Potential temperature",
      units: "K",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [4, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "temperature",
      canonical_field_name: "temperature",
      display_name: "Temperature",
      units: "K",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [4, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "qv",
      canonical_field_name: "water_vapor",
      display_name: "Water vapor",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [4, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "dbz",
      canonical_field_name: "reflectivity",
      display_name: "Reflectivity",
      units: "dBZ",
      dimensions: ["time", "zh", "yh", "xh"],
      shape: [4, 2, 2, 3],
      native_grid: "zh/yh/xh",
      coordinate_names: { time: "time", vertical: "zh", y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation"],
    },
    {
      raw_field_name: "rain",
      canonical_field_name: "accumulated_surface_rain",
      display_name: "Accumulated surface rain",
      units: "mm",
      dimensions: ["time", "yh", "xh"],
      shape: [4, 2, 3],
      native_grid: "surface/yh/xh",
      coordinate_names: { time: "time", vertical: null, y: "yh", x: "xh" },
      time_coordinate_values: [0, 900, 1800, 2700],
      provenance,
      caveats: ["native_grid_view_no_interpolation", "surface_field_no_vertical_dimension"],
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
    qr: {
      field: "qr",
      time_index: 2,
      time_seconds: 1800,
      horizontal_level_index: 1,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_qr_native_grid_location",
      max_value: 0.000002,
      selected_time_index: null,
      selected_time_seconds: null,
      caveats: ["default_location_uses_field_maximum"],
    },
    theta: {
      field: "theta",
      time_index: 0,
      time_seconds: 0,
      horizontal_level_index: 1,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_theta_native_grid_location",
      max_value: 302,
      selected_time_index: null,
      selected_time_seconds: null,
      caveats: ["default_location_uses_field_maximum"],
    },
    temperature: {
      field: "temperature",
      time_index: 0,
      time_seconds: 0,
      horizontal_level_index: 1,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_temperature_native_grid_location",
      max_value: 289,
      selected_time_index: null,
      selected_time_seconds: null,
      caveats: ["default_location_uses_field_maximum"],
    },
    qv: {
      field: "qv",
      time_index: 1,
      time_seconds: 900,
      horizontal_level_index: 1,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_qv_native_grid_location",
      max_value: 0.012,
      selected_time_index: null,
      selected_time_seconds: null,
      caveats: ["default_location_uses_field_maximum"],
    },
    dbz: {
      field: "dbz",
      time_index: 2,
      time_seconds: 1800,
      horizontal_level_index: 1,
      vertical_x_index: 1,
      vertical_y_index: 2,
      source: "max_dbz_native_grid_location",
      max_value: 28,
      selected_time_index: null,
      selected_time_seconds: null,
      caveats: ["default_location_uses_field_maximum"],
    },
    rain: {
      field: "rain",
      time_index: 2,
      time_seconds: 1800,
      horizontal_level_index: 0,
      vertical_x_index: 0,
      vertical_y_index: 0,
      source: "surface_rain_domain_floor",
      max_value: 4.2,
      selected_time_index: null,
      selected_time_seconds: null,
      caveats: ["surface_field_rendered_on_domain_floor"],
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
      ...viewDefaultsResponse.fields,
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
      qr: {
        ...viewDefaultsResponse.fields.qr,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
      theta: {
        ...viewDefaultsResponse.fields.theta,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
      temperature: {
        ...viewDefaultsResponse.fields.temperature,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
      qv: {
        ...viewDefaultsResponse.fields.qv,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
      dbz: {
        ...viewDefaultsResponse.fields.dbz,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
        selected_time_index: Number(timeIndex),
        selected_time_seconds: Number(timeIndex) * 900,
      },
      rain: {
        ...viewDefaultsResponse.fields.rain,
        time_index: Number(timeIndex),
        time_seconds: Number(timeIndex) * 900,
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

const cappedFieldCatalogResponse = {
  ...fieldCatalogResponse,
  result_id: "result-capped-cumulus",
  run_id: "dry-run-capped-suppressed-20260526015634",
  scenario_id: "capped-suppressed-cumulus",
  available_fields: fieldCatalogResponse.available_fields.map((field) => ({
    ...field,
    provenance: {
      ...field.provenance,
      result_id: "result-capped-cumulus",
      run_id: "dry-run-capped-suppressed-20260526015634",
      scenario_id: "capped-suppressed-cumulus",
    },
  })),
};

const deepConvectionFieldCatalogResponse = {
  ...fieldCatalogResponse,
  result_id: "result-deep-convection",
  run_id: "dry-run-deep-convection",
  scenario_id: "baseline-shallow-cumulus",
  available_fields: fieldCatalogResponse.available_fields.map((field) => ({
    ...field,
    provenance: {
      ...field.provenance,
      result_id: "result-deep-convection",
      run_id: "dry-run-deep-convection",
    },
  })),
};

const deepConvectionViewDefaultsResponse = {
  ...viewDefaultsResponse,
  result_id: "result-deep-convection",
  run_id: "dry-run-deep-convection",
  preferred_field: "w",
};

function sliceResponse({
  field = "qc",
  orientation = "horizontal",
  timeIndex = 0,
  levelIndex = 0,
}: {
  field?: MockVisualFieldName;
  orientation?: "horizontal" | "vertical_x" | "vertical_y";
  timeIndex?: number;
  levelIndex?: number;
}) {
  const fieldMetadata =
    fieldCatalogResponse.available_fields.find((candidate) => candidate.raw_field_name === field) ??
    fieldCatalogResponse.available_fields[0];
  const units = fieldMetadata.units;
  const isSurface = field === "rain";
  const isVertical = orientation !== "horizontal" && !isSurface;
  const values =
    field === "w"
      ? [
          [1.5, 2.5, 3.5],
          [4.5, 5.5, 6.5],
        ]
      : mockSliceValues(field, timeIndex);
  const finiteValues = values
    .flat()
    .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  return {
    result_id: "result-dry-run-quicklook",
    run_id: "dry-run-quicklook",
    scenario_id: "baseline-shallow-cumulus",
    field: fieldMetadata,
    selection: {
      time_index: timeIndex,
      time_seconds: [0, 900, 1800, 2700][timeIndex] ?? 1800,
      orientation,
      selected_dimension: isSurface
        ? "surface"
        : orientation === "vertical_y"
          ? "xh"
          : orientation === "vertical_x"
            ? "yh"
            : "zh",
      selected_index: isSurface ? 0 : levelIndex,
      selected_coordinate_value: isSurface
        ? 0
        : orientation === "horizontal"
          ? ([0.4, 0.8, 1.2][levelIndex] ?? 0.8)
          : ([-3.2, 0, 3.2][levelIndex] ?? 0),
      level_units: orientation === "horizontal" ? "km" : null,
      level_coordinate_value:
        orientation === "horizontal"
          ? isSurface
            ? 0
            : ([0.4, 0.8, 1.2][levelIndex] ?? 0.8)
          : null,
      level_meters:
        orientation === "horizontal"
          ? isSurface
            ? 0
            : ([0.4, 0.8, 1.2][levelIndex] ?? 0.8) * 1000
          : null,
    },
    coordinate_units: isVertical ? { zh: "km", xh: "km" } : { yh: "km", xh: "km" },
    shape: [2, 3],
    dimension_order: isVertical ? ["zh", "xh"] : ["yh", "xh"],
    data_encoding: "json",
    values,
    stats: {
      min: Math.min(...finiteValues),
      max: Math.max(...finiteValues),
      mean: finiteValues.reduce((sum, value) => sum + value, 0) / finiteValues.length,
      finite_count: finiteValues.length,
      non_finite_count: values.flat().length - finiteValues.length,
    },
    provenance,
    caveats: ["native_grid_view_no_interpolation", "json_numeric_slice_mvp"],
    units,
  };
}

function mockSliceValues(
  field: MockVisualFieldName,
  timeIndex: number,
): Array<Array<number | null>> {
  if (field === "theta") {
    return timeIndex < 2
      ? [
          [300, 301, null],
          [302, 303, 304],
        ]
      : [
          [305, 306, 307],
          [308, 309, 310],
        ];
  }
  if (field === "temperature") {
    return timeIndex < 2
      ? [
          [285, 286, null],
          [287, 288, 289],
        ]
      : [
          [289, 290, 291],
          [292, 293, 294],
        ];
  }
  if (field === "qv") {
    return timeIndex < 2
      ? [
          [0.0101, 0.0104, null],
          [0.0107, 0.0109, 0.0112],
        ]
      : [
          [0.0113, 0.0115, 0.0118],
          [0.012, 0.0122, 0.0124],
        ];
  }
  if (field === "dbz") {
    return timeIndex < 2
      ? [
          [-8, 2, null],
          [8, 14, 20],
        ]
      : [
          [6, 12, 18],
          [22, 26, 30],
        ];
  }
  if (field === "rain") {
    return timeIndex < 2
      ? [
          [0, 0.2, null],
          [0.6, 0.8, 1.1],
        ]
      : [
          [1.3, 1.8, 2.1],
          [2.6, 3.4, 4.2],
        ];
  }
  return timeIndex < 2
    ? [
        [0, field === "qr" ? 2e-7 : 0.000002, null],
        [
          field === "qr" ? 4e-7 : 0.000004,
          field === "qr" ? 6e-7 : 0.000006,
          field === "qr" ? 8e-7 : 0.000008,
        ],
      ]
    : [
        [
          field === "qr" ? 1e-6 : 0.00001,
          field === "qr" ? 1.2e-6 : 0.000012,
          field === "qr" ? 1.4e-6 : 0.000014,
        ],
        [
          field === "qr" ? 1.6e-6 : 0.000016,
          field === "qr" ? 1.8e-6 : 0.000018,
          field === "qr" ? 2e-6 : 0.00002,
        ],
      ];
}

function pointCloudResponse({
  field = "qc",
  threshold = 0.000001,
  timeIndex = 2,
  points,
  fieldRange,
}: {
  field?: MockPointFieldName;
  threshold?: number;
  timeIndex?: number;
  points?: Array<[number, number, number, number]>;
  fieldRange?: { min: number; max: number; mean: number };
} = {}) {
  const fieldMetadata =
    fieldCatalogResponse.available_fields.find((candidate) => candidate.raw_field_name === field) ??
    fieldCatalogResponse.available_fields[0];
  const isSurface = field === "rain";
  const returnedPoints =
    points ??
    (threshold >= 1 || timeIndex === 0
      ? []
      : [
          [0, 0, field === "rain" ? 0 : 0.8, mockPointValue(field, 0)],
          [1, 1, field === "rain" ? 0 : 0.8, mockPointValue(field, 1)],
          [2, 1, field === "rain" ? 0 : 1.2, mockPointValue(field, 2)],
        ]);
  const values = returnedPoints.map((point) => point[3]);
  return {
    result_id: "result-dry-run-quicklook",
    run_id: "dry-run-quicklook",
    scenario_id: "baseline-shallow-cumulus",
    field: fieldMetadata,
    selection: {
      field,
      time_index: timeIndex,
      time_seconds: [0, 900, 1800, 2700][timeIndex] ?? 1800,
      threshold,
      max_points: 50000,
    },
    coordinate_units: isSurface
      ? { xh: "km", yh: "km", z: "km" }
      : { xh: "km", yh: "km", zh: "km" },
    coordinate_extents: {
      xh: { min: -3.2, max: 3.2, units: "km" },
      yh: { min: -3.2, max: 3.2, units: "km" },
      ...(isSurface
        ? { z: { min: 0.0, max: 3.0, units: "km" } }
        : { zh: { min: 0.0, max: 3.0, units: "km" } }),
    },
    point_order: ["x", "y", "z", "value"],
    points: returnedPoints,
    stats: {
      source_count: returnedPoints.length,
      returned_count: returnedPoints.length,
      field_min_value: (fieldRange ?? mockFieldRange(field)).min,
      field_max_value: (fieldRange ?? mockFieldRange(field)).max,
      field_mean_value: (fieldRange ?? mockFieldRange(field)).mean,
      field_finite_count: 24,
      field_non_finite_count: 0,
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
      provenance_label: `CM1-derived ${fieldMetadata.display_name.toLowerCase()} point cloud; native-grid threshold; visualizer interpretation`,
    },
    caveats: ["native_grid_thresholded_point_cloud", `visualizer_interpretation_of_cm1_${field}`],
  };
}

function mockFieldRange(field: MockPointFieldName): { min: number; max: number; mean: number } {
  const ranges: Record<MockPointFieldName, { min: number; max: number; mean: number }> = {
    qc: { min: 0, max: 0.000008, mean: 0.000002 },
    qr: { min: 0, max: 0.0000008, mean: 0.0000002 },
    qv: { min: 0.0098, max: 0.0124, mean: 0.0111 },
    dbz: { min: -8, max: 30, mean: 9.5 },
    rain: { min: 0, max: 4.2, mean: 1.4 },
  };
  return ranges[field];
}

function mockPointValue(field: MockPointFieldName, index: number): number {
  const values: Record<MockPointFieldName, number[]> = {
    qc: [0.000002, 0.000006, 0.000008],
    qr: [0.0000002, 0.0000006, 0.0000008],
    qv: [0.0104, 0.0112, 0.0124],
    dbz: [8, 18, 30],
    rain: [0.8, 2.2, 4.2],
  };
  return values[field][index] ?? values[field][0];
}

function mockFieldFromParam(value: string | null): MockVisualFieldName {
  if (
    value === "w" ||
    value === "qr" ||
    value === "theta" ||
    value === "temperature" ||
    value === "qv" ||
    value === "dbz" ||
    value === "rain"
  ) {
    return value;
  }
  return "qc";
}

function mockPointFieldFromParam(value: string | null): MockPointFieldName {
  if (value === "qr" || value === "qv" || value === "dbz" || value === "rain") {
    return value;
  }
  return "qc";
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
  const base = sliceResponse({
    field: "qc",
    orientation: "horizontal",
    timeIndex: 1,
    levelIndex: 1,
  });
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
  let runStatusRefreshCount = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/observed-soundings/parse") {
        return Promise.resolve(
          new Response(JSON.stringify(observedSoundingParseResponse), { status: 200 }),
        );
      }
      if (url === "/api/igra/recent/catalog") {
        return Promise.resolve(new Response(JSON.stringify(igraCatalogResponse), { status: 200 }));
      }
      if (url === "/api/igra/recent/refresh-catalog" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify(igraCatalogResponse.catalog), { status: 200 }),
        );
      }
      if (url === "/api/igra/recent/cache") {
        return Promise.resolve(new Response(JSON.stringify(igraCacheResponse), { status: 200 }));
      }
      if (url === "/api/igra/recent/cache-batch" && init?.method === "POST") {
        const body = JSON.parse(String(init.body ?? "{}")) as { station_ids?: string[] };
        return Promise.resolve(
          new Response(
            JSON.stringify({
              requested_limit: 10,
              requested_station_ids: body.station_ids ?? [],
              selected_count: body.station_ids?.length ?? 1,
              cached_entries: [igraCacheResponse.entries[0]],
              failed: [],
              remaining_uncached_count: 0,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/sounding-candidates/screening-inputs") {
        return Promise.resolve(
          new Response(JSON.stringify(screeningInputsResponse), { status: 200 }),
        );
      }
      if (url === "/api/sounding-candidates/analyze") {
        return Promise.resolve(
          new Response(JSON.stringify(screeningResponseForRequest(init)), { status: 200 }),
        );
      }
      if (url === "/api/sounding-candidates/saved" && init?.method === "POST") {
        const body = JSON.parse(String(init.body ?? "{}")) as {
          candidate?: typeof shallowCandidate;
          tags?: string[];
          notes?: string | null;
        };
        const candidate = body.candidate ?? shallowCandidate;
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...savedCandidatesResponse.saved_candidates[0],
              saved_candidate_id: candidate.candidate_id,
              candidate,
              primary_story: candidate.primary_story,
              tags: body.tags ?? [],
              notes: body.notes ?? null,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/sounding-candidates/saved") {
        return Promise.resolve(
          new Response(JSON.stringify(emptySavedCandidatesResponse), { status: 200 }),
        );
      }
      if (url.startsWith("/api/sounding-candidates/saved/") && init?.method === "DELETE") {
        return Promise.resolve(new Response(JSON.stringify({ removed: true }), { status: 200 }));
      }
      if (url.startsWith("/api/sounding-candidates/saved/") && init?.method === "PATCH") {
        const body = JSON.parse(String(init.body ?? "{}")) as {
          tags?: string[];
          notes?: string | null;
        };
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...savedCandidatesResponse.saved_candidates[0],
              tags: body.tags ?? [],
              notes: body.notes ?? null,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/dry-run-package") {
        return Promise.resolve(
          new Response(JSON.stringify(dryRunResponseForRequest(init)), { status: 200 }),
        );
      }
      if (url === "/api/runs/launch") {
        return Promise.resolve(new Response(JSON.stringify(runningRunStatus), { status: 200 }));
      }
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify(runningRunQueue), { status: 200 }));
      }
      if (url === "/api/runs/queue") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: false,
              available: false,
              message: "LAN worker is not configured.",
              cm1_env_keys: [],
              cm1_env_settings: [],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      if (url.startsWith("/api/runs/status")) {
        runStatusRefreshCount += 1;
        return Promise.resolve(
          new Response(
            JSON.stringify(runStatusRefreshCount === 1 ? runningRunStatus : completedRunStatus),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results/ingest") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              result_id: "result-dry-run-quicklook",
              run_id: "dry-run-001",
              diagnostics_summary:
                "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify(resultsResponse), { status: 200 }));
      }
      if (url === "/api/results/result-dry-run-quicklook/delete-preview") {
        return Promise.resolve(
          new Response(JSON.stringify(resultDeletePreviewResponse), { status: 200 }),
        );
      }
      if (url === "/api/results/result-dry-run-quicklook/delete") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...resultDeletePreviewResponse,
              dry_run: false,
              deleted: true,
              message: "Result and local run data deleted.",
            }),
            { status: 200 },
          ),
        );
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
      if (url === "/api/results/result-capped-cumulus/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(cappedFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url.startsWith("/api/results/result-capped-cumulus/visualization/defaults")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...viewDefaultsResponse,
              result_id: "result-capped-cumulus",
              run_id: "dry-run-capped-suppressed-20260526015634",
              scenario_id: "capped-suppressed-cumulus",
              preferred_field: "qc",
            }),
            { status: 200 },
          ),
        );
      }
      if (url.includes("/visualization/point-cloud")) {
        const parsed = new URL(url, "http://localhost");
        const isDryFailed = parsed.pathname.includes("result-dry-failed-cumulus");
        const requestedField = mockPointFieldFromParam(parsed.searchParams.get("field"));
        return Promise.resolve(
          new Response(
            JSON.stringify(
              pointCloudResponse({
                field: requestedField,
                threshold: Number(parsed.searchParams.get("threshold") ?? 0.000001),
                timeIndex: Number(parsed.searchParams.get("time_index") ?? 0),
                points: isDryFailed ? [] : undefined,
                fieldRange:
                  isDryFailed && requestedField === "qc" ? { min: 0, max: 0, mean: 0 } : undefined,
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
                field: mockFieldFromParam(parsed.searchParams.get("field")),
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
      return Promise.resolve(new Response("not found", { status: 404 }));
    }),
  );
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

async function openSelectedResultInExplore() {
  const resultDetail = await screen.findByLabelText("Result detail");
  fireEvent.click(await within(resultDetail).findByRole("button", { name: "Open in Explore" }));
}

describe("App", () => {
  it("renders guided Build setup with extensible experiment metadata", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Build and run a CM1 experiment" }),
    ).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Observed Soundings" })).toBeInTheDocument();
    expect(screen.getByLabelText("Experiment")).toHaveValue("__observed_sounding_upload__");
    expect(screen.queryByLabelText("Low-level humidity")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
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
    expect(screen.getByRole("heading", { name: "Configure this CM1 run" })).toBeInTheDocument();
    expect(
      screen.getByText("360 min runtime; 900 s output; 25 saved frames; 3 s timestep"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("64 x 64 x 100; dx/dy 100 m; top 18 km, dz 40 m to 600 m stretched"),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Local run launchpad" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Packages and runs needing action" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Not packaged yet").length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "No package has been created from the current setup in this browser session.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Build pipeline")).toBeInTheDocument();
    expect(screen.queryByText("Local experiment loop")).not.toBeInTheDocument();
    expect(screen.queryByText("namelist.input")).not.toBeInTheDocument();
  });

  it("uploads and reviews an observed IGRA sounding before package creation", async () => {
    let dryRunBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/observed-soundings/parse") {
        return Promise.resolve(
          new Response(JSON.stringify(observedSoundingParseResponse), { status: 200 }),
        );
      }
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
        return Promise.resolve(new Response(JSON.stringify(dryRunResponse), { status: 200 }));
      }
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      if (url === "/api/runs/queue") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
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

    expect(await screen.findByRole("heading", { name: "Observed Soundings" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Cached recommendations" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.queryByLabelText("IGRA station sounding-data file")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Upload IGRA station text" }));
    expect(screen.getByLabelText("IGRA station sounding-data file")).toBeInTheDocument();
    expect(screen.queryByLabelText("Low-level humidity")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Use uploaded sounding")).not.toBeInTheDocument();

    const file = new File(["#USM00072558 2025 01 02 00"], "USM00072558-data-beg2025.txt", {
      type: "text/plain",
    });
    fireEvent.change(screen.getByLabelText("IGRA station sounding-data file"), {
      target: { files: [file] },
    });

    expect(
      await screen.findByText("Observed sounding validated for package review"),
    ).toBeInTheDocument();
    expect(screen.getByText("Valley, Nebraska (USM00072558)")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Uploaded-sounding review"));
    expect(screen.getByText("USM00072558 · Valley, Nebraska")).toBeInTheDocument();
    expect(screen.getByText(/CM1 z=0 is station surface at 351.5 m MSL/)).toBeInTheDocument();
    expect(screen.getAllByText(/observed sounding winds/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Configure this CM1 run" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Experiment recipe")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Diagnostic set")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Surface heat flux")).toHaveValue("8.0e-3");
    expect(screen.getByLabelText("Surface moisture flux")).toHaveValue("5.2e-5");
    fireEvent.change(screen.getByLabelText("Surface heat flux"), {
      target: { value: "0.037" },
    });
    fireEvent.change(screen.getByLabelText("Surface moisture flux"), {
      target: { value: "9.5e-5" },
    });
    expect(screen.getByText(/Surface heat flux 0.037 K m\/s/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Add to run plan" }));
    expect(screen.getByRole("heading", { name: "Plan multiple CM1 runs" })).toBeInTheDocument();
    expect(
      within(screen.getByLabelText("Run plan")).queryByLabelText("Recipe"),
    ).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Create packages and queue selected runs" }),
    );

    await waitFor(() => {
      expect(dryRunBody).toContain('"run_recipe":"observed_surface_forced_evolution"');
      expect(dryRunBody).toContain('"diagnostic_set":"full"');
      expect(dryRunBody).toContain('"surface_heat_flux_k_m_s":"0.037"');
      expect(dryRunBody).toContain('"surface_moisture_flux_g_g_m_s":"9.5e-5"');
      expect(dryRunBody).toContain('"observed_sounding"');
      expect(dryRunBody).toContain('"station_id":"USM00072558"');
      expect(dryRunBody).toContain('"model_bottom_elevation_m_msl":351.5');
    });
  });

  it("stages deep-convection candidates as Deep-Tower Benchmark runs", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let dryRunBody = "";
    let screenBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/analyze") {
        screenBody = String(init?.body ?? "");
      }
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
      }
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });
    fireEvent.click(await screen.findByText("Advanced filters"));
    const storyFilter = await screen.findByLabelText("Story");
    expect(storyFilter).toHaveTextContent("Deep-convection stories");
    fireEvent.change(storyFilter, {
      target: { value: "deep_convection_trial" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));

    expect(await screen.findByText("Cached sounding analysis loaded")).toBeInTheDocument();
    expect(screenBody).toContain('"story_filter":"deep_convection_trial"');
    const deepCard = screen.getByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)");
    expect(deepCard).toHaveTextContent("Supercell-like environment");
    expect(deepCard).toHaveTextContent(
      "Experimental Deep-Tower evidence is high, but recent benchmark misses show this score is not a reliable recommendation to spend scout compute.",
    );
    expect(deepCard).toHaveTextContent("Experimental Deep-Tower evidence");

    fireEvent.click(within(deepCard).getByRole("button", { name: "Configure run" }));
    expect(screen.getByLabelText("Candidate details")).toHaveTextContent(
      "Experimental Deep-Tower evidence only.",
    );
    expect(screen.getByLabelText("Candidate details")).toHaveTextContent(
      "not a reliable recommendation to spend scout compute",
    );
    expect(screen.getByLabelText("Candidate details")).not.toHaveTextContent(
      "Recommended Deep-Tower scout",
    );
    fireEvent.click(screen.getByRole("button", { name: "Add to run plan" }));

    expect(
      await screen.findByText("Norman, Oklahoma (USM00072357) added to the run plan"),
    ).toBeInTheDocument();
    const runPlan = within(screen.getByLabelText("Run plan"));
    expect(runPlan.queryByLabelText("Recipe")).not.toBeInTheDocument();
    expect(runPlan.getByLabelText("Surface forcing")).toHaveValue("disabled");
    expect(runPlan.getByLabelText("Surface heat flux")).toHaveValue("0");
    expect(runPlan.getByLabelText("Surface moisture flux")).toHaveValue("0");
    expect(runPlan.getByLabelText("Duration")).toHaveValue("scout_2h");
    expect(runPlan.getByLabelText("Horizontal cells")).toHaveValue("cells_120");
    expect(runPlan.getByLabelText("Domain size")).toHaveValue("deep_tower_120km");
    expect(screen.getByText("deep_tower_benchmark_v0")).toBeInTheDocument();
    expect(
      screen.getByText(/Explicit initiation is supplied with CM1 iinit=3/i),
    ).toBeInTheDocument();
    expect(screen.getAllByLabelText(/^Run plan item /)).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Duplicate variant" }));
    expect(await screen.findByText("Run-plan variant duplicated")).toBeInTheDocument();
    expect(screen.getAllByLabelText(/^Run plan item /)).toHaveLength(2);

    fireEvent.click(
      screen.getByRole("button", { name: "Create packages and queue selected runs" }),
    );

    await waitFor(() => {
      expect(dryRunBody).toContain('"run_recipe":"deep_tower_benchmark"');
      expect(dryRunBody).toContain('"diagnostic_set":"full"');
      expect(dryRunBody).toContain('"duration":"scout_2h"');
      expect(dryRunBody).toContain('"horizontal_cell_count":"cells_120"');
      expect(dryRunBody).toContain('"domain_size":"deep_tower_120km"');
      expect(dryRunBody).toContain('"surface_forcing_mode":"disabled"');
      expect(dryRunBody).toContain('"surface_heat_flux_k_m_s":"0"');
      expect(dryRunBody).toContain('"surface_moisture_flux_g_g_m_s":"0"');
      expect(dryRunBody).toContain('"time_step_seconds":"6.0"');
      expect(dryRunBody).toContain('"candidate_screening"');
      expect(dryRunBody).toContain('"primary_story":"supercell_environment"');
      expect(dryRunBody).toContain('"candidate_id":"USM00072357-2025052000-supercell"');
      expect(dryRunBody).toContain('"ingredient_score":82');
      expect(dryRunBody).toContain(
        '"ingredient_score_label":"Experimental Deep-Tower evidence"',
      );
    });
  });

  it("does not present severe-story support as experimental Deep-Tower support", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    const lowOpportunityCandidate = {
      ...deepConvectionCandidate,
      candidate_id: "USM00072456-2025060300-low-deep-opportunity",
      station_id: "USM00072456",
      station_name: "Topeka, Kansas",
      valid_time_utc: "2025-06-03T00:00:00Z",
      rank_score: 91,
      story_scores: [
        {
          story: "supercell_environment",
          label: "Supercell-like environment",
          score_0_to_100: 91,
          support: "supported",
        },
        {
          story: "severe_thunderstorm_environment",
          label: "Severe thunderstorm environment",
          score_0_to_100: 84,
          support: "supported",
        },
      ],
      features: {
        ...deepConvectionCandidate.features,
        deep_tower_opportunity: 41,
        deep_tower_opportunity_support: "unavailable",
        deep_tower_opportunity_summary:
          "Experimental Deep-Tower evidence is low: the current heuristic does not surface this as a strong fixed-benchmark comparison case.",
      },
    };
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/analyze") {
        const request = JSON.parse(String(init?.body ?? "{}")) as {
          story_filter?: string;
          story_family?: string;
          support?: string;
        };
        const activeCandidate = candidateWithActiveFieldsForTest(
          lowOpportunityCandidate as (typeof screeningResponse.candidates)[number],
          request.story_filter ?? "all",
          request.story_family ?? "all",
        );
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...screeningResponse,
              candidates:
                request.support === "supported" ? [] : [activeCandidate],
              total_candidate_count: 1,
              filtered_candidate_count: request.support === "supported" ? 0 : 1,
              filters: {
                ...screeningResponse.filters,
                story_filter: request.story_filter ?? "all",
                story_family: request.story_family ?? "all",
                support: request.support ?? "all",
              },
              filter_trace: {
                ...screeningResponse.filter_trace,
                selected_station_count: 1,
                selected_cached_soundings: 1,
                analyzed_soundings: 1,
                story_score_records: 2,
                stage_counts: {
                  ...screeningResponse.filter_trace.stage_counts,
                  analyzed_soundings: 1,
                  story_filter: 1,
                  story_family: 1,
                  support: request.support === "supported" ? 0 : 1,
                  readiness: request.support === "supported" ? 0 : 1,
                  station_search: request.support === "supported" ? 0 : 1,
                  sorted_or_recommended: request.support === "supported" ? 0 : 1,
                  limited: request.support === "supported" ? 0 : 1,
                },
                station_distribution:
                  request.support === "supported"
                    ? []
                    : [
                        {
                          station_id: "USM00072456",
                          station_name: "Topeka, Kansas",
                          count: 1,
                        },
                      ],
              },
            }),
            { status: 200 },
          ),
        );
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });
    fireEvent.click(await screen.findByText("Advanced filters"));
    fireEvent.change(await screen.findByLabelText("Story"), {
      target: { value: "deep_convection_trial" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));

    const lowCard = await screen.findByLabelText("Sounding candidate Topeka, Kansas (USM00072456)");
    expect(lowCard).toHaveTextContent("Supercell-like environment");
    expect(lowCard).toHaveTextContent("Experimental Deep-Tower evidence");
    expect(lowCard).toHaveTextContent("41 %");
    expect(lowCard).toHaveTextContent(
      "Experimental Deep-Tower evidence is low: the current heuristic does not surface this as a strong fixed-benchmark comparison case.",
    );
    expect(lowCard).not.toHaveTextContent("stronger screening support");

    fireEvent.click(within(lowCard).getByRole("button", { name: "Configure run" }));
    const details = screen.getByLabelText("Candidate details");
    expect(details).toHaveTextContent("Low experimental Deep-Tower evidence.");
    expect(details).toHaveTextContent("Experimental Deep-Tower evidence");
    expect(details).toHaveTextContent("41 %");
    expect(within(lowCard).getByRole("button", { name: "Configure run" })).not.toBeDisabled();
  });

  it("keeps humid/rainy candidates with weak deep scores on observed quick-look", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let dryRunBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
      }
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });
    fireEvent.click(await screen.findByText("Advanced filters"));
    fireEvent.change(await screen.findByLabelText("Story"), {
      target: { value: "humid_rainy_candidate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));

    expect(await screen.findByText("Cached sounding analysis loaded")).toBeInTheDocument();
    const humidCard = screen.getByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)");
    expect(humidCard).toHaveTextContent("Humid / rainy");

    fireEvent.click(within(humidCard).getByRole("button", { name: "Configure run" }));
    fireEvent.click(screen.getByRole("button", { name: "Add to run plan" }));

    expect(
      await screen.findByText("Wilmington, Ohio (USM00072426) added to the run plan"),
    ).toBeInTheDocument();
    expect(
      within(screen.getByLabelText("Run plan")).queryByLabelText("Recipe"),
    ).not.toBeInTheDocument();
    expect(screen.getByText("observed_surface_forced_evolution_v0")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Create packages and queue selected runs" }),
    );

    await waitFor(() => {
      expect(dryRunBody).toContain('"run_recipe":"observed_surface_forced_evolution"');
      expect(dryRunBody).toContain('"primary_story":"humid_rainy_candidate"');
      expect(dryRunBody).toContain(
        '"candidate_id":"USM00072426-2025010300-humid-secondary-shallow"',
      );
    });
  });

  it("screens, saves, and uses observed-atmosphere candidates as package-review guidance", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let dryRunBody = "";
    let screenBody = "";
    let saveBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/analyze") {
        screenBody = String(init?.body ?? "");
      }
      if (url === "/api/sounding-candidates/saved" && init?.method === "POST") {
        saveBody = String(init.body ?? "");
      }
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
      }
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    expect(
      await screen.findByRole("heading", { name: "Find interesting soundings" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Choose the stations and history/)).toBeInTheDocument();
    expect(screen.getByText("Cached soundings ready to search")).toBeInTheDocument();
    expect(screen.queryByLabelText("Save into")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search selected soundings" })).toBeInTheDocument();

    fireEvent.click(screen.getByText("Advanced filters"));
    fireEvent.change(screen.getByLabelText("Story"), {
      target: { value: "shallow_cumulus_candidate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));

    expect(await screen.findByText("Cached sounding analysis loaded")).toBeInTheDocument();
    expect(screenBody).toContain('"story_filter":"shallow_cumulus_candidate"');
    expect(screen.getByRole("heading", { name: "Refined candidates" })).toBeInTheDocument();
    expect(screen.getByText(/Search filters applied/)).toBeInTheDocument();
    const valleyCard = screen.getByLabelText("Sounding candidate Valley, Nebraska (USM00072558)");
    expect(valleyCard).toHaveTextContent("Cloud-forming shallow cumulus");
    expect(valleyCard).toHaveTextContent("Package-ready");
    expect(valleyCard).toHaveTextContent("Why it surfaced");
    expect(valleyCard).toHaveTextContent("Good for a surface-forced run.");
    fireEvent.click(within(valleyCard).getByRole("button", { name: /Valley, Nebraska/ }));
    expect(
      screen.getByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)"),
    ).toHaveTextContent("Cloud-forming shallow cumulus");
    expect(
      screen.queryByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)"),
    ).not.toBeInTheDocument();
    const candidateDetails = screen.getByLabelText("Candidate details");
    expect(candidateDetails).toHaveTextContent("Run guidance");
    expect(candidateDetails).toHaveTextContent("Run fit");
    expect(candidateDetails).toHaveTextContent("Top limits");
    expect(candidateDetails).not.toHaveTextContent("Scores rank sounding ingredients only");
    expect(
      within(candidateDetails).getByText("All evidence").closest("details"),
    ).not.toHaveAttribute("open");
    expect(
      within(candidateDetails).getByText("Feature values").closest("details"),
    ).not.toHaveAttribute("open");
    expect(within(candidateDetails).queryByLabelText("Tags")).not.toBeInTheDocument();
    fireEvent.click(within(candidateDetails).getByRole("button", { name: "Save candidate" }));
    fireEvent.change(within(candidateDetails).getByLabelText("Tags"), {
      target: { value: "compare, rerun" },
    });
    fireEvent.change(within(candidateDetails).getByLabelText("Notes"), {
      target: { value: "Compare this against the humid case." },
    });
    fireEvent.click(within(candidateDetails).getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Sounding candidate saved")).toBeInTheDocument();
    expect(saveBody).toContain('"tags":["compare","rerun"]');
    expect(saveBody).toContain('"notes":"Compare this against the humid case."');
    fireEvent.click(screen.getByRole("tab", { name: /Saved candidates/ }));
    const savedCard = await screen.findByLabelText(
      "Saved sounding candidate Valley, Nebraska (USM00072558)",
    );
    expect(savedCard).toHaveTextContent("2 tags");
    expect(savedCard).toHaveTextContent("notes saved");
    fireEvent.click(within(savedCard).getByText("Tags and notes"));
    expect(within(savedCard).getByLabelText("Tags")).toHaveValue("compare, rerun");
    expect(within(savedCard).getByLabelText("Notes")).toHaveValue(
      "Compare this against the humid case.",
    );

    fireEvent.click(within(savedCard).getByRole("button", { name: "Configure run" }));
    const selectedRunSetup = screen.getByLabelText("Selected sounding run setup");
    const runPlanSection = screen.getByLabelText("Run plan");
    expect(
      savedCard.compareDocumentPosition(selectedRunSetup) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      selectedRunSetup.compareDocumentPosition(runPlanSection) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Add to run plan" }));

    expect(
      await screen.findByText("Valley, Nebraska (USM00072558) added to the run plan"),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Create packages and queue selected runs" }),
    );

    await waitFor(() => {
      expect(dryRunBody).toContain('"user_tags":["compare","rerun"]');
      expect(dryRunBody).toContain('"user_notes":"Compare this against the humid case."');
      expect(dryRunBody).toContain('"saved_notes":"Compare this against the humid case."');
    });

    fireEvent.click(within(savedCard).getByRole("button", { name: "Remove saved" }));
    expect(await screen.findByText("Saved sounding candidate removed")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Saved sounding candidate Valley, Nebraska (USM00072558)"),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Cached recommendations" }));
    fireEvent.change(screen.getByLabelText("Story"), {
      target: { value: "needs_review" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));
    const normanCard = await screen.findByLabelText(
      "Sounding candidate Norman, Oklahoma (USM00072357)",
    );
    expect(normanCard).toHaveTextContent("Blocked");
    expect(within(normanCard).getByRole("button", { name: "Configure run" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Story"), {
      target: { value: "all" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));
    const selectedValleyCard = await screen.findByLabelText(
      "Sounding candidate Valley, Nebraska (USM00072558)",
    );
    expect(
      screen.getByRole("heading", { name: "Screened cached soundings" }),
    ).toBeInTheDocument();

    fireEvent.click(within(selectedValleyCard).getByRole("button", { name: "Configure run" }));
    fireEvent.click(screen.getByRole("button", { name: "Add to run plan" }));
    expect(
      await screen.findByText("Valley, Nebraska (USM00072558) added to the run plan"),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Create packages and queue selected runs" }),
    );

    await waitFor(() => {
      expect(dryRunBody).toContain('"observed_sounding"');
      expect(dryRunBody).toContain('"candidate_screening"');
      expect(dryRunBody).toContain('"primary_story":"shallow_cumulus_candidate"');
      expect(dryRunBody).toContain('"candidate_id":"USM00072558-2025010200-shallow"');
    });
  });

  it("loads saved sounding candidates as soon as Observed Soundings is selected", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/saved" && !init?.method) {
        return Promise.resolve(
          new Response(JSON.stringify(savedCandidatesResponse), { status: 200 }),
        );
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    expect(await screen.findByRole("tab", { name: "Cached recommendations" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(
      screen.queryByLabelText("Saved sounding candidate Valley, Nebraska (USM00072558)"),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Saved candidates/ }));
    expect(
      await screen.findByLabelText("Saved sounding candidate Valley, Nebraska (USM00072558)"),
    ).toBeInTheDocument();
    expect(screen.queryByText("No saved candidates yet.")).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalledWith("/api/igra/recent/refresh-catalog", expect.anything());
    expect(fetch).not.toHaveBeenCalledWith("/api/sounding-candidates/analyze", expect.anything());
  });

  it("updates saved candidate tags and notes through the metadata drawer", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let savedStore: Array<(typeof savedCandidatesResponse.saved_candidates)[number]> = [];
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/saved" && init?.method === "POST") {
        const body = JSON.parse(String(init.body ?? "{}")) as {
          candidate?: typeof shallowCandidate;
          tags?: string[];
          notes?: string | null;
        };
        const candidate = body.candidate ?? shallowCandidate;
        const saved = {
          ...savedCandidatesResponse.saved_candidates[0],
          saved_candidate_id: candidate.candidate_id,
          candidate,
          primary_story: candidate.primary_story,
          story_scores: candidate.story_scores,
          features: candidate.features,
          evidence: candidate.evidence,
          caveats: candidate.caveats,
          tags: body.tags ?? [],
          notes: body.notes ?? "",
        };
        savedStore = [saved];
        return Promise.resolve(new Response(JSON.stringify(saved), { status: 200 }));
      }
      if (url.startsWith("/api/sounding-candidates/saved/") && init?.method === "PATCH") {
        const savedCandidateId = url.split("/").at(-1);
        const body = JSON.parse(String(init.body ?? "{}")) as {
          tags?: string[];
          notes?: string | null;
        };
        const updated = savedStore.map((saved) =>
          saved.saved_candidate_id === savedCandidateId
            ? {
                ...saved,
                tags: body.tags ?? saved.tags,
                notes: body.notes ?? saved.notes,
              }
            : saved,
        );
        savedStore = updated;
        return Promise.resolve(new Response(JSON.stringify(savedStore[0]), { status: 200 }));
      }
      if (url === "/api/sounding-candidates/saved") {
        return Promise.resolve(
          new Response(JSON.stringify({ saved_candidates: savedStore }), { status: 200 }),
        );
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });
    fireEvent.click(screen.getByText("Advanced filters"));
    fireEvent.change(screen.getByLabelText("Story"), {
      target: { value: "shallow_cumulus_candidate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));

    const valleyCard = await screen.findByLabelText(
      "Sounding candidate Valley, Nebraska (USM00072558)",
    );
    fireEvent.click(within(valleyCard).getByRole("button", { name: /Valley, Nebraska/ }));
    const candidateDetails = screen.getByLabelText("Candidate details");
    expect(within(candidateDetails).queryByLabelText("Tags")).not.toBeInTheDocument();
    fireEvent.click(within(candidateDetails).getByRole("button", { name: "Save candidate" }));
    fireEvent.change(within(candidateDetails).getByLabelText("Tags"), {
      target: { value: "Maybe rerun" },
    });
    fireEvent.change(within(candidateDetails).getByLabelText("Notes"), {
      target: { value: "Keep this one in the candidate notebook." },
    });
    fireEvent.click(within(candidateDetails).getByRole("button", { name: "Save" }));

    fireEvent.click(screen.getByRole("tab", { name: /Saved candidates/ }));
    const savedCard = await screen.findByLabelText(
      "Saved sounding candidate Valley, Nebraska (USM00072558)",
    );
    expect(savedCard).toHaveTextContent("1 tag");
    expect(savedCard).toHaveTextContent("notes saved");
    expect(within(savedCard).queryByText("Working set")).not.toBeInTheDocument();
    fireEvent.click(within(savedCard).getByText("Tags and notes"));
    expect(within(savedCard).getByLabelText("Tags")).toHaveValue("Maybe rerun");
    expect(within(savedCard).getByLabelText("Notes")).toHaveValue(
      "Keep this one in the candidate notebook.",
    );
    fireEvent.click(within(savedCard).getByRole("button", { name: "Deep convection candidates" }));
    await waitFor(() =>
      expect(within(savedCard).getByLabelText("Tags")).toHaveValue(
        "Maybe rerun, Deep convection candidates",
      ),
    );
    fireEvent.click(within(savedCard).getByRole("button", { name: "Save tags and notes" }));

    expect(await screen.findByText("Saved sounding candidate updated")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });
    fireEvent.click(screen.getByRole("tab", { name: /Saved candidates/ }));

    const reloadedSavedCard = await screen.findByLabelText(
      "Saved sounding candidate Valley, Nebraska (USM00072558)",
    );
    fireEvent.click(within(reloadedSavedCard).getByText("Tags and notes"));
    expect(within(reloadedSavedCard).getByLabelText("Tags")).toHaveValue(
      "Maybe rerun, Deep convection candidates",
    );
    expect(within(reloadedSavedCard).getByLabelText("Notes")).toHaveValue(
      "Keep this one in the candidate notebook.",
    );
  });

  it("uses family-scoped deep-convection defaults across the selected cached soundings", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let analyzeBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/analyze") {
        analyzeBody = String(init?.body ?? "");
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });
    fireEvent.change(await screen.findByDisplayValue("Best overall recommendations"), {
      target: { value: "deep_convection" },
    });
    expect(screen.getByText("Advanced filters").closest("details")).not.toHaveAttribute("open");
    expect(
      screen.getByText("Search intent changed; search selected soundings"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Search selected soundings" }));

    expect(await screen.findByText("Recommendation run complete")).toBeInTheDocument();
    expect(analyzeBody).toContain('"story_filter":"all"');
    expect(analyzeBody).toContain('"story_family":"deep_convection"');
    expect(analyzeBody).toContain('"support":"all"');
    expect(analyzeBody).toContain('"history_scope":"all_cached"');
    expect(analyzeBody).toContain('"latest_per_station":null');
    expect(analyzeBody).toContain('"limit":100');
    expect(
      screen.getByText(
        (content) =>
          content.includes("5 analyzed from 5 selected cached soundings") &&
          content.includes("4 stations") &&
          content.includes("all cached history") &&
          content.includes("2 matched deep convection stories") &&
          content.includes("2 shown"),
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)"),
    ).toBeInTheDocument();
  });

  it("searches and caches explicitly selected stations", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let analyzeBody = "";
    let cacheBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/analyze") {
        analyzeBody = String(init?.body ?? "");
      }
      if (url === "/api/igra/recent/cache-batch" && init?.method === "POST") {
        cacheBody = String(init.body ?? "");
      }
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    fireEvent.click(await screen.findByRole("button", { name: "Choose stations" }));
    fireEvent.click(await screen.findByLabelText(/Norman, Oklahoma/));
    fireEvent.click(await screen.findByLabelText(/North Platte, Nebraska/));

    fireEvent.click(screen.getByRole("button", { name: "Cache selected stations" }));
    await waitFor(() => {
      expect(cacheBody).toContain('"station_ids":["USM00072357","USM00072562"]');
    });

    fireEvent.change(screen.getByLabelText("History scope"), {
      target: { value: "latest_per_station" },
    });
    fireEvent.change(screen.getByLabelText("Latest soundings per station"), {
      target: { value: "3" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search selected soundings" }));

    await waitFor(() => {
      expect(analyzeBody).toContain('"station_ids":["USM00072357","USM00072562"]');
      expect(analyzeBody).toContain('"history_scope":"latest_per_station"');
      expect(analyzeBody).toContain('"latest_per_station":3');
    });
    expect(
      (await screen.findAllByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)")).length,
    ).toBeGreaterThan(0);
  });

  it("shows secondary family candidates with the scoped story ingredient score", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    fireEvent.click(screen.getByText("Advanced filters"));
    fireEvent.change(screen.getByLabelText("Story family"), {
      target: { value: "deep_convection" },
    });
    fireEvent.change(screen.getByLabelText("Evidence tier"), {
      target: { value: "weak" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));

    const wilmingtonCard = await screen.findByLabelText(
      "Sounding candidate Wilmington, Ohio (USM00072426)",
    );
    expect(wilmingtonCard).toHaveTextContent("High-CAPE pulse storm");
    expect(wilmingtonCard).not.toHaveTextContent("Primary: Humid / rainy");
    expect(wilmingtonCard).toHaveTextContent("48.9 % experimental deep-tower evidence");
    expect(wilmingtonCard).toHaveTextContent("optional Deep-Tower benchmark context");
    expect(wilmingtonCard).toHaveTextContent(
      "Experimental Deep-Tower evidence is caveated: some cloud-depth ingredients are present, but the fixed benchmark response is uncertain.",
    );
    expect(
      screen.getByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)"),
    ).toHaveTextContent("82 % experimental deep-tower evidence");

    fireEvent.click(within(wilmingtonCard).getByRole("button", { name: /Wilmington, Ohio/ }));
    const candidateDetails = screen.getByLabelText("Candidate details");
    expect(candidateDetails).toHaveTextContent("High-CAPE pulse storm");
    expect(candidateDetails).toHaveTextContent("Screened story family");
    expect(candidateDetails).toHaveTextContent("Deep convection stories");
    expect(candidateDetails).toHaveTextContent("Primary story");
    expect(candidateDetails).toHaveTextContent("Humid / rainy");
    expect(candidateDetails).toHaveTextContent("48.9 %");
  });

  it("keeps secondary story matches visible and sorts missing LCL last", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Search selected soundings" }));
    expect(await screen.findByText("Recommendation run complete")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Advanced filters"));
    fireEvent.change(screen.getByLabelText("Story"), {
      target: { value: "shallow_cumulus_candidate" },
    });
    expect(screen.getByText("Story filter changed; apply advanced filters")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));
    expect(
      await screen.findByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Sort"), {
      target: { value: "estimated_lcl_height_m_agl" },
    });
    expect(screen.getByText("Sort changed; apply advanced filters")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Apply advanced filters" }));
    await waitFor(() => {
      const candidateCards = screen.getAllByLabelText(/^Sounding candidate /);
      const visibleOrder = candidateCards.map((card) => card.textContent ?? "");
      const validLclIndex = visibleOrder.findIndex((text) => text.includes("Wilmington, Ohio"));
      const missingLclIndex = visibleOrder.findIndex((text) =>
        text.includes("Springfield, Missouri"),
      );
      expect(validLclIndex).toBeGreaterThanOrEqual(0);
      expect(missingLclIndex).toBeGreaterThan(validLclIndex);
    });
  });

  it("sends explicit high-detail run configuration and shows package cost", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/dry-run-package") {
        expect(init?.body).toEqual(expect.stringContaining('"duration":"standard_12h"'));
        expect(init?.body).toEqual(expect.stringContaining('"horizontal_cell_count":"cells_256"'));
        expect(init?.body).toEqual(expect.stringContaining('"domain_size":"wide_12km"'));
        expect(init?.body).toEqual(expect.stringContaining('"output_cadence":"detailed_5min"'));
        expect(init?.body).toEqual(expect.stringContaining('"diagnostic_set":"full"'));
        expect(init?.body).toEqual(expect.stringContaining('"surface_heat_flux_k_m_s":"0.04"'));
        expect(init?.body).toEqual(
          expect.stringContaining('"surface_moisture_flux_g_g_m_s":"1.1e-4"'),
        );
        return Promise.resolve(new Response(JSON.stringify(deepDryRunResponse), { status: 200 }));
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
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.change(await screen.findByLabelText("Domain size"), {
      target: { value: "wide_12km" },
    });
    expect(screen.getAllByText(/better suited to larger compute/i).length).toBeGreaterThan(0);

    fireEvent.change(await screen.findByLabelText("Duration"), {
      target: { value: "standard_12h" },
    });
    fireEvent.change(screen.getByLabelText("Horizontal cells"), {
      target: { value: "cells_256" },
    });
    fireEvent.change(screen.getByLabelText("Output cadence"), {
      target: { value: "detailed_5min" },
    });
    expect(screen.queryByLabelText("Diagnostic set")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Surface heat flux"), {
      target: { value: "0.04" },
    });
    fireEvent.change(screen.getByLabelText("Surface moisture flux"), {
      target: { value: "1.1e-4" },
    });

    fireEvent.click(screen.getByTestId("create-package-btn"));

    const packageReview = await screen.findByTestId("package-review-panel");
    expect(packageReview).toHaveTextContent("Pre-run validation");
    expect(packageReview).toHaveTextContent("Valid with caveats");
    expect(packageReview).toHaveTextContent("generated_reference_lower_atmosphere_v1");
    expect(packageReview).toHaveTextContent("256 x 256 x 100");
    expect(packageReview).toHaveTextContent("dx/dy 50 m");
    expect(packageReview).toHaveTextContent("300 s output");
    expect(packageReview).toHaveTextContent("145 saved frames");
    expect(packageReview).toHaveTextContent("92.8x output volume");
  });

  it("shows blocked pre-run validation details when package creation is refused", async () => {
    const blockedReport = {
      ...defaultPreRunValidationReport,
      status: "blocked",
      selected_hypothesis: {
        hypothesis_id: "humid_rainy_candidate",
        story_id: "humid_rainy_candidate",
        story_label: "Humid / rainy",
        ingredient_score: 82,
        predicted_output_signature: ["qc", "qr", "rain", "dbz"],
      },
      selected_run_recipe: {
        run_recipe: "observed_surface_forced_evolution",
        recipe_id: "observed_surface_forced_evolution_v0",
        display_name: "Observed Surface-Forced Evolution",
        recipe_display_name: "Observed Surface-Forced Evolution v0",
        assumption_set_id: "observed_surface_forced_evolution_v0_assumptions",
        assumption_mode: "observed_surface_forced_evolution",
      },
      hypothesis_recipe_alignment: {
        status: "blocked",
        reasons: ["Surface-flux values must be reviewed before this package can be created."],
        missing_assumptions: ["surface_flux_values_need_manual_review"],
        missing_outputs: [],
      },
      blocking_errors: ["Surface-flux values must be reviewed before this package can be created."],
      caveats: [],
    };
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/dry-run-package") {
        expect(init?.body).toEqual(expect.stringContaining("baseline-shallow-cumulus"));
        return Promise.resolve(
          new Response(
            JSON.stringify({
              detail: {
                message:
                  "Pre-run validation blocked package creation: Surface-flux values must be reviewed before this package can be created.",
                pre_run_validation_report: blockedReport,
              },
            }),
            { status: 400 },
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
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.click(await screen.findByTestId("create-package-btn"));

    expect(
      await screen.findByText(/Pre-run validation blocked package creation/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Pre-run validation report")).toHaveTextContent("Blocked");
    expect(screen.getByLabelText("Pre-run validation report")).toHaveTextContent(
      "Surface-flux values must be reviewed before this package can be created.",
    );
    expect(screen.getByLabelText("Pre-run validation report")).toHaveTextContent(
      "surface_flux_values_need_manual_review",
    );
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

    expect(await screen.findByRole("heading", { name: "Observed Soundings" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
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
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    const runMonitor = screen.getByText("Run monitor").closest("details");
    expect(runMonitor).toHaveAttribute("open");
    expect(await screen.findByRole("heading", { name: "Local run launchpad" })).toBeInTheDocument();
    expect(screen.queryByText("Local experiment loop")).not.toBeInTheDocument();
    expect(screen.getByText("Build pipeline")).toBeInTheDocument();
    expect(screen.getByText("Packages and runs needing action")).toBeInTheDocument();
    expect(screen.getByText("Ready to run")).toBeInTheDocument();
    expect(screen.getAllByText("Ready to ingest").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Running").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Result pending").length).toBeGreaterThan(0);
    expect(screen.queryByText("Ready to review")).not.toBeInTheDocument();
    expect(screen.queryByText("Quick-look shallow cumulus")).not.toBeInTheDocument();
    expect(screen.queryByText("Ingested result")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run with local CM1" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run on LAN worker" })).not.toBeInTheDocument();
    expect(screen.getByTestId("create-package-btn")).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Create run package" })).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Preview cleanup" }).length).toBeGreaterThan(0);
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

  it("queues a stored package for serial local CM1 execution", async () => {
    const queuedPackage = {
      ...runningRunQueue,
      entries: [
        {
          ...runningRunQueue.entries[0],
          run_id: "dry-run-old-launch",
          manifest_path: "/tmp/CloudChamber/runs/dry-run-old-launch/run_manifest.json",
          state: "launch_failed",
          message: "Previous local launch failed.",
        },
        {
          ...runningRunQueue.entries[0],
          run_id: "dry-run-packaged",
          manifest_path: "/tmp/CloudChamber/runs/dry-run-packaged/run_manifest.json",
          message: "Running local CM1 process for dry-run-packaged.",
        },
      ],
      active_run_id: "dry-run-packaged",
    };
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
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify(queuedPackage), { status: 200 }));
      }
      if (url === "/api/runs/queue") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      if (url.startsWith("/api/runs/status")) {
        return Promise.resolve(new Response(JSON.stringify(runningRunStatus), { status: 200 }));
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: false,
              available: false,
              message: "LAN worker is not configured.",
              cm1_env_keys: [],
              cm1_env_settings: [],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    const queueButtons = await screen.findAllByRole("button", { name: "Queue local CM1 run" });
    fireEvent.click(queueButtons[0]);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/runs/queue",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            manifest_path: "/tmp/CloudChamber/runs/dry-run-packaged/run_manifest.json",
          }),
        }),
      );
    });
    expect(await screen.findByText(/Running dry-run-packaged/)).toBeInTheDocument();
    expect(screen.getAllByText("dry-run-packaged").length).toBeGreaterThan(0);
    expect(screen.queryByText("dry-run-old-launch")).not.toBeInTheDocument();
  });

  it("shows auto-ingested queue entries without implying result-backed data was deleted", async () => {
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
      if (url === "/api/runs/queue") {
        return Promise.resolve(new Response(JSON.stringify(autoIngestedRunQueue), { status: 200 }));
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: false,
              available: false,
              message: "LAN worker is not configured.",
              cm1_env_keys: [],
              cm1_env_settings: [],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Build" }));

    expect(await screen.findByText("Auto-ingested")).toBeInTheDocument();
    expect(screen.getByText(/package retained for Results\/Explore/)).toBeInTheDocument();
    expect(
      screen.queryByText("Result was auto-ingested. Refresh Results if it is not visible."),
    ).not.toBeInTheDocument();
  });

  it("does not show contradictory ingest actions for a current auto-ingested package", async () => {
    const currentAutoIngestedQueue = {
      ...autoIngestedRunQueue,
      entries: [
        {
          ...autoIngestedRunQueue.entries[0],
          run_id: "dry-run-001",
          manifest_path: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
        },
      ],
    };
    const currentAutoIngestedRun = {
      ...storageRuns[1],
      run_id: "dry-run-001",
      path: "/tmp/CloudChamber/runs/dry-run-001",
      manifest_path: "/tmp/CloudChamber/runs/dry-run-001/run_manifest.json",
    };
    const currentOnlyInventory = {
      ...storageInventoryResponse,
      runs: [currentAutoIngestedRun],
      largest_runs: [currentAutoIngestedRun],
    };

    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify({ results: [] }), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(new Response(JSON.stringify(currentOnlyInventory), { status: 200 }));
      }
      if (url === "/api/dry-run-package") {
        return Promise.resolve(
          new Response(JSON.stringify(dryRunResponseForRequest(init)), { status: 200 }),
        );
      }
      if (url === "/api/runs/queue") {
        return Promise.resolve(
          new Response(JSON.stringify(currentAutoIngestedQueue), { status: 200 }),
        );
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: false,
              available: false,
              message: "LAN worker is not configured.",
              cm1_env_keys: [],
              cm1_env_settings: [],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "Create run package" }));

    let card: HTMLElement | null = null;
    await waitFor(() => {
      card =
        screen
          .getAllByText("dry-run-001")
          .map((node) => node.closest("article"))
          .find((article): article is HTMLElement => Boolean(article)) ?? null;
      expect(card).toBeTruthy();
    });
    if (!card) throw new Error("Expected current auto-ingested package card.");
    expect(within(card).getByText("Auto-ingested")).toBeInTheDocument();
    expect(within(card).queryByText("Ready to ingest")).not.toBeInTheDocument();
    expect(within(card).queryByText("Not ingested")).not.toBeInTheDocument();
    expect(within(card).queryByRole("button", { name: "Ingest output" })).not.toBeInTheDocument();
    expect(within(card).queryByRole("button", { name: "Preview cleanup" })).not.toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Open result" })).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Open in Explore" })).toBeInTheDocument();
  });

  it("automatically copies back, ingests, and cleans LAN worker output after completion", async () => {
    let ingested = false;
    const workerRun = {
      ...storageRuns[0],
      run_id: "dry-run-worker-completed",
      scenario_id: "humid-vigorous-cumulus",
      scenario_name: "Humid Vigorous Cumulus",
      run_configuration: defaultRunConfiguration,
      category: "running",
      manifest_path: "/tmp/CloudChamber/runs/dry-run-worker-completed/run_manifest.json",
      path: "/tmp/CloudChamber/runs/dry-run-worker-completed",
      worker_state: "completed",
      worker_message: "CM1 completed with output artifacts.",
      worker_netcdf_count: 14,
      worker_raw_artifact_count: 0,
      worker_remote_dir: "/worker/runs/dry-run-worker-completed",
      worker_started_at: "2026-07-01T04:30:07Z",
      worker_finished_at: "2026-07-01T04:39:23Z",
      worker_progress: {
        elapsed_wall_seconds: 556,
        model_time_seconds: 10800,
        total_model_time_seconds: 10800,
        percent_complete: 100,
        estimated_remaining_wall_seconds: null,
        estimated_finish_at: null,
        last_refreshed_at: new Date().toISOString(),
        stale: false,
        model_time_source: "completed_worker_state",
        total_model_time_source: "namelist.input timax",
        unavailable_reason: null,
        caveats: [],
      },
    };
    const workerResult = {
      ...resultCard,
      result_id: "result-dry-run-worker-completed",
      run_id: "dry-run-worker-completed",
      name: "Humid Vigorous Cumulus quick-look",
      scenario_id: "humid-vigorous-cumulus",
      scenario_name: "Humid Vigorous Cumulus",
    };

    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: true,
              available: true,
              message: "LAN worker configured.",
              cm1_env_keys: ["OMP_NUM_THREADS"],
              cm1_env_settings: ["OMP_NUM_THREADS=16"],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...storageInventoryResponse,
              runs: [workerRun],
              largest_runs: [workerRun],
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ results: ingested ? [workerResult] : [] }), {
            status: 200,
          }),
        );
      }
      if (url === "/api/lan-worker/collect") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              run_id: "dry-run-worker-completed",
              state: "ready_for_local_ingest",
              message: "LAN worker output copied back to this MacBook.",
              netcdf_count: 14,
              raw_artifact_count: 0,
              ready_for_ingest: true,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/results/ingest") {
        ingested = true;
        return Promise.resolve(
          new Response(
            JSON.stringify({
              result_id: "result-dry-run-worker-completed",
              run_id: "dry-run-worker-completed",
              diagnostics_summary:
                "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/lan-worker/cleanup") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              run_id: "dry-run-worker-completed",
              state: "worker_cleanup_complete",
              message: "LAN worker run directory was removed.",
              netcdf_count: 0,
              raw_artifact_count: 0,
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Build" }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/lan-worker/collect",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            manifest_path: "/tmp/CloudChamber/runs/dry-run-worker-completed/run_manifest.json",
          }),
        }),
      );
      expect(fetch).toHaveBeenCalledWith(
        "/api/results/ingest",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            manifest_path: "/tmp/CloudChamber/runs/dry-run-worker-completed/run_manifest.json",
          }),
        }),
      );
      expect(fetch).toHaveBeenCalledWith(
        "/api/lan-worker/cleanup",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            manifest_path: "/tmp/CloudChamber/runs/dry-run-worker-completed/run_manifest.json",
          }),
        }),
      );
    });
    expect(screen.queryByRole("button", { name: "Copy back and ingest" })).not.toBeInTheDocument();
  });

  it("shows parsed LAN worker model-time progress when worker status includes it", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify({ results: [] }), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      if (url === "/api/dry-run-package") {
        return Promise.resolve(new Response(JSON.stringify(dryRunResponse), { status: 200 }));
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: true,
              available: true,
              message: "LAN worker configured.",
              cm1_env_keys: [],
              cm1_env_settings: [],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/lan-worker/start" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              run_id: "dry-run-001",
              state: "running",
              message: "CM1 is running on the LAN worker.",
              netcdf_count: 0,
              raw_artifact_count: 0,
              started_at: "2026-05-22T15:15:36Z",
              progress: {
                elapsed_wall_seconds: 600,
                model_time_seconds: 3600,
                total_model_time_seconds: 10800,
                percent_complete: 33.3,
                estimated_remaining_wall_seconds: 1200,
                estimated_finish_at: "2026-05-22T15:45:36Z",
                last_refreshed_at: new Date().toISOString(),
                stale: false,
                model_time_source: "stdout model-minute progress",
                total_model_time_source: "namelist.input timax",
                unavailable_reason: null,
                caveats: [],
              },
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.click(await screen.findByTestId("create-package-btn"));

    await screen.findByRole("heading", { name: "Package ready for CM1" });
    const packageQueuePanel = screen.getByLabelText("Package and queue");
    const lanLaunchButton = within(packageQueuePanel).getByRole("button", {
      name: "Run on LAN worker",
    });
    expect(lanLaunchButton).toBeEnabled();
    expect(
      within(screen.getByLabelText("LAN worker run status")).queryByRole("button", {
        name: "Run on LAN worker",
      }),
    ).not.toBeInTheDocument();
    fireEvent.click(lanLaunchButton);

    await waitFor(() => {
      expect(screen.getByText("Worker model-time progress").nextElementSibling).toHaveTextContent(
        "60 min / 180 min (33.3%)",
      );
      expect(screen.getByText("Worker ETA").nextElementSibling).toHaveTextContent(
        "20 min remaining",
      );
    });
  });

  it("shows LAN worker model-time progress as unavailable when status has no parsed progress", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(new Response(JSON.stringify({ results: [] }), { status: 200 }));
      }
      if (url === "/api/storage/inventory") {
        return Promise.resolve(
          new Response(JSON.stringify(storageInventoryResponse), { status: 200 }),
        );
      }
      if (url === "/api/dry-run-package") {
        return Promise.resolve(new Response(JSON.stringify(dryRunResponse), { status: 200 }));
      }
      if (url === "/api/lan-worker/config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              configured: true,
              available: true,
              message: "LAN worker configured.",
              cm1_env_keys: [],
              cm1_env_settings: [],
              custom_launch_command: false,
            }),
            { status: 200 },
          ),
        );
      }
      if (url === "/api/lan-worker/start" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              run_id: "dry-run-001",
              state: "running",
              message: "CM1 is running on the LAN worker.",
              netcdf_count: 0,
              raw_artifact_count: 0,
              started_at: "2026-05-22T15:15:36Z",
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.click(await screen.findByTestId("create-package-btn"));

    await screen.findByRole("heading", { name: "Package ready for CM1" });
    fireEvent.click(
      within(screen.getByLabelText("Package and queue")).getByRole("button", {
        name: "Run on LAN worker",
      }),
    );

    await waitFor(() => {
      expect(screen.getByText("Worker model-time progress").nextElementSibling).toHaveTextContent(
        "Model-time progress unavailable from current status.",
      );
    });
  });

  it("requests a dry-run package and displays generated files without claiming CM1 ran", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
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
    expect(screen.getByRole("button", { name: "Create another package" })).toHaveClass(
      "secondary-button",
    );
    const packageQueuePanel = screen.getByLabelText("Package and queue");
    expect(
      within(packageQueuePanel).getByRole("button", { name: "Queue local CM1 run" }),
    ).toBeEnabled();
    expect(
      within(packageQueuePanel).getByRole("button", { name: "Run on LAN worker" }),
    ).toBeDisabled();
    expect(
      within(packageQueuePanel).getByText(/LAN worker execution is unavailable/i),
    ).toBeInTheDocument();
    expect(
      within(screen.getByLabelText("LAN worker run status")).queryByRole("button", {
        name: "Run on LAN worker",
      }),
    ).not.toBeInTheDocument();
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
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
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
    expect(screen.getByText("Elapsed runtime").nextElementSibling).toHaveTextContent("5 min");
    expect(screen.getByText("Model-time progress").nextElementSibling).toHaveTextContent(
      "48.7 min / 180 min (27.1%)",
    );
    expect(screen.getByText("ETA").nextElementSibling).toHaveTextContent("13 min 29 s remaining");
    expect(screen.getByText("Progress source").nextElementSibling).toHaveTextContent(
      "stdout model-minute progress",
    );
    expect(screen.getByText("CM1 started")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "View status / logs" }));

    await waitFor(() => {
      expect(screen.getAllByText("Completed CM1 result").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Output summary").nextElementSibling).toHaveTextContent("14 NetCDF");
    expect(screen.getByText("Final elapsed runtime").nextElementSibling).toHaveTextContent(
      "30 min",
    );
    expect(screen.getByText("Model-time progress").nextElementSibling).toHaveTextContent(
      "180 min / 180 min (100.0%)",
    );
    expect(screen.getAllByText(/IEEE_INVALID_FLAG/).length).toBeGreaterThan(0);
    expect(screen.getByTestId("ingest-results-btn")).toBeEnabled();

    fireEvent.click(screen.getByTestId("ingest-results-btn"));

    expect(await screen.findByText(/Result metadata created/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open in Results" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Open in Explore" }).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Ingested").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      "/api/runs/queue",
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
      if (url === "/api/runs/queue" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "CM1 executable is missing. Missing: cm1.exe" }), {
            status: 400,
          }),
        );
      }
      if (url === "/api/runs/queue") {
        return Promise.resolve(new Response(JSON.stringify(emptyRunQueue), { status: 200 }));
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.click(await screen.findByTestId("create-package-btn"));
    fireEvent.click(await screen.findByTestId("launch-cm1-btn"));

    expect(await screen.findByRole("alert")).toHaveTextContent("CM1 executable is missing");
    const packageReview = screen.getByTestId("package-review-panel");
    expect(packageReview).toHaveTextContent("Package ready");
    expect(packageReview).toHaveTextContent("/tmp/CloudChamber/runs/dry-run-001");
    expect(packageReview).toHaveTextContent("/tmp/CloudChamber/runs/dry-run-001/run_manifest.json");
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
    expect(screen.queryByRole("tab", { name: "Notebook" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Compare" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Storage" })).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Review ingested cloud experiments, scan result cards, and open results for explanation.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Results list")).toBeInTheDocument();
    const resultDetail = screen.getByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("Quick-look shallow cumulus");
    expect(screen.getAllByText(/Validated reference baseline/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Minor caveat/).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Open in Explore" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Quick-look shallow cumulus" })).toBeInTheDocument();
    expect(screen.getAllByText(/Baseline Shallow Cumulus/).length).toBeGreaterThan(0);
    expect(resultDetail).toHaveTextContent(
      "Short evolution; Local 6 km; Scout 64 x 64; 100 m dx/dy; Standard 15 min",
    );
    expect(
      screen.getAllByText(
        "cloud formed; rain water aloft detected; surface rain reached ground; reflectivity available",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Cloud formed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Rain water aloft detected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Reached ground; max 4.2 mm").length).toBeGreaterThan(0);
    expect(screen.getByText("1,800 s")).toBeInTheDocument();
    expect(screen.getAllByText("2.193e-3 kg/kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6.867 m/s").length).toBeGreaterThan(0);
    expect(screen.getAllByText("-4.215 m/s").length).toBeGreaterThan(0);
    expect(resultDetail).toHaveTextContent("Science landmarks");
    expect(resultDetail).toHaveTextContent("Surface forcing response");
    expect(resultDetail).toHaveTextContent("Differential patch evidence");
    expect(resultDetail).toHaveTextContent("circle · 1,500 m radius · 500 m taper");
    expect(resultDetail).toHaveTextContent("Footprint and response diagnostics available");
    expect(resultDetail).toHaveTextContent("6.00x center/background");
    expect(resultDetail).toHaveTextContent("2.000e-3 s^-1");
    expect(resultDetail).toHaveTextContent("4.5 m/s; max 0 m from center at 900 s");
    expect(resultDetail).toHaveTextContent("Interesting times");
    expect(resultDetail).toHaveTextContent("Highest coherent cloud-object top");
    expect(resultDetail).toHaveTextContent("1,940 m");
    expect(resultDetail).toHaveTextContent("Rain-water onset");
    expect(resultDetail).toHaveTextContent("Default Explore time");
    expect(resultDetail).toHaveTextContent("2,700 s");
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

  it("renders science summary and observed-sounding source metadata in Results", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(screen.getAllByText(/first cloud 1,800 s/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/max qc 2.193e-3 kg\/kg/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/max updraft 6.867 m\/s/).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Observed sounding: USM00072558 · Valley, Nebraska").length,
    ).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Uploaded Sounding — Valley, Nebraska" }));
    const resultDetail = screen.getByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("Uploaded Sounding");
    expect(resultDetail).toHaveTextContent("Observed sounding: USM00072558 · Valley, Nebraska");
    expect(resultDetail).toHaveTextContent("Input source");
  });

  it("renders deep-convection candidate comparison and opens Explore on updraft time", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ results: [deepConvectionResultCard] }), { status: 200 }),
        );
      }
      if (url === "/api/results/result-deep-convection/visualization/fields") {
        return Promise.resolve(
          new Response(JSON.stringify(deepConvectionFieldCatalogResponse), { status: 200 }),
        );
      }
      if (url.startsWith("/api/results/result-deep-convection/visualization/defaults")) {
        return Promise.resolve(
          new Response(JSON.stringify(deepConvectionViewDefaultsResponse), { status: 200 }),
        );
      }
      if (url.includes("/visualization/point-cloud")) {
        return Promise.resolve(
          new Response(JSON.stringify(pointCloudResponse({ field: "qc", timeIndex: 2 })), {
            status: 200,
          }),
        );
      }
      if (url.includes("/visualization/slice")) {
        return Promise.resolve(
          new Response(JSON.stringify(sliceResponse({ field: "w", timeIndex: 2 })), {
            status: 200,
          }),
        );
      }
      return Promise.resolve(new Response("not found", { status: 404 }));
    });

    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("Observed Surface-Forced Experiment — Norman, Oklahoma");
    expect(resultDetail).toHaveTextContent("Deep convection formed");
    expect(resultDetail).toHaveTextContent("Screening vs CM1");
    expect(resultDetail).toHaveTextContent("Supercell-like environment");
    expect(resultDetail).toHaveTextContent("Supported");
    expect(resultDetail).toHaveTextContent(
      "Deep convection formed with strong updraft and rain water aloft.",
    );
    expect(resultDetail).toHaveTextContent("max updraft 15 m/s");
    expect(resultDetail).toHaveTextContent("First deep convection");

    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByLabelText("Explore viewer controls")).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByLabelText("Time")).toHaveValue("2");
    expect(screen.getByText(/Supercell-like environment · Supported/)).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "/api/results/result-deep-convection/visualization/slice?field=w&time_index=2",
        ),
      );
    });
  });

  it("filters Results by search text and cloud/rain outcomes", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    const filterBar = screen.getByLabelText("Filter and sort results");
    const resultsList = screen.getByLabelText("Results list");

    fireEvent.change(within(filterBar).getByLabelText("Search"), { target: { value: "Valley" } });
    expect(
      within(resultsList).getByText("Uploaded Sounding — Valley, Nebraska"),
    ).toBeInTheDocument();
    expect(within(resultsList).queryByText("Quick-look shallow cumulus")).not.toBeInTheDocument();

    fireEvent.change(within(filterBar).getByLabelText("Search"), {
      target: { value: "dry failed" },
    });
    expect(within(resultsList).getByText("Dry Failed Cumulus quick-look")).toBeInTheDocument();
    expect(
      within(resultsList).queryByText("Uploaded Sounding — Valley, Nebraska"),
    ).not.toBeInTheDocument();

    fireEvent.change(within(filterBar).getByLabelText("Search"), { target: { value: "" } });
    fireEvent.change(within(filterBar).getByLabelText("Scenario"), {
      target: { value: "input_source:observed_sounding" },
    });
    expect(
      within(resultsList).getByText("Uploaded Sounding — Valley, Nebraska"),
    ).toBeInTheDocument();
    expect(within(resultsList).queryByText("Quick-look shallow cumulus")).not.toBeInTheDocument();

    fireEvent.change(within(filterBar).getByLabelText("Scenario"), { target: { value: "all" } });
    fireEvent.change(within(filterBar).getByLabelText("Cloud"), { target: { value: "no" } });
    expect(within(resultsList).getByText("Dry Failed Cumulus quick-look")).toBeInTheDocument();
    expect(within(resultsList).getAllByText("No cloud formed").length).toBeGreaterThan(0);

    fireEvent.change(within(filterBar).getByLabelText("Cloud"), { target: { value: "all" } });
    fireEvent.change(within(filterBar).getByLabelText("Rain-water outcome"), {
      target: { value: "yes" },
    });
    expect(within(resultsList).getAllByText("Rain water aloft detected").length).toBeGreaterThan(0);
    expect(
      within(resultsList).queryByText("Dry Failed Cumulus quick-look"),
    ).not.toBeInTheDocument();
  });

  it("sorts Results by science metrics and resets empty filters", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    const filterBar = screen.getByLabelText("Filter and sort results");
    const resultsList = screen.getByLabelText("Results list");

    fireEvent.change(within(filterBar).getByLabelText("Sort"), {
      target: { value: "max_updraft" },
    });
    const sortedCards = resultsList.querySelectorAll(".experiment-card");
    expect(sortedCards[0]).toHaveTextContent("Uploaded Sounding — Valley, Nebraska");
    expect(sortedCards[0]).toHaveTextContent("max updraft 9.25 m/s");

    fireEvent.change(within(filterBar).getByLabelText("Search"), {
      target: { value: "no result has this phrase" },
    });
    expect(screen.getByText("No results match the current filters.")).toBeInTheDocument();
    expect(
      within(filterBar).getByText(
        (_, node) => node?.textContent === "Showing 0 of 6 notebook entries",
      ),
    ).toBeInTheDocument();

    fireEvent.click(within(filterBar).getByRole("button", { name: "Clear filters" }));
    expect(within(resultsList).getByText("Quick-look shallow cumulus")).toBeInTheDocument();
    expect(
      within(resultsList).getByText("Uploaded Sounding — Valley, Nebraska"),
    ).toBeInTheDocument();
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

  it("supports name tag notes editing through the backend API", async () => {
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
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(screen.getByText("Notebook changes saved")).toBeInTheDocument();
    });
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook",
      expect.objectContaining({
        method: "PATCH",
        body: expect.stringContaining("Saved notebook entry"),
      }),
    );
    expect(screen.queryByRole("button", { name: "Save result" })).not.toBeInTheDocument();
    expect(screen.queryByText("Unsaved")).not.toBeInTheDocument();
    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  it("shows missing diagnostics and warnings without exposing Explore slice controls in Results", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    const resultDetail = screen.getByLabelText("Result detail");

    expect(screen.getAllByText("Diagnostics unavailable").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Cloud unavailable").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Rain water aloft unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText("missing_qc_field")).toBeInTheDocument();
    expect(screen.getByText("missing_w_field")).toBeInTheDocument();
    fireEvent.click(within(resultDetail).getByText("Technical details"));
    expect(screen.getByText(/Cloud water \(qc\) is unavailable/)).toBeInTheDocument();
    expect(screen.getByText("Surface rain was not assessed.")).toBeInTheDocument();
    expect(screen.queryByText(/horizontal slice/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/vertical slice/i)).not.toBeInTheDocument();
  });

  it("does not treat legacy missing field-quality assessment as trusted", async () => {
    const legacyQualityCard = {
      ...resultCard,
      result_id: "result-legacy-quality",
      run_id: "dry-run-legacy-quality",
      name: "Legacy quality result",
      field_quality_assessed: false,
      field_quality: {},
      science_summary: {
        ...resultCard.science_summary,
        field_quality_assessed: false,
        field_quality: {},
      },
    };
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ results: [legacyQualityCard] }), { status: 200 }),
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

    fireEvent.click(await screen.findByRole("button", { name: "Legacy quality result" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByText("Technical details"));

    expect(screen.getByText("Field quality not assessed for this result.")).toBeInTheDocument();
    expect(
      screen.queryByText("All tracked field-quality checks are trusted."),
    ).not.toBeInTheDocument();
  });

  it("shows failed runtime integrity on result details", async () => {
    const failedRuntimeCard = {
      ...resultCard,
      result_id: "result-runtime-failed",
      run_id: "dry-run-runtime-failed",
      name: "Runtime failed result",
      runtime_integrity: {
        assessed: true,
        state: "failed",
        reason: "runtime_integrity_failure_evidence_present",
        summary:
          "CM1 process completion is not enough to trust this result; runtime-integrity checks found fatal floating-point, stats-collapse, or terminal output evidence.",
        exit_code: 0,
        normal_completion_reported: true,
        warning_flags: ["IEEE_INVALID_FLAG", "IEEE_OVERFLOW_FLAG"],
        fatal_warning_flags: ["IEEE_INVALID_FLAG", "IEEE_OVERFLOW_FLAG"],
        stats_sentinel_collapse_detected: true,
        stats_sentinel_times_seconds: [21480],
        terminal_non_finite_fields: ["qc", "qv", "hfx", "qfx"],
        caveats: [
          "runtime_integrity_failed_fatal_floating_point_flags",
          "runtime_integrity_failed_cm1_stats_sentinel_collapse",
          "runtime_integrity_failed_terminal_output_frame_entirely_non_finite",
        ],
        evidence: [
          "stdout:program_terminated_normally",
          "runtime_warning_flag:IEEE_INVALID_FLAG",
          "cm1_stats_sentinel_collapse:cm1out_stats.nc:umax:frame_358:time_21480",
        ],
      },
    };
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ results: [failedRuntimeCard] }), { status: 200 }),
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

    fireEvent.click(await screen.findByRole("button", { name: "Runtime failed result" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByText("Technical details"));

    expect(screen.getByRole("heading", { name: "Runtime integrity failed" })).toBeInTheDocument();
    expect(
      screen.getByText(/CM1 process completion is not enough to trust this result/),
    ).toBeInTheDocument();
    expect(screen.getByText("qc, qv, hfx, qfx")).toBeInTheDocument();
    expect(
      screen.getByText("runtime_integrity_failed_cm1_stats_sentinel_collapse"),
    ).toBeInTheDocument();
  });

  it("shows result delete preview and confirm inside Results", async () => {
    render(<App />);

    expect(await screen.findByLabelText("Result detail")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Storage" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Runtime inventory and cleanup" }),
    ).not.toBeInTheDocument();
    const resultDetail = screen.getByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("Local data");
    expect(resultDetail).toHaveTextContent("Run-directory backed");

    fireEvent.click(
      within(resultDetail).getByRole("button", {
        name: "Preview delete result and local run data",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Delete result and local run data preview" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/result will disappear from Results, Explore, and local inventory/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Storage inventory/)).not.toBeInTheDocument();
    expect(screen.getByText("Result metadata and notebook edits")).toBeInTheDocument();
    expect(screen.getByText("CM1 output and stats")).toBeInTheDocument();
    expect(screen.getByText("Derived diagnostics and Explore data")).toBeInTheDocument();
    expect(screen.getByText("Dry run only; no files were deleted.")).toBeInTheDocument();
    expect(screen.getByText("/tmp/CloudChamber/runs/dry-run-quicklook")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook/delete-preview",
      expect.objectContaining({ method: "POST" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByLabelText("Result delete preview")).not.toBeInTheDocument();

    fireEvent.click(
      within(resultDetail).getByRole("button", {
        name: "Preview delete result and local run data",
      }),
    );
    expect(
      await screen.findByRole("heading", { name: "Delete result and local run data preview" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete result and local run data" }));

    expect(await screen.findByText(/Result and local run data deleted/)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook/delete",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ confirm: true }),
      }),
    );
    expect(
      screen.queryByRole("button", { name: "Quick-look shallow cumulus" }),
    ).not.toBeInTheDocument();
  });

  it("clears result delete preview when a different result is selected", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("Quick-look shallow cumulus");

    fireEvent.click(
      within(resultDetail).getByRole("button", {
        name: "Preview delete result and local run data",
      }),
    );

    expect(await screen.findByLabelText("Result delete preview")).toBeInTheDocument();
    expect(screen.getByText("/tmp/CloudChamber/runs/dry-run-quicklook")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Dry Failed Cumulus quick-look" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Result detail")).toHaveTextContent(
        "Dry Failed Cumulus quick-look",
      );
    });
    expect(screen.queryByLabelText("Result delete preview")).not.toBeInTheDocument();
    expect(screen.queryByText("/tmp/CloudChamber/runs/dry-run-quicklook")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Delete result and local run data" }),
    ).not.toBeInTheDocument();
  });

  it("keeps non-ingested cleanup preview in Build", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    expect(
      await screen.findByRole("heading", { name: "Packages and runs needing action" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Runtime inventory and cleanup" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Storage" })).not.toBeInTheDocument();

    const pipelineRuns = screen.getByLabelText("Local packages and runs");
    const packageRun = within(pipelineRuns)
      .getAllByText(/dry-run-packaged/)[0]
      .closest("article");
    const ingestReadyRun = within(pipelineRuns)
      .getAllByText(/dry-run-uningested/)[0]
      .closest("article");
    const runningRun = within(pipelineRuns)
      .getAllByText(/dry-run-running/)[0]
      .closest("article");
    expect(packageRun).not.toBeNull();
    expect(ingestReadyRun).not.toBeNull();
    expect(runningRun).not.toBeNull();
    expect(
      within(packageRun as HTMLElement).getByRole("button", { name: "Preview cleanup" }),
    ).toBeEnabled();
    expect(
      within(ingestReadyRun as HTMLElement).getByRole("button", { name: "Ingest output" }),
    ).toBeEnabled();
    expect(
      within(ingestReadyRun as HTMLElement).queryByRole("button", { name: "Open result" }),
    ).not.toBeInTheDocument();
    expect(
      within(runningRun as HTMLElement).getByRole("button", { name: "Preview cleanup" }),
    ).toBeDisabled();
    expect(screen.getByText("Running runs cannot be deleted.")).toBeInTheDocument();

    fireEvent.click(
      within(ingestReadyRun as HTMLElement).getByRole("button", { name: "Ingest output" }),
    );
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "/api/results/ingest",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            manifest_path: "/tmp/CloudChamber/runs/dry-run-uningested/run_manifest.json",
          }),
        }),
      ),
    );

    fireEvent.click(
      within(packageRun as HTMLElement).getByRole("button", { name: "Preview cleanup" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Delete local package/run data preview" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/does not touch Results entries/)).toBeInTheDocument();
    expect(screen.getByText(/the source repo/)).toBeInTheDocument();
    expect(screen.getByText("Dry run only; no files were deleted.")).toBeInTheDocument();
    expect(screen.getAllByText("/tmp/CloudChamber/runs/dry-run-packaged").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByRole("button", { name: "Confirm delete local run data" }),
    ).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole("button", { name: "Confirm delete local run data" }));

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

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "baseline-shallow-cumulus" },
    });
    fireEvent.click((await screen.findAllByRole("button", { name: "Preview cleanup" }))[0]);

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

    await openSelectedResultInExplore();

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    expect(await screen.findByLabelText("Explore viewer controls")).toBeInTheDocument();
    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/kg\/kg/).length).toBeGreaterThan(0);
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
    expect(
      screen.getByRole("img", { name: /Vertical x-z slice at y = .* heatmap/ }),
    ).toBeInTheDocument();
  });

  it("opens Explore at the result-card science default time", async () => {
    render(<App />);

    await openSelectedResultInExplore();

    await screen.findByText("Slice synced");

    expect(screen.getByLabelText("Time")).toHaveValue("3");
    expect(screen.getAllByText("2,700 s").length).toBeGreaterThan(0);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/results/result-dry-run-quicklook/visualization/point-cloud?field=qc&time_index=3",
      ),
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/results/result-dry-run-quicklook/visualization/slice?field=qc&time_index=3",
      ),
    );
  });

  it("keeps Explore controls stable when the selected result refreshes", async () => {
    const visualizerResult = resultCard as unknown as Parameters<
      typeof VisualizerSceneShell
    >[0]["result"];
    const { rerender } = render(<VisualizerSceneShell result={visualizerResult} />);

    await screen.findByText("Slice synced");
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });
    await waitFor(() => expect(screen.getByLabelText("Time")).toHaveValue("1"));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "/api/results/result-dry-run-quicklook/visualization/slice?field=qc&time_index=1",
        ),
      ),
    );
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "/api/results/result-dry-run-quicklook/visualization/defaults?time_index=1",
        ),
      ),
    );
    vi.mocked(fetch).mockClear();

    rerender(
      <VisualizerSceneShell
        result={{
          ...visualizerResult,
          name: "Quick-look shallow cumulus refreshed",
          notes: "Refreshed in the notebook while Explore was open.",
        }}
      />,
    );
    await act(async () => undefined);

    expect(screen.getByLabelText("Time")).toHaveValue("1");
    expect(screen.getByLabelText("Saved output time")).toHaveValue("1");
    expect(
      vi.mocked(fetch).mock.calls.some(([url]) => String(url).includes("/visualization/fields")),
    ).toBe(false);
  });

  it("plays saved output times without refetching fields until pause and resets at the end", async () => {
    render(<App />);

    await openSelectedResultInExplore();
    await screen.findByText("Slice synced");

    const fetchMock = vi.mocked(fetch);

    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("time_index=1")),
    );
    fetchMock.mockClear();

    fireEvent.click(screen.getByRole("button", { name: "Move down" }));
    expect(screen.getByLabelText("Slice position")).toHaveValue("0");

    const heatmap = screen.getAllByRole("img", { name: /heatmap/i })[0];
    fireEvent.click(within(heatmap).getByRole("button", { name: /row 1, column 2/i }));
    expect(await screen.findByText("Selected-point diagnostics loaded")).toBeInTheDocument();

    vi.useFakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Play time" }));

    expect(screen.getByRole("button", { name: "Pause time" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(
      screen.getByText("Pause playback to select a cell and explain this time step."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Selected point")).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Animating 3-D scene at 900 s; slice and evidence remain at 900 s until playback is paused.",
      ),
    ).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(900);
    });

    expect(screen.getByLabelText("Time")).toHaveValue("2");
    expect(screen.getByLabelText("Saved output time")).toHaveValue("2");
    expect(
      screen.getByText(
        "Animating 3-D scene at 1,800 s; slice and evidence remain at 900 s until playback is paused.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Slice position")).toHaveValue("0");
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url).includes("/visualization/point-cloud") &&
          String(url).includes("time_index=2"),
      ),
    ).toBe(true);
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url).includes("/visualization/slice") && String(url).includes("time_index=2"),
      ),
    ).toBe(false);
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url).includes("/visualization/defaults") && String(url).includes("time_index=2"),
      ),
    ).toBe(false);
    expect(
      screen.getByText("Pause playback to select a cell and explain this time step."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Pause time" }));
    expect(screen.getByRole("button", { name: "Play time" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    vi.useRealTimers();
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          ([url]) =>
            String(url).includes("/visualization/slice") && String(url).includes("time_index=2"),
        ),
      ).toBe(true),
    );
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url).includes("/visualization/defaults") && String(url).includes("time_index=2"),
      ),
    ).toBe(true);
    expect(screen.getByLabelText("Slice position")).toHaveValue("0");

    fireEvent.click(screen.getByRole("button", { name: "Last frame" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("time_index=3")),
    );
    fetchMock.mockClear();

    vi.useFakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Play time" }));
    await act(async () => {
      vi.advanceTimersByTime(900);
    });
    expect(screen.getByRole("button", { name: "Play time" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByLabelText("Time")).toHaveValue("0");
    expect(screen.getByLabelText("Saved output time")).toHaveValue("0");
    vi.useRealTimers();
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("time_index=0")),
    );
  });

  it("selects a slice region and renders backend Thermal Fate Inspector diagnostics", async () => {
    render(<App />);

    await openSelectedResultInExplore();
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
    expect(screen.getAllByText("Rain water aloft detected").length).toBeGreaterThan(0);
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

    await openSelectedResultInExplore();
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
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("x_index=1&y_index=0&z_index=1"));
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
        const requestedField = mockPointFieldFromParam(parsed.searchParams.get("field"));
        return Promise.resolve(
          new Response(
            JSON.stringify(
              pointCloudResponse({
                field: requestedField,
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
                field: mockFieldFromParam(parsed.searchParams.get("field")),
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

  it("keeps only supported process evidence modes in the Baseline primary focus control", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findAllByText("Cloud-water point layer loaded");
    expect(screen.getByText("Result explanation")).toBeInTheDocument();
    expect(
      screen.getAllByText(/Cloud water formed in the validated reference baseline/).length,
    ).toBeGreaterThan(0);

    fireEvent.click(screen.getByText("Process evidence details"));
    const processMode = screen.getByLabelText("Process mode");
    expect(processMode).toHaveValue("thermal_fate");
    expect(
      within(processMode).getByRole("option", { name: /Thermal Fate summary/ }),
    ).toBeInTheDocument();
    expect(within(processMode).getByRole("option", { name: "Cloud Water" })).toBeInTheDocument();
    expect(within(processMode).getByRole("option", { name: "Updrafts" })).toBeInTheDocument();
    expect(
      within(processMode).getByRole("option", { name: /Cloud Lifecycle/ }),
    ).toBeInTheDocument();
    expect(within(processMode).queryByRole("option", { name: /Moisture/ })).not.toBeInTheDocument();
    expect(within(processMode).queryByRole("option", { name: /Buoyancy/ })).not.toBeInTheDocument();
    expect(
      within(processMode).queryByRole("option", { name: /Deep Breakthrough/ }),
    ).not.toBeInTheDocument();
    expect(
      within(processMode).queryByRole("option", { name: /Precipitation Feedback/ }),
    ).not.toBeInTheDocument();

    fireEvent.change(processMode, { target: { value: "cloud_water" } });

    expect(processMode).toHaveValue("cloud_water");
    expect(screen.getByRole("heading", { name: "Cloud Water" })).toBeInTheDocument();

    expect(screen.getByText("Not available for this result")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Not available for this result"));
    expect(screen.getByText(/Moisture \/ Saturation/)).toBeInTheDocument();
    expect(screen.getByText(/missing required CM1 fields/i)).toBeInTheDocument();
    expect(screen.getByText(/Deep Breakthrough/)).toBeInTheDocument();
    expect(screen.getAllByText(/Future diagnostic/i).length).toBeGreaterThan(0);
  });

  it("shows Dry Failed moisture limitation as a candidate focus instead of a dead-end", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Dry Failed Cumulus quick-look" }));
    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findByText("Slice synced");
    fireEvent.click(screen.getByText("Process evidence details"));
    const processMode = screen.getByLabelText("Process mode");
    expect(
      within(processMode).getByRole("option", { name: /Moisture \/ Saturation \(candidate\)/ }),
    ).toBeInTheDocument();
    expect(within(processMode).queryByRole("option", { name: /Buoyancy/ })).not.toBeInTheDocument();

    fireEvent.change(processMode, { target: { value: "moisture" } });

    expect(processMode).toHaveValue("moisture");
    expect(screen.getByRole("heading", { name: "Moisture / Saturation" })).toBeInTheDocument();
    expect(screen.getAllByText("Candidate").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/thermals are present while cloud water and rain stay below threshold/i),
    ).toBeInTheDocument();
  });

  it("shows capped-style results with cap inversion as a candidate focus", async () => {
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Capped / Suppressed Cumulus quick-look" }),
    );
    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findByText("Slice synced");
    fireEvent.click(screen.getByText("Process evidence details"));
    const processMode = screen.getByLabelText("Process mode");
    expect(
      within(processMode).getByRole("option", { name: /Cap \/ Inversion \(candidate\)/ }),
    ).toBeInTheDocument();

    fireEvent.change(processMode, { target: { value: "cap" } });

    expect(processMode).toHaveValue("cap");
    expect(screen.getByRole("heading", { name: "Cap / Inversion" })).toBeInTheDocument();
    expect(screen.getByText(/candidate process view/i)).toBeInTheDocument();
  });

  it("handles missing qc fields without treating no-qc as a broken Explore state", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.queryByRole("option", { name: /qc/ })).not.toBeInTheDocument();
    expect(screen.getByLabelText("True 3-D scalar field viewer")).toBeInTheDocument();
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
  });

  it("opens a cloud-forming result in Explore with qc and w available in both views", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findByText("Slice synced");
    expect(screen.getByLabelText("True 3-D scalar field viewer")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("option", { name: "w - Vertical velocity (slice only)" }).length,
    ).toBeGreaterThan(0);

    await screen.findAllByText("Cloud-water point layer loaded");
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("option", { name: "w - Vertical velocity (slice only)" }).length,
    ).toBeGreaterThan(0);
  });

  it("explains when liquid cloud water is shallower than the hydrometeor envelope", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/results") {
        return Promise.resolve(
          new Response(JSON.stringify({ results: [deepConvectionResultCard] }), { status: 200 }),
        );
      }
      if (url === "/api/results/result-deep-convection/visualization/fields") {
        return Promise.resolve(new Response(JSON.stringify(fieldCatalogResponse), { status: 200 }));
      }
      if (url.startsWith("/api/results/result-deep-convection/visualization/defaults")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...selectedTimeDefaultsResponse(url),
              result_id: "result-deep-convection",
            }),
            { status: 200 },
          ),
        );
      }
      if (url.includes("/api/results/result-deep-convection/visualization/point-cloud")) {
        const parsed = new URL(url, "http://localhost");
        return Promise.resolve(
          new Response(
            JSON.stringify(
              pointCloudResponse({
                field: mockPointFieldFromParam(parsed.searchParams.get("field")),
                threshold: Number(parsed.searchParams.get("threshold") ?? 0.000001),
                timeIndex: Number(parsed.searchParams.get("time_index") ?? 0),
              }),
            ),
            { status: 200 },
          ),
        );
      }
      if (url.includes("/api/results/result-deep-convection/visualization/slice")) {
        const parsed = new URL(url, "http://localhost");
        return Promise.resolve(
          new Response(
            JSON.stringify(
              sliceResponse({
                field: mockFieldFromParam(parsed.searchParams.get("field")),
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
      return (
        defaultFetch?.(input, init) ?? Promise.resolve(new Response("not found", { status: 404 }))
      );
    });
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    expect(resultDetail).toHaveTextContent("coherent cloud-object top 10,200 m");
    expect(resultDetail).toHaveTextContent(/Liquid cloud top\s*6,200 m/);
    expect(resultDetail).toHaveTextContent(/Coherent cloud top\s*10,200 m/);
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByText(
        /Viewing liquid cloud water only: qc tops near 6,200 m, while the coherent cloud object reaches 10,200 m from qc\+qi\+qs\./,
      ),
    ).toBeInTheDocument();
  });

  it("separates 3-D scalar fields from slice-only fields", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    await screen.findAllByText("Cloud-water point layer loaded");

    const threeDField = screen.getByLabelText("3-D scalar field") as HTMLSelectElement;
    const threeDOptions = Array.from(threeDField.options).map((option) => option.textContent);
    expect(threeDOptions).toEqual(
      expect.arrayContaining([
        "qc - Cloud water",
        "qr - Rain water",
        "qv - Water vapor",
        "dbz - Reflectivity",
        "rain - Accumulated surface rain",
      ]),
    );
    expect(threeDOptions.join(" ")).not.toContain("theta");
    expect(threeDOptions.join(" ")).not.toContain("temperature");
    expect(threeDOptions.join(" ")).not.toContain("Vertical velocity");

    const sliceField = screen.getByLabelText("Slice field") as HTMLSelectElement;
    const sliceOptions = Array.from(sliceField.options).map((option) => option.textContent);
    expect(sliceOptions).toEqual(
      expect.arrayContaining([
        "w - Vertical velocity (slice only)",
        "theta - Potential temperature (slice only)",
        "temperature - Temperature (slice only)",
      ]),
    );

    fireEvent.change(sliceField, { target: { value: "temperature" } });
    await waitFor(() => {
      expect(screen.getByLabelText("Slice field")).toHaveValue("temperature");
    });
    expect(screen.getByLabelText("3-D scalar field")).toHaveValue("qc");
  });

  it("renders expanded 3-D scalar fields with honest legends and floor-layer rain", async () => {
    render(<App />);

    const resultDetail = await screen.findByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));
    await screen.findAllByText("Cloud-water point layer loaded");

    const threeDField = screen.getByLabelText("3-D scalar field");
    fireEvent.change(threeDField, { target: { value: "qr" } });
    expect((await screen.findAllByText("Rain-water point layer loaded")).length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Slice field")).toHaveValue("qr");
    expect(screen.getAllByText("Rain water").length).toBeGreaterThan(0);

    fireEvent.change(threeDField, { target: { value: "qv" } });
    expect((await screen.findAllByText("Water-vapor point layer loaded")).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByLabelText("Slice field")).toHaveValue("qv");
    expect(screen.getAllByText("Water vapor").length).toBeGreaterThan(0);

    fireEvent.change(threeDField, { target: { value: "dbz" } });
    expect((await screen.findAllByText("Reflectivity point layer loaded")).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByLabelText("Slice field")).toHaveValue("dbz");
    expect(screen.getAllByText("0 dBZ").length).toBeGreaterThan(0);
    expect(screen.getAllByText("60+ dBZ").length).toBeGreaterThan(0);

    fireEvent.change(threeDField, { target: { value: "rain" } });
    expect((await screen.findAllByText("Surface-rain floor layer loaded")).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByLabelText("Slice field")).toHaveValue("rain");
    expect(screen.getByRole("button", { name: "Vertical x-z slice" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toBeDisabled();
  });

  it("opens Dry Failed as a no-cloud result with a useful w/updraft path", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Dry Failed Cumulus quick-look" }));
    fireEvent.click(
      within(screen.getByLabelText("Result detail")).getByRole("button", {
        name: "Open in Explore",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findAllByText("Cloud water max is 0 kg/kg; no points are above 1.000e-6 kg/kg");
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getAllByRole("option", { name: "qc - Cloud water" }).length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("option", { name: "w - Vertical velocity (slice only)" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "Thermals rose, but low-level moisture stayed too dry for meaningful cloud water or rain.",
      ).length,
    ).toBeGreaterThan(0);
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

    await openSelectedResultInExplore();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Visualization fields temporarily failed.",
    );

    fireEvent.click(screen.getByRole("button", { name: "Retry loading fields" }));

    await screen.findAllByText("Cloud-water point layer loaded");
    await waitFor(() => {
      expect(
        screen.queryByText("Visualization fields temporarily failed."),
      ).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders cloud-water context in unified Explore", async () => {
    render(<App />);

    await openSelectedResultInExplore();

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findAllByText("Cloud-water point layer loaded");
    expect(screen.getByText("Cloud formed in this result")).toBeInTheDocument();
    expect(screen.queryByText("Cloud formed here")).not.toBeInTheDocument();
    const viewer = screen.getByLabelText("True 3-D scalar field viewer");
    expect(viewer).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "Interactive Three.js scene showing a CM1 scalar field, domain bounds, slice plane, and selected point",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Scientific visualization workbench")).toBeInTheDocument();
    expect(screen.getByLabelText("Fixed visualization viewport region")).toBeInTheDocument();
    expect(screen.getByLabelText("Visualization details")).toBeInTheDocument();
    expect(screen.getByLabelText("Explore viewer controls")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Inspect the current slice" })).toBeInTheDocument();
    expect(within(viewer).getByText("True 3-D scene")).toBeInTheDocument();
    expect(within(viewer).getByText("Cloud water")).toBeInTheDocument();
    const axisLabels = within(viewer).getByLabelText("3-D axis tick labels");
    expect(within(axisLabels).getByText("x -3 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("x 0 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("x +3 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("y -3 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("y 0 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("y +3 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("z 0 km")).toBeInTheDocument();
    expect(within(axisLabels).getByText("z +1 km")).toBeInTheDocument();
    expect(within(viewer).getByText(/Slice plane: Horizontal layer at z = /)).toBeInTheDocument();
    expect(screen.getByLabelText(/Horizontal layer at z = .* heatmap/)).toBeInTheDocument();
    expect(within(viewer).getByRole("button", { name: "Zoom in" })).toBeInTheDocument();
    expect(within(viewer).getByRole("button", { name: "Zoom out" })).toBeInTheDocument();
    expect(within(viewer).getByRole("button", { name: "Reset camera" })).toBeInTheDocument();
    expect(within(viewer).getByRole("button", { name: "Top-down x-y" })).toBeInTheDocument();
    expect(within(viewer).getByRole("button", { name: "Look along x" })).toBeInTheDocument();
    expect(within(viewer).getByRole("button", { name: "Look along y" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Oblique" })).not.toBeInTheDocument();
    expect(screen.queryByRole("slider", { name: "Zoom" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("qc");
    expect(screen.getByRole("button", { name: "Horizontal layer" })).toHaveClass("active-control");
    expect(screen.getByRole("button", { name: "Vertical x-z slice" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toBeInTheDocument();
    expect(screen.getByLabelText("Time")).toBeInTheDocument();
    expect(screen.getByLabelText("Show slice plane")).toBeChecked();
    expect(
      screen.getAllByText(
        "Current field max: 8.000e-6 kg/kg. Visible points above 1.000e-6 kg/kg: 3.",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("0 to 3 km")).toBeInTheDocument();
    expect(screen.getByText("0.8 km to 1.2 km")).toBeInTheDocument();
    expect(screen.getByText("x 2, y 1, z 1.2 km, value 8.000e-6")).toBeInTheDocument();
    expect(
      screen.getByText("Slice planes: native-grid JSON slices from the backend"),
    ).toBeInTheDocument();
    expect(screen.getByText("3 of 3")).toBeInTheDocument();
    expect(screen.getAllByText("2,700 s").length).toBeGreaterThan(0);
    expect(screen.getByText("2.000e-6 kg/kg to 8.000e-6 kg/kg")).toBeInTheDocument();
    expect(screen.getByText("Visualizer interpretation of CM1-derived output")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Processing method: backend native-grid thresholded point cloud for supported scalar fields",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Rendering method: direct Three.js scalar point cloud"),
    ).toBeInTheDocument();
    expect(screen.getByText("No raw NetCDF parsing in the browser")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("time_index=3"));
    expect(fetch).toHaveBeenCalledWith(
      "/api/results/result-dry-run-quicklook/visualization/defaults?time_index=3",
    );
  });

  it("supports qc and w slice planes synced to Explore time", async () => {
    render(<App />);

    await openSelectedResultInExplore();
    await screen.findAllByText("Cloud-water point layer loaded");

    const viewer = screen.getByLabelText("True 3-D scalar field viewer");
    expect(within(viewer).getByText(/Slice plane: Horizontal layer at z = /)).toBeInTheDocument();
    expect(
      within(viewer).queryByText(/Slice plane: Vertical x-z slice at y = /),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("qc (Cloud water)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("native_grid_view_no_interpolation").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Move down" }));
    expect(screen.getByLabelText("Slice position")).toHaveValue("0");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("orientation=horizontal"));
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("level_index=0"));
    });

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z slice" }));
    expect(screen.getByRole("button", { name: "Vertical x-z slice" })).toHaveClass(
      "active-control",
    );
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
    await waitFor(() => {
      expect(
        within(viewer).getByText(/Slice plane: Vertical x-z slice at y = /),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Vertical y-z slice" }));
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toHaveClass(
      "active-control",
    );
    expect(screen.getByLabelText("Slice position")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("orientation=vertical_y"));
      expect(
        within(viewer).getByText(/Slice plane: Vertical y-z slice at x = /),
      ).toBeInTheDocument();
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

  it("uses shared controls to switch field and slice context", async () => {
    render(<App />);

    await openSelectedResultInExplore();
    await screen.findAllByText("Cloud-water point layer loaded");

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z slice" }));
    const viewer = screen.getByLabelText("True 3-D scalar field viewer");
    await waitFor(() => {
      expect(
        within(viewer).getByText(/Slice plane: Vertical x-z slice at y = /),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Horizontal layer" }));
    await waitFor(() => {
      expect(within(viewer).getByText(/Slice plane: Horizontal layer at z = /)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Slice field"), { target: { value: "w" } });
    fireEvent.click(screen.getByRole("button", { name: "Vertical y-z slice" }));
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByRole("button", { name: "Vertical y-z slice" })).toHaveClass(
      "active-control",
    );
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w"));
    });
  });

  it("updates and resets true 3-D camera controls", async () => {
    render(<App />);

    await openSelectedResultInExplore();
    await screen.findAllByText("Cloud-water point layer loaded");

    const cameraControls = screen.getByLabelText("3-D camera controls");
    expect(within(cameraControls).getByText(/Camera ready/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Top-down x-y" }));
    expect(within(cameraControls).getByText(/Camera set to top-down x-y view/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Look along x" }));
    expect(within(cameraControls).getByText(/Camera looking along the x axis/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Look along y" }));
    expect(within(cameraControls).getByText(/Camera looking along the y axis/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Zoom in" }));
    expect(within(cameraControls).getByText(/Camera zoomed in/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Zoom out" }));
    expect(within(cameraControls).getByText(/Camera zoomed out/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Pan view up" }));
    expect(within(cameraControls).getByText(/Camera moved up/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Pan view down" }));
    expect(within(cameraControls).getByText(/Camera moved down/)).toBeInTheDocument();
    fireEvent.click(within(cameraControls).getByRole("button", { name: "Taller viewport" }));
    expect(within(cameraControls).getByText(/Viewport set taller/)).toBeInTheDocument();
    expect(
      within(cameraControls).getByRole("button", { name: "Standard viewport" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByText("Technical visualization details"));
    expect(screen.getByText("Direct Three.js point cloud")).toBeInTheDocument();

    fireEvent.click(within(cameraControls).getByRole("button", { name: "Reset camera" }));

    expect(within(cameraControls).getByText(/Camera reset to overview/)).toBeInTheDocument();
  });

  it("updates cloud-water threshold opacity point size and time requests", async () => {
    render(<App />);

    await openSelectedResultInExplore();
    await screen.findAllByText("Cloud-water point layer loaded");

    fireEvent.change(screen.getByLabelText("Cloud-water threshold"), { target: { value: "1" } });

    await screen.findAllByText(
      "Cloud water max is 8.000e-6 kg/kg; no points are above 1.000e+0 kg/kg",
    );
    expect(
      screen.getByText("No cloud water above the selected threshold at this time."),
    ).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("threshold=1"));

    fireEvent.change(screen.getByLabelText("Layer opacity"), { target: { value: "0.8" } });
    fireEvent.change(screen.getByLabelText("Point size"), { target: { value: "14" } });
    fireEvent.change(screen.getByLabelText("Time"), { target: { value: "1" } });

    expect(screen.getByText("0.8", { selector: "output" })).toBeInTheDocument();
    expect(screen.getByText("14px", { selector: "output" })).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("time_index=1"));
    });
  });

  it("handles missing qc in the unified Explore cloud context", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No diagnostics yet" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findAllByText("Slice fields ready; no 3-D scalar field available");
    expect(screen.getByText("No supported 3-D scalar field")).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByLabelText("3-D scalar field")).toBeDisabled();
  });

  it("handles an Explore result with no visualization-ready fields", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "No visual fields" }));
    const resultDetail = screen.getByLabelText("Result detail");
    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    await screen.findAllByText("No fields available");
    expect(
      screen.getByText("No visualization-ready fields are available for this result."),
    ).toBeInTheDocument();
    expect(screen.getByText("No supported 3-D scalar field")).toBeInTheDocument();
  });
});
