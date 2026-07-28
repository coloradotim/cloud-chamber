import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StorageWorkspace } from "./StorageWorkspace";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("StorageWorkspace", () => {
  it("summarizes retained assets, filters them, and exposes no destructive action", async () => {
    vi.stubGlobal("fetch", storageFetch());

    render(<StorageWorkspace />);

    expect(await screen.findByRole("heading", { name: "Storage" })).toBeVisible();
    expect(screen.getAllByText("12 GB").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Canonical BOMEX Baseline" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Boulder Windstorm" })).toBeVisible();
    expect(screen.queryByRole("button", { name: /delete|remove|clean/i })).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox", { name: "Search" }), {
      target: { value: "Boulder" },
    });
    expect(
      screen.queryByRole("heading", { name: "Canonical BOMEX Baseline" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Boulder Windstorm" })).toBeVisible();
    expect(screen.getByText("1 of 2")).toBeVisible();
  });

  it("records an immutable review and runs the immediate prelaunch check", async () => {
    const fetchMock = storageFetch();
    vi.stubGlobal("fetch", fetchMock);

    render(<StorageWorkspace />);

    await screen.findByRole("heading", { name: "Launch budget" });
    fireEvent.click(screen.getByRole("button", { name: "Record launch review" }));
    await waitFor(() => expect(screen.getByText(/Snapshot abcdef12/)).toBeVisible());
    fireEvent.click(screen.getByRole("button", { name: "Recheck before launch" }));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Launch budget passes at immediate prelaunch.",
      ),
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/storage/launch-reviews",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/storage/launch-reviews/preflight",
      expect.objectContaining({ method: "POST" }),
    );
  });
});

function storageFetch() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.startsWith("/api/storage/assets")) return ok(inventory());
    if (url === "/api/storage/run-cost-profiles") {
      return ok({ schema_version: "1", estimates: [estimate()] });
    }
    if (url === "/api/storage/launch-reviews" && init?.method === "POST") {
      return ok(review(false));
    }
    if (url === "/api/storage/launch-reviews/preflight" && init?.method === "POST") {
      return ok(review(true));
    }
    return new Response(JSON.stringify({ detail: `Unhandled fixture request: ${url}` }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  });
}

function inventory() {
  return {
    schema_version: "1",
    generated_at: "2026-07-28T12:00:00Z",
    runtime_home: "/Volumes/ExternalHDD/CloudChamber",
    total_usage_bytes: 12 * 1024 ** 3,
    free_space_bytes: 300 * 1024 ** 3,
    system_protected_bytes: 10 * 1024 ** 3,
    ordinary_retained_bytes: 2 * 1024 ** 3,
    temporary_bytes: 0,
    uncounted_asset_count: 0,
    warning_threshold_bytes: 50 * 1024 ** 3,
    minimum_free_space_bytes: 2 * 1024 ** 3,
    above_usage_warning: false,
    below_minimum_free_space: false,
    usage_by_owner: [
      {
        id: "trade_cumulus",
        label: "Trade Cumulus",
        size_bytes: 10 * 1024 ** 3,
        asset_count: 1,
      },
      {
        id: "mountain_waves",
        label: "Mountain Waves",
        size_bytes: 2 * 1024 ** 3,
        asset_count: 1,
      },
    ],
    usage_by_class: [
      {
        id: "simulation_output",
        label: "Simulation output",
        size_bytes: 12 * 1024 ** 3,
        asset_count: 2,
      },
    ],
    state_counts: { protected: 2 },
    assets: [
      asset({
        asset_id: "run:trade",
        stable_name: "Canonical BOMEX Baseline",
        owner_id: "trade_cumulus",
        owner_label: "Trade Cumulus",
        size_bytes: 10 * 1024 ** 3,
      }),
      asset({
        asset_id: "run:mountain",
        stable_name: "Boulder Windstorm",
        owner_id: "mountain_waves",
        owner_label: "Mountain Waves",
        size_bytes: 2 * 1024 ** 3,
      }),
    ],
    performance: {
      cache_hit: true,
      scan_duration_ms: 0,
      scanned_file_count: 0,
      fingerprint: "fixture",
    },
    warnings: [],
  };
}

