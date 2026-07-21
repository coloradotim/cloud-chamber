import { type ReactNode, useCallback, useEffect, useState } from "react";

export type CloudWorldSummary = {
  world_id: "trade_cumulus";
  display_name: "Trade Cumulus";
  status: "mvp_candidate";
  short_description: string;
  reference_simulation_id: "trade_cumulus_canonical_bomex";
  reference_available: boolean;
  simulation_count: number;
  saved_view_count: 0;
  saved_comparison_count: number;
  featured_comparison_count: number;
  active_run_count: number;
  completed_uninspected_run_count: number;
  availability_state: "available" | "partial" | "unavailable" | "conflict";
  availability_message: string;
};

type LoadState =
  | { status: "loading"; worlds: CloudWorldSummary[]; error: null }
  | { status: "loaded"; worlds: CloudWorldSummary[]; error: null }
  | { status: "failed"; worlds: []; error: string };

export function CloudWorldsHome({
  onEnterTradeCumulus,
  fallback,
}: {
  onEnterTradeCumulus: () => void;
  fallback?: ReactNode;
}) {
  const [loadState, setLoadState] = useState<LoadState>({
    status: "loading",
    worlds: [],
    error: null,
  });

  const loadWorlds = useCallback(async () => {
    setLoadState({ status: "loading", worlds: [], error: null });
    try {
      const response = await fetch("/api/worlds");
      if (!response.ok)
        throw new Error(await responseMessage(response, "Cloud Worlds unavailable."));
      const worlds = validateWorldSummaries(await response.json());
      setLoadState({ status: "loaded", worlds, error: null });
    } catch (caught) {
      setLoadState({
        status: "failed",
        worlds: [],
        error: caught instanceof Error ? caught.message : "Cloud Worlds unavailable.",
      });
    }
  }, []);

  useEffect(() => {
    void loadWorlds();
  }, [loadWorlds]);

  if (loadState.status === "loading") {
    return (
      <section className="worlds-home" aria-labelledby="cloud-worlds-title">
        <WorldsHeading />
        <section className="status-panel" role="status">
          Loading Cloud Worlds...
        </section>
      </section>
    );
  }

  if (loadState.status === "failed") {
    return (
      <section className="worlds-home" aria-labelledby="cloud-worlds-title">
        <WorldsHeading />
        <section className="world-load-failure" aria-label="Cloud Worlds unavailable">
          <div>
            <h2>Cloud Worlds could not be loaded</h2>
            <p>{loadState.error}</p>
          </div>
          <button type="button" onClick={() => void loadWorlds()}>
            Retry Worlds
          </button>
        </section>
        {fallback}
      </section>
    );
  }

  const tradeCumulus = loadState.worlds[0];
  return (
    <section className="worlds-home" aria-labelledby="cloud-worlds-title">
      <WorldsHeading />
      {tradeCumulus ? (
        <article className="world-card" aria-labelledby="trade-cumulus-world-title">
          <div className="world-card-main">
            <div className="world-card-heading">
              <div>
                <p className="eyebrow">Installed World</p>
                <h2 id="trade-cumulus-world-title">{tradeCumulus.display_name}</h2>
              </div>
              {tradeCumulus.availability_state !== "available" && (
                <span className={`world-availability ${tradeCumulus.availability_state}`}>
                  {availabilityLabel(tradeCumulus.availability_state)}
                </span>
              )}
            </div>
            <p className="world-description">{tradeCumulus.short_description}</p>
            {tradeCumulus.availability_state !== "available" && (
              <p className="world-availability-message">{tradeCumulus.availability_message}</p>
            )}
          </div>

          <dl className="world-card-metrics">
            <div>
              <dt>Reference</dt>
              <dd>{tradeCumulus.reference_available ? "Canonical BOMEX" : "Unavailable"}</dd>
            </div>
            <div>
              <dt>Simulations</dt>
              <dd>{tradeCumulus.simulation_count}</dd>
            </div>
            <div>
              <dt>Comparisons</dt>
              <dd>{tradeCumulus.saved_comparison_count}</dd>
            </div>
            <div>
              <dt>Lab</dt>
              <dd>{labSummary(tradeCumulus)}</dd>
            </div>
          </dl>

          <div className="world-card-action">
            <button type="button" onClick={onEnterTradeCumulus}>
              Enter Trade Cumulus
            </button>
          </div>
        </article>
      ) : (
        <section className="status-panel">
          <p>No Cloud Worlds are installed.</p>
        </section>
      )}
    </section>
  );
}

function WorldsHeading() {
  return (
    <header className="worlds-heading">
      <h2 id="cloud-worlds-title">Cloud Worlds</h2>
    </header>
  );
}

function availabilityLabel(state: CloudWorldSummary["availability_state"]): string {
  return {
    available: "Available",
    partial: "Partially available",
    unavailable: "Unavailable",
    conflict: "Identity conflict",
  }[state];
}

function labSummary(world: CloudWorldSummary): string {
  if (world.active_run_count > 0) {
    return `${world.active_run_count} active`;
  }
  if (world.completed_uninspected_run_count > 0) {
    return `${world.completed_uninspected_run_count} awaiting inspection`;
  }
  return "Idle";
}

function validateWorldSummaries(payload: unknown): CloudWorldSummary[] {
  if (!Array.isArray(payload) || payload.length !== 1 || !isWorldSummary(payload[0])) {
    throw new Error("Cloud Worlds response does not match the required contract.");
  }
  return payload;
}

function isWorldSummary(value: unknown): value is CloudWorldSummary {
  if (!isRecord(value)) return false;
  return (
    value.world_id === "trade_cumulus" &&
    value.display_name === "Trade Cumulus" &&
    value.status === "mvp_candidate" &&
    typeof value.short_description === "string" &&
    value.reference_simulation_id === "trade_cumulus_canonical_bomex" &&
    typeof value.reference_available === "boolean" &&
    isNonnegativeNumber(value.simulation_count) &&
    value.saved_view_count === 0 &&
    isNonnegativeNumber(value.saved_comparison_count) &&
    isNonnegativeNumber(value.featured_comparison_count) &&
    isNonnegativeNumber(value.active_run_count) &&
    isNonnegativeNumber(value.completed_uninspected_run_count) &&
    ["available", "partial", "unavailable", "conflict"].includes(
      String(value.availability_state),
    ) &&
    typeof value.availability_message === "string"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonnegativeNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
