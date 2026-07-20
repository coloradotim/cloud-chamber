import { useEffect, useState } from "react";

import { True3DViewer } from "./True3DViewer";
import { type UpdraftLensFrame, UpdraftLensSlice } from "./UpdraftLensSlice";

export type TradeCumulusCuratedView = {
  time_index: number;
  time_seconds: number;
  orientation: "vertical_x";
  plane_dimension: "y";
  plane_index: number;
  plane_coordinate: number;
  plane_units: "km";
  camera_preset: "overview";
  cloud_field: "ql";
  cloud_threshold_kg_kg: number;
  lens_id: "updraft";
  scale_id: "trade_cumulus_updraft_velocity_v1";
  wind_mode: "perturbation";
  show_wind: true;
  show_cloud_boundary: true;
  opacity: number;
  point_size: number;
  caption: string;
};

export type TradeCumulusComparisonMember = {
  result_id: string;
  run_id: string;
  display_name: string;
  control_state: "baseline" | "more_moisture";
  control_label: "Surface moisture supply";
  control_value: number;
  control_units: "g/g m/s";
  control_display: string;
  curated_view: TradeCumulusCuratedView;
};

export type TradeCumulusMaterialResponse = {
  metric_id: string;
  label: string;
  baseline_value: number;
  more_moisture_value: number;
  absolute_delta: number;
  percent_delta: number;
  units: string;
  method: string;
  window: string;
  baseline_display: string;
  more_moisture_display: string;
  change_display: string;
};

export type TradeCumulusComparisonStoryResponse = {
  comparison_id: "trade_cumulus_moisture_v1";
  comparison_group_id: "trade_cumulus_moisture_v1";
  product_slice_id: "trade_cumulus_v1";
  case_id: "bomex_trade_cumulus_baseline_v0";
  title: string;
  question: string;
  illustrative_view_note: string;
  baseline: TradeCumulusComparisonMember;
  more_moisture: TradeCumulusComparisonMember;
  changed_condition: {
    label: "Surface moisture supply";
    baseline_display: string;
    more_moisture_display: string;
    change_display: "+50%";
  };
  material_responses: TradeCumulusMaterialResponse[];
  small_or_mixed_responses: Array<{ title: string; body: string }>;
  held_fixed_by_design: {
    lead: "Only surface moisture supply changed.";
    groups: Array<{ title: string; body: string }>;
  };
  explanation_paragraphs: string[];
  evidence_summary: {
    analysis_window: "time >= 10800 s";
    analysis_start_seconds: number;
    analysis_end_seconds: number;
    output_cadence_seconds: number;
    paired_saved_frame_count: number;
  };
  provenance: {
    evidence_state: "matched_runs_valid";
    evidence_version: string;
    implementation_commit: string;
    fixed_assumptions_sha256: string;
    baseline_run_id: string;
    baseline_result_id: string;
    more_moisture_run_id: string;
    more_moisture_result_id: string;
    scale_id: "trade_cumulus_updraft_velocity_v1";
    comparison_source: "runtime_matched_pair_evidence";
  };
  caveats: string[];
};

type PointCloudResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  field: {
    raw_field_name: string;
    display_name: string;
    units: string | null;
  };
  selection: {
    field: string;
    time_index: number;
    time_seconds: number | null;
    threshold: number;
    max_points: number;
  };
  coordinate_units: Record<string, string | null>;
  coordinate_extents: Record<string, { min: number; max: number; units: string | null }>;
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
    downsampled: boolean;
    downsample_stride: number;
  };
  provenance: {
    source_model: string;
    result_id: string;
    run_id: string;
    scenario_id: string;
    processing_method: string;
    rendering_method: string;
    provenance_label: string;
  };
  caveats: string[];
};

type CuratedMemberData = {
  member: TradeCumulusComparisonMember;
  pointCloud: PointCloudResponse;
  frame: UpdraftLensFrame;
};

type ComparisonData = {
  baseline: CuratedMemberData;
  moreMoisture: CuratedMemberData;
};

