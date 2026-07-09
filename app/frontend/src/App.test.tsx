import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { act } from "react";
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
        {
          id: "deep_overnight",
          label: "Deep / overnight",
          purpose: "Expensive opt-in run for high spatial and saved-output resolution",
          expected_runtime: "target roughly 10-12x Standard wall-clock",
          confidence: "requires local/manual validation",
          output_notes: "192 x 192 grid at about 33.333 m and 300 s saved-output cadence",
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
    run_size_details: {
      preset: "quick_look",
      runtime_seconds: 10800,
      output_cadence_seconds: 900,
      expected_output_frames: 13,
      nx: 64,
      ny: 64,
      nz: 75,
      dx_m: 100,
      dy_m: 100,
      dz_m: 40,
      model_top_m: 18000,
      time_step_seconds: 3,
      grid_cell_count: 307200,
      grid_cell_multiplier_vs_standard: 1,
      time_step_multiplier_vs_standard: 1,
      output_frame_multiplier_vs_standard: 1.86,
      estimated_compute_multiplier_vs_standard: 0.5,
      estimated_output_volume_multiplier_vs_standard: 1.86,
      target_wall_clock_multiplier_vs_standard: "1x",
      cost_warning:
        "Normal local run-size preset; estimates remain approximate until local validation.",
      validation_note: "Preset preserves the validated reference-derived spatial grid.",
    },
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

const deepDryRunResponse = {
  ...dryRunResponse,
  report: {
    ...dryRunResponse.report,
    run_size_preset: "deep_overnight",
    estimated_cost_or_size:
      "Deep Overnight is an expensive local run intended to take roughly 10-12x Standard wall-clock after manual validation.",
    run_size_details: {
      preset: "deep_overnight",
      runtime_seconds: 21600,
      output_cadence_seconds: 300,
      expected_output_frames: 73,
      nx: 192,
      ny: 192,
      nz: 75,
      dx_m: 33.3333333333,
      dy_m: 33.3333333333,
      dz_m: 40,
      model_top_m: 18000,
      time_step_seconds: 3,
      time_step_note:
        "Deep Overnight keeps the Standard CM1 solver timestep; cost comes from higher spatial resolution and much higher saved-output cadence.",
      grid_cell_count: 2764800,
      grid_cell_multiplier_vs_standard: 9,
      time_step_multiplier_vs_standard: 1,
      output_frame_multiplier_vs_standard: 10.43,
      estimated_compute_multiplier_vs_standard: 9,
      estimated_output_volume_multiplier_vs_standard: 93.86,
      target_wall_clock_multiplier_vs_standard: "10-12x",
      cost_warning:
        "Deep Overnight is an expensive local run intended to take roughly 10-12x Standard wall-clock after manual validation.",
      validation_note:
        "Deep Overnight preserves the physical domain and scenario controls while changing horizontal resolution and saved-output cadence.",
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
  },
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
};

const screeningInputsResponse = {
  inputs: [
    {
      station_id: "USM00072558",
      source_file_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data.txt",
      source_file_name: "USM00072558-data.txt",
      sounding_count: 2,
      package_ready_count: 1,
      blocked_count: 1,
      latest_valid_time_utc: "2025-01-02T00:00:00Z",
    },
  ],
};

const screeningResponse = {
  story: "all",
  generated_at: "2026-07-01T12:00:00Z",
  candidates: [
    shallowCandidate,
    deepConvectionCandidate,
    blockedCandidate,
    secondaryShallowCandidate,
    missingLclCandidate,
  ],
  caveats: ["screening_guidance_only"],
};

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
        station_name: "VALLEY",
        cached_status: "cached",
        url: "https://example.test/USM00072558-data-beg2025.txt.zip",
      },
    ],
  },
};

