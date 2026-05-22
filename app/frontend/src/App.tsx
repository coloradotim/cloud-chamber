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

export function App() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("baseline-shallow-cumulus");
  const [controls, setControls] = useState<Record<string, string | number | boolean>>({});
  const [runSizePreset, setRunSizePreset] = useState("quick_look");
  const [dryRun, setDryRun] = useState<DryRunResponse | null>(null);
  const [status, setStatus] = useState("Loading scenarios...");
  const [error, setError] = useState<string | null>(null);

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

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0],
    [scenarios, selectedScenarioId],
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
          <dd>{dryRun.report.not_a_completed_cm1_result ? "Packaged dry-run output" : "Unknown"}</dd>
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
