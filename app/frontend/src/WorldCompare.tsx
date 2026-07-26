import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { ExploreWorldState } from "./ExploreStatePersistence";
import {
  ExploreContextContent,
  ExploreInspector,
  ExploreSelectedEvidence,
  IntegratedExploreWorkspace,
} from "./IntegratedExploreWorkspace";
import { NativeSlicePositionControl } from "./NativeSlicePositionControl";
import {
  CompareControlGroup,
  type CompareSelectedEvidence,
  type TerrainScale,
  WorldCompareSideVisual,
} from "./WorldCompareAdapters";
import {
  mapCamera,
  nearestCompareTime,
  timeIndexForSeconds,
  validateWorldCompareDescriptor,
  WORLD_COMPARE_ADAPTERS,
} from "./WorldCompare.logic";
import {
  isMountainState,
  isSupercellsState,
  isTradeState,
  type CompareDifference,
  type CompareLinkModes,
  type ComparePerformanceSample,
  type ComparePerformanceSummary,
  type CompareSide,
  type CompareSimulationDescriptor,
  type CompareWorldSlug,
  type WorldCompareDescriptor,
} from "./WorldCompare.types";

import "./WorldCompare.css";

type WorldCompareProps = {
  worldSlug: CompareWorldSlug;
  initialLeftSimulationId?: string | null;
  initialRightSimulationId?: string | null;
  resumeExistingState?: boolean;
  onBack: () => void;
  onOpenSimulation: (simulationId: string) => void;
};

type SideStates = Record<CompareSide, ExploreWorldState>;
type SideStatus = Record<CompareSide, "loading" | "ready" | "error">;
type SideEvidence = Record<CompareSide, CompareSelectedEvidence | null>;
type SideScales = Record<CompareSide, TerrainScale | null>;
type PlaybackTarget = "linked" | CompareSide | null;

const INDEPENDENT_LINKS: CompareLinkModes = {
  time: false,
  view: false,
  plane: false,
  camera: false,
  selection: false,
};

