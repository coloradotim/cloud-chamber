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

type BuildRunStage =
  | "not_packaged"
  | "package_ready"
  | "running"
  | "completed"
  | "failed"
  | "ingested";

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
  time_of_max_qc_seconds?: number | null;
  max_w_m_s: number | null;
  time_of_max_w_seconds?: number | null;
  min_w_m_s: number | null;
  time_of_min_w_seconds?: number | null;
  rain_present: boolean | null;
  first_rain_time_seconds?: number | null;
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
type ProjectionMode = "oblique" | "side_xz" | "side_yz" | "top_down";
type SceneSlicePlane = "horizontal" | "vertical_x" | "vertical_y";

const FIELD_LOAD_TIMEOUT_MS = 30000;

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
  const [focusedStorageRunId, setFocusedStorageRunId] = useState<string | null>(null);
  const [deletePreview, setDeletePreview] = useState<DeleteRunResponse | null>(null);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);
  const [, setStatus] = useState("Loading scenarios...");
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

  async function refreshStorageAfterWorkflow(statusWhenLoaded?: string) {
    try {
      const payload = await fetchStorageInventory();
      setStorageInventory(payload);
      setStorageStatus(
        statusWhenLoaded ??
          (payload.runs.length > 0 ? "Storage inventory loaded" : "No runtime runs"),
      );
    } catch (caught) {
      setStorageError(
        caught instanceof Error ? caught.message : "Unable to load runtime storage inventory.",
      );
      setStorageStatus("Storage unavailable");
    }
  }

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
      await refreshStorageAfterWorkflow("Package added to local pipeline");
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
      await refreshStorageAfterWorkflow("Local pipeline updated");
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
      await refreshStorageAfterWorkflow("Local pipeline updated");
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
      await refreshStorageAfterWorkflow("Local pipeline updated");
      setStatus("Ingested result metadata");
    } catch (caught) {
      setRunWorkflowError(
        caught instanceof Error ? caught.message : "Unable to ingest completed CM1 output.",
      );
      setStatus("Ingest blocked");
    }
  }

  async function handleLaunchStoredRun(manifestPath: string) {
    setRunWorkflowError(null);
    setStatus("Launching selected local package");
    try {
      const launched = await launchLocalRun(manifestPath);
      setRunStatus(launched);
      setStatus(userFacingRunWorkflowStatus(launched));
      await refreshStorageAfterWorkflow("Local pipeline updated");
    } catch (caught) {
      setRunWorkflowError(caught instanceof Error ? caught.message : "Unable to launch local CM1.");
      setStatus("Launch blocked");
    }
  }

  async function handleIngestStoredRun(manifestPath: string) {
    setRunWorkflowError(null);
    setStorageError(null);
    setStorageStatus("Ingesting completed output");
    setStatus("Ingesting selected completed output");
    try {
      const ingested = await ingestCompletedRun(manifestPath);
      setIngestedResultId(ingested.result_id);
      await refreshResults(ingested.result_id);
      await refreshStorageAfterWorkflow("Local pipeline updated");
      setStatus("Ingested result metadata");
      setStorageStatus("Ingested result metadata");
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to ingest completed CM1 output.";
      setRunWorkflowError(
        message,
      );
      setStorageError(message);
      setStatus("Ingest blocked");
      setStorageStatus("Ingest blocked");
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
        <div className="brand-mark">
          <p className="eyebrow">Local CM1 experiment lab</p>
          <h1>Cloud Chamber</h1>
        </div>

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
      </header>

      {activeSection === "build" && (
        <BuildWorkspace
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
          storageInventory={storageInventory}
          storageStatus={storageStatus}
          storageError={storageError}
          results={results}
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
          onLaunchStoredRun={handleLaunchStoredRun}
          onIngestStoredRun={handleIngestStoredRun}
          onOpenInResults={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("results");
            setActiveResultsTab("notebook");
          }}
          onInspectIngested={() => {
            if (ingestedResultId) setSelectedResultId(ingestedResultId);
            setActiveSection("explore");
          }}
          onOpenStoredResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("results");
            setActiveResultsTab("notebook");
          }}
          onExploreStoredResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
          }}
          onOpenStorage={(runId) => {
            setFocusedStorageRunId(runId ?? null);
            setActiveSection("results");
            setActiveResultsTab("storage");
          }}
          onRefreshStorage={handleRefreshStorage}
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
          focusedRunId={focusedStorageRunId}
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
          }}
          onManageLocalFiles={(result) => {
            setSelectedResultId(result.result_id);
            setFocusedStorageRunId(result.run_id);
            setActiveResultsTab("storage");
          }}
          onCompareInspect={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
          }}
          onStorageOpenResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveResultsTab("notebook");
          }}
          onStorageExploreResult={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("explore");
          }}
          onStorageIngestRun={handleIngestStoredRun}
          onRefreshStorage={handleRefreshStorage}
          onPreviewDelete={handlePreviewRunDelete}
          onConfirmDelete={handleConfirmRunDelete}
        />
      )}

      {activeSection === "explore" && (
        <ExploreWorkspace selectedResult={selectedResult} />
      )}
    </main>
  );
}

function BuildWorkspace({
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
  storageInventory,
  storageStatus,
  storageError,
  results,
  onSelectScenario,
  onControlChange,
  onRunSizeChange,
  onDryRun,
  onLaunchRun,
  onRefreshRunStatus,
  onIngestRun,
  onLaunchStoredRun,
  onIngestStoredRun,
  onOpenInResults,
  onInspectIngested,
  onOpenStoredResult,
  onExploreStoredResult,
  onOpenStorage,
  onRefreshStorage,
  onRetryScenarios,
}: {
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
  storageInventory: StorageInventoryResponse | null;
  storageStatus: string;
  storageError: string | null;
  results: ResultCard[];
  onSelectScenario: (scenarioId: string) => void;
  onControlChange: (controlId: string, value: string) => void;
  onRunSizeChange: (presetId: string) => void;
  onDryRun: (event: FormEvent<HTMLFormElement>) => void;
  onLaunchRun: () => void;
  onRefreshRunStatus: () => void;
  onIngestRun: () => void;
  onLaunchStoredRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenInResults: () => void;
  onInspectIngested: () => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onOpenStorage: (runId?: string | null) => void;
  onRefreshStorage: () => void;
  onRetryScenarios: () => void;
}) {
  const scenarioControlsReady = scenarioLoadState === "loaded" && selectedScenario !== undefined;
  const selectedRunSize = selectedScenario?.run_size_presets.find(
    (preset) => preset.id === runSizePreset,
  );

  return (
    <section className="workspace-section" aria-labelledby="build-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Build</p>
          <h2 id="build-title">Build and run a CM1 experiment</h2>
        </div>
      </div>

      <section className="builder-layout" aria-label="Scenario Builder">
        <form id="build-run-package-form" className="builder-panel" onSubmit={onDryRun}>
          <label className="field-label" htmlFor="scenario">
            Experiment
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
                <p className="eyebrow">Guided local CM1 experiment</p>
                <h2>{selectedScenario.display_name}</h2>
                <p>{selectedScenario.description}</p>
              </div>

              <section aria-labelledby="physical-question-title">
                <h3 id="physical-question-title">Physical Question</h3>
                <p>{selectedScenario.physical_question}</p>
              </section>

              <section className="experiment-summary" aria-labelledby="experiment-summary-title">
                <h3 id="experiment-summary-title">Experiment setup summary</h3>
                <dl className="compact-metrics">
                  <Metric label="Expected outcome" value={selectedScenario.expected_behavior} />
                  <Metric
                    label="Readiness"
                    value="Supported local package template from the scenario catalog"
                  />
                  <Metric
                    label="What changes"
                    value={selectedScenario.controls.map((control) => control.label).join(", ")}
                  />
                  <Metric
                    label="What stays controlled"
                    value="CM1 remains the source of truth; raw namelist details stay in technical review."
                  />
                </dl>
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
                      <small>
                        Selected:{" "}
                        {selectedControlOption(control, controls)?.label ??
                          String(controls[control.id] ?? control.default)}
                        .{" "}
                        {selectedControlOption(control, controls)?.description ??
                          "Supported scenario option; raw CM1 settings remain in technical review."}
                      </small>
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
              {selectedRunSize && (
                <p className="field-help">
                  {selectedRunSize.purpose}. Expected runtime: {selectedRunSize.expected_runtime}.
                  Confidence: {selectedRunSize.confidence}. Output: {selectedRunSize.output_notes}.
                </p>
              )}

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

            </>
          )}
        </form>

        <aside className="side-stack">
          <LocalRunWorkflowPanel
            dryRun={dryRun}
            runStatus={runStatus}
            error={runWorkflowError}
            ingestedResultId={ingestedResultId}
            showCreatePackageAction={scenarioControlsReady}
            canCreatePackage={validationMessages.length === 0}
            onLaunchRun={onLaunchRun}
            onRefreshRunStatus={onRefreshRunStatus}
            onIngestRun={onIngestRun}
            storageInventory={storageInventory}
            storageStatus={storageStatus}
            storageError={storageError}
            results={results}
            onLaunchStoredRun={onLaunchStoredRun}
            onIngestStoredRun={onIngestStoredRun}
            onOpenInResults={onOpenInResults}
            onInspectIngested={onInspectIngested}
            onOpenStoredResult={onOpenStoredResult}
            onExploreStoredResult={onExploreStoredResult}
            onOpenStorage={onOpenStorage}
            onRefreshStorage={onRefreshStorage}
          />
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
  focusedRunId,
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
  onManageLocalFiles,
  onCompareInspect,
  onStorageOpenResult,
  onStorageExploreResult,
  onStorageIngestRun,
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
  focusedRunId: string | null;
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
  onManageLocalFiles: (result: ResultCard) => void;
  onCompareInspect: (resultId: string) => void;
  onStorageOpenResult: (resultId: string) => void;
  onStorageExploreResult: (resultId: string) => void;
  onStorageIngestRun: (manifestPath: string) => void;
  onRefreshStorage: () => void;
  onPreviewDelete: (runId: string) => void;
  onConfirmDelete: (runId: string) => void;
}) {
  return (
    <section className="results-library" aria-labelledby="results-title">
      <div className="section-heading">
        <div>
          <h2 id="results-title">Experiment Notebook</h2>
          <p>Review saved cloud experiments, compare variants, and open results for explanation.</p>
        </div>
      </div>
      {resultsStatus !== "Results loaded" && resultsStatus !== "Loading results..." && (
        <p className="inline-status" role="status">
          {resultsStatus}
        </p>
      )}

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
          onManageLocalFiles={onManageLocalFiles}
          onCompare={() => onTabChange("compare")}
          onOpenResultInExplore={onCompareInspect}
        />
      )}

      {activeTab === "compare" && (
        <ComparisonWorkspace
          pair={comparisonPair}
          onInspect={onCompareInspect}
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
          focusedRunId={focusedRunId}
          deletePreview={deletePreview}
          deleteMessage={deleteMessage}
          onRefresh={onRefreshStorage}
          onPreviewDelete={onPreviewDelete}
          onConfirmDelete={onConfirmDelete}
          onOpenResult={onStorageOpenResult}
          onExploreResult={onStorageExploreResult}
          onIngestRun={onStorageIngestRun}
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
  onManageLocalFiles,
  onCompare,
  onOpenResultInExplore,
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
  onManageLocalFiles: (result: ResultCard) => void;
  onCompare: () => void;
  onOpenResultInExplore: (resultId: string) => void;
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
              <h3 id="notebook-title">Notebook entries</h3>
        </div>
        <button type="button" onClick={onRefreshResults}>
          Refresh results
        </button>
      </div>
      <div className="results-layout">
        <ExperimentNotebookList
          results={results}
          selectedResultId={selectedResultId}
          onSelect={onSelectResult}
          onOpenExplore={onOpenResultInExplore}
        />
        <ResultNotebookCard
          result={selectedResult}
          draft={draft}
          onDraftChange={onDraftChange}
          onSubmit={onSubmit}
          onSave={onSave}
          onInspect={onInspect}
          onManageLocalFiles={onManageLocalFiles}
          onCompare={onCompare}
        />
      </div>
    </section>
  );
}

