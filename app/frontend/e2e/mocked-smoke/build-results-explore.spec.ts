import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults, openRunMonitor } from "../helpers";
import { mockCloudChamberApis, results } from "../fixtures";

const comparisonBaselineId = "result-trade-cumulus-5b-full-baseline-20260720T162342Z";
const comparisonMoreMoistureId = "result-trade-cumulus-5b-full-more_moisture-20260720T162342Z";

const comparisonBaselineResult = {
  ...results[0],
  result_id: comparisonBaselineId,
  run_id: "trade-cumulus-5b-full-baseline-20260720T162342Z",
  name: "Canonical BOMEX Baseline",
  scenario_id: "bomex_trade_cumulus_baseline_v0",
  scenario_name: "Trade Cumulus",
  run_configuration: {
    ...results[0].run_configuration,
    case_id: "bomex_trade_cumulus_baseline_v0",
  },
};

const comparisonMoreMoistureResult = {
  ...comparisonBaselineResult,
  result_id: comparisonMoreMoistureId,
  run_id: "trade-cumulus-5b-full-more_moisture-20260720T162342Z",
  name: "More Moisture",
};

const comparisonStory = {
  comparison_id: "trade_cumulus_moisture_v1",
  comparison_group_id: "trade_cumulus_moisture_v1",
  product_slice_id: "trade_cumulus_v1",
  case_id: "bomex_trade_cumulus_baseline_v0",
  title: "Trade Cumulus: Baseline and More Moisture",
  question: "How does stronger surface moisture supply change the trade-cumulus field?",
  illustrative_view_note:
    "Illustrative views: selected to help show the response measured across the full simulations. Times and locations may differ, and these are not corresponding individual clouds.",
  baseline: {
    result_id: comparisonBaselineId,
    run_id: comparisonBaselineResult.run_id,
    display_name: "Canonical BOMEX Baseline",
    control_state: "baseline",
    control_label: "Surface moisture supply",
    control_value: 5.2e-5,
    control_units: "g/g m/s",
    control_display: "5.2 × 10⁻⁵ g/g m/s",
    curated_view: {
      time_index: 152,
      time_seconds: 18_240,
      orientation: "vertical_x",
      plane_dimension: "y",
      plane_index: 5,
      plane_coordinate: -2.6500000953674316,
      plane_units: "km",
      camera_preset: "overview",
      cloud_field: "ql",
      cloud_threshold_kg_kg: 1e-6,
      lens_id: "updraft",
      scale_id: "trade_cumulus_updraft_velocity_v1",
      wind_mode: "perturbation",
      show_wind: true,
      show_cloud_boundary: true,
      opacity: 0.68,
      point_size: 11,
      caption:
        "This illustrative Baseline view shows one concentrated active cloud reaching about 2 km, with a strong rising core bordered by sinking air.",
    },
  },
  more_moisture: {
    result_id: comparisonMoreMoistureId,
    run_id: comparisonMoreMoistureResult.run_id,
    display_name: "More Moisture",
    control_state: "more_moisture",
    control_label: "Surface moisture supply",
    control_value: 7.8e-5,
    control_units: "g/g m/s",
    control_display: "7.8 × 10⁻⁵ g/g m/s",
    curated_view: {
      time_index: 169,
      time_seconds: 20_280,
      orientation: "vertical_x",
      plane_dimension: "y",
      plane_index: 51,
      plane_coordinate: 1.9500000476837158,
      plane_units: "km",
      camera_preset: "overview",
      cloud_field: "ql",
      cloud_threshold_kg_kg: 1e-6,
      lens_id: "updraft",
      scale_id: "trade_cumulus_updraft_velocity_v1",
      wind_mode: "perturbation",
      show_wind: true,
      show_cloud_boundary: true,
      opacity: 0.68,
      point_size: 11,
      caption:
        "This illustrative More Moisture view shows several active clouds across the slice, with rising cores distributed through a broader cloud-filled region reaching just above 2 km.",
    },
  },
  changed_condition: {
    label: "Surface moisture supply",
    baseline_display: "5.2 × 10⁻⁵ g/g m/s",
    more_moisture_display: "7.8 × 10⁻⁵ g/g m/s",
    change_display: "+50%",
  },
  material_responses: [
    {
      metric_id: "mean_cloud_cover_final_three_hours",
      label: "Mean cloud cover, final three hours",
      baseline_value: 10.596239697802197,
      more_moisture_value: 12.710873111263735,
      absolute_delta: 2.1146334134615383,
      percent_delta: 19.956451286206196,
      units: "%",
      method: "time mean of horizontal columns containing ql >= 1e-6 kg/kg",
      window: "time >= 10800 s",
      baseline_display: "10.596%",
      more_moisture_display: "12.711%",
      change_display: "+2.115 percentage points",
    },
    {
      metric_id: "mean_cloud_water_path_final_three_hours",
      label: "Mean cloud-water path, final three hours",
      baseline_value: 0.006351999299305916,
      more_moisture_value: 0.009071426778155891,
      absolute_delta: 0.0027194274788499753,
      percent_delta: 42.81215017053178,
      units: "kg/m^2",
      method: "time mean of horizontal domain-mean cwp",
      window: "time >= 10800 s",
      baseline_display: "0.006352 kg/m²",
      more_moisture_display: "0.009071 kg/m²",
      change_display: "+42.812%",
    },
    {
      metric_id: "mean_coherent_cloud_top_final_three_hours",
      label: "Mean coherent cloud top, final three hours",
      baseline_value: 1668.3517340775375,
      more_moisture_value: 1805.0550379595913,
      absolute_delta: 136.7033038820539,
      percent_delta: 8.193913854600911,
      units: "m",
      method: "mean supported coherent cloud-object top",
      window: "time >= 10800 s",
      baseline_display: "1,668 m",
      more_moisture_display: "1,805 m",
      change_display: "+137 m",
    },
  ],
  small_or_mixed_responses: [
    {
      title: "Initial cloud-liquid onset was unchanged.",
      body: "Both simulations first reached the cloud-liquid threshold at 1,080 s.",
    },
    {
      title: "The cloud-fraction peak stayed at the same height.",
      body: "Both final-three-hour profiles peaked near 620 m.",
    },
    {
      title: "The fraction of cloudy air rising changed very little.",
      body: "It was 90.379% in Baseline and 90.451% in More Moisture.",
    },
    {
      title: "The response varied through time.",
      body: "More Moisture was not cloudier or wetter than Baseline at every individual saved frame.",
    },
  ],
  held_fixed_by_design: {
    lead: "Only surface moisture supply changed.",
    groups: [
      {
        title: "Initial atmosphere",
        body: "Thermodynamic, moisture, and wind profiles, including the deterministic perturbation.",
      },
      {
        title: "Forcing",
        body: "Sensible heat supply, friction velocity, large-scale forcing, geostrophic wind, and Coriolis treatment.",
      },
      {
        title: "Model setup",
        body: "Moist physics, turbulence, boundaries, domain, grid, and timestep strategy.",
      },
      {
        title: "Execution and outputs",
        body: "Duration, output cadence, requested fields, CM1 source and executable, and the Cloud Chamber implementation commit.",
      },
    ],
  },
  explanation_paragraphs: [
    "More surface moisture produced a cloudier, wetter, somewhat deeper trade-cumulus field.",
    "Only the lower-boundary moisture supply changed. Over the final three hours, More Moisture covered more of the domain with cloud, held about 43 percent more mean cloud-water path, and produced coherent clouds averaging 137 meters taller.",
    "It did not create a completely different circulation regime. Initial cloud-liquid onset and the height of the cloud-fraction maximum were unchanged, and about 90 percent of cloudy cells were rising in both simulations.",
    "The illustrative Lens views are selected to help show the measured response. They show different times and locations and are not one-to-one matches of individual clouds. More Moisture was also not cloudier at every saved frame, so the result is a change in the evolving cloud field rather than a rule that every moment must look larger.",
  ],
  evidence_summary: {
    analysis_window: "time >= 10800 s",
    analysis_start_seconds: 10_800,
    analysis_end_seconds: 21_600,
    output_cadence_seconds: 120,
    paired_saved_frame_count: 181,
  },
  provenance: {
    evidence_state: "matched_runs_valid",
    evidence_version: "trade_cumulus_moisture_comparison_evidence_v1",
    implementation_commit: "49da1defc9914d3cc903ed9589c1312ddd843726",
    fixed_assumptions_sha256: "71d746b110fb1310ebb6dafbef4cfa4bd44c379fc6964ed1787deaf45e422535",
    baseline_run_id: comparisonBaselineResult.run_id,
    baseline_result_id: comparisonBaselineId,
    more_moisture_run_id: comparisonMoreMoistureResult.run_id,
    more_moisture_result_id: comparisonMoreMoistureId,
    scale_id: "trade_cumulus_updraft_velocity_v1",
    comparison_source: "runtime_matched_pair_evidence",
  },
  caveats: [
    "one_deterministic_les_realization_per_control_state",
    "illustrative_views_are_not_direct_frame_matches",
    "individual_clouds_are_not_paired_one_to_one",
    "candidate_product_slice_not_supported_status",
  ],
};

const worldBaselineSimulation = {
  simulation_id: "trade_cumulus_canonical_bomex",
  display_name: "Canonical BOMEX Baseline",
  role: "reference",
  world_id: "trade_cumulus",
  product_slice_id: "trade_cumulus_v1",
  case_id: "bomex_trade_cumulus_baseline_v0",
  result_id: comparisonBaselineId,
  run_id: comparisonBaselineResult.run_id,
  source_recipe_id: null,
  parent_simulation_id: null,
  reference_simulation_id: "trade_cumulus_canonical_bomex",
  technical_state: "available",
  technical_state_message: "Completed output is available.",
  technical_trust_state: "caveated",
  explore_available: true,
  compare_suggestions: [],
  configuration_difference_from_reference: [],
  lineage_state: "known",
  created_at: null,
  completed_at: null,
};

const worldMoreMoistureSimulation = {
  ...worldBaselineSimulation,
  simulation_id: "trade_cumulus_more_moisture",
  display_name: "More Moisture",
  role: "variation",
  result_id: comparisonMoreMoistureId,
  run_id: comparisonMoreMoistureResult.run_id,
  parent_simulation_id: "trade_cumulus_canonical_bomex",
  compare_suggestions: [
    {
      comparison_id: "trade_cumulus_moisture_v1",
      display_name: "More Moisture versus Baseline",
      target_simulation_id: "trade_cumulus_canonical_bomex",
    },
  ],
  configuration_difference_from_reference: [
    {
      path: "run_configuration.surface_moisture_flux_g_g_m_s",
      label: "Surface moisture supply",
      category: "atmospheric",
      left_value: 0.000052,
      right_value: 0.000078,
      units: "g/g m/s",
      material: true,
    },
  ],
};

const tradeCumulusWorld = {
  world_id: "trade_cumulus",
  display_name: "Trade Cumulus",
  status: "mvp_candidate",
  short_description: "Investigate shallow maritime cumulus and surface moisture supply.",
  availability_state: "available",
  availability_message: "Reference, variation, and featured comparison are available.",
  reference_simulation: worldBaselineSimulation,
  simulations: [worldBaselineSimulation, worldMoreMoistureSimulation],
  lab_history: [],
  featured_comparison: {
    comparison_id: "trade_cumulus_moisture_v1",
    display_name: "More Moisture versus Baseline",
    baseline_simulation_id: "trade_cumulus_canonical_bomex",
    more_moisture_simulation_id: "trade_cumulus_more_moisture",
    availability_state: "available",
    availability_message: "Featured comparison is available.",
    open_available: true,
  },
  lab_summary: {
    active_run_count: 0,
    completed_uninspected_run_count: 1,
    lab_history_count: 0,
    summary: "1 completed run awaits inspection",
  },
  capabilities: {
    reference_explore: true,
    featured_comparison: true,
    lab: true,
    saved_views: false,
    ordinary_compare: true,
  },
  caveats: [],
};

function compareTradeState(
  member: typeof comparisonStory.baseline | typeof comparisonStory.more_moisture,
) {
  return {
    state_version: 1,
    world_id: "trade_cumulus",
    model_time_seconds: member.curated_view.time_seconds,
    context_collapsed: true,
    secondary_section: "notes",
    selected_point: null,
    view_id: "updraft_lens",
    scene_field_id: "ql",
    slice_field_id: "w",
    fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
    active_slice_plane: "vertical_x",
    slice_coordinate_km: member.curated_view.plane_coordinate,
    slice_native_index: member.curated_view.plane_index,
    horizontal_slice_coordinate_km: 1,
    threshold_native: 1e-6,
    layer_opacity: 0.68,
    point_size_px: 11,
    lens_opacity: 0.9,
    show_slice_plane: true,
    show_cloud_boundary: true,
    show_horizontal_wind: true,
    wind_mode: "perturbation",
    camera_preset: "overview",
    camera_transform: null,
    playback_speed: 1,
    display_controls_open: false,
  };
}

function compareTradeSimulation(
  simulation: typeof worldBaselineSimulation,
  member: typeof comparisonStory.baseline | typeof comparisonStory.more_moisture,
) {
  return {
    simulation_id: simulation.simulation_id,
    display_name: simulation.display_name,
    world_id: "trade_cumulus",
    role: simulation.role,
    run_id: simulation.run_id,
    result_id: simulation.result_id,
    case_id: simulation.case_id,
    parent_simulation_id: simulation.parent_simulation_id,
    reference_simulation_id: simulation.reference_simulation_id,
    lineage_state: simulation.lineage_state,
    availability_state: simulation.technical_state,
    availability_message: simulation.technical_state_message,
    inspectable: simulation.explore_available,
    grid: {
      topology: "native_3d",
      nx: 96,
      ny: 96,
      nz: 100,
      dx_m: 6400 / 96,
      dy_m: 6400 / 96,
      dz_m: 30,
      x_extent_km: [-3.2, 3.2],
      y_extent_km: [-3.2, 3.2],
      z_extent_km: [0, 3],
    },
    time: {
      times_seconds: Array.from({ length: 181 }, (_, index) => index * 120),
      start_seconds: 0,
      end_seconds: 21_600,
      cadence_seconds: 120,
      saved_output_count: 181,
      interpolation_allowed: false,
    },
    available_field_ids: ["ql"],
    available_view_ids: ["field", "updraft_lens"],
    fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
    plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
    camera_mapping: "normalized_3d",
    initial_state: compareTradeState(member),
    caveats: [],
  };
}

