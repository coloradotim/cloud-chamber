import { type ReactNode, useCallback, useEffect, useState } from "react";

export type ConfigurationDifference = {
  path: string;
  label: string;
  category: "atmospheric" | "numerical" | "output" | "operational" | "metadata";
  left_value: unknown;
  right_value: unknown;
  units: string | null;
  material: boolean;
};

export type SimulationRecord = {
  simulation_id: string | null;
  display_name: string;
  role: "reference" | "variation" | "lab_history";
  world_id: "trade_cumulus";
  product_slice_id: string;
  case_id: string;
  result_id: string;
  run_id: string;
  source_recipe_id: string | null;
  parent_simulation_id: string | null;
  reference_simulation_id: string | null;
  technical_state: "available" | "missing" | "conflict";
  technical_state_message: string;
  technical_trust_state: "trusted" | "caveated" | "untrusted" | "unassessed" | "unavailable";
  explore_available: boolean;
  compare_suggestions: Array<{
    comparison_id: string;
    display_name: string;
    target_simulation_id: string;
  }>;
  configuration_difference_from_reference: ConfigurationDifference[] | null;
  lineage_state: "known" | "valid" | "unlineaged" | "invalid";
  created_at: string | null;
  completed_at: string | null;
};

export type TradeCumulusWorldDetail = {
  world_id: "trade_cumulus";
  display_name: "Trade Cumulus";
  status: "mvp_candidate";
  short_description: string;
  availability_state: "available" | "partial" | "unavailable" | "conflict";
  availability_message: string;
  reference_simulation: SimulationRecord;
  simulations: SimulationRecord[];
  lab_history: SimulationRecord[];
  featured_comparison: {
    comparison_id: "trade_cumulus_moisture_v1";
    display_name: "More Moisture versus Baseline";
    baseline_simulation_id: string;
    more_moisture_simulation_id: "trade_cumulus_more_moisture";
    availability_state: "available" | "missing" | "conflict";
    availability_message: string;
    open_available: boolean;
  };
  lab_summary: {
    active_run_count: number;
    completed_uninspected_run_count: number;
    lab_history_count: number;
    summary: string;
  };
  capabilities: {
    reference_explore: boolean;
    featured_comparison: boolean;
    lab: true;
    saved_views: false;
    ordinary_compare: false;
  };
  caveats: string[];
};

export type TradeCumulusWorldSection =
  | "overview"
  | "simulations"
  | "saved_views"
  | "comparisons"
  | "lab";
export type TradeCumulusLabSection = "build" | "results";

