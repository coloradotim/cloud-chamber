import {
  type FormEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import type { ExploreSecondarySection } from "./IntegratedExploreWorkspace";
import type { CameraPreset, CameraTransform } from "./True3DViewer";

export type ExplorePoint = {
  x_km: number;
  y_km: number | null;
  z_km: number;
};

type ExploreStateCommon = {
  state_version: 1;
  model_time_seconds: number;
  context_collapsed: boolean;
  secondary_section: ExploreSecondarySection;
  selected_point: ExplorePoint | null;
};

export type TradeCumulusExploreState = ExploreStateCommon & {
  world_id: "trade_cumulus";
  view_id: "field" | "updraft_lens";
  scene_field_id: string;
  slice_field_id: string;
  fixed_scale_id: string | null;
  active_slice_plane: "horizontal" | "vertical_x" | "vertical_y";
  slice_coordinate_km: number;
  slice_native_index: number;
  horizontal_slice_coordinate_km: number | null;
  threshold_native: number;
  layer_opacity: number;
  point_size_px: number;
  lens_opacity: number;
  show_slice_plane: boolean;
  show_cloud_boundary: boolean;
  show_horizontal_wind: boolean;
  wind_mode: "perturbation" | "total";
  camera_preset: CameraPreset;
  camera_transform: CameraTransform | null;
  playback_speed: number;
  display_controls_open: boolean;
};

export type MountainWavesExploreState = ExploreStateCommon & {
  world_id: "mountain_waves";
  view_id: "field" | "wave_structure" | "wave_cloud";
  field_id: "w" | "theta_perturbation" | "cloud_liquid" | "relative_humidity";
  fixed_scale_id: string;
  viewport_id: "focus" | "full";
  geometry_id: "expanded" | "physical";
  overlays: {
    cloud_points: boolean;
    cloud_boundary: boolean;
    saturation_contour: boolean;
    horizontal_wind: boolean;
    potential_temperature_contours: boolean;
  };
  cloud_opacity: number;
  cloud_point_size_px: number;
  playback_speed: number;
};

export type SupercellsExploreState = ExploreStateCommon & {
  world_id: "supercells";
  lens_id: "rotating_updraft" | "cloud_precipitation" | "low_level_interactions";
  viewport_id: "storm" | "full";
  evidence_view: "plan" | "xz" | "yz";
  plane_coordinate_km: number;
  visible_layer_ids: string[];
  fixed_scale_ids: string[];
  overlays: {
    rotation: boolean;
    updraft_helicity: boolean;
    reflectivity: boolean;
    condensate: boolean;
    rain: boolean;
    wind: boolean;
    precipitating_condensate: boolean;
    vertical_motion: boolean;
  };
  hydrometeor_category_codes: number[];
  camera_preset: CameraPreset;
  camera_transform: CameraTransform | null;
  scene_opacity: number;
  scene_point_size: number;
  selected_evidence_visible: boolean;
  playback_speed: number;
  display_controls_open: boolean;
};

export type ExploreWorldState =
  | TradeCumulusExploreState
  | MountainWavesExploreState
  | SupercellsExploreState;

export type ExploreStateSnapshot = {
  schema_version: 1;
  world_id: string;
  simulation_id: string;
  captured_at: string;
  state: ExploreWorldState;
};

export type SavedViewRecord = {
  saved_view_id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  restoration_status: "healthy" | "partially_restorable" | "unavailable";
  restoration_message: string | null;
  snapshot: ExploreStateSnapshot;
};

export type ExploreStateLibrary = {
  schema_version: 1;
  world_id: string;
  simulation_id: string;
  last_active: ExploreStateSnapshot | null;
  saved_views: SavedViewRecord[];
};

type ExploreStateLibraryResponse = {
  library: ExploreStateLibrary;
  backing_simulation_available: boolean;
};

export type ExploreRestorationResult = {
  status: "healthy" | "partially_restorable" | "unavailable";
  message: string;
};

// eslint-disable-next-line react-refresh/only-export-components
export function nearestSavedCoordinate(
  values: number[],
  target: number,
  maximumDistance: number,
): { index: number; value: number; exact: boolean } | null {
  if (!Number.isFinite(target) || values.length === 0) return null;
  let index = -1;
  let distance = Number.POSITIVE_INFINITY;
  values.forEach((value, candidateIndex) => {
    if (!Number.isFinite(value)) return;
    const candidateDistance = Math.abs(value - target);
    if (candidateDistance < distance) {
      index = candidateIndex;
      distance = candidateDistance;
    }
  });
  if (index < 0 || distance > maximumDistance + Number.EPSILON) return null;
  return {
    index,
    value: values[index],
    exact: distance <= Number.EPSILON,
  };
}

export type ExploreStateLibraryController = {
  library: ExploreStateLibrary | null;
  loading: boolean;
  error: string | null;
  savingResume: boolean;
  backingSimulationAvailable: boolean;
  saveResume: (state: ExploreWorldState) => Promise<void>;
  createSavedView: (title: string, description: string, state: ExploreWorldState) => Promise<void>;
  updateSavedView: (
    savedViewId: string,
    update: {
      title?: string;
      description?: string | null;
      restoration_status?: ExploreRestorationResult["status"];
      restoration_message?: string | null;
    },
  ) => Promise<void>;
  deleteSavedView: (savedViewId: string) => Promise<void>;
  retry: () => void;
};

// eslint-disable-next-line react-refresh/only-export-components
export function useExploreStateLibrary(
  worldId: ExploreWorldState["world_id"] | null,
  simulationId: string | null,
): ExploreStateLibraryController {
  const [library, setLibrary] = useState<ExploreStateLibrary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingResume, setSavingResume] = useState(false);
  const [backingSimulationAvailable, setBackingSimulationAvailable] = useState(true);
  const [retryNonce, setRetryNonce] = useState(0);
  const lastResumeSignature = useRef<string | null>(null);
  const activeResumeSignature = useRef<string | null>(null);
  const queuedResume = useRef<{ state: ExploreWorldState; signature: string } | null>(null);
  const resumeDrain = useRef<Promise<void> | null>(null);
  const activeIdentity = useRef<string | null>(null);

  useEffect(() => {
    if (!worldId || !simulationId) {
      activeIdentity.current = null;
      queuedResume.current = null;
      activeResumeSignature.current = null;
      resumeDrain.current = null;
      setLibrary(null);
      setLoading(false);
      setError(null);
      setSavingResume(false);
      setBackingSimulationAvailable(false);
      return;
    }
    const identity = `${worldId}/${simulationId}`;
    activeIdentity.current = identity;
    queuedResume.current = null;
    activeResumeSignature.current = null;
    resumeDrain.current = null;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSavingResume(false);
    setLibrary(null);
    lastResumeSignature.current = null;
    void exploreRequest(exploreStateUrl(worldId, simulationId), { signal: controller.signal })
      .then((response) => {
        if (activeIdentity.current !== identity) return;
        setLibrary(response.library);
        setBackingSimulationAvailable(response.backing_simulation_available);
        lastResumeSignature.current = response.library.last_active
          ? JSON.stringify(response.library.last_active.state)
          : null;
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        if (activeIdentity.current !== identity) return;
        setError(exploreErrorMessage(caught, "Unable to load Saved Views and resume state."));
      })
      .finally(() => {
        if (!controller.signal.aborted && activeIdentity.current === identity) setLoading(false);
      });
    return () => controller.abort();
  }, [retryNonce, simulationId, worldId]);

  const saveResume = useCallback(
    (state: ExploreWorldState): Promise<void> => {
      if (!worldId || !simulationId) throw new Error("Stable Simulation identity is unavailable.");
      const identity = `${worldId}/${simulationId}`;
      const signature = JSON.stringify(state);
      if (
        signature === lastResumeSignature.current ||
        signature === activeResumeSignature.current ||
        signature === queuedResume.current?.signature
      ) {
        return resumeDrain.current ?? Promise.resolve();
      }
      queuedResume.current = { state, signature };
      if (resumeDrain.current) return resumeDrain.current;

      const drain = async () => {
        setSavingResume(true);
        while (queuedResume.current && activeIdentity.current === identity) {
          const pending = queuedResume.current;
          queuedResume.current = null;
          activeResumeSignature.current = pending.signature;
          try {
            const response = await exploreRequest(
              `${exploreStateUrl(worldId, simulationId)}/resume`,
              {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ state: pending.state }),
              },
            );
            if (activeIdentity.current !== identity) return;
            if (queuedResume.current) continue;
            lastResumeSignature.current = pending.signature;
            setLibrary(response.library);
            setBackingSimulationAvailable(response.backing_simulation_available);
            setError(null);
          } catch (caught) {
            if (activeIdentity.current !== identity) return;
            if (!queuedResume.current) {
              setError(exploreErrorMessage(caught, "Unable to save Explore resume state."));
            }
          } finally {
            activeResumeSignature.current = null;
          }
        }
      };
      const currentDrain = drain().finally(() => {
        if (activeIdentity.current === identity) setSavingResume(false);
        if (resumeDrain.current === currentDrain) resumeDrain.current = null;
      });
      resumeDrain.current = currentDrain;
      return currentDrain;
    },
    [simulationId, worldId],
  );

  const createSavedView = useCallback(
    async (title: string, description: string, state: ExploreWorldState) => {
      if (!worldId || !simulationId) throw new Error("Stable Simulation identity is unavailable.");
      try {
        const response = await exploreRequest(savedViewsUrl(worldId, simulationId), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title.trim(),
            description: description.trim() || null,
            state,
          }),
        });
        setLibrary(response.library);
        setBackingSimulationAvailable(response.backing_simulation_available);
        setError(null);
      } catch (caught) {
        setError(exploreErrorMessage(caught, "Unable to save this view."));
        throw caught;
      }
    },
    [simulationId, worldId],
  );

  const updateSavedView = useCallback(
    async (
      savedViewId: string,
      update: {
        title?: string;
        description?: string | null;
        restoration_status?: ExploreRestorationResult["status"];
        restoration_message?: string | null;
      },
    ) => {
      if (!worldId || !simulationId) throw new Error("Stable Simulation identity is unavailable.");
      try {
        const response = await exploreRequest(
          `${savedViewsUrl(worldId, simulationId)}/${encodeURIComponent(savedViewId)}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(update),
          },
        );
        setLibrary(response.library);
        setBackingSimulationAvailable(response.backing_simulation_available);
        setError(null);
      } catch (caught) {
        setError(exploreErrorMessage(caught, "Unable to update this Saved View."));
        throw caught;
      }
    },
    [simulationId, worldId],
  );

  const deleteSavedView = useCallback(
    async (savedViewId: string) => {
      if (!worldId || !simulationId) throw new Error("Stable Simulation identity is unavailable.");
      try {
        const response = await exploreRequest(
          `${savedViewsUrl(worldId, simulationId)}/${encodeURIComponent(savedViewId)}`,
          { method: "DELETE" },
        );
        setLibrary(response.library);
        setBackingSimulationAvailable(response.backing_simulation_available);
        setError(null);
      } catch (caught) {
        setError(exploreErrorMessage(caught, "Unable to delete this Saved View."));
        throw caught;
      }
    },
    [simulationId, worldId],
  );

  return {
    library,
    loading,
    error,
    savingResume,
    backingSimulationAvailable,
    saveResume,
    createSavedView,
    updateSavedView,
    deleteSavedView,
    retry: () => setRetryNonce((current) => current + 1),
  };
}

export function SavedViewsControl({
  controller,
  currentState,
  coherent,
  onOpen,
}: {
  controller: ExploreStateLibraryController;
  currentState: ExploreWorldState | null;
  coherent: boolean;
  onOpen: (
    state: ExploreWorldState,
    savedView: SavedViewRecord,
  ) => Promise<ExploreRestorationResult>;
}) {
  const panelId = useId();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [actionState, setActionState] = useState<"idle" | "saving" | "failed">("idle");
  const [actionMessage, setActionMessage] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const savedViews = controller.library?.saved_views ?? [];

  async function saveCurrentView(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentState || !coherent || !title.trim()) return;
    setActionState("saving");
    setActionMessage("Saving view...");
    try {
      await controller.createSavedView(title, description, currentState);
      setTitle("");
      setDescription("");
      setActionState("idle");
      setActionMessage("Saved");
    } catch (caught) {
      setActionState("failed");
      setActionMessage(exploreErrorMessage(caught, "Unable to save this view."));
    }
  }

  async function openSavedView(savedView: SavedViewRecord) {
    setActionState("saving");
    setActionMessage(`Opening ${savedView.title}...`);
    let result: ExploreRestorationResult;
    try {
      result = await onOpen(savedView.snapshot.state, savedView);
    } catch (caught) {
      setActionState("failed");
      setActionMessage(exploreErrorMessage(caught, "Unable to open this Saved View."));
      return;
    }
    try {
      await controller.updateSavedView(savedView.saved_view_id, {
        restoration_status: result.status,
        restoration_message: result.message,
      });
      setActionState(result.status === "unavailable" ? "failed" : "idle");
      setActionMessage(result.message);
    } catch (caught) {
      setActionState("failed");
      setActionMessage(
        `${result.message} Its restoration status could not be recorded: ${exploreErrorMessage(
          caught,
          "local persistence failed.",
        )}`,
      );
    }
  }

  async function renameSavedView(event: FormEvent<HTMLFormElement>, savedViewId: string) {
    event.preventDefault();
    if (!editTitle.trim()) return;
    setActionState("saving");
    try {
      await controller.updateSavedView(savedViewId, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      setEditingId(null);
      setActionState("idle");
      setActionMessage("Saved View updated");
    } catch (caught) {
      setActionState("failed");
      setActionMessage(exploreErrorMessage(caught, "Unable to update this Saved View."));
    }
  }

  async function removeSavedView(savedView: SavedViewRecord) {
    if (!window.confirm(`Delete the Saved View "${savedView.title}"?`)) return;
    setActionState("saving");
    try {
      await controller.deleteSavedView(savedView.saved_view_id);
      setActionState("idle");
      setActionMessage("Saved View deleted");
    } catch (caught) {
      setActionState("failed");
      setActionMessage(exploreErrorMessage(caught, "Unable to delete this Saved View."));
    }
  }

  return (
    <details className="saved-views-control">
      <summary aria-controls={panelId}>
        Saved Views{savedViews.length > 0 ? ` (${savedViews.length})` : ""}
        {controller.error && (
          <span className="saved-views-summary-error" title={controller.error}>
            State error
          </span>
        )}
      </summary>
      <section id={panelId} className="saved-views-popover" aria-label="Saved Views">
        <header>
          <div>
            <p className="eyebrow">Live examinations</p>
            <h3>Saved Views</h3>
          </div>
          {controller.savingResume && (
            <span className="saved-views-resume-state">Saving state...</span>
          )}
        </header>

        {controller.loading ? (
          <p role="status">Loading Saved Views...</p>
        ) : controller.error && !controller.library ? (
          <div className="saved-views-error">
            <p role="alert">{controller.error}</p>
            <button type="button" onClick={controller.retry}>
              Retry
            </button>
          </div>
        ) : (
          <>
            <form
              className="saved-view-create-form"
              onSubmit={(event) => void saveCurrentView(event)}
            >
              <label>
                Title
                <input
                  type="text"
                  maxLength={120}
                  required
                  value={title}
                  placeholder="Name this examination"
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>
              <label>
                Description <span>optional</span>
                <textarea
                  rows={2}
                  maxLength={1_000}
                  value={description}
                  placeholder="What is worth returning to?"
                  onChange={(event) => setDescription(event.target.value)}
                />
              </label>
              <button
                type="submit"
                disabled={!coherent || !currentState || !title.trim() || actionState === "saving"}
              >
                Save current view
              </button>
              {!coherent && <small>Wait for the current scientific view to finish loading.</small>}
            </form>

            <div className="saved-view-list">
              {savedViews.length === 0 ? (
                <p className="saved-view-empty">No Saved Views yet.</p>
              ) : (
                savedViews.map((savedView) => (
                  <article key={savedView.saved_view_id} className="saved-view-item">
                    {editingId === savedView.saved_view_id ? (
                      <form
                        className="saved-view-edit-form"
                        onSubmit={(event) => void renameSavedView(event, savedView.saved_view_id)}
                      >
                        <label>
                          Title
                          <input
                            type="text"
                            maxLength={120}
                            required
                            value={editTitle}
                            onChange={(event) => setEditTitle(event.target.value)}
                          />
                        </label>
                        <label>
                          Description
                          <textarea
                            rows={2}
                            maxLength={1_000}
                            value={editDescription}
                            onChange={(event) => setEditDescription(event.target.value)}
                          />
                        </label>
                        <div className="saved-view-actions">
                          <button type="submit">Save</button>
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => setEditingId(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : (
                      <>
                        <div className="saved-view-item-heading">
                          <div>
                            <h4>{savedView.title}</h4>
                            <p>{savedViewSummary(savedView.snapshot.state)}</p>
                          </div>
                          <SavedViewStatus record={savedView} />
                        </div>
                        {savedView.description && <p>{savedView.description}</p>}
                        {savedView.restoration_message && (
                          <small>{savedView.restoration_message}</small>
                        )}
                        <div className="saved-view-actions">
                          <button
                            type="button"
                            disabled={
                              !controller.backingSimulationAvailable || actionState === "saving"
                            }
                            onClick={() => void openSavedView(savedView)}
                          >
                            Open
                          </button>
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => {
                              setEditingId(savedView.saved_view_id);
                              setEditTitle(savedView.title);
                              setEditDescription(savedView.description ?? "");
                            }}
                          >
                            Rename
                          </button>
                          <button
                            type="button"
                            className="secondary-button danger-button"
                            onClick={() => void removeSavedView(savedView)}
                          >
                            Delete
                          </button>
                        </div>
                      </>
                    )}
                  </article>
                ))
              )}
            </div>
          </>
        )}

        {(actionMessage || controller.error) && (
          <p
            className={`saved-views-action-message${
              actionState === "failed" || controller.error
                ? " saved-views-action-message-error"
                : ""
            }`}
            role={actionState === "failed" || controller.error ? "alert" : "status"}
          >
            {actionMessage || controller.error}
          </p>
        )}
      </section>
    </details>
  );
}

function SavedViewStatus({ record }: { record: SavedViewRecord }) {
  const labels: Record<SavedViewRecord["restoration_status"], string> = {
    healthy: "Ready",
    partially_restorable: "Adjusted",
    unavailable: "Unavailable",
  };
  return (
    <span className={`saved-view-status saved-view-status-${record.restoration_status}`}>
      {labels[record.restoration_status]}
    </span>
  );
}

function savedViewSummary(state: ExploreWorldState): ReactNode {
  const time = formatSavedTime(state.model_time_seconds);
  if (state.world_id === "trade_cumulus") {
    return `${state.view_id === "updraft_lens" ? "Updraft Lens" : "Field"} · ${time} · ${sliceOrientationLabel(state.active_slice_plane)}`;
  }
  if (state.world_id === "mountain_waves") {
    const view =
      state.view_id === "wave_cloud"
        ? "Wave Cloud Lens"
        : state.view_id === "wave_structure"
          ? "Wave Structure Lens"
          : "Field";
    return `${view} · ${time} · ${state.geometry_id === "expanded" ? "Expanded height" : "True physical scale"}`;
  }
  const lens = state.lens_id
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
  return `${lens} · ${time} · ${sliceOrientationLabel(state.evidence_view)}`;
}

function sliceOrientationLabel(orientation: string): string {
  if (orientation === "plan" || orientation === "horizontal") return "Horizontal x-y";
  if (orientation === "xz" || orientation === "vertical_x") return "Vertical x-z";
  return "Vertical y-z";
}

function formatSavedTime(seconds: number): string {
  return `${Math.round(seconds).toLocaleString()} s`;
}

function exploreStateUrl(worldId: string, simulationId: string): string {
  return `/api/worlds/${worldId.replaceAll("_", "-")}/simulations/${encodeURIComponent(
    simulationId,
  )}/explore-state`;
}

function savedViewsUrl(worldId: string, simulationId: string): string {
  return `/api/worlds/${worldId.replaceAll("_", "-")}/simulations/${encodeURIComponent(
    simulationId,
  )}/saved-views`;
}

async function exploreRequest(
  url: string,
  init?: RequestInit,
): Promise<ExploreStateLibraryResponse> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(await responseMessage(response, "Explore state request failed."));
  }
  return (await response.json()) as ExploreStateLibraryResponse;
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || fallback;
  } catch {
    return fallback;
  }
}

function exploreErrorMessage(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}
