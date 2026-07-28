import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LifecycleWorkspace, type LifecycleRecord } from "./LifecycleWorkspace";

const relationshipAttempts: LifecycleRecord["attempts"] = [
  attempt("run-initial", "initial", true),
  attempt("run-retry", "unchanged_retry"),
  attempt("run-restart", "checkpoint_restart"),
  attempt("run-observation", "alternate_observation_attempt"),
  attempt("run-extension", "extension"),
  attempt("run-backing", "later_backing_candidate"),
];

const records: LifecycleRecord[] = [
  record({
    record_id: "simulation:mountain_waves_broader_boulder_ridge",
    owner_id: "mountain_waves",
    owner_label: "Mountain Waves",
    simulation_id: "mountain_waves_broader_boulder_ridge",
    display_name: "Broader Boulder Ridge",
    question: "How does broader terrain change the wave cloud?",
    parent_simulation_id: "mountain_waves_boulder_windstorm",
    activity_group: "available_with_caveats",
    lifecycle_label: "Available with caveats",
    lifecycle_detail: "Inspectable output is retained with a visible caveat.",
    trust_state: "caveated",
    caveats: ["Runtime integrity is caveated."],
    tags: ["terrain"],
    differences: [
      {
        category: "terrain",
        label: "Terrain half width",
        before: 10,
        after: 18,
        units: "km",
        material: true,
      },
    ],
    attempts: relationshipAttempts,
    facts: facts({
      simulation_availability: "present",
      parent_eligibility: "eligible",
      retained_assets: "present",
      technical_integrity: "caveated",
    }),
    actions: [
      action("explore", { result_id: "result-broader" }),
      action("compare_parent", {
        target_simulation_id: "mountain_waves_boulder_windstorm",
      }),
    ],
  }),
  record({
    record_id: "experiment:sounding-queued",
    owner_id: "fun_with_soundings",
    owner_label: "Fun With Soundings",
    record_kind: "experiment",
    experiment_id: "sounding-queued",
    simulation_id: null,
    world_id: null,
    display_name: "Topeka surface-forced evolution",
    question: "Will the observed atmosphere sustain deep convection?",
    activity_group: "queued",
    lifecycle_label: "Queued",
    lifecycle_detail: "Waiting for local execution.",
    facts: facts({ queue: "pending", attempt: "present", retained_assets: "present" }),
    actions: [
      action("cancel", { run_id: "run-sounding" }),
      action("open_run_controls", { run_id: "run-sounding" }),
    ],
  }),
  record({
    record_id: "experiment:failed",
    owner_id: "legacy_unassigned",
    owner_label: "Legacy / unassigned",
    record_kind: "experiment",
    experiment_id: "failed",
    simulation_id: null,
    world_id: null,
    display_name: "Ambiguous legacy attempt",
    activity_group: "needs_attention",
    lifecycle_label: "Failed",
    lifecycle_detail: "CM1 exited before expected output was complete.",
    trust_state: "failed",
    facts: facts({
      process: "failed",
      expected_output: "missing",
      retained_assets: "missing",
    }),
    actions: [action("review")],
  }),
  record({
    record_id: "simulation:trade-cumulus",
    owner_id: "trade_cumulus",
    owner_label: "Trade Cumulus",
    simulation_id: "trade_cumulus_canonical_bomex",
    display_name: "Canonical BOMEX Baseline",
    activity_group: "recently_completed",
    lifecycle_label: "Available",
    lifecycle_detail: "Available in Trade Cumulus.",
    trust_state: "trusted",
    facts: facts({
      simulation_availability: "present",
      parent_eligibility: "eligible",
      retained_assets: "present",
    }),
    actions: [action("explore", { result_id: "result-bomex" })],
  }),
];