export function TradeCumulusWorld({
  onBackToWorlds,
  onExploreSimulation,
  onOpenFeaturedComparison,
  buildContent,
  resultsContent,
  section: controlledSection,
  labSection: controlledLabSection,
  onSectionChange,
  onLabSectionChange,
  onWorldDetailChange,
  initialSection = "overview",
  initialLabSection = "results",
}: {
  onBackToWorlds: () => void;
  onExploreSimulation: (simulation: SimulationRecord) => void;
  onOpenFeaturedComparison: () => void;
  buildContent: ReactNode;
  resultsContent: ReactNode;
  section?: TradeCumulusWorldSection;
  labSection?: TradeCumulusLabSection;
  onSectionChange?: (section: TradeCumulusWorldSection) => void;
  onLabSectionChange?: (section: TradeCumulusLabSection) => void;
  onWorldDetailChange?: (world: TradeCumulusWorldDetail | null) => void;
  initialSection?: TradeCumulusWorldSection;
  initialLabSection?: TradeCumulusLabSection;
}) {
  const [internalSection, setInternalSection] = useState<TradeCumulusWorldSection>(initialSection);
  const [internalLabSection, setInternalLabSection] =
    useState<TradeCumulusLabSection>(initialLabSection);
  const section = controlledSection ?? internalSection;
  const labSection = controlledLabSection ?? internalLabSection;
  const [world, setWorld] = useState<TradeCumulusWorldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWorld = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/worlds/trade-cumulus");
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Trade Cumulus is unavailable."));
      }
      setWorld(validateWorldDetail(await response.json()));
    } catch (caught) {
      setWorld(null);
      setError(caught instanceof Error ? caught.message : "Trade Cumulus is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorld();
  }, [loadWorld]);

  useEffect(() => {
    onWorldDetailChange?.(world);
  }, [onWorldDetailChange, world]);

  function changeSection(target: TradeCumulusWorldSection) {
    if (controlledSection === undefined) setInternalSection(target);
    onSectionChange?.(target);
  }

  function changeLabSection(target: TradeCumulusLabSection) {
    if (controlledLabSection === undefined) setInternalLabSection(target);
    onLabSectionChange?.(target);
  }

  function openLab(target: TradeCumulusLabSection = "build") {
    changeLabSection(target);
    changeSection("lab");
  }

  if (loading) {
    return (
      <section className="world-shell" aria-label="Trade Cumulus World">
        <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
        <section className="status-panel" role="status">
          Loading Trade Cumulus...
        </section>
      </section>
    );
  }

  if (!world) {
    return (
      <section className="world-shell" aria-label="Trade Cumulus World">
        <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
        <section className="world-load-failure" aria-label="Trade Cumulus unavailable">
          <div>
            <h2>Trade Cumulus could not be loaded</h2>
            <p role="alert">{error}</p>
            <p>The existing Lab remains available while World data is retried.</p>
          </div>
          <button type="button" onClick={() => void loadWorld()}>
            Retry Trade Cumulus
          </button>
        </section>
        <LabWorkspace
          labSection={labSection}
          setLabSection={changeLabSection}
          buildContent={buildContent}
          resultsContent={resultsContent}
          history={[]}
          onExploreSimulation={onExploreSimulation}
        />
      </section>
    );
  }

  return (
    <section className="world-shell" aria-label="Trade Cumulus World">
      <WorldBreadcrumb onBackToWorlds={onBackToWorlds} />
      <header className="world-header">
        <div>
          <h2>{world.display_name}</h2>
          <p>{world.short_description}</p>
        </div>
      </header>

      <nav className="world-section-nav" aria-label="Trade Cumulus sections">
        {(
          [
            "overview",
            "simulations",
            "saved_views",
            "comparisons",
            "lab",
          ] as TradeCumulusWorldSection[]
        ).map((item) => (
          <button
            key={item}
            type="button"
            className={section === item ? "active-control" : ""}
            onClick={() => changeSection(item)}
          >
            {sectionLabel(item)}
          </button>
        ))}
      </nav>

      {section === "overview" && (
        <Overview
          world={world}
          onExploreSimulation={onExploreSimulation}
          onOpenFeaturedComparison={onOpenFeaturedComparison}
          onOpenLab={() => openLab("build")}
        />
      )}
      {section === "simulations" && (
        <SimulationsSection
          world={world}
          onExploreSimulation={onExploreSimulation}
          onOpenFeaturedComparison={onOpenFeaturedComparison}
        />
      )}
      {section === "saved_views" && <SavedViewsSection />}
      {section === "comparisons" && (
        <ComparisonsSection world={world} onOpenFeaturedComparison={onOpenFeaturedComparison} />
      )}
      {section === "lab" && (
        <LabWorkspace
          labSection={labSection}
          setLabSection={changeLabSection}
          buildContent={buildContent}
          resultsContent={resultsContent}
          history={world.lab_history}
          onExploreSimulation={onExploreSimulation}
        />
      )}
    </section>
  );
}

function WorldBreadcrumb({ onBackToWorlds }: { onBackToWorlds: () => void }) {
  return (
    <nav className="world-breadcrumb" aria-label="Breadcrumb">
      <button type="button" onClick={onBackToWorlds}>
        Cloud Worlds
      </button>
      <span aria-hidden="true">/</span>
      <span>Trade Cumulus</span>
    </nav>
  );
}

