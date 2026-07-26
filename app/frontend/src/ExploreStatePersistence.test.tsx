import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  type ExploreStateLibraryController,
  type SavedViewRecord,
  SavedViewsControl,
  type TradeCumulusExploreState,
  nearestSavedCoordinate,
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

afterEach(() => {
  vi.restoreAllMocks();
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
    const onOpen = vi.fn().mockReturnValue({
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
});