describe("LifecycleWorkspace", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input) === "/api/lifecycle") return okProjection(records);
        if (String(input) === "/api/runs/cancel") return ok({ message: "Canceled" });
        throw new Error(`Unexpected fetch ${String(input)}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("groups actionable work by owner and exposes every attempt relationship on demand", async () => {
    const onExplore = vi.fn();
    const onCompare = vi.fn();
    render(
      <LifecycleWorkspace
        ownerIds={["mountain_waves"]}
        onExplore={onExplore}
        onCompare={onCompare}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Available with caveats" }),
    ).toBeInTheDocument();
    const card = screen.getByRole("heading", { name: "Broader Boulder Ridge" }).closest("article");
    expect(card).not.toBeNull();
    if (!card) return;
    expect(card).toHaveTextContent("Broader Boulder Ridge");
    expect(card).toHaveTextContent("Terrain half width");
    expect(card).toHaveTextContent("10 km to 18 km");
    expect(card).toHaveTextContent("Variation parent: Eligible");

    fireEvent.click(within(card).getByRole("button", { name: "Explore" }));
    expect(onExplore).toHaveBeenCalledWith(
      expect.objectContaining({ record_id: records[0].record_id }),
    );
    fireEvent.click(within(card).getByRole("button", { name: "Compare to parent" }));
    expect(onCompare).toHaveBeenCalledWith(
      expect.objectContaining({ record_id: records[0].record_id }),
      "mountain_waves_boulder_windstorm",
    );

    fireEvent.click(within(card).getByText("Technical details"));
    for (const label of [
      "Initial attempt",
      "Unchanged retry",
      "Checkpoint restart",
      "Alternate observation attempt",
      "Extension",
      "Later backing candidate",
    ]) {
      expect(within(card).getByText(label)).toBeInTheDocument();
    }
    expect(within(card).getByText("Backing output")).toBeInTheDocument();
  });

  it("keeps History owner-aware and supports practical search and trust filters", async () => {
    render(
      <LifecycleWorkspace
        ownerIds={["fun_with_soundings", "legacy_unassigned"]}
        view="history"
        onExplore={vi.fn()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Retained scientific work" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Topeka surface-forced evolution")).toBeInTheDocument();
    expect(screen.getByText("Ambiguous legacy attempt")).toBeInTheDocument();
    expect(screen.queryByText("Canonical BOMEX Baseline")).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "Topeka" } });
    expect(screen.getByText("Topeka surface-forced evolution")).toBeInTheDocument();
    expect(screen.queryByText("Ambiguous legacy attempt")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("More filters"));
    fireEvent.change(screen.getByLabelText("Trust"), { target: { value: "failed" } });
    expect(screen.queryByText("Topeka surface-forced evolution")).not.toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Clear filters" })[0]);
    expect(screen.getByText("Ambiguous legacy attempt")).toBeInTheDocument();
  });

  it("executes a direct lifecycle action and refreshes from backend state", async () => {
    render(
      <LifecycleWorkspace
        ownerIds={["fun_with_soundings"]}
        onExplore={vi.fn()}
        onOpenRunControls={vi.fn()}
      />,
    );
    const cancel = await screen.findByRole("button", { name: "Cancel" });
    fireEvent.click(cancel);
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/runs/cancel", { method: "POST" }));
    expect(await screen.findByText("Cancel completed.")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/lifecycle");
  });

  it("recovers from a failed projection read and reloads persisted backend state", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(errorResponse("Lifecycle unavailable"))
      .mockResolvedValueOnce(okProjection([records[3]]));
    const { unmount } = render(
      <LifecycleWorkspace ownerIds={["trade_cumulus"]} onExplore={vi.fn()} />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("Lifecycle unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Canonical BOMEX Baseline")).toBeInTheDocument();

    unmount();
    render(<LifecycleWorkspace ownerIds={["trade_cumulus"]} onExplore={vi.fn()} />);
    expect(await screen.findByText("Canonical BOMEX Baseline")).toBeInTheDocument();
  });
});

function record(overrides: Partial<LifecycleRecord>): LifecycleRecord {
  return {
    record_id: "simulation:default",
    record_kind: "simulation",
    owner_id: "trade_cumulus",
    owner_label: "Trade Cumulus",
    simulation_id: "simulation-default",
    experiment_id: null,
    world_id: "trade_cumulus",
    recipe_id: "recipe",
    recipe_version: "1",
    parent_simulation_id: null,
    reference_simulation_id: null,
    display_name: "Simulation",
    question: null,
    role: "variation",
    case_id: "case",
    differences: [],
    attempts: [attempt("run-default", "initial", true)],
    facts: facts(),
    trust_state: "unassessed",
    caveats: [],
    tags: [],
    notes: null,
    lifecycle_label: "Ready",
    lifecycle_detail: "Ready.",
    activity_group: "ready_to_run",
    in_activity: true,
    created_at: "2026-07-20T12:00:00Z",
    updated_at: "2026-07-27T12:00:00Z",
    size_bytes: 1_024,
    dependencies: [],
    actions: [],
    ...overrides,
  };
}

function facts(overrides: Partial<LifecycleRecord["facts"]> = {}): LifecycleRecord["facts"] {
  return {
    scientific_work: "present",
    package: "present",
    attempt: "present",
    queue: "not_applicable",
    process: "not_applicable",
    expected_output: "unknown",
    technical_integrity: "unknown",
    ingest: "unknown",
    world_inspectability: "unknown",
    simulation_availability: "unknown",
    parent_eligibility: "not_applicable",
    retained_assets: "unknown",
    ...overrides,
  };
}

function attempt(
  runId: string,
  relationship: LifecycleRecord["attempts"][number]["relationship"],
  acceptedBacking = false,
): LifecycleRecord["attempts"][number] {
  return {
    attempt_id: `attempt:${runId}`,
    run_id: runId,
    relationship,
    accepted_backing: acceptedBacking,
    manifest_path: `/runs/${runId}/run_manifest.json`,
    lifecycle_state: "completed",
    queue_state: null,
    product_state: "available",
    validation_status: "passed",
    result_id: `result:${runId}`,
    output_artifact_count: 12,
    size_bytes: 1_024,
    retained_state: "retained",
    created_at: "2026-07-20T12:00:00Z",
    started_at: "2026-07-20T12:01:00Z",
    finished_at: "2026-07-20T12:20:00Z",
    updated_at: "2026-07-20T12:20:00Z",
    message: null,
    failure_reason: null,
  };
}

function action(
  kind: LifecycleRecord["actions"][number]["kind"],
  overrides: Partial<LifecycleRecord["actions"][number]> = {},
): LifecycleRecord["actions"][number] {
  return {
    kind,
    label: {
      run: "Run",
      cancel: "Cancel",
      ingest: "Ingest",
      explore: "Explore",
      compare_parent: "Compare to parent",
      compare_reference: "Compare to reference",
      review: "Review",
      open_run_controls: "Open run controls",
    }[kind],
    run_id: null,
    manifest_path: null,
    result_id: null,
    world_id: null,
    simulation_id: null,
    target_simulation_id: null,
    ...overrides,
  };
}

function okProjection(projectionRecords: LifecycleRecord[]): Response {
  return {
    ok: true,
    json: async () => ({
      schema_version: "1",
      generated_at: "2026-07-27T12:00:00Z",
      records: projectionRecords,
      warnings: [],
    }),
  } as Response;
}

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

function errorResponse(detail: string): Response {
  return { ok: false, json: async () => ({ detail }) } as Response;
}
