import { useEffect, useMemo, useState } from "react";
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

type WorkspaceSection = "build" | "results" | "compare" | "inspect" | "visualize";

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
type SceneViewPreset = "cloud-overview" | "vertical-cross-section" | "top-down-slice" | "updraft";
type ProjectionMode = "oblique" | "side_xz" | "side_yz" | "top_down";

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

async function fetchResults(): Promise<ResultsResponse> {
  const response = await fetch("/api/results");
  if (!response.ok) {
    throw new Error("Unable to load results.");
  }
  return response.json() as Promise<ResultsResponse>;
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

async function fetchVisualizationFields(resultId: string): Promise<FieldCatalogResponse> {
  const response = await fetch(`/api/results/${resultId}/visualization/fields`);
  if (!response.ok) {
    throw new Error(await responseError(response, "Unable to load visualization fields."));
  }
  return response.json() as Promise<FieldCatalogResponse>;
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
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("baseline-shallow-cumulus");
  const [controls, setControls] = useState<Record<string, string | number | boolean>>({});
  const [runSizePreset, setRunSizePreset] = useState("quick_look");
  const [dryRun, setDryRun] = useState<DryRunResponse | null>(null);
  const [results, setResults] = useState<ResultCard[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [resultDraft, setResultDraft] = useState({ name: "", tags: "", notes: "" });
  const [resultsStatus, setResultsStatus] = useState("Loading results...");
  const [status, setStatus] = useState("Loading scenarios...");
  const [error, setError] = useState<string | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchScenarioCatalog()
      .then((catalog) => {
        if (!active) return;
        setScenarios(catalog.scenarios);
        setSelectedScenarioId(catalog.golden_path_scenario_id);
        setStatus("Scenario setup");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setError(caught instanceof Error ? caught.message : "Unable to load scenarios.");
      });
    return () => {
      active = false;
    };
  }, []);

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
        setResultsError(caught instanceof Error ? caught.message : "Unable to load results.");
        setResultsStatus("Results unavailable");
      });
    return () => {
      active = false;
    };
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
    try {
      const result = await requestDryRunPackage(selectedScenario.id, controls, runSizePreset);
      setDryRun(result);
      setStatus("Packaged dry-run output");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create dry-run package.");
      setStatus("Scenario setup");
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

  if (error && scenarios.length === 0) {
    return (
      <main className="app-shell">
        <h1>Cloud Chamber</h1>
        <p role="alert">{error}</p>
      </main>
    );
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
        {(["build", "results", "compare", "inspect", "visualize"] as WorkspaceSection[]).map((section) => (
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
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          selectedScenarioId={selectedScenarioId}
          controls={controls}
          runSizePreset={runSizePreset}
          validationMessages={validationMessages}
          dryRun={dryRun}
          onSelectScenario={setSelectedScenarioId}
          onControlChange={(id, value) =>
            setControls((current) => ({
              ...current,
              [id]: value,
            }))
          }
          onRunSizeChange={setRunSizePreset}
          onDryRun={handleDryRun}
        />
      )}

      {activeSection === "results" && (
        <ResultsWorkspace
          results={results}
          selectedResult={selectedResult}
          selectedResultId={selectedResult?.result_id ?? null}
          resultsStatus={resultsStatus}
          resultsError={resultsError}
          draft={resultDraft}
          onSelectResult={setSelectedResultId}
          onDraftChange={setResultDraft}
          onSubmit={handleResultUpdate}
          onSave={handleResultSave}
          onInspect={() => {
            setActiveSection("inspect");
          }}
          onOpenVisualizer={() => {
            setActiveSection("visualize");
          }}
        />
      )}

      {activeSection === "compare" && (
        <ComparisonWorkspace
          pair={comparisonPair}
          onInspect={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("inspect");
          }}
          onVisualize={(resultId) => {
            setSelectedResultId(resultId);
            setActiveSection("visualize");
          }}
        />
      )}

      {activeSection === "inspect" && (
        <section className="workspace-section" aria-labelledby="inspect-workspace-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Inspect</p>
              <h2 id="inspect-workspace-title">Inspect fields</h2>
            </div>
            <p className="state-chip">{selectedResult ? selectedResult.name : "No result"}</p>
          </div>
          {selectedResult ? (
            <FieldInspector result={selectedResult} />
          ) : (
            <section className="status-panel">
              <p>Select an ingested result before inspecting fields.</p>
            </section>
          )}
        </section>
      )}

      {activeSection === "visualize" && (
        <section className="workspace-section" aria-labelledby="visualize-workspace-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Visualize</p>
              <h2 id="visualize-workspace-title">3-D cloud view</h2>
            </div>
            <p className="state-chip">{selectedResult ? selectedResult.name : "No result"}</p>
          </div>
          {selectedResult ? (
            <VisualizerSceneShell result={selectedResult} />
          ) : (
            <section className="status-panel">
              <p>Select an ingested result before opening the 3-D view.</p>
            </section>
          )}
        </section>
      )}
    </main>
  );
}

