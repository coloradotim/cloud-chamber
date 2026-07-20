import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  TradeCumulusComparisonStory,
  type TradeCumulusComparisonStoryResponse,
} from "./TradeCumulusComparisonStory";

vi.mock("./True3DViewer", () => ({
  True3DViewer: ({ resultName }: { resultName: string }) => (
    <div data-testid="comparison-true3d-viewer">{resultName} 3-D viewer</div>
  ),
}));

vi.mock("./UpdraftLensSlice", () => ({
  UpdraftLensSlice: ({ frame }: { frame: { result_id: string } }) => (
    <div data-testid="comparison-updraft-lens-slice">{frame.result_id} Lens slice</div>
  ),
}));

const baselineId = "result-trade-cumulus-5b-full-baseline-20260720T162342Z";
const moreId = "result-trade-cumulus-5b-full-more_moisture-20260720T162342Z";

const story: TradeCumulusComparisonStoryResponse = {
  comparison_id: "trade_cumulus_moisture_v1",
  comparison_group_id: "trade_cumulus_moisture_v1",
  product_slice_id: "trade_cumulus_v1",
  case_id: "bomex_trade_cumulus_baseline_v0",
  title: "Trade Cumulus: Baseline and More Moisture",
  question: "How does stronger surface moisture supply change the trade-cumulus field?",
  illustrative_view_note:
    "Illustrative views: selected to help show the response measured across the full simulations. Times and locations may differ, and these are not corresponding individual clouds.",
  baseline: {
    result_id: baselineId,
    run_id: "trade-cumulus-5b-full-baseline-20260720T162342Z",
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
    result_id: moreId,
    run_id: "trade-cumulus-5b-full-more_moisture-20260720T162342Z",
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
    baseline_run_id: "trade-cumulus-5b-full-baseline-20260720T162342Z",
    baseline_result_id: baselineId,
    more_moisture_run_id: "trade-cumulus-5b-full-more_moisture-20260720T162342Z",
    more_moisture_result_id: moreId,
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

function pointCloud(member: TradeCumulusComparisonStoryResponse["baseline"]) {
  return {
    result_id: member.result_id,
    run_id: member.run_id,
    scenario_id: "bomex_trade_cumulus_baseline_v0",
    field: { raw_field_name: "ql", display_name: "Cloud water", units: "kg/kg" },
    selection: {
      field: "ql",
      time_index: member.curated_view.time_index,
      time_seconds: member.curated_view.time_seconds,
      threshold: 1e-6,
      max_points: 50_000,
    },
    coordinate_units: { xh: "km", yh: "km", zh: "km" },
    coordinate_extents: {
      xh: { min: -3.2, max: 3.2, units: "km" },
      yh: { min: -3.2, max: 3.2, units: "km" },
      zh: { min: 0, max: 3, units: "km" },
    },
    points: [[0, 0, 1, 0.001]],
    stats: {
      source_count: 1,
      returned_count: 1,
      field_min_value: 0,
      field_max_value: 0.001,
      field_mean_value: 0.0001,
      field_finite_count: 1,
      field_non_finite_count: 0,
      min_value: 0.001,
      max_value: 0.001,
      active_z_min: 1,
      active_z_max: 1,
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

function frame(member: TradeCumulusComparisonStoryResponse["baseline"]) {
  return {
    result_id: member.result_id,
    time_index: member.curated_view.time_index,
    time_seconds: member.curated_view.time_seconds,
    orientation: "vertical_x",
    plane_dimension: "y",
    plane_index: member.curated_view.plane_index,
    plane_coordinate: member.curated_view.plane_coordinate,
    plane_units: "km",
    dimension_order: ["z", "x"],
    x_indices: [0, 1],
    x_values_km: [-0.05, 0.05],
    y_indices: [0, 1],
    y_values_km: [-0.05, 0.05],
    z_indices: [0, 1],
    z_values_km: [0.02, 0.06],
    w_values_m_s: [[-0.5, 1]],
    cloud_mask: [[true, false]],
    cloud_threshold_kg_kg: 1e-6,
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
    w_scale_clipping_behavior: "endpoint colors",
    w_finite_count: 2,
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
    wind_vectors: [{ x_km: 0, y_km: 0, z_km: 0.58, u_m_s: 0.4, v_m_s: 0.2, magnitude_m_s: 0.45 }],
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

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      const member = url.includes(moreId) ? story.more_moisture : story.baseline;
      const payload = url.includes("point-cloud") ? pointCloud(member) : frame(member);
      return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TradeCumulusComparisonStory", () => {
  it("loads both exact views and renders the complete authored story", async () => {
    render(
      <TradeCumulusComparisonStory
        story={story}
        onOpenResult={vi.fn()}
        onBackToResults={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toBeInTheDocument();
    expect(screen.getByText(story.question)).toBeInTheDocument();
    expect(screen.getByText(story.illustrative_view_note)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByTestId("comparison-true3d-viewer")).toHaveLength(2);
    });
    expect(screen.getAllByTestId("comparison-updraft-lens-slice")).toHaveLength(2);
    expect(screen.getByText("18,240 s · 05:04:00")).toBeInTheDocument();
    expect(screen.getByText("20,280 s · 05:38:00")).toBeInTheDocument();
    expect(screen.getAllByText("Vertical x-z slice at y = -2.65 km")).toHaveLength(2);
    expect(screen.getAllByText("Vertical x-z slice at y = 1.95 km")).toHaveLength(2);
    expect(screen.getByText(story.baseline.curated_view.caption)).toBeInTheDocument();
    expect(screen.getByText(story.more_moisture.curated_view.caption)).toBeInTheDocument();
    expect(screen.getByText("+50%")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What responded materially" })).toBeInTheDocument();
    expect(screen.getByText("+2.115 percentage points")).toBeInTheDocument();
    expect(screen.getByText("+42.812%")).toBeInTheDocument();
    expect(screen.getByText("+137 m")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "What changed little or varied" }),
    ).toBeInTheDocument();
    expect(screen.getByText(story.small_or_mixed_responses[3].body)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What stayed fixed" })).toBeInTheDocument();
    expect(screen.getByText("Execution and outputs")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "What this comparison suggests" }),
    ).toBeInTheDocument();
    story.explanation_paragraphs.forEach((paragraph) => {
      expect(screen.getByText(paragraph)).toBeInTheDocument();
    });

    const requestedUrls = vi.mocked(fetch).mock.calls.map(([input]) => String(input));
    expect(requestedUrls).toContain(
      `/api/results/${baselineId}/visualization/point-cloud?field=ql&time_index=152&threshold=0.000001&max_points=50000&encoding=json`,
    );
    expect(requestedUrls).toContain(
      `/api/results/${baselineId}/visualization/trade-cumulus-updraft-lens/frame?time_index=152&plane_index=5&orientation=vertical_x&wind_mode=perturbation`,
    );
    expect(requestedUrls).toContain(
      `/api/results/${moreId}/visualization/point-cloud?field=ql&time_index=169&threshold=0.000001&max_points=50000&encoding=json`,
    );
    expect(requestedUrls).toContain(
      `/api/results/${moreId}/visualization/trade-cumulus-updraft-lens/frame?time_index=169&plane_index=51&orientation=vertical_x&wind_mode=perturbation`,
    );
    expect(screen.queryByRole("button", { name: "Play time" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Position")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("2-D slice field")).not.toBeInTheDocument();
  });

  it("fails closed when either returned frame conflicts with the story", async () => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      const member = url.includes(moreId) ? story.more_moisture : story.baseline;
      const payload = url.includes("point-cloud")
        ? pointCloud(member)
        : {
            ...frame(member),
            time_seconds:
              member === story.more_moisture ? 20_400 : member.curated_view.time_seconds,
          };
      return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
    });

    render(
      <TradeCumulusComparisonStory
        story={story}
        onOpenResult={vi.fn()}
        onBackToResults={vi.fn()}
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Curated Updraft Lens data conflicts with the comparison story.",
    );
    expect(screen.queryByTestId("comparison-true3d-viewer")).not.toBeInTheDocument();
    expect(screen.queryByTestId("comparison-updraft-lens-slice")).not.toBeInTheDocument();
  });

  it.each([
    { caseName: "empty", points: [] as number[][], returnedCount: 0 },
    { caseName: "count-inconsistent", points: [[0, 0, 1, 0.001]], returnedCount: 2 },
  ])("fails closed when a point cloud is $caseName", async ({ points, returnedCount }) => {
    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      const member = url.includes(moreId) ? story.more_moisture : story.baseline;
      let payload = url.includes("point-cloud") ? pointCloud(member) : frame(member);
      if (url.includes("point-cloud") && member === story.baseline) {
        payload = {
          ...pointCloud(member),
          points,
          stats: {
            ...pointCloud(member).stats,
            returned_count: returnedCount,
          },
        };
      }
      return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
    });

    render(
      <TradeCumulusComparisonStory
        story={story}
        onOpenResult={vi.fn()}
        onBackToResults={vi.fn()}
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Curated point-cloud data conflicts with the comparison story.",
    );
    expect(screen.queryByTestId("comparison-true3d-viewer")).not.toBeInTheDocument();
    expect(screen.queryByTestId("comparison-updraft-lens-slice")).not.toBeInTheDocument();
  });

  it("routes Back and both member actions without adding comparison controls", async () => {
    const onOpenResult = vi.fn();
    const onBackToResults = vi.fn();
    render(
      <TradeCumulusComparisonStory
        story={story}
        onOpenResult={onOpenResult}
        onBackToResults={onBackToResults}
      />,
    );
    await screen.findAllByTestId("comparison-true3d-viewer");

    fireEvent.click(screen.getByRole("button", { name: "Open Baseline in Explore" }));
    fireEvent.click(screen.getByRole("button", { name: "Open More Moisture in Explore" }));
    fireEvent.click(screen.getByRole("button", { name: "Back to Results" }));

    expect(onOpenResult).toHaveBeenNthCalledWith(1, baselineId);
    expect(onOpenResult).toHaveBeenNthCalledWith(2, moreId);
    expect(onBackToResults).toHaveBeenCalledOnce();
    const storyRegion = screen.getByRole("heading", {
      name: "Trade Cumulus: Baseline and More Moisture",
    }).parentElement?.parentElement;
    expect(storyRegion).not.toBeNull();
    expect(within(storyRegion!).queryByRole("button", { name: /orientation/i })).toBeNull();
  });
});