const tradeCumulusCompareDescriptor = {
  schema_version: "world_compare_v1",
  world_id: "trade_cumulus",
  display_name: "Trade Cumulus",
  simulations: [
    compareTradeSimulation(worldBaselineSimulation, comparisonStory.baseline),
    compareTradeSimulation(worldMoreMoistureSimulation, comparisonStory.more_moisture),
  ],
  default_left_simulation_id: worldBaselineSimulation.simulation_id,
  default_right_simulation_id: worldMoreMoistureSimulation.simulation_id,
  selected_left_simulation_id: worldBaselineSimulation.simulation_id,
  selected_right_simulation_id: worldMoreMoistureSimulation.simulation_id,
  material_differences: [
    {
      path: "run_configuration.surface_moisture_flux_g_g_m_s",
      label: "Surface moisture supply",
      category: "atmospheric",
      left_value: 0.052,
      right_value: 0.078,
      left_known: true,
      right_known: true,
      units: "g/kg m/s",
      material: true,
    },
  ],
  compatibility: {
    same_world: true,
    both_inspectable: true,
    relationship: "More Moisture is a child of Canonical BOMEX Baseline.",
    controlled_pair: true,
    controlled_pair_message:
      "Only surface moisture supply changed; the retained pair is a controlled comparison.",
    shared_field_ids: ["ql"],
    shared_view_ids: ["field", "updraft_lens"],
    shared_fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
    exact_time_link_available: true,
    nearest_time_link_available: true,
    time_tolerance_seconds: 180,
    physical_plane_link_available: true,
    camera_link_available: true,
    selection_link_available: true,
    blockers: [],
  },
  no_second_simulation_message: null,
  persistence: "transient_only",
};

const cloudWorldSummary = {
  world_id: "trade_cumulus",
  display_name: "Trade Cumulus",
  status: "mvp_candidate",
  short_description: tradeCumulusWorld.short_description,
  reference_simulation_id: "trade_cumulus_canonical_bomex",
  reference_available: true,
  simulation_count: 2,
  saved_view_count: 0,
  saved_comparison_count: 1,
  featured_comparison_count: 1,
  active_run_count: 0,
  completed_uninspected_run_count: 1,
  availability_state: "available",
  availability_message: tradeCumulusWorld.availability_message,
};

