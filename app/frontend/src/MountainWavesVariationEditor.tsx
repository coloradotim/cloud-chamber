import { useEffect, useMemo, useRef, useState } from "react";

import type { MountainWavesDifference, MountainWavesWorldDetail } from "./MountainWavesWorld";

type TerrainConfiguration = {
  height_m: number;
  half_width_m: number;
  center_m: number;
};

type SoundingLevel = {
  height_m: number;
  pressure_pa: number;
  theta_k: number;
  qv_g_kg: number;
  u_m_s: number;
  v_m_s: number;
};

type MountainWavesConfiguration = {
  terrain: TerrainConfiguration;
  sounding: SoundingLevel[];
  duration_seconds: number;
  output_cadence_seconds: number;
};

type VariationTemplate = {
  parent_simulation_id: string;
  parent_run_id: string;
  parent_display_name: string;
  parent_configuration_source: string;
  reference_simulation_id: string;
  configuration: MountainWavesConfiguration;
  can_create_variation: boolean;
  unavailable_reason: string | null;
};

type VariationPreview = {
  differences: Record<string, MountainWavesDifference[]>;
  warnings: string[];
  blocking_errors: string[];
  derived_stability_n2_s2: number[];
  terrain_profile: Array<{ x_m: number; height_m: number }>;
};

type VariationPackage = {
  simulation_id: string;
  run_id: string;
  manifest_path: string;
  package_dir: string;
  warnings: string[];
};

const DIFFERENCE_GROUPS = [
  "terrain",
  "wind",
  "moisture",
  "stability/thermodynamics",
  "numerics/time",
  "output",
] as const;