export function WorldCompare({
  worldSlug,
  initialLeftSimulationId = null,
  initialRightSimulationId = null,
  resumeExistingState = false,
  onBack,
  onOpenSimulation,
}: WorldCompareProps) {
  const [descriptor, setDescriptor] = useState<WorldCompareDescriptor | null>(null);
  const [descriptorLoading, setDescriptorLoading] = useState(true);
  const [descriptorError, setDescriptorError] = useState<string | null>(null);
  const [phase, setPhase] = useState<"review" | "workspace">("review");
  const [states, setStates] = useState<SideStates | null>(null);
  const [links, setLinks] = useState<CompareLinkModes>(INDEPENDENT_LINKS);
  const [mappingNotices, setMappingNotices] = useState<string[]>([]);
  const [sideStatus, setSideStatus] = useState<SideStatus>({
    left: "loading",
    right: "loading",
  });
  const [evidence, setEvidence] = useState<SideEvidence>({ left: null, right: null });
  const [sideScales, setSideScales] = useState<SideScales>({ left: null, right: null });
  const [contextCollapsed, setContextCollapsed] = useState(true);
  const [playbackTarget, setPlaybackTarget] = useState<PlaybackTarget>(null);
  const [performance, setPerformance] = useState<ComparePerformanceSummary>({
    first_useful_dual_view_ms: null,
    cache_entries: { left: 0, right: 0 },
    estimated_cached_payload_bytes: { left: 0, right: 0 },
    samples: [],
  });
  const workspaceStartedAt = useRef<number | null>(null);

  const loadDescriptor = useCallback(
    async (leftId?: string | null, rightId?: string | null) => {
      setDescriptorLoading(true);
      setDescriptorError(null);
      const search = new URLSearchParams();
      if (leftId) search.set("left_simulation_id", leftId);
      if (rightId) search.set("right_simulation_id", rightId);
      try {
        const response = await fetch(
          `/api/worlds/${worldSlug}/compare${search.size ? `?${search}` : ""}`,
        );
        if (!response.ok) {
          throw new Error(await responseMessage(response, "World Compare could not be loaded."));
        }
        const payload = validateWorldCompareDescriptor(await response.json());
        setDescriptor(payload);
        setPhase("review");
        setStates(null);
        setPlaybackTarget(null);
        setMappingNotices([]);
      } catch (caught) {
        setDescriptor(null);
        setDescriptorError(
          caught instanceof Error ? caught.message : "World Compare could not be loaded.",
        );
      } finally {
        setDescriptorLoading(false);
      }
    },
    [worldSlug],
  );

  useEffect(() => {
    void loadDescriptor(initialLeftSimulationId, initialRightSimulationId);
  }, [initialLeftSimulationId, initialRightSimulationId, loadDescriptor]);

  const leftSimulation = descriptor
    ? selectedSimulation(descriptor, descriptor.selected_left_simulation_id)
    : null;
  const rightSimulation = descriptor
    ? selectedSimulation(descriptor, descriptor.selected_right_simulation_id)
    : null;
  const adapter = descriptor ? WORLD_COMPARE_ADAPTERS[descriptor.world_id] : null;

  const startWorkspace = useCallback(async () => {
    if (!descriptor || !leftSimulation || !rightSimulation || !descriptor.compatibility) return;
    const [leftState, rightState] = await Promise.all([
      initialCompareState(leftSimulation, resumeExistingState),
      initialCompareState(rightSimulation, resumeExistingState),
    ]);
    workspaceStartedAt.current = window.performance.now();
    setPerformance({
      first_useful_dual_view_ms: null,
      cache_entries: { left: 0, right: 0 },
      estimated_cached_payload_bytes: { left: 0, right: 0 },
      samples: [],
    });
    setStates({ left: leftState, right: rightState });
    setLinks(INDEPENDENT_LINKS);
    setMappingNotices([]);
    setPhase("workspace");
    setSideStatus({ left: "loading", right: "loading" });
  }, [descriptor, leftSimulation, resumeExistingState, rightSimulation]);

  const handleFrameState = useCallback(
    (side: CompareSide, status: "loading" | "ready" | "error") => {
      setSideStatus((current) => ({ ...current, [side]: status }));
      if (status === "error") {
        setPlaybackTarget((current) => (current === "linked" || current === side ? null : current));
      }
    },
    [],
  );

  useEffect(() => {
    if (
      phase !== "workspace" ||
      performance.first_useful_dual_view_ms !== null ||
      sideStatus.left !== "ready" ||
      sideStatus.right !== "ready" ||
      workspaceStartedAt.current === null
    ) {
      return;
    }
    const elapsed = window.performance.now() - workspaceStartedAt.current;
    setPerformance((current) => ({ ...current, first_useful_dual_view_ms: elapsed }));
  }, [performance.first_useful_dual_view_ms, phase, sideStatus]);

  const handlePerformance = useCallback((sample: ComparePerformanceSample) => {
    setPerformance((current) => {
      const samples = [...current.samples, sample].slice(-30);
      const uniqueBySide = (side: CompareSide) => {
        const values = new Map<string, number>();
        samples
          .filter((item) => item.side === side)
          .forEach((item) => {
            values.delete(item.key);
            values.set(item.key, item.payload_bytes);
            while (values.size > 6) {
              const oldest = values.keys().next().value;
              if (typeof oldest !== "string") break;
              values.delete(oldest);
            }
          });
        return values;
      };
      const left = uniqueBySide("left");
      const right = uniqueBySide("right");
      const next = {
        ...current,
        samples,
        cache_entries: { left: left.size, right: right.size },
        estimated_cached_payload_bytes: {
          left: [...left.values()].reduce((sum, value) => sum + value, 0),
          right: [...right.values()].reduce((sum, value) => sum + value, 0),
        },
      };
      (
        window as typeof window & {
          __CLOUD_CHAMBER_COMPARE_METRICS__?: ComparePerformanceSummary;
        }
      ).__CLOUD_CHAMBER_COMPARE_METRICS__ = next;
      return next;
    });
  }, []);

  const updateSideState = useCallback(
    (side: CompareSide, nextState: ExploreWorldState) => {
      if (!descriptor) return;
      setStates((current) => {
        if (!current) return current;
        const targetSide = otherSide(side);
        const synchronized = synchronizeState(
          descriptor,
          side,
          nextState,
          current[targetSide],
          links,
        );
        setMappingNotices(synchronized.notices);
        return {
          ...current,
          [side]: nextState,
          [targetSide]: synchronized.state,
        };
      });
    },
    [descriptor, links],
  );

  const applyAlignedPreset = useCallback(() => {
    if (!descriptor || !states) return;
    const nextLinks = alignedLinks(descriptor);
    const synchronized = synchronizeState(descriptor, "left", states.left, states.right, nextLinks);
    setLinks(nextLinks);
    setStates({ left: states.left, right: synchronized.state });
    setMappingNotices(synchronized.notices);
  }, [descriptor, states]);

  const applyIndependentPreset = useCallback(() => {
    setLinks(INDEPENDENT_LINKS);
    setMappingNotices([]);
    setPlaybackTarget(null);
  }, []);

  const toggleLink = useCallback(
    (key: keyof CompareLinkModes) => {
      if (!descriptor || !states) return;
      const nextLinks = { ...links, [key]: !links[key] };
      setLinks(nextLinks);
      if (nextLinks[key]) {
        const synchronized = synchronizeState(
          descriptor,
          "left",
          states.left,
          states.right,
          nextLinks,
        );
        setStates({ left: states.left, right: synchronized.state });
        setMappingNotices(synchronized.notices);
      }
      if (key === "time" && !nextLinks.time) setPlaybackTarget(null);
    },
    [descriptor, links, states],
  );

  const stepSide = useCallback(
    (side: CompareSide, offset: number) => {
      if (!descriptor || !states) return false;
      const simulation = side === "left" ? leftSimulation : rightSimulation;
      if (!simulation) return false;
      const current = states[side];
      const index = timeIndexForSeconds(simulation, current.model_time_seconds);
      const nextIndex = Math.min(
        simulation.time.times_seconds.length - 1,
        Math.max(0, index + offset),
      );
      if (nextIndex === index) return false;
      updateSideState(side, {
        ...current,
        model_time_seconds: simulation.time.times_seconds[nextIndex],
        selected_point: null,
      });
      return true;
    },
    [descriptor, leftSimulation, rightSimulation, states, updateSideState],
  );

  useEffect(() => {
    if (!playbackTarget || !states) return;
    const side = playbackTarget === "right" ? "right" : "left";
    const speed = Math.max(0.25, states[side].playback_speed);
    const timer = window.setInterval(() => {
      if (!stepSide(side, 1)) setPlaybackTarget(null);
    }, 900 / speed);
    return () => window.clearInterval(timer);
  }, [playbackTarget, states, stepSide]);

  const commonMountainScale = useMemo(() => {
    if (
      descriptor?.world_id !== "mountain_waves" ||
      !links.view ||
      !sideScales.left ||
      !sideScales.right ||
      sideScales.left.scale_id !== sideScales.right.scale_id
    ) {
      return null;
    }
    return combinedMountainScale(sideScales.left, sideScales.right);
  }, [descriptor?.world_id, links.view, sideScales]);

  const handleScale = useCallback((side: CompareSide, scale: TerrainScale | null) => {
    setSideScales((current) => (current[side] === scale ? current : { ...current, [side]: scale }));
  }, []);

  const handleEvidence = useCallback((side: CompareSide, item: CompareSelectedEvidence | null) => {
    setEvidence((current) =>
      evidenceSignature(current[side]) === evidenceSignature(item)
        ? current
        : { ...current, [side]: item },
    );
    if (item) setContextCollapsed(false);
  }, []);

  if (descriptorLoading) {
    return <CompareStatus title="Loading Compare" body="Reading bounded World metadata..." />;
  }
  if (!descriptor || descriptorError) {
    return (
      <CompareStatus
        title="Compare is unavailable"
        body={descriptorError ?? "World Compare metadata is unavailable."}
        actionLabel="Retry"
        onAction={() => void loadDescriptor(initialLeftSimulationId, initialRightSimulationId)}
      />
    );
  }
  if (descriptor.no_second_simulation_message || !rightSimulation) {
    return (
      <IntegratedExploreWorkspace
        worldName={descriptor.display_name}
        simulationName="Compare"
        onBack={onBack}
      >
        <section className="compare-empty-state" aria-label="No second Simulation">
          <p className="eyebrow">Compare</p>
          <h3>Choose two distinct Simulations</h3>
          <p>{descriptor.no_second_simulation_message}</p>
          <p>The existing reference remains available in Explore and is not duplicated.</p>
          {leftSimulation && (
            <button type="button" onClick={() => onOpenSimulation(leftSimulation.simulation_id)}>
              Open {leftSimulation.display_name}
            </button>
          )}
        </section>
      </IntegratedExploreWorkspace>
    );
  }
  if (!leftSimulation || !adapter) {
    return (
      <CompareStatus title="Compare is unavailable" body="Simulation identity is incomplete." />
    );
  }

  if (phase === "review" || !states) {
    return (
      <IntegratedExploreWorkspace
        worldName={descriptor.display_name}
        simulationName="Compare"
        onBack={onBack}
      >
        <ComparePairReview
          descriptor={descriptor}
          left={leftSimulation}
          right={rightSimulation}
          onPairChange={(leftId, rightId) => void loadDescriptor(leftId, rightId)}
          onStart={() => void startWorkspace()}
        />
      </IntegratedExploreWorkspace>
    );
  }

  return (
    <IntegratedExploreWorkspace
      worldName={descriptor.display_name}
      simulationName={`${leftSimulation.display_name} and ${rightSimulation.display_name}`}
      onBack={onBack}
      headerActions={
        <button type="button" className="secondary-button" onClick={() => setPhase("review")}>
          Change pair
        </button>
      }
    >
      <section className="world-compare-shell" aria-label={`${descriptor.display_name} Compare`}>
        <CompareToolbar
          descriptor={descriptor}
          links={links}
          onAligned={applyAlignedPreset}
          onIndependent={applyIndependentPreset}
          onToggleLink={toggleLink}
        />
        {mappingNotices.length > 0 && (
          <div className="compare-mapping-notices" role="status">
            {mappingNotices.map((notice) => (
              <span key={notice}>{notice}</span>
            ))}
          </div>
        )}
        <div className="world-compare-workspace-grid">
          <div className="compare-side-pair">
            {(["left", "right"] as CompareSide[]).map((side) => {
              const simulation = side === "left" ? leftSimulation : rightSimulation;
              return (
                <CompareSidePanel
                  key={side}
                  side={side}
                  simulation={simulation}
                  state={states[side]}
                  descriptor={descriptor}
                  onStateChange={(state) => updateSideState(side, state)}
                  onOpen={() => onOpenSimulation(simulation.simulation_id)}
                  onFrameState={handleFrameState}
                  onPerformance={handlePerformance}
                  commonMountainScale={commonMountainScale}
                  onMountainScale={handleScale}
                  onEvidence={handleEvidence}
                />
              );
            })}
          </div>
          <ExploreInspector collapsed={contextCollapsed} onCollapsedChange={setContextCollapsed}>
            <CompareContext
              descriptor={descriptor}
              left={leftSimulation}
              right={rightSimulation}
              evidence={evidence}
              onClear={(side) => {
                updateSideState(side, { ...states[side], selected_point: null });
                setEvidence((current) => ({ ...current, [side]: null }));
              }}
            />
          </ExploreInspector>
        </div>
        <CompareTimeline
          descriptor={descriptor}
          states={states}
          links={links}
          playbackTarget={playbackTarget}
          onPlaybackTarget={setPlaybackTarget}
          onStateChange={updateSideState}
          onStep={stepSide}
        />
        <CompareTechnicalDetails performance={performance} descriptor={descriptor} />
      </section>
    </IntegratedExploreWorkspace>
  );
}

