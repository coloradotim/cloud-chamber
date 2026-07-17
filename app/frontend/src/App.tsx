import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { CSSProperties, FormEvent } from "react";

import "./App.css";
import { True3DViewer } from "./True3DViewer";

type ControlOption = {
  value: string;
  label: string;
  description?: string | null;
};

type ScenarioControl = {
  id: string;
  label: string;
  description: string;
  type: "choice";
  default: string | number | boolean;
  options: ControlOption[];
};

type Scenario = {
  id: string;
  display_name: string;
  description: string;
  physical_question: string;
  intended_behavior: string;
  expected_behavior: string;
  learning_goals: string[];
  warnings: string[];
  limitations: string[];
  controls: ScenarioControl[];
};

type ScenarioResponse = {
  golden_path_scenario_id: string;
  scenarios: Scenario[];
};

type RunConfigurationInput = {
  duration: string;
  horizontal_cell_count: string;
  domain_size: string;
  output_cadence: string;
  diagnostic_set: string;
  surface_forcing_mode: string;
  surface_heat_flux_k_m_s: string;
  surface_moisture_flux_g_g_m_s: string;
  surface_patch_shape: string;
  surface_patch_radius_m: string;
  surface_patch_radius_x_m: string;
  surface_patch_radius_y_m: string;
  surface_patch_heat_flux_perturbation_k_m_s: string;
  surface_patch_moisture_flux_perturbation_g_g_m_s: string;
  surface_patch_taper_width_m: string;
  surface_patch_ramp_seconds: string;
  time_step_seconds?: string;
};

type SurfaceForcingPatch = {
  schema_version: string;
  shape: "circle" | string;
  center_x_m: number;
  center_y_m: number;
  radius_x_m: number;
  radius_y_m: number;
  taper_function: string;
  taper_width_m: number;
  ramp_seconds: number;
  background_heat_flux_k_m_s: number;
  background_moisture_flux_g_g_m_s: number;
  heat_flux_perturbation_k_m_s: number;
  moisture_flux_perturbation_g_g_m_s: number;
  domain_x_m: number;
  domain_y_m: number;
  dx_m: number;
  dy_m: number;
  support_status?: string;
  cm1_application_status?: string;
  pattern_sha256?: string;
  caveats?: string[];
};

type RunConfigurationCM1Values = {
  nx: number;
  ny: number;
  nz: number;
  dx_m: number;
  dy_m: number;
  dz_m: number;
  stretch_z: number;
  str_bot_m: number;
  str_top_m: number;
  dz_bot_m: number;
  dz_top_m: number;
  model_top_m: number;
  domain_x_km: number;
  domain_y_km: number;
  time_step_seconds: number;
  runtime_seconds: number;
  output_cadence_seconds: number;
  restart_cadence_seconds: number;
  rayleigh_damping_start_m: number;
  expected_output_frames: number;
  grid_cell_count: number;
};

type RunConfigurationSurfaceFluxCM1Values = {
  isfcflx: number;
  sfcmodel: number;
  oceanmodel: number;
  set_flx: number;
  cnst_shflx: number;
  cnst_shflx_units: string;
  cnst_lhflx: number;
  cnst_lhflx_units: string;
  set_znt: number;
  cnst_znt: number;
  set_ust: number;
  cnst_ust: number;
};

type RunConfiguration = Omit<
  RunConfigurationInput,
  "horizontal_cell_count" | "surface_heat_flux_k_m_s" | "surface_moisture_flux_g_g_m_s"
> & {
  configuration_id: string;
  mode: "smoke" | "science";
  label: string;
  horizontal_cell_count: string | number;
  duration_seconds: number;
  output_cadence_seconds: number;
  surface_heat_flux_k_m_s: number;
  surface_moisture_flux_g_g_m_s: number;
  cost_runtime_summary: string;
  output_volume_summary: string;
  cm1_values: RunConfigurationCM1Values;
  surface_flux_mode: string;
  surface_flux_summary: string;
  surface_flux_cm1_values: RunConfigurationSurfaceFluxCM1Values;
  surface_forcing_patch?: SurfaceForcingPatch | null;
  surface_flux_caveats: string[];
  caveats: string[];
};

type RunConfigurationSummary = {
  configuration_id: string;
  mode: "smoke" | "science";
  label: string;
  duration: string;
  horizontal_cell_count: string | number;
  domain_size: string;
  output_cadence: string;
  diagnostic_set: string;
  surface_heat_flux_k_m_s?: number;
  surface_moisture_flux_g_g_m_s?: number;
  surface_flux_mode?: string;
  surface_flux_summary?: string;
  surface_flux_cm1_values?: RunConfigurationSurfaceFluxCM1Values;
  surface_forcing_patch?: SurfaceForcingPatch | null;
  surface_flux_caveats?: string[];
  runtime_seconds: number;
  output_cadence_seconds: number;
  expected_output_frames: number;
  nx: number;
  ny: number;
  nz: number;
  dx_m: number;
  dy_m: number;
  dz_m: number;
  stretch_z?: number;
  str_bot_m?: number;
  str_top_m?: number;
  dz_bot_m?: number;
  dz_top_m?: number;
  model_top_m: number;
  time_step_seconds: number;
  time_step_note?: string;
  grid_cell_count: number;
  grid_cell_multiplier_vs_default: number;
  time_step_multiplier_vs_default: number;
  output_frame_multiplier_vs_default: number;
  estimated_compute_multiplier_vs_default: number;
  estimated_output_volume_multiplier_vs_default: number;
  cost_warning: string;
  validation_note: string;
};

type PreRunValidationReport = {
  status: "valid" | "caveated" | "blocked" | string;
  selected_candidate?: {
    candidate_id?: string | null;
    station_id?: string | null;
    valid_time_utc?: string | null;
  } | null;
  selected_hypothesis?: {
    hypothesis_id?: string | null;
    story_id?: string | null;
    story_label?: string | null;
    ingredient_score?: number | null;
    ingredient_score_label?: string | null;
    predicted_output_signature?: string[];
  } | null;
  selected_run_recipe?: {
    run_recipe?: string | null;
    recipe_id?: string | null;
    display_name?: string | null;
    recipe_display_name?: string | null;
    assumption_set_id?: string | null;
    assumption_mode?: string | null;
    required_fields?: string[];
    caveats?: string[];
  } | null;
  hypothesis_recipe_alignment?: {
    status?: string;
    reasons?: string[];
    missing_assumptions?: string[];
    missing_outputs?: string[];
  } | null;
  run_shape_validation?: {
    estimated_frames?: number | null;
    estimated_output_volume?: string | null;
    duration?: string | null;
    domain?: string | null;
    horizontal_cell_count?: number | string | null;
    output_cadence?: string | null;
    diagnostic_set?: string | null;
  } | null;
  output_validation?: {
    required_fields?: string[];
    enabled_fields?: string[];
    missing_fields?: string[];
  } | null;
  blocking_errors?: string[];
  caveats?: string[];
};

type DryRunReport = {
  scenario_id: string;
  run_recipe?: RunRecipe;
  run_recipe_display_name?: string;
  recipe_id?: string | null;
  recipe_display_name?: string | null;
  assumption_set_id?: string | null;
  assumption_mode?: string | null;
  recipe_assumptions?: Record<string, unknown>;
  required_output_fields?: string[];
  missing_required_output_fields?: string[];
  recipe_caveats?: string[];
  input_source?: string;
  trigger_type?: string | null;
  trigger_parameters?: Record<string, string | number | boolean> | null;
  physical_question: string;
  controls: Record<string, string | number | boolean>;
  run_configuration: RunConfiguration;
  run_configuration_summary?: RunConfigurationSummary;
  pre_run_validation_report?: PreRunValidationReport | null;
  estimated_cost_or_size: string;
  expected_diagnostics: string[];
  expected_outputs?: string[];
  run_caveats?: string[];
  manual_validation_status?: string | null;
  visualization_defaults: Record<string, unknown>;
  generated_files: Record<string, string>;
  not_a_completed_cm1_result: boolean;
  cm1_was_launched: boolean;
  provenance: {
    product_state: string;
    source_model: string;
    preview_is_guidance_only: boolean;
    visualizer_is_interpretation: boolean;
  };
  observed_sounding?: ObservedSoundingSummary | null;
  user?: UserRunMetadata | null;
};

type DryRunResponse = {
  package_dir: string;
  manifest_path: string;
  report_path: string;
  generated_files: string[];
  report: DryRunReport;
};

type SoundingTimeSummary = {
  station_id: string;
  valid_time_utc: string;
  source_time_text: string;
  num_levels: number;
  pressure_source: string;
  non_pressure_source: string;
};

type ObservedSoundingLevel = {
  pressure_pa: number;
  source_height_m_msl: number;
  model_z_m: number;
  temperature_c: number;
  potential_temperature_k: number;
  qv_g_kg: number;
  wind_direction_degrees?: number | null;
  wind_speed_m_s?: number | null;
  u_wind_m_s?: number | null;
  v_wind_m_s?: number | null;
};

type ObservedSoundingRecord = {
  source_type: string;
  source_provider: string;
  source_format: string;
  uploaded_filename: string;
  station_id: string;
  station_name?: string | null;
  station_latitude?: number | null;
  station_longitude?: number | null;
  station_elevation_m_msl: number;
  valid_time_utc: string;
  source_time_text: string;
  source_units: Record<string, string>;
  converted_cm1_units: Record<string, string>;
  source_vertical_coordinate_type: string;
  model_bottom_elevation_m_msl: number;
  levels: ObservedSoundingLevel[];
  wind_handling: string;
  conversion_choices: Record<string, string>;
  validation: {
    status: string;
    errors: string[];
    caveats: string[];
  };
  provenance: Record<string, string>;
};

type ObservedSoundingParseResponse = {
  source_provider: string;
  source_format: string;
  uploaded_filename: string;
  available_soundings: SoundingTimeSummary[];
  selected_sounding: ObservedSoundingRecord;
};

type CandidateStoryId =
  | "shallow_cumulus_candidate"
  | "dry_failed_candidate"
  | "capped_suppressed_candidate"
  | "humid_rainy_candidate"
  | "severe_thunderstorm_environment"
  | "supercell_environment"
  | "high_cape_pulse_storm"
  | "dry_microburst_inverted_v"
  | "squall_line_cold_pool_candidate"
  | "elevated_convection"
  | "needs_review"
  | "poor_or_incomplete_candidate";

type CandidateStoryFilter =
  | "all"
  | "deep_convection_trial"
  | "shallow_cumulus_candidate"
  | "dry_failed_candidate"
  | "capped_suppressed_candidate"
  | "humid_rainy_candidate"
  | "severe_thunderstorm_environment"
  | "supercell_environment"
  | "high_cape_pulse_storm"
  | "dry_microburst_inverted_v"
  | "squall_line_cold_pool_candidate"
  | "elevated_convection"
  | "needs_review"
  | "poor_or_incomplete_candidate";

type CandidateSort =
  | "best_match"
  | "valid_time"
  | "station_id"
  | "station_name"
  | "primary_story"
  | "story_family"
  | "rank_score"
  | "deep_tower_opportunity"
  | "confidence"
  | "support"
  | "package_readiness"
  | "observed_wind_available"
  | "profile_top_m_agl"
  | "lowest_level_m_agl"
  | "data_completeness_score"
  | "low_level_qv_g_kg"
  | "mean_qv_0_500m_g_kg"
  | "mean_qv_0_1000m_g_kg"
  | "surface_t_td_spread_c"
  | "estimated_lcl_height_m_agl"
  | "lapse_rate_0_1000m_c_per_km"
  | "midlevel_lapse_rate_700_500_hpa_c_per_km"
  | "cap_strength_proxy"
  | "cap_height_m_agl"
  | "bulk_shear_0_1km_m_s"
  | "bulk_shear_0_3km_m_s"
  | "bulk_shear_0_6km_m_s"
  | "midlevel_dry_layer_proxy"
  | "dry_microburst_inverted_v_proxy"
  | "freezing_level_m_agl";

type CandidateStoryFamilyFilter = "all" | "lower_atmosphere" | "deep_convection" | "review";
type CandidateSupportFilter = "all" | "supported" | "weak" | "unavailable";
type CandidateReadinessFilter = "all" | "package_ready" | "blocked";
type CandidateRecipeFitStatus =
  | "testable_now"
  | "partially_testable"
  | "requires_surface_forcing_recipe"
  | "not_testable_with_current_recipes"
  | "blocked_profile";
type CandidateRecipeFitDisplay = {
  status: CandidateRecipeFitStatus;
  label: string;
  summary: string;
  caveats: string[];
};

type RunRecipe =
  | "generated_reference_lower_atmosphere"
  | "observed_surface_forced_evolution"
  | "differential_surface_forced_evolution"
  | "deep_tower_benchmark";

type ObservedRunRecipe =
  | "observed_surface_forced_evolution"
  | "differential_surface_forced_evolution"
  | "deep_tower_benchmark";
type AtmosphereSourcePath = "cached_recommendations" | "saved_candidates" | "upload_igra_text";
type SearchIntent =
  | "best_overall"
  | "deep_convection"
  | "humid_rainy"
  | "dry_microburst"
  | "shallow_boundary_layer";
type StationSelectionMode = "all_cached" | "selected";
type CandidateHistoryScope = "all_cached" | "latest_per_station";
type RunPlanQueueTarget = "local" | "lan";
const CURRENT_OBSERVED_RUN_RECIPE: ObservedRunRecipe = "observed_surface_forced_evolution";
const DIFFERENTIAL_SURFACE_FORCING_MODE = "differential_surface_forcing_patch_v0";
const UNIFORM_SURFACE_FORCING_MODE = "constant_uniform_surface_flux_proxy";
const DISABLED_SURFACE_FORCING_MODE = "disabled";
type RunPlanItemStatus =
  | "planned"
  | "packaging"
  | "queued"
  | "lan_started"
  | "package_failed"
  | "skipped";

type RunPlanItem = {
  id: string;
  selected: boolean;
  source: AtmosphereSourcePath;
  candidate: SoundingCandidate | null;
  savedCandidate?: SavedSoundingCandidate | null;
  observedSounding: ObservedSoundingRecord | null;
  candidateScreening: Record<string, unknown> | null;
  activeStory: CandidateStoryId | null;
  runRecipe: ObservedRunRecipe;
  runConfiguration: RunConfigurationInput;
  controls: Record<string, string | number | boolean>;
  queueTarget: RunPlanQueueTarget;
  status: RunPlanItemStatus;
  message: string | null;
  dryRun: DryRunResponse | null;
  blockedPreRunValidationReport: PreRunValidationReport | null;
};

type StoryScore = {
  story: CandidateStoryId;
  label: string;
  score_0_to_100: number;
  support: string;
  reasons: string[];
  caveats: string[];
};

type EvidenceItem = {
  label: string;
  value: string | number | boolean | null;
  units?: string | null;
  interpretation: string;
  supports_story: CandidateStoryId[];
  caveats: string[];
};

type SoundingCandidate = {
  candidate_id: string;
  station_id: string;
  station_name?: string | null;
  station_latitude?: number | null;
  station_longitude?: number | null;
  station_elevation_m_msl?: number | null;
  valid_time_utc: string;
  source_time_text: string;
  source_file_name: string;
  source_file_hash: string;
  source_format: string;
  source_provider: string;
  primary_story: CandidateStoryId;
  primary_story_label: string;
  story_family?: CandidateStoryFamilyFilter;
  story_scores: StoryScore[];
  rank_score: number;
  confidence: "low" | "medium" | "high";
  package_ready: boolean;
  features: Record<string, string | number | boolean | null>;
  evidence: EvidenceItem[];
  caveats: string[];
  selected_sounding_payload?: ObservedSoundingRecord | null;
  interest_summary?: string | null;
  interest_reasons?: string[];
  discovery_bucket?: string | null;
  recipe_fit_status?: CandidateRecipeFitStatus;
  recipe_fit_label?: string;
  recipe_fit_summary?: string;
  recipe_fit_caveats?: string[];
  active_story?: CandidateStoryId | null;
  active_story_label?: string | null;
  display_story?: string | null;
  matched_story_ids?: CandidateStoryId[];
  active_story_score?: number | null;
  ingredient_score?: number | null;
  ingredient_score_label?: string | null;
  active_story_support?: "supported" | "weak" | "unavailable" | null;
  package_readiness?: string | null;
  recipe_fit?: CandidateRecipeFitStatus | string | null;
  top_reasons?: string[];
  top_caveats?: string[];
  evidence_summary?: string[];
  screening_version: string;
  created_at: string;
};

type CandidateFilterTrace = {
  selected_station_count?: number;
  selected_cached_soundings?: number;
  history_scope?: CandidateHistoryScope;
  latest_per_station?: number | null;
  analyzed_soundings: number;
  story_score_records: number;
  stage_counts: Record<string, number>;
  stages: Array<{
    key: string;
    label: string;
    count: number;
    active: boolean;
  }>;
  station_distribution: Array<{
    station_id: string;
    station_name?: string | null;
    count: number;
  }>;
  top_excluded_reasons: Array<{
    reason: string;
    count: number;
  }>;
  applied_limit: number;
};

type ScreeningInput = {
  station_id: string;
  station_name?: string | null;
  cached_text_path: string;
  source_file_name: string;
  cached_status: string;
  sounding_count?: number | null;
  latest_valid_time_utc?: string | null;
  caveats?: string[];
};

type ScreeningInputsResponse = {
  inputs: ScreeningInput[];
};

type ScreeningResult = {
  screening_version: string;
  generated_at: string;
  candidates: SoundingCandidate[];
  caveats: string[];
  total_candidate_count?: number;
  filtered_candidate_count?: number;
  sort_by?: CandidateSort;
  sort_direction?: "asc" | "desc";
  filters?: {
    station_id?: string | null;
    station_ids?: string[];
    history_scope?: CandidateHistoryScope;
    latest_per_station?: number | null;
    story_filter: CandidateStoryFilter;
    story_family: CandidateStoryFamilyFilter;
    support: CandidateSupportFilter;
    readiness: CandidateReadinessFilter;
    station_search: string;
  };
  filter_trace?: CandidateFilterTrace;
};

type UserRunMetadata = {
  name: string;
  tags: string[];
  notes?: string | null;
  saved?: boolean;
};

type SavedSoundingCandidate = {
  saved_candidate_id: string;
  candidate: SoundingCandidate;
  selected_sounding_payload?: ObservedSoundingRecord | null;
  screening_version: string;
  primary_story: CandidateStoryId;
  story_scores: StoryScore[];
  features: Record<string, string | number | boolean | null>;
  evidence: EvidenceItem[];
  caveats: string[];
  tags: string[];
  notes?: string | null;
  created_at: string;
  last_used_at?: string | null;
  linked_run_ids: string[];
  linked_result_ids: string[];
};

type SavedCandidatesResponse = {
  saved_candidates: SavedSoundingCandidate[];
};

type IGRACatalogResponse = {
  catalog: {
    refreshed_at: string;
    region: { label: string; tag: string };
    stations: unknown[];
    zip_references: Array<{
      station_id: string;
      station_name?: string | null;
      latitude?: number | null;
      longitude?: number | null;
      filename: string;
      cached_status: string;
    }>;
  } | null;
};

type IGRACacheResponse = {
  entries: {
    station_id: string;
    station_name?: string | null;
    cached_text_path?: string | null;
  }[];
  updated_at: string;
};

type IGRABatchCacheResponse = {
  requested_limit: number;
  requested_station_ids?: string[];
  selected_count: number;
  cached_entries: unknown[];
  failed: Array<{ station_id: string; filename: string; error: string }>;
  remaining_uncached_count: number;
};

type ObservedSoundingSummary = {
  source_provider: string;
  source_format: string;
  uploaded_filename: string;
  station_id: string;
  station_name?: string | null;
  station_latitude?: number | null;
  station_longitude?: number | null;
  station_elevation_m_msl: number;
  valid_time_utc: string;
  source_vertical_coordinate_type: string;
  model_bottom_elevation_m_msl: number;
  usable_levels: number;
  lowest_model_z_m: number | null;
  highest_model_z_m: number | null;
  wind_handling: string;
  validation_status: string;
  validation_errors: string[];
  caveats: string[];
  provenance: Record<string, string>;
};

type RunProgressResponse = {
  elapsed_wall_seconds?: number | null;
  model_time_seconds?: number | null;
  total_model_time_seconds?: number | null;
  percent_complete?: number | null;
  estimated_remaining_wall_seconds?: number | null;
  estimated_finish_at?: string | null;
  last_refreshed_at?: string | null;
  stale?: boolean;
  model_time_source?: string | null;
  total_model_time_source?: string | null;
  unavailable_reason?: string | null;
  caveats?: string[];
};

type RunStatusResponse = {
  run_id: string;
  lifecycle_state: string;
  product_state: string;
  validation_status: string;
  manifest_path: string;
  command: string[];
  stdout_log: string;
  stderr_log: string;
  stdout_tail: string | null;
  stderr_tail: string | null;
  exit_code: number | null;
  started_at: string | null;
  finished_at: string | null;
  output_summary: {
    raw_cm1_artifacts: number;
    netcdf_paths: number;
    processed_artifacts: number;
  };
  runtime_warnings: string[];
  runtime_integrity?: RuntimeIntegrity | null;
  progress: RunProgressResponse | null;
  user?: UserRunMetadata | null;
  observed_sounding?: ObservedSoundingSummary | null;
  candidate_screening?: Record<string, unknown> | null;
  run_recipe?: RunRecipe | string | null;
  run_recipe_display_name?: string | null;
  input_source?: string | null;
  run_configuration?: RunConfiguration | null;
  pre_run_validation_report?: PreRunValidationReport | null;
};

type RunQueueEntry = {
  run_id: string;
  manifest_path: string;
  state: string;
  queued_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  result_id?: string | null;
  message?: string | null;
  error?: string | null;
  cleanup_status?: string | null;
};

type RunQueueResponse = {
  schema_version: string;
  entries: RunQueueEntry[];
  active_run_id: string | null;
  queued_count: number;
  updated_at: string;
};

type LanWorkerConfigResponse = {
  configured: boolean;
  available: boolean;
  message: string;
  cm1_env_keys: string[];
  cm1_env_settings: string[];
  custom_launch_command: boolean;
};

type LanWorkerRunResponse = {
  run_id: string;
  state: string;
  message?: string | null;
  exit_code?: number | null;
  netcdf_count?: number;
  raw_artifact_count?: number;
  started_at?: string | null;
  finished_at?: string | null;
  local_package_dir?: string | null;
  ready_for_ingest?: boolean;
  progress?: RunProgressResponse | null;
};

type IngestResponse = {
  result_id: string;
  run_id: string;
  diagnostics_summary: string | null;
};

type BuildRunStage =
  | "not_packaged"
  | "package_ready"
  | "lan_worker_running"
  | "lan_worker_completed"
  | "ready_for_local_ingest"
  | "running"
  | "completed"
  | "failed"
  | "ingested"
  | "worker_cleanup_pending"
  | "worker_cleanup_complete"
  | "worker_cleanup_failed";

type OutputFileSummary = {
  netcdf_count: number;
  model_output_count: number;
  stats_netcdf_count: number;
  raw_cm1_artifact_count: number;
  processed_artifact_count: number;
  visualization_ready_artifact_count: number;
  total_output_count: number;
  model_output_file_count: number;
  time_steps: number | null;
  first_output_time_seconds: number | null;
  last_output_time_seconds: number | null;
};

type InterestingTimeSupportState =
  | "supported"
  | "fallback"
  | "unavailable"
  | "unsupported_missing_fields"
  | "unsupported_missing_diagnostic";

type FieldQualityState = "trusted" | "caveated" | "untrusted" | "unavailable";

type RuntimeIntegrityState = "trusted" | "caveated" | "failed" | "not_assessed";

type RuntimeIntegrity = {
  assessed: boolean;
  state: RuntimeIntegrityState;
  reason: string;
  summary: string;
  exit_code?: number | null;
  normal_completion_reported?: boolean | null;
  warning_flags: string[];
  fatal_warning_flags: string[];
  stats_sentinel_collapse_detected: boolean;
  stats_sentinel_times_seconds: Array<number | null>;
  terminal_non_finite_fields: string[];
  caveats: string[];
  evidence: string[];
};

type FieldQuality = {
  field: string;
  source_field: string;
  quality_state: FieldQualityState;
  reason?: string | null;
  finite_count: number;
  non_finite_count: number;
  total_count: number;
  caveats: string[];
};

type SurfaceFluxFieldDiagnostics = {
  source_field: string;
  available: boolean;
  field_absent: boolean;
  min_value?: number | null;
  max_value?: number | null;
  mean_value?: number | null;
  units?: string | null;
  finite_count: number;
  non_finite_count: number;
  total_count: number;
  caveats: string[];
};

type SurfaceFluxDiagnostics = {
  hfx: SurfaceFluxFieldDiagnostics;
  qfx: SurfaceFluxFieldDiagnostics;
};

type DifferentialPatchGeometryDiagnostics = {
  pattern_sha256?: string | null;
  shape?: string | null;
  center_x_m?: number | null;
  center_y_m?: number | null;
  radius_x_m?: number | null;
  radius_y_m?: number | null;
  taper_width_m?: number | null;
  ramp_seconds?: number | null;
};

type PatchSpatialFieldDiagnostics = {
  source_field: string;
  available: boolean;
  field_absent: boolean;
  units?: string | null;
  quality_state?: string | null;
  quality_reason?: string | null;
  finite_count?: number;
  non_finite_count?: number;
  total_count?: number;
  finite_fraction?: number | null;
  time_index?: number | null;
  time_seconds?: number | null;
  time_selection_method?: string | null;
  vertical_coordinate_name?: string | null;
  vertical_level_index?: number | null;
  vertical_level_height_m?: number | null;
  max_value?: number | null;
  max_x_m?: number | null;
  max_y_m?: number | null;
  max_distance_from_patch_center_m?: number | null;
  max_inside_patch_radius?: boolean | null;
  max_region?: string | null;
  center_value?: number | null;
  core_mean?: number | null;
  taper_mean?: number | null;
  background_mean?: number | null;
  center_to_background_ratio?: number | null;
  core_to_background_ratio?: number | null;
  core_finite_count?: number;
  taper_finite_count?: number;
  background_finite_count?: number;
  inside_patch_mean?: number | null;
  outside_patch_mean?: number | null;
  center_to_outside_ratio?: number | null;
  inside_finite_count: number;
  outside_finite_count: number;
  total_finite_count: number;
  method: string;
  geometry_note?: string;
  caveats: string[];
};

type PatchConvergenceDiagnostics = {
  available: boolean;
  source_fields: string[];
  units: string;
  quality_state?: string | null;
  quality_reason?: string | null;
  finite_count?: number;
  non_finite_count?: number;
  total_count?: number;
  finite_fraction?: number | null;
  time_index?: number | null;
  time_seconds?: number | null;
  time_selection_method?: string | null;
  vertical_coordinate_name?: string | null;
  vertical_level_index?: number | null;
  vertical_level_height_m?: number | null;
  max_convergence_s_1?: number | null;
  max_convergence_x_m?: number | null;
  max_convergence_y_m?: number | null;
  max_convergence_distance_from_patch_center_m?: number | null;
  max_convergence_inside_patch_radius?: boolean | null;
  max_convergence_region?: string | null;
  max_convergence_time_series?: Array<{ time_seconds: number | null; value: number | null }>;
  core_mean_convergence_s_1?: number | null;
  taper_mean_convergence_s_1?: number | null;
  background_mean_convergence_s_1?: number | null;
  core_to_background_convergence_ratio?: number | null;
  core_finite_count?: number;
  taper_finite_count?: number;
  background_finite_count?: number;
  inside_patch_mean_convergence_s_1?: number | null;
  outside_patch_mean_convergence_s_1?: number | null;
  method: string;
  geometry_note?: string;
  caveats: string[];
};

type LocalizedResponseDiagnostics = {
  available: boolean;
  support_state: string;
  geometry?: DifferentialPatchGeometryDiagnostics | null;
  hfx_footprint: PatchSpatialFieldDiagnostics;
  qfx_footprint: PatchSpatialFieldDiagnostics;
  near_surface_convergence: PatchConvergenceDiagnostics;
  updraft: PatchSpatialFieldDiagnostics;
  cloud_water: PatchSpatialFieldDiagnostics;
  rain_water_aloft: PatchSpatialFieldDiagnostics;
  surface_rain: PatchSpatialFieldDiagnostics;
  reflectivity: PatchSpatialFieldDiagnostics;
  caveats: string[];
};

type InterestingTimeRecord = {
  key: string;
  label: string;
  time_index?: number | null;
  time_seconds?: number | null;
  source_time_value?: number | string | null;
  source_field?: string | null;
  source_diagnostic?: string | null;
  value?: number | boolean | null;
  units?: string | null;
  support_state: InterestingTimeSupportState;
  field_quality?: FieldQuality | null;
  caveats: string[];
  fallback_reason?: string | null;
};

type FieldDefaultTime = {
  field: string;
  time_index?: number | null;
  time_seconds?: number | null;
  source_interesting_time_key: string;
  support_state: InterestingTimeSupportState;
  field_quality?: FieldQuality | null;
  fallback_reason?: string | null;
  caveats: string[];
};

type ScienceSummary = {
  cloud_formed?: boolean | null;
  deep_cloud_formed?: boolean | null;
  deep_cloud_threshold_m?: number;
  strong_updraft_formed?: boolean | null;
  strong_updraft_threshold_m_s?: number;
  first_cloud_time_seconds?: number | null;
  first_cloud_time_label?: string | null;
  time_of_first_deep_convection_seconds?: number | null;
  max_qc_kg_kg?: number | null;
  max_qc_time_seconds?: number | null;
  max_updraft_w_m_s?: number | null;
  max_updraft_time_seconds?: number | null;
  min_downdraft_w_m_s?: number | null;
  min_downdraft_time_seconds?: number | null;
  highest_cloud_top_m?: number | null;
  highest_liquid_cloud_top_m?: number | null;
  highest_coherent_cloud_object_top_m?: number | null;
  coherent_cloud_object_source_fields?: string[];
  highest_raw_hydrometeor_envelope_top_m?: number | null;
  highest_hydrometeor_envelope_top_m?: number | null;
  hydrometeor_envelope_source_fields?: string[];
  rain_onset_time_seconds?: number | null;
  max_qr_kg_kg?: number | null;
  max_rain_or_surface_precip?: number | null;
  max_dbz_or_reflectivity_proxy?: number | null;
  cold_pool_proxy?: number | null;
  near_surface_theta_perturbation_proxy?: number | null;
  updraft_depth_proxy_m?: number | null;
  latest_output_time_seconds?: number | null;
  default_explore_time_index?: number | null;
  default_explore_time_seconds?: number | null;
  cm1_outcome?: string | null;
  field_quality_assessed?: boolean;
  field_quality?: Record<string, FieldQuality>;
  surface_fluxes?: SurfaceFluxDiagnostics | null;
  localized_response?: LocalizedResponseDiagnostics | null;
  diagnostic_availability?: ScienceDiagnosticAvailability[];
  interesting_time_caveats: string[];
  interesting_time_support_state: string;
};

type ScienceDiagnosticAvailability = {
  key: string;
  label: string;
  support_state: string;
  source_field?: string | null;
  field_quality?: FieldQuality | null;
  value?: number | boolean | null;
  units?: string | null;
  caveats: string[];
};

type CandidateHypothesisComparison = {
  screened_as?: string | null;
  ran_as: string;
  cm1_outcome: string;
  match_status: string;
  match_status_label: string;
  evidence: string[];
  caveats: string[];
};

type ResultCard = {
  result_id: string;
  run_id: string;
  name: string;
  tags: string[];
  notes: string | null;
  saved: boolean;
  protected: boolean;
  scenario_id: string;
  scenario_name: string | null;
  run_configuration: RunConfiguration;
  pre_run_validation_report?: PreRunValidationReport | null;
  physical_question: string;
  controls: Record<string, string | number | boolean>;
  status: string;
  source_lifecycle_state: string;
  source_product_state: string;
  source_model: string;
  input_source?: "generated_reference" | "observed_sounding" | string;
  input_source_label?: string;
  observed_sounding?: ObservedSoundingSummary | null;
  run_recipe?: string | null;
  run_recipe_display_name?: string | null;
  recipe_id?: string | null;
  recipe_display_name?: string | null;
  assumption_set_id?: string | null;
  assumption_mode?: string | null;
  recipe_assumptions?: Record<string, unknown>;
  required_output_fields?: string[];
  missing_required_output_fields?: string[];
  recipe_caveats?: string[];
  trigger_type?: string | null;
  trigger_parameters?: Record<string, unknown> | null;
  expected_outputs?: string[];
  run_caveats?: string[];
  manual_validation_status?: string | null;
  candidate_screening?: Record<string, unknown> | null;
  candidate_hypothesis_comparison?: CandidateHypothesisComparison | null;
  provenance_labels: string[];
  diagnostics_summary: string | null;
  thermal_fate_label?: string | null;
  thermal_fate_confidence?: string | null;
  main_limiting_factor?: string | null;
  first_cloud_time_seconds: number | null;
  max_qc_kg_kg: number | null;
  time_of_max_qc_seconds?: number | null;
  max_w_m_s: number | null;
  time_of_max_w_seconds?: number | null;
  min_w_m_s: number | null;
  time_of_min_w_seconds?: number | null;
  rain_present: boolean | null;
  first_rain_time_seconds?: number | null;
  surface_rain_present?: boolean | null;
  max_surface_rain?: number | null;
  surface_rain_units?: string | null;
  max_dbz?: number | null;
  reflectivity_available?: boolean | null;
  surface_fluxes?: SurfaceFluxDiagnostics | null;
  localized_response?: LocalizedResponseDiagnostics | null;
  runtime_integrity?: RuntimeIntegrity | null;
  field_quality_assessed?: boolean;
  field_quality?: Record<string, FieldQuality>;
  interesting_times?: InterestingTimeRecord[];
  default_time_by_field?: Record<string, FieldDefaultTime>;
  science_summary?: ScienceSummary | null;
  interesting_time_caveats?: string[];
  caveats: string[];
  output_file_summary: OutputFileSummary;
  created_at: string;
  completed_at: string | null;
  ingested_at: string;
  updated_at: string;
};

type ResultsResponse = {
  results: ResultCard[];
};

type ResultsBooleanFilter = "all" | "yes" | "no" | "unknown";
type ResultsSortKey =
  | "newest"
  | "oldest"
  | "name"
  | "scenario"
  | "first_cloud"
  | "max_qc"
  | "max_updraft"
  | "rain_onset"
  | "latest_output";

type ResultsFilterState = {
  search: string;
  scenario: string;
  cloud: ResultsBooleanFilter;
  rain: ResultsBooleanFilter;
  sort: ResultsSortKey;
};

type RunStorageEntry = {
  run_id: string;
  scenario_id: string | null;
  scenario_name: string | null;
  lifecycle_state: string | null;
  validation_status: string | null;
  product_state: string | null;
  run_configuration: RunConfiguration | null;
  pre_run_validation_report?: PreRunValidationReport | null;
  created_at: string | null;
  updated_at: string | null;
  saved: boolean;
  protected: boolean;
  output_artifact_count: number;
  output_summary: {
    raw_cm1_artifacts?: number;
    netcdf_paths?: number;
    processed_artifacts?: number;
  };
  size_bytes: number;
  path: string;
  category: string;
  manifest_path: string | null;
  manifest_error: string | null;
  progress?: RunProgressResponse | null;
  worker_state: string | null;
  worker_message: string | null;
  worker_started_at: string | null;
  worker_finished_at: string | null;
  worker_status_updated_at: string | null;
  worker_remote_dir: string | null;
  worker_netcdf_count: number | null;
  worker_raw_artifact_count: number | null;
  worker_progress?: RunProgressResponse | null;
};

type StorageInventoryResponse = {
  runtime_home: string;
  runs_directory: string;
  total_size_bytes: number;
  warning_threshold_bytes: number;
  above_warning_threshold: boolean;
  warning_message: string | null;
  runs: RunStorageEntry[];
  largest_runs: RunStorageEntry[];
};

type DeleteRunResponse = {
  run_id: string;
  run_directory: string;
  dry_run: boolean;
  deleted: boolean;
  size_bytes: number;
  message: string;
};

type ResultCleanupCategory = {
  label: string;
  description: string;
  present: boolean;
  item_count: number;
};

type DeleteResultResponse = {
  result_id: string;
  run_id: string;
  run_directory: string;
  dry_run: boolean;
  deleted: boolean;
  size_bytes: number;
  message: string;
  affected_surfaces: string[];
  categories: ResultCleanupCategory[];
};

type WorkspaceSection = "build" | "results" | "explore";
type ScenarioLoadState = "loading" | "loaded" | "failed" | "empty";

type ProvenancePayload = {
  source_model: string;
  result_id: string;
  run_id: string;
  scenario_id: string;
  source_product_state: string;
  result_state: string;
  processing_method: string;
  rendering_method: string;
  provenance_label: string;
};

type VisualizableField = {
  raw_field_name: string;
  canonical_field_name: string;
  display_name: string;
  units: string | null;
  dimensions: string[];
  shape: number[];
  native_grid: string;
  coordinate_names: {
    time: string | null;
    vertical: string | null;
    y: string | null;
    x: string | null;
  };
  time_coordinate_values: Array<number | string | null>;
  provenance: ProvenancePayload;
  caveats: string[];
};

type FieldCatalogResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  source_model: string;
  available_fields: VisualizableField[];
  provenance: ProvenancePayload;
  caveats: string[];
};

type SliceResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  field: VisualizableField;
  selection: {
    time_index: number;
    time_seconds: number | null;
    orientation: "horizontal" | "vertical_x" | "vertical_y";
    selected_dimension: string;
    selected_index: number;
    selected_coordinate_value: number | string | null;
    level_units: string | null;
    level_coordinate_value: number | string | null;
    level_meters: number | null;
  };
  coordinate_units: Record<string, string | null>;
  shape: number[];
  dimension_order: string[];
  data_encoding: "json";
  values: Array<Array<number | null>>;
  stats: {
    min: number | null;
    max: number | null;
    mean: number | null;
    finite_count: number;
    non_finite_count: number;
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type PointCloudResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  field: VisualizableField;
  selection: {
    field: string;
    time_index: number;
    time_seconds: number | null;
    threshold: number;
    max_points: number;
  };
  coordinate_units: Record<string, string | null>;
  coordinate_extents: Record<string, { min: number; max: number; units: string | null }>;
  point_order: string[];
  points: Array<[number, number, number, number]>;
  stats: {
    source_count: number;
    returned_count: number;
    field_min_value: number | null;
    field_max_value: number | null;
    field_mean_value: number | null;
    field_finite_count: number;
    field_non_finite_count: number;
    min_value: number | null;
    max_value: number | null;
    active_z_min: number | null;
    active_z_max: number | null;
    max_value_location: { x: number; y: number; z: number; value: number } | null;
    downsampled: boolean;
    downsample_stride: number;
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type ThreeDScalarEncoding = {
  field: VisualizableField;
  defaultThreshold: number;
  thresholdStep: number;
  statusLabel: string;
  emptyStateTitle: string;
  thresholdAriaLabel: string;
  thresholdLabel: string;
  rangeLabel: string;
  valueChannel: string;
};

type RegionType = "point" | "column" | "box";

type SelectedRegionRequest = {
  regionType: RegionType;
  xIndex?: number;
  yIndex?: number;
  zIndex?: number;
  xStart?: number;
  xEnd?: number;
  yStart?: number;
  yEnd?: number;
  zStart?: number;
  zEnd?: number;
  neighborhood?: number;
};

type AxisSelection = {
  dimension: string;
  start_index: number;
  end_index: number;
  start_coordinate: number | string | null;
  end_coordinate: number | string | null;
  units: string | null;
};

type TimeValue = {
  time_seconds: number | null;
  value: number | null;
};

type SelectedRegionDiagnosticsResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  region: {
    region_type: RegionType;
    requested: Record<string, unknown>;
    x: AxisSelection | null;
    y: AxisSelection | null;
    vertical: AxisSelection | null;
    native_grid: string | null;
    cell_count: number | null;
  };
  diagnostics: {
    available: boolean;
    local_max_w_m_s: number | null;
    time_of_local_max_w_seconds: number | null;
    local_min_w_m_s: number | null;
    time_of_local_min_w_seconds: number | null;
    local_w_max_time_series: TimeValue[];
    local_w_min_time_series: TimeValue[];
    local_max_qc_kg_kg: number | null;
    time_of_local_max_qc_seconds: number | null;
    first_local_cloud_time_seconds: number | null;
    local_cloud_fraction_time_series: TimeValue[];
    local_qc_max_time_series: TimeValue[];
    local_cloud_base_time_series: TimeValue[];
    local_cloud_top_time_series: TimeValue[];
    local_max_qc_height_time_series: TimeValue[];
    local_max_w_height_time_series: TimeValue[];
    local_rain_present: boolean;
    first_local_rain_time_seconds: number | null;
    local_max_qr_kg_kg: number | null;
    time_of_local_max_qr_seconds: number | null;
    local_qr_max_time_series: TimeValue[];
  };
  comparison_to_domain: {
    local_max_w_fraction_of_domain: number | null;
    local_max_qc_fraction_of_domain: number | null;
    local_first_cloud_time_delta_seconds: number | null;
    local_cloud_top_fraction_of_domain: number | null;
    local_first_rain_time_delta_seconds: number | null;
    caveats: string[];
  };
  interpretation: {
    thermal_fate_label: string;
    confidence: ProcessSupport;
    main_limiting_factor: string;
    summary: string;
    caveats: string[];
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type FieldViewDefaults = {
  field: string;
  time_index: number;
  time_seconds: number | null;
  horizontal_level_index: number;
  vertical_x_index: number;
  vertical_y_index: number;
  source: string;
  max_value: number | null;
  selected_time_index: number | null;
  selected_time_seconds: number | null;
  caveats: string[];
};

type ViewDefaultsResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  preferred_field: string | null;
  fields: Record<string, FieldViewDefaults>;
  provenance: ProvenancePayload;
  caveats: string[];
};

type ProcessMode =
  | "thermal_fate"
  | "cloud_water"
  | "updrafts"
  | "moisture"
  | "buoyancy"
  | "cap"
  | "cloud_lifecycle"
  | "deep_breakthrough"
  | "precipitation_feedback";
type SceneSlicePlane = "horizontal" | "vertical_x" | "vertical_y";

const FIELD_LOAD_TIMEOUT_MS = 30000;
const OBSERVED_SOUNDING_EXPERIMENT_ID = "__observed_sounding_upload__";
const OBSERVED_SOUNDING_BASE_SCENARIO_ID = "baseline-shallow-cumulus";
const candidateStoryIdValues = new Set<string>([
  "shallow_cumulus_candidate",
  "dry_failed_candidate",
  "capped_suppressed_candidate",
  "humid_rainy_candidate",
  "severe_thunderstorm_environment",
  "supercell_environment",
  "high_cape_pulse_storm",
  "dry_microburst_inverted_v",
  "squall_line_cold_pool_candidate",
  "elevated_convection",
  "needs_review",
  "poor_or_incomplete_candidate",
]);
const deepConvectionStoryIds = new Set<string>([
  "severe_thunderstorm_environment",
  "supercell_environment",
  "high_cape_pulse_storm",
  "dry_microburst_inverted_v",
  "squall_line_cold_pool_candidate",
  "elevated_convection",
]);
const candidateSuggestedTags = [
  "Deep convection candidates",
  "Surface-forced candidates",
  "Needs longer run",
  "Needs finer output cadence",
  "Maybe rerun",
  "Needs review",
] as const;

const DEFAULT_SHALLOW_RUN_CONFIGURATION: RunConfigurationInput = {
  duration: "short_6h",
  horizontal_cell_count: "cells_64",
  domain_size: "local_6km",
  output_cadence: "standard_15min",
  diagnostic_set: "full",
  surface_forcing_mode: UNIFORM_SURFACE_FORCING_MODE,
  surface_heat_flux_k_m_s: "8.0e-3",
  surface_moisture_flux_g_g_m_s: "5.2e-5",
  surface_patch_shape: "circle",
  surface_patch_radius_m: "1500",
  surface_patch_radius_x_m: "1500",
  surface_patch_radius_y_m: "1500",
  surface_patch_heat_flux_perturbation_k_m_s: "4.0e-2",
  surface_patch_moisture_flux_perturbation_g_g_m_s: "5.0e-5",
  surface_patch_taper_width_m: "500",
  surface_patch_ramp_seconds: "1800",
};

const DEFAULT_OBSERVED_RUN_CONFIGURATION: RunConfigurationInput = {
  duration: "short_6h",
  horizontal_cell_count: "cells_128",
  domain_size: "wide_12km",
  output_cadence: "standard_15min",
  diagnostic_set: "full",
  surface_forcing_mode: UNIFORM_SURFACE_FORCING_MODE,
  surface_heat_flux_k_m_s: "8.0e-3",
  surface_moisture_flux_g_g_m_s: "5.2e-5",
  surface_patch_shape: "circle",
  surface_patch_radius_m: "1500",
  surface_patch_radius_x_m: "1500",
  surface_patch_radius_y_m: "1500",
  surface_patch_heat_flux_perturbation_k_m_s: "4.0e-2",
  surface_patch_moisture_flux_perturbation_g_g_m_s: "5.0e-5",
  surface_patch_taper_width_m: "500",
  surface_patch_ramp_seconds: "1800",
};

const DEFAULT_DEEP_TOWER_RUN_CONFIGURATION: RunConfigurationInput = {
  duration: "scout_2h",
  horizontal_cell_count: "cells_120",
  domain_size: "deep_tower_120km",
  output_cadence: "standard_15min",
  diagnostic_set: "full",
  surface_forcing_mode: DISABLED_SURFACE_FORCING_MODE,
  surface_heat_flux_k_m_s: "0",
  surface_moisture_flux_g_g_m_s: "0",
  surface_patch_shape: "circle",
  surface_patch_radius_m: "1500",
  surface_patch_radius_x_m: "1500",
  surface_patch_radius_y_m: "1500",
  surface_patch_heat_flux_perturbation_k_m_s: "4.0e-2",
  surface_patch_moisture_flux_perturbation_g_g_m_s: "5.0e-5",
  surface_patch_taper_width_m: "500",
  surface_patch_ramp_seconds: "1800",
  time_step_seconds: "6.0",
};

const SEARCH_INTENT_OPTIONS: Array<{ value: SearchIntent; label: string }> = [
  { value: "best_overall", label: "Best overall recommendations" },
  { value: "deep_convection", label: "Deep-convection ingredients" },
  { value: "humid_rainy", label: "Humid/rainy evolution" },
  { value: "dry_microburst", label: "Dry microburst / inverted-V" },
  { value: "shallow_boundary_layer", label: "Shallow cumulus / boundary layer" },
];

const HISTORY_SCOPE_OPTIONS: Array<{
  value: CandidateHistoryScope;
  label: string;
  description: string;
}> = [
  {
    value: "all_cached",
    label: "All cached history",
    description: "Analyze every cached sounding for the selected stations.",
  },
  {
    value: "latest_per_station",
    label: "Latest N per station",
    description: "Analyze an explicit recent-history set for the selected stations.",
  },
];

const DEFAULT_LATEST_PER_STATION = "20";
const DEFAULT_CANDIDATE_RESULT_LIMIT = "100";

class DryRunRequestError extends Error {
  preRunValidationReport: PreRunValidationReport | null;

  constructor(message: string, preRunValidationReport: PreRunValidationReport | null = null) {
    super(message);
    this.name = "DryRunRequestError";
    this.preRunValidationReport = preRunValidationReport;
  }
}

async function fetchScenarioCatalog(): Promise<ScenarioResponse> {
  const response = await fetch("/api/scenarios");
  if (!response.ok) {
    throw new Error("Unable to load scenarios.");
  }
  return response.json() as Promise<ScenarioResponse>;
}

async function requestDryRunPackage(
  scenarioId: string,
  controls: Record<string, string | number | boolean>,
  runConfiguration: RunConfigurationInput,
  runRecipe?: RunRecipe | null,
  observedSounding?: ObservedSoundingRecord | null,
  candidateScreening?: Record<string, unknown> | null,
  userMetadata?: {
    name?: string | null;
    tags?: string[];
    notes?: string | null;
  } | null,
): Promise<DryRunResponse> {
  const response = await fetch("/api/dry-run-package", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario_id: scenarioId,
      controls,
      run_configuration: runConfiguration,
      run_recipe: runRecipe ?? null,
      observed_sounding: observedSounding ?? null,
      candidate_screening: candidateScreening ?? null,
      user_name: userMetadata?.name ?? null,
      user_tags: userMetadata?.tags ?? [],
      user_notes: userMetadata?.notes ?? null,
    }),
  });
  if (!response.ok) {
    const detail = await dryRunErrorDetail(response);
    throw new DryRunRequestError(detail.message, detail.preRunValidationReport);
  }
  return response.json() as Promise<DryRunResponse>;
}

async function dryRunErrorDetail(
  response: Response,
): Promise<{ message: string; preRunValidationReport: PreRunValidationReport | null }> {
  try {
    const payload = (await response.json()) as {
      detail?:
        | string
        | {
            message?: string;
            pre_run_validation_report?: unknown;
          };
    };
    if (typeof payload.detail === "string") {
      return { message: payload.detail, preRunValidationReport: null };
    }
    if (payload.detail && typeof payload.detail === "object") {
      return {
        message: payload.detail.message ?? "Unable to create dry-run package.",
        preRunValidationReport: isPreRunValidationReport(payload.detail.pre_run_validation_report)
          ? payload.detail.pre_run_validation_report
          : null,
      };
    }
  } catch {
    return { message: "Unable to create dry-run package.", preRunValidationReport: null };
  }
  return { message: "Unable to create dry-run package.", preRunValidationReport: null };
}

function isPreRunValidationReport(value: unknown): value is PreRunValidationReport {
  return Boolean(value && typeof value === "object" && "status" in value);
}

async function parseObservedSoundingUpload(
  uploadedFilename: string,
  text: string,
  selectedTimeUtc?: string | null,
): Promise<ObservedSoundingParseResponse> {
  const response = await fetch("/api/observed-soundings/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      uploaded_filename: uploadedFilename,
      text,
      selected_time_utc: selectedTimeUtc ?? null,
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to parse observed sounding."));
  }
  return response.json() as Promise<ObservedSoundingParseResponse>;
}

async function fetchIGRARecentCatalog(): Promise<IGRACatalogResponse> {
  const response = await fetch("/api/igra/recent/catalog");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load IGRA recent catalog."));
  }
  return response.json() as Promise<IGRACatalogResponse>;
}

async function refreshIGRARecentCatalog(): Promise<IGRACatalogResponse["catalog"]> {
  const response = await fetch("/api/igra/recent/refresh-catalog", { method: "POST" });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to refresh IGRA recent catalog."));
  }
  return response.json() as Promise<IGRACatalogResponse["catalog"]>;
}

async function fetchIGRARecentCache(): Promise<IGRACacheResponse> {
  const response = await fetch("/api/igra/recent/cache");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load IGRA recent cache."));
  }
  return response.json() as Promise<IGRACacheResponse>;
}

async function cacheIGRARecentBatch(options: {
  limit?: number;
  stationIds?: string[];
}): Promise<IGRABatchCacheResponse> {
  const response = await fetch("/api/igra/recent/cache-batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      limit: options.limit ?? 10,
      station_ids: options.stationIds ?? [],
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to cache IGRA station files."));
  }
  return response.json() as Promise<IGRABatchCacheResponse>;
}

async function fetchScreeningInputs(): Promise<ScreeningInputsResponse> {
  const response = await fetch("/api/sounding-candidates/screening-inputs");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load screenable soundings."));
  }
  return response.json() as Promise<ScreeningInputsResponse>;
}

async function screenSoundingCandidates(options: {
  stationIds: string[];
  historyScope: CandidateHistoryScope;
  story: CandidateStoryFilter;
  storyFamily: CandidateStoryFamilyFilter;
  support: CandidateSupportFilter;
  readiness: CandidateReadinessFilter;
  stationSearch: string;
  sort: CandidateSort;
  latestPerStation: number | null;
  limit: number;
}): Promise<ScreeningResult> {
  const response = await fetch("/api/sounding-candidates/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      station_ids: options.stationIds,
      history_scope: options.historyScope,
      latest_per_station: options.latestPerStation,
      limit: options.limit,
      story_filter: options.story,
      story_family: options.storyFamily,
      support: options.support,
      readiness: options.readiness,
      station_search: options.stationSearch,
      sort_by: options.sort,
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to search selected soundings."));
  }
  return response.json() as Promise<ScreeningResult>;
}

async function fetchSavedSoundingCandidates(): Promise<SavedCandidatesResponse> {
  const response = await fetch("/api/sounding-candidates/saved");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load saved sounding candidates."));
  }
  return response.json() as Promise<SavedCandidatesResponse>;
}

async function saveSoundingCandidate(
  candidate: SoundingCandidate,
  tags: string[],
  notes: string | null,
): Promise<SavedSoundingCandidate> {
  const response = await fetch("/api/sounding-candidates/saved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate, tags, notes }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to save sounding candidate."));
  }
  return response.json() as Promise<SavedSoundingCandidate>;
}

async function updateSavedSoundingCandidate(
  savedCandidateId: string,
  tags: string[],
  notes: string | null,
): Promise<SavedSoundingCandidate> {
  const response = await fetch(`/api/sounding-candidates/saved/${savedCandidateId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tags, notes }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to update saved sounding candidate."));
  }
  return response.json() as Promise<SavedSoundingCandidate>;
}

async function deleteSavedSoundingCandidate(savedCandidateId: string): Promise<void> {
  const response = await fetch(`/api/sounding-candidates/saved/${savedCandidateId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to remove saved candidate."));
  }
}

async function readUploadedTextFile(file: File): Promise<string> {
  const textMethod = (file as Blob & { text?: () => Promise<string> }).text;
  if (typeof textMethod === "function") {
    return textMethod.call(file);
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
        return;
      }
      reject(new Error("Unable to read uploaded sounding as text."));
    };
    reader.onerror = () => reject(reader.error ?? new Error("Unable to read uploaded sounding."));
    reader.readAsText(file);
  });
}

async function enqueueLocalRun(manifestPath: string): Promise<RunQueueResponse> {
  const response = await fetch("/api/runs/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to queue local CM1 run."));
  }
  return response.json() as Promise<RunQueueResponse>;
}

async function fetchRunQueue(): Promise<RunQueueResponse> {
  const response = await fetch("/api/runs/queue");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to refresh local run queue."));
  }
  return response.json() as Promise<RunQueueResponse>;
}

async function fetchRunStatus(manifestPath: string): Promise<RunStatusResponse> {
  const search = new URLSearchParams({ manifest_path: manifestPath });
  const response = await fetch(`/api/runs/status?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to refresh run status."));
  }
  return response.json() as Promise<RunStatusResponse>;
}

async function fetchLanWorkerConfig(): Promise<LanWorkerConfigResponse> {
  const response = await fetch("/api/lan-worker/config");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load LAN worker configuration."));
  }
  return response.json() as Promise<LanWorkerConfigResponse>;
}

async function startLanWorkerRun(manifestPath: string): Promise<LanWorkerRunResponse> {
  const response = await fetch("/api/lan-worker/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to start LAN worker run."));
  }
  return response.json() as Promise<LanWorkerRunResponse>;
}

async function fetchLanWorkerStatus(manifestPath: string): Promise<LanWorkerRunResponse> {
  const search = new URLSearchParams({ manifest_path: manifestPath });
  const response = await fetch(`/api/lan-worker/status?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to refresh LAN worker status."));
  }
  return response.json() as Promise<LanWorkerRunResponse>;
}

async function collectLanWorkerRun(manifestPath: string): Promise<LanWorkerRunResponse> {
  const response = await fetch("/api/lan-worker/collect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to copy LAN worker output back."));
  }
  return response.json() as Promise<LanWorkerRunResponse>;
}

async function cleanupLanWorkerRun(manifestPath: string): Promise<LanWorkerRunResponse> {
  const response = await fetch("/api/lan-worker/cleanup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to clean up LAN worker copy."));
  }
  return response.json() as Promise<LanWorkerRunResponse>;
}

async function ingestCompletedRun(manifestPath: string): Promise<IngestResponse> {
  const response = await fetch("/api/results/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to ingest completed CM1 output."));
  }
  return response.json() as Promise<IngestResponse>;
}

async function fetchResults(): Promise<ResultsResponse> {
  const response = await fetch("/api/results");
  if (!response.ok) {
    throw new Error("Could not load results.");
  }
  return normalizeResultsResponse(await response.json());
}

function normalizeResultsResponse(payload: unknown): ResultsResponse {
  if (Array.isArray(payload)) {
    return { results: payload as ResultCard[] };
  }
  if (isObject(payload) && Array.isArray(payload.results)) {
    return { results: payload.results as ResultCard[] };
  }
  throw new Error("Could not load results.");
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function patchResultCard(
  resultId: string,
  update: Partial<Pick<ResultCard, "name" | "tags" | "notes">>,
): Promise<ResultCard> {
  const response = await fetch(`/api/results/${resultId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  if (!response.ok) {
    throw new Error("Unable to update result card.");
  }
  return response.json() as Promise<ResultCard>;
}

async function fetchStorageInventory(): Promise<StorageInventoryResponse> {
  const response = await fetch("/api/storage/inventory");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load runtime run inventory."));
  }
  return response.json() as Promise<StorageInventoryResponse>;
}

async function requestRunDeletePreview(runId: string): Promise<DeleteRunResponse> {
  const response = await fetch("/api/storage/delete-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_id: runId,
      dry_run: true,
      confirm: false,
      force_saved: false,
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to preview run deletion."));
  }
  return response.json() as Promise<DeleteRunResponse>;
}

async function confirmRunDelete(runId: string): Promise<DeleteRunResponse> {
  const response = await fetch("/api/storage/delete-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_id: runId,
      dry_run: false,
      confirm: true,
      force_saved: false,
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to delete selected run."));
  }
  return response.json() as Promise<DeleteRunResponse>;
}

async function requestResultDeletePreview(resultId: string): Promise<DeleteResultResponse> {
  const response = await fetch(`/api/results/${resultId}/delete-preview`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to preview result deletion."));
  }
  return response.json() as Promise<DeleteResultResponse>;
}

async function confirmResultDelete(resultId: string): Promise<DeleteResultResponse> {
  const response = await fetch(`/api/results/${resultId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to delete selected result."));
  }
  return response.json() as Promise<DeleteResultResponse>;
}

async function fetchVisualizationFields(resultId: string): Promise<FieldCatalogResponse> {
  const response = await fetch(`/api/results/${resultId}/visualization/fields`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization fields."));
  }
  return response.json() as Promise<FieldCatalogResponse>;
}

function withTimeout<T>(promise: Promise<T>, message: string, timeoutMs = FIELD_LOAD_TIMEOUT_MS) {
  let timeoutId: number | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = window.setTimeout(() => reject(new Error(message)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => {
    if (timeoutId !== undefined) window.clearTimeout(timeoutId);
  });
}

async function fetchVisualizationDefaults(
  resultId: string,
  timeIndex?: number,
): Promise<ViewDefaultsResponse> {
  const search = timeIndex === undefined ? "" : `?time_index=${timeIndex}`;
  const response = await fetch(`/api/results/${resultId}/visualization/defaults${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization defaults."));
  }
  return response.json() as Promise<ViewDefaultsResponse>;
}

async function fetchVisualizationSlice(
  resultId: string,
  params: {
    field: string;
    timeIndex: number;
    orientation: "horizontal" | "vertical_x" | "vertical_y";
    levelIndex: number;
  },
): Promise<SliceResponse> {
  const search = new URLSearchParams({
    field: params.field,
    time_index: String(params.timeIndex),
    orientation: params.orientation,
    level_index: String(params.levelIndex),
    encoding: "json",
  });
  const response = await fetch(`/api/results/${resultId}/visualization/slice?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization slice."));
  }
  return response.json() as Promise<SliceResponse>;
}

async function fetchVisualizationPointCloud(
  resultId: string,
  params: {
    field: string;
    timeIndex: number;
    threshold: number;
    maxPoints: number;
  },
): Promise<PointCloudResponse> {
  const search = new URLSearchParams({
    field: params.field,
    time_index: String(params.timeIndex),
    threshold: String(params.threshold),
    max_points: String(params.maxPoints),
    encoding: "json",
  });
  const response = await fetch(`/api/results/${resultId}/visualization/point-cloud?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load 3-D scalar point layer."));
  }
  return response.json() as Promise<PointCloudResponse>;
}

async function fetchSelectedRegionDiagnostics(
  resultId: string,
  request: SelectedRegionRequest,
): Promise<SelectedRegionDiagnosticsResponse> {
  const search = new URLSearchParams({
    region_type: request.regionType,
    neighborhood: String(request.neighborhood ?? 0),
  });
  addOptionalIndex(search, "x_index", request.xIndex);
  addOptionalIndex(search, "y_index", request.yIndex);
  addOptionalIndex(search, "z_index", request.zIndex);
  addOptionalIndex(search, "x_start", request.xStart);
  addOptionalIndex(search, "x_end", request.xEnd);
  addOptionalIndex(search, "y_start", request.yStart);
  addOptionalIndex(search, "y_end", request.yEnd);
  addOptionalIndex(search, "z_start", request.zStart);
  addOptionalIndex(search, "z_end", request.zEnd);
  const response = await fetch(`/api/results/${resultId}/diagnostics/selected-region?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to inspect the selected region."));
  }
  return response.json() as Promise<SelectedRegionDiagnosticsResponse>;
}

function addOptionalIndex(search: URLSearchParams, key: string, value: number | undefined) {
  if (value !== undefined) search.set(key, String(value));
}

async function responseError(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export function App() {
  const [activeSection, setActiveSection] = useState<WorkspaceSection>("results");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(OBSERVED_SOUNDING_EXPERIMENT_ID);
  const [controls, setControls] = useState<Record<string, string | number | boolean>>({});
  const [runConfiguration, setRunConfiguration] = useState<RunConfigurationInput>(
    DEFAULT_SHALLOW_RUN_CONFIGURATION,
  );
  const [observedSoundingFilename, setObservedSoundingFilename] = useState<string | null>(null);
  const [observedSoundingText, setObservedSoundingText] = useState<string | null>(null);
  const [observedSoundingParse, setObservedSoundingParse] =
    useState<ObservedSoundingParseResponse | null>(null);
  const [observedSoundingStatus, setObservedSoundingStatus] = useState<string | null>(null);
  const [observedSoundingError, setObservedSoundingError] = useState<string | null>(null);
  const [selectedCandidateScreening, setSelectedCandidateScreening] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [atmosphereSourcePath, setAtmosphereSourcePath] =
    useState<AtmosphereSourcePath>("cached_recommendations");
  const [searchIntent, setSearchIntent] = useState<SearchIntent>("best_overall");
  const [stationSelectionMode, setStationSelectionMode] =
    useState<StationSelectionMode>("all_cached");
  const [selectedStationIds, setSelectedStationIds] = useState<string[]>([]);
  const [candidateHistoryScope, setCandidateHistoryScope] =
    useState<CandidateHistoryScope>("all_cached");
  const [igraCatalog, setIgraCatalog] = useState<IGRACatalogResponse["catalog"] | null>(null);
  const [igraCache, setIgraCache] = useState<IGRACacheResponse | null>(null);
  const [screeningInputs, setScreeningInputs] = useState<ScreeningInput[]>([]);
  const [candidateStoryFilter, setCandidateStoryFilter] = useState<CandidateStoryFilter>("all");
  const [candidateStoryFamilyFilter, setCandidateStoryFamilyFilter] =
    useState<CandidateStoryFamilyFilter>("all");
  const [candidateSupportFilter, setCandidateSupportFilter] =
    useState<CandidateSupportFilter>("all");
  const [candidateSort, setCandidateSort] = useState<CandidateSort>("best_match");
  const [candidateStationSearch, setCandidateStationSearch] = useState("");
  const [candidateReadinessFilter, setCandidateReadinessFilter] =
    useState<CandidateReadinessFilter>("all");
  const [candidateLatestPerStation, setCandidateLatestPerStation] = useState(
    DEFAULT_LATEST_PER_STATION,
  );
  const [candidateResultLimit, setCandidateResultLimit] = useState(DEFAULT_CANDIDATE_RESULT_LIMIT);
  const [candidateStatus, setCandidateStatus] = useState("IGRA cache not checked yet");
  const [candidateError, setCandidateError] = useState<string | null>(null);
  const [candidateScreening, setCandidateScreening] = useState<ScreeningResult | null>(null);
  const [savedCandidates, setSavedCandidates] = useState<SavedSoundingCandidate[]>([]);
  const [candidateDetailId, setCandidateDetailId] = useState<string | null>(null);
  const [runPlanItems, setRunPlanItems] = useState<RunPlanItem[]>([]);
  const [batchQueueStatus, setBatchQueueStatus] = useState<string | null>(null);
  const [dryRun, setDryRun] = useState<DryRunResponse | null>(null);
  const [blockedPreRunValidationReport, setBlockedPreRunValidationReport] =
    useState<PreRunValidationReport | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [runQueue, setRunQueue] = useState<RunQueueResponse | null>(null);
  const [runQueueStatus, setRunQueueStatus] = useState("Local run queue not checked yet");
  const [runWorkflowError, setRunWorkflowError] = useState<string | null>(null);
  const [lanWorkerConfig, setLanWorkerConfig] = useState<LanWorkerConfigResponse | null>(null);
  const [lanWorkerStatus, setLanWorkerStatus] = useState<LanWorkerRunResponse | null>(null);
  const [lanWorkerError, setLanWorkerError] = useState<string | null>(null);
  const [lanWorkerActionStatus, setLanWorkerActionStatus] = useState<string | null>(null);
  const [autoFinalizingWorkerRunIds, setAutoFinalizingWorkerRunIds] = useState<string[]>([]);
  const [failedAutoFinalizingWorkerRunIds, setFailedAutoFinalizingWorkerRunIds] = useState<
    string[]
  >([]);
  const [ingestedResultId, setIngestedResultId] = useState<string | null>(null);
  const [results, setResults] = useState<ResultCard[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const selectedResultIdRef = useRef<string | null>(null);
  const [resultDraft, setResultDraft] = useState({ name: "", tags: "", notes: "" });
  const [resultsStatus, setResultsStatus] = useState("Loading results...");
  const [storageInventory, setStorageInventory] = useState<StorageInventoryResponse | null>(null);
  const [storageStatus, setStorageStatus] = useState("Loading run inventory...");
  const [storageError, setStorageError] = useState<string | null>(null);
  const [runDeletePreview, setRunDeletePreview] = useState<DeleteRunResponse | null>(null);
  const [runDeleteMessage, setRunDeleteMessage] = useState<string | null>(null);
  const [resultDeletePreview, setResultDeletePreview] = useState<DeleteResultResponse | null>(null);
  const [, setStatus] = useState("Loading scenarios...");
  const [scenarioLoadState, setScenarioLoadState] = useState<ScenarioLoadState>("loading");
  const [scenarioError, setScenarioError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);

  const loadScenarios = useCallback(async (active: () => boolean = () => true) => {
    setScenarioLoadState("loading");
    setScenarioError(null);
    setError(null);
    setStatus("Loading scenarios...");
    setScenarios([]);
    setDryRun(null);
    setBlockedPreRunValidationReport(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setLanWorkerStatus(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus(null);
    setIngestedResultId(null);
    try {
      const catalog = await fetchScenarioCatalog();
      if (!active()) return;
      setScenarios(catalog.scenarios);
      setSelectedScenarioId(
        catalog.scenarios.some((scenario) => scenario.id === OBSERVED_SOUNDING_BASE_SCENARIO_ID)
          ? OBSERVED_SOUNDING_EXPERIMENT_ID
          : catalog.golden_path_scenario_id,
      );
      if (catalog.scenarios.length === 0) {
        setScenarioLoadState("empty");
        setStatus("No scenarios available");
      } else {
        setScenarioLoadState("loaded");
        setStatus("Scenario setup");
      }
    } catch (caught: unknown) {
      if (!active()) return;
      setScenarioLoadState("failed");
      setScenarioError(caught instanceof Error ? caught.message : "Unable to load scenarios.");
      setStatus("Scenario load failed");
    }
  }, []);

  useEffect(() => {
    let active = true;
    loadScenarios(() => active);
    return () => {
      active = false;
    };
  }, [loadScenarios]);

  useEffect(() => {
    let active = true;
    fetchResults()
      .then((payload) => {
        if (!active) return;
        const prioritized = prioritizeResults(payload.results);
        setResults(prioritized);
        setSelectedResultId((current) => current ?? prioritized[0]?.result_id ?? null);
        setResultsStatus(payload.results.length > 0 ? "Results loaded" : "No ingested results");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setResults([]);
        setSelectedResultId(null);
        setResultsError(caught instanceof Error ? caught.message : "Could not load results.");
        setResultsStatus("Results unavailable");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    fetchLanWorkerConfig()
      .then((payload) => {
        if (!active) return;
        setLanWorkerConfig(payload);
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setLanWorkerConfig({
          configured: false,
          available: false,
          message: caught instanceof Error ? caught.message : "Unable to load LAN worker setup.",
          cm1_env_keys: [],
          cm1_env_settings: [],
          custom_launch_command: false,
        });
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    refreshStorageInventory().catch(() => undefined);
    return () => {
      active = false;
    };

    async function refreshStorageInventory() {
      try {
        const payload = await fetchStorageInventory();
        if (!active) return;
        setStorageInventory(payload);
        setStorageStatus(payload.runs.length > 0 ? "Run inventory loaded" : "No runtime runs");
      } catch (caught) {
        if (!active) return;
        setStorageError(
          caught instanceof Error ? caught.message : "Unable to load runtime run inventory.",
        );
        setStorageStatus("Run inventory unavailable");
      }
    }
  }, []);

  const selectedScenario = useMemo(
    () =>
      scenarios.find((scenario) =>
        selectedScenarioId === OBSERVED_SOUNDING_EXPERIMENT_ID
          ? scenario.id === OBSERVED_SOUNDING_BASE_SCENARIO_ID
          : scenario.id === selectedScenarioId,
      ) ?? scenarios[0],
    [scenarios, selectedScenarioId],
  );
  const observedSoundingExperimentSelected = selectedScenarioId === OBSERVED_SOUNDING_EXPERIMENT_ID;

  const selectedResult = useMemo(
    () =>
      selectedResultId
        ? results.find((result) => result.result_id === selectedResultId)
        : results[0],
    [results, selectedResultId],
  );

  useEffect(() => {
    selectedResultIdRef.current = selectedResultId;
    setResultDeletePreview(null);
  }, [selectedResultId]);
  const autoFinalizingWorkerRunIdSet = useMemo(
    () => new Set(autoFinalizingWorkerRunIds),
    [autoFinalizingWorkerRunIds],
  );
  const failedAutoFinalizingWorkerRunIdSet = useMemo(
    () => new Set(failedAutoFinalizingWorkerRunIds),
    [failedAutoFinalizingWorkerRunIds],
  );
  const runQueuePollKey = useMemo(() => runQueuePollingKey(runQueue), [runQueue]);

  useEffect(() => {
    if (!selectedScenario) return;
    const defaults = Object.fromEntries(
      selectedScenario.controls.map((control) => [control.id, control.default]),
    );
    setControls(defaults);
    setRunConfiguration(defaultRunConfigurationForSelection(selectedScenarioId));
    setObservedSoundingFilename(null);
    setObservedSoundingText(null);
    setObservedSoundingParse(null);
    setObservedSoundingStatus(null);
    setObservedSoundingError(null);
    setDryRun(null);
    setBlockedPreRunValidationReport(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setLanWorkerStatus(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus(null);
    setIngestedResultId(null);
  }, [selectedScenario, selectedScenarioId]);

  useEffect(() => {
    if (!observedSoundingExperimentSelected) return;
    let active = true;
    setCandidateStatus("Loading local sounding data");
    setCandidateError(null);
    Promise.all([
      fetchIGRARecentCatalog(),
      fetchIGRARecentCache(),
      fetchScreeningInputs(),
      fetchSavedSoundingCandidates(),
    ])
      .then(([catalogPayload, cachePayload, inputsPayload, savedPayload]) => {
        if (!active) return;
        setIgraCatalog(catalogPayload.catalog);
        setIgraCache(cachePayload);
        setScreeningInputs(inputsPayload.inputs);
        setSavedCandidates(savedPayload.saved_candidates);
        setCandidateStatus(
          inputsPayload.inputs.length > 0
            ? "Cached soundings ready to search"
            : "No cached sounding files ready",
        );
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setIgraCatalog(null);
        setIgraCache(null);
        setScreeningInputs([]);
        setCandidateError(
          caught instanceof Error ? caught.message : "Unable to load local sounding data.",
        );
        setCandidateStatus("Local sounding data unavailable");
      });
    return () => {
      active = false;
    };
  }, [observedSoundingExperimentSelected]);

  useEffect(() => {
    if (!selectedResult) return;
    setResultDraft({
      name: selectedResult.name,
      tags: selectedResult.tags.join(", "),
      notes: selectedResult.notes ?? "",
    });
  }, [selectedResult]);

  useEffect(() => {
    if (!storageInventory) return;
    const nextRun = storageInventory.runs.find(
      (run) =>
        run.worker_state === "completed" &&
        run.manifest_path &&
        !resultForRun(results, run.run_id) &&
        !autoFinalizingWorkerRunIdSet.has(run.run_id) &&
        !failedAutoFinalizingWorkerRunIdSet.has(run.run_id),
    );
    if (!nextRun?.manifest_path) return;
    void autoFinalizeStoredLanWorkerRun(nextRun.manifest_path, nextRun.run_id);
    // autoFinalizeStoredLanWorkerRun is intentionally omitted because it mutates the
    // same worker-finalization state that gates this effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoFinalizingWorkerRunIdSet, failedAutoFinalizingWorkerRunIdSet, results, storageInventory]);

  useEffect(() => {
    void refreshLocalRunQueue("Local run queue refreshed");
    // refreshLocalRunQueue intentionally mutates several workflow surfaces after auto-ingest.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!runQueueHasOpenEntries(runQueue)) return;
    const intervalId = window.setInterval(() => {
      void refreshLocalRunQueue();
    }, 10000);
    return () => window.clearInterval(intervalId);
    // refreshLocalRunQueue intentionally reads current dryRun/results/storage state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runQueuePollKey]);

  const validationMessages = useMemo(() => {
    if (!selectedScenario) return [];
    return selectedScenario.controls.flatMap((control) => {
      const value = controls[control.id];
      const optionValues = new Set(control.options.map((option) => option.value));
      if (typeof value === "string" && optionValues.has(value)) return [];
      return [`${control.label} needs one of the listed values.`];
    });
  }, [controls, selectedScenario]);

  async function refreshStorageAfterWorkflow(statusWhenLoaded?: string) {
    try {
      const payload = await fetchStorageInventory();
      setStorageInventory(payload);
      setStorageStatus(
        statusWhenLoaded ?? (payload.runs.length > 0 ? "Run inventory loaded" : "No runtime runs"),
      );
    } catch (caught) {
      setStorageError(
        caught instanceof Error ? caught.message : "Unable to load runtime run inventory.",
      );
      setStorageStatus("Run inventory unavailable");
    }
  }

  async function refreshLocalRunQueue(statusWhenLoaded?: string): Promise<RunQueueResponse | null> {
    try {
      const payload = await fetchRunQueue();
      setRunQueue(payload);
      setRunQueueStatus(statusWhenLoaded ?? runQueueSummary(payload));
      await syncCurrentRunStatusFromQueue(payload);
      await processAutoIngestedQueue(payload);
      return payload;
    } catch (caught) {
      setRunQueueStatus("Local run queue unavailable");
      setRunWorkflowError(
        caught instanceof Error ? caught.message : "Unable to refresh local run queue.",
      );
      return null;
    }
  }

  async function syncCurrentRunStatusFromQueue(queue: RunQueueResponse): Promise<void> {
    if (!dryRun) return;
    const currentRunId = runIdFromPackage(dryRun);
    const currentEntry = queue.entries.find((entry) => entry.run_id === currentRunId);
    if (!currentEntry || !queueEntryIsOpen(currentEntry)) return;
    try {
      const refreshed = await fetchRunStatus(dryRun.manifest_path);
      setRunStatus(refreshed);
      setStatus(userFacingRunWorkflowStatus(refreshed));
    } catch {
      // The queue panel still shows serial state; status refresh can be retried manually.
    }
  }

  async function processAutoIngestedQueue(queue: RunQueueResponse): Promise<void> {
    const latestIngestedEntry = latestAutoIngestedQueueEntry(queue);
    if (!latestIngestedEntry?.result_id) return;
    if (dryRun && latestIngestedEntry.run_id === runIdFromPackage(dryRun)) {
      setIngestedResultId(latestIngestedEntry.result_id);
    }
    await refreshResults(latestIngestedEntry.result_id);
    await refreshStorageAfterWorkflow("Auto-ingested completed local run");
  }

  function handleSelectScenario(scenarioId: string) {
    setSelectedScenarioId(scenarioId);
    setObservedSoundingFilename(null);
    setObservedSoundingText(null);
    setObservedSoundingParse(null);
    setObservedSoundingStatus(null);
    setObservedSoundingError(null);
    setSelectedCandidateScreening(null);
    setRunConfiguration(defaultRunConfigurationForSelection(scenarioId));
    setDryRun(null);
    setBlockedPreRunValidationReport(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setLanWorkerStatus(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus(null);
    setIngestedResultId(null);
  }

  function handleAtmosphereSourcePathChange(sourcePath: AtmosphereSourcePath) {
    setAtmosphereSourcePath(sourcePath);
    if (selectedScenarioId !== OBSERVED_SOUNDING_EXPERIMENT_ID) {
      handleSelectScenario(OBSERVED_SOUNDING_EXPERIMENT_ID);
    }
    if (sourcePath === "cached_recommendations") {
      setCandidateStatus("Cached recommendations selected");
    } else if (sourcePath === "saved_candidates") {
      setCandidateStatus("Saved candidates selected");
    } else {
      setObservedSoundingStatus((current) => current ?? "Upload an IGRA station text file");
    }
  }

  function markCandidateSearchSettingsChanged(status: string) {
    setCandidateScreening(null);
    setCandidateDetailId(null);
    setCandidateError(null);
    setCandidateStatus(status);
  }

  function handleSearchIntentChange(intent: SearchIntent) {
    setSearchIntent(intent);
    const filters = searchIntentFilters(intent);
    setCandidateStoryFilter(filters.story);
    setCandidateStoryFamilyFilter(filters.storyFamily);
    setCandidateSupportFilter(filters.support);
    setCandidateReadinessFilter("all");
    setCandidateSort("best_match");
    setCandidateStationSearch("");
    markCandidateSearchSettingsChanged("Search intent changed; search selected soundings");
  }

  function handleStationSelectionModeChange(mode: StationSelectionMode) {
    setStationSelectionMode(mode);
    markCandidateSearchSettingsChanged("Station set changed; search selected soundings");
  }

  function handleSelectedStationToggle(stationId: string) {
    setSelectedStationIds((current) =>
      current.includes(stationId)
        ? current.filter((selected) => selected !== stationId)
        : [...current, stationId],
    );
    setStationSelectionMode("selected");
    markCandidateSearchSettingsChanged("Station selection changed; search selected soundings");
  }

  function handleSelectAllCachedStations() {
    setSelectedStationIds([]);
    setStationSelectionMode("all_cached");
    markCandidateSearchSettingsChanged("All cached stations selected; search selected soundings");
  }

  function handleClearSelectedStations() {
    setSelectedStationIds([]);
    setStationSelectionMode("selected");
    markCandidateSearchSettingsChanged("Station selection cleared");
  }

  function handleCandidateHistoryScopeChange(scope: CandidateHistoryScope) {
    setCandidateHistoryScope(scope);
    markCandidateSearchSettingsChanged("History scope changed; search selected soundings");
  }

  function handleCandidateStoryFilterChange(filter: CandidateStoryFilter) {
    setCandidateStoryFilter(filter);
    markCandidateSearchSettingsChanged("Story filter changed; apply advanced filters");
  }

  function handleCandidateStoryFamilyFilterChange(filter: CandidateStoryFamilyFilter) {
    setCandidateStoryFamilyFilter(filter);
    markCandidateSearchSettingsChanged("Story family changed; apply advanced filters");
  }

  function handleCandidateSupportFilterChange(filter: CandidateSupportFilter) {
    setCandidateSupportFilter(filter);
    markCandidateSearchSettingsChanged("Support filter changed; apply advanced filters");
  }

  function handleCandidateSortChange(sort: CandidateSort) {
    setCandidateSort(sort);
    markCandidateSearchSettingsChanged("Sort changed; apply advanced filters");
  }

  function handleCandidateStationSearchChange(search: string) {
    setCandidateStationSearch(search);
    markCandidateSearchSettingsChanged("Station search changed; apply advanced filters");
  }

  function handleCandidateReadinessFilterChange(filter: CandidateReadinessFilter) {
    setCandidateReadinessFilter(filter);
    markCandidateSearchSettingsChanged("Readiness filter changed; apply advanced filters");
  }

  function handleCandidateLatestPerStationChange(limit: string) {
    setCandidateLatestPerStation(limit);
    markCandidateSearchSettingsChanged("History scope changed; search selected soundings");
  }

  function handleCandidateResultLimitChange(limit: string) {
    setCandidateResultLimit(limit);
    markCandidateSearchSettingsChanged("Returned candidate limit changed; apply advanced filters");
  }

  function selectedStationIdsForCandidateRequest(): string[] {
    return stationSelectionMode === "selected" ? selectedStationIds : [];
  }

  function selectedHistoryLatestPerStation(): number | null {
    return candidateHistoryScope === "latest_per_station"
      ? boundedInteger(candidateLatestPerStation, 1, 2000, 20)
      : null;
  }

  function candidateSearchStatus(
    action: "Searching" | "Analyzing",
    inputs: ScreeningInput[] = screeningInputs,
  ): string {
    const stationIds = selectedStationIdsForCandidateRequest();
    const selectedStationSet = new Set(stationIds);
    const selectedInputs =
      stationSelectionMode === "selected"
        ? inputs.filter((input) => selectedStationSet.has(input.station_id))
        : inputs;
    const latestPerStation = selectedHistoryLatestPerStation();
    const soundingCount =
      candidateHistoryScope === "all_cached"
        ? selectedInputs.reduce((total, input) => total + (input.sounding_count ?? 0), 0)
        : selectedInputs.reduce(
            (total, input) => total + Math.min(input.sounding_count ?? 0, latestPerStation ?? 0),
            0,
          );
    const stationCount = selectedInputs.length;
    if (soundingCount >= 1000) {
      return `${action} ${soundingCount.toLocaleString()} cached soundings from ${stationCount.toLocaleString()} station${stationCount === 1 ? "" : "s"}; this can take a minute or two`;
    }
    if (soundingCount > 0) {
      return `${action} ${soundingCount.toLocaleString()} selected sounding${soundingCount === 1 ? "" : "s"}`;
    }
    return `${action} selected soundings`;
  }

  async function refreshSoundingCandidateState(statusWhenLoaded?: string) {
    setCandidateError(null);
    setCandidateStatus("Checking local IGRA cache");
    try {
      const [catalogPayload, cachePayload, inputsPayload, savedPayload] = await Promise.all([
        fetchIGRARecentCatalog(),
        fetchIGRARecentCache(),
        fetchScreeningInputs(),
        fetchSavedSoundingCandidates(),
      ]);
      setIgraCatalog(catalogPayload.catalog);
      setIgraCache(cachePayload);
      setScreeningInputs(inputsPayload.inputs);
      setSavedCandidates(savedPayload.saved_candidates);
      setCandidateStatus(
        statusWhenLoaded ??
          (inputsPayload.inputs.length > 0
            ? "Cached soundings ready to screen"
            : "No cached sounding files ready to screen"),
      );
    } catch (caught) {
      setCandidateError(
        caught instanceof Error ? caught.message : "Unable to load sounding candidate state.",
      );
      setCandidateStatus("Sounding candidate state unavailable");
    }
  }

  async function handlePrepareAndSearchLocalSoundings() {
    const stationIds = selectedStationIdsForCandidateRequest();
    if (stationSelectionMode === "selected" && stationIds.length === 0) {
      setCandidateError("Select at least one station, or switch to all cached stations.");
      setCandidateStatus("Station selection required");
      return;
    }
    const resultLimit = boundedInteger(candidateResultLimit, 1, 500, 100);
    setCandidateError(null);
    setCandidateScreening(null);
    setCandidateDetailId(null);
    setCandidateStatus("Preparing selected soundings");
    try {
      const [catalogPayload, cachePayload, inputsPayload, savedPayload] = await Promise.all([
        fetchIGRARecentCatalog(),
        fetchIGRARecentCache(),
        fetchScreeningInputs(),
        fetchSavedSoundingCandidates(),
      ]);
      setIgraCatalog(catalogPayload.catalog);
      setIgraCache(cachePayload);
      setScreeningInputs(inputsPayload.inputs);
      setSavedCandidates(savedPayload.saved_candidates);
      setCandidateStatus(candidateSearchStatus("Searching", inputsPayload.inputs));
      const result = await screenSoundingCandidates({
        stationIds,
        historyScope: candidateHistoryScope,
        story: candidateStoryFilter,
        storyFamily: candidateStoryFamilyFilter,
        support: candidateSupportFilter,
        readiness: candidateReadinessFilter,
        stationSearch: candidateStationSearch,
        sort: candidateSort,
        latestPerStation: selectedHistoryLatestPerStation(),
        limit: resultLimit,
      });
      setCandidateScreening(result);
      setCandidateDetailId(result.candidates[0]?.candidate_id ?? null);
      setCandidateStatus(
        result.candidates.length > 0
          ? "Recommendation run complete"
          : "Recommendation run found no matching candidates",
      );
    } catch (caught) {
      setCandidateError(
        caught instanceof Error ? caught.message : "Unable to search selected soundings.",
      );
      setCandidateStatus("Selected sounding search failed");
    }
  }

  async function handleRefreshIGRAData() {
    setCandidateError(null);
    setCandidateStatus("Refreshing IGRA station catalog");
    try {
      const catalog = await refreshIGRARecentCatalog();
      setIgraCatalog(catalog);
      await refreshSoundingCandidateState("IGRA station catalog refreshed");
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to refresh IGRA station catalog.";
      setCandidateError(message);
      setCandidateStatus(`IGRA catalog refresh blocked: ${message}`);
    }
  }

  async function handleCacheIGRAStationFiles() {
    const stationIds = selectedStationIdsForCandidateRequest();
    if (stationIds.length === 0) {
      setCandidateError("Select one or more catalog stations to cache.");
      setCandidateStatus("Station selection required");
      return;
    }
    setCandidateError(null);
    setCandidateStatus(
      `Caching ${stationIds.length} selected station${stationIds.length === 1 ? "" : "s"}`,
    );
    try {
      const result = await cacheIGRARecentBatch({ stationIds });
      await refreshSoundingCandidateState(
        result.cached_entries.length > 0
          ? `Cached ${result.cached_entries.length} station file${
              result.cached_entries.length === 1 ? "" : "s"
            }`
          : result.failed.length > 0
            ? "Station-file caching had errors"
            : "No uncached station files found",
      );
      if (result.failed.length > 0) {
        setCandidateError(
          `${result.failed.length} station file${result.failed.length === 1 ? "" : "s"} could not be cached. Check the IGRA cache details or try a smaller batch.`,
        );
      }
    } catch (caught) {
      setCandidateError(
        caught instanceof Error ? caught.message : "Unable to cache IGRA station files.",
      );
      setCandidateStatus("Station-file caching blocked");
    }
  }

  async function handleScreenSoundingCandidates() {
    const stationIds = selectedStationIdsForCandidateRequest();
    if (stationSelectionMode === "selected" && stationIds.length === 0) {
      setCandidateError("Select at least one station, or switch to all cached stations.");
      setCandidateStatus("Station selection required");
      return;
    }
    setCandidateError(null);
    setCandidateScreening(null);
    setCandidateDetailId(null);
    setCandidateStatus(candidateSearchStatus("Analyzing"));
    try {
      const result = await screenSoundingCandidates({
        stationIds,
        historyScope: candidateHistoryScope,
        story: candidateStoryFilter,
        storyFamily: candidateStoryFamilyFilter,
        support: candidateSupportFilter,
        readiness: candidateReadinessFilter,
        stationSearch: candidateStationSearch,
        sort: candidateSort,
        latestPerStation: selectedHistoryLatestPerStation(),
        limit: boundedInteger(candidateResultLimit, 1, 500, 100),
      });
      setCandidateScreening(result);
      setCandidateDetailId(result.candidates[0]?.candidate_id ?? null);
      setCandidateStatus(
        result.candidates.length > 0
          ? "Cached sounding analysis loaded"
          : "No candidates found in cached soundings",
      );
      const savedPayload = await fetchSavedSoundingCandidates();
      setSavedCandidates(savedPayload.saved_candidates);
    } catch (caught) {
      setCandidateError(
        caught instanceof Error ? caught.message : "Unable to search selected soundings.",
      );
      setCandidateStatus("Candidate search failed");
    }
  }

  function handleClearCandidateAnalysisFilters() {
    setCandidateStoryFilter("all");
    setCandidateStoryFamilyFilter("all");
    setCandidateSupportFilter("all");
    setCandidateStationSearch("");
    setCandidateReadinessFilter("all");
    setCandidateSort("best_match");
    markCandidateSearchSettingsChanged(
      "Showing default recommendation settings; search selected soundings",
    );
  }

  async function handleSaveSoundingCandidate(
    candidate: SoundingCandidate,
    tags: string[] = [],
    notes: string | null = null,
  ) {
    setCandidateError(null);
    const existing = savedCandidates.find(
      (saved) => saved.candidate.candidate_id === candidate.candidate_id,
    );
    setCandidateStatus(
      existing ? "Updating saved sounding candidate" : "Saving sounding candidate",
    );
    try {
      if (existing) {
        const saved = await updateSavedSoundingCandidate(existing.saved_candidate_id, tags, notes);
        setSavedCandidates((current) =>
          current.map((item) =>
            item.saved_candidate_id === saved.saved_candidate_id ? saved : item,
          ),
        );
        setCandidateStatus("Saved sounding candidate updated");
      } else {
        const saved = await saveSoundingCandidate(candidate, tags, notes);
        setSavedCandidates((current) => [
          saved,
          ...current.filter((item) => item.saved_candidate_id !== saved.saved_candidate_id),
        ]);
        setCandidateStatus("Sounding candidate saved");
      }
    } catch (caught) {
      setCandidateError(
        caught instanceof Error ? caught.message : "Unable to save sounding candidate.",
      );
      setCandidateStatus("Save candidate failed");
    }
  }

  async function handleRemoveSavedSoundingCandidate(savedCandidateId: string) {
    setCandidateError(null);
    setCandidateStatus("Removing saved sounding candidate");
    try {
      await deleteSavedSoundingCandidate(savedCandidateId);
      setSavedCandidates((current) =>
        current.filter((item) => item.saved_candidate_id !== savedCandidateId),
      );
      setCandidateStatus("Saved sounding candidate removed");
    } catch (caught) {
      setCandidateError(
        caught instanceof Error ? caught.message : "Unable to remove saved candidate.",
      );
      setCandidateStatus("Remove candidate failed");
    }
  }

  function handleUseSoundingCandidate(
    candidate: SoundingCandidate,
    savedCandidate?: SavedSoundingCandidate,
    activeStory?: CandidateStoryId,
  ) {
    if (!candidate.package_ready || !candidate.selected_sounding_payload) {
      setCandidateError(
        "This candidate is not package-ready. Review its caveats before trying another sounding.",
      );
      return;
    }
    const selectedSounding = candidate.selected_sounding_payload;
    const candidateScreening = candidateScreeningMetadata(candidate, savedCandidate, activeStory);
    setSelectedScenarioId(OBSERVED_SOUNDING_EXPERIMENT_ID);
    setObservedSoundingFilename(candidate.source_file_name);
    setObservedSoundingText(null);
    setObservedSoundingParse(observedSoundingParseFromCandidate(candidate, selectedSounding));
    setObservedSoundingStatus("Candidate loaded from recommendation");
    setObservedSoundingError(null);
    setSelectedCandidateScreening(candidateScreening);
    setRunConfiguration(defaultRunConfigurationForCandidateScreening(candidateScreening));
    setDryRun(null);
    setBlockedPreRunValidationReport(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setLanWorkerStatus(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus(null);
    setIngestedResultId(null);
    setCandidateStatus("Candidate selected for run setup");
  }

  function handleSelectCandidateForRunSetup(
    candidate: SoundingCandidate,
    savedCandidate?: SavedSoundingCandidate,
    activeStory?: CandidateStoryId,
  ) {
    if (!candidate.package_ready || !candidate.selected_sounding_payload) {
      setCandidateError(
        "This candidate is not package-ready. Review its caveats before selecting it for setup.",
      );
      return;
    }
    handleUseSoundingCandidate(candidate, savedCandidate, activeStory);
    setBatchQueueStatus(`${candidateStationLabel(candidate)} selected for run setup`);
  }

  function handleAddSelectedSoundingToRunPlan() {
    if (!observedSoundingParse?.selected_sounding) {
      setObservedSoundingError("Upload and validate an IGRA sounding before adding it.");
      return;
    }
    const item = runPlanItemFromUploadedSounding({
      observedSounding: observedSoundingParse.selected_sounding,
      source: runPlanSourceFromCandidateScreening(selectedCandidateScreening),
      runConfiguration,
      controls,
      selectedCandidateScreening,
    });
    setRunPlanItems((current) => [...current, item]);
    const selected = observedSoundingParse.selected_sounding;
    const label = selectedObservedSoundingStationLabel(selected, selectedCandidateScreening);
    setBatchQueueStatus(`${label} added to the run plan`);
  }

  function handleDuplicateRunPlanItem(itemId: string) {
    setRunPlanItems((current) => {
      const item = current.find((entry) => entry.id === itemId);
      if (!item) return current;
      return [
        ...current,
        {
          ...item,
          id: createRunPlanItemId(),
          selected: true,
          status: "planned",
          message: "Variant duplicated; edit recipe or configuration before queueing.",
          dryRun: null,
          blockedPreRunValidationReport: null,
        },
      ];
    });
    setBatchQueueStatus("Run-plan variant duplicated");
  }

  function handleRemoveRunPlanItem(itemId: string) {
    setRunPlanItems((current) => current.filter((item) => item.id !== itemId));
  }

  function handleClearSelectedRunPlanItems() {
    setRunPlanItems((current) => current.filter((item) => !item.selected));
    setBatchQueueStatus("Selected run-plan items removed");
  }

  function handleClearRunPlan() {
    setRunPlanItems([]);
    setBatchQueueStatus("Run plan cleared");
  }

  function handleRunPlanItemSelectedChange(itemId: string, selected: boolean) {
    updateRunPlanItem(itemId, (item) => ({ ...item, selected }));
  }

  function handleRunPlanItemQueueTargetChange(itemId: string, queueTarget: RunPlanQueueTarget) {
    updateRunPlanItem(itemId, (item) => ({
      ...item,
      queueTarget,
      status: "planned",
      message: null,
    }));
  }

  function handleRunPlanItemConfigurationChange(
    itemId: string,
    runConfiguration: RunConfigurationInput,
  ) {
    updateRunPlanItem(itemId, (item) => ({
      ...item,
      runConfiguration,
      runRecipe: observedRecipeForSelection(item.candidateScreening, runConfiguration),
      status: "planned",
      message: "Run configuration changed; package not created yet.",
      dryRun: null,
      blockedPreRunValidationReport: null,
    }));
  }

  function updateRunPlanItem(itemId: string, update: (item: RunPlanItem) => RunPlanItem) {
    setRunPlanItems((current) => current.map((item) => (item.id === itemId ? update(item) : item)));
  }

  async function handleCreateAndQueueRunPlan() {
    const selectedItems = runPlanItems.filter((item) => item.selected);
    if (selectedItems.length === 0) {
      setBatchQueueStatus("Select at least one run-plan item before queueing.");
      return;
    }
    setBatchQueueStatus(
      `Creating and queueing ${selectedItems.length} selected run${selectedItems.length === 1 ? "" : "s"}`,
    );
    setRunWorkflowError(null);
    let queued = 0;
    let lanStarted = 0;
    let failed = 0;
    let skipped = 0;

    for (const item of selectedItems) {
      if (!item.observedSounding) {
        skipped += 1;
        updateRunPlanItem(item.id, (current) => ({
          ...current,
          status: "skipped",
          message: "Skipped because the selected sounding data is missing.",
        }));
        continue;
      }
      if (item.queueTarget === "lan" && !lanWorkerConfig?.configured) {
        skipped += 1;
        updateRunPlanItem(item.id, (current) => ({
          ...current,
          status: "skipped",
          message: "Skipped because LAN worker execution is not configured.",
        }));
        continue;
      }

      updateRunPlanItem(item.id, (current) => ({
        ...current,
        status: "packaging",
        message: "Creating package",
        dryRun: null,
        blockedPreRunValidationReport: null,
      }));

      try {
        const packageUserMetadata = runUserMetadataFromCandidateScreening(item.candidateScreening);
        const result = await requestDryRunPackage(
          OBSERVED_SOUNDING_BASE_SCENARIO_ID,
          item.controls,
          item.runConfiguration,
          item.runRecipe,
          item.observedSounding,
          item.candidateScreening,
          packageUserMetadata,
        );
        setDryRun(result);
        setBlockedPreRunValidationReport(null);

        if (item.queueTarget === "lan") {
          const launched = await startLanWorkerRun(result.manifest_path);
          setLanWorkerStatus(launched);
          setLanWorkerActionStatus(lanWorkerStatusLabel(launched));
          lanStarted += 1;
          updateRunPlanItem(item.id, (current) => ({
            ...current,
            status: "lan_started",
            message: launched.message ?? "Package sent to LAN worker.",
            dryRun: result,
            blockedPreRunValidationReport: null,
          }));
        } else {
          const queuedResponse = await enqueueLocalRun(result.manifest_path);
          setRunQueue(queuedResponse);
          setRunQueueStatus(runQueueSummary(queuedResponse));
          await processAutoIngestedQueue(queuedResponse);
          queued += 1;
          updateRunPlanItem(item.id, (current) => ({
            ...current,
            status: "queued",
            message: "Queued for local serial CM1 run.",
            dryRun: result,
            blockedPreRunValidationReport: null,
          }));
        }
      } catch (caught) {
        failed += 1;
        const blockedReport =
          caught instanceof DryRunRequestError ? caught.preRunValidationReport : null;
        if (blockedReport) setBlockedPreRunValidationReport(blockedReport);
        updateRunPlanItem(item.id, (current) => ({
          ...current,
          status: "package_failed",
          message: caught instanceof Error ? caught.message : "Unable to create or queue package.",
          blockedPreRunValidationReport: blockedReport,
        }));
      }
    }

    await refreshLocalRunQueue();
    await refreshStorageAfterWorkflow("Local pipeline updated");
    setBatchQueueStatus(
      batchQueueSummary({
        queued,
        lanStarted,
        failed,
        skipped,
      }),
    );
  }

  async function handleDryRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedScenario || validationMessages.length > 0) return;
    if (observedSoundingExperimentSelected && !observedSoundingParse?.selected_sounding) {
      setObservedSoundingError("Upload and validate an IGRA sounding before creating a package.");
      return;
    }
    setStatus("Creating dry-run package");
    setError(null);
    setDryRun(null);
    setBlockedPreRunValidationReport(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setLanWorkerStatus(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus(null);
    setIngestedResultId(null);
    const packageUserMetadata = observedSoundingExperimentSelected
      ? runUserMetadataFromCandidateScreening(selectedCandidateScreening)
      : null;
    try {
      const result = await requestDryRunPackage(
        selectedScenario.id,
        controls,
        runConfiguration,
        observedSoundingExperimentSelected
          ? observedRecipeForSelection(selectedCandidateScreening, runConfiguration)
          : null,
        observedSoundingExperimentSelected ? observedSoundingParse?.selected_sounding : null,
        observedSoundingExperimentSelected ? selectedCandidateScreening : null,
        packageUserMetadata,
      );
      setDryRun(result);
      setBlockedPreRunValidationReport(null);
      setStatus("Packaged dry-run output");
      await refreshStorageAfterWorkflow("Package added to local pipeline");
    } catch (caught) {
      if (caught instanceof DryRunRequestError) {
        setBlockedPreRunValidationReport(caught.preRunValidationReport);
      }
      setError(caught instanceof Error ? caught.message : "Unable to create dry-run package.");
      setStatus("Scenario setup");
    }
  }

  async function handleObservedSoundingFile(file: File) {
    setObservedSoundingFilename(file.name);
    setObservedSoundingStatus("Reading observed sounding file...");
    setObservedSoundingError(null);
    setObservedSoundingParse(null);
    setSelectedCandidateScreening(null);
    setRunConfiguration(defaultRunConfigurationForSelection(OBSERVED_SOUNDING_EXPERIMENT_ID));
    setDryRun(null);
    setBlockedPreRunValidationReport(null);
    setRunStatus(null);
    setLanWorkerStatus(null);
    try {
      const text = await readUploadedTextFile(file);
      setObservedSoundingText(text);
      setObservedSoundingStatus("Parsing observed sounding...");
      const parsed = await parseObservedSoundingUpload(file.name, text);
      setObservedSoundingParse(parsed);
      setSelectedCandidateScreening(null);
      setRunConfiguration(defaultRunConfigurationForSelection(OBSERVED_SOUNDING_EXPERIMENT_ID));
      setObservedSoundingStatus("Observed sounding validated for package review");
    } catch (caught) {
      setObservedSoundingText(null);
      setObservedSoundingError(
        caught instanceof Error ? caught.message : "Unable to parse observed sounding.",
      );
      setObservedSoundingStatus("Observed sounding blocked");
    }
  }

  async function handleObservedSoundingTimeChange(validTimeUtc: string) {
    if (!observedSoundingFilename || observedSoundingText === null) return;
    setObservedSoundingStatus("Validating selected sounding time...");
    setObservedSoundingError(null);
    setDryRun(null);
    setRunStatus(null);
    setLanWorkerStatus(null);
    try {
      const parsed = await parseObservedSoundingUpload(
        observedSoundingFilename,
        observedSoundingText,
        validTimeUtc,
      );
      setObservedSoundingParse(parsed);
      setSelectedCandidateScreening(null);
      setRunConfiguration(defaultRunConfigurationForSelection(OBSERVED_SOUNDING_EXPERIMENT_ID));
      setObservedSoundingStatus("Observed sounding validated for package review");
    } catch (caught) {
      setObservedSoundingError(
        caught instanceof Error ? caught.message : "Unable to validate selected sounding.",
      );
      setObservedSoundingStatus("Observed sounding blocked");
    }
  }

  async function handleLaunchRun() {
    if (!dryRun) return;
    setRunWorkflowError(null);
    setStatus("Queueing local CM1 run");
    try {
      const queued = await enqueueLocalRun(dryRun.manifest_path);
      setRunQueue(queued);
      setRunQueueStatus(runQueueSummary(queued));
      setStatus(runQueueSummary(queued));
      await syncCurrentRunStatusFromQueue(queued);
      await processAutoIngestedQueue(queued);
      await refreshStorageAfterWorkflow("Local pipeline updated");
    } catch (caught) {
      setRunWorkflowError(caught instanceof Error ? caught.message : "Unable to queue local CM1.");
      setStatus("Queue blocked");
    }
  }

  async function handleRefreshRunStatus() {
    if (!dryRun) return;
    setRunWorkflowError(null);
    try {
      const refreshed = await fetchRunStatus(dryRun.manifest_path);
      setRunStatus(refreshed);
      setStatus(userFacingRunWorkflowStatus(refreshed));
      await refreshLocalRunQueue();
      await refreshStorageAfterWorkflow("Local pipeline updated");
    } catch (caught) {
      setRunWorkflowError(
        caught instanceof Error ? caught.message : "Unable to refresh local CM1 status.",
      );
    }
  }

  async function handleLaunchLanWorkerRun(manifestPath?: string) {
    const targetManifestPath = manifestPath ?? dryRun?.manifest_path;
    if (!targetManifestPath) return;
    setRunWorkflowError(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus("Copying package to LAN worker");
    setStatus("Copying package to LAN worker");
    try {
      const launched = await startLanWorkerRun(targetManifestPath);
      setLanWorkerStatus(launched);
      setLanWorkerActionStatus("Running CM1 on LAN worker");
      setStatus("Running CM1 on LAN worker");
      await refreshStorageAfterWorkflow("Local pipeline updated");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unable to start LAN worker run.";
      setLanWorkerError(message);
      setRunWorkflowError(message);
      setLanWorkerActionStatus("LAN worker launch blocked");
      setStatus("LAN worker launch blocked");
    }
  }

  async function handleRefreshLanWorkerStatus() {
    if (!dryRun) return;
    setLanWorkerError(null);
    setLanWorkerActionStatus("Refreshing LAN worker status");
    try {
      const refreshed = await fetchLanWorkerStatus(dryRun.manifest_path);
      setLanWorkerStatus(refreshed);
      setLanWorkerActionStatus(lanWorkerStatusLabel(refreshed));
      await refreshStorageAfterWorkflow("Local pipeline updated");
      if (refreshed.state === "completed" && !ingestedResultId) {
        await collectAndIngestLanWorkerRun(dryRun.manifest_path);
      }
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to refresh LAN worker status.";
      setLanWorkerError(message);
      setLanWorkerActionStatus("LAN worker status unavailable");
    }
  }

  async function handleCollectLanWorkerRun() {
    if (!dryRun) return;
    await collectAndIngestLanWorkerRun(dryRun.manifest_path);
  }

  async function collectAndIngestLanWorkerRun(manifestPath: string): Promise<boolean> {
    setLanWorkerError(null);
    setLanWorkerActionStatus("Copying completed output back");
    setStatus("Copying completed output back");
    try {
      const collected = await collectLanWorkerRun(manifestPath);
      setLanWorkerStatus(collected);
      setLanWorkerActionStatus(lanWorkerStatusLabel(collected));
      await refreshStorageAfterWorkflow("Completed LAN worker output returned");
      if (collected.ready_for_ingest || collected.state === "ready_for_local_ingest") {
        setLanWorkerActionStatus("Ingesting copied LAN worker output");
        setStatus("Ingesting copied LAN worker output");
        const ingested = await ingestCompletedRun(manifestPath);
        setIngestedResultId(ingested.result_id);
        await refreshResults(ingested.result_id);
        await refreshStorageAfterWorkflow("LAN worker output ingested locally");
        setLanWorkerActionStatus("Cleaning LAN worker copy");
        setStatus("Cleaning LAN worker copy");
        try {
          const cleaned = await cleanupLanWorkerRun(manifestPath);
          setLanWorkerStatus(cleaned);
          setLanWorkerActionStatus(lanWorkerStatusLabel(cleaned));
          await refreshStorageAfterWorkflow("LAN worker cleanup complete");
          setStatus("Ingested result metadata and cleaned worker copy");
        } catch (cleanupError) {
          const cleanupMessage =
            cleanupError instanceof Error
              ? cleanupError.message
              : "Unable to clean up LAN worker copy.";
          setLanWorkerError(cleanupMessage);
          setLanWorkerActionStatus("LAN worker cleanup failed");
          setStatus("Ingested result metadata; worker cleanup needs retry");
        }
        return true;
      } else {
        setStatus("Copied output needs review before ingest");
        return false;
      }
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to copy and ingest LAN worker output.";
      setLanWorkerError(message);
      setLanWorkerActionStatus("LAN worker copy-back or ingest failed");
      setStatus("LAN worker copy-back or ingest failed");
      return false;
    }
  }

  async function handleCleanupLanWorkerRun() {
    if (!dryRun) return;
    setLanWorkerError(null);
    setLanWorkerActionStatus("Cleaning LAN worker copy");
    try {
      const cleaned = await cleanupLanWorkerRun(dryRun.manifest_path);
      setLanWorkerStatus(cleaned);
      setLanWorkerActionStatus(lanWorkerStatusLabel(cleaned));
      await refreshStorageAfterWorkflow("LAN worker cleanup complete");
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to clean up LAN worker copy.";
      setLanWorkerError(message);
      setLanWorkerStatus((current) =>
        current
          ? {
              ...current,
              state: "worker_cleanup_failed",
              message,
            }
          : current,
      );
      setLanWorkerActionStatus("LAN worker cleanup failed");
    }
  }

  async function refreshResults(selectResultId?: string) {
    const payload = await fetchResults();
    const prioritized = prioritizeResults(payload.results);
    setResults(prioritized);
    setSelectedResultId((current) => {
      if (selectResultId) return selectResultId;
      if (current && prioritized.some((result) => result.result_id === current)) return current;
      return prioritized[0]?.result_id ?? null;
    });
    setResultsStatus(payload.results.length > 0 ? "Results loaded" : "No ingested results");
    return prioritized;
  }

  async function handleRefreshResults() {
    setResultsError(null);
    setResultsStatus("Refreshing results");
    try {
      await refreshResults();
    } catch (caught) {
      setResults([]);
      setSelectedResultId(null);
      setResultsError(caught instanceof Error ? caught.message : "Could not load results.");
      setResultsStatus("Results unavailable");
    }
  }

  async function handleIngestRun() {
    if (!dryRun) return;
    setRunWorkflowError(null);
    setStatus("Ingesting completed CM1 output");
    try {
      const ingested = await ingestCompletedRun(dryRun.manifest_path);
      setIngestedResultId(ingested.result_id);
      await refreshResults(ingested.result_id);
      await refreshStorageAfterWorkflow("Local pipeline updated");
      if (lanWorkerStatus && lanWorkerStatus.state !== "worker_cleanup_complete") {
        setLanWorkerActionStatus("Worker cleanup pending");
      }
      setStatus("Ingested result metadata");
    } catch (caught) {
      setRunWorkflowError(
        caught instanceof Error ? caught.message : "Unable to ingest completed CM1 output.",
      );
      setStatus("Ingest blocked");
    }
  }

  async function handleLaunchStoredRun(manifestPath: string) {
    setRunWorkflowError(null);
    setStatus("Queueing selected local package");
    try {
      const queued = await enqueueLocalRun(manifestPath);
      setRunQueue(queued);
      setRunQueueStatus(runQueueSummary(queued));
      setStatus(runQueueSummary(queued));
      await syncCurrentRunStatusFromQueue(queued);
      await processAutoIngestedQueue(queued);
      await refreshStorageAfterWorkflow("Local pipeline updated");
    } catch (caught) {
      setRunWorkflowError(caught instanceof Error ? caught.message : "Unable to queue local CM1.");
      setStatus("Queue blocked");
    }
  }

  async function handleFinalizeStoredLanWorkerRun(manifestPath: string) {
    await collectAndIngestLanWorkerRun(manifestPath);
  }

  async function autoFinalizeStoredLanWorkerRun(manifestPath: string, runId: string) {
    setAutoFinalizingWorkerRunIds((current) =>
      current.includes(runId) ? current : [...current, runId],
    );
    setFailedAutoFinalizingWorkerRunIds((current) => current.filter((id) => id !== runId));
    const succeeded = await collectAndIngestLanWorkerRun(manifestPath);
    setAutoFinalizingWorkerRunIds((current) => current.filter((id) => id !== runId));
    if (!succeeded) {
      setFailedAutoFinalizingWorkerRunIds((current) =>
        current.includes(runId) ? current : [...current, runId],
      );
    }
  }

  async function handleRefreshStoredLanWorkerStatus(manifestPath: string) {
    setRunWorkflowError(null);
    setLanWorkerError(null);
    setLanWorkerActionStatus("Refreshing LAN worker status");
    setStatus("Refreshing LAN worker status");
    try {
      const refreshed = await fetchLanWorkerStatus(manifestPath);
      if (dryRun?.manifest_path === manifestPath) {
        setLanWorkerStatus(refreshed);
      }
      setLanWorkerActionStatus(lanWorkerStatusLabel(refreshed));
      await refreshStorageAfterWorkflow(
        `LAN worker status refreshed at ${new Date().toLocaleTimeString()}`,
      );
      if (refreshed.state === "completed") {
        await collectAndIngestLanWorkerRun(manifestPath);
      }
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to refresh LAN worker status.";
      setLanWorkerError(message);
      setRunWorkflowError(message);
      setLanWorkerActionStatus("LAN worker status unavailable");
      setStatus("LAN worker status unavailable");
    }
  }

  async function handleIngestStoredRun(manifestPath: string) {
    setRunWorkflowError(null);
    setStorageError(null);
    setStorageStatus("Ingesting completed output");
    setStatus("Ingesting selected completed output");
    try {
      const ingested = await ingestCompletedRun(manifestPath);
      setIngestedResultId(ingested.result_id);
      await refreshResults(ingested.result_id);
      await refreshStorageAfterWorkflow("Local pipeline updated");
      setStatus("Ingested result metadata");
      setStorageStatus("Ingested result metadata");
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to ingest completed CM1 output.";
      setRunWorkflowError(message);
      setStorageError(message);
      setStatus("Ingest blocked");
      setStorageStatus("Ingest blocked");
    }
  }

  function updateResultInList(updated: ResultCard) {
    setResults((current) =>
      prioritizeResults(
        current.map((result) => (result.result_id === updated.result_id ? updated : result)),
      ),
    );
    setSelectedResultId(updated.result_id);
  }

  async function handleResultUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedResult) return;
    setResultsError(null);
    setResultsStatus("Saving notebook changes");
    try {
      const updated = await patchResultCard(selectedResult.result_id, {
        name: resultDraft.name,
        tags: parseTags(resultDraft.tags),
        notes: resultDraft.notes,
      });
      updateResultInList(updated);
      setResultsStatus("Notebook changes saved");
    } catch (caught) {
      setResultsError(
        caught instanceof Error ? caught.message : "Unable to save notebook changes.",
      );
      setResultsStatus("Results loaded");
    }
  }

  async function handleRefreshStorage() {
    setStorageError(null);
    setStorageStatus("Refreshing run inventory");
    setRunDeletePreview(null);
    setRunDeleteMessage(null);
    try {
      const payload = await fetchStorageInventory();
      setStorageInventory(payload);
      setStorageStatus(payload.runs.length > 0 ? "Run inventory loaded" : "No runtime runs");
    } catch (caught) {
      setStorageError(
        caught instanceof Error ? caught.message : "Unable to load runtime run inventory.",
      );
      setStorageStatus("Run inventory unavailable");
    }
  }

  async function handlePreviewRunDelete(runId: string) {
    setStorageError(null);
    setRunDeleteMessage(null);
    setStorageStatus("Preparing delete preview");
    try {
      const preview = await requestRunDeletePreview(runId);
      setRunDeletePreview(preview);
      setStorageStatus("Delete preview ready");
    } catch (caught) {
      setStorageError(caught instanceof Error ? caught.message : "Unable to preview run deletion.");
      setStorageStatus("Run inventory loaded");
    }
  }

  async function handleConfirmRunDelete(runId: string) {
    setStorageError(null);
    setStorageStatus("Deleting selected run");
    try {
      const deleted = await confirmRunDelete(runId);
      setRunDeleteMessage(`${deleted.message} Reclaimed ${formatBytes(deleted.size_bytes)}.`);
      setRunDeletePreview(null);
      const payload = await fetchStorageInventory();
      setStorageInventory(payload);
      setStorageStatus("Run deleted");
    } catch (caught) {
      setStorageError(caught instanceof Error ? caught.message : "Unable to delete selected run.");
      setStorageStatus("Delete failed");
    }
  }

  async function handlePreviewResultDelete(resultId: string) {
    setResultsError(null);
    setResultsStatus("Preparing result delete preview");
    try {
      const preview = await requestResultDeletePreview(resultId);
      if (selectedResultIdRef.current !== resultId) return;
      setResultDeletePreview(preview);
      setResultsStatus("Result delete preview ready");
    } catch (caught) {
      setResultsError(
        caught instanceof Error ? caught.message : "Unable to preview result deletion.",
      );
      setResultsStatus("Results loaded");
    }
  }

  async function handleConfirmResultDelete(resultId: string) {
    if (resultDeletePreview?.result_id !== resultId) {
      setResultDeletePreview(null);
      setResultsError("Delete preview is stale. Preview deletion again before confirming.");
      setResultsStatus("Delete preview expired");
      return;
    }
    setResultsError(null);
    setResultsStatus("Deleting selected result");
    try {
      const deleted = await confirmResultDelete(resultId);
      const remaining = results.filter((result) => result.result_id !== resultId);
      const deleteMessage = `${deleted.message} Reclaimed ${formatBytes(
        deleted.size_bytes,
      )} from local storage.`;
      setResults(remaining);
      setSelectedResultId((current) =>
        current === resultId ? (remaining[0]?.result_id ?? null) : current,
      );
      setResultDeletePreview(null);
      setResultsStatus(deleteMessage);
      await refreshStorageAfterWorkflow("Local pipeline updated");
    } catch (caught) {
      setResultsError(
        caught instanceof Error ? caught.message : "Unable to delete selected result.",
      );
      setResultsStatus("Delete failed");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark">
          <p className="eyebrow">Local CM1 experiment lab</p>
          <h1>Cloud Chamber</h1>
        </div>

        <nav className="workspace-nav" aria-label="Cloud Chamber workspace">
          {(["build", "results", "explore"] as WorkspaceSection[]).map((section) => (
            <button
              key={section}
              type="button"
              className={activeSection === section ? "active-control" : ""}
              onClick={() => setActiveSection(section)}
            >
              {sectionLabel(section)}
            </button>
          ))}
        </nav>
      </header>

      {activeSection === "build" && (
        <BuildWorkspace
          scenarioLoadState={scenarioLoadState}
          scenarioError={scenarioError}
          packageError={error}
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          selectedScenarioId={selectedScenarioId}
          observedSoundingExperimentSelected={observedSoundingExperimentSelected}
          controls={controls}
          runConfiguration={runConfiguration}
          observedSoundingParse={observedSoundingParse}
          observedSoundingStatus={observedSoundingStatus}
          observedSoundingError={observedSoundingError}
          selectedCandidateScreening={selectedCandidateScreening}
          atmosphereSourcePath={atmosphereSourcePath}
          searchIntent={searchIntent}
          stationSelectionMode={stationSelectionMode}
          selectedStationIds={selectedStationIds}
          candidateHistoryScope={candidateHistoryScope}
          igraCatalog={igraCatalog}
          igraCache={igraCache}
          screeningInputs={screeningInputs}
          candidateStoryFilter={candidateStoryFilter}
          candidateStoryFamilyFilter={candidateStoryFamilyFilter}
          candidateSupportFilter={candidateSupportFilter}
          candidateSort={candidateSort}
          candidateStationSearch={candidateStationSearch}
          candidateReadinessFilter={candidateReadinessFilter}
          candidateLatestPerStation={candidateLatestPerStation}
          candidateResultLimit={candidateResultLimit}
          candidateStatus={candidateStatus}
          candidateError={candidateError}
          candidateScreening={candidateScreening}
          savedCandidates={savedCandidates}
          candidateDetailId={candidateDetailId}
          runPlanItems={runPlanItems}
          batchQueueStatus={batchQueueStatus}
          validationMessages={validationMessages}
          dryRun={dryRun}
          blockedPreRunValidationReport={blockedPreRunValidationReport}
          runStatus={runStatus}
          runQueue={runQueue}
          runQueueStatus={runQueueStatus}
          runWorkflowError={runWorkflowError}
          lanWorkerConfig={lanWorkerConfig}
          lanWorkerStatus={lanWorkerStatus}
          lanWorkerError={lanWorkerError}
          lanWorkerActionStatus={lanWorkerActionStatus}
          ingestedResultId={ingestedResultId}
          storageInventory={storageInventory}
          storageStatus={storageStatus}
          storageError={storageError}
          runDeletePreview={runDeletePreview}
          runDeleteMessage={runDeleteMessage}
          results={results}
          autoFinalizingWorkerRunIds={autoFinalizingWorkerRunIdSet}
          failedAutoFinalizingWorkerRunIds={failedAutoFinalizingWorkerRunIdSet}
          onSelectScenario={handleSelectScenario}
          onControlChange={(id, value) =>
            setControls((current) => ({
              ...current,
              [id]: value,
            }))
          }
          onRunConfigurationChange={setRunConfiguration}
          onObservedSoundingFile={handleObservedSoundingFile}
          onObservedSoundingTimeChange={handleObservedSoundingTimeChange}
          onAtmosphereSourcePathChange={handleAtmosphereSourcePathChange}
          onSearchIntentChange={handleSearchIntentChange}
          onStationSelectionModeChange={handleStationSelectionModeChange}
          onSelectedStationToggle={handleSelectedStationToggle}
          onSelectAllCachedStations={handleSelectAllCachedStations}
          onClearSelectedStations={handleClearSelectedStations}
          onCandidateHistoryScopeChange={handleCandidateHistoryScopeChange}
          onCandidateStoryFilterChange={handleCandidateStoryFilterChange}
          onCandidateStoryFamilyFilterChange={handleCandidateStoryFamilyFilterChange}
          onCandidateSupportFilterChange={handleCandidateSupportFilterChange}
          onCandidateSortChange={handleCandidateSortChange}
          onCandidateStationSearchChange={handleCandidateStationSearchChange}
          onCandidateReadinessFilterChange={handleCandidateReadinessFilterChange}
          onClearCandidateAnalysisFilters={handleClearCandidateAnalysisFilters}
          onCandidateLatestPerStationChange={handleCandidateLatestPerStationChange}
          onCandidateResultLimitChange={handleCandidateResultLimitChange}
          onCandidateDetailChange={setCandidateDetailId}
          onRefreshIGRAData={handleRefreshIGRAData}
          onCacheIGRAStationFiles={handleCacheIGRAStationFiles}
          onPrepareAndSearchLocalSoundings={handlePrepareAndSearchLocalSoundings}
          onScreenSoundingCandidates={handleScreenSoundingCandidates}
          onSaveSoundingCandidate={handleSaveSoundingCandidate}
          onRemoveSavedSoundingCandidate={handleRemoveSavedSoundingCandidate}
          onSelectCandidateForRunSetup={handleSelectCandidateForRunSetup}
          onAddSelectedSoundingToRunPlan={handleAddSelectedSoundingToRunPlan}
          onDuplicateRunPlanItem={handleDuplicateRunPlanItem}
          onRemoveRunPlanItem={handleRemoveRunPlanItem}
          onClearSelectedRunPlanItems={handleClearSelectedRunPlanItems}
          onClearRunPlan={handleClearRunPlan}
          onRunPlanItemSelectedChange={handleRunPlanItemSelectedChange}
          onRunPlanItemQueueTargetChange={handleRunPlanItemQueueTargetChange}
          onRunPlanItemConfigurationChange={handleRunPlanItemConfigurationChange}
          onCreateAndQueueRunPlan={handleCreateAndQueueRunPlan}
          onDryRun={handleDryRun}
          onLaunchRun={handleLaunchRun}
          onRefreshRunStatus={handleRefreshRunStatus}
          onLaunchLanWorkerRun={() => void handleLaunchLanWorkerRun()}
          onRefreshLanWorkerStatus={handleRefreshLanWorkerStatus}
          onCollectLanWorkerRun={handleCollectLanWorkerRun}
          onCleanupLanWorkerRun={handleCleanupLanWorkerRun}
          onIngestRun={handleIngestRun}
          onLaunchStoredRun={handleLaunchStoredRun}
          onLaunchStoredLanWorkerRun={(manifestPath) => void handleLaunchLanWorkerRun(manifestPath)}
          onRefreshStoredLanWorkerStatus={handleRefreshStoredLanWorkerStatus}
          onFinalizeStoredLanWorkerRun={handleFinalizeStoredLanWorkerRun}
          onIngestStoredRun={handleIngestStoredRun}
          onOpenInResults={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("results");
          }}
          onInspectIngested={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("explore");
          }}
          onOpenStoredResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("results");
          }}
          onExploreStoredResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
          }}
          onRefreshStorage={handleRefreshStorage}
          onPreviewRunDelete={handlePreviewRunDelete}
          onConfirmRunDelete={handleConfirmRunDelete}
          onRetryScenarios={() => {
            void loadScenarios();
          }}
        />
      )}

      {activeSection === "results" && (
        <ResultsWorkspace
          results={results}
          selectedResult={selectedResult}
          selectedResultId={selectedResultId}
          resultsStatus={resultsStatus}
          resultsError={resultsError}
          resultDeletePreview={resultDeletePreview}
          draft={resultDraft}
          onSelectResult={setSelectedResultId}
          onDraftChange={setResultDraft}
          onSubmit={handleResultUpdate}
          onRefreshResults={handleRefreshResults}
          onInspect={() => {
            setActiveSection("explore");
          }}
          onPreviewResultDelete={handlePreviewResultDelete}
          onConfirmResultDelete={handleConfirmResultDelete}
          onCancelResultDelete={() => {
            setResultDeletePreview(null);
            setResultsStatus("Results loaded");
          }}
        />
      )}

      {activeSection === "explore" && <ExploreWorkspace selectedResult={selectedResult} />}
    </main>
  );
}

function BuildWorkspace({
  scenarioLoadState,
  scenarioError,
  packageError,
  scenarios,
  selectedScenario,
  selectedScenarioId,
  observedSoundingExperimentSelected,
  controls,
  runConfiguration,
  observedSoundingParse,
  observedSoundingStatus,
  observedSoundingError,
  selectedCandidateScreening,
  atmosphereSourcePath,
  searchIntent,
  stationSelectionMode,
  selectedStationIds,
  candidateHistoryScope,
  igraCatalog,
  igraCache,
  screeningInputs,
  candidateStoryFilter,
  candidateStoryFamilyFilter,
  candidateSupportFilter,
  candidateSort,
  candidateStationSearch,
  candidateReadinessFilter,
  candidateLatestPerStation,
  candidateResultLimit,
  candidateStatus,
  candidateError,
  candidateScreening,
  savedCandidates,
  candidateDetailId,
  runPlanItems,
  batchQueueStatus,
  validationMessages,
  dryRun,
  blockedPreRunValidationReport,
  runStatus,
  runQueue,
  runQueueStatus,
  runWorkflowError,
  lanWorkerConfig,
  lanWorkerStatus,
  lanWorkerError,
  lanWorkerActionStatus,
  ingestedResultId,
  storageInventory,
  storageStatus,
  storageError,
  runDeletePreview,
  runDeleteMessage,
  results,
  autoFinalizingWorkerRunIds,
  failedAutoFinalizingWorkerRunIds,
  onSelectScenario,
  onControlChange,
  onRunConfigurationChange,
  onObservedSoundingFile,
  onObservedSoundingTimeChange,
  onAtmosphereSourcePathChange,
  onSearchIntentChange,
  onStationSelectionModeChange,
  onSelectedStationToggle,
  onSelectAllCachedStations,
  onClearSelectedStations,
  onCandidateHistoryScopeChange,
  onCandidateStoryFilterChange,
  onCandidateStoryFamilyFilterChange,
  onCandidateSupportFilterChange,
  onCandidateSortChange,
  onCandidateStationSearchChange,
  onCandidateReadinessFilterChange,
  onClearCandidateAnalysisFilters,
  onCandidateLatestPerStationChange,
  onCandidateResultLimitChange,
  onCandidateDetailChange,
  onRefreshIGRAData,
  onCacheIGRAStationFiles,
  onPrepareAndSearchLocalSoundings,
  onScreenSoundingCandidates,
  onSaveSoundingCandidate,
  onRemoveSavedSoundingCandidate,
  onSelectCandidateForRunSetup,
  onAddSelectedSoundingToRunPlan,
  onDuplicateRunPlanItem,
  onRemoveRunPlanItem,
  onClearSelectedRunPlanItems,
  onClearRunPlan,
  onRunPlanItemSelectedChange,
  onRunPlanItemQueueTargetChange,
  onRunPlanItemConfigurationChange,
  onCreateAndQueueRunPlan,
  onDryRun,
  onLaunchRun,
  onRefreshRunStatus,
  onLaunchLanWorkerRun,
  onRefreshLanWorkerStatus,
  onCollectLanWorkerRun,
  onCleanupLanWorkerRun,
  onIngestRun,
  onLaunchStoredRun,
  onLaunchStoredLanWorkerRun,
  onRefreshStoredLanWorkerStatus,
  onFinalizeStoredLanWorkerRun,
  onIngestStoredRun,
  onOpenInResults,
  onInspectIngested,
  onOpenStoredResult,
  onExploreStoredResult,
  onRefreshStorage,
  onPreviewRunDelete,
  onConfirmRunDelete,
  onRetryScenarios,
}: {
  scenarioLoadState: ScenarioLoadState;
  scenarioError: string | null;
  packageError: string | null;
  scenarios: Scenario[];
  selectedScenario: Scenario | undefined;
  selectedScenarioId: string;
  observedSoundingExperimentSelected: boolean;
  controls: Record<string, string | number | boolean>;
  runConfiguration: RunConfigurationInput;
  observedSoundingParse: ObservedSoundingParseResponse | null;
  observedSoundingStatus: string | null;
  observedSoundingError: string | null;
  selectedCandidateScreening: Record<string, unknown> | null;
  atmosphereSourcePath: AtmosphereSourcePath;
  searchIntent: SearchIntent;
  stationSelectionMode: StationSelectionMode;
  selectedStationIds: string[];
  candidateHistoryScope: CandidateHistoryScope;
  igraCatalog: IGRACatalogResponse["catalog"] | null;
  igraCache: IGRACacheResponse | null;
  screeningInputs: ScreeningInput[];
  candidateStoryFilter: CandidateStoryFilter;
  candidateStoryFamilyFilter: CandidateStoryFamilyFilter;
  candidateSupportFilter: CandidateSupportFilter;
  candidateSort: CandidateSort;
  candidateStationSearch: string;
  candidateReadinessFilter: CandidateReadinessFilter;
  candidateLatestPerStation: string;
  candidateResultLimit: string;
  candidateStatus: string;
  candidateError: string | null;
  candidateScreening: ScreeningResult | null;
  savedCandidates: SavedSoundingCandidate[];
  candidateDetailId: string | null;
  runPlanItems: RunPlanItem[];
  batchQueueStatus: string | null;
  validationMessages: string[];
  dryRun: DryRunResponse | null;
  blockedPreRunValidationReport: PreRunValidationReport | null;
  runStatus: RunStatusResponse | null;
  runQueue: RunQueueResponse | null;
  runQueueStatus: string;
  runWorkflowError: string | null;
  lanWorkerConfig: LanWorkerConfigResponse | null;
  lanWorkerStatus: LanWorkerRunResponse | null;
  lanWorkerError: string | null;
  lanWorkerActionStatus: string | null;
  ingestedResultId: string | null;
  storageInventory: StorageInventoryResponse | null;
  storageStatus: string;
  storageError: string | null;
  runDeletePreview: DeleteRunResponse | null;
  runDeleteMessage: string | null;
  results: ResultCard[];
  autoFinalizingWorkerRunIds: Set<string>;
  failedAutoFinalizingWorkerRunIds: Set<string>;
  onSelectScenario: (scenarioId: string) => void;
  onControlChange: (controlId: string, value: string) => void;
  onRunConfigurationChange: (configuration: RunConfigurationInput) => void;
  onObservedSoundingFile: (file: File) => void;
  onObservedSoundingTimeChange: (validTimeUtc: string) => void;
  onAtmosphereSourcePathChange: (sourcePath: AtmosphereSourcePath) => void;
  onSearchIntentChange: (intent: SearchIntent) => void;
  onStationSelectionModeChange: (mode: StationSelectionMode) => void;
  onSelectedStationToggle: (stationId: string) => void;
  onSelectAllCachedStations: () => void;
  onClearSelectedStations: () => void;
  onCandidateHistoryScopeChange: (scope: CandidateHistoryScope) => void;
  onCandidateStoryFilterChange: (filter: CandidateStoryFilter) => void;
  onCandidateStoryFamilyFilterChange: (filter: CandidateStoryFamilyFilter) => void;
  onCandidateSupportFilterChange: (filter: CandidateSupportFilter) => void;
  onCandidateSortChange: (sort: CandidateSort) => void;
  onCandidateStationSearchChange: (value: string) => void;
  onCandidateReadinessFilterChange: (filter: CandidateReadinessFilter) => void;
  onClearCandidateAnalysisFilters: () => void;
  onCandidateLatestPerStationChange: (value: string) => void;
  onCandidateResultLimitChange: (value: string) => void;
  onCandidateDetailChange: (candidateId: string) => void;
  onRefreshIGRAData: () => void;
  onCacheIGRAStationFiles: () => void;
  onPrepareAndSearchLocalSoundings: () => void;
  onScreenSoundingCandidates: () => void;
  onSaveSoundingCandidate: (candidate: SoundingCandidate) => void;
  onRemoveSavedSoundingCandidate: (savedCandidateId: string) => void;
  onSelectCandidateForRunSetup: (
    candidate: SoundingCandidate,
    savedCandidate?: SavedSoundingCandidate,
    activeStory?: CandidateStoryId,
  ) => void;
  onAddSelectedSoundingToRunPlan: () => void;
  onDuplicateRunPlanItem: (itemId: string) => void;
  onRemoveRunPlanItem: (itemId: string) => void;
  onClearSelectedRunPlanItems: () => void;
  onClearRunPlan: () => void;
  onRunPlanItemSelectedChange: (itemId: string, selected: boolean) => void;
  onRunPlanItemQueueTargetChange: (itemId: string, target: RunPlanQueueTarget) => void;
  onRunPlanItemConfigurationChange: (
    itemId: string,
    runConfiguration: RunConfigurationInput,
  ) => void;
  onCreateAndQueueRunPlan: () => void;
  onDryRun: (event: FormEvent<HTMLFormElement>) => void;
  onLaunchRun: () => void;
  onRefreshRunStatus: () => void;
  onLaunchLanWorkerRun: () => void;
  onRefreshLanWorkerStatus: () => void;
  onCollectLanWorkerRun: () => void;
  onCleanupLanWorkerRun: () => void;
  onIngestRun: () => void;
  onLaunchStoredRun: (manifestPath: string) => void;
  onLaunchStoredLanWorkerRun: (manifestPath: string) => void;
  onRefreshStoredLanWorkerStatus: (manifestPath: string) => void;
  onFinalizeStoredLanWorkerRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenInResults: () => void;
  onInspectIngested: () => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onRefreshStorage: () => void;
  onPreviewRunDelete: (runId: string) => void;
  onConfirmRunDelete: (runId: string) => void;
  onRetryScenarios: () => void;
}) {
  const scenarioControlsReady = scenarioLoadState === "loaded" && selectedScenario !== undefined;
  const runConfigurationPreview = previewRunConfiguration(runConfiguration);
  const runPlanPanel = (
    <RunPlanPanel
      items={runPlanItems}
      batchStatus={batchQueueStatus}
      lanWorkerConfigured={lanWorkerConfig?.configured ?? false}
      onSelectedChange={onRunPlanItemSelectedChange}
      onQueueTargetChange={onRunPlanItemQueueTargetChange}
      onConfigurationChange={onRunPlanItemConfigurationChange}
      onDuplicate={onDuplicateRunPlanItem}
      onRemove={onRemoveRunPlanItem}
      onClearSelected={onClearSelectedRunPlanItems}
      onClearAll={onClearRunPlan}
      onCreateAndQueue={onCreateAndQueueRunPlan}
    />
  );

  return (
    <section className="workspace-section" aria-labelledby="build-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Build</p>
          <h2 id="build-title">Build and run a CM1 experiment</h2>
        </div>
      </div>

      <section className="builder-layout" aria-label="Scenario Builder">
        <form id="build-run-package-form" className="builder-panel" onSubmit={onDryRun}>
          <label className="field-label" htmlFor="scenario">
            Experiment
          </label>
          <select
            id="scenario"
            value={scenarioControlsReady ? selectedScenarioId : ""}
            disabled={!scenarioControlsReady}
            onChange={(event) => onSelectScenario(event.target.value)}
          >
            {!scenarioControlsReady && <option value="">Scenario unavailable</option>}
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.display_name}
              </option>
            ))}
            {scenarios.some((scenario) => scenario.id === OBSERVED_SOUNDING_BASE_SCENARIO_ID) && (
              <option value={OBSERVED_SOUNDING_EXPERIMENT_ID}>Observed Soundings</option>
            )}
          </select>

          {scenarioLoadState === "loading" && (
            <ScenarioStatePanel
              title="Loading scenario catalog"
              body="Cloud Chamber is waiting for the local backend to return available CM1 scenario templates. Package controls will appear after a scenario is loaded."
            />
          )}

          {scenarioLoadState === "failed" && (
            <ScenarioStatePanel
              title="Scenario catalog unavailable"
              body={`Cloud Chamber could not load scenario templates from the local backend. ${
                scenarioError ?? "The backend may be stopped or temporarily unavailable."
              }`}
              actionLabel="Retry scenarios"
              onAction={onRetryScenarios}
            />
          )}

          {scenarioLoadState === "empty" && (
            <ScenarioStatePanel
              title="No scenarios available"
              body="The local backend responded, but it did not return any scenario templates. Package generation is unavailable until at least one scenario is configured."
              actionLabel="Retry scenarios"
              onAction={onRetryScenarios}
            />
          )}

          {scenarioControlsReady && (
            <>
              <div className="hero-case">
                <p className="eyebrow">Guided local CM1 experiment</p>
                <h2>
                  {observedSoundingExperimentSelected
                    ? "Observed Soundings"
                    : selectedScenario.display_name}
                </h2>
                <p>
                  {observedSoundingExperimentSelected
                    ? "Choose a local sounding source, review why an atmosphere looks interesting, then add one or more run variants to a batch plan."
                    : selectedScenario.description}
                </p>
              </div>

              <section aria-labelledby="physical-question-title">
                <h3 id="physical-question-title">Physical Question</h3>
                <p>
                  {observedSoundingExperimentSelected
                    ? "Given this observed atmosphere, what can CM1 honestly test under the selected surface forcing, run shape, and explicit assumptions?"
                    : selectedScenario.physical_question}
                </p>
              </section>

              {!observedSoundingExperimentSelected && (
                <>
                  <section
                    className="experiment-summary"
                    aria-labelledby="experiment-summary-title"
                  >
                    <h3 id="experiment-summary-title">Experiment setup summary</h3>
                    <dl className="compact-metrics">
                      <Metric label="Expected outcome" value={selectedScenario.expected_behavior} />
                      <Metric
                        label="Readiness"
                        value="Supported local package template from the scenario catalog"
                      />
                      <Metric
                        label="What changes"
                        value={selectedScenario.controls.map((control) => control.label).join(", ")}
                      />
                      <Metric
                        label="What stays controlled"
                        value="CM1 remains the source of truth; raw namelist details stay in technical review."
                      />
                    </dl>
                  </section>

                  <section aria-labelledby="controls-title">
                    <h3 id="controls-title">Curated Atmospheric Controls</h3>
                    {selectedScenario.controls.map((control) => (
                      <BuildControlRow
                        key={control.id}
                        control={control}
                        value={controls[control.id] ?? control.default}
                        onChange={(value) => onControlChange(control.id, value)}
                      />
                    ))}
                  </section>
                </>
              )}

              {observedSoundingExperimentSelected && (
                <>
                  <AtmosphereSourcePicker
                    sourcePath={atmosphereSourcePath}
                    savedCandidateCount={savedCandidates.length}
                    onChange={onAtmosphereSourcePathChange}
                  />

                  {atmosphereSourcePath === "cached_recommendations" && (
                    <ObservedAtmosphereCandidatesPanel
                      catalog={igraCatalog}
                      cache={igraCache}
                      screeningInputs={screeningInputs}
                      searchIntent={searchIntent}
                      stationSelectionMode={stationSelectionMode}
                      selectedStationIds={selectedStationIds}
                      historyScope={candidateHistoryScope}
                      storyFilter={candidateStoryFilter}
                      storyFamilyFilter={candidateStoryFamilyFilter}
                      supportFilter={candidateSupportFilter}
                      sort={candidateSort}
                      stationSearch={candidateStationSearch}
                      readinessFilter={candidateReadinessFilter}
                      latestPerStation={candidateLatestPerStation}
                      resultLimit={candidateResultLimit}
                      status={candidateStatus}
                      error={candidateError}
                      screening={candidateScreening}
                      savedCandidates={savedCandidates}
                      selectedCandidateId={candidateDetailId}
                      onSearchIntentChange={onSearchIntentChange}
                      onStationSelectionModeChange={onStationSelectionModeChange}
                      onSelectedStationToggle={onSelectedStationToggle}
                      onSelectAllCachedStations={onSelectAllCachedStations}
                      onClearSelectedStations={onClearSelectedStations}
                      onHistoryScopeChange={onCandidateHistoryScopeChange}
                      onStoryFilterChange={onCandidateStoryFilterChange}
                      onStoryFamilyFilterChange={onCandidateStoryFamilyFilterChange}
                      onSupportFilterChange={onCandidateSupportFilterChange}
                      onSortChange={onCandidateSortChange}
                      onStationSearchChange={onCandidateStationSearchChange}
                      onReadinessFilterChange={onCandidateReadinessFilterChange}
                      onClearFilters={onClearCandidateAnalysisFilters}
                      onLatestPerStationChange={onCandidateLatestPerStationChange}
                      onResultLimitChange={onCandidateResultLimitChange}
                      onCandidateDetailChange={onCandidateDetailChange}
                      onRefreshIGRAData={onRefreshIGRAData}
                      onCacheStationFiles={onCacheIGRAStationFiles}
                      onPrepareAndSearch={onPrepareAndSearchLocalSoundings}
                      onScreen={onScreenSoundingCandidates}
                      onSave={onSaveSoundingCandidate}
                      onSelectForRunSetup={onSelectCandidateForRunSetup}
                    />
                  )}

                  {atmosphereSourcePath === "saved_candidates" && (
                    <SavedCandidatesSourcePanel
                      savedCandidates={savedCandidates}
                      status={candidateStatus}
                      error={candidateError}
                      onSave={onSaveSoundingCandidate}
                      onRemoveSaved={onRemoveSavedSoundingCandidate}
                      onSelectForRunSetup={onSelectCandidateForRunSetup}
                    />
                  )}

                  {atmosphereSourcePath === "upload_igra_text" && (
                    <UploadSoundingSourcePanel
                      observedSoundingParse={observedSoundingParse}
                      observedSoundingStatus={observedSoundingStatus}
                      observedSoundingError={observedSoundingError}
                      selectedCandidateScreening={selectedCandidateScreening}
                      onObservedSoundingFile={onObservedSoundingFile}
                      onObservedSoundingTimeChange={onObservedSoundingTimeChange}
                    />
                  )}

                  {observedSoundingParse?.selected_sounding && (
                    <SelectedSoundingRunSetupPanel
                      observedSounding={observedSoundingParse.selected_sounding}
                      selectedCandidateScreening={selectedCandidateScreening}
                      runConfiguration={runConfiguration}
                      runConfigurationPreview={runConfigurationPreview}
                      onRunConfigurationChange={onRunConfigurationChange}
                      onAddSelectedSoundingToRunPlan={onAddSelectedSoundingToRunPlan}
                    />
                  )}

                  {runPlanPanel}
                </>
              )}

              {!observedSoundingExperimentSelected && (
                <RunConfigurationPanel
                  configuration={runConfiguration}
                  preview={runConfigurationPreview}
                  onChange={onRunConfigurationChange}
                />
              )}

              {validationMessages.length > 0 && (
                <div className="validation" role="alert">
                  {validationMessages.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                </div>
              )}

              {packageError && (
                <div className="validation" role="alert">
                  <p>{packageError}</p>
                </div>
              )}

              {blockedPreRunValidationReport && (
                <PreRunValidationReportPanel report={blockedPreRunValidationReport} />
              )}

              {!observedSoundingExperimentSelected && (
                <BuildRunActionPanel
                  dryRun={dryRun}
                  runStatus={runStatus}
                  lanWorkerStatus={lanWorkerStatus}
                  lanWorkerConfigured={lanWorkerConfig?.configured ?? false}
                  canCreatePackage={validationMessages.length === 0}
                  onLaunchRun={onLaunchRun}
                  onLaunchLanWorkerRun={onLaunchLanWorkerRun}
                />
              )}
            </>
          )}
        </form>

        <aside className="side-stack">
          <RunMonitorPanel
            dryRun={dryRun}
            runStatus={runStatus}
            runQueue={runQueue}
            runQueueStatus={runQueueStatus}
            error={runWorkflowError}
            lanWorkerConfig={lanWorkerConfig}
            lanWorkerStatus={lanWorkerStatus}
            lanWorkerError={lanWorkerError}
            lanWorkerActionStatus={lanWorkerActionStatus}
            ingestedResultId={ingestedResultId}
            onRefreshRunStatus={onRefreshRunStatus}
            onLaunchLanWorkerRun={onLaunchLanWorkerRun}
            onRefreshLanWorkerStatus={onRefreshLanWorkerStatus}
            onCollectLanWorkerRun={onCollectLanWorkerRun}
            onCleanupLanWorkerRun={onCleanupLanWorkerRun}
            onIngestRun={onIngestRun}
            storageInventory={storageInventory}
            storageStatus={storageStatus}
            storageError={storageError}
            runDeletePreview={runDeletePreview}
            runDeleteMessage={runDeleteMessage}
            results={results}
            autoFinalizingWorkerRunIds={autoFinalizingWorkerRunIds}
            failedAutoFinalizingWorkerRunIds={failedAutoFinalizingWorkerRunIds}
            onLaunchStoredRun={onLaunchStoredRun}
            onLaunchStoredLanWorkerRun={onLaunchStoredLanWorkerRun}
            onRefreshStoredLanWorkerStatus={onRefreshStoredLanWorkerStatus}
            onFinalizeStoredLanWorkerRun={onFinalizeStoredLanWorkerRun}
            onIngestStoredRun={onIngestStoredRun}
            onOpenInResults={onOpenInResults}
            onInspectIngested={onInspectIngested}
            onOpenStoredResult={onOpenStoredResult}
            onExploreStoredResult={onExploreStoredResult}
            onRefreshStorage={onRefreshStorage}
            onPreviewRunDelete={onPreviewRunDelete}
            onConfirmRunDelete={onConfirmRunDelete}
          />
        </aside>
      </section>
    </section>
  );
}

function BuildControlRow({
  control,
  value,
  onChange,
}: {
  control: ScenarioControl;
  value: string | number | boolean;
  onChange: (value: string) => void;
}) {
  const selectedOption = selectedControlOption(control, { [control.id]: value });
  return (
    <div className="control-row">
      <span>
        <label htmlFor={`control-${control.id}`}>
          <strong>{control.label}</strong>
        </label>
        <small>{control.description}</small>
        <small>
          Selected: {selectedOption?.label ?? String(value ?? control.default)}.{" "}
          {selectedOption?.description ??
            "Supported scenario option; raw CM1 settings remain in technical review."}
        </small>
      </span>
      <select
        id={`control-${control.id}`}
        value={String(value ?? control.default)}
        onChange={(event) => onChange(event.target.value)}
      >
        {control.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function PreRunValidationReportPanel({ report }: { report: PreRunValidationReport }) {
  const hypothesis = report.selected_hypothesis ?? null;
  const recipe = report.selected_run_recipe ?? null;
  const alignment = report.hypothesis_recipe_alignment ?? null;
  const runShape = report.run_shape_validation ?? null;
  const outputValidation = report.output_validation ?? null;
  const blockingErrors = report.blocking_errors ?? [];
  const caveats = report.caveats ?? [];

  return (
    <section
      className="experiment-summary pre-run-validation-panel"
      aria-label="Pre-run validation report"
    >
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Pre-run validation</p>
          <h3>Hypothesis and experiment setup check</h3>
          <p className="field-help">
            Cloud Chamber checks whether the selected hypothesis, forcing, fields, and run shape can
            be compared honestly before CM1 is launched.
          </p>
        </div>
        <StatusBadge
          label={preRunValidationStatusLabel(report.status)}
          tone={preRunValidationTone(report.status)}
        />
      </div>

      <dl className="compact-metrics">
        <Metric
          label="Hypothesis"
          value={
            hypothesis?.story_label ??
            humanize(hypothesis?.story_id ?? hypothesis?.hypothesis_id ?? "none")
          }
        />
        {typeof hypothesis?.ingredient_score === "number" && (
          <Metric
            label={hypothesis.ingredient_score_label ?? "Ingredient score"}
            value={`${Math.round(hypothesis.ingredient_score)} %`}
          />
        )}
        <Metric
          label="Run recipe"
          value={
            recipe?.recipe_display_name ??
            recipe?.display_name ??
            humanize(recipe?.recipe_id ?? "unknown")
          }
        />
        <Metric label="Assumption set" value={recipe?.assumption_set_id ?? "Not declared"} />
        <Metric
          label="Run shape"
          value={
            runShape
              ? preRunValidationRunShapeLabel(runShape)
              : "Run shape unavailable before package generation"
          }
        />
        <Metric
          label="Required outputs"
          value={compactList(outputValidation?.required_fields, "No specific fields required")}
        />
        <Metric
          label="Missing assumptions"
          value={compactList(alignment?.missing_assumptions, "None")}
        />
        <Metric
          label="Missing outputs"
          value={compactList(outputValidation?.missing_fields, "None")}
        />
      </dl>

      {alignment?.reasons?.length ? (
        <ul>
          {alignment.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : null}

      {blockingErrors.length > 0 && (
        <div className="validation">
          <h4>Blocking issues</h4>
          <ul>
            {blockingErrors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {caveats.length > 0 && (
        <details className="technical-details">
          <summary>Validation caveats</summary>
          <ul>
            {caveats.map((caveat) => (
              <li key={caveat}>{humanize(caveat)}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

function BuildRunActionPanel({
  dryRun,
  runStatus,
  lanWorkerStatus,
  lanWorkerConfigured,
  canCreatePackage,
  onLaunchRun,
  onLaunchLanWorkerRun,
}: {
  dryRun: DryRunResponse | null;
  runStatus: RunStatusResponse | null;
  lanWorkerStatus: LanWorkerRunResponse | null;
  lanWorkerConfigured: boolean;
  canCreatePackage: boolean;
  onLaunchRun: () => void;
  onLaunchLanWorkerRun: () => void;
}) {
  const packageReadyForQueue = Boolean(dryRun && !runStatus && !lanWorkerStatus);
  return (
    <section className="experiment-summary build-run-action-panel" aria-label="Package and queue">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Package and queue</p>
          <h3>{dryRun ? "Package ready for CM1" : "Ready to package this setup"}</h3>
          <p className="field-help">
            Create the run package from the selected sounding, hypothesis, and CM1 run settings.
            Then choose whether this package should run locally or on the trusted LAN worker.
          </p>
        </div>
        <StatusBadge
          label={dryRun ? "Package ready" : canCreatePackage ? "Ready" : "Needs setup"}
          tone={dryRun ? "good" : canCreatePackage ? "good" : "warning"}
        />
      </div>

      <div className="button-row">
        <button
          type="submit"
          data-testid="create-package-btn"
          className={dryRun ? "secondary-button" : undefined}
          disabled={!canCreatePackage}
        >
          {dryRun ? "Create another package" : "Create run package"}
        </button>
        {packageReadyForQueue && (
          <>
            <button type="button" data-testid="launch-cm1-btn" onClick={onLaunchRun}>
              Queue local CM1 run
            </button>
            <button
              type="button"
              className="secondary-button"
              data-testid="launch-lan-worker-btn"
              onClick={onLaunchLanWorkerRun}
              disabled={!lanWorkerConfigured}
            >
              Run on LAN worker
            </button>
          </>
        )}
      </div>
      {packageReadyForQueue && !lanWorkerConfigured && (
        <p className="state-note">
          LAN worker execution is unavailable until an ignored local worker config is present.
        </p>
      )}
    </section>
  );
}

function RunConfigurationPanel({
  configuration,
  preview,
  selectedCandidateScreening,
  onAddToRunPlan,
  onChange,
  embedded = false,
}: {
  configuration: RunConfigurationInput;
  preview: RunConfiguration;
  selectedCandidateScreening?: Record<string, unknown> | null;
  onAddToRunPlan?: () => void;
  onChange: (configuration: RunConfigurationInput) => void;
  embedded?: boolean;
}) {
  const recipeMismatchWarning = selectedCandidateScreening
    ? candidateRecipeMismatchWarning(selectedCandidateScreening)
    : null;
  const appliedForcing = observedRecipeAppliedForcing(preview);
  const configurationHelp =
    "Choose lower-boundary forcing, model time, grid, domain, and cadence for this atmosphere.";
  const configurationNotes: string[] = [];
  if (preview.mode === "smoke") {
    configurationNotes.push(
      "Smoke mode is only for package health and CM1 startup behavior; it should not be used to judge atmospheric evolution.",
    );
  }
  if (preview.caveats.includes("configuration_better_suited_to_larger_compute")) {
    configurationNotes.push(
      "This configuration may be better suited to larger compute. Cloud Chamber still shows the CM1-facing values before launch.",
    );
  }
  const update = (key: keyof RunConfigurationInput, value: string) => {
    onChange({ ...configuration, [key]: value });
  };
  const panelClassName = embedded
    ? "run-configuration-panel embedded-run-configuration-panel"
    : "experiment-summary run-configuration-panel";
  return (
    <section className={panelClassName} aria-labelledby="run-configuration-title">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Run configuration</p>
          <h3 id="run-configuration-title">Configure this CM1 run</h3>
          <p className="field-help">{configurationHelp}</p>
        </div>
        <StatusBadge
          label={preview.mode === "smoke" ? "Smoke check" : "Science run"}
          tone={preview.mode === "smoke" ? "warning" : "good"}
        />
      </div>

      <div className="run-configuration-grid">
        <RunConfigurationSelect
          id="run-surface-forcing-mode"
          label="Surface forcing"
          description="Uniform background fluxes, or an idealized warm/moist lower-boundary patch."
          value={configuration.surface_forcing_mode}
          options={SURFACE_FORCING_OPTIONS}
          onChange={(value) => update("surface_forcing_mode", value)}
        />
        <RunConfigurationTextInput
          id="run-surface-heat-flux"
          label="Surface heat flux"
          units="K m/s"
          description="CM1 cnst_shflx. Current baseline is 8.0e-3; 0.03-0.10 is a stronger daytime-heating sensitivity; values above about 0.2 are very aggressive."
          value={configuration.surface_heat_flux_k_m_s}
          onChange={(value) => update("surface_heat_flux_k_m_s", value)}
        />
        <RunConfigurationTextInput
          id="run-surface-moisture-flux"
          label="Surface moisture flux"
          units="g/g m/s"
          description="CM1 cnst_lhflx. Current baseline is 5.2e-5; 2e-5-1e-4 is a useful moisture-supply sensitivity; values above about 2e-4 are very aggressive."
          value={configuration.surface_moisture_flux_g_g_m_s}
          onChange={(value) => update("surface_moisture_flux_g_g_m_s", value)}
        />
        {configuration.surface_forcing_mode === DIFFERENTIAL_SURFACE_FORCING_MODE && (
          <>
            <RunConfigurationTextInput
              id="run-surface-patch-radius"
              label="Patch radius"
              units="m"
              description="Centered circle radius; must fit inside the domain and span at least three cells."
              value={configuration.surface_patch_radius_m}
              onChange={(value) => update("surface_patch_radius_m", value)}
            />
            <RunConfigurationTextInput
              id="run-surface-patch-heat"
              label="Patch heat perturbation"
              units="K m/s"
              description="Added to the background inside the patch after taper and ramp."
              value={configuration.surface_patch_heat_flux_perturbation_k_m_s}
              onChange={(value) => update("surface_patch_heat_flux_perturbation_k_m_s", value)}
            />
            <RunConfigurationTextInput
              id="run-surface-patch-moisture"
              label="Patch moisture perturbation"
              units="g/g m/s"
              description="Added to the background inside the patch after taper and ramp."
              value={configuration.surface_patch_moisture_flux_perturbation_g_g_m_s}
              onChange={(value) =>
                update("surface_patch_moisture_flux_perturbation_g_g_m_s", value)
              }
            />
            <RunConfigurationTextInput
              id="run-surface-patch-taper"
              label="Patch taper"
              units="m"
              description="Raised-cosine edge width."
              value={configuration.surface_patch_taper_width_m}
              onChange={(value) => update("surface_patch_taper_width_m", value)}
            />
            <RunConfigurationTextInput
              id="run-surface-patch-ramp"
              label="Patch ramp"
              units="s"
              description="Seconds to ramp from background to full perturbation."
              value={configuration.surface_patch_ramp_seconds}
              onChange={(value) => update("surface_patch_ramp_seconds", value)}
            />
          </>
        )}
        <RunConfigurationSelect
          id="run-duration"
          label="Duration"
          description="Model-time length."
          value={configuration.duration}
          options={DURATION_OPTIONS}
          onChange={(value) => update("duration", value)}
        />
        <RunConfigurationSelect
          id="run-grid"
          label="Horizontal cells"
          description="Cell budget; more cells reduce dx/dy and increase cost."
          value={configuration.horizontal_cell_count}
          options={HORIZONTAL_CELL_OPTIONS}
          onChange={(value) => update("horizontal_cell_count", value)}
        />
        <RunConfigurationSelect
          id="run-domain"
          label="Domain size"
          description="Domain width and model top."
          value={configuration.domain_size}
          options={DOMAIN_OPTIONS}
          onChange={(value) => update("domain_size", value)}
        />
        <RunConfigurationSelect
          id="run-cadence"
          label="Output cadence"
          description="Saved-output interval for Results and Explore."
          value={configuration.output_cadence}
          options={OUTPUT_CADENCE_OPTIONS}
          onChange={(value) => update("output_cadence", value)}
        />
      </div>

      {recipeMismatchWarning && (
        <div className="validation" role="alert">
          {recipeMismatchWarning}
        </div>
      )}

      <dl className="compact-metrics run-configuration-summary">
        <Metric label="Forcing" value={appliedForcing} />
        <Metric label="Runtime" value={runConfigurationTimingSummary(preview)} />
        <Metric label="Grid" value={runConfigurationGridSummary(preview)} />
        <Metric label="Saved fields" value={runConfigurationFieldSummary(preview)} />
      </dl>

      {configurationNotes.length > 0 && (
        <details className="technical-details run-configuration-notes">
          <summary>Configuration notes</summary>
          <ul className="compact-list">
            {configurationNotes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </details>
      )}

      {selectedCandidateScreening && (
        <ObservedRunRecipePanel selectedCandidateScreening={selectedCandidateScreening} />
      )}

      <details className="technical-details">
        <summary>CM1-facing values</summary>
        <dl className="compact-metrics">
          <Metric
            label="nx / ny / nz"
            value={`${preview.cm1_values.nx} / ${preview.cm1_values.ny} / ${preview.cm1_values.nz}`}
          />
          <Metric
            label="dx / dy / dz"
            value={`${formatMeters(preview.cm1_values.dx_m)} / ${formatMeters(preview.cm1_values.dy_m)} / ${formatMeters(preview.cm1_values.dz_m)}`}
          />
          <Metric label="Model top" value={formatMeters(preview.cm1_values.model_top_m)} />
          <Metric label="Timestep" value={formatSeconds(preview.cm1_values.time_step_seconds)} />
          <Metric
            label="Saved output cadence"
            value={formatSeconds(preview.cm1_values.output_cadence_seconds)}
          />
          <Metric
            label="Rayleigh damping start"
            value={formatMeters(preview.cm1_values.rayleigh_damping_start_m)}
          />
          <Metric label="Surface flux mode" value={humanize(preview.surface_flux_mode)} />
          <Metric
            label="cnst_shflx"
            value={formatScientific(
              preview.surface_flux_cm1_values.cnst_shflx,
              preview.surface_flux_cm1_values.cnst_shflx_units,
            )}
          />
          <Metric
            label="cnst_lhflx"
            value={formatScientific(
              preview.surface_flux_cm1_values.cnst_lhflx,
              preview.surface_flux_cm1_values.cnst_lhflx_units,
            )}
          />
          <Metric
            label="Surface switches"
            value={`isfcflx ${preview.surface_flux_cm1_values.isfcflx}; sfcmodel ${preview.surface_flux_cm1_values.sfcmodel}; set_flx ${preview.surface_flux_cm1_values.set_flx}; set_ust ${preview.surface_flux_cm1_values.set_ust}`}
          />
        </dl>
      </details>

      {onAddToRunPlan && (
        <div className="run-configuration-action-row">
          <div>
            <p className="eyebrow">Add to run plan</p>
            <h4>Stage this configured run</h4>
            <p className="field-help">
              Adds an editable planned run below; duplicate it there to compare variants.
            </p>
          </div>
          <button type="button" onClick={onAddToRunPlan}>
            Add to run plan
          </button>
        </div>
      )}
    </section>
  );
}

function RunConfigurationSelect({
  id,
  label,
  description,
  value,
  options,
  onChange,
}: {
  id: string;
  label: string;
  description: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  const descriptionId = `${id}-description`;
  return (
    <div className="run-configuration-control">
      <span>
        <label htmlFor={id}>
          <strong>{label}</strong>
        </label>
        <small id={descriptionId}>{description}</small>
      </span>
      <select
        id={id}
        value={value}
        aria-describedby={descriptionId}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function RunConfigurationTextInput({
  id,
  label,
  units,
  description,
  value,
  onChange,
}: {
  id: string;
  label: string;
  units: string;
  description: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const descriptionId = `${id}-description`;
  return (
    <div className="run-configuration-control">
      <span>
        <label htmlFor={id}>
          <strong>{label}</strong>
        </label>
        <small id={descriptionId}>
          {units}; {description}
        </small>
      </span>
      <input
        id={id}
        type="text"
        inputMode="decimal"
        value={value}
        aria-describedby={descriptionId}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function ScenarioStatePanel({
  title,
  body,
  actionLabel,
  onAction,
}: {
  title: string;
  body: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <section className="scenario-state-panel" aria-live="polite">
      <h3>{title}</h3>
      <p>{body}</p>
      {actionLabel && onAction && (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </section>
  );
}

function AtmosphereSourcePicker({
  sourcePath,
  savedCandidateCount,
  onChange,
}: {
  sourcePath: AtmosphereSourcePath;
  savedCandidateCount: number;
  onChange: (sourcePath: AtmosphereSourcePath) => void;
}) {
  const options: Array<{ value: AtmosphereSourcePath; label: string; description: string }> = [
    {
      value: "cached_recommendations",
      label: "Cached recommendations",
      description: "Search local cached soundings and review recommendation evidence.",
    },
    {
      value: "saved_candidates",
      label: `Saved candidates${savedCandidateCount > 0 ? ` (${savedCandidateCount})` : ""}`,
      description: "Use your saved shortlist as the atmosphere source.",
    },
    {
      value: "upload_igra_text",
      label: "Upload IGRA station text",
      description: "Manually upload and validate a station text file.",
    },
  ];
  const selected = options.find((option) => option.value === sourcePath) ?? options[0];
  return (
    <section className="experiment-summary atmosphere-source-panel" aria-label="Atmosphere source">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Atmosphere source</p>
          <h3>Choose one source path</h3>
          <p className="field-help">{selected.description}</p>
        </div>
        <StatusBadge label={selected.label} tone="neutral" />
      </div>
      <div className="button-row source-path-tabs" role="tablist" aria-label="Atmosphere sources">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={sourcePath === option.value}
            className={sourcePath === option.value ? "active-control" : "secondary-button"}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </section>
  );
}

function ObservedAtmosphereCandidatesPanel({
  catalog,
  cache,
  screeningInputs,
  searchIntent,
  stationSelectionMode,
  selectedStationIds,
  historyScope,
  storyFilter,
  storyFamilyFilter,
  supportFilter,
  sort,
  stationSearch,
  readinessFilter,
  latestPerStation,
  resultLimit,
  status,
  error,
  screening,
  savedCandidates,
  selectedCandidateId,
  onSearchIntentChange,
  onStationSelectionModeChange,
  onSelectedStationToggle,
  onSelectAllCachedStations,
  onClearSelectedStations,
  onHistoryScopeChange,
  onStoryFilterChange,
  onStoryFamilyFilterChange,
  onSupportFilterChange,
  onSortChange,
  onStationSearchChange,
  onReadinessFilterChange,
  onClearFilters,
  onLatestPerStationChange,
  onResultLimitChange,
  onCandidateDetailChange,
  onRefreshIGRAData,
  onCacheStationFiles,
  onPrepareAndSearch,
  onScreen,
  onSave,
  onSelectForRunSetup,
}: {
  catalog: IGRACatalogResponse["catalog"] | null;
  cache: IGRACacheResponse | null;
  screeningInputs: ScreeningInput[];
  searchIntent: SearchIntent;
  stationSelectionMode: StationSelectionMode;
  selectedStationIds: string[];
  historyScope: CandidateHistoryScope;
  storyFilter: CandidateStoryFilter;
  storyFamilyFilter: CandidateStoryFamilyFilter;
  supportFilter: CandidateSupportFilter;
  sort: CandidateSort;
  stationSearch: string;
  readinessFilter: CandidateReadinessFilter;
  latestPerStation: string;
  resultLimit: string;
  status: string;
  error: string | null;
  screening: ScreeningResult | null;
  savedCandidates: SavedSoundingCandidate[];
  selectedCandidateId: string | null;
  onSearchIntentChange: (intent: SearchIntent) => void;
  onStationSelectionModeChange: (mode: StationSelectionMode) => void;
  onSelectedStationToggle: (stationId: string) => void;
  onSelectAllCachedStations: () => void;
  onClearSelectedStations: () => void;
  onHistoryScopeChange: (scope: CandidateHistoryScope) => void;
  onStoryFilterChange: (filter: CandidateStoryFilter) => void;
  onStoryFamilyFilterChange: (filter: CandidateStoryFamilyFilter) => void;
  onSupportFilterChange: (filter: CandidateSupportFilter) => void;
  onSortChange: (sort: CandidateSort) => void;
  onStationSearchChange: (value: string) => void;
  onReadinessFilterChange: (filter: CandidateReadinessFilter) => void;
  onClearFilters: () => void;
  onLatestPerStationChange: (value: string) => void;
  onResultLimitChange: (value: string) => void;
  onCandidateDetailChange: (candidateId: string) => void;
  onRefreshIGRAData: () => void;
  onCacheStationFiles: () => void;
  onPrepareAndSearch: () => void;
  onScreen: () => void;
  onSave: (candidate: SoundingCandidate, tags?: string[], notes?: string | null) => void;
  onSelectForRunSetup: (
    candidate: SoundingCandidate,
    savedCandidate?: SavedSoundingCandidate,
    activeStory?: CandidateStoryId,
  ) => void;
}) {
  const visibleCandidates = screening?.candidates ?? [];
  const selectedCandidate =
    visibleCandidates.find((candidate) => candidate.candidate_id === selectedCandidateId) ??
    visibleCandidates[0] ??
    null;
  const savedCandidateIds = useMemo(
    () => new Set(savedCandidates.map((saved) => saved.candidate.candidate_id)),
    [savedCandidates],
  );
  const selectedSavedCandidate =
    selectedCandidate === null
      ? null
      : (savedCandidates.find(
          (saved) => saved.candidate.candidate_id === selectedCandidate.candidate_id,
        ) ?? null);
  const cachedStations =
    screeningInputs.length > 0
      ? new Set(screeningInputs.map((input) => input.station_id)).size
      : new Set((cache?.entries ?? []).map((entry) => entry.station_id)).size;
  const cachedStationFiles =
    screeningInputs.length > 0 ? screeningInputs.length : (cache?.entries.length ?? 0);
  const stationOptions = useMemo(() => {
    const inputByStation = new Map(screeningInputs.map((input) => [input.station_id, input]));
    const optionByStation = new Map<
      string,
      {
        station_id: string;
        station_name?: string | null;
        cached: boolean;
        cached_status?: string | null;
        sounding_count: number;
        latest_valid_time_utc?: string | null;
      }
    >();
    for (const reference of catalog?.zip_references ?? []) {
      const input = inputByStation.get(reference.station_id);
      optionByStation.set(reference.station_id, {
        station_id: reference.station_id,
        station_name: reference.station_name,
        cached: Boolean(input) || reference.cached_status !== "not_cached",
        cached_status: reference.cached_status,
        sounding_count: input?.sounding_count ?? 0,
        latest_valid_time_utc: input?.latest_valid_time_utc ?? null,
      });
    }
    for (const input of screeningInputs) {
      const current = optionByStation.get(input.station_id);
      optionByStation.set(input.station_id, {
        station_id: input.station_id,
        station_name: input.station_name ?? current?.station_name ?? null,
        cached: true,
        cached_status: input.cached_status,
        sounding_count: input.sounding_count ?? 0,
        latest_valid_time_utc: input.latest_valid_time_utc ?? null,
      });
    }
    return [...optionByStation.values()].sort((left, right) =>
      (left.station_name ?? left.station_id).localeCompare(right.station_name ?? right.station_id),
    );
  }, [catalog?.zip_references, screeningInputs]);
  const selectedStationIdSet = useMemo(() => new Set(selectedStationIds), [selectedStationIds]);
  const cachedStationOptions = stationOptions.filter((option) => option.cached);
  const activeStationOptions =
    stationSelectionMode === "selected"
      ? stationOptions.filter((option) => selectedStationIdSet.has(option.station_id))
      : cachedStationOptions;
  const selectedCachedStationOptions = activeStationOptions.filter((option) => option.cached);
  const selectedUncachedStationOptions = activeStationOptions.filter((option) => !option.cached);
  const selectedCachedSoundingCount = selectedCachedStationOptions.reduce(
    (total, option) => total + option.sounding_count,
    0,
  );
  const screenableSoundingCount = screeningInputs.reduce(
    (total, input) => total + (input.sounding_count ?? 0),
    0,
  );
  const cachedInventorySummary =
    screenableSoundingCount > 0
      ? `${screenableSoundingCount.toLocaleString()} cached soundings`
      : `${screeningInputs.length.toLocaleString()} cached files`;
  const latestPerCachedFile = boundedInteger(latestPerStation, 1, 2000, 20);
  const plannedAnalysisCount =
    historyScope === "all_cached"
      ? selectedCachedSoundingCount
      : selectedCachedStationOptions.reduce(
          (total, option) => total + Math.min(option.sounding_count, latestPerCachedFile),
          0,
        );
  const plannedAnalysisSummary =
    selectedCachedStationOptions.length > 0
      ? `${plannedAnalysisCount.toLocaleString()} sounding${plannedAnalysisCount === 1 ? "" : "s"} from ${selectedCachedStationOptions.length.toLocaleString()} cached station${selectedCachedStationOptions.length === 1 ? "" : "s"}`
      : "No cached stations selected";
  const stationSelectionSummary =
    stationSelectionMode === "all_cached"
      ? `All ${cachedStationOptions.length.toLocaleString()} cached station${cachedStationOptions.length === 1 ? "" : "s"}`
      : `${selectedStationIds.length.toLocaleString()} selected station${selectedStationIds.length === 1 ? "" : "s"}`;
  const lastAnalysisSummary = screening
    ? `${visibleCandidates.length.toLocaleString()} shown from ${(
        screening.filtered_candidate_count ?? visibleCandidates.length
      ).toLocaleString()} matching / ${(screening.total_candidate_count ?? visibleCandidates.length).toLocaleString()} analyzed`
    : "Not run yet";
  const filterTraceSummary = candidateFilterTraceSummary(screening, {
    storyFilter,
    storyFamilyFilter,
    supportFilter,
    readinessFilter,
  });
  const activeRefinements = [
    storyFilter !== "all" ? `Story: ${candidateStoryLabel(storyFilter)}` : null,
    storyFamilyFilter !== "all" ? `Family: ${candidateStoryFamilyLabel(storyFamilyFilter)}` : null,
    supportFilter !== "all" ? `Evidence tier: ${supportTierLabel(supportFilter)}` : null,
    readinessFilter !== "all" ? `Readiness: ${humanize(readinessFilter)}` : null,
    stationSearch.trim() ? `Station search: ${stationSearch.trim()}` : null,
    sort !== "best_match" ? `Sort: ${candidateSortLabel(sort)}` : null,
  ].filter((item): item is string => item !== null);

  return (
    <section
      className="experiment-summary sounding-candidate-workbench"
      aria-labelledby="sounding-candidates-title"
    >
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Observed atmosphere</p>
          <h3 id="sounding-candidates-title">Find interesting soundings</h3>
          <p className="field-help">
            Choose the stations and history to search, then review the matching candidate evidence.
          </p>
        </div>
        <p className="state-chip" role="status">
          {status}
        </p>
      </div>

      <section
        className="candidate-search-controls"
        aria-label="Prepare and search local soundings"
      >
        <div className="run-configuration-grid">
          <label>
            <span>Source region</span>
            <select aria-label="Source region" value="great_plains_midwest" disabled>
              <option value="great_plains_midwest">Great Plains / Midwest</option>
            </select>
            <small>Current local station catalog scope.</small>
          </label>
          <label>
            <span>Search intent</span>
            <select
              aria-label="Search intent"
              value={searchIntent}
              onChange={(event) => onSearchIntentChange(event.target.value as SearchIntent)}
            >
              {SEARCH_INTENT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
              <option value="winter_disabled" disabled>
                Cold season / winter (not supported yet)
              </option>
            </select>
            <small>Sets the recommendation category and explanation focus.</small>
          </label>
          <label>
            <span>History scope</span>
            <select
              aria-label="History scope"
              value={historyScope}
              onChange={(event) =>
                onHistoryScopeChange(event.target.value as CandidateHistoryScope)
              }
            >
              {HISTORY_SCOPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <small>
              {HISTORY_SCOPE_OPTIONS.find((option) => option.value === historyScope)?.description}
            </small>
          </label>
          {historyScope === "latest_per_station" && (
            <label>
              <span>Latest soundings per station</span>
              <input
                aria-label="Latest soundings per station"
                type="number"
                min="1"
                max="2000"
                value={latestPerStation}
                onChange={(event) => onLatestPerStationChange(event.target.value)}
              />
              <small>Applied to each selected cached station.</small>
            </label>
          )}
          <label>
            <span>Returned candidate limit</span>
            <input
              aria-label="Returned candidate limit"
              type="number"
              min="1"
              max="500"
              value={resultLimit}
              onChange={(event) => onResultLimitChange(event.target.value)}
            />
            <small>Limit is applied after the selected soundings are analyzed.</small>
          </label>
        </div>
        <div className="candidate-search-set-summary" aria-label="Selected soundings">
          <Metric label="Selected soundings" value={plannedAnalysisSummary} />
          <Metric label="Station set" value={stationSelectionSummary} />
          <Metric label="Cached inventory" value={cachedInventorySummary} />
          <Metric
            label="Uncached selected"
            value={`${selectedUncachedStationOptions.length.toLocaleString()} station${selectedUncachedStationOptions.length === 1 ? "" : "s"}`}
          />
        </div>
        <div className="candidate-discovery-actions" aria-label="Sounding search action">
          <button type="button" onClick={onPrepareAndSearch}>
            Search selected soundings
          </button>
        </div>
      </section>

      <section className="candidate-station-picker" aria-label="Station picker">
        <div className="panel-heading-row">
          <div>
            <h4>Station set</h4>
            <p className="field-help">
              Search all cached stations, or choose specific stations to cache or analyze.
            </p>
          </div>
          <div className="button-row">
            <button
              type="button"
              className={
                stationSelectionMode === "all_cached"
                  ? "active-secondary-button"
                  : "secondary-button"
              }
              onClick={onSelectAllCachedStations}
            >
              All cached stations
            </button>
            <button
              type="button"
              className={
                stationSelectionMode === "selected" ? "active-secondary-button" : "secondary-button"
              }
              onClick={() => onStationSelectionModeChange("selected")}
            >
              Choose stations
            </button>
            <button type="button" className="secondary-button" onClick={onClearSelectedStations}>
              Clear selected
            </button>
          </div>
        </div>
        {stationSelectionMode === "selected" ? (
          <div className="station-picklist">
            {stationOptions.length === 0 ? (
              <p className="field-help">Refresh the IGRA catalog to load station choices.</p>
            ) : (
              stationOptions.map((station) => (
                <label key={station.station_id} className="station-picklist-row">
                  <input
                    type="checkbox"
                    checked={selectedStationIdSet.has(station.station_id)}
                    onChange={() => onSelectedStationToggle(station.station_id)}
                  />
                  <span>
                    <strong>{station.station_name ?? station.station_id}</strong>
                    <small>
                      {station.station_id} ·{" "}
                      {station.cached
                        ? `${station.sounding_count.toLocaleString()} cached sounding${station.sounding_count === 1 ? "" : "s"}`
                        : "not cached"}
                    </small>
                  </span>
                  <StatusBadge
                    label={station.cached ? "Cached" : "Available to cache"}
                    tone={station.cached ? "good" : "neutral"}
                  />
                </label>
              ))
            )}
          </div>
        ) : (
          <p className="field-help">
            Using all cached stations. Click Choose stations to pick specific stations or cache
            uncached catalog stations.
          </p>
        )}
      </section>

      <details className="candidate-cache-summary" aria-label="Local sounding data">
        <summary>
          {screeningInputs.length > 0
            ? `Local data ready · ${cachedStationFiles.toLocaleString()} station file${cachedStationFiles === 1 ? "" : "s"} · ${cachedInventorySummary} · refreshed ${
                catalog?.refreshed_at ? formatDate(catalog.refreshed_at) : "not refreshed here"
              }`
            : "No cached soundings ready"}
        </summary>
        <dl className="compact-metrics candidate-cache-metrics">
          <Metric label="Region" value={catalog?.region.label ?? "Great Plains / Midwest"} />
          <Metric
            label="Catalog"
            value={catalog?.refreshed_at ? formatDate(catalog.refreshed_at) : "Not refreshed here"}
          />
          <Metric label="Station files" value={cachedStationFiles.toLocaleString()} />
          <Metric label="Parsed soundings" value={cachedInventorySummary} />
          <Metric label="Last search" value={lastAnalysisSummary} />
        </dl>
      </details>

      {error && (
        <div className="validation" role="alert">
          <p>{error}</p>
        </div>
      )}

      {activeRefinements.length > 0 && (
        <div className="screening-guidance-note">
          <strong>Search filters applied</strong>
          <span>{activeRefinements.join(" · ")}</span>
          <button type="button" className="link-button" onClick={onClearFilters}>
            Clear refinements
          </button>
        </div>
      )}

      <details className="candidate-advanced-filters">
        <summary>Advanced filters</summary>
        <div className="candidate-toolbar" aria-label="Advanced sounding candidate controls">
          <label>
            Story
            <select
              value={storyFilter}
              onChange={(event) => onStoryFilterChange(event.target.value as CandidateStoryFilter)}
            >
              <option value="all">All screening stories</option>
              <option value="deep_convection_trial">Deep-convection stories</option>
              <option value="shallow_cumulus_candidate">Cloud-forming shallow cumulus</option>
              <option value="dry_failed_candidate">Dry failed cumulus</option>
              <option value="capped_suppressed_candidate">Capped / suppressed</option>
              <option value="humid_rainy_candidate">Humid / rainy</option>
              <option value="severe_thunderstorm_environment">
                Severe thunderstorm environment
              </option>
              <option value="supercell_environment">Supercell-like environment</option>
              <option value="high_cape_pulse_storm">High-CAPE pulse storm</option>
              <option value="dry_microburst_inverted_v">Dry microburst / inverted-V</option>
              <option value="squall_line_cold_pool_candidate">
                Squall-line / cold-pool candidate
              </option>
              <option value="elevated_convection">Elevated convection</option>
              <option value="needs_review">Needs review</option>
              <option value="poor_or_incomplete_candidate">Poor or incomplete</option>
            </select>
          </label>
          <label>
            Story family
            <select
              value={storyFamilyFilter}
              onChange={(event) =>
                onStoryFamilyFilterChange(event.target.value as CandidateStoryFamilyFilter)
              }
            >
              <option value="all">All families</option>
              <option value="lower_atmosphere">Lower-atmosphere stories</option>
              <option value="deep_convection">Deep-convection stories</option>
              <option value="review">Needs review / incomplete</option>
            </select>
          </label>
          <label>
            Evidence tier
            <select
              value={supportFilter}
              onChange={(event) =>
                onSupportFilterChange(event.target.value as CandidateSupportFilter)
              }
            >
              <option value="all">All evidence tiers</option>
              <option value="supported">Supported</option>
              <option value="weak">Plausible / caveated</option>
              <option value="unavailable">Little or no signal</option>
            </select>
          </label>
          <label>
            Sort
            <select
              value={sort}
              onChange={(event) => onSortChange(event.target.value as CandidateSort)}
            >
              <option value="best_match">Recommended</option>
              <option value="valid_time">Valid time</option>
              <option value="station_id">Station ID</option>
              <option value="station_name">Station name</option>
              <option value="primary_story">Primary story</option>
              <option value="story_family">Story family</option>
              <option value="rank_score">Rank score</option>
              <option value="deep_tower_opportunity">Deep-Tower opportunity</option>
              <option value="confidence">Confidence</option>
              <option value="support">Evidence tier</option>
              <option value="package_readiness">Package readiness</option>
              <option value="observed_wind_available">Observed wind availability</option>
              <option value="profile_top_m_agl">Profile top</option>
              <option value="lowest_level_m_agl">Lowest usable level</option>
              <option value="data_completeness_score">Data completeness</option>
              <option value="low_level_qv_g_kg">Low-level qv</option>
              <option value="mean_qv_0_500m_g_kg">Mean qv 0-500 m</option>
              <option value="mean_qv_0_1000m_g_kg">Mean qv 0-1 km</option>
              <option value="surface_t_td_spread_c">Surface T-Td spread</option>
              <option value="estimated_lcl_height_m_agl">Estimated LCL</option>
              <option value="lapse_rate_0_1000m_c_per_km">Low-level lapse rate</option>
              <option value="midlevel_lapse_rate_700_500_hpa_c_per_km">Midlevel lapse rate</option>
              <option value="cap_strength_proxy">Cap/inversion strength</option>
              <option value="cap_height_m_agl">Cap/inversion height</option>
              <option value="bulk_shear_0_1km_m_s">Bulk shear 0-1 km</option>
              <option value="bulk_shear_0_3km_m_s">Bulk shear 0-3 km</option>
              <option value="bulk_shear_0_6km_m_s">Bulk shear 0-6 km</option>
              <option value="midlevel_dry_layer_proxy">Dry-layer proxy</option>
              <option value="dry_microburst_inverted_v_proxy">Inverted-V proxy</option>
              <option value="freezing_level_m_agl">Freezing level</option>
            </select>
          </label>
          <label>
            Result text search
            <input
              type="search"
              value={stationSearch}
              placeholder="Station name, ID, or story"
              onChange={(event) => onStationSearchChange(event.target.value)}
            />
          </label>
          <label>
            Readiness
            <select
              value={readinessFilter}
              onChange={(event) =>
                onReadinessFilterChange(event.target.value as CandidateReadinessFilter)
              }
            >
              <option value="all">All readiness states</option>
              <option value="package_ready">Package-ready only</option>
              <option value="blocked">Blocked / needs review</option>
            </select>
          </label>
          <div className="candidate-toolbar-actions">
            <button type="button" className="secondary-button" onClick={onScreen}>
              Apply advanced filters
            </button>
            <button type="button" className="secondary-button" onClick={onRefreshIGRAData}>
              Refresh catalog
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={selectedUncachedStationOptions.length === 0}
              onClick={onCacheStationFiles}
            >
              Cache selected stations
            </button>
          </div>
        </div>
        <dl className="compact-metrics">
          <Metric label="Cached stations" value={cachedStations.toString()} />
          <Metric label="Cached station files" value={cachedStationFiles.toString()} />
          <Metric label="Selected soundings" value={plannedAnalysisSummary} />
          <Metric label="Returned candidate limit" value={resultLimit} />
        </dl>
      </details>

      <div className="candidate-workspace">
        <section aria-label="Screened sounding candidates">
          {screening && (
            <div className="candidate-list-heading">
              <h4>
                {activeRefinements.length > 0
                  ? "Refined candidates"
                  : "Recommended cached soundings"}
              </h4>
              <p className="field-help">{filterTraceSummary.summary}</p>
              {filterTraceSummary.detail && (
                <p className="field-help candidate-filter-detail">{filterTraceSummary.detail}</p>
              )}
            </div>
          )}
          {visibleCandidates.length === 0 ? (
            <div className="scenario-state-panel">
              <h4>No screened candidates loaded</h4>
              <p>
                Refresh the IGRA catalog if needed, cache station files, then analyze
                recommendations from the soundings already cached locally.
              </p>
            </div>
          ) : (
            <div className="candidate-list">
              {visibleCandidates.map((candidate) => (
                <SoundingCandidateCard
                  key={candidate.candidate_id}
                  candidate={candidate}
                  storyFilter={storyFilter}
                  storyFamilyFilter={storyFamilyFilter}
                  selected={selectedCandidate?.candidate_id === candidate.candidate_id}
                  saved={savedCandidateIds.has(candidate.candidate_id)}
                  onSelect={() => onCandidateDetailChange(candidate.candidate_id)}
                  onSave={() => onSave(candidate)}
                  onSelectForRunSetup={(activeStory) =>
                    onSelectForRunSetup(
                      candidate,
                      savedCandidates.find(
                        (saved) => saved.candidate.candidate_id === candidate.candidate_id,
                      ),
                      activeStory,
                    )
                  }
                />
              ))}
            </div>
          )}
        </section>

        <SoundingCandidateDetail
          candidate={selectedCandidate}
          storyFilter={storyFilter}
          storyFamilyFilter={storyFamilyFilter}
          savedCandidate={selectedSavedCandidate}
          onSave={onSave}
          onSelectForRunSetup={(candidate, activeStory) =>
            onSelectForRunSetup(candidate, selectedSavedCandidate ?? undefined, activeStory)
          }
        />
      </div>
    </section>
  );
}

function SavedCandidatesSourcePanel({
  savedCandidates,
  status,
  error,
  onSave,
  onRemoveSaved,
  onSelectForRunSetup,
}: {
  savedCandidates: SavedSoundingCandidate[];
  status: string;
  error: string | null;
  onSave: (candidate: SoundingCandidate, tags?: string[], notes?: string | null) => void;
  onRemoveSaved: (savedCandidateId: string) => void;
  onSelectForRunSetup: (
    candidate: SoundingCandidate,
    savedCandidate?: SavedSoundingCandidate,
    activeStory?: CandidateStoryId,
  ) => void;
}) {
  return (
    <section
      className="experiment-summary saved-candidates-panel"
      aria-labelledby="saved-candidates-title"
    >
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Saved source</p>
          <h3 id="saved-candidates-title">Saved candidate shortlist</h3>
          <p className="field-help">
            Saved candidates are atmosphere hypotheses you chose to keep. Add one or more to the run
            plan, then duplicate variants if you want different recipes or configurations.
          </p>
        </div>
        <StatusBadge
          label={`${savedCandidates.length.toLocaleString()} saved`}
          tone={savedCandidates.length > 0 ? "good" : "warning"}
        />
      </div>
      <p className="state-chip" role="status">
        {status}
      </p>
      {error && <p className="error-text">{error}</p>}
      {savedCandidates.length === 0 ? (
        <div className="scenario-state-panel">
          <h4>No saved candidates yet</h4>
          <p>
            Switch to cached recommendations, select a candidate, and save it with tags or notes.
          </p>
        </div>
      ) : (
        <div className="saved-candidate-list">
          {savedCandidates.map((saved) => (
            <SavedSoundingCandidateCard
              key={saved.saved_candidate_id}
              saved={saved}
              onUpdateAnnotations={(tags, notes) => onSave(saved.candidate, tags, notes)}
              onUse={() =>
                onSelectForRunSetup(
                  saved.candidate,
                  saved,
                  saved.candidate.active_story ?? saved.primary_story,
                )
              }
              onRemove={() => onRemoveSaved(saved.saved_candidate_id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function SavedSoundingCandidateCard({
  saved,
  onUpdateAnnotations,
  onUse,
  onRemove,
}: {
  saved: SavedSoundingCandidate;
  onUpdateAnnotations: (tags: string[], notes: string | null) => void;
  onUse: () => void;
  onRemove: () => void;
}) {
  const [tagDraft, setTagDraft] = useState(saved.tags.join(", "));
  const [notesDraft, setNotesDraft] = useState(saved.notes ?? "");
  useEffect(() => {
    setTagDraft(saved.tags.join(", "));
    setNotesDraft(saved.notes ?? "");
  }, [saved.saved_candidate_id, saved.tags, saved.notes]);
  const handleTagSuggestion = (tag: string) => {
    setTagDraft(_dedupeStrings([...parseTags(tagDraft), tag]).join(", "));
  };
  const handleSaveAnnotations = () => {
    onUpdateAnnotations(parseTags(tagDraft), notesDraft.trim() || null);
  };
  return (
    <article
      className="saved-candidate-card"
      aria-label={`Saved sounding candidate ${candidateStationLabel(saved.candidate)}`}
    >
      <div>
        <strong>{candidateStationLabel(saved.candidate)}</strong>
        <small>
          {formatDate(saved.candidate.valid_time_utc)} · {candidateStoryLabel(saved.primary_story)}
        </small>
        {(saved.tags.length > 0 || saved.notes) && (
          <small>
            {saved.tags.length > 0
              ? `${saved.tags.length} tag${saved.tags.length === 1 ? "" : "s"}`
              : "No tags"}
            {saved.notes ? " · notes saved" : ""}
          </small>
        )}
        {saved.linked_run_ids.length > 0 && (
          <small>Used in {saved.linked_run_ids.join(", ")}</small>
        )}
      </div>
      <details className="saved-candidate-notes-drawer">
        <summary>Tags and notes</summary>
        <div className="candidate-notes-form">
          <label htmlFor={`saved-tags-${saved.saved_candidate_id}`}>
            Tags
            <input
              id={`saved-tags-${saved.saved_candidate_id}`}
              value={tagDraft}
              placeholder="deep convection, rerun, compare"
              onChange={(event) => setTagDraft(event.target.value)}
            />
          </label>
          <div className="candidate-tag-suggestions" aria-label="Suggested label shortcuts">
            {candidateSuggestedTags.map((tag) => (
              <button
                type="button"
                className="secondary-button"
                key={tag}
                onClick={() => handleTagSuggestion(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
          <label htmlFor={`saved-notes-${saved.saved_candidate_id}`}>
            Notes
            <textarea
              id={`saved-notes-${saved.saved_candidate_id}`}
              value={notesDraft}
              placeholder="What makes this worth running or comparing?"
              onChange={(event) => setNotesDraft(event.target.value)}
            />
          </label>
          <button type="button" className="secondary-button" onClick={handleSaveAnnotations}>
            Save tags and notes
          </button>
        </div>
      </details>
      <div className="button-row">
        <button type="button" onClick={onUse}>
          Configure run
        </button>
        <button type="button" className="secondary-button" onClick={onRemove}>
          Remove saved
        </button>
      </div>
    </article>
  );
}

function SoundingCandidateCard({
  candidate,
  storyFilter,
  storyFamilyFilter,
  selected,
  saved,
  onSelect,
  onSave,
  onSelectForRunSetup,
}: {
  candidate: SoundingCandidate;
  storyFilter: CandidateStoryFilter;
  storyFamilyFilter: CandidateStoryFamilyFilter;
  selected: boolean;
  saved: boolean;
  onSelect: () => void;
  onSave: () => void;
  onSelectForRunSetup: (activeStory: CandidateStoryId) => void;
}) {
  const story = candidateActiveStoryId(candidate, storyFilter, storyFamilyFilter);
  const activeFamily = story ? candidateStoryFamilyForStory(story) : candidate.story_family;
  const ingredientScore = candidateIngredientScore(candidate, storyFilter, storyFamilyFilter);
  const ingredientScoreLabel = candidateIngredientScoreLabel(
    candidate,
    storyFilter,
    storyFamilyFilter,
  );
  const recipeFit = candidateRecipeFitForStory(candidate, story);
  const reasons = candidateInterestReasons(candidate).slice(0, 3);
  const keyNote = candidateKeyNote(candidate, story, recipeFit);
  return (
    <article
      className={`candidate-card${selected ? " selected-candidate-card" : ""}`}
      aria-label={`Sounding candidate ${candidateStationLabel(candidate)}`}
    >
      <button
        type="button"
        className="candidate-card-main candidate-card-select"
        onClick={onSelect}
      >
        <span>
          <strong>{candidateStationLabel(candidate)}</strong>
          <small>{formatDate(candidate.valid_time_utc)}</small>
        </span>
        <span className="candidate-card-storyline">
          {candidateDisplayStoryLabel(candidate, storyFilter, storyFamilyFilter)} ·{" "}
          {formatNumber(ingredientScore, "%")} {ingredientScoreLabel.toLowerCase()} ·{" "}
          {candidate.package_ready ? "Package-ready" : "Blocked"}
        </span>
      </button>
      <p className="candidate-card-context">
        {candidate.discovery_bucket ? `${candidate.discovery_bucket} · ` : ""}
        {candidateStoryFamilyLabel(activeFamily)} · {recipeFit.label}
      </p>
      {reasons.length > 0 && (
        <div>
          <h5>Why it surfaced</h5>
          <ul className="compact-list candidate-reason-list">
            {reasons.map((reason) => (
              <li key={`${candidate.candidate_id}-card-${reason}`}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="candidate-card-note">{keyNote}</p>
      <div className="button-row">
        <button
          type="button"
          disabled={!candidate.package_ready}
          onClick={() => onSelectForRunSetup(story)}
        >
          Configure run
        </button>
        <button type="button" className="secondary-button" disabled={saved} onClick={onSave}>
          {saved ? "Saved" : "Save"}
        </button>
      </div>
    </article>
  );
}

function SoundingCandidateDetail({
  candidate,
  storyFilter,
  storyFamilyFilter,
  savedCandidate,
  onSave,
  onSelectForRunSetup,
}: {
  candidate: SoundingCandidate | null;
  storyFilter: CandidateStoryFilter;
  storyFamilyFilter: CandidateStoryFamilyFilter;
  savedCandidate: SavedSoundingCandidate | null;
  onSave: (candidate: SoundingCandidate, tags?: string[], notes?: string | null) => void;
  onSelectForRunSetup: (candidate: SoundingCandidate, activeStory: CandidateStoryId) => void;
}) {
  const [tagDraft, setTagDraft] = useState("");
  const [notesDraft, setNotesDraft] = useState("");
  const [saveDrawerOpen, setSaveDrawerOpen] = useState(false);
  const candidateId = candidate?.candidate_id ?? "";
  const savedTagsText = savedCandidate?.tags.join(", ") ?? "";
  const savedNotesText = savedCandidate?.notes ?? "";
  useEffect(() => {
    setTagDraft(savedTagsText);
    setNotesDraft(savedNotesText);
    setSaveDrawerOpen(false);
  }, [candidateId, savedCandidate?.saved_candidate_id, savedTagsText, savedNotesText]);

  if (!candidate) {
    return (
      <aside className="candidate-detail-panel">
        <h4>Candidate details</h4>
        <p>Select or screen a sounding candidate to inspect evidence, caveats, and readiness.</p>
      </aside>
    );
  }
  const activeCandidate = candidate;
  const activeScore = candidateActiveStoryScore(activeCandidate, storyFilter, storyFamilyFilter);
  const story = candidateActiveStoryId(activeCandidate, storyFilter, storyFamilyFilter);
  const activeFamily = story ? candidateStoryFamilyForStory(story) : activeCandidate.story_family;
  const ingredientScore = candidateIngredientScore(activeCandidate, storyFilter, storyFamilyFilter);
  const ingredientScoreLabel = candidateIngredientScoreLabel(
    activeCandidate,
    storyFilter,
    storyFamilyFilter,
  );
  const recipeFit = candidateRecipeFitForStory(activeCandidate, story);
  const reasons = candidateInterestReasons(activeCandidate).slice(0, 5);
  const topLimits = candidateTopLimits(activeCandidate, story, recipeFit);
  const runRecommendation = candidateRunRecommendation(activeCandidate, story, recipeFit);
  const savedTagValues = parseTags(tagDraft);
  function handleTagSuggestion(tag: string) {
    setTagDraft(_dedupeStrings([...savedTagValues, tag]).join(", "));
  }
  function handleAnnotationSubmit() {
    onSave(activeCandidate, parseTags(tagDraft), notesDraft.trim() || null);
    setSaveDrawerOpen(false);
  }
  const featureRows = [
    ["Observed wind profile", "observed_wind_available", ""],
    ["Profile top", "profile_top_m_agl", "m AGL"],
    ["Lowest usable level", "lowest_level_m_agl", "m AGL"],
    ["Data completeness", "data_completeness_score", "%"],
    ["Low-level qv", "low_level_qv_g_kg", "g/kg"],
    ["Mean qv 0-500 m", "mean_qv_0_500m_g_kg", "g/kg"],
    ["Low-level moisture", "mean_qv_0_1000m_g_kg", "g/kg"],
    ["Surface T-Td spread", "surface_t_td_spread_c", "C"],
    ["Estimated LCL", "estimated_lcl_height_m_agl", "m AGL"],
    ["Low-level lapse rate", "lapse_rate_0_1000m_c_per_km", "C/km"],
    ["Midlevel lapse rate", "midlevel_lapse_rate_700_500_hpa_c_per_km", "C/km"],
    ["Cap / inversion strength", "cap_strength_proxy", "C"],
    ["Cap / inversion height", "cap_height_m_agl", "m AGL"],
    ["Bulk shear 0-1 km", "bulk_shear_0_1km_m_s", "m/s"],
    ["Bulk shear 0-3 km", "bulk_shear_0_3km_m_s", "m/s"],
    ["Bulk shear 0-6 km", "bulk_shear_0_6km_m_s", "m/s"],
    ["Dry-layer proxy", "midlevel_dry_layer_proxy", "g/kg"],
    ["Inverted-V proxy", "dry_microburst_inverted_v_proxy", "0-100"],
    ["Freezing level", "freezing_level_m_agl", "m AGL"],
    ["Moisture depth", "moisture_depth_m", "m"],
  ] as const;
  return (
    <aside className="candidate-detail-panel" aria-label="Candidate details">
      <div className="panel-heading-row">
        <div>
          <h4>{candidateStationLabel(candidate)}</h4>
          <p>
            {formatDate(candidate.valid_time_utc)} ·{" "}
            {candidateDisplayStoryLabel(candidate, storyFilter, storyFamilyFilter)}
          </p>
        </div>
        <span className="badge-row">
          <StatusBadge
            label={candidate.package_ready ? "Package-ready" : "Needs review"}
            tone={candidate.package_ready ? "good" : "warning"}
          />
          <StatusBadge label={recipeFit.label} tone={candidateRecipeFitTone(recipeFit.status)} />
          <StatusBadge label={savedCandidate ? "Saved" : "Not saved"} tone="neutral" />
        </span>
      </div>
      <div className="candidate-detail-actions">
        <button
          type="button"
          disabled={!candidate.package_ready}
          onClick={() => onSelectForRunSetup(candidate, story)}
        >
          Configure run
        </button>
        <button type="button" className="secondary-button" onClick={() => setSaveDrawerOpen(true)}>
          {savedCandidate ? "Edit saved notes" : "Save candidate"}
        </button>
      </div>
      {saveDrawerOpen && (
        <div className="candidate-save-drawer" aria-label="Save candidate notes">
          <h5>Tags and notes</h5>
          <label htmlFor={`candidate-tags-${candidate.candidate_id}`}>
            Tags
            <input
              id={`candidate-tags-${candidate.candidate_id}`}
              value={tagDraft}
              placeholder="deep convection, rerun, compare"
              onChange={(event) => setTagDraft(event.target.value)}
            />
          </label>
          <div className="candidate-tag-suggestions" aria-label="Suggested label shortcuts">
            {candidateSuggestedTags.map((tag) => (
              <button
                type="button"
                className="secondary-button"
                key={tag}
                onClick={() => handleTagSuggestion(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
          <label htmlFor={`candidate-notes-${candidate.candidate_id}`}>
            Notes
            <textarea
              id={`candidate-notes-${candidate.candidate_id}`}
              value={notesDraft}
              placeholder="What makes this worth running or comparing?"
              onChange={(event) => setNotesDraft(event.target.value)}
            />
          </label>
          <div className="button-row">
            <button type="button" onClick={handleAnnotationSubmit}>
              {savedCandidate ? "Update saved candidate" : "Save"}
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setSaveDrawerOpen(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      <section className="candidate-detail-section">
        <h5>Why this is interesting</h5>
        <ul className="compact-list candidate-reason-list">
          {reasons.map((reason) => (
            <li key={`${candidate.candidate_id}-detail-${reason}`}>{reason}</li>
          ))}
        </ul>
      </section>
      <section className="candidate-detail-section">
        <h5>Recommended first run</h5>
        <p className="candidate-interest-summary">{runRecommendation.title}</p>
        <p className="field-help">{runRecommendation.detail}</p>
        {runRecommendation.followUp && <p className="field-help">{runRecommendation.followUp}</p>}
      </section>
      <section className="candidate-detail-section">
        <h5>Run fit</h5>
        <p className="candidate-interest-summary">
          {candidateKeyNote(candidate, story, recipeFit)}
        </p>
        <p className="field-help">{recipeFit.summary}</p>
      </section>
      <section className="candidate-detail-section">
        <h5>Top limits</h5>
        <ul className="compact-list">
          {topLimits.map((limit) => (
            <li key={`${candidate.candidate_id}-limit-${limit}`}>{limit}</li>
          ))}
        </ul>
      </section>
      <dl className="compact-metrics">
        <Metric label={ingredientScoreLabel} value={formatNumber(ingredientScore, "%")} />
        <Metric label="Evidence level" value={humanize(candidate.confidence)} />
        <Metric label="Screened story family" value={candidateStoryFamilyLabel(activeFamily)} />
        <Metric label="Recipe fit" value={recipeFit.label} />
        {activeScore && activeScore.story !== candidate.primary_story && (
          <Metric label="Primary story" value={candidate.primary_story_label} />
        )}
        <Metric label="Station ID" value={candidate.station_id} />
        <Metric
          label="Location"
          value={
            candidate.station_latitude !== null &&
            candidate.station_latitude !== undefined &&
            candidate.station_longitude !== null &&
            candidate.station_longitude !== undefined
              ? `${formatNumber(candidate.station_latitude, "deg")}, ${formatNumber(candidate.station_longitude, "deg")}`
              : "Not available"
          }
        />
      </dl>
      <details>
        <summary>All evidence</summary>
        <ul className="compact-list">
          {candidate.evidence.map((item) => (
            <li key={`${candidate.candidate_id}-detail-${item.label}`}>
              <strong>{item.label}:</strong> {candidateEvidenceValue(item)}. {item.interpretation}
            </li>
          ))}
        </ul>
      </details>
      <details>
        <summary>All ingredient scores</summary>
        <dl className="compact-metrics">
          {candidate.story_scores.map((score) => (
            <Metric
              key={score.story}
              label={score.label}
              value={`${formatNumber(score.score_0_to_100, "%")} · ${humanize(score.support)}`}
            />
          ))}
        </dl>
      </details>
      <details>
        <summary>Feature values</summary>
        <dl className="compact-metrics">
          {featureRows.map(([label, key, units]) => (
            <Metric key={key} label={label} value={candidateFeatureValue(candidate, key, units)} />
          ))}
        </dl>
      </details>
      {candidate.caveats.length > 0 && (
        <details>
          <summary>Screening caveats</summary>
          <ul className="compact-list">
            {candidate.caveats.map((caveat) => (
              <li key={caveat}>{humanize(caveat)}</li>
            ))}
          </ul>
        </details>
      )}
      <details>
        <summary>Raw metadata</summary>
        <dl className="compact-metrics">
          <Metric label="Candidate ID" value={candidate.candidate_id} />
          <Metric label="Screening version" value={candidate.screening_version} />
          <Metric label="Source file" value={candidate.source_file_name} />
          <Metric label="Source provider" value={candidate.source_provider} />
          <Metric label="Source format" value={candidate.source_format} />
          <Metric label="Source hash" value={candidate.source_file_hash} />
        </dl>
      </details>
    </aside>
  );
}

function UploadSoundingSourcePanel({
  observedSoundingParse,
  observedSoundingStatus,
  observedSoundingError,
  selectedCandidateScreening,
  onObservedSoundingFile,
  onObservedSoundingTimeChange,
}: {
  observedSoundingParse: ObservedSoundingParseResponse | null;
  observedSoundingStatus: string | null;
  observedSoundingError: string | null;
  selectedCandidateScreening: Record<string, unknown> | null;
  onObservedSoundingFile: (file: File) => void;
  onObservedSoundingTimeChange: (validTimeUtc: string) => void;
}) {
  return (
    <section className="upload-source-stack" aria-label="Upload IGRA station text source">
      <ObservedSoundingInputPanel
        parsed={observedSoundingParse}
        status={observedSoundingStatus}
        error={observedSoundingError}
        selectedCandidateScreening={selectedCandidateScreening}
        onFile={onObservedSoundingFile}
        onTimeChange={onObservedSoundingTimeChange}
      />
    </section>
  );
}

function SelectedSoundingRunSetupPanel({
  observedSounding,
  selectedCandidateScreening,
  runConfiguration,
  runConfigurationPreview,
  onRunConfigurationChange,
  onAddSelectedSoundingToRunPlan,
}: {
  observedSounding: ObservedSoundingRecord;
  selectedCandidateScreening: Record<string, unknown> | null;
  runConfiguration: RunConfigurationInput;
  runConfigurationPreview: RunConfiguration;
  onRunConfigurationChange: (configuration: RunConfigurationInput) => void;
  onAddSelectedSoundingToRunPlan: () => void;
}) {
  const source = runPlanSourceFromCandidateScreening(selectedCandidateScreening);
  const sourceLabel =
    source === "saved_candidates"
      ? "Saved candidate"
      : source === "cached_recommendations"
        ? "Cached recommendation"
        : "Uploaded IGRA station text";
  const stationLabel = selectedObservedSoundingStationLabel(
    observedSounding,
    selectedCandidateScreening,
  );
  const activeStoryLabel = observedRecipeStoryLabel(selectedCandidateScreening);
  const setupRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    setupRef.current?.scrollIntoView?.({ block: "start", behavior: "auto" });
  }, [observedSounding.station_id, observedSounding.valid_time_utc]);
  return (
    <section
      ref={setupRef}
      className="experiment-summary selected-sounding-setup selected-run-builder"
      aria-label="Selected sounding run setup"
    >
      <div className="selected-sounding-strip">
        <div className="panel-heading-row">
          <div>
            <p className="eyebrow">Selected sounding</p>
            <h3>{stationLabel}</h3>
          </div>
          <StatusBadge label="Ready to configure" tone="good" />
        </div>
        <p className="selected-sounding-context">
          {formatDate(observedSounding.valid_time_utc)} · {sourceLabel} · {activeStoryLabel} ·{" "}
          {humanize(observedSounding.validation.status)}
        </p>
        <details className="technical-details selected-sounding-details">
          <summary>Source, validation, and sounding details</summary>
          <dl className="compact-metrics selected-sounding-metrics">
            <Metric label="Source" value={sourceLabel} />
            <Metric label="Selected time" value={formatDate(observedSounding.valid_time_utc)} />
            <Metric label="Screened hypothesis" value={activeStoryLabel} />
            <Metric label="Validation" value={humanize(observedSounding.validation.status)} />
            <Metric label="Usable levels" value={observedSounding.levels.length.toString()} />
            <Metric label="Wind handling" value={humanize(observedSounding.wind_handling)} />
            <Metric
              label="Model bottom"
              value={formatNumber(observedSounding.model_bottom_elevation_m_msl, "m MSL")}
            />
          </dl>
        </details>
      </div>

      <RunConfigurationPanel
        configuration={runConfiguration}
        preview={runConfigurationPreview}
        selectedCandidateScreening={selectedCandidateScreening}
        onAddToRunPlan={onAddSelectedSoundingToRunPlan}
        onChange={onRunConfigurationChange}
        embedded
      />
    </section>
  );
}

function ObservedSoundingInputPanel({
  parsed,
  status,
  error,
  selectedCandidateScreening,
  onFile,
  onTimeChange,
}: {
  parsed: ObservedSoundingParseResponse | null;
  status: string | null;
  error: string | null;
  selectedCandidateScreening: Record<string, unknown> | null;
  onFile: (file: File) => void;
  onTimeChange: (validTimeUtc: string) => void;
}) {
  const selected = parsed?.selected_sounding;

  return (
    <section
      className="experiment-summary observed-sounding-panel"
      aria-labelledby="observed-sounding-title"
    >
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Observed sounding</p>
          <h3 id="observed-sounding-title">Use NOAA/NCEI IGRA station text</h3>
        </div>
      </div>

      <p className="field-help">
        Upload an extracted IGRA station sounding-data .txt file. Cloud Chamber anchors CM1 z=0 to
        the station surface and keeps place/time/source metadata as provenance.
      </p>

      <label className="field-label" htmlFor="observed-sounding-file">
        IGRA station sounding-data file
      </label>
      <input
        id="observed-sounding-file"
        type="file"
        accept=".txt,text/plain"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          if (file) onFile(file);
        }}
      />

      {status && <p className="inline-status">{status}</p>}
      {error && (
        <div className="validation" role="alert">
          <p>{error}</p>
        </div>
      )}

      {parsed && selected && (
        <section className="observed-sounding-review" aria-label="Observed sounding review">
          {selectedCandidateScreening && (
            <div className="screening-guidance-note">
              <strong>Screening guidance only</strong>
              <span>
                Screened as{" "}
                {candidateStoryLabel(
                  String(
                    selectedCandidateScreening.primary_story ?? "needs_review",
                  ) as CandidateStoryId,
                )}
                . CM1 decides what actually happens.
              </span>
            </div>
          )}
          <div className="control-row">
            <span>
              <label htmlFor="observed-sounding-time">
                <strong>Selected sounding time</strong>
              </label>
              <small>
                Latest available is selected by default. Choose another time from the uploaded
                station file if needed.
              </small>
            </span>
            <select
              id="observed-sounding-time"
              value={selected.valid_time_utc}
              onChange={(event) => onTimeChange(event.target.value)}
            >
              {parsed.available_soundings.map((sounding) => (
                <option key={sounding.valid_time_utc} value={sounding.valid_time_utc}>
                  {formatDate(sounding.valid_time_utc)} · {sounding.num_levels} source levels
                </option>
              ))}
            </select>
          </div>

          <details className="technical-details source-review-details">
            <summary>Uploaded-sounding review</summary>
            <dl className="compact-metrics">
              <Metric
                label="Source"
                value={`${parsed.source_provider} · ${parsed.source_format}`}
              />
              <Metric label="Uploaded file" value={parsed.uploaded_filename} />
              <Metric
                label="Station"
                value={`${selected.station_id}${selected.station_name ? ` · ${selected.station_name}` : ""}`}
              />
              <Metric
                label="Location"
                value={
                  selected.station_latitude !== null &&
                  selected.station_latitude !== undefined &&
                  selected.station_longitude !== null &&
                  selected.station_longitude !== undefined
                    ? `${formatNumber(selected.station_latitude, "deg")}, ${formatNumber(selected.station_longitude, "deg")}`
                    : "Not available"
                }
              />
              <Metric
                label="Model bottom / vertical datum"
                value={`CM1 z=0 is station surface at ${formatNumber(selected.model_bottom_elevation_m_msl, "m MSL")}`}
              />
              <Metric
                label="Source heights"
                value={`${humanize(selected.source_vertical_coordinate_type)} converted to height above station surface`}
              />
              <Metric
                label="Converted model z range"
                value={`${formatNumber(selected.levels[0]?.model_z_m ?? null, "m")} to ${formatNumber(selected.levels.at(-1)?.model_z_m ?? null, "m")}`}
              />
              <Metric label="Usable levels" value={selected.levels.length.toString()} />
              <Metric label="Wind handling" value={humanize(selected.wind_handling)} />
              <Metric label="Validation" value={humanize(selected.validation.status)} />
            </dl>

            {selected.validation.caveats.length > 0 && (
              <details>
                <summary>Observed-sounding caveats</summary>
                <ul className="compact-list">
                  {selected.validation.caveats.map((caveat) => (
                    <li key={caveat}>{humanize(caveat)}</li>
                  ))}
                </ul>
              </details>
            )}
          </details>
        </section>
      )}
    </section>
  );
}

function ObservedRunRecipePanel({
  selectedCandidateScreening,
}: {
  selectedCandidateScreening: Record<string, unknown> | null;
}) {
  const activeStory = observedRecipeStoryId(selectedCandidateScreening);
  const activeStoryLabel = observedRecipeStoryLabel(selectedCandidateScreening);
  const expectedSignatures = observedRecipeSignatureLabels(activeStory);
  const hypothesisSummary = observedRecipeHypothesisSummary(activeStory);
  const evidenceSummary = observedRecipeEvidenceSummary(selectedCandidateScreening);
  const recipeFitSummary = observedRecipeFitSummary(selectedCandidateScreening, activeStory);

  return (
    <details className="technical-details hypothesis-details-panel">
      <summary>
        Hypothesis, evidence, and expected outputs
        <span className="summary-note">{activeStoryLabel}</span>
      </summary>
      <dl className="compact-metrics">
        <Metric label="Atmospheric hypothesis" value={activeStoryLabel} />
        <Metric label="Expected evolution to check" value={hypothesisSummary} />
        <Metric label="Why this sounding looked interesting" value={evidenceSummary} />
        <Metric label="Can this run test it?" value={recipeFitSummary} />
      </dl>

      {expectedSignatures.length > 0 && (
        <div>
          <p className="eyebrow">CM1-observable signatures</p>
          <ul className="compact-list">
            {expectedSignatures.map((signature) => (
              <li key={signature}>{signature}</li>
            ))}
          </ul>
        </div>
      )}

      <dl className="compact-metrics">
        <Metric
          label="Run scope"
          value={
            activeStory && deepConvectionStoryIds.has(activeStory)
              ? "CM1 evolves the observed profile with explicit idealized thermal initiation."
              : "CM1 evolves the observed profile with the selected lower-boundary heat/moisture forcing."
          }
        />
      </dl>
    </details>
  );
}

function RunPlanPanel({
  items,
  batchStatus,
  lanWorkerConfigured,
  onSelectedChange,
  onQueueTargetChange,
  onConfigurationChange,
  onDuplicate,
  onRemove,
  onClearSelected,
  onClearAll,
  onCreateAndQueue,
}: {
  items: RunPlanItem[];
  batchStatus: string | null;
  lanWorkerConfigured: boolean;
  onSelectedChange: (itemId: string, selected: boolean) => void;
  onQueueTargetChange: (itemId: string, target: RunPlanQueueTarget) => void;
  onConfigurationChange: (itemId: string, configuration: RunConfigurationInput) => void;
  onDuplicate: (itemId: string) => void;
  onRemove: (itemId: string) => void;
  onClearSelected: () => void;
  onClearAll: () => void;
  onCreateAndQueue: () => void;
}) {
  const selectedCount = items.filter((item) => item.selected).length;
  const queuedCount = items.filter(
    (item) => item.status === "queued" || item.status === "lan_started",
  ).length;
  const failedCount = items.filter(
    (item) => item.status === "package_failed" || item.status === "skipped",
  ).length;
  return (
    <section className="experiment-summary run-plan-panel" aria-label="Run plan">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Run plan</p>
          <h3>Plan multiple CM1 runs</h3>
          <p className="field-help">
            Add candidate atmospheres, duplicate variants, edit forcing and run shape, then queue
            selected items as a batch.
          </p>
        </div>
        <StatusBadge
          label={`${items.length.toLocaleString()} planned · ${selectedCount.toLocaleString()} selected`}
          tone={items.length > 0 ? "good" : "warning"}
        />
      </div>

      {items.length === 0 ? (
        <div className="scenario-state-panel">
          <h4>No planned runs yet</h4>
          <p>
            Add a cached recommendation, saved candidate, or uploaded sounding to build a batch.
          </p>
        </div>
      ) : (
        <>
          <dl className="compact-metrics">
            <Metric label="Selected for queue" value={selectedCount.toLocaleString()} />
            <Metric label="Queued / launched" value={queuedCount.toLocaleString()} />
            <Metric label="Needs attention" value={failedCount.toLocaleString()} />
          </dl>
          <div className="run-plan-list">
            {items.map((item, index) => (
              <RunPlanItemCard
                key={item.id}
                item={item}
                index={index}
                lanWorkerConfigured={lanWorkerConfigured}
                onSelectedChange={onSelectedChange}
                onQueueTargetChange={onQueueTargetChange}
                onConfigurationChange={onConfigurationChange}
                onDuplicate={onDuplicate}
                onRemove={onRemove}
              />
            ))}
          </div>
        </>
      )}

      {batchStatus && <p className="inline-status">{batchStatus}</p>}

      <div className="button-row">
        <button type="button" disabled={selectedCount === 0} onClick={onCreateAndQueue}>
          Create packages and queue selected runs
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={selectedCount === 0}
          onClick={onClearSelected}
        >
          Clear selected
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={items.length === 0}
          onClick={onClearAll}
        >
          Clear all
        </button>
      </div>
    </section>
  );
}

function RunPlanItemCard({
  item,
  index,
  lanWorkerConfigured,
  onSelectedChange,
  onQueueTargetChange,
  onConfigurationChange,
  onDuplicate,
  onRemove,
}: {
  item: RunPlanItem;
  index: number;
  lanWorkerConfigured: boolean;
  onSelectedChange: (itemId: string, selected: boolean) => void;
  onQueueTargetChange: (itemId: string, target: RunPlanQueueTarget) => void;
  onConfigurationChange: (itemId: string, configuration: RunConfigurationInput) => void;
  onDuplicate: (itemId: string) => void;
  onRemove: (itemId: string) => void;
}) {
  const metadata = runPlanRecipeMetadata(item);
  const activeStory = item.activeStory ?? observedRecipeStoryId(item.candidateScreening);
  const preview = previewRunConfiguration(item.runConfiguration);
  const sourceLabel =
    item.candidate !== null
      ? `${candidateStationLabel(item.candidate)} · ${formatDate(item.candidate.valid_time_utc)}`
      : item.observedSounding
        ? `${selectedObservedSoundingStationLabel(item.observedSounding, item.candidateScreening)} · ${formatDate(item.observedSounding.valid_time_utc)}`
        : "Observed sounding";
  return (
    <article className="run-plan-card" aria-label={`Run plan item ${index + 1}`}>
      <div className="panel-heading-row">
        <label className="run-plan-select">
          <input
            type="checkbox"
            checked={item.selected}
            onChange={(event) => onSelectedChange(item.id, event.target.checked)}
          />
          <span>
            <strong>{sourceLabel}</strong>
            <small>
              {activeStory ? candidateStoryLabel(activeStory) : "Uploaded observed sounding"}
            </small>
          </span>
        </label>
        <StatusBadge
          label={runPlanStatusLabel(item.status)}
          tone={runPlanStatusTone(item.status)}
        />
      </div>

      {item.message && <p className="state-note">{item.message}</p>}
      {item.blockedPreRunValidationReport && (
        <PreRunValidationReportPanel report={item.blockedPreRunValidationReport} />
      )}

      <section
        className="run-plan-config-primary"
        aria-label={`Run configuration for item ${index + 1}`}
      >
        <div className="run-plan-config-heading">
          <div>
            <p className="eyebrow">Run configuration</p>
            <h4>Choose what CM1 will run</h4>
          </div>
          <span>{runConfigurationTimingSummary(preview)}</span>
        </div>
        <div className="run-configuration-grid run-plan-configuration-grid">
          <RunConfigurationSelect
            id={`run-plan-target-${item.id}`}
            label="Queue target"
            description="Choose where this package should run after creation."
            value={item.queueTarget}
            options={[
              { value: "local", label: "Local serial queue" },
              {
                value: "lan",
                label: lanWorkerConfigured ? "LAN worker" : "LAN worker unavailable",
              },
            ]}
            onChange={(value) => onQueueTargetChange(item.id, value as RunPlanQueueTarget)}
          />
          <RunPlanConfigurationFields
            item={item}
            preview={preview}
            onConfigurationChange={onConfigurationChange}
          />
        </div>
      </section>

      <details className="technical-details run-plan-recipe-details">
        <summary>Recipe assumptions, outputs, and caveats</summary>
        <dl className="compact-metrics run-plan-metadata-grid">
          <Metric label="Recipe ID" value={metadata.recipeId} />
          <Metric label="Assumption set" value={metadata.assumptionSetId} />
          <Metric label="Assumption mode" value={metadata.assumptionMode} />
          <Metric label="Assumptions" value={metadata.assumptionsSummary} />
          <Metric
            label="Required outputs"
            value={compactList(metadata.requiredOutputFields, "Not declared")}
          />
          <Metric
            label="Missing outputs"
            value={compactList(metadata.missingRequiredOutputFields, "None declared")}
          />
        </dl>
        {metadata.recipeCaveats.length > 0 && (
          <ul className="compact-list">
            {metadata.recipeCaveats.map((caveat) => (
              <li key={caveat}>{humanize(caveat)}</li>
            ))}
          </ul>
        )}
      </details>

      <div className="button-row">
        <button type="button" className="secondary-button" onClick={() => onDuplicate(item.id)}>
          Duplicate variant
        </button>
        <button type="button" className="secondary-button" onClick={() => onRemove(item.id)}>
          Remove
        </button>
      </div>
    </article>
  );
}

function RunPlanConfigurationFields({
  item,
  preview,
  onConfigurationChange,
}: {
  item: RunPlanItem;
  preview: RunConfiguration;
  onConfigurationChange: (itemId: string, configuration: RunConfigurationInput) => void;
}) {
  const update = (key: keyof RunConfigurationInput, value: string) => {
    onConfigurationChange(item.id, { ...item.runConfiguration, [key]: value });
  };
  return (
    <>
      <RunConfigurationSelect
        id={`run-plan-surface-forcing-mode-${item.id}`}
        label="Surface forcing"
        description="Uniform background fluxes, or an idealized warm/moist lower-boundary patch."
        value={item.runConfiguration.surface_forcing_mode}
        options={SURFACE_FORCING_OPTIONS}
        onChange={(value) => update("surface_forcing_mode", value)}
      />
      <RunConfigurationTextInput
        id={`run-plan-surface-heat-flux-${item.id}`}
        label="Surface heat flux"
        units="K m/s"
        description="CM1 cnst_shflx; baseline 8.0e-3, stronger sensitivity about 0.03-0.10."
        value={item.runConfiguration.surface_heat_flux_k_m_s}
        onChange={(value) => update("surface_heat_flux_k_m_s", value)}
      />
      <RunConfigurationTextInput
        id={`run-plan-surface-moisture-flux-${item.id}`}
        label="Surface moisture flux"
        units="g/g m/s"
        description="CM1 cnst_lhflx; baseline 5.2e-5, useful sensitivity about 2e-5-1e-4."
        value={item.runConfiguration.surface_moisture_flux_g_g_m_s}
        onChange={(value) => update("surface_moisture_flux_g_g_m_s", value)}
      />
      {item.runConfiguration.surface_forcing_mode === DIFFERENTIAL_SURFACE_FORCING_MODE && (
        <>
          <RunConfigurationTextInput
            id={`run-plan-surface-patch-radius-${item.id}`}
            label="Patch radius"
            units="m"
            description="Centered circle radius; must fit inside domain and span at least three cells."
            value={item.runConfiguration.surface_patch_radius_m}
            onChange={(value) => update("surface_patch_radius_m", value)}
          />
          <RunConfigurationTextInput
            id={`run-plan-surface-patch-heat-${item.id}`}
            label="Patch heat perturbation"
            units="K m/s"
            description="Added to background after taper and ramp."
            value={item.runConfiguration.surface_patch_heat_flux_perturbation_k_m_s}
            onChange={(value) => update("surface_patch_heat_flux_perturbation_k_m_s", value)}
          />
          <RunConfigurationTextInput
            id={`run-plan-surface-patch-moisture-${item.id}`}
            label="Patch moisture perturbation"
            units="g/g m/s"
            description="Added to background after taper and ramp."
            value={item.runConfiguration.surface_patch_moisture_flux_perturbation_g_g_m_s}
            onChange={(value) => update("surface_patch_moisture_flux_perturbation_g_g_m_s", value)}
          />
          <RunConfigurationTextInput
            id={`run-plan-surface-patch-taper-${item.id}`}
            label="Patch taper"
            units="m"
            description="Raised-cosine edge width."
            value={item.runConfiguration.surface_patch_taper_width_m}
            onChange={(value) => update("surface_patch_taper_width_m", value)}
          />
          <RunConfigurationTextInput
            id={`run-plan-surface-patch-ramp-${item.id}`}
            label="Patch ramp"
            units="s"
            description="Seconds to ramp to full perturbation."
            value={item.runConfiguration.surface_patch_ramp_seconds}
            onChange={(value) => update("surface_patch_ramp_seconds", value)}
          />
        </>
      )}
      <RunConfigurationSelect
        id={`run-plan-duration-${item.id}`}
        label="Duration"
        description="Model-time length."
        value={item.runConfiguration.duration}
        options={DURATION_OPTIONS}
        onChange={(value) => update("duration", value)}
      />
      <RunConfigurationSelect
        id={`run-plan-grid-${item.id}`}
        label="Horizontal cells"
        description="Controls dx/dy and compute."
        value={item.runConfiguration.horizontal_cell_count}
        options={HORIZONTAL_CELL_OPTIONS}
        onChange={(value) => update("horizontal_cell_count", value)}
      />
      <RunConfigurationSelect
        id={`run-plan-domain-${item.id}`}
        label="Domain size"
        description="Width and model top."
        value={item.runConfiguration.domain_size}
        options={DOMAIN_OPTIONS}
        onChange={(value) => update("domain_size", value)}
      />
      <RunConfigurationSelect
        id={`run-plan-cadence-${item.id}`}
        label="Output cadence"
        description="Saved-output interval."
        value={item.runConfiguration.output_cadence}
        options={OUTPUT_CADENCE_OPTIONS}
        onChange={(value) => update("output_cadence", value)}
      />
      <p className="field-help run-plan-config-summary">
        {runConfigurationGridSummary(preview)} · {preview.output_volume_summary}
      </p>
    </>
  );
}

function ResultsWorkspace({
  results,
  selectedResult,
  selectedResultId,
  resultsStatus,
  resultsError,
  resultDeletePreview,
  draft,
  onSelectResult,
  onDraftChange,
  onSubmit,
  onRefreshResults,
  onInspect,
  onPreviewResultDelete,
  onConfirmResultDelete,
  onCancelResultDelete,
}: {
  results: ResultCard[];
  selectedResult: ResultCard | undefined;
  selectedResultId: string | null;
  resultsStatus: string;
  resultsError: string | null;
  resultDeletePreview: DeleteResultResponse | null;
  draft: { name: string; tags: string; notes: string };
  onSelectResult: (resultId: string) => void;
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onRefreshResults: () => void;
  onInspect: () => void;
  onPreviewResultDelete: (resultId: string) => void;
  onConfirmResultDelete: (resultId: string) => void;
  onCancelResultDelete: () => void;
}) {
  return (
    <section className="results-library" aria-labelledby="results-title">
      <div className="section-heading">
        <div>
          <h2 id="results-title">Experiment Notebook</h2>
          <p>
            Review ingested cloud experiments, scan result cards, and open results for explanation.
          </p>
        </div>
        <button type="button" onClick={onRefreshResults}>
          Refresh results
        </button>
      </div>
      {resultsStatus !== "Results loaded" && resultsStatus !== "Loading results..." && (
        <p className="inline-status" role="status">
          {resultsStatus}
        </p>
      )}

      {resultsError && <p role="alert">{resultsError}</p>}

      <NotebookWorkspace
        results={results}
        selectedResult={selectedResult}
        selectedResultId={selectedResultId}
        draft={draft}
        onSelectResult={onSelectResult}
        onDraftChange={onDraftChange}
        onSubmit={onSubmit}
        onInspect={onInspect}
        onOpenResultInExplore={(resultId) => {
          onSelectResult(resultId);
          onInspect();
        }}
        deletePreview={resultDeletePreview}
        onPreviewDelete={onPreviewResultDelete}
        onConfirmDelete={onConfirmResultDelete}
        onCancelDelete={onCancelResultDelete}
      />
    </section>
  );
}

function NotebookWorkspace({
  results,
  selectedResult,
  selectedResultId,
  draft,
  onSelectResult,
  onDraftChange,
  onSubmit,
  onInspect,
  onOpenResultInExplore,
  deletePreview,
  onPreviewDelete,
  onConfirmDelete,
  onCancelDelete,
}: {
  results: ResultCard[];
  selectedResult: ResultCard | undefined;
  selectedResultId: string | null;
  draft: { name: string; tags: string; notes: string };
  onSelectResult: (resultId: string) => void;
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onInspect: () => void;
  onOpenResultInExplore: (resultId: string) => void;
  deletePreview: DeleteResultResponse | null;
  onPreviewDelete: (resultId: string) => void;
  onConfirmDelete: (resultId: string) => void;
  onCancelDelete: () => void;
}) {
  const [filters, setFilters] = useState<ResultsFilterState>(DEFAULT_RESULTS_FILTERS);
  const scenarioOptions = useMemo(() => resultScenarioOptions(results), [results]);
  const filteredResults = useMemo(() => filterAndSortResults(results, filters), [results, filters]);
  const filtersActive = resultsFiltersActive(filters);

  return (
    <section className="workspace-section" aria-label="Notebook entries">
      <ResultsFilterBar
        filters={filters}
        scenarioOptions={scenarioOptions}
        totalCount={results.length}
        visibleCount={filteredResults.length}
        onChange={setFilters}
        onReset={() => setFilters(DEFAULT_RESULTS_FILTERS)}
      />
      <div className="results-layout">
        <ExperimentNotebookList
          results={filteredResults}
          totalResults={results.length}
          filtersActive={filtersActive}
          selectedResultId={selectedResultId}
          onSelect={onSelectResult}
          onOpenExplore={onOpenResultInExplore}
          onResetFilters={() => setFilters(DEFAULT_RESULTS_FILTERS)}
        />
        <ResultNotebookCard
          result={selectedResult}
          draft={draft}
          onDraftChange={onDraftChange}
          onSubmit={onSubmit}
          onInspect={onInspect}
          deletePreview={deletePreview}
          onPreviewDelete={onPreviewDelete}
          onConfirmDelete={onConfirmDelete}
          onCancelDelete={onCancelDelete}
        />
      </div>
    </section>
  );
}

function ExploreWorkspace({ selectedResult }: { selectedResult: ResultCard | undefined }) {
  return (
    <section className="workspace-section explore-workspace" aria-label="Explore this result">
      {!selectedResult && (
        <section className="status-panel">
          <p>Select an ingested result from Results to inspect or visualize it.</p>
        </section>
      )}

      {selectedResult && (
        <section className="explore-result-view">
          <ExploreResultSummary result={selectedResult} />
          <VisualizerSceneShell result={selectedResult} />
        </section>
      )}
    </section>
  );
}

function ExploreResultSummary({ result }: { result: ResultCard }) {
  return (
    <section className="explore-result-summary" aria-label="Selected Explore result">
      <div>
        <h3>{result.name}</h3>
        <p>
          {result.scenario_name ?? humanize(result.scenario_id)} ·{" "}
          {resultRunConfigurationLabel(result.run_configuration)}
          {result.completed_at ? ` · ${formatDate(result.completed_at)}` : ""}
        </p>
        <p>{resultStory(result)}</p>
        {result.candidate_hypothesis_comparison && (
          <p className="secondary-result-note">
            {result.candidate_hypothesis_comparison.screened_as ?? "Screened candidate"} ·{" "}
            {result.candidate_hypothesis_comparison.match_status_label}:{" "}
            {result.candidate_hypothesis_comparison.cm1_outcome}
          </p>
        )}
      </div>
      <div className="badge-row">
        <OutcomeBadge result={result} />
        <StatusBadge label={rainWaterOutcome(result)} tone="neutral" />
        <StatusBadge label={resultInputSourceLabel(result)} tone="neutral" />
        <StatusBadge label={scienceSupportLabel(result)} tone="neutral" />
      </div>
    </section>
  );
}

type LocalRunWorkflowPanelProps = {
  dryRun: DryRunResponse | null;
  runStatus: RunStatusResponse | null;
  runQueue: RunQueueResponse | null;
  runQueueStatus: string;
  error: string | null;
  lanWorkerConfig: LanWorkerConfigResponse | null;
  lanWorkerStatus: LanWorkerRunResponse | null;
  lanWorkerError: string | null;
  lanWorkerActionStatus: string | null;
  ingestedResultId: string | null;
  storageInventory: StorageInventoryResponse | null;
  storageStatus: string;
  storageError: string | null;
  runDeletePreview: DeleteRunResponse | null;
  runDeleteMessage: string | null;
  results: ResultCard[];
  autoFinalizingWorkerRunIds: Set<string>;
  failedAutoFinalizingWorkerRunIds: Set<string>;
  onRefreshRunStatus: () => void;
  onLaunchLanWorkerRun: () => void;
  onRefreshLanWorkerStatus: () => void;
  onCollectLanWorkerRun: () => void;
  onCleanupLanWorkerRun: () => void;
  onIngestRun: () => void;
  onLaunchStoredRun: (manifestPath: string) => void;
  onLaunchStoredLanWorkerRun: (manifestPath: string) => void;
  onRefreshStoredLanWorkerStatus: (manifestPath: string) => void;
  onFinalizeStoredLanWorkerRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenInResults: () => void;
  onInspectIngested: () => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onRefreshStorage: () => void;
  onPreviewRunDelete: (runId: string) => void;
  onConfirmRunDelete: (runId: string) => void;
};

function RunMonitorPanel(props: LocalRunWorkflowPanelProps) {
  const activeRunIds = new Set<string>();
  if (props.runQueue?.active_run_id) activeRunIds.add(props.runQueue.active_run_id);
  if (
    props.lanWorkerStatus &&
    ["submitted", "running", "copied_to_worker"].includes(props.lanWorkerStatus.state)
  ) {
    activeRunIds.add(props.lanWorkerStatus.run_id);
  }
  props.storageInventory?.runs.forEach((run) => {
    if (run.category === "running" || run.lifecycle_state === "running") {
      activeRunIds.add(run.run_id);
    }
  });
  const activeCount = activeRunIds.size;
  const queuedCount = props.runQueue?.queued_count ?? 0;
  const completedCount =
    props.storageInventory?.runs.filter((run) => run.lifecycle_state === "completed").length ?? 0;
  return (
    <details className="run-monitor-panel" open={activeCount > 0 || queuedCount > 0}>
      <summary>
        <span>
          <strong>Run monitor</strong>
          <small>
            {activeCount.toLocaleString()} active · {queuedCount.toLocaleString()} queued ·{" "}
            {completedCount.toLocaleString()} completed
          </small>
        </span>
      </summary>
      <LocalRunWorkflowPanel {...props} />
    </details>
  );
}

function LocalRunWorkflowPanel({
  dryRun,
  runStatus,
  runQueue,
  runQueueStatus,
  error,
  lanWorkerConfig,
  lanWorkerStatus,
  lanWorkerError,
  lanWorkerActionStatus,
  ingestedResultId,
  storageInventory,
  storageStatus,
  storageError,
  runDeletePreview,
  runDeleteMessage,
  results,
  autoFinalizingWorkerRunIds,
  failedAutoFinalizingWorkerRunIds,
  onRefreshRunStatus,
  onLaunchLanWorkerRun,
  onRefreshLanWorkerStatus,
  onCollectLanWorkerRun,
  onCleanupLanWorkerRun,
  onIngestRun,
  onLaunchStoredRun,
  onLaunchStoredLanWorkerRun,
  onRefreshStoredLanWorkerStatus,
  onFinalizeStoredLanWorkerRun,
  onIngestStoredRun,
  onOpenInResults,
  onInspectIngested,
  onOpenStoredResult,
  onExploreStoredResult,
  onRefreshStorage,
  onPreviewRunDelete,
  onConfirmRunDelete,
}: LocalRunWorkflowPanelProps) {
  const stage = buildRunStage(dryRun, runStatus, ingestedResultId, lanWorkerStatus);
  const canIngestLocal =
    runStatus?.lifecycle_state === "completed" &&
    runStatus.product_state === "completed_cm1_result" &&
    !ingestedResultId;
  const canIngestLanWorker =
    lanWorkerStatus?.state === "ready_for_local_ingest" && !ingestedResultId;
  const canIngest = canIngestLocal || canIngestLanWorker;
  const outputCount = runStatus
    ? Object.values(runStatus.output_summary).reduce((total, value) => total + value, 0)
    : 0;
  const generatedInputNames = dryRun ? generatedInputSummary(dryRun) : [];
  const currentRunId = dryRun ? runIdFromPackage(dryRun) : null;
  const showRefreshButton = Boolean(dryRun && runStatus);
  const showIngestButton = Boolean(dryRun && canIngest);
  const showActionRow = showRefreshButton || showIngestButton;
  const packageObservedSounding = dryRun?.report.observed_sounding ?? null;
  const packageUserMetadata = dryRun?.report.user ?? null;

  return (
    <section
      className="status-panel local-run-panel"
      aria-labelledby="local-run-title"
      data-testid="package-review-panel"
    >
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Run management</p>
          <h3 id="local-run-title">Local run launchpad</h3>
        </div>
        <StatusBadge label={buildStageLabel(stage)} tone={buildStageTone(stage)} />
      </div>

      <div className="run-state-card package-setup-card">
        <div className="panel-heading-row">
          <div>
            <p className="eyebrow">Package status</p>
            <h4>{dryRun ? "Latest generated package" : "No generated package yet"}</h4>
          </div>
          <strong className="next-action">{buildStageLabel(stage)}</strong>
        </div>

        <p className="state-note">
          Package creation and queueing live at the end of the setup flow. This rail keeps the
          generated package, queue, ingest, worker, and cleanup state visible while you work.
        </p>

        {error && <p role="alert">{error}</p>}

        {dryRun ? (
          <>
            <dl className="compact-metrics">
              <Metric label="Run ID" value={runIdFromPackage(dryRun)} />
              {packageObservedSounding && (
                <>
                  <Metric label="Sounding" value={observedSoundingLabel(packageObservedSounding)} />
                  <Metric
                    label="Sounding location"
                    value={observedSoundingLocationLabel(packageObservedSounding)}
                  />
                </>
              )}
              {packageUserMetadata?.tags.length ? (
                <Metric label="Package tags" value={packageUserMetadata.tags.join(", ")} />
              ) : null}
              {packageUserMetadata?.notes ? (
                <Metric label="Package notes" value={packageUserMetadata.notes} />
              ) : null}
              <Metric label="Package path" value={dryRun.package_dir} />
              <Metric label="Manifest path" value={dryRun.manifest_path} />
              <Metric label="Expected output directory" value={dryRun.package_dir} />
              <Metric
                label="Generated inputs"
                value={
                  generatedInputNames.length > 0
                    ? generatedInputNames.join(", ")
                    : "No generated inputs reported"
                }
              />
              {dryRun.report.run_configuration_summary && (
                <>
                  <Metric
                    label="Generated grid"
                    value={runConfigurationSummaryGrid(dryRun.report.run_configuration_summary)}
                  />
                  <Metric
                    label="Runtime / saved frames"
                    value={runConfigurationSummaryTiming(dryRun.report.run_configuration_summary)}
                  />
                  <Metric
                    label="Estimated output volume"
                    value={runConfigurationSummaryMultiplier(
                      dryRun.report.run_configuration_summary,
                    )}
                  />
                </>
              )}
              <Metric
                label="CM1 executable / settings"
                value={
                  runStatus?.command.length
                    ? runStatus.command.join(" ")
                    : "Checked before CM1 starts"
                }
              />
              <Metric
                label="Current lifecycle state"
                value={runStatus ? userFacingRunWorkflowStatus(runStatus) : "Package ready"}
              />
            </dl>
            {dryRun.report.pre_run_validation_report && (
              <PreRunValidationReportPanel report={dryRun.report.pre_run_validation_report} />
            )}
            <p className="state-note">
              A generated package is not a completed CM1 result. Launch, output detection, ingest,
              and saved result review are separate states.
            </p>
            {dryRun.report.run_configuration_summary && (
              <p className="state-note">
                {dryRun.report.estimated_cost_or_size}{" "}
                {dryRun.report.run_configuration_summary.time_step_note}
              </p>
            )}
          </>
        ) : (
          <p>No package has been created from the current setup in this browser session.</p>
        )}

        {showActionRow && dryRun && (
          <div className="button-row">
            {showRefreshButton && (
              <button type="button" data-testid="refresh-status-btn" onClick={onRefreshRunStatus}>
                {stage === "running" || stage === "failed"
                  ? "View status / logs"
                  : "Refresh status"}
              </button>
            )}
            {showIngestButton && (
              <button
                type="button"
                data-testid="ingest-results-btn"
                onClick={onIngestRun}
                disabled={!canIngest}
              >
                Ingest completed output
              </button>
            )}
          </div>
        )}

        {dryRun && (
          <LanWorkerRunPanel
            configured={lanWorkerConfig?.configured ?? false}
            configMessage={lanWorkerConfig?.message ?? "Checking LAN worker setup."}
            cm1EnvKeys={lanWorkerConfig?.cm1_env_keys ?? []}
            cm1EnvSettings={lanWorkerConfig?.cm1_env_settings ?? []}
            status={lanWorkerStatus}
            actionStatus={lanWorkerActionStatus}
            error={lanWorkerError}
            ingestedResultId={ingestedResultId}
            canStart={false}
            onLaunch={onLaunchLanWorkerRun}
            onRefresh={onRefreshLanWorkerStatus}
            onCollect={onCollectLanWorkerRun}
            onCleanup={onCleanupLanWorkerRun}
          />
        )}

        <LocalRunQueuePanel queue={runQueue} status={runQueueStatus} />

        {runStatus ? (
          <div className="run-status-panel" aria-label="Local run status">
            <dl>
              <Metric label="Lifecycle state" value={humanize(runStatus.lifecycle_state)} />
              {runStatus.observed_sounding && (
                <>
                  <Metric
                    label="Sounding"
                    value={observedSoundingLabel(runStatus.observed_sounding)}
                  />
                  <Metric
                    label="Sounding location"
                    value={observedSoundingLocationLabel(runStatus.observed_sounding)}
                  />
                </>
              )}
              {runStatus.user?.tags.length ? (
                <Metric label="Run tags" value={runStatus.user.tags.join(", ")} />
              ) : null}
              {runStatus.user?.notes ? (
                <Metric label="Run notes" value={runStatus.user.notes} />
              ) : null}
              <Metric label="Product state" value={humanize(runStatus.product_state)} />
              <Metric label="Validation" value={humanize(runStatus.validation_status)} />
              <Metric label="Exit code" value={runStatus.exit_code?.toString() ?? "Running"} />
              <Metric label="Started" value={runStatus.started_at ?? "Not recorded"} />
              <Metric label="Finished" value={runStatus.finished_at ?? "Not finished"} />
              <Metric
                label={
                  runStatus.lifecycle_state === "completed"
                    ? "Final elapsed runtime"
                    : "Elapsed runtime"
                }
                value={elapsedRuntimeLabel(runStatus.progress)}
              />
              <Metric
                label="Model-time progress"
                value={modelTimeProgressLabel(runStatus.progress)}
              />
              <Metric label="ETA" value={runProgressEtaLabel(runStatus.progress)} />
              <Metric
                label="Last status refresh"
                value={runProgressRefreshLabel(runStatus.progress)}
              />
              <Metric label="Progress source" value={runProgressSourceLabel(runStatus.progress)} />
              <Metric label="stdout log" value={runStatus.stdout_log || "Unavailable"} />
              <Metric label="stderr log" value={runStatus.stderr_log || "Unavailable"} />
              <Metric
                label="Output summary"
                value={
                  outputCount > 0
                    ? `${runStatus.output_summary.netcdf_paths} NetCDF, ${runStatus.output_summary.raw_cm1_artifacts} raw CM1, ${runStatus.output_summary.processed_artifacts} processed`
                    : "No output artifacts detected yet"
                }
              />
            </dl>
            {runStatus.runtime_warnings.length > 0 && (
              <div>
                <h5>Runtime caveats</h5>
                <ul>
                  {runStatus.runtime_warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
            <RuntimeIntegritySummary runtimeIntegrity={runStatus.runtime_integrity ?? null} />
            {(runStatus.stdout_tail || runStatus.stderr_tail) && (
              <details>
                <summary>Latest log tail</summary>
                {runStatus.stdout_tail && (
                  <>
                    <h5>stdout</h5>
                    <pre>{runStatus.stdout_tail}</pre>
                  </>
                )}
                {runStatus.stderr_tail && (
                  <>
                    <h5>stderr</h5>
                    <pre>{runStatus.stderr_tail}</pre>
                  </>
                )}
              </details>
            )}
          </div>
        ) : (
          dryRun && (
            <p>
              Running uses the configured local CM1 install and preserves one local run at a time.
              If CM1 settings are missing, Cloud Chamber will stop before any CM1 process starts.
            </p>
          )
        )}

        {dryRun && (
          <details className="technical-details">
            <summary>Technical package details</summary>
            <dl className="compact-metrics">
              <Metric label="Scenario ID" value={dryRun.report.scenario_id} />
              <Metric label="Run configuration" value={dryRun.report.run_configuration.label} />
              <Metric label="Cost / size" value={dryRun.report.estimated_cost_or_size} />
              {dryRun.report.run_configuration_summary && (
                <>
                  <Metric
                    label="Output cadence"
                    value={`${dryRun.report.run_configuration_summary.output_cadence_seconds.toLocaleString()} s`}
                  />
                  <Metric
                    label="Model top"
                    value={`${(dryRun.report.run_configuration_summary.model_top_m / 1000).toLocaleString()} km`}
                  />
                  <Metric
                    label="Grid cells"
                    value={dryRun.report.run_configuration_summary.grid_cell_count.toLocaleString()}
                  />
                </>
              )}
              <Metric label="CM1 launched" value={dryRun.report.cm1_was_launched ? "Yes" : "No"} />
              <Metric
                label="Product state"
                value={humanize(dryRun.report.provenance.product_state)}
              />
              <Metric
                label="Expected diagnostics"
                value={dryRun.report.expected_diagnostics.join(", ")}
              />
            </dl>
            <h5>Generated files</h5>
            <ul>
              {Object.values(dryRun.report.generated_files).map((path) => (
                <li key={path}>{path.split("/").at(-1)}</li>
              ))}
            </ul>
            <p>{dryRun.report.physical_question}</p>
          </details>
        )}

        {ingestedResultId && (
          <div className="post-ingest-actions" aria-label="Ingested result actions">
            <p>Result metadata created: {ingestedResultId}</p>
            <div className="button-row">
              <button type="button" onClick={onOpenInResults}>
                Open in Results
              </button>
              <button type="button" onClick={onInspectIngested}>
                Open in Explore
              </button>
            </div>
          </div>
        )}
      </div>

      <LocalPipelinePanel
        inventory={storageInventory}
        status={storageStatus}
        error={storageError}
        deletePreview={runDeletePreview}
        deleteMessage={runDeleteMessage}
        results={results}
        currentRunId={currentRunId}
        runQueue={runQueue}
        lanWorkerConfigured={lanWorkerConfig?.configured ?? false}
        autoFinalizingWorkerRunIds={autoFinalizingWorkerRunIds}
        failedAutoFinalizingWorkerRunIds={failedAutoFinalizingWorkerRunIds}
        onLaunchStoredRun={onLaunchStoredRun}
        onLaunchStoredLanWorkerRun={onLaunchStoredLanWorkerRun}
        onRefreshStoredLanWorkerStatus={onRefreshStoredLanWorkerStatus}
        onFinalizeStoredLanWorkerRun={onFinalizeStoredLanWorkerRun}
        onIngestStoredRun={onIngestStoredRun}
        onOpenStoredResult={onOpenStoredResult}
        onExploreStoredResult={onExploreStoredResult}
        onRefreshStorage={onRefreshStorage}
        onPreviewDelete={onPreviewRunDelete}
        onConfirmDelete={onConfirmRunDelete}
      />
    </section>
  );
}

function LocalRunQueuePanel({ queue, status }: { queue: RunQueueResponse | null; status: string }) {
  const visibleEntries = visibleRunQueueEntries(queue);
  return (
    <section className="run-status-panel" aria-label="Local serial run queue">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Local serial queue</p>
          <h5>Local CM1 queue</h5>
        </div>
        <StatusBadge
          label={queue?.active_run_id ? "Running one package" : "Queue idle"}
          tone={queue?.active_run_id ? "neutral" : "good"}
        />
      </div>
      <p className="state-note">{status}</p>
      {queue && (
        <dl className="compact-metrics">
          <Metric label="Active run" value={queue.active_run_id ?? "None"} />
          <Metric label="Waiting" value={queue.queued_count.toLocaleString()} />
          <Metric label="Last queue refresh" value={formatShortTime(queue.updated_at)} />
        </dl>
      )}
      {visibleEntries.length > 0 ? (
        <ol className="queue-list">
          {visibleEntries.map((entry) => (
            <li key={`${entry.run_id}-${entry.queued_at}`}>
              <strong>{entry.run_id}</strong>{" "}
              <span className="muted-inline">{runQueueEntryLabel(entry)}</span>
              {entry.result_id && <span className="muted-inline"> result {entry.result_id}</span>}
              {entry.cleanup_status && (
                <span className="muted-inline"> package retained for Results/Explore</span>
              )}
            </li>
          ))}
        </ol>
      ) : (
        <p className="state-note">
          Queue local CM1 runs from package cards. Cloud Chamber starts the next package only after
          the active run reaches terminal status.
        </p>
      )}
    </section>
  );
}

function visibleRunQueueEntries(queue: RunQueueResponse | null): RunQueueEntry[] {
  if (!queue) return [];
  const newestFirst = [...queue.entries].reverse();
  const activeOrQueued = newestFirst.filter((entry) => queueEntryIsOpen(entry));
  const recentResultBacked = newestFirst.filter((entry) => queueEntryHasIngestedResult(entry));
  if (queue.active_run_id || activeOrQueued.length > 0) {
    const seen = new Set<string>();
    return [...activeOrQueued, ...recentResultBacked.slice(0, 3)]
      .filter((entry) => {
        if (seen.has(entry.run_id)) return false;
        seen.add(entry.run_id);
        return true;
      })
      .slice(0, 5);
  }
  return recentResultBacked.slice(0, 5);
}

function LanWorkerRunPanel({
  configured,
  configMessage,
  cm1EnvKeys,
  cm1EnvSettings,
  status,
  actionStatus,
  error,
  ingestedResultId,
  canStart,
  onLaunch,
  onRefresh,
  onCollect,
  onCleanup,
}: {
  configured: boolean;
  configMessage: string;
  cm1EnvKeys: string[];
  cm1EnvSettings: string[];
  status: LanWorkerRunResponse | null;
  actionStatus: string | null;
  error: string | null;
  ingestedResultId: string | null;
  canStart: boolean;
  onLaunch: () => void;
  onRefresh: () => void;
  onCollect: () => void;
  onCleanup: () => void;
}) {
  const canCollect = status?.state === "completed" && Boolean(error);
  const cleanupComplete = status?.state === "worker_cleanup_complete";
  const cleanupFailed = status?.state === "worker_cleanup_failed";
  const cleanupAvailable =
    Boolean(ingestedResultId) &&
    Boolean(status) &&
    !cleanupComplete &&
    status?.state !== "running" &&
    status?.state !== "completed";

  return (
    <section className="run-status-panel lan-worker-panel" aria-label="LAN worker run status">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Trusted LAN worker</p>
          <h5>LAN worker status</h5>
        </div>
        <StatusBadge
          label={
            status ? lanWorkerStatusLabel(status) : configured ? "Configured" : "Not configured"
          }
          tone={lanWorkerTone(status, configured)}
        />
      </div>

      <p className="state-note">
        {configured
          ? status
            ? "Use the LAN worker as a compute appliance. Copy completed output back, ingest locally, then clean up the worker copy."
            : "Use Package and queue to start this package on the LAN worker. This panel tracks worker progress, copy-back, ingest, and cleanup after launch."
          : "LAN worker execution is unavailable until an ignored local worker config is present."}
      </p>
      {!configured && <p className="state-note">{configMessage}</p>}
      {error && <p role="alert">{error}</p>}
      {actionStatus && <p role="status">{actionStatus}</p>}

      {configured && (
        <>
          <dl className="compact-metrics">
            <Metric label="Worker state" value={status ? lanWorkerStatusLabel(status) : "Ready"} />
            <Metric
              label="Worker output"
              value={
                status
                  ? `${status.netcdf_count ?? 0} NetCDF, ${status.raw_artifact_count ?? 0} raw CM1`
                  : "Not started"
              }
            />
            <Metric
              label="Worker runtime settings"
              value={
                cm1EnvSettings.length > 0
                  ? cm1EnvSettings.join(", ")
                  : cm1EnvKeys.length > 0
                    ? cm1EnvKeys.join(", ")
                    : "Default worker environment"
              }
            />
            {status && (
              <Metric
                label="Worker model-time progress"
                value={modelTimeProgressLabel(status.progress ?? null)}
              />
            )}
            {status && <Metric label="Worker ETA" value={runProgressEtaLabel(status.progress)} />}
            {status && (
              <Metric
                label="Worker status refresh"
                value={runProgressRefreshLabel(status.progress)}
              />
            )}
            {status?.message && <Metric label="Worker message" value={status.message} />}
          </dl>
          <div className="button-row">
            {!status && canStart && (
              <button type="button" className="secondary-button" onClick={onLaunch}>
                Run on LAN worker
              </button>
            )}
            {status && status.state !== "worker_cleanup_complete" && (
              <button type="button" className="secondary-button" onClick={onRefresh}>
                Refresh LAN worker status
              </button>
            )}
            {canCollect && (
              <button type="button" onClick={onCollect}>
                Retry copy-back and ingest
              </button>
            )}
            {cleanupAvailable && (
              <button type="button" onClick={onCleanup}>
                {cleanupFailed ? "Retry LAN worker cleanup" : "Clean up LAN worker copy"}
              </button>
            )}
          </div>
          {status?.state === "ready_for_local_ingest" && !ingestedResultId && (
            <p className="state-note">
              Worker output is now on this MacBook. Cloud Chamber will ingest it locally and clean
              up the worker copy after ingest succeeds.
            </p>
          )}
          {cleanupComplete && (
            <p className="state-note">
              LAN worker cleanup complete. Results and Explore use the MacBook-local copy.
            </p>
          )}
        </>
      )}
    </section>
  );
}

function LocalPipelinePanel({
  inventory,
  status,
  error,
  deletePreview,
  deleteMessage,
  results,
  currentRunId,
  runQueue,
  lanWorkerConfigured,
  autoFinalizingWorkerRunIds,
  failedAutoFinalizingWorkerRunIds,
  onLaunchStoredRun,
  onLaunchStoredLanWorkerRun,
  onRefreshStoredLanWorkerStatus,
  onFinalizeStoredLanWorkerRun,
  onIngestStoredRun,
  onOpenStoredResult,
  onExploreStoredResult,
  onRefreshStorage,
  onPreviewDelete,
  onConfirmDelete,
}: {
  inventory: StorageInventoryResponse | null;
  status: string;
  error: string | null;
  deletePreview: DeleteRunResponse | null;
  deleteMessage: string | null;
  results: ResultCard[];
  currentRunId: string | null;
  runQueue: RunQueueResponse | null;
  lanWorkerConfigured: boolean;
  autoFinalizingWorkerRunIds: Set<string>;
  failedAutoFinalizingWorkerRunIds: Set<string>;
  onLaunchStoredRun: (manifestPath: string) => void;
  onLaunchStoredLanWorkerRun: (manifestPath: string) => void;
  onRefreshStoredLanWorkerStatus: (manifestPath: string) => void;
  onFinalizeStoredLanWorkerRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onRefreshStorage: () => void;
  onPreviewDelete: (runId: string) => void;
  onConfirmDelete: (runId: string) => void;
}) {
  const runs = selectPipelineRuns(inventory?.runs ?? [], results, currentRunId, runQueue);
  const panelStatus = localPipelinePanelStatus(status, runQueue);

  return (
    <section className="pipeline-panel" aria-labelledby="pipeline-title">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Build pipeline</p>
          <h4 id="pipeline-title">Packages and runs needing action</h4>
        </div>
        <StatusBadge label={panelStatus} tone={error ? "warning" : "neutral"} />
      </div>
      <p className="state-note">
        Active packages and runs that still need launch, status review, troubleshooting, or ingest.
        Ingested results live in Results; non-ingested package and run cleanup stays here.
      </p>
      {error && <p role="alert">{error}</p>}
      {deleteMessage && <p role="status">{deleteMessage}</p>}
      <div className="button-row">
        <button type="button" className="secondary-button" onClick={onRefreshStorage}>
          Refresh runs
        </button>
      </div>

      {deletePreview && (
        <section className="delete-preview" aria-label="Local run delete preview">
          <h5>Delete local package/run data preview</h5>
          <p>
            Cleanup removes local generated package files, copied runtime files, CM1 output/logs if
            present, and local sidecars stored under this run directory. It does not touch Results
            entries, the source repo, the runtime home itself, or the external CM1 install. No files
            have been deleted yet.
          </p>
          <dl className="metric-grid">
            <Metric label="Run ID" value={deletePreview.run_id} />
            <Metric label="Selected path" value={deletePreview.run_directory} />
            <Metric label="Estimated reclaimed" value={formatBytes(deletePreview.size_bytes)} />
            <Metric label="Preview status" value={deletePreview.message} />
          </dl>
          <button
            type="button"
            className="danger-button"
            onClick={() => onConfirmDelete(deletePreview.run_id)}
          >
            Confirm delete local run data
          </button>
        </section>
      )}

      {runs.length === 0 ? (
        <p>
          No active or incomplete packages/runs need Build action. Ingested experiments are managed
          in Results.
        </p>
      ) : (
        <div className="pipeline-run-list" aria-label="Local packages and runs">
          {runs.map((run, index) => (
            <PipelineRunCard
              key={`${run.run_id}-${run.path ?? run.manifest_path ?? index}`}
              run={run}
              result={resultForRun(results, run.run_id)}
              current={run.run_id === currentRunId}
              queueEntry={queueEntryForRun(runQueue, run.run_id)}
              lanWorkerConfigured={lanWorkerConfigured}
              autoFinalizing={autoFinalizingWorkerRunIds.has(run.run_id)}
              autoFinalizeFailed={failedAutoFinalizingWorkerRunIds.has(run.run_id)}
              onLaunchStoredRun={onLaunchStoredRun}
              onLaunchStoredLanWorkerRun={onLaunchStoredLanWorkerRun}
              onRefreshStoredLanWorkerStatus={onRefreshStoredLanWorkerStatus}
              onFinalizeStoredLanWorkerRun={onFinalizeStoredLanWorkerRun}
              onIngestStoredRun={onIngestStoredRun}
              onOpenStoredResult={onOpenStoredResult}
              onExploreStoredResult={onExploreStoredResult}
              onPreviewDelete={onPreviewDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function PipelineRunCard({
  run,
  result,
  current,
  queueEntry,
  lanWorkerConfigured,
  autoFinalizing,
  autoFinalizeFailed,
  onLaunchStoredRun,
  onLaunchStoredLanWorkerRun,
  onRefreshStoredLanWorkerStatus,
  onFinalizeStoredLanWorkerRun,
  onIngestStoredRun,
  onOpenStoredResult,
  onExploreStoredResult,
  onPreviewDelete,
}: {
  run: RunStorageEntry;
  result: ResultCard | undefined;
  current: boolean;
  queueEntry: RunQueueEntry | undefined;
  lanWorkerConfigured: boolean;
  autoFinalizing: boolean;
  autoFinalizeFailed: boolean;
  onLaunchStoredRun: (manifestPath: string) => void;
  onLaunchStoredLanWorkerRun: (manifestPath: string) => void;
  onRefreshStoredLanWorkerStatus: (manifestPath: string) => void;
  onFinalizeStoredLanWorkerRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onPreviewDelete: (runId: string) => void;
}) {
  const displayName = result?.name ?? run.scenario_name ?? run.scenario_id ?? run.run_id;
  const canLaunch = Boolean(
    run.manifest_path &&
    run.category === "dry_run_only" &&
    !run.worker_state &&
    !queueEntryIsOpen(queueEntry),
  );
  const canRefreshWorker = Boolean(run.manifest_path && run.worker_state === "running");
  const canFinalizeWorker = Boolean(
    run.manifest_path && run.worker_state === "completed" && !result && autoFinalizeFailed,
  );
  const queueAutoIngested = Boolean(queueEntry?.state === "ingested" && queueEntry.result_id);
  const queueOpen = queueEntryIsOpen(queueEntry);
  const resultPending = queueOpen || run.category === "running" || run.worker_state === "running";
  const resultId = result?.result_id ?? queueEntry?.result_id ?? null;
  const resultBacked = Boolean(result || queueEntryHasIngestedResult(queueEntry));
  const canIngest = Boolean(
    run.manifest_path &&
    !resultBacked &&
    (run.category === "completed_with_output" || run.worker_state === "ready_for_local_ingest"),
  );
  const stateLabel =
    queueAutoIngested && !result ? "Auto-ingested" : pipelineRunStateLabel(run, result);
  const stateTone = resultBacked ? "good" : pipelineRunTone(run, result);
  const nextStep =
    queueAutoIngested && !result
      ? "Result auto-ingested. The run directory is retained because it backs Results and Explore."
      : pipelineRunNextStep(run, result);
  const showWorkerMessage = Boolean(run.worker_message && !run.worker_state);
  const runProgress = pipelineRunProgressSummary(run);
  const workerProgress = workerProgressSummary(run);

  return (
    <article className={current ? "pipeline-run-card current" : "pipeline-run-card"}>
      <div className="panel-heading-row">
        <div>
          <h5>{displayName}</h5>
          <small>{run.run_id}</small>
        </div>
        {current && <StatusBadge label="Current package" tone="neutral" />}
      </div>
      <div className="badge-row">
        <StatusBadge label={stateLabel} tone={stateTone} />
        {queueEntry && queueEntry.state !== "ingested" && (
          <StatusBadge
            label={runQueueEntryLabel(queueEntry)}
            tone={runQueueEntryTone(queueEntry)}
          />
        )}
        {!resultBacked && resultPending && <StatusBadge label="Result pending" tone="neutral" />}
        {!resultBacked && !resultPending && <StatusBadge label="Not ingested" tone="neutral" />}
      </div>
      <p>
        {humanize(result?.scenario_id ?? run.scenario_id ?? "unknown scenario")} ·{" "}
        {result
          ? resultRunConfigurationLabel(result.run_configuration)
          : runConfigurationLabel(run.run_configuration)}
      </p>
      <p className="state-note">
        {pipelineRunOutputSummary(run, result)} · Local package {formatBytes(run.size_bytes)}
      </p>
      {runProgress && <p className="state-note">{runProgress}</p>}
      {workerProgress && <p className="state-note">{workerProgress}</p>}
      {showWorkerMessage && <p className="state-note">{run.worker_message}</p>}
      {queueEntry?.message && <p className="state-note">{queueEntry.message}</p>}
      {queueEntry?.error && (
        <p className="state-note" role="alert">
          {queueEntry.error}
        </p>
      )}
      {autoFinalizing && (
        <p className="state-note" role="status">
          Copying worker output back and ingesting locally.
        </p>
      )}
      {autoFinalizeFailed && (
        <p className="state-note" role="alert">
          Automatic copy-back or ingest failed. Retry when the backend and worker are reachable.
        </p>
      )}
      <p className="state-note">{nextStep}</p>
      <div className="button-row">
        {canLaunch && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onLaunchStoredRun(run.manifest_path!)}
          >
            Queue local CM1 run
          </button>
        )}
        {canLaunch && lanWorkerConfigured && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onLaunchStoredLanWorkerRun(run.manifest_path!)}
          >
            Run on LAN worker
          </button>
        )}
        {canRefreshWorker && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onRefreshStoredLanWorkerStatus(run.manifest_path!)}
          >
            Refresh LAN worker status
          </button>
        )}
        {canFinalizeWorker && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onFinalizeStoredLanWorkerRun(run.manifest_path!)}
          >
            Retry copy-back and ingest
          </button>
        )}
        {canIngest && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onIngestStoredRun(run.manifest_path!)}
          >
            Ingest output
          </button>
        )}
        {resultId && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onOpenStoredResult(resultId)}
          >
            Open result
          </button>
        )}
        {resultId && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onExploreStoredResult(resultId)}
          >
            Open in Explore
          </button>
        )}
        {!resultBacked && (
          <button
            type="button"
            className="secondary-button"
            disabled={!canPreviewDelete(run)}
            onClick={() => onPreviewDelete(run.run_id)}
          >
            Preview cleanup
          </button>
        )}
      </div>
      {!resultBacked && !canPreviewDelete(run) && <small>{deleteDisabledReason(run)}</small>}
    </article>
  );
}

function localPipelinePanelStatus(status: string, runQueue: RunQueueResponse | null): string {
  if (runQueue?.active_run_id && runQueue.queued_count > 0) return "CM1 running; queue waiting";
  if (runQueue?.active_run_id) return "CM1 running";
  if (runQueue && runQueue.queued_count > 0) return "Local runs queued";
  return status;
}

function buildRunStage(
  dryRun: DryRunResponse | null,
  runStatus: RunStatusResponse | null,
  ingestedResultId: string | null,
  lanWorkerStatus: LanWorkerRunResponse | null,
): BuildRunStage {
  if (ingestedResultId && lanWorkerStatus?.state === "worker_cleanup_complete") {
    return "worker_cleanup_complete";
  }
  if (ingestedResultId && lanWorkerStatus?.state === "worker_cleanup_failed") {
    return "worker_cleanup_failed";
  }
  if (ingestedResultId && lanWorkerStatus) return "worker_cleanup_pending";
  if (ingestedResultId) return "ingested";
  if (!dryRun) return "not_packaged";
  if (lanWorkerStatus?.state === "running") return "lan_worker_running";
  if (lanWorkerStatus?.state === "completed") return "lan_worker_completed";
  if (lanWorkerStatus?.state === "ready_for_local_ingest") return "ready_for_local_ingest";
  if (lanWorkerStatus?.state === "failed" || lanWorkerStatus?.state === "completed_no_output") {
    return "failed";
  }
  if (!runStatus) return "package_ready";
  if (runStatus.lifecycle_state === "queued" || runStatus.lifecycle_state === "running") {
    return "running";
  }
  if (runStatus.lifecycle_state === "completed") return "completed";
  if (runStatus.lifecycle_state === "failed" || runStatus.lifecycle_state === "canceled") {
    return "failed";
  }
  return "package_ready";
}

function buildStageLabel(stage: BuildRunStage): string {
  const labels: Record<BuildRunStage, string> = {
    not_packaged: "Not packaged yet",
    package_ready: "Package ready",
    lan_worker_running: "Running on LAN worker",
    lan_worker_completed: "Ready to copy back",
    ready_for_local_ingest: "Ready to ingest",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    ingested: "Ingested",
    worker_cleanup_pending: "Cleanup pending",
    worker_cleanup_complete: "Worker cleanup complete",
    worker_cleanup_failed: "Cleanup retry needed",
  };
  return labels[stage];
}

function buildStageTone(stage: BuildRunStage): "good" | "warning" | "neutral" {
  if (stage === "completed" || stage === "ingested") return "good";
  if (stage === "ready_for_local_ingest" || stage === "worker_cleanup_complete") return "good";
  if (stage === "failed" || stage === "worker_cleanup_failed") return "warning";
  return "neutral";
}

function lanWorkerStatusLabel(status: LanWorkerRunResponse): string {
  const labels: Record<string, string> = {
    running: "Running CM1 on LAN worker",
    completed: "Worker completed with output",
    completed_no_output: "Worker completed with no output",
    failed: "LAN worker failed",
    copied_back_to_mac: "Copied back to MacBook",
    ready_for_local_ingest: "Completed output ready to ingest",
    worker_cleanup_pending: "Worker cleanup pending",
    worker_cleanup_complete: "LAN worker cleanup complete",
    worker_cleanup_failed: "LAN worker cleanup failed",
  };
  return labels[status.state] ?? humanize(status.state);
}

function lanWorkerTone(
  status: LanWorkerRunResponse | null,
  configured: boolean,
): "good" | "warning" | "neutral" {
  if (!configured) return "neutral";
  if (!status) return "neutral";
  if (
    status.state === "completed" ||
    status.state === "ready_for_local_ingest" ||
    status.state === "worker_cleanup_complete"
  ) {
    return "good";
  }
  if (
    status.state === "failed" ||
    status.state === "completed_no_output" ||
    status.state === "worker_cleanup_failed"
  ) {
    return "warning";
  }
  return "neutral";
}

function runQueueSummary(queue: RunQueueResponse): string {
  if (queue.active_run_id && queue.queued_count > 0) {
    return `Running ${queue.active_run_id}; ${queue.queued_count.toLocaleString()} queued.`;
  }
  if (queue.active_run_id) return `Running ${queue.active_run_id}.`;
  if (queue.queued_count > 0) return `${queue.queued_count.toLocaleString()} local runs queued.`;
  const latest = queue.entries.at(-1);
  if (latest?.state === "ingested" && latest.result_id) {
    return `Auto-ingested ${latest.result_id}; queue idle.`;
  }
  if (latest?.state === "ingest_failed") return "Auto-ingest needs manual retry.";
  if (latest?.state === "launch_failed") return "Local queue launch blocked.";
  return "Local run queue idle.";
}

function runQueuePollingKey(queue: RunQueueResponse | null): string {
  if (!queue) return "none";
  return queue.entries
    .map((entry) => `${entry.run_id}:${entry.state}:${entry.updated_at}`)
    .join("|");
}

function runQueueHasOpenEntries(queue: RunQueueResponse | null): boolean {
  return Boolean(queue?.entries.some((entry) => queueEntryIsOpen(entry)));
}

function queueEntryIsOpen(entry: RunQueueEntry | undefined): boolean {
  return Boolean(entry && (entry.state === "queued" || entry.state === "running"));
}

function queueEntryHasIngestedResult(entry: RunQueueEntry | undefined): boolean {
  return Boolean(entry?.state === "ingested" && entry.result_id);
}

function latestAutoIngestedQueueEntry(queue: RunQueueResponse): RunQueueEntry | undefined {
  return [...queue.entries].reverse().find((entry) => queueEntryHasIngestedResult(entry));
}

function queueEntryForRun(
  queue: RunQueueResponse | null,
  runId: string,
): RunQueueEntry | undefined {
  return queue?.entries.find((entry) => entry.run_id === runId);
}

function runQueueEntryLabel(entry: RunQueueEntry): string {
  const labels: Record<string, string> = {
    queued: "Queued",
    running: "Running in serial queue",
    ingested: "Auto-ingested",
    ingest_failed: "Auto-ingest failed",
    completed_no_output: "Completed with no ingestable output",
    failed: "Run failed",
    canceled: "Canceled",
    launch_failed: "Launch failed",
  };
  return labels[entry.state] ?? humanize(entry.state);
}

function runQueueEntryTone(entry: RunQueueEntry): "good" | "warning" | "neutral" {
  if (entry.state === "ingested") return "good";
  if (
    entry.state === "ingest_failed" ||
    entry.state === "completed_no_output" ||
    entry.state === "failed" ||
    entry.state === "canceled" ||
    entry.state === "launch_failed"
  ) {
    return "warning";
  }
  return "neutral";
}

function generatedInputSummary(dryRun: DryRunResponse): string[] {
  return Object.values(dryRun.report.generated_files)
    .map((path) => path.split("/").at(-1) ?? path)
    .filter((name) => name === "namelist.input" || name === "input_sounding");
}

function selectPipelineRuns(
  runs: RunStorageEntry[],
  results: ResultCard[],
  currentRunId: string | null,
  runQueue: RunQueueResponse | null,
): RunStorageEntry[] {
  const queueHasOpenEntries = runQueueHasOpenEntries(runQueue);
  const queueBusy = Boolean(runQueue?.active_run_id || queueHasOpenEntries);
  const activeRuns = runs.filter((run) => {
    const queueEntry = queueEntryForRun(runQueue, run.run_id);
    if (currentRunId && run.run_id === currentRunId) return true;
    if (queueEntryIsOpen(queueEntry)) return true;
    if (queueBusy) return run.category === "running";
    if (resultForRun(results, run.run_id)) return false;
    if (queueEntryHasIngestedResult(queueEntry)) return false;
    if (queueHasOpenEntries && queueEntry && !queueEntryIsOpen(queueEntry)) return false;
    return [
      "dry_run_only",
      "running",
      "completed_with_output",
      "completed_no_output",
      "failed",
      "canceled",
      "missing_manifest",
      "malformed_manifest",
      "unknown",
    ].includes(run.category);
  });
  const sorted = [...activeRuns].sort((left, right) => {
    if (currentRunId) {
      if (left.run_id === currentRunId) return -1;
      if (right.run_id === currentRunId) return 1;
    }
    const leftTime = Date.parse(left.updated_at ?? left.created_at ?? "");
    const rightTime = Date.parse(right.updated_at ?? right.created_at ?? "");
    return (
      (Number.isFinite(rightTime) ? rightTime : 0) - (Number.isFinite(leftTime) ? leftTime : 0)
    );
  });
  return sorted.slice(0, 6);
}

function pipelineRunStateLabel(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result) return "Ready to review";
  if (run.worker_state) {
    return lanWorkerStatusLabel({
      run_id: run.run_id,
      state: run.worker_state,
      message: run.worker_message,
      started_at: run.worker_started_at,
      finished_at: run.worker_finished_at,
      netcdf_count: run.worker_netcdf_count ?? 0,
      raw_artifact_count: run.worker_raw_artifact_count ?? 0,
    });
  }
  const labels: Record<string, string> = {
    dry_run_only: "Ready to run",
    running: "Running",
    completed_with_output: "Ready to ingest",
    completed_no_output: "Completed with no output",
    failed: "Failed",
    canceled: "Canceled",
    missing_manifest: "Missing manifest",
    malformed_manifest: "Manifest problem",
    saved_or_protected: "Cleanup review",
    unknown: "Needs review",
  };
  return labels[run.category] ?? humanize(run.category);
}

function pipelineRunTone(
  run: RunStorageEntry,
  result: ResultCard | undefined,
): "good" | "warning" | "neutral" {
  if (result?.saved || result?.protected || result) return "good";
  if (run.worker_state) {
    return lanWorkerTone(
      {
        run_id: run.run_id,
        state: run.worker_state,
        message: run.worker_message,
        started_at: run.worker_started_at,
        finished_at: run.worker_finished_at,
        netcdf_count: run.worker_netcdf_count ?? 0,
        raw_artifact_count: run.worker_raw_artifact_count ?? 0,
      },
      true,
    );
  }
  if (run.category === "completed_with_output") return "good";
  if (
    run.category === "failed" ||
    run.category === "canceled" ||
    run.category === "completed_no_output" ||
    run.category === "missing_manifest" ||
    run.category === "malformed_manifest"
  ) {
    return "warning";
  }
  return "neutral";
}

function pipelineRunNextStep(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result) return "Review and local result cleanup are available in Results.";
  if (run.worker_state === "running")
    return "CM1 is running on the LAN worker; refresh runs for status.";
  if (run.worker_state === "completed") {
    return "LAN worker output is complete; Cloud Chamber will copy it back, ingest locally, and clean up the worker copy.";
  }
  if (run.worker_state === "ready_for_local_ingest") {
    return "Worker output is on this MacBook; ingest it locally before worker cleanup.";
  }
  if (run.worker_message) return run.worker_message;
  if (run.category === "dry_run_only") return "Ready to run after CM1 checks.";
  if (run.category === "running") return "CM1 is active or queued; refresh runs for status.";
  if (run.category === "completed_with_output") {
    return "CM1 output exists; ingest it to create a notebook result.";
  }
  if (run.category === "completed_no_output") {
    return "CM1 completed without usable output; inspect logs or clean up safely.";
  }
  if (run.category === "failed" || run.category === "canceled") {
    return "Run did not complete; inspect logs or clean up safely.";
  }
  if (run.category === "missing_manifest" || run.category === "malformed_manifest") {
    return "Run directory needs cleanup review before trusting it.";
  }
  return "Review the local run state before cleanup.";
}

function pipelineRunProgressSummary(run: RunStorageEntry): string | null {
  if (!run.worker_state && run.category === "dry_run_only") return null;
  const progress = run.worker_state ? run.worker_progress : run.progress;
  if (!progress) return null;
  const parts = [modelTimeProgressLabel(progress)];
  const eta = runProgressEtaLabel(progress);
  if (eta !== "Unavailable") parts.push(eta);
  const refresh = runProgressRefreshLabel(progress);
  if (refresh !== "Unavailable") parts.push(`Last refreshed ${refresh}`);
  return parts.join(" · ");
}

function workerProgressSummary(run: RunStorageEntry): string | null {
  if (!run.worker_state) return null;
  if (run.worker_progress) return null;
  const parts: string[] = [];
  if (run.worker_status_updated_at) {
    parts.push(`Last checked ${formatShortTime(run.worker_status_updated_at)}`);
  }
  if (run.worker_state === "running") {
    const estimate = workerEstimatedFinish(run);
    if (estimate) parts.push(estimate);
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}

function workerEstimatedFinish(run: RunStorageEntry): string | null {
  if (!run.worker_started_at) return null;
  const expectedFrames = run.run_configuration?.cm1_values.expected_output_frames ?? null;
  if (!expectedFrames) return null;
  const netcdfCount = run.worker_netcdf_count ?? 0;
  const observedModelFrames = Math.max(0, netcdfCount - 1);
  if (observedModelFrames < 2 || observedModelFrames >= expectedFrames) return null;
  const startedAt = Date.parse(run.worker_started_at);
  if (!Number.isFinite(startedAt)) return null;
  const elapsedMs = Date.now() - startedAt;
  if (elapsedMs <= 0) return null;
  const totalMs = (elapsedMs / observedModelFrames) * expectedFrames;
  const remainingMs = totalMs - elapsedMs;
  if (!Number.isFinite(remainingMs) || remainingMs <= 0) return null;
  return `Approx finish ${formatDurationFromNow(remainingMs)} (${observedModelFrames}/${expectedFrames} output frames)`;
}

function elapsedRuntimeLabel(progress: RunProgressResponse | null | undefined): string {
  return formatRunDuration(progress?.elapsed_wall_seconds);
}

function modelTimeProgressLabel(progress: RunProgressResponse | null | undefined): string {
  if (!progress) return "Model-time progress unavailable from current status.";
  const modelTime = progress.model_time_seconds;
  const totalTime = progress.total_model_time_seconds;
  const percent = progress.percent_complete;
  if (isFiniteNumber(modelTime) && isFiniteNumber(totalTime)) {
    const percentText = isFiniteNumber(percent) ? ` (${percent.toFixed(1)}%)` : "";
    return `${formatModelTime(modelTime)} / ${formatModelTime(totalTime)}${percentText}`;
  }
  if (isFiniteNumber(modelTime)) return `${formatModelTime(modelTime)} reached`;
  if (isFiniteNumber(totalTime)) {
    return `${progress.unavailable_reason ?? "Latest model time unavailable."} Total ${formatModelTime(totalTime)}.`;
  }
  return progress.unavailable_reason ?? "Model-time progress unavailable from current status.";
}

function runProgressEtaLabel(progress: RunProgressResponse | null | undefined): string {
  if (!progress || !isFiniteNumber(progress.estimated_remaining_wall_seconds)) {
    return "Unavailable";
  }
  const finish = progress.estimated_finish_at
    ? `; finish about ${formatShortTime(progress.estimated_finish_at)}`
    : "";
  return `${formatRunDuration(progress.estimated_remaining_wall_seconds)} remaining${finish}`;
}

function runProgressRefreshLabel(progress: RunProgressResponse | null | undefined): string {
  if (!progress?.last_refreshed_at) return "Unavailable";
  const stale = progress.stale || isProgressRefreshStale(progress);
  return `${formatShortTime(progress.last_refreshed_at)}${stale ? " (stale)" : ""}`;
}

function runProgressSourceLabel(progress: RunProgressResponse | null | undefined): string {
  if (!progress) return "Unavailable";
  const sources = [progress.model_time_source, progress.total_model_time_source].filter(Boolean);
  const caveats = progress.caveats ?? [];
  if (sources.length === 0 && caveats.length === 0) return "Unavailable";
  return [...sources, ...caveats].join("; ");
}

function formatRunDuration(seconds: number | null | undefined): string {
  if (!isFiniteNumber(seconds)) return "Unavailable";
  const roundedSeconds = Math.max(0, Math.round(seconds));
  const hours = Math.floor(roundedSeconds / 3600);
  const minutes = Math.floor((roundedSeconds % 3600) / 60);
  const remainingSeconds = roundedSeconds % 60;
  if (hours > 0) {
    return `${hours} hr ${minutes} min`;
  }
  if (minutes > 0) {
    return remainingSeconds > 0 ? `${minutes} min ${remainingSeconds} s` : `${minutes} min`;
  }
  return `${remainingSeconds} s`;
}

function formatModelTime(seconds: number): string {
  const minutes = seconds / 60;
  if (minutes >= 1) {
    const rounded = Math.abs(minutes - Math.round(minutes)) < 0.05 ? Math.round(minutes) : minutes;
    return `${rounded.toLocaleString(undefined, { maximumFractionDigits: 1 })} min`;
  }
  return `${Math.round(seconds)} s`;
}

function isProgressRefreshStale(progress: RunProgressResponse): boolean {
  if (!progress.last_refreshed_at || progress.percent_complete === 100) return false;
  const refreshedAt = Date.parse(progress.last_refreshed_at);
  if (!Number.isFinite(refreshedAt)) return false;
  return Date.now() - refreshedAt > 15 * 60 * 1000;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatShortTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });
}

function formatDurationFromNow(durationMs: number): string {
  const totalMinutes = Math.max(1, Math.round(durationMs / 60000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours <= 0) return `in about ${minutes} min`;
  if (minutes === 0) return `in about ${hours} hr`;
  return `in about ${hours} hr ${minutes} min`;
}

function selectedControlOption(
  control: ScenarioControl,
  controls: Record<string, string | number | boolean>,
): ControlOption | undefined {
  const value = String(controls[control.id] ?? control.default);
  return control.options.find((option) => option.value === value);
}

function ResultsFilterBar({
  filters,
  scenarioOptions,
  totalCount,
  visibleCount,
  onChange,
  onReset,
}: {
  filters: ResultsFilterState;
  scenarioOptions: Array<{ value: string; label: string }>;
  totalCount: number;
  visibleCount: number;
  onChange: (filters: ResultsFilterState) => void;
  onReset: () => void;
}) {
  const update = (patch: Partial<ResultsFilterState>) => onChange({ ...filters, ...patch });

  return (
    <section className="results-filter-bar" aria-label="Filter and sort results">
      <div className="results-filter-summary">
        <p>
          Showing <strong>{visibleCount}</strong> of <strong>{totalCount}</strong> notebook entries
        </p>
        <button
          type="button"
          className="secondary-button"
          onClick={onReset}
          disabled={!resultsFiltersActive(filters)}
        >
          Clear filters
        </button>
      </div>
      <div className="results-filter-grid">
        <label>
          Search
          <input
            value={filters.search}
            onChange={(event) => update({ search: event.target.value })}
            placeholder="name, run, scenario, tag, station"
          />
        </label>
        <label>
          Scenario
          <select
            value={filters.scenario}
            onChange={(event) => update({ scenario: event.target.value })}
          >
            <option value="all">All scenarios</option>
            {scenarioOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cloud
          <select
            aria-label="Cloud outcome"
            value={filters.cloud}
            onChange={(event) => update({ cloud: event.target.value as ResultsBooleanFilter })}
          >
            <option value="all">All</option>
            <option value="yes">Cloud formed</option>
            <option value="no">No cloud</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        <label>
          Rain water aloft
          <select
            aria-label="Rain-water outcome"
            value={filters.rain}
            onChange={(event) => update({ rain: event.target.value as ResultsBooleanFilter })}
          >
            <option value="all">All</option>
            <option value="yes">Rain water aloft detected</option>
            <option value="no">No rain water aloft</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        <label>
          Sort
          <select
            aria-label="Sort results"
            value={filters.sort}
            onChange={(event) => update({ sort: event.target.value as ResultsSortKey })}
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="name">Name A-Z</option>
            <option value="scenario">Scenario</option>
            <option value="first_cloud">First cloud time</option>
            <option value="max_qc">Max qc</option>
            <option value="max_updraft">Max updraft</option>
            <option value="rain_onset">Rain-water onset</option>
            <option value="latest_output">Latest output time</option>
          </select>
        </label>
      </div>
    </section>
  );
}

function ExperimentNotebookList({
  results,
  totalResults,
  filtersActive,
  selectedResultId,
  onSelect,
  onOpenExplore,
  onResetFilters,
}: {
  results: ResultCard[];
  totalResults: number;
  filtersActive: boolean;
  selectedResultId: string | null;
  onSelect: (resultId: string) => void;
  onOpenExplore: (resultId: string) => void;
  onResetFilters: () => void;
}) {
  if (results.length === 0) {
    if (filtersActive && totalResults > 0) {
      return (
        <section className="notebook-list-panel empty-results" aria-label="Results list">
          <p className="eyebrow">No matches</p>
          <h3>No results match the current filters.</h3>
          <p>Try clearing filters or widening the search to see the full experiment notebook.</p>
          <button type="button" onClick={onResetFilters}>
            Clear filters
          </button>
        </section>
      );
    }
    return (
      <section className="notebook-list-panel empty-results" aria-label="Results list">
        <p className="eyebrow">Notebook empty</p>
        <h3>No ingested CM1 results yet.</h3>
        <p>Completed and ingested CM1 runs will appear here as experiment notebook entries.</p>
      </section>
    );
  }

  return (
    <section className="notebook-list-panel" aria-label="Results list">
      <p className="eyebrow">Experiment list</p>
      <div className="experiment-card-list">
        {results.map((result) => {
          const selected = result.result_id === selectedResultId;
          return (
            <article
              key={result.result_id}
              className={`experiment-card${selected ? " selected-experiment-card" : ""}`}
              aria-label={`${result.name} experiment`}
            >
              <div className="experiment-card-main">
                <button
                  type="button"
                  className="link-button"
                  onClick={() => onSelect(result.result_id)}
                  aria-pressed={selected}
                >
                  {result.name}
                </button>
                <p className="experiment-subtitle">
                  {result.scenario_name ?? humanize(result.scenario_id)} ·{" "}
                  {resultRunConfigurationLabel(result.run_configuration)} ·{" "}
                  {formatDate(result.completed_at ?? result.created_at)}
                </p>
                <div className="badge-row">
                  <OutcomeBadge result={result} />
                  <StatusBadge label={rainWaterOutcome(result)} tone="neutral" />
                  <StatusBadge label={resultInputSourceLabel(result)} tone="neutral" />
                </div>
                <p className="science-card-summary">{compactScienceSummary(result)}</p>
                <p className="result-story">{resultStory(result)}</p>
              </div>
              <div className="experiment-card-actions">
                <button type="button" onClick={() => onOpenExplore(result.result_id)}>
                  Open in Explore
                </button>
              </div>
              <details className="technical-details">
                <summary>Technical details</summary>
                <dl className="metric-grid">
                  <Metric label="Run ID" value={result.run_id} />
                  <Metric label="Scenario ID" value={result.scenario_id} />
                  <Metric label="State" value={userFacingStatus(result)} />
                  <Metric label="Output" value={outputSummary(result.output_file_summary)} />
                </dl>
              </details>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function ResultNotebookCard({
  result,
  draft,
  onDraftChange,
  onSubmit,
  onInspect,
  deletePreview,
  onPreviewDelete,
  onConfirmDelete,
  onCancelDelete,
}: {
  result: ResultCard | undefined;
  draft: { name: string; tags: string; notes: string };
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onInspect: () => void;
  deletePreview: DeleteResultResponse | null;
  onPreviewDelete: (resultId: string) => void;
  onConfirmDelete: (resultId: string) => void;
  onCancelDelete: () => void;
}) {
  if (!result) {
    return (
      <section className="status-panel" aria-label="Result detail">
        <p>Select an ingested CM1 result to review its notebook card.</p>
      </section>
    );
  }

  const visibleDeletePreview = deletePreview?.result_id === result.result_id ? deletePreview : null;

  return (
    <section className="notebook-card" aria-label="Result detail">
      <div className="notebook-title">
        <div>
          <p className="eyebrow">Notebook entry</p>
          <h3>{result.name}</h3>
          <p>
            {result.scenario_name ?? humanize(result.scenario_id)} ·{" "}
            {resultRunConfigurationLabel(result.run_configuration)}
          </p>
        </div>
      </div>

      <div className="badge-row">
        <OutcomeBadge result={result} />
        <StatusBadge label={rainWaterOutcome(result)} tone="neutral" />
      </div>

      <p className="result-story">{resultStory(result)}</p>
      <CandidateHypothesisSummary result={result} />
      <LocalizedResponseSummary result={result} />

      {(isValidatedQuickLookBaseline(result) || result.caveats.length > 0) && (
        <p className="secondary-result-note">
          {[
            isValidatedQuickLookBaseline(result) ? "Validated reference baseline" : null,
            result.caveats.length > 0 ? caveatLabel(result) : null,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      )}

      <dl className="metric-grid key-result-values">
        <Metric label="Cloud" value={cloudOutcome(result)} />
        <Metric label="Rain water aloft" value={rainWaterOutcome(result)} />
        <Metric label="Surface rain" value={surfaceRainOutcome(result)} />
        <Metric label="Reflectivity" value={reflectivityOutcome(result)} />
        <Metric label="First cloud time" value={formatSeconds(resultFirstCloudTime(result))} />
        <Metric label="Max qc" value={formatScientific(resultMaxQc(result), "kg/kg")} />
        <Metric label="Max updraft" value={formatNumber(resultMaxUpdraft(result), "m/s")} />
        <Metric label="Min downdraft" value={formatNumber(resultMinDowndraft(result), "m/s")} />
        {resultLiquidCloudTopMeters(result) !== null && (
          <Metric
            label="Liquid cloud top"
            value={formatNumber(resultLiquidCloudTopMeters(result), "m")}
          />
        )}
        <Metric
          label="Coherent cloud top"
          value={formatNumber(resultCloudTopMeters(result), "m")}
        />
        {resultRawHydrometeorEnvelopeTopMeters(result) !== null &&
          resultRawHydrometeorEnvelopeTopMeters(result) !== resultCloudTopMeters(result) && (
            <Metric
              label="Raw hydrometeor trace top"
              value={formatNumber(resultRawHydrometeorEnvelopeTopMeters(result), "m")}
            />
          )}
        {hasDeepConvectionDiagnostics(result) && (
          <Metric label="Deep convection" value={deepConvectionOutcome(result)} />
        )}
        <Metric label="Latest output" value={formatSeconds(resultLatestOutputTime(result))} />
        <Metric
          label="Local data"
          value="Run-directory backed; delete removes the result and local run files"
        />
      </dl>

      <InterestingTimesSummary result={result} />
      {visibleDeletePreview && (
        <section
          className="delete-preview result-delete-preview"
          aria-label="Result delete preview"
        >
          <h4>Delete result and local run data preview</h4>
          <p>
            This removes the ingested result, notebook edits, diagnostics, derived products, CM1
            output, logs, and local run files stored under this run directory. The result will
            disappear from Results, Explore, and local inventory after confirmation. It does not
            touch the source repo, runtime home itself, or external CM1 install. No files have been
            deleted yet.
          </p>
          <dl className="metric-grid">
            <Metric label="Run ID" value={visibleDeletePreview.run_id} />
            <Metric label="Selected path" value={visibleDeletePreview.run_directory} />
            <Metric
              label="Estimated reclaimed"
              value={formatBytes(visibleDeletePreview.size_bytes)}
            />
            <Metric label="Preview status" value={visibleDeletePreview.message} />
          </dl>
          <ul className="compact-list">
            {visibleDeletePreview.categories.map((category) => (
              <li key={category.label}>
                <strong>{category.label}</strong>: {category.description}{" "}
                {category.present ? `(${category.item_count} local item(s))` : "(none found)"}
              </li>
            ))}
          </ul>
          <div className="button-row">
            <button type="button" onClick={onCancelDelete}>
              Cancel
            </button>
            <button
              type="button"
              className="danger-button"
              onClick={() => onConfirmDelete(visibleDeletePreview.result_id)}
            >
              Delete result and local run data
            </button>
          </div>
        </section>
      )}

      <details className="technical-details">
        <summary>Technical details</summary>
        <dl className="metric-grid">
          <Metric label="Run ID" value={result.run_id} />
          <Metric label="Scenario ID" value={result.scenario_id} />
          <Metric label="Lifecycle" value={result.source_lifecycle_state} />
          <Metric label="Product state" value={result.source_product_state} />
          <Metric label="Result state" value={result.status} />
          <Metric label="Source model" value={result.source_model} />
          <Metric
            label="Input source"
            value={result.input_source_label ?? resultInputSourceLabel(result)}
          />
          <Metric label="Output" value={outputSummary(result.output_file_summary)} />
          <Metric
            label="Raw diagnostics"
            value={result.diagnostics_summary ?? "Diagnostics unavailable"}
          />
        </dl>

        <section aria-labelledby="result-question-title">
          <h4 id="result-question-title">Physical question</h4>
          <p>{result.physical_question}</p>
        </section>

        <section aria-labelledby="controls-used-title">
          <h4 id="controls-used-title">Controls used</h4>
          {Object.keys(result.controls).length > 0 ? (
            <ul className="compact-list">
              {Object.entries(result.controls).map(([key, value]) => (
                <li key={key}>
                  {humanize(key)}: {String(value)}
                </li>
              ))}
            </ul>
          ) : (
            <p>No controls recorded.</p>
          )}
        </section>

        <section aria-labelledby="provenance-title">
          <h4 id="provenance-title">Provenance labels</h4>
          <ul className="tag-list">
            {result.provenance_labels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </section>

        <FieldQualitySummary result={result} />
        <RuntimeIntegritySummary runtimeIntegrity={result.runtime_integrity ?? null} />

        <section aria-labelledby="caveats-title">
          <h4 id="caveats-title">Caveats / warnings</h4>
          {result.caveats.length > 0 ? (
            <ul className="compact-list">
              {result.caveats.map((caveat) => (
                <li key={caveat}>{caveat}</li>
              ))}
            </ul>
          ) : (
            <p>No caveats recorded.</p>
          )}
        </section>
      </details>

      <form className="notebook-form" onSubmit={onSubmit}>
        <label htmlFor="result-name">Name</label>
        <input
          id="result-name"
          value={draft.name}
          onChange={(event) => onDraftChange({ ...draft, name: event.target.value })}
        />

        <label htmlFor="result-tags">Tags</label>
        <input
          id="result-tags"
          value={draft.tags}
          onChange={(event) => onDraftChange({ ...draft, tags: event.target.value })}
          placeholder="baseline, reference"
        />

        <label htmlFor="result-notes">Notes</label>
        <textarea
          id="result-notes"
          value={draft.notes}
          onChange={(event) => onDraftChange({ ...draft, notes: event.target.value })}
        />

        <div className="button-row">
          <button type="button" onClick={onInspect}>
            Open in Explore
          </button>
          <button
            type="button"
            className="danger-button"
            onClick={() => onPreviewDelete(result.result_id)}
          >
            Preview delete result and local run data
          </button>
          <button type="submit" className="secondary-button">
            Save changes
          </button>
        </div>
      </form>
    </section>
  );
}

function InterestingTimesSummary({ result }: { result: ResultCard }) {
  const records = visibleInterestingTimes(result);
  if (records.length === 0) return null;
  return (
    <section className="science-landmarks" aria-labelledby="science-landmarks-title">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Science landmarks</p>
          <h4 id="science-landmarks-title">Interesting times</h4>
        </div>
        <StatusBadge label={scienceSupportLabel(result)} tone="neutral" />
      </div>
      <dl className="science-landmark-list">
        {records.map((record) => (
          <div key={record.key} className="science-landmark-item">
            <dt>{record.label}</dt>
            <dd>
              <span>{interestingTimePrimaryValue(record, result)}</span>
              {interestingTimeShowsTimeSuffix(record) &&
              record.time_seconds !== null &&
              record.time_seconds !== undefined ? (
                <span className="muted-inline">at {formatSeconds(record.time_seconds)}</span>
              ) : null}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function CandidateHypothesisSummary({ result }: { result: ResultCard }) {
  const comparison = result.candidate_hypothesis_comparison;
  if (!comparison) return null;
  return (
    <section className="candidate-outcome-summary" aria-label="Candidate hypothesis comparison">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Candidate hypothesis</p>
          <h4>Screening vs CM1</h4>
        </div>
        <StatusBadge
          label={comparison.match_status_label}
          tone={candidateMatchTone(comparison.match_status)}
        />
      </div>
      <dl className="metric-grid">
        <Metric label="Screened as" value={comparison.screened_as ?? "Not recorded"} />
        <Metric label="Ran as" value={comparison.ran_as} />
        <Metric label="CM1 outcome" value={comparison.cm1_outcome} />
      </dl>
      {comparison.evidence.length > 0 && (
        <p className="secondary-result-note">Evidence: {comparison.evidence.join(" · ")}</p>
      )}
      {comparison.caveats.length > 0 && (
        <p className="secondary-result-note">Caveats: {comparison.caveats.join(" · ")}</p>
      )}
    </section>
  );
}

function LocalizedResponseSummary({ result }: { result: ResultCard }) {
  const response = result.localized_response ?? result.science_summary?.localized_response ?? null;
  if (!response || (!response.geometry && response.support_state === "unavailable")) return null;
  const geometry = response.geometry;
  return (
    <section className="candidate-outcome-summary" aria-label="Surface forcing response">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Surface forcing response</p>
          <h4>Differential patch evidence</h4>
        </div>
        <StatusBadge label={localizedResponseLabel(response.support_state)} tone="neutral" />
      </div>
      <dl className="metric-grid">
        <Metric label="Patch" value={patchGeometryLabel(geometry)} />
        <Metric label="Heat footprint" value={patchRatioLabel(response.hfx_footprint, "hfx")} />
        <Metric label="Moisture footprint" value={patchRatioLabel(response.qfx_footprint, "qfx")} />
        <Metric
          label="Near-surface convergence"
          value={convergenceLabel(response.near_surface_convergence)}
        />
        <Metric label="Instantaneous updraft" value={patchDistanceLabel(response.updraft)} />
        <Metric label="Cloud-water alignment" value={patchDistanceLabel(response.cloud_water)} />
      </dl>
      {response.caveats.length > 0 && (
        <p className="secondary-result-note">Caveats: {response.caveats.join(" · ")}</p>
      )}
    </section>
  );
}

function localizedResponseLabel(state: string): string {
  if (state === "footprint_and_response_diagnostics_available") {
    return "Footprint and response diagnostics available";
  }
  if (state === "footprint_available_response_diagnostics_limited") {
    return "Footprint available; response diagnostics limited";
  }
  if (state === "unavailable_missing_emitted_surface_flux_fields") {
    return "Footprint unavailable";
  }
  if (state === "unavailable_not_differential_surface_forcing") {
    return "Not a patch run";
  }
  return humanize(state);
}

function patchGeometryLabel(geometry: DifferentialPatchGeometryDiagnostics | null | undefined) {
  if (!geometry) return "Patch geometry unavailable";
  const radius =
    geometry.radius_x_m !== null &&
    geometry.radius_x_m !== undefined &&
    geometry.radius_y_m !== null &&
    geometry.radius_y_m !== undefined &&
    geometry.radius_x_m === geometry.radius_y_m
      ? formatNumber(geometry.radius_x_m, "m radius")
      : `${formatNumber(geometry.radius_x_m ?? null, "m")} x ${formatNumber(
          geometry.radius_y_m ?? null,
          "m",
        )}`;
  const taper = formatNumber(geometry.taper_width_m ?? null, "m taper");
  return `${geometry.shape ?? "patch"} · ${radius} · ${taper}`;
}

function patchRatioLabel(field: PatchSpatialFieldDiagnostics, label: string): string {
  if (!field.available) {
    return `${label}: unavailable`;
  }
  const ratio =
    field.center_to_background_ratio !== null && field.center_to_background_ratio !== undefined
      ? `${field.center_to_background_ratio.toFixed(2)}x center/background`
      : "ratio unavailable";
  const coreRatio =
    field.core_to_background_ratio !== null && field.core_to_background_ratio !== undefined
      ? `; core/background ${field.core_to_background_ratio.toFixed(2)}x`
      : "";
  const distance = formatNumber(field.max_distance_from_patch_center_m ?? null, "m from center");
  const quality = field.quality_state ? `; ${humanize(field.quality_state)}` : "";
  return `${ratio}${coreRatio}; max ${distance}${quality}`;
}

function convergenceLabel(convergence: PatchConvergenceDiagnostics): string {
  if (!convergence.available) return "Unavailable";
  const fields =
    convergence.source_fields.length > 0 ? convergence.source_fields.join("/") : "winds";
  const time =
    convergence.time_seconds !== null && convergence.time_seconds !== undefined
      ? ` at ${formatNumber(convergence.time_seconds, "s")}`
      : "";
  const quality = convergence.quality_state ? `; ${humanize(convergence.quality_state)}` : "";
  return `${formatScientific(convergence.max_convergence_s_1 ?? null, "s^-1")}; max ${formatNumber(
    convergence.max_convergence_distance_from_patch_center_m ?? null,
    "m from center",
  )}${time}; ${fields}${quality}`;
}

function patchDistanceLabel(field: PatchSpatialFieldDiagnostics): string {
  if (!field.available) return "Unavailable";
  const time =
    field.time_seconds !== null && field.time_seconds !== undefined
      ? ` at ${formatNumber(field.time_seconds, "s")}`
      : "";
  const quality = field.quality_state ? `; ${humanize(field.quality_state)}` : "";
  return `${formatNumber(field.max_value ?? null, field.units ?? "")}; max ${formatNumber(
    field.max_distance_from_patch_center_m ?? null,
    "m from center",
  )}${time}${quality}`;
}

function threeDScalarEncoding(field: VisualizableField | undefined): ThreeDScalarEncoding | null {
  if (
    !field ||
    !field.coordinate_names.time ||
    !field.coordinate_names.y ||
    !field.coordinate_names.x
  ) {
    return null;
  }
  if (field.raw_field_name === "w" || field.canonical_field_name === "vertical_velocity") {
    return null;
  }
  if (isSliceOnlyTemperatureField(field)) return null;
  const hasVerticalGrid = Boolean(field.coordinate_names.vertical);

  if (field.canonical_field_name === "cloud_water" || field.raw_field_name === "qc") {
    if (!hasVerticalGrid) return null;
    return {
      field,
      defaultThreshold: 1e-6,
      thresholdStep: 1e-6,
      statusLabel: "Cloud-water point layer loaded",
      emptyStateTitle: "No cloud water above the selected threshold at this time.",
      thresholdAriaLabel: "Cloud-water threshold",
      thresholdLabel: "Cloud-water threshold",
      rangeLabel: "Cloud-water range",
      valueChannel:
        "Color intensity shows cloud-water magnitude above threshold; opacity and point size are rendering controls.",
    };
  }

  if (field.canonical_field_name === "rain_water" || field.raw_field_name === "qr") {
    if (!hasVerticalGrid) return null;
    return {
      field,
      defaultThreshold: 1e-7,
      thresholdStep: 1e-7,
      statusLabel: "Rain-water point layer loaded",
      emptyStateTitle: "No rain water above the selected threshold at this time.",
      thresholdAriaLabel: "Rain-water threshold",
      thresholdLabel: "Rain-water threshold",
      rangeLabel: "Rain-water range",
      valueChannel:
        "Color intensity shows rain-water magnitude above threshold; opacity and point size are rendering controls.",
    };
  }

  if (field.canonical_field_name === "reflectivity" || field.raw_field_name === "dbz") {
    if (!hasVerticalGrid) return null;
    return {
      field,
      defaultThreshold: 0,
      thresholdStep: 1,
      statusLabel: "Reflectivity point layer loaded",
      emptyStateTitle: "No reflectivity values above the selected threshold at this time.",
      thresholdAriaLabel: "Reflectivity threshold",
      thresholdLabel: "Reflectivity threshold",
      rangeLabel: "Reflectivity range",
      valueChannel:
        "Color intensity shows reflectivity value; point size stays globally controlled and does not imply mass.",
    };
  }

  if (field.canonical_field_name === "water_vapor" || field.raw_field_name === "qv") {
    if (!hasVerticalGrid) return null;
    return {
      field,
      defaultThreshold: 0.01,
      thresholdStep: 1e-6,
      statusLabel: "Water-vapor point layer loaded",
      emptyStateTitle: "No water-vapor values above the selected threshold at this time.",
      thresholdAriaLabel: "Water-vapor visible minimum",
      thresholdLabel: "Water-vapor visible minimum",
      rangeLabel: "Water-vapor range",
      valueChannel:
        "Color intensity shows water-vapor magnitude above threshold; opacity and point size are rendering controls.",
    };
  }

  if (isSurfaceRainField(field)) {
    return {
      field,
      defaultThreshold: 0,
      thresholdStep: 0.1,
      statusLabel: "Surface-rain floor layer loaded",
      emptyStateTitle: "No accumulated surface rain above the selected threshold at this time.",
      thresholdAriaLabel: "Surface-rain threshold",
      thresholdLabel: "Surface-rain threshold",
      rangeLabel: "Surface-rain range",
      valueChannel:
        "Color intensity shows accumulated surface rain on the domain floor; opacity and point size are rendering controls.",
    };
  }

  return null;
}

function isSurfaceRainField(field: VisualizableField | undefined): boolean {
  if (!field) return false;
  return (
    field.raw_field_name === "rain" || field.canonical_field_name === "accumulated_surface_rain"
  );
}

function isSliceOnlyTemperatureField(field: VisualizableField | undefined): boolean {
  if (!field) return false;
  return (
    field.canonical_field_name === "potential_temperature" ||
    field.canonical_field_name === "temperature" ||
    field.raw_field_name === "th" ||
    field.raw_field_name === "theta" ||
    field.raw_field_name === "t" ||
    field.raw_field_name === "temp" ||
    field.raw_field_name === "temperature"
  );
}

function sliceFieldOptionLabel(field: VisualizableField): string {
  const suffix = threeDScalarEncoding(field) ? "" : " (slice only)";
  return `${field.raw_field_name} - ${field.display_name}${suffix}`;
}

export function VisualizerSceneShell({ result }: { result: ResultCard }) {
  const resultId = result.result_id;
  const initialResultRef = useRef(result);
  if (initialResultRef.current.result_id !== resultId) {
    initialResultRef.current = result;
  }
  const [catalog, setCatalog] = useState<FieldCatalogResponse | null>(null);
  const [viewDefaults, setViewDefaults] = useState<ViewDefaultsResponse | null>(null);
  const [selectedTimeDefaults, setSelectedTimeDefaults] = useState<ViewDefaultsResponse | null>(
    null,
  );
  const [selectedFieldName, setSelectedFieldName] = useState("");
  const [timeIndex, setTimeIndex] = useState(0);
  const [playbackTimeIndex, setPlaybackTimeIndex] = useState(0);
  const [isPlaybackRunning, setIsPlaybackRunning] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [threshold, setThreshold] = useState(1e-6);
  const [opacity, setOpacity] = useState(0.68);
  const [pointSize, setPointSize] = useState(11);
  const [pointCloud, setPointCloud] = useState<PointCloudResponse | null>(null);
  const [processMode, setProcessMode] = useState<ProcessMode>("thermal_fate");
  const [showSlicePlanes, setShowSlicePlanes] = useState(true);
  const [sliceFieldName, setSliceFieldName] = useState("qc");
  const [activeSlicePlane, setActiveSlicePlane] = useState<SceneSlicePlane>("horizontal");
  const [sliceOrientation, setSliceOrientation] = useState<"vertical_x" | "vertical_y">(
    "vertical_x",
  );
  const [horizontalSliceLevel, setHorizontalSliceLevel] = useState(0);
  const [verticalSliceIndex, setVerticalSliceIndex] = useState(0);
  const [sceneHorizontalSlice, setSceneHorizontalSlice] = useState<SliceResponse | null>(null);
  const [sceneVerticalSlice, setSceneVerticalSlice] = useState<SliceResponse | null>(null);
  const [sceneStatus, setSceneStatus] = useState("Loading scene data...");
  const [sceneError, setSceneError] = useState<string | null>(null);
  const [sliceLoading, setSliceLoading] = useState(false);
  const [sliceError, setSliceError] = useState<string | null>(null);
  const [fieldLoadAttempt, setFieldLoadAttempt] = useState(0);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegionRequest | null>(null);
  const [regionDiagnostics, setRegionDiagnostics] =
    useState<SelectedRegionDiagnosticsResponse | null>(null);
  const [regionStatus, setRegionStatus] = useState("Click a slice cell to inspect that point.");
  const [regionError, setRegionError] = useState<string | null>(null);
  const maxPoints = 50_000;

  useEffect(() => {
    let active = true;
    setCatalog(null);
    setViewDefaults(null);
    setSelectedTimeDefaults(null);
    setSceneError(null);
    setSelectedFieldName("");
    setTimeIndex(0);
    setPlaybackTimeIndex(0);
    setIsPlaybackRunning(false);
    setPlaybackSpeed(1);
    setThreshold(1e-6);
    setOpacity(0.68);
    setPointSize(11);
    setPointCloud(null);
    setProcessMode("thermal_fate");
    setShowSlicePlanes(true);
    setSliceFieldName("qc");
    setActiveSlicePlane("horizontal");
    setSliceOrientation("vertical_x");
    setHorizontalSliceLevel(0);
    setVerticalSliceIndex(0);
    setSceneHorizontalSlice(null);
    setSceneVerticalSlice(null);
    setSliceLoading(false);
    setSliceError(null);
    setSelectedRegion(null);
    setRegionDiagnostics(null);
    setRegionError(null);
    setRegionStatus("Click a slice cell to inspect that point.");
    setSceneStatus("Loading scene data...");
    withTimeout(
      Promise.all([
        fetchVisualizationFields(resultId),
        fetchVisualizationDefaults(resultId).catch(() => null),
      ]),
      "Timed out loading visualization fields. Check the backend and retry.",
    )
      .then(([payload, defaults]) => {
        if (!active) return;
        setSceneError(null);
        setCatalog(payload);
        setViewDefaults(defaults);
        const renderableEncodings = payload.available_fields
          .map(threeDScalarEncoding)
          .filter((encoding): encoding is ThreeDScalarEncoding => encoding !== null);
        const firstPreferred =
          payload.available_fields.find(
            (field) => field.raw_field_name === (defaults?.preferred_field ?? "qc"),
          ) ??
          payload.available_fields.find((field) => field.raw_field_name === "qc") ??
          payload.available_fields[0];
        const firstRenderable =
          renderableEncodings.find(
            (encoding) => encoding.field.raw_field_name === (defaults?.preferred_field ?? "qc"),
          ) ??
          renderableEncodings.find((encoding) => encoding.field.raw_field_name === "qc") ??
          renderableEncodings[0] ??
          null;
        const initialSliceField =
          firstPreferred ?? firstRenderable?.field ?? payload.available_fields[0];
        const initialDefaults = defaultsForField(defaults, initialSliceField?.raw_field_name);
        const initialTimeIndex = defaultTimeIndex(
          initialSliceField,
          initialResultRef.current,
          initialDefaults,
        );
        setSelectedFieldName(firstRenderable?.field.raw_field_name ?? "");
        setSliceFieldName(initialSliceField?.raw_field_name ?? "");
        setTimeIndex(initialTimeIndex);
        setPlaybackTimeIndex(initialTimeIndex);
        setThreshold(firstRenderable?.defaultThreshold ?? 1e-6);
        setHorizontalSliceLevel(defaultHorizontalLevel(initialSliceField, initialDefaults));
        setVerticalSliceIndex(
          defaultVerticalIndex(initialSliceField, "vertical_x", initialDefaults),
        );
        setSceneStatus(
          payload.available_fields.length === 0
            ? "No fields available"
            : firstRenderable
              ? "Field view ready"
              : "Slice fields ready; no 3-D scalar field available",
        );
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setSceneError(caught instanceof Error ? caught.message : "Unable to load scene data.");
        setSceneStatus("Scene unavailable");
      });
    return () => {
      active = false;
    };
  }, [fieldLoadAttempt, resultId]);

  const selectedField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === selectedFieldName),
    [catalog, selectedFieldName],
  );
  const sliceField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === sliceFieldName),
    [catalog, sliceFieldName],
  );
  const threeDScalarEncodings = useMemo(
    () =>
      (catalog?.available_fields ?? [])
        .map(threeDScalarEncoding)
        .filter((encoding): encoding is ThreeDScalarEncoding => encoding !== null),
    [catalog],
  );
  const selectedEncoding = useMemo(
    () =>
      threeDScalarEncodings.find(
        (encoding) => encoding.field.raw_field_name === selectedFieldName,
      ) ?? null,
    [selectedFieldName, threeDScalarEncodings],
  );
  const controlField = selectedField ?? sliceField;

  const timeOptions = controlField?.time_coordinate_values ?? [];
  const timeMax = Math.max(0, timeOptions.length - 1);
  const resolvedTimeIndex = Math.min(timeIndex, timeMax);
  const resolvedPlaybackTimeIndex = Math.min(playbackTimeIndex, timeMax);
  const displayTimeIndex = isPlaybackRunning ? resolvedPlaybackTimeIndex : resolvedTimeIndex;
  const sceneTimeIndex = displayTimeIndex;
  const wField = catalog?.available_fields.find((field) => field.raw_field_name === "w");
  const isNoCloudWithUpdraft =
    cloudOutcome(result) === "No cloud formed" && Boolean(wField) && (result.max_w_m_s ?? 0) > 0;
  const sliceVerticalSize = sliceField?.coordinate_names.vertical
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.vertical)]
    : 1;
  const sliceSupportsVertical = Boolean(sliceField?.coordinate_names.vertical);
  const sliceYSize = sliceField?.coordinate_names.y
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.y)]
    : 1;
  const sliceXSize = sliceField?.coordinate_names.x
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.x)]
    : 1;
  const activeSliceMax =
    activeSlicePlane === "horizontal"
      ? sliceVerticalSize
      : activeSlicePlane === "vertical_x"
        ? sliceYSize
        : sliceXSize;
  const activeSliceIndex =
    activeSlicePlane === "horizontal" ? horizontalSliceLevel : verticalSliceIndex;
  const activeSlicePositionLabel = activeSlicePosition(
    activeSlicePlane,
    sceneHorizontalSlice,
    sceneVerticalSlice,
  );
  const provenanceLabel =
    pointCloud?.provenance.provenance_label ??
    selectedField?.provenance.provenance_label ??
    catalog?.provenance.provenance_label ??
    "CM1-derived visualization-ready data; rendering not implemented";
  const selectedDefaults = defaultsForField(viewDefaults, selectedFieldName);
  const selectedTimeFieldDefaults = defaultsForField(selectedTimeDefaults, selectedFieldName);
  const selectedTimeSliceDefaults = defaultsForField(selectedTimeDefaults, sliceFieldName);
  const selectedTimeValue = timeOptions[resolvedTimeIndex] ?? null;
  const selectedTimeLabel = formatTimeValue(selectedTimeValue);
  const displayTimeValue = timeOptions[displayTimeIndex] ?? null;
  const displayTimeLabel = formatTimeValue(displayTimeValue);
  const sceneTimeValue = timeOptions[sceneTimeIndex] ?? null;
  const sceneTimeLabel = formatTimeValue(sceneTimeValue);
  const playbackSpeedOptions = [0.5, 1, 2, 4];
  const playbackIntervalMs = Math.max(150, Math.round(900 / playbackSpeed));
  const canPlayTimelapse = timeOptions.length > 1;
  const activeSlice = activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice;
  const activeSliceLabel = slicePlainLabel(activeSlice, activeSlicePlane, activeSliceIndex);
  const selectedSliceValue = selectedSliceCellValue(activeSlice, selectedRegion);
  const processModeStates = useMemo(
    () => processModeClassifications(result, catalog, sliceField, activeSlice),
    [activeSlice, catalog, result, sliceField],
  );
  const primaryProcessModes = processModeStates.filter((state) => state.primary);
  const unavailableProcessModes = processModeStates.filter((state) => !state.primary);
  const activeProcessMode = primaryProcessModes.some((state) => state.mode === processMode)
    ? processMode
    : (primaryProcessModes[0]?.mode ?? "thermal_fate");
  const activeProcessModeState =
    primaryProcessModes.find((state) => state.mode === activeProcessMode) ??
    processModeStates.find((state) => state.mode === activeProcessMode);
  const timePresets = [
    result.time_of_max_qc_seconds !== null && result.time_of_max_qc_seconds !== undefined
      ? { label: "Max cloud water", seconds: result.time_of_max_qc_seconds }
      : null,
    result.first_cloud_time_seconds !== null
      ? { label: "First cloud", seconds: result.first_cloud_time_seconds }
      : null,
    result.time_of_max_w_seconds !== null && result.time_of_max_w_seconds !== undefined
      ? { label: "Max updraft", seconds: result.time_of_max_w_seconds }
      : null,
    result.first_rain_time_seconds !== null && result.first_rain_time_seconds !== undefined
      ? { label: "Rain-water onset", seconds: result.first_rain_time_seconds }
      : null,
  ].filter((preset): preset is { label: string; seconds: number } => preset !== null);

  const clearSelectedRegionForTimeChange = useCallback(
    (nextStatus = "Click a slice cell to inspect that point.") => {
      setSelectedRegion(null);
      setRegionDiagnostics(null);
      setRegionError(null);
      setRegionStatus(nextStatus);
    },
    [],
  );

  const handleTimeIndexChange = useCallback(
    (nextIndex: number) => {
      const clampedIndex = clampIndex(nextIndex, timeOptions.length || 1);
      setIsPlaybackRunning(false);
      setTimeIndex(clampedIndex);
      setPlaybackTimeIndex(clampedIndex);
      clearSelectedRegionForTimeChange();
    },
    [clearSelectedRegionForTimeChange, timeOptions.length],
  );

  const handlePlaybackToggle = useCallback(() => {
    if (isPlaybackRunning) {
      const clampedIndex = clampIndex(playbackTimeIndex, timeOptions.length || 1);
      setIsPlaybackRunning(false);
      setTimeIndex(clampedIndex);
      setPlaybackTimeIndex(clampedIndex);
      clearSelectedRegionForTimeChange();
      return;
    }
    setPlaybackTimeIndex(resolvedTimeIndex);
    setIsPlaybackRunning(true);
    clearSelectedRegionForTimeChange("Pause playback to select a cell and explain this time step.");
  }, [
    clearSelectedRegionForTimeChange,
    isPlaybackRunning,
    playbackTimeIndex,
    resolvedTimeIndex,
    timeOptions.length,
  ]);

  useEffect(() => {
    if (processMode !== activeProcessMode) {
      setProcessMode(activeProcessMode);
    }
  }, [activeProcessMode, processMode]);

  useEffect(() => {
    if (!canPlayTimelapse && isPlaybackRunning) {
      setIsPlaybackRunning(false);
      setPlaybackTimeIndex(resolvedTimeIndex);
    }
  }, [canPlayTimelapse, isPlaybackRunning, resolvedTimeIndex]);

  useEffect(() => {
    if (!isPlaybackRunning || !canPlayTimelapse) return undefined;
    clearSelectedRegionForTimeChange("Pause playback to select a cell and explain this time step.");
    const intervalId = window.setInterval(() => {
      clearSelectedRegionForTimeChange(
        "Pause playback to select a cell and explain this time step.",
      );
      setPlaybackTimeIndex((current) => {
        if (current >= timeMax) {
          setIsPlaybackRunning(false);
          setTimeIndex(0);
          return 0;
        }
        return current + 1;
      });
    }, playbackIntervalMs);
    return () => window.clearInterval(intervalId);
  }, [
    canPlayTimelapse,
    clearSelectedRegionForTimeChange,
    isPlaybackRunning,
    playbackIntervalMs,
    timeMax,
  ]);

  useEffect(() => {
    if (!sliceSupportsVertical && activeSlicePlane !== "horizontal") {
      setActiveSlicePlane("horizontal");
      setSelectedRegion(null);
    }
  }, [activeSlicePlane, sliceSupportsVertical]);

  useEffect(() => {
    if (!selectedEncoding) {
      setPointCloud(null);
      return;
    }
    let active = true;
    setSceneError(null);
    setSceneStatus(`Loading ${selectedEncoding.field.display_name.toLowerCase()} points...`);
    fetchVisualizationPointCloud(result.result_id, {
      field: selectedEncoding.field.raw_field_name,
      timeIndex: sceneTimeIndex,
      threshold,
      maxPoints,
    })
      .then((payload) => {
        if (!active) return;
        setPointCloud(payload);
        setSceneStatus(
          payload.points.length > 0
            ? selectedEncoding.statusLabel
            : emptyPointCloudStatus(payload, selectedEncoding),
        );
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setPointCloud(null);
        setSceneError(
          caught instanceof Error ? caught.message : "Unable to load 3-D scalar point layer.",
        );
        setSceneStatus("3-D scalar layer unavailable");
      });
    return () => {
      active = false;
    };
  }, [maxPoints, result.result_id, sceneTimeIndex, selectedEncoding, threshold]);

  useEffect(() => {
    if (!catalog) {
      setSelectedTimeDefaults(null);
      return;
    }
    let active = true;
    fetchVisualizationDefaults(result.result_id, resolvedTimeIndex)
      .then((defaults) => {
        if (!active) return;
        setSelectedTimeDefaults(defaults);
      })
      .catch(() => {
        if (active) setSelectedTimeDefaults(null);
      });
    return () => {
      active = false;
    };
  }, [catalog, result.result_id, resolvedTimeIndex]);

  useEffect(() => {
    if (!sliceField) {
      setSceneHorizontalSlice(null);
      setSceneVerticalSlice(null);
      setSliceLoading(false);
      return;
    }
    let active = true;
    setSliceLoading(true);
    setSliceError(null);
    const horizontalPromise = fetchVisualizationSlice(result.result_id, {
      field: sliceField.raw_field_name,
      timeIndex: resolvedTimeIndex,
      orientation: "horizontal",
      levelIndex: horizontalSliceLevel,
    });
    const verticalPromise = sliceSupportsVertical
      ? fetchVisualizationSlice(result.result_id, {
          field: sliceField.raw_field_name,
          timeIndex: resolvedTimeIndex,
          orientation: sliceOrientation,
          levelIndex: verticalSliceIndex,
        })
      : Promise.resolve(null);
    Promise.all([horizontalPromise, verticalPromise])
      .then(([horizontal, vertical]) => {
        if (!active) return;
        setSceneHorizontalSlice(horizontal);
        setSceneVerticalSlice(vertical);
        setSliceLoading(false);
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setSceneHorizontalSlice(null);
        setSceneVerticalSlice(null);
        setSliceLoading(false);
        setSliceError(caught instanceof Error ? caught.message : "Unable to load slice planes.");
      });
    return () => {
      active = false;
    };
  }, [
    horizontalSliceLevel,
    result.result_id,
    resolvedTimeIndex,
    sliceField,
    sliceSupportsVertical,
    sliceOrientation,
    verticalSliceIndex,
  ]);

  useEffect(() => {
    if (!selectedRegion) {
      setRegionDiagnostics(null);
      setRegionError(null);
      setRegionStatus("Click a slice cell to inspect that point.");
      return;
    }
    let active = true;
    setRegionDiagnostics(null);
    setRegionError(null);
    setRegionStatus("Loading selected-point diagnostics...");
    fetchSelectedRegionDiagnostics(result.result_id, selectedRegion)
      .then((payload) => {
        if (!active) return;
        setRegionDiagnostics(payload);
        setRegionStatus("Selected-point diagnostics loaded");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setRegionDiagnostics(null);
        setRegionError(
          caught instanceof Error ? caught.message : "Unable to inspect the selected point.",
        );
        setRegionStatus("Selected-point request failed");
      });
    return () => {
      active = false;
    };
  }, [result.result_id, selectedRegion]);

  function selectPointFromSlice(slice: SliceResponse, rowIndex: number, columnIndex: number) {
    if (isPlaybackRunning) {
      clearSelectedRegionForTimeChange(
        "Pause playback to select a cell and explain this time step.",
      );
      return;
    }
    setSelectedRegion(selectionFromSlice(slice, rowIndex, columnIndex, "point"));
  }

  return (
    <section className="visualizer-shell" aria-labelledby="visualizer-shell-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Field view</p>
          <h2 id="visualizer-shell-title">What happened in this result?</h2>
        </div>
        <p className="state-chip">{sceneStatus}</p>
      </div>

      {sceneError && (
        <div role="alert">
          <p>{sceneError}</p>
          <button type="button" onClick={() => setFieldLoadAttempt((current) => current + 1)}>
            Retry loading fields
          </button>
        </div>
      )}

      {catalog && catalog.available_fields.length === 0 && (
        <p role="status">No visualization-ready fields are available for this result.</p>
      )}

      <div className="visualizer-workbench" aria-label="Scientific visualization workbench">
        <div className="visualizer-stage" aria-label="Fixed visualization viewport region">
          <True3DViewer
            resultName={result.name}
            pointCloud={pointCloud}
            fieldLabel={
              selectedEncoding
                ? `${selectedEncoding.field.raw_field_name} — ${selectedEncoding.field.display_name}`
                : "No supported 3-D scalar field"
            }
            valueChannelLabel={
              selectedEncoding?.valueChannel ?? "3-D scalar rendering unavailable."
            }
            activeSlice={
              activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice
            }
            activeSliceLabel={activeSliceLabel}
            showSlicePlane={showSlicePlanes}
            selectedRegion={selectedRegion}
            coordinateSizes={{ x: sliceXSize, y: sliceYSize, z: sliceVerticalSize }}
            selectedTimeLabel={selectedTimeLabel}
            sceneTimeLabel={sceneTimeLabel}
            thresholdLabel={formatScientific(threshold, selectedEncoding?.field.units ?? "")}
            opacity={opacity}
            pointSize={pointSize}
            status={sceneStatus}
            provenanceLabel={provenanceLabel}
            noCloudMessage={
              !selectedEncoding
                ? "No supported 3-D scalar field is available for this result. Use the 2-D slice inspector for available fields."
                : selectedEncoding.field.raw_field_name === "qc" && isNoCloudWithUpdraft
                  ? "No cloud water formed in this result; vertical velocity is available in the 2-D slice inspector."
                  : selectedEncoding.emptyStateTitle
            }
          />
          {catalog && sliceField && (
            <section className="explore-control-deck" aria-label="Explore viewer controls">
              <fieldset className="explore-control-card explore-control-card-time">
                <legend>Time</legend>
                <div className="timelapse-controls" aria-label="Timelapse playback controls">
                  <button
                    type="button"
                    disabled={!canPlayTimelapse}
                    aria-pressed={isPlaybackRunning}
                    onClick={handlePlaybackToggle}
                  >
                    {isPlaybackRunning ? "Pause time" : "Play time"}
                  </button>
                  <label htmlFor="explore-playback-speed">
                    Speed
                    <select
                      id="explore-playback-speed"
                      aria-label="Playback speed"
                      value={playbackSpeed}
                      onChange={(event) => setPlaybackSpeed(Number(event.target.value))}
                    >
                      {playbackSpeedOptions.map((speed) => (
                        <option key={speed} value={speed}>
                          {speed}x
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label htmlFor="explore-time-scrubber">
                  Saved output time
                  <input
                    id="explore-time-scrubber"
                    aria-label="Saved output time"
                    type="range"
                    min={0}
                    max={timeMax}
                    value={displayTimeIndex}
                    disabled={timeMax === 0}
                    onChange={(event) => handleTimeIndexChange(Number(event.target.value))}
                  />
                  <span className="slice-position-label">
                    <span>{displayTimeLabel}</span>
                    <small>
                      frame {displayTimeIndex + 1} of {Math.max(1, timeOptions.length)}
                    </small>
                  </span>
                </label>
                <label htmlFor="explore-time">
                  Output time
                  <select
                    id="explore-time"
                    aria-label="Time"
                    value={displayTimeIndex}
                    onChange={(event) => handleTimeIndexChange(Number(event.target.value))}
                  >
                    {timeOptions.map((value, index) => (
                      <option key={`${value}-${index}`} value={index}>
                        {formatTimeValue(value)}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="time-preset-buttons" aria-label="Time presets">
                  {timePresets.map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() =>
                        handleTimeIndexChange(closestTimeIndex(timeOptions, preset.seconds))
                      }
                    >
                      {preset.label}
                    </button>
                  ))}
                  <button type="button" onClick={() => handleTimeIndexChange(timeMax)}>
                    Last frame
                  </button>
                </div>
                {isPlaybackRunning && (
                  <p className="control-help">
                    Animating 3-D scene at {sceneTimeLabel}; slice and evidence remain at{" "}
                    {selectedTimeLabel} until playback is paused.
                  </p>
                )}
              </fieldset>

              <fieldset className="explore-control-card explore-control-card-slice">
                <legend>Slice</legend>
                <label htmlFor="explore-slice-field">
                  2-D slice field
                  <select
                    id="explore-slice-field"
                    aria-label="Slice field"
                    value={sliceFieldName}
                    onChange={(event) => {
                      const nextField = catalog.available_fields.find(
                        (field) => field.raw_field_name === event.target.value,
                      );
                      setSliceFieldName(event.target.value);
                      const nextDefaults = defaultsForField(viewDefaults, event.target.value);
                      setHorizontalSliceLevel(defaultHorizontalLevel(nextField, nextDefaults));
                      setVerticalSliceIndex(
                        defaultVerticalIndex(nextField, sliceOrientation, nextDefaults),
                      );
                      if (!nextField?.coordinate_names.vertical) {
                        setActiveSlicePlane("horizontal");
                      }
                      setSelectedRegion(null);
                    }}
                  >
                    {catalog.available_fields.map((field) => (
                      <option key={field.raw_field_name} value={field.raw_field_name}>
                        {sliceFieldOptionLabel(field)}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="segmented-buttons" aria-label="Slice orientation">
                  <button
                    type="button"
                    className={activeSlicePlane === "horizontal" ? "active-control" : ""}
                    onClick={() => {
                      setActiveSlicePlane("horizontal");
                      setSelectedRegion(null);
                    }}
                  >
                    Horizontal layer
                  </button>
                  <button
                    type="button"
                    className={activeSlicePlane === "vertical_x" ? "active-control" : ""}
                    disabled={!sliceSupportsVertical}
                    onClick={() => {
                      setActiveSlicePlane("vertical_x");
                      setSliceOrientation("vertical_x");
                      setSelectedRegion(null);
                    }}
                  >
                    Vertical x-z slice
                  </button>
                  <button
                    type="button"
                    className={activeSlicePlane === "vertical_y" ? "active-control" : ""}
                    disabled={!sliceSupportsVertical}
                    onClick={() => {
                      setActiveSlicePlane("vertical_y");
                      setSliceOrientation("vertical_y");
                      setSelectedRegion(null);
                    }}
                  >
                    Vertical y-z slice
                  </button>
                </div>

                <label htmlFor="explore-slice-position">
                  Position
                  <input
                    id="explore-slice-position"
                    aria-label="Slice position"
                    type="range"
                    min={0}
                    max={Math.max(0, activeSliceMax - 1)}
                    value={activeSliceIndex}
                    onChange={(event) => {
                      const nextIndex = Number(event.target.value);
                      if (activeSlicePlane === "horizontal") {
                        setHorizontalSliceLevel(nextIndex);
                      } else {
                        setVerticalSliceIndex(nextIndex);
                      }
                      setSelectedRegion(null);
                    }}
                  />
                  <span className="slice-position-label">
                    {activeSlicePositionLabel || `index ${activeSliceIndex}`}{" "}
                    <small>index {activeSliceIndex}</small>
                  </span>
                </label>

                <div className="button-row slice-move-buttons">
                  <button
                    type="button"
                    onClick={() => {
                      const nextIndex = Math.max(0, activeSliceIndex - 1);
                      if (activeSlicePlane === "horizontal") {
                        setHorizontalSliceLevel(nextIndex);
                      } else {
                        setVerticalSliceIndex(nextIndex);
                      }
                      setSelectedRegion(null);
                    }}
                  >
                    {activeSlicePlane === "horizontal" ? "Move down" : "Move back"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const nextIndex = Math.min(
                        Math.max(0, activeSliceMax - 1),
                        activeSliceIndex + 1,
                      );
                      if (activeSlicePlane === "horizontal") {
                        setHorizontalSliceLevel(nextIndex);
                      } else {
                        setVerticalSliceIndex(nextIndex);
                      }
                      setSelectedRegion(null);
                    }}
                  >
                    {activeSlicePlane === "horizontal" ? "Move up" : "Move forward"}
                  </button>
                </div>

                <label className="checkbox-label" htmlFor="show-slice-plane">
                  <input
                    id="show-slice-plane"
                    type="checkbox"
                    checked={showSlicePlanes}
                    onChange={(event) => setShowSlicePlanes(event.target.checked)}
                  />
                  Show slice plane
                </label>
              </fieldset>

              <fieldset className="explore-control-card explore-control-card-rendering">
                <legend>3-D scalar layer</legend>
                <label htmlFor="explore-3d-field">
                  3-D field
                  <select
                    id="explore-3d-field"
                    aria-label="3-D scalar field"
                    value={selectedFieldName}
                    disabled={threeDScalarEncodings.length === 0}
                    onChange={(event) => {
                      const nextEncoding =
                        threeDScalarEncodings.find(
                          (encoding) => encoding.field.raw_field_name === event.target.value,
                        ) ?? null;
                      setSelectedFieldName(event.target.value);
                      if (nextEncoding) {
                        setSliceFieldName(nextEncoding.field.raw_field_name);
                        setThreshold(nextEncoding.defaultThreshold);
                        if (!nextEncoding.field.coordinate_names.vertical) {
                          setActiveSlicePlane("horizontal");
                        }
                        const nextDefaults =
                          defaultsForField(
                            selectedTimeDefaults,
                            nextEncoding.field.raw_field_name,
                          ) ?? defaultsForField(viewDefaults, nextEncoding.field.raw_field_name);
                        setHorizontalSliceLevel(
                          defaultHorizontalLevel(nextEncoding.field, nextDefaults),
                        );
                        setVerticalSliceIndex(
                          defaultVerticalIndex(nextEncoding.field, sliceOrientation, nextDefaults),
                        );
                      }
                      setSelectedRegion(null);
                    }}
                  >
                    {threeDScalarEncodings.length === 0 && (
                      <option value="">No 3-D scalar fields</option>
                    )}
                    {threeDScalarEncodings.map((encoding) => (
                      <option
                        key={encoding.field.raw_field_name}
                        value={encoding.field.raw_field_name}
                      >
                        {encoding.field.raw_field_name} - {encoding.field.display_name}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="control-help">
                  {selectedEncoding
                    ? selectedEncoding.valueChannel
                    : "Only fields with a defined 3-D scalar encoding appear here; vertical velocity remains slice-only."}
                </p>
                {pointCloud && selectedEncoding && (
                  <p className="control-help">
                    {pointCloudFieldSummary(pointCloud)}
                    {selectedEncoding.field.raw_field_name === "dbz"
                      ? " Weather-radar colors use a fixed 0 to 60+ dBZ scale."
                      : ""}
                  </p>
                )}
                {selectedEncoding?.field.raw_field_name === "qc" &&
                  cloudTopMismatchNotice(result) && (
                    <p className="control-help">{cloudTopMismatchNotice(result)}</p>
                  )}
                <label htmlFor="cloud-threshold">
                  {selectedEncoding?.thresholdLabel ?? "Visible minimum"}
                  <input
                    id="cloud-threshold"
                    aria-label={selectedEncoding?.thresholdAriaLabel ?? "3-D scalar threshold"}
                    type="number"
                    min={0}
                    step={selectedEncoding?.thresholdStep ?? 0.000001}
                    value={threshold}
                    onChange={(event) => setThreshold(Number(event.target.value))}
                    disabled={!selectedEncoding}
                  />
                </label>
                <label htmlFor="cloud-opacity">
                  Opacity
                  <input
                    id="cloud-opacity"
                    aria-label="Layer opacity"
                    type="range"
                    min={0.1}
                    max={1}
                    step={0.05}
                    value={opacity}
                    onChange={(event) => setOpacity(Number(event.target.value))}
                  />
                  <output htmlFor="cloud-opacity">{opacity}</output>
                </label>
                <label htmlFor="cloud-point-size">
                  Point size
                  <input
                    id="cloud-point-size"
                    aria-label="Point size"
                    type="range"
                    min={3}
                    max={18}
                    value={pointSize}
                    onChange={(event) => setPointSize(Number(event.target.value))}
                  />
                  <output htmlFor="cloud-point-size">{pointSize}px</output>
                </label>
              </fieldset>
            </section>
          )}
        </div>

        <aside className="visualizer-details-panel" aria-label="Visualization details">
          <ResultExplanationPanel result={result} isNoCloudWithUpdraft={isNoCloudWithUpdraft} />

          <details className="technical-details">
            <summary>Process evidence details</summary>
            <ProcessModeControl
              processMode={activeProcessMode}
              processModeStates={primaryProcessModes}
              activeProcessModeState={activeProcessModeState}
              unavailableProcessModes={unavailableProcessModes}
              onProcessModeChange={setProcessMode}
            />
            <ProcessOverlayPanel
              result={result}
              catalog={catalog}
              selectedField={sliceField}
              processMode={activeProcessMode}
              slice={activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice}
            />
          </details>

          {sliceError && <p role="alert">{sliceError}</p>}

          <details className="technical-details">
            <summary>Technical visualization details</summary>
            <dl className="metric-grid">
              <Metric label="Run ID" value={result.run_id} />
              <Metric label="Renderer" value="Direct Three.js point cloud" />
              <Metric
                label="3-D field"
                value={
                  selectedField
                    ? `${selectedField.raw_field_name} (${selectedField.display_name})`
                    : "Unavailable"
                }
              />
              <Metric label="3-D scene time" value={sceneTimeLabel} />
              <Metric label="Slice/evidence time" value={selectedTimeLabel} />
              <Metric label="Slice plane" value={activeSliceLabel} />
              <Metric label="Slice plane visible" value={showSlicePlanes ? "Yes" : "No"} />
              <Metric
                label={selectedEncoding?.thresholdLabel ?? "Visible threshold"}
                value={formatScientific(threshold, selectedField?.units ?? "")}
              />
              <Metric label="Opacity" value={String(opacity)} />
              <Metric label="Point size" value={`${pointSize}px`} />
              <Metric
                label="Point count"
                value={
                  pointCloud
                    ? `${pointCloud.stats.returned_count.toLocaleString()} of ${pointCloud.stats.source_count.toLocaleString()}`
                    : "Unavailable"
                }
              />
              <Metric
                label={selectedEncoding?.rangeLabel ?? "3-D field range"}
                value={
                  pointCloud
                    ? `${formatMaybeNumber(pointCloud.stats.min_value, selectedField?.units ?? "kg/kg")} to ${formatMaybeNumber(
                        pointCloud.stats.max_value,
                        selectedField?.units ?? "kg/kg",
                      )}`
                    : "Unavailable"
                }
              />
              <Metric
                label="Selected-field range"
                value={
                  pointCloud
                    ? `${formatMaybeNumber(
                        pointCloud.stats.field_min_value,
                        selectedField?.units ?? "kg/kg",
                      )} to ${formatMaybeNumber(
                        pointCloud.stats.field_max_value,
                        selectedField?.units ?? "kg/kg",
                      )}`
                    : "Unavailable"
                }
              />
              <Metric
                label="Downsampling"
                value={
                  pointCloud?.stats.downsampled
                    ? `Deterministic stride ${pointCloud.stats.downsample_stride}`
                    : "Not applied"
                }
              />
              <Metric
                label="Default source"
                value={
                  selectedTimeFieldDefaults?.source ??
                  selectedDefaults?.source ??
                  "domain center fallback"
                }
              />
              <Metric
                label="Slice source"
                value={
                  sliceField
                    ? `${sliceField.raw_field_name} (${sliceField.display_name})`
                    : "Unavailable"
                }
              />
              <Metric
                label="Slice orientation"
                value={
                  activeSlicePlane === "horizontal" && sceneHorizontalSlice
                    ? `${sceneHorizontalSlice.selection.orientation} at ${sceneHorizontalSlice.selection.selected_dimension}[${sceneHorizontalSlice.selection.selected_index}]`
                    : sceneVerticalSlice
                      ? `${sceneVerticalSlice.selection.orientation} at ${sceneVerticalSlice.selection.selected_dimension}[${sceneVerticalSlice.selection.selected_index}]`
                      : "Unavailable"
                }
              />
              <Metric label="Domain x extent" value={extentLabel(pointCloud, "xh")} />
              <Metric label="Domain y extent" value={extentLabel(pointCloud, "yh")} />
              <Metric label="Domain z extent" value={verticalExtentLabel(pointCloud)} />
              <Metric
                label="Active cloud z range"
                value={
                  pointCloud
                    ? `${formatMaybeNumber(pointCloud.stats.active_z_min, verticalCoordinateUnit(pointCloud))} to ${formatMaybeNumber(
                        pointCloud.stats.active_z_max,
                        verticalCoordinateUnit(pointCloud),
                      )}`
                    : "Unavailable"
                }
              />
              <Metric label="Max 3-D field location" value={maxPointLocationLabel(pointCloud)} />
              <Metric
                label="Selected-time slice default"
                value={selectedTimeSliceDefaults?.source ?? "Unavailable"}
              />
            </dl>

            <section aria-labelledby="visualizer-provenance-title">
              <h3 id="visualizer-provenance-title">Provenance / rendering labels</h3>
              <ul className="compact-list">
                <li>{provenanceLabel}</li>
                <li>Visualizer interpretation of CM1-derived output</li>
                <li>
                  Value channel:{" "}
                  {selectedEncoding?.valueChannel ?? "3-D scalar rendering unavailable"}
                </li>
                <li>
                  Processing method: backend native-grid thresholded point cloud for supported
                  scalar fields
                </li>
                <li>Rendering method: direct Three.js scalar point cloud</li>
                <li>Slice planes: native-grid JSON slices from the backend</li>
                <li>No raw NetCDF parsing in the browser</li>
                <li>
                  No interpolation, ray marching, isosurface extraction, or synthetic cloud physics
                </li>
              </ul>
            </section>
          </details>
        </aside>
      </div>

      {catalog && sliceField && (
        <section className="unified-slice-inspector" aria-labelledby="unified-slice-title">
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Slice inspector</p>
              <h2 id="unified-slice-title">Inspect the current slice</h2>
              <p>
                {activeSliceLabel} · {sliceField.raw_field_name} · {selectedTimeLabel}
              </p>
            </div>
            <p className="state-chip">
              {sliceError
                ? "Slice unavailable"
                : sliceLoading || !activeSlice
                  ? "Loading slice"
                  : "Slice synced"}
            </p>
          </div>

          {sliceError && <p role="alert">{sliceError}</p>}

          <SlicePanel
            title={activeSliceLabel}
            slice={activeSlice}
            pointCloud={pointCloud}
            selectedRegion={selectedRegion}
            onSelectRegion={selectPointFromSlice}
          />

          <SelectedRegionInspector
            selectedRegion={selectedRegion}
            slice={activeSlice}
            selectedValue={selectedSliceValue}
            diagnostics={regionDiagnostics}
            status={regionStatus}
            error={regionError}
            playbackRunning={isPlaybackRunning}
          />
        </section>
      )}
    </section>
  );
}

function ResultExplanationPanel({
  result,
  isNoCloudWithUpdraft,
}: {
  result: ResultCard;
  isNoCloudWithUpdraft: boolean;
}) {
  const cloudLabel = cloudOutcome(result);
  return (
    <section className="selected-region-inspector" aria-label="Result-level explanation panel">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Explanation</p>
          <h3>Result explanation</h3>
        </div>
        <StatusBadge
          label={
            cloudLabel === "Cloud formed"
              ? "Cloud formed in this result"
              : cloudLabel === "No cloud formed"
                ? "No cloud formed in this result"
                : cloudLabel
          }
          tone={cloudLabel === "Cloud formed" ? "good" : "warning"}
        />
      </div>
      <p>{resultStory(result)}</p>
      <section aria-label="Evidence">
        <h4>Evidence</h4>
        <dl className="metric-grid">
          <Metric label="First cloud time" value={formatSeconds(result.first_cloud_time_seconds)} />
          <Metric label="Max qc" value={formatScientific(result.max_qc_kg_kg, "kg/kg")} />
          <Metric label="Max w" value={formatNumber(result.max_w_m_s, "m/s")} />
          <Metric label="Rain water aloft" value={rainWaterOutcome(result)} />
          <Metric label="Surface rain" value={surfaceRainOutcome(result)} />
          <Metric label="Reflectivity" value={reflectivityOutcome(result)} />
        </dl>
      </section>
      {isNoCloudWithUpdraft && (
        <p>For this no-cloud result, use vertical velocity (w) slices to inspect the thermals.</p>
      )}
      <details>
        <summary>Technical details</summary>
        <ul className="compact-list">
          <li>Thermal Fate is the internal explanation model.</li>
          <li>Evidence comes from ingested CM1 diagnostics and visualization-ready fields.</li>
          <li>No raw NetCDF parsing in the browser.</li>
          {result.caveats.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}

function activeSlicePosition(
  activeSlicePlane: SceneSlicePlane,
  horizontalSlice: SliceResponse | null,
  verticalSlice: SliceResponse | null,
): string {
  const slice = activeSlicePlane === "horizontal" ? horizontalSlice : verticalSlice;
  if (!slice) return "";
  const coordinate = slice.selection.selected_coordinate_value;
  const units =
    slice.selection.level_units ?? slice.coordinate_units[slice.selection.selected_dimension];
  if (coordinate === null || coordinate === undefined) return "";
  const numericCoordinate = typeof coordinate === "number" ? coordinate : Number(coordinate);
  if (!Number.isFinite(numericCoordinate)) return String(coordinate);
  return `${formatCompactNumber(numericCoordinate)}${units ? ` ${units}` : ""}`;
}

function slicePlainLabel(
  slice: SliceResponse | null,
  activeSlicePlane: SceneSlicePlane,
  fallbackIndex: number,
): string {
  if (!slice) {
    const fallbackLabels: Record<SceneSlicePlane, string> = {
      horizontal: `Horizontal layer at z index ${fallbackIndex}`,
      vertical_x: `Vertical x-z slice at y index ${fallbackIndex}`,
      vertical_y: `Vertical y-z slice at x index ${fallbackIndex}`,
    };
    return fallbackLabels[activeSlicePlane];
  }
  const coordinate =
    slice.selection.selected_coordinate_value ?? slice.selection.level_coordinate_value;
  const units =
    slice.selection.level_units ?? slice.coordinate_units[slice.selection.selected_dimension];
  const coordinateText = coordinateTextWithUnits(coordinate, units, slice.selection.selected_index);
  if (slice.selection.orientation === "horizontal") {
    return `Horizontal layer at z = ${coordinateText}`;
  }
  if (slice.selection.orientation === "vertical_x") {
    return `Vertical x-z slice at y = ${coordinateText}`;
  }
  return `Vertical y-z slice at x = ${coordinateText}`;
}

function sliceAxisSummary(slice: SliceResponse | null, activeSlicePlane: SceneSlicePlane): string {
  const fixed = slice
    ? slicePlainLabel(slice, activeSlicePlane, slice.selection.selected_index)
    : "";
  if (activeSlicePlane === "horizontal") {
    return `x-axis = x; y-axis = y${fixed ? `; ${fixed}` : ""}`;
  }
  if (activeSlicePlane === "vertical_x") {
    return `x-axis = x; y-axis = height z${fixed ? `; ${fixed}` : ""}`;
  }
  return `x-axis = y; y-axis = height z${fixed ? `; ${fixed}` : ""}`;
}

function coordinateTextWithUnits(
  coordinate: number | string | null | undefined,
  units: string | null | undefined,
  fallbackIndex: number,
): string {
  if (coordinate === null || coordinate === undefined) return `index ${fallbackIndex}`;
  const numericCoordinate = typeof coordinate === "number" ? coordinate : Number(coordinate);
  const value = Number.isFinite(numericCoordinate)
    ? formatCompactNumber(numericCoordinate)
    : String(coordinate);
  return `${value}${units ? ` ${units}` : ""}`;
}

function selectedSliceCellValue(
  slice: SliceResponse | null,
  selectedRegion: SelectedRegionRequest | null,
): number | null {
  if (!slice || !selectedRegion) return null;
  for (let rowIndex = 0; rowIndex < slice.values.length; rowIndex += 1) {
    for (
      let columnIndex = 0;
      columnIndex < (slice.values[rowIndex]?.length ?? 0);
      columnIndex += 1
    ) {
      if (isSelectedSliceCell(slice, selectedRegion, rowIndex, columnIndex)) {
        return slice.values[rowIndex]?.[columnIndex] ?? null;
      }
    }
  }
  return null;
}

function SlicePanel({
  title,
  slice,
  pointCloud,
  selectedRegion,
  onSelectRegion,
}: {
  title: string;
  slice: SliceResponse | null;
  pointCloud?: PointCloudResponse | null;
  selectedRegion?: SelectedRegionRequest | null;
  onSelectRegion?: (slice: SliceResponse, rowIndex: number, columnIndex: number) => void;
}) {
  if (!slice) {
    return (
      <section className="slice-panel" aria-label={title}>
        <h3>{title}</h3>
        <p>Slice unavailable.</p>
      </section>
    );
  }

  const anchors = sliceAnchorLabels(slice, pointCloud);

  return (
    <section className="slice-panel" aria-label={title}>
      <h3>{title}</h3>
      <p className="slice-axis-summary">{sliceAxisSummary(slice, slice.selection.orientation)}</p>
      <div className="slice-map-frame" aria-label={`${title} orientation map`}>
        <span className="slice-map-anchor slice-map-anchor-top">{anchors.top}</span>
        <span className="slice-map-anchor slice-map-anchor-left">{anchors.left}</span>
        <SliceHeatmap
          title={title}
          slice={slice}
          selectedRegion={selectedRegion}
          onSelectRegion={onSelectRegion}
        />
        <span className="slice-map-anchor slice-map-anchor-right">{anchors.right}</span>
        <span className="slice-map-anchor slice-map-anchor-bottom">{anchors.bottom}</span>
      </div>
      <div className="heatmap-legend" aria-label={`${title} color scale`}>
        <span>{sliceLegendMinimum(slice)}</span>
        <span className={`heatmap-scale ${heatmapScaleClass(slice.field)}`} />
        <span>{sliceLegendMaximum(slice)}</span>
      </div>
      <details>
        <summary>Technical slice details</summary>
        <dl className="metric-grid">
          <Metric label="Orientation" value={slice.selection.orientation} />
          <Metric label="Time" value={formatSeconds(slice.selection.time_seconds)} />
          <Metric label="Shape" value={slice.shape.join(" x ")} />
          <Metric label="Dimensions" value={slice.dimension_order.join(", ")} />
          <Metric label="Min" value={formatMaybeNumber(slice.stats.min, slice.field.units)} />
          <Metric label="Max" value={formatMaybeNumber(slice.stats.max, slice.field.units)} />
          <Metric label="Finite values" value={String(slice.stats.finite_count)} />
          <Metric label="Non-finite values" value={String(slice.stats.non_finite_count)} />
        </dl>
        {slice.selection.level_units && (
          <p>
            Selected level: {String(slice.selection.level_coordinate_value)}{" "}
            {slice.selection.level_units}
            {slice.selection.level_meters !== null
              ? ` (${slice.selection.level_meters.toLocaleString()} m)`
              : ""}
          </p>
        )}
        <p>{slice.provenance.provenance_label}</p>
        {slice.caveats.length > 0 && (
          <ul className="compact-list">
            {slice.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        )}
        <div className="slice-values" role="table" aria-label={`${title} raw values`}>
          {slice.values.map((row, rowIndex) => (
            <div className="slice-row" role="row" key={`${title}-${rowIndex}`}>
              {row.map((value, columnIndex) => (
                <span
                  className="slice-cell"
                  role="cell"
                  key={`${title}-${rowIndex}-${columnIndex}`}
                >
                  {value === null ? "null" : formatCompactNumber(value)}
                </span>
              ))}
            </div>
          ))}
        </div>
      </details>
    </section>
  );
}

function sliceAnchorLabels(
  slice: SliceResponse,
  pointCloud?: PointCloudResponse | null,
): {
  left: string;
  right: string;
  top: string;
  bottom: string;
} {
  const xSize = axisSize(slice, slice.field.coordinate_names.x);
  const ySize = axisSize(slice, slice.field.coordinate_names.y);
  const zSize = axisSize(slice, slice.field.coordinate_names.vertical);
  const xMin = axisEndpointLabel("x", pointCloud?.coordinate_extents.xh, 0);
  const xMax = axisEndpointLabel("x", pointCloud?.coordinate_extents.xh, Math.max(0, xSize - 1));
  const yMin = axisEndpointLabel("y", pointCloud?.coordinate_extents.yh, 0);
  const yMax = axisEndpointLabel("y", pointCloud?.coordinate_extents.yh, Math.max(0, ySize - 1));
  const zMin = axisEndpointLabel("z", pointCloud?.coordinate_extents.zh, 0);
  const zMax = axisEndpointLabel("z", pointCloud?.coordinate_extents.zh, Math.max(0, zSize - 1));
  const orientation = slice.selection.orientation;
  if (orientation === "horizontal") {
    return {
      left: xMin,
      right: xMax,
      top: yMax,
      bottom: yMin,
    };
  }
  if (orientation === "vertical_x") {
    return {
      left: xMin,
      right: xMax,
      top: zMax,
      bottom: zMin,
    };
  }
  return {
    left: yMin,
    right: yMax,
    top: zMax,
    bottom: zMin,
  };
}

function axisEndpointLabel(
  axis: string,
  extent: { min: number; max: number; units: string | null } | undefined,
  fallbackIndex: number,
): string {
  if (!extent) return `${axis} index ${fallbackIndex}`;
  const value = fallbackIndex === 0 ? extent.min : extent.max;
  return `${axis} ${formatCompactNumber(value)}${extent.units ? ` ${extent.units}` : ""}`;
}

function axisSize(slice: SliceResponse, dimension: string | null): number {
  if (!dimension) return 1;
  const index = slice.field.dimensions.indexOf(dimension);
  return index >= 0 ? (slice.field.shape[index] ?? 1) : 1;
}

function ProcessModeControl({
  processMode,
  processModeStates,
  activeProcessModeState,
  unavailableProcessModes,
  onProcessModeChange,
}: {
  processMode: ProcessMode;
  processModeStates: ProcessModeClassification[];
  activeProcessModeState: ProcessModeClassification | undefined;
  unavailableProcessModes: ProcessModeClassification[];
  onProcessModeChange: (mode: ProcessMode) => void;
}) {
  return (
    <fieldset className="process-mode-control">
      <legend>Explanation focus</legend>
      {processModeStates.length > 0 ? (
        <>
          <select
            aria-label="Process mode"
            value={processMode}
            onChange={(event) => onProcessModeChange(event.target.value as ProcessMode)}
          >
            {processModeStates.map((state) => (
              <option key={state.mode} value={state.mode}>
                {processModeLabel(state.mode)}
                {state.support === "candidate" ? " (candidate)" : ""}
              </option>
            ))}
          </select>
          {activeProcessModeState && (
            <p className="process-mode-helper">
              <StatusBadge
                label={processSupportLabel(activeProcessModeState.support)}
                tone={
                  activeProcessModeState.support === "supported"
                    ? "good"
                    : activeProcessModeState.support === "candidate"
                      ? "neutral"
                      : "warning"
                }
              />
              <span>{activeProcessModeState.primaryReason}</span>
            </p>
          )}
        </>
      ) : (
        <p>No supported process evidence focus is available for this result yet.</p>
      )}
      {unavailableProcessModes.length > 0 && (
        <details className="unavailable-diagnostics">
          <summary>Not available for this result</summary>
          <ul className="compact-list">
            {unavailableProcessModes.map((state) => (
              <li key={state.mode}>
                <strong>{processModeLabel(state.mode)}</strong>{" "}
                <span className="muted-text">
                  {processSupportLabel(state.support)}. {state.primaryReason} {state.description}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </fieldset>
  );
}

function ProcessOverlayPanel({
  result,
  catalog,
  selectedField,
  processMode,
  slice,
}: {
  result: ResultCard;
  catalog: FieldCatalogResponse | null;
  selectedField: VisualizableField | undefined;
  processMode: ProcessMode;
  slice?: SliceResponse | null;
}) {
  const summary = processModeSummary(processMode, result, catalog, selectedField, slice ?? null);
  return (
    <section className="process-overlay-panel" aria-label="Explanation evidence">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Evidence</p>
          <h3>{processModeLabel(processMode)}</h3>
        </div>
        <StatusBadge
          label={processSupportLabel(summary.support)}
          tone={
            summary.support === "supported"
              ? "good"
              : summary.support === "candidate"
                ? "neutral"
                : "warning"
          }
        />
      </div>
      <p>{summary.description}</p>
      <dl className="metric-grid">
        <Metric label="Evidence type" value={summary.evidenceType} />
        <Metric label="Source" value={summary.source} />
        <Metric label="Process confidence" value={processSupportLabel(summary.support)} />
        <Metric label="Selected field" value={selectedField?.raw_field_name ?? "Unavailable"} />
      </dl>
      {summary.annotations.length > 0 && (
        <ul className="compact-list">
          {summary.annotations.map((annotation) => (
            <li key={annotation}>{annotation}</li>
          ))}
        </ul>
      )}
      {summary.caveats.length > 0 && (
        <details>
          <summary>Process caveats</summary>
          <ul className="compact-list">
            {_dedupeStrings(summary.caveats).map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

function SelectedRegionInspector({
  selectedRegion,
  slice,
  selectedValue,
  diagnostics,
  status,
  error,
  playbackRunning,
}: {
  selectedRegion: SelectedRegionRequest | null;
  slice: SliceResponse | null;
  selectedValue: number | null;
  diagnostics: SelectedRegionDiagnosticsResponse | null;
  status: string;
  error: string | null;
  playbackRunning?: boolean;
}) {
  if (!selectedRegion && !error && !playbackRunning) {
    return null;
  }

  return (
    <section className="selected-region-inspector" aria-label="What happened here panel">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Explanation</p>
          <h3>What happened here?</h3>
        </div>
        <p className="state-chip">
          {playbackRunning && !selectedRegion && !error ? "Playback running" : status}
        </p>
      </div>

      {error && <p role="alert">{error}</p>}

      {playbackRunning && !selectedRegion && !error && (
        <p>Pause playback to select a cell and explain this time step.</p>
      )}

      {selectedRegion && (
        <SelectedPointContext
          selectedRegion={selectedRegion}
          slice={slice}
          selectedValue={selectedValue}
          diagnostics={diagnostics}
        />
      )}

      {diagnostics && (
        <>
          <div className="inspector-summary">
            <StatusBadge
              label={diagnostics.interpretation.thermal_fate_label}
              tone={
                diagnostics.interpretation.confidence === "supported"
                  ? "good"
                  : diagnostics.interpretation.confidence === "candidate"
                    ? "neutral"
                    : "warning"
              }
            />
            <p>{diagnostics.interpretation.summary}</p>
          </div>

          <dl className="metric-grid">
            <Metric
              label="Confidence"
              value={processSupportLabel(diagnostics.interpretation.confidence)}
            />
            <Metric
              label="Main limiting factor"
              value={humanize(diagnostics.interpretation.main_limiting_factor)}
            />
            <Metric
              label="First local cloud time"
              value={formatSeconds(diagnostics.diagnostics.first_local_cloud_time_seconds)}
            />
            <Metric
              label="Local max qc"
              value={formatScientific(diagnostics.diagnostics.local_max_qc_kg_kg, "kg/kg")}
            />
            <Metric
              label="Local max w"
              value={formatNumber(diagnostics.diagnostics.local_max_w_m_s, "m/s")}
            />
            <Metric
              label="Local min w"
              value={formatNumber(diagnostics.diagnostics.local_min_w_m_s, "m/s")}
            />
            <Metric
              label="Local rain"
              value={
                diagnostics.diagnostics.local_rain_present
                  ? "Rain water aloft detected"
                  : "No rain water aloft detected"
              }
            />
          </dl>

          <details>
            <summary>Technical details and provenance</summary>
            <dl className="metric-grid">
              <Metric label="Region type" value={humanize(diagnostics.region.region_type)} />
              <Metric label="Native grid" value={diagnostics.region.native_grid ?? "Unavailable"} />
              <Metric
                label="Cell count"
                value={String(diagnostics.region.cell_count ?? "unknown")}
              />
              <Metric label="x" value={axisSelectionLabel(diagnostics.region.x)} />
              <Metric label="y" value={axisSelectionLabel(diagnostics.region.y)} />
              <Metric label="vertical" value={axisSelectionLabel(diagnostics.region.vertical)} />
              <Metric
                label="Max w fraction"
                value={formatRatio(diagnostics.comparison_to_domain.local_max_w_fraction_of_domain)}
              />
              <Metric
                label="Max qc fraction"
                value={formatRatio(
                  diagnostics.comparison_to_domain.local_max_qc_fraction_of_domain,
                )}
              />
              <Metric
                label="First cloud delta"
                value={formatSignedSeconds(
                  diagnostics.comparison_to_domain.local_first_cloud_time_delta_seconds,
                )}
              />
              <Metric
                label="Cloud-top fraction"
                value={formatRatio(
                  diagnostics.comparison_to_domain.local_cloud_top_fraction_of_domain,
                )}
              />
            </dl>
            <p>{diagnostics.provenance.provenance_label}</p>
            <ul className="compact-list">
              <li>Backend xarray selected-region diagnostics; no raw NetCDF parsing in browser.</li>
              <li>Selected region is not cloud-object tracking.</li>
              {_dedupeStrings([
                ...diagnostics.caveats,
                ...diagnostics.interpretation.caveats,
                ...diagnostics.comparison_to_domain.caveats,
              ]).map((caveat) => (
                <li key={caveat}>{caveat}</li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}

function SelectedPointContext({
  selectedRegion,
  slice,
  selectedValue,
  diagnostics,
}: {
  selectedRegion: SelectedRegionRequest;
  slice: SliceResponse | null;
  selectedValue: number | null;
  diagnostics: SelectedRegionDiagnosticsResponse | null;
}) {
  const x = diagnostics?.region.x
    ? axisSelectionLabel(diagnostics.region.x)
    : indexOrUnavailable(selectedRegion.xIndex);
  const y = diagnostics?.region.y
    ? axisSelectionLabel(diagnostics.region.y)
    : indexOrUnavailable(selectedRegion.yIndex);
  const z = diagnostics?.region.vertical
    ? axisSelectionLabel(diagnostics.region.vertical)
    : indexOrUnavailable(selectedRegion.zIndex);
  return (
    <section className="selected-point-context" aria-label="Selected point context">
      <h4>Selected point</h4>
      <dl className="metric-grid">
        <Metric
          label="Slice"
          value={
            slice
              ? slicePlainLabel(slice, slice.selection.orientation, slice.selection.selected_index)
              : "Unavailable"
          }
        />
        <Metric label="Time" value={formatSeconds(slice?.selection.time_seconds ?? null)} />
        <Metric
          label="Field"
          value={
            slice ? `${slice.field.raw_field_name} (${slice.field.display_name})` : "Unavailable"
          }
        />
        <Metric
          label="Selected field value"
          value={formatMaybeNumber(selectedValue, slice?.field.units ?? null)}
        />
        <Metric label="x" value={x} />
        <Metric label="y" value={y} />
        <Metric label="z" value={z} />
      </dl>
    </section>
  );
}

function SliceHeatmap({
  title,
  slice,
  selectedRegion,
  onSelectRegion,
}: {
  title: string;
  slice: SliceResponse;
  selectedRegion?: SelectedRegionRequest | null;
  onSelectRegion?: (slice: SliceResponse, rowIndex: number, columnIndex: number) => void;
}) {
  const displayRows = downsampleSliceValues(slice);
  return (
    <div className="slice-heatmap" role="img" aria-label={`${title} heatmap`}>
      {displayRows.map((row, displayRowIndex) => (
        <div className="heatmap-row" key={`${title}-heatmap-${displayRowIndex}`}>
          {row.map((cell, displayColumnIndex) => {
            const selected = isSelectedSliceDisplayCell(slice, selectedRegion, cell);
            return (
              <button
                type="button"
                className={`heatmap-cell${selected ? " heatmap-cell-selected" : ""}`}
                key={`${title}-heatmap-${displayRowIndex}-${displayColumnIndex}`}
                title={
                  cell.value === null ? "missing" : formatMaybeNumber(cell.value, slice.field.units)
                }
                aria-label={`Inspect ${title} row ${displayRowIndex + 1}, column ${displayColumnIndex + 1}`}
                style={sliceCellStyle(cell.value, slice)}
                onClick={() => onSelectRegion?.(slice, cell.sourceRowIndex, cell.sourceColumnIndex)}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

type DisplayHeatmapCell = {
  value: number | null;
  sourceRowIndex: number;
  sourceColumnIndex: number;
  rowStart: number;
  rowEnd: number;
  columnStart: number;
  columnEnd: number;
};

function downsampleSliceValues(slice: SliceResponse): DisplayHeatmapCell[][] {
  const values = slice.values;
  const maxRows = 28;
  const maxColumns = 60;
  const rowCount = values.length;
  const columnCount = values[0]?.length ?? 0;
  const rowStride = Math.max(1, Math.ceil(rowCount / maxRows));
  const columnStride = Math.max(1, Math.ceil(columnCount / maxColumns));

  const rows: DisplayHeatmapCell[][] = [];
  for (let rowStart = 0; rowStart < rowCount; rowStart += rowStride) {
    const rowEnd = Math.min(rowCount, rowStart + rowStride);
    const displayRow: DisplayHeatmapCell[] = [];
    for (let columnStart = 0; columnStart < columnCount; columnStart += columnStride) {
      const columnEnd = Math.min(columnCount, columnStart + columnStride);
      const summary = summarizeSliceBlock(slice, rowStart, rowEnd, columnStart, columnEnd);
      displayRow.push({
        value: summary.value,
        sourceRowIndex: summary.sourceRowIndex,
        sourceColumnIndex: summary.sourceColumnIndex,
        rowStart,
        rowEnd: rowEnd - 1,
        columnStart,
        columnEnd: columnEnd - 1,
      });
    }
    rows.push(displayRow);
  }
  return rows;
}

function summarizeSliceBlock(
  slice: SliceResponse,
  rowStart: number,
  rowEnd: number,
  columnStart: number,
  columnEnd: number,
): { value: number | null; sourceRowIndex: number; sourceColumnIndex: number } {
  const values = slice.values;
  const centerRow = Math.floor((rowStart + rowEnd - 1) / 2);
  const centerColumn = Math.floor((columnStart + columnEnd - 1) / 2);
  const fallbackRow = Math.min(Math.max(0, centerRow), Math.max(0, values.length - 1));
  const fallbackColumn = Math.min(
    Math.max(0, centerColumn),
    Math.max(0, (values[0]?.length ?? 1) - 1),
  );
  const mode = sliceAggregationMode(slice.field);
  let total = 0;
  let count = 0;
  let selectedValue: number | null = null;
  let selectedRow = fallbackRow;
  let selectedColumn = fallbackColumn;

  for (let rowIndex = rowStart; rowIndex < rowEnd; rowIndex += 1) {
    for (let columnIndex = columnStart; columnIndex < columnEnd; columnIndex += 1) {
      const value = values[rowIndex]?.[columnIndex];
      if (typeof value === "number" && Number.isFinite(value)) {
        total += value;
        count += 1;
        if (mode === "max") {
          if (selectedValue === null || value > selectedValue) {
            selectedValue = value;
            selectedRow = rowIndex;
            selectedColumn = columnIndex;
          }
        } else if (
          mode === "largest_magnitude" &&
          (selectedValue === null || Math.abs(value) > Math.abs(selectedValue))
        ) {
          selectedValue = value;
          selectedRow = rowIndex;
          selectedColumn = columnIndex;
        }
      }
    }
  }

  if (count === 0) {
    return { value: null, sourceRowIndex: fallbackRow, sourceColumnIndex: fallbackColumn };
  }

  if (mode === "mean") {
    return { value: total / count, sourceRowIndex: fallbackRow, sourceColumnIndex: fallbackColumn };
  }

  return {
    value: selectedValue,
    sourceRowIndex: selectedRow,
    sourceColumnIndex: selectedColumn,
  };
}

function sliceAggregationMode(field: VisualizableField): "max" | "largest_magnitude" | "mean" {
  if (
    field.raw_field_name === "qc" ||
    field.canonical_field_name === "cloud_water" ||
    field.raw_field_name === "qr" ||
    field.canonical_field_name === "rain_water"
  ) {
    return "max";
  }
  if (field.raw_field_name === "w" || field.canonical_field_name === "vertical_velocity") {
    return "largest_magnitude";
  }
  return "mean";
}

function OutcomeBadge({ result }: { result: ResultCard }) {
  const label = cloudOutcome(result);
  const goodOutcome = label === "Cloud formed" || label === "Deep convection formed";
  const warningOutcome = label === "No cloud formed" || label === "Deep convection not detected";
  return (
    <StatusBadge
      label={label}
      tone={goodOutcome ? "good" : warningOutcome ? "warning" : "neutral"}
    />
  );
}

function candidateStoryLabel(story: CandidateStoryId | CandidateStoryFilter): string {
  switch (story) {
    case "shallow_cumulus_candidate":
      return "Cloud-forming shallow cumulus";
    case "dry_failed_candidate":
      return "Dry failed cumulus";
    case "capped_suppressed_candidate":
      return "Capped / suppressed";
    case "humid_rainy_candidate":
      return "Humid / rainy";
    case "severe_thunderstorm_environment":
      return "Severe thunderstorm environment";
    case "supercell_environment":
      return "Supercell-like environment";
    case "high_cape_pulse_storm":
      return "High-CAPE pulse storm";
    case "dry_microburst_inverted_v":
      return "Dry microburst / inverted-V";
    case "squall_line_cold_pool_candidate":
      return "Squall-line / cold-pool candidate";
    case "elevated_convection":
      return "Elevated convection";
    case "poor_or_incomplete_candidate":
      return "Poor or incomplete";
    case "needs_review":
      return "Needs review";
    case "deep_convection_trial":
      return "Deep-convection stories";
    case "all":
      return "All screening stories";
  }
}

function candidateStoryFamilyLabel(family: CandidateStoryFamilyFilter | undefined): string {
  switch (family) {
    case "deep_convection":
      return "Deep convection stories";
    case "review":
      return "Review / incomplete";
    case "lower_atmosphere":
      return "Lower-atmosphere stories";
    case "all":
    case undefined:
      return "Story family unavailable";
  }
}

function candidateStoryFamilyForStory(story: CandidateStoryId): CandidateStoryFamilyFilter {
  if (deepConvectionStoryIds.has(story)) return "deep_convection";
  if (story === "needs_review" || story === "poor_or_incomplete_candidate") return "review";
  return "lower_atmosphere";
}

function candidateSortLabel(sort: CandidateSort): string {
  const labels: Record<CandidateSort, string> = {
    best_match: "Recommended",
    valid_time: "Valid time",
    station_id: "Station ID",
    station_name: "Station name",
    primary_story: "Primary story",
    story_family: "Story family",
    rank_score: "Rank score",
    deep_tower_opportunity: "Deep-Tower opportunity",
    confidence: "Confidence",
    support: "Evidence tier",
    package_readiness: "Package readiness",
    observed_wind_available: "Observed wind availability",
    profile_top_m_agl: "Profile top",
    lowest_level_m_agl: "Lowest usable level",
    data_completeness_score: "Data completeness",
    low_level_qv_g_kg: "Low-level qv",
    mean_qv_0_500m_g_kg: "Mean qv 0-500 m",
    mean_qv_0_1000m_g_kg: "Mean qv 0-1 km",
    surface_t_td_spread_c: "Surface T-Td spread",
    estimated_lcl_height_m_agl: "Estimated LCL",
    lapse_rate_0_1000m_c_per_km: "Low-level lapse rate",
    midlevel_lapse_rate_700_500_hpa_c_per_km: "Midlevel lapse rate",
    cap_strength_proxy: "Cap/inversion strength",
    cap_height_m_agl: "Cap/inversion height",
    bulk_shear_0_1km_m_s: "Bulk shear 0-1 km",
    bulk_shear_0_3km_m_s: "Bulk shear 0-3 km",
    bulk_shear_0_6km_m_s: "Bulk shear 0-6 km",
    midlevel_dry_layer_proxy: "Dry-layer proxy",
    dry_microburst_inverted_v_proxy: "Inverted-V proxy",
    freezing_level_m_agl: "Freezing level",
  };
  return labels[sort];
}

function supportTierLabel(support: CandidateSupportFilter): string {
  const labels: Record<CandidateSupportFilter, string> = {
    all: "All evidence tiers",
    supported: "Supported",
    weak: "Plausible / caveated",
    unavailable: "Little or no signal",
  };
  return labels[support];
}

function candidateRecipeFitForStory(
  candidate: SoundingCandidate,
  story: CandidateStoryId,
): CandidateRecipeFitDisplay {
  if (
    story === candidate.primary_story &&
    candidate.recipe_fit_status &&
    candidate.recipe_fit_label &&
    candidate.recipe_fit_summary
  ) {
    return {
      status: candidate.recipe_fit_status,
      label: candidate.recipe_fit_label,
      summary: candidate.recipe_fit_summary,
      caveats: candidate.recipe_fit_caveats ?? [],
    };
  }
  if (!candidate.package_ready || story === "poor_or_incomplete_candidate") {
    return {
      status: "blocked_profile",
      label: "blocked profile",
      summary: "This cached sounding cannot be used for a run until profile caveats are resolved.",
      caveats: ["profile_or_run_generation_blocked"],
    };
  }
  if (story === "needs_review") {
    return {
      status: "not_testable_with_current_recipes",
      label: "not testable with current experiment setup",
      summary: "This candidate needs manual screening before it maps to a current run path.",
      caveats: ["candidate_requires_manual_screening_review"],
    };
  }
  if (deepConvectionStoryIds.has(story)) {
    const caveats = [
      "deep_convection_outcome_depends_on_explicit_trigger_duration_domain_and_resolution",
      "deep_tower_benchmark_uses_idealized_warm_bubbles_not_observed_boundary",
    ];
    if (candidate.features.observed_wind_available !== true) {
      caveats.push("complete_observed_wind_profile_required_for_input_sounding");
    }
    return {
      status: "partially_testable",
      label: "testable with Deep-Tower Benchmark",
      summary:
        "This story screens deep-convection ingredients. CM1 can evolve the observed atmosphere with the explicit Deep-Tower Benchmark trigger; use surface-forced recipes when lower-boundary initiation is the question.",
      caveats,
    };
  }
  if (story === "humid_rainy_candidate") {
    return {
      status: "partially_testable",
      label: "partially testable with current observed-sounding run",
      summary:
        "The current observed-sounding path can inspect moist evolution, but later comparison needs rain-water, surface-rain, and/or reflectivity outputs.",
      caveats: ["rain_water_surface_rain_or_reflectivity_outputs_required"],
    };
  }
  if (story === "capped_suppressed_candidate") {
    return {
      status: "partially_testable",
      label: "partially testable with current observed-sounding run",
      summary:
        "The current observed-sounding path can inspect capped or suppressed evolution when cap evidence, duration, and diagnostics are adequate.",
      caveats: ["run_duration_and_diagnostics_must_be_checked_for_cap_story"],
    };
  }
  return {
    status: "partially_testable",
    label: "partially testable with current observed-sounding run",
    summary:
      "The current observed-sounding path can inspect cloud and moisture evolution under selected surface forcing, but the recipe still shapes what CM1 can test.",
    caveats: ["observed_surface_forced_evolution_is_recipe_dependent"],
  };
}

function candidateRecipeFitTone(status: CandidateRecipeFitStatus): "good" | "warning" | "neutral" {
  if (status === "testable_now") return "good";
  if (status === "partially_testable") return "neutral";
  return "warning";
}

function observedRecipeStoryId(
  selectedCandidateScreening: Record<string, unknown> | null,
): CandidateStoryId | null {
  if (!selectedCandidateScreening) return null;
  const activeStory = selectedCandidateScreening.active_story;
  if (typeof activeStory === "string" && candidateStoryIdValues.has(activeStory)) {
    return activeStory as CandidateStoryId;
  }
  const primaryStory = selectedCandidateScreening.primary_story;
  if (typeof primaryStory === "string" && candidateStoryIdValues.has(primaryStory)) {
    return primaryStory as CandidateStoryId;
  }
  return null;
}

function observedRecipeHypothesisSummary(story: CandidateStoryId | null): string {
  if (!story) {
    return "Inspect cloud, updraft, moisture, and precipitation evolution without a saved pre-run story.";
  }
  if (deepConvectionStoryIds.has(story)) {
    return "Deep-convection ingredients are present; check whether explicit thermal initiation produces deep cloud, strong updraft, and precipitation signatures.";
  }
  switch (story) {
    case "shallow_cumulus_candidate":
      return "Shallow cloud formation is plausible; check whether cloud water appears with modest vertical motion.";
    case "dry_failed_candidate":
      return "Cloud failure is plausible; check whether vertical motion occurs without meaningful cloud water.";
    case "capped_suppressed_candidate":
      return "Suppressed or delayed growth is plausible; check whether cloud stays shallow or capped.";
    case "humid_rainy_candidate":
      return "Moist cloud and precipitation processes are plausible; check cloud water, rain water aloft, surface rain, and reflectivity separately.";
    case "needs_review":
      return "The analyzer could not identify a trustworthy story; inspect manually before treating this as a comparison case.";
    case "poor_or_incomplete_candidate":
      return "The profile is incomplete or unsafe for comparison until blocking caveats are resolved.";
  }
  return "Inspect the CM1-observable output signatures that match this candidate story.";
}

function observedRecipeSignatureLabels(story: CandidateStoryId | null): string[] {
  if (!story) return [];
  if (deepConvectionStoryIds.has(story)) {
    return ["Deep cloud", "Strong updraft", "Rain water aloft", "Reflectivity"];
  }
  switch (story) {
    case "shallow_cumulus_candidate":
      return ["Shallow cloud water", "Modest vertical velocity"];
    case "dry_failed_candidate":
      return ["Vertical motion without meaningful cloud water"];
    case "capped_suppressed_candidate":
      return ["Suppressed or shallow cloud", "Limited cloud depth"];
    case "humid_rainy_candidate":
      return [
        "Cloud water",
        "Rain water aloft",
        "Surface rain or accumulated precipitation",
        "Reflectivity",
      ];
    case "needs_review":
    case "poor_or_incomplete_candidate":
      return [];
  }
  return ["Cloud water", "Vertical velocity", "Moisture evolution"];
}

function observedRecipeEvidenceSummary(
  selectedCandidateScreening: Record<string, unknown> | null,
): string {
  if (!selectedCandidateScreening) {
    return "No cached-sounding recommendation is attached.";
  }
  const interestReasons = selectedCandidateScreening.interest_reasons;
  if (Array.isArray(interestReasons)) {
    const reasons = interestReasons.filter(
      (reason): reason is string => typeof reason === "string" && reason.length > 0,
    );
    if (reasons.length > 0) return reasons.slice(0, 2).join(" ");
  }
  const interestSummary = selectedCandidateScreening.interest_summary;
  if (typeof interestSummary === "string" && interestSummary.length > 0) {
    return interestSummary;
  }
  const rankScore = selectedCandidateScreening.rank_score;
  if (typeof rankScore === "number") {
    return `${Math.round(rankScore)}% ingredient match from cached-sounding screening.`;
  }
  return "Screening evidence is attached in the candidate details.";
}

function observedRecipeFitSummary(
  selectedCandidateScreening: Record<string, unknown> | null,
  story: CandidateStoryId | null,
): string {
  if (!selectedCandidateScreening) {
    return "Inspectable, but not comparable to a saved candidate hypothesis.";
  }
  const fitSummary = selectedCandidateScreening.recipe_fit_summary;
  if (typeof fitSummary === "string" && fitSummary.length > 0) {
    return fitSummary;
  }
  if (story && deepConvectionStoryIds.has(story)) {
    return "Inspectable with the explicit Deep-Tower Benchmark trigger; deep outcomes still depend on duration, domain, resolution, and CM1 output fields.";
  }
  return "The selected observed-sounding method can inspect this story when duration, cadence, and requested fields are adequate.";
}

function observedRecipeAppliedForcing(configuration: RunConfiguration): string {
  return configuration.surface_flux_summary;
}

function candidateRecipeMismatchWarning(
  selectedCandidateScreening: Record<string, unknown> | null,
): string | null {
  if (!selectedCandidateScreening) return null;
  const activeStory =
    typeof selectedCandidateScreening.active_story === "string"
      ? selectedCandidateScreening.active_story
      : "";
  const primaryStory =
    typeof selectedCandidateScreening.primary_story === "string"
      ? selectedCandidateScreening.primary_story
      : "";
  const storyScores = candidateScreeningStoryScores(selectedCandidateScreening);
  const hasMeaningfulDeepStory =
    deepConvectionStoryIds.has(activeStory) ||
    (!activeStory &&
      (deepConvectionStoryIds.has(primaryStory) ||
        storyScores.some(
          (score) =>
            deepConvectionStoryIds.has(score.story) &&
            score.score_0_to_100 > 0 &&
            score.support !== "unavailable",
        )));
  if (hasMeaningfulDeepStory) {
    return "This candidate was screened for deep-convection potential. This run will test how it evolves under explicit thermal initiation; deep outcomes still depend on duration, domain, resolution, and diagnostics.";
  }
  const hasHumidRainyStory =
    activeStory === "humid_rainy_candidate" ||
    (!activeStory &&
      (primaryStory === "humid_rainy_candidate" ||
        storyScores.some(
          (score) =>
            score.story === "humid_rainy_candidate" &&
            score.score_0_to_100 > 0 &&
            score.support !== "unavailable",
        )));
  if (hasHumidRainyStory) {
    return "This candidate was screened as humid/rainy. Predicted rain behavior needs rain-water, surface-rain, and/or reflectivity outputs to compare later.";
  }
  return null;
}

function observedRecipeStoryLabel(
  selectedCandidateScreening: Record<string, unknown> | null,
): string {
  if (!selectedCandidateScreening) return "Uploaded observed sounding";
  if (typeof selectedCandidateScreening.active_story_label === "string") {
    return selectedCandidateScreening.active_story_label;
  }
  if (typeof selectedCandidateScreening.primary_story_label === "string") {
    return selectedCandidateScreening.primary_story_label;
  }
  if (typeof selectedCandidateScreening.active_story === "string") {
    return candidateStoryLabel(selectedCandidateScreening.active_story as CandidateStoryId);
  }
  if (typeof selectedCandidateScreening.primary_story === "string") {
    return candidateStoryLabel(selectedCandidateScreening.primary_story as CandidateStoryId);
  }
  return "Selected candidate hypothesis";
}

function candidateScreeningStoryScores(
  selectedCandidateScreening: Record<string, unknown>,
): Array<Pick<StoryScore, "story" | "score_0_to_100" | "support">> {
  if (!Array.isArray(selectedCandidateScreening.story_scores)) return [];
  return selectedCandidateScreening.story_scores.flatMap((score) => {
    if (
      score &&
      typeof score === "object" &&
      "story" in score &&
      "score_0_to_100" in score &&
      "support" in score &&
      typeof score.story === "string" &&
      typeof score.score_0_to_100 === "number" &&
      typeof score.support === "string"
    ) {
      return [
        {
          story: score.story as CandidateStoryId,
          score_0_to_100: score.score_0_to_100,
          support: score.support,
        },
      ];
    }
    return [];
  });
}

function candidateStationLabel(candidate: SoundingCandidate): string {
  return `${candidate.station_name ?? "Observed sounding"} (${candidate.station_id})`;
}

function observedSoundingLabel(observed: ObservedSoundingSummary): string {
  const station = observed.station_name
    ? `${observed.station_name} (${observed.station_id})`
    : observed.station_id;
  return `${station} - ${formatDate(observed.valid_time_utc)}`;
}

function observedSoundingLocationLabel(observed: ObservedSoundingSummary): string {
  if (
    observed.station_latitude !== null &&
    observed.station_latitude !== undefined &&
    observed.station_longitude !== null &&
    observed.station_longitude !== undefined
  ) {
    return `${formatNumber(observed.station_latitude, "deg")}, ${formatNumber(
      observed.station_longitude,
      "deg",
    )}`;
  }
  return "Not available";
}

function candidateActiveStoryId(
  candidate: SoundingCandidate,
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter,
): CandidateStoryId {
  const scopedStories = new Set(
    candidateStoryScoresForScope(candidate, storyFilter, storyFamilyFilter).map(
      (score) => score.story,
    ),
  );
  if (candidate.active_story && scopedStories.has(candidate.active_story)) {
    return candidate.active_story;
  }
  return (
    candidateActiveStoryScore(candidate, storyFilter, storyFamilyFilter)?.story ??
    candidate.primary_story
  );
}

function candidateDisplayStoryLabel(
  candidate: SoundingCandidate,
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter,
): string {
  const activeStory = candidateActiveStoryId(candidate, storyFilter, storyFamilyFilter);
  if (candidate.active_story === activeStory) {
    return (
      candidate.display_story ?? candidate.active_story_label ?? candidateStoryLabel(activeStory)
    );
  }
  return candidateStoryLabel(activeStory);
}

function candidateIngredientScore(
  candidate: SoundingCandidate,
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter = "all",
): number {
  const activeStory = candidateActiveStoryId(candidate, storyFilter, storyFamilyFilter);
  if (
    candidate.active_story === activeStory &&
    typeof candidate.ingredient_score === "number" &&
    Number.isFinite(candidate.ingredient_score)
  ) {
    return candidate.ingredient_score;
  }
  return (
    candidateActiveStoryScore(candidate, storyFilter, storyFamilyFilter)?.score_0_to_100 ??
    candidate.rank_score
  );
}

function candidateIngredientScoreLabel(
  candidate: SoundingCandidate,
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter = "all",
): string {
  if (candidateScopeIsDeepTower(storyFilter, storyFamilyFilter)) {
    return candidate.ingredient_score_label ?? "Deep-Tower opportunity";
  }
  return candidate.ingredient_score_label ?? "Ingredient score";
}

function candidateScopeIsDeepTower(
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter,
): boolean {
  return storyFilter === "deep_convection_trial" || storyFamilyFilter === "deep_convection";
}

function candidateActiveStoryScore(
  candidate: SoundingCandidate,
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter,
): StoryScore | null {
  return (
    [...candidateStoryScoresForScope(candidate, storyFilter, storyFamilyFilter)].sort(
      (left, right) => right.score_0_to_100 - left.score_0_to_100,
    )[0] ?? null
  );
}

function candidateStoryScoresForScope(
  candidate: SoundingCandidate,
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter,
): StoryScore[] {
  let scores = candidate.story_scores;
  if (storyFilter === "deep_convection_trial") {
    scores = scores.filter((score) => deepConvectionStoryIds.has(score.story));
  } else if (storyFilter !== "all") {
    scores = scores.filter((score) => score.story === storyFilter);
  }
  if (storyFamilyFilter !== "all") {
    scores = scores.filter(
      (score) => candidateStoryFamilyForStory(score.story) === storyFamilyFilter,
    );
  }
  if (storyFilter === "all" && storyFamilyFilter === "all") {
    const readyScores = scores.filter((score) => score.story !== "poor_or_incomplete_candidate");
    return readyScores.length > 0 ? readyScores : scores;
  }
  return scores;
}

function candidateInterestReasons(candidate: SoundingCandidate): string[] {
  const topReasons = candidate.top_reasons?.filter(Boolean) ?? [];
  if (topReasons.length > 0) return topReasons;
  const explicitReasons = candidate.interest_reasons?.filter(Boolean) ?? [];
  if (explicitReasons.length > 0) return explicitReasons;
  if (candidate.interest_summary) return [candidate.interest_summary];
  const evidenceReasons = candidate.evidence
    .map((item) => item.interpretation)
    .filter((reason): reason is string => Boolean(reason));
  if (evidenceReasons.length > 0) return evidenceReasons.slice(0, 3);
  return [candidate.primary_story_label];
}

function candidateDisplayCaveats(candidate: SoundingCandidate): string[] {
  const topCaveats = candidate.top_caveats?.filter(Boolean) ?? [];
  return topCaveats.length > 0 ? topCaveats : candidate.caveats;
}

function candidateKeyNote(
  candidate: SoundingCandidate,
  story: CandidateStoryId,
  recipeFit: CandidateRecipeFitDisplay,
): string {
  if (!candidate.package_ready) {
    return candidateTopLimits(candidate, story, recipeFit)[0] ?? "Needs review before run setup.";
  }
  if (candidateStoryFamilyForStory(story) === "deep_convection") {
    const opportunitySummary = candidateDeepTowerOpportunitySummary(candidate);
    if (opportunitySummary) return opportunitySummary;
    const activeSupport =
      candidate.active_story === story
        ? candidate.active_story_support
        : candidate.story_scores.find((score) => score.story === story)?.support;
    if (activeSupport === "supported") {
      return "Deep-Tower opportunity is supported; use the benchmark trigger to test the convective ceiling.";
    }
    if (activeSupport === "weak") {
      return "Caveated Deep-Tower opportunity; use the benchmark trigger to test the convective ceiling.";
    }
    return "Deep-Tower candidate; use the benchmark trigger to test the convective ceiling.";
  }
  if (
    story === "humid_rainy_candidate" ||
    story === "shallow_cumulus_candidate" ||
    story === "dry_failed_candidate" ||
    story === "capped_suppressed_candidate"
  ) {
    return "Good for a surface-forced run.";
  }
  return candidateTopLimits(candidate, story, recipeFit)[0] ?? "No major blocker found.";
}

function candidateDeepTowerOpportunitySummary(candidate: SoundingCandidate): string | null {
  const summary = candidate.features.deep_tower_opportunity_summary;
  return typeof summary === "string" && summary.length > 0 ? summary : null;
}

function candidateDeepTowerOpportunityScore(candidate: SoundingCandidate): number | null {
  if (typeof candidate.ingredient_score === "number" && Number.isFinite(candidate.ingredient_score)) {
    return candidate.ingredient_score;
  }
  const opportunity = candidate.features.deep_tower_opportunity;
  if (typeof opportunity === "number" && Number.isFinite(opportunity)) {
    return opportunity;
  }
  return null;
}

function candidateTopLimits(
  candidate: SoundingCandidate,
  story: CandidateStoryId,
  recipeFit: CandidateRecipeFitDisplay,
): string[] {
  const limits: string[] = [];
  if (!candidate.package_ready) {
    limits.push("Needs profile review before run setup.");
  }
  if (candidateStoryFamilyForStory(story) === "deep_convection") {
    limits.push("Uniform forcing may not trigger organized storms.");
  }
  for (const caveat of [...recipeFit.caveats, ...candidateDisplayCaveats(candidate)]) {
    const copy = candidatePracticalLimitCopy(caveat);
    if (copy && !limits.includes(copy)) {
      limits.push(copy);
    }
  }
  return limits.length > 0 ? limits.slice(0, 3) : ["No practical limits flagged in screening."];
}

function candidatePracticalLimitCopy(caveat: string): string | null {
  switch (caveat) {
    case "screening_is_not_cm1_outcome_prediction":
    case "candidate_screening_is_a_pre_run_hypothesis":
    case "candidate_match_uses_simple_v1_deep_convection_rules":
      return null;
    case "observed_surface_forced_evolution_is_recipe_dependent":
      return "Uniform forcing may not trigger organized storms.";
    case "observed_wind_profile_missing_or_incomplete":
      return "Needs complete wind profile.";
    case "missing_surface_level":
      return "Missing surface-level data needs review.";
    case "near_surface_discontinuity_caveat":
      return "Near-surface discontinuity can make the setup misleading.";
    default:
      return humanize(caveat);
  }
}

function candidateRunRecommendation(
  candidate: SoundingCandidate,
  story: CandidateStoryId,
  recipeFit: CandidateRecipeFitDisplay,
): { title: string; detail: string; followUp?: string } {
  if (!candidate.package_ready || recipeFit.status === "blocked_profile") {
    return {
      title: "No run recommendation yet.",
      detail: "Resolve profile limits before choosing a first CM1 run.",
    };
  }
  if (candidateStoryFamilyForStory(story) === "deep_convection") {
    const opportunityScore = candidateDeepTowerOpportunityScore(candidate);
    if (opportunityScore !== null && opportunityScore >= 70) {
      return {
        title: "Recommended Deep-Tower scout · stock CM1 iinit=3 · ~120 km · 2 h.",
        detail:
          "Disable surface fluxes and use explicit thermal initiation to test this observed atmosphere's convective ceiling.",
        followUp:
          "Inspect cloud depth, updraft, precipitation, and reflectivity before changing the trigger or resolution.",
      };
    }
    if (opportunityScore !== null && opportunityScore >= 45) {
      return {
        title:
          "Weak Deep-Tower opportunity · run for calibration or learning, not as a best cloud bet.",
        detail:
          "If deliberately running it, keep the Deep-Tower Benchmark setup comparable: stock CM1 iinit=3, ~120 km domain, 2 h, and disabled surface fluxes.",
        followUp:
          "Use the result to calibrate the selector rather than treating it as the next visual cloud-making target.",
      };
    }
    return {
      title: "Skip for Deep-Tower cloud-making unless deliberately overriding.",
      detail:
        "Manual configuration remains available; if overriding, keep the Deep-Tower Benchmark setup comparable so the outcome is interpretable.",
      followUp:
        "Spend normal cloud-making scout compute on candidates with supported Deep-Tower opportunity.",
    };
  }
  if (story === "dry_failed_candidate" || story === "capped_suppressed_candidate") {
    return {
      title: "First run: Wide 12 km · 6 h · baseline surface forcing.",
      detail: "Scout whether the boundary layer stays suppressed or mixes out.",
    };
  }
  if (recipeFit.status === "testable_now" || recipeFit.status === "partially_testable") {
    return {
      title: "First run: Wide 12 km · 6 h · baseline surface forcing.",
      detail: "Use it to inspect cloud, moisture, and precipitation response.",
    };
  }
  return {
    title: "No run recommendation yet.",
    detail: "This story is useful to inspect, but it does not map cleanly to a first run.",
  };
}

function candidateFilterTraceSummary(
  screening: ScreeningResult | null,
  filters: {
    storyFilter: CandidateStoryFilter;
    storyFamilyFilter: CandidateStoryFamilyFilter;
    supportFilter: CandidateSupportFilter;
    readinessFilter: CandidateReadinessFilter;
  },
): { summary: string; detail: string | null } {
  if (!screening) {
    return { summary: "No recommendation run loaded.", detail: null };
  }
  const trace = screening.filter_trace;
  const shown = screening.candidates.length;
  if (!trace) {
    return {
      summary: `${shown.toLocaleString()} shown from ${(
        screening.filtered_candidate_count ?? shown
      ).toLocaleString()} matching / ${(screening.total_candidate_count ?? shown).toLocaleString()} analyzed.`,
      detail: "Open a candidate to inspect the ingredients, limits, and first-run fit.",
    };
  }
  const storyStage =
    filters.storyFilter !== "all"
      ? trace.stage_counts.story_filter
      : filters.storyFamilyFilter !== "all"
        ? trace.stage_counts.story_family
        : undefined;
  const supportStage = filters.supportFilter !== "all" ? trace.stage_counts.support : undefined;
  const readinessStage =
    filters.readinessFilter !== "all" ? trace.stage_counts.readiness : undefined;
  const stationDistribution = trace.station_distribution ?? [];
  const topExcludedReasons = trace.top_excluded_reasons ?? [];
  const historyScope =
    trace.history_scope === "latest_per_station" && trace.latest_per_station
      ? `latest ${trace.latest_per_station.toLocaleString()} per station`
      : "all cached history";
  const selectedStations = trace.selected_station_count ?? stationDistribution.length;
  const selectedSoundings = trace.selected_cached_soundings ?? trace.analyzed_soundings;
  const parts = [
    `${trace.analyzed_soundings.toLocaleString()} analyzed from ${selectedSoundings.toLocaleString()} selected cached sounding${selectedSoundings === 1 ? "" : "s"}`,
    `${selectedStations.toLocaleString()} station${selectedStations === 1 ? "" : "s"}`,
    historyScope,
    storyStage !== undefined
      ? `${storyStage.toLocaleString()} matched ${candidateTraceScopeLabel(
          filters.storyFilter,
          filters.storyFamilyFilter,
        )}`
      : null,
    supportStage !== undefined
      ? `${supportStage.toLocaleString()} ${supportTierLabel(filters.supportFilter).toLowerCase()}`
      : null,
    readinessStage !== undefined
      ? `${readinessStage.toLocaleString()} ${humanize(filters.readinessFilter)}`
      : null,
    `${shown.toLocaleString()} shown`,
  ].filter((part): part is string => part !== null);
  const mainExclusion = topExcludedReasons[0];
  const detail =
    shown === 1 && mainExclusion
      ? `Only one candidate remains; the largest filter impact was ${mainExclusion.reason} (${mainExclusion.count.toLocaleString()} removed).`
      : `Trace includes ${trace.story_score_records.toLocaleString()} story-score records across ${stationDistribution.length.toLocaleString()} shown station${stationDistribution.length === 1 ? "" : "s"}.`;
  return {
    summary: parts.join(" · "),
    detail,
  };
}

function candidateTraceScopeLabel(
  storyFilter: CandidateStoryFilter,
  storyFamilyFilter: CandidateStoryFamilyFilter,
): string {
  if (storyFilter !== "all") return candidateStoryLabel(storyFilter).toLowerCase();
  if (storyFamilyFilter !== "all")
    return candidateStoryFamilyLabel(storyFamilyFilter).toLowerCase();
  return "selected intent";
}

function boundedInteger(value: string, min: number, max: number, fallback: number): number {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function candidateEvidenceValue(item: EvidenceItem): string {
  if (item.value === null || item.value === undefined || item.value === "") return "not available";
  return `${String(item.value)}${item.units ? ` ${item.units}` : ""}`;
}

function candidateFeatureValue(candidate: SoundingCandidate, key: string, units: string): string {
  const value = candidate.features[key];
  if (typeof value === "number") return formatNumber(value, units);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string" && value.length > 0) return value;
  return "Not available";
}

function observedSoundingParseFromCandidate(
  candidate: SoundingCandidate,
  selectedSounding: ObservedSoundingRecord,
): ObservedSoundingParseResponse {
  return {
    source_provider: candidate.source_provider,
    source_format: candidate.source_format,
    uploaded_filename: candidate.source_file_name,
    available_soundings: [
      {
        station_id: selectedSounding.station_id,
        valid_time_utc: selectedSounding.valid_time_utc,
        source_time_text: selectedSounding.source_time_text,
        num_levels: selectedSounding.levels.length,
        pressure_source: "observed_sounding_candidate",
        non_pressure_source: "observed_sounding_candidate",
      },
    ],
    selected_sounding: selectedSounding,
  };
}

function candidateScreeningMetadata(
  candidate: SoundingCandidate,
  savedCandidate?: SavedSoundingCandidate,
  activeStory?: CandidateStoryId,
): Record<string, unknown> {
  const selectedActiveStory = activeStory ?? candidate.active_story ?? candidate.primary_story;
  const activeScore = candidate.story_scores.find((score) => score.story === selectedActiveStory);
  return {
    candidate_id: candidate.candidate_id,
    station_id: candidate.station_id,
    station_name: candidate.station_name ?? null,
    valid_time_utc: candidate.valid_time_utc,
    saved_candidate_id: savedCandidate?.saved_candidate_id ?? null,
    screening_version: candidate.screening_version,
    primary_story: candidate.primary_story,
    active_story: selectedActiveStory,
    active_story_label:
      activeScore?.label ??
      (candidate.active_story === selectedActiveStory
        ? (candidate.active_story_label ?? candidate.display_story)
        : null) ??
      candidate.primary_story_label,
    display_story: candidate.display_story ?? null,
    matched_story_ids: candidate.matched_story_ids ?? [],
    story_scores: candidate.story_scores,
    rank_score: candidate.rank_score,
    active_story_score: candidate.active_story_score ?? null,
    ingredient_score: candidate.ingredient_score ?? null,
    ingredient_score_label: candidate.ingredient_score_label ?? null,
    active_story_support: candidate.active_story_support ?? null,
    confidence: candidate.confidence,
    features: candidate.features,
    evidence: candidate.evidence,
    caveats: candidate.caveats,
    top_reasons: candidate.top_reasons ?? [],
    top_caveats: candidate.top_caveats ?? [],
    evidence_summary: candidate.evidence_summary ?? [],
    interest_summary: candidate.interest_summary ?? null,
    interest_reasons: candidate.interest_reasons ?? [],
    discovery_bucket: candidate.discovery_bucket ?? null,
    recipe_fit_status: candidate.recipe_fit_status ?? null,
    recipe_fit_label: candidate.recipe_fit_label ?? null,
    recipe_fit_summary: candidate.recipe_fit_summary ?? null,
    recipe_fit_caveats: candidate.recipe_fit_caveats ?? [],
    source_file_name: candidate.source_file_name,
    source_file_hash: candidate.source_file_hash,
    saved_tags: savedCandidate?.tags ?? [],
    saved_notes: savedCandidate?.notes ?? null,
  };
}

function runUserMetadataFromCandidateScreening(
  candidateScreening: Record<string, unknown> | null,
): { tags: string[]; notes: string | null } | null {
  if (!candidateScreening) return null;
  const tags = Array.isArray(candidateScreening.saved_tags)
    ? candidateScreening.saved_tags.filter((tag): tag is string => typeof tag === "string")
    : [];
  const notes =
    typeof candidateScreening.saved_notes === "string" && candidateScreening.saved_notes.trim()
      ? candidateScreening.saved_notes.trim()
      : null;
  if (tags.length === 0 && !notes) return null;
  return { tags, notes };
}

function createRunPlanItemId(): string {
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `run-plan-${random}`;
}

function runPlanItemFromUploadedSounding({
  observedSounding,
  source,
  runConfiguration,
  controls,
  selectedCandidateScreening,
}: {
  observedSounding: ObservedSoundingRecord;
  source: AtmosphereSourcePath;
  runConfiguration: RunConfigurationInput;
  controls: Record<string, string | number | boolean>;
  selectedCandidateScreening: Record<string, unknown> | null;
}): RunPlanItem {
  return {
    id: createRunPlanItemId(),
    selected: true,
    source,
    candidate: null,
    savedCandidate: null,
    observedSounding,
    candidateScreening: selectedCandidateScreening,
    activeStory: observedRecipeStoryId(selectedCandidateScreening),
    runRecipe: observedRecipeForSelection(selectedCandidateScreening, runConfiguration),
    runConfiguration,
    controls,
    queueTarget: "local",
    status: "planned",
    message: null,
    dryRun: null,
    blockedPreRunValidationReport: null,
  };
}

function runPlanSourceFromCandidateScreening(
  selectedCandidateScreening: Record<string, unknown> | null,
): AtmosphereSourcePath {
  if (selectedCandidateScreening) {
    return selectedCandidateScreening.saved_candidate_id
      ? "saved_candidates"
      : "cached_recommendations";
  }
  return "upload_igra_text";
}

function candidateScreeningStationLabel(
  candidateScreening: Record<string, unknown> | null,
): string | null {
  if (!candidateScreening) return null;
  const stationId =
    typeof candidateScreening.station_id === "string" ? candidateScreening.station_id : null;
  const stationName =
    typeof candidateScreening.station_name === "string" && candidateScreening.station_name
      ? candidateScreening.station_name
      : null;
  if (stationName && stationId) return `${stationName} (${stationId})`;
  return stationName ?? stationId;
}

function selectedObservedSoundingStationLabel(
  observedSounding: ObservedSoundingRecord,
  candidateScreening: Record<string, unknown> | null,
): string {
  return (
    candidateScreeningStationLabel(candidateScreening) ??
    (observedSounding.station_name
      ? `${observedSounding.station_name} (${observedSounding.station_id})`
      : observedSounding.station_id)
  );
}

function searchIntentFilters(intent: SearchIntent): {
  story: CandidateStoryFilter;
  storyFamily: CandidateStoryFamilyFilter;
  support: CandidateSupportFilter;
} {
  switch (intent) {
    case "deep_convection":
      return {
        story: "all",
        storyFamily: "deep_convection",
        support: "all",
      };
    case "humid_rainy":
      return { story: "humid_rainy_candidate", storyFamily: "all", support: "all" };
    case "dry_microburst":
      return { story: "dry_microburst_inverted_v", storyFamily: "all", support: "all" };
    case "shallow_boundary_layer":
      return {
        story: "shallow_cumulus_candidate",
        storyFamily: "lower_atmosphere",
        support: "all",
      };
    case "best_overall":
      return { story: "all", storyFamily: "all", support: "all" };
  }
}

function batchQueueSummary({
  queued,
  lanStarted,
  failed,
  skipped,
}: {
  queued: number;
  lanStarted: number;
  failed: number;
  skipped: number;
}): string {
  const parts = [
    queued > 0 ? `${queued.toLocaleString()} queued locally` : null,
    lanStarted > 0 ? `${lanStarted.toLocaleString()} sent to LAN worker` : null,
    failed > 0 ? `${failed.toLocaleString()} package failed validation or queueing` : null,
    skipped > 0 ? `${skipped.toLocaleString()} skipped` : null,
  ].filter((part): part is string => part !== null);
  return parts.length > 0 ? parts.join(" · ") : "No run-plan items were queued.";
}

function runPlanStatusLabel(status: RunPlanItemStatus): string {
  switch (status) {
    case "planned":
      return "Planned";
    case "packaging":
      return "Creating package";
    case "queued":
      return "Queued";
    case "lan_started":
      return "LAN worker started";
    case "package_failed":
      return "Package failed";
    case "skipped":
      return "Skipped";
  }
}

function runPlanStatusTone(status: RunPlanItemStatus): "good" | "warning" | "neutral" {
  if (status === "queued" || status === "lan_started") return "good";
  if (status === "package_failed" || status === "skipped") return "warning";
  return "neutral";
}

function runPlanRecipeMetadata(item: RunPlanItem): {
  recipeId: string;
  recipeDisplayName: string;
  assumptionSetId: string;
  assumptionMode: string;
  assumptionsSummary: string;
  requiredOutputFields: string[];
  missingRequiredOutputFields: string[];
  recipeCaveats: string[];
} {
  const report = item.dryRun?.report;
  const staticMetadata = staticRecipeMetadata(item.runRecipe);
  return {
    recipeId: report?.recipe_id ?? staticMetadata.recipeId,
    recipeDisplayName: report?.recipe_display_name ?? staticMetadata.recipeDisplayName,
    assumptionSetId: report?.assumption_set_id ?? staticMetadata.assumptionSetId,
    assumptionMode: report?.assumption_mode ?? staticMetadata.assumptionMode,
    assumptionsSummary: compactRecipeAssumptions(report?.recipe_assumptions),
    requiredOutputFields: report?.required_output_fields ?? staticMetadata.requiredOutputFields,
    missingRequiredOutputFields: report?.missing_required_output_fields ?? [],
    recipeCaveats: report?.recipe_caveats ?? staticMetadata.recipeCaveats,
  };
}

function staticRecipeMetadata(runRecipe: ObservedRunRecipe = CURRENT_OBSERVED_RUN_RECIPE): {
  recipeId: string;
  recipeDisplayName: string;
  assumptionSetId: string;
  assumptionMode: string;
  requiredOutputFields: string[];
  recipeCaveats: string[];
} {
  if (runRecipe === "deep_tower_benchmark") {
    return {
      recipeId: "deep_tower_benchmark_v0",
      recipeDisplayName: "Deep-Tower Benchmark v0",
      assumptionSetId: "deep_tower_benchmark_v0_assumptions",
      assumptionMode: "explicit_thermal_initiation",
      requiredOutputFields: [
        "qv",
        "qc",
        "w",
        "qr",
        "rain",
        "dbz",
        "u",
        "v",
        "th",
        "updraft_helicity",
      ],
      recipeCaveats: [
        "Explicit initiation is supplied with CM1 iinit=3 three warm bubbles.",
        "The warm bubbles are an idealized trigger, not a real front, dryline, terrain feature, or observed boundary.",
        "Surface heat/moisture fluxes, radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0.",
      ],
    };
  }
  if (runRecipe === "differential_surface_forced_evolution") {
    return {
      recipeId: "differential_surface_forced_evolution_v0",
      recipeDisplayName: "Differential Surface-Forced Evolution v0",
      assumptionSetId: "differential_surface_forced_evolution_v0_assumptions",
      assumptionMode: "differential_surface_forced_evolution",
      requiredOutputFields: [
        "qv",
        "qc",
        "w",
        "qr",
        "rain",
        "dbz",
        "hfx",
        "qfx",
        "u",
        "v",
        "th",
        "updraft_helicity",
      ],
      recipeCaveats: [
        "No artificial atmospheric trigger is applied.",
        "A centered lower-boundary heat/moisture forcing patch is applied through Cloud Chamber's external CM1 source customization.",
        "The patch is an idealized surface contrast, not a real land-surface or radiation model.",
      ],
    };
  }
  return {
    recipeId: "observed_surface_forced_evolution_v0",
    recipeDisplayName: "Observed Surface-Forced Evolution v0",
    assumptionSetId: "observed_surface_forced_evolution_v0_assumptions",
    assumptionMode: "observed_surface_forced_evolution",
    requiredOutputFields: ["qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx"],
    recipeCaveats: [
      "No artificial atmospheric trigger is applied.",
      "Surface fluxes use numeric constant uniform lower-boundary proxy values; they are not validated place/time surface-energy inputs.",
      "Radiation, terrain, GIS surface initialization, and large-scale forcing are not part of v0.",
    ],
  };
}

function compactRecipeAssumptions(assumptions: Record<string, unknown> | undefined): string {
  const trigger = assumptions?.trigger;
  const surfaceFluxes = assumptions?.surface_fluxes;
  const radiation = assumptions?.radiation;
  const largeScaleForcing = assumptions?.large_scale_forcing;
  const triggerLabel =
    trigger &&
    typeof trigger === "object" &&
    "mode" in trigger &&
    trigger.mode === "cm1_iinit_3_three_warm_bubbles"
      ? "CM1 iinit=3 three warm bubbles"
      : "No artificial trigger";
  const fluxLabel =
    surfaceFluxes &&
    typeof surfaceFluxes === "object" &&
    "mode" in surfaceFluxes &&
    surfaceFluxes.mode === DIFFERENTIAL_SURFACE_FORCING_MODE
      ? "differential surface forcing patch"
      : surfaceFluxes &&
          typeof surfaceFluxes === "object" &&
          "mode" in surfaceFluxes &&
          surfaceFluxes.mode === DISABLED_SURFACE_FORCING_MODE
        ? "surface fluxes disabled"
        : "numeric uniform surface fluxes";
  const radiationLabel =
    radiation &&
    typeof radiation === "object" &&
    "mode" in radiation &&
    radiation.mode === "disabled"
      ? "radiation disabled"
      : "radiation disabled";
  const forcingLabel =
    largeScaleForcing &&
    typeof largeScaleForcing === "object" &&
    "mode" in largeScaleForcing &&
    largeScaleForcing.mode === "none"
      ? "no large-scale forcing"
      : "no large-scale forcing";
  return `${triggerLabel} · ${fluxLabel} · ${radiationLabel} · ${forcingLabel}`;
}

function preRunValidationStatusLabel(status: string): string {
  if (status === "valid") return "Valid";
  if (status === "caveated") return "Valid with caveats";
  if (status === "blocked") return "Blocked";
  return humanize(status);
}

function preRunValidationTone(status: string): "good" | "warning" | "neutral" {
  if (status === "valid") return "good";
  if (status === "caveated" || status === "blocked") return "warning";
  return "neutral";
}

function preRunValidationRunShapeLabel(
  runShape: NonNullable<PreRunValidationReport["run_shape_validation"]>,
): string {
  const parts = [
    runShape.duration ? humanize(runShape.duration) : null,
    runShape.domain ? humanize(runShape.domain) : null,
    runShape.horizontal_cell_count
      ? `${runShape.horizontal_cell_count.toLocaleString()} x ${runShape.horizontal_cell_count.toLocaleString()} horizontal cells`
      : null,
    runShape.output_cadence ? `${humanize(runShape.output_cadence)} output` : null,
    runShape.diagnostic_set ? `${humanize(runShape.diagnostic_set)} diagnostics` : null,
    typeof runShape.estimated_frames === "number"
      ? `${runShape.estimated_frames.toLocaleString()} saved frames`
      : null,
  ].filter((part): part is string => Boolean(part));
  return parts.length > 0 ? parts.join(" · ") : "Not resolved";
}

function compactList(values: string[] | undefined | null, fallback: string): string {
  return values?.length ? values.join(", ") : fallback;
}

function StatusBadge({ label, tone }: { label: string; tone: "good" | "warning" | "neutral" }) {
  return <span className={`status-badge status-badge-${tone}`}>{label}</span>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

const PROCESS_MODES: ProcessMode[] = [
  "thermal_fate",
  "cloud_water",
  "updrafts",
  "cloud_lifecycle",
  "cap",
  "moisture",
  "buoyancy",
  "deep_breakthrough",
  "precipitation_feedback",
];

type ProcessSupport =
  | "supported"
  | "candidate"
  | "insufficient_evidence"
  | "unsupported_missing_fields"
  | "future";

type ProcessModeSummary = {
  support: ProcessSupport;
  evidenceType: string;
  source: string;
  description: string;
  annotations: string[];
  caveats: string[];
};

type ProcessModeClassification = ProcessModeSummary & {
  mode: ProcessMode;
  primary: boolean;
  primaryReason: string;
};

function processModeSummary(
  mode: ProcessMode,
  result: ResultCard,
  catalog: FieldCatalogResponse | null,
  selectedField: VisualizableField | undefined,
  slice: SliceResponse | null,
): ProcessModeSummary {
  const fields = new Set(catalog?.available_fields.map((field) => field.raw_field_name) ?? []);
  const caveats = [...result.caveats];
  const thermalLabel = result.thermal_fate_label ?? "Insufficient evidence";
  const confidence = normalizeProcessSupport(result.thermal_fate_confidence);
  const fieldSource = selectedField
    ? `${selectedField.raw_field_name} on native ${selectedField.native_grid}`
    : "No selected field";
  const sliceAnnotation = slice
    ? `Active slice ${slice.selection.orientation} shows ${slice.field.raw_field_name} min ${formatMaybeNumber(
        slice.stats.min,
        slice.field.units,
      )}, max ${formatMaybeNumber(slice.stats.max, slice.field.units)}.`
    : "No active slice summary is available yet.";

  if (mode === "thermal_fate") {
    const hasResultSummary = Boolean(result.thermal_fate_label || result.diagnostics_summary);
    const summarySupport =
      confidence === "insufficient_evidence" && hasResultSummary ? "candidate" : confidence;
    return {
      support: summarySupport,
      evidenceType: "backend process diagnostics",
      source: "Result Card process fields from ingested CM1 output",
      description: `${thermalLabel}. ${
        result.main_limiting_factor && result.main_limiting_factor !== "unknown"
          ? `Main limiting factor: ${result.main_limiting_factor}.`
          : "No supported main limiting factor is available yet."
      }`,
      annotations: [
        `Diagnostics summary: ${result.diagnostics_summary ?? "Unavailable"}`,
        `Cloud: ${cloudOutcome(result)}; rain water aloft: ${rainWaterOutcome(result)}`,
      ],
      caveats,
    };
  }

  if (mode === "cloud_water") {
    return {
      support: fields.has("qc") ? "supported" : "unsupported_missing_fields",
      evidenceType: "direct CM1 field plus derived threshold diagnostics",
      source: fieldSource,
      description: fields.has("qc")
        ? "Cloud-water overlay uses direct qc output with the documented cloud threshold."
        : "Cloud-water overlay is unavailable because qc is missing for this result.",
      annotations: [
        `Max qc: ${formatScientific(result.max_qc_kg_kg, "kg/kg")}`,
        `First cloud time: ${formatSeconds(result.first_cloud_time_seconds)}`,
        sliceAnnotation,
      ],
      caveats: fields.has("qc") ? caveats : [...caveats, "missing_visualization_field:qc"],
    };
  }

  if (mode === "updrafts") {
    return {
      support: fields.has("w") ? "supported" : "unsupported_missing_fields",
      evidenceType: "direct CM1 vertical-velocity field",
      source: fieldSource,
      description: fields.has("w")
        ? "Updraft overlay uses direct w output and max/min vertical velocity summaries."
        : "Updraft overlay is unavailable because w is missing for this result.",
      annotations: [
        `Max w: ${formatNumber(result.max_w_m_s, "m/s")}`,
        `Min w: ${formatNumber(result.min_w_m_s, "m/s")}`,
        sliceAnnotation,
      ],
      caveats: fields.has("w") ? caveats : [...caveats, "missing_visualization_field:w"],
    };
  }

  if (mode === "cloud_lifecycle") {
    const available = result.first_cloud_time_seconds !== null || result.max_qc_kg_kg !== null;
    return {
      support: available ? "candidate" : "insufficient_evidence",
      evidenceType: "derived cloud lifecycle diagnostics",
      source: "Ingested result diagnostics",
      description: available
        ? "Cloud lifecycle uses first cloud time, qc summaries, cloud fraction, and slice annotations where available."
        : "Cloud lifecycle diagnostics are not available for this result.",
      annotations: [
        `First cloud time: ${formatSeconds(result.first_cloud_time_seconds)}`,
        `Max qc: ${formatScientific(result.max_qc_kg_kg, "kg/kg")}`,
        sliceAnnotation,
      ],
      caveats,
    };
  }

  if (mode === "cap") {
    const capped =
      result.scenario_id.includes("capped") || result.controls.cap_strength === "stronger";
    return {
      support: capped ? "candidate" : "insufficient_evidence",
      evidenceType: "scenario/control proxy plus cloud-top diagnostics",
      source: "Scenario metadata and derived diagnostics",
      description: capped
        ? "Cap/inversion overlay is a candidate process view; current data suggests cap context but does not directly diagnose inhibition."
        : "Cap/inversion overlay needs stronger-cap metadata or cap-relative diagnostics before making a process claim.",
      annotations: [
        `Cap strength: ${String(result.controls.cap_strength ?? "not recorded")}`,
        `Thermal Fate label: ${thermalLabel}`,
      ],
      caveats: [...caveats, "cap_layer_annotation_is_proxy_without_full_cap_diagnostics"],
    };
  }

  if (mode === "moisture") {
    const moistureLimited =
      result.main_limiting_factor === "moisture" ||
      result.scenario_id.includes("dry-failed") ||
      result.caveats.some((caveat) => caveat.includes("moisture"));
    return {
      support: moistureLimited ? "candidate" : "unsupported_missing_fields",
      evidenceType: moistureLimited
        ? "scenario/control proxy plus cloud-water and updraft diagnostics"
        : "unavailable moisture diagnostic group",
      source: moistureLimited
        ? "Dry Failed / moisture-limited result metadata and derived diagnostics"
        : "Required humidity, qv, RH, or saturation-deficit fields were not ingested",
      description: moistureLimited
        ? "Moisture limitation is a candidate explanation for this contrast case because thermals are present while cloud water and rain stay below threshold."
        : "Moisture / saturation diagnostics need qv, RH, or saturation-deficit fields before they can be selected as a focus.",
      annotations: [
        `Main limiting factor: ${String(result.main_limiting_factor ?? "not recorded")}`,
        `Cloud: ${cloudOutcome(result)}; max w: ${formatNumber(result.max_w_m_s, "m/s")}`,
      ],
      caveats: moistureLimited
        ? [...caveats, "moisture_limitation_is_candidate_without_direct_qv_or_rh_diagnostics"]
        : [...caveats, "moisture_unsupported_missing_fields"],
    };
  }

  if (mode === "precipitation_feedback") {
    const rainWaterDetected = rainWaterOutcome(result) === "Rain water aloft detected";
    return {
      support: "future",
      evidenceType: "qr/rain and downdraft proxy diagnostics",
      source: rainWaterDetected
        ? "Rain-water aloft summary exists, but cold-pool/outflow evidence is not available"
        : "Required rain, downdraft, cold-pool, and outflow evidence is not available",
      description: rainWaterDetected
        ? "Rain water aloft is present, but precipitation-feedback needs downdraft/cold-pool evidence before it can be selected as a normal focus."
        : "Precipitation feedback is future work for this result because rain-water, cold-pool, and outflow diagnostics are not available.",
      annotations: [
        `Rain water aloft: ${rainWaterOutcome(result)}`,
        `Min w: ${formatNumber(result.min_w_m_s, "m/s")}`,
      ],
      caveats: [...caveats, "precipitation_feedback_requires_downdraft_and_cold_pool_diagnostics"],
    };
  }

  const unavailableLabels: Record<ProcessMode, string> = {
    thermal_fate: "",
    cloud_water: "",
    updrafts: "",
    cloud_lifecycle: "",
    cap: "",
    moisture: "Moisture / saturation diagnostics need qv/RH or saturation-deficit fields.",
    buoyancy: "Buoyancy diagnostics need thermodynamic fields and a documented buoyancy method.",
    deep_breakthrough:
      "Deep-breakthrough diagnostics need CAPE/CIN/LFC/EL and sustained-updraft context.",
    precipitation_feedback:
      "Precipitation-feedback diagnostics need rain, downdraft, cold-pool, and outflow evidence.",
  };
  return {
    support:
      mode === "buoyancy" || mode === "deep_breakthrough" ? "future" : "unsupported_missing_fields",
    evidenceType: "unavailable diagnostic group",
    source: "Required source fields were not ingested",
    description: unavailableLabels[mode],
    annotations: ["Unavailable diagnostics are shown explicitly rather than hidden."],
    caveats: [...caveats, `${mode}_unsupported_missing_fields`],
  };
}

function processModeClassifications(
  result: ResultCard,
  catalog: FieldCatalogResponse | null,
  selectedField: VisualizableField | undefined,
  slice: SliceResponse | null,
): ProcessModeClassification[] {
  return PROCESS_MODES.map((mode) => {
    const summary = processModeSummary(mode, result, catalog, selectedField, slice);
    const primary = processModeIsPrimary(mode, summary, result);
    return {
      mode,
      ...summary,
      primary,
      primaryReason: primary
        ? "Supported or useful candidate for this result."
        : unavailableProcessReason(mode, summary),
    };
  });
}

function processModeIsPrimary(
  mode: ProcessMode,
  summary: ProcessModeSummary,
  result: ResultCard,
): boolean {
  if (summary.support === "supported") return true;
  if (summary.support !== "candidate") return false;
  if (mode === "precipitation_feedback") return false;
  if (mode === "cap") {
    return result.scenario_id.includes("capped") || result.controls.cap_strength === "stronger";
  }
  if (mode === "moisture") {
    return (
      result.main_limiting_factor === "moisture" ||
      result.scenario_id.includes("dry-failed") ||
      result.caveats.some((caveat) => caveat.includes("moisture"))
    );
  }
  return true;
}

function unavailableProcessReason(mode: ProcessMode, summary: ProcessModeSummary): string {
  if (summary.support === "future") {
    return "Future diagnostic: required backend evidence is not implemented for this result family.";
  }
  if (summary.support === "unsupported_missing_fields") {
    return "Missing required CM1 fields or derived diagnostics for this selected result.";
  }
  if (summary.support === "insufficient_evidence") {
    return "Evidence is present but not enough to make this a useful primary focus.";
  }
  if (summary.support === "candidate" && mode === "precipitation_feedback") {
    return "Rain alone is not enough to select precipitation feedback without downdraft/cold-pool evidence.";
  }
  return "Not useful as a primary focus for this selected result.";
}

function processModeLabel(mode: ProcessMode): string {
  const labels: Record<ProcessMode, string> = {
    thermal_fate: "Thermal Fate summary",
    cloud_water: "Cloud Water",
    updrafts: "Updrafts",
    moisture: "Moisture / Saturation",
    buoyancy: "Buoyancy",
    cap: "Cap / Inversion",
    cloud_lifecycle: "Cloud Lifecycle",
    deep_breakthrough: "Deep Breakthrough",
    precipitation_feedback: "Precipitation Feedback",
  };
  return labels[mode];
}

function normalizeProcessSupport(value: string | null | undefined): ProcessSupport {
  if (
    value === "supported" ||
    value === "candidate" ||
    value === "insufficient_evidence" ||
    value === "unsupported_missing_fields" ||
    value === "future"
  ) {
    return value;
  }
  return "insufficient_evidence";
}

function processSupportLabel(value: ProcessSupport): string {
  const labels: Record<ProcessSupport, string> = {
    supported: "Supported",
    candidate: "Candidate",
    insufficient_evidence: "Insufficient evidence",
    unsupported_missing_fields: "Unavailable",
    future: "Future",
  };
  return labels[value];
}

function selectionFromSlice(
  slice: SliceResponse,
  rowIndex: number,
  columnIndex: number,
  regionType: "point" | "column",
): SelectedRegionRequest {
  const orientation = slice.selection.orientation;
  if (orientation === "horizontal") {
    return {
      regionType,
      xIndex: columnIndex,
      yIndex: rowIndex,
      zIndex: slice.selection.selected_index,
      neighborhood: regionType === "point" ? 0 : 1,
    };
  }
  if (orientation === "vertical_x") {
    return {
      regionType,
      xIndex: columnIndex,
      yIndex: slice.selection.selected_index,
      zIndex: rowIndex,
      neighborhood: regionType === "point" ? 0 : 1,
    };
  }
  return {
    regionType,
    xIndex: slice.selection.selected_index,
    yIndex: columnIndex,
    zIndex: rowIndex,
    neighborhood: regionType === "point" ? 0 : 1,
  };
}

function isSelectedSliceCell(
  slice: SliceResponse,
  selectedRegion: SelectedRegionRequest | null | undefined,
  rowIndex: number,
  columnIndex: number,
): boolean {
  if (!selectedRegion) return false;
  const candidate = selectionFromSlice(slice, rowIndex, columnIndex, "point");
  if (selectedRegion.regionType === "box") {
    return (
      candidate.xIndex !== undefined &&
      candidate.yIndex !== undefined &&
      candidate.zIndex !== undefined &&
      candidate.xIndex >= (selectedRegion.xStart ?? -Infinity) &&
      candidate.xIndex <= (selectedRegion.xEnd ?? Infinity) &&
      candidate.yIndex >= (selectedRegion.yStart ?? -Infinity) &&
      candidate.yIndex <= (selectedRegion.yEnd ?? Infinity) &&
      candidate.zIndex >= (selectedRegion.zStart ?? -Infinity) &&
      candidate.zIndex <= (selectedRegion.zEnd ?? Infinity)
    );
  }
  return (
    selectedRegion.xIndex === candidate.xIndex &&
    selectedRegion.yIndex === candidate.yIndex &&
    (selectedRegion.regionType === "column" || selectedRegion.zIndex === candidate.zIndex)
  );
}

function isSelectedSliceDisplayCell(
  slice: SliceResponse,
  selectedRegion: SelectedRegionRequest | null | undefined,
  cell: DisplayHeatmapCell,
): boolean {
  if (!selectedRegion) return false;
  for (let rowIndex = cell.rowStart; rowIndex <= cell.rowEnd; rowIndex += 1) {
    for (let columnIndex = cell.columnStart; columnIndex <= cell.columnEnd; columnIndex += 1) {
      if (isSelectedSliceCell(slice, selectedRegion, rowIndex, columnIndex)) return true;
    }
  }
  return false;
}

function axisSelectionLabel(axis: AxisSelection | null): string {
  if (!axis) return "Unavailable";
  const coordinate =
    axis.start_coordinate === axis.end_coordinate
      ? formatAxisCoordinate(axis.start_coordinate)
      : `${formatAxisCoordinate(axis.start_coordinate)} to ${formatAxisCoordinate(axis.end_coordinate)}`;
  const index =
    axis.start_index === axis.end_index
      ? `${axis.dimension}[${axis.start_index}]`
      : `${axis.dimension}[${axis.start_index}..${axis.end_index}]`;
  return `${index}; ${coordinate}${axis.units ? ` ${axis.units}` : ""}`;
}

function formatAxisCoordinate(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return "unknown";
  const numericValue = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numericValue) ? formatCompactNumber(numericValue) : String(value);
}

function indexOrUnavailable(index: number | undefined): string {
  return index === undefined ? "Unavailable" : `index ${index}`;
}

function formatRatio(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  return `${formatCompactNumber(value * 100)}%`;
}

function formatSignedSeconds(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatSeconds(value)}`;
}

function _dedupeStrings(values: string[]): string[] {
  return [...new Set(values)];
}

function parseTags(value: string): string[] {
  return _dedupeStrings(
    value
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
  );
}

const DURATION_OPTIONS = [
  { value: "smoke_1h", label: "Smoke check (1 h)" },
  { value: "scout_2h", label: "Scout evolution (2 h)" },
  { value: "short_6h", label: "Short evolution (6 h)" },
  { value: "standard_12h", label: "Standard evolution (12 h)" },
  { value: "long_24h", label: "Long evolution (24 h)" },
];

const HORIZONTAL_CELL_OPTIONS = [
  { value: "cells_64", label: "Scout (64 x 64)" },
  { value: "cells_96", label: "Light (96 x 96)" },
  { value: "cells_120", label: "Deep-tower scout (120 x 120)" },
  { value: "cells_128", label: "Standard (128 x 128)" },
  { value: "cells_192", label: "Detailed (192 x 192)" },
  { value: "cells_256", label: "High detail (256 x 256)" },
  { value: "cells_384", label: "Very high detail (384 x 384)" },
];

const DOMAIN_OPTIONS = [
  { value: "local_6km", label: "Local 6 km" },
  { value: "wide_12km", label: "Wide 12 km" },
  { value: "regional_60km", label: "Regional 60 km" },
  { value: "regional_120km", label: "Regional 120 km" },
  { value: "deep_tower_120km", label: "Deep tower 120 km" },
];

const OUTPUT_CADENCE_OPTIONS = [
  { value: "sparse_60min", label: "Sparse (60 min)" },
  { value: "standard_15min", label: "Standard (15 min)" },
  { value: "detailed_5min", label: "Detailed (5 min)" },
];

const SURFACE_FORCING_OPTIONS = [
  { value: UNIFORM_SURFACE_FORCING_MODE, label: "Uniform surface forcing" },
  { value: DIFFERENTIAL_SURFACE_FORCING_MODE, label: "Differential surface patch" },
  { value: DISABLED_SURFACE_FORCING_MODE, label: "Disabled surface fluxes" },
];

function defaultRunConfigurationForSelection(scenarioId: string): RunConfigurationInput {
  if (scenarioId === OBSERVED_SOUNDING_EXPERIMENT_ID) {
    return { ...DEFAULT_OBSERVED_RUN_CONFIGURATION };
  }
  return { ...DEFAULT_SHALLOW_RUN_CONFIGURATION };
}

function defaultRunConfigurationForCandidateScreening(
  selectedCandidateScreening: Record<string, unknown> | null,
): RunConfigurationInput {
  if (selectedCandidateUsesDeepTowerRecipe(selectedCandidateScreening)) {
    return { ...DEFAULT_DEEP_TOWER_RUN_CONFIGURATION };
  }
  return { ...DEFAULT_OBSERVED_RUN_CONFIGURATION };
}

function runRecipeForRunConfiguration(configuration: RunConfigurationInput): ObservedRunRecipe {
  const surfaceForcingMode = surfaceForcingModeValue(configuration.surface_forcing_mode);
  if (surfaceForcingMode === DIFFERENTIAL_SURFACE_FORCING_MODE) {
    return "differential_surface_forced_evolution";
  }
  if (surfaceForcingMode === DISABLED_SURFACE_FORCING_MODE) {
    return "deep_tower_benchmark";
  }
  return CURRENT_OBSERVED_RUN_RECIPE;
}

function observedRecipeForSelection(
  selectedCandidateScreening: Record<string, unknown> | null,
  configuration: RunConfigurationInput,
): ObservedRunRecipe {
  if (configuration.surface_forcing_mode === DIFFERENTIAL_SURFACE_FORCING_MODE) {
    return "differential_surface_forced_evolution";
  }
  return runRecipeForRunConfiguration(configuration);
}

function selectedCandidateUsesDeepTowerRecipe(
  selectedCandidateScreening: Record<string, unknown> | null,
): boolean {
  const story = observedRecipeStoryId(selectedCandidateScreening);
  return Boolean(story && deepConvectionStoryIds.has(story));
}

function previewRunConfiguration(configuration: RunConfigurationInput): RunConfiguration {
  const duration = durationValue(configuration.duration);
  const horizontalCells = horizontalCellValue(configuration.horizontal_cell_count);
  const domain = domainValue(configuration.domain_size);
  const cadence = cadenceValue(configuration.output_cadence);
  const diagnosticSet = { value: "full" };
  const surfaceForcingMode = surfaceForcingModeValue(configuration.surface_forcing_mode);
  const surfaceFluxEnabled = surfaceForcingMode !== DISABLED_SURFACE_FORCING_MODE;
  const deepTowerShape =
    surfaceForcingMode === DISABLED_SURFACE_FORCING_MODE &&
    configuration.domain_size === "deep_tower_120km";
  const heatFlux = surfaceFluxEnabled
    ? numericConfigurationValue(configuration.surface_heat_flux_k_m_s, 8.0e-3)
    : 0;
  const moistureFlux = surfaceFluxEnabled
    ? numericConfigurationValue(configuration.surface_moisture_flux_g_g_m_s, 5.2e-5)
    : 0;
  const timeStepSeconds = numericConfigurationValue(
    configuration.time_step_seconds,
    deepTowerShape ? 6 : 3,
  );
  const nx = horizontalCells.cells;
  const ny = horizontalCells.cells;
  const dxM = (domain.xKm * 1000) / nx;
  const dyM = (domain.yKm * 1000) / ny;
  const gridCellCount = nx * ny * domain.nz;
  const expectedFrames = Math.floor(duration.seconds / cadence.seconds) + 1;
  const caveats: string[] = [];
  if (duration.mode === "smoke") {
    caveats.push("short_smoke_mode_is_for_package_health_not_science_evolution");
  }
  if (duration.mode === "science" && duration.seconds >= 21600) {
    caveats.push("science_run_configuration_minimum_duration_6h");
  }
  if (duration.mode === "science" && duration.seconds < 21600) {
    caveats.push("short_scout_duration_for_initial_deep_tower_chase");
  }
  if (domain.value === "deep_tower_120km") {
    caveats.push("storm_scale_domain_for_explicit_deep_tower_initiation");
  }
  if (
    horizontalCells.cells >= 256 ||
    domain.value === "wide_12km" ||
    domain.value === "regional_60km" ||
    domain.value === "regional_120km"
  ) {
    caveats.push("configuration_better_suited_to_larger_compute");
  }
  if (heatFlux < 0 || moistureFlux < 0) {
    caveats.push("surface_flux_values_must_be_non_negative");
  }
  if (timeStepSeconds !== 3) {
    caveats.push("non_default_timestep_target_requires_like_for_like_campaign_evidence");
  }
  const patchShape = "circle";
  const patchRadiusM = numericConfigurationValue(configuration.surface_patch_radius_m, 1500);
  const patchRadiusXM = patchRadiusM;
  const patchRadiusYM = patchRadiusM;
  const patchTaperM = numericConfigurationValue(configuration.surface_patch_taper_width_m, 500);
  const patchRampSeconds = numericConfigurationValue(
    configuration.surface_patch_ramp_seconds,
    1800,
  );
  const patchHeatPerturbation = numericConfigurationValue(
    configuration.surface_patch_heat_flux_perturbation_k_m_s,
    4.0e-2,
  );
  const patchMoisturePerturbation = numericConfigurationValue(
    configuration.surface_patch_moisture_flux_perturbation_g_g_m_s,
    5.0e-5,
  );
  let surfaceForcingPatch: SurfaceForcingPatch | null = null;
  if (surfaceForcingMode === DIFFERENTIAL_SURFACE_FORCING_MODE) {
    surfaceForcingPatch = {
      schema_version: "surface_forcing_patch_v0",
      shape: patchShape,
      center_x_m: 0,
      center_y_m: 0,
      radius_x_m: patchRadiusXM,
      radius_y_m: patchRadiusYM,
      taper_function: "raised_cosine",
      taper_width_m: patchTaperM,
      ramp_seconds: patchRampSeconds,
      background_heat_flux_k_m_s: heatFlux,
      background_moisture_flux_g_g_m_s: moistureFlux,
      heat_flux_perturbation_k_m_s: patchHeatPerturbation,
      moisture_flux_perturbation_g_g_m_s: patchMoisturePerturbation,
      domain_x_m: domain.xKm * 1000,
      domain_y_m: domain.yKm * 1000,
      dx_m: dxM,
      dy_m: dyM,
      support_status: "requires_cm1_source_customization",
      cm1_application_status: "source_customization_required_at_launch",
      caveats: [
        "differential_surface_forcing_patch_not_real_land_surface_or_radiation",
        "differential_surface_forcing_patch_requires_cm1_source_customization",
      ],
    };
    if (patchRadiusXM < 3 * dxM || patchRadiusYM < 3 * dyM) {
      caveats.push("surface_patch_must_span_at_least_three_grid_cells");
    }
    if (
      patchRadiusXM + patchTaperM > (domain.xKm * 1000) / 2 ||
      patchRadiusYM + patchTaperM > (domain.yKm * 1000) / 2
    ) {
      caveats.push("surface_patch_radius_and_taper_must_fit_inside_domain");
    }
    if (patchHeatPerturbation < 0 || patchMoisturePerturbation < 0) {
      caveats.push("surface_patch_perturbations_must_be_non_negative");
    }
    if (patchHeatPerturbation === 0 && patchMoisturePerturbation === 0) {
      caveats.push("surface_patch_requires_heat_or_moisture_perturbation");
    }
    if (patchRampSeconds <= 0 || patchRampSeconds > duration.seconds) {
      caveats.push("surface_patch_ramp_must_be_positive_and_within_run_duration");
    }
  }
  const surfaceFluxCm1Values: RunConfigurationSurfaceFluxCM1Values = {
    isfcflx: surfaceFluxEnabled ? 1 : 0,
    sfcmodel: surfaceFluxEnabled ? 1 : 0,
    oceanmodel: surfaceFluxEnabled ? 1 : 0,
    set_flx: surfaceFluxEnabled ? 1 : 0,
    cnst_shflx: heatFlux,
    cnst_shflx_units: "K m/s",
    cnst_lhflx: moistureFlux,
    cnst_lhflx_units: "g/g m/s",
    set_znt: 0,
    cnst_znt: 0,
    set_ust: surfaceFluxEnabled ? 1 : 0,
    cnst_ust: 0.28,
  };
  const cm1Values: RunConfigurationCM1Values = {
    nx,
    ny,
    nz: domain.nz,
    dx_m: dxM,
    dy_m: dyM,
    dz_m: domain.dzM,
    stretch_z: domain.stretchZ,
    str_bot_m: domain.strBotM,
    str_top_m: domain.strTopM,
    dz_bot_m: domain.dzBotM,
    dz_top_m: domain.dzTopM,
    model_top_m: domain.modelTopM,
    domain_x_km: domain.xKm,
    domain_y_km: domain.yKm,
    time_step_seconds: timeStepSeconds,
    runtime_seconds: duration.seconds,
    output_cadence_seconds: cadence.seconds,
    restart_cadence_seconds: Math.max(cadence.seconds, Math.min(duration.seconds, 10800)),
    rayleigh_damping_start_m: deepTowerShape ? 15000 : 12000,
    expected_output_frames: expectedFrames,
    grid_cell_count: gridCellCount,
  };
  const hours = Number((duration.seconds / 3600).toFixed(1));
  const cadenceMinutes = Number((cadence.seconds / 60).toFixed(1));
  return {
    ...configuration,
    configuration_id: [
      configuration.duration,
      configuration.horizontal_cell_count,
      configuration.domain_size,
      configuration.output_cadence,
      diagnosticSet.value,
      surfaceForcingMode,
    ].join("__"),
    mode: duration.mode,
    label: `${duration.label}; ${domain.label}; ${horizontalCells.label}; ${formatMeters(dxM)} dx/dy; ${cadence.label}`,
    duration_seconds: duration.seconds,
    output_cadence_seconds: cadence.seconds,
    diagnostic_set: diagnosticSet.value,
    cost_runtime_summary: `${hours.toLocaleString()} h model time, ${gridCellCount.toLocaleString()} cells, ${cadenceMinutes.toLocaleString()} min saved-output cadence`,
    output_volume_summary: `${expectedFrames.toLocaleString()} saved frames, full output fields, ${gridCellCount.toLocaleString()} cells per frame`,
    cm1_values: cm1Values,
    surface_heat_flux_k_m_s: heatFlux,
    surface_moisture_flux_g_g_m_s: moistureFlux,
    surface_flux_mode: surfaceForcingMode,
    surface_flux_summary:
      surfaceForcingMode === DIFFERENTIAL_SURFACE_FORCING_MODE && surfaceForcingPatch
        ? `Differential warm/moist surface patch; source customization required at launch; background H ${formatCompactNumber(heatFlux)} K m/s, M ${formatCompactNumber(moistureFlux)} g/g m/s; patch +H ${formatCompactNumber(patchHeatPerturbation)} K m/s, +M ${formatCompactNumber(patchMoisturePerturbation)} g/g m/s; ${formatMeters(patchRadiusXM)} x ${formatMeters(patchRadiusYM)} ${patchShape}`
        : surfaceForcingMode === DISABLED_SURFACE_FORCING_MODE
          ? "Surface heat/moisture flux forcing disabled"
          : `Surface heat flux ${formatCompactNumber(heatFlux)} K m/s; surface moisture flux ${formatCompactNumber(moistureFlux)} g/g m/s; constant uniform proxy`,
    surface_flux_cm1_values: surfaceFluxCm1Values,
    surface_forcing_patch: surfaceForcingPatch,
    surface_flux_caveats:
      surfaceForcingMode === DIFFERENTIAL_SURFACE_FORCING_MODE
        ? [
            "differential_surface_forcing_patch_not_real_land_surface_or_radiation",
            "differential_surface_forcing_patch_requires_cm1_source_customization",
            "differential_surface_forcing_patch_requires_emitted_flux_and_convergence_validation",
          ]
        : surfaceForcingMode === DISABLED_SURFACE_FORCING_MODE
          ? []
          : [
              "surface_flux_proxy_constant_uniform_not_place_time_energy_budget",
              "surface_flux_proxy_not_real_land_surface_or_evaporation_model",
              "surface_flux_proxy_values_need_local_smoke_validation",
            ],
    caveats,
  };
}

function numericConfigurationValue(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function surfaceForcingModeValue(value: string): string {
  if (value === DIFFERENTIAL_SURFACE_FORCING_MODE) return DIFFERENTIAL_SURFACE_FORCING_MODE;
  if (value === DISABLED_SURFACE_FORCING_MODE) return DISABLED_SURFACE_FORCING_MODE;
  return UNIFORM_SURFACE_FORCING_MODE;
}

function durationValue(value: string): {
  seconds: number;
  mode: "smoke" | "science";
  label: string;
} {
  if (value === "smoke_1h") return { seconds: 3600, mode: "smoke", label: "Smoke check" };
  if (value === "scout_2h") return { seconds: 7200, mode: "science", label: "Scout evolution" };
  if (value === "standard_12h") {
    return { seconds: 43200, mode: "science", label: "Standard evolution" };
  }
  if (value === "long_24h") return { seconds: 86400, mode: "science", label: "Long evolution" };
  return { seconds: 21600, mode: "science", label: "Short evolution" };
}

function horizontalCellValue(value: string): { cells: number; label: string } {
  if (value === "cells_64") return { cells: 64, label: "Scout 64 x 64" };
  if (value === "cells_96") return { cells: 96, label: "Light 96 x 96" };
  if (value === "cells_120") return { cells: 120, label: "Deep-tower scout 120 x 120" };
  if (value === "cells_192") return { cells: 192, label: "Detailed 192 x 192" };
  if (value === "cells_256") return { cells: 256, label: "High detail 256 x 256" };
  if (value === "cells_384") return { cells: 384, label: "Very high detail 384 x 384" };
  return { cells: 128, label: "Standard 128 x 128" };
}

function domainValue(value: string): {
  value: string;
  xKm: number;
  yKm: number;
  nz: number;
  dzM: number;
  stretchZ: number;
  strBotM: number;
  strTopM: number;
  dzBotM: number;
  dzTopM: number;
  modelTopM: number;
  label: string;
} {
  if (value === "wide_12km") {
    return {
      value,
      xKm: 12.8,
      yKm: 12.8,
      nz: 100,
      dzM: 40,
      stretchZ: 1,
      strBotM: 2000,
      strTopM: 18000,
      dzBotM: 40,
      dzTopM: 600,
      modelTopM: 18000,
      label: "Wide 12 km",
    };
  }
  if (value === "regional_60km") {
    return {
      value,
      xKm: 60,
      yKm: 60,
      nz: 100,
      dzM: 40,
      stretchZ: 1,
      strBotM: 2000,
      strTopM: 18000,
      dzBotM: 40,
      dzTopM: 600,
      modelTopM: 18000,
      label: "Regional 60 km",
    };
  }
  if (value === "regional_120km") {
    return {
      value,
      xKm: 120,
      yKm: 120,
      nz: 100,
      dzM: 40,
      stretchZ: 1,
      strBotM: 2000,
      strTopM: 18000,
      dzBotM: 40,
      dzTopM: 600,
      modelTopM: 18000,
      label: "Regional 120 km",
    };
  }
  if (value === "deep_tower_120km") {
    return {
      value,
      xKm: 120,
      yKm: 120,
      nz: 40,
      dzM: 500,
      stretchZ: 0,
      strBotM: 0,
      strTopM: 2000,
      dzBotM: 125,
      dzTopM: 500,
      modelTopM: 20000,
      label: "Storm 120 km",
    };
  }
  return {
    value: "local_6km",
    xKm: 6.4,
    yKm: 6.4,
    nz: 100,
    dzM: 40,
    stretchZ: 1,
    strBotM: 2000,
    strTopM: 18000,
    dzBotM: 40,
    dzTopM: 600,
    modelTopM: 18000,
    label: "Local 6 km",
  };
}

function cadenceValue(value: string): { seconds: number; label: string } {
  if (value === "sparse_60min") return { seconds: 3600, label: "Sparse 60 min" };
  if (value === "detailed_5min") return { seconds: 300, label: "Detailed 5 min" };
  return { seconds: 900, label: "Standard 15 min" };
}

function runConfigurationGridSummary(configuration: RunConfiguration): string {
  const values = configuration.cm1_values;
  return `${values.nx} x ${values.ny} x ${values.nz}; dx/dy ${formatMeters(values.dx_m)}; ${runConfigurationVerticalSummary(values)}`;
}

function runConfigurationTimingSummary(configuration: RunConfiguration): string {
  const values = configuration.cm1_values;
  return `${formatModelTime(values.runtime_seconds)} runtime; ${formatSeconds(values.output_cadence_seconds)} output; ${values.expected_output_frames.toLocaleString()} saved frames; ${formatSeconds(values.time_step_seconds)} timestep`;
}

function runConfigurationFieldSummary(configuration: RunConfiguration): string {
  return `Full output fields; ${configuration.cm1_values.expected_output_frames.toLocaleString()} saved frames`;
}

function formatSeconds(value: number | null): string {
  if (value === null) return "Unavailable";
  return `${value.toLocaleString()} s`;
}

function runConfigurationLabel(configuration: RunConfiguration | null | undefined): string {
  if (!configuration) return "Run configuration unavailable";
  return configuration.label || humanize(configuration.configuration_id);
}

function resultRunConfigurationLabel(configuration: RunConfiguration): string {
  return runConfigurationLabel(configuration);
}

function runConfigurationSummaryGrid(details: RunConfigurationSummary): string {
  return `${details.nx} x ${details.ny} x ${details.nz}; dx/dy ${formatMeters(details.dx_m)}; ${runConfigurationSummaryVertical(details)}`;
}

function runConfigurationVerticalSummary(values: RunConfigurationCM1Values): string {
  if (values.stretch_z === 1) {
    return `top ${formatKilometers(values.model_top_m)}, dz ${formatMeters(values.dz_bot_m)} to ${formatMeters(values.dz_top_m)} stretched`;
  }
  return `top ${formatKilometers(values.model_top_m)}, dz ${formatMeters(values.dz_m)}`;
}

function runConfigurationSummaryVertical(details: RunConfigurationSummary): string {
  if (details.stretch_z === 1 && details.dz_bot_m !== undefined && details.dz_top_m !== undefined) {
    return `top ${formatKilometers(details.model_top_m)}, dz ${formatMeters(details.dz_bot_m)} to ${formatMeters(details.dz_top_m)} stretched`;
  }
  return `top ${formatKilometers(details.model_top_m)}, dz ${formatMeters(details.dz_m)}`;
}

function runConfigurationSummaryTiming(details: RunConfigurationSummary): string {
  return `${formatSeconds(details.runtime_seconds)} runtime; ${details.output_cadence_seconds.toLocaleString()} s output; ${details.expected_output_frames.toLocaleString()} saved frames; ${details.time_step_seconds.toLocaleString()} s timestep`;
}

function runConfigurationSummaryMultiplier(details: RunConfigurationSummary): string {
  return `${details.grid_cell_multiplier_vs_default.toLocaleString()}x grid, ${details.output_frame_multiplier_vs_default.toLocaleString()}x saved frames, ${details.estimated_output_volume_multiplier_vs_default.toLocaleString()}x output volume vs default`;
}

function formatMeters(value: number): string {
  const text = value.toFixed(3).replace(/\.?0+$/, "");
  return `${text} m`;
}

function formatKilometers(value: number): string {
  const kilometers = value / 1000;
  const text = kilometers.toFixed(3).replace(/\.?0+$/, "");
  return `${text} km`;
}

function formatScientific(value: number | null, units: string): string {
  if (value === null) return "Unavailable";
  return `${value.toExponential(3)}${units ? ` ${units}` : ""}`;
}

function formatNumber(value: number | null, units: string): string {
  if (value === null) return "Unavailable";
  const formatted = Number(value.toFixed(3)).toLocaleString();
  return units ? `${formatted} ${units}` : formatted;
}

function formatMaybeNumber(value: number | null, units: string | null): string {
  if (value === null) return "Unavailable";
  const suffix = units ? ` ${units}` : "";
  return `${formatCompactNumber(value)}${suffix}`;
}

function formatCompactNumber(value: number): string {
  if (Math.abs(value) > 0 && Math.abs(value) < 0.001) {
    return value.toExponential(3);
  }
  return Number(value.toFixed(4)).toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value.toLocaleString()} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let size = value / 1024;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  const digits = size >= 10 ? 1 : 2;
  return `${Number(size.toFixed(digits)).toLocaleString()} ${units[unitIndex]}`;
}

function formatTimeValue(value: number | string | null): string {
  if (value === null) return "Time unavailable";
  if (typeof value === "number") return `${value.toLocaleString()} s`;
  return value;
}

function runIdFromPackage(dryRun: DryRunResponse): string {
  return dryRun.package_dir.split("/").filter(Boolean).at(-1) ?? dryRun.report.scenario_id;
}

function userFacingRunWorkflowStatus(status: RunStatusResponse): string {
  if (status.lifecycle_state === "queued") return "Queued";
  if (status.lifecycle_state === "running") return "Running";
  if (status.lifecycle_state === "completed") {
    return status.product_state === "completed_cm1_result"
      ? "Completed CM1 result"
      : "Completed with no usable output";
  }
  if (status.lifecycle_state === "failed") return "Failed";
  if (status.lifecycle_state === "canceled") return "Canceled";
  return humanize(status.lifecycle_state);
}

function normalize(value: number, min: number, max: number): number {
  if (max <= min) return 0.5;
  return (value - min) / (max - min);
}

function extentLabel(pointCloud: PointCloudResponse | null, coordinate: string): string {
  const extent = pointCloud?.coordinate_extents[coordinate];
  if (!extent) return "Unavailable";
  const suffix = extent.units ? ` ${extent.units}` : "";
  return `${formatCompactNumber(extent.min)} to ${formatCompactNumber(extent.max)}${suffix}`;
}

function verticalExtentLabel(pointCloud: PointCloudResponse | null): string {
  const extent =
    pointCloud?.coordinate_extents.zh ??
    pointCloud?.coordinate_extents.zf ??
    pointCloud?.coordinate_extents.z;
  if (!extent) return "Unavailable";
  const suffix = extent.units ? ` ${extent.units}` : "";
  return `${formatCompactNumber(extent.min)} to ${formatCompactNumber(extent.max)}${suffix}`;
}

function verticalCoordinateUnit(pointCloud: PointCloudResponse | null): string | null {
  return (
    pointCloud?.coordinate_units.zh ??
    pointCloud?.coordinate_units.zf ??
    pointCloud?.coordinate_units.z ??
    null
  );
}

function pointCloudFieldSummary(pointCloud: PointCloudResponse): string {
  const units = pointCloud.field.units ?? "";
  const maxValue = formatMaybeNumber(pointCloud.stats.field_max_value, units);
  const threshold = formatScientific(pointCloud.selection.threshold, units);
  return `Current field max: ${maxValue}. Visible points above ${threshold}: ${pointCloud.stats.source_count.toLocaleString()}.`;
}

function emptyPointCloudStatus(
  pointCloud: PointCloudResponse,
  selectedEncoding: ThreeDScalarEncoding,
): string {
  const maxValue = formatMaybeNumber(
    pointCloud.stats.field_max_value,
    selectedEncoding.field.units ?? "",
  );
  const threshold = formatScientific(
    pointCloud.selection.threshold,
    selectedEncoding.field.units ?? "",
  );
  return `${selectedEncoding.field.display_name} max is ${maxValue}; no points are above ${threshold}`;
}

function maxPointLocationLabel(pointCloud: PointCloudResponse | null): string {
  const location = pointCloud?.stats.max_value_location;
  if (!location) return "Unavailable";
  const units = verticalCoordinateUnit(pointCloud) ?? "";
  return `x ${formatCompactNumber(location.x)}, y ${formatCompactNumber(location.y)}, z ${formatCompactNumber(
    location.z,
  )}${units ? ` ${units}` : ""}, value ${formatCompactNumber(location.value)}`;
}

function heatmapScaleClass(field: VisualizableField): string {
  if (field.raw_field_name === "w" || field.canonical_field_name === "vertical_velocity") {
    return "heatmap-scale-velocity";
  }
  if (field.raw_field_name === "dbz" || field.canonical_field_name === "reflectivity") {
    return "heatmap-scale-reflectivity";
  }
  if (field.canonical_field_name === "temperature") {
    return "heatmap-scale-temperature";
  }
  if (field.canonical_field_name === "potential_temperature") {
    return "heatmap-scale-potential-temperature";
  }
  if (field.raw_field_name === "qv" || field.canonical_field_name === "water_vapor") {
    return "heatmap-scale-water-vapor";
  }
  if (isSurfaceRainField(field)) {
    return "heatmap-scale-surface-rain";
  }
  if (field.raw_field_name === "qc" || field.canonical_field_name === "cloud_water") {
    return "heatmap-scale-cloud-water";
  }
  if (field.raw_field_name === "qr" || field.canonical_field_name === "rain_water") {
    return "heatmap-scale-rain-water";
  }
  return "heatmap-scale-default";
}

function sliceCellStyle(value: number | null, slice: SliceResponse): CSSProperties {
  if (value === null) {
    return { background: "rgba(255, 255, 255, 0.36)" };
  }

  if (
    slice.field.raw_field_name === "w" ||
    slice.field.canonical_field_name === "vertical_velocity"
  ) {
    const maxMagnitude = Math.max(
      Math.abs(slice.stats.min ?? value),
      Math.abs(slice.stats.max ?? value),
      Number.EPSILON,
    );
    const scaled = Math.max(-1, Math.min(1, value / maxMagnitude));
    if (scaled >= 0) {
      return {
        background: `rgba(${224 - scaled * 96}, ${242 - scaled * 86}, ${236 - scaled * 132}, ${0.58 + scaled * 0.34})`,
      };
    }
    const magnitude = Math.abs(scaled);
    return {
      background: `rgba(${229 - magnitude * 90}, ${238 - magnitude * 112}, ${247 - magnitude * 88}, ${0.58 + magnitude * 0.32})`,
    };
  }

  if (slice.field.raw_field_name === "dbz" || slice.field.canonical_field_name === "reflectivity") {
    return { background: radarReflectivityBackground(value) };
  }

  const min = slice.stats.min ?? value;
  const max = slice.stats.max ?? value;
  const normalized = normalize(value, min, max);
  if (
    slice.field.canonical_field_name === "temperature" ||
    slice.field.canonical_field_name === "potential_temperature"
  ) {
    return { background: temperatureBackground(normalized) };
  }

  const intensity = Math.sqrt(Math.max(0, normalized));
  if (intensity < 0.015) {
    return { background: "rgba(234, 244, 248, 0.72)" };
  }
  return { background: scalarMagnitudeBackground(slice.field, intensity) };
}

function sliceLegendMinimum(slice: SliceResponse): string {
  if (slice.field.raw_field_name === "dbz" || slice.field.canonical_field_name === "reflectivity") {
    return "0 dBZ";
  }
  return formatMaybeNumber(slice.stats.min, slice.field.units);
}

function sliceLegendMaximum(slice: SliceResponse): string {
  if (slice.field.raw_field_name === "dbz" || slice.field.canonical_field_name === "reflectivity") {
    return "60+ dBZ";
  }
  return formatMaybeNumber(slice.stats.max, slice.field.units);
}

function radarReflectivityBackground(dbz: number): string {
  const stops = [
    { value: 0, color: [37, 97, 199] },
    { value: 10, color: [46, 184, 208] },
    { value: 20, color: [56, 169, 65] },
    { value: 30, color: [245, 220, 51] },
    { value: 40, color: [237, 92, 31] },
    { value: 50, color: [194, 27, 42] },
    { value: 60, color: [165, 45, 188] },
  ];
  const alpha = 0.72;
  if (!Number.isFinite(dbz)) return "rgba(255, 255, 255, 0.36)";
  if (dbz <= stops[0].value) return `rgba(${stops[0].color.join(", ")}, ${alpha})`;
  for (let index = 1; index < stops.length; index += 1) {
    const lower = stops[index - 1];
    const upper = stops[index];
    if (dbz <= upper.value) {
      const amount = (dbz - lower.value) / (upper.value - lower.value);
      const color = lower.color.map((component, componentIndex) =>
        Math.round(component + (upper.color[componentIndex] - component) * amount),
      );
      return `rgba(${color.join(", ")}, ${alpha})`;
    }
  }
  return `rgba(${stops[stops.length - 1].color.join(", ")}, ${alpha})`;
}

function scalarMagnitudeBackground(field: VisualizableField, intensity: number): string {
  const alpha = 0.58 + intensity * 0.34;
  let start = [234, 244, 248];
  let end = [180, 239, 228];
  if (field.raw_field_name === "qr" || field.canonical_field_name === "rain_water") {
    start = [231, 239, 255];
    end = [134, 116, 217];
  } else if (field.raw_field_name === "qv" || field.canonical_field_name === "water_vapor") {
    start = [232, 248, 245];
    end = [77, 170, 146];
  } else if (isSurfaceRainField(field)) {
    start = [229, 242, 255];
    end = [46, 116, 190];
  }
  const color = start.map((component, index) =>
    Math.round(component + (end[index] - component) * intensity),
  );
  return `rgba(${color.join(", ")}, ${alpha})`;
}

function temperatureBackground(intensity: number): string {
  const clamped = Math.max(0, Math.min(1, intensity));
  const cold = [74, 143, 232];
  const middle = [214, 189, 105];
  const warm = [240, 143, 78];
  const lower = clamped < 0.5 ? cold : middle;
  const upper = clamped < 0.5 ? middle : warm;
  const amount = clamped < 0.5 ? clamped * 2 : (clamped - 0.5) * 2;
  const color = lower.map((component, index) =>
    Math.round(component + (upper[index] - component) * amount),
  );
  return `rgba(${color.join(", ")}, ${0.52 + clamped * 0.34})`;
}

function formatDate(value: string | null): string {
  if (!value) return "Time unavailable";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

function sectionLabel(section: WorkspaceSection): string {
  const labels: Record<WorkspaceSection, string> = {
    build: "Build",
    results: "Results",
    explore: "Explore",
  };
  return labels[section];
}

const DEFAULT_RESULTS_FILTERS: ResultsFilterState = {
  search: "",
  scenario: "all",
  cloud: "all",
  rain: "all",
  sort: "newest",
};

function prioritizeResults(results: ResultCard[]): ResultCard[] {
  return [...results].sort((left, right) => resultPriority(right) - resultPriority(left));
}

function filterAndSortResults(results: ResultCard[], filters: ResultsFilterState): ResultCard[] {
  const query = filters.search.trim().toLowerCase();
  return [...results]
    .filter((result) => resultMatchesSearch(result, query))
    .filter(
      (result) =>
        filters.scenario === "all" || resultScenarioFilterValue(result) === filters.scenario,
    )
    .filter((result) =>
      matchesBooleanFilter(cloudOutcome(result), filters.cloud, "Cloud formed", "No cloud formed"),
    )
    .filter((result) =>
      matchesBooleanFilter(
        rainWaterOutcome(result),
        filters.rain,
        "Rain water aloft detected",
        "No rain water aloft detected",
      ),
    )
    .sort((left, right) => compareResults(left, right, filters.sort));
}

function resultsFiltersActive(filters: ResultsFilterState): boolean {
  return JSON.stringify(filters) !== JSON.stringify(DEFAULT_RESULTS_FILTERS);
}

function resultScenarioOptions(results: ResultCard[]): Array<{ value: string; label: string }> {
  const seen = new Map<string, string>();
  for (const result of results) {
    seen.set(
      resultScenarioFilterValue(result),
      result.scenario_name ?? humanize(result.scenario_id),
    );
  }
  return [...seen.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((left, right) => left.label.localeCompare(right.label));
}

function resultScenarioFilterValue(result: ResultCard): string {
  if (result.input_source === "observed_sounding") return "input_source:observed_sounding";
  return `scenario:${result.scenario_id}`;
}

function resultMatchesSearch(result: ResultCard, query: string): boolean {
  if (!query) return true;
  return resultSearchText(result).includes(query);
}

function resultSearchText(result: ResultCard): string {
  return [
    result.name,
    result.run_id,
    result.result_id,
    result.scenario_id,
    result.scenario_name,
    resultRunConfigurationLabel(result.run_configuration),
    result.tags.join(" "),
    result.notes,
    result.input_source_label,
    result.observed_sounding?.station_id,
    result.observed_sounding?.station_name,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function matchesBooleanFilter(
  value: string,
  filter: ResultsBooleanFilter,
  yesValue: string,
  noValue: string,
): boolean {
  if (filter === "all") return true;
  if (filter === "yes") return value === yesValue;
  if (filter === "no") return value === noValue;
  return value === "Unknown" || value.endsWith(" unavailable");
}

function compareResults(left: ResultCard, right: ResultCard, sort: ResultsSortKey): number {
  if (sort === "oldest") return dateSortValue(left) - dateSortValue(right);
  if (sort === "name") return left.name.localeCompare(right.name);
  if (sort === "scenario") {
    return (left.scenario_name ?? left.scenario_id).localeCompare(
      right.scenario_name ?? right.scenario_id,
    );
  }
  if (sort === "first_cloud")
    return nullableNumberSort(resultFirstCloudTime(left), resultFirstCloudTime(right), "asc");
  if (sort === "max_qc") return nullableNumberSort(resultMaxQc(left), resultMaxQc(right), "desc");
  if (sort === "max_updraft")
    return nullableNumberSort(resultMaxUpdraft(left), resultMaxUpdraft(right), "desc");
  if (sort === "rain_onset")
    return nullableNumberSort(resultRainOnsetTime(left), resultRainOnsetTime(right), "asc");
  if (sort === "latest_output")
    return nullableNumberSort(resultLatestOutputTime(left), resultLatestOutputTime(right), "desc");
  return dateSortValue(right) - dateSortValue(left);
}

function nullableNumberSort(
  left: number | null,
  right: number | null,
  direction: "asc" | "desc",
): number {
  if (left === null && right === null) return 0;
  if (left === null) return 1;
  if (right === null) return -1;
  return direction === "asc" ? left - right : right - left;
}

function dateSortValue(result: ResultCard): number {
  return new Date(result.completed_at ?? result.created_at).getTime();
}

function resultPriority(result: ResultCard): number {
  let score = 0;
  if (result.scenario_id === "baseline-shallow-cumulus") score += 30;
  if (result.source_lifecycle_state === "completed") score += 20;
  if (cloudOutcome(result) === "Cloud formed") score += 20;
  if (result.saved || result.protected) score += 10;
  score += new Date(result.completed_at ?? result.created_at).getTime() / 1_000_000_000_000;
  return score;
}

function isValidatedQuickLookBaseline(result: ResultCard): boolean {
  return (
    resultInputSource(result) === "generated_reference" &&
    result.scenario_id === "baseline-shallow-cumulus" &&
    result.source_lifecycle_state === "completed" &&
    cloudOutcome(result) === "Cloud formed"
  );
}

function isDryFailedContrast(result: ResultCard): boolean {
  return (
    result.scenario_id === "dry-failed-cumulus" &&
    result.source_lifecycle_state === "completed" &&
    cloudOutcome(result) === "No cloud formed" &&
    rainWaterOutcome(result) === "No rain water aloft detected" &&
    (result.max_w_m_s ?? 0) > 0
  );
}

function resultStory(result: ResultCard): string {
  const comparison = result.candidate_hypothesis_comparison;
  if (comparison) {
    return `${comparison.cm1_outcome} Candidate hypothesis ${comparison.match_status_label.toLowerCase()}.`;
  }
  if (hasDeepConvectionDiagnostics(result) && result.science_summary?.cm1_outcome) {
    return result.science_summary.cm1_outcome;
  }
  if (isDryFailedContrast(result)) {
    return "Thermals rose, but low-level moisture stayed too dry for meaningful cloud water or rain.";
  }
  if (isValidatedQuickLookBaseline(result)) {
    return "Cloud water formed in the validated reference baseline; vertical motion and rain were both detected.";
  }
  if (cloudOutcome(result) === "Cloud formed") {
    return "Cloud water formed during this run. Open it in Explore to inspect the cloud and updraft structure.";
  }
  if (cloudOutcome(result) === "No cloud formed") {
    return "No cloud formed by the current diagnostic threshold. The vertical velocity field may still explain the thermal behavior.";
  }
  return result.diagnostics_summary ?? "Diagnostics are not available yet.";
}

function compactScienceSummary(result: ResultCard): string {
  if (hasDeepConvectionDiagnostics(result)) {
    const parts = [
      deepConvectionOutcome(result),
      resultMaxUpdraft(result) !== null
        ? `max updraft ${formatNumber(resultMaxUpdraft(result), "m/s")}`
        : null,
      resultRainOnsetTime(result) !== null
        ? `rain-water onset ${formatSeconds(resultRainOnsetTime(result))}`
        : null,
      resultCloudTopMeters(result) !== null
        ? `coherent cloud top ${formatNumber(resultCloudTopMeters(result), "m")}`
        : null,
    ].filter(Boolean);
    return parts.join(" · ");
  }
  const parts = [
    resultFirstCloudTime(result) !== null
      ? `first cloud ${formatSeconds(resultFirstCloudTime(result))}`
      : null,
    resultMaxQc(result) !== null
      ? `max qc ${formatScientific(resultMaxQc(result), "kg/kg")}`
      : null,
    resultMaxUpdraft(result) !== null
      ? `max updraft ${formatNumber(resultMaxUpdraft(result), "m/s")}`
      : null,
    resultRainOnsetTime(result) !== null
      ? `rain-water onset ${formatSeconds(resultRainOnsetTime(result))}`
      : null,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "Science summary unavailable";
}

function resultFirstCloudTime(result: ResultCard): number | null {
  return result.science_summary?.first_cloud_time_seconds ?? result.first_cloud_time_seconds;
}

function resultMaxQc(result: ResultCard): number | null {
  return result.science_summary?.max_qc_kg_kg ?? result.max_qc_kg_kg;
}

function resultMaxUpdraft(result: ResultCard): number | null {
  return result.science_summary?.max_updraft_w_m_s ?? result.max_w_m_s;
}

function resultMinDowndraft(result: ResultCard): number | null {
  return result.science_summary?.min_downdraft_w_m_s ?? result.min_w_m_s;
}

function resultRainOnsetTime(result: ResultCard): number | null {
  return result.science_summary?.rain_onset_time_seconds ?? result.first_rain_time_seconds ?? null;
}

function resultLatestOutputTime(result: ResultCard): number | null {
  return (
    result.science_summary?.latest_output_time_seconds ??
    result.output_file_summary.last_output_time_seconds
  );
}

function resultCloudTopMeters(result: ResultCard): number | null {
  const value =
    result.science_summary?.highest_coherent_cloud_object_top_m ??
    result.science_summary?.highest_cloud_top_m ??
    null;
  if (value === null || value === undefined) return null;
  if (legacyCloudTopWasStoredInKilometers(result)) return value * 1000;
  return value;
}

function resultRawHydrometeorEnvelopeTopMeters(result: ResultCard): number | null {
  const value =
    result.science_summary?.highest_raw_hydrometeor_envelope_top_m ??
    result.science_summary?.highest_hydrometeor_envelope_top_m ??
    null;
  if (value === null || value === undefined) return null;
  if (legacyCloudTopWasStoredInKilometers(result)) return value * 1000;
  return value;
}

function resultLiquidCloudTopMeters(result: ResultCard): number | null {
  const value = result.science_summary?.highest_liquid_cloud_top_m ?? null;
  if (value === null || value === undefined) return null;
  if (legacyCloudTopWasStoredInKilometers(result)) return value * 1000;
  return value;
}

function cloudTopMismatchNotice(result: ResultCard): string | null {
  const liquidTop = resultLiquidCloudTopMeters(result);
  const coherentTop = resultCloudTopMeters(result);
  const rawTraceTop = resultRawHydrometeorEnvelopeTopMeters(result);
  if (liquidTop === null) {
    return null;
  }
  if (coherentTop !== null && coherentTop > liquidTop + 500) {
    const fields = result.science_summary?.coherent_cloud_object_source_fields;
    const fieldLabel = fields && fields.length > 1 ? fields.join("+") : "qc plus hydrometeors";
    return (
      `Viewing liquid cloud water only: qc tops near ${formatNumber(liquidTop, "m")}, ` +
      `while the coherent cloud object reaches ${formatNumber(coherentTop, "m")} from ${fieldLabel}.`
    );
  }
  if (rawTraceTop !== null && rawTraceTop > liquidTop + 500) {
    const fields = result.science_summary?.hydrometeor_envelope_source_fields;
    const fieldLabel = fields && fields.length > 1 ? fields.join("+") : "qc plus hydrometeors";
    return (
      `Viewing liquid cloud water only: qc tops near ${formatNumber(liquidTop, "m")}; ` +
      `a sparse hydrometeor trace reaches ${formatNumber(rawTraceTop, "m")} from ${fieldLabel}, ` +
      "but deep-cloud classification uses coherent cloud-object top."
    );
  }
  return null;
}

function legacyCloudTopWasStoredInKilometers(result: ResultCard): boolean {
  const caveats = [
    ...result.caveats,
    ...(result.science_summary?.interesting_time_caveats ?? []),
    ...(result.interesting_time_caveats ?? []),
  ];
  return caveats.some((caveat) => caveat === "cloud_base_top_vertical_units_not_meters:km");
}

function visibleInterestingTimes(result: ResultCard): InterestingTimeRecord[] {
  const priority = [
    "first_deep_convection",
    "first_cloud",
    "max_qc",
    "highest_liquid_cloud_top",
    "highest_cloud_top",
    "highest_raw_hydrometeor_envelope_top",
    "max_updraft_w",
    "min_downdraft_w",
    "rain_onset",
    "max_qr",
    "latest_output",
    "field_default_time",
  ];
  const byKey = new Map((result.interesting_times ?? []).map((record) => [record.key, record]));
  return priority
    .map((key) => byKey.get(key))
    .filter((record): record is InterestingTimeRecord => Boolean(record))
    .filter(
      (record) => record.support_state === "supported" || record.support_state === "fallback",
    );
}

function interestingTimePrimaryValue(record: InterestingTimeRecord, result: ResultCard): string {
  if (record.key === "highest_cloud_top") {
    const cloudTop = resultCloudTopMeters(result);
    return cloudTop === null ? "Unavailable" : formatNumber(cloudTop, "m");
  }
  if (record.key === "highest_liquid_cloud_top") {
    const cloudTop = resultLiquidCloudTopMeters(result);
    return cloudTop === null ? "Unavailable" : formatNumber(cloudTop, "m");
  }
  if (record.key === "highest_raw_hydrometeor_envelope_top") {
    const cloudTop = resultRawHydrometeorEnvelopeTopMeters(result);
    return cloudTop === null ? "Unavailable" : formatNumber(cloudTop, "m");
  }
  if (record.key === "latest_output" || record.key === "field_default_time") {
    return record.time_seconds !== null && record.time_seconds !== undefined
      ? formatSeconds(record.time_seconds)
      : "Unavailable";
  }
  if (typeof record.value === "number") {
    if (record.units === "kg/kg") return formatScientific(record.value, record.units);
    return formatNumber(record.value, record.units ?? "");
  }
  if (typeof record.value === "boolean") {
    return record.value ? "Detected" : "Not detected";
  }
  return record.time_seconds !== null && record.time_seconds !== undefined
    ? formatSeconds(record.time_seconds)
    : "Unavailable";
}

function interestingTimeShowsTimeSuffix(record: InterestingTimeRecord): boolean {
  return record.key !== "latest_output" && record.key !== "field_default_time";
}

function resultInputSource(result: ResultCard): "generated_reference" | "observed_sounding" {
  if (result.input_source === "observed_sounding") return "observed_sounding";
  return "generated_reference";
}

function resultInputSourceLabel(result: ResultCard): string {
  if (result.input_source_label) return result.input_source_label;
  return resultInputSource(result) === "observed_sounding"
    ? "Observed sounding"
    : "Generated reference";
}

function scienceSupportLabel(result: ResultCard): string {
  const state = result.science_summary?.interesting_time_support_state;
  if (!state) return "Legacy summary";
  if (state === "supported") return "Interesting times supported";
  if (state === "fallback") return "Interesting-time fallback";
  return "Interesting times limited";
}

function hasDeepConvectionDiagnostics(result: ResultCard): boolean {
  return (
    result.science_summary?.deep_cloud_formed !== undefined ||
    result.science_summary?.strong_updraft_formed !== undefined ||
    result.science_summary?.time_of_first_deep_convection_seconds !== undefined ||
    (result.interesting_times ?? []).some((time) => time.key === "first_deep_convection")
  );
}

function deepConvectionOutcome(result: ResultCard): string {
  if (fieldQualityBlocksEvidence(result, "qc") || fieldQualityBlocksEvidence(result, "w")) {
    return "Deep convection unavailable";
  }
  const formed = result.science_summary?.deep_cloud_formed;
  if (formed === true) return "Deep convection formed";
  if (formed === false) return "Deep convection not detected";
  return "Deep convection unknown";
}

function candidateMatchTone(matchStatus: string): "good" | "warning" | "neutral" {
  if (matchStatus === "supported") return "good";
  if (matchStatus === "inconclusive" || matchStatus === "not_comparable") return "warning";
  return "neutral";
}

function userFacingStatus(result: ResultCard): string {
  if (result.source_lifecycle_state === "completed" && result.status.includes("ingested")) {
    return "Completed CM1 result";
  }
  if (result.status.includes("ingested")) return "Ingested";
  if (result.caveats.length > 0) return "Needs review";
  return humanize(result.status);
}

function caveatLabel(result: ResultCard): string {
  return cloudOutcome(result) === "Cloud formed" || isDryFailedContrast(result)
    ? "Minor caveat"
    : "Needs review";
}

const FIELD_QUALITY_LABELS: Record<string, string> = {
  qc: "Cloud water",
  w: "Vertical velocity",
  qr: "Rain water aloft",
  surface_rain: "Surface rain",
  dbz: "Reflectivity",
};

const FIELD_QUALITY_ORDER = ["qc", "w", "qr", "surface_rain", "dbz"];

function resultFieldQuality(result: ResultCard, field: string): FieldQuality | null {
  if (result.field_quality_assessed !== undefined) {
    return result.field_quality?.[field] ?? null;
  }
  return result.science_summary?.field_quality?.[field] ?? null;
}

function resultFieldQualityAssessed(result: ResultCard): boolean {
  if (result.field_quality_assessed !== undefined) return result.field_quality_assessed;
  return result.science_summary?.field_quality_assessed ?? false;
}

function fieldQualityBlocksEvidence(result: ResultCard, field: string): boolean {
  if (!resultFieldQualityAssessed(result)) return false;
  const quality = resultFieldQuality(result, field);
  if (!quality) return true;
  return quality?.quality_state === "untrusted" || quality?.quality_state === "unavailable";
}

type FieldQualityDisplayRow = {
  key: string;
  description: string;
};

function nonTrustedFieldQuality(result: ResultCard): FieldQualityDisplayRow[] {
  const rows = new Map<string, FieldQualityDisplayRow>();
  for (const field of FIELD_QUALITY_ORDER) {
    const quality = resultFieldQuality(result, field);
    if (!quality) {
      rows.set(field, {
        key: field,
        description: `${FIELD_QUALITY_LABELS[field] ?? humanize(field)} was not assessed.`,
      });
    } else if (quality.quality_state !== "trusted") {
      rows.set(field, {
        key: field,
        description: fieldQualityDescription(quality),
      });
    }
  }
  return [...rows.values()];
}

function fieldQualityCounts(quality: FieldQuality): string {
  if (quality.total_count <= 0) return "no sampled values";
  return `${quality.finite_count} finite / ${quality.non_finite_count} non-finite / ${quality.total_count} total`;
}

function fieldQualityDescription(quality: FieldQuality): string {
  const label = FIELD_QUALITY_LABELS[quality.field] ?? humanize(quality.field);
  const reason = quality.reason ? `; ${quality.reason}` : "";
  return `${label} (${quality.source_field}) is ${quality.quality_state}; ${fieldQualityCounts(
    quality,
  )}${reason}`;
}

function RuntimeIntegritySummary({
  runtimeIntegrity,
}: {
  runtimeIntegrity: RuntimeIntegrity | null;
}) {
  const titleId = useId();
  if (!runtimeIntegrity || runtimeIntegrity.state === "trusted") return null;
  const title =
    runtimeIntegrity.state === "failed" ? "Runtime integrity failed" : "Runtime integrity caveated";
  return (
    <section aria-labelledby={titleId}>
      <h4 id={titleId}>{title}</h4>
      <p>{runtimeIntegrity.summary}</p>
      <dl className="metric-grid">
        <Metric label="State" value={humanize(runtimeIntegrity.state)} />
        <Metric label="Reason" value={humanize(runtimeIntegrity.reason)} />
        <Metric
          label="Normal completion"
          value={
            runtimeIntegrity.normal_completion_reported === null ||
            runtimeIntegrity.normal_completion_reported === undefined
              ? "Unknown"
              : runtimeIntegrity.normal_completion_reported
                ? "Yes"
                : "No"
          }
        />
        <Metric
          label="Terminal affected fields"
          value={
            runtimeIntegrity.terminal_non_finite_fields.length > 0
              ? runtimeIntegrity.terminal_non_finite_fields.join(", ")
              : "None"
          }
        />
      </dl>
      {runtimeIntegrity.caveats.length > 0 && (
        <ul className="compact-list">
          {runtimeIntegrity.caveats.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function FieldQualitySummary({ result }: { result: ResultCard }) {
  const assessed = resultFieldQualityAssessed(result);
  const rows = nonTrustedFieldQuality(result);
  return (
    <section aria-labelledby="field-quality-title">
      <h4 id="field-quality-title">Field quality</h4>
      {!assessed ? (
        <p>Field quality not assessed for this result.</p>
      ) : rows.length > 0 ? (
        <ul className="compact-list">
          {rows.map((row) => (
            <li key={row.key}>{row.description}</li>
          ))}
        </ul>
      ) : (
        <p>All tracked field-quality checks are trusted.</p>
      )}
    </section>
  );
}

function cloudOutcome(result: ResultCard): string {
  if (fieldQualityBlocksEvidence(result, "qc")) return "Cloud unavailable";
  if (hasDeepConvectionDiagnostics(result)) return deepConvectionOutcome(result);
  if (!result.diagnostics_summary) return "Unknown";
  return result.diagnostics_summary.includes("cloud formed") &&
    !result.diagnostics_summary.includes("no cloud formed")
    ? "Cloud formed"
    : "No cloud formed";
}

function rainOutcome(value: boolean | null): string {
  if (value === null) return "Unknown";
  return value ? "Rain water aloft detected" : "No rain water aloft detected";
}

function rainWaterOutcome(result: ResultCard): string {
  if (fieldQualityBlocksEvidence(result, "qr")) return "Rain water aloft unavailable";
  return rainOutcome(result.rain_present);
}

function surfaceRainOutcome(result: ResultCard): string {
  if (fieldQualityBlocksEvidence(result, "surface_rain")) return "Unavailable";
  if (result.surface_rain_present === true) {
    return result.max_surface_rain !== null && result.max_surface_rain !== undefined
      ? `Reached ground; max ${formatNumber(result.max_surface_rain, result.surface_rain_units ?? "")}`
      : "Reached ground";
  }
  if (result.surface_rain_present === false) return "Did not reach ground";
  return "Unavailable";
}

function reflectivityOutcome(result: ResultCard): string {
  if (fieldQualityBlocksEvidence(result, "dbz")) return "Unavailable";
  if (!result.reflectivity_available) return "Unavailable";
  return result.max_dbz !== null && result.max_dbz !== undefined
    ? `Max ${formatNumber(result.max_dbz, "dBZ")}`
    : "Available";
}

function outputSummary(summary: OutputFileSummary): string {
  const safeSummary = summary as Partial<OutputFileSummary>;
  const modelFileCount = safeSummary.model_output_count ?? safeSummary.model_output_file_count;
  const outputFileLabel =
    modelFileCount !== undefined
      ? `${modelFileCount} model files`
      : safeSummary.netcdf_count !== undefined
        ? `${safeSummary.netcdf_count} NetCDF files`
        : "unknown output files";
  const parts = [outputFileLabel, `${safeSummary.time_steps ?? "unknown"} time steps`];
  if ((safeSummary.stats_netcdf_count ?? 0) > 0) {
    parts.push(`${safeSummary.stats_netcdf_count} stats files`);
  }
  if ((safeSummary.raw_cm1_artifact_count ?? 0) > 0) {
    parts.push(`${safeSummary.raw_cm1_artifact_count} raw files`);
  }
  return parts.join(", ");
}

function storageOutputSummary(run: RunStorageEntry): string {
  const netcdf = run.output_summary.netcdf_paths ?? 0;
  const raw = run.output_summary.raw_cm1_artifacts ?? 0;
  const processed = run.output_summary.processed_artifacts ?? 0;
  if (run.output_artifact_count === 0) return "No output artifacts";
  const parts = [];
  if (netcdf > 0) parts.push(`${netcdf} NetCDF files`);
  if (raw > 0) parts.push(`${raw} raw CM1 files`);
  if (processed > 0) parts.push(`${processed} processed files`);
  return parts.length > 0 ? parts.join(", ") : `${run.output_artifact_count} output artifacts`;
}

function pipelineRunOutputSummary(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result) return outputSummary(result.output_file_summary);
  if (run.category === "running") return "CM1 output in progress";
  if (!run.worker_state) return storageOutputSummary(run);
  const netcdf = run.worker_netcdf_count ?? 0;
  const raw = run.worker_raw_artifact_count ?? 0;
  if (netcdf === 0 && raw === 0) return "Worker output not detected yet";
  const parts = [];
  if (netcdf > 0) parts.push(`${netcdf} remote NetCDF files`);
  if (raw > 0) parts.push(`${raw} remote raw CM1 files`);
  return parts.join(", ");
}

function resultForRun(results: ResultCard[], runId: string): ResultCard | undefined {
  return results.find((result) => result.run_id === runId);
}

function canPreviewDelete(run: RunStorageEntry): boolean {
  return run.category !== "running";
}

function deleteDisabledReason(run: RunStorageEntry): string {
  if (run.category === "running") return "Running runs cannot be deleted.";
  return "Cleanup unavailable.";
}

function clampIndex(index: number, length: number): number {
  return Math.min(Math.max(0, index), Math.max(0, length - 1));
}

function defaultsForField(
  defaults: ViewDefaultsResponse | null,
  fieldName: string | undefined,
): FieldViewDefaults | undefined {
  if (!fieldName) return undefined;
  return defaults?.fields[fieldName];
}

function defaultTimeIndex(
  field: VisualizableField | undefined,
  result: ResultCard,
  defaults: FieldViewDefaults | undefined,
): number {
  const timeOptions = field?.time_coordinate_values ?? [];
  const fieldDefault =
    field?.raw_field_name !== undefined
      ? result.default_time_by_field?.[field.raw_field_name]?.time_index
      : undefined;
  const resultDefault = fieldDefault ?? result.science_summary?.default_explore_time_index;
  if (resultDefault !== null && resultDefault !== undefined) {
    return clampIndex(resultDefault, timeOptions.length || 1);
  }
  if (defaults) return clampIndex(defaults.time_index, timeOptions.length || 1);
  return interestingTimeIndex(timeOptions, result);
}

function interestingTimeIndex(
  timeOptions: Array<number | string | null>,
  result: ResultCard,
): number {
  const target =
    result.science_summary?.default_explore_time_seconds ??
    result.first_cloud_time_seconds ??
    result.output_file_summary.last_output_time_seconds;
  return closestTimeIndex(timeOptions, target);
}

function closestTimeIndex(
  timeOptions: Array<number | string | null>,
  target: number | null,
): number {
  if (timeOptions.length === 0) return 0;
  if (target === null) return timeOptions.length - 1;
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  timeOptions.forEach((value, index) => {
    const seconds = numericTimeSeconds(value);
    if (seconds === null) return;
    const distance = Math.abs(seconds - target);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  });
  return bestIndex;
}

function numericTimeSeconds(value: number | string | null): number | null {
  if (typeof value === "number") return value;
  if (typeof value !== "string") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function defaultHorizontalLevel(
  field: VisualizableField | undefined,
  defaults?: FieldViewDefaults,
): number {
  if (defaults) return defaults.horizontal_level_index;
  return Math.max(0, Math.floor(verticalDimensionSize(field) / 3));
}

function defaultVerticalIndex(
  field: VisualizableField | undefined,
  orientation: "vertical_x" | "vertical_y",
  defaults?: FieldViewDefaults,
): number {
  if (defaults) {
    return orientation === "vertical_x" ? defaults.vertical_x_index : defaults.vertical_y_index;
  }
  const dimension =
    orientation === "vertical_x" ? field?.coordinate_names.y : field?.coordinate_names.x;
  if (!field || !dimension) return 0;
  const size = field.shape[field.dimensions.indexOf(dimension)] ?? 1;
  return Math.max(0, Math.floor(size / 2));
}

function verticalDimensionSize(field: VisualizableField | undefined): number {
  if (!field?.coordinate_names.vertical) return 1;
  return field.shape[field.dimensions.indexOf(field.coordinate_names.vertical)] ?? 1;
}
