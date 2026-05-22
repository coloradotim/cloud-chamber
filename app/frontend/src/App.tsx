import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

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

export function App() {
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
          />
        </div>
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
}: {
  result: ResultCard | undefined;
  draft: { name: string; tags: string; notes: string };
  onDraftChange: (draft: { name: string; tags: string; notes: string }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSave: () => void;
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
          <button type="button" disabled title="Available after #73">
            Inspect fields
          </button>
        </div>
      </form>
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