function ExploreWorkspace({ selectedResult }: { selectedResult: ResultCard | undefined }) {
  return (
    <section className="workspace-section explore-workspace" aria-label="Explore this result">
      {!selectedResult && (
        <section className="status-panel">
          <p>Select an ingested result from Results to inspect or visualize it.</p>
        </section>
      )}

      {selectedResult && (
        <section className="explore-result-view">
          <ExploreResultSummary result={selectedResult} />
          <VisualizerSceneShell result={selectedResult} />
        </section>
      )}
    </section>
  );
}

function ExploreResultSummary({ result }: { result: ResultCard }) {
  return (
    <section className="explore-result-summary" aria-label="Selected Explore result">
      <div>
        <h3>{result.name}</h3>
        <p>
          {result.scenario_name ?? humanize(result.scenario_id)} ·{" "}
          {humanize(result.run_size_preset)}
          {result.completed_at ? ` · ${formatDate(result.completed_at)}` : ""}
        </p>
        <p>{resultStory(result)}</p>
      </div>
      <div className="badge-row">
        <OutcomeBadge result={result} />
        <StatusBadge label={rainOutcome(result.rain_present)} tone="neutral" />
        {result.saved ? <StatusBadge label="Saved" tone="good" /> : null}
      </div>
    </section>
  );
}

function ComparisonWorkspace({
  pair,
  onInspect,
  onSelectInNotebook,
}: {
  pair: { baseline: ResultCard | undefined; dryFailed: ResultCard | undefined };
  onInspect: (resultId: string) => void;
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
              onSelectInNotebook={onSelectInNotebook}
            />
            <ComparisonResultCard
              roleLabel="Dry Failed"
              result={pair.dryFailed}
              onInspect={onInspect}
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
  onSelectInNotebook,
}: {
  roleLabel: "Baseline" | "Dry Failed";
  result: ResultCard | undefined;
  onInspect: (resultId: string) => void;
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
  focusedRunId,
  deletePreview,
  deleteMessage,
  onRefresh,
  onPreviewDelete,
  onConfirmDelete,
  onOpenResult,
  onExploreResult,
  onIngestRun,
}: {
  inventory: StorageInventoryResponse | null;
  results: ResultCard[];
  status: string;
  error: string | null;
  focusedRunId: string | null;
  deletePreview: DeleteRunResponse | null;
  deleteMessage: string | null;
  onRefresh: () => void;
  onPreviewDelete: (runId: string) => void;
  onConfirmDelete: (runId: string) => void;
  onOpenResult: (resultId: string) => void;
  onExploreResult: (resultId: string) => void;
  onIngestRun: (manifestPath: string) => void;
}) {
  const displayedRuns =
    inventory && inventory.largest_runs.length > 0 ? inventory.largest_runs : inventory?.runs ?? [];

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
          <h2 id="storage-title">Runtime inventory and cleanup</h2>
          <p>
            Review generated packages, running CM1 jobs, completed output, ingested results, and
            cleanup candidates under the local runtime home.
          </p>
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
            Cleanup removes local generated package files, copied runtime files, CM1 output, logs,
            and any local metadata stored under the selected run directory. It does not touch the
            source repo, the runtime home itself, or the external CM1 install. No files have been
            deleted yet.
          </p>
          <dl className="metric-grid">
            <Metric label="Run ID" value={deletePreview.run_id} />
            <Metric label="Selected path" value={deletePreview.run_directory} />
            <Metric label="Estimated reclaimed" value={formatBytes(deletePreview.size_bytes)} />
            <Metric label="Preview status" value={deletePreview.message} />
          </dl>
          <button
            type="button"
            className="danger-button"
            onClick={() => onConfirmDelete(deletePreview.run_id)}
          >
            Confirm delete selected run
          </button>
        </section>
      )}

      <RuntimeRunsTable
        runs={displayedRuns}
        results={results}
        focusedRunId={focusedRunId}
        onPreviewDelete={onPreviewDelete}
        onOpenResult={onOpenResult}
        onExploreResult={onExploreResult}
        onIngestRun={onIngestRun}
      />
    </section>
  );
}

function RuntimeRunsTable({
  runs,
  results,
  focusedRunId,
  onPreviewDelete,
  onOpenResult,
  onExploreResult,
  onIngestRun,
}: {
  runs: RunStorageEntry[];
  results: ResultCard[];
  focusedRunId: string | null;
  onPreviewDelete: (runId: string) => void;
  onOpenResult: (resultId: string) => void;
  onExploreResult: (resultId: string) => void;
  onIngestRun: (manifestPath: string) => void;
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
            const displayName = storageDisplayName(run, associatedResult);
            const savedOrProtected =
              associatedResult?.saved || associatedResult?.protected || run.saved || run.protected;
            const deleteBlockedRun = {
              ...run,
              saved: Boolean(savedOrProtected),
              protected: Boolean(savedOrProtected),
            };
            const canIngest = canIngestStorageRun(run, associatedResult);
            return (
              <tr key={run.run_id} className={focusedRunId === run.run_id ? "selected-row" : ""}>
                <td>
                  <strong>{displayName}</strong>
                  <small>{storageScenarioSummary(run, associatedResult)}</small>
                  <small>Run ID: {run.run_id}</small>
                  <small>{run.path}</small>
                  {run.manifest_error && <small>{run.manifest_error}</small>}
                </td>
                <td>
                  {storageScenarioName(run, associatedResult)}
                  <small>{storagePresetAndControls(run, associatedResult)}</small>
                </td>
                <td>
                  <div className="badge-row">
                    {storageStateBadges(run, associatedResult).map((badge) => (
                      <StatusBadge key={badge.label} label={badge.label} tone={badge.tone} />
                    ))}
                  </div>
                  <small>{storageNextStep(run, associatedResult)}</small>
                </td>
                <td>{storageResultOutputSummary(run, associatedResult)}</td>
                <td>{formatBytes(run.size_bytes)}</td>
                <td>
                  <div className="button-row">
                    {associatedResult && (
                      <button
                        type="button"
                        onClick={() => onOpenResult(associatedResult.result_id)}
                      >
                        Open result
                      </button>
                    )}
                    {associatedResult && (
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => onExploreResult(associatedResult.result_id)}
                      >
                        Open in Explore
                      </button>
                    )}
                    {canIngest && run.manifest_path && (
                      <button
                        type="button"
                        onClick={() => onIngestRun(run.manifest_path!)}
                      >
                        Ingest completed output
                      </button>
                    )}
                    <button
                      type="button"
                      className="secondary-button"
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

function LocalRunWorkflowPanel({
  dryRun,
  runStatus,
  error,
  ingestedResultId,
  storageInventory,
  storageStatus,
  storageError,
  results,
  showCreatePackageAction,
  canCreatePackage,
  onLaunchRun,
  onRefreshRunStatus,
  onIngestRun,
  onLaunchStoredRun,
  onIngestStoredRun,
  onOpenInResults,
  onInspectIngested,
  onOpenStoredResult,
  onExploreStoredResult,
  onOpenStorage,
  onRefreshStorage,
}: {
  dryRun: DryRunResponse | null;
  runStatus: RunStatusResponse | null;
  error: string | null;
  ingestedResultId: string | null;
  storageInventory: StorageInventoryResponse | null;
  storageStatus: string;
  storageError: string | null;
  results: ResultCard[];
  showCreatePackageAction: boolean;
  canCreatePackage: boolean;
  onLaunchRun: () => void;
  onRefreshRunStatus: () => void;
  onIngestRun: () => void;
  onLaunchStoredRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenInResults: () => void;
  onInspectIngested: () => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onOpenStorage: (runId?: string | null) => void;
  onRefreshStorage: () => void;
}) {
  const stage = buildRunStage(dryRun, runStatus, ingestedResultId);
  const canIngest =
    runStatus?.lifecycle_state === "completed" &&
    runStatus.product_state === "completed_cm1_result" &&
    !ingestedResultId;
  const outputCount = runStatus
    ? Object.values(runStatus.output_summary).reduce((total, value) => total + value, 0)
    : 0;
  const generatedInputNames = dryRun ? generatedInputSummary(dryRun) : [];
  const currentRunId = dryRun ? runIdFromPackage(dryRun) : null;
  const showCreatePackageButton = showCreatePackageAction;
  const showLaunchButton = Boolean(dryRun && stage === "package_ready");
  const showRefreshButton = Boolean(dryRun && runStatus);
  const showIngestButton = Boolean(dryRun && canIngest);
  const showActionRow =
    showCreatePackageButton || showLaunchButton || showRefreshButton || showIngestButton;

  return (
    <section
      className="status-panel local-run-panel"
      aria-labelledby="local-run-title"
      data-testid="package-review-panel"
    >
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Run management</p>
          <h3 id="local-run-title">Local run launchpad</h3>
        </div>
        <StatusBadge label={buildStageLabel(stage)} tone={buildStageTone(stage)} />
      </div>

      <div className="run-state-card package-setup-card">
        <div className="panel-heading-row">
          <div>
            <p className="eyebrow">Package this setup</p>
            <h4>{dryRun ? "Latest generated package" : "Create a local run package"}</h4>
          </div>
          <strong className="next-action">{buildStageLabel(stage)}</strong>
        </div>

        <p className="state-note">
          Packages are repeatable local run directories. Create a new package for this setup, then
          use the package list below to run CM1, ingest completed output, or route old runs to
          cleanup.
        </p>

        {error && <p role="alert">{error}</p>}

        {showCreatePackageButton && (
          <div className="button-row">
            <button
              type="submit"
              form="build-run-package-form"
              data-testid="create-package-btn"
              className={dryRun ? "secondary-button" : undefined}
              disabled={!canCreatePackage}
            >
              {dryRun ? "Create another package" : "Create run package"}
            </button>
          </div>
        )}

        {dryRun ? (
          <>
            <dl className="compact-metrics">
              <Metric label="Run ID" value={runIdFromPackage(dryRun)} />
              <Metric label="Package path" value={dryRun.package_dir} />
              <Metric label="Manifest path" value={dryRun.manifest_path} />
              <Metric label="Expected output directory" value={dryRun.package_dir} />
              <Metric
                label="Generated inputs"
                value={
                  generatedInputNames.length > 0
                    ? generatedInputNames.join(", ")
                    : "No generated inputs reported"
                }
              />
              <Metric
                label="CM1 executable / settings"
                value={
                  runStatus?.command.length
                    ? runStatus.command.join(" ")
                    : "Checked before CM1 starts"
                }
              />
              <Metric
                label="Current lifecycle state"
                value={runStatus ? userFacingRunWorkflowStatus(runStatus) : "Package ready"}
              />
            </dl>
            <p className="state-note">
              A generated package is not a completed CM1 result. Launch, output detection, ingest,
              and saved result review are separate states.
            </p>
          </>
        ) : (
          <p>No package has been created from the current setup in this browser session.</p>
        )}

        {showActionRow && dryRun && (
          <div className="button-row">
            {showLaunchButton && (
              <button type="button" data-testid="launch-cm1-btn" onClick={onLaunchRun}>
                Run with local CM1
              </button>
            )}
            {showRefreshButton && (
              <button type="button" data-testid="refresh-status-btn" onClick={onRefreshRunStatus}>
                {stage === "running" || stage === "failed" ? "View status / logs" : "Refresh status"}
              </button>
            )}
            {showIngestButton && (
              <button
                type="button"
                data-testid="ingest-results-btn"
                onClick={onIngestRun}
                disabled={!canIngest}
              >
                Ingest completed output
              </button>
            )}
          </div>
        )}

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
          dryRun && (
            <p>
              Running uses the configured local CM1 install and preserves one local run at a time.
              If CM1 settings are missing, Cloud Chamber will stop before any CM1 process starts.
            </p>
          )
        )}

        {dryRun && (
          <details className="technical-details">
            <summary>Technical package details</summary>
            <dl className="compact-metrics">
              <Metric label="Scenario ID" value={dryRun.report.scenario_id} />
              <Metric label="Run-size preset" value={humanize(dryRun.report.run_size_preset)} />
              <Metric label="Cost / size" value={dryRun.report.estimated_cost_or_size} />
              <Metric
                label="CM1 launched"
                value={dryRun.report.cm1_was_launched ? "Yes" : "No"}
              />
              <Metric
                label="Product state"
                value={humanize(dryRun.report.provenance.product_state)}
              />
              <Metric
                label="Expected diagnostics"
                value={dryRun.report.expected_diagnostics.join(", ")}
              />
            </dl>
            <h5>Generated files</h5>
            <ul>
              {Object.values(dryRun.report.generated_files).map((path) => (
                <li key={path}>{path.split("/").at(-1)}</li>
              ))}
            </ul>
            <p>{dryRun.report.physical_question}</p>
          </details>
        )}

        {ingestedResultId && (
          <div className="post-ingest-actions" aria-label="Ingested result actions">
            <p>Result metadata created: {ingestedResultId}</p>
            <div className="button-row">
              <button type="button" onClick={onOpenInResults}>
                Open in Results
              </button>
              <button type="button" onClick={onInspectIngested}>
                Open in Explore
              </button>
            </div>
          </div>
        )}
      </div>

      <LocalPipelinePanel
        inventory={storageInventory}
        status={storageStatus}
        error={storageError}
        results={results}
        currentRunId={currentRunId}
        onLaunchStoredRun={onLaunchStoredRun}
        onIngestStoredRun={onIngestStoredRun}
        onOpenStoredResult={onOpenStoredResult}
        onExploreStoredResult={onExploreStoredResult}
        onOpenStorage={onOpenStorage}
        onRefreshStorage={onRefreshStorage}
      />

    </section>
  );
}