const igraCacheResponse = {
  entries: [
    {
      station_id: "USM00072558",
      station_name: "VALLEY",
      data_txt_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data.txt",
      zip_path: "/tmp/CloudChamber/cache/igra/recent/stations/USM00072558-data-beg2025.txt.zip",
      sounding_count: 2,
      latest_valid_time_utc: "2025-01-02T00:00:00Z",
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
    rain_onset_time_seconds: 5400,
    max_qr_kg_kg: 2e-7,
    max_rain_or_surface_precip: 4.2,
    max_dbz_or_reflectivity_proxy: 30,
    latest_output_time_seconds: 10800,
    default_explore_time_index: 3,
    default_explore_time_seconds: 2700,
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
      label: "Highest cloud top",
      time_index: 3,
      time_seconds: 2700,
      source_field: "qc",
      source_diagnostic: "diagnostics.cloud.cloud_top_time_series",
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
  rain_present: false,
  first_rain_time_seconds: null,
  surface_rain_present: null,
  max_surface_rain: null,
  surface_rain_units: null,
  reflectivity_available: null,
  max_dbz: null,
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
  name: "Deep Convection Trial — Norman, Oklahoma",
  tags: ["deep-convection", "candidate"],
  scenario_name: "Deep Convection Trial",
  package_family: "deep_convection_trial",
  package_display_name: "Deep Convection Trial",
  trigger_type: "warm_bubble",
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
      source_field: "qc+qr+qi+qs+qg when available",
      source_diagnostic: "diagnostics.cloud.cloud_top_time_series",
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
    ran_as: "Deep Convection Trial",
    cm1_outcome: "Deep convection formed with strong updraft and rain water aloft.",
    match_status: "matched",
    match_status_label: "Matched",
    evidence: ["deep cloud formed", "cloud top 10200 m", "max updraft 15 m/s"],
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

const resultDeletePreviewResponse = {
  result_id: "result-dry-run-quicklook",
  run_id: "dry-run-quicklook",
  run_directory: "/tmp/CloudChamber/runs/dry-run-quicklook",
  dry_run: true,
  deleted: false,
  size_bytes: 852 * 1024 ** 2,
  message: "Dry run only; no files were deleted.",
  affected_surfaces: ["Results", "Explore", "Compare", "local inventory"],
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
        return Promise.resolve(
          new Response(
            JSON.stringify({
              requested_limit: 10,
              selected_count: 1,
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
      if (url === "/api/sounding-candidates/screen") {
        return Promise.resolve(new Response(JSON.stringify(screeningResponse), { status: 200 }));
      }
      if (url === "/api/sounding-candidates/saved" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify(savedCandidatesResponse.saved_candidates[0]), {
            status: 200,
          }),
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
      if (url === "/api/dry-run-package") {
        return Promise.resolve(new Response(JSON.stringify(dryRunResponse), { status: 200 }));
      }
      if (url === "/api/runs/launch") {
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
      if (url.startsWith("/api/runs/status")) {
        return Promise.resolve(new Response(JSON.stringify(completedRunStatus), { status: 200 }));
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
    expect(
      screen.getByRole("heading", { name: "Packages and runs needing action" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Not packaged yet").length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "No package has been created from the current setup in this browser session.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Experiment")).toHaveTextContent("Upload a Sounding");
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
      await screen.findByRole("heading", { name: "Experiment setup summary" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    expect(await screen.findByRole("heading", { name: "Upload a Sounding" })).toBeInTheDocument();
    expect(screen.getByText("Observed sounding profile, Surface heating")).toBeInTheDocument();
    expect(screen.queryByLabelText("Low-level humidity")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Surface heating")).not.toBeDisabled();
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
    expect(screen.getByText("USM00072558 · Valley, Nebraska")).toBeInTheDocument();
    expect(screen.getByText(/CM1 z=0 is station surface at 351.5 m MSL/)).toBeInTheDocument();
    expect(screen.getByText(/observed sounding winds/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Choose how to try this sounding" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Package type")).toHaveValue("observed_sounding_quicklook");

    fireEvent.change(screen.getByLabelText("Package type"), {
      target: { value: "deep_convection_trial" },
    });
    expect(screen.getByText("Three-bubble trigger")).toBeInTheDocument();
    expect(
      screen.getByText(
        /observed temperature, moisture, and wind profile with an idealized CM1 three-warm-bubble trigger/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/wider box for storm growth and precipitation/i)).toBeInTheDocument();
    expect(
      screen.getByText(/wider storm-growth domain than the shallow-cumulus quick look/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("create-package-btn"));

    await waitFor(() => {
      expect(dryRunBody).toContain('"package_family":"deep_convection_trial"');
      expect(dryRunBody).toContain('"observed_sounding"');
      expect(dryRunBody).toContain('"station_id":"USM00072558"');
      expect(dryRunBody).toContain('"model_bottom_elevation_m_msl":351.5');
    });
  });

  it("defaults deep-convection candidates to the Deep Convection Trial package", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let dryRunBody = "";
    let screenBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/screen") {
        screenBody = String(init?.body ?? "");
      }
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
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
    const storyFilter = await screen.findByLabelText("Story filter");
    expect(storyFilter).toHaveTextContent("Deep Convection Trial stories");
    fireEvent.change(storyFilter, {
      target: { value: "deep_convection_trial" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Screen cached soundings" }));

    expect(await screen.findByText("Screening guidance loaded")).toBeInTheDocument();
    expect(screenBody).toContain('"target_story":"deep_convection_trial"');
    const deepCard = screen.getByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)");
    expect(deepCard).toHaveTextContent("Supercell-like environment");

    fireEvent.click(within(deepCard).getByRole("button", { name: "Use this sounding" }));

    expect(await screen.findByText("Candidate selected for package review")).toBeInTheDocument();
    expect(screen.getByLabelText("Package type")).toHaveValue("deep_convection_trial");
    expect(screen.getByText("Three-bubble trigger")).toBeInTheDocument();
    expect(screen.getByText(/strong fit for Deep Convection Trial/)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("create-package-btn"));

    await waitFor(() => {
      expect(dryRunBody).toContain('"package_family":"deep_convection_trial"');
      expect(dryRunBody).toContain('"candidate_screening"');
      expect(dryRunBody).toContain('"primary_story":"supercell_environment"');
      expect(dryRunBody).toContain('"candidate_id":"USM00072357-2025052000-supercell"');
    });
  });

  it("keeps humid/rainy candidates with weak deep scores on observed quick-look", async () => {
    const defaultFetch = vi.mocked(fetch).getMockImplementation();
    let dryRunBody = "";
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
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
    fireEvent.change(await screen.findByLabelText("Story filter"), {
      target: { value: "humid_rainy_candidate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Screen cached soundings" }));

    expect(await screen.findByText("Screening guidance loaded")).toBeInTheDocument();
    const humidCard = screen.getByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)");
    expect(humidCard).toHaveTextContent("Humid / rainy");

    fireEvent.click(within(humidCard).getByRole("button", { name: "Use this sounding" }));

    expect(await screen.findByText("Candidate selected for package review")).toBeInTheDocument();
    expect(screen.getByLabelText("Package type")).toHaveValue("observed_sounding_quicklook");

    fireEvent.click(screen.getByTestId("create-package-btn"));

    await waitFor(() => {
      expect(dryRunBody).toContain('"package_family":"observed_sounding_quicklook"');
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
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/sounding-candidates/screen") {
        screenBody = String(init?.body ?? "");
      }
      if (url === "/api/dry-run-package") {
        dryRunBody = String(init?.body ?? "");
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
    expect(screen.getByText(/Screening guidance only/)).toBeInTheDocument();
    expect(screen.getByText("IGRA cache not checked yet")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Refresh IGRA catalog" }));

    expect(await screen.findByText("IGRA station catalog refreshed")).toBeInTheDocument();
    expect(screen.getByText("Screenable soundings").nextElementSibling).toHaveTextContent(
      "2 soundings",
    );

    fireEvent.click(screen.getByRole("button", { name: "Cache station files" }));
    expect(await screen.findByText("Cached 1 station file")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Story filter"), {
      target: { value: "shallow_cumulus_candidate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Screen cached soundings" }));

    expect(await screen.findByText("Screening guidance loaded")).toBeInTheDocument();
    expect(screenBody).toContain('"target_story":"shallow_cumulus_candidate"');
    const valleyCard = screen.getByLabelText("Sounding candidate Valley, Nebraska (USM00072558)");
    expect(valleyCard).toHaveTextContent("Cloud-forming shallow cumulus");
    expect(valleyCard).toHaveTextContent("Package-ready");
    expect(valleyCard).toHaveTextContent("Low-level moisture: 10.2 g/kg");
    expect(
      screen.getByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)"),
    ).toHaveTextContent("Cloud-forming shallow cumulus");
    expect(
      screen.queryByLabelText("Sounding candidate Norman, Oklahoma (USM00072357)"),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("Candidate details")).toHaveTextContent(
      "Candidate match score is screening guidance only",
    );

    fireEvent.change(screen.getByLabelText("Story filter"), {
      target: { value: "needs_review" },
    });
    const normanCard = await screen.findByLabelText(
      "Sounding candidate Norman, Oklahoma (USM00072357)",
    );
    expect(normanCard).toHaveTextContent("Blocked");
    expect(within(normanCard).getByRole("button", { name: "Use this sounding" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Story filter"), {
      target: { value: "all" },
    });
    const selectedValleyCard = await screen.findByLabelText(
      "Sounding candidate Valley, Nebraska (USM00072558)",
    );
    fireEvent.click(within(selectedValleyCard).getByRole("button", { name: "Save candidate" }));

    expect(await screen.findByText("Sounding candidate saved")).toBeInTheDocument();
    const savedCard = screen.getByLabelText(
      "Saved sounding candidate Valley, Nebraska (USM00072558)",
    );
    expect(savedCard).toHaveTextContent("Cloud-forming shallow cumulus");

    fireEvent.click(within(savedCard).getByRole("button", { name: "Remove saved" }));
    expect(await screen.findByText("Saved sounding candidate removed")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Saved sounding candidate Valley, Nebraska (USM00072558)"),
    ).not.toBeInTheDocument();

    fireEvent.click(within(selectedValleyCard).getByRole("button", { name: "Use this sounding" }));

    expect(await screen.findByText("Candidate selected for package review")).toBeInTheDocument();
    expect(
      screen.getByText("Candidate loaded into observed-sounding package review"),
    ).toBeInTheDocument();
    expect(screen.getByText("USM00072558 · Valley, Nebraska")).toBeInTheDocument();
    expect(screen.getByText(/Screened as Cloud-forming shallow cumulus/)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("create-package-btn"));

    await waitFor(() => {
      expect(dryRunBody).toContain('"observed_sounding"');
      expect(dryRunBody).toContain('"candidate_screening"');
      expect(dryRunBody).toContain('"primary_story":"shallow_cumulus_candidate"');
      expect(dryRunBody).toContain('"candidate_id":"USM00072558-2025010200-shallow"');
    });
  });

  it("loads saved sounding candidates as soon as Upload a Sounding is selected", async () => {
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

    expect(
      await screen.findByLabelText("Saved sounding candidate Valley, Nebraska (USM00072558)"),
    ).toBeInTheDocument();
    expect(screen.queryByText("No saved candidates yet.")).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalledWith("/api/igra/recent/refresh-catalog", expect.anything());
    expect(fetch).not.toHaveBeenCalledWith("/api/sounding-candidates/screen", expect.anything());
  });

  it("keeps secondary story matches visible and sorts missing LCL last", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Build" }));
    fireEvent.change(await screen.findByLabelText("Experiment"), {
      target: { value: "__observed_sounding_upload__" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Screen cached soundings" }));
    expect(await screen.findByText("Screening guidance loaded")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Story filter"), {
      target: { value: "shallow_cumulus_candidate" },
    });
    expect(
      screen.getByLabelText("Sounding candidate Wilmington, Ohio (USM00072426)"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Sort"), {
      target: { value: "lowest_lcl" },
    });
    const candidateCards = screen.getAllByLabelText(/^Sounding candidate /);
    const visibleOrder = candidateCards.map((card) => card.textContent ?? "");
    const validLclIndex = visibleOrder.findIndex((text) => text.includes("Wilmington, Ohio"));
    const missingLclIndex = visibleOrder.findIndex((text) =>
      text.includes("Springfield, Missouri"),
    );
    expect(validLclIndex).toBeGreaterThanOrEqual(0);
    expect(missingLclIndex).toBeGreaterThan(validLclIndex);
  });

  it("shows Deep Overnight as an expensive distinct generated package", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/scenarios") {
        return Promise.resolve(new Response(JSON.stringify(scenarioResponse), { status: 200 }));
      }
      if (url === "/api/dry-run-package") {
        expect(init?.body).toEqual(expect.stringContaining("deep_overnight"));
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
    fireEvent.change(await screen.findByLabelText("Run-size preset"), {
      target: { value: "deep_overnight" },
    });

    expect(screen.getAllByText(/10-12x Standard wall-clock/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/expensive opt-in preset/i).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByTestId("create-package-btn"));

    const packageReview = await screen.findByTestId("package-review-panel");
    expect(packageReview).toHaveTextContent("192 x 192 x 75");
    expect(packageReview).toHaveTextContent("dx/dy 33.333 m");
    expect(packageReview).toHaveTextContent("300 s output");
    expect(packageReview).toHaveTextContent("73 saved frames");
    expect(packageReview).toHaveTextContent("9x grid");
    expect(packageReview).toHaveTextContent("1x timestep");
    expect(packageReview).toHaveTextContent("10.43x saved frames");
    expect(packageReview).toHaveTextContent("93.86x output volume");
    expect(packageReview).toHaveTextContent("Deep Overnight is an expensive local run");
    expect(packageReview).toHaveTextContent("keeps the Standard CM1 solver timestep");
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
    expect(await screen.findByRole("heading", { name: "Local run launchpad" })).toBeInTheDocument();
    expect(screen.queryByText("Local experiment loop")).not.toBeInTheDocument();
    expect(screen.getByText("Build pipeline")).toBeInTheDocument();
    expect(screen.getByText("Packages and runs needing action")).toBeInTheDocument();
    expect(screen.getByText("Ready to run")).toBeInTheDocument();
    expect(screen.getAllByText("Ready to ingest").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Running").length).toBeGreaterThan(0);
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

  it("automatically copies back, ingests, and cleans LAN worker output after completion", async () => {
    let ingested = false;
    const workerRun = {
      ...storageRuns[0],
      run_id: "dry-run-worker-completed",
      scenario_id: "humid-vigorous-cumulus",
      scenario_name: "Humid Vigorous Cumulus",
      run_size_preset: "quick_look",
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
    expect(screen.getByRole("button", { name: "Create another package" })).toHaveClass(
      "secondary-button",
    );
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
    expect(screen.getByRole("tab", { name: "Notebook" })).toHaveClass("active-control");
    expect(screen.getByRole("tab", { name: "Compare" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Storage" })).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Experiment Notebook" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Review ingested cloud experiments, compare variants, and open results for explanation.",
      ),
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
    expect(resultDetail).toHaveTextContent("Interesting times");
    expect(resultDetail).toHaveTextContent("Highest cloud top");
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
    expect(resultDetail).toHaveTextContent("Deep Convection Trial — Norman, Oklahoma");
    expect(resultDetail).toHaveTextContent("Deep convection formed");
    expect(resultDetail).toHaveTextContent("Screening vs CM1");
    expect(resultDetail).toHaveTextContent("Supercell-like environment");
    expect(resultDetail).toHaveTextContent("Matched");
    expect(resultDetail).toHaveTextContent(
      "Deep convection formed with strong updraft and rain water aloft.",
    );
    expect(resultDetail).toHaveTextContent("max updraft 15 m/s");
    expect(resultDetail).toHaveTextContent("First deep convection");

    fireEvent.click(within(resultDetail).getByRole("button", { name: "Open in Explore" }));

    expect(await screen.findByLabelText("Explore viewer controls")).toBeInTheDocument();
    expect(screen.getByLabelText("Slice field")).toHaveValue("w");
    expect(screen.getByLabelText("Time")).toHaveValue("2");
    expect(screen.getByText(/Supercell-like environment · Matched/)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/results/result-deep-convection/visualization/slice?field=w&time_index=2",
      ),
    );
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
    expect(within(resultsList).getAllByText("Rain water aloft detected").length).toBeGreaterThan(
      0,
    );
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
    expect(screen.getAllByText("Rain water aloft detected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No rain water aloft detected").length).toBeGreaterThan(0);
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
    expect(screen.getByLabelText("Comparison time")).toHaveValue("3");
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
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    expect(await screen.findByLabelText("Explore viewer controls")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Inspect the current slice" }),
    ).toBeInTheDocument();
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
    expect(
      await screen.findByRole("heading", { name: "What happened in this result?" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("True 3-D scalar field viewer")).toBeInTheDocument();
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

    expect(screen.getAllByText("Diagnostics unavailable").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unknown").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No rain water aloft detected").length).toBeGreaterThan(0);
    expect(screen.getByText("missing_qc_field")).toBeInTheDocument();
    expect(screen.getByText("missing_w_field")).toBeInTheDocument();
    expect(screen.queryByText(/horizontal slice/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/vertical slice/i)).not.toBeInTheDocument();
  });

  it("shows result delete preview and confirm inside Results", async () => {
    render(<App />);

    expect(await screen.findByLabelText("Result detail")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Storage" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Runtime inventory and cleanup" })).not.toBeInTheDocument();
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
      screen.getByText(/result will disappear from Results, Explore, Compare, and local inventory/),
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
    expect(screen.queryByRole("heading", { name: "Runtime inventory and cleanup" })).not.toBeInTheDocument();
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
      screen.getAllByText(/Cloud water formed in the validated quick-look baseline/).length,
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

    fireEvent.click(await screen.findByRole("tab", { name: "Compare" }));
    fireEvent.click(await screen.findByRole("button", { name: "Open Dry Failed in Explore" }));

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
    fireEvent.click(screen.getByText("Technical visualization details"));
    expect(screen.getByText("Direct Three.js point cloud")).toBeInTheDocument();

    fireEvent.click(within(cameraControls).getByRole("button", { name: "Reset camera" }));

    expect(
      within(cameraControls).getByText(/Camera reset to shallow-cumulus overview/),
    ).toBeInTheDocument();
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