function ComparePairReview({
  descriptor,
  left,
  right,
  onPairChange,
  onStart,
}: {
  descriptor: WorldCompareDescriptor;
  left: CompareSimulationDescriptor;
  right: CompareSimulationDescriptor;
  onPairChange: (leftId: string, rightId: string) => void;
  onStart: () => void;
}) {
  const compatibility = descriptor.compatibility;
  return (
    <section className="compare-pair-review" aria-labelledby="compare-review-title">
      <header>
        <p className="eyebrow">Compare setup</p>
        <h3 id="compare-review-title">Review the two Simulations before loading frames</h3>
        <p>
          Compare is transient. It does not create a Saved Comparison or change either Simulation.
        </p>
      </header>
      <div className="compare-pair-selectors">
        <SimulationSelector
          label="Left Simulation"
          value={left.simulation_id}
          simulations={descriptor.simulations}
          exclude={right.simulation_id}
          onChange={(value) => onPairChange(value, right.simulation_id)}
        />
        <button
          type="button"
          className="compare-swap-button"
          aria-label="Swap left and right Simulations"
          title="Swap Simulations"
          onClick={() => onPairChange(right.simulation_id, left.simulation_id)}
        >
          ⇄
        </button>
        <SimulationSelector
          label="Right Simulation"
          value={right.simulation_id}
          simulations={descriptor.simulations}
          exclude={left.simulation_id}
          onChange={(value) => onPairChange(left.simulation_id, value)}
        />
      </div>
      {compatibility && (
        <section className="compare-relationship-summary">
          <div>
            <strong>{compatibility.relationship}</strong>
            <p>{compatibility.controlled_pair_message}</p>
          </div>
          <span className={compatibility.controlled_pair ? "state-chip" : "compare-caveat-chip"}>
            {compatibility.controlled_pair ? "Controlled pair" : "Structural comparison"}
          </span>
        </section>
      )}
      <div className="compare-review-columns">
        <SimulationFacts simulation={left} />
        <SimulationFacts simulation={right} />
      </div>
      <DifferenceTable
        differences={descriptor.material_differences}
        leftLabel={left.display_name}
        rightLabel={right.display_name}
      />
      {compatibility && (
        <section className="compare-compatibility-summary">
          <h4>Coordination available</h4>
          <dl>
            <div>
              <dt>Modeled time</dt>
              <dd>
                {compatibility.exact_time_link_available
                  ? "Exact saved seconds; nearest is labeled when requested"
                  : "Independent only"}
              </dd>
            </div>
            <div>
              <dt>Shared views</dt>
              <dd>{compatibility.shared_view_ids.join(", ") || "None"}</dd>
            </div>
            <div>
              <dt>Physical slice plane</dt>
              <dd>
                {compatibility.physical_plane_link_available ? "Available" : "Not applicable"}
              </dd>
            </div>
            <div>
              <dt>Camera</dt>
              <dd>
                {compatibility.camera_link_available
                  ? "Normalized domain mapping"
                  : "Independent native 2-D framing"}
              </dd>
            </div>
          </dl>
          {compatibility.blockers.map((blocker) => (
            <p role="alert" key={blocker}>
              {blocker}
            </p>
          ))}
        </section>
      )}
      <div className="compare-review-actions">
        <button
          type="button"
          disabled={!compatibility || compatibility.blockers.length > 0}
          onClick={onStart}
        >
          Open dual view
        </button>
      </div>
    </section>
  );
}

