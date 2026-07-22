import { useCallback, useEffect, useState } from "react";

import { MountainWavesVariationEditor } from "./MountainWavesVariationEditor";

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

type WorldSection = "overview" | "simulations" | "lab";
type LabSection = "activity" | "create" | "history";

export function MountainWavesWorld({
  onBackToWorlds,
  onExploreSimulation,
}: {
  onBackToWorlds: () => void;
  onExploreSimulation: (simulation: MountainWavesSimulation) => void;
}) {
  const [section, setSection] = useState<WorldSection>("overview");
  const [labSection, setLabSection] = useState<LabSection>("create");
  const [world, setWorld] = useState<MountainWavesWorldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [parentSimulationId, setParentSimulationId] = useState<string | null>(null);
  const [cancelStatus, setCancelStatus] = useState<string | null>(null);

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

  useEffect(() => {
    if (!world || world.activity.length === 0) return;
    const timer = window.setInterval(() => void loadWorld(true), 2_000);
    return () => window.clearInterval(timer);
  }, [loadWorld, world]);

  function openVariation(parentId: string) {
    setParentSimulationId(parentId);
    setLabSection("create");
    setSection("lab");
  }

  async function cancelActiveRun() {
    setCancelStatus("Canceling active CM1 run...");
    try {
      const response = await fetch("/api/runs/cancel", { method: "POST" });
      if (!response.ok) throw new Error(await responseMessage(response, "Unable to cancel run."));
      setCancelStatus("Run canceled.");
      await loadWorld(true);
    } catch (caught) {
      setCancelStatus(caught instanceof Error ? caught.message : "Unable to cancel run.");
    }
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
        {(["overview", "simulations", "lab"] as WorldSection[]).map((item) => (
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
                />
              ))}
          </div>
          <p className="world-science-note">{world.caveats[0]}</p>
          <section className="world-lab-summary" aria-label="Mountain Waves Lab status">
            <div>
              <p className="eyebrow">Lab</p>
              <h3>{labSummary(world)}</h3>
              <p>
                {world.lab_summary.active_run_count} active · {world.lab_summary.packaged_run_count}{" "}
                packaged · {world.lab_summary.total_variation_count} in history
              </p>
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
              />
            ))}
          </div>
        </section>
      )}

      {section === "lab" && (
        <section className="world-section mountain-waves-lab" aria-label="Mountain Waves Lab">
          <nav className="lab-subnav" aria-label="Mountain Waves Lab sections">
            {(["activity", "create", "history"] as LabSection[]).map((item) => (
              <button
                key={item}
                type="button"
                className={labSection === item ? "active-control" : ""}
                onClick={() => setLabSection(item)}
              >
                {item === "create" ? "Create Variation" : capitalize(item)}
              </button>
            ))}
          </nav>

          {labSection === "activity" && (
            <section className="lab-content" aria-labelledby="mountain-waves-activity-title">
              <div className="world-section-heading">
                <div>
                  <p className="eyebrow">Activity</p>
                  <h3 id="mountain-waves-activity-title">Current CM1 work</h3>
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void loadWorld(true)}
                >
                  Refresh
                </button>
              </div>
              {world.activity.length ? (
                <div className="lab-history-list mountain-waves-activity-list">
                  {world.activity.map((attempt) => (
                    <MountainWavesAttemptRow
                      key={attempt.simulation_id}
                      attempt={attempt}
                      onExplore={onExploreSimulation}
                    />
                  ))}
                </div>
              ) : (
                <section className="world-empty-state">
                  <h3>Lab is idle</h3>
                  <p>Packaged, queued, and running variations will remain visible here.</p>
                </section>
              )}
              {world.activity.some((attempt) => attempt.state === "running") && (
                <button
                  type="button"
                  className="danger-button"
                  onClick={() => void cancelActiveRun()}
                >
                  Cancel active run
                </button>
              )}
              {cancelStatus && <p role="status">{cancelStatus}</p>}
            </section>
          )}

          {labSection === "create" && (
            <MountainWavesVariationEditor
              world={world}
              initialParentSimulationId={parentSimulationId ?? world.default_parent_simulation_id}
              onCreated={async () => {
                await loadWorld(true);
                setLabSection("activity");
              }}
            />
          )}

          {labSection === "history" && (
            <section className="lab-content" aria-labelledby="mountain-waves-history-title">
              <div className="world-section-heading">
                <div>
                  <p className="eyebrow">History</p>
                  <h3 id="mountain-waves-history-title">Every retained variation attempt</h3>
                </div>
              </div>
              {world.history.length ? (
                <div className="lab-history-list mountain-waves-history-list">
                  {world.history.map((attempt) => (
                    <MountainWavesAttemptRow
                      key={attempt.simulation_id}
                      attempt={attempt}
                      onExplore={onExploreSimulation}
                      onCreateVariation={openVariation}
                    />
                  ))}
                </div>
              ) : (
                <section className="world-empty-state">
                  <p>No Mountain Waves variations have been created yet.</p>
                </section>
              )}
            </section>
          )}
        </section>
      )}
    </section>
  );
}

function MountainWavesSimulationCard({
  simulation,
  onExplore,
  onCreateVariation,
}: {
  simulation: MountainWavesSimulation;
  onExplore: (simulation: MountainWavesSimulation) => void;
  onCreateVariation: (simulationId: string) => void;
}) {
  return (
    <article className="simulation-card">
      <header>
        <div>
          <p className="eyebrow">
            {simulation.role === "variation"
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

function MountainWavesAttemptRow({
  attempt,
  onExplore,
  onCreateVariation,
}: {
  attempt: MountainWavesSimulation;
  onExplore: (simulation: MountainWavesSimulation) => void;
  onCreateVariation?: (simulationId: string) => void;
}) {
  return (
    <article>
      <div>
        <strong>{attempt.display_name}</strong>
        <span>
          {stateLabel(attempt.state)} · {attempt.state_message}
        </span>
        <code>{attempt.run_id}</code>
      </div>
      <div className="simulation-actions">
        {attempt.inspectable && (
          <button type="button" onClick={() => onExplore(attempt)}>
            Explore
          </button>
        )}
        {attempt.can_create_variation && onCreateVariation && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onCreateVariation(attempt.simulation_id)}
          >
            Create variation
          </button>
        )}
      </div>
    </article>
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
  return section === "overview" ? "Overview" : section === "simulations" ? "Simulations" : "Lab";
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
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

function labSummary(world: MountainWavesWorldDetail): string {
  if (world.lab_summary.active_run_count) return "CM1 is running";
  if (world.lab_summary.packaged_run_count) return "A variation is ready to run";
  return world.lab_summary.total_variation_count
    ? "Ready for another experiment"
    : "Start an experiment";
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
