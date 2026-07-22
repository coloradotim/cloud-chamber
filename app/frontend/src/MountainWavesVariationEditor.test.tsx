import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MountainWavesVariationEditor } from "./MountainWavesVariationEditor";
import type { MountainWavesWorldDetail } from "./MountainWavesWorld";

const configuration = {
  terrain: { height_m: 1_000, half_width_m: 10_000, center_m: 0 },
  sounding: [
    { height_m: 0, pressure_pa: 100_000, theta_k: 288, qv_g_kg: 5, u_m_s: 10, v_m_s: 0 },
    { height_m: 1_000, pressure_pa: 90_000, theta_k: 292, qv_g_kg: 4, u_m_s: 12, v_m_s: 0 },
    { height_m: 2_000, pressure_pa: 80_000, theta_k: 296, qv_g_kg: 3, u_m_s: 14, v_m_s: 0 },
  ],
  duration_seconds: 3_600,
  output_cadence_seconds: 180,
};

const world = {
  world_id: "mountain_waves",
  display_name: "Mountain Waves",
  short_description: "Mountain waves",
  availability_state: "available",
  availability_message: "Available",
  default_parent_simulation_id: "mountain_waves_boulder_moist_reference",
  simulations: [
    {
      simulation_id: "mountain_waves_boulder_moist_reference",
      display_name: "Boulder Windstorm",
      role: "built_in",
      world_id: "mountain_waves",
      run_id: "parent-run",
      case_id: "parent-case",
      parent_simulation_id: null,
      parent_run_id: null,
      reference_simulation_id: "mountain_waves_boulder_moist_reference",
      user_question: null,
      state: "available",
      state_message: "Available",
      inspectable: true,
      can_create_variation: true,
      moist: true,
      moist_fields_available: true,
      purpose: "Reference",
      configuration: null,
      differences: {},
      warnings: [],
      caveats: [],
      manifest_path: "/parent/manifest.json",
      created_at: null,
      started_at: null,
      completed_at: null,
    },
  ],
  activity: [],
  history: [],
  lab_summary: {
    active_run_count: 0,
    packaged_run_count: 0,
    completed_simulation_count: 1,
    failed_run_count: 0,
    total_variation_count: 0,
  },
  caveats: [],
} satisfies MountainWavesWorldDetail;

describe("MountainWavesVariationEditor", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("variation-template")) {
          return ok({
            parent_simulation_id: world.default_parent_simulation_id,
            parent_run_id: "parent-run",
            parent_display_name: "Boulder Windstorm",
            parent_configuration_source: "retained_exact_sounding",
            reference_simulation_id: world.default_parent_simulation_id,
            configuration,
            can_create_variation: true,
            unavailable_reason: null,
          });
        }
        if (url.endsWith("/variations/preview")) {
          const body = JSON.parse(String(init?.body));
          return ok({
            differences: {
              terrain:
                body.configuration.terrain.height_m === 1_200
                  ? [{ label: "Ridge height", before: 1_000, after: 1_200, units: "m" }]
                  : [],
              wind: [],
              moisture: [],
              "stability/thermodynamics": [],
              "numerics/time": [],
              output: [],
            },
            warnings: [],
            blocking_errors: [],
            derived_stability_n2_s2: [0.00013, 0.00012],
            terrain_profile: [
              { x_m: -10_000, height_m: 100 },
              { x_m: 0, height_m: body.configuration.terrain.height_m },
              { x_m: 10_000, height_m: 100 },
            ],
          });
        }
        if (url.endsWith("/variations")) {
          return ok({
            simulation_id: "mountain_waves_broader_ridge_1234",
            run_id: "run-variation",
            manifest_path: "/runs/variation/manifest.json",
            package_dir: "/runs/variation",
            differences: {},
            warnings: [],
            preflight: { passed: true },
          });
        }
        if (url === "/api/runs/queue") return ok({ state: "queued" });
        throw new Error(`Unexpected fetch ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("previews exact physical changes and queues only on the explicit action", async () => {
    const onCreated = vi.fn();
    render(
      <MountainWavesVariationEditor
        world={world}
        initialParentSimulationId={world.default_parent_simulation_id}
        onCreated={onCreated}
      />,
    );

    expect(await screen.findByRole("heading", { name: /Change the terrain/ })).toBeInTheDocument();
    await screen.findByText("0 exact changes");
    fireEvent.change(screen.getByLabelText("Height"), { target: { value: "1200" } });
    expect(await screen.findByText("1 exact changes")).toBeInTheDocument();
    expect(screen.getByText("Ridge height")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Variation name"), {
      target: { value: "Broader ridge" },
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Create and queue" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Create and queue" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(fetch).toHaveBeenCalledWith(
      "/api/runs/queue",
      expect.objectContaining({
        body: JSON.stringify({ manifest_path: "/runs/variation/manifest.json" }),
      }),
    );
  });
});

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}