function SimulationSelector({
  label,
  value,
  simulations,
  exclude,
  onChange,
}: {
  label: string;
  value: string;
  simulations: CompareSimulationDescriptor[];
  exclude: string;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.currentTarget.value)}>
        {simulations.map((simulation) => (
          <option
            key={simulation.simulation_id}
            value={simulation.simulation_id}
            disabled={simulation.simulation_id === exclude || !simulation.inspectable}
          >
            {simulation.display_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function SimulationFacts({ simulation }: { simulation: CompareSimulationDescriptor }) {
  return (
    <article className="compare-simulation-facts">
      <p className="eyebrow">{simulation.role.replaceAll("_", " ")}</p>
      <h4>{simulation.display_name}</h4>
      <dl>
        <div>
          <dt>Lineage</dt>
          <dd>{lineageLabel(simulation)}</dd>
        </div>
        <div>
          <dt>Domain / grid</dt>
          <dd>
            {simulation.grid.nx} × {simulation.grid.ny} × {simulation.grid.nz} ·{" "}
            {formatSpacing(simulation.grid)}
          </dd>
        </div>
        <div>
          <dt>Retained output</dt>
          <dd>
            {formatSeconds(simulation.time.end_seconds)} · every{" "}
            {formatSeconds(simulation.time.cadence_seconds)} ·{" "}
            {simulation.time.saved_output_count.toLocaleString()} frames
          </dd>
        </div>
        <div>
          <dt>Available science</dt>
          <dd>{simulation.available_view_ids.map(viewDisplayName).join(", ")}</dd>
        </div>
      </dl>
    </article>
  );
}

function DifferenceTable({
  differences,
  leftLabel,
  rightLabel,
}: {
  differences: CompareDifference[];
  leftLabel: string;
  rightLabel: string;
}) {
  return (
    <section className="compare-difference-preview" aria-labelledby="material-differences-title">
      <h4 id="material-differences-title">Material configuration differences</h4>
      {differences.length === 0 ? (
        <p>No material difference is declared in retained World metadata.</p>
      ) : (
        <div className="compare-difference-table" role="table">
          <div role="row" className="compare-difference-header">
            <span role="columnheader">Setting</span>
            <span role="columnheader">{leftLabel}</span>
            <span role="columnheader">{rightLabel}</span>
          </div>
          {differences.map((difference) => (
            <div role="row" key={difference.path}>
              <strong role="cell">{difference.label}</strong>
              <span role="cell">{formatDifferenceValue(difference, "left")}</span>
              <span role="cell">{formatDifferenceValue(difference, "right")}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function CompareToolbar({
  descriptor,
  links,
  onAligned,
  onIndependent,
  onToggleLink,
}: {
  descriptor: WorldCompareDescriptor;
  links: CompareLinkModes;
  onAligned: () => void;
  onIndependent: () => void;
  onToggleLink: (key: keyof CompareLinkModes) => void;
}) {
  const compatibility = descriptor.compatibility!;
  const controls: Array<{
    key: keyof CompareLinkModes;
    label: string;
    available: boolean;
    title?: string;
  }> = [
    { key: "time", label: "Time", available: compatibility.nearest_time_link_available },
    { key: "view", label: "Field / Lens", available: compatibility.shared_view_ids.length > 0 },
    {
      key: "plane",
      label: "Slice plane",
      available: compatibility.physical_plane_link_available,
      title: compatibility.physical_plane_link_available
        ? undefined
        : "This pair has no compatible physical slice-plane control.",
    },
    {
      key: "camera",
      label: "Camera",
      available: compatibility.camera_link_available,
      title: compatibility.camera_link_available
        ? undefined
        : "Native 2-D Mountain Waves framing is not a 3-D camera.",
    },
    { key: "selection", label: "Selection", available: compatibility.selection_link_available },
  ];
  const allAvailableLinked = controls.every((item) => !item.available || links[item.key]);
  const allIndependent = Object.values(links).every((value) => !value);
  return (
    <section className="compare-toolbar" aria-label="Compare coordination">
      <div className="compare-presets">
        <span>Coordination</span>
        <div className="segmented-control">
          <button
            type="button"
            className={allAvailableLinked ? "active-control" : ""}
            onClick={onAligned}
          >
            Aligned
          </button>
          <button
            type="button"
            className={allIndependent ? "active-control" : ""}
            onClick={onIndependent}
          >
            Independent
          </button>
        </div>
      </div>
      <div className="compare-link-controls">
        {controls.map((item) => (
          <label key={item.key} title={item.title}>
            <input
              type="checkbox"
              checked={links[item.key]}
              disabled={!item.available}
              onChange={() => onToggleLink(item.key)}
            />
            {item.label}
          </label>
        ))}
      </div>
    </section>
  );
}

function CompareSidePanel({
  side,
  simulation,
  state,
  descriptor,
  onStateChange,
  onOpen,
  onFrameState,
  onPerformance,
  commonMountainScale,
  onMountainScale,
  onEvidence,
}: {
  side: CompareSide;
  simulation: CompareSimulationDescriptor;
  state: ExploreWorldState;
  descriptor: WorldCompareDescriptor;
  onStateChange: (state: ExploreWorldState) => void;
  onOpen: () => void;
  onFrameState: (side: CompareSide, status: "loading" | "ready" | "error") => void;
  onPerformance: (sample: ComparePerformanceSample) => void;
  commonMountainScale: TerrainScale | null;
  onMountainScale: (side: CompareSide, scale: TerrainScale | null) => void;
  onEvidence: (side: CompareSide, evidence: CompareSelectedEvidence | null) => void;
}) {
  const adapter = WORLD_COMPARE_ADAPTERS[descriptor.world_id];
  const viewOptions = adapter.viewOptions(simulation);
  const currentView = adapter.viewId(state);
  const fieldOptions = simulation.available_field_ids;
  return (
    <article
      className="compare-side-panel"
      aria-label={`${simulation.display_name} comparison side`}
    >
      <header className="compare-side-header">
        <div>
          <p className="eyebrow">{side === "left" ? "Left Simulation" : "Right Simulation"}</p>
          <h3>{simulation.display_name}</h3>
          <p>
            {formatSeconds(state.model_time_seconds)} · {viewDisplayName(currentView)}
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={onOpen}>
          Open in Explore
        </button>
      </header>
      <div className="compare-side-controls">
        <CompareControlGroup label={adapter.viewLabel}>
          <div className="segmented-control">
            {viewOptions.map((option) => (
              <button
                type="button"
                key={option.id}
                className={currentView === option.id ? "active-control" : ""}
                onClick={() => onStateChange(adapter.setView(state, option.id))}
              >
                {option.label}
              </button>
            ))}
          </div>
        </CompareControlGroup>
        {currentView === "field" && (
          <CompareControlGroup label="Field">
            <select
              aria-label={`${simulation.display_name} Field`}
              value={adapter.fieldId(state) ?? fieldOptions[0]}
              onChange={(event) =>
                onStateChange(adapter.setField(state, event.currentTarget.value))
              }
            >
              {fieldOptions.map((field) => (
                <option key={field} value={field}>
                  {fieldDisplayName(field)}
                </option>
              ))}
            </select>
          </CompareControlGroup>
        )}
        <WorldSpecificControls
          simulation={simulation}
          state={state}
          onStateChange={onStateChange}
        />
      </div>
      <WorldCompareSideVisual
        side={side}
        simulation={simulation}
        state={state}
        onStateChange={onStateChange}
        onFrameState={onFrameState}
        onPerformance={onPerformance}
        commonMountainScale={commonMountainScale}
        onMountainScale={onMountainScale}
        onEvidence={onEvidence}
      />
    </article>
  );
}

function WorldSpecificControls({
  simulation,
  state,
  onStateChange,
}: {
  simulation: CompareSimulationDescriptor;
  state: ExploreWorldState;
  onStateChange: (state: ExploreWorldState) => void;
}) {
  if (isTradeState(state) && state.view_id === "field") {
    return (
      <>
        <label>
          <span>Cloud opacity</span>
          <input
            type="range"
            min={0.15}
            max={1}
            step={0.05}
            value={state.layer_opacity}
            onChange={(event) =>
              onStateChange({ ...state, layer_opacity: Number(event.currentTarget.value) })
            }
          />
        </label>
        <label>
          <span>Point size</span>
          <input
            type="range"
            min={4}
            max={18}
            step={1}
            value={state.point_size_px}
            onChange={(event) =>
              onStateChange({ ...state, point_size_px: Number(event.currentTarget.value) })
            }
          />
        </label>
      </>
    );
  }
  if (isSupercellsState(state)) {
    const planeValues = supercellPlaneCoordinates(simulation, state.evidence_view);
    const positionIndex = nearestNumberIndex(planeValues, state.plane_coordinate_km);
    const overlayOptions = supercellOverlayOptions(state.lens_id, state.evidence_view);
    return (
      <>
        <CompareControlGroup label="Viewport">
          <div className="segmented-control">
            <button
              type="button"
              className={state.viewport_id === "storm" ? "active-control" : ""}
              onClick={() => onStateChange({ ...state, viewport_id: "storm" })}
            >
              Storm region
            </button>
            <button
              type="button"
              className={state.viewport_id === "full" ? "active-control" : ""}
              onClick={() => onStateChange({ ...state, viewport_id: "full" })}
            >
              Full domain
            </button>
          </div>
        </CompareControlGroup>
        <CompareControlGroup label="Slice position">
          <NativeSlicePositionControl
            id={`compare-${simulation.simulation_id}-supercell-plane`}
            ariaLabel={`${simulation.display_name} slice position`}
            plane={
              state.evidence_view === "plan"
                ? "horizontal"
                : state.evidence_view === "xz"
                  ? "vertical_x"
                  : "vertical_y"
            }
            positionIndex={positionIndex}
            positionCount={planeValues.length}
            positionLabel={`${supercellPlaneAxis(state.evidence_view)} ${(
              planeValues[positionIndex] ?? 0
            ).toFixed(2)} km`}
            indexLabel={`native index ${positionIndex}`}
            onPositionChange={(nextIndex) => {
              const coordinate = planeValues[nextIndex];
              if (!Number.isFinite(coordinate)) return;
              const selected = state.selected_point ?? { x_km: 0, y_km: 0, z_km: 0 };
              onStateChange({
                ...state,
                plane_coordinate_km: coordinate,
                selected_point:
                  state.evidence_view === "plan"
                    ? { ...selected, z_km: coordinate }
                    : state.evidence_view === "xz"
                      ? { ...selected, y_km: coordinate }
                      : { ...selected, x_km: coordinate },
              });
            }}
            compact
          />
        </CompareControlGroup>
        <CompareControlGroup label="Evidence overlays">
          <div className="compare-overlay-controls">
            {overlayOptions.map((option) => (
              <label key={option.key}>
                <input
                  type="checkbox"
                  checked={state.overlays[option.key]}
                  onChange={(event) =>
                    onStateChange({
                      ...state,
                      overlays: {
                        ...state.overlays,
                        [option.key]: event.currentTarget.checked,
                      },
                    })
                  }
                />
                {option.label}
              </label>
            ))}
          </div>
        </CompareControlGroup>
        <CompareControlGroup label="3-D rendering">
          <div className="compare-cloud-render-controls">
            <label>
              <span>Opacity</span>
              <input
                type="range"
                aria-label={`${simulation.display_name} scene opacity`}
                min={0.25}
                max={1.25}
                step={0.05}
                value={state.scene_opacity}
                onChange={(event) =>
                  onStateChange({
                    ...state,
                    scene_opacity: Number(event.currentTarget.value),
                  })
                }
              />
              <output>{state.scene_opacity.toFixed(2)}x</output>
            </label>
            <label>
              <span>Point size</span>
              <input
                type="range"
                aria-label={`${simulation.display_name} scene point size`}
                min={0.5}
                max={1.8}
                step={0.1}
                value={state.scene_point_size}
                onChange={(event) =>
                  onStateChange({
                    ...state,
                    scene_point_size: Number(event.currentTarget.value),
                  })
                }
              />
              <output>{state.scene_point_size.toFixed(1)}x</output>
            </label>
          </div>
        </CompareControlGroup>
      </>
    );
  }
  if (!isMountainState(state)) return null;
  return (
    <>
      <CompareControlGroup label="Viewport">
        <div className="segmented-control">
          <button
            type="button"
            disabled={simulation.simulation_id === "mountain_waves_dry_ridge"}
            className={state.viewport_id === "focus" ? "active-control" : ""}
            onClick={() => onStateChange({ ...state, viewport_id: "focus" })}
          >
            Focus region
          </button>
          <button
            type="button"
            className={state.viewport_id === "full" ? "active-control" : ""}
            onClick={() => onStateChange({ ...state, viewport_id: "full" })}
          >
            Full domain
          </button>
        </div>
      </CompareControlGroup>
      <CompareControlGroup label="Geometry">
        <div className="segmented-control">
          <button
            type="button"
            className={state.geometry_id === "expanded" ? "active-control" : ""}
            onClick={() => onStateChange({ ...state, geometry_id: "expanded" })}
          >
            Expanded height
          </button>
          <button
            type="button"
            className={state.geometry_id === "physical" ? "active-control" : ""}
            onClick={() => onStateChange({ ...state, geometry_id: "physical" })}
          >
            True physical scale
          </button>
        </div>
      </CompareControlGroup>
      {state.view_id !== "field" && (
        <CompareControlGroup label="Overlays">
          <div className="compare-overlay-controls">
            <label>
              <input
                type="checkbox"
                checked={state.overlays.horizontal_wind}
                onChange={(event) =>
                  onStateChange({
                    ...state,
                    overlays: { ...state.overlays, horizontal_wind: event.currentTarget.checked },
                  })
                }
              />
              Horizontal wind
            </label>
            <label>
              <input
                type="checkbox"
                checked={state.overlays.potential_temperature_contours}
                onChange={(event) =>
                  onStateChange({
                    ...state,
                    overlays: {
                      ...state.overlays,
                      potential_temperature_contours: event.currentTarget.checked,
                    },
                  })
                }
              />
              Potential temperature
            </label>
            {state.view_id === "wave_cloud" && (
              <>
                <label>
                  <input
                    type="checkbox"
                    checked={state.overlays.cloud_points}
                    onChange={(event) =>
                      onStateChange({
                        ...state,
                        overlays: { ...state.overlays, cloud_points: event.currentTarget.checked },
                      })
                    }
                  />
                  Cloud points
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={state.overlays.cloud_boundary}
                    onChange={(event) =>
                      onStateChange({
                        ...state,
                        overlays: {
                          ...state.overlays,
                          cloud_boundary: event.currentTarget.checked,
                        },
                      })
                    }
                  />
                  Cloud boundary
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={state.overlays.saturation_contour}
                    onChange={(event) =>
                      onStateChange({
                        ...state,
                        overlays: {
                          ...state.overlays,
                          saturation_contour: event.currentTarget.checked,
                        },
                      })
                    }
                  />
                  RH = 100%
                </label>
              </>
            )}
          </div>
        </CompareControlGroup>
      )}
      {state.view_id === "wave_cloud" && state.overlays.cloud_points && (
        <CompareControlGroup label="Cloud points">
          <div className="compare-cloud-render-controls">
            <label>
              <span>Opacity</span>
              <input
                type="range"
                aria-label={`${simulation.display_name} cloud opacity`}
                min={0.15}
                max={1}
                step={0.05}
                value={state.cloud_opacity}
                onChange={(event) =>
                  onStateChange({ ...state, cloud_opacity: Number(event.currentTarget.value) })
                }
              />
              <output>{state.cloud_opacity.toFixed(2)}</output>
            </label>
            <label>
              <span>Point size</span>
              <input
                type="range"
                aria-label={`${simulation.display_name} cloud point size`}
                min={4}
                max={18}
                step={1}
                value={state.cloud_point_size_px}
                onChange={(event) =>
                  onStateChange({
                    ...state,
                    cloud_point_size_px: Number(event.currentTarget.value),
                  })
                }
              />
              <output>{state.cloud_point_size_px}px</output>
            </label>
          </div>
        </CompareControlGroup>
      )}
    </>
  );
}

function supercellPlaneAxis(view: "plan" | "xz" | "yz"): "x" | "y" | "z" {
  return view === "plan" ? "z" : view === "xz" ? "y" : "x";
}

function supercellPlaneCoordinates(
  simulation: CompareSimulationDescriptor,
  view: "plan" | "xz" | "yz",
): number[] {
  const axis = supercellPlaneAxis(view);
  const extent =
    axis === "x"
      ? simulation.grid.x_extent_km
      : axis === "y"
        ? (simulation.grid.y_extent_km ?? simulation.grid.x_extent_km)
        : simulation.grid.z_extent_km;
  const count =
    axis === "x" ? simulation.grid.nx : axis === "y" ? simulation.grid.ny : simulation.grid.nz;
  const spacing = (extent[1] - extent[0]) / count;
  return Array.from({ length: count }, (_, index) => extent[0] + (index + 0.5) * spacing);
}

function nearestNumberIndex(values: number[], target: number): number {
  return values.reduce(
    (nearest, value, index) =>
      Math.abs(value - target) < Math.abs(values[nearest] - target) ? index : nearest,
    0,
  );
}

function supercellOverlayOptions(
  lens: "rotating_updraft" | "cloud_precipitation" | "low_level_interactions",
  evidenceView: "plan" | "xz" | "yz",
): Array<{
  key:
    | "rotation"
    | "updraft_helicity"
    | "reflectivity"
    | "condensate"
    | "rain"
    | "wind"
    | "precipitating_condensate"
    | "vertical_motion";
  label: string;
}> {
  if (lens === "rotating_updraft") {
    return [
      { key: "condensate", label: "Cloud boundary" },
      { key: "rotation", label: "Rotation contour" },
      ...(evidenceView === "plan"
        ? [{ key: "updraft_helicity" as const, label: "2-5 km UH footprint" }]
        : []),
      { key: "reflectivity", label: "Reflectivity contour" },
    ];
  }
  if (lens === "cloud_precipitation") {
    return [
      { key: "vertical_motion", label: "Vertical-motion contours" },
      { key: "reflectivity", label: "Reflectivity contour" },
    ];
  }
  return [
    { key: "precipitating_condensate", label: "Current precipitation" },
    { key: "rain", label: "Accumulated rain" },
    { key: "wind", label: "Model-relative flow" },
    { key: "reflectivity", label: "Reflectivity contour" },
  ];
}

function CompareTimeline({
  descriptor,
  states,
  links,
  playbackTarget,
  onPlaybackTarget,
  onStateChange,
  onStep,
}: {
  descriptor: WorldCompareDescriptor;
  states: SideStates;
  links: CompareLinkModes;
  playbackTarget: PlaybackTarget;
  onPlaybackTarget: (target: PlaybackTarget) => void;
  onStateChange: (side: CompareSide, state: ExploreWorldState) => void;
  onStep: (side: CompareSide, offset: number) => boolean;
}) {
  return (
    <section className="compare-timeline" aria-label="Compare time controls">
      <header>
        <strong>Saved output time</strong>
        <span>
          {links.time
            ? "Linked by modeled seconds; nearest saved output is labeled."
            : "Each Simulation uses its own retained output history."}
        </span>
      </header>
      <div className="compare-timeline-rows">
        {(["left", "right"] as CompareSide[]).map((side) => {
          const simulation = selectedSimulation(
            descriptor,
            side === "left"
              ? descriptor.selected_left_simulation_id
              : descriptor.selected_right_simulation_id,
          )!;
          const state = states[side];
          const index = timeIndexForSeconds(simulation, state.model_time_seconds);
          const target = links.time ? "linked" : side;
          const playing = playbackTarget === target;
          return (
            <div className="compare-timeline-row" key={side}>
              <span>{simulation.display_name}</span>
              <button
                type="button"
                aria-label={`Previous ${simulation.display_name} output`}
                onClick={() => onStep(side, -1)}
              >
                ‹
              </button>
              <button
                type="button"
                aria-label={`${playing ? "Pause" : "Play"} ${simulation.display_name}`}
                onClick={() => onPlaybackTarget(playing ? null : target)}
              >
                <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
              </button>
              <button
                type="button"
                aria-label={`Next ${simulation.display_name} output`}
                onClick={() => onStep(side, 1)}
              >
                ›
              </button>
              <input
                type="range"
                aria-label={`${simulation.display_name} saved output time`}
                min={0}
                max={Math.max(0, simulation.time.times_seconds.length - 1)}
                step={1}
                value={index}
                onChange={(event) => {
                  const nextIndex = Number(event.currentTarget.value);
                  onStateChange(side, {
                    ...state,
                    model_time_seconds: simulation.time.times_seconds[nextIndex],
                    selected_point: null,
                  });
                }}
              />
              <strong>{formatSeconds(state.model_time_seconds)}</strong>
              <select
                aria-label={`${simulation.display_name} playback speed`}
                value={state.playback_speed}
                onChange={(event) =>
                  onStateChange(side, {
                    ...state,
                    playback_speed: Number(event.currentTarget.value),
                  })
                }
              >
                {[0.5, 1, 2, 4].map((speed) => (
                  <option key={speed} value={speed}>
                    {speed}x
                  </option>
                ))}
              </select>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function CompareContext({
  descriptor,
  left,
  right,
  evidence,
  onClear,
}: {
  descriptor: WorldCompareDescriptor;
  left: CompareSimulationDescriptor;
  right: CompareSimulationDescriptor;
  evidence: SideEvidence;
  onClear: (side: CompareSide) => void;
}) {
  const difference = selectedEvidenceDifference(evidence.left, evidence.right);
  return (
    <ExploreContextContent
      identity="Comparison"
      question="What is aligned, and what remains different?"
      explanation={
        <p>
          {descriptor.compatibility?.controlled_pair_message} Each side keeps its own native
          evidence and retained output time.
        </p>
      }
      selectedEvidence={
        evidence.left || evidence.right ? (
          <div className="compare-selected-evidence">
            {(["left", "right"] as CompareSide[]).map((side) => {
              const item = evidence[side];
              const simulation = side === "left" ? left : right;
              return item ? (
                <ExploreSelectedEvidence
                  key={side}
                  eyebrow={simulation.display_name}
                  title={item.title}
                  states={item.states}
                  metrics={item.metrics.map((metric) => ({
                    label: metric.label,
                    value: metric.value,
                  }))}
                  onClear={() => onClear(side)}
                />
              ) : (
                <section className="compare-selection-empty" key={side}>
                  <strong>{simulation.display_name}</strong>
                  <p>No point selected.</p>
                </section>
              );
            })}
            <section className="compare-evidence-difference" aria-label="Selected point difference">
              <strong>Difference summary</strong>
              <p>{difference}</p>
            </section>
          </div>
        ) : undefined
      }
      orientation={[
        { label: "Left", value: left.display_name },
        { label: "Right", value: right.display_name },
        {
          label: "Relationship",
          value: descriptor.compatibility?.relationship ?? "Unknown",
        },
        {
          label: "Time rule",
          value: "Exact modeled seconds or explicitly labeled nearest saved output",
        },
      ]}
      selectionPrompt={
        evidence.left || evidence.right
          ? undefined
          : "Select a cell in either scientific view to compare native or explicitly derived evidence."
      }
    />
  );
}

function CompareTechnicalDetails({
  performance,
  descriptor,
}: {
  performance: ComparePerformanceSummary;
  descriptor: WorldCompareDescriptor;
}) {
  const latestRequests = performance.samples.filter((sample) => !sample.cache_hit).slice(-2);
  return (
    <details className="compare-technical-details">
      <summary>Compare technical details</summary>
      <dl>
        <div>
          <dt>First useful dual view</dt>
          <dd>
            {performance.first_useful_dual_view_ms === null
              ? "Not measured yet"
              : `${Math.round(performance.first_useful_dual_view_ms).toLocaleString()} ms`}
          </dd>
        </div>
        <div>
          <dt>Bounded frame cache</dt>
          <dd>
            {performance.cache_entries.left} left / {performance.cache_entries.right} right · max 6
            per side
          </dd>
        </div>
        <div>
          <dt>Estimated serialized cache</dt>
          <dd>
            {formatBytes(performance.estimated_cached_payload_bytes.left)} left /{" "}
            {formatBytes(performance.estimated_cached_payload_bytes.right)} right
          </dd>
        </div>
        <div>
          <dt>Latest side requests</dt>
          <dd>
            {latestRequests.length
              ? latestRequests
                  .map(
                    (sample) =>
                      `${sample.side}: ${Math.round(sample.request_ms)} ms, ${formatBytes(
                        sample.payload_bytes,
                      )}`,
                  )
                  .join(" · ")
              : "No uncached frames requested yet"}
          </dd>
        </div>
        <div>
          <dt>Persistence</dt>
          <dd>{descriptor.persistence.replace("_", " ")}</dd>
        </div>
      </dl>
    </details>
  );
}

function CompareStatus({
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
    <section className="status-panel" role="status">
      <h2>{title}</h2>
      <p>{body}</p>
      {actionLabel && onAction && (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </section>
  );
}

function alignedLinks(descriptor: WorldCompareDescriptor): CompareLinkModes {
  const compatibility = descriptor.compatibility;
  if (!compatibility) return INDEPENDENT_LINKS;
  return {
    time: compatibility.nearest_time_link_available,
    view: compatibility.shared_view_ids.length > 0,
    plane: compatibility.physical_plane_link_available,
    camera: compatibility.camera_link_available,
    selection: compatibility.selection_link_available,
  };
}

function synchronizeState(
  descriptor: WorldCompareDescriptor,
  sourceSide: CompareSide,
  source: ExploreWorldState,
  target: ExploreWorldState,
  links: CompareLinkModes,
): { state: ExploreWorldState; notices: string[] } {
  const adapter = WORLD_COMPARE_ADAPTERS[descriptor.world_id];
  const targetSimulation = selectedSimulation(
    descriptor,
    sourceSide === "left"
      ? descriptor.selected_right_simulation_id
      : descriptor.selected_left_simulation_id,
  );
  const sourceSimulation = selectedSimulation(
    descriptor,
    sourceSide === "left"
      ? descriptor.selected_left_simulation_id
      : descriptor.selected_right_simulation_id,
  );
  if (!targetSimulation || !sourceSimulation || source.world_id !== target.world_id) {
    return { state: target, notices: [] };
  }
  const notices: string[] = [];
  let next = target;
  if (links.time) {
    const mapped = nearestCompareTime(
      targetSimulation,
      adapter.modelTime(source),
      descriptor.compatibility?.time_tolerance_seconds ?? 0,
    );
    if (mapped) {
      next = adapter.setModelTime(next, mapped.value);
      if (mapped.message) notices.push(`${targetSimulation.display_name}: ${mapped.message}`);
    } else {
      notices.push(
        `${targetSimulation.display_name}: no saved output is within the approved time tolerance.`,
      );
    }
  }
  if (links.view) {
    const sourceView = adapter.viewId(source);
    if (descriptor.compatibility?.shared_view_ids.includes(sourceView)) {
      next = adapter.setView(next, sourceView);
      const field = adapter.fieldId(source);
      if (field && descriptor.compatibility.shared_field_ids.includes(field)) {
        next = adapter.setField(next, field);
      }
    }
  }
  if (links.plane && isTradeState(source) && isTradeState(next)) {
    next = {
      ...next,
      active_slice_plane: source.active_slice_plane,
      slice_coordinate_km: source.slice_coordinate_km,
      slice_native_index: source.slice_native_index,
    };
  }
  if (links.plane && isSupercellsState(source) && isSupercellsState(next)) {
    next = {
      ...next,
      evidence_view: source.evidence_view,
      plane_coordinate_km: source.plane_coordinate_km,
    };
  }
  if (links.camera) {
    const preset = adapter.cameraPreset(source);
    if (preset) {
      const mapped = mapCamera(
        preset,
        adapter.cameraTransform(source),
        sourceSimulation,
        targetSimulation,
      );
      if (mapped) {
        next = adapter.setCamera(next, mapped.preset, mapped.transform);
        if (mapped.message) notices.push(mapped.message);
      }
    }
  }
  if (links.selection) {
    next = adapter.setSelectedPoint(next, adapter.selectedPoint(source));
  }
  return { state: next, notices: [...new Set(notices)] };
}

async function initialCompareState(
  simulation: CompareSimulationDescriptor,
  resumeExistingState: boolean,
): Promise<ExploreWorldState> {
  if (!resumeExistingState) return simulation.initial_state;
  try {
    const response = await fetch(
      `/api/worlds/${simulation.world_id}/simulations/${simulation.simulation_id}/explore-state`,
    );
    if (!response.ok) return simulation.initial_state;
    const payload = (await response.json()) as {
      library?: { last_active?: { state?: ExploreWorldState } | null };
    };
    const restored = payload.library?.last_active?.state;
    return restored?.world_id === simulation.world_id ? restored : simulation.initial_state;
  } catch {
    return simulation.initial_state;
  }
}

function selectedSimulation(
  descriptor: WorldCompareDescriptor,
  simulationId: string | null,
): CompareSimulationDescriptor | null {
  return (
    descriptor.simulations.find((simulation) => simulation.simulation_id === simulationId) ?? null
  );
}

function otherSide(side: CompareSide): CompareSide {
  return side === "left" ? "right" : "left";
}

function combinedMountainScale(left: TerrainScale, right: TerrainScale): TerrainScale {
  const limit = Math.max(
    Math.abs(left.minimum),
    Math.abs(left.maximum),
    Math.abs(right.minimum),
    Math.abs(right.maximum),
  );
  const fractions = [-0.8, -0.6, -0.4, -0.2, -0.1, 0.1, 0.2, 0.4, 0.6, 0.8];
  return {
    ...left,
    minimum: -limit,
    maximum: limit,
    selected_time_minimum: left.selected_time_minimum,
    selected_time_maximum: left.selected_time_maximum,
    breakpoints: fractions.map((fraction) => fraction * limit),
    scale_id: left.scale_id,
  };
}

function selectedEvidenceDifference(
  left: CompareSelectedEvidence | null,
  right: CompareSelectedEvidence | null,
): string {
  if (!left || !right) return "Select a point on both sides to calculate like-unit differences.";
  const differences: string[] = [];
  left.metrics.forEach((leftMetric) => {
    if (leftMetric.numericValue === undefined || !leftMetric.units) return;
    const rightMetric = right.metrics.find(
      (candidate) =>
        candidate.label === leftMetric.label &&
        candidate.units === leftMetric.units &&
        candidate.numericValue !== undefined,
    );
    if (!rightMetric || rightMetric.numericValue === undefined) return;
    const delta = rightMetric.numericValue - leftMetric.numericValue;
    differences.push(
      `${leftMetric.label}: ${formatSigned(delta)} ${leftMetric.units} (right minus left)`,
    );
  });
  return differences.length
    ? differences.join(" · ")
    : "The selected points do not expose directly comparable numeric evidence.";
}

function evidenceSignature(value: CompareSelectedEvidence | null): string {
  return value ? JSON.stringify(value) : "";
}

function lineageLabel(simulation: CompareSimulationDescriptor): string {
  if (simulation.parent_simulation_id) return `Child of ${simulation.parent_simulation_id}`;
  if (simulation.reference_simulation_id === simulation.simulation_id) return "Retained reference";
  if (simulation.reference_simulation_id) {
    return `Reference: ${simulation.reference_simulation_id}`;
  }
  if (simulation.lineage_state === "independent_built_in") return "Independent built-in";
  return simulation.lineage_state === "known" ? "Known" : simulation.lineage_state;
}

function formatSpacing(grid: CompareSimulationDescriptor["grid"]): string {
  if (grid.topology === "native_2d_xz") {
    return `${formatMeters(grid.dx_m)} x / ${formatMeters(grid.dz_m)} z · native 2-D x-z`;
  }
  return `${formatMeters(grid.dx_m)} × ${formatMeters(grid.dy_m)} × ${formatMeters(grid.dz_m)}`;
}

function formatMeters(value: number): string {
  return value >= 1_000 ? `${formatNumber(value / 1_000)} km` : `${formatNumber(value)} m`;
}

function formatDifferenceValue(difference: CompareDifference, side: "left" | "right"): string {
  const known = side === "left" ? difference.left_known : difference.right_known;
  if (!known) return "Unknown";
  const value = side === "left" ? difference.left_value : difference.right_value;
  if (difference.path === "controls.surface_moisture_flux_g_g_m_s" && typeof value === "number") {
    return `${(value * 1_000).toFixed(5)} g/kg m/s`;
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return `${value.toLocaleString()}${difference.units ? ` ${difference.units}` : ""}`;
    }
    return `${formatNumber(value)}${difference.units ? ` ${difference.units}` : ""}`;
  }
  return `${String(value)}${difference.units ? ` ${difference.units}` : ""}`;
}

function fieldDisplayName(value: string): string {
  const labels: Record<string, string> = {
    ql: "Cloud water",
    w: "Vertical velocity",
    theta_perturbation: "Potential-temperature perturbation",
    cloud_liquid: "Cloud liquid water",
    relative_humidity: "Relative humidity",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function viewDisplayName(value: string): string {
  const labels: Record<string, string> = {
    field: "Field",
    updraft_lens: "Updraft Lens",
    wave_structure: "Wave Structure Lens",
    wave_cloud: "Wave Cloud Lens",
    rotating_updraft: "Rotating Updraft",
    cloud_precipitation: "Cloud and Precipitation",
    low_level_interactions: "Low-Level Interactions",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function formatSeconds(value: number): string {
  return `${Math.round(value).toLocaleString()} s`;
}

function formatNumber(value: number): string {
  if (Math.abs(value) >= 1_000) return Math.round(value).toLocaleString();
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  if (Math.abs(value) >= 1) return value.toFixed(2);
  return value.toPrecision(3);
}

function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${formatNumber(value)}`;
}

function formatBytes(value: number): string {
  if (value < 1_024) return `${value} B`;
  if (value < 1_048_576) return `${(value / 1_024).toFixed(1)} KB`;
  return `${(value / 1_048_576).toFixed(1)} MB`;
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
