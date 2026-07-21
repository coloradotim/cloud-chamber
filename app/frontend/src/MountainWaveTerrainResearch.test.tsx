import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  type MountainWaveTerrainFrame,
  MountainWaveTerrainResearch,
  buildTerrainDisplayCells,
  centerValuesToEdges,
  terrainReadoutForCell,
  terrainFieldColor,
} from "./MountainWaveTerrainResearch";

const frame: MountainWaveTerrainFrame = {
  schema_version: "mountain_wave_terrain_research_v1",
  run_id: "dry-mountain-wave-official-20260721T183530Z",
  case_label: "CM1 r21.1 dry mountain-wave benchmark",
  time_index: 0,
  time_seconds: 0,
  times_seconds: [0, 216, 432, 648, 864, 1080, 1296, 1512, 1728, 1944, 2160],
  dimensionality: "2-D x-z cross-section",
  singleton_y: true,
  dry_case: true,
  field: {
    key: "w",
    display_name: "Vertical velocity",
    units: "m/s",
    native_dimensions: ["zf", "yh", "xh"],
    vertical_grid: "physical_full_levels",
    derivation: "native CM1 w; no interpolation or collocation",
  },
  values: [
    [-0.2, 0.1],
    [-1.0, 1.0],
    [-0.1, 0.2],
  ],
  geometry: {
    x_center_m: [-500, 500],
    x_edge_m: [-1000, 0, 1000],
    terrain_m: [0, 400],
    scalar_height_m: [
      [5000, 5300],
      [15000, 15100],
    ],
    full_height_m: [
      [0, 400],
      [10000, 10200],
      [20000, 20000],
    ],
    nominal_scalar_height_m: [5000, 15000],
    nominal_full_height_m: [0, 10000, 20000],
    active_top_m: 20000,
    singleton_y_m: 0,
    horizontal_units: "m",
    vertical_units: "m",
  },
  active_top_evidence: {
    transform_top_source: "final_nominal_zf",
    final_nominal_zf_m: 20000,
    runtime_ztop_m: 20000,
    configured_nz: 2,
    configured_dz_m: 10000,
    nz_times_dz_m: 20000,
    all_sources_agree: true,
    inactive_namelist_ztop_m: 18000,
  },
  vertical_references: {
    physical_model_height: "terrain-following geometric height above model datum",
    local_agl: "physical model height minus native terrain height at the same x cell",
    nominal_coordinate: "terrain coordinate used by CM1; not physical altitude over terrain",
    model_height_is_msl: false,
  },
  scale: {
    fixed_across_all_times: true,
    minimum: -3.1,
    maximum: 3.1,
    selected_time_minimum: -1,
    selected_time_maximum: 1,
    palette: "blue_white_red_diverging",
  },
  provenance: {
    source_history_file: "cm1out_000001.nc",
    reference_history_file: null,
    source_kind: "native_cm1_numbered_history",
    topology: "native_2d_x_z_singleton_y",
    horizontal_collocation: "none",
    interpolation: "none",
    display_binning: "Native full-level samples painted between physical vertical midpoints.",
    physical_height_source: "native zhval",
    full_height_source: "reconstructed",
    masked_below_terrain: true,
  },
  identity: {
    implementation_commit: "9ff73ff244c393bee2a2e93a851ad1ba2dc16287",
    verification_mode: "pinned_sha256_before_and_after_extraction",
    verified_file_count: 23,
    verified_before_and_after_extraction: true,
  },
  performance: {
    extraction_ms: 31.2,
    serialization_ms: 1.1,
    serialized_payload_bytes: 160000,
  },
  caveats: [
    "This dry two-dimensional benchmark does not simulate moisture or cloud formation.",
    "The singleton y dimension is native CM1 output, not an extruded three-dimensional field.",
  ],
};

describe("terrain-aware display geometry", () => {
  it("places full-level samples between physical midpoints without cells below terrain", () => {
    const cells = buildTerrainDisplayCells(frame);
    expect(cells).toHaveLength(6);
    expect(cells[0]?.nominalHeightM).toBe(0);
    expect(cells[0]?.corners[0]).toEqual({ x: -1000, z: 0 });
    expect(cells[1]?.corners[0]?.z).toBe(200);
    expect(cells.every((cell) => cell.corners.every((corner) => corner.z >= 0))).toBe(true);
    expect(cells.at(-1)?.corners[2]?.z).toBe(20000);
    expect(terrainReadoutForCell(frame, cells[1]!)).toMatchObject({
      xM: 500,
      modelHeightM: 400,
      terrainHeightM: 400,
      aglM: 0,
    });
  });

  it("uses physical full-level bounds for scalar theta cells", () => {
    const thetaFrame: MountainWaveTerrainFrame = {
      ...frame,
      field: {
        ...frame.field,
        key: "theta_perturbation",
        units: "K",
        native_dimensions: ["zh", "yh", "xh"],
        vertical_grid: "physical_scalar_levels",
      },
      values: [
        [0.1, 0.2],
        [-0.1, -0.2],
      ],
    };
    const cells = buildTerrainDisplayCells(thetaFrame);
    expect(cells).toHaveLength(4);
    expect(cells[0]?.nominalHeightM).toBe(5000);
    expect(cells[2]?.corners[0]?.z).toBe(10000);
  });

  it("derives continuous geometry edges and a deterministic diverging scale", () => {
    expect(centerValuesToEdges([0, 400, 100])).toEqual([0, 200, 250, 100]);
    expect(terrainFieldColor(-1, -1, 1)).toBe("#173f8a");
    expect(terrainFieldColor(0, -1, 1)).toBe("#f7f7f2");
    expect(terrainFieldColor(1, -1, 1)).toBe("#9d1d20");
  });
});

describe("MountainWaveTerrainResearch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ok(frame)));
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("opens on native w with exact-time controls and explicit dry singleton-y scope", async () => {
    render(<MountainWaveTerrainResearch />);

    expect(
      await screen.findByRole("heading", { name: "Dry mountain-wave cross-section" }),
    ).toBeInTheDocument();
    await screen.findByRole("img", { name: /Vertical velocity over native curved terrain/ });
    expect(screen.getByText("Dry 2-D x-z cross-section · singleton y")).toBeInTheDocument();
    expect(screen.getByText(/does not simulate moisture or cloud formation/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vertical velocity" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("slider", { name: "Saved output time" })).toHaveAttribute("max", "10");
    expect(fetch).toHaveBeenCalledWith(
      "/api/research/mountain-wave-terrain?field=w&time_index=10",
      expect.any(Object),
    );
  });

  it("requests the selected field and exact previous history", async () => {
    render(<MountainWaveTerrainResearch />);
    await screen.findByRole("img", { name: /Vertical velocity over native curved terrain/ });

    fireEvent.click(screen.getByRole("button", { name: "θ perturbation" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "/api/research/mountain-wave-terrain?field=theta_perturbation&time_index=10",
        expect.any(Object),
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Previous output" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "/api/research/mountain-wave-terrain?field=theta_perturbation&time_index=9",
        expect.any(Object),
      ),
    );
  });
});

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}