const comparisonUpdraftScale = {
  w_range_min_m_s: -1,
  w_range_max_m_s: 5,
  w_range_method: "fixed_trade_cumulus_updraft_velocity_v1",
  w_scale_id: "trade_cumulus_updraft_velocity_v1",
  w_scale_owner: "trade_cumulus",
  w_scale_type: "fixed_discrete",
  w_scale_units: "m/s",
  w_scale_breakpoints_m_s: [-1, -0.5, -0.1, 0.1, 0.5, 1, 2, 3, 5],
  w_scale_colors: [
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
  w_scale_neutral_interval_m_s: [-0.1, 0.1],
  w_scale_source: "pm_approved_issue_379_from_stage5b2_matched_pair",
  w_scale_clipping_behavior:
    "values_below_-1.0_and_at_or_above_5.0_use_endpoint_colors_and_are_reported_as_clipped",
};

type ComparisonMember = typeof comparisonStory.baseline;

function authoredExplorePresentation(member: ComparisonMember) {
  return member.control_state === "baseline"
    ? {
        time_index: 100,
        time_seconds: 12_060,
        plane_index: 1,
        plane_coordinate: 2.366666555404663,
      }
    : {
        time_index: 116,
        time_seconds: 13_920,
        plane_index: 1,
        plane_coordinate: 1.6333333253860474,
      };
}

function frameTimeSeconds(member: ComparisonMember, timeIndex: number) {
  if (timeIndex === member.curated_view.time_index) return member.curated_view.time_seconds;
  const authored = authoredExplorePresentation(member);
  if (timeIndex === authored.time_index) return authored.time_seconds;
  return timeIndex * 120;
}

function comparisonPointCloud(
  member: ComparisonMember,
  timeIndex = member.curated_view.time_index,
) {
  const offset = member.control_state === "baseline" ? 0 : 0.45;
  const points: Array<[number, number, number, number]> = [
    [-1.8 + offset, -0.8, 0.5, 0.00035],
    [-1.2 + offset, -0.4, 0.9, 0.0008],
    [-0.5 + offset, 0.1, 1.35, 0.0012],
    [0.3 + offset, 0.6, 1.8, 0.00095],
    [1.4 + offset, 1.1, 1.15, 0.0005],
  ];
  return {
    result_id: member.result_id,
    run_id: member.run_id,
    scenario_id: "bomex_trade_cumulus_baseline_v0",
    field: { raw_field_name: "ql", display_name: "Cloud water", units: "kg/kg" },
    selection: {
      field: "ql",
      time_index: timeIndex,
      time_seconds: frameTimeSeconds(member, timeIndex),
      threshold: 1e-6,
      max_points: 50_000,
    },
    coordinate_units: { xh: "km", yh: "km", zh: "km" },
    coordinate_extents: {
      xh: { min: -3.2, max: 3.2, units: "km" },
      yh: { min: -3.2, max: 3.2, units: "km" },
      zh: { min: 0, max: 3, units: "km" },
    },
    points,
    stats: {
      source_count: points.length,
      returned_count: points.length,
      field_min_value: 0,
      field_max_value: 0.0012,
      field_mean_value: 0.00076,
      field_finite_count: points.length,
      field_non_finite_count: 0,
      min_value: 0.00035,
      max_value: 0.0012,
      active_z_min: 0.5,
      active_z_max: 1.8,
      downsampled: false,
      downsample_stride: 1,
    },
    provenance: {
      source_model: "CM1",
      result_id: member.result_id,
      run_id: member.run_id,
      scenario_id: "bomex_trade_cumulus_baseline_v0",
      processing_method: "backend_xarray_native_grid_threshold",
      rendering_method: "thresholded_point_cloud",
      provenance_label: "CM1-derived cloud water point cloud",
    },
    caveats: [],
  };
}

function comparisonLensFrame(
  member: ComparisonMember,
  {
    timeIndex = member.curated_view.time_index,
    planeIndex = member.curated_view.plane_index,
  }: { timeIndex?: number; planeIndex?: number } = {},
) {
  const authored = authoredExplorePresentation(member);
  const values =
    member.control_state === "baseline"
      ? [
          [-0.6, -0.2, 0.3, 0.6],
          [-0.3, 0.1, 0.9, 1.4],
          [-0.1, 0.4, 1.8, 2.5],
          [0, 0.2, 0.8, 0.4],
        ]
      : [
          [-0.5, -0.1, 0.4, 0.8],
          [-0.2, 0.5, 1.5, 2.2],
          [0.1, 0.9, 2.8, 4.1],
          [0.2, 0.6, 1.7, 0.7],
        ];
  return {
    result_id: member.result_id,
    time_index: timeIndex,
    time_seconds: frameTimeSeconds(member, timeIndex),
    orientation: "vertical_x",
    plane_dimension: "y",
    plane_index: planeIndex,
    plane_coordinate:
      planeIndex === authored.plane_index
        ? authored.plane_coordinate
        : planeIndex === member.curated_view.plane_index
          ? member.curated_view.plane_coordinate
          : -3.2 + planeIndex * 0.1,
    plane_units: "km",
    dimension_order: ["z", "x"],
    x_indices: [0, 1, 2, 3],
    x_values_km: [-3.2, -1.1, 1.1, 3.2],
    y_indices: [0, 1],
    y_values_km: [-3.2, 3.2],
    z_indices: [0, 1, 2, 3],
    z_values_km: [0, 1, 2, 3],
    w_values_m_s: values,
    cloud_mask: [
      [false, true, true, false],
      [true, true, true, false],
      [false, true, true, true],
      [false, false, true, false],
    ],
    cloud_threshold_kg_kg: 1e-6,
    ...comparisonUpdraftScale,
    w_finite_count: 16,
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
    domain_mean_u_m_s: 0,
    domain_mean_v_m_s: 0,
    wind_vectors: [
      { x_km: -2, y_km: 0, z_km: 0.58, u_m_s: 0.4, v_m_s: 0.2, magnitude_m_s: 0.45 },
      { x_km: 0, y_km: 0, z_km: 0.58, u_m_s: -0.3, v_m_s: 0.4, magnitude_m_s: 0.5 },
      { x_km: 2, y_km: 0, z_km: 0.58, u_m_s: 0.2, v_m_s: -0.4, magnitude_m_s: 0.45 },
    ],
    provenance: {
      source_model: "CM1",
      result_id: member.result_id,
      run_id: member.run_id,
      scenario_id: "bomex_trade_cumulus_baseline_v0",
      processing_method: "trade_cumulus_updraft_lens_frame",
      rendering_method: "native_grid_slice",
      provenance_label: "CM1-derived Updraft Lens frame",
    },
    caveats: [],
  };
}

function comparisonLensDefaults(member: ComparisonMember) {
  const authored = authoredExplorePresentation(member);
  return {
    result_id: member.result_id,
    case_id: "bomex_trade_cumulus_baseline_v0",
    eligible: true,
    primary_field: "w",
    cloud_field: "ql",
    orientation: "vertical_x",
    default_time_index: authored.time_index,
    default_time_seconds: authored.time_seconds,
    default_time_method: "authored_simulation_presentation",
    default_plane_dimension: "y",
    default_plane_index: authored.plane_index,
    default_plane_coordinate: authored.plane_coordinate,
    default_plane_units: "km",
    default_plane_method: "authored_simulation_presentation",
    cloud_threshold_kg_kg: 1e-6,
    ...comparisonUpdraftScale,
    wind_target_level_m: 600,
    wind_actual_level_m: 580,
    wind_level_index: 14,
    wind_default_mode: "perturbation",
    wind_stride: 8,
    wind_shown_by_default: true,
    perturbation_wind_reference_m_s: 0.9,
    total_wind_reference_m_s: 8.8,
    wind_arrow_domain_fraction: 0.08,
    provenance: comparisonLensFrame(member).provenance,
    caveats: [],
  };
}

function comparisonFieldCatalog(member: ComparisonMember) {
  const times = Array.from(
    { length: Math.max(member.curated_view.time_index + 1, 181) },
    (_, index) => index * 120,
  );
  const authored = authoredExplorePresentation(member);
  times[authored.time_index] = authored.time_seconds;
  const provenance = {
    source_model: "CM1",
    result_id: member.result_id,
    run_id: member.run_id,
    scenario_id: "bomex_trade_cumulus_baseline_v0",
    source_product_state: "completed_cm1_result",
    result_state: "ingested",
    processing_method: "native-grid field catalog",
    rendering_method: "visualization-ready metadata",
    provenance_label: "CM1-derived Trade Cumulus visualization fields",
  };
  const fields = [
    {
      raw_field_name: "ql",
      canonical_field_name: "cloud_water",
      display_name: "Cloud liquid",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      native_grid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw_field_name: "qv",
      canonical_field_name: "water_vapor",
      display_name: "Water vapor",
      units: "kg/kg",
      dimensions: ["time", "zh", "yh", "xh"],
      native_grid: "zh/yh/xh",
      vertical: "zh",
    },
    {
      raw_field_name: "w",
      canonical_field_name: "vertical_velocity",
      display_name: "Vertical velocity",
      units: "m/s",
      dimensions: ["time", "zf", "yh", "xh"],
      native_grid: "zf/yh/xh",
      vertical: "zf",
    },
  ];
  return {
    result_id: member.result_id,
    run_id: member.run_id,
    scenario_id: "bomex_trade_cumulus_baseline_v0",
    source_model: "CM1",
    available_fields: fields.map((field) => ({
      ...field,
      shape: [times.length, 64, 128, 128],
      coordinate_names: {
        time: "time",
        vertical: field.vertical,
        y: "yh",
        x: "xh",
      },
      time_coordinate_values: times,
      provenance,
      caveats: ["native_grid_no_interpolation"],
    })),
    provenance,
    caveats: [],
  };
}

async function mockTradeCumulusComparison(page: Parameters<typeof mockCloudChamberApis>[0]) {
  for (const result of [comparisonBaselineResult, comparisonMoreMoistureResult]) {
    await page.route(`**/api/results/${result.result_id}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(result),
      }),
    );
  }
  await page.route("**/api/results", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [comparisonBaselineResult, comparisonMoreMoistureResult, results[0]],
      }),
    }),
  );
  await page.route("**/api/comparisons/trade-cumulus-moisture-v1", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comparisonStory),
    }),
  );
  await page.route("**/api/results/*/visualization/point-cloud**", (route) => {
    const url = route.request().url();
    const parsed = new URL(url);
    const member = url.includes(comparisonMoreMoistureId)
      ? comparisonStory.more_moisture
      : comparisonStory.baseline;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        comparisonPointCloud(member, Number(parsed.searchParams.get("time_index") ?? 0)),
      ),
    });
  });
  await page.route("**/api/results/*/visualization/fields", (route) => {
    const member = route.request().url().includes(comparisonMoreMoistureId)
      ? comparisonStory.more_moisture
      : comparisonStory.baseline;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comparisonFieldCatalog(member)),
    });
  });
  await page.route(
    "**/api/results/*/visualization/trade-cumulus-updraft-lens/defaults",
    (route) => {
      const member = route.request().url().includes(comparisonMoreMoistureId)
        ? comparisonStory.more_moisture
        : comparisonStory.baseline;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(comparisonLensDefaults(member)),
      });
    },
  );
  await page.route("**/api/results/*/visualization/trade-cumulus-updraft-lens/frame**", (route) => {
    const url = route.request().url();
    const parsed = new URL(url);
    const member = url.includes(comparisonMoreMoistureId)
      ? comparisonStory.more_moisture
      : comparisonStory.baseline;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        comparisonLensFrame(member, {
          timeIndex: Number(parsed.searchParams.get("time_index") ?? 0),
          planeIndex: Number(parsed.searchParams.get("plane_index") ?? 0),
        }),
      ),
    });
  });
}

async function mockTradeCumulusWorld(page: Parameters<typeof mockCloudChamberApis>[0]) {
  await mockTradeCumulusComparison(page);
  await page.route("**/api/worlds", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([cloudWorldSummary]),
    }),
  );
  await page.route("**/api/worlds/trade-cumulus", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(tradeCumulusWorld),
    }),
  );
  await page.route("**/api/worlds/trade-cumulus/compare**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(tradeCumulusCompareDescriptor),
    }),
  );
}

const tradeVariationReferenceControls = {
  surface_sensible_heat_flux_k_m_s: 0.008,
  surface_moisture_flux_g_kg_m_s: 0.052,
  sub_inversion_total_water_g_kg: 16.65,
  inversion_base_m_agl: 520,
  inversion_thickness_m: 960,
  inversion_strength_k: 3.7,
  free_tropospheric_rh_percent: 41,
  cloud_layer_shear_m_s: 4.14,
  cloud_layer_shear_direction_deg: 0,
  cloud_layer_mean_u_m_s: -7.5,
  cloud_layer_mean_v_m_s: 0,
  large_scale_vertical_motion_m_s: -0.0065,
  temperature_tendency_k_day: -2,
  total_water_tendency_g_kg_day: -1.0368,
};

function tradeVariationProfile(
  profileId: string,
  role: string,
  duration: number,
  cadence: number,
  histories: number,
  blocked = false,
) {
  return {
    profile: {
      schema_version: "1",
      world_id: "trade_cumulus",
      world_name: "Trade Cumulus",
      recipe_id: "canonical_bomex_trade_cumulus",
      recipe_version: "approved_variation_contract_v1",
      profile_id: profileId,
      profile_name: `${role} — Trade Cumulus experiment`,
      role,
      numerical_realization: {
        domain: role === "Extended" ? "12.8 km square" : "6.4 km square",
        grid: role === "Presentation" ? "96 × 96 × 100" : "64 × 64 × 75",
        spacing: role === "Presentation" ? "66.7 × 66.7 × 30 m" : "100 × 100 × 40 m",
        timestep_strategy: role === "Presentation" ? "target 2 s" : "target 3 s",
        physics_source: "Canonical BOMEX",
      },
      observation_plan: {
        duration_seconds: duration,
        output_cadence_seconds: cadence,
        diagnostic_cadence_seconds: null,
        expected_history_count: histories,
        retained_field_inventory: ["ql", "qv", "th", "prs", "u", "v", "w"],
      },
      expected_runtime_min_seconds: blocked ? null : 900,
      expected_runtime_max_seconds: blocked ? null : 1800,
      expected_size_min_bytes: blocked ? null : 1.6 * 1024 ** 3,
      expected_size_max_bytes: blocked ? null : 2.2 * 1024 ** 3,
      estimate_basis: blocked ? "uncharacterized" : "scaled_from_measured",
      confidence: blocked ? "Requires bounded characterization." : "Scaled evidence.",
      cost_change_reasons: [],
      scientific_limitations:
        role === "Quick" ? ["Early response, not a full steady-period assessment."] : [],
      required_post_run_reserve_bytes: 2 * 1024 ** 3,
    },
    current_free_space_bytes: 100 * 1024 ** 3,
    projected_free_space_bytes: blocked ? null : 97.8 * 1024 ** 3,
    required_free_space_bytes: blocked ? null : 4.2 * 1024 ** 3,
    disposition: blocked ? "blocked" : "passes",
    disposition_reason: blocked
      ? "This profile is uncharacterized."
      : "The high estimate fits while preserving the safety margin.",
  };
}

function tradeVariationTemplate(parent = worldBaselineSimulation) {
  const more = parent.simulation_id === worldMoreMoistureSimulation.simulation_id;
  return {
    parent_simulation_id: parent.simulation_id,
    parent_run_id: parent.run_id,
    parent_display_name: parent.display_name,
    parent_configuration_source: "Retained source-backed BOMEX atmosphere and forcing",
    reference_simulation_id: worldBaselineSimulation.simulation_id,
    recipe_id: "canonical_bomex_trade_cumulus",
    recipe_name: "Canonical BOMEX Trade Cumulus",
    recipe_contract_version: "1",
    controls: {
      ...tradeVariationReferenceControls,
      surface_moisture_flux_g_kg_m_s: more ? 0.078 : 0.052,
    },
    canonical_reference_controls: tradeVariationReferenceControls,
    run_profiles: [
      tradeVariationProfile("trade_cumulus_quick_v1", "Quick", 10_800, 180, 61),
      tradeVariationProfile("trade_cumulus_standard_v1", "Standard", 14_400, 120, 121),
      tradeVariationProfile("trade_cumulus_full_cycle_v1", "Full-cycle", 21_600, 120, 181),
      tradeVariationProfile("trade_cumulus_presentation_v1", "Presentation", 14_400, 60, 241),
      tradeVariationProfile("trade_cumulus_extended_v1", "Extended", 14_400, 120, 121, true),
    ],
    default_run_profile_id: "trade_cumulus_presentation_v1",
    can_create_variation: true,
    unavailable_reason: null,
  };
}

function tradeVariationPreview(request: {
  controls: typeof tradeVariationReferenceControls;
  run_profile_id: string;
}) {
  const physical = Object.entries(request.controls).filter(
    ([key, value]) =>
      value !==
      tradeVariationReferenceControls[key as keyof typeof tradeVariationReferenceControls],
  );
  const profileChanged = request.run_profile_id !== "trade_cumulus_presentation_v1";
  const impossible =
    request.controls.inversion_base_m_agl + request.controls.inversion_thickness_m >= 3_000;
  const differences = physical.map(([key, value]) => ({
    path: `controls.${key}`,
    label:
      key === "surface_moisture_flux_g_kg_m_s"
        ? "Surface moisture flux"
        : key === "surface_sensible_heat_flux_k_m_s"
          ? "Surface sensible-heat flux"
          : key.replaceAll("_", " "),
    before: tradeVariationReferenceControls[key as keyof typeof tradeVariationReferenceControls],
    after: value,
    units: null,
    material: true,
  }));
  const cost = request.run_profile_id.includes("extended")
    ? tradeVariationProfile("trade_cumulus_extended_v1", "Extended", 14_400, 120, 121, true)
    : request.run_profile_id.includes("standard")
      ? tradeVariationProfile("trade_cumulus_standard_v1", "Standard", 14_400, 120, 121)
      : tradeVariationProfile("trade_cumulus_presentation_v1", "Presentation", 14_400, 60, 241);
  return {
    requested_controls: request.controls,
    resolved_controls: request.controls,
    canonical_reference_controls: tradeVariationReferenceControls,
    parent_controls: tradeVariationReferenceControls,
    differences: {
      wind: differences.filter((item) => item.path.includes("shear")),
      moisture: differences.filter((item) => item.path.includes("moisture")),
      "stability/thermodynamics": differences.filter((item) => item.path.includes("inversion")),
      "forcing/initiation": differences.filter(
        (item) =>
          !item.path.includes("moisture") &&
          !item.path.includes("inversion") &&
          !item.path.includes("shear"),
      ),
      "numerical realization": profileChanged
        ? [
            {
              path: "run_profile_id",
              label: "Run profile",
              before: "Presentation",
              after: request.run_profile_id.includes("standard") ? "Standard" : "Extended",
              units: null,
              material: true,
            },
          ]
        : [],
      "observation plan": [],
    },
    relationship_classification:
      physical.length && profileChanged
        ? "mixed_variation"
        : physical.length > 1
          ? "multi_factor_physical_variation"
          : physical.length === 1
            ? "controlled_physical_variation"
            : profileChanged
              ? "numerical_sensitivity"
              : null,
    warnings:
      request.controls.surface_sensible_heat_flux_k_m_s < 0
        ? ["Surface sensible heat flux is downward."]
        : [],
    blocking_errors: impossible ? ["The requested inversion does not fit the model top."] : [],
    diagnostics: {
      inversion_top_m_agl:
        request.controls.inversion_base_m_agl + request.controls.inversion_thickness_m,
      model_top_m: 3_000,
      sub_inversion_total_water_g_kg: request.controls.sub_inversion_total_water_g_kg,
      free_tropospheric_rh_percent: request.controls.free_tropospheric_rh_percent,
      cloud_layer_shear_m_s: request.controls.cloud_layer_shear_m_s,
      cloud_layer_shear_direction_deg: request.controls.cloud_layer_shear_direction_deg,
      cloud_layer_mean_u_m_s: request.controls.cloud_layer_mean_u_m_s,
      cloud_layer_mean_v_m_s: request.controls.cloud_layer_mean_v_m_s,
      initial_saturated_level_count: 0,
      minimum_theta_gradient_k_km: 0,
      labels: ["Large-scale subsidence"],
    },
    sounding_profile: [
      {
        height_m: 0,
        theta_l_k: 298.7,
        total_water_g_kg: request.controls.sub_inversion_total_water_g_kg,
        relative_humidity_percent: 70,
        u_m_s: -9,
        v_m_s: 0,
      },
      {
        height_m: 3_000,
        theta_l_k: 311,
        total_water_g_kg: 3,
        relative_humidity_percent: request.controls.free_tropospheric_rh_percent,
        u_m_s: -5,
        v_m_s: 0,
      },
    ],
    forcing_profile: [
      {
        height_m: 0,
        vertical_motion_m_s: request.controls.large_scale_vertical_motion_m_s,
        temperature_tendency_k_day: request.controls.temperature_tendency_k_day,
        total_water_tendency_g_kg_day: request.controls.total_water_tendency_g_kg_day,
      },
      {
        height_m: 3_000,
        vertical_motion_m_s: 0,
        temperature_tendency_k_day: 0,
        total_water_tendency_g_kg_day: 0,
      },
    ],
    numerical_realization: cost.profile.numerical_realization,
    observation_plan: cost.profile.observation_plan,
    cost_estimate: cost,
  };
}

async function mockTradeCumulusVariationPath(
  page: Parameters<typeof mockCloudChamberApis>[0],
  options: { failPackage?: boolean } = {},
) {
  await mockTradeCumulusWorld(page);
  let completed = false;
  const variation = {
    ...worldBaselineSimulation,
    simulation_id: "trade_cumulus_direct_moisture_abcd1234",
    display_name: "Direct Moisture Target",
    role: "variation",
    result_id: "result-trade-direct-moisture",
    run_id: "trade-direct-moisture-run",
    parent_simulation_id: worldBaselineSimulation.simulation_id,
    recipe_contract_version: "1",
    relationship_classification: "controlled_physical_variation",
    can_create_variation: true,
    parent_eligibility_reason: null,
    attempt_count: 1,
    compare_suggestions: [
      {
        comparison_id: "trade_cumulus_direct_moisture_parent",
        display_name: "Direct Moisture Target versus Canonical BOMEX Baseline",
        target_simulation_id: worldBaselineSimulation.simulation_id,
      },
    ],
    configuration_difference_from_reference: [
      {
        path: "scientific_design.controls.surface_moisture_flux_g_kg_m_s",
        label: "Surface moisture flux",
        category: "atmospheric",
        left_value: 0.052,
        right_value: 0.09,
        units: "g/kg m/s",
        material: true,
      },
    ],
  };
  await page.unroute("**/api/worlds/trade-cumulus");
  await page.route("**/api/worlds/trade-cumulus", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...tradeCumulusWorld,
        reference_simulation: { ...worldBaselineSimulation, can_create_variation: true },
        simulations: [
          { ...worldBaselineSimulation, can_create_variation: true },
          { ...worldMoreMoistureSimulation, can_create_variation: true },
          ...(completed ? [variation] : []),
        ],
      }),
    }),
  );
  await page.unroute("**/api/worlds/trade-cumulus/compare**");
  await page.route("**/api/worlds/trade-cumulus/compare**", (route) => {
    const search = new URL(route.request().url()).searchParams;
    const leftId = search.get("left_simulation_id") ?? worldBaselineSimulation.simulation_id;
    const rightId = search.get("right_simulation_id") ?? variation.simulation_id;
    const descriptors = [
      compareTradeSimulation(worldBaselineSimulation, comparisonStory.baseline),
      {
        ...compareTradeSimulation(worldBaselineSimulation, comparisonStory.baseline),
        simulation_id: variation.simulation_id,
        display_name: variation.display_name,
        role: "variation",
        run_id: variation.run_id,
        result_id: variation.result_id,
        parent_simulation_id: worldBaselineSimulation.simulation_id,
        lineage_state: "valid",
      },
    ];
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...tradeCumulusCompareDescriptor,
        simulations: descriptors,
        default_left_simulation_id: worldBaselineSimulation.simulation_id,
        default_right_simulation_id: variation.simulation_id,
        selected_left_simulation_id: leftId,
        selected_right_simulation_id: rightId,
        material_differences: variation.configuration_difference_from_reference,
        compatibility: {
          ...tradeCumulusCompareDescriptor.compatibility,
          relationship:
            "Direct Moisture Target is a controlled physical variation of Canonical BOMEX Baseline.",
          controlled_pair_message:
            "One material physical control changed while numerical and observation layers remain matched.",
        },
      }),
    });
  });
  await page.route("**/api/worlds/trade-cumulus/variation-template**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        tradeVariationTemplate(
          new URL(route.request().url()).searchParams.get("parent_simulation_id") ===
            variation.simulation_id
            ? variation
            : worldBaselineSimulation,
        ),
      ),
    }),
  );
  await page.route("**/api/worlds/trade-cumulus/variations/preview", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(tradeVariationPreview(route.request().postDataJSON())),
    }),
  );
  await page.route("**/api/worlds/trade-cumulus/variations", (route) =>
    route.fulfill({
      status: options.failPackage ? 400 : 200,
      contentType: "application/json",
      body: JSON.stringify(
        options.failPackage
          ? { detail: "Variation package preflight failed." }
          : {
              simulation_id: variation.simulation_id,
              run_id: variation.run_id,
              manifest_path: "/mock/trade-direct-moisture/run_manifest.json",
              package_dir: "/mock/trade-direct-moisture",
              launch_review_snapshot_id: "trade-launch-review",
              warnings: [],
            },
      ),
    }),
  );
  await page.unroute("**/api/runs/queue");
  await page.route("**/api/runs/queue", (route) => {
    if (route.request().method() === "POST") completed = true;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        entries: [],
        active_run_id: null,
        queued_count: 0,
        updated_at: "2026-07-28T18:00:00Z",
      }),
    });
  });
  await page.unroute("**/api/lifecycle");
  await page.route("**/api/lifecycle", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        schema_version: "1",
        generated_at: "2026-07-28T18:00:00Z",
        records: completed
          ? [
              {
                record_id: `simulation:trade_cumulus:${variation.simulation_id}`,
                record_kind: "simulation",
                owner_id: "trade_cumulus",
                owner_label: "Trade Cumulus",
                simulation_id: variation.simulation_id,
                experiment_id: null,
                world_id: "trade_cumulus",
                recipe_id: "canonical_bomex_trade_cumulus",
                recipe_version: "1",
                parent_simulation_id: worldBaselineSimulation.simulation_id,
                reference_simulation_id: worldBaselineSimulation.simulation_id,
                display_name: variation.display_name,
                question: "How does a direct moisture target change the cloud field?",
                role: "variation",
                case_id: "trade_cumulus_recipe_variation_v1",
                differences: variation.configuration_difference_from_reference,
                attempts: [
                  {
                    attempt_id: variation.run_id,
                    run_id: variation.run_id,
                    relationship: "initial",
                    accepted_backing: true,
                    manifest_path: "/mock/trade-direct-moisture/run_manifest.json",
                    lifecycle_state: "completed",
                    queue_state: null,
                    product_state: "completed_cm1_result",
                    validation_status: "valid",
                    result_id: variation.result_id,
                    output_artifact_count: 121,
                    size_bytes: 2 * 1024 ** 3,
                    retained_state: "retained",
                    created_at: "2026-07-28T17:00:00Z",
                    started_at: "2026-07-28T17:01:00Z",
                    finished_at: "2026-07-28T17:25:00Z",
                    updated_at: "2026-07-28T17:25:00Z",
                    message: null,
                    failure_reason: null,
                  },
                ],
                facts: {
                  scientific_work: "present",
                  package: "present",
                  attempt: "present",
                  queue: "not_applicable",
                  process: "passed",
                  expected_output: "present",
                  technical_integrity: "passed",
                  ingest: "present",
                  world_inspectability: "passed",
                  simulation_availability: "present",
                  parent_eligibility: "eligible",
                  retained_assets: "present",
                },
                trust_state: "trusted",
                caveats: [],
                tags: ["controlled physical variation"],
                notes: null,
                lifecycle_label: "Available",
                lifecycle_detail: "The Simulation is inspectable in Trade Cumulus.",
                activity_group: "recently_completed",
                in_activity: true,
                created_at: "2026-07-28T17:00:00Z",
                updated_at: "2026-07-28T17:25:00Z",
                size_bytes: 2 * 1024 ** 3,
                dependencies: [],
                actions: [
                  {
                    kind: "explore",
                    label: "Explore",
                    world_id: "trade_cumulus",
                    simulation_id: variation.simulation_id,
                    result_id: variation.result_id,
                  },
                ],
              },
            ]
          : [],
        warnings: [],
      }),
    }),
  );
}

test.describe("mocked smoke: Build, Results, Explore path", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockCloudChamberApis(page);
    await page.route("**/api/comparisons/trade-cumulus-moisture-v1", (route) =>
      route.fulfill({ status: 404, contentType: "application/json", body: "{}" }),
    );
    await gotoApp(page);
  });

  test("Cloud Worlds completes the World-scoped desktop journey", async ({ page }) => {
    const browserErrors: string[] = [];
    const failedRequests: string[] = [];
    page.on("pageerror", (error) => browserErrors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("response", (response) => {
      if (response.status() >= 400) {
        failedRequests.push(`${response.status()} ${new URL(response.url()).pathname}`);
      }
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.unroute("**/api/worlds");
    await page.unroute("**/api/comparisons/trade-cumulus-moisture-v1");
    await mockTradeCumulusWorld(page);
    await gotoApp(page);

    await expect(page.getByRole("heading", { name: "Cloud Worlds" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Trade Cumulus" })).toBeVisible();
    await page.waitForLoadState("networkidle");
    failedRequests.length = 0;
    browserErrors.length = 0;
    await expect(page.getByRole("navigation", { name: "Cloud Chamber workspace" })).toHaveCount(0);
    await page.getByRole("button", { name: "Enter Trade Cumulus" }).click();

    await expect(page.getByRole("navigation", { name: "Trade Cumulus sections" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Return to the cloud field" })).toBeVisible();
    await page
      .getByLabel("Canonical BOMEX Baseline Simulation")
      .getByRole("button", { name: "Explore" })
      .click();
    await expect(page.getByRole("heading", { name: "Canonical BOMEX Baseline" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Back to Trade Cumulus" })).toBeVisible();
    await expect(page.getByLabel("Canonical BOMEX Baseline workspace")).toBeVisible();
    await expect(page.getByLabel("True 3-D scalar field viewer")).toBeVisible();
    await expect(page.getByRole("slider", { name: "Saved output time" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Context" })).toBeVisible();
    await expect(page.getByText("Cloud formed")).toBeVisible();
    await expect(page.getByText("Deep convection not detected")).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Updraft Lens" })).toBeVisible({
      timeout: 12_000,
    });
    const lensButton = page.getByRole("button", { name: "Updraft Lens" });
    await expect(lensButton).toBeEnabled();
    await expect(lensButton).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toBeVisible();
    await page.getByRole("button", { name: "Previous" }).click();
    await page.getByLabel("Updraft Lens slice position").fill("3");
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("3");
    await expect(page.getByLabel("Current scientific context")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Where is air rising and sinking through cloud?" }),
    ).toBeVisible();
    await page.getByRole("tab", { name: "Details" }).click();
    await expect(page.getByRole("heading", { name: "Simulation details" })).toBeVisible();
    await page.getByRole("button", { name: "Hide Context" }).click();
    await expect(page.getByRole("button", { name: "Show Context" })).toBeVisible();
    await page.getByRole("button", { name: "Show Context" }).click();
    await expect(page.getByLabel("Current scientific context")).toBeVisible();
    await expect(page.getByRole("button", { name: "Compare" })).toBeVisible();
    await page.getByRole("button", { name: "Back to Trade Cumulus" }).click();

    await page.getByRole("button", { name: "Activity", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Current work" })).toBeVisible();
    await expect(page.getByText("Canonical BOMEX Baseline")).toBeVisible();
    await page.getByRole("button", { name: "History", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Retained scientific work" })).toBeVisible();
    await expect(page.getByText("Trade Cumulus · Simulation")).toBeVisible();
    await page.getByText("Technical details").click();
    await expect(page.getByRole("region", { name: "Technical attempts" })).toContainText(
      "Backing output",
    );
    await page.getByRole("button", { name: "Overview", exact: true }).click();

    await page.getByRole("button", { name: "Open Comparison" }).click();
    await expect(
      page.getByRole("heading", {
        name: "Review the two Simulations before loading frames",
      }),
    ).toBeVisible();
    await expect(page.getByText("0.0520 g/kg m/s")).toBeVisible();
    await expect(page.getByText("0.0780 g/kg m/s")).toBeVisible();
    await page.getByRole("button", { name: "Open dual view" }).click();
    await expect(page.getByLabel("Trade Cumulus Compare")).toBeVisible();
    await expect(page.getByLabel("Canonical BOMEX Baseline comparison side")).toBeVisible();
    await expect(page.getByLabel("More Moisture comparison side")).toBeVisible();
    await expect(page.getByRole("button", { name: "Independent" })).toHaveClass(/active-control/);
    await page.getByRole("button", { name: "Aligned" }).click();
    await expect(page.getByRole("checkbox", { name: "Time", exact: true })).toBeChecked();
    await expect(page.getByRole("checkbox", { name: "Field / Lens", exact: true })).toBeChecked();
    await page.getByRole("button", { name: "Back to Trade Cumulus" }).click();

    const worldNav = page.getByRole("navigation", { name: "Trade Cumulus sections" });
    await expect(worldNav.getByRole("button", { name: "Activity" })).toBeVisible();
    await expect(worldNav.getByRole("button", { name: "History" })).toBeVisible();
    await expect(worldNav.getByRole("button", { name: "Lab" })).toHaveCount(0);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
    expect(failedRequests).toEqual([]);
    expect(browserErrors).toEqual([]);
  });

  test("Fun With Soundings carries a selected atmosphere into shared Activity and History", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.unroute("**/api/worlds");
    await page.unroute("**/api/comparisons/trade-cumulus-moisture-v1");
    await mockTradeCumulusWorld(page);
    await page.route("**/api/worlds/mountain-waves", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ simulations: [] }),
      }),
    );
    await page.route("**/api/worlds/supercells", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ simulations: [] }),
      }),
    );
    await page.route("**/api/results", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [comparisonBaselineResult, comparisonMoreMoistureResult, ...results],
        }),
      }),
    );
    await gotoApp(page);

    await page.getByRole("button", { name: "Open Fun With Soundings" }).click();
    await expect(page).toHaveURL(/\/fun-with-soundings$/);
    await expect(page.getByRole("heading", { name: "Fun With Soundings" })).toBeVisible();
    await expect(page.getByText("Atmospheric workbench", { exact: true })).toBeVisible();
    await expect(page.getByText("Not a Cloud World", { exact: true })).toBeVisible();

    const jobs = page.getByRole("navigation", { name: "Fun With Soundings sections" });
    await expect(jobs.getByRole("button")).toHaveCount(5);
    await jobs.getByRole("button", { name: "2 Candidates" }).click();
    await page.getByText("Advanced filters", { exact: true }).click();
    await page.getByRole("button", { name: "Apply advanced filters" }).click();

    const valleyCard = page.getByLabel("Sounding candidate Valley, Nebraska (USM00072558)");
    await expect(valleyCard).toBeVisible();
    await valleyCard.getByRole("button", { name: "Configure run" }).click();
    await expect(page.getByLabel("Selected sounding run setup")).toBeVisible();
    await expect(page.getByLabel("Selected atmosphere")).toContainText(
      "Valley, Nebraska (USM00072558)",
    );

    await page.getByRole("button", { name: "Add to run plan" }).click();
    await expect(page.getByRole("region", { name: "Run plan" })).toBeVisible();
    await page.getByRole("button", { name: "Create packages and queue selected runs" }).click();
    await expect(page.getByText("1 queued locally")).toBeVisible();
    await page.getByRole("button", { name: "Open Runs" }).click();
    await expect(page.getByRole("heading", { name: "Current work" })).toBeVisible();
    await expect(
      page.getByText("Observed Surface-Forced Evolution — TOPEKA/MUN.; KS."),
    ).toBeVisible();
    await expect(page.getByText("Legacy surface-forcing attempt")).toBeVisible();
    await page.getByRole("button", { name: "History", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Retained scientific work" })).toBeVisible();
    await page.getByText("More filters", { exact: true }).click();
    await expect(page.getByLabel("Owner")).toHaveValue("all");
    await page.getByRole("searchbox", { name: "Search" }).fill("legacy");
    await expect(page.getByText("Legacy surface-forcing attempt")).toBeVisible();
    await expect(
      page.getByText("Observed Surface-Forced Evolution — TOPEKA/MUN.; KS."),
    ).toHaveCount(0);
    await page.getByRole("button", { name: "Clear filters" }).click();

    await page.getByRole("button", { name: "Activity", exact: true }).click();
    await page
      .locator("article", { hasText: "Observed Surface-Forced Evolution — TOPEKA/MUN.; KS." })
      .getByRole("button", { name: "Explore" })
      .click();
    await expect(page).toHaveURL(/\/fun-with-soundings\/explore\/result-observed-sounding$/);
    await expect(page.getByRole("combobox", { name: "Soundings Experiment" })).toHaveValue(
      "result-observed-sounding",
    );
    await page.getByRole("button", { name: "Back to Activity & History" }).click();
    await expect(page.getByRole("heading", { name: "Current work" })).toBeVisible();
  });

  test("Build exposes the Golden Path scenario and creates a safe dry-run package", async ({
    page,
  }) => {
    await gotoBuild(page);

    await expect(page.locator("select").first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Observed Soundings" })).toBeVisible();
    await page.getByLabel("Experiment", { exact: true }).selectOption("baseline-shallow-cumulus");
    await expect(page.getByText(/physical question/i).first()).toBeVisible();
    await expect(page.getByText(/how do low-level moisture/i).first()).toBeVisible();
    await openRunMonitor(page);
    await expect(
      page.getByRole("heading", { name: "Packages and runs needing action" }),
    ).toBeVisible();
    await expect(
      page.getByTestId("package-review-panel").getByText("Not packaged yet").first(),
    ).toBeVisible();
    await expect(page.getByText("Build pipeline")).toBeVisible();
    await expect(page.getByText("Local experiment loop")).not.toBeVisible();
    await expect(page.getByText("Ready to ingest")).toBeVisible();
    await expect(page.getByRole("button", { name: "Preview cleanup" }).first()).toBeVisible();
    await page.getByLabel("Low-level humidity").selectOption("more_humid");
    await expect(page.getByText(/Selected: More humid/i)).toBeVisible();

    await page.getByTestId("create-package-btn").scrollIntoViewIfNeeded();
    await page.getByTestId("create-package-btn").click();

    await expect(page.getByTestId("package-review-panel")).toBeVisible();
    await expect(page.getByText("Package ready").first()).toBeVisible();
    await expect(page.getByText("Latest generated package")).toBeVisible();
    await expect(page.getByRole("button", { name: "Create another package" })).toBeVisible();
    await expect(page.getByText("/tmp/cloud-chamber-e2e/run/run_manifest.json")).toBeVisible();
    await expect(page.getByText("Expected output directory").locator("..")).toContainText(
      "/tmp/cloud-chamber-e2e/run",
    );
    await expect(page.getByText(/not a completed CM1 result/i).first()).toBeVisible();
    await expect(page.getByTestId("launch-cm1-btn")).toBeEnabled();

    await page.getByTestId("launch-cm1-btn").click();
    await expect(
      page.getByLabel("Local serial run queue").getByText("Auto-ingested", { exact: true }),
    ).toBeVisible();
    await expect(page.getByTestId("ingest-results-btn")).toHaveCount(0);

    await page
      .getByLabel("Ingested result actions")
      .getByRole("button", { name: "Open in Results" })
      .click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
  });

  test("Build can review an observed IGRA sounding before package creation", async ({ page }) => {
    await gotoBuild(page);

    await page
      .getByLabel("Experiment", { exact: true })
      .selectOption("__observed_sounding_upload__");
    await expect(page.getByRole("heading", { name: "Observed Soundings" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Find interesting soundings" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Station catalog" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(page.getByLabel("IGRA station sounding-data file")).not.toBeVisible();
    await page.getByRole("tab", { name: "Upload IGRA file" }).click();
    await expect(page.getByLabel("IGRA station sounding-data file")).toBeVisible();
    await expect(page.getByLabel("Low-level humidity")).not.toBeVisible();
    await expect(page.getByLabel("Use uploaded sounding")).not.toBeVisible();

    await page.getByLabel("IGRA station sounding-data file").setInputFiles({
      name: "USM00072558-data.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("#USM00072558 2025 01 02 00"),
    });

    await expect(page.getByText("Observed sounding validated for package review")).toBeVisible();
    await expect(page.getByText("Valley, Nebraska (USM00072558)").first()).toBeVisible();
    await expect(page.locator("#observed-sounding-time")).toHaveValue("2025-01-02T00:00:00Z");
    const observedReview = page.getByLabel("Observed sounding review");
    await observedReview.getByText("Uploaded-sounding review").click();
    await expect(observedReview.getByText("USM00072558 · Valley, Nebraska")).toBeVisible();
    await expect(
      observedReview.getByText(/CM1 z=0 is station surface at 351.5 m MSL/i),
    ).toBeVisible();
    await expect(observedReview.getByText(/generated CM1 namelist uses isnd=7/i)).toBeVisible();

    await observedReview.getByText("Observed-sounding caveats").click();
    await expect(
      observedReview.getByText("Station elevation joined from igra station fixture"),
    ).toBeVisible();

    await page.getByRole("button", { name: "Add to run plan" }).click();
    await expect(
      page.getByText("Valley, Nebraska (USM00072558) added to the run plan"),
    ).toBeVisible();
    await expect(page.getByLabel("Run plan").getByLabel("Surface heat flux").first()).toHaveValue(
      "8.0e-3",
    );
    await expect(
      page.getByLabel("Run plan").getByLabel("Surface moisture flux").first(),
    ).toHaveValue("5.2e-5");

    await page.getByRole("button", { name: "Create packages and queue selected runs" }).click();
    await expect(page.getByText("Queued for local serial CM1 run.")).toBeVisible();
    await expect(page.getByText("1 queued locally")).toBeVisible();
  });

  test("Build can screen, save, and use observed sounding candidates", async ({ page }) => {
    await gotoBuild(page);

    await page
      .getByLabel("Experiment", { exact: true })
      .selectOption("__observed_sounding_upload__");
    await expect(page.getByRole("heading", { name: "Find interesting soundings" })).toBeVisible();
    await expect(page.getByText("Cached soundings ready to search")).toBeVisible();
    await expect(page.getByLabel("Prepare and search local soundings")).toContainText(
      "Selected soundings",
    );
    await expect(page.getByLabel("Station picker")).toContainText("All cached stations");
    await expect(page.getByLabel("Local sounding data")).toContainText("2 cached soundings");
    await expect(page.getByLabel("Advanced sounding candidate controls")).not.toBeVisible();

    await page.getByText("Advanced filters", { exact: true }).click();
    await page.getByRole("button", { name: "Refresh catalog" }).click();
    await expect(page.getByText("IGRA station catalog refreshed")).toBeVisible();
    await expect(page.getByLabel("Local sounding data")).toContainText("2 cached soundings");
    await page.getByLabel("Local sounding data").locator("summary").click();
    await expect(page.getByText("Parsed soundings")).toBeVisible();

    const candidateControls = page.getByLabel("Advanced sounding candidate controls");
    const storySelect = candidateControls.getByRole("combobox").first();
    await storySelect.selectOption("shallow_cumulus_candidate");
    await page.getByRole("button", { name: "Apply advanced filters" }).click();

    await expect(page.getByText("Cached sounding analysis loaded")).toBeVisible();
    const valleyCard = page.getByLabel("Sounding candidate Valley, Nebraska (USM00072558)");
    await expect(valleyCard).toBeVisible();
    await expect(valleyCard).toContainText("Cloud-forming shallow cumulus");
    await expect(valleyCard).toContainText("Package-ready");
    await expect(valleyCard).toContainText("Why it surfaced");
    await expect(valleyCard).toContainText("Good for a surface-forced run");
    const candidateDetails = page.getByLabel("Candidate details");
    await expect(candidateDetails).toContainText("Why this is interesting");
    await expect(candidateDetails).toContainText("Run guidance");
    await expect(candidateDetails).toContainText("Run fit");
    await expect(candidateDetails).toContainText("Top limits");
    await expect(candidateDetails).not.toContainText("Scores rank sounding ingredients only");
    await expect(
      candidateDetails.getByText("All evidence").locator("xpath=.."),
    ).not.toHaveAttribute("open");

    await storySelect.selectOption("needs_review");
    await page.getByRole("button", { name: "Apply advanced filters" }).click();
    const blockedCard = page.getByLabel("Sounding candidate Norman, Oklahoma (USM00072357)");
    await expect(blockedCard).toBeVisible();
    await expect(blockedCard).toContainText("Blocked");
    await expect(blockedCard.getByRole("button", { name: "Configure run" })).toBeDisabled();

    await storySelect.selectOption("all");
    await page.getByRole("button", { name: "Apply advanced filters" }).click();
    const refreshedValleyCard = page.getByLabel(
      "Sounding candidate Valley, Nebraska (USM00072558)",
    );
    await refreshedValleyCard.click();
    await expect(page.getByRole("textbox", { name: "Tags" })).toHaveCount(0);
    await page
      .getByLabel("Candidate details")
      .getByRole("button", { name: "Save candidate" })
      .click();
    await page.getByRole("textbox", { name: "Tags" }).fill("smoke");
    await page.getByLabel("Save candidate notes").getByRole("button", { name: "Save" }).click();
    await expect(page.getByText("Sounding candidate saved")).toBeVisible();
    await page.getByRole("tab", { name: /Saved candidates/ }).click();
    const savedCard = page.getByLabel("Saved sounding candidate Valley, Nebraska (USM00072558)");
    await expect(savedCard).toBeVisible();

    await savedCard.getByRole("button", { name: "Configure run" }).click();
    await expect(page.getByLabel("Selected sounding run setup")).toBeVisible();
    const selectedSetupOrderIsCorrect = await page.evaluate(() => {
      const saved = document.querySelector(
        '[aria-label="Saved sounding candidate Valley, Nebraska (USM00072558)"]',
      );
      const setup = document.querySelector('[aria-label="Selected sounding run setup"]');
      const runPlan = document.querySelector('[aria-label="Run plan"]');
      return Boolean(
        saved &&
        setup &&
        runPlan &&
        saved.compareDocumentPosition(setup) & Node.DOCUMENT_POSITION_FOLLOWING &&
        setup.compareDocumentPosition(runPlan) & Node.DOCUMENT_POSITION_FOLLOWING,
      );
    });
    expect(selectedSetupOrderIsCorrect).toBe(true);
    await page.getByRole("button", { name: "Add to run plan" }).click();
    await expect(
      page.getByText("Valley, Nebraska (USM00072558) added to the run plan"),
    ).toBeVisible();
    await expect(page.getByLabel("Run plan").getByLabel("Surface heat flux").first()).toHaveValue(
      "8.0e-3",
    );
    await expect(
      page.getByLabel("Run plan").getByLabel("Surface moisture flux").first(),
    ).toHaveValue("5.2e-5");
    await page.getByRole("button", { name: "Duplicate variant" }).click();
    await expect(page.getByText("Run-plan variant duplicated")).toBeVisible();

    await page.getByRole("button", { name: "Create packages and queue selected runs" }).click();
    await expect(page.getByText("2 queued locally")).toBeVisible();
    await expect(page.getByText("Queued for local serial CM1 run.").first()).toBeVisible();
  });

  test("Results notebook renders with mocked data", async ({ page }) => {
    await gotoResults(page);

    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    const resultsList = page.getByLabel("Results list");
    await expect(resultsList).toBeVisible();
    await expect(page.getByText("Baseline Shallow Cumulus — Quick Look").first()).toBeVisible();
    await expect(
      resultsList.getByText(/Cloud water formed in the validated reference baseline/i),
    ).toBeVisible();
    await expect(resultsList.getByText("Cloud formed").first()).toBeVisible();
    await expect(resultsList.getByText("Rain water aloft detected").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Open in Explore" }).first()).toBeVisible();
    const resultDetail = page.getByLabel("Result detail");
    await resultDetail.getByText("Technical details").click();
    await expect(resultDetail.getByText("Run ID")).toBeVisible();
    await expect(resultDetail.getByText("Product state")).toBeVisible();
    await expect(
      resultDetail.getByRole("button", { name: "Preview delete result and local run data" }),
    ).toBeVisible();
    await expect(resultDetail.getByText("Local data")).toBeVisible();
    await expect(page.getByRole("tab", { name: "Compare" })).toHaveCount(0);
    await expect(page.getByRole("tab", { name: "Storage" })).toHaveCount(0);
  });

  test("Results opens the complete curated Trade Cumulus comparison story", async ({ page }) => {
    const browserErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(`console: ${message.text()}`);
    });
    page.on("pageerror", (error) => browserErrors.push(`page: ${error.message}`));
    page.on("requestfailed", (request) => {
      const failure = request.failure()?.errorText ?? "unknown failure";
      if (request.url().includes("/api/") && !failure.includes("ERR_ABORTED")) {
        browserErrors.push(`request: ${request.method()} ${request.url()} (${failure})`);
      }
    });

    await mockTradeCumulusComparison(page);
    await page.reload();
    await gotoResults(page);
    browserErrors.length = 0;

    await page.getByRole("button", { name: "Canonical BOMEX Baseline" }).click();
    const resultDetail = page.getByLabel("Result detail");
    await resultDetail.getByRole("button", { name: "Compare Baseline and More Moisture" }).click();

    await expect(
      page.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toBeVisible();
    await expect(page.getByText(comparisonStory.question)).toBeVisible();
    await expect(page.getByLabel("Changed condition")).toContainText("+50%");
    await expect(page.getByText(comparisonStory.illustrative_view_note)).toBeVisible();

    const simulations = page.locator("article.comparison-simulation");
    await expect(simulations).toHaveCount(2);
    await expect(simulations.nth(0)).toContainText("18,240 s · 05:04:00");
    await expect(simulations.nth(0)).toContainText("Vertical x-z slice at y = -2.65 km");
    await expect(simulations.nth(1)).toContainText("20,280 s · 05:38:00");
    await expect(simulations.nth(1)).toContainText("Vertical x-z slice at y = 1.95 km");
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toHaveCount(2);
    await expect(page.getByTestId("updraft-lens-cloud-boundary")).toHaveCount(2);
    await expect(page.getByLabel(/3-D viewer Vertical velocity \(w\), m\/s/)).toHaveCount(2);
    await expect(page.getByLabel(/2-D inspector Vertical velocity \(w\), m\/s/)).toHaveCount(2);
    await expect(page.getByRole("heading", { name: "What responded materially" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "What changed little or varied" }),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "What stayed fixed" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "What this comparison suggests" }),
    ).toBeVisible();

    const canvases = page.locator("canvas.true3d-canvas");
    await expect(canvases).toHaveCount(2);
    for (let index = 0; index < 2; index += 1) {
      await expect(canvases.nth(index)).toBeVisible();
      const dimensions = await canvases.nth(index).evaluate((canvas: HTMLCanvasElement) => ({
        displayWidth: canvas.clientWidth,
        displayHeight: canvas.clientHeight,
        renderWidth: canvas.width,
        renderHeight: canvas.height,
      }));
      expect(dimensions.displayWidth).toBeGreaterThan(100);
      expect(dimensions.displayHeight).toBeGreaterThan(100);
      expect(dimensions.renderWidth).toBeGreaterThan(100);
      expect(dimensions.renderHeight).toBeGreaterThan(100);
      const renderedPixels = await canvases.nth(index).screenshot();
      expect(renderedPixels.byteLength).toBeGreaterThan(5_000);
    }

    const baselineControls = simulations.nth(0).getByLabel("3-D camera controls");
    const moreMoistureControls = simulations.nth(1).getByLabel("3-D camera controls");
    await baselineControls.getByRole("button", { name: "Look along x" }).click();
    await expect(baselineControls).toContainText("Camera looking along the x axis");
    await expect(moreMoistureControls).toContainText("Camera set to overview");

    await page.setViewportSize({ width: 1440, height: 1000 });
    await simulations.nth(1).getByRole("button", { name: "Open More Moisture in Explore" }).click();
    await expect(
      page.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toHaveCount(0);
    await expect(page.getByLabel("Explore viewer controls")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("More Moisture").first()).toBeVisible();

    await page
      .getByRole("navigation", { name: "Cloud Chamber workspace" })
      .getByRole("button", { name: "Results" })
      .click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    await page.getByRole("button", { name: "More Moisture", exact: true }).click();
    await page
      .getByLabel("Result detail")
      .getByRole("button", { name: "Compare Baseline and More Moisture" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Back to Results" }).click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    expect(browserErrors).toEqual([]);
  });

  test("Results filters and sorts by science metadata", async ({ page }) => {
    await gotoResults(page);

    const filterBar = page.getByLabel("Filter and sort results");
    const resultsList = page.getByLabel("Results list");

    await expect(filterBar).toBeVisible();
    await expect(resultsList.getByText(/first cloud 1,800 s/i).first()).toBeVisible();

    await filterBar.getByLabel("Search").fill("Valley");
    await expect(resultsList.getByText("Uploaded Sounding — Valley, Nebraska")).toBeVisible();
    await expect(
      resultsList.getByText("Observed sounding: USM00072558 · Valley, Nebraska"),
    ).toBeVisible();
    await expect(resultsList.getByText("Baseline Shallow Cumulus — Quick Look")).toHaveCount(0);

    await filterBar.getByLabel("Search").fill("");
    await filterBar.getByLabel("Scenario").selectOption("input_source:observed_sounding");
    await expect(resultsList.getByText("Uploaded Sounding — Valley, Nebraska")).toBeVisible();
    await expect(resultsList.getByText("Baseline Shallow Cumulus — Quick Look")).toHaveCount(0);

    await filterBar.getByLabel("Scenario").selectOption("all");
    await filterBar.getByLabel("Cloud outcome").selectOption("no");
    await expect(resultsList.getByText("Dry Failed Cumulus — Quick Look")).toBeVisible();
    await expect(resultsList.getByText("Uploaded Sounding — Valley, Nebraska")).toHaveCount(0);

    await filterBar.getByLabel("Cloud outcome").selectOption("all");
    await filterBar.getByLabel("Sort results").selectOption("max_updraft");
    await expect(resultsList.locator(".experiment-card").first()).toContainText(
      "Uploaded Sounding — Valley, Nebraska",
    );
  });

  test("Results deletes ingested results and Build keeps non-ingested cleanup", async ({
    page,
  }) => {
    await gotoResults(page);

    const resultDetail = page.getByLabel("Result detail");
    await resultDetail
      .getByRole("button", { name: "Preview delete result and local run data" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Delete result and local run data preview" }),
    ).toBeVisible();
    await expect(
      page.getByText(/result will disappear from Results, Explore, and local inventory/),
    ).toBeVisible();
    await expect(page.getByText("Result metadata and notebook edits")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Delete result and local run data", exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Delete result and local run data", exact: true })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: /Result and local run data deleted/ }),
    ).toBeVisible();
    await expect(
      page.getByLabel("Results list").getByText("Baseline Shallow Cumulus — Quick Look"),
    ).toHaveCount(0);

    await gotoBuild(page);
    await openRunMonitor(page);
    const pipelineRuns = page.getByLabel("Local packages and runs");
    const ingestReadyRun = pipelineRuns.locator("article", { hasText: "dry-run-disposable" });
    await expect(ingestReadyRun.getByText("Ready to ingest")).toBeVisible();
    await expect(ingestReadyRun.getByRole("button", { name: "Preview cleanup" })).toBeEnabled();
    await ingestReadyRun.getByRole("button", { name: "Preview cleanup" }).click();
    await expect(
      page.getByRole("heading", { name: "Delete local package/run data preview" }),
    ).toBeVisible();
    await expect(page.getByText(/does not touch Results entries/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Confirm delete local run data" })).toBeVisible();

    await ingestReadyRun.getByRole("button", { name: "Ingest output" }).click();
    await expect(page.getByText("Ingested result metadata")).toBeVisible();

    const runningRun = pipelineRuns.locator("article", { hasText: "dry-run-running" });
    await expect(runningRun.getByText("Running", { exact: true })).toBeVisible();
    await expect(runningRun.getByRole("button", { name: "Preview cleanup" })).toBeDisabled();

    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();
    await expect(page.getByLabel("Integrated Explore workspace")).toBeVisible();
  });

  test("Unified Explore renders cloud context, slice inspector, and explanation", async ({
    page,
  }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByLabel("Integrated Explore workspace")).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByLabel("Explore viewer controls")).toBeVisible();
    await expect(page.getByLabel("True 3-D scalar field viewer")).toBeVisible({
      timeout: 12_000,
    });
    await expect(
      page.getByLabel(
        "Interactive Three.js scene showing a CM1 scalar field, domain bounds, slice plane, and selected point",
      ),
    ).toBeVisible();
    await expect(page.getByLabel("3-D camera controls")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Field Slice" })).toBeVisible();
    await expect(page.getByText(/Horizontal layer at z = /i).first()).toBeVisible();
    await expect(page.getByLabel("Slice position")).toBeVisible();
    const heatmap = page.getByRole("img", { name: /heatmap/i });
    await expect(heatmap).toBeVisible();
    await expect(page.getByTestId("slice-cloud-boundary")).toBeVisible();
    const heatmapLayout = await heatmap.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      const grid = element.querySelector<HTMLElement>(".slice-heatmap-grid");
      const row = element.querySelector<HTMLElement>(".heatmap-row");
      return {
        declaredAspect: Number(element.getAttribute("data-domain-aspect")),
        renderedAspect: bounds.width / bounds.height,
        renderedWidth: bounds.width,
        renderedHeight: bounds.height,
        contentFits:
          element.scrollWidth <= element.clientWidth &&
          element.scrollHeight <= element.clientHeight,
        gridGap: grid ? getComputedStyle(grid).gap : null,
        rowGap: row ? getComputedStyle(row).gap : null,
        padding: getComputedStyle(element).padding,
      };
    });
    expect(Math.abs(heatmapLayout.declaredAspect - heatmapLayout.renderedAspect)).toBeLessThan(
      0.03,
    );
    expect(heatmapLayout.renderedWidth).toBeGreaterThan(220);
    expect(heatmapLayout.renderedHeight).toBeGreaterThan(220);
    expect(heatmapLayout.contentFits).toBe(true);
    expect(heatmapLayout.gridGap).toBe("0px");
    expect(heatmapLayout.rowGap).toBe("0px");
    expect(heatmapLayout.padding).toBe("0px");
    const fieldControlsPrecedeHeatmap = await heatmap.evaluate((element) => {
      const fieldControl = document.querySelector("#explore-slice-field");
      return Boolean(
        fieldControl &&
        fieldControl.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING,
      );
    });
    expect(fieldControlsPrecedeHeatmap).toBe(true);
    await expect(page.getByText("Cloud formed")).toBeVisible();
    await expect(page.getByText("Cloud formed here")).toHaveCount(0);
    await page
      .getByRole("button", { name: /inspect .*row 2, column 2/i })
      .first()
      .click();
    const selectedEvidence = page.getByLabel("Selected native-grid evidence");
    await expect(selectedEvidence).toBeVisible();
    await expect(
      selectedEvidence.getByRole("heading", { name: "Native-grid evidence" }),
    ).toBeVisible();
    await expect(selectedEvidence.getByText("Cloud water", { exact: true })).toBeVisible();
    await expect(selectedEvidence.getByText("Native cell", { exact: true })).toBeVisible();
    await page.getByRole("tab", { name: "Science" }).click();
    await expect(page.getByRole("button", { name: "Load selected-column history" })).toBeVisible();
    await expect(page.getByText("Thermal Fate")).toHaveCount(0);
    await expect(page.getByText("What happened here?")).toHaveCount(0);
    await page.getByRole("button", { name: "Load selected-column history" }).click();
    const localHistory = page.getByLabel("Selected-column history");
    await expect(localHistory.getByText("Vertical-motion envelope")).toBeVisible();
    await expect(localHistory.getByText("First local cloud")).toBeVisible();
    await localHistory.getByText("Cloud-depth evolution").click();
    await expect(localHistory.getByText(/1,800 s: base 500 m, top 1,100 m/)).toBeVisible();
    await page.getByRole("tab", { name: "Details" }).click();
    await page.getByText("Technical slice details").first().click();
    await expect(page.getByText(/finite values/i).first()).toBeVisible();
    await expect(page.getByText(/\[\[[\d.,\s]+\]\]/)).not.toBeVisible();

    await expect(page.getByRole("button", { name: /reset camera/i })).toBeVisible();
    await expect(page.getByText(/selected: x/i)).toBeVisible();
  });

  test("Trade Cumulus activates the Updraft Lens with coordinated rendering controls", async ({
    page,
  }) => {
    const catalog = await page.evaluate(async () =>
      fetch("/api/results/result-baseline/visualization/fields").then((response) =>
        response.json(),
      ),
    );
    const tradeResult = {
      ...results[0],
      name: "Trade Cumulus",
      scenario_id: "bomex_trade_cumulus_baseline_v0",
      scenario_name: "Trade Cumulus",
      run_configuration: {
        ...results[0].run_configuration,
        case_id: "bomex_trade_cumulus_baseline_v0",
      },
    };
    catalog.scenario_id = "bomex_trade_cumulus_baseline_v0";
    catalog.available_fields[0] = {
      ...catalog.available_fields[0],
      raw_field: "ql",
      raw_field_name: "ql",
      display_name: "Cloud liquid",
    };
    const updraftScale = {
      w_range_min_m_s: -1.0,
      w_range_max_m_s: 5.0,
      w_range_method: "fixed_trade_cumulus_updraft_velocity_v1",
      w_scale_id: "trade_cumulus_updraft_velocity_v1",
      w_scale_owner: "trade_cumulus",
      w_scale_type: "fixed_discrete",
      w_scale_units: "m/s",
      w_scale_breakpoints_m_s: [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 2.0, 3.0, 5.0],
      w_scale_colors: [
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
      w_scale_neutral_interval_m_s: [-0.1, 0.1],
      w_scale_source: "pm_approved_issue_379_from_stage5b2_matched_pair",
      w_scale_clipping_behavior:
        "values_below_-1.0_and_at_or_above_5.0_use_endpoint_colors_and_are_reported_as_clipped",
    };

    await page.route("**/api/results", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ results: [tradeResult] }),
      }),
    );
    await page.route("**/api/results/result-baseline/visualization/fields", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(catalog),
      }),
    );
    await page.route(
      "**/api/results/result-baseline/visualization/trade-cumulus-updraft-lens/defaults",
      (route) =>
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            result_id: "result-baseline",
            case_id: "bomex_trade_cumulus_baseline_v0",
            eligible: true,
            primary_field: "w",
            cloud_field: "ql",
            orientation: "vertical_x",
            default_time_index: 1,
            default_time_seconds: 1800,
            default_time_method: "max_finite_domain_mean_cwp_at_or_after_10800_seconds",
            default_plane_dimension: "y",
            default_plane_index: 2,
            default_plane_coordinate: 0.05,
            default_plane_units: "km",
            default_plane_method: "greatest_coherent_positive_w_times_ql_score",
            cloud_threshold_kg_kg: 1e-6,
            ...updraftScale,
            wind_target_level_m: 600,
            wind_actual_level_m: 580,
            wind_level_index: 1,
            wind_default_mode: "perturbation",
            wind_stride: 8,
            wind_shown_by_default: true,
            perturbation_wind_reference_m_s: 0.9,
            total_wind_reference_m_s: 8.8,
            wind_arrow_domain_fraction: 0.08,
            provenance: catalog.provenance,
            caveats: [],
          }),
        }),
    );
    await page.route(
      "**/api/results/result-baseline/visualization/trade-cumulus-updraft-lens/frame**",
      (route) => {
        const url = new URL(route.request().url());
        const windMode = url.searchParams.get("wind_mode") === "total" ? "total" : "perturbation";
        const orientation =
          url.searchParams.get("orientation") === "horizontal"
            ? "horizontal"
            : url.searchParams.get("orientation") === "vertical_y"
              ? "vertical_y"
              : "vertical_x";
        const planeIndex = Number(url.searchParams.get("plane_index") ?? 2);
        const timeIndex = Number(url.searchParams.get("time_index") ?? 1);
        const planeDimension =
          orientation === "horizontal" ? "z" : orientation === "vertical_y" ? "x" : "y";
        const dimensionOrder =
          orientation === "horizontal"
            ? ["y", "x"]
            : orientation === "vertical_y"
              ? ["z", "y"]
              : ["z", "x"];
        const wValues =
          orientation === "horizontal"
            ? [
                [-1.2, -0.4, 0.2, 0.6],
                [-0.5, 0, 0.5, 0.9],
                [-0.2, 0.3, 0.7, 5.2],
                [0, 0.1, 0.4, 0.2],
              ]
            : [
                [-1.2, -0.4, 0.2, 0.6],
                [-0.5, 0, 0.5, 0.9],
                [-0.2, 0.3, 0.7, 5.2],
                [0, 0.1, 0.4, 0.2],
              ];
        const finiteW = wValues.flat().filter((value): value is number => Number.isFinite(value));
        const lowClippedCount = finiteW.filter((value) => value < -1.0).length;
        const highClippedCount = finiteW.filter((value) => value >= 5.0).length;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            result_id: "result-baseline",
            time_index: timeIndex,
            time_seconds: [0, 1800, 3600][timeIndex] ?? 1800,
            orientation,
            plane_dimension: planeDimension,
            plane_index: planeIndex,
            plane_coordinate: [-0.15, -0.05, 0.05, 0.15][planeIndex] ?? 0.05,
            plane_units: "km",
            dimension_order: dimensionOrder,
            x_indices: [0, 1, 2, 3],
            x_values_km: [-0.15, -0.05, 0.05, 0.15],
            y_indices: [0, 1, 2, 3],
            y_values_km: [-0.15, -0.05, 0.05, 0.15],
            z_indices: [0, 1, 2, 3],
            z_values_km: [0.1, 0.3, 0.5, 0.7],
            w_values_m_s: wValues,
            cloud_mask: [
              [false, false, false, false],
              [false, true, true, false],
              [true, true, true, false],
              [false, true, false, false],
            ],
            cloud_threshold_kg_kg: 1e-6,
            ...updraftScale,
            w_finite_count: finiteW.length,
            w_low_clipped_count: lowClippedCount,
            w_high_clipped_count: highClippedCount,
            w_low_clipped_fraction: lowClippedCount / finiteW.length,
            w_high_clipped_fraction: highClippedCount / finiteW.length,
            wind_mode: windMode,
            wind_target_level_m: 600,
            wind_actual_level_m: 580,
            wind_level_index: 1,
            wind_stride: 8,
            wind_reference_m_s: windMode === "total" ? 8.8 : 0.9,
            wind_arrow_domain_fraction: 0.08,
            domain_mean_u_m_s: -8,
            domain_mean_v_m_s: 0,
            wind_vectors: [
              {
                x_km: 0,
                y_km: 0,
                z_km: 0.58,
                u_m_s: windMode === "total" ? -7.5 : 0.5,
                v_m_s: 0.2,
                magnitude_m_s: windMode === "total" ? 7.5 : 0.54,
              },
            ],
            provenance: catalog.provenance,
            caveats: [],
          }),
        });
      },
    );

    await page.reload();
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    const savedTime = page.getByRole("slider", { name: "Saved output time" });
    const viewMode = page.getByLabel("Explore view mode");
    await expect(viewMode).toBeVisible();
    const lensToggle = viewMode.getByRole("button", { name: "Updraft Lens" });
    await expect(lensToggle).toBeEnabled();
    await expect(lensToggle).toHaveAttribute("aria-pressed", "true");
    await expect(viewMode.getByRole("button").allTextContents()).resolves.toEqual([
      "Updraft Lens",
      "Field",
    ]);
    await viewMode.getByRole("button", { name: "Field" }).click();
    await expect(page.getByRole("heading", { name: "Field Slice" })).toBeVisible();
    await lensToggle.click();
    await expect(page.getByRole("heading", { name: "Updraft Lens" })).toBeVisible();
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toBeVisible();
    await expect(page.getByLabel("Cloud boundary")).toBeChecked();
    await expect(page.getByRole("checkbox", { name: "Horizontal wind" })).toBeChecked();
    await expect(page.getByRole("button", { name: "Local departures" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByLabel("Horizontal wind overlay legend")).toContainText(
      "0.9 m/s reference",
    );
    const inspectorLegend = page.getByLabel(/Explore workspace Vertical velocity \(w\), m\/s/);
    await expect(inspectorLegend).toContainText("w (m/s)");
    await expect(inspectorLegend).toContainText("-0.1 to < 0.1");
    await expect(page.locator(".updraft-lens-scale-swatch")).toHaveCount(10);
    await expect(inspectorLegend.getByRole("listitem").first()).not.toContainText("m/s");
    await expect(page.getByText("Slice maximum 5.20 m/s.")).toHaveCount(0);
    await expect(page.getByText("Slice minimum -1.20 m/s.")).toHaveCount(0);
    await expect(page.getByText(/Clipped in this slice/)).toHaveCount(0);
    const compactLensLayout = await page
      .locator(".updraft-lens-instrument-body-compact")
      .evaluate((body) => {
        const svg = body.querySelector<SVGElement>(".updraft-lens-svg");
        const legend = body.querySelector<HTMLElement>(".updraft-lens-scale-legend-compact");
        const svgBounds = svg?.getBoundingClientRect();
        const legendBounds = legend?.getBoundingClientRect();
        return {
          plotWidth: svgBounds?.width ?? 0,
          plotHeight: svgBounds?.height ?? 0,
          legendBelowPlot: Boolean(
            svgBounds && legendBounds && legendBounds.top >= svgBounds.bottom,
          ),
        };
      });
    expect(compactLensLayout.plotWidth).toBeGreaterThan(100);
    expect(compactLensLayout.plotHeight).toBeGreaterThan(200);
    expect(compactLensLayout.legendBelowPlot).toBe(true);
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("2");
    await expect(page.getByRole("button", { name: "Vertical x-z" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(
      page.getByText("Updraft Lens: Vertical x-z slice at y = 0.05 km", { exact: true }),
    ).toBeVisible();
    await expect(page.getByLabel("Slice field")).toHaveCount(0);
    await page.locator("details.true3d-display-control > summary").click();
    const displayAlignment = await page.locator(".true3d-controls-compact").evaluate((controls) => {
      const elements = [
        controls.querySelector(".true3d-display-control > summary"),
        controls.querySelector("select[aria-label='Camera view']"),
        ...controls.querySelectorAll(":scope > button"),
      ].filter((element): element is Element => element !== null);
      const centers = elements.map((element) => {
        const bounds = element.getBoundingClientRect();
        return bounds.top + bounds.height / 2;
      });
      return Math.max(...centers) - Math.min(...centers);
    });
    expect(displayAlignment).toBeLessThan(1.5);
    const scalarField = page.getByLabel("3-D scalar field", { exact: true });
    await expect(scalarField).toBeVisible();
    await scalarField.selectOption("qv");
    await expect(scalarField).toHaveValue("qv");
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("2");
    await expect(page.getByRole("img", { name: /y index 2/ })).toBeVisible();
    await page.getByLabel("Layer opacity").fill("0.45");
    await page.getByLabel("Point size").fill("14");
    await page.getByLabel("Lens opacity").fill("0.6");
    await expect(page.getByLabel("Layer opacity")).toHaveValue("0.45");
    await expect(page.getByLabel("Point size")).toHaveValue("14");
    await expect(page.getByLabel("Lens opacity")).toHaveValue("0.6");
    await expect(page.getByLabel("True 3-D scalar field viewer")).toHaveAttribute(
      "data-updraft-lens-opacity",
      "0.6",
    );
    const sliceAspect = await page.locator(".updraft-lens-svg").evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      return {
        declared: Number(element.getAttribute("data-domain-aspect")),
        rendered: bounds.width / bounds.height,
      };
    });
    expect(Math.abs(sliceAspect.declared - sliceAspect.rendered)).toBeLessThan(0.03);

    await page.getByRole("button", { name: "Horizontal x-y" }).click();
    await expect(
      page.getByRole("img", { name: /Updraft Lens horizontal x-y slice/ }),
    ).toBeVisible();
    await expect(page.getByText(/Updraft Lens: Horizontal x-y layer at z =/)).toBeVisible();
    await page.getByRole("button", { name: "Vertical y-z" }).click();
    await expect(page.getByRole("img", { name: /Updraft Lens vertical y-z slice/ })).toBeVisible();
    await expect(page.getByText(/Updraft Lens: Vertical y-z slice at x =/)).toBeVisible();
    await page.getByRole("button", { name: "Vertical x-z" }).click();
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toBeVisible();

    await page.getByLabel("Updraft Lens slice position").fill("3");
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("3");
    await expect(page.getByRole("img", { name: /y index 3/ })).toBeVisible();
    await expect(
      page.getByText("Updraft Lens: Vertical x-z slice at y = 0.15 km", { exact: true }),
    ).toBeVisible();
    await savedTime.fill("2");
    await expect(page.getByText("3,600 s · frame 3 of 3", { exact: true })).toBeVisible();
    await expect(inspectorLegend).toContainText("w (m/s)");
    await expect(inspectorLegend).toContainText(">= 5.0");

    await page.getByRole("button", { name: "Total wind" }).click();
    await expect(page.getByLabel("Horizontal wind overlay legend")).toContainText(
      "8.8 m/s reference",
    );
    await page.getByLabel("Cloud boundary").uncheck();
    await expect(page.getByTestId("updraft-lens-cloud-boundary")).toHaveCount(0);
    await expect(page.getByLabel("True 3-D scalar field viewer")).toHaveAttribute(
      "data-updraft-lens-cloud-boundary",
      "false",
    );
    await page.getByRole("checkbox", { name: "Horizontal wind" }).uncheck();
    await expect(page.getByLabel("Horizontal wind overlay legend")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    ).toBe(true);

    await page.getByRole("button", { name: "Maximize slice viewer" }).click();
    await expect(inspectorLegend).toContainText("Vertical velocity (w), m/s");
    await expect(inspectorLegend).toContainText("Slice maximum 5.20 m/s.");
    await expect(inspectorLegend).toContainText("Slice minimum -1.20 m/s.");
    const focusedLensFit = await page.locator(".updraft-lens-instrument-body").evaluate((body) => {
      const svg = body.querySelector<SVGElement>(".updraft-lens-svg");
      const xLabels = body.querySelectorAll<HTMLElement>(".updraft-lens-axis-x span");
      const zLabels = body.querySelectorAll<HTMLElement>(".updraft-lens-axis-z span");
      const bodyBounds = body.getBoundingClientRect();
      const svgBounds = svg?.getBoundingClientRect();
      return {
        bodyFits: body.scrollWidth <= body.clientWidth && body.scrollHeight <= body.clientHeight,
        expands: Boolean(svgBounds) && svgBounds!.height >= 420,
        svgFits:
          Boolean(svgBounds) &&
          svgBounds!.right <= bodyBounds.right + 1 &&
          svgBounds!.bottom <= bodyBounds.bottom + 1,
        axesAlign:
          Boolean(svgBounds) &&
          Math.abs(xLabels[0].getBoundingClientRect().left - svgBounds!.left) < 4 &&
          Math.abs(xLabels[1].getBoundingClientRect().right - svgBounds!.right) < 4 &&
          Math.abs(zLabels[0].getBoundingClientRect().top - svgBounds!.top) < 4 &&
          Math.abs(zLabels[1].getBoundingClientRect().bottom - svgBounds!.bottom) < 4,
        axisDeltas: svgBounds
          ? {
              xStart: xLabels[0].getBoundingClientRect().left - svgBounds.left,
              xEnd: xLabels[1].getBoundingClientRect().right - svgBounds.right,
              zTop: zLabels[0].getBoundingClientRect().top - svgBounds.top,
              zBottom: zLabels[1].getBoundingClientRect().bottom - svgBounds.bottom,
            }
          : null,
      };
    });
    expect(focusedLensFit).toMatchObject({
      bodyFits: true,
      expands: true,
      svgFits: true,
      axesAlign: true,
    });

    await page.getByRole("button", { name: "Horizontal x-y" }).click();
    await expect(
      page.getByRole("img", { name: /Updraft Lens horizontal x-y slice/ }),
    ).toBeVisible();
    const focusedTopDownFit = await page
      .locator(".updraft-lens-instrument-body")
      .evaluate((body) => {
        const svg = body.querySelector<SVGElement>(".updraft-lens-svg");
        const bounds = svg?.getBoundingClientRect();
        return {
          expands: Boolean(bounds) && bounds!.height >= 420,
          preservesAspect:
            Boolean(bounds) &&
            Math.abs(
              bounds!.width / bounds!.height - Number(svg!.getAttribute("data-domain-aspect")),
            ) < 0.03,
          noOverflow:
            body.scrollWidth <= body.clientWidth && body.scrollHeight <= body.clientHeight,
        };
      });
    expect(focusedTopDownFit).toEqual({
      expands: true,
      preservesAspect: true,
      noOverflow: true,
    });
    await page.getByRole("button", { name: "Vertical x-z" }).click();
    await page.getByRole("button", { name: "Restore slice viewer" }).click();

    await viewMode.getByRole("button", { name: "Field" }).click();
    await expect(page.getByRole("heading", { name: "Field Slice" })).toBeVisible();
    await expect(page.getByLabel("Slice field")).toBeVisible();
    await expect(savedTime).toHaveValue("2");
    await expect(page.getByLabel("Slice position")).toHaveValue("3");
    await expect(page.getByRole("button", { name: "Vertical x-z slice", exact: true })).toHaveClass(
      /active-control/,
    );

    await lensToggle.click();
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("3");
    await expect(savedTime).toHaveValue("2");
    await expect(page.getByRole("button", { name: "Vertical x-z" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  test("Unified Explore plays through saved output times", async ({ page }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByLabel("Explore viewer controls")).toBeVisible();
    await expect(page.getByLabel("Timelapse playback controls")).toBeVisible();
    const playbackButton = page.getByLabel("Timelapse playback controls").getByRole("button");
    await expect(playbackButton).toHaveAccessibleName("Play");
    await expect(page.getByLabel("Playback speed")).toHaveValue("1");
    await expect(page.getByRole("slider", { name: "Saved output time" })).toBeVisible();

    const savedTime = page.getByRole("slider", { name: "Saved output time" });
    await savedTime.fill("1");
    await page.getByLabel("Playback speed").selectOption("0.5");
    await playbackButton.click();

    await expect(playbackButton).toHaveAccessibleName("Pause");
    await expect(playbackButton).toHaveAttribute("aria-pressed", "true");
    await expect(savedTime).toHaveValue("2", { timeout: 4_000 });
    await expect(playbackButton).toHaveAccessibleName("Play", { timeout: 4_000 });
    await expect(playbackButton).toHaveAttribute("aria-pressed", "false");
    await expect(savedTime).toHaveValue("0");

    await page.getByLabel("Key moments").selectOption({ label: "Last frame" });
    await expect(savedTime).toHaveValue("2");
    await playbackButton.click();
    await expect(savedTime).toHaveValue("0", { timeout: 4_000 });
    await expect(playbackButton).toHaveAccessibleName("Play");
    await expect(playbackButton).toHaveAttribute("aria-pressed", "false");
  });

  test("Explore keeps current context primary and persists notes below the viewers", async ({
    page,
  }) => {
    await mockTradeCumulusWorld(page);
    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Trade Cumulus" }).click();
    await page
      .getByLabel("Canonical BOMEX Baseline Simulation")
      .getByRole("button", { name: "Explore" })
      .click();

    await expect(page.getByLabel("Integrated Explore workspace")).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByLabel("Current scientific context")).toBeVisible();
    await expect(page.getByRole("tab", { name: "Science" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Notes" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Details" })).toBeVisible();
    await expect(page.getByText("Process evidence")).toHaveCount(0);

    const support = page.getByLabel("Simulation support", { exact: true });
    await support.scrollIntoViewIfNeeded();
    await support.getByRole("tab", { name: "Notes" }).click();
    const notes = support.getByRole("textbox", { name: /Notes for/ });
    await notes.fill("Watch the western cloud turret.");
    await support.getByRole("button", { name: "Save note" }).click();
    await expect(support.getByRole("status")).toHaveText("Saved");
    await expect(notes).toHaveValue("Watch the western cloud turret.");
    await support.getByRole("tab", { name: "Details" }).click();
    await expect(page.getByRole("heading", { name: "Simulation details" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Field quality" })).toBeVisible();
  });

  test("Results to Explore loads cloud-forming qc and w fields", async ({ page }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/slice synced/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#explore-slice-field")).toHaveValue("qc");
    await expect(
      page.locator("#explore-slice-field option", { hasText: "qc - Cloud water" }),
    ).toHaveCount(1);
    await expect(
      page.locator("#explore-slice-field option", {
        hasText: "w - Vertical velocity (slice only)",
      }),
    ).toHaveCount(1);
    await expect(page.getByText(/loading fields/i)).not.toBeVisible();

    await expect(page.getByText(/cloud-water point layer loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.getByText(/cloud-water point layer/i).first()).toBeVisible();
  });

  test("Explore exposes expanded 3-D scalar fields without promoting slice-only fields", async ({
    page,
  }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/cloud-water point layer loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await page.locator("details.true3d-display-control > summary").click();
    const threeDField = page.locator("#explore-3d-field");
    await expect(threeDField).toBeVisible();
    await expect(threeDField.locator("option", { hasText: "qc - Cloud water" })).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "qr - Rain water" })).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "qv - Water vapor" })).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "dbz - Reflectivity" })).toHaveCount(1);
    await expect(
      threeDField.locator("option", { hasText: "rain - Accumulated surface rain" }),
    ).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "temperature" })).toHaveCount(0);
    await expect(threeDField.locator("option", { hasText: "theta" })).toHaveCount(0);
    await expect(threeDField.locator("option", { hasText: "Vertical velocity" })).toHaveCount(0);

    await threeDField.selectOption("qr");
    await expect(page.getByText("Rain-water point layer loaded").first()).toBeVisible();
    await expect(page.locator("#explore-slice-field")).toHaveValue("qr");

    await threeDField.selectOption("qv");
    await expect(page.getByText("Water-vapor point layer loaded").first()).toBeVisible();
    await expect(page.locator("#explore-slice-field")).toHaveValue("qv");

    await threeDField.selectOption("dbz");
    await expect(page.getByText("Reflectivity point layer loaded").first()).toBeVisible();
    const threeDLegend = page.getByLabel("3-D field color legend");
    await expect(threeDLegend.getByText("0 dBZ")).toBeVisible();
    await expect(threeDLegend.getByText("60+ dBZ")).toBeVisible();

    await threeDField.selectOption("rain");
    await expect(page.getByText("Surface-rain floor layer loaded").first()).toBeVisible();
    await expect(page.locator("#explore-slice-field")).toHaveValue("rain");
    await expect(page.getByRole("button", { name: "Vertical x-z slice" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Vertical y-z slice" })).toBeDisabled();
  });

  test("Results to Explore treats Dry Failed as no-cloud with updraft inspection", async ({
    page,
  }) => {
    await gotoResults(page);
    await page
      .getByRole("article", { name: "Dry Failed Cumulus — Quick Look experiment" })
      .getByRole("button", { name: "Open in Explore" })
      .click();

    await expect(page.getByText("Dry Failed Cumulus — Quick Look").first()).toBeVisible();
    await expect(page.getByText(/No cloud water formed in this result/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.locator("#explore-slice-field")).toHaveValue("w");
    await expect(
      page.getByText(/No cloud water formed in this result; vertical velocity is available/i),
    ).toBeVisible();
    await expect(page.getByLabel("Current scientific context")).toContainText(
      "Use vertical velocity slices to inspect thermals that did not produce cloud.",
    );
    await expect(page.getByText("No cloud formed here")).toHaveCount(0);

    await expect(page.getByText(/slice synced/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#explore-slice-field")).toHaveValue("w");
    await expect(
      page.locator("#explore-slice-field option", {
        hasText: "w - Vertical velocity (slice only)",
      }),
    ).toHaveCount(1);
  });

  test("Explore field loading failure shows an error and retry instead of a stuck spinner", async ({
    page,
  }) => {
    await page.route("**/api/results/*/visualization/fields", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Visualization fields temporarily failed." }),
      }),
    );

    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByRole("alert")).toContainText("Visualization fields temporarily failed.");
    await expect(page.getByRole("button", { name: "Retry loading fields" })).toBeVisible();
    await expect(page.getByText("Loading fields...", { exact: true })).not.toBeVisible();
  });

  test("Explore isolates a failed 3-D layer from the slice timeline and inspector", async ({
    page,
  }) => {
    await page.route("**/api/results/*/visualization/point-cloud**", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Point cloud temporarily unavailable." }),
      }),
    );

    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText("3-D cloud layer unavailable")).toBeVisible();
    await expect(page.getByRole("button", { name: "Retry 3-D layer" })).toBeVisible();
    await expect(page.getByText("Slice synced")).toBeVisible();
    await expect(page.getByRole("slider", { name: "Saved output time" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Context" })).toBeVisible();
  });

  test("Explore isolates a failed slice from the 3-D scene timeline and inspector", async ({
    page,
  }) => {
    await page.route("**/api/results/*/visualization/slice**", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Slice temporarily unavailable." }),
      }),
    );

    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText("Field Slice unavailable")).toBeVisible();
    await expect(page.getByRole("button", { name: "Retry Field Slice" })).toBeVisible();
    await expect(page.getByLabel("True 3-D scalar field viewer")).toBeVisible();
    await expect(page.getByRole("slider", { name: "Saved output time" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Context" })).toBeVisible();
  });

  test("Explore desktop cockpit prioritizes viewers and supports either maximized view", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/Horizontal layer at z = /i).first()).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByLabel("Slice position")).toBeVisible();
    const heatmap = page.getByRole("img", { name: /heatmap/i });
    await expect(heatmap).toBeVisible({ timeout: 10_000 });

    const scene = page.getByLabel("True 3-D scalar field viewer");
    const slice = page.getByLabel("Field Slice");
    const context = page.getByRole("complementary", { name: "Context" });
    const notebook = page.getByRole("region", {
      name: "Simulation support",
      exact: true,
    });
    await expect(scene).toBeVisible({ timeout: 12_000 });
    await expect(slice).toBeVisible();
    await expect(context).toBeVisible();

    const cockpitGeometry = await page.evaluate(() => {
      const rect = (selector: string) => document.querySelector(selector)?.getBoundingClientRect();
      const sliceControls = document.querySelector<HTMLElement>(".explore-control-card-slice");
      const timeline = document.querySelector<HTMLElement>(".explore-control-card-time");
      const notebookRegion = document.querySelector<HTMLElement>(".explore-secondary-content");
      const sceneRegion = document.querySelector<HTMLElement>(".true3d-viewer");
      return {
        documentFits: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
        sliceControlsFit:
          Boolean(sliceControls) &&
          sliceControls!.scrollWidth <= sliceControls!.clientWidth &&
          sliceControls!.scrollHeight <= sliceControls!.clientHeight,
        timelineFits:
          Boolean(timeline) &&
          timeline!.scrollWidth <= timeline!.clientWidth &&
          timeline!.scrollHeight <= timeline!.clientHeight,
        notebookBelowScene:
          Boolean(notebookRegion && sceneRegion) &&
          notebookRegion!.getBoundingClientRect().top >=
            sceneRegion!.getBoundingClientRect().bottom,
        shell: rect(".visualizer-shell")?.width ?? 0,
      };
    });
    expect(cockpitGeometry).toEqual({
      documentFits: true,
      sliceControlsFit: true,
      timelineFits: true,
      notebookBelowScene: true,
      shell: expect.any(Number),
    });
    expect(cockpitGeometry.shell).toBeGreaterThan(1200);

    await page.getByRole("button", { name: "Maximize 3-D viewer" }).click();
    await expect(page.getByLabel("Integrated Explore workspace")).toHaveClass(
      /visualizer-shell-focused-scene/,
    );
    await expect(page.getByRole("button", { name: "Restore 3-D viewer" })).toBeVisible();
    await page.getByRole("button", { name: "Restore 3-D viewer" }).click();

    await page.getByRole("button", { name: "Maximize slice viewer" }).click();
    await expect(page.getByLabel("Integrated Explore workspace")).toHaveClass(
      /visualizer-shell-focused-slice/,
    );
    await expect(page.getByRole("button", { name: "Restore slice viewer" })).toBeVisible();
    const focusedHeatmap = page.getByRole("img", { name: /heatmap/i });
    const focusedHeatmapBox = await focusedHeatmap.boundingBox();
    expect(focusedHeatmapBox?.width ?? 0).toBeGreaterThan(280);
    expect(focusedHeatmapBox?.height ?? 0).toBeGreaterThan(280);
    await page.getByRole("button", { name: "Restore slice viewer" }).click();
    await expect(notebook).toBeAttached();
  });

  test("Trade Cumulus direct-value variation reaches Activity, Explore, Compare, and reuse", async ({
    page,
  }) => {
    await mockTradeCumulusVariationPath(page);
    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Trade Cumulus" }).click();
    await page
      .getByRole("navigation", { name: "Trade Cumulus sections" })
      .getByRole("button", { name: "Create Variation", exact: true })
      .click();

    await expect(page.getByRole("heading", { name: "Atmosphere and forcing" })).toBeVisible();
    await expect(page.getByLabel("Moisture flux exact value")).toHaveValue("0.052");
    await expect(page.getByText("0 material changes")).toBeVisible();

    await page.getByLabel("Moisture flux exact value").fill("0.09");
    await page.getByLabel("Sensible heat flux exact value").fill("0.012");
    await expect(page.getByText("2 material changes")).toBeVisible();
    await expect(page.getByText("Multi-factor physical variation")).toBeVisible();

    await page.getByRole("radio", { name: /Standard/ }).check();
    await expect(page.getByText("Mixed physical and numerical variation")).toBeVisible();
    await page.getByLabel("Inversion base exact value").fill("4000");
    await expect(page.getByRole("alert")).toContainText(
      "requested inversion does not fit the model top",
    );
    await expect(page.getByRole("button", { name: "Package variation" })).toBeDisabled();

    await page.getByRole("button", { name: "Restore parent" }).click();
    await page.getByRole("radio", { name: /Extended/ }).check();
    await expect(page.getByText("This profile is uncharacterized.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Package variation" })).toBeDisabled();

    await page.getByRole("button", { name: "Restore parent" }).click();
    await page.getByLabel("Variation name").fill("Direct Moisture Target");
    await page.getByLabel("Moisture flux exact value").fill("0.09");
    await expect(page.getByText("Controlled physical variation")).toBeVisible();
    await page.getByRole("button", { name: "Package variation" }).click();
    await expect(
      page.getByText("Direct Moisture Target is packaged. It has not been queued."),
    ).toBeVisible();
    await page.getByRole("button", { name: "Queue CM1" }).click();

    await expect(page.getByRole("heading", { name: "Current work" })).toBeVisible();
    await expect(page.locator("article", { hasText: "Direct Moisture Target" })).toBeVisible();
    await page.getByRole("button", { name: "Simulations" }).click();
    const descendant = page.locator("article", { hasText: "Direct Moisture Target" });
    await expect(descendant.getByRole("button", { name: "Explore" })).toBeEnabled();
    await expect(descendant.getByRole("button", { name: "Compare" })).toBeEnabled();
    await expect(descendant.getByRole("button", { name: "Create variation" })).toBeEnabled();

    await descendant.getByRole("button", { name: "Compare" }).click();
    await expect(
      page.getByRole("heading", { name: "Review the two Simulations before loading frames" }),
    ).toBeVisible();
    await expect(page.getByText("Controlled pair")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Surface moisture flux" })).toBeVisible();
    await page.getByRole("button", { name: "Back to Trade Cumulus" }).click();

    await page.getByRole("button", { name: "Simulations" }).click();
    await page
      .locator("article", { hasText: "Direct Moisture Target" })
      .getByRole("button", { name: "Create variation" })
      .click();
    await expect(page.getByLabel("Parent Simulation")).toHaveValue(
      "trade_cumulus_direct_moisture_abcd1234",
    );
  });

  test("Trade Cumulus keeps a package failure inside Create Variation", async ({ page }) => {
    await mockTradeCumulusVariationPath(page, { failPackage: true });
    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Trade Cumulus" }).click();
    await page
      .getByRole("navigation", { name: "Trade Cumulus sections" })
      .getByRole("button", { name: "Create Variation", exact: true })
      .click();
    await page.getByLabel("Variation name").fill("Rejected direct target");
    await page.getByLabel("Moisture flux exact value").fill("0.09");
    await page.getByRole("button", { name: "Package variation" }).click();

    await expect(page.getByRole("alert")).toHaveText("Variation package preflight failed.");
    await expect(page.getByRole("heading", { name: "Atmosphere and forcing" })).toBeVisible();
  });
});