function LocalPipelinePanel({
  inventory,
  status,
  error,
  results,
  currentRunId,
  onLaunchStoredRun,
  onIngestStoredRun,
  onOpenStoredResult,
  onExploreStoredResult,
  onOpenStorage,
  onRefreshStorage,
}: {
  inventory: StorageInventoryResponse | null;
  status: string;
  error: string | null;
  results: ResultCard[];
  currentRunId: string | null;
  onLaunchStoredRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onOpenStorage: (runId?: string | null) => void;
  onRefreshStorage: () => void;
}) {
  const runs = selectPipelineRuns(inventory?.runs ?? [], currentRunId);

  return (
    <section className="pipeline-panel" aria-labelledby="pipeline-title">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Local run inventory</p>
          <h4 id="pipeline-title">Packages, runs, and results</h4>
        </div>
        <StatusBadge label={status} tone={error ? "warning" : "neutral"} />
      </div>
      <p className="state-note">
        See local run directories by state and move them forward when possible. Cleanup stays in
        Storage so saved results and running runs remain protected.
      </p>
      {error && <p role="alert">{error}</p>}
      <div className="button-row">
        <button type="button" className="secondary-button" onClick={onRefreshStorage}>
          Refresh runs
        </button>
        <button type="button" className="secondary-button" onClick={() => onOpenStorage()}>
          Open Storage cleanup
        </button>
      </div>

      {runs.length === 0 ? (
        <p>No local packages or run directories were found yet.</p>
      ) : (
        <div className="pipeline-run-list" aria-label="Local packages and runs">
          {runs.map((run) => (
            <PipelineRunCard
              key={run.run_id}
              run={run}
              result={resultForRun(results, run.run_id)}
              current={run.run_id === currentRunId}
              onLaunchStoredRun={onLaunchStoredRun}
              onIngestStoredRun={onIngestStoredRun}
              onOpenStoredResult={onOpenStoredResult}
              onExploreStoredResult={onExploreStoredResult}
              onOpenStorage={onOpenStorage}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function PipelineRunCard({
  run,
  result,
  current,
  onLaunchStoredRun,
  onIngestStoredRun,
  onOpenStoredResult,
  onExploreStoredResult,
  onOpenStorage,
}: {
  run: RunStorageEntry;
  result: ResultCard | undefined;
  current: boolean;
  onLaunchStoredRun: (manifestPath: string) => void;
  onIngestStoredRun: (manifestPath: string) => void;
  onOpenStoredResult: (resultId: string) => void;
  onExploreStoredResult: (resultId: string) => void;
  onOpenStorage: (runId?: string | null) => void;
}) {
  const displayName = result?.name ?? run.scenario_name ?? run.scenario_id ?? run.run_id;
  const canLaunch = Boolean(run.manifest_path && run.category === "dry_run_only");
  const canIngest = Boolean(run.manifest_path && run.category === "completed_with_output" && !result);
  const savedOrProtected = Boolean(result?.saved || result?.protected || run.saved || run.protected);
  const stateLabel = pipelineRunStateLabel(run, result);
  const showSavedStateBadge = stateLabel !== "Saved/protected";

  return (
    <article className={current ? "pipeline-run-card current" : "pipeline-run-card"}>
      <div className="panel-heading-row">
        <div>
          <h5>{displayName}</h5>
          <small>{run.run_id}</small>
        </div>
        {current && <StatusBadge label="Current package" tone="neutral" />}
      </div>
      <div className="badge-row">
        <StatusBadge label={stateLabel} tone={pipelineRunTone(run, result)} />
        {!result && <StatusBadge label="Not ingested" tone="neutral" />}
        {showSavedStateBadge && (
          <StatusBadge label={savedOrProtected ? "Saved/protected" : "Not saved"} tone="neutral" />
        )}
      </div>
      <p>
        {humanize(result?.scenario_id ?? run.scenario_id ?? "unknown scenario")} ·{" "}
        {humanize(result?.run_size_preset ?? run.run_size_preset ?? "preset unknown")}
      </p>
      <p className="state-note">
        {storageResultOutputSummary(run, result)} · {formatBytes(run.size_bytes)}
      </p>
      <p className="state-note">{pipelineRunNextStep(run, result)}</p>
      <div className="button-row">
        {canLaunch && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onLaunchStoredRun(run.manifest_path!)}
          >
            Run with local CM1
          </button>
        )}
        {canIngest && run.manifest_path && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onIngestStoredRun(run.manifest_path!)}
          >
            Ingest output
          </button>
        )}
        {result && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onOpenStoredResult(result.result_id)}
          >
            Open result
          </button>
        )}
        {result && (
          <button
            type="button"
            className="secondary-button"
            onClick={() => onExploreStoredResult(result.result_id)}
          >
            Open in Explore
          </button>
        )}
        <button
          type="button"
          className="secondary-button"
          onClick={() => onOpenStorage(run.run_id)}
        >
          Manage cleanup
        </button>
      </div>
    </article>
  );
}

function buildRunStage(
  dryRun: DryRunResponse | null,
  runStatus: RunStatusResponse | null,
  ingestedResultId: string | null,
): BuildRunStage {
  if (ingestedResultId) return "ingested";
  if (!dryRun) return "not_packaged";
  if (!runStatus) return "package_ready";
  if (runStatus.lifecycle_state === "queued" || runStatus.lifecycle_state === "running") {
    return "running";
  }
  if (runStatus.lifecycle_state === "completed") return "completed";
  if (runStatus.lifecycle_state === "failed" || runStatus.lifecycle_state === "canceled") {
    return "failed";
  }
  return "package_ready";
}

function buildStageLabel(stage: BuildRunStage): string {
  const labels: Record<BuildRunStage, string> = {
    not_packaged: "Not packaged yet",
    package_ready: "Package ready",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    ingested: "Ingested",
  };
  return labels[stage];
}

function buildStageTone(stage: BuildRunStage): "good" | "warning" | "neutral" {
  if (stage === "completed" || stage === "ingested") return "good";
  if (stage === "failed") return "warning";
  return "neutral";
}

function generatedInputSummary(dryRun: DryRunResponse): string[] {
  return Object.values(dryRun.report.generated_files)
    .map((path) => path.split("/").at(-1) ?? path)
    .filter((name) => name === "namelist.input" || name === "input_sounding");
}

function selectPipelineRuns(runs: RunStorageEntry[], currentRunId: string | null): RunStorageEntry[] {
  const sorted = [...runs].sort((left, right) => {
    if (currentRunId) {
      if (left.run_id === currentRunId) return -1;
      if (right.run_id === currentRunId) return 1;
    }
    const leftTime = Date.parse(left.updated_at ?? left.created_at ?? "");
    const rightTime = Date.parse(right.updated_at ?? right.created_at ?? "");
    return (Number.isFinite(rightTime) ? rightTime : 0) - (Number.isFinite(leftTime) ? leftTime : 0);
  });
  return sorted.slice(0, 6);
}

function pipelineRunStateLabel(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result) return "Ready to review";
  if (run.saved || run.protected) return "Saved/protected";
  const labels: Record<string, string> = {
    dry_run_only: "Ready to run",
    running: "Running",
    completed_with_output: "Ready to ingest",
    completed_no_output: "Completed with no output",
    failed: "Failed",
    canceled: "Canceled",
    missing_manifest: "Missing manifest",
    malformed_manifest: "Manifest problem",
    saved_or_protected: "Saved/protected",
    unknown: "Needs review",
  };
  return labels[run.category] ?? humanize(run.category);
}

function pipelineRunTone(
  run: RunStorageEntry,
  result: ResultCard | undefined,
): "good" | "warning" | "neutral" {
  if (result?.saved || result?.protected || result) return "good";
  if (run.category === "completed_with_output") return "good";
  if (
    run.category === "failed" ||
    run.category === "canceled" ||
    run.category === "completed_no_output" ||
    run.category === "missing_manifest" ||
    run.category === "malformed_manifest"
  ) {
    return "warning";
  }
  return "neutral";
}

