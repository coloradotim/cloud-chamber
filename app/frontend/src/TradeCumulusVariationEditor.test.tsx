import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TradeCumulusVariationEditor } from "./TradeCumulusVariationEditor";
import type { SimulationRecord, TradeCumulusWorldDetail } from "./TradeCumulusWorld";

const referenceControls = {
  surface_sensible_heat_flux_k_m_s: 0.008,
  surface_moisture_flux_g_kg_m_s: 0.052,
  sub_inversion_total_water_g_kg: 16.65,
  inversion_base_m_agl: 520,
  inversion_thickness_m: 960,
  inversion_strength_k: 3.7,
  free_tropospheric_rh_percent: 41,
  cloud_layer_shear_m_s: 4.14,
  cloud_layer_shear_direction_deg: 0,
  cloud_layer_mean_u_m_s: -7.5,
  cloud_layer_mean_v_m_s: 0,
  large_scale_vertical_motion_m_s: -0.0065,
  temperature_tendency_k_day: -2,
  total_water_tendency_g_kg_day: -1.0368,
};

const baseline = simulation({
  simulation_id: "trade_cumulus_canonical_bomex",
  display_name: "Canonical BOMEX Baseline",
  role: "reference",
  run_id: "baseline-run",
  result_id: "baseline-result",
  can_create_variation: true,
});

const moreMoisture = simulation({
  simulation_id: "trade_cumulus_more_moisture",
  display_name: "More Moisture",
  run_id: "more-run",
  result_id: "more-result",
  parent_simulation_id: baseline.simulation_id,
  can_create_variation: true,
});

const world: TradeCumulusWorldDetail = {
  world_id: "trade_cumulus",
  display_name: "Trade Cumulus",
  status: "mvp_candidate",
  short_description: "Trade cumulus",
  availability_state: "available",
  availability_message: "Available",
  reference_simulation: baseline,
  simulations: [baseline, moreMoisture],
  lab_history: [],
  featured_comparison: {
    comparison_id: "trade_cumulus_moisture_v1",
    display_name: "More Moisture versus Baseline",
    baseline_simulation_id: "trade_cumulus_canonical_bomex",
    more_moisture_simulation_id: "trade_cumulus_more_moisture",
    availability_state: "available",
    availability_message: "Available",
    open_available: true,
  },
  lab_summary: {
    active_run_count: 0,
    completed_uninspected_run_count: 0,
    lab_history_count: 0,
    summary: "Idle",
  },
  capabilities: {
    reference_explore: true,
    featured_comparison: true,
    lab: true,
    saved_views: false,
    ordinary_compare: true,
    saved_comparisons: true,
  },
  caveats: [],
};

