import { type ReactNode, useCallback, useEffect, useState } from "react";

export type TradeCumulusWorldSummary = {
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

export type MountainWavesWorldSummary = {
  world_id: "mountain_waves";
  display_name: "Mountain Waves";
  short_description: string;
  reference_simulation_id: "mountain_waves_boulder_moist_reference";
  reference_available: boolean;
  simulation_count: number;
  saved_view_count: 0;
  saved_comparison_count: 0;
  featured_comparison_count: 0;
  active_run_count: number;
  completed_uninspected_run_count: number;
  availability_state: "available" | "partial" | "unavailable" | "conflict";
  availability_message: string;
};

export type CloudWorldSummary = TradeCumulusWorldSummary | MountainWavesWorldSummary;

type LoadState =
  | { status: "loading"; worlds: CloudWorldSummary[]; error: null }
  | { status: "loaded"; worlds: CloudWorldSummary[]; error: null }
  | { status: "failed"; worlds: []; error: string };

export function CloudWorldsHome({
  onEnterTradeCumulus,
  onEnterMountainWaves,
  fallback,
}: {
  onEnterTradeCumulus: () => void;
  onEnterMountainWaves: () => void;
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

  return (
    <section className="worlds-home" aria-labelledby="cloud-worlds-title">
      <WorldsHeading />
      {loadState.worlds.length > 0 ? (
        <div className="world-card-list">
          {loadState.worlds.map((world) => (
            <WorldCard
              key={world.world_id}
              world={world}
              onEnter={
                world.world_id === "trade_cumulus" ? onEnterTradeCumulus : onEnterMountainWaves
              }
            />
          ))}
        </div>
      ) : (
        <section className="status-panel">
          <p>No Cloud Worlds are installed.</p>
        </section>
      )}
    </section>
  );
}

function WorldCard({ world, onEnter }: { world: CloudWorldSummary; onEnter: () => void }) {
  const titleId = `${world.world_id}-world-title`;
  return (
    <article className="world-card" aria-labelledby={titleId}>
      <div className="world-card-main">
        <div className="world-card-heading">
          <div>
            <p className="eyebrow">Cloud World</p>
            <h2 id={titleId}>{world.display_name}</h2>
          </div>
          {world.availability_state !== "available" && (
            <span className={`world-availability ${world.availability_state}`}>
              {availabilityLabel(world.availability_state)}
            </span>
          )}
        </div>
        <p className="world-description">{world.short_description}</p>
        {world.availability_state !== "available" && (
          <p className="world-availability-message">{world.availability_message}</p>
        )}
      </div>

      <dl className="world-card-metrics">
        <div>
          <dt>Reference</dt>
          <dd>{referenceLabel(world)}</dd>
        </div>
        <div>
          <dt>Simulations</dt>
          <dd>{world.simulation_count}</dd>
        </div>
        <div>
          <dt>Comparisons</dt>
          <dd>{world.saved_comparison_count}</dd>
        </div>
        <div>
          <dt>Lab</dt>
          <dd>{labSummary(world)}</dd>
        </div>
      </dl>

      <div className="world-card-action">
        <button type="button" onClick={onEnter}>
          Enter {world.display_name}
        </button>
      </div>
    </article>
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

function referenceLabel(world: CloudWorldSummary): string {
  if (!world.reference_available) return "Unavailable";
  return world.world_id === "trade_cumulus" ? "Canonical BOMEX" : "Boulder Windstorm";
}

function validateWorldSummaries(payload: unknown): CloudWorldSummary[] {
  if (!Array.isArray(payload) || payload.length === 0 || !payload.every(isWorldSummary)) {
    throw new Error("Cloud Worlds response does not match the required contract.");
  }
  return payload;
}

function isWorldSummary(value: unknown): value is CloudWorldSummary {
  if (!isRecord(value)) return false;
  if (value.world_id === "mountain_waves") {
    return (
      value.display_name === "Mountain Waves" &&
      typeof value.short_description === "string" &&
      value.reference_simulation_id === "mountain_waves_boulder_moist_reference" &&
      typeof value.reference_available === "boolean" &&
      isNonnegativeNumber(value.simulation_count) &&
      value.saved_view_count === 0 &&
      value.saved_comparison_count === 0 &&
      value.featured_comparison_count === 0 &&
      isNonnegativeNumber(value.active_run_count) &&
      isNonnegativeNumber(value.completed_uninspected_run_count) &&
      ["available", "partial", "unavailable", "conflict"].includes(
        String(value.availability_state),
      ) &&
      typeof value.availability_message === "string"
    );
  }
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
