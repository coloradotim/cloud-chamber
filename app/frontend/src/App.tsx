import { useCallback, useEffect, useMemo, useState } from "react";
import type { CSSProperties, FormEvent } from "react";

import "./App.css";

type ControlOption = {
  value: string;
  label: string;
  description?: string | null;
};

type ScenarioControl = {
  id: string;
  label: string;
  description: string;
  type: "choice";
  default: string | number | boolean;
  options: ControlOption[];
};

type RunSizePreset = {
  id: string;
  label: string;
  purpose: string;
  expected_runtime: string;
  confidence: string;
  output_notes: string;
};

type Scenario = {
  id: string;
  display_name: string;
  description: string;
  physical_question: string;
  intended_behavior: string;
  expected_behavior: string;
  learning_goals: string[];
  warnings: string[];
  limitations: string[];
  controls: ScenarioControl[];
  run_size_presets: RunSizePreset[];
};

type ScenarioResponse = {
  golden_path_scenario_id: string;
  scenarios: Scenario[];
};

type DryRunReport = {
  scenario_id: string;
  physical_question: string;
  controls: Record<string, string | number | boolean>;
  run_size_preset: string;
  estimated_cost_or_size: string;
  expected_diagnostics: string[];
  visualization_defaults: Record<string, unknown>;
  generated_files: Record<string, string>;
  not_a_completed_cm1_result: boolean;
  cm1_was_launched: boolean;
  provenance: {
    product_state: string;
    source_model: string;
    preview_is_guidance_only: boolean;
    visualizer_is_interpretation: boolean;
  };
};

type DryRunResponse = {
  package_dir: string;
  manifest_path: string;
  report_path: string;
  generated_files: string[];
  report: DryRunReport;
};

type RunStatusResponse = {
  run_id: string;
  lifecycle_state: string;
  product_state: string;
  validation_status: string;
  manifest_path: string;
  command: string[];
  stdout_log: string;
  stderr_log: string;
  stdout_tail: string | null;
  stderr_tail: string | null;
  exit_code: number | null;
  started_at: string | null;
  finished_at: string | null;
  output_summary: {
    raw_cm1_artifacts: number;
    netcdf_paths: number;
    processed_artifacts: number;
  };
  runtime_warnings: string[];
};

type IngestResponse = {
  result_id: string;
  run_id: string;
  diagnostics_summary: string | null;
};

type OutputFileSummary = {
  netcdf_count: number;
  model_output_count: number;
  stats_netcdf_count: number;
  raw_cm1_artifact_count: number;
  processed_artifact_count: number;
  visualization_ready_artifact_count: number;
  total_output_count: number;
  model_output_file_count: number;
  time_steps: number | null;
  first_output_time_seconds: number | null;
  last_output_time_seconds: number | null;
};

type ResultCard = {
  result_id: string;
  run_id: string;
  name: string;
  tags: string[];
  notes: string | null;
  saved: boolean;
  protected: boolean;
  scenario_id: string;
  scenario_name: string | null;
  run_size_preset: string;
  physical_question: string;
  controls: Record<string, string | number | boolean>;
  status: string;
  source_lifecycle_state: string;
  source_product_state: string;
  source_model: string;
  provenance_labels: string[];
  diagnostics_summary: string | null;
  thermal_fate_label?: string | null;
  thermal_fate_confidence?: string | null;
  main_limiting_factor?: string | null;
  first_cloud_time_seconds: number | null;
  max_qc_kg_kg: number | null;
  max_w_m_s: number | null;
  min_w_m_s: number | null;
  rain_present: boolean | null;
  caveats: string[];
  output_file_summary: OutputFileSummary;
  created_at: string;
  completed_at: string | null;
  ingested_at: string;
  updated_at: string;
};

type ResultsResponse = {
  results: ResultCard[];
};

type RunStorageEntry = {
  run_id: string;
  scenario_id: string | null;
  scenario_name: string | null;
  lifecycle_state: string | null;
  validation_status: string | null;
  product_state: string | null;
  run_size_preset: string | null;
  created_at: string | null;
  updated_at: string | null;
  saved: boolean;
  protected: boolean;
  output_artifact_count: number;
  output_summary: {
    raw_cm1_artifacts?: number;
    netcdf_paths?: number;
    processed_artifacts?: number;
  };
  size_bytes: number;
  path: string;
  category: string;
  manifest_path: string | null;
  manifest_error: string | null;
};

type StorageInventoryResponse = {
  runtime_home: string;
  runs_directory: string;
  total_size_bytes: number;
  warning_threshold_bytes: number;
  above_warning_threshold: boolean;
  warning_message: string | null;
  runs: RunStorageEntry[];
  largest_runs: RunStorageEntry[];
};

type DeleteRunResponse = {
  run_id: string;
  run_directory: string;
  dry_run: boolean;
  deleted: boolean;
  size_bytes: number;
  message: string;
};

type WorkspaceSection = "build" | "results" | "explore";
type ResultsTab = "notebook" | "compare" | "storage";
type ExploreTab = "slices" | "view3d";
type ScenarioLoadState = "loading" | "loaded" | "failed" | "empty";

type ProvenancePayload = {
  source_model: string;
  result_id: string;
  run_id: string;
  scenario_id: string;
  source_product_state: string;
  result_state: string;
  processing_method: string;
  rendering_method: string;
  provenance_label: string;
};

type VisualizableField = {
  raw_field_name: string;
  canonical_field_name: string;
  display_name: string;
  units: string | null;
  dimensions: string[];
  shape: number[];
  native_grid: string;
  coordinate_names: {
    time: string | null;
    vertical: string | null;
    y: string | null;
    x: string | null;
  };
  time_coordinate_values: Array<number | string | null>;
  provenance: ProvenancePayload;
  caveats: string[];
};

type FieldCatalogResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  source_model: string;
  available_fields: VisualizableField[];
  provenance: ProvenancePayload;
  caveats: string[];
};

type SliceResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  field: VisualizableField;
  selection: {
    time_index: number;
    time_seconds: number | null;
    orientation: "horizontal" | "vertical_x" | "vertical_y";
    selected_dimension: string;
    selected_index: number;
    selected_coordinate_value: number | string | null;
    level_units: string | null;
    level_coordinate_value: number | string | null;
    level_meters: number | null;
  };
  coordinate_units: Record<string, string | null>;
  shape: number[];
  dimension_order: string[];
  data_encoding: "json";
  values: Array<Array<number | null>>;
  stats: {
    min: number | null;
    max: number | null;
    mean: number | null;
    finite_count: number;
    non_finite_count: number;
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type PointCloudResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  field: VisualizableField;
  selection: {
    field: string;
    time_index: number;
    time_seconds: number | null;
    threshold: number;
    max_points: number;
  };
  coordinate_units: Record<string, string | null>;
  coordinate_extents: Record<string, { min: number; max: number; units: string | null }>;
  point_order: string[];
  points: Array<[number, number, number, number]>;
  stats: {
    source_count: number;
    returned_count: number;
    min_value: number | null;
    max_value: number | null;
    active_z_min: number | null;
    active_z_max: number | null;
    max_value_location: { x: number; y: number; z: number; value: number } | null;
    downsampled: boolean;
    downsample_stride: number;
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type RegionType = "point" | "column" | "box";

type SelectedRegionRequest = {
  regionType: RegionType;
  xIndex?: number;
  yIndex?: number;
  zIndex?: number;
  xStart?: number;
  xEnd?: number;
  yStart?: number;
  yEnd?: number;
  zStart?: number;
  zEnd?: number;
  neighborhood?: number;
};

type AxisSelection = {
  dimension: string;
  start_index: number;
  end_index: number;
  start_coordinate: number | string | null;
  end_coordinate: number | string | null;
  units: string | null;
};

type TimeValue = {
  time_seconds: number | null;
  value: number | null;
};

type SelectedRegionDiagnosticsResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  region: {
    region_type: RegionType;
    requested: Record<string, unknown>;
    x: AxisSelection | null;
    y: AxisSelection | null;
    vertical: AxisSelection | null;
    native_grid: string | null;
    cell_count: number | null;
  };
  diagnostics: {
    available: boolean;
    local_max_w_m_s: number | null;
    time_of_local_max_w_seconds: number | null;
    local_min_w_m_s: number | null;
    time_of_local_min_w_seconds: number | null;
    local_w_max_time_series: TimeValue[];
    local_w_min_time_series: TimeValue[];
    local_max_qc_kg_kg: number | null;
    time_of_local_max_qc_seconds: number | null;
    first_local_cloud_time_seconds: number | null;
    local_cloud_fraction_time_series: TimeValue[];
    local_qc_max_time_series: TimeValue[];
    local_cloud_base_time_series: TimeValue[];
    local_cloud_top_time_series: TimeValue[];
    local_max_qc_height_time_series: TimeValue[];
    local_max_w_height_time_series: TimeValue[];
    local_rain_present: boolean;
    first_local_rain_time_seconds: number | null;
    local_max_qr_kg_kg: number | null;
    time_of_local_max_qr_seconds: number | null;
    local_qr_max_time_series: TimeValue[];
  };
  comparison_to_domain: {
    local_max_w_fraction_of_domain: number | null;
    local_max_qc_fraction_of_domain: number | null;
    local_first_cloud_time_delta_seconds: number | null;
    local_cloud_top_fraction_of_domain: number | null;
    local_first_rain_time_delta_seconds: number | null;
    caveats: string[];
  };
  interpretation: {
    thermal_fate_label: string;
    confidence: ProcessSupport;
    main_limiting_factor: string;
    summary: string;
    caveats: string[];
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type FieldViewDefaults = {
  field: string;
  time_index: number;
  time_seconds: number | null;
  horizontal_level_index: number;
  vertical_x_index: number;
  vertical_y_index: number;
  source: string;
  max_value: number | null;
  selected_time_index: number | null;
  selected_time_seconds: number | null;
  caveats: string[];
};

type ViewDefaultsResponse = {
  result_id: string;
  run_id: string;
  scenario_id: string;
  preferred_field: string | null;
  fields: Record<string, FieldViewDefaults>;
  provenance: ProvenancePayload;
  caveats: string[];
};

type InspectorViewMode = "horizontal" | "vertical_x" | "vertical_y" | "compare";
type ProcessMode =
  | "thermal_fate"
  | "cloud_water"
  | "updrafts"
  | "moisture"
  | "buoyancy"
  | "cap"
  | "cloud_lifecycle"
  | "deep_breakthrough"
  | "precipitation_feedback";
type SceneViewPreset = "cloud-overview" | "vertical-cross-section" | "top-down-slice" | "updraft";
type ProjectionMode = "oblique" | "side_xz" | "side_yz" | "top_down";
type SceneSlicePlane = "horizontal" | "vertical_x" | "vertical_y";

const FIELD_LOAD_TIMEOUT_MS = 8000;

async function fetchScenarioCatalog(): Promise<ScenarioResponse> {
  const response = await fetch("/api/scenarios");
  if (!response.ok) {
    throw new Error("Unable to load scenarios.");
  }
  return response.json() as Promise<ScenarioResponse>;
}

async function requestDryRunPackage(
  scenarioId: string,
  controls: Record<string, string | number | boolean>,
  runSizePreset: string,
): Promise<DryRunResponse> {
  const response = await fetch("/api/dry-run-package", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario_id: scenarioId,
      controls,
      run_size_preset: runSizePreset,
    }),
  });
  if (!response.ok) {
    throw new Error("Unable to create dry-run package.");
  }
  return response.json() as Promise<DryRunResponse>;
}

async function launchLocalRun(manifestPath: string): Promise<RunStatusResponse> {
  const response = await fetch("/api/runs/launch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to launch local CM1."));
  }
  return response.json() as Promise<RunStatusResponse>;
}

async function fetchRunStatus(manifestPath: string): Promise<RunStatusResponse> {
  const search = new URLSearchParams({ manifest_path: manifestPath });
  const response = await fetch(`/api/runs/status?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to refresh run status."));
  }
  return response.json() as Promise<RunStatusResponse>;
}

async function ingestCompletedRun(manifestPath: string): Promise<IngestResponse> {
  const response = await fetch("/api/results/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manifest_path: manifestPath }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to ingest completed CM1 output."));
  }
  return response.json() as Promise<IngestResponse>;
}

async function fetchResults(): Promise<ResultsResponse> {
  const response = await fetch("/api/results");
  if (!response.ok) {
    throw new Error("Could not load results.");
  }
  return normalizeResultsResponse(await response.json());
}

function normalizeResultsResponse(payload: unknown): ResultsResponse {
  if (Array.isArray(payload)) {
    return { results: payload as ResultCard[] };
  }
  if (isObject(payload) && Array.isArray(payload.results)) {
    return { results: payload.results as ResultCard[] };
  }
  throw new Error("Could not load results.");
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function patchResultCard(
  resultId: string,
  update: Partial<Pick<ResultCard, "name" | "tags" | "notes" | "saved" | "protected">>,
): Promise<ResultCard> {
  const response = await fetch(`/api/results/${resultId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  if (!response.ok) {
    throw new Error("Unable to update result card.");
  }
  return response.json() as Promise<ResultCard>;
}

async function saveResultCard(resultId: string): Promise<ResultCard> {
  const response = await fetch(`/api/results/${resultId}/save`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Unable to save result card.");
  }
  return response.json() as Promise<ResultCard>;
}

async function fetchStorageInventory(): Promise<StorageInventoryResponse> {
  const response = await fetch("/api/storage/inventory");
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load runtime storage inventory."));
  }
  return response.json() as Promise<StorageInventoryResponse>;
}

async function requestRunDeletePreview(runId: string): Promise<DeleteRunResponse> {
  const response = await fetch("/api/storage/delete-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_id: runId,
      dry_run: true,
      confirm: false,
      force_saved: false,
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to preview run deletion."));
  }
  return response.json() as Promise<DeleteRunResponse>;
}

async function confirmRunDelete(runId: string): Promise<DeleteRunResponse> {
  const response = await fetch("/api/storage/delete-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_id: runId,
      dry_run: false,
      confirm: true,
      force_saved: false,
    }),
  });
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to delete selected run."));
  }
  return response.json() as Promise<DeleteRunResponse>;
}

async function fetchVisualizationFields(resultId: string): Promise<FieldCatalogResponse> {
  const response = await fetch(`/api/results/${resultId}/visualization/fields`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization fields."));
  }
  return response.json() as Promise<FieldCatalogResponse>;
}