describe("TradeCumulusVariationEditor", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("variation-template")) {
          const more = url.includes("trade_cumulus_more_moisture");
          return ok(template(more));
        }
        if (url.endsWith("/variations/preview")) {
          const body = JSON.parse(String(init?.body));
          return ok(preview(body));
        }
        if (url.endsWith("/variations")) {
          return ok({
            simulation_id: "trade_cumulus_direct_target_abcd1234",
            run_id: "trade-variation-run",
            manifest_path: "/runs/trade-variation-run/run_manifest.json",
            package_dir: "/runs/trade-variation-run",
            launch_review_snapshot_id: "launch-review-trade",
            warnings: [],
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

  it("shows direct values, exact reference-parent-child review, and separate queueing", async () => {
    const onCreated = vi.fn();
    render(
      <TradeCumulusVariationEditor
        world={world}
        initialParentSimulationId={baseline.simulation_id ?? ""}
        onCreated={onCreated}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Atmosphere and forcing" }),
    ).toBeInTheDocument();
    const moistureInput = screen.getByLabelText("Moisture flux exact value");
    expect(moistureInput).toHaveValue(0.052);
    expect(moistureInput.closest("label")).toHaveTextContent("g kg⁻¹ m s⁻¹");
    expect(screen.queryByText(/forcing strength/i)).not.toBeInTheDocument();
    await screen.findByText("0 material changes");

    fireEvent.change(screen.getByLabelText("Moisture flux exact value"), {
      target: { value: "0.09" },
    });
    expect(await screen.findByText("1 material changes")).toBeInTheDocument();
    const review = screen.getByLabelText("Variation review");
    expect(within(review).getByText("Reference")).toBeInTheDocument();
    expect(within(review).getByText("Parent")).toBeInTheDocument();
    expect(within(review).getByText("Child")).toBeInTheDocument();
    expect(within(review).getByText("Δ")).toBeInTheDocument();
    expect(within(review).getByText("+0.038")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Variation name"), {
      target: { value: "Direct moisture target" },
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Package variation" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Package variation" }));
    expect(
      await screen.findByText("Direct moisture target is packaged. It has not been queued."),
    ).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Queue CM1" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(fetch).toHaveBeenCalledWith(
      "/api/runs/queue",
      expect.objectContaining({
        body: JSON.stringify({
          manifest_path: "/runs/trade-variation-run/run_manifest.json",
        }),
      }),
    );
  });

  it("applies forcing shortcuts visibly and exposes advanced direct controls", async () => {
    render(
      <TradeCumulusVariationEditor
        world={world}
        initialParentSimulationId={baseline.simulation_id ?? ""}
        onCreated={vi.fn()}
      />,
    );
    await screen.findByText("0 material changes");
    fireEvent.click(screen.getByText("Advanced profile structure"));
    expect(screen.getByLabelText("Inversion thickness exact value")).toHaveValue(960);
    expect(screen.getByLabelText("Shear direction exact value")).toHaveValue(0);
    expect(screen.getByText("u -7.5 · v 0.0 m s⁻¹")).toBeInTheDocument();
    expect(screen.queryByLabelText("Layer-mean u wind exact value")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Zero forcing" }));
    expect(screen.getByLabelText("Peak vertical motion exact value")).toHaveValue(0);
    expect(screen.getByLabelText("Temperature tendency exact value")).toHaveValue(0);
    expect(screen.getByLabelText("Total-water tendency exact value")).toHaveValue(0);
    expect(await screen.findByText("3 material changes")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Restore reference forcing" }));
    expect(screen.getByLabelText("Peak vertical motion exact value")).toHaveValue(-0.0065);
    expect(await screen.findByText("0 material changes")).toBeInTheDocument();
  });

  it("switches parents without compounding the canonical Recipe transform", async () => {
    render(
      <TradeCumulusVariationEditor
        world={world}
        initialParentSimulationId={baseline.simulation_id ?? ""}
        onCreated={vi.fn()}
      />,
    );
    const parent = await screen.findByLabelText("Parent Simulation");
    fireEvent.change(parent, { target: { value: "trade_cumulus_more_moisture" } });

    const moistureInput = await screen.findByLabelText("Moisture flux exact value");
    expect(moistureInput).toHaveValue(0.078);
    expect(moistureInput.closest("label")).toHaveTextContent("Ref 0.052");
    expect(moistureInput.closest("label")).toHaveTextContent("Parent 0.078");
  });

  it("keeps unusual science launchable and blocks an impossible generated profile", async () => {
    render(
      <TradeCumulusVariationEditor
        world={world}
        initialParentSimulationId={baseline.simulation_id ?? ""}
        onCreated={vi.fn()}
      />,
    );
    await screen.findByText("0 material changes");
    fireEvent.change(screen.getByLabelText("Sensible heat flux exact value"), {
      target: { value: "-0.01" },
    });
    expect(await screen.findByText("Surface sensible heat flux is downward.")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Variation name"), {
      target: { value: "Surface cooling" },
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Package variation" })).toBeEnabled(),
    );

    fireEvent.change(screen.getByLabelText("Inversion base exact value"), {
      target: { value: "4000" },
    });
    expect(await screen.findByText(/requested inversion does not fit/i)).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("button", { name: "Package variation" })).toBeDisabled();
  });
});

