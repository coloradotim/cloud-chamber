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
  point_order: string[];
  points: Array<[number, number, number, number]>;
  stats: {
    source_count: number;
    returned_count: number;
    min_value: number | null;
    max_value: number | null;
    downsampled: boolean;
    downsample_stride: number;
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

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
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("baseline-shallow-cumulus");
  const [controls, setControls] = useState<Record<string, string | number | boolean>>({});
  const [runSizePreset, setRunSizePreset] = useState("quick_look");
  const [dryRun, setDryRun] = useState<DryRunResponse | null>(null);
  const [results, setResults] = useState<ResultCard[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [resultDraft, setResultDraft] = useState({ name: "", tags: "", notes: "" });
  const [inspectedResultId, setInspectedResultId] = useState<string | null>(null);
  const [visualizerResultId, setVisualizerResultId] = useState<string | null>(null);
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
        setResults(payload.results);
        setSelectedResultId((current) => current ?? payload.results[0]?.result_id ?? null);
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
      current.map((result) => (result.result_id === updated.result_id ? updated : result)),
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
        <p className="state-chip">{status}</p>
      </header>

      <section className="builder-layout" aria-label="Scenario Builder">
        <form className="builder-panel" onSubmit={handleDryRun}>
          <label className="field-label" htmlFor="scenario">
            Scenario
          </label>
          <select
            id="scenario"
            value={selectedScenarioId}
            onChange={(event) => setSelectedScenarioId(event.target.value)}
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
                      onChange={(event) =>
                        setControls((current) => ({
                          ...current,
                          [control.id]: event.target.value,
                        }))
                      }
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
                onChange={(event) => setRunSizePreset(event.target.value)}
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
                Create dry-run package
              </button>
            </>
          )}
        </form>

        <aside className="side-stack">
          <section className="status-panel" aria-labelledby="preview-title">
            <p className="eyebrow">Preview estimate</p>
            <h3 id="preview-title">Preview not implemented</h3>
            <p>
              Future preview estimates will be guidance only. This panel is not CM1 output, not a
              completed result, and not a visualization interpretation.
            </p>
          </section>

          <section className="status-panel" aria-labelledby="review-title">
            <p className="eyebrow">Dry-run review</p>
            <h3 id="review-title">What will be generated</h3>
            {dryRun ? (
              <DryRunReview dryRun={dryRun} />
            ) : (
              <p>
                Request a package to review the manifest, CM1 input placeholders, runtime checklist,
                and dry-run report before any local CM1 launch exists.
              </p>
            )}
          </section>
        </aside>
      </section>

      <section className="results-library" aria-labelledby="results-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Results Library</p>
            <h2 id="results-title">Experiment Notebook</h2>
          </div>
          <p className="state-chip">{resultsStatus}</p>
        </div>

        {resultsError && <p role="alert">{resultsError}</p>}

        <div className="results-layout">
          <ResultsTable
            results={results}
            selectedResultId={selectedResult?.result_id ?? null}
            onSelect={setSelectedResultId}
          />
          <ResultNotebookCard
            result={selectedResult}
            draft={resultDraft}
            onDraftChange={setResultDraft}
            onSubmit={handleResultUpdate}
            onSave={handleResultSave}
            onInspect={() => setInspectedResultId(selectedResult?.result_id ?? null)}
            onOpenVisualizer={() => setVisualizerResultId(selectedResult?.result_id ?? null)}
          />
        </div>

        {inspectedResultId && selectedResult && selectedResult.result_id === inspectedResultId && (
          <FieldInspector result={selectedResult} />
        )}

        {visualizerResultId &&
          selectedResult &&
          selectedResult.result_id === visualizerResultId && (
            <VisualizerSceneShell result={selectedResult} />
          )}
      </section>
    </main>
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
                  {result.name}
                </button>
                <small>{formatDate(result.completed_at ?? result.created_at)}</small>
              </td>
              <td>{result.scenario_name ?? result.scenario_id}</td>
              <td>{humanize(result.status)}</td>
              <td>{humanize(result.run_size_preset)}</td>
              <td>{result.diagnostics_summary ?? "Diagnostics unavailable"}</td>
              <td>{outputSummary(result.output_file_summary)}</td>
              <td>{result.saved || result.protected ? "Saved / protected" : "Not saved"}</td>
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
        <span className={result.saved || result.protected ? "saved-badge" : "plain-badge"}>
          {result.saved || result.protected ? "Saved / protected" : "Not saved"}
        </span>
      </div>

      <dl className="metric-grid">
        <Metric label="Run ID" value={result.run_id} />
        <Metric label="Scenario" value={result.scenario_name ?? result.scenario_id} />
        <Metric label="Run-size preset" value={humanize(result.run_size_preset)} />
        <Metric label="Status" value={humanize(result.status)} />
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

      <section aria-labelledby="provenance-title">
        <h4 id="provenance-title">Provenance labels</h4>
        <ul className="tag-list">
          {result.provenance_labels.map((label) => (
            <li key={label}>{label}</li>
          ))}
        </ul>
      </section>

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
            Open 3-D scene shell
          </button>
        </div>
      </form>
    </section>
  );
}