function Overview({
  world,
  onExploreSimulation,
  onOpenFeaturedComparison,
  onOpenLab,
}: {
  world: TradeCumulusWorldDetail;
  onExploreSimulation: (simulation: SimulationRecord) => void;
  onOpenFeaturedComparison: () => void;
  onOpenLab: () => void;
}) {
  const moreMoisture = world.simulations.find(
    (simulation) =>
      simulation.simulation_id === "trade_cumulus_more_moisture" &&
      simulation.parent_simulation_id === world.reference_simulation.simulation_id,
  );
  const comparisonMatchesReference =
    world.featured_comparison.baseline_simulation_id ===
    world.reference_simulation.simulation_id;
  return (
    <section className="world-section" aria-labelledby="world-overview-title">
      <div className="world-section-heading">
        <div>
          <p className="eyebrow">Overview</p>
          <h3 id="world-overview-title">Return to the cloud field</h3>
        </div>
      </div>

      <div className="world-overview-grid">
        <SimulationCard
          simulation={world.reference_simulation}
          comparisonAvailable={world.featured_comparison.open_available}
          onExplore={onExploreSimulation}
          onCompare={onOpenFeaturedComparison}
        />
        {moreMoisture && moreMoisture.technical_state !== "missing" && (
          <SimulationCard
            simulation={moreMoisture}
            comparisonAvailable={world.featured_comparison.open_available}
            onExplore={onExploreSimulation}
            onCompare={onOpenFeaturedComparison}
          />
        )}
        {comparisonMatchesReference && (
          <ComparisonCard
            comparison={world.featured_comparison}
            onOpen={onOpenFeaturedComparison}
          />
        )}
      </div>

      <section className="world-lab-summary" aria-label="Trade Cumulus Lab status">
        <div>
          <p className="eyebrow">Lab</p>
          <h3>{world.lab_summary.summary}</h3>
          <p>
            {world.lab_summary.active_run_count} active ·{" "}
            {world.lab_summary.completed_uninspected_run_count} awaiting inspection ·{" "}
            {world.lab_summary.lab_history_count} in Lab history
          </p>
        </div>
        <button type="button" onClick={onOpenLab}>
          Open Trade Cumulus Lab
        </button>
      </section>
    </section>
  );
}

function SimulationsSection({
  world,
  onExploreSimulation,
  onOpenFeaturedComparison,
}: {
  world: TradeCumulusWorldDetail;
  onExploreSimulation: (simulation: SimulationRecord) => void;
  onOpenFeaturedComparison: () => void;
}) {
  return (
    <section className="world-section" aria-labelledby="world-simulations-title">
      <div className="world-section-heading">
        <div>
          <p className="eyebrow">Simulations</p>
          <h3 id="world-simulations-title">Retained Trade Cumulus Simulations</h3>
        </div>
        <p>
          {world.simulations.filter((item) => item.technical_state === "available").length}{" "}
          available
        </p>
      </div>
      <div className="simulation-card-grid">
        {world.simulations.map((simulation) => (
          <SimulationCard
            key={simulation.simulation_id ?? simulation.result_id}
            simulation={simulation}
            comparisonAvailable={world.featured_comparison.open_available}
            onExplore={onExploreSimulation}
            onCompare={onOpenFeaturedComparison}
          />
        ))}
      </div>
    </section>
  );
}

