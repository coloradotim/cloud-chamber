import { useCallback, useEffect, useState } from "react";

import { LifecycleWorkspace, type LifecycleRecord } from "./LifecycleWorkspace";
import { MountainWavesVariationEditor } from "./MountainWavesVariationEditor";
import { SavedComparisonsCollection } from "./SavedComparisons";

export type MountainWavesDifference = {
  label: string;
  before: unknown;
  after: unknown;
  units?: string | null;
  level_index?: number;
};

export type MountainWavesSimulation = {
  simulation_id: string;
  display_name: string;
  role: "built_in" | "variation";
  world_id: "mountain_waves";
  run_id: string;
  case_id: string;
  parent_simulation_id: string | null;
  parent_run_id: string | null;
  reference_simulation_id: string;
  user_question: string | null;
  recipe_id?: string | null;
  recipe_contract_version?: string | null;
  relationship_classification?: string | null;
  legacy_contract?: boolean;
  parent_eligibility_reason?: string | null;
  state:
    | "available"
    | "packaged"
    | "queued"
    | "running"
    | "failed"
    | "canceled"
    | "unavailable"
    | "conflict";
  state_message: string;
  inspectable: boolean;
  can_create_variation: boolean;
  moist: boolean;
  moist_fields_available: boolean;
  purpose: string;
  configuration: Record<string, unknown> | null;
  scientific_design?: Record<string, unknown> | null;
  numerical_realization?: Record<string, unknown> | null;
  observation_plan?: Record<string, unknown> | null;
  differences: Record<string, MountainWavesDifference[]>;
  warnings: string[];
  caveats: string[];
  manifest_path: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type MountainWavesWorldDetail = {
  world_id: "mountain_waves";
  display_name: "Mountain Waves";
  short_description: string;
  availability_state: "available" | "partial" | "unavailable" | "conflict";
  availability_message: string;
  default_parent_simulation_id: string;
  simulations: MountainWavesSimulation[];
  activity: MountainWavesSimulation[];
  history: MountainWavesSimulation[];
  lab_summary: {
    active_run_count: number;
    packaged_run_count: number;
    completed_simulation_count: number;
    failed_run_count: number;
    total_variation_count: number;
  };
  caveats: string[];
};

type WorldSection =
  | "overview"
  | "simulations"
  | "saved_comparisons"
  | "activity"
  | "create"
  | "history";

export function MountainWavesWorld({
  onBackToWorlds,
  onExploreSimulation,
  onCompareSimulation,
  onOpenSavedComparison,
}: {
  onBackToWorlds: () => void;
  onExploreSimulation: (simulation: MountainWavesSimulation) => void;
  onCompareSimulation?: (
    simulation: MountainWavesSimulation,
    targetSimulationId: string | null,
  ) => void;
  onOpenSavedComparison: (savedComparisonId: string) => void;
}) {
  const [section, setSection] = useState<WorldSection>("overview");
  const [world, setWorld] = useState<MountainWavesWorldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [parentSimulationId, setParentSimulationId] = useState<string | null>(null);

  const loadWorld = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/worlds/mountain-waves");
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Mountain Waves is unavailable."));
      }
      const payload = validateMountainWavesWorld(await response.json());
      setWorld(payload);
      setParentSimulationId((current) => current ?? payload.default_parent_simulation_id);
    } catch (caught) {
      if (!quiet) setWorld(null);
      setError(caught instanceof Error ? caught.message : "Mountain Waves is unavailable.");
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorld();
  }, [loadWorld]);

  function openVariation(parentId: string) {
    setParentSimulationId(parentId);
    setSection("create");
  }

  if (loading) {
    return (
      <section className="world-shell" aria-label="Mountain Waves World">
        <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
        <section className="status-panel" role="status">
          Loading Mountain Waves...
        </section>
      </section>
    );
  }

  if (!world) {
    return (
      <section className="world-shell" aria-label="Mountain Waves World">
        <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
        <section className="world-load-failure" aria-label="Mountain Waves unavailable">
          <div>
            <h2>Mountain Waves could not be loaded</h2>
            <p role="alert">{error}</p>
            <p>The World remains available for retry without affecting other Cloud Worlds.</p>
          </div>
          <button type="button" onClick={() => void loadWorld()}>
            Retry Mountain Waves
          </button>
        </section>
      </section>
    );
  }

  return (
    <section className="world-shell" aria-label="Mountain Waves World">
      <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
      <header className="world-header">
        <div>
          <h2>{world.display_name}</h2>
          <p>{world.short_description}</p>
        </div>
      </header>

      <nav className="world-section-nav" aria-label="Mountain Waves sections">
        {(
          [
            "overview",
            "simulations",
            "saved_comparisons",
            "activity",
            "create",
            "history",
          ] as WorldSection[]
        ).map((item) => (
          <button
            key={item}
            type="button"
            className={section === item ? "active-control" : ""}
            onClick={() => setSection(item)}
          >
            {sectionLabel(item)}
          </button>
        ))}
      </nav>

      {section === "overview" && (
        <section className="world-section" aria-labelledby="mountain-waves-overview-title">
          <div className="world-section-heading">
            <div>
              <p className="eyebrow">Overview</p>
              <h3 id="mountain-waves-overview-title">Built-in Simulations</h3>
            </div>
          </div>
          {world.availability_state !== "available" && (
            <p className="world-availability-message">{world.availability_message}</p>
          )}
          <div className="world-overview-grid mountain-waves-overview-grid">
            {world.simulations
              .filter((simulation) => simulation.role === "built_in")
              .map((simulation) => (
                <MountainWavesSimulationCard
                  key={simulation.simulation_id}
                  simulation={simulation}
                  onExplore={onExploreSimulation}
                  onCreateVariation={openVariation}
                  onCompare={
                    onCompareSimulation
                      ? (candidate) =>
                          onCompareSimulation(
                            candidate,
                            mountainWavesCompareTarget(world.simulations, candidate),
                          )
                      : undefined
                  }
                />
              ))}
          </div>
          <p className="world-science-note">{world.caveats[0]}</p>
          <section className="world-lab-summary" aria-label="Create a Mountain Waves variation">
            <div>
              <p className="eyebrow">Experiment</p>
              <h3>Start a related Simulation</h3>
              <p>Use an eligible retained Simulation as the parent for a bounded variation.</p>
            </div>
            <button type="button" onClick={() => openVariation(world.default_parent_simulation_id)}>
              Create variation
            </button>
          </section>
        </section>
      )}

      {section === "simulations" && (
        <section className="world-section" aria-labelledby="mountain-waves-simulations-title">
          <div className="world-section-heading">
            <div>
              <p className="eyebrow">Simulations</p>
              <h3 id="mountain-waves-simulations-title">Retained Mountain Waves Simulations</h3>
            </div>
            <p>{world.simulations.filter((item) => item.inspectable).length} inspectable</p>
          </div>
          <div className="simulation-card-grid">
            {world.simulations.map((simulation) => (
              <MountainWavesSimulationCard
                key={simulation.simulation_id}
                simulation={simulation}
                onExplore={onExploreSimulation}
                onCreateVariation={openVariation}
                onCompare={
                  onCompareSimulation
                    ? (candidate) =>
                        onCompareSimulation(
                          candidate,
                          mountainWavesCompareTarget(world.simulations, candidate),
                        )
                    : undefined
                }
              />
            ))}
          </div>
        </section>
      )}

      {section === "saved_comparisons" && (
        <section className="world-section">
          <SavedComparisonsCollection worldSlug="mountain-waves" onOpen={onOpenSavedComparison} />
        </section>
      )}

      {(section === "activity" || section === "history") && (
        <section className="world-section">
          <LifecycleWorkspace
            ownerIds={["mountain_waves"]}
            view={section}
            showViewTabs={false}
            onExplore={(record) => {
              const simulation = simulationForLifecycleRecord(world, record);
              if (simulation) onExploreSimulation(simulation);
            }}
            onCompare={(record, targetSimulationId) => {
              const simulation = simulationForLifecycleRecord(world, record);
              if (simulation) onCompareSimulation?.(simulation, targetSimulationId);
            }}
            onOpenRunControls={(record) =>
              openVariation(record.parent_simulation_id ?? world.default_parent_simulation_id)
            }
          />
        </section>
      )}

      {section === "create" && (
        <section className="world-section mountain-waves-lab" aria-label="Create variation">
          <MountainWavesVariationEditor
            world={world}
            initialParentSimulationId={parentSimulationId ?? world.default_parent_simulation_id}
            onCreated={async () => {
              await loadWorld(true);
              setSection("activity");
            }}
          />
        </section>
      )}
    </section>
  );
}