function VisualizerSceneShell({ result }: { result: ResultCard }) {
  const [catalog, setCatalog] = useState<FieldCatalogResponse | null>(null);
  const [selectedFieldName, setSelectedFieldName] = useState("");
  const [timeIndex, setTimeIndex] = useState(0);
  const [cameraMode, setCameraMode] = useState<"orbit" | "pan">("orbit");
  const [zoom, setZoom] = useState(100);
  const [threshold, setThreshold] = useState(1e-6);
  const [opacity, setOpacity] = useState(0.45);
  const [pointSize, setPointSize] = useState(8);
  const [isPlaying, setIsPlaying] = useState(false);
  const [pointCloud, setPointCloud] = useState<PointCloudResponse | null>(null);
  const [sliceFieldName, setSliceFieldName] = useState("qc");
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
  const maxPoints = 50_000;

  useEffect(() => {
    let active = true;
    setCatalog(null);
    setSceneError(null);
    setSelectedFieldName("");
    setTimeIndex(0);
    setCameraMode("orbit");
    setZoom(100);
    setThreshold(1e-6);
    setOpacity(0.45);
    setPointSize(8);
    setIsPlaying(false);
    setPointCloud(null);
    setSliceFieldName("qc");
    setSliceOrientation("vertical_x");
    setHorizontalSliceLevel(0);
    setVerticalSliceIndex(0);
    setSceneHorizontalSlice(null);
    setSceneVerticalSlice(null);
    setSliceError(null);
    setSceneStatus("Loading scene data...");
    fetchVisualizationFields(result.result_id)
      .then((payload) => {
        if (!active) return;
        setCatalog(payload);
        const firstPreferred =
          payload.available_fields.find((field) => field.raw_field_name === "qc") ??
          payload.available_fields[0];
        setSelectedFieldName(firstPreferred?.raw_field_name ?? "");
        setSliceFieldName(firstPreferred?.raw_field_name ?? "");
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
  }, [result.result_id]);

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
  }, [maxPoints, result.result_id, selectedField, threshold, timeIndex]);

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

  function resetCamera() {
    setCameraMode("orbit");
    setZoom(100);
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
        This is a thresholded point-cloud interpretation of CM1 cloud water. The browser is not
        parsing raw NetCDF, and the points use native-grid qc values without interpolation.
      </p>

      {sceneError && <p role="alert">{sceneError}</p>}

      {catalog && catalog.available_fields.length === 0 && (
        <p role="status">No visualization-ready fields are available for this result.</p>
      )}

      <div className="visualizer-layout">
        <div className="scene-container" aria-label="3-D scene container">
          <div className="scene-horizon" />
          <div className="scene-grid" />
          <SlicePlane title="Horizontal slice plane" slice={sceneHorizontalSlice} />
          <SlicePlane title="Vertical slice plane" slice={sceneVerticalSlice} />
          {pointCloud && pointCloud.points.length > 0 && (
            <div className="point-cloud-layer" aria-label="Cloud-water point cloud">
              {pointCloud.points.map((point, index) => (
                <span
                  className="cloud-point"
                  key={`${point.join("-")}-${index}`}
                  style={cloudPointStyle(
                    point,
                    pointCloud.points,
                    pointCloud.stats,
                    opacity,
                    pointSize,
                  )}
                />
              ))}
            </div>
          )}
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
            <legend>Camera</legend>
            <div className="segmented-buttons">
              <button
                type="button"
                className={cameraMode === "orbit" ? "active-control" : ""}
                onClick={() => setCameraMode("orbit")}
              >
                Orbit
              </button>
              <button
                type="button"
                className={cameraMode === "pan" ? "active-control" : ""}
                onClick={() => setCameraMode("pan")}
              >
                Pan
              </button>
            </div>
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
            <button type="button" onClick={resetCamera}>
              Reset camera
            </button>
          </fieldset>

          {catalog && selectedField && (
            <fieldset>
              <legend>Field and time</legend>
              <label htmlFor="scene-field">
                Field
                <select
                  id="scene-field"
                  value={selectedFieldName}
                  onChange={(event) => {
                    setSelectedFieldName(event.target.value);
                    setTimeIndex(0);
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
              <label htmlFor="slice-field">
                Slice field
                <select
                  id="slice-field"
                  value={sliceFieldName}
                  onChange={(event) => {
                    setSliceFieldName(event.target.value);
                    setHorizontalSliceLevel(0);
                    setVerticalSliceIndex(0);
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
                  onChange={(event) =>
                    setSliceOrientation(event.target.value as "vertical_x" | "vertical_y")
                  }
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

          <dl className="metric-grid">
            <Metric label="Run ID" value={result.run_id} />
            <Metric label="Camera mode" value={cameraMode} />
            <Metric label="Zoom" value={`${zoom}%`} />
            <Metric label="Opacity" value={String(opacity)} />
            <Metric label="Point size" value={`${pointSize}px`} />
            <Metric
              label="Selected time"
              value={formatTimeValue(timeOptions[Math.min(timeIndex, timeMax)] ?? null)}
            />
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
          </dl>

          {pointCloud?.stats.downsampled && (
            <p role="status">
              Point cloud downsampled with deterministic stride {pointCloud.stats.downsample_stride}
              .
            </p>
          )}
          {sliceError && <p role="alert">{sliceError}</p>}

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
  const [selectedFieldName, setSelectedFieldName] = useState("qc");
  const [timeIndex, setTimeIndex] = useState(0);
  const [horizontalLevelIndex, setHorizontalLevelIndex] = useState(0);
  const [verticalLevelIndex, setVerticalLevelIndex] = useState(0);
  const [verticalOrientation, setVerticalOrientation] = useState<"vertical_x" | "vertical_y">(
    "vertical_x",
  );
  const [horizontalSlice, setHorizontalSlice] = useState<SliceResponse | null>(null);
  const [verticalSlice, setVerticalSlice] = useState<SliceResponse | null>(null);
  const [inspectorStatus, setInspectorStatus] = useState("Loading fields...");
  const [inspectorError, setInspectorError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setInspectorStatus("Loading fields...");
    setInspectorError(null);
    setCatalog(null);
    setHorizontalSlice(null);
    setVerticalSlice(null);
    fetchVisualizationFields(result.result_id)
      .then((payload) => {
        if (!active) return;
        setCatalog(payload);
        const firstPreferred =
          payload.available_fields.find((field) => field.raw_field_name === "qc") ??
          payload.available_fields[0];
        setSelectedFieldName(firstPreferred?.raw_field_name ?? "");
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
  }, [result.result_id]);

  const selectedField = useMemo(
    () => catalog?.available_fields.find((field) => field.raw_field_name === selectedFieldName),
    [catalog, selectedFieldName],
  );

  useEffect(() => {
    if (!selectedField) return;
    setTimeIndex(0);
    setHorizontalLevelIndex(0);
    setVerticalLevelIndex(0);
  }, [selectedField]);

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

            <label htmlFor="vertical-orientation">
              Vertical slice
              <select
                id="vertical-orientation"
                value={verticalOrientation}
                onChange={(event) =>
                  setVerticalOrientation(event.target.value as "vertical_x" | "vertical_y")
                }
              >
                <option value="vertical_x">vertical_x</option>
                <option value="vertical_y">vertical_y</option>
              </select>
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
            <Metric label="Native grid" value={selectedField.native_grid} />
            <Metric label="Provenance" value={catalog.provenance.provenance_label} />
          </dl>

          <div className="slice-grid">
            <SlicePanel title="Horizontal slice" slice={horizontalSlice} />
            <SlicePanel title="Vertical slice" slice={verticalSlice} />
          </div>
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
      <div className="slice-values" role="table" aria-label={`${title} values`}>
        {slice.values.map((row, rowIndex) => (
          <div className="slice-row" role="row" key={`${title}-${rowIndex}`}>
            {row.map((value, columnIndex) => (
              <span className="slice-cell" role="cell" key={`${title}-${rowIndex}-${columnIndex}`}>
                {value === null ? "null" : formatCompactNumber(value)}
              </span>
            ))}
          </div>
        ))}
      </div>
      <p>{slice.provenance.provenance_label}</p>
      {slice.caveats.length > 0 && (
        <ul className="compact-list">
          {slice.caveats.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      )}
    </section>
  );
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
  points: Array<[number, number, number, number]>,
  stats: PointCloudResponse["stats"],
  opacity: number,
  pointSize: number,
): CSSProperties {
  const xs = points.map((candidate) => candidate[0]);
  const ys = points.map((candidate) => candidate[1]);
  const zs = points.map((candidate) => candidate[2]);
  const x = normalize(point[0], Math.min(...xs), Math.max(...xs));
  const y = normalize(point[1], Math.min(...ys), Math.max(...ys));
  const z = normalize(point[2], Math.min(...zs), Math.max(...zs));
  const intensity = normalize(point[3], stats.min_value ?? point[3], stats.max_value ?? point[3]);
  return {
    left: `${12 + x * 76}%`,
    bottom: `${16 + y * 44}%`,
    width: `${pointSize}px`,
    height: `${pointSize}px`,
    opacity,
    transform: `translate(-50%, 50%) translateY(${-z * 92}px) scale(${0.8 + intensity * 0.75})`,
    background: `rgba(229, 250, 255, ${0.44 + intensity * 0.46})`,
  };
}

function normalize(value: number, min: number, max: number): number {
  if (max <= min) return 0.5;
  return (value - min) / (max - min);
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