function pipelineRunNextStep(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result?.saved || result?.protected || run.saved || run.protected) {
    return "Keeper result; normal cleanup is protected in Storage.";
  }
  if (result) return "Review in Results or Explore fields; cleanup remains available in Storage.";
  if (run.category === "dry_run_only") return "Ready to run after CM1 checks.";
  if (run.category === "running") return "CM1 is active or queued; refresh runs for status.";
  if (run.category === "completed_with_output") {
    return "CM1 output exists; ingest it to create a notebook result.";
  }
  if (run.category === "completed_no_output") {
    return "CM1 completed without usable output; inspect logs or clean up safely.";
  }
  if (run.category === "failed" || run.category === "canceled") {
    return "Run did not complete; inspect logs or clean up safely.";
  }
  if (run.category === "missing_manifest" || run.category === "malformed_manifest") {
    return "Run directory needs cleanup review before trusting it.";
  }
  return "Review in Storage for the safest next action.";
}

function selectedControlOption(
  control: ScenarioControl,
  controls: Record<string, string | number | boolean>,
): ControlOption | undefined {
  const value = String(controls[control.id] ?? control.default);
  return control.options.find((option) => option.value === value);
}

function ExperimentNotebookList({
  results,
  selectedResultId,
  onSelect,
  onOpenExplore,
}: {
  results: ResultCard[];
  selectedResultId: string | null;
  onSelect: (resultId: string) => void;
  onOpenExplore: (resultId: string) => void;
}) {
  if (results.length === 0) {
    return (
      <section className="notebook-list-panel empty-results" aria-label="Results list">
        <p className="eyebrow">Notebook empty</p>
        <h3>No ingested CM1 results yet.</h3>
        <p>
          Completed and ingested CM1 runs will appear here as experiment notebook entries.
        </p>
      </section>
    );
  }

  return (
    <section className="notebook-list-panel" aria-label="Results list">
      <p className="eyebrow">Experiment list</p>
      <div className="experiment-card-list">
        {results.map((result) => {
          const selected = result.result_id === selectedResultId;
          return (
            <article
              key={result.result_id}
              className={`experiment-card${selected ? " selected-experiment-card" : ""}`}
              aria-label={`${result.name} experiment`}
            >
              <div className="experiment-card-main">
                <button
                  type="button"
                  className="link-button"
                  onClick={() => onSelect(result.result_id)}
                  aria-pressed={selected}
                >
                  {result.name}
                </button>
                <p className="experiment-subtitle">
                  {result.scenario_name ?? humanize(result.scenario_id)} ·{" "}
                  {humanize(result.run_size_preset)} · {formatDate(result.completed_at ?? result.created_at)}
                </p>
                <div className="badge-row">
                  <OutcomeBadge result={result} />
                  <StatusBadge
                    label={result.saved || result.protected ? "Saved" : "Unsaved"}
                    tone={result.saved || result.protected ? "good" : "neutral"}
                  />
                </div>
                <p className="result-story">{resultStory(result)}</p>
              </div>
              <div className="experiment-card-actions">
                <button type="button" onClick={() => onOpenExplore(result.result_id)}>
                  Open in Explore
                </button>
              </div>
              <details className="technical-details">
                <summary>Technical details</summary>
                <dl className="metric-grid">
                  <Metric label="Run ID" value={result.run_id} />
                  <Metric label="Scenario ID" value={result.scenario_id} />
                  <Metric label="State" value={userFacingStatus(result)} />
                  <Metric label="Output" value={outputSummary(result.output_file_summary)} />
                </dl>
              </details>
            </article>
          );
        })}
      </div>
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
  onManageLocalFiles,
  onCompare,
}: {
  result: ResultCard | undefined;
  draft: { name: string; tags: string; notes: string };
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSave: () => void;
  onInspect: () => void;
  onManageLocalFiles: (result: ResultCard) => void;
  onCompare: () => void;
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
          <p className="eyebrow">Notebook entry</p>
          <h3>{result.name}</h3>
          <p>
            {result.scenario_name ?? humanize(result.scenario_id)} ·{" "}
            {humanize(result.run_size_preset)}
          </p>
        </div>
        <StatusBadge
          label={result.saved || result.protected ? "Saved" : "Unsaved"}
          tone={result.saved || result.protected ? "good" : "neutral"}
        />
      </div>

      <div className="badge-row">
        <OutcomeBadge result={result} />
        <StatusBadge label={rainOutcome(result.rain_present)} tone="neutral" />
      </div>

      <p className="result-story">{resultStory(result)}</p>

      {(isValidatedQuickLookBaseline(result) || result.caveats.length > 0) && (
        <p className="secondary-result-note">
          {[
            isValidatedQuickLookBaseline(result) ? "Validated quick-look baseline" : null,
            result.caveats.length > 0 ? caveatLabel(result) : null,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      )}

      <dl className="metric-grid key-result-values">
        <Metric label="Cloud" value={cloudOutcome(result)} />
        <Metric label="Rain" value={rainOutcome(result.rain_present)} />
        <Metric label="First cloud time" value={formatSeconds(result.first_cloud_time_seconds)} />
        <Metric label="Max qc" value={formatScientific(result.max_qc_kg_kg, "kg/kg")} />
        <Metric label="Max w" value={formatNumber(result.max_w_m_s, "m/s")} />
        <Metric label="Min w" value={formatNumber(result.min_w_m_s, "m/s")} />
      </dl>

      <details className="technical-details">
        <summary>Technical details</summary>
        <dl className="metric-grid">
          <Metric label="Run ID" value={result.run_id} />
          <Metric label="Scenario ID" value={result.scenario_id} />
          <Metric label="Lifecycle" value={result.source_lifecycle_state} />
          <Metric label="Product state" value={result.source_product_state} />
          <Metric label="Result state" value={result.status} />
          <Metric label="Source model" value={result.source_model} />
          <Metric label="Output" value={outputSummary(result.output_file_summary)} />
          <Metric
            label="Raw diagnostics"
            value={result.diagnostics_summary ?? "Diagnostics unavailable"}
          />
        </dl>

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
        </section>

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
          <button type="button" onClick={onInspect}>
            Open in Explore
          </button>
          <button type="button" className="secondary-button" onClick={onCompare}>
            Compare
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => onManageLocalFiles(result)}
          >
            Manage local files
          </button>
          <button type="submit" className="secondary-button">
            Update notebook
          </button>
          <button type="button" className="secondary-button" onClick={onSave}>
            Save result
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
  const [pointCloud, setPointCloud] = useState<PointCloudResponse | null>(null);
  const [processMode, setProcessMode] = useState<ProcessMode>("thermal_fate");
  const [projectionMode, setProjectionMode] = useState<ProjectionMode>("oblique");
  const [showSlicePlanes, setShowSlicePlanes] = useState(true);
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
  const [sliceLoading, setSliceLoading] = useState(false);
  const [sliceError, setSliceError] = useState<string | null>(null);
  const [fieldLoadAttempt, setFieldLoadAttempt] = useState(0);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegionRequest | null>(null);
  const [regionDiagnostics, setRegionDiagnostics] =
    useState<SelectedRegionDiagnosticsResponse | null>(null);
  const [regionStatus, setRegionStatus] = useState("Click a slice cell to inspect that point.");
  const [regionError, setRegionError] = useState<string | null>(null);
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
    setPointCloud(null);
    setProcessMode("thermal_fate");
    setProjectionMode("oblique");
    setShowSlicePlanes(true);
    setSliceFieldName("qc");
    setActiveSlicePlane("horizontal");
    setSliceOrientation("vertical_x");
    setHorizontalSliceLevel(0);
    setVerticalSliceIndex(0);
    setSceneHorizontalSlice(null);
    setSceneVerticalSlice(null);
    setSliceLoading(false);
    setSliceError(null);
    setSelectedRegion(null);
    setRegionDiagnostics(null);
    setRegionError(null);
    setRegionStatus("Click a slice cell to inspect that point.");
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
        const cloudContextField =
          payload.available_fields.find((field) => field.raw_field_name === "qc") ??
          firstPreferred;
        const initialDefaults = defaultsForField(defaults, firstPreferred?.raw_field_name);
        const initialTimeIndex = defaultTimeIndex(firstPreferred, result, initialDefaults);
        setSelectedFieldName(cloudContextField?.raw_field_name ?? "");
        setSliceFieldName(firstPreferred?.raw_field_name ?? "");
        setTimeIndex(initialTimeIndex);
        setHorizontalSliceLevel(defaultHorizontalLevel(firstPreferred, initialDefaults));
        setVerticalSliceIndex(defaultVerticalIndex(firstPreferred, "vertical_x", initialDefaults));
        setSceneStatus(
          payload.available_fields.length > 0 ? "Cloud view ready" : "No fields available",
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
  const activeSlice = activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice;
  const activeSliceLabel = slicePlainLabel(activeSlice, activeSlicePlane, activeSliceIndex);
  const activeSliceAxisSummary = sliceAxisSummary(activeSlice, activeSlicePlane);
  const selectedSliceValue = selectedSliceCellValue(activeSlice, selectedRegion);
  const selectedContextPointStyle = selectedRegionContextPointStyle(
    selectedRegion,
    { x: sliceXSize, y: sliceYSize, z: sliceVerticalSize },
    pointCloud,
    projectionMode,
  );
  const timePresets = [
    result.time_of_max_qc_seconds !== null && result.time_of_max_qc_seconds !== undefined
      ? { label: "Max cloud water", seconds: result.time_of_max_qc_seconds }
      : null,
    result.first_cloud_time_seconds !== null
      ? { label: "First cloud", seconds: result.first_cloud_time_seconds }
      : null,
    result.time_of_max_w_seconds !== null && result.time_of_max_w_seconds !== undefined
      ? { label: "Max updraft", seconds: result.time_of_max_w_seconds }
      : null,
    result.first_rain_time_seconds !== null && result.first_rain_time_seconds !== undefined
      ? { label: "Rain onset", seconds: result.first_rain_time_seconds }
      : null,
  ].filter((preset): preset is { label: string; seconds: number } => preset !== null);

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
            const fieldDefaults =
              defaultsForField(defaults, sliceFieldName) ??
              defaultsForField(defaults, selectedField.raw_field_name);
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
  }, [
    maxPoints,
    result.result_id,
    selectedField,
    sliceFieldName,
    sliceOrientation,
    threshold,
    timeIndex,
  ]);

  useEffect(() => {
    if (!sliceField) {
      setSceneHorizontalSlice(null);
      setSceneVerticalSlice(null);
      setSliceLoading(false);
      return;
    }
    let active = true;
    setSliceLoading(true);
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
        setSliceLoading(false);
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setSceneHorizontalSlice(null);
        setSceneVerticalSlice(null);
        setSliceLoading(false);
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
    if (!selectedRegion) {
      setRegionDiagnostics(null);
      setRegionError(null);
      setRegionStatus("Click a slice cell to inspect that point.");
      return;
    }
    let active = true;
    setRegionDiagnostics(null);
    setRegionError(null);
    setRegionStatus("Loading selected-point diagnostics...");
    fetchSelectedRegionDiagnostics(result.result_id, selectedRegion)
      .then((payload) => {
        if (!active) return;
        setRegionDiagnostics(payload);
        setRegionStatus("Selected-point diagnostics loaded");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setRegionDiagnostics(null);
        setRegionError(
          caught instanceof Error ? caught.message : "Unable to inspect the selected point.",
        );
        setRegionStatus("Selected-point request failed");
      });
    return () => {
      active = false;
    };
  }, [result.result_id, selectedRegion]);

  function selectPointFromSlice(slice: SliceResponse, rowIndex: number, columnIndex: number) {
    setSelectedRegion(selectionFromSlice(slice, rowIndex, columnIndex, "point"));
  }

  function resetView() {
    setZoom(100);
    setProjectionMode("oblique");
  }

  return (
    <section className="visualizer-shell" aria-labelledby="visualizer-shell-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Cloud view</p>
          <h2 id="visualizer-shell-title">What happened in this result?</h2>
        </div>
        <p className="state-chip">{sceneStatus}</p>
      </div>

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

      {catalog && sliceField && selectedField && (
        <section className="explore-shared-controls" aria-label="Shared Explore controls">
          <div className="explore-control-group explore-control-group-time">
            <label htmlFor="explore-time">
              Time
              <select
                id="explore-time"
                value={Math.min(timeIndex, timeMax)}
                onChange={(event) => setTimeIndex(Number(event.target.value))}
              >
                {timeOptions.map((value, index) => (
                  <option key={`${value}-${index}`} value={index}>
                    {formatTimeValue(value)}
                  </option>
                ))}
              </select>
            </label>

            <div className="time-preset-buttons" aria-label="Time presets">
              {timePresets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => setTimeIndex(closestTimeIndex(timeOptions, preset.seconds))}
                >
                  {preset.label}
                </button>
              ))}
              <button type="button" onClick={() => setTimeIndex(timeMax)}>Last frame</button>
            </div>
          </div>

          <div className="explore-control-group explore-control-group-slice">
            <label htmlFor="explore-slice-field">
              Slice field
              <select
                id="explore-slice-field"
                value={sliceFieldName}
                onChange={(event) => {
                  const nextField = catalog.available_fields.find(
                    (field) => field.raw_field_name === event.target.value,
                  );
                  setSliceFieldName(event.target.value);
                  const nextDefaults = defaultsForField(viewDefaults, event.target.value);
                  setHorizontalSliceLevel(defaultHorizontalLevel(nextField, nextDefaults));
                  setVerticalSliceIndex(defaultVerticalIndex(nextField, sliceOrientation, nextDefaults));
                  setSelectedRegion(null);
                }}
              >
                {catalog.available_fields.map((field) => (
                  <option key={field.raw_field_name} value={field.raw_field_name}>
                    {field.raw_field_name} - {field.display_name}
                  </option>
                ))}
              </select>
            </label>

            <fieldset className="view-mode-control">
              <legend>Slice orientation</legend>
              <div className="segmented-buttons">
                <button
                  type="button"
                  className={activeSlicePlane === "horizontal" ? "active-control" : ""}
                  onClick={() => {
                    setActiveSlicePlane("horizontal");
                    setProjectionMode("top_down");
                    setSelectedRegion(null);
                  }}
                >
                  Horizontal layer
                </button>
                <button
                  type="button"
                  className={activeSlicePlane === "vertical_x" ? "active-control" : ""}
                  onClick={() => {
                    setActiveSlicePlane("vertical_x");
                    setSliceOrientation("vertical_x");
                    setProjectionMode("side_xz");
                    setSelectedRegion(null);
                  }}
                >
                  Vertical x-z slice
                </button>
                <button
                  type="button"
                  className={activeSlicePlane === "vertical_y" ? "active-control" : ""}
                  onClick={() => {
                    setActiveSlicePlane("vertical_y");
                    setSliceOrientation("vertical_y");
                    setProjectionMode("side_yz");
                    setSelectedRegion(null);
                  }}
                >
                  Vertical y-z slice
                </button>
              </div>
            </fieldset>
          </div>

          <div className="explore-control-group explore-control-group-position">
            <label htmlFor="explore-slice-position">
              Slice position
              <input
                id="explore-slice-position"
                aria-label="Slice position"
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
                  setSelectedRegion(null);
                }}
              />
              <span className="slice-position-label">
                {activeSlicePositionLabel || `index ${activeSliceIndex}`}{" "}
                <small>index {activeSliceIndex}</small>
              </span>
            </label>

            <div className="button-row slice-move-buttons">
              <button
                type="button"
                onClick={() => {
                  const nextIndex = Math.max(0, activeSliceIndex - 1);
                  if (activeSlicePlane === "horizontal") {
                    setHorizontalSliceLevel(nextIndex);
                  } else {
                    setVerticalSliceIndex(nextIndex);
                  }
                  setSelectedRegion(null);
                }}
              >
                {activeSlicePlane === "horizontal" ? "Move down" : "Move back"}
              </button>
              <button
                type="button"
                onClick={() => {
                  const nextIndex = Math.min(Math.max(0, activeSliceMax - 1), activeSliceIndex + 1);
                  if (activeSlicePlane === "horizontal") {
                    setHorizontalSliceLevel(nextIndex);
                  } else {
                    setVerticalSliceIndex(nextIndex);
                  }
                  setSelectedRegion(null);
                }}
              >
                {activeSlicePlane === "horizontal" ? "Move up" : "Move forward"}
              </button>
            </div>
          </div>

          <div className="explore-control-group explore-control-group-view">
            <fieldset className="view-mode-control">
              <legend>View</legend>
              <div className="segmented-buttons">
                <button
                  type="button"
                  className={projectionMode === "oblique" ? "active-control" : ""}
                  onClick={() => setProjectionMode("oblique")}
                >
                  Oblique
                </button>
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
                  Top-down
                </button>
              </div>
            </fieldset>

            <label htmlFor="scene-zoom">
              Zoom
              <input
                id="scene-zoom"
                aria-label="Zoom"
                type="range"
                min={70}
                max={160}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
              />
              <span>{zoom}%</span>
            </label>

            <label className="checkbox-label" htmlFor="show-slice-plane">
              <input
                id="show-slice-plane"
                type="checkbox"
                checked={showSlicePlanes}
                onChange={(event) => setShowSlicePlanes(event.target.checked)}
              />
              Show slice plane
            </label>

            <button type="button" onClick={resetView}>
              Reset view
            </button>
          </div>
        </section>
      )}

      {catalog && sliceField && (
        <div className="linked-view-strip" aria-label="Linked Explore view summary">
          <span>
            <strong>3-D context:</strong>{" "}
            {qcField ? "qc — Cloud water" : "cloud-water context unavailable"}
          </span>
          <span>
            <strong>Current slice plane:</strong> {activeSliceLabel}
          </span>
          <span>
            <strong>Slice axes:</strong> {activeSliceAxisSummary}
          </span>
          <span>
            <strong>2-D slice field:</strong> {sliceField.raw_field_name} —{" "}
            {sliceField.display_name}
          </span>
        </div>
      )}

      <div className="visualizer-workbench" aria-label="Scientific visualization workbench">
        <div className="visualizer-stage" aria-label="Fixed visualization viewport region">
          <div className="scene-container" aria-label="3-D scene container">
            <div className="viewport-frame" style={plotFrameStyle(pointCloud, projectionMode)}>
              <div className="scene-horizon" />
              <div className={`scene-grid scene-grid-${projectionMode}`} />
              <div className="plot-axis-labels" aria-label="Domain axes">
                <span className="axis-label axis-label-x">
                  {projectionMode === "side_yz" ? "y" : "x"}
                </span>
                <span className="axis-label axis-label-y">
                  {projectionMode === "side_xz"
                    ? "viewing along y"
                    : projectionMode === "top_down"
                      ? "y"
                      : "depth y"}
                </span>
                <span className="axis-label axis-label-z">
                  {projectionMode === "top_down" ? "top-down x-y" : "height z"}
                </span>
                <span className="ground-label">domain floor</span>
              </div>
              <div
                className="plot-data-layer"
                aria-label="Zoomable visualizer data layer"
                style={{ transform: `scale(${zoom / 100})` }}
              >
                {showSlicePlanes && (
                  <SliceGuidePlane
                    title={activeSliceLabel}
                    slice={
                      activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice
                    }
                    pointCloud={pointCloud}
                    projectionMode={projectionMode}
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
                {selectedContextPointStyle && (
                  <span
                    className="selected-context-point"
                    aria-label="Selected point in context view"
                    style={selectedContextPointStyle}
                  />
                )}
              </div>
              {showSlicePlanes && (
                <SliceGuideLabel
                  title={activeSliceLabel}
                  slice={activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice}
                  pointCloud={pointCloud}
                  projectionMode={projectionMode}
                />
              )}
              <ScaleMarkers pointCloud={pointCloud} projectionMode={projectionMode} />
              <div className="scene-context-label">
                <strong>{projectionLabel(projectionMode)}</strong>
                <span>{selectedTimeLabel}</span>
                <span>Cloud-water threshold {formatScientific(threshold, "kg/kg")}</span>
              </div>
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
                      ? "No cloud water formed in this result; vertical velocity is available."
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
        </div>

        <aside className="visualizer-details-panel" aria-label="Visualization details">
          <ResultExplanationPanel result={result} isNoCloudWithUpdraft={isNoCloudWithUpdraft} />

          <details className="technical-details">
            <summary>Evidence details</summary>
            <ProcessModeControl processMode={processMode} onProcessModeChange={setProcessMode} />
            <ProcessOverlayPanel
              result={result}
              catalog={catalog}
              selectedField={sliceField}
              processMode={processMode}
              slice={activeSlicePlane === "horizontal" ? sceneHorizontalSlice : sceneVerticalSlice}
            />
          </details>

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
            <fieldset className="technical-rendering-controls">
              <legend>Rendering controls</legend>
              <label htmlFor="cloud-threshold">
                Cloud-water threshold
                <input
                  id="cloud-threshold"
                  type="number"
                  min={0}
                  step="0.000001"
                  value={threshold}
                  onChange={(event) => setThreshold(Number(event.target.value))}
                  disabled={!qcField}
                />
              </label>
              <label htmlFor="cloud-opacity">
                Cloud opacity
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
            </fieldset>
            <dl className="metric-grid">
              <Metric label="Run ID" value={result.run_id} />
              <Metric label="View control" value="2.5-D fixed projection; data-only zoom" />
              <Metric label="Zoom" value={`${zoom}%`} />
              <Metric label="Opacity" value={String(opacity)} />
              <Metric label="Point size" value={`${pointSize}px`} />
              <Metric label="Slice plane visible" value={showSlicePlanes ? "Yes" : "No"} />
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

      {catalog && sliceField && (
        <section className="unified-slice-inspector" aria-labelledby="unified-slice-title">
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Slice inspector</p>
              <h2 id="unified-slice-title">Inspect the current slice</h2>
              <p>
                {activeSliceLabel} · {sliceField.raw_field_name} ·{" "}
                {selectedTimeLabel}
              </p>
            </div>
            <p className="state-chip">
              {sliceError
                ? "Slice unavailable"
                : sliceLoading || !activeSlice
                  ? "Loading slice"
                  : "Slice synced"}
            </p>
          </div>

          {sliceError && <p role="alert">{sliceError}</p>}

          <SlicePanel
            title={activeSliceLabel}
            slice={activeSlice}
            pointCloud={pointCloud}
            selectedRegion={selectedRegion}
            onSelectRegion={selectPointFromSlice}
          />

          <SelectedRegionInspector
            selectedRegion={selectedRegion}
            slice={activeSlice}
            selectedValue={selectedSliceValue}
            diagnostics={regionDiagnostics}
            status={regionStatus}
            error={regionError}
          />
        </section>
      )}
    </section>
  );
}