function withTimeout<T>(promise: Promise<T>, message: string, timeoutMs = FIELD_LOAD_TIMEOUT_MS) {
  let timeoutId: number | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = window.setTimeout(() => reject(new Error(message)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => {
    if (timeoutId !== undefined) window.clearTimeout(timeoutId);
  });
}

async function fetchVisualizationDefaults(
  resultId: string,
  timeIndex?: number,
): Promise<ViewDefaultsResponse> {
  const search = timeIndex === undefined ? "" : `?time_index=${timeIndex}`;
  const response = await fetch(`/api/results/${resultId}/visualization/defaults${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization defaults."));
  }
  return response.json() as Promise<ViewDefaultsResponse>;
}

async function fetchVisualizationSlice(
  resultId: string,
  params: {
    field: string;
    timeIndex: number;
    orientation: "horizontal" | "vertical_x" | "vertical_y";
    levelIndex: number;
  },
): Promise<SliceResponse> {
  const search = new URLSearchParams({
    field: params.field,
    time_index: String(params.timeIndex),
    orientation: params.orientation,
    level_index: String(params.levelIndex),
    encoding: "json",
  });
  const response = await fetch(`/api/results/${resultId}/visualization/slice?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization slice."));
  }
  return response.json() as Promise<SliceResponse>;
}

async function fetchVisualizationPointCloud(
  resultId: string,
  params: {
    field: string;
    timeIndex: number;
    threshold: number;
    maxPoints: number;
  },
): Promise<PointCloudResponse> {
  const search = new URLSearchParams({
    field: params.field,
    time_index: String(params.timeIndex),
    threshold: String(params.threshold),
    max_points: String(params.maxPoints),
    encoding: "json",
  });
  const response = await fetch(`/api/results/${resultId}/visualization/point-cloud?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load cloud-water point cloud."));
  }
  return response.json() as Promise<PointCloudResponse>;
}

async function fetchSelectedRegionDiagnostics(
  resultId: string,
  request: SelectedRegionRequest,
): Promise<SelectedRegionDiagnosticsResponse> {
  const search = new URLSearchParams({
    region_type: request.regionType,
    neighborhood: String(request.neighborhood ?? 0),
  });
  addOptionalIndex(search, "x_index", request.xIndex);
  addOptionalIndex(search, "y_index", request.yIndex);
  addOptionalIndex(search, "z_index", request.zIndex);
  addOptionalIndex(search, "x_start", request.xStart);
  addOptionalIndex(search, "x_end", request.xEnd);
  addOptionalIndex(search, "y_start", request.yStart);
  addOptionalIndex(search, "y_end", request.yEnd);
  addOptionalIndex(search, "z_start", request.zStart);
  addOptionalIndex(search, "z_end", request.zEnd);
  const response = await fetch(`/api/results/${resultId}/diagnostics/selected-region?${search}`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to inspect the selected region."));
  }
  return response.json() as Promise<SelectedRegionDiagnosticsResponse>;
}

function addOptionalIndex(search: URLSearchParams, key: string, value: number | undefined) {
  if (value !== undefined) search.set(key, String(value));
}

async function responseError(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export function App() {
  const [activeSection, setActiveSection] = useState<WorkspaceSection>("results");
  const [activeResultsTab, setActiveResultsTab] = useState<ResultsTab>("notebook");
  const [activeExploreTab, setActiveExploreTab] = useState<ExploreTab>("view3d");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("baseline-shallow-cumulus");
  const [controls, setControls] = useState<Record<string, string | number | boolean>>({});
  const [runSizePreset, setRunSizePreset] = useState("quick_look");
  const [dryRun, setDryRun] = useState<DryRunResponse | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [runWorkflowError, setRunWorkflowError] = useState<string | null>(null);
  const [ingestedResultId, setIngestedResultId] = useState<string | null>(null);
  const [results, setResults] = useState<ResultCard[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [resultDraft, setResultDraft] = useState({ name: "", tags: "", notes: "" });
  const [resultsStatus, setResultsStatus] = useState("Loading results...");
  const [storageInventory, setStorageInventory] = useState<StorageInventoryResponse | null>(null);
  const [storageStatus, setStorageStatus] = useState("Loading storage inventory...");
  const [storageError, setStorageError] = useState<string | null>(null);
  const [deletePreview, setDeletePreview] = useState<DeleteRunResponse | null>(null);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);
  const [status, setStatus] = useState("Loading scenarios...");
  const [scenarioLoadState, setScenarioLoadState] = useState<ScenarioLoadState>("loading");
  const [scenarioError, setScenarioError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);

  const loadScenarios = useCallback(async (active: () => boolean = () => true) => {
    setScenarioLoadState("loading");
    setScenarioError(null);
    setError(null);
    setStatus("Loading scenarios...");
    setScenarios([]);
    setDryRun(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setIngestedResultId(null);
    try {
      const catalog = await fetchScenarioCatalog();
      if (!active()) return;
      setScenarios(catalog.scenarios);
      setSelectedScenarioId(catalog.golden_path_scenario_id);
      if (catalog.scenarios.length === 0) {
        setScenarioLoadState("empty");
        setStatus("No scenarios available");
      } else {
        setScenarioLoadState("loaded");
        setStatus("Scenario setup");
      }
    } catch (caught: unknown) {
      if (!active()) return;
      setScenarioLoadState("failed");
      setScenarioError(caught instanceof Error ? caught.message : "Unable to load scenarios.");
      setStatus("Scenario load failed");
    }
  }, []);

  useEffect(() => {
    let active = true;
    loadScenarios(() => active);
    return () => {
      active = false;
    };
  }, [loadScenarios]);

  useEffect(() => {
    let active = true;
    fetchResults()
      .then((payload) => {
        if (!active) return;
        const prioritized = prioritizeResults(payload.results);
        setResults(prioritized);
        setSelectedResultId((current) => current ?? prioritized[0]?.result_id ?? null);
        setResultsStatus(payload.results.length > 0 ? "Results loaded" : "No ingested results");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setResults([]);
        setSelectedResultId(null);
        setResultsError(caught instanceof Error ? caught.message : "Could not load results.");
        setResultsStatus("Results unavailable");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    refreshStorageInventory().catch(() => undefined);
    return () => {
      active = false;
    };

    async function refreshStorageInventory() {
      try {
        const payload = await fetchStorageInventory();
        if (!active) return;
        setStorageInventory(payload);
        setStorageStatus(payload.runs.length > 0 ? "Storage inventory loaded" : "No runtime runs");
      } catch (caught) {
        if (!active) return;
        setStorageError(
          caught instanceof Error ? caught.message : "Unable to load runtime storage inventory.",
        );
        setStorageStatus("Storage unavailable");
      }
    }
  }, []);

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0],
    [scenarios, selectedScenarioId],
  );

  const selectedResult = useMemo(
    () => results.find((result) => result.result_id === selectedResultId) ?? results[0],
    [results, selectedResultId],
  );
  const comparisonPair = useMemo(() => defaultComparisonPair(results), [results]);

  useEffect(() => {
    if (!selectedScenario) return;
    const defaults = Object.fromEntries(
      selectedScenario.controls.map((control) => [control.id, control.default]),
    );
    setControls(defaults);
    setRunSizePreset(selectedScenario.run_size_presets[0]?.id ?? "quick_look");
    setDryRun(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setIngestedResultId(null);
  }, [selectedScenario]);

  useEffect(() => {
    if (!selectedResult) return;
    setResultDraft({
      name: selectedResult.name,
      tags: selectedResult.tags.join(", "),
      notes: selectedResult.notes ?? "",
    });
  }, [selectedResult]);

  const validationMessages = useMemo(() => {
    if (!selectedScenario) return [];
    return selectedScenario.controls.flatMap((control) => {
      const value = controls[control.id];
      const optionValues = new Set(control.options.map((option) => option.value));
      if (typeof value === "string" && optionValues.has(value)) return [];
      return [`${control.label} needs one of the listed values.`];
    });
  }, [controls, selectedScenario]);

  async function handleDryRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedScenario || validationMessages.length > 0) return;
    setStatus("Creating dry-run package");
    setError(null);
    setDryRun(null);
    setRunStatus(null);
    setRunWorkflowError(null);
    setIngestedResultId(null);
    try {
      const result = await requestDryRunPackage(selectedScenario.id, controls, runSizePreset);
      setDryRun(result);
      setStatus("Packaged dry-run output");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create dry-run package.");
      setStatus("Scenario setup");
    }
  }

  async function handleLaunchRun() {
    if (!dryRun) return;
    setRunWorkflowError(null);
    setStatus("Launching local CM1");
    try {
      const launched = await launchLocalRun(dryRun.manifest_path);
      setRunStatus(launched);
      setStatus(userFacingRunWorkflowStatus(launched));
    } catch (caught) {
      setRunWorkflowError(caught instanceof Error ? caught.message : "Unable to launch local CM1.");
      setStatus("Launch blocked");
    }
  }

  async function handleRefreshRunStatus() {
    if (!dryRun) return;
    setRunWorkflowError(null);
    try {
      const refreshed = await fetchRunStatus(dryRun.manifest_path);
      setRunStatus(refreshed);
      setStatus(userFacingRunWorkflowStatus(refreshed));
    } catch (caught) {
      setRunWorkflowError(
        caught instanceof Error ? caught.message : "Unable to refresh local CM1 status.",
      );
    }
  }

  async function refreshResults(selectResultId?: string) {
    const payload = await fetchResults();
    const prioritized = prioritizeResults(payload.results);
    setResults(prioritized);
    setSelectedResultId((current) => {
      if (selectResultId) return selectResultId;
      if (current && prioritized.some((result) => result.result_id === current)) return current;
      return prioritized[0]?.result_id ?? null;
    });
    setResultsStatus(payload.results.length > 0 ? "Results loaded" : "No ingested results");
    return prioritized;
  }

  async function handleRefreshResults() {
    setResultsError(null);
    setResultsStatus("Refreshing results");
    try {
      await refreshResults();
    } catch (caught) {
      setResults([]);
      setSelectedResultId(null);
      setResultsError(caught instanceof Error ? caught.message : "Could not load results.");
      setResultsStatus("Results unavailable");
    }
  }

  async function handleIngestRun() {
    if (!dryRun) return;
    setRunWorkflowError(null);
    setStatus("Ingesting completed CM1 output");
    try {
      const ingested = await ingestCompletedRun(dryRun.manifest_path);
      setIngestedResultId(ingested.result_id);
      await refreshResults(ingested.result_id);
      setStatus("Ingested result metadata");
    } catch (caught) {
      setRunWorkflowError(
        caught instanceof Error ? caught.message : "Unable to ingest completed CM1 output.",
      );
      setStatus("Ingest blocked");
    }
  }

  function updateResultInList(updated: ResultCard) {
    setResults((current) =>
      prioritizeResults(
        current.map((result) => (result.result_id === updated.result_id ? updated : result)),
      ),
    );
    setSelectedResultId(updated.result_id);
  }

  async function handleResultUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedResult) return;
    setResultsError(null);
    setResultsStatus("Updating result card");
    try {
      const updated = await patchResultCard(selectedResult.result_id, {
        name: resultDraft.name,
        tags: parseTags(resultDraft.tags),
        notes: resultDraft.notes,
      });
      updateResultInList(updated);
      setResultsStatus("Result card updated");
    } catch (caught) {
      setResultsError(caught instanceof Error ? caught.message : "Unable to update result card.");
      setResultsStatus("Results loaded");
    }
  }

  async function handleResultSave() {
    if (!selectedResult) return;
    setResultsError(null);
    setResultsStatus("Saving result card");
    try {
      const saved = await saveResultCard(selectedResult.result_id);
      updateResultInList(saved);
      setResultsStatus("Result card saved");
    } catch (caught) {
      setResultsError(caught instanceof Error ? caught.message : "Unable to save result card.");
      setResultsStatus("Results loaded");
    }
  }

  async function handleRefreshStorage() {
    setStorageError(null);
    setStorageStatus("Refreshing storage inventory");
    setDeletePreview(null);
    setDeleteMessage(null);
    try {
      const payload = await fetchStorageInventory();
      setStorageInventory(payload);
      setStorageStatus(payload.runs.length > 0 ? "Storage inventory loaded" : "No runtime runs");
    } catch (caught) {
      setStorageError(
        caught instanceof Error ? caught.message : "Unable to load runtime storage inventory.",
      );
      setStorageStatus("Storage unavailable");
    }
  }

  async function handlePreviewRunDelete(runId: string) {
    setStorageError(null);
    setDeleteMessage(null);
    setStorageStatus("Preparing delete preview");
    try {
      const preview = await requestRunDeletePreview(runId);
      setDeletePreview(preview);
      setStorageStatus("Delete preview ready");
    } catch (caught) {
      setStorageError(caught instanceof Error ? caught.message : "Unable to preview run deletion.");
      setStorageStatus("Storage inventory loaded");
    }
  }

  async function handleConfirmRunDelete(runId: string) {
    setStorageError(null);
    setStorageStatus("Deleting selected run");
    try {
      const deleted = await confirmRunDelete(runId);
      setDeleteMessage(`${deleted.message} Reclaimed ${formatBytes(deleted.size_bytes)}.`);
      setDeletePreview(null);
      const payload = await fetchStorageInventory();
      setStorageInventory(payload);
      setStorageStatus("Run deleted");
    } catch (caught) {
      setStorageError(caught instanceof Error ? caught.message : "Unable to delete selected run.");
      setStorageStatus("Delete failed");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local CM1 experiment lab</p>
          <h1>Cloud Chamber</h1>
        </div>
        <p className="state-chip">{sectionLabel(activeSection)}</p>
      </header>

      <nav className="workspace-nav" aria-label="Cloud Chamber workspace">
        {(["build", "results", "explore"] as WorkspaceSection[]).map((section) => (
          <button
            key={section}
            type="button"
            className={activeSection === section ? "active-control" : ""}
            onClick={() => setActiveSection(section)}
          >
            {sectionLabel(section)}
          </button>
        ))}
      </nav>

      {activeSection === "build" && (
        <BuildWorkspace
          status={status}
          scenarioLoadState={scenarioLoadState}
          scenarioError={scenarioError}
          packageError={error}
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          selectedScenarioId={selectedScenarioId}
          controls={controls}
          runSizePreset={runSizePreset}
          validationMessages={validationMessages}
          dryRun={dryRun}
          runStatus={runStatus}
          runWorkflowError={runWorkflowError}
          ingestedResultId={ingestedResultId}
          onSelectScenario={setSelectedScenarioId}
          onControlChange={(id, value) =>
            setControls((current) => ({
              ...current,
              [id]: value,
            }))
          }
          onRunSizeChange={setRunSizePreset}
          onDryRun={handleDryRun}
          onLaunchRun={handleLaunchRun}
          onRefreshRunStatus={handleRefreshRunStatus}
          onIngestRun={handleIngestRun}
          onOpenInResults={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("results");
            setActiveResultsTab("notebook");
          }}
          onInspectIngested={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("explore");
            setActiveExploreTab("slices");
          }}
          onVisualizeIngested={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("explore");
            setActiveExploreTab("view3d");
          }}
          onRetryScenarios={() => {
            void loadScenarios();
          }}
        />
      )}

      {activeSection === "results" && (
        <ResultsWorkspace
          activeTab={activeResultsTab}
          results={results}
          selectedResult={selectedResult}
          selectedResultId={selectedResult?.result_id ?? null}
          resultsStatus={resultsStatus}
          resultsError={resultsError}
          comparisonPair={comparisonPair}
          storageInventory={storageInventory}
          storageStatus={storageStatus}
          storageError={storageError}
          deletePreview={deletePreview}
          deleteMessage={deleteMessage}
          onTabChange={setActiveResultsTab}
          draft={resultDraft}
          onSelectResult={setSelectedResultId}
          onDraftChange={setResultDraft}
          onSubmit={handleResultUpdate}
          onSave={handleResultSave}
          onRefreshResults={handleRefreshResults}
          onInspect={() => {
            setActiveSection("explore");
            setActiveExploreTab("slices");
          }}
          onOpenVisualizer={() => {
            setActiveSection("explore");
            setActiveExploreTab("view3d");
          }}
          onCompareInspect={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
            setActiveExploreTab("slices");
          }}
          onCompareVisualize={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
            setActiveExploreTab("view3d");
          }}
          onStorageOpenResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveResultsTab("notebook");
          }}
          onStorageExploreResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
            setActiveExploreTab("slices");
          }}
          onRefreshStorage={handleRefreshStorage}
          onPreviewDelete={handlePreviewRunDelete}
          onConfirmDelete={handleConfirmRunDelete}
        />
      )}

      {activeSection === "explore" && (
        <ExploreWorkspace
          activeTab={activeExploreTab}
          selectedResult={selectedResult}
          onTabChange={setActiveExploreTab}
        />
      )}
    </main>
  );
}

function BuildWorkspace({
  status,
  scenarioLoadState,
  scenarioError,
  packageError,
  scenarios,
  selectedScenario,
  selectedScenarioId,
  controls,
  runSizePreset,
  validationMessages,
  dryRun,
  runStatus,
  runWorkflowError,
  ingestedResultId,
  onSelectScenario,
  onControlChange,
  onRunSizeChange,
  onDryRun,
  onLaunchRun,
  onRefreshRunStatus,
  onIngestRun,
  onOpenInResults,
  onInspectIngested,
  onVisualizeIngested,
  onRetryScenarios,
}: {
  status: string;
  scenarioLoadState: ScenarioLoadState;
  scenarioError: string | null;
  packageError: string | null;
  scenarios: Scenario[];
  selectedScenario: Scenario | undefined;
  selectedScenarioId: string;
  controls: Record<string, string | number | boolean>;
  runSizePreset: string;
  validationMessages: string[];
  dryRun: DryRunResponse | null;
  runStatus: RunStatusResponse | null;
  runWorkflowError: string | null;
  ingestedResultId: string | null;
  onSelectScenario: (scenarioId: string) => void;
  onControlChange: (controlId: string, value: string) => void;
  onRunSizeChange: (presetId: string) => void;
  onDryRun: (event: FormEvent<HTMLFormElement>) => void;
  onLaunchRun: () => void;
  onRefreshRunStatus: () => void;
  onIngestRun: () => void;
  onOpenInResults: () => void;
  onInspectIngested: () => void;
  onVisualizeIngested: () => void;
  onRetryScenarios: () => void;
}) {
  const scenarioControlsReady = scenarioLoadState === "loaded" && selectedScenario !== undefined;

  return (
    <section className="workspace-section" aria-labelledby="build-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Build</p>
          <h2 id="build-title">Create a CM1 run package</h2>
        </div>
        <p className="state-chip">{status}</p>
      </div>

      <section className="builder-layout" aria-label="Scenario Builder">
        <form className="builder-panel" onSubmit={onDryRun}>
          <label className="field-label" htmlFor="scenario">
            Scenario
          </label>
          <select
            id="scenario"
            value={scenarioControlsReady ? selectedScenarioId : ""}
            disabled={!scenarioControlsReady}
            onChange={(event) => onSelectScenario(event.target.value)}
          >
            {!scenarioControlsReady && <option value="">Scenario unavailable</option>}
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.display_name}
              </option>
            ))}
          </select>

          {scenarioLoadState === "loading" && (
            <ScenarioStatePanel
              title="Loading scenario catalog"
              body="Cloud Chamber is waiting for the local backend to return available CM1 scenario templates. Package controls will appear after a scenario is loaded."
            />
          )}

          {scenarioLoadState === "failed" && (
            <ScenarioStatePanel
              title="Scenario catalog unavailable"
              body={`Cloud Chamber could not load scenario templates from the local backend. ${
                scenarioError ?? "The backend may be stopped or temporarily unavailable."
              }`}
              actionLabel="Retry scenarios"
              onAction={onRetryScenarios}
            />
          )}

          {scenarioLoadState === "empty" && (
            <ScenarioStatePanel
              title="No scenarios available"
              body="The local backend responded, but it did not return any scenario templates. Package generation is unavailable until at least one scenario is configured."
              actionLabel="Retry scenarios"
              onAction={onRetryScenarios}
            />
          )}

          {scenarioControlsReady && (
            <>
              <div className="hero-case">
                <p className="eyebrow">First Golden Path hero case</p>
                <h2>{selectedScenario.display_name}</h2>
                <p>{selectedScenario.description}</p>
              </div>

              <section aria-labelledby="physical-question-title">
                <h3 id="physical-question-title">Physical Question</h3>
                <p>{selectedScenario.physical_question}</p>
              </section>

              <section aria-labelledby="controls-title">
                <h3 id="controls-title">Curated Atmospheric Controls</h3>
                {selectedScenario.controls.map((control) => (
                  <div className="control-row" key={control.id}>
                    <span>
                      <label htmlFor={`control-${control.id}`}>
                        <strong>{control.label}</strong>
                      </label>
                      <small>{control.description}</small>
                    </span>
                    <select
                      id={`control-${control.id}`}
                      value={String(controls[control.id] ?? control.default)}
                      onChange={(event) => onControlChange(control.id, event.target.value)}
                    >
                      {control.options.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </section>

              <label className="field-label" htmlFor="run-size">
                Run-size preset
              </label>
              <select
                id="run-size"
                value={runSizePreset}
                onChange={(event) => onRunSizeChange(event.target.value)}
              >
                {selectedScenario.run_size_presets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.label}
                  </option>
                ))}
              </select>

              {validationMessages.length > 0 && (
                <div className="validation" role="alert">
                  {validationMessages.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                </div>
              )}

              {packageError && (
                <div className="validation" role="alert">
                  <p>{packageError}</p>
                </div>
              )}

              <button
                type="submit"
                data-testid="create-package-btn"
                disabled={validationMessages.length > 0}
              >
                Create run package
              </button>
            </>
          )}
        </form>

        <aside className="side-stack">
          <section className="status-panel secondary-panel" aria-labelledby="preview-title">
            <p className="eyebrow">Future guidance</p>
            <h3 id="preview-title">Preview estimate not implemented</h3>
            <p>
              Future preview estimates will be guidance only. This panel is not CM1 output, not a
              completed result, and not a visualization interpretation.
            </p>
          </section>

          <section
            className="status-panel"
            aria-labelledby="review-title"
            data-testid="package-review-panel"
          >
            <p className="eyebrow">Generated package</p>
            <h3 id="review-title">Review before local CM1 run</h3>
            {dryRun ? (
              <GuidedRunWorkflow
                dryRun={dryRun}
                runStatus={runStatus}
                error={runWorkflowError}
                ingestedResultId={ingestedResultId}
                onLaunchRun={onLaunchRun}
                onRefreshRunStatus={onRefreshRunStatus}
                onIngestRun={onIngestRun}
                onOpenInResults={onOpenInResults}
                onInspectIngested={onInspectIngested}
                onVisualizeIngested={onVisualizeIngested}
              />
            ) : (
              <p>
                Create a package to review the manifest, CM1 inputs, runtime checklist, and run
                report before launching local CM1 or ingesting a saved result.
              </p>
            )}
          </section>
        </aside>
      </section>
    </section>
  );
}

function ScenarioStatePanel({
  title,
  body,
  actionLabel,
  onAction,
}: {
  title: string;
  body: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <section className="scenario-state-panel" aria-live="polite">
      <h3>{title}</h3>
      <p>{body}</p>
      {actionLabel && onAction && (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </section>
  );
}

function ResultsWorkspace({
  activeTab,
  results,
  selectedResult,
  selectedResultId,
  resultsStatus,
  resultsError,
  comparisonPair,
  storageInventory,
  storageStatus,
  storageError,
  deletePreview,
  deleteMessage,
  onTabChange,
  draft,
  onSelectResult,
  onDraftChange,
  onSubmit,
  onSave,
  onRefreshResults,
  onInspect,
  onOpenVisualizer,
  onCompareInspect,
  onCompareVisualize,
  onStorageOpenResult,
  onStorageExploreResult,
  onRefreshStorage,
  onPreviewDelete,
  onConfirmDelete,
}: {
  activeTab: ResultsTab;
  results: ResultCard[];
  selectedResult: ResultCard | undefined;
  selectedResultId: string | null;
  resultsStatus: string;
  resultsError: string | null;
  comparisonPair: { baseline: ResultCard | undefined; dryFailed: ResultCard | undefined };
  storageInventory: StorageInventoryResponse | null;
  storageStatus: string;
  storageError: string | null;
  deletePreview: DeleteRunResponse | null;
  deleteMessage: string | null;
  onTabChange: (tab: ResultsTab) => void;
  draft: { name: string; tags: string; notes: string };
  onSelectResult: (resultId: string) => void;
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSave: () => void;
  onRefreshResults: () => void;
  onInspect: () => void;
  onOpenVisualizer: () => void;
  onCompareInspect: (resultId: string) => void;
  onCompareVisualize: (resultId: string) => void;
  onStorageOpenResult: (resultId: string) => void;
  onStorageExploreResult: (resultId: string) => void;
  onRefreshStorage: () => void;
  onPreviewDelete: (runId: string) => void;
  onConfirmDelete: (runId: string) => void;
}) {
  return (
    <section className="results-library" aria-labelledby="results-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Results</p>
          <h2 id="results-title">Review, compare, and manage experiments</h2>
        </div>
        <p className="state-chip">{resultsStatus}</p>
      </div>

      <nav className="subtab-nav" role="tablist" aria-label="Results views">
        {(["notebook", "compare", "storage"] as ResultsTab[]).map((tab) => (
          <button
            key={tab}
            type="button"
            id={`${tab}-tab`}
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`${tab}-panel`}
            className={activeTab === tab ? "active-control" : ""}
            onClick={() => onTabChange(tab)}
          >
            {resultsTabLabel(tab)}
          </button>
        ))}
      </nav>

      {selectedResult && (
        <section className="featured-result" aria-label="Selected result">
          <div>
            <p className="eyebrow">Selected experiment</p>
            <h3>{selectedResult.name}</h3>
            <p>
              {selectedResult.scenario_name ?? selectedResult.scenario_id} ·{" "}
              {humanize(selectedResult.run_size_preset)}
            </p>
          </div>
          <div className="badge-row">
            {isValidatedQuickLookBaseline(selectedResult) && (
              <StatusBadge label="Validated quick-look baseline" tone="good" />
            )}
            <OutcomeBadge result={selectedResult} />
            <StatusBadge label={rainOutcome(selectedResult.rain_present)} tone="neutral" />
            {selectedResult.saved || selectedResult.protected ? (
              <StatusBadge label="Saved" tone="good" />
            ) : (
              <StatusBadge label="Unsaved" tone="neutral" />
            )}
          </div>
          <div className="button-row">
            <button type="button" onClick={onInspect}>
              Open in Explore
            </button>
            <button type="button" onClick={onOpenVisualizer}>
              Open 3-D
            </button>
          </div>
        </section>
      )}

      {resultsError && <p role="alert">{resultsError}</p>}

      {activeTab === "notebook" && (
        <NotebookWorkspace
          results={results}
          selectedResult={selectedResult}
          selectedResultId={selectedResultId}
          draft={draft}
          onSelectResult={onSelectResult}
          onDraftChange={onDraftChange}
          onSubmit={onSubmit}
          onSave={onSave}
          onRefreshResults={onRefreshResults}
          onInspect={onInspect}
          onOpenVisualizer={onOpenVisualizer}
        />
      )}

      {activeTab === "compare" && (
        <ComparisonWorkspace
          pair={comparisonPair}
          onInspect={onCompareInspect}
          onVisualize={onCompareVisualize}
          onSelectInNotebook={(resultId) => {
            onSelectResult(resultId);
            onTabChange("notebook");
          }}
        />
      )}

      {activeTab === "storage" && (
        <StorageWorkspace
          inventory={storageInventory}
          results={results}
          status={storageStatus}
          error={storageError}
          deletePreview={deletePreview}
          deleteMessage={deleteMessage}
          onRefresh={onRefreshStorage}
          onPreviewDelete={onPreviewDelete}
          onConfirmDelete={onConfirmDelete}
          onOpenResult={onStorageOpenResult}
          onExploreResult={onStorageExploreResult}
        />
      )}
    </section>
  );
}

function NotebookWorkspace({
  results,
  selectedResult,
  selectedResultId,
  draft,
  onSelectResult,
  onDraftChange,
  onSubmit,
  onSave,
  onRefreshResults,
  onInspect,
  onOpenVisualizer,
}: {
  results: ResultCard[];
  selectedResult: ResultCard | undefined;
  selectedResultId: string | null;
  draft: { name: string; tags: string; notes: string };
  onSelectResult: (resultId: string) => void;
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSave: () => void;
  onRefreshResults: () => void;
  onInspect: () => void;
  onOpenVisualizer: () => void;
}) {
  return (
    <section
      className="workspace-section"
      role="tabpanel"
      id="notebook-panel"
      aria-labelledby="notebook-tab notebook-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Notebook</p>
          <h3 id="notebook-title">Experiment Notebook</h3>
        </div>
        <button type="button" onClick={onRefreshResults}>
          Refresh results
        </button>
      </div>
      <div className="results-layout">
        <ResultsTable
          results={results}
          selectedResultId={selectedResultId}
          onSelect={onSelectResult}
        />
        <ResultNotebookCard
          result={selectedResult}
          draft={draft}
          onDraftChange={onDraftChange}
          onSubmit={onSubmit}
          onSave={onSave}
          onInspect={onInspect}
          onOpenVisualizer={onOpenVisualizer}
        />
      </div>
    </section>
  );
}

function ExploreWorkspace({
  activeTab,
  selectedResult,
  onTabChange,
}: {
  activeTab: ExploreTab;
  selectedResult: ResultCard | undefined;
  onTabChange: (tab: ExploreTab) => void;
}) {
  return (
    <section className="workspace-section" aria-labelledby="explore-workspace-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Explore</p>
          <h2 id="explore-workspace-title">Inspect and visualize fields</h2>
        </div>
        <p className="state-chip">{selectedResult ? selectedResult.name : "No result"}</p>
      </div>

      <nav className="subtab-nav" role="tablist" aria-label="Explore views">
        {(["slices", "view3d"] as ExploreTab[]).map((tab) => (
          <button
            key={tab}
            type="button"
            id={`${tab}-tab`}
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`${tab}-panel`}
            className={activeTab === tab ? "active-control" : ""}
            onClick={() => onTabChange(tab)}
          >
            {exploreTabLabel(tab)}
          </button>
        ))}
      </nav>

      {!selectedResult && (
        <section
          className="status-panel"
          role="tabpanel"
          id={`${activeTab}-panel`}
          aria-labelledby={`${activeTab}-tab`}
        >
          <p>Select an ingested result from Results to inspect or visualize it.</p>
        </section>
      )}

      {selectedResult && activeTab === "slices" && (
        <section
          role="tabpanel"
          id="slices-panel"
          aria-labelledby="slices-tab explore-slices-title"
        >
          <p className="eyebrow">2-D Slices</p>
          <h3 id="explore-slices-title">2-D Slices</h3>
          <FieldInspector result={selectedResult} />
        </section>
      )}

      {selectedResult && activeTab === "view3d" && (
        <section role="tabpanel" id="view3d-panel" aria-labelledby="view3d-tab explore-3d-title">
          <p className="eyebrow">3-D View</p>
          <h3 id="explore-3d-title">3-D View</h3>
          <VisualizerSceneShell result={selectedResult} />
        </section>
      )}
    </section>
  );
}

function ComparisonWorkspace({
  pair,
  onInspect,
  onVisualize,
  onSelectInNotebook,
}: {
  pair: { baseline: ResultCard | undefined; dryFailed: ResultCard | undefined };
  onInspect: (resultId: string) => void;
  onVisualize: (resultId: string) => void;
  onSelectInNotebook: (resultId: string) => void;
}) {
  const missing = comparisonMissingItems(pair);

  return (
    <section
      className="comparison-workspace"
      role="tabpanel"
      id="compare-panel"
      aria-labelledby="compare-tab comparison-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Compare</p>
          <h2 id="comparison-title">Baseline vs Dry Failed Cumulus</h2>
        </div>
        <p className="state-chip">
          {missing.length === 0 ? "Lab pair ready" : "Waiting for lab pair"}
        </p>
      </div>

      {missing.length > 0 ? (
        <section className="status-panel" aria-label="Comparison requirements">
          <h3>Comparison needs Baseline and Dry Failed results</h3>
          <p>
            Ingested quick-look results are needed before Cloud Chamber can compare cloud-forming
            and moisture-limited outcomes.
          </p>
          <ul className="compact-list">
            {missing.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : (
        <>
          <section className="comparison-intro">
            <p>
              This comparison shows the first useful Cloud Chamber lab pair: Baseline Shallow
              Cumulus forms cloud, while Dry Failed Cumulus is an intentional moisture-limited
              contrast with vertical motion but little or no cloud water.
            </p>
            <p>
              Dry Failed Cumulus is not a failed model run when thermals are present and cloud water
              stays below threshold. It teaches how low-level moisture changes the outcome.
            </p>
          </section>

          <div className="comparison-grid">
            <ComparisonResultCard
              roleLabel="Baseline"
              result={pair.baseline}
              onInspect={onInspect}
              onVisualize={onVisualize}
              onSelectInNotebook={onSelectInNotebook}
            />
            <ComparisonResultCard
              roleLabel="Dry Failed"
              result={pair.dryFailed}
              onInspect={onInspect}
              onVisualize={onVisualize}
              onSelectInNotebook={onSelectInNotebook}
            />
          </div>

          <section className="comparison-interpretation" aria-labelledby="comparison-meaning-title">
            <h3 id="comparison-meaning-title">What changed?</h3>
            <dl className="metric-grid">
              <Metric label="Baseline" value={comparisonMeaning(pair.baseline)} />
              <Metric label="Dry Failed" value={comparisonMeaning(pair.dryFailed)} />
              <Metric
                label="Learning target"
                value="Compare qc against w to see moisture limitation separate from vertical motion."
              />
              <Metric
                label="Slice comparison"
                value="Use the field comparison below for side-by-side CM1-derived qc and w slices."
              />
            </dl>
          </section>

          <SliceComparisonPanel baseline={pair.baseline} dryFailed={pair.dryFailed} />

          <details>
            <summary>Technical comparison details</summary>
            <div className="comparison-grid">
              <ComparisonTechnicalDetails title="Baseline provenance" result={pair.baseline} />
              <ComparisonTechnicalDetails title="Dry Failed provenance" result={pair.dryFailed} />
            </div>
          </details>
        </>
      )}
    </section>
  );
}

function ComparisonResultCard({
  roleLabel,
  result,
  onInspect,
  onVisualize,
  onSelectInNotebook,
}: {
  roleLabel: "Baseline" | "Dry Failed";
  result: ResultCard | undefined;
  onInspect: (resultId: string) => void;
  onVisualize: (resultId: string) => void;
  onSelectInNotebook: (resultId: string) => void;
}) {
  if (!result) return null;
  const moistureLimited = isDryFailedContrast(result);

  return (
    <section className="comparison-card" aria-label={`${roleLabel} result`}>
      <div className="comparison-card-header">
        <div>
          <p className="eyebrow">{roleLabel}</p>
          <h3>{result.scenario_name ?? result.scenario_id}</h3>
          <p>{humanize(result.run_size_preset)} result card</p>
        </div>
        <StatusBadge
          label={result.saved || result.protected ? "Saved" : "Unsaved"}
          tone={result.saved || result.protected ? "good" : "neutral"}
        />
      </div>

      <div className="badge-row">
        <OutcomeBadge result={result} />
        <StatusBadge label={rainOutcome(result.rain_present)} tone="neutral" />
        {moistureLimited && <StatusBadge label="Moisture-limited" tone="warning" />}
        {result.caveats.length > 0 && (
          <StatusBadge label={caveatLabel(result)} tone={caveatTone(result)} />
        )}
      </div>

      <dl className="metric-grid">
        <Metric label="Scenario" value={result.scenario_name ?? result.scenario_id} />
        <Metric label="Run-size preset" value={humanize(result.run_size_preset)} />
        <Metric
          label="Diagnostics"
          value={result.diagnostics_summary ?? "Diagnostics unavailable"}
        />
        <Metric label="Cloud" value={cloudOutcome(result)} />
        <Metric label="First cloud time" value={formatSeconds(result.first_cloud_time_seconds)} />
        <Metric label="Rain" value={rainOutcome(result.rain_present)} />
        <Metric label="Max qc" value={formatScientific(result.max_qc_kg_kg, "kg/kg")} />
        <Metric label="Max w" value={formatNumber(result.max_w_m_s, "m/s")} />
        <Metric label="Min w" value={formatNumber(result.min_w_m_s, "m/s")} />
        <Metric label="Output" value={outputSummary(result.output_file_summary)} />
      </dl>

      <section aria-labelledby={`${result.result_id}-caveats`}>
        <h4 id={`${result.result_id}-caveats`}>Caveats / warnings</h4>
        {result.caveats.length > 0 ? (
          <ul className="compact-list">
            {result.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        ) : (
          <p>No caveats recorded.</p>
        )}
      </section>

      <div className="button-row">
        <button type="button" onClick={() => onInspect(result.result_id)}>
          Open {roleLabel} in Explore
        </button>
        <button type="button" onClick={() => onVisualize(result.result_id)}>
          Open {roleLabel} 3-D
        </button>
        <button type="button" onClick={() => onSelectInNotebook(result.result_id)}>
          Select {roleLabel} in Notebook
        </button>
      </div>
    </section>
  );
}

function SliceComparisonPanel({
  baseline,
  dryFailed,
}: {
  baseline: ResultCard | undefined;
  dryFailed: ResultCard | undefined;
}) {
  const [fieldName, setFieldName] = useState("qc");
  const [orientation, setOrientation] = useState<"horizontal" | "vertical_x">("vertical_x");
  const [timeIndex, setTimeIndex] = useState(0);
  const [catalogs, setCatalogs] = useState<{
    baseline: FieldCatalogResponse;
    dryFailed: FieldCatalogResponse;
  } | null>(null);
  const [slices, setSlices] = useState<{
    baseline: SliceResponse;
    dryFailed: SliceResponse;
  } | null>(null);
  const [status, setStatus] = useState("Loading field catalogs...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!baseline || !dryFailed) return;
    let active = true;
    setCatalogs(null);
    setSlices(null);
    setError(null);
    setStatus("Loading field catalogs...");
    Promise.all([
      fetchVisualizationFields(baseline.result_id),
      fetchVisualizationFields(dryFailed.result_id),
    ])
      .then(([baselineCatalog, dryFailedCatalog]) => {
        if (!active) return;
        setCatalogs({ baseline: baselineCatalog, dryFailed: dryFailedCatalog });
        const preferred = ["qc", "w"].find((candidate) =>
          bothCatalogsContainField(baselineCatalog, dryFailedCatalog, candidate),
        );
        setFieldName(preferred ?? baselineCatalog.available_fields[0]?.raw_field_name ?? "");
        setTimeIndex(
          interestingTimeIndexForComparison(baselineCatalog, dryFailedCatalog, preferred),
        );
        setStatus("Field catalogs loaded");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setError(caught instanceof Error ? caught.message : "Unable to load comparison fields.");
        setStatus("Comparison unavailable");
      });
    return () => {
      active = false;
    };
  }, [baseline, dryFailed]);

  const baselineField = useMemo(
    () => catalogs?.baseline.available_fields.find((field) => field.raw_field_name === fieldName),
    [catalogs, fieldName],
  );
  const dryFailedField = useMemo(
    () => catalogs?.dryFailed.available_fields.find((field) => field.raw_field_name === fieldName),
    [catalogs, fieldName],
  );
  const comparableFields = useMemo(() => {
    if (!catalogs) return [];
    return ["qc", "w"].filter((candidate) =>
      bothCatalogsContainField(catalogs.baseline, catalogs.dryFailed, candidate),
    );
  }, [catalogs]);
  const timeOptions =
    baselineField?.time_coordinate_values ?? dryFailedField?.time_coordinate_values ?? [];
  const clampedTimeIndex = clampIndex(timeIndex, timeOptions.length || 1);
  const levelIndex = comparisonLevelIndex(baselineField, orientation);
  const timeMismatch = Boolean(
    baselineField &&
    dryFailedField &&
    JSON.stringify(baselineField.time_coordinate_values) !==
      JSON.stringify(dryFailedField.time_coordinate_values),
  );

  useEffect(() => {
    if (!baseline || !dryFailed || !baselineField || !dryFailedField || !fieldName) return;
    let active = true;
    setSlices(null);
    setError(null);
    setStatus("Loading comparison slices...");
    Promise.all([
      fetchVisualizationSlice(baseline.result_id, {
        field: fieldName,
        timeIndex: clampedTimeIndex,
        orientation,
        levelIndex,
      }),
      fetchVisualizationSlice(dryFailed.result_id, {
        field: fieldName,
        timeIndex: clampedTimeIndex,
        orientation,
        levelIndex,
      }),
    ])
      .then(([baselineSlice, dryFailedSlice]) => {
        if (!active) return;
        setSlices({ baseline: baselineSlice, dryFailed: dryFailedSlice });
        setStatus("Comparison slices loaded");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setError(caught instanceof Error ? caught.message : "Unable to load comparison slices.");
        setStatus("Comparison slice unavailable");
      });
    return () => {
      active = false;
    };
  }, [
    baseline,
    dryFailed,
    baselineField,
    dryFailedField,
    fieldName,
    clampedTimeIndex,
    orientation,
    levelIndex,
  ]);

  if (!baseline || !dryFailed) return null;

  return (
    <section className="slice-comparison-panel" aria-labelledby="slice-comparison-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">2-D field comparison</p>
          <h3 id="slice-comparison-title">Baseline vs Dry Failed slices</h3>
        </div>
        <p className="state-chip">{status}</p>
      </div>

      <p>
        Dry Failed Cumulus is an intentional moisture-limited contrast when vertical motion is
        present and cloud water remains below threshold. These slices are CM1-derived backend
        payloads; the browser is not parsing raw NetCDF.
      </p>

      {error && <p role="alert">{error}</p>}

      <div className="comparison-controls">
        <label>
          Field
          <select
            aria-label="Comparison field"
            value={fieldName}
            onChange={(event) => setFieldName(event.target.value)}
          >
            {comparableFields.length > 0 ? (
              comparableFields.map((candidate) => (
                <option key={candidate} value={candidate}>
                  {candidate} ({candidate === "qc" ? "Cloud water" : "Vertical velocity"})
                </option>
              ))
            ) : (
              <option value="">No shared qc/w fields</option>
            )}
          </select>
        </label>

        <label>
          Time
          <input
            aria-label="Comparison time"
            type="range"
            min="0"
            max={Math.max(0, timeOptions.length - 1)}
            value={clampedTimeIndex}
            onChange={(event) => setTimeIndex(Number(event.target.value))}
            disabled={timeOptions.length === 0}
          />
          <span>{formatTimeValue(timeOptions[clampedTimeIndex] ?? null)}</span>
        </label>

        <fieldset>
          <legend>Slice orientation</legend>
          <div className="segmented-buttons">
            <button
              type="button"
              className={orientation === "horizontal" ? "active-control" : ""}
              onClick={() => setOrientation("horizontal")}
            >
              Horizontal
            </button>
            <button
              type="button"
              className={orientation === "vertical_x" ? "active-control" : ""}
              onClick={() => setOrientation("vertical_x")}
            >
              Vertical x-z
            </button>
          </div>
        </fieldset>
      </div>

      {timeMismatch && (
        <p className="validation" role="status">
          Output times differ between these results. The comparison uses the selected output index
          and labels each slice with its own time metadata.
        </p>
      )}

      {comparableFields.length === 0 && (
        <section className="status-panel">
          <p>These results do not share qc or w visualization-ready fields.</p>
        </section>
      )}

      {slices && (
        <div className="slice-comparison-grid">
          <ComparedSliceCard roleLabel="Baseline" result={baseline} slice={slices.baseline} />
          <ComparedSliceCard roleLabel="Dry Failed" result={dryFailed} slice={slices.dryFailed} />
        </div>
      )}
    </section>
  );
}

function ComparedSliceCard({
  roleLabel,
  result,
  slice,
}: {
  roleLabel: string;
  result: ResultCard;
  slice: SliceResponse;
}) {
  return (
    <section className="slice-panel" aria-label={`${roleLabel} comparison slice`}>
      <div className="notebook-title">
        <div>
          <p className="eyebrow">{roleLabel}</p>
          <h4>{result.scenario_name ?? result.scenario_id}</h4>
        </div>
        <StatusBadge
          label={cloudOutcome(result)}
          tone={cloudOutcome(result) === "Cloud formed" ? "good" : "warning"}
        />
      </div>
      <SliceHeatmap title={`${roleLabel} ${slice.field.raw_field_name} comparison`} slice={slice} />
      <dl className="metric-grid">
        <Metric
          label="Field"
          value={`${slice.field.raw_field_name} (${slice.field.display_name})`}
        />
        <Metric label="Units" value={slice.field.units ?? "Units unavailable"} />
        <Metric label="Time" value={formatSeconds(slice.selection.time_seconds)} />
        <Metric label="Orientation" value={humanize(slice.selection.orientation)} />
        <Metric label="Min" value={formatMaybeNumber(slice.stats.min, slice.field.units)} />
        <Metric label="Max" value={formatMaybeNumber(slice.stats.max, slice.field.units)} />
        <Metric label="Finite cells" value={slice.stats.finite_count.toLocaleString()} />
        <Metric label="Non-finite cells" value={slice.stats.non_finite_count.toLocaleString()} />
      </dl>
      <details>
        <summary>Provenance labels</summary>
        <ul className="compact-list">
          <li>{slice.provenance.provenance_label}</li>
          <li>Processing method: {slice.provenance.processing_method}</li>
          <li>Rendering method: {slice.provenance.rendering_method}</li>
          {slice.caveats.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}

function ComparisonTechnicalDetails({
  title,
  result,
}: {
  title: string;
  result: ResultCard | undefined;
}) {
  if (!result) return null;
  return (
    <section className="status-panel" aria-label={title}>
      <h3>{title}</h3>
      <dl className="metric-grid">
        <Metric label="Run ID" value={result.run_id} />
        <Metric label="Result ID" value={result.result_id} />
        <Metric label="Source model" value={result.source_model} />
        <Metric label="Lifecycle" value={result.source_lifecycle_state} />
        <Metric label="Product state" value={result.source_product_state} />
        <Metric label="Result state" value={result.status} />
      </dl>
      <h4>Physical question</h4>
      <p>{result.physical_question}</p>
      <h4>Controls used</h4>
      {Object.keys(result.controls).length > 0 ? (
        <ul className="compact-list">
          {Object.entries(result.controls).map(([key, value]) => (
            <li key={key}>
              {humanize(key)}: {String(value)}
            </li>
          ))}
        </ul>
      ) : (
        <p>No controls recorded.</p>
      )}
      <h4>Provenance labels</h4>
      <ul className="tag-list">
        {result.provenance_labels.map((label) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
    </section>
  );
}

function StorageWorkspace({
  inventory,
  results,
  status,
  error,
  deletePreview,
  deleteMessage,
  onRefresh,
  onPreviewDelete,
  onConfirmDelete,
  onOpenResult,
  onExploreResult,
}: {
  inventory: StorageInventoryResponse | null;
  results: ResultCard[];
  status: string;
  error: string | null;
  deletePreview: DeleteRunResponse | null;
  deleteMessage: string | null;
  onRefresh: () => void;
  onPreviewDelete: (runId: string) => void;
  onConfirmDelete: (runId: string) => void;
  onOpenResult: (resultId: string) => void;
  onExploreResult: (resultId: string) => void;
}) {
  return (
    <section
      className="storage-workspace"
      role="tabpanel"
      id="storage-panel"
      aria-labelledby="storage-tab storage-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Storage</p>
          <h2 id="storage-title">Runtime storage cleanup</h2>
        </div>
        <p className="state-chip">{status}</p>
      </div>

      {error && <p role="alert">{error}</p>}
      {deleteMessage && <p role="status">{deleteMessage}</p>}

      <section className="storage-summary" aria-label="Runtime storage summary">
        <dl className="metric-grid">
          <Metric label="Runtime home" value={inventory?.runtime_home ?? "Unavailable"} />
          <Metric label="Runs directory" value={inventory?.runs_directory ?? "Unavailable"} />
          <Metric
            label="Total runtime-home size"
            value={inventory ? formatBytes(inventory.total_size_bytes) : "Unavailable"}
          />
          <Metric
            label="Warning threshold"
            value={inventory ? formatBytes(inventory.warning_threshold_bytes) : "Unavailable"}
          />
          <Metric
            label="Threshold status"
            value={
              inventory
                ? inventory.above_warning_threshold
                  ? "At or above 50 GB warning threshold"
                  : "Below 50 GB warning threshold"
                : "Unavailable"
            }
          />
          <Metric label="Run directories" value={String(inventory?.runs.length ?? 0)} />
        </dl>
        {inventory?.warning_message && (
          <p className="validation" role="status">
            {inventory.warning_message}
          </p>
        )}
        <div className="button-row">
          <button type="button" onClick={onRefresh}>
            Refresh storage
          </button>
        </div>
      </section>

      {deletePreview && (
        <section className="delete-preview" aria-label="Delete preview">
          <h3>Delete preview</h3>
          <p>
            Deleting this run will remove local generated inputs, copied runtime files, output, and
            logs under the selected run directory. No files have been deleted yet.
          </p>
          <dl className="metric-grid">
            <Metric label="Run ID" value={deletePreview.run_id} />
            <Metric label="Selected path" value={deletePreview.run_directory} />
            <Metric label="Estimated reclaimed" value={formatBytes(deletePreview.size_bytes)} />
            <Metric label="Preview status" value={deletePreview.message} />
          </dl>
          <button type="button" onClick={() => onConfirmDelete(deletePreview.run_id)}>
            Confirm delete selected run
          </button>
        </section>
      )}

      <RuntimeRunsTable
        runs={inventory?.largest_runs ?? []}
        results={results}
        onPreviewDelete={onPreviewDelete}
        onOpenResult={onOpenResult}
        onExploreResult={onExploreResult}
      />
    </section>
  );
}

function RuntimeRunsTable({
  runs,
  results,
  onPreviewDelete,
  onOpenResult,
  onExploreResult,
}: {
  runs: RunStorageEntry[];
  results: ResultCard[];
  onPreviewDelete: (runId: string) => void;
  onOpenResult: (resultId: string) => void;
  onExploreResult: (resultId: string) => void;
}) {
  if (runs.length === 0) {
    return (
      <section className="status-panel" aria-label="Runtime runs">
        <p>No local Cloud Chamber run directories were found.</p>
      </section>
    );
  }

  return (
    <section className="table-panel" aria-label="Runtime runs">
      <table>
        <thead>
          <tr>
            <th scope="col">Run</th>
            <th scope="col">Scenario</th>
            <th scope="col">State</th>
            <th scope="col">Output</th>
            <th scope="col">Size</th>
            <th scope="col">Cleanup</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const associatedResult = resultForRun(results, run.run_id);
            const displayName =
              associatedResult?.name ?? run.scenario_name ?? run.scenario_id ?? run.run_id;
            const savedOrProtected =
              associatedResult?.saved || associatedResult?.protected || run.saved || run.protected;
            const deleteBlockedRun = {
              ...run,
              saved: Boolean(savedOrProtected),
              protected: Boolean(savedOrProtected),
            };
            return (
              <tr key={run.run_id}>
                <td>
                  <strong>{displayName}</strong>
                  <small>{run.run_id}</small>
                  <small>{run.path}</small>
                  {run.manifest_error && <small>{run.manifest_error}</small>}
                </td>
                <td>
                  {associatedResult?.scenario_name ??
                    run.scenario_name ??
                    run.scenario_id ??
                    "Unknown scenario"}
                  <small>
                    {humanize(
                      associatedResult?.run_size_preset ?? run.run_size_preset ?? "preset unknown",
                    )}
                    {associatedResult
                      ? ` · ${storageControlSummary(associatedResult.controls)}`
                      : ""}
                  </small>
                </td>
                <td>
                  <div className="badge-row">
                    <StatusBadge label={humanize(run.category)} tone={storageCategoryTone(run)} />
                    <StatusBadge
                      label={associatedResult ? "Ingested result" : "Not ingested"}
                      tone={associatedResult ? "good" : "neutral"}
                    />
                    <StatusBadge
                      label={savedOrProtected ? "Saved/protected" : "Not saved"}
                      tone={savedOrProtected ? "good" : "neutral"}
                    />
                  </div>
                  <small>
                    {run.lifecycle_state ? humanize(run.lifecycle_state) : "No manifest state"}
                  </small>
                </td>
                <td>{storageResultOutputSummary(run, associatedResult)}</td>
                <td>{formatBytes(run.size_bytes)}</td>
                <td>
                  <div className="button-row">
                    <button
                      type="button"
                      disabled={!associatedResult}
                      onClick={() => associatedResult && onOpenResult(associatedResult.result_id)}
                    >
                      Open result
                    </button>
                    <button
                      type="button"
                      disabled={!associatedResult}
                      onClick={() =>
                        associatedResult && onExploreResult(associatedResult.result_id)
                      }
                    >
                      Open in Explore
                    </button>
                    <button
                      type="button"
                      disabled={!canPreviewDelete(deleteBlockedRun)}
                      onClick={() => onPreviewDelete(run.run_id)}
                    >
                      Preview delete
                    </button>
                  </div>
                  {!canPreviewDelete(deleteBlockedRun) && (
                    <small>{deleteDisabledReason(deleteBlockedRun)}</small>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function DryRunReview({ dryRun }: { dryRun: DryRunResponse }) {
  return (
    <div className="dry-run-review">
      <dl>
        <div>
          <dt>Run ID</dt>
          <dd>{runIdFromPackage(dryRun)}</dd>
        </div>
        <div>
          <dt>Package path</dt>
          <dd>{dryRun.package_dir}</dd>
        </div>
        <div>
          <dt>Manifest path</dt>
          <dd>{dryRun.manifest_path}</dd>
        </div>
        <div>
          <dt>Scenario</dt>
          <dd>{dryRun.report.scenario_id}</dd>
        </div>
        <div>
          <dt>Validation status</dt>
          <dd>
            {dryRun.report.not_a_completed_cm1_result ? "Packaged dry-run output" : "Unknown"}
          </dd>
        </div>
        <div>
          <dt>CM1 launched</dt>
          <dd>{dryRun.report.cm1_was_launched ? "Yes" : "No"}</dd>
        </div>
        <div>
          <dt>Cost / size</dt>
          <dd>{dryRun.report.estimated_cost_or_size}</dd>
        </div>
      </dl>

      <h4>Generated files</h4>
      <ul>
        {Object.values(dryRun.report.generated_files).map((path) => (
          <li key={path}>{path.split("/").at(-1)}</li>
        ))}
      </ul>

      <h4>Manifest summary</h4>
      <p>{dryRun.report.physical_question}</p>
      <p>Run-size preset: {dryRun.report.run_size_preset}</p>
      <p>Expected diagnostics: {dryRun.report.expected_diagnostics.join(", ")}</p>
      <p>Product state: {dryRun.report.provenance.product_state}</p>
    </div>
  );
}

function GuidedRunWorkflow({
  dryRun,
  runStatus,
  error,
  ingestedResultId,
  onLaunchRun,
  onRefreshRunStatus,
  onIngestRun,
  onOpenInResults,
  onInspectIngested,
  onVisualizeIngested,
}: {
  dryRun: DryRunResponse;
  runStatus: RunStatusResponse | null;
  error: string | null;
  ingestedResultId: string | null;
  onLaunchRun: () => void;
  onRefreshRunStatus: () => void;
  onIngestRun: () => void;
  onOpenInResults: () => void;
  onInspectIngested: () => void;
  onVisualizeIngested: () => void;
}) {
  const isRunning =
    runStatus?.lifecycle_state === "queued" || runStatus?.lifecycle_state === "running";
  const canIngest =
    runStatus?.lifecycle_state === "completed" &&
    runStatus.product_state === "completed_cm1_result" &&
    !ingestedResultId;
  const outputCount = runStatus
    ? Object.values(runStatus.output_summary).reduce((total, value) => total + value, 0)
    : 0;

  return (
    <div className="guided-run-workflow">
      <DryRunReview dryRun={dryRun} />

      <section aria-labelledby="local-run-title">
        <h4 id="local-run-title">Local CM1 run</h4>
        <ol className="workflow-steps">
          <li className="complete">Package ready</li>
          <li className={runStatus ? "complete" : ""}>
            {isRunning
              ? "Running"
              : runStatus
                ? userFacingRunWorkflowStatus(runStatus)
                : "Ready to launch"}
          </li>
          <li className={runStatus?.lifecycle_state === "completed" ? "complete" : ""}>
            {runStatus?.lifecycle_state === "completed"
              ? "Ready to ingest"
              : "Waiting for CM1 output"}
          </li>
          <li className={ingestedResultId ? "complete" : ""}>
            {ingestedResultId ? "Ingested" : "Not ingested yet"}
          </li>
        </ol>

        {error && <p role="alert">{error}</p>}

        <div className="button-row">
          <button
            type="button"
            data-testid="launch-cm1-btn"
            onClick={onLaunchRun}
            disabled={Boolean(runStatus)}
          >
            Launch local CM1
          </button>
          <button
            type="button"
            data-testid="refresh-status-btn"
            onClick={onRefreshRunStatus}
            disabled={!runStatus}
          >
            Refresh status
          </button>
          <button
            type="button"
            data-testid="ingest-results-btn"
            onClick={onIngestRun}
            disabled={!canIngest}
          >
            Ingest output
          </button>
        </div>

        {runStatus ? (
          <div className="run-status-panel" aria-label="Local run status">
            <dl>
              <Metric label="Lifecycle state" value={humanize(runStatus.lifecycle_state)} />
              <Metric label="Product state" value={humanize(runStatus.product_state)} />
              <Metric label="Validation" value={humanize(runStatus.validation_status)} />
              <Metric label="Exit code" value={runStatus.exit_code?.toString() ?? "Running"} />
              <Metric label="Started" value={runStatus.started_at ?? "Not recorded"} />
              <Metric label="Finished" value={runStatus.finished_at ?? "Not finished"} />
              <Metric label="stdout log" value={runStatus.stdout_log || "Unavailable"} />
              <Metric label="stderr log" value={runStatus.stderr_log || "Unavailable"} />
              <Metric
                label="Output summary"
                value={
                  outputCount > 0
                    ? `${runStatus.output_summary.netcdf_paths} NetCDF, ${runStatus.output_summary.raw_cm1_artifacts} raw CM1, ${runStatus.output_summary.processed_artifacts} processed`
                    : "No output artifacts detected yet"
                }
              />
            </dl>
            {runStatus.runtime_warnings.length > 0 && (
              <div>
                <h5>Runtime caveats</h5>
                <ul>
                  {runStatus.runtime_warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
            {(runStatus.stdout_tail || runStatus.stderr_tail) && (
              <details>
                <summary>Latest log tail</summary>
                {runStatus.stdout_tail && (
                  <>
                    <h5>stdout</h5>
                    <pre>{runStatus.stdout_tail}</pre>
                  </>
                )}
                {runStatus.stderr_tail && (
                  <>
                    <h5>stderr</h5>
                    <pre>{runStatus.stderr_tail}</pre>
                  </>
                )}
              </details>
            )}
          </div>
        ) : (
          <p>
            Launch uses the configured local CM1 install and preserves one local run at a time. If
            CM1 settings are missing, launch will fail before any process starts.
          </p>
        )}

        {ingestedResultId && (
          <div className="post-ingest-actions" aria-label="Ingested result actions">
            <p>Result metadata created: {ingestedResultId}</p>
            <div className="button-row">
              <button type="button" onClick={onOpenInResults}>
                Open in Results
              </button>
              <button type="button" onClick={onInspectIngested}>
                Inspect fields
              </button>
              <button type="button" onClick={onVisualizeIngested}>
                Open 3-D visualization
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function ResultsTable({
  results,
  selectedResultId,
  onSelect,
}: {
  results: ResultCard[];
  selectedResultId: string | null;
  onSelect: (resultId: string) => void;
}) {
  if (results.length === 0) {
    return (
      <section className="status-panel" aria-label="Results list">
        <p>No ingested CM1 results yet.</p>
      </section>
    );
  }

  return (
    <section className="table-panel" aria-label="Results list">
      <table>
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Scenario</th>
            <th scope="col">Status</th>
            <th scope="col">Run size</th>
            <th scope="col">Outcome</th>
            <th scope="col">Output</th>
            <th scope="col">Saved</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr
              key={result.result_id}
              className={result.result_id === selectedResultId ? "selected-row" : ""}
            >
              <td>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => onSelect(result.result_id)}
                >
                  {compactResultName(result.name)}
                </button>
                <small>{formatDate(result.completed_at ?? result.created_at)}</small>
              </td>
              <td>{result.scenario_name ?? result.scenario_id}</td>
              <td>
                <StatusBadge label={userFacingStatus(result)} tone={statusTone(result)} />
              </td>
              <td>{humanize(result.run_size_preset)}</td>
              <td>
                <div className="badge-row">
                  <OutcomeBadge result={result} />
                  {isValidatedQuickLookBaseline(result) && (
                    <StatusBadge label="Validated quick-look baseline" tone="good" />
                  )}
                  <StatusBadge label={rainOutcome(result.rain_present)} tone="neutral" />
                  {result.caveats.length > 0 && (
                    <StatusBadge label={caveatLabel(result)} tone={caveatTone(result)} />
                  )}
                </div>
                <small>{result.diagnostics_summary ?? "Diagnostics unavailable"}</small>
              </td>
              <td>{outputSummary(result.output_file_summary)}</td>
              <td>
                <StatusBadge
                  label={result.saved || result.protected ? "Saved" : "Unsaved"}
                  tone={result.saved || result.protected ? "good" : "neutral"}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function ResultNotebookCard({
  result,
  draft,
  onDraftChange,
  onSubmit,
  onSave,
  onInspect,
  onOpenVisualizer,
}: {
  result: ResultCard | undefined;
  draft: { name: string; tags: string; notes: string };
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSave: () => void;
  onInspect: () => void;
  onOpenVisualizer: () => void;
}) {
  if (!result) {
    return (
      <section className="status-panel" aria-label="Result detail">
        <p>Select an ingested CM1 result to review its notebook card.</p>
      </section>
    );
  }

  return (
    <section className="notebook-card" aria-label="Result detail">
      <div className="notebook-title">
        <div>
          <p className="eyebrow">Result detail / notebook card</p>
          <h3>{result.name}</h3>
        </div>
        <StatusBadge
          label={result.saved || result.protected ? "Saved" : "Unsaved"}
          tone={result.saved || result.protected ? "good" : "neutral"}
        />
      </div>

      <div className="badge-row">
        <OutcomeBadge result={result} />
        <StatusBadge label={rainOutcome(result.rain_present)} tone="neutral" />
        {result.caveats.length > 0 && (
          <StatusBadge label={caveatLabel(result)} tone={caveatTone(result)} />
        )}
        <StatusBadge label={userFacingStatus(result)} tone={statusTone(result)} />
      </div>

      <dl className="metric-grid">
        <Metric label="Run ID" value={result.run_id} />
        <Metric label="Scenario" value={result.scenario_name ?? result.scenario_id} />
        <Metric label="Run-size preset" value={humanize(result.run_size_preset)} />
        <Metric
          label="Diagnostics"
          value={result.diagnostics_summary ?? "Diagnostics unavailable"}
        />
        <Metric label="Cloud" value={cloudOutcome(result)} />
        <Metric label="Rain" value={rainOutcome(result.rain_present)} />
        <Metric label="First cloud time" value={formatSeconds(result.first_cloud_time_seconds)} />
        <Metric label="Max qc" value={formatScientific(result.max_qc_kg_kg, "kg/kg")} />
        <Metric label="Max w" value={formatNumber(result.max_w_m_s, "m/s")} />
        <Metric label="Min w" value={formatNumber(result.min_w_m_s, "m/s")} />
        <Metric label="Output" value={outputSummary(result.output_file_summary)} />
      </dl>

      <section aria-labelledby="caveats-title">
        <h4 id="caveats-title">Caveats / warnings</h4>
        {result.caveats.length > 0 ? (
          <ul className="compact-list">
            {result.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        ) : (
          <p>No caveats recorded.</p>
        )}
      </section>

      <details>
        <summary>Technical details</summary>
        <section aria-labelledby="result-question-title">
          <h4 id="result-question-title">Physical question</h4>
          <p>{result.physical_question}</p>
        </section>

        <section aria-labelledby="controls-used-title">
          <h4 id="controls-used-title">Controls used</h4>
          {Object.keys(result.controls).length > 0 ? (
            <ul className="compact-list">
              {Object.entries(result.controls).map(([key, value]) => (
                <li key={key}>
                  {humanize(key)}: {String(value)}
                </li>
              ))}
            </ul>
          ) : (
            <p>No controls recorded.</p>
          )}
        </section>

        <section aria-labelledby="provenance-title">
          <h4 id="provenance-title">Provenance labels</h4>
          <ul className="tag-list">
            {result.provenance_labels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
          <dl className="metric-grid">
            <Metric label="Lifecycle" value={result.source_lifecycle_state} />
            <Metric label="Product state" value={result.source_product_state} />
            <Metric label="Result state" value={result.status} />
            <Metric label="Source model" value={result.source_model} />
          </dl>
        </section>
      </details>

      <form className="notebook-form" onSubmit={onSubmit}>
        <label htmlFor="result-name">Name</label>
        <input
          id="result-name"
          value={draft.name}
          onChange={(event) => onDraftChange({ ...draft, name: event.target.value })}
        />

        <label htmlFor="result-tags">Tags</label>
        <input
          id="result-tags"
          value={draft.tags}
          onChange={(event) => onDraftChange({ ...draft, tags: event.target.value })}
          placeholder="baseline, quick-look"
        />

        <label htmlFor="result-notes">Notes</label>
        <textarea
          id="result-notes"
          value={draft.notes}
          onChange={(event) => onDraftChange({ ...draft, notes: event.target.value })}
        />

        <div className="button-row">
          <button type="submit">Update notebook</button>
          <button type="button" onClick={onSave}>
            Save result
          </button>
          <button type="button" onClick={onInspect}>
            Inspect fields
          </button>
          <button type="button" onClick={onOpenVisualizer}>
            Open 3-D
          </button>
        </div>
      </form>
    </section>
  );
}

function VisualizerSceneShell({ result }: { result: ResultCard }) {
  const [catalog, setCatalog] = useState<FieldCatalogResponse | null>(null);
  const [viewDefaults, setViewDefaults] = useState<ViewDefaultsResponse | null>(null);
  const [selectedTimeDefaults, setSelectedTimeDefaults] = useState<ViewDefaultsResponse | null>(
    null,
  );
  const [selectedFieldName, setSelectedFieldName] = useState("");
  const [timeIndex, setTimeIndex] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [threshold, setThreshold] = useState(1e-6);
  const [opacity, setOpacity] = useState(0.68);
  const [pointSize, setPointSize] = useState(11);
  const [isPlaying, setIsPlaying] = useState(false);
  const [pointCloud, setPointCloud] = useState<PointCloudResponse | null>(null);
  const [processMode, setProcessMode] = useState<ProcessMode>("thermal_fate");
  const [viewPreset, setViewPreset] = useState<SceneViewPreset>("cloud-overview");
  const [projectionMode, setProjectionMode] = useState<ProjectionMode>("oblique");
  const [showSlicePlanes, setShowSlicePlanes] = useState(false);
  const [sliceFieldName, setSliceFieldName] = useState("qc");
  const [activeSlicePlane, setActiveSlicePlane] = useState<SceneSlicePlane>("horizontal");
  const [sliceOrientation, setSliceOrientation] = useState<"vertical_x" | "vertical_y">(
    "vertical_x",
  );
  const [horizontalSliceLevel, setHorizontalSliceLevel] = useState(0);
  const [verticalSliceIndex, setVerticalSliceIndex] = useState(0);
  const [sceneHorizontalSlice, setSceneHorizontalSlice] = useState<SliceResponse | null>(null);
  const [sceneVerticalSlice, setSceneVerticalSlice] = useState<SliceResponse | null>(null);
  const [sceneStatus, setSceneStatus] = useState("Loading scene data...");
  const [sceneError, setSceneError] = useState<string | null>(null);
  const [sliceError, setSliceError] = useState<string | null>(null);
  const [fieldLoadAttempt, setFieldLoadAttempt] = useState(0);
  const maxPoints = 50_000;

  useEffect(() => {
    let active = true;
    setCatalog(null);
    setViewDefaults(null);
    setSelectedTimeDefaults(null);
    setSceneError(null);
    setSelectedFieldName("");
    setTimeIndex(0);
    setZoom(100);
    setThreshold(1e-6);
    setOpacity(0.68);
    setPointSize(11);
    setIsPlaying(false);
    setPointCloud(null);
    setProcessMode("thermal_fate");
    setViewPreset("cloud-overview");
    setProjectionMode("oblique");
    setShowSlicePlanes(false);
    setSliceFieldName("qc");
    setActiveSlicePlane("horizontal");
    setSliceOrientation("vertical_x");
    setHorizontalSliceLevel(0);
    setVerticalSliceIndex(0);
    setSceneHorizontalSlice(null);
    setSceneVerticalSlice(null);
    setSliceError(null);
    setSceneStatus("Loading scene data...");
    withTimeout(
      Promise.all([
        fetchVisualizationFields(result.result_id),
        fetchVisualizationDefaults(result.result_id).catch(() => null),
      ]),
      "Timed out loading visualization fields. Check the backend and retry.",
    )
      .then(([payload, defaults]) => {
        if (!active) return;
        setSceneError(null);
        setCatalog(payload);
        setViewDefaults(defaults);
        const firstPreferred =
          payload.available_fields.find(
            (field) => field.raw_field_name === (defaults?.preferred_field ?? "qc"),
          ) ??
          payload.available_fields.find((field) => field.raw_field_name === "qc") ??
          payload.available_fields[0];
        const initialDefaults = defaultsForField(defaults, firstPreferred?.raw_field_name);
        const initialTimeIndex = defaultTimeIndex(firstPreferred, result, initialDefaults);
        setSelectedFieldName(firstPreferred?.raw_field_name ?? "");
        setSliceFieldName(firstPreferred?.raw_field_name ?? "");
        setTimeIndex(initialTimeIndex);
        setHorizontalSliceLevel(defaultHorizontalLevel(firstPreferred, initialDefaults));
        setVerticalSliceIndex(defaultVerticalIndex(firstPreferred, "vertical_x", initialDefaults));
        setSceneStatus(
          payload.available_fields.length > 0 ? "Scene shell ready" : "No fields available",
        );
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setSceneError(caught instanceof Error ? caught.message : "Unable to load scene data.");
        setSceneStatus("Scene unavailable");
      });
    return () => {
      active = false;
    };
  }, [fieldLoadAttempt, result]);

  const selectedField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === selectedFieldName),
    [catalog, selectedFieldName],
  );
  const qcField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === "qc"),
    [catalog],
  );
  const sliceField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === sliceFieldName),
    [catalog, sliceFieldName],
  );

  const timeOptions = selectedField?.time_coordinate_values ?? [];
  const timeMax = Math.max(0, timeOptions.length - 1);
  const canRenderCloudWater = selectedFieldName === "qc" && Boolean(qcField);
  const wField = catalog?.available_fields.find((field) => field.raw_field_name === "w");
  const isNoCloudWithUpdraft =
    cloudOutcome(result) === "No cloud formed" && Boolean(wField) && (result.max_w_m_s ?? 0) > 0;
  const sliceVerticalSize = sliceField?.coordinate_names.vertical
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.vertical)]
    : 1;
  const sliceYSize = sliceField?.coordinate_names.y
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.y)]
    : 1;
  const sliceXSize = sliceField?.coordinate_names.x
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.x)]
    : 1;
  const activeSliceMax =
    activeSlicePlane === "horizontal"
      ? sliceVerticalSize
      : activeSlicePlane === "vertical_x"
        ? sliceYSize
        : sliceXSize;
  const activeSliceIndex =
    activeSlicePlane === "horizontal" ? horizontalSliceLevel : verticalSliceIndex;
  const activeSlicePositionLabel = activeSlicePosition(
    activeSlicePlane,
    sceneHorizontalSlice,
    sceneVerticalSlice,
  );
  const provenanceLabel =
    pointCloud?.provenance.provenance_label ??
    selectedField?.provenance.provenance_label ??
    catalog?.provenance.provenance_label ??
    "CM1-derived visualization-ready data; rendering not implemented";
  const selectedDefaults = defaultsForField(viewDefaults, selectedFieldName);
  const selectedTimeFieldDefaults = defaultsForField(selectedTimeDefaults, selectedFieldName);
  const selectedTimeSliceDefaults = defaultsForField(selectedTimeDefaults, sliceFieldName);
  const selectedTimeValue = timeOptions[Math.min(timeIndex, timeMax)] ?? null;
  const selectedTimeLabel = formatTimeValue(selectedTimeValue);

  useEffect(() => {
    if (!selectedField || selectedField.raw_field_name !== "qc") {
      setPointCloud(null);
      return;
    }
    let active = true;
    setSceneError(null);
    setSceneStatus("Loading cloud-water points...");
    fetchVisualizationPointCloud(result.result_id, {
      field: "qc",
      timeIndex,
      threshold,
      maxPoints,
    })
      .then((payload) => {
        if (!active) return;
        setPointCloud(payload);
        setSceneStatus(
          payload.points.length > 0
            ? "Cloud-water point cloud loaded"
            : "No cloud water above threshold",
        );
        return fetchVisualizationDefaults(result.result_id, timeIndex)
          .then((defaults) => {
            if (!active) return;
            setSelectedTimeDefaults(defaults);
            const fieldDefaults = defaultsForField(defaults, selectedField.raw_field_name);
            if (fieldDefaults) {
              setHorizontalSliceLevel(fieldDefaults.horizontal_level_index);
              setVerticalSliceIndex(
                sliceOrientation === "vertical_y"
                  ? fieldDefaults.vertical_y_index
                  : fieldDefaults.vertical_x_index,
              );
            }
          })
          .catch(() => {
            if (active) setSelectedTimeDefaults(null);
          });
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setPointCloud(null);
        setSceneError(
          caught instanceof Error ? caught.message : "Unable to load cloud-water point cloud.",
        );
        setSceneStatus("Point cloud unavailable");
      });
    return () => {
      active = false;
    };
  }, [maxPoints, result.result_id, selectedField, sliceOrientation, threshold, timeIndex]);

  useEffect(() => {
    if (!sliceField) {
      setSceneHorizontalSlice(null);
      setSceneVerticalSlice(null);
      return;
    }
    let active = true;
    setSliceError(null);
    Promise.all([
      fetchVisualizationSlice(result.result_id, {
        field: sliceField.raw_field_name,
        timeIndex,
        orientation: "horizontal",
        levelIndex: horizontalSliceLevel,
      }),
      fetchVisualizationSlice(result.result_id, {
        field: sliceField.raw_field_name,
        timeIndex,
        orientation: sliceOrientation,
        levelIndex: verticalSliceIndex,
      }),
    ])
      .then(([horizontal, vertical]) => {
        if (!active) return;
        setSceneHorizontalSlice(horizontal);
        setSceneVerticalSlice(vertical);
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setSceneHorizontalSlice(null);
        setSceneVerticalSlice(null);
        setSliceError(caught instanceof Error ? caught.message : "Unable to load slice planes.");
      });
    return () => {
      active = false;
    };
  }, [
    horizontalSliceLevel,
    result.result_id,
    sliceField,
    sliceOrientation,
    timeIndex,
    verticalSliceIndex,
  ]);

  useEffect(() => {
    if (!isPlaying || timeMax <= 0) return;
    const interval = window.setInterval(() => {
      setTimeIndex((current) => (current >= timeMax ? 0 : current + 1));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [isPlaying, timeMax]);

  function resetView() {
    setZoom(100);
    setProjectionMode("oblique");
  }

  return (
    <section className="visualizer-shell" aria-labelledby="visualizer-shell-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">3-D visualizer</p>
          <h2 id="visualizer-shell-title">Scene shell</h2>
        </div>
        <p className="state-chip">{sceneStatus}</p>
      </div>

      <p>
        Cloud-water points are CM1 grid cells where qc exceeds the selected threshold. Slice planes
        are optional native-grid inspection aids; the browser is not parsing raw NetCDF.
      </p>

      {sceneError && (
        <div role="alert">
          <p>{sceneError}</p>
          <button type="button" onClick={() => setFieldLoadAttempt((current) => current + 1)}>
            Retry loading fields
          </button>
        </div>
      )}

      {catalog && catalog.available_fields.length === 0 && (
        <p role="status">No visualization-ready fields are available for this result.</p>
      )}

      <div className="visualizer-workbench" aria-label="Scientific visualization workbench">
        <div className="workbench-status-strip" aria-label="Result scenario time status">
          <Metric label="Result" value={result.name || result.run_id} />
          <Metric label="Scenario" value={result.scenario_name ?? result.scenario_id} />
          <Metric label="Time" value={selectedTimeLabel} />
          <Metric label="Status" value={sceneStatus} />
        </div>

        <aside
          className="visualizer-controls visualizer-primary-controls"
          aria-label="Primary visualizer controls"
        >
          <ProcessModeControl processMode={processMode} onProcessModeChange={setProcessMode} />

          <fieldset>
            <legend>View controls</legend>
            <label htmlFor="scene-zoom">
              Zoom
              <input
                id="scene-zoom"
                type="range"
                min={50}
                max={180}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
              />
            </label>
            <p>Zoom: {zoom}%</p>
            <button type="button" onClick={resetView}>
              Reset view
            </button>
            <small>
              Zoom scales the data layer only; it does not change CM1 coordinates or slice
              selection.
            </small>
          </fieldset>

          {catalog && selectedField && (
            <fieldset>
              <legend>View presets</legend>
              <div className="segmented-buttons">
                <button
                  type="button"
                  className={viewPreset === "cloud-overview" ? "active-control" : ""}
                  onClick={() =>
                    applyScenePreset("cloud-overview", {
                      catalog,
                      viewDefaults,
                      result,
                      setViewPreset,
                      setSelectedFieldName,
                      setSliceFieldName,
                      setTimeIndex,
                      setHorizontalSliceLevel,
                      setVerticalSliceIndex,
                      setActiveSlicePlane,
                      setSliceOrientation,
                      setShowSlicePlanes,
                      setProjectionMode,
                    })
                  }
                >
                  Cloud overview
                </button>
                <button
                  type="button"
                  className={viewPreset === "vertical-cross-section" ? "active-control" : ""}
                  onClick={() =>
                    applyScenePreset("vertical-cross-section", {
                      catalog,
                      viewDefaults,
                      result,
                      setViewPreset,
                      setSelectedFieldName,
                      setSliceFieldName,
                      setTimeIndex,
                      setHorizontalSliceLevel,
                      setVerticalSliceIndex,
                      setActiveSlicePlane,
                      setSliceOrientation,
                      setShowSlicePlanes,
                      setProjectionMode,
                    })
                  }
                >
                  Vertical cross-section
                </button>
                <button
                  type="button"
                  className={viewPreset === "top-down-slice" ? "active-control" : ""}
                  onClick={() =>
                    applyScenePreset("top-down-slice", {
                      catalog,
                      viewDefaults,
                      result,
                      setViewPreset,
                      setSelectedFieldName,
                      setSliceFieldName,
                      setTimeIndex,
                      setHorizontalSliceLevel,
                      setVerticalSliceIndex,
                      setActiveSlicePlane,
                      setSliceOrientation,
                      setShowSlicePlanes,
                      setProjectionMode,
                    })
                  }
                >
                  Top-down slice
                </button>
                <button
                  type="button"
                  className={viewPreset === "updraft" ? "active-control" : ""}
                  onClick={() =>
                    applyScenePreset("updraft", {
                      catalog,
                      viewDefaults,
                      result,
                      setViewPreset,
                      setSelectedFieldName,
                      setSliceFieldName,
                      setTimeIndex,
                      setHorizontalSliceLevel,
                      setVerticalSliceIndex,
                      setActiveSlicePlane,
                      setSliceOrientation,
                      setShowSlicePlanes,
                      setProjectionMode,
                    })
                  }
                >
                  Updraft view
                </button>
              </div>
              <small>
                Defaults use first cloud time or native-grid maxima when available; fallback is the
                domain center.
              </small>
            </fieldset>
          )}

          {catalog && selectedField && (
            <fieldset>
              <legend>Projection</legend>
              <div className="segmented-buttons">
                <button
                  type="button"
                  className={projectionMode === "side_xz" ? "active-control" : ""}
                  onClick={() => setProjectionMode("side_xz")}
                >
                  Side x-z
                </button>
                <button
                  type="button"
                  className={projectionMode === "side_yz" ? "active-control" : ""}
                  onClick={() => setProjectionMode("side_yz")}
                >
                  Side y-z
                </button>
                <button
                  type="button"
                  className={projectionMode === "top_down" ? "active-control" : ""}
                  onClick={() => setProjectionMode("top_down")}
                >
                  Top-down x-y
                </button>
                <button
                  type="button"
                  className={projectionMode === "oblique" ? "active-control" : ""}
                  onClick={() => setProjectionMode("oblique")}
                >
                  Oblique overview
                </button>
              </div>
              <small>
                Side views map model height z to screen height for cloud-base and cloud-top checks.
              </small>
            </fieldset>
          )}

          {catalog && selectedField && (
            <fieldset>
              <legend>Field</legend>
              <label htmlFor="scene-field">
                Field
                <select
                  id="scene-field"
                  value={selectedFieldName}
                  onChange={(event) => {
                    const nextField = catalog.available_fields.find(
                      (field) => field.raw_field_name === event.target.value,
                    );
                    setSelectedFieldName(event.target.value);
                    setTimeIndex(
                      defaultTimeIndex(
                        nextField,
                        result,
                        defaultsForField(viewDefaults, event.target.value),
                      ),
                    );
                  }}
                >
                  {catalog.available_fields.map((field) => (
                    <option key={field.raw_field_name} value={field.raw_field_name}>
                      {field.raw_field_name} - {field.display_name}
                    </option>
                  ))}
                </select>
              </label>
            </fieldset>
          )}

          {catalog && selectedField && (
            <fieldset>
              <legend>Cloud-water rendering</legend>
              <label htmlFor="cloud-threshold">
                Threshold
                <input
                  id="cloud-threshold"
                  type="number"
                  min={0}
                  step="0.000001"
                  value={threshold}
                  onChange={(event) => setThreshold(Number(event.target.value))}
                  disabled={!canRenderCloudWater}
                />
              </label>
              <label htmlFor="cloud-opacity">
                Opacity
                <input
                  id="cloud-opacity"
                  type="range"
                  min={0.1}
                  max={1}
                  step={0.05}
                  value={opacity}
                  onChange={(event) => setOpacity(Number(event.target.value))}
                />
              </label>
              <label htmlFor="cloud-point-size">
                Point size
                <input
                  id="cloud-point-size"
                  type="range"
                  min={3}
                  max={18}
                  value={pointSize}
                  onChange={(event) => setPointSize(Number(event.target.value))}
                />
              </label>
              <p>Default max points: {maxPoints.toLocaleString()}</p>
            </fieldset>
          )}

          {catalog && sliceField && (
            <fieldset>
              <legend>Slice planes</legend>
              <label htmlFor="show-slice-planes" className="checkbox-label">
                <input
                  id="show-slice-planes"
                  type="checkbox"
                  checked={showSlicePlanes}
                  onChange={(event) => setShowSlicePlanes(event.target.checked)}
                />
                Show slice planes
              </label>
              <label htmlFor="slice-field">
                Slice field
                <select
                  id="slice-field"
                  value={sliceFieldName}
                  onChange={(event) => {
                    const nextField = catalog.available_fields.find(
                      (field) => field.raw_field_name === event.target.value,
                    );
                    setSliceFieldName(event.target.value);
                    const nextDefaults = defaultsForField(viewDefaults, event.target.value);
                    setHorizontalSliceLevel(defaultHorizontalLevel(nextField, nextDefaults));
                    setVerticalSliceIndex(
                      defaultVerticalIndex(nextField, sliceOrientation, nextDefaults),
                    );
                  }}
                >
                  {catalog.available_fields
                    .filter(
                      (field) => field.raw_field_name === "qc" || field.raw_field_name === "w",
                    )
                    .map((field) => (
                      <option key={field.raw_field_name} value={field.raw_field_name}>
                        {field.raw_field_name} - {field.display_name}
                      </option>
                    ))}
                </select>
              </label>
            </fieldset>
          )}
        </aside>

        <div className="visualizer-stage" aria-label="Fixed visualization viewport region">
          <div className="scene-container" aria-label="3-D scene container">
            <div className="viewport-frame" style={plotFrameStyle(pointCloud, projectionMode)}>
              <div
                className="plot-data-layer"
                aria-label="Zoomable visualizer data layer"
                style={{ transform: `scale(${zoom / 100})` }}
              >
                <div className="scene-horizon" />
                <div className="scene-grid" />
                <div
                  className={`domain-box domain-box-${projectionMode}`}
                  aria-label="Domain bounding box"
                >
                  <span className="axis-label axis-label-x">
                    {projectionMode === "side_yz" ? "y" : "x"}
                  </span>
                  <span className="axis-label axis-label-y">
                    {projectionMode === "side_xz"
                      ? "depth y"
                      : projectionMode === "top_down"
                        ? "y"
                        : "depth y"}
                  </span>
                  <span className="axis-label axis-label-z">
                    {projectionMode === "top_down" ? "top-down x-y" : "height z"}
                  </span>
                  <span className="ground-label">domain floor</span>
                </div>
                {showSlicePlanes && activeSlicePlane === "horizontal" && (
                  <SlicePlane title="Horizontal z slice plane" slice={sceneHorizontalSlice} />
                )}
                {showSlicePlanes && activeSlicePlane !== "horizontal" && (
                  <SlicePlane
                    title={
                      activeSlicePlane === "vertical_x"
                        ? "Vertical x-z slice plane"
                        : "Vertical y-z slice plane"
                    }
                    slice={sceneVerticalSlice}
                  />
                )}
                {pointCloud && pointCloud.points.length > 0 && (
                  <div className="point-cloud-layer" aria-label="Cloud-water point cloud">
                    {pointCloud.points.map((point, index) => (
                      <span
                        className="cloud-point"
                        key={`${point.join("-")}-${index}`}
                        style={cloudPointStyle(
                          point,
                          pointCloud,
                          projectionMode,
                          pointCloud.stats,
                          opacity,
                          pointSize,
                        )}
                      />
                    ))}
                  </div>
                )}
              </div>
              <ScaleMarkers pointCloud={pointCloud} projectionMode={projectionMode} />
              <div className="scene-context-label">
                <strong>{projectionLabel(projectionMode)}</strong>
                <span>{selectedTimeLabel}</span>
                <span>Cloud-water threshold {formatScientific(threshold, "kg/kg")}</span>
              </div>
              <p className="active-slice-label" aria-label="Active slice label">
                {activeSlicePlaneDescription(activeSlicePlane)}: index {activeSliceIndex}
                {activeSlicePositionLabel ? ` (${activeSlicePositionLabel})` : ""}
              </p>
            </div>
            <p className="projection-description" aria-label="Projection description">
              {projectionDescription(projectionMode)}
            </p>
            {(!pointCloud || pointCloud.points.length === 0) && (
              <div className="scene-empty-state">
                <p className="eyebrow">Cloud-water point cloud</p>
                <h3>
                  {!qcField
                    ? "Cloud water field qc is not available for this result."
                    : isNoCloudWithUpdraft
                      ? "No cloud water formed here; vertical velocity is available."
                      : "No cloud water above the selected threshold at this time."}
                </h3>
                <p>
                  {!qcField
                    ? "Use available fields such as vertical velocity when present. Rendering remains an interpretation of CM1-derived data."
                    : isNoCloudWithUpdraft
                      ? "This no-cloud result is still useful: use the vertical velocity field (w) to inspect the thermals."
                      : "Adjust the time or threshold after qc is available. Rendering remains an interpretation of CM1-derived data."}
                </p>
              </div>
            )}
          </div>

          <div className="visualizer-bottom-controls" aria-label="Timeline and slice controls">
            {catalog && selectedField && (
              <fieldset>
                <legend>Timeline</legend>
                <label htmlFor="scene-time">
                  Time
                  <input
                    id="scene-time"
                    type="range"
                    min={0}
                    max={timeMax}
                    value={Math.min(timeIndex, timeMax)}
                    onChange={(event) => setTimeIndex(Number(event.target.value))}
                  />
                </label>
                <button type="button" onClick={() => setIsPlaying((current) => !current)}>
                  {isPlaying ? "Pause time" : "Play time"}
                </button>
                <div className="button-row">
                  <button
                    type="button"
                    onClick={() => setTimeIndex(jumpTimeIndex(timeOptions, result, "first-cloud"))}
                  >
                    Jump to first cloud
                  </button>
                  <button
                    type="button"
                    onClick={() => setTimeIndex(jumpTimeIndex(timeOptions, result, "max-qc"))}
                  >
                    Jump to max cloud water
                  </button>
                  <button
                    type="button"
                    onClick={() => setTimeIndex(jumpTimeIndex(timeOptions, result, "max-w"))}
                  >
                    Jump to max updraft
                  </button>
                </div>
              </fieldset>
            )}

            {catalog && sliceField && (
              <fieldset>
                <legend>Slice position</legend>
                <div className="segmented-buttons" aria-label="Slice plane orientation">
                  <button
                    type="button"
                    className={activeSlicePlane === "horizontal" ? "active-control" : ""}
                    onClick={() => {
                      setActiveSlicePlane("horizontal");
                      setShowSlicePlanes(true);
                      setProjectionMode("top_down");
                    }}
                  >
                    Horizontal z
                  </button>
                  <button
                    type="button"
                    className={activeSlicePlane === "vertical_x" ? "active-control" : ""}
                    onClick={() => {
                      setActiveSlicePlane("vertical_x");
                      setSliceOrientation("vertical_x");
                      setVerticalSliceIndex(
                        defaultVerticalIndex(
                          sliceField,
                          "vertical_x",
                          selectedTimeSliceDefaults ??
                            defaultsForField(viewDefaults, sliceFieldName),
                        ),
                      );
                      setShowSlicePlanes(true);
                      setProjectionMode("side_xz");
                    }}
                  >
                    Vertical x-z
                  </button>
                  <button
                    type="button"
                    className={activeSlicePlane === "vertical_y" ? "active-control" : ""}
                    onClick={() => {
                      setActiveSlicePlane("vertical_y");
                      setSliceOrientation("vertical_y");
                      setVerticalSliceIndex(
                        defaultVerticalIndex(
                          sliceField,
                          "vertical_y",
                          selectedTimeSliceDefaults ??
                            defaultsForField(viewDefaults, sliceFieldName),
                        ),
                      );
                      setShowSlicePlanes(true);
                      setProjectionMode("side_yz");
                    }}
                  >
                    Vertical y-z
                  </button>
                </div>
                <label htmlFor="active-slice-position">
                  {activeSlicePlaneLabel(activeSlicePlane)}
                  <input
                    id="active-slice-position"
                    type="range"
                    min={0}
                    max={Math.max(0, activeSliceMax - 1)}
                    value={activeSliceIndex}
                    onChange={(event) => {
                      const nextIndex = Number(event.target.value);
                      if (activeSlicePlane === "horizontal") {
                        setHorizontalSliceLevel(nextIndex);
                      } else {
                        setVerticalSliceIndex(nextIndex);
                      }
                    }}
                  />
                </label>
                <div className="button-row">
                  <button
                    type="button"
                    onClick={() => {
                      const nextIndex = Math.max(0, activeSliceIndex - 1);
                      if (activeSlicePlane === "horizontal") {
                        setHorizontalSliceLevel(nextIndex);
                      } else {
                        setVerticalSliceIndex(nextIndex);
                      }
                    }}
                  >
                    {activeSlicePlane === "horizontal" ? "Move down" : "Move back"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const nextIndex = Math.min(
                        Math.max(0, activeSliceMax - 1),
                        activeSliceIndex + 1,
                      );
                      if (activeSlicePlane === "horizontal") {
                        setHorizontalSliceLevel(nextIndex);
                      } else {
                        setVerticalSliceIndex(nextIndex);
                      }
                    }}
                  >
                    {activeSlicePlane === "horizontal" ? "Move up" : "Move forward"}
                  </button>
                </div>
                <p>
                  Active slice: {activeSlicePlaneDescription(activeSlicePlane)} at index{" "}
                  {activeSliceIndex}
                  {activeSlicePositionLabel ? ` (${activeSlicePositionLabel})` : ""}.
                </p>
                <small>
                  Slice controls move native-grid slices only. They do not interpolate, rotate raw
                  NetCDF, or change the CM1 result.
                </small>
              </fieldset>
            )}
          </div>
        </div>

        <aside className="visualizer-details-panel" aria-label="Visualization details">
          <ProcessOverlayPanel
            result={result}
            catalog={catalog}
            selectedField={selectedField}
            processMode={processMode}
            slice={activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice}
          />

          <div className="summary-strip">
            <Metric
              label="Selected time"
              value={formatTimeValue(timeOptions[Math.min(timeIndex, timeMax)] ?? null)}
            />
            <Metric
              label="Points"
              value={
                pointCloud
                  ? `${pointCloud.stats.returned_count.toLocaleString()} of ${pointCloud.stats.source_count.toLocaleString()}`
                  : "Unavailable"
              }
            />
            <Metric
              label="Cloud-water range"
              value={
                pointCloud
                  ? `${formatMaybeNumber(pointCloud.stats.min_value, selectedField?.units ?? "kg/kg")} to ${formatMaybeNumber(
                      pointCloud.stats.max_value,
                      selectedField?.units ?? "kg/kg",
                    )}`
                  : "Unavailable"
              }
            />
          </div>

          {pointCloud?.stats.downsampled && (
            <p role="status">
              Point cloud downsampled with deterministic stride {pointCloud.stats.downsample_stride}
              .
            </p>
          )}
          {sliceError && <p role="alert">{sliceError}</p>}

          <details>
            <summary>About this visualization</summary>
            <dl className="metric-grid">
              <Metric label="Run ID" value={result.run_id} />
              <Metric label="View control" value="zoom-only data-layer transform" />
              <Metric label="Zoom" value={`${zoom}%`} />
              <Metric label="Opacity" value={String(opacity)} />
              <Metric label="Point size" value={`${pointSize}px`} />
              <Metric
                label="Selected field"
                value={
                  selectedField
                    ? `${selectedField.raw_field_name} (${selectedField.display_name})`
                    : "Unavailable"
                }
              />
              <Metric label="Threshold" value={formatScientific(threshold, "kg/kg")} />
              <Metric label="Rendering method" value="thresholded_point_cloud" />
              <Metric label="View preset" value={humanize(viewPreset)} />
              <Metric
                label="Default source"
                value={
                  selectedTimeFieldDefaults?.source ??
                  selectedDefaults?.source ??
                  "domain center fallback"
                }
              />
              <Metric
                label="Slice field"
                value={
                  sliceField
                    ? `${sliceField.raw_field_name} (${sliceField.display_name})`
                    : "Unavailable"
                }
              />
              <Metric
                label="Slice orientation"
                value={
                  activeSlicePlane === "horizontal" && sceneHorizontalSlice
                    ? `${sceneHorizontalSlice.selection.orientation} at ${sceneHorizontalSlice.selection.selected_dimension}[${sceneHorizontalSlice.selection.selected_index}]`
                    : sceneVerticalSlice
                      ? `${sceneVerticalSlice.selection.orientation} at ${sceneVerticalSlice.selection.selected_dimension}[${sceneVerticalSlice.selection.selected_index}]`
                      : "Unavailable"
                }
              />
              <Metric label="Projection" value={humanize(projectionMode)} />
              <Metric label="Domain x extent" value={extentLabel(pointCloud, "xh")} />
              <Metric label="Domain y extent" value={extentLabel(pointCloud, "yh")} />
              <Metric label="Domain z extent" value={extentLabel(pointCloud, "zh")} />
              <Metric
                label="Active cloud z range"
                value={
                  pointCloud
                    ? `${formatMaybeNumber(pointCloud.stats.active_z_min, pointCloud.coordinate_units.zh ?? null)} to ${formatMaybeNumber(
                        pointCloud.stats.active_z_max,
                        pointCloud.coordinate_units.zh ?? null,
                      )}`
                    : "Unavailable"
                }
              />
              <Metric label="Max cloud-water location" value={maxPointLocationLabel(pointCloud)} />
              <Metric
                label="Selected-time slice default"
                value={selectedTimeSliceDefaults?.source ?? "Unavailable"}
              />
            </dl>

            <div className="slice-plane-summary">
              <SceneSliceSummary title="Horizontal slice plane" slice={sceneHorizontalSlice} />
              <SceneSliceSummary title="Vertical slice plane" slice={sceneVerticalSlice} />
            </div>

            <section aria-labelledby="visualizer-provenance-title">
              <h3 id="visualizer-provenance-title">Provenance / rendering labels</h3>
              <ul className="compact-list">
                <li>{provenanceLabel}</li>
                <li>Visualizer interpretation of CM1-derived output</li>
                <li>Processing method: native-grid thresholded point cloud</li>
                <li>Rendering method: thresholded point cloud</li>
                <li>Slice planes: native-grid JSON slices from the backend</li>
                <li>No raw NetCDF parsing in the browser</li>
                <li>
                  No interpolation, ray marching, isosurface extraction, or synthetic cloud physics
                </li>
              </ul>
            </section>
          </details>
        </aside>
      </div>
    </section>
  );
}

function SlicePlane({ title, slice }: { title: string; slice: SliceResponse | null }) {
  if (!slice) return null;
  const cells = slice.values.flat();
  return (
    <div
      className={
        slice.selection.orientation === "horizontal"
          ? "slice-plane slice-plane-horizontal"
          : "slice-plane slice-plane-vertical"
      }
      aria-label={title}
    >
      <span className="slice-plane-label">
        {slice.field.raw_field_name} {slice.selection.orientation}
      </span>
      <div
        className="slice-plane-cells"
        style={{ gridTemplateColumns: `repeat(${slice.values[0]?.length ?? 1}, minmax(0, 1fr))` }}
      >
        {cells.map((value, index) => (
          <span
            className="slice-plane-cell"
            key={`${title}-${index}`}
            style={sliceCellStyle(value, slice.stats)}
          />
        ))}
      </div>
    </div>
  );
}

function ScaleMarkers({
  pointCloud,
  projectionMode,
}: {
  pointCloud: PointCloudResponse | null;
  projectionMode: ProjectionMode;
}) {
  const showHeight = projectionMode !== "top_down";
  const horizontalCoordinate = projectionMode === "side_yz" ? "yh" : "xh";
  const horizontalLabel = projectionMode === "side_yz" ? "y" : "x";
  const activeRange =
    pointCloud?.stats.active_z_min !== null && pointCloud?.stats.active_z_max !== null
      ? `${formatCompactNumber(pointCloud?.stats.active_z_min ?? 0)}-${formatCompactNumber(
          pointCloud?.stats.active_z_max ?? 0,
        )} ${pointCloud?.coordinate_units.zh ?? ""}`.trim()
      : "unavailable";

  return (
    <div className="scale-markers" aria-label="Scale markers">
      <div
        className="axis-ticks axis-ticks-horizontal"
        aria-label={`${horizontalLabel}-axis ticks`}
      >
        {extentTicks(pointCloud, horizontalCoordinate).map((tick) => (
          <span
            key={`${horizontalCoordinate}-${tick.position}`}
            style={{ left: `${tick.position}%` }}
          >
            {horizontalLabel}: {tick.label}
          </span>
        ))}
      </div>
      {projectionMode === "top_down" && (
        <div className="axis-ticks axis-ticks-y" aria-label="y-axis ticks">
          {extentTicks(pointCloud, "yh").map((tick) => (
            <span key={`y-${tick.position}`} style={{ bottom: `${tick.position}%` }}>
              y: {tick.label}
            </span>
          ))}
        </div>
      )}
      {showHeight && (
        <div className="axis-ticks axis-ticks-height" aria-label="height-axis ticks">
          {extentTicks(pointCloud, "zh").map((tick) => (
            <span key={`z-${tick.position}`} style={{ bottom: `${tick.position}%` }}>
              height: {tick.label}
            </span>
          ))}
        </div>
      )}
      {showHeight && <p className="active-z-range">active cloud water: {activeRange}</p>}
    </div>
  );
}

function extentTicks(
  pointCloud: PointCloudResponse | null,
  coordinate: string,
): Array<{ position: number; label: string }> {
  const extent = pointCloud?.coordinate_extents[coordinate];
  if (!extent) return [];
  const midpoint = (extent.min + extent.max) / 2;
  const units = extent.units ? ` ${extent.units}` : "";
  return [
    { position: 12, label: `${formatCompactNumber(extent.min)}${units}` },
    { position: 50, label: `${formatCompactNumber(midpoint)}${units}` },
    { position: 88, label: `${formatCompactNumber(extent.max)}${units}` },
  ];
}

function SceneSliceSummary({ title, slice }: { title: string; slice: SliceResponse | null }) {
  if (!slice) {
    return (
      <section className="slice-plane-card" aria-label={title}>
        <h3>{title}</h3>
        <p>Slice unavailable.</p>
      </section>
    );
  }
  const selected = `${slice.selection.selected_dimension}[${slice.selection.selected_index}]`;
  const coordinate =
    slice.selection.level_coordinate_value !== null
      ? ` (${slice.selection.level_coordinate_value} ${slice.selection.level_units ?? ""}${
          slice.selection.level_meters !== null
            ? ` / ${slice.selection.level_meters.toLocaleString()} m`
            : ""
        })`
      : "";
  return (
    <section className="slice-plane-card" aria-label={title}>
      <h3>{title}</h3>
      <dl className="metric-grid">
        <Metric
          label="Field"
          value={`${slice.field.raw_field_name} (${slice.field.display_name})`}
        />
        <Metric label="Units" value={slice.field.units ?? "Units unavailable"} />
        <Metric label="Time" value={formatSeconds(slice.selection.time_seconds)} />
        <Metric label="Location" value={`${selected}${coordinate}`} />
        <Metric label="Min" value={formatMaybeNumber(slice.stats.min, slice.field.units)} />
        <Metric label="Max" value={formatMaybeNumber(slice.stats.max, slice.field.units)} />
        <Metric label="Dimensions" value={slice.dimension_order.join(", ")} />
        <Metric label="Rendering method" value={slice.provenance.rendering_method} />
      </dl>
      <p>{slice.provenance.provenance_label}</p>
      {slice.caveats.length > 0 && (
        <ul className="compact-list">
          {slice.caveats.map((caveat) => (
            <li key={`${title}-${caveat}`}>{caveat}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function activeSlicePlaneLabel(activeSlicePlane: SceneSlicePlane): string {
  const labels: Record<SceneSlicePlane, string> = {
    horizontal: "Height level (up/down)",
    vertical_x: "Y position (forward/back)",
    vertical_y: "X position (left/right)",
  };
  return labels[activeSlicePlane];
}

function activeSlicePlaneDescription(activeSlicePlane: SceneSlicePlane): string {
  const descriptions: Record<SceneSlicePlane, string> = {
    horizontal: "horizontal z/height slice",
    vertical_x: "vertical x-z slice",
    vertical_y: "vertical y-z slice",
  };
  return descriptions[activeSlicePlane];
}

function activeSlicePosition(
  activeSlicePlane: SceneSlicePlane,
  horizontalSlice: SliceResponse | null,
  verticalSlice: SliceResponse | null,
): string {
  const slice = activeSlicePlane === "horizontal" ? horizontalSlice : verticalSlice;
  if (!slice) return "";
  const coordinate = slice.selection.selected_coordinate_value;
  const units =
    slice.selection.level_units ?? slice.coordinate_units[slice.selection.selected_dimension];
  if (coordinate === null || coordinate === undefined) return "";
  const numericCoordinate = typeof coordinate === "number" ? coordinate : Number(coordinate);
  if (!Number.isFinite(numericCoordinate)) return String(coordinate);
  return `${formatCompactNumber(numericCoordinate)}${units ? ` ${units}` : ""}`;
}

function FieldInspector({ result }: { result: ResultCard }) {
  const [catalog, setCatalog] = useState<FieldCatalogResponse | null>(null);
  const [viewDefaults, setViewDefaults] = useState<ViewDefaultsResponse | null>(null);
  const [selectedFieldName, setSelectedFieldName] = useState("qc");
  const [timeIndex, setTimeIndex] = useState(0);
  const [horizontalLevelIndex, setHorizontalLevelIndex] = useState(0);
  const [verticalLevelIndex, setVerticalLevelIndex] = useState(0);
  const [viewMode, setViewMode] = useState<InspectorViewMode>("vertical_x");
  const [processMode, setProcessMode] = useState<ProcessMode>("thermal_fate");
  const [horizontalSlice, setHorizontalSlice] = useState<SliceResponse | null>(null);
  const [verticalSlice, setVerticalSlice] = useState<SliceResponse | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegionRequest | null>(null);
  const [regionDiagnostics, setRegionDiagnostics] =
    useState<SelectedRegionDiagnosticsResponse | null>(null);
  const [regionStatus, setRegionStatus] = useState("Select a slice cell to inspect a region.");
  const [regionError, setRegionError] = useState<string | null>(null);
  const [inspectorStatus, setInspectorStatus] = useState("Loading fields...");
  const [inspectorError, setInspectorError] = useState<string | null>(null);
  const [fieldLoadAttempt, setFieldLoadAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setInspectorStatus("Loading fields...");
    setInspectorError(null);
    setCatalog(null);
    setViewDefaults(null);
    setHorizontalSlice(null);
    setVerticalSlice(null);
    setSelectedRegion(null);
    setRegionDiagnostics(null);
    setRegionError(null);
    setRegionStatus("Select a slice cell to inspect a region.");
    setViewMode("vertical_x");
    setProcessMode("thermal_fate");
    withTimeout(
      Promise.all([
        fetchVisualizationFields(result.result_id),
        fetchVisualizationDefaults(result.result_id).catch(() => null),
      ]),
      "Timed out loading visualization fields. Check the backend and retry.",
    )
      .then(([payload, defaults]) => {
        if (!active) return;
        setCatalog(payload);
        setViewDefaults(defaults);
        const firstPreferred =
          payload.available_fields.find(
            (field) => field.raw_field_name === (defaults?.preferred_field ?? "qc"),
          ) ??
          payload.available_fields.find((field) => field.raw_field_name === "qc") ??
          payload.available_fields[0];
        const fieldDefaults = defaultsForField(defaults, firstPreferred?.raw_field_name);
        setSelectedFieldName(firstPreferred?.raw_field_name ?? "");
        setTimeIndex(defaultTimeIndex(firstPreferred, result, fieldDefaults));
        setHorizontalLevelIndex(defaultHorizontalLevel(firstPreferred, fieldDefaults));
        setVerticalLevelIndex(defaultVerticalIndex(firstPreferred, "vertical_x", fieldDefaults));
        setInspectorStatus(
          payload.available_fields.length > 0 ? "Fields loaded" : "No fields available",
        );
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setInspectorError(caught instanceof Error ? caught.message : "Unable to load fields.");
        setInspectorStatus("Field inspection unavailable");
      });
    return () => {
      active = false;
    };
  }, [fieldLoadAttempt, result]);

  const selectedField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === selectedFieldName),
    [catalog, selectedFieldName],
  );
  const selectedDefaults = defaultsForField(viewDefaults, selectedFieldName);
  const verticalOrientation = viewMode === "vertical_y" ? "vertical_y" : "vertical_x";

  useEffect(() => {
    if (!selectedField) return;
    setTimeIndex(defaultTimeIndex(selectedField, result, selectedDefaults));
    setHorizontalLevelIndex(defaultHorizontalLevel(selectedField, selectedDefaults));
    setVerticalLevelIndex(
      defaultVerticalIndex(selectedField, verticalOrientation, selectedDefaults),
    );
  }, [result, selectedDefaults, selectedField, verticalOrientation]);

  useEffect(() => {
    if (!selectedField) return;
    let active = true;
    setInspectorStatus("Loading slices...");
    setInspectorError(null);
    Promise.all([
      fetchVisualizationSlice(result.result_id, {
        field: selectedField.raw_field_name,
        timeIndex,
        orientation: "horizontal",
        levelIndex: horizontalLevelIndex,
      }),
      fetchVisualizationSlice(result.result_id, {
        field: selectedField.raw_field_name,
        timeIndex,
        orientation: verticalOrientation,
        levelIndex: verticalLevelIndex,
      }),
    ])
      .then(([horizontal, vertical]) => {
        if (!active) return;
        setHorizontalSlice(horizontal);
        setVerticalSlice(vertical);
        setInspectorStatus("Slices loaded");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setHorizontalSlice(null);
        setVerticalSlice(null);
        setInspectorError(caught instanceof Error ? caught.message : "Unable to load slices.");
        setInspectorStatus("Slice request failed");
      });
    return () => {
      active = false;
    };
  }, [
    horizontalLevelIndex,
    result.result_id,
    selectedField,
    timeIndex,
    verticalLevelIndex,
    verticalOrientation,
  ]);

  useEffect(() => {
    if (!selectedRegion) {
      setRegionDiagnostics(null);
      setRegionError(null);
      setRegionStatus("Select a slice cell to inspect a region.");
      return;
    }
    let active = true;
    setRegionDiagnostics(null);
    setRegionError(null);
    setRegionStatus("Loading selected-region diagnostics...");
    fetchSelectedRegionDiagnostics(result.result_id, selectedRegion)
      .then((payload) => {
        if (!active) return;
        setRegionDiagnostics(payload);
        setRegionStatus("Selected-region diagnostics loaded");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setRegionDiagnostics(null);
        setRegionError(
          caught instanceof Error ? caught.message : "Unable to inspect the selected region.",
        );
        setRegionStatus("Selected-region request failed");
      });
    return () => {
      active = false;
    };
  }, [result.result_id, selectedRegion]);

  const timeOptions = selectedField?.time_coordinate_values ?? [];
  const verticalSize = selectedField?.coordinate_names.vertical
    ? selectedField.shape[selectedField.dimensions.indexOf(selectedField.coordinate_names.vertical)]
    : 1;
  const ySize = selectedField?.coordinate_names.y
    ? selectedField.shape[selectedField.dimensions.indexOf(selectedField.coordinate_names.y)]
    : 1;
  const xSize = selectedField?.coordinate_names.x
    ? selectedField.shape[selectedField.dimensions.indexOf(selectedField.coordinate_names.x)]
    : 1;
  const verticalSliceMax = verticalOrientation === "vertical_x" ? ySize : xSize;
  const activeSlice = viewMode === "horizontal" ? horizontalSlice : verticalSlice;

  function selectRegionFromSlice(slice: SliceResponse, rowIndex: number, columnIndex: number) {
    setSelectedRegion(selectionFromSlice(slice, rowIndex, columnIndex, "column"));
  }

  function selectPointFromActiveSlice() {
    if (!activeSlice) return;
    const rowIndex = Math.floor(activeSlice.values.length / 2);
    const columnIndex = Math.floor((activeSlice.values[0]?.length ?? 1) / 2);
    setSelectedRegion(selectionFromSlice(activeSlice, rowIndex, columnIndex, "point"));
  }

  function selectBoxFromActiveSlice() {
    if (!activeSlice) return;
    const rowIndex = Math.floor(activeSlice.values.length / 2);
    const columnIndex = Math.floor((activeSlice.values[0]?.length ?? 1) / 2);
    const center = selectionFromSlice(activeSlice, rowIndex, columnIndex, "column");
    setSelectedRegion({
      regionType: "box",
      xStart: Math.max(0, (center.xIndex ?? 0) - 1),
      xEnd: (center.xIndex ?? 0) + 1,
      yStart: Math.max(0, (center.yIndex ?? 0) - 1),
      yEnd: (center.yIndex ?? 0) + 1,
      zStart: Math.max(0, (center.zIndex ?? 0) - 1),
      zEnd: (center.zIndex ?? 0) + 1,
    });
  }

  return (
    <section className="field-inspector" aria-labelledby="field-inspector-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">2-D field inspection</p>
          <h2 id="field-inspector-title">Inspect CM1 fields</h2>
        </div>
        <p className="state-chip">{inspectorStatus}</p>
      </div>

      <p>
        These slices are backend-prepared inspections of CM1 output. The browser is not parsing raw
        NetCDF, and this is not a 3-D visualization.
      </p>

      {inspectorError && (
        <div role="alert">
          <p>{inspectorError}</p>
          <button type="button" onClick={() => setFieldLoadAttempt((current) => current + 1)}>
            Retry loading fields
          </button>
        </div>
      )}

      {catalog && catalog.available_fields.length === 0 && (
        <p role="status">No qc/w/qr fields are available for this result.</p>
      )}

      {catalog && selectedField && (
        <>
          <div className="inspector-controls">
            <ProcessModeControl processMode={processMode} onProcessModeChange={setProcessMode} />

            <fieldset className="view-mode-control">
              <legend>Slice view</legend>
              <div className="segmented-buttons">
                <button
                  type="button"
                  className={viewMode === "horizontal" ? "active-control" : ""}
                  onClick={() => setViewMode("horizontal")}
                >
                  Horizontal
                </button>
                <button
                  type="button"
                  className={viewMode === "vertical_x" ? "active-control" : ""}
                  onClick={() => setViewMode("vertical_x")}
                >
                  Vertical X
                </button>
                <button
                  type="button"
                  className={viewMode === "vertical_y" ? "active-control" : ""}
                  onClick={() => setViewMode("vertical_y")}
                >
                  Vertical Y
                </button>
                <button
                  type="button"
                  className={viewMode === "compare" ? "active-control" : ""}
                  onClick={() => setViewMode("compare")}
                >
                  Compare
                </button>
              </div>
            </fieldset>

            <label htmlFor="inspect-field">
              Field
              <select
                id="inspect-field"
                value={selectedFieldName}
                onChange={(event) => setSelectedFieldName(event.target.value)}
              >
                {catalog.available_fields.map((field) => (
                  <option key={field.raw_field_name} value={field.raw_field_name}>
                    {field.raw_field_name} - {field.display_name}
                  </option>
                ))}
              </select>
            </label>

            <label htmlFor="inspect-time">
              Time
              <select
                id="inspect-time"
                value={timeIndex}
                onChange={(event) => setTimeIndex(Number(event.target.value))}
              >
                {timeOptions.map((value, index) => (
                  <option key={`${value}-${index}`} value={index}>
                    {formatTimeValue(value)}
                  </option>
                ))}
              </select>
            </label>

            <label htmlFor="horizontal-level">
              Horizontal level
              <input
                id="horizontal-level"
                type="number"
                min={0}
                max={Math.max(0, verticalSize - 1)}
                value={horizontalLevelIndex}
                onChange={(event) => setHorizontalLevelIndex(Number(event.target.value))}
              />
            </label>

            <label htmlFor="vertical-index">
              Vertical slice index
              <input
                id="vertical-index"
                type="number"
                min={0}
                max={Math.max(0, verticalSliceMax - 1)}
                value={verticalLevelIndex}
                onChange={(event) => setVerticalLevelIndex(Number(event.target.value))}
              />
            </label>
          </div>

          <dl className="metric-grid">
            <Metric
              label="Field"
              value={`${selectedField.raw_field_name} (${selectedField.display_name})`}
            />
            <Metric label="Units" value={selectedField.units ?? "Units unavailable"} />
            <Metric
              label="Selected time"
              value={formatTimeValue(
                timeOptions[Math.min(timeIndex, timeOptions.length - 1)] ?? null,
              )}
            />
            <Metric label="Default source" value={selectedDefaults?.source ?? "domain center"} />
            <Metric label="Native grid" value={selectedField.native_grid} />
          </dl>

          <ProcessOverlayPanel
            result={result}
            catalog={catalog}
            selectedField={selectedField}
            processMode={processMode}
            slice={viewMode === "horizontal" ? horizontalSlice : verticalSlice}
          />

          <SelectedRegionControls
            selectedRegion={selectedRegion}
            regionStatus={regionStatus}
            onSelectPoint={selectPointFromActiveSlice}
            onSelectBox={selectBoxFromActiveSlice}
            onClear={() => setSelectedRegion(null)}
          />

          <div className={viewMode === "compare" ? "slice-grid" : "primary-slice-grid"}>
            {(viewMode === "horizontal" || viewMode === "compare") && (
              <SlicePanel
                title="Horizontal slice"
                slice={horizontalSlice}
                selectedRegion={selectedRegion}
                onSelectRegion={selectRegionFromSlice}
              />
            )}
            {(viewMode === "vertical_x" || viewMode === "vertical_y" || viewMode === "compare") && (
              <SlicePanel
                title={viewMode === "vertical_y" ? "Vertical Y slice" : "Vertical X slice"}
                slice={verticalSlice}
                selectedRegion={selectedRegion}
                onSelectRegion={selectRegionFromSlice}
              />
            )}
          </div>

          <SelectedRegionInspector
            selectedRegion={selectedRegion}
            diagnostics={regionDiagnostics}
            status={regionStatus}
            error={regionError}
          />

          <details>
            <summary>Technical field details</summary>
            <p>{catalog.provenance.provenance_label}</p>
            <ul className="compact-list">
              <li>Native-grid view; no interpolation</li>
              <li>Raw numeric values live under each slice's technical details.</li>
              <li>No raw NetCDF parsing in the browser</li>
            </ul>
          </details>
        </>
      )}
    </section>
  );
}

function SlicePanel({
  title,
  slice,
  selectedRegion,
  onSelectRegion,
}: {
  title: string;
  slice: SliceResponse | null;
  selectedRegion?: SelectedRegionRequest | null;
  onSelectRegion?: (slice: SliceResponse, rowIndex: number, columnIndex: number) => void;
}) {
  if (!slice) {
    return (
      <section className="slice-panel" aria-label={title}>
        <h3>{title}</h3>
        <p>Slice unavailable.</p>
      </section>
    );
  }

  return (
    <section className="slice-panel" aria-label={title}>
      <h3>{title}</h3>
      <dl className="metric-grid">
        <Metric label="Orientation" value={slice.selection.orientation} />
        <Metric label="Time" value={formatSeconds(slice.selection.time_seconds)} />
        <Metric label="Shape" value={slice.shape.join(" x ")} />
        <Metric label="Dimensions" value={slice.dimension_order.join(", ")} />
        <Metric label="Min" value={formatMaybeNumber(slice.stats.min, slice.field.units)} />
        <Metric label="Max" value={formatMaybeNumber(slice.stats.max, slice.field.units)} />
        <Metric label="Finite values" value={String(slice.stats.finite_count)} />
        <Metric label="Non-finite values" value={String(slice.stats.non_finite_count)} />
      </dl>
      {slice.selection.level_units && (
        <p>
          Selected level: {String(slice.selection.level_coordinate_value)}{" "}
          {slice.selection.level_units}
          {slice.selection.level_meters !== null
            ? ` (${slice.selection.level_meters.toLocaleString()} m)`
            : ""}
        </p>
      )}
      <SliceHeatmap
        title={title}
        slice={slice}
        selectedRegion={selectedRegion}
        onSelectRegion={onSelectRegion}
      />
      <div className="heatmap-legend" aria-label={`${title} color scale`}>
        <span>{formatMaybeNumber(slice.stats.min, slice.field.units)}</span>
        <span className="heatmap-scale" />
        <span>{formatMaybeNumber(slice.stats.max, slice.field.units)}</span>
      </div>
      <details>
        <summary>Technical slice details</summary>
        <p>{slice.provenance.provenance_label}</p>
        {slice.caveats.length > 0 && (
          <ul className="compact-list">
            {slice.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        )}
        <div className="slice-values" role="table" aria-label={`${title} raw values`}>
          {slice.values.map((row, rowIndex) => (
            <div className="slice-row" role="row" key={`${title}-${rowIndex}`}>
              {row.map((value, columnIndex) => (
                <span
                  className="slice-cell"
                  role="cell"
                  key={`${title}-${rowIndex}-${columnIndex}`}
                >
                  {value === null ? "null" : formatCompactNumber(value)}
                </span>
              ))}
            </div>
          ))}
        </div>
      </details>
    </section>
  );
}

function ProcessModeControl({
  processMode,
  onProcessModeChange,
}: {
  processMode: ProcessMode;
  onProcessModeChange: (mode: ProcessMode) => void;
}) {
  return (
    <fieldset className="process-mode-control">
      <legend>Process mode</legend>
      <select
        aria-label="Process mode"
        value={processMode}
        onChange={(event) => onProcessModeChange(event.target.value as ProcessMode)}
      >
        {PROCESS_MODES.map((mode) => (
          <option key={mode} value={mode}>
            {processModeLabel(mode)}
          </option>
        ))}
      </select>
    </fieldset>
  );
}

function ProcessOverlayPanel({
  result,
  catalog,
  selectedField,
  processMode,
  slice,
}: {
  result: ResultCard;
  catalog: FieldCatalogResponse | null;
  selectedField: VisualizableField | undefined;
  processMode: ProcessMode;
  slice?: SliceResponse | null;
}) {
  const summary = processModeSummary(processMode, result, catalog, selectedField, slice ?? null);
  return (
    <section className="process-overlay-panel" aria-label="Thermal Fate process overlay">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Thermal Fate overlay</p>
          <h3>{processModeLabel(processMode)}</h3>
        </div>
        <StatusBadge
          label={processSupportLabel(summary.support)}
          tone={summary.support === "supported" ? "good" : summary.support === "candidate" ? "neutral" : "warning"}
        />
      </div>
      <p>{summary.description}</p>
      <dl className="metric-grid">
        <Metric label="Evidence type" value={summary.evidenceType} />
        <Metric label="Source" value={summary.source} />
        <Metric label="Process confidence" value={processSupportLabel(summary.support)} />
        <Metric label="Selected field" value={selectedField?.raw_field_name ?? "Unavailable"} />
      </dl>
      {summary.annotations.length > 0 && (
        <ul className="compact-list">
          {summary.annotations.map((annotation) => (
            <li key={annotation}>{annotation}</li>
          ))}
        </ul>
      )}
      {summary.caveats.length > 0 && (
        <details>
          <summary>Process caveats</summary>
          <ul className="compact-list">
            {summary.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

function SelectedRegionControls({
  selectedRegion,
  regionStatus,
  onSelectPoint,
  onSelectBox,
  onClear,
}: {
  selectedRegion: SelectedRegionRequest | null;
  regionStatus: string;
  onSelectPoint: () => void;
  onSelectBox: () => void;
  onClear: () => void;
}) {
  return (
    <section className="selected-region-controls" aria-label="Selected-region controls">
      <div>
        <p className="eyebrow">What happened here?</p>
        <h3>Thermal Fate Inspector</h3>
        <p>
          Click a slice cell to inspect the nearest column, or use the buttons below for a bounded
          point or box around the current view center.
        </p>
      </div>
      <div className="segmented-buttons">
        <button type="button" onClick={onSelectPoint}>
          Inspect center point
        </button>
        <button type="button" onClick={onSelectBox}>
          Inspect small box
        </button>
        <button type="button" onClick={onClear} disabled={!selectedRegion}>
          Clear selection
        </button>
      </div>
      <p className="state-chip">{selectedRegion ? selectionLabel(selectedRegion) : regionStatus}</p>
    </section>
  );
}

function SelectedRegionInspector({
  selectedRegion,
  diagnostics,
  status,
  error,
}: {
  selectedRegion: SelectedRegionRequest | null;
  diagnostics: SelectedRegionDiagnosticsResponse | null;
  status: string;
  error: string | null;
}) {
  return (
    <section className="selected-region-inspector" aria-label="Thermal Fate Inspector">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Selected region</p>
          <h3>What happened here?</h3>
        </div>
        <p className="state-chip">{status}</p>
      </div>

      {!selectedRegion && (
        <p>
          No region is selected. Select a point, column, or box to request backend Thermal Fate
          diagnostics.
        </p>
      )}

      {error && <p role="alert">{error}</p>}

      {diagnostics && (
        <>
          <div className="inspector-summary">
            <StatusBadge
              label={diagnostics.interpretation.thermal_fate_label}
              tone={
                diagnostics.interpretation.confidence === "supported"
                  ? "good"
                  : diagnostics.interpretation.confidence === "candidate"
                    ? "neutral"
                    : "warning"
              }
            />
            <p>{diagnostics.interpretation.summary}</p>
          </div>

          <dl className="metric-grid">
            <Metric
              label="Confidence"
              value={processSupportLabel(diagnostics.interpretation.confidence)}
            />
            <Metric
              label="Main limiting factor"
              value={humanize(diagnostics.interpretation.main_limiting_factor)}
            />
            <Metric label="Region type" value={humanize(diagnostics.region.region_type)} />
            <Metric label="Native grid" value={diagnostics.region.native_grid ?? "Unavailable"} />
            <Metric label="Cell count" value={String(diagnostics.region.cell_count ?? "unknown")} />
            <Metric
              label="First local cloud time"
              value={formatSeconds(diagnostics.diagnostics.first_local_cloud_time_seconds)}
            />
            <Metric
              label="Local max qc"
              value={formatScientific(diagnostics.diagnostics.local_max_qc_kg_kg, "kg/kg")}
            />
            <Metric
              label="Local max w"
              value={formatNumber(diagnostics.diagnostics.local_max_w_m_s, "m/s")}
            />
            <Metric
              label="Local min w"
              value={formatNumber(diagnostics.diagnostics.local_min_w_m_s, "m/s")}
            />
            <Metric
              label="Local rain"
              value={diagnostics.diagnostics.local_rain_present ? "Rain detected" : "No rain detected"}
            />
          </dl>

          <section aria-label="Selected-region bounds">
            <h4>Selected-region bounds</h4>
            <dl className="metric-grid">
              <Metric label="x" value={axisSelectionLabel(diagnostics.region.x)} />
              <Metric label="y" value={axisSelectionLabel(diagnostics.region.y)} />
              <Metric label="vertical" value={axisSelectionLabel(diagnostics.region.vertical)} />
            </dl>
          </section>

          <section aria-label="Domain comparison">
            <h4>Compared with whole result</h4>
            <dl className="metric-grid">
              <Metric
                label="Max w fraction"
                value={formatRatio(diagnostics.comparison_to_domain.local_max_w_fraction_of_domain)}
              />
              <Metric
                label="Max qc fraction"
                value={formatRatio(diagnostics.comparison_to_domain.local_max_qc_fraction_of_domain)}
              />
              <Metric
                label="First cloud delta"
                value={formatSignedSeconds(
                  diagnostics.comparison_to_domain.local_first_cloud_time_delta_seconds,
                )}
              />
              <Metric
                label="Cloud-top fraction"
                value={formatRatio(diagnostics.comparison_to_domain.local_cloud_top_fraction_of_domain)}
              />
            </dl>
          </section>

          <details>
            <summary>Technical selected-region details</summary>
            <p>{diagnostics.provenance.provenance_label}</p>
            <ul className="compact-list">
              <li>Backend xarray selected-region diagnostics; no raw NetCDF parsing in browser.</li>
              <li>Selected region is not cloud-object tracking.</li>
              {_dedupeStrings([
                ...diagnostics.caveats,
                ...diagnostics.interpretation.caveats,
                ...diagnostics.comparison_to_domain.caveats,
              ]).map((caveat) => (
                <li key={caveat}>{caveat}</li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}

function SliceHeatmap({
  title,
  slice,
  selectedRegion,
  onSelectRegion,
}: {
  title: string;
  slice: SliceResponse;
  selectedRegion?: SelectedRegionRequest | null;
  onSelectRegion?: (slice: SliceResponse, rowIndex: number, columnIndex: number) => void;
}) {
  return (
    <div className="slice-heatmap" role="img" aria-label={`${title} heatmap`}>
      {slice.values.map((row, rowIndex) => (
        <div className="heatmap-row" key={`${title}-heatmap-${rowIndex}`}>
          {row.map((value, columnIndex) => {
            const selected = isSelectedSliceCell(slice, selectedRegion, rowIndex, columnIndex);
            return (
              <button
                type="button"
                className={`heatmap-cell${selected ? " heatmap-cell-selected" : ""}`}
                key={`${title}-heatmap-${rowIndex}-${columnIndex}`}
                title={value === null ? "missing" : formatMaybeNumber(value, slice.field.units)}
                aria-label={`Inspect ${title} row ${rowIndex + 1}, column ${columnIndex + 1}`}
                style={sliceCellStyle(value, slice.stats)}
                onClick={() => onSelectRegion?.(slice, rowIndex, columnIndex)}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

function OutcomeBadge({ result }: { result: ResultCard }) {
  const label = cloudOutcome(result);
  return (
    <StatusBadge
      label={label}
      tone={label === "Cloud formed" ? "good" : label === "No cloud formed" ? "warning" : "neutral"}
    />
  );
}

function StatusBadge({ label, tone }: { label: string; tone: "good" | "warning" | "neutral" }) {
  return <span className={`status-badge status-badge-${tone}`}>{label}</span>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

const PROCESS_MODES: ProcessMode[] = [
  "thermal_fate",
  "cloud_water",
  "updrafts",
  "cloud_lifecycle",
  "cap",
  "moisture",
  "buoyancy",
  "deep_breakthrough",
  "precipitation_feedback",
];

type ProcessSupport = "supported" | "candidate" | "insufficient_evidence" | "unsupported_missing_fields";

type ProcessModeSummary = {
  support: ProcessSupport;
  evidenceType: string;
  source: string;
  description: string;
  annotations: string[];
  caveats: string[];
};

function processModeSummary(
  mode: ProcessMode,
  result: ResultCard,
  catalog: FieldCatalogResponse | null,
  selectedField: VisualizableField | undefined,
  slice: SliceResponse | null,
): ProcessModeSummary {
  const fields = new Set(catalog?.available_fields.map((field) => field.raw_field_name) ?? []);
  const caveats = [...result.caveats];
  const thermalLabel = result.thermal_fate_label ?? "Insufficient evidence";
  const confidence = normalizeProcessSupport(result.thermal_fate_confidence);
  const fieldSource = selectedField
    ? `${selectedField.raw_field_name} on native ${selectedField.native_grid}`
    : "No selected field";
  const sliceAnnotation = slice
    ? `Active slice ${slice.selection.orientation} shows ${slice.field.raw_field_name} min ${formatMaybeNumber(
        slice.stats.min,
        slice.field.units,
      )}, max ${formatMaybeNumber(slice.stats.max, slice.field.units)}.`
    : "No active slice summary is available yet.";

  if (mode === "thermal_fate") {
    return {
      support: confidence,
      evidenceType: "backend process diagnostics",
      source: "Result Card process fields from ingested CM1 output",
      description: `${thermalLabel}. ${
        result.main_limiting_factor && result.main_limiting_factor !== "unknown"
          ? `Main limiting factor: ${result.main_limiting_factor}.`
          : "No supported main limiting factor is available yet."
      }`,
      annotations: [
        `Diagnostics summary: ${result.diagnostics_summary ?? "Unavailable"}`,
        `Cloud: ${cloudOutcome(result)}; rain: ${rainOutcome(result.rain_present)}`,
      ],
      caveats,
    };
  }

  if (mode === "cloud_water") {
    return {
      support: fields.has("qc") ? "supported" : "unsupported_missing_fields",
      evidenceType: "direct CM1 field plus derived threshold diagnostics",
      source: fieldSource,
      description: fields.has("qc")
        ? "Cloud-water overlay uses direct qc output with the documented cloud threshold."
        : "Cloud-water overlay is unavailable because qc is missing for this result.",
      annotations: [
        `Max qc: ${formatScientific(result.max_qc_kg_kg, "kg/kg")}`,
        `First cloud time: ${formatSeconds(result.first_cloud_time_seconds)}`,
        sliceAnnotation,
      ],
      caveats: fields.has("qc") ? caveats : [...caveats, "missing_visualization_field:qc"],
    };
  }

  if (mode === "updrafts") {
    return {
      support: fields.has("w") ? "supported" : "unsupported_missing_fields",
      evidenceType: "direct CM1 vertical-velocity field",
      source: fieldSource,
      description: fields.has("w")
        ? "Updraft overlay uses direct w output and max/min vertical velocity summaries."
        : "Updraft overlay is unavailable because w is missing for this result.",
      annotations: [
        `Max w: ${formatNumber(result.max_w_m_s, "m/s")}`,
        `Min w: ${formatNumber(result.min_w_m_s, "m/s")}`,
        sliceAnnotation,
      ],
      caveats: fields.has("w") ? caveats : [...caveats, "missing_visualization_field:w"],
    };
  }

  if (mode === "cloud_lifecycle") {
    const available = result.first_cloud_time_seconds !== null || result.max_qc_kg_kg !== null;
    return {
      support: available ? "candidate" : "insufficient_evidence",
      evidenceType: "derived cloud lifecycle diagnostics",
      source: "Ingested result diagnostics",
      description: available
        ? "Cloud lifecycle uses first cloud time, qc summaries, cloud fraction, and slice annotations where available."
        : "Cloud lifecycle diagnostics are not available for this result.",
      annotations: [
        `First cloud time: ${formatSeconds(result.first_cloud_time_seconds)}`,
        `Max qc: ${formatScientific(result.max_qc_kg_kg, "kg/kg")}`,
        sliceAnnotation,
      ],
      caveats,
    };
  }

  if (mode === "cap") {
    const capped = result.scenario_id.includes("capped") || result.controls.cap_strength === "stronger";
    return {
      support: capped ? "candidate" : "insufficient_evidence",
      evidenceType: "scenario/control proxy plus cloud-top diagnostics",
      source: "Scenario metadata and derived diagnostics",
      description: capped
        ? "Cap/inversion overlay is a candidate process view; current data suggests cap context but does not directly diagnose inhibition."
        : "Cap/inversion overlay needs stronger-cap metadata or cap-relative diagnostics before making a process claim.",
      annotations: [
        `Cap strength: ${String(result.controls.cap_strength ?? "not recorded")}`,
        `Thermal Fate label: ${thermalLabel}`,
      ],
      caveats: [...caveats, "cap_layer_annotation_is_proxy_without_full_cap_diagnostics"],
    };
  }

  if (mode === "precipitation_feedback") {
    return {
      support: result.rain_present ? "candidate" : "unsupported_missing_fields",
      evidenceType: "qr/rain and downdraft proxy diagnostics",
      source: "Rain summary and w min diagnostics",
      description: result.rain_present
        ? "Rain is present, but precipitation-feedback needs downdraft/cold-pool evidence before a stronger claim."
        : "Precipitation-feedback overlay is unavailable because rain/qr was not detected or not output.",
      annotations: [
        `Rain: ${rainOutcome(result.rain_present)}`,
        `Min w: ${formatNumber(result.min_w_m_s, "m/s")}`,
      ],
      caveats: [...caveats, "precipitation_feedback_requires_downdraft_and_cold_pool_diagnostics"],
    };
  }

  const unavailableLabels: Record<ProcessMode, string> = {
    thermal_fate: "",
    cloud_water: "",
    updrafts: "",
    cloud_lifecycle: "",
    cap: "",
    precipitation_feedback: "",
    moisture: "Moisture / saturation diagnostics need qv/RH or saturation-deficit fields.",
    buoyancy: "Buoyancy diagnostics need thermodynamic fields and a documented buoyancy method.",
    deep_breakthrough: "Deep-breakthrough diagnostics need CAPE/CIN/LFC/EL and sustained-updraft context.",
  };
  return {
    support: "unsupported_missing_fields",
    evidenceType: "unavailable diagnostic group",
    source: "Required source fields were not ingested",
    description: unavailableLabels[mode],
    annotations: ["Unavailable diagnostics are shown explicitly rather than hidden."],
    caveats: [...caveats, `${mode}_unsupported_missing_fields`],
  };
}

function processModeLabel(mode: ProcessMode): string {
  const labels: Record<ProcessMode, string> = {
    thermal_fate: "Thermal Fate summary",
    cloud_water: "Cloud Water",
    updrafts: "Updrafts",
    moisture: "Moisture / Saturation",
    buoyancy: "Buoyancy",
    cap: "Cap / Inversion",
    cloud_lifecycle: "Cloud Lifecycle",
    deep_breakthrough: "Deep Breakthrough",
    precipitation_feedback: "Precipitation Feedback",
  };
  return labels[mode];
}

function normalizeProcessSupport(value: string | null | undefined): ProcessSupport {
  if (
    value === "supported" ||
    value === "candidate" ||
    value === "insufficient_evidence" ||
    value === "unsupported_missing_fields"
  ) {
    return value;
  }
  return "insufficient_evidence";
}

function processSupportLabel(value: ProcessSupport): string {
  const labels: Record<ProcessSupport, string> = {
    supported: "Supported",
    candidate: "Candidate",
    insufficient_evidence: "Insufficient evidence",
    unsupported_missing_fields: "Unavailable",
  };
  return labels[value];
}

function selectionFromSlice(
  slice: SliceResponse,
  rowIndex: number,
  columnIndex: number,
  regionType: "point" | "column",
): SelectedRegionRequest {
  const orientation = slice.selection.orientation;
  if (orientation === "horizontal") {
    return {
      regionType,
      xIndex: columnIndex,
      yIndex: rowIndex,
      zIndex: slice.selection.selected_index,
      neighborhood: regionType === "point" ? 0 : 1,
    };
  }
  if (orientation === "vertical_x") {
    return {
      regionType,
      xIndex: columnIndex,
      yIndex: slice.selection.selected_index,
      zIndex: rowIndex,
      neighborhood: regionType === "point" ? 0 : 1,
    };
  }
  return {
    regionType,
    xIndex: slice.selection.selected_index,
    yIndex: columnIndex,
    zIndex: rowIndex,
    neighborhood: regionType === "point" ? 0 : 1,
  };
}

function isSelectedSliceCell(
  slice: SliceResponse,
  selectedRegion: SelectedRegionRequest | null | undefined,
  rowIndex: number,
  columnIndex: number,
): boolean {
  if (!selectedRegion) return false;
  const candidate = selectionFromSlice(slice, rowIndex, columnIndex, "point");
  if (selectedRegion.regionType === "box") {
    return (
      candidate.xIndex !== undefined &&
      candidate.yIndex !== undefined &&
      candidate.zIndex !== undefined &&
      candidate.xIndex >= (selectedRegion.xStart ?? -Infinity) &&
      candidate.xIndex <= (selectedRegion.xEnd ?? Infinity) &&
      candidate.yIndex >= (selectedRegion.yStart ?? -Infinity) &&
      candidate.yIndex <= (selectedRegion.yEnd ?? Infinity) &&
      candidate.zIndex >= (selectedRegion.zStart ?? -Infinity) &&
      candidate.zIndex <= (selectedRegion.zEnd ?? Infinity)
    );
  }
  return (
    selectedRegion.xIndex === candidate.xIndex &&
    selectedRegion.yIndex === candidate.yIndex &&
    (selectedRegion.regionType === "column" || selectedRegion.zIndex === candidate.zIndex)
  );
}

function selectionLabel(selection: SelectedRegionRequest): string {
  if (selection.regionType === "box") {
    return `Box x ${selection.xStart}-${selection.xEnd}, y ${selection.yStart}-${selection.yEnd}, z ${selection.zStart}-${selection.zEnd}`;
  }
  const z = selection.regionType === "point" ? `, z ${selection.zIndex}` : "";
  return `${humanize(selection.regionType)} x ${selection.xIndex}, y ${selection.yIndex}${z}`;
}

function axisSelectionLabel(axis: AxisSelection | null): string {
  if (!axis) return "Unavailable";
  const coordinate =
    axis.start_coordinate === axis.end_coordinate
      ? String(axis.start_coordinate ?? "unknown")
      : `${String(axis.start_coordinate ?? "unknown")} to ${String(axis.end_coordinate ?? "unknown")}`;
  const index =
    axis.start_index === axis.end_index
      ? `${axis.dimension}[${axis.start_index}]`
      : `${axis.dimension}[${axis.start_index}..${axis.end_index}]`;
  return `${index}; ${coordinate}${axis.units ? ` ${axis.units}` : ""}`;
}

function formatRatio(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  return `${formatCompactNumber(value * 100)}%`;
}

function formatSignedSeconds(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatSeconds(value)}`;
}

function _dedupeStrings(values: string[]): string[] {
  return [...new Set(values)];
}

function parseTags(value: string): string[] {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function formatSeconds(value: number | null): string {
  if (value === null) return "Unavailable";
  return `${value.toLocaleString()} s`;
}

function formatScientific(value: number | null, units: string): string {
  if (value === null) return "Unavailable";
  return `${value.toExponential(3)} ${units}`;
}

function formatNumber(value: number | null, units: string): string {
  if (value === null) return "Unavailable";
  return `${Number(value.toFixed(3)).toLocaleString()} ${units}`;
}

function formatMaybeNumber(value: number | null, units: string | null): string {
  if (value === null) return "Unavailable";
  const suffix = units ? ` ${units}` : "";
  return `${formatCompactNumber(value)}${suffix}`;
}

function formatCompactNumber(value: number): string {
  if (Math.abs(value) > 0 && Math.abs(value) < 0.001) {
    return value.toExponential(3);
  }
  return Number(value.toFixed(4)).toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value.toLocaleString()} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let size = value / 1024;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  const digits = size >= 10 ? 1 : 2;
  return `${Number(size.toFixed(digits)).toLocaleString()} ${units[unitIndex]}`;
}

function formatTimeValue(value: number | string | null): string {
  if (value === null) return "Time unavailable";
  if (typeof value === "number") return `${value.toLocaleString()} s`;
  return value;
}

function runIdFromPackage(dryRun: DryRunResponse): string {
  return dryRun.package_dir.split("/").filter(Boolean).at(-1) ?? dryRun.report.scenario_id;
}

function userFacingRunWorkflowStatus(status: RunStatusResponse): string {
  if (status.lifecycle_state === "queued") return "Queued";
  if (status.lifecycle_state === "running") return "Running";
  if (status.lifecycle_state === "completed") {
    return status.product_state === "completed_cm1_result"
      ? "Completed CM1 result"
      : "Completed with no usable output";
  }
  if (status.lifecycle_state === "failed") return "Failed";
  if (status.lifecycle_state === "canceled") return "Canceled";
  return humanize(status.lifecycle_state);
}

function cloudPointStyle(
  point: [number, number, number, number],
  pointCloud: PointCloudResponse,
  projectionMode: ProjectionMode,
  stats: PointCloudResponse["stats"],
  opacity: number,
  pointSize: number,
): CSSProperties {
  const x = normalizeWithExtent(point[0], pointCloud.coordinate_extents.xh);
  const y = normalizeWithExtent(point[1], pointCloud.coordinate_extents.yh);
  const z = normalizeWithExtent(point[2], pointCloud.coordinate_extents.zh);
  const intensity = normalize(point[3], stats.min_value ?? point[3], stats.max_value ?? point[3]);
  const projected = projectPoint(x, y, z, projectionMode, pointCloud);
  const depthOpacity = projectionMode === "side_xz" ? 0.65 + y * 0.35 : 0.65 + x * 0.35;
  return {
    left: `${projected.left}%`,
    bottom: `${projected.bottom}%`,
    width: `${pointSize}px`,
    height: `${pointSize}px`,
    opacity: opacity * depthOpacity,
    transform: `translate(-50%, 50%) scale(${0.8 + intensity * 0.75})`,
    background: `rgba(229, 250, 255, ${0.44 + intensity * 0.46})`,
  };
}

function projectPoint(
  x: number,
  y: number,
  z: number,
  projectionMode: ProjectionMode,
  pointCloud: PointCloudResponse,
): { left: number; bottom: number } {
  const frame = plotFrame(pointCloud, projectionMode);
  if (projectionMode === "side_xz") {
    return { left: frame.left + x * frame.width, bottom: frame.bottom + z * frame.height };
  }
  if (projectionMode === "side_yz") {
    return { left: frame.left + y * frame.width, bottom: frame.bottom + z * frame.height };
  }
  if (projectionMode === "top_down") {
    return { left: frame.left + x * frame.width, bottom: frame.bottom + y * frame.height };
  }
  const verticalSpan = frame.height * 0.86;
  const depthLift = frame.height * 0.14;
  return {
    left: frame.left + (x * 0.72 + y * 0.28) * frame.width,
    bottom: frame.bottom + z * verticalSpan + y * depthLift,
  };
}

function plotFrameStyle(
  pointCloud: PointCloudResponse | null,
  projectionMode: ProjectionMode,
): CSSProperties & Record<string, string> {
  const frame = plotFrame(pointCloud, projectionMode);
  return {
    "--plot-left": `${frame.left}%`,
    "--plot-bottom": `${frame.bottom}%`,
    "--plot-width": `${frame.width}%`,
    "--plot-height": `${frame.height}%`,
  };
}

function plotFrame(
  pointCloud: PointCloudResponse | null,
  projectionMode: ProjectionMode,
): { left: number; bottom: number; width: number; height: number } {
  const left = 14;
  const width = 76;
  const horizontalCoordinate = projectionMode === "side_yz" ? "yh" : "xh";
  const verticalCoordinate = projectionMode === "top_down" ? "yh" : "zh";
  const horizontalRange = coordinateRange(pointCloud, horizontalCoordinate);
  const verticalRange = coordinateRange(pointCloud, verticalCoordinate);
  const ratio = horizontalRange > 0 ? verticalRange / horizontalRange : 0.7;
  const height = clamp(width * ratio, 20, 64);
  return {
    left,
    width,
    height,
    bottom: clamp((100 - height) / 2 - 3, 14, 32),
  };
}

function coordinateRange(pointCloud: PointCloudResponse | null, coordinate: string): number {
  const extent = pointCloud?.coordinate_extents[coordinate];
  if (!extent) return 1;
  const range = extent.max - extent.min;
  return Number.isFinite(range) && range > 0 ? range : 1;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function normalizeWithExtent(
  value: number,
  extent: { min: number; max: number; units: string | null } | undefined,
): number {
  if (!extent) return 0.5;
  return normalize(value, extent.min, extent.max);
}

function normalize(value: number, min: number, max: number): number {
  if (max <= min) return 0.5;
  return (value - min) / (max - min);
}

function extentLabel(pointCloud: PointCloudResponse | null, coordinate: string): string {
  const extent = pointCloud?.coordinate_extents[coordinate];
  if (!extent) return "Unavailable";
  const suffix = extent.units ? ` ${extent.units}` : "";
  return `${formatCompactNumber(extent.min)} to ${formatCompactNumber(extent.max)}${suffix}`;
}

function maxPointLocationLabel(pointCloud: PointCloudResponse | null): string {
  const location = pointCloud?.stats.max_value_location;
  if (!location) return "Unavailable";
  const units = pointCloud?.coordinate_units.zh ?? "";
  return `x ${formatCompactNumber(location.x)}, y ${formatCompactNumber(location.y)}, z ${formatCompactNumber(
    location.z,
  )}${units ? ` ${units}` : ""}, value ${formatCompactNumber(location.value)}`;
}

function projectionLabel(projectionMode: ProjectionMode): string {
  const labels: Record<ProjectionMode, string> = {
    side_xz: "Side x-z",
    side_yz: "Side y-z",
    top_down: "Top-down x-y",
    oblique: "Oblique overview",
  };
  return labels[projectionMode];
}

function projectionDescription(projectionMode: ProjectionMode): string {
  const descriptions: Record<ProjectionMode, string> = {
    side_xz:
      "Side x-z: height is vertical; y is compressed into point opacity for cloud-base and cloud-top checks.",
    side_yz:
      "Side y-z: height is vertical; x is compressed into point opacity for cloud-base and cloud-top checks.",
    top_down: "Top-down x-y: horizontal map view; height is not shown as vertical position.",
    oblique:
      "Oblique overview: interpretive overview based on CM1 coordinates, not a true perspective camera.",
  };
  return descriptions[projectionMode];
}

function sliceCellStyle(value: number | null, stats: SliceResponse["stats"]): CSSProperties {
  if (value === null) {
    return { background: "rgba(255, 255, 255, 0.12)" };
  }
  const intensity = normalize(value, stats.min ?? value, stats.max ?? value);
  return {
    background: `rgba(${78 + intensity * 110}, ${164 + intensity * 70}, ${206 + intensity * 40}, 0.72)`,
  };
}

function formatDate(value: string | null): string {
  if (!value) return "Time unavailable";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

function sectionLabel(section: WorkspaceSection): string {
  const labels: Record<WorkspaceSection, string> = {
    build: "Build",
    results: "Results",
    explore: "Explore",
  };
  return labels[section];
}

function resultsTabLabel(tab: ResultsTab): string {
  const labels: Record<ResultsTab, string> = {
    notebook: "Notebook",
    compare: "Compare",
    storage: "Storage",
  };
  return labels[tab];
}

function exploreTabLabel(tab: ExploreTab): string {
  const labels: Record<ExploreTab, string> = {
    slices: "2-D Slices",
    view3d: "3-D View",
  };
  return labels[tab];
}

function compactResultName(value: string): string {
  return value.length > 34 ? `${value.slice(0, 31)}...` : value;
}

function prioritizeResults(results: ResultCard[]): ResultCard[] {
  return [...results].sort((left, right) => resultPriority(right) - resultPriority(left));
}

function resultPriority(result: ResultCard): number {
  let score = 0;
  if (result.scenario_id === "baseline-shallow-cumulus") score += 30;
  if (result.run_size_preset === "quick_look") score += 20;
  if (result.source_lifecycle_state === "completed") score += 20;
  if (cloudOutcome(result) === "Cloud formed") score += 20;
  if (result.saved || result.protected) score += 10;
  score += new Date(result.completed_at ?? result.created_at).getTime() / 1_000_000_000_000;
  return score;
}

function isValidatedQuickLookBaseline(result: ResultCard): boolean {
  return (
    result.scenario_id === "baseline-shallow-cumulus" &&
    result.run_size_preset === "quick_look" &&
    result.source_lifecycle_state === "completed" &&
    cloudOutcome(result) === "Cloud formed"
  );
}

function isDryFailedContrast(result: ResultCard): boolean {
  return (
    result.scenario_id === "dry-failed-cumulus" &&
    result.run_size_preset === "quick_look" &&
    result.source_lifecycle_state === "completed" &&
    cloudOutcome(result) === "No cloud formed" &&
    result.rain_present === false &&
    (result.max_w_m_s ?? 0) > 0
  );
}

function defaultComparisonPair(results: ResultCard[]): {
  baseline: ResultCard | undefined;
  dryFailed: ResultCard | undefined;
} {
  const baseline =
    results.find(isValidatedQuickLookBaseline) ??
    results.find(
      (result) =>
        result.scenario_id === "baseline-shallow-cumulus" &&
        result.run_size_preset === "quick_look",
    ) ??
    results.find((result) => result.scenario_id === "baseline-shallow-cumulus");
  const dryFailed =
    results.find(isDryFailedContrast) ??
    results.find(
      (result) =>
        result.scenario_id === "dry-failed-cumulus" && result.run_size_preset === "quick_look",
    ) ??
    results.find((result) => result.scenario_id === "dry-failed-cumulus");
  return { baseline, dryFailed };
}

function comparisonMissingItems(pair: {
  baseline: ResultCard | undefined;
  dryFailed: ResultCard | undefined;
}): string[] {
  const missing = [];
  if (!pair.baseline) missing.push("Baseline Shallow Cumulus quick-look");
  if (!pair.dryFailed) missing.push("Dry Failed Cumulus quick-look");
  return missing;
}

function comparisonMeaning(result: ResultCard | undefined): string {
  if (!result) return "Unavailable";
  if (isDryFailedContrast(result)) {
    return "Moisture-limited failed cumulus: vertical motion is present, but qc stays below the cloud threshold and rain is absent.";
  }
  if (isValidatedQuickLookBaseline(result)) {
    return "Cloud-forming baseline: qc crosses the cloud threshold, rain is detected, and vertical motion is strong.";
  }
  return result.diagnostics_summary ?? "Diagnostics unavailable";
}

function userFacingStatus(result: ResultCard): string {
  if (result.saved || result.protected) return "Saved";
  if (result.source_lifecycle_state === "completed" && result.status.includes("ingested")) {
    return "Completed CM1 result";
  }
  if (result.status.includes("ingested")) return "Ingested";
  if (result.caveats.length > 0) return "Needs review";
  return humanize(result.status);
}

function caveatLabel(result: ResultCard): string {
  return cloudOutcome(result) === "Cloud formed" || isDryFailedContrast(result)
    ? "Minor caveat"
    : "Needs review";
}

function caveatTone(result: ResultCard): "good" | "warning" | "neutral" {
  return cloudOutcome(result) === "Cloud formed" || isDryFailedContrast(result)
    ? "neutral"
    : "warning";
}

function statusTone(result: ResultCard): "good" | "warning" | "neutral" {
  if (
    result.caveats.length > 0 &&
    cloudOutcome(result) !== "Cloud formed" &&
    !isDryFailedContrast(result)
  ) {
    return "warning";
  }
  if (result.source_lifecycle_state === "completed") return "good";
  return "neutral";
}

function cloudOutcome(result: ResultCard): string {
  if (!result.diagnostics_summary) return "Unknown";
  return result.diagnostics_summary.includes("cloud formed") &&
    !result.diagnostics_summary.includes("no cloud formed")
    ? "Cloud formed"
    : "No cloud formed";
}

function rainOutcome(value: boolean | null): string {
  if (value === null) return "Unknown";
  return value ? "Rain detected" : "No rain detected";
}

function outputSummary(summary: OutputFileSummary): string {
  const parts = [
    `${summary.model_output_count} model files`,
    `${summary.time_steps ?? "unknown"} time steps`,
  ];
  if (summary.stats_netcdf_count > 0) parts.push(`${summary.stats_netcdf_count} stats files`);
  if (summary.raw_cm1_artifact_count > 0) parts.push(`${summary.raw_cm1_artifact_count} raw files`);
  return parts.join(", ");
}

function storageOutputSummary(run: RunStorageEntry): string {
  const netcdf = run.output_summary.netcdf_paths ?? 0;
  const raw = run.output_summary.raw_cm1_artifacts ?? 0;
  const processed = run.output_summary.processed_artifacts ?? 0;
  if (run.output_artifact_count === 0) return "No output artifacts";
  return `${netcdf} NetCDF, ${raw} raw CM1, ${processed} processed`;
}

function storageResultOutputSummary(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result) return outputSummary(result.output_file_summary);
  return storageOutputSummary(run);
}

function resultForRun(results: ResultCard[], runId: string): ResultCard | undefined {
  return results.find((result) => result.run_id === runId);
}

function storageControlSummary(controls: ResultCard["controls"]): string {
  const keys = ["low_level_humidity", "surface_heating", "cap_strength"];
  const parts = keys.flatMap((key) => {
    const value = controls[key];
    return value === undefined ? [] : `${humanize(key)} ${humanize(String(value))}`;
  });
  return parts.length > 0 ? parts.join(" · ") : "controls recorded";
}

function canPreviewDelete(run: RunStorageEntry): boolean {
  return run.category !== "running" && !run.saved && !run.protected;
}

function deleteDisabledReason(run: RunStorageEntry): string {
  if (run.category === "running") return "Running runs cannot be deleted.";
  if (run.saved || run.protected) return "Saved/protected runs are not deleted from this UI.";
  return "Cleanup unavailable.";
}

function storageCategoryTone(run: RunStorageEntry): "good" | "warning" | "neutral" {
  if (run.category === "completed_with_output" || run.category === "saved_or_protected") {
    return "good";
  }
  if (
    run.category === "failed" ||
    run.category === "canceled" ||
    run.category === "malformed_manifest" ||
    run.category === "missing_manifest"
  ) {
    return "warning";
  }
  return "neutral";
}

function bothCatalogsContainField(
  left: FieldCatalogResponse,
  right: FieldCatalogResponse,
  fieldName: string | undefined,
): boolean {
  if (!fieldName) return false;
  return (
    left.available_fields.some((field) => field.raw_field_name === fieldName) &&
    right.available_fields.some((field) => field.raw_field_name === fieldName)
  );
}

function interestingTimeIndexForComparison(
  baselineCatalog: FieldCatalogResponse,
  dryFailedCatalog: FieldCatalogResponse,
  fieldName: string | undefined,
): number {
  const baselineField = baselineCatalog.available_fields.find(
    (field) => field.raw_field_name === fieldName,
  );
  const dryField = dryFailedCatalog.available_fields.find(
    (field) => field.raw_field_name === fieldName,
  );
  const length = Math.min(
    baselineField?.time_coordinate_values.length ?? 0,
    dryField?.time_coordinate_values.length ?? 0,
  );
  return Math.max(0, length - 1);
}

function clampIndex(index: number, length: number): number {
  return Math.min(Math.max(0, index), Math.max(0, length - 1));
}

function comparisonLevelIndex(
  field: VisualizableField | undefined,
  orientation: "horizontal" | "vertical_x",
): number {
  if (!field) return 0;
  if (orientation === "horizontal") return defaultHorizontalLevel(field);
  return defaultVerticalIndex(field, "vertical_x");
}

function defaultsForField(
  defaults: ViewDefaultsResponse | null,
  fieldName: string | undefined,
): FieldViewDefaults | undefined {
  if (!fieldName) return undefined;
  return defaults?.fields[fieldName];
}

function defaultTimeIndex(
  field: VisualizableField | undefined,
  result: ResultCard,
  defaults: FieldViewDefaults | undefined,
): number {
  if (defaults) return defaults.time_index;
  return interestingTimeIndex(field?.time_coordinate_values ?? [], result);
}

function interestingTimeIndex(
  timeOptions: Array<number | string | null>,
  result: ResultCard,
): number {
  const target =
    result.first_cloud_time_seconds ?? result.output_file_summary.last_output_time_seconds;
  return closestTimeIndex(timeOptions, target);
}

function jumpTimeIndex(
  timeOptions: Array<number | string | null>,
  result: ResultCard,
  target: "first-cloud" | "max-qc" | "max-w",
): number {
  const preferred =
    target === "first-cloud"
      ? result.first_cloud_time_seconds
      : (result.first_cloud_time_seconds ?? result.output_file_summary.last_output_time_seconds);
  return closestTimeIndex(timeOptions, preferred);
}

function applyScenePreset(
  preset: SceneViewPreset,
  options: {
    catalog: FieldCatalogResponse;
    viewDefaults: ViewDefaultsResponse | null;
    result: ResultCard;
    setViewPreset: (preset: SceneViewPreset) => void;
    setSelectedFieldName: (field: string) => void;
    setSliceFieldName: (field: string) => void;
    setTimeIndex: (index: number) => void;
    setHorizontalSliceLevel: (index: number) => void;
    setVerticalSliceIndex: (index: number) => void;
    setActiveSlicePlane: (plane: SceneSlicePlane) => void;
    setSliceOrientation: (orientation: "vertical_x" | "vertical_y") => void;
    setShowSlicePlanes: (show: boolean) => void;
    setProjectionMode: (mode: ProjectionMode) => void;
  },
): void {
  const fieldName = preset === "updraft" ? "w" : "qc";
  const field =
    options.catalog.available_fields.find((candidate) => candidate.raw_field_name === fieldName) ??
    options.catalog.available_fields.find((candidate) => candidate.raw_field_name === "qc") ??
    options.catalog.available_fields[0];
  if (!field) return;
  const defaults = defaultsForField(options.viewDefaults, field.raw_field_name);
  const orientation = preset === "updraft" ? "vertical_y" : "vertical_x";
  const activeSlicePlane: SceneSlicePlane =
    preset === "top-down-slice" || preset === "cloud-overview" ? "horizontal" : orientation;
  options.setViewPreset(preset);
  options.setSelectedFieldName(field.raw_field_name);
  options.setSliceFieldName(field.raw_field_name);
  options.setTimeIndex(defaultTimeIndex(field, options.result, defaults));
  options.setHorizontalSliceLevel(defaultHorizontalLevel(field, defaults));
  options.setVerticalSliceIndex(defaultVerticalIndex(field, orientation, defaults));
  options.setActiveSlicePlane(activeSlicePlane);
  options.setSliceOrientation(orientation);
  options.setShowSlicePlanes(preset !== "cloud-overview");
  options.setProjectionMode(
    preset === "vertical-cross-section"
      ? "side_xz"
      : preset === "top-down-slice"
        ? "top_down"
        : preset === "updraft"
          ? "side_yz"
          : "oblique",
  );
}

function closestTimeIndex(
  timeOptions: Array<number | string | null>,
  target: number | null,
): number {
  if (timeOptions.length === 0) return 0;
  if (target === null) return timeOptions.length - 1;
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  timeOptions.forEach((value, index) => {
    const seconds = numericTimeSeconds(value);
    if (seconds === null) return;
    const distance = Math.abs(seconds - target);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  });
  return bestIndex;
}

function numericTimeSeconds(value: number | string | null): number | null {
  if (typeof value === "number") return value;
  if (typeof value !== "string") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function defaultHorizontalLevel(
  field: VisualizableField | undefined,
  defaults?: FieldViewDefaults,
): number {
  if (defaults) return defaults.horizontal_level_index;
  return Math.max(0, Math.floor(verticalDimensionSize(field) / 3));
}

function defaultVerticalIndex(
  field: VisualizableField | undefined,
  orientation: "vertical_x" | "vertical_y",
  defaults?: FieldViewDefaults,
): number {
  if (defaults) {
    return orientation === "vertical_x" ? defaults.vertical_x_index : defaults.vertical_y_index;
  }
  const dimension =
    orientation === "vertical_x" ? field?.coordinate_names.y : field?.coordinate_names.x;
  if (!field || !dimension) return 0;
  const size = field.shape[field.dimensions.indexOf(dimension)] ?? 1;
  return Math.max(0, Math.floor(size / 2));
}

function verticalDimensionSize(field: VisualizableField | undefined): number {
  if (!field?.coordinate_names.vertical) return 1;
  return field.shape[field.dimensions.indexOf(field.coordinate_names.vertical)] ?? 1;
}
