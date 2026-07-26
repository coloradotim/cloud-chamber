import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { TradeCumulusExploreState } from "./ExploreStatePersistence";
import type { CompareSimulationDescriptor } from "./WorldCompare.types";
import { WorldCompareSideVisual } from "./WorldCompareAdapters";

vi.mock("./True3DViewer", () => ({
  True3DViewer: ({
    pointCloud,
    status,
  }: {
    pointCloud: { frame_marker?: string } | null;
    status: string;
  }) => (
    <section aria-label="mock 3-D field">
      <span>{status}</span>
      <span>{pointCloud?.frame_marker ?? "no frame"}</span>
    </section>
  ),
}));

const commonState = {
  state_version: 1 as const,
  context_collapsed: true,
  secondary_section: "notes" as const,
  selected_point: null,
};

function state(modelTimeSeconds: number): TradeCumulusExploreState {
  return {
    ...commonState,
    world_id: "trade_cumulus",
    model_time_seconds: modelTimeSeconds,
    view_id: "field",
    scene_field_id: "ql",
    slice_field_id: "ql",
    fixed_scale_id: null,
    active_slice_plane: "vertical_x",
    slice_coordinate_km: 1,
    slice_native_index: 50,
    horizontal_slice_coordinate_km: 1,
    threshold_native: 1e-6,
    layer_opacity: 0.68,
    point_size_px: 11,
    lens_opacity: 0.9,
    show_slice_plane: true,
    show_cloud_boundary: false,
    show_horizontal_wind: false,
    wind_mode: "perturbation",
    camera_preset: "overview",
    camera_transform: null,
    playback_speed: 1,
    display_controls_open: false,
  };
}

const simulation: CompareSimulationDescriptor = {
  simulation_id: "baseline",
  display_name: "Canonical BOMEX Baseline",
  world_id: "trade_cumulus",
  role: "reference",
  run_id: "baseline-run",
  result_id: "baseline-result",
  case_id: "bomex",
  parent_simulation_id: null,
  reference_simulation_id: "baseline",
  lineage_state: "known",
  availability_state: "available",
  availability_message: "Available",
  inspectable: true,
  grid: {
    topology: "native_3d",
    nx: 96,
    ny: 96,
    nz: 100,
    dx_m: 66.67,
    dy_m: 66.67,
    dz_m: 30,
    x_extent_km: [-3.2, 3.2],
    y_extent_km: [-3.2, 3.2],
    z_extent_km: [0, 3],
  },
  time: {
    times_seconds: [0, 60, 120],
    start_seconds: 0,
    end_seconds: 120,
    cadence_seconds: 60,
    saved_output_count: 3,
    interpolation_allowed: false,
  },
  available_field_ids: ["ql"],
  available_view_ids: ["field", "updraft_lens"],
  fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
  plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
  camera_mapping: "normalized_3d",
  initial_state: state(0),
  caveats: [],
};

function payload(marker: string, seconds: number) {
  return {
    frame_marker: marker,
    selection: { time_seconds: seconds },
    provenance: { provenance_label: "Native CM1 scalar cells" },
  };
}

function deferredResponse() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

function renderSide(exploreState: TradeCumulusExploreState) {
  const onFrameState = vi.fn();
  const onPerformance = vi.fn();
  const result = render(
    <WorldCompareSideVisual
      side="left"
      simulation={simulation}
      state={exploreState}
      onStateChange={vi.fn()}
      onFrameState={onFrameState}
      onPerformance={onPerformance}
    />,
  );
  return { ...result, onFrameState, onPerformance };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("WorldCompareSideVisual request lifecycle", () => {
  it("retries a failed side without replacing its adapter", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response("temporary failure", { status: 503 }))
        .mockResolvedValueOnce(
          new Response(JSON.stringify(payload("recovered frame", 0)), { status: 200 }),
        ),
    );
    const { onFrameState } = renderSide(state(0));

    fireEvent.click(await screen.findByRole("button", { name: "Retry this side" }));

    expect(await screen.findByText("recovered frame")).toBeVisible();
    expect(onFrameState).toHaveBeenCalledWith("left", "error");
    expect(onFrameState).toHaveBeenLastCalledWith("left", "ready");
  });

  it("aborts and ignores a stale response when the requested time changes", async () => {
    const stale = deferredResponse();
    let firstSignal: AbortSignal | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input).includes("time_index=0")) {
          firstSignal = init?.signal ?? undefined;
          return stale.promise;
        }
        return Promise.resolve(
          new Response(JSON.stringify(payload("current frame", 60)), { status: 200 }),
        );
      }),
    );
    const rendered = renderSide(state(0));

    rendered.rerender(
      <WorldCompareSideVisual
        side="left"
        simulation={simulation}
        state={state(60)}
        onStateChange={vi.fn()}
        onFrameState={rendered.onFrameState}
        onPerformance={rendered.onPerformance}
      />,
    );

    expect(await screen.findByText("current frame")).toBeVisible();
    expect(firstSignal?.aborted).toBe(true);
    await act(async () => {
      stale.resolve(
        new Response(JSON.stringify(payload("stale frame", 0)), { status: 200 }),
      );
      await stale.promise;
    });
    await waitFor(() => expect(screen.queryByText("stale frame")).not.toBeInTheDocument());
    expect(screen.getByText("current frame")).toBeVisible();
  });

  it("reuses a bounded side cache when returning to a prior saved output", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const isFirst = String(input).includes("time_index=0");
      return Promise.resolve(
        new Response(
          JSON.stringify(payload(isFirst ? "first frame" : "second frame", isFirst ? 0 : 60)),
          { status: 200 },
        ),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const rendered = renderSide(state(0));
    expect(await screen.findByText("first frame")).toBeVisible();

    rendered.rerender(
      <WorldCompareSideVisual
        side="left"
        simulation={simulation}
        state={state(60)}
        onStateChange={vi.fn()}
        onFrameState={rendered.onFrameState}
        onPerformance={rendered.onPerformance}
      />,
    );
    expect(await screen.findByText("second frame")).toBeVisible();

    rendered.rerender(
      <WorldCompareSideVisual
        side="left"
        simulation={simulation}
        state={state(0)}
        onStateChange={vi.fn()}
        onFrameState={rendered.onFrameState}
        onPerformance={rendered.onPerformance}
      />,
    );
    expect(await screen.findByText("first frame")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(rendered.onPerformance).toHaveBeenLastCalledWith(
      expect.objectContaining({ cache_hit: true, side: "left" }),
    );
  });
});