function SimulationCard({
  simulation,
  comparisonAvailable,
  onExplore,
  onCompare,
}: {
  simulation: SimulationRecord;
  comparisonAvailable: boolean;
  onExplore: (simulation: SimulationRecord) => void;
  onCompare: () => void;
}) {
  const differences = simulation.configuration_difference_from_reference ?? [];
  const materialDifferences = differences.filter((difference) => difference.material);
  return (
    <article className="simulation-card" aria-label={`${simulation.display_name} Simulation`}>
      <header>
        <div>
          <p className="eyebrow">{roleLabel(simulation.role)}</p>
          <h3>{simulation.display_name}</h3>
        </div>
        {simulation.technical_state !== "available" && (
          <div className="simulation-state-row">
            <span className={`technical-state ${simulation.technical_state}`}>
              {technicalStateLabel(simulation.technical_state)}
            </span>
          </div>
        )}
      </header>
      {simulation.technical_state !== "available" && <p>{simulation.technical_state_message}</p>}
      {simulation.parent_simulation_id && (
        <p className="simulation-relationship">
          Parent: {relationshipName(simulation.parent_simulation_id)}
        </p>
      )}
      {materialDifferences.length > 0 && (
        <dl className="configuration-differences">
          {materialDifferences.map((difference) => (
            <div key={difference.path}>
              <dt>{difference.label}</dt>
              <dd>{formatDifference(difference)}</dd>
            </div>
          ))}
        </dl>
      )}
      <details className="simulation-details">
        <summary>Details</summary>
        <dl>
          <div>
            <dt>Simulation ID</dt>
            <dd>{simulation.simulation_id ?? "No retained identity"}</dd>
          </div>
          <div>
            <dt>Result ID</dt>
            <dd>{simulation.result_id}</dd>
          </div>
          <div>
            <dt>Run ID</dt>
            <dd>{simulation.run_id}</dd>
          </div>
          <div>
            <dt>Runtime integrity</dt>
            <dd>{trustLabel(simulation.technical_trust_state)}</dd>
          </div>
        </dl>
      </details>
      <div className="simulation-actions">
        <button
          type="button"
          disabled={!simulation.explore_available}
          onClick={() => onExplore(simulation)}
        >
          Explore
        </button>
        {comparisonAvailable && simulation.compare_suggestions.length > 0 && (
          <button type="button" className="secondary-button" onClick={onCompare}>
            Compare
          </button>
        )}
      </div>
    </article>
  );
}

function SavedViewsSection() {
  return (
    <section className="world-section" aria-labelledby="saved-views-title">
      <div className="world-section-heading">
        <div>
          <p className="eyebrow">Saved Views</p>
          <h3 id="saved-views-title">No Saved Views yet</h3>
        </div>
      </div>
      <section className="world-empty-state">
        <p>Saved Views are not implemented in this increment.</p>
      </section>
    </section>
  );
}

function ComparisonsSection({
  world,
  onOpenFeaturedComparison,
}: {
  world: TradeCumulusWorldDetail;
  onOpenFeaturedComparison: () => void;
}) {
  return (
    <section className="world-section" aria-labelledby="world-comparisons-title">
      <div className="world-section-heading">
        <div>
          <p className="eyebrow">Comparisons</p>
          <h3 id="world-comparisons-title">Trade Cumulus Comparisons</h3>
        </div>
      </div>
      <ComparisonCard comparison={world.featured_comparison} onOpen={onOpenFeaturedComparison} />
    </section>
  );
}

function ComparisonCard({
  comparison,
  onOpen,
}: {
  comparison: TradeCumulusWorldDetail["featured_comparison"];
  onOpen: () => void;
}) {
  return (
    <article className="comparison-card" aria-label="Featured Trade Cumulus Comparison">
      <header>
        <div>
          <p className="eyebrow">Featured Comparison</p>
          <h3>{comparison.display_name}</h3>
        </div>
        {comparison.availability_state !== "available" && (
          <span className={`technical-state ${comparison.availability_state}`}>
            {technicalStateLabel(comparison.availability_state)}
          </span>
        )}
      </header>
      {comparison.availability_state !== "available" && <p>{comparison.availability_message}</p>}
      <button type="button" disabled={!comparison.open_available} onClick={onOpen}>
        Open Comparison
      </button>
    </article>
  );
}