function template(more: boolean) {
  const controls = {
    ...referenceControls,
    surface_moisture_flux_g_kg_m_s: more ? 0.078 : 0.052,
  };
  return {
    parent_simulation_id: more ? "trade_cumulus_more_moisture" : "trade_cumulus_canonical_bomex",
    parent_run_id: more ? "more-run" : "baseline-run",
    parent_display_name: more ? "More Moisture" : "Canonical BOMEX Baseline",
    parent_configuration_source: "Retained source-backed BOMEX atmosphere and forcing",
    reference_simulation_id: "trade_cumulus_canonical_bomex",
    recipe_id: "canonical_bomex_trade_cumulus",
    recipe_name: "Canonical BOMEX Trade Cumulus",
    recipe_contract_version: "1",
    controls,
    canonical_reference_controls: referenceControls,
    run_profiles: [
      cost("quick", "Quick", 10_800, 180, 61),
      cost("standard", "Standard", 14_400, 120, 121),
      cost("full-cycle", "Full-cycle", 21_600, 120, 181),
      cost("presentation", "Presentation", 14_400, 60, 241),
      cost("extended", "Extended", 14_400, 120, 121, true),
    ],
    default_run_profile_id: "presentation",
    can_create_variation: true,
    unavailable_reason: null,
  };
}

function cost(
  profileId: string,
  role: string,
  duration: number,
  cadence: number,
  histories: number,
  blocked = false,
) {
  return {
    profile: {
      profile_id: profileId,
      profile_name: `${role} — Trade Cumulus`,
      role,
      numerical_realization: {
        domain: "6.4 km × 6.4 km × 3 km",
        grid: "64 × 64 × 75",
        spacing: "100 × 100 × 40 m",
        timestep_strategy: "target 3 s",
        physics_source: "Canonical BOMEX",
      },
      observation_plan: {
        duration_seconds: duration,
        output_cadence_seconds: cadence,
        expected_history_count: histories,
        retained_field_inventory: ["ql", "qv", "th", "prs", "u", "v", "w"],
      },
      expected_runtime_min_seconds: blocked ? null : 600,
      expected_runtime_max_seconds: blocked ? null : 1_200,
      expected_size_min_bytes: blocked ? null : 1024 ** 3,
      expected_size_max_bytes: blocked ? null : 2 * 1024 ** 3,
      estimate_basis: blocked ? "uncharacterized" : "scaled_from_measured",
      confidence: blocked ? "Requires characterization" : "Existing evidence",
      scientific_limitations: [],
    },
    current_free_space_bytes: 100 * 1024 ** 3,
    projected_free_space_bytes: blocked ? null : 98 * 1024 ** 3,
    required_free_space_bytes: blocked ? null : 4 * 1024 ** 3,
    disposition: blocked ? "blocked" : "passes",
    disposition_reason: blocked ? "Requires characterization" : "Passes",
  };
}