function MountainWavesSimulationCard({
  simulation,
  onExplore,
  onCreateVariation,
  onCompare,
}: {
  simulation: MountainWavesSimulation;
  onExplore: (simulation: MountainWavesSimulation) => void;
  onCreateVariation: (simulationId: string) => void;
  onCompare?: (simulation: MountainWavesSimulation) => void;
}) {
  return (
    <article className="simulation-card">
      <header>
        <div>
          <p className="eyebrow">
            {simulation.legacy_contract
              ? "Legacy-contract Simulation"
              : simulation.role === "variation"
                ? "Variation"
                : simulation.simulation_id === simulation.reference_simulation_id
                  ? "Reference Simulation"
                  : "Built-in Simulation"}
          </p>
          <h3>{simulation.display_name}</h3>
        </div>
        {!simulation.inspectable && (
          <span className={`technical-state ${simulation.state}`}>
            {stateLabel(simulation.state)}
          </span>
        )}
      </header>
      <p>{simulation.purpose}</p>
      {simulation.parent_simulation_id && (
        <p className="simulation-relationship">
          Parent: {simulation.parent_simulation_id.replace("mountain_waves_", "")}
        </p>
      )}
      {!simulation.inspectable && <p>{simulation.state_message}</p>}
      <details className="simulation-details">
        <summary>Details</summary>
        <dl>
          <div>
            <dt>Run</dt>
            <dd>{simulation.run_id}</dd>
          </div>
          <div>
            <dt>Atmosphere</dt>
            <dd>{simulation.moist ? "Moist" : "Dry"}</dd>
          </div>
          <div>
            <dt>Geometry</dt>
            <dd>Native 2-D x-z · singleton y</dd>
          </div>
          {simulation.recipe_id && (
            <div>
              <dt>Recipe</dt>
              <dd>
                {simulation.recipe_id.replaceAll("_", " ")}
                {simulation.recipe_contract_version
                  ? ` · contract ${simulation.recipe_contract_version}`
                  : ""}
              </dd>
            </div>
          )}
          {simulation.relationship_classification && (
            <div>
              <dt>Relationship</dt>
              <dd>{simulation.relationship_classification.replaceAll("_", " ")}</dd>
            </div>
          )}
          <div>
            <dt>Parent eligibility</dt>
            <dd>
              {simulation.can_create_variation
                ? "Eligible"
                : (simulation.parent_eligibility_reason ?? "Not eligible")}
            </dd>
          </div>
        </dl>
        {simulation.caveats.map((caveat) => (
          <p key={caveat}>{caveat}</p>
        ))}
      </details>
      <div className="simulation-actions">
        <button
          type="button"
          disabled={!simulation.inspectable}
          onClick={() => onExplore(simulation)}
        >
          Explore
        </button>
        {onCompare && (
          <button
            type="button"
            className="secondary-button"
            disabled={!simulation.inspectable}
            onClick={() => onCompare(simulation)}
          >
            Compare
          </button>
        )}
        {simulation.can_create_variation && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onCreateVariation(simulation.simulation_id)}
          >
            Create variation
          </button>
        )}
      </div>
    </article>
  );
}