function LabWorkspace({
  labSection,
  setLabSection,
  buildContent,
  resultsContent,
  history,
  onExploreSimulation,
}: {
  labSection: TradeCumulusLabSection;
  setLabSection: (section: TradeCumulusLabSection) => void;
  buildContent: ReactNode;
  resultsContent: ReactNode;
  history: SimulationRecord[];
  onExploreSimulation: (simulation: SimulationRecord) => void;
}) {
  return (
    <section className="world-section world-lab" aria-labelledby="world-lab-title">
      <div className="world-section-heading">
        <div>
          <p className="eyebrow">Trade Cumulus Lab</p>
          <h3 id="world-lab-title">Build and inspect model runs</h3>
        </div>
        <nav className="lab-subnav" aria-label="Trade Cumulus Lab">
          {(["build", "results"] as TradeCumulusLabSection[]).map((item) => (
            <button
              key={item}
              type="button"
              className={labSection === item ? "active-control" : ""}
              onClick={() => setLabSection(item)}
            >
              {item === "build" ? "Build" : "Results"}
            </button>
          ))}
        </nav>
      </div>
      {history.length > 0 && (
        <details className="lab-history">
          <summary>Lab history ({history.length})</summary>
          <div className="lab-history-list">
            {history.map((simulation) => (
              <article key={simulation.result_id}>
                <div>
                  <strong>{simulation.display_name}</strong>
                  <span>{simulation.technical_state_message}</span>
                  <code>{simulation.result_id}</code>
                </div>
                <button
                  type="button"
                  disabled={!simulation.explore_available}
                  onClick={() => onExploreSimulation(simulation)}
                >
                  Explore
                </button>
              </article>
            ))}
          </div>
        </details>
      )}
      <div className="lab-content">{labSection === "build" ? buildContent : resultsContent}</div>
    </section>
  );
}

function validateWorldDetail(payload: unknown): TradeCumulusWorldDetail {
  if (!isRecord(payload) || !isSimulation(payload.reference_simulation)) {
    throw new Error("Trade Cumulus response does not match the required contract.");
  }
  const simulations = payload.simulations;
  const labHistory = payload.lab_history;
  const comparison = payload.featured_comparison;
  const labSummary = payload.lab_summary;
  const capabilities = payload.capabilities;
  if (
    payload.world_id !== "trade_cumulus" ||
    payload.display_name !== "Trade Cumulus" ||
    payload.status !== "mvp_candidate" ||
    typeof payload.short_description !== "string" ||
    !isAvailabilityState(payload.availability_state) ||
    typeof payload.availability_message !== "string" ||
    !Array.isArray(simulations) ||
    !simulations.every(isSimulation) ||
    !Array.isArray(labHistory) ||
    !labHistory.every(isSimulation) ||
    !isFeaturedComparison(comparison) ||
    !isLabSummary(labSummary) ||
    !isCapabilities(capabilities) ||
    !Array.isArray(payload.caveats) ||
    !payload.caveats.every((item) => typeof item === "string")
  ) {
    throw new Error("Trade Cumulus response does not match the required contract.");
  }
  return payload as TradeCumulusWorldDetail;
}

function isSimulation(value: unknown): value is SimulationRecord {
  if (!isRecord(value)) return false;
  return (
    (typeof value.simulation_id === "string" || value.simulation_id === null) &&
    typeof value.display_name === "string" &&
    ["reference", "variation", "lab_history"].includes(String(value.role)) &&
    value.world_id === "trade_cumulus" &&
    typeof value.product_slice_id === "string" &&
    typeof value.case_id === "string" &&
    typeof value.result_id === "string" &&
    typeof value.run_id === "string" &&
    ["available", "missing", "conflict"].includes(String(value.technical_state)) &&
    typeof value.technical_state_message === "string" &&
    typeof value.explore_available === "boolean" &&
    Array.isArray(value.compare_suggestions) &&
    (value.configuration_difference_from_reference === null ||
      (Array.isArray(value.configuration_difference_from_reference) &&
        value.configuration_difference_from_reference.every(isDifference))) &&
    ["known", "valid", "unlineaged", "invalid"].includes(String(value.lineage_state))
  );
}