function preview(body: {
  controls: typeof referenceControls;
  parent_simulation_id: string;
  run_profile_id: string;
}) {
  const parent = {
    ...referenceControls,
    surface_moisture_flux_g_kg_m_s:
      body.parent_simulation_id === "trade_cumulus_more_moisture" ? 0.078 : 0.052,
  };
  const changed = Object.entries(body.controls).filter(
    ([key, value]) => value !== parent[key as keyof typeof parent],
  );
  const impossible = body.controls.inversion_base_m_agl === 4000;
  const differences = changed.map(([key, value]) => ({
    path: `controls.${key}`,
    label:
      key === "surface_moisture_flux_g_kg_m_s"
        ? "Surface moisture flux"
        : key === "surface_sensible_heat_flux_k_m_s"
          ? "Surface sensible heat flux"
          : key.replaceAll("_", " "),
    before: parent[key as keyof typeof parent],
    after: value,
    units: null,
    material: true,
  }));
  return {
    requested_controls: body.controls,
    resolved_controls: impossible
      ? { ...body.controls, free_tropospheric_rh_percent: null }
      : body.controls,
    canonical_reference_controls: referenceControls,
    parent_controls: parent,
    differences: {
      wind: [],
      moisture: differences.filter((item) => item.path.includes("moisture_flux")),
      "stability/thermodynamics": differences.filter((item) =>
        item.path.includes("inversion_base"),
      ),
      "forcing/initiation": differences.filter(
        (item) => !item.path.includes("moisture_flux") && !item.path.includes("inversion_base"),
      ),
      "numerical realization": [],
      "observation plan": [],
    },
    relationship_classification:
      changed.length === 1
        ? "controlled_physical_variation"
        : changed.length
          ? "multi_factor_physical_variation"
          : null,
    warnings:
      body.controls.surface_sensible_heat_flux_k_m_s < 0
        ? ["Surface sensible heat flux is downward."]
        : [],
    blocking_errors: impossible ? ["The requested inversion does not fit the model top."] : [],
    diagnostics: {
      inversion_top_m_agl: body.controls.inversion_base_m_agl + 960,
      model_top_m: 3_000,
      sub_inversion_total_water_g_kg: body.controls.sub_inversion_total_water_g_kg,
      free_tropospheric_rh_percent: impossible ? null : body.controls.free_tropospheric_rh_percent,
      cloud_layer_shear_m_s: body.controls.cloud_layer_shear_m_s,
      cloud_layer_shear_direction_deg: body.controls.cloud_layer_shear_direction_deg,
      cloud_layer_mean_u_m_s: body.controls.cloud_layer_mean_u_m_s,
      cloud_layer_mean_v_m_s: body.controls.cloud_layer_mean_v_m_s,
      initial_saturated_level_count: 0,
      minimum_theta_gradient_k_km: 0,
      labels: ["Large-scale subsidence"],
    },
    sounding_profile: profile(),
    forcing_profile: profile().map((level) => ({
      height_m: level.height_m,
      vertical_motion_m_s: -0.005,
      temperature_tendency_k_day: -2,
      total_water_tendency_g_kg_day: -1,
    })),
    numerical_realization: {
      domain: "6.4 km × 6.4 km × 3 km",
      grid: "64 × 64 × 75",
      spacing: "100 × 100 × 40 m",
      timestep_strategy: "target 3 s",
      physics_source: "Canonical BOMEX",
    },
    observation_plan: {
      duration_seconds: 14_400,
      output_cadence_seconds: 60,
      expected_history_count: 241,
      retained_field_inventory: ["ql", "qv", "th", "prs", "u", "v", "w"],
    },
    cost_estimate: cost(body.run_profile_id, "Presentation", 14_400, 60, 241),
  };
}

function profile() {
  return [
    {
      height_m: 0,
      theta_l_k: 298.7,
      total_water_g_kg: 17,
      relative_humidity_percent: 60,
      u_m_s: -9,
      v_m_s: 0,
    },
    {
      height_m: 3_000,
      theta_l_k: 311,
      total_water_g_kg: 3,
      relative_humidity_percent: 41,
      u_m_s: -5,
      v_m_s: 0,
    },
  ];
}

function simulation(overrides: Partial<SimulationRecord>): SimulationRecord {
  return {
    simulation_id: "simulation",
    display_name: "Simulation",
    role: "variation",
    world_id: "trade_cumulus",
    product_slice_id: "trade_cumulus_v1",
    case_id: "bomex_trade_cumulus_baseline_v0",
    result_id: "result",
    run_id: "run",
    source_recipe_id: "canonical_bomex_trade_cumulus",
    parent_simulation_id: null,
    reference_simulation_id: "trade_cumulus_canonical_bomex",
    technical_state: "available",
    technical_state_message: "Available",
    technical_trust_state: "trusted",
    explore_available: true,
    compare_suggestions: [],
    configuration_difference_from_reference: [],
    lineage_state: "valid",
    can_create_variation: false,
    created_at: null,
    completed_at: null,
    ...overrides,
  };
}

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}
