import { useCallback, useEffect, useState } from "react";

export type SupercellSimulation = {
  simulation_id: "supercells_quarter_circle_reference";
  display_name: "Quarter-Circle Supercell";
  role: "reference";
  world_id: "supercells";
  run_id: string;
  case_id: string;
  technical_state: "available" | "missing" | "invalid";
  technical_state_message: string;
  explore_available: boolean;
  saved_output_count: number;
  model_start_seconds: number | null;
  model_end_seconds: number | null;
  history_cadence_seconds: number | null;
  default_explore_time_index: number;
  lineage_state: "known";
};

export type SupercellsWorldDetail = {
  world_id: "supercells";
  display_name: "Supercells";
  short_description: string;
  availability_state: "available" | "partial" | "unavailable";
  availability_message: string;
  reference_simulation: SupercellSimulation;
  simulations: SupercellSimulation[];
  capabilities: {
    reference_explore: boolean;
    lab: false;
    compare: false;
    saved_views: false;
  };
  caveats: string[];
};

type WorldSection = "overview" | "simulations";

export function SupercellsWorld({
  onBackToWorlds,
  onExploreSimulation,
}: {
  onBackToWorlds: () => void;
  onExploreSimulation: (simulation: SupercellSimulation) => void;
}) {
  const [section, setSection] = useState<WorldSection>("overview");
  const [world, setWorld] = useState<SupercellsWorldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWorld = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/worlds/supercells");
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Supercells is unavailable."));
      }
      setWorld(validateSupercellsWorld(await response.json()));
    } catch (caught) {
      setWorld(null);
      setError(caught instanceof Error ? caught.message : "Supercells is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorld();
  }, [loadWorld]);

  if (loading) {
    return (
      <section className="world-shell" aria-label="Supercells World">
        <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
        <section className="status-panel" role="status">
          Loading Supercells...
        </section>
      </section>
    );
  }

  if (!world) {
    return (
      <section className="world-shell" aria-label="Supercells World">
        <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
        <section className="world-load-failure" aria-label="Supercells unavailable">
          <div>
            <h2>Supercells could not be loaded</h2>
            <p role="alert">{error}</p>
            <p>Other Cloud Worlds remain available.</p>
          </div>
          <button type="button" onClick={() => void loadWorld()}>
            Retry Supercells
          </button>
        </section>
      </section>
    );
  }

  const simulation = world.reference_simulation;
  return (
    <section className="world-shell" aria-label="Supercells World">
      <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
      <header className="world-header">
        <div>
          <h2>{world.display_name}</h2>
          <p>{world.short_description}</p>
        </div>
      </header>

      <nav className="world-section-nav" aria-label="Supercells sections">
        {(["overview", "simulations"] as WorldSection[]).map((item) => (
          <button
            key={item}
            type="button"
            className={section === item ? "active-control" : ""}
            onClick={() => setSection(item)}
          >
            {item === "overview" ? "Overview" : "Simulations"}
          </button>
        ))}
      </nav>

      <section className="world-section" aria-labelledby={`supercells-${section}-title`}>
        <div className="world-section-heading">
          <div>
            <p className="eyebrow">{section === "overview" ? "Overview" : "Simulations"}</p>
            <h3 id={`supercells-${section}-title`}>
              {section === "overview"
                ? "Enter the rotating storm"
                : "Retained Supercell Simulations"}
            </h3>
          </div>
          {section === "simulations" && (
            <p>{simulation.explore_available ? "1 inspectable" : "0 inspectable"}</p>
          )}
        </div>
        {world.availability_state !== "available" && (
          <p className="world-availability-message">{world.availability_message}</p>
        )}
        <div className="simulation-card-grid supercells-simulation-grid">
          <SupercellSimulationCard simulation={simulation} onExplore={onExploreSimulation} />
        </div>
        {section === "overview" && <p className="world-science-note">{world.caveats[0]}</p>}
      </section>
    </section>
  );
}

function SupercellSimulationCard({
  simulation,
  onExplore,
}: {
  simulation: SupercellSimulation;
  onExplore: (simulation: SupercellSimulation) => void;
}) {
  return (
    <article className="simulation-card supercell-simulation-card">
      <div className="simulation-card-heading">
        <div>
          <p className="eyebrow">Reference Simulation</p>
          <h3>{simulation.display_name}</h3>
        </div>
        {simulation.technical_state !== "available" && (
          <span className={`world-availability ${simulation.technical_state}`}>
            {simulation.technical_state === "missing" ? "Output unavailable" : "Output invalid"}
          </span>
        )}
      </div>
      <p>
        Follow organized ascent and rotation, liquid and ice, precipitation, and low-level flow
        through an idealized CM1 supercell.
      </p>
      {simulation.explore_available ? (
        <dl className="simulation-card-facts">
          <div>
            <dt>Saved outputs</dt>
            <dd>{simulation.saved_output_count}</dd>
          </div>
          <div>
            <dt>Model time</dt>
            <dd>{formatDuration(simulation.model_end_seconds)}</dd>
          </div>
          <div>
            <dt>Cadence</dt>
            <dd>{formatDuration(simulation.history_cadence_seconds)}</dd>
          </div>
        </dl>
      ) : (
        <p className="world-availability-message">{simulation.technical_state_message}</p>
      )}
      <div className="button-row">
        <button
          type="button"
          disabled={!simulation.explore_available}
          onClick={() => onExplore(simulation)}
        >
          Explore
        </button>
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
      <span>Supercells</span>
    </nav>
  );
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "Unavailable";
  if (seconds >= 3_600 && seconds % 3_600 === 0) return `${seconds / 3_600} hr`;
  if (seconds >= 60 && seconds % 60 === 0) return `${seconds / 60} min`;
  return `${seconds.toLocaleString()} s`;
}

function validateSupercellsWorld(payload: unknown): SupercellsWorldDetail {
  if (
    !isRecord(payload) ||
    payload.world_id !== "supercells" ||
    !Array.isArray(payload.simulations)
  ) {
    throw new Error("Supercells response does not match the required World contract.");
  }
  const reference = payload.reference_simulation;
  if (
    !isRecord(reference) ||
    reference.simulation_id !== "supercells_quarter_circle_reference" ||
    reference.display_name !== "Quarter-Circle Supercell" ||
    typeof reference.default_explore_time_index !== "number"
  ) {
    throw new Error("Supercells reference Simulation identity is invalid.");
  }
  return payload as SupercellsWorldDetail;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