export function MountainWavesVariationEditor({
  world,
  initialParentSimulationId,
  onCreated,
}: {
  world: MountainWavesWorldDetail;
  initialParentSimulationId: string;
  onCreated: () => Promise<void> | void;
}) {
  const eligibleParents = useMemo(
    () => world.simulations.filter((simulation) => simulation.can_create_variation),
    [world.simulations],
  );
  const [parentSimulationId, setParentSimulationId] = useState(initialParentSimulationId);
  const [template, setTemplate] = useState<VariationTemplate | null>(null);
  const [configuration, setConfiguration] = useState<MountainWavesConfiguration | null>(null);
  const [simulationName, setSimulationName] = useState("");
  const [userQuestion, setUserQuestion] = useState("");
  const [windMultiplier, setWindMultiplier] = useState(1);
  const [windOffset, setWindOffset] = useState(0);
  const [moistureMultiplier, setMoistureMultiplier] = useState(1);
  const [preview, setPreview] = useState<VariationPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewing, setPreviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const previewSequence = useRef(0);

  useEffect(() => {
    setParentSimulationId(initialParentSimulationId);
  }, [initialParentSimulationId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setStatus(null);
    void fetch(
      `/api/worlds/mountain-waves/variation-template?${new URLSearchParams({
        parent_simulation_id: parentSimulationId,
      })}`,
    )
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(await responseMessage(response, "Unable to load the parent Simulation."));
        }
        return (await response.json()) as VariationTemplate;
      })
      .then((payload) => {
        if (!active) return;
        setTemplate(payload);
        setConfiguration(cloneConfiguration(payload.configuration));
        setWindMultiplier(1);
        setWindOffset(0);
        setMoistureMultiplier(1);
      })
      .catch((caught) => {
        if (!active) return;
        setTemplate(null);
        setConfiguration(null);
        setError(
          caught instanceof Error ? caught.message : "Unable to load the parent Simulation.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [parentSimulationId]);

  useEffect(() => {
    if (!configuration || !template?.can_create_variation) {
      setPreview(null);
      return;
    }
    const sequence = previewSequence.current + 1;
    previewSequence.current = sequence;
    const timer = window.setTimeout(() => {
      setPreviewing(true);
      void fetch("/api/worlds/mountain-waves/variations/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestPayload(
            parentSimulationId,
            simulationName.trim() || "Untitled Mountain Waves variation",
            userQuestion,
            configuration,
          ),
        ),
      })
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(await responseMessage(response, "Unable to preview this variation."));
          }
          return (await response.json()) as VariationPreview;
        })
        .then((payload) => {
          if (sequence === previewSequence.current) {
            setPreview(payload);
            setError(null);
          }
        })
        .catch((caught) => {
          if (sequence === previewSequence.current) {
            setPreview(null);
            setError(
              caught instanceof Error ? caught.message : "Unable to preview this variation.",
            );
          }
        })
        .finally(() => {
          if (sequence === previewSequence.current) setPreviewing(false);
        });
    }, 300);
    return () => window.clearTimeout(timer);
  }, [configuration, parentSimulationId, simulationName, template, userQuestion]);

  function updateTerrain(field: keyof TerrainConfiguration, value: number) {
    setConfiguration((current) =>
      current ? { ...current, terrain: { ...current.terrain, [field]: value } } : current,
    );
  }

  function updateLevel(index: number, field: "u_m_s" | "qv_g_kg" | "theta_k", value: number) {
    setConfiguration((current) => {
      if (!current) return current;
      const sounding = current.sounding.map((level, levelIndex) =>
        levelIndex === index ? { ...level, [field]: value } : level,
      );
      return { ...current, sounding };
    });
  }

  function applyWindTransform() {
    if (!template) return;
    setConfiguration((current) =>
      current
        ? {
            ...current,
            sounding: current.sounding.map((level, index) => ({
              ...level,
              u_m_s: template.configuration.sounding[index].u_m_s * windMultiplier + windOffset,
            })),
          }
        : current,
    );
  }

  function applyMoistureTransform(multiplier: number) {
    if (!template) return;
    setMoistureMultiplier(multiplier);
    setConfiguration((current) =>
      current
        ? {
            ...current,
            sounding: current.sounding.map((level, index) => ({
              ...level,
              qv_g_kg: template.configuration.sounding[index].qv_g_kg * multiplier,
            })),
          }
        : current,
    );
  }

  function restoreParent() {
    if (!template) return;
    setConfiguration(cloneConfiguration(template.configuration));
    setWindMultiplier(1);
    setWindOffset(0);
    setMoistureMultiplier(1);
    setStatus("Parent configuration restored.");
  }

  async function createAndQueue() {
    if (!configuration || !simulationName.trim()) return;
    setSubmitting(true);
    setError(null);
    setStatus("Packaging the variation...");
    try {
      const packageResponse = await fetch("/api/worlds/mountain-waves/variations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestPayload(parentSimulationId, simulationName.trim(), userQuestion, configuration),
        ),
      });
      if (!packageResponse.ok) {
        throw new Error(
          await responseMessage(packageResponse, "Unable to package this variation."),
        );
      }
      const packageResult = (await packageResponse.json()) as VariationPackage;
      setStatus(`Queueing ${simulationName.trim()}...`);
      const queueResponse = await fetch("/api/runs/queue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifest_path: packageResult.manifest_path }),
      });
      if (!queueResponse.ok) {
        throw new Error(
          await responseMessage(
            queueResponse,
            `The package was created, but ${simulationName.trim()} could not be queued.`,
          ),
        );
      }
      setStatus(`${simulationName.trim()} is queued as ${packageResult.run_id}.`);
      await onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create this variation.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <section className="lab-content status-panel">Loading parent configuration...</section>;
  }

  if (!configuration || !template) {
    return (
      <section className="lab-content world-load-failure">
        <h3>Variation editor unavailable</h3>
        <p role="alert">{error}</p>
      </section>
    );
  }

  const differenceCount = preview
    ? Object.values(preview.differences).reduce(
        (total, differences) => total + differences.length,
        0,
      )
    : 0;
  const maximumN2 = preview?.derived_stability_n2_s2.length
    ? Math.max(...preview.derived_stability_n2_s2)
    : null;
  const minimumN2 = preview?.derived_stability_n2_s2.length
    ? Math.min(...preview.derived_stability_n2_s2)
    : null;
  const canSubmit =
    template.can_create_variation &&
    Boolean(simulationName.trim()) &&
    !previewing &&
    !submitting &&
    Boolean(preview) &&
    preview!.blocking_errors.length === 0;

  return (
    <section
      className="lab-content mountain-waves-variation-editor"
      aria-labelledby="variation-title"
    >
      <header className="variation-editor-header">
        <div>
          <p className="eyebrow">Create Variation</p>
          <h3 id="variation-title">Change the terrain or upstream atmosphere</h3>
          <p>
            Start from an inspectable Simulation. Every native sounding level and exact change is
            retained with the new run.
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={restoreParent}>
          Restore parent
        </button>
      </header>

      <div className="variation-editor-grid">
        <div className="variation-editor-main">
          <fieldset className="variation-section variation-identity-section">
            <legend>Experiment</legend>
            <label>
              Parent Simulation
              <select
                value={parentSimulationId}
                onChange={(event) => setParentSimulationId(event.target.value)}
              >
                {eligibleParents.map((parent) => (
                  <option key={parent.simulation_id} value={parent.simulation_id}>
                    {parent.display_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Variation name
              <input
                value={simulationName}
                placeholder="e.g. Broader ridge, stronger wind"
                onChange={(event) => setSimulationName(event.target.value)}
              />
            </label>
            <label className="variation-question-field">
              Question <span>optional</span>
              <input
                value={userQuestion}
                placeholder="What are you trying to learn?"
                onChange={(event) => setUserQuestion(event.target.value)}
              />
            </label>
            <p className="variation-parent-source">
              Parent source: {template.parent_configuration_source.replaceAll("_", " ")}
            </p>
          </fieldset>

          <div className="variation-physical-grid">
            <fieldset className="variation-section">
              <legend>Terrain</legend>
              <div className="compact-field-grid">
                <NumberField
                  label="Height"
                  value={configuration.terrain.height_m}
                  units="m"
                  step={50}
                  onChange={(value) => updateTerrain("height_m", value)}
                />
                <NumberField
                  label="Half-width"
                  value={configuration.terrain.half_width_m}
                  units="m"
                  step={100}
                  onChange={(value) => updateTerrain("half_width_m", value)}
                />
                <NumberField
                  label="Center"
                  value={configuration.terrain.center_m}
                  units="m"
                  step={100}
                  onChange={(value) => updateTerrain("center_m", value)}
                />
              </div>
              <TerrainPreview profile={preview?.terrain_profile ?? []} />
            </fieldset>

            <fieldset className="variation-section variation-profile-transforms">
              <legend>Upstream profile</legend>
              <div className="profile-transform-row">
                <NumberField
                  label="Wind multiplier"
                  value={windMultiplier}
                  step={0.1}
                  onChange={setWindMultiplier}
                />
                <NumberField
                  label="Wind offset"
                  value={windOffset}
                  units="m/s"
                  step={1}
                  onChange={setWindOffset}
                />
                <button type="button" className="secondary-button" onClick={applyWindTransform}>
                  Apply wind
                </button>
              </div>
              <div className="profile-transform-row moisture-transform-row">
                <NumberField
                  label="Moisture multiplier"
                  value={moistureMultiplier}
                  step={0.1}
                  onChange={setMoistureMultiplier}
                />
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => applyMoistureTransform(moistureMultiplier)}
                >
                  Apply moisture
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => applyMoistureTransform(0)}
                >
                  Make dry
                </button>
              </div>
              <p className="control-help">
                Quick transforms start from the parent profile. Individual levels remain editable
                below.
              </p>
              <div className="stability-summary" aria-label="Derived stability summary">
                <span>Derived N²</span>
                <strong>
                  {minimumN2 === null || maximumN2 === null
                    ? "Previewing..."
                    : `${formatScientific(minimumN2)} to ${formatScientific(maximumN2)} s⁻²`}
                </strong>
              </div>
            </fieldset>
          </div>

          <fieldset className="variation-section variation-time-section">
            <legend>Time and output</legend>
            <NumberField
              label="Duration"
              value={configuration.duration_seconds}
              units="s"
              step={300}
              onChange={(value) =>
                setConfiguration((current) =>
                  current ? { ...current, duration_seconds: value } : current,
                )
              }
            />
            <NumberField
              label="Saved-output cadence"
              value={configuration.output_cadence_seconds}
              units="s"
              step={30}
              onChange={(value) =>
                setConfiguration((current) =>
                  current ? { ...current, output_cadence_seconds: value } : current,
                )
              }
            />
            <span className="variation-output-count">
              {Math.floor(configuration.duration_seconds / configuration.output_cadence_seconds) +
                1}{" "}
              saved frames
            </span>
          </fieldset>

          <details className="variation-advanced">
            <summary>Advanced sounding levels ({configuration.sounding.length})</summary>
            <p>
              Edit the exact cross-ridge wind, water vapor, or potential temperature at native
              sounding levels. Heights and pressure remain tied to the parent grid.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Height (m)</th>
                  <th>Pressure (Pa)</th>
                  <th>u (m/s)</th>
                  <th>qv (g/kg)</th>
                  <th>Theta (K)</th>
                </tr>
              </thead>
              <tbody>
                {configuration.sounding.map((level, index) => (
                  <tr key={level.height_m}>
                    <td>{formatNumber(level.height_m)}</td>
                    <td>{formatNumber(level.pressure_pa)}</td>
                    <td>
                      <input
                        aria-label={`u at ${level.height_m} m`}
                        type="number"
                        step="0.1"
                        value={level.u_m_s}
                        onChange={(event) =>
                          updateLevel(index, "u_m_s", event.currentTarget.valueAsNumber)
                        }
                      />
                    </td>
                    <td>
                      <input
                        aria-label={`Water vapor at ${level.height_m} m`}
                        type="number"
                        step="0.01"
                        min="0"
                        value={level.qv_g_kg}
                        onChange={(event) =>
                          updateLevel(index, "qv_g_kg", event.currentTarget.valueAsNumber)
                        }
                      />
                    </td>
                    <td>
                      <input
                        aria-label={`Potential temperature at ${level.height_m} m`}
                        type="number"
                        step="0.1"
                        value={level.theta_k}
                        onChange={(event) =>
                          updateLevel(index, "theta_k", event.currentTarget.valueAsNumber)
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>

        <aside className="variation-preview" aria-label="Variation preview">
          <header>
            <div>
              <p className="eyebrow">Change summary</p>
              <h3>
                {previewing
                  ? "Updating..."
                  : `${differenceCount} exact ${differenceCount === 1 ? "change" : "changes"}`}
              </h3>
            </div>
            {preview && preview.blocking_errors.length === 0 && (
              <span className="technical-state available">Ready</span>
            )}
          </header>

          {preview?.blocking_errors.map((message) => (
            <p key={message} className="variation-message variation-message-blocking" role="alert">
              {message}
            </p>
          ))}
          {preview?.warnings.map((message) => (
            <p key={message} className="variation-message variation-message-warning">
              {message}
            </p>
          ))}

          <div className="variation-difference-groups">
            {DIFFERENCE_GROUPS.map((group) => {
              const differences = preview?.differences[group] ?? [];
              return (
                <section key={group}>
                  <header>
                    <strong>{differenceGroupLabel(group)}</strong>
                    <span>{differences.length}</span>
                  </header>
                  {differences.length ? (
                    <ul>
                      {differences.slice(0, 8).map((difference, index) => (
                        <li key={`${difference.label}-${index}`}>
                          <span>{difference.label}</span>
                          <strong>
                            {displayDifferenceValue(difference.before)} →{" "}
                            {displayDifferenceValue(difference.after)}
                            {difference.units ? ` ${difference.units}` : ""}
                          </strong>
                        </li>
                      ))}
                      {differences.length > 8 && (
                        <li>+ {differences.length - 8} more native levels</li>
                      )}
                    </ul>
                  ) : (
                    <p>Unchanged</p>
                  )}
                </section>
              );
            })}
          </div>

          <div className="variation-submit">
            <button type="button" disabled={!canSubmit} onClick={() => void createAndQueue()}>
              {submitting ? "Creating..." : "Create and queue"}
            </button>
            {!simulationName.trim() && <p>Name this variation to create it.</p>}
            {status && <p role="status">{status}</p>}
            {error && <p role="alert">{error}</p>}
          </div>
        </aside>
      </div>
    </section>
  );
}

function NumberField({
  label,
  value,
  units,
  step,
  onChange,
}: {
  label: string;
  value: number;
  units?: string;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="number-field">
      <span>{label}</span>
      <span className="number-input-wrap">
        <input
          aria-label={label}
          type="number"
          value={value}
          step={step}
          onChange={(event) => onChange(event.currentTarget.valueAsNumber)}
        />
        {units && <small>{units}</small>}
      </span>
    </label>
  );
}

function TerrainPreview({ profile }: { profile: Array<{ x_m: number; height_m: number }> }) {
  if (!profile.length) return <div className="terrain-preview-placeholder" />;
  const width = 420;
  const height = 102;
  const maximum = Math.max(...profile.map((point) => point.height_m), 1);
  const path = profile
    .map((point, index) => {
      const x = (index / (profile.length - 1)) * width;
      const y = height - 12 - (point.height_m / maximum) * (height - 24);
      return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg
      className="terrain-preview-svg"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Terrain profile preview"
    >
      <path d={`${path} L${width},${height - 10} L0,${height - 10} Z`} />
      <line x1="0" y1={height - 10} x2={width} y2={height - 10} />
    </svg>
  );
}

function requestPayload(
  parentSimulationId: string,
  simulationName: string,
  userQuestion: string,
  configuration: MountainWavesConfiguration,
) {
  return {
    parent_simulation_id: parentSimulationId,
    simulation_name: simulationName,
    user_question: userQuestion.trim() || null,
    configuration,
  };
}

function cloneConfiguration(configuration: MountainWavesConfiguration): MountainWavesConfiguration {
  return {
    ...configuration,
    terrain: { ...configuration.terrain },
    sounding: configuration.sounding.map((level) => ({ ...level })),
  };
}

function differenceGroupLabel(group: (typeof DIFFERENCE_GROUPS)[number]): string {
  return {
    terrain: "Terrain",
    wind: "Wind",
    moisture: "Moisture",
    "stability/thermodynamics": "Stability and thermodynamics",
    "numerics/time": "Time",
    output: "Output",
  }[group];
}

function displayDifferenceValue(value: unknown): string {
  return typeof value === "number" ? formatNumber(value) : String(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 }).format(value);
}

function formatScientific(value: number): string {
  return value.toExponential(2);
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