function asset(overrides: Record<string, unknown>) {
  return {
    asset_id: "run:fixture",
    stable_name: "Fixture",
    owner_id: "trade_cumulus",
    owner_label: "Trade Cumulus",
    asset_class: "simulation_output",
    lifecycle_role: "reference",
    world_id: "trade_cumulus",
    simulation_id: "fixture",
    experiment_id: null,
    recipe_id: "fixture_recipe",
    recipe_version: "1",
    parent_simulation_id: null,
    reference_simulation_id: "fixture",
    attempt_id: "fixture",
    run_id: "fixture",
    result_id: "result-fixture",
    case_id: "fixture",
    question: "How does this retained atmosphere evolve?",
    tags: ["built-in"],
    technical_path: "/runtime/runs/fixture",
    size_bytes: 1,
    components: [{ component: "model output", size_bytes: 1, file_count: 1 }],
    created_at: "2026-07-28T10:00:00Z",
    modified_at: "2026-07-28T11:00:00Z",
    last_used_at: null,
    built_in: true,
    accepted_backing: "accepted",
    availability_state: "retained",
    protection_state: "system_protected",
    repairability_state: "unknown",
    trust_state: "trusted",
    caveats: [],
    recreation_method: null,
    dependencies: [],
    required_for_explore: true,
    required_for_compare: false,
    required_for_parent_reuse: false,
    required_for_repair: false,
    ...overrides,
  };
}

function estimate() {
  return {
    profile: {
      schema_version: "1",
      world_id: "trade_cumulus",
      world_name: "Trade Cumulus",
      recipe_id: "canonical_bomex_trade_cumulus",
      recipe_version: "1",
      profile_id: "trade_cumulus_quick_v1",
      profile_name: "Quick — Three-hour field response",
      role: "Quick",
      numerical_realization: {
        domain: "6.4 × 6.4 × 3 km",
        grid: "64 × 64 × 75",
        spacing: "100 × 100 × 40 m",
        timestep_strategy: "target 3 s",
        physics_source: "Approved World contract",
      },
      observation_plan: {
        duration_seconds: 10_800,
        output_cadence_seconds: 180,
        diagnostic_cadence_seconds: null,
        expected_history_count: 61,
        retained_field_inventory: "World-required fields",
      },
      expected_runtime_min_seconds: 600,
      expected_runtime_max_seconds: 1200,
      expected_size_min_bytes: 800 * 1024 ** 2,
      expected_size_max_bytes: 1100 * 1024 ** 2,
      estimate_basis: "scaled_from_measured",
      confidence: "Scaled from measured six-hour lower-resolution runs.",
      cost_change_reasons: [],
      scientific_limitations: ["Early response."],
      required_post_run_reserve_bytes: 2 * 1024 ** 3,
    },
    current_free_space_bytes: 300 * 1024 ** 3,
    projected_free_space_bytes: 298.9 * 1024 ** 3,
    required_free_space_bytes: 3.1 * 1024 ** 3,
    disposition: "passes",
    disposition_reason:
      "The high retained-size estimate fits while preserving the required safety margin.",
  };
}

function review(checked: boolean) {
  return {
    snapshot: {
      snapshot_id: "abcdef1234567890",
      created_at: "2026-07-28T12:05:00Z",
      estimate: estimate(),
      review_free_space_bytes: 300 * 1024 ** 3,
      warning_threshold_bytes: 50 * 1024 ** 3,
      minimum_free_space_bytes: 2 * 1024 ** 3,
    },
    immediate_prelaunch_checks: checked
      ? [
          {
            check_id: "check-1",
            snapshot_id: "abcdef1234567890",
            checked_at: "2026-07-28T12:06:00Z",
            current_free_space_bytes: 300 * 1024 ** 3,
            expected_size_high_bytes: 1100 * 1024 ** 2,
            required_post_run_reserve_bytes: 2 * 1024 ** 3,
            projected_free_space_bytes: 298.9 * 1024 ** 3,
            disposition: "passes",
            reason: "Launch budget passes at immediate prelaunch.",
          },
        ]
      : [],
  };
}

function ok(payload: unknown) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