function ResultExplanationPanel({
  result,
  isNoCloudWithUpdraft,
}: {
  result: ResultCard;
  isNoCloudWithUpdraft: boolean;
}) {
  return (
    <section className="selected-region-inspector" aria-label="Result-level explanation panel">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Explanation</p>
          <h3>Result explanation</h3>
        </div>
        <StatusBadge
          label={
            cloudOutcome(result) === "Cloud formed"
              ? "Cloud formed in this result"
              : "No cloud formed in this result"
          }
          tone={cloudOutcome(result) === "Cloud formed" ? "good" : "warning"}
        />
      </div>
      <p>{resultStory(result)}</p>
      <section aria-label="Evidence">
        <h4>Evidence</h4>
        <dl className="metric-grid">
          <Metric label="First cloud time" value={formatSeconds(result.first_cloud_time_seconds)} />
          <Metric label="Max qc" value={formatScientific(result.max_qc_kg_kg, "kg/kg")} />
          <Metric label="Max w" value={formatNumber(result.max_w_m_s, "m/s")} />
          <Metric label="Rain" value={rainOutcome(result.rain_present)} />
        </dl>
      </section>
      {isNoCloudWithUpdraft && (
        <p>For this no-cloud result, use vertical velocity (w) slices to inspect the thermals.</p>
      )}
      <details>
        <summary>Technical details</summary>
        <ul className="compact-list">
          <li>Thermal Fate is the internal explanation model.</li>
          <li>Evidence comes from ingested CM1 diagnostics and visualization-ready fields.</li>
          <li>No raw NetCDF parsing in the browser.</li>
          {result.caveats.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}

function SliceGuidePlane({
  title,
  slice,
  pointCloud,
  projectionMode,
}: {
  title: string;
  slice: SliceResponse | null;
  pointCloud: PointCloudResponse | null;
  projectionMode: ProjectionMode;
}) {
  if (!slice) return null;
  const marker = sliceGuidePlaneStyle(slice, pointCloud, projectionMode);
  return (
    <div
      className={`slice-guide-plane slice-guide-plane-${slice.selection.orientation}`}
      aria-label={`${title} full-domain slice plane`}
      role="note"
      style={marker}
    />
  );
}

function SliceGuideLabel({
  title,
  slice,
  pointCloud,
  projectionMode,
}: {
  title: string;
  slice: SliceResponse | null;
  pointCloud: PointCloudResponse | null;
  projectionMode: ProjectionMode;
}) {
  if (!slice) return null;
  return (
    <p className="slice-guide-label" style={sliceGuideLabelStyle(slice, pointCloud, projectionMode)}>
      {title}
    </p>
  );
}

function sliceGuidePlaneStyle(
  slice: SliceResponse,
  pointCloud: PointCloudResponse | null,
  projectionMode: ProjectionMode,
): CSSProperties & Record<string, string> {
  const fixed = selectedSliceNormalizedCoordinate(slice, pointCloud);
  const frame = plotFrame(pointCloud, projectionMode);

  if (slice.selection.orientation === "horizontal") {
    const projected = projectPoint(0, 0, fixed, projectionMode, pointCloud);
    const planeDepth =
      projectionMode === "top_down"
        ? frame.height
        : projectionMode === "oblique"
          ? Math.max(16, frame.height * 0.52)
          : Math.max(2.2, frame.height * 0.045);
    const planeBottom =
      projectionMode === "top_down"
        ? frame.bottom
        : projectionMode === "oblique"
          ? projected.bottom - planeDepth * 0.18
          : projected.bottom - planeDepth / 2;
    return {
      "--slice-guide-left": `${frame.left}%`,
      "--slice-guide-bottom": `${planeBottom}%`,
      "--slice-guide-width": `${frame.width}%`,
      "--slice-guide-height": `${planeDepth}%`,
      "--slice-guide-transform":
        projectionMode === "oblique" ? "perspective(760px) rotateX(64deg)" : "none",
    };
  }

  const useYCoordinate = slice.selection.orientation === "vertical_x";
  if (
    (projectionMode === "side_xz" && useYCoordinate) ||
    (projectionMode === "side_yz" && !useYCoordinate)
  ) {
    return {
      "--slice-guide-left": `${frame.left}%`,
      "--slice-guide-bottom": `${frame.bottom}%`,
      "--slice-guide-width": `${frame.width}%`,
      "--slice-guide-height": `${frame.height}%`,
      "--slice-guide-transform": "none",
    };
  }

  if (projectionMode === "top_down") {
    const projected = projectPoint(
      useYCoordinate ? 0 : fixed,
      useYCoordinate ? fixed : 0,
      0,
      projectionMode,
      pointCloud,
    );
    return {
      "--slice-guide-left": `${useYCoordinate ? frame.left : projected.left - frame.width * 0.012}%`,
      "--slice-guide-bottom": `${useYCoordinate ? projected.bottom - frame.height * 0.012 : frame.bottom}%`,
      "--slice-guide-width": `${useYCoordinate ? frame.width : Math.max(1.4, frame.width * 0.024)}%`,
      "--slice-guide-height": `${useYCoordinate ? Math.max(1.4, frame.height * 0.024) : frame.height}%`,
      "--slice-guide-transform": "none",
    };
  }

  const projected = projectPoint(useYCoordinate ? 0 : fixed, useYCoordinate ? fixed : 0, 0, projectionMode, pointCloud);
  return {
    "--slice-guide-left": `${
      useYCoordinate ? projected.left : Math.max(frame.left, projected.left - frame.width * 0.12)
    }%`,
    "--slice-guide-bottom": `${frame.bottom}%`,
    "--slice-guide-width": `${useYCoordinate ? frame.width * 0.72 : frame.width * 0.28}%`,
    "--slice-guide-height": `${frame.height}%`,
    "--slice-guide-transform": useYCoordinate ? "skewX(-14deg)" : "skewX(16deg)",
  };
}

function sliceGuideLabelStyle(
  slice: SliceResponse,
  pointCloud: PointCloudResponse | null,
  projectionMode: ProjectionMode,
): CSSProperties {
  const fixed = selectedSliceNormalizedCoordinate(slice, pointCloud);
  const frame = plotFrame(pointCloud, projectionMode);
  const projected =
    slice.selection.orientation === "horizontal"
      ? projectPoint(0.06, 0.08, fixed, projectionMode, pointCloud)
      : slice.selection.orientation === "vertical_x"
        ? projectPoint(0.04, fixed, 0.72, projectionMode, pointCloud)
        : projectPoint(fixed, 0.04, 0.72, projectionMode, pointCloud);
  return {
    left: `${clamp(projected.left, frame.left + 1, frame.left + frame.width - 20)}%`,
    bottom: `${clamp(projected.bottom + 1.6, frame.bottom + 1, frame.bottom + frame.height - 4)}%`,
  };
}

function selectedRegionContextPointStyle(
  selectedRegion: SelectedRegionRequest | null,
  sizes: { x: number; y: number; z: number },
  pointCloud: PointCloudResponse | null,
  projectionMode: ProjectionMode,
): CSSProperties | null {
  if (
    !selectedRegion ||
    selectedRegion.xIndex === undefined ||
    selectedRegion.yIndex === undefined ||
    selectedRegion.zIndex === undefined
  ) {
    return null;
  }
  const x = normalizeIndex(selectedRegion.xIndex, sizes.x);
  const y = normalizeIndex(selectedRegion.yIndex, sizes.y);
  const z = normalizeIndex(selectedRegion.zIndex, sizes.z);
  const point = projectPoint(x, y, z, projectionMode, pointCloud);
  return {
    left: `${point.left}%`,
    bottom: `${point.bottom}%`,
  };
}

function normalizeIndex(index: number, size: number): number {
  if (!Number.isFinite(index) || size <= 1) return 0.5;
  return clamp((index + 0.5) / size, 0, 1);
}

function selectedSliceNormalizedCoordinate(
  slice: SliceResponse,
  pointCloud: PointCloudResponse | null,
): number {
  const coordinate = slice.selection.selected_coordinate_value ?? slice.selection.level_coordinate_value;
  const numericCoordinate = typeof coordinate === "number" ? coordinate : Number(coordinate);
  if (!Number.isFinite(numericCoordinate)) return 0.5;
  if (slice.selection.orientation === "horizontal") {
    return normalizeWithExtent(numericCoordinate, pointCloud?.coordinate_extents.zh);
  }
  if (slice.selection.orientation === "vertical_x") {
    return normalizeWithExtent(numericCoordinate, pointCloud?.coordinate_extents.yh);
  }
  return normalizeWithExtent(numericCoordinate, pointCloud?.coordinate_extents.xh);
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
          {heightTicks(pointCloud).map((tick) => (
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

function heightTicks(pointCloud: PointCloudResponse | null): Array<{ position: number; label: string }> {
  const extent = pointCloud?.coordinate_extents.zh;
  if (!extent) return [];
  const units = extent?.units ? ` ${extent.units}` : "";
  const midpoint = (extent.min + extent.max) / 2;
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

function slicePlainLabel(
  slice: SliceResponse | null,
  activeSlicePlane: SceneSlicePlane,
  fallbackIndex: number,
): string {
  if (!slice) {
    const fallbackLabels: Record<SceneSlicePlane, string> = {
      horizontal: `Horizontal layer at z index ${fallbackIndex}`,
      vertical_x: `Vertical x-z slice at y index ${fallbackIndex}`,
      vertical_y: `Vertical y-z slice at x index ${fallbackIndex}`,
    };
    return fallbackLabels[activeSlicePlane];
  }
  const coordinate = slice.selection.selected_coordinate_value ?? slice.selection.level_coordinate_value;
  const units =
    slice.selection.level_units ?? slice.coordinate_units[slice.selection.selected_dimension];
  const coordinateText = coordinateTextWithUnits(coordinate, units, slice.selection.selected_index);
  if (slice.selection.orientation === "horizontal") {
    return `Horizontal layer at z = ${coordinateText}`;
  }
  if (slice.selection.orientation === "vertical_x") {
    return `Vertical x-z slice at y = ${coordinateText}`;
  }
  return `Vertical y-z slice at x = ${coordinateText}`;
}

function sliceAxisSummary(slice: SliceResponse | null, activeSlicePlane: SceneSlicePlane): string {
  const fixed = slice ? slicePlainLabel(slice, activeSlicePlane, slice.selection.selected_index) : "";
  if (activeSlicePlane === "horizontal") {
    return `x-axis = x; y-axis = y${fixed ? `; ${fixed}` : ""}`;
  }
  if (activeSlicePlane === "vertical_x") {
    return `x-axis = x; y-axis = height z${fixed ? `; ${fixed}` : ""}`;
  }
  return `x-axis = y; y-axis = height z${fixed ? `; ${fixed}` : ""}`;
}

function coordinateTextWithUnits(
  coordinate: number | string | null | undefined,
  units: string | null | undefined,
  fallbackIndex: number,
): string {
  if (coordinate === null || coordinate === undefined) return `index ${fallbackIndex}`;
  const numericCoordinate = typeof coordinate === "number" ? coordinate : Number(coordinate);
  const value = Number.isFinite(numericCoordinate)
    ? formatCompactNumber(numericCoordinate)
    : String(coordinate);
  return `${value}${units ? ` ${units}` : ""}`;
}

function selectedSliceCellValue(
  slice: SliceResponse | null,
  selectedRegion: SelectedRegionRequest | null,
): number | null {
  if (!slice || !selectedRegion) return null;
  for (let rowIndex = 0; rowIndex < slice.values.length; rowIndex += 1) {
    for (let columnIndex = 0; columnIndex < (slice.values[rowIndex]?.length ?? 0); columnIndex += 1) {
      if (isSelectedSliceCell(slice, selectedRegion, rowIndex, columnIndex)) {
        return slice.values[rowIndex]?.[columnIndex] ?? null;
      }
    }
  }
  return null;
}

function SlicePanel({
  title,
  slice,
  pointCloud,
  selectedRegion,
  onSelectRegion,
}: {
  title: string;
  slice: SliceResponse | null;
  pointCloud?: PointCloudResponse | null;
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

  const anchors = sliceAnchorLabels(slice, pointCloud);

  return (
    <section className="slice-panel" aria-label={title}>
      <h3>{title}</h3>
      <p className="slice-axis-summary">{sliceAxisSummary(slice, slice.selection.orientation)}</p>
      <div className="slice-map-frame" aria-label={`${title} orientation map`}>
        <span className="slice-map-anchor slice-map-anchor-top">{anchors.top}</span>
        <span className="slice-map-anchor slice-map-anchor-left">{anchors.left}</span>
        <SliceHeatmap
          title={title}
          slice={slice}
          selectedRegion={selectedRegion}
          onSelectRegion={onSelectRegion}
        />
        <span className="slice-map-anchor slice-map-anchor-right">{anchors.right}</span>
        <span className="slice-map-anchor slice-map-anchor-bottom">{anchors.bottom}</span>
      </div>
      <div className="heatmap-legend" aria-label={`${title} color scale`}>
        <span>{formatMaybeNumber(slice.stats.min, slice.field.units)}</span>
        <span className={`heatmap-scale ${heatmapScaleClass(slice.field)}`} />
        <span>{formatMaybeNumber(slice.stats.max, slice.field.units)}</span>
      </div>
      <details>
        <summary>Technical slice details</summary>
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

function sliceAnchorLabels(
  slice: SliceResponse,
  pointCloud?: PointCloudResponse | null,
): {
  left: string;
  right: string;
  top: string;
  bottom: string;
} {
  const xSize = axisSize(slice, slice.field.coordinate_names.x);
  const ySize = axisSize(slice, slice.field.coordinate_names.y);
  const zSize = axisSize(slice, slice.field.coordinate_names.vertical);
  const xMin = axisEndpointLabel("x", pointCloud?.coordinate_extents.xh, 0);
  const xMax = axisEndpointLabel("x", pointCloud?.coordinate_extents.xh, Math.max(0, xSize - 1));
  const yMin = axisEndpointLabel("y", pointCloud?.coordinate_extents.yh, 0);
  const yMax = axisEndpointLabel("y", pointCloud?.coordinate_extents.yh, Math.max(0, ySize - 1));
  const zMin = axisEndpointLabel("z", pointCloud?.coordinate_extents.zh, 0);
  const zMax = axisEndpointLabel("z", pointCloud?.coordinate_extents.zh, Math.max(0, zSize - 1));
  const orientation = slice.selection.orientation;
  if (orientation === "horizontal") {
    return {
      left: xMin,
      right: xMax,
      top: yMax,
      bottom: yMin,
    };
  }
  if (orientation === "vertical_x") {
    return {
      left: xMin,
      right: xMax,
      top: zMax,
      bottom: zMin,
    };
  }
  return {
    left: yMin,
    right: yMax,
    top: zMax,
    bottom: zMin,
  };
}

function axisEndpointLabel(
  axis: string,
  extent: { min: number; max: number; units: string | null } | undefined,
  fallbackIndex: number,
): string {
  if (!extent) return `${axis} index ${fallbackIndex}`;
  const value = fallbackIndex === 0 ? extent.min : extent.max;
  return `${axis} ${formatCompactNumber(value)}${extent.units ? ` ${extent.units}` : ""}`;
}

function axisSize(slice: SliceResponse, dimension: string | null): number {
  if (!dimension) return 1;
  const index = slice.field.dimensions.indexOf(dimension);
  return index >= 0 ? (slice.field.shape[index] ?? 1) : 1;
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
      <legend>Explanation focus</legend>
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
    <section className="process-overlay-panel" aria-label="Explanation evidence">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Evidence</p>
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

function SelectedRegionInspector({
  selectedRegion,
  slice,
  selectedValue,
  diagnostics,
  status,
  error,
}: {
  selectedRegion: SelectedRegionRequest | null;
  slice: SliceResponse | null;
  selectedValue: number | null;
  diagnostics: SelectedRegionDiagnosticsResponse | null;
  status: string;
  error: string | null;
}) {
  return (
    <section className="selected-region-inspector" aria-label="What happened here panel">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Explanation</p>
          <h3>What happened here?</h3>
        </div>
        <p className="state-chip">{status}</p>
      </div>

      {!selectedRegion && (
        <p>
          Click a slice cell to inspect that point.
        </p>
      )}

      {error && <p role="alert">{error}</p>}

      {selectedRegion && (
        <SelectedPointContext
          selectedRegion={selectedRegion}
          slice={slice}
          selectedValue={selectedValue}
          diagnostics={diagnostics}
        />
      )}

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

          <details>
            <summary>Technical details and provenance</summary>
            <dl className="metric-grid">
              <Metric label="Region type" value={humanize(diagnostics.region.region_type)} />
              <Metric label="Native grid" value={diagnostics.region.native_grid ?? "Unavailable"} />
              <Metric label="Cell count" value={String(diagnostics.region.cell_count ?? "unknown")} />
              <Metric label="x" value={axisSelectionLabel(diagnostics.region.x)} />
              <Metric label="y" value={axisSelectionLabel(diagnostics.region.y)} />
              <Metric label="vertical" value={axisSelectionLabel(diagnostics.region.vertical)} />
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

function SelectedPointContext({
  selectedRegion,
  slice,
  selectedValue,
  diagnostics,
}: {
  selectedRegion: SelectedRegionRequest;
  slice: SliceResponse | null;
  selectedValue: number | null;
  diagnostics: SelectedRegionDiagnosticsResponse | null;
}) {
  const x = diagnostics?.region.x ? axisSelectionLabel(diagnostics.region.x) : indexOrUnavailable(selectedRegion.xIndex);
  const y = diagnostics?.region.y ? axisSelectionLabel(diagnostics.region.y) : indexOrUnavailable(selectedRegion.yIndex);
  const z = diagnostics?.region.vertical
    ? axisSelectionLabel(diagnostics.region.vertical)
    : indexOrUnavailable(selectedRegion.zIndex);
  return (
    <section className="selected-point-context" aria-label="Selected point context">
      <h4>Selected point</h4>
      <dl className="metric-grid">
        <Metric
          label="Slice"
          value={slice ? slicePlainLabel(slice, slice.selection.orientation, slice.selection.selected_index) : "Unavailable"}
        />
        <Metric label="Time" value={formatSeconds(slice?.selection.time_seconds ?? null)} />
        <Metric
          label="Field"
          value={slice ? `${slice.field.raw_field_name} (${slice.field.display_name})` : "Unavailable"}
        />
        <Metric
          label="Selected field value"
          value={formatMaybeNumber(selectedValue, slice?.field.units ?? null)}
        />
        <Metric label="x" value={x} />
        <Metric label="y" value={y} />
        <Metric label="z" value={z} />
      </dl>
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
  const displayRows = downsampleSliceValues(slice);
  return (
    <div className="slice-heatmap" role="img" aria-label={`${title} heatmap`}>
      {displayRows.map((row, displayRowIndex) => (
        <div className="heatmap-row" key={`${title}-heatmap-${displayRowIndex}`}>
          {row.map((cell, displayColumnIndex) => {
            const selected = isSelectedSliceDisplayCell(slice, selectedRegion, cell);
            return (
              <button
                type="button"
                className={`heatmap-cell${selected ? " heatmap-cell-selected" : ""}`}
                key={`${title}-heatmap-${displayRowIndex}-${displayColumnIndex}`}
                title={cell.value === null ? "missing" : formatMaybeNumber(cell.value, slice.field.units)}
                aria-label={`Inspect ${title} row ${displayRowIndex + 1}, column ${displayColumnIndex + 1}`}
                style={sliceCellStyle(cell.value, slice)}
                onClick={() => onSelectRegion?.(slice, cell.sourceRowIndex, cell.sourceColumnIndex)}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

type DisplayHeatmapCell = {
  value: number | null;
  sourceRowIndex: number;
  sourceColumnIndex: number;
  rowStart: number;
  rowEnd: number;
  columnStart: number;
  columnEnd: number;
};

function downsampleSliceValues(slice: SliceResponse): DisplayHeatmapCell[][] {
  const values = slice.values;
  const maxRows = 28;
  const maxColumns = 60;
  const rowCount = values.length;
  const columnCount = values[0]?.length ?? 0;
  const rowStride = Math.max(1, Math.ceil(rowCount / maxRows));
  const columnStride = Math.max(1, Math.ceil(columnCount / maxColumns));

  const rows: DisplayHeatmapCell[][] = [];
  for (let rowStart = 0; rowStart < rowCount; rowStart += rowStride) {
    const rowEnd = Math.min(rowCount, rowStart + rowStride);
    const displayRow: DisplayHeatmapCell[] = [];
    for (let columnStart = 0; columnStart < columnCount; columnStart += columnStride) {
      const columnEnd = Math.min(columnCount, columnStart + columnStride);
      const summary = summarizeSliceBlock(slice, rowStart, rowEnd, columnStart, columnEnd);
      displayRow.push({
        value: summary.value,
        sourceRowIndex: summary.sourceRowIndex,
        sourceColumnIndex: summary.sourceColumnIndex,
        rowStart,
        rowEnd: rowEnd - 1,
        columnStart,
        columnEnd: columnEnd - 1,
      });
    }
    rows.push(displayRow);
  }
  return rows;
}

function summarizeSliceBlock(
  slice: SliceResponse,
  rowStart: number,
  rowEnd: number,
  columnStart: number,
  columnEnd: number,
): { value: number | null; sourceRowIndex: number; sourceColumnIndex: number } {
  const values = slice.values;
  const centerRow = Math.floor((rowStart + rowEnd - 1) / 2);
  const centerColumn = Math.floor((columnStart + columnEnd - 1) / 2);
  const fallbackRow = Math.min(Math.max(0, centerRow), Math.max(0, values.length - 1));
  const fallbackColumn = Math.min(
    Math.max(0, centerColumn),
    Math.max(0, (values[0]?.length ?? 1) - 1),
  );
  const mode = sliceAggregationMode(slice.field);
  let total = 0;
  let count = 0;
  let selectedValue: number | null = null;
  let selectedRow = fallbackRow;
  let selectedColumn = fallbackColumn;

  for (let rowIndex = rowStart; rowIndex < rowEnd; rowIndex += 1) {
    for (let columnIndex = columnStart; columnIndex < columnEnd; columnIndex += 1) {
      const value = values[rowIndex]?.[columnIndex];
      if (typeof value === "number" && Number.isFinite(value)) {
        total += value;
        count += 1;
        if (mode === "max") {
          if (selectedValue === null || value > selectedValue) {
            selectedValue = value;
            selectedRow = rowIndex;
            selectedColumn = columnIndex;
          }
        } else if (
          mode === "largest_magnitude" &&
          (selectedValue === null || Math.abs(value) > Math.abs(selectedValue))
        ) {
          selectedValue = value;
          selectedRow = rowIndex;
          selectedColumn = columnIndex;
        }
      }
    }
  }

  if (count === 0) {
    return { value: null, sourceRowIndex: fallbackRow, sourceColumnIndex: fallbackColumn };
  }

  if (mode === "mean") {
    return { value: total / count, sourceRowIndex: fallbackRow, sourceColumnIndex: fallbackColumn };
  }

  return {
    value: selectedValue,
    sourceRowIndex: selectedRow,
    sourceColumnIndex: selectedColumn,
  };
}

function sliceAggregationMode(field: VisualizableField): "max" | "largest_magnitude" | "mean" {
  if (
    field.raw_field_name === "qc" ||
    field.canonical_field_name === "cloud_water" ||
    field.raw_field_name === "qr" ||
    field.canonical_field_name === "rain_water"
  ) {
    return "max";
  }
  if (field.raw_field_name === "w" || field.canonical_field_name === "vertical_velocity") {
    return "largest_magnitude";
  }
  return "mean";
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

function isSelectedSliceDisplayCell(
  slice: SliceResponse,
  selectedRegion: SelectedRegionRequest | null | undefined,
  cell: DisplayHeatmapCell,
): boolean {
  if (!selectedRegion) return false;
  for (let rowIndex = cell.rowStart; rowIndex <= cell.rowEnd; rowIndex += 1) {
    for (let columnIndex = cell.columnStart; columnIndex <= cell.columnEnd; columnIndex += 1) {
      if (isSelectedSliceCell(slice, selectedRegion, rowIndex, columnIndex)) return true;
    }
  }
  return false;
}

function axisSelectionLabel(axis: AxisSelection | null): string {
  if (!axis) return "Unavailable";
  const coordinate =
    axis.start_coordinate === axis.end_coordinate
      ? formatAxisCoordinate(axis.start_coordinate)
      : `${formatAxisCoordinate(axis.start_coordinate)} to ${formatAxisCoordinate(axis.end_coordinate)}`;
  const index =
    axis.start_index === axis.end_index
      ? `${axis.dimension}[${axis.start_index}]`
      : `${axis.dimension}[${axis.start_index}..${axis.end_index}]`;
  return `${index}; ${coordinate}${axis.units ? ` ${axis.units}` : ""}`;
}

function formatAxisCoordinate(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return "unknown";
  const numericValue = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numericValue) ? formatCompactNumber(numericValue) : String(value);
}

function indexOrUnavailable(index: number | undefined): string {
  return index === undefined ? "Unavailable" : `index ${index}`;
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
    background: `rgba(63, 178, 206, ${0.36 + intensity * 0.52})`,
  };
}

function projectPoint(
  x: number,
  y: number,
  z: number,
  projectionMode: ProjectionMode,
  pointCloud: PointCloudResponse | null,
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
  const left = 8;
  const width = 88;
  const horizontalCoordinate = projectionMode === "side_yz" ? "yh" : "xh";
  const verticalCoordinate = projectionMode === "top_down" ? "yh" : "zh";
  const horizontalRange = coordinateRange(pointCloud, horizontalCoordinate);
  const verticalRange = coordinateRange(pointCloud, verticalCoordinate);
  const ratio = horizontalRange > 0 ? verticalRange / horizontalRange : 0.7;
  const height =
    projectionMode === "top_down" ? clamp(width * ratio, 34, 68) : clamp(width * ratio * 1.3, 48, 64);
  return {
    left,
    width,
    height,
    bottom: 10,
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

function heatmapScaleClass(field: VisualizableField): string {
  if (field.raw_field_name === "w" || field.canonical_field_name === "vertical_velocity") {
    return "heatmap-scale-velocity";
  }
  if (field.raw_field_name === "qc" || field.canonical_field_name === "cloud_water") {
    return "heatmap-scale-cloud-water";
  }
  if (field.raw_field_name === "qr" || field.canonical_field_name === "rain_water") {
    return "heatmap-scale-rain-water";
  }
  return "heatmap-scale-default";
}

function sliceCellStyle(value: number | null, slice: SliceResponse): CSSProperties {
  if (value === null) {
    return { background: "rgba(255, 255, 255, 0.36)" };
  }

  if (slice.field.raw_field_name === "w" || slice.field.canonical_field_name === "vertical_velocity") {
    const maxMagnitude = Math.max(
      Math.abs(slice.stats.min ?? value),
      Math.abs(slice.stats.max ?? value),
      Number.EPSILON,
    );
    const scaled = Math.max(-1, Math.min(1, value / maxMagnitude));
    if (scaled >= 0) {
      return {
        background: `rgba(${224 - scaled * 96}, ${242 - scaled * 86}, ${236 - scaled * 132}, ${0.58 + scaled * 0.34})`,
      };
    }
    const magnitude = Math.abs(scaled);
    return {
      background: `rgba(${229 - magnitude * 90}, ${238 - magnitude * 112}, ${247 - magnitude * 88}, ${0.58 + magnitude * 0.32})`,
    };
  }

  const min = slice.stats.min ?? value;
  const max = slice.stats.max ?? value;
  const normalized = normalize(value, min, max);
  const intensity =
    slice.field.raw_field_name === "qc" || slice.field.canonical_field_name === "cloud_water"
      ? Math.sqrt(Math.max(0, normalized))
      : normalized;
  if (intensity < 0.015) {
    return { background: "rgba(234, 244, 248, 0.72)" };
  }
  return {
    background: `rgba(${38 + intensity * 155}, ${98 + intensity * 130}, ${128 + intensity * 108}, ${0.62 + intensity * 0.28})`,
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

function resultStory(result: ResultCard): string {
  if (isDryFailedContrast(result)) {
    return "Thermals rose, but low-level moisture stayed too dry for meaningful cloud water or rain.";
  }
  if (isValidatedQuickLookBaseline(result)) {
    return "Cloud water formed in the validated quick-look baseline; vertical motion and rain were both detected.";
  }
  if (cloudOutcome(result) === "Cloud formed") {
    return "Cloud water formed during this run. Open it in Explore to inspect the cloud and updraft structure.";
  }
  if (cloudOutcome(result) === "No cloud formed") {
    return "No cloud formed by the current diagnostic threshold. The vertical velocity field may still explain the thermal behavior.";
  }
  return result.diagnostics_summary ?? "Diagnostics are not available yet.";
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
  const safeSummary = summary as Partial<OutputFileSummary>;
  const modelFileCount = safeSummary.model_output_count ?? safeSummary.model_output_file_count;
  const outputFileLabel =
    modelFileCount !== undefined
      ? `${modelFileCount} model files`
      : safeSummary.netcdf_count !== undefined
        ? `${safeSummary.netcdf_count} NetCDF files`
        : "unknown output files";
  const parts = [
    outputFileLabel,
    `${safeSummary.time_steps ?? "unknown"} time steps`,
  ];
  if ((safeSummary.stats_netcdf_count ?? 0) > 0) {
    parts.push(`${safeSummary.stats_netcdf_count} stats files`);
  }
  if ((safeSummary.raw_cm1_artifact_count ?? 0) > 0) {
    parts.push(`${safeSummary.raw_cm1_artifact_count} raw files`);
  }
  return parts.join(", ");
}

function storageDisplayName(run: RunStorageEntry, result: ResultCard | undefined): string {
  return result?.name ?? run.scenario_name ?? (run.scenario_id ? humanize(run.scenario_id) : run.run_id);
}

function storageScenarioName(run: RunStorageEntry, result: ResultCard | undefined): string {
  return result?.scenario_name ?? run.scenario_name ?? humanize(run.scenario_id ?? "unknown scenario");
}

function storageScenarioSummary(run: RunStorageEntry, result: ResultCard | undefined): string {
  const scenario = storageScenarioName(run, result);
  const preset = humanize(result?.run_size_preset ?? run.run_size_preset ?? "preset unknown");
  return `${scenario} · ${preset}`;
}

function storagePresetAndControls(run: RunStorageEntry, result: ResultCard | undefined): string {
  const preset = humanize(result?.run_size_preset ?? run.run_size_preset ?? "preset unknown");
  if (!result) return preset;
  return `${preset} · ${storageControlSummary(result.controls)}`;
}

function canIngestStorageRun(run: RunStorageEntry, result: ResultCard | undefined): boolean {
  return Boolean(!result && run.manifest_path && run.category === "completed_with_output");
}

function storageStateBadges(
  run: RunStorageEntry,
  result: ResultCard | undefined,
): Array<{ label: string; tone: "good" | "warning" | "neutral" }> {
  const savedOrProtected = Boolean(result?.saved || result?.protected || run.saved || run.protected);
  if (savedOrProtected) {
    return [
      { label: "Saved/protected", tone: "good" },
      { label: result ? "Ingested / ready to review" : "Protected local run", tone: "neutral" },
    ];
  }
  if (result) {
    return [
      { label: "Ingested / ready to review", tone: "good" },
      { label: "Not saved", tone: "neutral" },
    ];
  }
  const primary: Record<string, { label: string; tone: "good" | "warning" | "neutral" }> = {
    dry_run_only: { label: "Ready-to-run package", tone: "neutral" },
    running: { label: "Running CM1 process", tone: "neutral" },
    completed_with_output: { label: "Ready to ingest", tone: "good" },
    completed_no_output: { label: "Completed with no usable output", tone: "warning" },
    failed: { label: "Failed run", tone: "warning" },
    canceled: { label: "Canceled run", tone: "warning" },
    missing_manifest: { label: "Needs cleanup review", tone: "warning" },
    malformed_manifest: { label: "Needs cleanup review", tone: "warning" },
    unknown: { label: "Needs cleanup review", tone: "warning" },
  };
  const badge = primary[run.category] ?? { label: humanize(run.category), tone: "neutral" };
  const badges = [badge];
  if (run.category !== "running" && run.category !== "dry_run_only") {
    badges.push({ label: "Not saved", tone: "neutral" });
  }
  return badges;
}

function storageNextStep(run: RunStorageEntry, result: ResultCard | undefined): string {
  if (result?.saved || result?.protected || run.saved || run.protected) {
    return "Keeper result; normal cleanup is blocked here.";
  }
  if (result) return "Review in Results or Explore; cleanup preview remains available.";
  if (run.category === "dry_run_only") return "Package is generated and can be launched from Build.";
  if (run.category === "running") return "CM1 is active or queued; cleanup is blocked until it stops.";
  if (run.category === "completed_with_output") {
    return "Output exists; ingest to create a notebook result before deciding cleanup.";
  }
  if (run.category === "completed_no_output") {
    return "No usable output was detected; inspect logs or preview cleanup.";
  }
  if (run.category === "failed" || run.category === "canceled") {
    return "Run did not complete; inspect logs or preview cleanup.";
  }
  if (run.category === "missing_manifest" || run.category === "malformed_manifest") {
    return "Manifest is missing or unreadable; review carefully before cleanup.";
  }
  return "Review the local directory state before cleanup.";
}

function storageOutputSummary(run: RunStorageEntry): string {
  const netcdf = run.output_summary.netcdf_paths ?? 0;
  const raw = run.output_summary.raw_cm1_artifacts ?? 0;
  const processed = run.output_summary.processed_artifacts ?? 0;
  if (run.output_artifact_count === 0) return "No output artifacts";
  const parts = [];
  if (netcdf > 0) parts.push(`${netcdf} NetCDF files`);
  if (raw > 0) parts.push(`${raw} raw CM1 files`);
  if (processed > 0) parts.push(`${processed} processed files`);
  return parts.length > 0 ? parts.join(", ") : `${run.output_artifact_count} output artifacts`;
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
