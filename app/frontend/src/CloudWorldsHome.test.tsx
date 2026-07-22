import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CloudWorldsHome, type CloudWorldSummary } from "./CloudWorldsHome";

const summary: CloudWorldSummary = {
  world_id: "trade_cumulus",
  display_name: "Trade Cumulus",
  status: "mvp_candidate",
  short_description: "Investigate shallow maritime cumulus and its response to surface moisture.",
  reference_simulation_id: "trade_cumulus_canonical_bomex",
  reference_available: true,
  simulation_count: 2,
  saved_view_count: 0,
  saved_comparison_count: 1,
  featured_comparison_count: 1,
  active_run_count: 0,
  completed_uninspected_run_count: 2,
  availability_state: "available",
  availability_message: "Reference, variation, and featured comparison are available.",
};

const mountainWavesSummary: CloudWorldSummary = {
  world_id: "mountain_waves",
  display_name: "Mountain Waves",
  short_description: "Investigate terrain-forced waves and the clouds they organize.",
  reference_simulation_id: "mountain_waves_boulder_moist_reference",
  reference_available: true,
  simulation_count: 2,
  saved_view_count: 0,
  saved_comparison_count: 0,
  featured_comparison_count: 0,
  active_run_count: 0,
  completed_uninspected_run_count: 0,
  availability_state: "available",
  availability_message: "Dry Ridge and Boulder Windstorm are available.",
};

describe("CloudWorldsHome", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("presents both Cloud Worlds as peer entrances", async () => {
    vi.mocked(fetch).mockResolvedValue(ok([summary, mountainWavesSummary]));
    const onEnterTradeCumulus = vi.fn();
    const onEnterMountainWaves = vi.fn();
    render(
      <CloudWorldsHome
        onEnterTradeCumulus={onEnterTradeCumulus}
        onEnterMountainWaves={onEnterMountainWaves}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Trade Cumulus" })).toBeInTheDocument();
    expect(screen.getByText(summary.short_description)).toBeInTheDocument();
    expect(screen.getByText("2 awaiting inspection")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Mountain Waves" })).toBeInTheDocument();
    expect(screen.getByText(mountainWavesSummary.short_description)).toBeInTheDocument();
    expect(screen.getByText("Boulder Windstorm")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Enter Trade Cumulus" }));
    fireEvent.click(screen.getByRole("button", { name: "Enter Mountain Waves" }));
    expect(onEnterTradeCumulus).toHaveBeenCalledOnce();
    expect(onEnterMountainWaves).toHaveBeenCalledOnce();
  });

  it("shows bounded partial availability", async () => {
    vi.mocked(fetch).mockResolvedValue(
      ok([
        {
          ...summary,
          reference_available: false,
          availability_state: "partial",
          availability_message: "Canonical BOMEX Baseline is missing.",
        },
      ]),
    );
    render(<CloudWorldsHome onEnterTradeCumulus={vi.fn()} onEnterMountainWaves={vi.fn()} />);

    expect(await screen.findByText("Partially available")).toBeInTheDocument();
    expect(screen.getByText("Canonical BOMEX Baseline is missing.")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("keeps the existing application available and retries a failed request", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(error(500, "World inventory unavailable."))
      .mockResolvedValueOnce(ok([summary]));
    render(
      <CloudWorldsHome
        onEnterTradeCumulus={vi.fn()}
        onEnterMountainWaves={vi.fn()}
        fallback={<div>Existing application remains available</div>}
      />,
    );

    expect(await screen.findByText("World inventory unavailable.")).toBeInTheDocument();
    expect(screen.getByText("Existing application remains available")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry Worlds" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("heading", { name: "Trade Cumulus" })).toBeInTheDocument();
  });
});

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

function error(status: number, detail: string): Response {
  return { ok: false, status, json: async () => ({ detail }) } as Response;
}
