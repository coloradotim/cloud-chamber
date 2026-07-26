import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  type ExploreStateLibraryController,
  type SavedViewRecord,
  SavedViewsControl,
  type TradeCumulusExploreState,
  nearestSavedCoordinate,
  useExploreStateLibrary,
} from "./ExploreStatePersistence";

const tradeState: TradeCumulusExploreState = {
  state_version: 1,
  world_id: "trade_cumulus",
  model_time_seconds: 12_060,
  context_collapsed: false,
  secondary_section: "science",
  selected_point: null,
  view_id: "updraft_lens",
  scene_field_id: "ql",
  slice_field_id: "ql",
  fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
  active_slice_plane: "vertical_x",
  slice_coordinate_km: 0.05,
  slice_native_index: 1,
  horizontal_slice_coordinate_km: 0.8,
  threshold_native: 0.000001,
  layer_opacity: 0.68,
  point_size_px: 11,
  lens_opacity: 0.9,
  show_slice_plane: true,
  show_cloud_boundary: true,
  show_horizontal_wind: true,
  wind_mode: "perturbation",
  camera_preset: "overview",
  camera_transform: null,
  playback_speed: 1,
  display_controls_open: false,
};

const savedView: SavedViewRecord = {
  saved_view_id: "0123456789abcdef0123456789abcdef",
  title: "Cloud turret",
  description: "Before the pulse weakens.",
  created_at: "2026-07-26T12:00:00Z",
  updated_at: "2026-07-26T12:00:00Z",
  restoration_status: "healthy",
  restoration_message: null,
  snapshot: {
    schema_version: 1,
    world_id: "trade_cumulus",
    simulation_id: "trade_cumulus_canonical_bomex",
    captured_at: "2026-07-26T12:00:00Z",
    state: tradeState,
  },
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function libraryResponse(state: TradeCumulusExploreState | null) {
  return {
    library: {
      schema_version: 1 as const,
      world_id: "trade_cumulus",
      simulation_id: "trade_cumulus_canonical_bomex",
      last_active: state
        ? {
            schema_version: 1 as const,
            world_id: "trade_cumulus",
            simulation_id: "trade_cumulus_canonical_bomex",
            captured_at: "2026-07-26T12:00:00Z",
            state,
          }
        : null,
      saved_views: [],
    },
    backing_simulation_available: true,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("nearestSavedCoordinate", () => {
  it("maps exact and bounded physical coordinates without accepting distant output", () => {
    expect(nearestSavedCoordinate([-1, 0, 1], 0, 0.2)).toEqual({
      index: 1,
      value: 0,
      exact: true,
    });
    expect(nearestSavedCoordinate([-1, 0, 1], 0.08, 0.2)).toEqual({
      index: 1,
      value: 0,
      exact: false,
    });
    expect(nearestSavedCoordinate([-1, 0, 1], 0.4, 0.2)).toBeNull();
  });
});

describe("SavedViewsControl", () => {
  it("surfaces persistence errors before the control is opened", () => {
    const controller: ExploreStateLibraryController = {
      library: null,
      loading: false,
      error: "Unable to load Saved Views and resume state.",
      savingResume: false,
      backingSimulationAvailable: false,
      saveResume: vi.fn(),
      createSavedView: vi.fn(),
      updateSavedView: vi.fn(),
      deleteSavedView: vi.fn(),
      retry: vi.fn(),
    };

    render(
      <SavedViewsControl
        controller={controller}
        currentState={null}
        coherent={false}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText("State error")).toBeVisible();
  });

  it("creates, opens, renames, and deletes live examinations", async () => {
    const createSavedView = vi.fn().mockResolvedValue(undefined);
    const updateSavedView = vi.fn().mockResolvedValue(undefined);
    const deleteSavedView = vi.fn().mockResolvedValue(undefined);
    const onOpen = vi.fn().mockResolvedValue({
      status: "healthy",
      message: "Saved View restored.",
    });
    const controller: ExploreStateLibraryController = {
      library: {
        schema_version: 1,
        world_id: "trade_cumulus",
        simulation_id: "trade_cumulus_canonical_bomex",
        last_active: null,
        saved_views: [savedView],
      },
      loading: false,
      error: null,
      savingResume: false,
      backingSimulationAvailable: true,
      saveResume: vi.fn(),
      createSavedView,
      updateSavedView,
      deleteSavedView,
      retry: vi.fn(),
    };
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(
      <SavedViewsControl
        controller={controller}
        currentState={tradeState}
        coherent
        onOpen={onOpen}
      />,
    );

    fireEvent.click(screen.getByText("Saved Views (1)"));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Later pulse" } });
    fireEvent.change(screen.getByLabelText(/Description/), {
      target: { value: "Compare after the next retained output." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save current view" }));
    await waitFor(() =>
      expect(createSavedView).toHaveBeenCalledWith(
        "Later pulse",
        "Compare after the next retained output.",
        tradeState,
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    await waitFor(() => expect(onOpen).toHaveBeenCalledWith(tradeState, savedView));
    expect(updateSavedView).toHaveBeenCalledWith(savedView.saved_view_id, {
      restoration_status: "healthy",
      restoration_message: "Saved View restored.",
    });

    fireEvent.click(screen.getByRole("button", { name: "Rename" }));
    const titleInputs = screen.getAllByLabelText("Title");
    fireEvent.change(titleInputs.at(-1)!, { target: { value: "Renamed turret" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() =>
      expect(updateSavedView).toHaveBeenCalledWith(savedView.saved_view_id, {
        title: "Renamed turret",
        description: "Before the pulse weakens.",
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(deleteSavedView).toHaveBeenCalledWith(savedView.saved_view_id));
  });

  it("keeps a Saved View opening until its target evidence is coherent", async () => {
    const restoration = deferred<{
      status: "healthy";
      message: string;
    }>();
    const updateSavedView = vi.fn().mockResolvedValue(undefined);
    const controller: ExploreStateLibraryController = {
      library: {
        ...libraryResponse(null).library,
        saved_views: [savedView],
      },
      loading: false,
      error: null,
      savingResume: false,
      backingSimulationAvailable: true,
      saveResume: vi.fn(),
      createSavedView: vi.fn(),
      updateSavedView,
      deleteSavedView: vi.fn(),
      retry: vi.fn(),
    };

    render(
      <SavedViewsControl
        controller={controller}
        currentState={tradeState}
        coherent
        onOpen={() => restoration.promise}
      />,
    );

    fireEvent.click(screen.getByText("Saved Views (1)"));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(screen.getByText("Opening Cloud turret...")).toBeVisible();
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    expect(updateSavedView).not.toHaveBeenCalled();

    restoration.resolve({ status: "healthy", message: "Saved View restored." });
    await waitFor(() =>
      expect(updateSavedView).toHaveBeenCalledWith(savedView.saved_view_id, {
        restoration_status: "healthy",
        restoration_message: "Saved View restored.",
      }),
    );
    expect(screen.getByText("Saved View restored.")).toBeVisible();
  });

  it("records failed evidence loading only after restoration reaches a final state", async () => {
    const updateSavedView = vi.fn().mockResolvedValue(undefined);
    const controller: ExploreStateLibraryController = {
      library: {
        ...libraryResponse(null).library,
        saved_views: [savedView],
      },
      loading: false,
      error: null,
      savingResume: false,
      backingSimulationAvailable: true,
      saveResume: vi.fn(),
      createSavedView: vi.fn(),
      updateSavedView,
      deleteSavedView: vi.fn(),
      retry: vi.fn(),
    };

    render(
      <SavedViewsControl
        controller={controller}
        currentState={tradeState}
        coherent
        onOpen={vi.fn().mockResolvedValue({
          status: "unavailable",
          message: "The saved output evidence is unavailable.",
        })}
      />,
    );

    fireEvent.click(screen.getByText("Saved Views (1)"));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));

    expect(await screen.findByText("The saved output evidence is unavailable.")).toBeVisible();
    expect(updateSavedView).toHaveBeenCalledTimes(1);
    expect(updateSavedView).toHaveBeenCalledWith(savedView.saved_view_id, {
      restoration_status: "unavailable",
      restoration_message: "The saved output evidence is unavailable.",
    });
  });

  it("keeps a successful live restoration usable when status persistence fails", async () => {
    const updateSavedView = vi.fn().mockRejectedValue(new Error("Local state is read-only."));
    const controller: ExploreStateLibraryController = {
      library: {
        ...libraryResponse(null).library,
        saved_views: [savedView],
      },
      loading: false,
      error: null,
      savingResume: false,
      backingSimulationAvailable: true,
      saveResume: vi.fn(),
      createSavedView: vi.fn(),
      updateSavedView,
      deleteSavedView: vi.fn(),
      retry: vi.fn(),
    };

    render(
      <SavedViewsControl
        controller={controller}
        currentState={tradeState}
        coherent
        onOpen={vi.fn().mockResolvedValue({
          status: "healthy",
          message: "Saved View restored.",
        })}
      />,
    );

    fireEvent.click(screen.getByText("Saved Views (1)"));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));

    expect(
      await screen.findByText(
        "Saved View restored. Its restoration status could not be recorded: Local state is read-only.",
      ),
    ).toBeVisible();
    expect(updateSavedView).toHaveBeenCalledTimes(1);
  });
});

describe("useExploreStateLibrary", () => {
  it("serializes overlapping resume writes and leaves the newest state in client and storage", async () => {
    const firstWrite = deferred<Response>();
    const secondWrite = deferred<Response>();
    const requestedStates: TradeCumulusExploreState[] = [];
    let persistedState: TradeCumulusExploreState | null = null;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (init?.method !== "PUT") {
          return Promise.resolve(
            new Response(JSON.stringify(libraryResponse(null)), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        expect(url).toContain("/explore-state/resume");
        const state = JSON.parse(String(init.body)).state as TradeCumulusExploreState;
        requestedStates.push(state);
        return requestedStates.length === 1 ? firstWrite.promise : secondWrite.promise;
      }),
    );
    const { result } = renderHook(() =>
      useExploreStateLibrary("trade_cumulus", "trade_cumulus_canonical_bomex"),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));

    const olderState = { ...tradeState, model_time_seconds: 900 };
    const newestState = { ...tradeState, model_time_seconds: 1_800 };
    let drain!: Promise<void>;
    act(() => {
      drain = result.current.saveResume(olderState);
      void result.current.saveResume(newestState);
    });
    await waitFor(() => expect(result.current.savingResume).toBe(true));
    expect(requestedStates).toEqual([olderState]);

    persistedState = olderState;
    firstWrite.resolve(
      new Response(JSON.stringify(libraryResponse(olderState)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() => expect(requestedStates).toEqual([olderState, newestState]));
    expect(result.current.library?.last_active).toBeNull();
    expect(result.current.savingResume).toBe(true);

    persistedState = newestState;
    secondWrite.resolve(
      new Response(JSON.stringify(libraryResponse(newestState)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await act(async () => drain);

    expect(result.current.savingResume).toBe(false);
    expect(result.current.library?.last_active?.state.model_time_seconds).toBe(1_800);
    expect(persistedState.model_time_seconds).toBe(1_800);
  });

  it("clears a different queued state when the newest state matches the active write", async () => {
    const activeWrite = deferred<Response>();
    const requestedStates: TradeCumulusExploreState[] = [];
    const persisted = { state: null as TradeCumulusExploreState | null };
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method !== "PUT") {
          return Promise.resolve(
            new Response(JSON.stringify(libraryResponse(null)), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        const state = JSON.parse(String(init.body)).state as TradeCumulusExploreState;
        requestedStates.push(state);
        return activeWrite.promise.then((response) => {
          persisted.state = state;
          return response;
        });
      }),
    );
    const { result } = renderHook(() =>
      useExploreStateLibrary("trade_cumulus", "trade_cumulus_canonical_bomex"),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));

    const activeState = { ...tradeState, model_time_seconds: 900 };
    const supersededState = { ...tradeState, model_time_seconds: 1_800 };
    let drain!: Promise<void>;
    act(() => {
      drain = result.current.saveResume(activeState);
      void result.current.saveResume(supersededState);
      void result.current.saveResume(activeState);
    });

    expect(requestedStates).toEqual([activeState]);
    expect(result.current.savingResume).toBe(true);
    activeWrite.resolve(
      new Response(JSON.stringify(libraryResponse(activeState)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await act(async () => drain);

    expect(requestedStates).toEqual([activeState]);
    expect(result.current.savingResume).toBe(false);
    expect(result.current.library?.last_active?.state.model_time_seconds).toBe(900);
    expect(persisted.state?.model_time_seconds).toBe(900);
  });

  it("rewrites the persisted state when a different active write could overwrite it", async () => {
    const activeWrite = deferred<Response>();
    const latestWrite = deferred<Response>();
    const persistedState = { ...tradeState, model_time_seconds: 900 };
    let simulatedPersistedState = persistedState;
    const requestedStates: TradeCumulusExploreState[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method !== "PUT") {
          return Promise.resolve(
            new Response(JSON.stringify(libraryResponse(persistedState)), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        const state = JSON.parse(String(init.body)).state as TradeCumulusExploreState;
        requestedStates.push(state);
        const write = requestedStates.length === 1 ? activeWrite.promise : latestWrite.promise;
        return write.then((response) => {
          simulatedPersistedState = state;
          return response;
        });
      }),
    );
    const { result } = renderHook(() =>
      useExploreStateLibrary("trade_cumulus", "trade_cumulus_canonical_bomex"),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));

    const interveningState = { ...tradeState, model_time_seconds: 1_800 };
    let drain!: Promise<void>;
    act(() => {
      drain = result.current.saveResume(interveningState);
      void result.current.saveResume(persistedState);
    });

    expect(requestedStates).toEqual([interveningState]);
    expect(result.current.savingResume).toBe(true);
    activeWrite.resolve(
      new Response(JSON.stringify(libraryResponse(interveningState)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() => expect(requestedStates).toEqual([interveningState, persistedState]));
    expect(result.current.library?.last_active?.state.model_time_seconds).toBe(900);
    expect(result.current.savingResume).toBe(true);

    latestWrite.resolve(
      new Response(JSON.stringify(libraryResponse(persistedState)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await act(async () => drain);

    expect(result.current.savingResume).toBe(false);
    expect(result.current.library?.last_active?.state.model_time_seconds).toBe(900);
    expect(simulatedPersistedState.model_time_seconds).toBe(900);
  });
});