export function TradeCumulusComparisonStory({
  story,
  onOpenResult,
  onBackToResults,
}: {
  story: TradeCumulusComparisonStoryResponse;
  onOpenResult: (resultId: string) => void;
  onBackToResults: () => void;
}) {
  const [data, setData] = useState<ComparisonData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setData(null);
    setError(null);

    Promise.all([
      loadCuratedMember(story.baseline, controller.signal),
      loadCuratedMember(story.more_moisture, controller.signal),
    ])
      .then(([baseline, moreMoisture]) => {
        if (!active) return;
        setData({ baseline, moreMoisture });
      })
      .catch((caught: unknown) => {
        if (!active || controller.signal.aborted) return;
        setData(null);
        setError(
          caught instanceof Error
            ? caught.message
            : "The curated comparison views could not be loaded.",
        );
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [story]);

  return (
    <section className="trade-cumulus-comparison" aria-labelledby="comparison-story-title">
      <header className="comparison-story-header">
        <div className="comparison-story-heading-row">
          <div>
            <p className="eyebrow">Curated comparison</p>
            <h2 id="comparison-story-title">{story.title}</h2>
            <p className="comparison-story-question">{story.question}</p>
          </div>
          <button type="button" className="secondary-button" onClick={onBackToResults}>
            Back to Results
          </button>
        </div>

        <dl className="comparison-changed-condition" aria-label="Changed condition">
          <div>
            <dt>{story.changed_condition.label}</dt>
            <dd>
              <span>{story.changed_condition.baseline_display}</span>
              <span aria-hidden="true">to</span>
              <span>{story.changed_condition.more_moisture_display}</span>
              <strong>{story.changed_condition.change_display}</strong>
            </dd>
          </div>
        </dl>
        <p className="comparison-illustrative-note">{story.illustrative_view_note}</p>
      </header>

      {error && (
        <section className="comparison-story-load-state" role="alert">
          <h3>Curated views unavailable</h3>
          <p>{error}</p>
        </section>
      )}

      {!data && !error && (
        <section className="comparison-story-load-state" role="status">
          <p>Loading both curated simulation views...</p>
        </section>
      )}

      {data && (
        <>
          <div className="comparison-simulation-grid" aria-label="Curated simulation views">
            <SimulationView
              data={data.baseline}
              actionLabel="Open Baseline in Explore"
              onOpenResult={onOpenResult}
            />
            <SimulationView
              data={data.moreMoisture}
              actionLabel="Open More Moisture in Explore"
              onOpenResult={onOpenResult}
            />
          </div>

          <section className="comparison-story-section" aria-labelledby="material-response-title">
            <h3 id="material-response-title">What responded materially</h3>
            <dl className="comparison-material-responses">
              {story.material_responses.map((response) => (
                <div key={response.metric_id}>
                  <dt>{response.label}</dt>
                  <dd>
                    <span>Baseline {response.baseline_display}</span>
                    <span>More Moisture {response.more_moisture_display}</span>
                    <strong>{response.change_display}</strong>
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="comparison-story-section" aria-labelledby="mixed-response-title">
            <h3 id="mixed-response-title">What changed little or varied</h3>
            <ul className="comparison-authored-list">
              {story.small_or_mixed_responses.map((response) => (
                <li key={response.title}>
                  <strong>{response.title}</strong>
                  <span>{response.body}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="comparison-story-section" aria-labelledby="held-fixed-title">
            <h3 id="held-fixed-title">What stayed fixed</h3>
            <p className="comparison-section-lead">{story.held_fixed_by_design.lead}</p>
            <dl className="comparison-held-fixed">
              {story.held_fixed_by_design.groups.map((group) => (
                <div key={group.title}>
                  <dt>{group.title}</dt>
                  <dd>{group.body}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="comparison-story-section" aria-labelledby="comparison-suggests-title">
            <h3 id="comparison-suggests-title">What this comparison suggests</h3>
            <div className="comparison-explanation">
              {story.explanation_paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </section>
        </>
      )}
    </section>
  );
}

function SimulationView({
  data,
  actionLabel,
  onOpenResult,
}: {
  data: CuratedMemberData;
  actionLabel: string;
  onOpenResult: (resultId: string) => void;
}) {
  const { member, pointCloud, frame } = data;
  const timeLabel = `${formatSeconds(member.curated_view.time_seconds)} · ${formatClock(
    member.curated_view.time_seconds,
  )}`;
  const planeLabel = `Vertical x-z slice at y = ${formatCoordinate(
    member.curated_view.plane_coordinate,
  )} km`;

  return (
    <article
      className="comparison-simulation"
      aria-labelledby={`comparison-simulation-${member.control_state}`}
      data-result-id={member.result_id}
    >
      <header className="comparison-simulation-header">
        <div>
          <p className="eyebrow">Simulation</p>
          <h3 id={`comparison-simulation-${member.control_state}`}>{member.display_name}</h3>
          <p>{member.control_display}</p>
        </div>
        <dl>
          <div>
            <dt>Model time</dt>
            <dd>{timeLabel}</dd>
          </div>
          <div>
            <dt>Lens plane</dt>
            <dd>{planeLabel}</dd>
          </div>
        </dl>
      </header>

      <p className="comparison-view-caption">{member.curated_view.caption}</p>

      <True3DViewer
        resultName={member.display_name}
        pointCloud={pointCloud}
        fieldLabel="ql — Cloud water"
        valueChannelLabel="Cloud water above the fixed threshold."
        activeSlice={null}
        activeSliceLabel={planeLabel}
        showSlicePlane={false}
        selectedRegion={null}
        coordinateSizes={{
          x: frame.x_indices.length,
          y: frame.y_indices.length,
          z: frame.z_indices.length,
        }}
        selectedTimeLabel={timeLabel}
        sceneTimeLabel={timeLabel}
        thresholdLabel="1.000e-6 kg/kg"
        opacity={member.curated_view.opacity}
        pointSize={member.curated_view.point_size}
        status="Curated view loaded"
        provenanceLabel={frame.provenance.provenance_label}
        noCloudMessage="No cloud water is visible in this curated frame."
        windVectors={frame.wind_vectors}
        showWindVectors={member.curated_view.show_wind}
        windMode={member.curated_view.wind_mode}
        windReferenceMps={frame.wind_reference_m_s}
        windArrowDomainFraction={frame.wind_arrow_domain_fraction}
        updraftLensFrame={frame}
      />

      <section className="comparison-lens-view" aria-label={`${member.display_name} Lens slice`}>
        <div className="comparison-lens-heading">
          <p className="eyebrow">Updraft Lens</p>
          <h4>{planeLabel}</h4>
        </div>
        <UpdraftLensSlice frame={frame} showCloudBoundary selectedPoint={null} />
      </section>

      <div className="comparison-simulation-action">
        <button type="button" onClick={() => onOpenResult(member.result_id)}>
          {actionLabel}
        </button>
      </div>
    </article>
  );
}

async function loadCuratedMember(
  member: TradeCumulusComparisonMember,
  signal: AbortSignal,
): Promise<CuratedMemberData> {
  const view = member.curated_view;
  const pointCloudQuery = new URLSearchParams({
    field: view.cloud_field,
    time_index: String(view.time_index),
    threshold: String(view.cloud_threshold_kg_kg),
    max_points: "50000",
    encoding: "json",
  });
  const frameQuery = new URLSearchParams({
    time_index: String(view.time_index),
    plane_index: String(view.plane_index),
    orientation: view.orientation,
    wind_mode: view.wind_mode,
  });
  const [pointCloudResponse, frameResponse] = await Promise.all([
    fetch(
      `/api/results/${member.result_id}/visualization/point-cloud?${pointCloudQuery.toString()}`,
      { signal },
    ),
    fetch(
      `/api/results/${member.result_id}/visualization/trade-cumulus-updraft-lens/frame?${frameQuery.toString()}`,
      { signal },
    ),
  ]);
  if (!pointCloudResponse.ok || !frameResponse.ok) {
    throw new Error("Both curated simulation views must load before comparison.");
  }
  const pointCloud = (await pointCloudResponse.json()) as PointCloudResponse;
  const frame = (await frameResponse.json()) as UpdraftLensFrame;
  validatePointCloud(member, pointCloud);
  validateFrame(member, frame);
  return { member, pointCloud, frame };
}

function validatePointCloud(member: TradeCumulusComparisonMember, pointCloud: PointCloudResponse) {
  const view = member.curated_view;
  if (
    pointCloud.result_id !== member.result_id ||
    pointCloud.provenance.result_id !== member.result_id ||
    pointCloud.field.raw_field_name !== view.cloud_field ||
    pointCloud.selection.field !== view.cloud_field ||
    pointCloud.selection.time_index !== view.time_index ||
    !numbersMatch(pointCloud.selection.time_seconds, view.time_seconds) ||
    !numbersMatch(pointCloud.selection.threshold, view.cloud_threshold_kg_kg) ||
    pointCloud.points.length === 0 ||
    !Number.isInteger(pointCloud.stats.returned_count) ||
    pointCloud.stats.returned_count <= 0 ||
    pointCloud.stats.returned_count !== pointCloud.points.length
  ) {
    throw new Error("Curated point-cloud data conflicts with the comparison story.");
  }
}

function validateFrame(member: TradeCumulusComparisonMember, frame: UpdraftLensFrame) {
  const view = member.curated_view;
  if (
    frame.result_id !== member.result_id ||
    frame.time_index !== view.time_index ||
    !numbersMatch(frame.time_seconds, view.time_seconds) ||
    frame.orientation !== view.orientation ||
    frame.plane_dimension !== view.plane_dimension ||
    frame.plane_index !== view.plane_index ||
    !numbersMatch(frame.plane_coordinate, view.plane_coordinate, 1e-9) ||
    frame.plane_units !== view.plane_units ||
    frame.w_scale_id !== view.scale_id ||
    !numbersMatch(frame.cloud_threshold_kg_kg, view.cloud_threshold_kg_kg)
  ) {
    throw new Error("Curated Updraft Lens data conflicts with the comparison story.");
  }
}

function numbersMatch(left: number | null, right: number, tolerance = 1e-12): boolean {
  return left !== null && Number.isFinite(left) && Math.abs(left - right) <= tolerance;
}

function formatSeconds(seconds: number): string {
  return `${seconds.toLocaleString("en-US", { maximumFractionDigits: 0 })} s`;
}

function formatClock(seconds: number): string {
  const rounded = Math.round(seconds);
  const hours = Math.floor(rounded / 3600);
  const minutes = Math.floor((rounded % 3600) / 60);
  const remainingSeconds = rounded % 60;
  return [hours, minutes, remainingSeconds]
    .map((value) => String(value).padStart(2, "0"))
    .join(":");
}

function formatCoordinate(value: number): string {
  return Number(value.toFixed(2)).toString();
}
