import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  SaveComparisonControl,
  SavedComparisonsCollection,
  type SavedComparisonEntry,
  type SavedComparisonWorkspace,
} from "./SavedComparisons";

const state = {
  state_version: 1 as const,
  world_id: "trade_cumulus" as const,
  model_time_seconds: 12_060,
  context_collapsed: false,
  secondary_section: "science" as const,
  selected_point: null,
  view_id: "updraft_lens" as const,
  scene_field_id: "ql",
  slice_field_id: "w",
  fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
  active_slice_plane: "vertical_x" as const,
  slice_coordinate_km: 2.3,
  slice_native_index: 5,
  horizontal_slice_coordinate_km: null,
  threshold_native: 1e-6,
  layer_opacity: 0.68,
  point_size_px: 11,
  lens_opacity: 0.9,
  show_slice_plane: true,
  show_cloud_boundary: true,
  show_horizontal_wind: true,
  wind_mode: "perturbation" as const,
  camera_preset: "overview" as const,
  camera_transform: null,
  playback_speed: 1,
  display_controls_open: false,
};

const workspace: SavedComparisonWorkspace = {
  schema_version: 1,
  world_id: "trade_cumulus",
  left_simulation_id: "trade_cumulus_canonical_bomex",
  right_simulation_id: "trade_cumulus_more_moisture",
  left_state: state,
  right_state: { ...state, model_time_seconds: 12_180 },
  links: { time: true, view: true, plane: true, camera: false, selection: false },
  context_collapsed: false,
  supercells_presentation: null,
};

const entry: SavedComparisonEntry = {
  record: {
    saved_comparison_id: "a".repeat(32),
    title: "Moisture response",
    scientific_question: "How does added moisture change the cloud field?",
    created_at: "2026-07-27T12:00:00Z",
    updated_at: "2026-07-27T12:05:00Z",
    restoration_status: "healthy",
    restoration_message: null,
    captured_pair: {
      left_display_name: "Canonical BOMEX Baseline",
      right_display_name: "More Moisture",
      relationship: "Reference and controlled variation",
      controlled_pair: true,
      controlled_pair_message: "Only moisture changed.",
      material_differences: [],
    },
    workspace,
  },
  dependencies: [
    {
      side: "left",
      simulation_id: workspace.left_simulation_id,
      display_name: "Canonical BOMEX Baseline",
      available: true,
    },
    {
      side: "right",
      simulation_id: workspace.right_simulation_id,
      display_name: "More Moisture",
      available: true,
    },
  ],
  effective_restoration_status: "healthy",
  effective_restoration_message: null,
};

describe("Saved Comparisons", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists, opens, edits, and deletes a World-owned comparison", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(ok({ world_id: "trade_cumulus", saved_comparisons: [entry] }))
      .mockResolvedValueOnce(ok({ ...entry, record: { ...entry.record, title: "Moisture pulse" } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    const onOpen = vi.fn();
    render(<SavedComparisonsCollection worldSlug="trade-cumulus" onOpen={onOpen} />);

    expect(await screen.findByRole("heading", { name: "Moisture response" })).toBeVisible();
    expect(screen.getByText("Ready")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(onOpen).toHaveBeenCalledWith(entry.record.saved_comparison_id);

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Moisture pulse" } });
    fireEvent.click(screen.getByRole("button", { name: "Save details" }));
    expect(await screen.findByRole("heading", { name: "Moisture pulse" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "No Saved Comparisons yet" })).toBeVisible(),
    );
  });

  it("creates a new immutable snapshot from a coherent workspace", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(ok(entry, 201));
    const onSaved = vi.fn();
    render(
      <SaveComparisonControl
        worldSlug="trade-cumulus"
        workspace={workspace}
        disabled={false}
        saveAsNew
        onSaved={onSaved}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save as new comparison" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Moisture response" } });
    fireEvent.change(screen.getByLabelText("Scientific question"), {
      target: { value: "How does added moisture change cloud growth?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save comparison" }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(entry));
    expect(fetch).toHaveBeenCalledWith(
      "/api/worlds/trade-cumulus/saved-comparisons",
      expect.objectContaining({ method: "POST" }),
    );
    const createCall = vi
      .mocked(fetch)
      .mock.calls.find(
        ([url, init]) =>
          url === "/api/worlds/trade-cumulus/saved-comparisons" && init?.method === "POST",
      );
    expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({
      title: "Moisture response",
      scientific_question: "How does added moisture change cloud growth?",
      workspace,
    });
  });

  it("keeps save unavailable while live frames are incoherent", () => {
    render(
      <SaveComparisonControl
        worldSlug="trade-cumulus"
        workspace={workspace}
        disabled
        saveAsNew={false}
        onSaved={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Save comparison" })).toBeDisabled();
  });
});

function ok(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