function mountainWavesCompareTarget(
  simulations: MountainWavesSimulation[],
  simulation: MountainWavesSimulation,
): string | null {
  if (simulation.parent_simulation_id) return simulation.parent_simulation_id;
  const child = simulations.find(
    (candidate) =>
      candidate.inspectable && candidate.parent_simulation_id === simulation.simulation_id,
  );
  if (child) return child.simulation_id;
  return (
    simulations.find(
      (candidate) => candidate.inspectable && candidate.simulation_id !== simulation.simulation_id,
    )?.simulation_id ?? null
  );
}

function WorldBreadcrumb({ onBackToWorlds }: { onBackToWorlds: () => void }) {
  return (
    <nav className="world-breadcrumb" aria-label="Breadcrumb">
      <button type="button" onClick={onBackToWorlds}>
        Cloud Worlds
      </button>
      <span aria-hidden="true">/</span>
      <span>Mountain Waves</span>
    </nav>
  );
}

function validateMountainWavesWorld(value: unknown): MountainWavesWorldDetail {
  if (
    !isRecord(value) ||
    value.world_id !== "mountain_waves" ||
    !Array.isArray(value.simulations)
  ) {
    throw new Error("Mountain Waves response does not match the required contract.");
  }
  return value as MountainWavesWorldDetail;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function sectionLabel(section: WorldSection): string {
  if (section === "overview") return "Overview";
  if (section === "simulations") return "Simulations";
  if (section === "saved_comparisons") return "Saved Comparisons";
  if (section === "create") return "Create Variation";
  return section === "activity" ? "Activity" : "History";
}

function simulationForLifecycleRecord(
  world: MountainWavesWorldDetail,
  record: LifecycleRecord,
): MountainWavesSimulation | null {
  const actionRunIds = new Set(
    record.actions
      .map((action) => action.run_id)
      .filter((runId): runId is string => Boolean(runId)),
  );
  return (
    world.simulations.find(
      (simulation) =>
        simulation.simulation_id === record.simulation_id || actionRunIds.has(simulation.run_id),
    ) ?? null
  );
}

function stateLabel(state: MountainWavesSimulation["state"]): string {
  return {
    available: "Completed",
    packaged: "Packaged",
    queued: "Queued",
    running: "Running",
    failed: "Failed",
    canceled: "Canceled",
    unavailable: "Unavailable",
    conflict: "Not inspectable",
  }[state];
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