function isDifference(value: unknown): value is ConfigurationDifference {
  if (!isRecord(value)) return false;
  return (
    typeof value.path === "string" &&
    typeof value.label === "string" &&
    ["atmospheric", "numerical", "output", "operational", "metadata"].includes(
      String(value.category),
    ) &&
    (typeof value.units === "string" || value.units === null) &&
    typeof value.material === "boolean"
  );
}

function isFeaturedComparison(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    value.comparison_id === "trade_cumulus_moisture_v1" &&
    value.display_name === "More Moisture versus Baseline" &&
    isTechnicalState(value.availability_state) &&
    typeof value.availability_message === "string" &&
    typeof value.open_available === "boolean"
  );
}

function isLabSummary(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    isNonnegativeNumber(value.active_run_count) &&
    isNonnegativeNumber(value.completed_uninspected_run_count) &&
    isNonnegativeNumber(value.lab_history_count) &&
    typeof value.summary === "string"
  );
}

function isCapabilities(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    typeof value.reference_explore === "boolean" &&
    typeof value.featured_comparison === "boolean" &&
    value.lab === true &&
    value.saved_views === false &&
    value.ordinary_compare === false
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonnegativeNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isAvailabilityState(value: unknown): boolean {
  return ["available", "partial", "unavailable", "conflict"].includes(String(value));
}

function isTechnicalState(value: unknown): boolean {
  return ["available", "missing", "conflict"].includes(String(value));
}

function sectionLabel(section: TradeCumulusWorldSection): string {
  return {
    overview: "Overview",
    simulations: "Simulations",
    saved_views: "Saved Views",
    comparisons: "Comparisons",
    lab: "Lab",
  }[section];
}

function technicalStateLabel(state: "available" | "missing" | "conflict"): string {
  return { available: "Available", missing: "Missing", conflict: "Conflict" }[state];
}

function trustLabel(state: SimulationRecord["technical_trust_state"]): string {
  return {
    trusted: "Trusted output",
    caveated: "Caveated output",
    untrusted: "Untrusted output",
    unassessed: "Trust not assessed",
    unavailable: "Trust unavailable",
  }[state];
}

function roleLabel(role: SimulationRecord["role"]): string {
  return {
    reference: "Reference Simulation",
    variation: "Variation",
    lab_history: "Lab history",
  }[role];
}

function relationshipName(simulationId: string): string {
  if (simulationId === "trade_cumulus_canonical_bomex") return "Canonical BOMEX Baseline";
  if (simulationId === "trade_cumulus_more_moisture") return "More Moisture";
  return simulationId;
}

function formatDifference(difference: ConfigurationDifference): string {
  const moistureFlux = difference.units === "g/g m/s";
  const left = formatValue(
    moistureFlux && typeof difference.left_value === "number"
      ? difference.left_value * 1000
      : difference.left_value,
  );
  const right = formatValue(
    moistureFlux && typeof difference.right_value === "number"
      ? difference.right_value * 1000
      : difference.right_value,
  );
  const displayUnits = moistureFlux ? "g/kg m/s" : difference.units;
  const units = displayUnits ? ` ${displayUnits}` : "";
  return `${left}${units} to ${right}${units}`;
}

function formatValue(value: unknown): string {
  if (typeof value === "number")
    return Number.isInteger(value) ? String(value) : value.toPrecision(4);
  if (typeof value === "string" || typeof value === "boolean") return String(value);
  if (value === null || value === undefined) return "Not set";
  return JSON.stringify(value);
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