function BuildWorkspace({
  status,
  scenarios,
  selectedScenario,
  selectedScenarioId,
  controls,
  runSizePreset,
  validationMessages,
  dryRun,
  onSelectScenario,
  onControlChange,
  onRunSizeChange,
  onDryRun,
}: {
  status: string;
  scenarios: Scenario[];
  selectedScenario: Scenario | undefined;
  selectedScenarioId: string;
  controls: Record<string, string | number | boolean>;
  runSizePreset: string;
  validationMessages: string[];
  dryRun: DryRunResponse | null;
  onSelectScenario: (scenarioId: string) => void;
  onControlChange: (controlId: string, value: string) => void;
  onRunSizeChange: (presetId: string) => void;
  onDryRun: (event: FormEvent<HTMLFormElement>) => void;
}) {
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
            value={selectedScenarioId}
            onChange={(event) => onSelectScenario(event.target.value)}
          >
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.display_name}
              </option>
            ))}
          </select>

          {selectedScenario && (
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

              <button type="submit" disabled={validationMessages.length > 0}>
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

          <section className="status-panel" aria-labelledby="review-title">
            <p className="eyebrow">Generated package</p>
            <h3 id="review-title">Review before local CM1 run</h3>
            {dryRun ? (
              <DryRunReview dryRun={dryRun} />
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

function ResultsWorkspace({
  results,
  selectedResult,
  selectedResultId,
  resultsStatus,
  resultsError,
  draft,
  onSelectResult,
  onDraftChange,
  onSubmit,
  onSave,
  onInspect,
  onOpenVisualizer,
}: {
  results: ResultCard[];
  selectedResult: ResultCard | undefined;
  selectedResultId: string | null;
  resultsStatus: string;
  resultsError: string | null;
  draft: { name: string; tags: string; notes: string };
  onSelectResult: (resultId: string) => void;
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSave: () => void;
  onInspect: () => void;
  onOpenVisualizer: () => void;
}) {
  return (
    <section className="results-library" aria-labelledby="results-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Results</p>
          <h2 id="results-title">Experiment Notebook</h2>
        </div>
        <p className="state-chip">{resultsStatus}</p>
      </div>

      {selectedResult && (
        <section className="featured-result" aria-label="Selected result">
          <div>
            <p className="eyebrow">Ready to inspect</p>
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
          <button type="button" onClick={onOpenVisualizer}>
            Open 3-D
          </button>
        </section>
      )}

      {resultsError && <p role="alert">{resultsError}</p>}

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

function ComparisonWorkspace({
  pair,
  onInspect,
  onVisualize,
}: {
  pair: { baseline: ResultCard | undefined; dryFailed: ResultCard | undefined };
  onInspect: (resultId: string) => void;
  onVisualize: (resultId: string) => void;
}) {
  const missing = comparisonMissingItems(pair);

  return (
    <section className="comparison-workspace" aria-labelledby="comparison-title">
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
            />
            <ComparisonResultCard
              roleLabel="Dry Failed"
              result={pair.dryFailed}
              onInspect={onInspect}
              onVisualize={onVisualize}
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
                value="Side-by-side 2-D slices are planned as follow-up; use Inspect for one result at a time."
              />
            </dl>
          </section>

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
}: {
  roleLabel: "Baseline" | "Dry Failed";
  result: ResultCard | undefined;
  onInspect: (resultId: string) => void;
  onVisualize: (resultId: string) => void;
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
          Inspect {roleLabel}
        </button>
        <button type="button" onClick={() => onVisualize(result.result_id)}>
          Visualize {roleLabel}
        </button>
      </div>
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

function DryRunReview({ dryRun }: { dryRun: DryRunResponse }) {
  return (
    <div className="dry-run-review">
      <dl>
        <div>
          <dt>Package path</dt>
          <dd>{dryRun.package_dir}</dd>
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
      <p>Product state: {dryRun.report.provenance.product_state}</p>
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
  const [selectedTimeDefaults, setSelectedTimeDefaults] = useState<ViewDefaultsResponse | null>(null);
  const [selectedFieldName, setSelectedFieldName] = useState("");
  const [timeIndex, setTimeIndex] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [threshold, setThreshold] = useState(1e-6);
  const [opacity, setOpacity] = useState(0.68);
  const [pointSize, setPointSize] = useState(11);
  const [isPlaying, setIsPlaying] = useState(false);
  const [pointCloud, setPointCloud] = useState<PointCloudResponse | null>(null);
  const [viewPreset, setViewPreset] = useState<SceneViewPreset>("cloud-overview");
  const [projectionMode, setProjectionMode] = useState<ProjectionMode>("oblique");
  const [showSlicePlanes, setShowSlicePlanes] = useState(false);
  const [sliceFieldName, setSliceFieldName] = useState("qc");
  const [sliceOrientation, setSliceOrientation] = useState<"vertical_x" | "vertical_y">("vertical_x");
  const [horizontalSliceLevel, setHorizontalSliceLevel] = useState(0);
  const [verticalSliceIndex, setVerticalSliceIndex] = useState(0);
  const [sceneHorizontalSlice, setSceneHorizontalSlice] = useState<SliceResponse | null>(null);
  const [sceneVerticalSlice, setSceneVerticalSlice] = useState<SliceResponse | null>(null);
  const [sceneStatus, setSceneStatus] = useState("Loading scene data...");
  const [sceneError, setSceneError] = useState<string | null>(null);
  const [sliceError, setSliceError] = useState<string | null>(null);
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
    setViewPreset("cloud-overview");
    setProjectionMode("oblique");
    setShowSlicePlanes(false);
    setSliceFieldName("qc");
    setSliceOrientation("vertical_x");
    setHorizontalSliceLevel(0);
    setVerticalSliceIndex(0);
    setSceneHorizontalSlice(null);
    setSceneVerticalSlice(null);
    setSliceError(null);
    setSceneStatus("Loading scene data...");
    Promise.all([
      fetchVisualizationFields(result.result_id),
      fetchVisualizationDefaults(result.result_id).catch(() => null),
    ])
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
  }, [result]);

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
  const sliceVerticalSize = sliceField?.coordinate_names.vertical
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.vertical)]
    : 1;
  const sliceYSize = sliceField?.coordinate_names.y
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.y)]
    : 1;
  const sliceXSize = sliceField?.coordinate_names.x
    ? sliceField.shape[sliceField.dimensions.indexOf(sliceField.coordinate_names.x)]
    : 1;
  const verticalSliceMax = sliceOrientation === "vertical_x" ? sliceYSize : sliceXSize;
  const provenanceLabel =
    pointCloud?.provenance.provenance_label ??
    selectedField?.provenance.provenance_label ??
    catalog?.provenance.provenance_label ??
    "CM1-derived visualization-ready data; rendering not implemented";
  const selectedDefaults = defaultsForField(viewDefaults, selectedFieldName);
  const sliceDefaults = defaultsForField(viewDefaults, sliceFieldName);
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

      {sceneError && <p role="alert">{sceneError}</p>}

      {catalog && catalog.available_fields.length === 0 && (
        <p role="status">No visualization-ready fields are available for this result.</p>
      )}

      <div className="visualizer-layout">
        <div className="scene-container" aria-label="3-D scene container">
          <div className="viewport-frame">
            <div
              className="plotting-layer"
              aria-label="Stable visualizer plotting group"
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
              <ScaleMarkers pointCloud={pointCloud} projectionMode={projectionMode} />
              <div className="scene-context-label">
                <strong>{projectionLabel(projectionMode)}</strong>
                <span>{selectedTimeLabel}</span>
                <span>Cloud-water threshold {formatScientific(threshold, "kg/kg")}</span>
              </div>
              {showSlicePlanes && (
                <>
                  {viewPreset === "top-down-slice" || viewPreset === "cloud-overview" ? (
                    <SlicePlane title="Horizontal slice plane" slice={sceneHorizontalSlice} />
                  ) : null}
                  {viewPreset !== "top-down-slice" ? (
                    <SlicePlane title="Vertical slice plane" slice={sceneVerticalSlice} />
                  ) : null}
                </>
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
                  : "No cloud water above the selected threshold at this time."}
              </h3>
              <p>
                Adjust the time or threshold after qc is available. Rendering remains an
                interpretation of CM1-derived data.
              </p>
            </div>
          )}
        </div>

        <aside className="visualizer-controls" aria-label="3-D scene controls">
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
              Zoom scales the plotting group only; it does not change CM1 coordinates or slice
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
              <legend>Field and time</legend>
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
                    setTimeIndex(defaultTimeIndex(nextField, result, defaultsForField(viewDefaults, event.target.value)));
                  }}
                >
                  {catalog.available_fields.map((field) => (
                    <option key={field.raw_field_name} value={field.raw_field_name}>
                      {field.raw_field_name} - {field.display_name}
                    </option>
                  ))}
                </select>
              </label>
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
              <label htmlFor="scene-horizontal-level">
                Horizontal slice level
                <input
                  id="scene-horizontal-level"
                  type="number"
                  min={0}
                  max={Math.max(0, sliceVerticalSize - 1)}
                  value={horizontalSliceLevel}
                  onChange={(event) => setHorizontalSliceLevel(Number(event.target.value))}
                />
              </label>
              <label htmlFor="scene-vertical-orientation">
                Vertical orientation
                <select
                  id="scene-vertical-orientation"
                  value={sliceOrientation}
                  onChange={(event) => {
                    const nextOrientation = event.target.value as "vertical_x" | "vertical_y";
                    setSliceOrientation(nextOrientation);
                    setVerticalSliceIndex(
                      defaultVerticalIndex(sliceField, nextOrientation, sliceDefaults),
                    );
                  }}
                >
                  <option value="vertical_x">vertical_x</option>
                  <option value="vertical_y">vertical_y</option>
                </select>
              </label>
              <label htmlFor="scene-vertical-index">
                Vertical slice index
                <input
                  id="scene-vertical-index"
                  type="number"
                  min={0}
                  max={Math.max(0, verticalSliceMax - 1)}
                  value={verticalSliceIndex}
                  onChange={(event) => setVerticalSliceIndex(Number(event.target.value))}
                />
              </label>
            </fieldset>
          )}

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
              <Metric label="View control" value="zoom-only CSS plotting transform" />
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
                value={selectedTimeFieldDefaults?.source ?? selectedDefaults?.source ?? "domain center fallback"}
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
                  sceneVerticalSlice
                    ? `${sceneVerticalSlice.selection.orientation} at ${sceneVerticalSlice.selection.selected_dimension}[${sceneVerticalSlice.selection.selected_index}]`
                    : "Unavailable"
                }
              />
              <Metric label="Projection" value={humanize(projectionMode)} />
              <Metric
                label="Domain x extent"
                value={extentLabel(pointCloud, "xh")}
              />
              <Metric
                label="Domain y extent"
                value={extentLabel(pointCloud, "yh")}
              />
              <Metric
                label="Domain z extent"
                value={extentLabel(pointCloud, "zh")}
              />
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
              <Metric
                label="Max cloud-water location"
                value={maxPointLocationLabel(pointCloud)}
              />
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
      <div className="axis-ticks axis-ticks-horizontal" aria-label={`${horizontalLabel}-axis ticks`}>
        {extentTicks(pointCloud, horizontalCoordinate).map((tick) => (
          <span key={`${horizontalCoordinate}-${tick.position}`} style={{ left: `${tick.position}%` }}>
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
      {showHeight && (
        <p className="active-z-range">active cloud water: {activeRange}</p>
      )}
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

function FieldInspector({ result }: { result: ResultCard }) {
  const [catalog, setCatalog] = useState<FieldCatalogResponse | null>(null);
  const [viewDefaults, setViewDefaults] = useState<ViewDefaultsResponse | null>(null);
  const [selectedFieldName, setSelectedFieldName] = useState("qc");
  const [timeIndex, setTimeIndex] = useState(0);
  const [horizontalLevelIndex, setHorizontalLevelIndex] = useState(0);
  const [verticalLevelIndex, setVerticalLevelIndex] = useState(0);
  const [viewMode, setViewMode] = useState<InspectorViewMode>("vertical_x");
  const [horizontalSlice, setHorizontalSlice] = useState<SliceResponse | null>(null);
  const [verticalSlice, setVerticalSlice] = useState<SliceResponse | null>(null);
  const [inspectorStatus, setInspectorStatus] = useState("Loading fields...");
  const [inspectorError, setInspectorError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setInspectorStatus("Loading fields...");
    setInspectorError(null);
    setCatalog(null);
    setViewDefaults(null);
    setHorizontalSlice(null);
    setVerticalSlice(null);
    setViewMode("vertical_x");
    Promise.all([
      fetchVisualizationFields(result.result_id),
      fetchVisualizationDefaults(result.result_id).catch(() => null),
    ])
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
  }, [result]);

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
    setVerticalLevelIndex(defaultVerticalIndex(selectedField, verticalOrientation, selectedDefaults));
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

      {inspectorError && <p role="alert">{inspectorError}</p>}

      {catalog && catalog.available_fields.length === 0 && (
        <p role="status">No qc/w/qr fields are available for this result.</p>
      )}

      {catalog && selectedField && (
        <>
          <div className="inspector-controls">
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
              value={formatTimeValue(timeOptions[Math.min(timeIndex, timeOptions.length - 1)] ?? null)}
            />
            <Metric label="Default source" value={selectedDefaults?.source ?? "domain center"} />
            <Metric label="Native grid" value={selectedField.native_grid} />
          </dl>

          <div className={viewMode === "compare" ? "slice-grid" : "primary-slice-grid"}>
            {(viewMode === "horizontal" || viewMode === "compare") && (
              <SlicePanel title="Horizontal slice" slice={horizontalSlice} />
            )}
            {(viewMode === "vertical_x" || viewMode === "vertical_y" || viewMode === "compare") && (
              <SlicePanel
                title={viewMode === "vertical_y" ? "Vertical Y slice" : "Vertical X slice"}
                slice={verticalSlice}
              />
            )}
          </div>

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

function SlicePanel({ title, slice }: { title: string; slice: SliceResponse | null }) {
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
      <SliceHeatmap title={title} slice={slice} />
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

function SliceHeatmap({ title, slice }: { title: string; slice: SliceResponse }) {
  return (
    <div className="slice-heatmap" role="img" aria-label={`${title} heatmap`}>
      {slice.values.map((row, rowIndex) => (
        <div className="heatmap-row" key={`${title}-heatmap-${rowIndex}`}>
          {row.map((value, columnIndex) => (
            <span
              className="heatmap-cell"
              key={`${title}-heatmap-${rowIndex}-${columnIndex}`}
              title={value === null ? "missing" : formatMaybeNumber(value, slice.field.units)}
              style={sliceCellStyle(value, slice.stats)}
            />
          ))}
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

function formatTimeValue(value: number | string | null): string {
  if (value === null) return "Time unavailable";
  if (typeof value === "number") return `${value.toLocaleString()} s`;
  return value;
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
  const projected = projectPoint(x, y, z, projectionMode);
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
): { left: number; bottom: number } {
  if (projectionMode === "side_xz") {
    return { left: 12 + x * 76, bottom: 14 + z * 72 };
  }
  if (projectionMode === "side_yz") {
    return { left: 12 + y * 76, bottom: 14 + z * 72 };
  }
  if (projectionMode === "top_down") {
    return { left: 12 + x * 76, bottom: 14 + y * 72 };
  }
  return {
    left: 18 + (x * 0.72 + y * 0.28) * 64,
    bottom: 16 + z * 62 + y * 10,
  };
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
    side_xz: "Side x-z: height is vertical; y is compressed into point opacity for cloud-base and cloud-top checks.",
    side_yz: "Side y-z: height is vertical; x is compressed into point opacity for cloud-base and cloud-top checks.",
    top_down: "Top-down x-y: horizontal map view; height is not shown as vertical position.",
    oblique: "Oblique overview: interpretive overview based on CM1 coordinates, not a true perspective camera.",
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
    compare: "Compare",
    inspect: "Inspect",
    visualize: "Visualize",
  };
  return labels[section];
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
        result.scenario_id === "dry-failed-cumulus" &&
        result.run_size_preset === "quick_look",
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
  const orientation = "vertical_x";
  options.setViewPreset(preset);
  options.setSelectedFieldName(field.raw_field_name);
  options.setSliceFieldName(field.raw_field_name);
  options.setTimeIndex(defaultTimeIndex(field, options.result, defaults));
  options.setHorizontalSliceLevel(defaultHorizontalLevel(field, defaults));
  options.setVerticalSliceIndex(defaultVerticalIndex(field, orientation, defaults));
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
