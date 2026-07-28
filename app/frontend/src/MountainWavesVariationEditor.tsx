import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { MountainWavesDifference, MountainWavesWorldDetail } from "./MountainWavesWorld";

type RecipeId = "dry_ridge_mechanics" | "boulder_moist_wave";

type DryRidgeControls = {
  ridge_height_m: number;
  ridge_half_width_m: number;
  cross_ridge_wind_m_s: number;
  dry_stability_n_s: number;
  wind_shear_through_10km_m_s: number;
  layered_stability: boolean;
  lower_stability_n_s: number;
  upper_stability_n_s: number;
  stability_transition_height_m: number;
  stability_transition_width_m: number;
};

type BoulderMoistControls = {
  ridge_height_m: number;
  ridge_half_width_m: number;
  flow_strength_factor: number;
  wind_offset_m_s: number;
  shear_strength_factor: number;
  lower_rh_deficit_factor: number;
  midlevel_rh_deficit_factor: number;
  dry_air_counterpart: boolean;
  lower_stability_factor: number;
  midlevel_stability_factor: number;
  upper_stability_factor: number;
};

type RecipeControls = {
  recipe_id: RecipeId;
  dry_ridge: DryRidgeControls | null;
  boulder_moist: BoulderMoistControls | null;
};

type NumericalRealization = {
  domain: string;
  grid: string;
  spacing: string;
  timestep_strategy: string;
  physics_source: string;
};

type ObservationPlan = {
  duration_seconds: number | null;
  output_cadence_seconds: number | null;
  expected_history_count: number | null;
  retained_field_inventory: string[];
};

type RunCostProfile = {
  profile_id: string;
  profile_name: string;
  role: string;
  recipe_id: string;
  numerical_realization: NumericalRealization;
  observation_plan: ObservationPlan;
  expected_runtime_min_seconds: number | null;
  expected_runtime_max_seconds: number | null;
  expected_size_min_bytes: number | null;
  expected_size_max_bytes: number | null;
  estimate_basis: "measured" | "scaled_from_measured" | "uncharacterized";
  confidence: string;
  scientific_limitations: string[];
};

type RunCostEstimate = {
  profile: RunCostProfile;
  current_free_space_bytes: number;
  projected_free_space_bytes: number | null;
  required_free_space_bytes: number | null;
  disposition: "passes" | "blocked";
  disposition_reason: string;
};

type VariationTemplate = {
  parent_simulation_id: string;
  parent_run_id: string;
  parent_display_name: string;
  parent_configuration_source: string;
  reference_simulation_id: string;
  recipe_id: RecipeId;
  recipe_name: string;
  recipe_contract_version: string;
  controls: RecipeControls;
  run_profiles: RunCostEstimate[];
  default_run_profile_id: string;
  can_create_variation: boolean;
  unavailable_reason: string | null;
};

type VariationPreview = {
  recipe_id: RecipeId;
  recipe_name: string;
  differences: Record<string, MountainWavesDifference[]>;
  relationship_classification: string | null;
  warnings: string[];
  blocking_errors: string[];
  diagnostics: {
    maximum_terrain_slope: number;
    cells_per_half_width: number;
    nondimensional_mountain_height: number;
    nonhydrostatic_width_parameter: number;
    critical_levels_m: number[];
    terrain_resolution: string;
    upstream_clearance_km: number;
    downstream_clearance_km: number;
    advective_time_seconds: number;
    periodic_wrap_time_seconds: number;
    model_top_m: number;
    damping_base_m: number;
    labels: string[];
  };
  terrain_profile: Array<{ x_m: number; height_m: number }>;
  wind_profile: Array<{ height_m: number; value: number }>;
  moisture_profile: Array<{ height_m: number; value: number }>;
  relative_humidity_profile: Array<{ height_m: number; value: number }>;
  theta_profile: Array<{ height_m: number; value: number }>;
  stability_profile: Array<{ height_m: number; n2_s2: number }>;
  numerical_realization: NumericalRealization;
  observation_plan: ObservationPlan;
  cost_estimate: RunCostEstimate;
};

type VariationPackage = {
  simulation_id: string;
  run_id: string;
  manifest_path: string;
  package_dir: string;
  launch_review_snapshot_id: string;
  warnings: string[];
};

const DIFFERENCE_GROUPS = [
  "terrain",
  "wind",
  "moisture",
  "stability/thermodynamics",
  "forcing/initiation",
  "numerical realization",
  "observation plan",
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
  const [controls, setControls] = useState<RecipeControls | null>(null);
  const [runProfileId, setRunProfileId] = useState("");
  const [simulationName, setSimulationName] = useState("");
  const [userQuestion, setUserQuestion] = useState("");
  const [preview, setPreview] = useState<VariationPreview | null>(null);
  const [packaged, setPackaged] = useState<VariationPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewing, setPreviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [queueing, setQueueing] = useState(false);
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
    setPackaged(null);
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
        setControls(cloneControls(payload.controls));
        setRunProfileId(payload.default_run_profile_id);
      })
      .catch((caught) => {
        if (!active) return;
        setTemplate(null);
        setControls(null);
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
    if (!controls || !template?.can_create_variation || !runProfileId || packaged) {
      if (!packaged) setPreview(null);
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
          requestPayload({
            parentSimulationId,
            simulationName: simulationName.trim() || "Untitled Mountain Waves variation",
            userQuestion,
            recipeId: template.recipe_id,
            runProfileId,
            controls,
          }),
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
    }, 250);
    return () => window.clearTimeout(timer);
  }, [
    controls,
    packaged,
    parentSimulationId,
    runProfileId,
    simulationName,
    template,
    userQuestion,
  ]);

  const selectedProfile = template?.run_profiles.find(
    (estimate) => estimate.profile.profile_id === runProfileId,
  );
  const differenceCount = preview
    ? Object.values(preview.differences).reduce((total, group) => total + group.length, 0)
    : 0;
  const canPackage =
    Boolean(simulationName.trim()) &&
    Boolean(preview) &&
    preview?.blocking_errors.length === 0 &&
    preview?.cost_estimate.disposition === "passes" &&
    !submitting;

  function updateDry<K extends keyof DryRidgeControls>(key: K, value: DryRidgeControls[K]) {
    setControls((current) =>
      current?.dry_ridge
        ? { ...current, dry_ridge: { ...current.dry_ridge, [key]: value } }
        : current,
    );
  }

  function updateBoulder<K extends keyof BoulderMoistControls>(
    key: K,
    value: BoulderMoistControls[K],
  ) {
    setControls((current) =>
      current?.boulder_moist
        ? { ...current, boulder_moist: { ...current.boulder_moist, [key]: value } }
        : current,
    );
  }

  function restoreParent() {
    if (!template) return;
    setControls(cloneControls(template.controls));
    setRunProfileId(template.default_run_profile_id);
    setPackaged(null);
    setStatus("Parent Recipe controls restored.");
  }

  async function packageVariation() {
    if (!controls || !template || !simulationName.trim()) return;
    setSubmitting(true);
    setError(null);
    setStatus("Writing the exact package and launch review...");
    try {
      const response = await fetch("/api/worlds/mountain-waves/variations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestPayload({
            parentSimulationId,
            simulationName: simulationName.trim(),
            userQuestion,
            recipeId: template.recipe_id,
            runProfileId,
            controls,
          }),
        ),
      });
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Unable to package this variation."));
      }
      const payload = (await response.json()) as VariationPackage;
      setPackaged(payload);
      setStatus(`${simulationName.trim()} is packaged. It has not been queued.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to package this variation.");
    } finally {
      setSubmitting(false);
    }
  }

  async function queuePackage() {
    if (!packaged) return;
    setQueueing(true);
    setError(null);
    setStatus("Running the immediate launch gate and joining the queue...");
    try {
      const response = await fetch("/api/runs/queue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifest_path: packaged.manifest_path }),
      });
      if (!response.ok) {
        throw new Error(
          await responseMessage(
            response,
            "The package remains available, but it could not be queued.",
          ),
        );
      }
      setStatus(`${simulationName.trim()} is queued as ${packaged.run_id}.`);
      await onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to queue this package.");
    } finally {
      setQueueing(false);
    }
  }

  if (loading) {
    return <section className="lab-content status-panel">Loading Recipe controls...</section>;
  }

  if (!template || !controls) {
    return (
      <section className="lab-content world-load-failure">
        <div>
          <h3>Variation controls are unavailable</h3>
          <p role="alert">{error}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="lab-content mountain-waves-variation-editor" aria-labelledby="variation-title">
      <header className="variation-editor-header">
        <div>
          <p className="eyebrow">Create Variation</p>
          <h3 id="variation-title">Design a related Mountain Waves Simulation</h3>
          <p>
            Change bounded Recipe controls, review the generated experiment, then package it before
            deciding whether to queue a CM1 attempt.
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={restoreParent}>
          Restore parent
        </button>
      </header>

      <div className="variation-editor-grid">
        <div className="variation-editor-main">
          <section className="variation-section variation-identity-section">
            <div className="variation-section-title">
              <span>1</span>
              <div>
                <h4>Simulation identity</h4>
                <p>The Recipe follows the selected parent and cannot be silently changed.</p>
              </div>
            </div>
            <div className="variation-identity-grid">
              <label>
                Parent Simulation
                <select
                  value={parentSimulationId}
                  onChange={(event) => setParentSimulationId(event.target.value)}
                  disabled={Boolean(packaged)}
                >
                  {eligibleParents.map((parent) => (
                    <option key={parent.simulation_id} value={parent.simulation_id}>
                      {parent.display_name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="variation-recipe-identity">
                <span>Recipe</span>
                <strong>{template.recipe_name}</strong>
                <small>Contract version {template.recipe_contract_version}</small>
              </div>
              <label>
                Variation name
                <input
                  value={simulationName}
                  placeholder="e.g. Broader ridge"
                  maxLength={80}
                  disabled={Boolean(packaged)}
                  onChange={(event) => setSimulationName(event.target.value)}
                />
              </label>
              <label>
                Scientific question <span className="optional-label">optional</span>
                <input
                  value={userQuestion}
                  placeholder="What are you trying to learn?"
                  disabled={Boolean(packaged)}
                  onChange={(event) => setUserQuestion(event.target.value)}
                />
              </label>
            </div>
            <p className="variation-parent-source">{template.parent_configuration_source}</p>
          </section>

          <section className="variation-section">
            <div className="variation-section-title">
              <span>2</span>
              <div>
                <h4>Atmosphere and terrain</h4>
                <p>Controls are absolute transforms against the approved Recipe reference.</p>
              </div>
            </div>
            {controls.dry_ridge ? (
              <DryControls controls={controls.dry_ridge} update={updateDry} disabled={Boolean(packaged)} />
            ) : controls.boulder_moist ? (
              <BoulderControls
                controls={controls.boulder_moist}
                update={updateBoulder}
                disabled={Boolean(packaged)}
              />
            ) : null}
            <ScientificPreview preview={preview} />
          </section>

          <section className="variation-section">
            <div className="variation-section-title">
              <span>3</span>
              <div>
                <h4>Run profile</h4>
                <p>Keep or change the numerical realization and observation plan explicitly.</p>
              </div>
            </div>
            <div className="variation-profile-options" role="radiogroup" aria-label="Run profile">
              {template.run_profiles.map((estimate) => (
                <label
                  key={estimate.profile.profile_id}
                  className={
                    runProfileId === estimate.profile.profile_id
                      ? "variation-profile-option selected"
                      : "variation-profile-option"
                  }
                >
                  <input
                    type="radio"
                    name="mountain-wave-profile"
                    value={estimate.profile.profile_id}
                    checked={runProfileId === estimate.profile.profile_id}
                    disabled={Boolean(packaged)}
                    onChange={() => setRunProfileId(estimate.profile.profile_id)}
                  />
                  <span>
                    <strong>{estimate.profile.role}</strong>
                    <small>{shortProfileName(estimate.profile.profile_name)}</small>
                  </span>
                  <span className={estimate.disposition === "passes" ? "profile-cost" : "profile-cost blocked"}>
                    {profileCost(estimate.profile)}
                  </span>
                </label>
              ))}
            </div>
            {selectedProfile && (
              <div className="variation-profile-detail">
                <div>
                  <span>Numerical realization</span>
                  <strong>{preview?.numerical_realization.grid ?? selectedProfile.profile.numerical_realization.grid}</strong>
                  <small>
                    {preview?.numerical_realization.spacing ??
                      selectedProfile.profile.numerical_realization.spacing}
                  </small>
                </div>
                <div>
                  <span>Observation plan</span>
                  <strong>
                    {formatDuration(
                      preview?.observation_plan.duration_seconds ??
                        selectedProfile.profile.observation_plan.duration_seconds,
                    )}
                  </strong>
                  <small>
                    {preview?.observation_plan.expected_history_count ??
                      selectedProfile.profile.observation_plan.expected_history_count ??
                      "Generated"}{" "}
                    saved outputs
                  </small>
                </div>
                <div>
                  <span>Expected local cost</span>
                  <strong>{profileCost(preview?.cost_estimate.profile ?? selectedProfile.profile)}</strong>
                  <small>{selectedProfile.profile.estimate_basis.replaceAll("_", " ")}</small>
                </div>
              </div>
            )}
          </section>
        </div>

        <aside className="variation-preview" aria-label="Variation review">
          <header>
            <div>
              <p className="eyebrow">Review</p>
              <h3>{previewing ? "Resolving experiment..." : `${differenceCount} material changes`}</h3>
            </div>
            {preview && preview.blocking_errors.length === 0 && (
              <span className="technical-state available">Ready to package</span>
            )}
          </header>

          {preview && (
            <>
              <section className="variation-review-summary">
                <p className="variation-relationship">
                  {relationshipLabel(preview.relationship_classification)}
                </p>
                <div className="variation-regime-labels">
                  {preview.diagnostics.labels.map((label) => (
                    <span key={label}>{label}</span>
                  ))}
                </div>
                <dl className="variation-diagnostics">
                  <div>
                    <dt>Nh/U</dt>
                    <dd>{preview.diagnostics.nondimensional_mountain_height.toFixed(2)}</dd>
                  </div>
                  <div>
                    <dt>Na/U</dt>
                    <dd>{preview.diagnostics.nonhydrostatic_width_parameter.toFixed(2)}</dd>
                  </div>
                  <div>
                    <dt>Maximum slope</dt>
                    <dd>{preview.diagnostics.maximum_terrain_slope.toFixed(2)}</dd>
                  </div>
                  <div>
                    <dt>Terrain resolution</dt>
                    <dd>{preview.diagnostics.terrain_resolution}</dd>
                  </div>
                  <div>
                    <dt>Model top</dt>
                    <dd>{formatDistance(preview.diagnostics.model_top_m)}</dd>
                  </div>
                  <div>
                    <dt>Wrap margin</dt>
                    <dd>{formatDuration(preview.diagnostics.periodic_wrap_time_seconds)}</dd>
                  </div>
                </dl>
              </section>

              {preview.blocking_errors.map((message) => (
                <p key={message} className="variation-message variation-message-blocking" role="alert">
                  {message}
                </p>
              ))}
              {preview.warnings.map((message) => (
                <p key={message} className="variation-message variation-message-warning">
                  {message}
                </p>
              ))}

              <div className="variation-difference-groups">
                {DIFFERENCE_GROUPS.map((group) => {
                  const differences = preview.differences[group] ?? [];
                  if (!differences.length) return null;
                  return (
                    <section key={group}>
                      <header>
                        <strong>{differenceGroupLabel(group)}</strong>
                        <span>{differences.length}</span>
                      </header>
                      <ul>
                        {differences.map((difference, index) => (
                          <li key={`${difference.label}-${index}`}>
                            <span>{difference.label}</span>
                            <strong>
                              {displayDifferenceValue(difference.before)} →{" "}
                              {displayDifferenceValue(difference.after)}
                              {difference.units ? ` ${difference.units}` : ""}
                            </strong>
                          </li>
                        ))}
                      </ul>
                    </section>
                  );
                })}
              </div>

              <section className="variation-budget">
                <div>
                  <span>Resolved storage</span>
                  <strong>{sizeRange(preview.cost_estimate.profile)}</strong>
                </div>
                <div>
                  <span>Free after high estimate</span>
                  <strong>{formatBytes(preview.cost_estimate.projected_free_space_bytes)}</strong>
                </div>
                <p className={preview.cost_estimate.disposition === "passes" ? "" : "blocked"}>
                  {preview.cost_estimate.disposition_reason}
                </p>
              </section>
            </>
          )}

          <div className="variation-submit">
            {!packaged ? (
              <button type="button" disabled={!canPackage} onClick={() => void packageVariation()}>
                {submitting ? "Packaging..." : "Package variation"}
              </button>
            ) : (
              <section className="variation-packaged-state">
                <p className="eyebrow">Packaged, not queued</p>
                <h4>{simulationName}</h4>
                <dl>
                  <div>
                    <dt>Simulation</dt>
                    <dd>{packaged.simulation_id}</dd>
                  </div>
                  <div>
                    <dt>Attempt</dt>
                    <dd>{packaged.run_id}</dd>
                  </div>
                </dl>
                <button type="button" disabled={queueing} onClick={() => void queuePackage()}>
                  {queueing ? "Queueing..." : "Queue CM1 run"}
                </button>
              </section>
            )}
            {!simulationName.trim() && <p>Name this variation to package it.</p>}
            {status && <p role="status">{status}</p>}
            {error && <p role="alert">{error}</p>}
          </div>
        </aside>
      </div>
    </section>
  );
}

function DryControls({
  controls,
  update,
  disabled,
}: {
  controls: DryRidgeControls;
  update: <K extends keyof DryRidgeControls>(key: K, value: DryRidgeControls[K]) => void;
  disabled: boolean;
}) {
  return (
    <>
      <div className="variation-control-groups">
        <ControlGroup title="Terrain">
          <RangeField
            label="Ridge height"
            value={controls.ridge_height_m}
            min={100}
            max={2500}
            step={50}
            units="m"
            disabled={disabled}
            onChange={(value) => update("ridge_height_m", value)}
          />
          <RangeField
            label="Ridge half-width"
            value={controls.ridge_half_width_m}
            min={500}
            max={20000}
            step={100}
            units="m"
            disabled={disabled}
            onChange={(value) => update("ridge_half_width_m", value)}
          />
        </ControlGroup>
        <ControlGroup title="Upstream flow">
          <RangeField
            label="Cross-ridge wind"
            value={controls.cross_ridge_wind_m_s}
            min={5}
            max={30}
            step={1}
            units="m/s"
            disabled={disabled}
            onChange={(value) => update("cross_ridge_wind_m_s", value)}
          />
          <RangeField
            label="Dry stability N"
            value={controls.dry_stability_n_s}
            min={0.005}
            max={0.02}
            step={0.001}
            units="s⁻¹"
            disabled={disabled || controls.layered_stability}
            onChange={(value) => update("dry_stability_n_s", value)}
          />
        </ControlGroup>
      </div>
      <details className="variation-advanced">
        <summary>Advanced vertical structure</summary>
        <div className="variation-control-groups">
          <ControlGroup title="Wind shear">
            <RangeField
              label="Change through 10 km"
              value={controls.wind_shear_through_10km_m_s}
              min={-20}
              max={20}
              step={1}
              units="m/s"
              disabled={disabled}
              onChange={(value) => update("wind_shear_through_10km_m_s", value)}
            />
          </ControlGroup>
          <ControlGroup title="Layered stability">
            <label className="variation-toggle">
              <input
                type="checkbox"
                checked={controls.layered_stability}
                disabled={disabled}
                onChange={(event) => update("layered_stability", event.target.checked)}
              />
              Use lower and upper stability layers
            </label>
            {controls.layered_stability && (
              <>
                <RangeField
                  label="Lower N"
                  value={controls.lower_stability_n_s}
                  min={0.005}
                  max={0.02}
                  step={0.001}
                  units="s⁻¹"
                  disabled={disabled}
                  onChange={(value) => update("lower_stability_n_s", value)}
                />
                <RangeField
                  label="Upper N"
                  value={controls.upper_stability_n_s}
                  min={0.005}
                  max={0.02}
                  step={0.001}
                  units="s⁻¹"
                  disabled={disabled}
                  onChange={(value) => update("upper_stability_n_s", value)}
                />
                <RangeField
                  label="Transition height"
                  value={controls.stability_transition_height_m}
                  min={2000}
                  max={12000}
                  step={500}
                  units="m"
                  disabled={disabled}
                  onChange={(value) => update("stability_transition_height_m", value)}
                />
                <RangeField
                  label="Transition width"
                  value={controls.stability_transition_width_m}
                  min={500}
                  max={3000}
                  step={250}
                  units="m"
                  disabled={disabled}
                  onChange={(value) => update("stability_transition_width_m", value)}
                />
              </>
            )}
          </ControlGroup>
        </div>
      </details>
    </>
  );
}

function BoulderControls({
  controls,
  update,
  disabled,
}: {
  controls: BoulderMoistControls;
  update: <K extends keyof BoulderMoistControls>(key: K, value: BoulderMoistControls[K]) => void;
  disabled: boolean;
}) {
  return (
    <>
      <div className="variation-control-groups">
        <ControlGroup title="Terrain">
          <RangeField
            label="Ridge height"
            value={controls.ridge_height_m}
            min={500}
            max={3500}
            step={100}
            units="m"
            disabled={disabled}
            onChange={(value) => update("ridge_height_m", value)}
          />
          <RangeField
            label="Ridge half-width"
            value={controls.ridge_half_width_m}
            min={5000}
            max={30000}
            step={500}
            units="m"
            disabled={disabled}
            onChange={(value) => update("ridge_half_width_m", value)}
          />
        </ControlGroup>
        <ControlGroup title="Wind">
          <RangeField
            label="Flow strength"
            value={controls.flow_strength_factor}
            min={0.5}
            max={1.5}
            step={0.05}
            units="×"
            disabled={disabled}
            onChange={(value) => update("flow_strength_factor", value)}
          />
          <RangeField
            label="Wind offset"
            value={controls.wind_offset_m_s}
            min={-10}
            max={10}
            step={1}
            units="m/s"
            disabled={disabled}
            onChange={(value) => update("wind_offset_m_s", value)}
          />
          <RangeField
            label="Shear strength"
            value={controls.shear_strength_factor}
            min={0.5}
            max={1.5}
            step={0.05}
            units="×"
            disabled={disabled}
            onChange={(value) => update("shear_strength_factor", value)}
          />
        </ControlGroup>
        <ControlGroup title="Moisture">
          <RangeField
            label="Lower RH deficit"
            value={controls.lower_rh_deficit_factor}
            min={0}
            max={2}
            step={0.1}
            units="×"
            disabled={disabled || controls.dry_air_counterpart}
            onChange={(value) => update("lower_rh_deficit_factor", value)}
          />
          <RangeField
            label="Midlevel RH deficit"
            value={controls.midlevel_rh_deficit_factor}
            min={0}
            max={2}
            step={0.1}
            units="×"
            disabled={disabled || controls.dry_air_counterpart}
            onChange={(value) => update("midlevel_rh_deficit_factor", value)}
          />
          <label className="variation-toggle">
            <input
              type="checkbox"
              checked={controls.dry_air_counterpart}
              disabled={disabled}
              onChange={(event) => update("dry_air_counterpart", event.target.checked)}
            />
            Boulder dry-air counterpart
          </label>
        </ControlGroup>
      </div>
      <details className="variation-advanced">
        <summary>Advanced stability structure</summary>
        <div className="variation-control-groups three-up">
          {(
            [
              ["lower_stability_factor", "Lower layer"],
              ["midlevel_stability_factor", "Midlevel"],
              ["upper_stability_factor", "Upper layer"],
            ] as const
          ).map(([key, label]) => (
            <RangeField
              key={key}
              label={label}
              value={controls[key]}
              min={0.5}
              max={1.5}
              step={0.05}
              units="×"
              disabled={disabled}
              onChange={(value) => update(key, value)}
            />
          ))}
        </div>
      </details>
    </>
  );
}

function ControlGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="variation-control-group">
      <h5>{title}</h5>
      {children}
    </section>
  );
}

function RangeField({
  label,
  value,
  min,
  max,
  step,
  units,
  disabled,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  units: string;
  disabled: boolean;
  onChange: (value: number) => void;
}) {
  return (
    <label className="variation-range-field">
      <span>
        <strong>{label}</strong>
        <output>
          {formatControlValue(value, step)} {units}
        </output>
      </span>
      <input
        aria-label={label}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.valueAsNumber)}
      />
      <small>
        {formatControlValue(min, step)} to {formatControlValue(max, step)} {units}
      </small>
    </label>
  );
}

function ScientificPreview({ preview }: { preview: VariationPreview | null }) {
  if (!preview) return <div className="scientific-preview-placeholder" />;
  return (
    <section className="variation-scientific-preview" aria-labelledby="scientific-preview-title">
      <header>
        <div>
          <h5 id="scientific-preview-title">Resolved scientific profiles</h5>
          <p>Complete generated atmosphere; height is shown in km.</p>
        </div>
        <span>{preview.recipe_name}</span>
      </header>
      <TerrainPreview profile={preview.terrain_profile} />
      <div className="variation-atmosphere-profiles">
        <VerticalProfilePlot
          label="Cross-ridge wind"
          symbol="u"
          units="m/s"
          profile={preview.wind_profile}
          includeZero
        />
        <VerticalProfilePlot
          label="Relative humidity"
          symbol="RH"
          units="%"
          profile={preview.relative_humidity_profile ?? []}
          domain={[0, 100]}
        />
        <VerticalProfilePlot
          label="Water vapor"
          symbol="qv"
          units="g/kg"
          profile={preview.moisture_profile}
          domain={[
            0,
            Math.max(...preview.moisture_profile.map((point) => point.value), 1),
          ]}
        />
        <VerticalProfilePlot
          label="Potential temperature"
          symbol="θ"
          units="K"
          profile={preview.theta_profile ?? []}
        />
        <VerticalProfilePlot
          label="Static stability"
          symbol="N"
          units="s⁻¹"
          profile={preview.stability_profile.map((point) => ({
            height_m: point.height_m,
            value: Math.sqrt(Math.max(point.n2_s2, 0)),
          }))}
          includeZero
        />
      </div>
    </section>
  );
}

function TerrainPreview({ profile }: { profile: Array<{ x_m: number; height_m: number }> }) {
  if (!profile.length) return <div className="terrain-preview-placeholder" />;
  const width = 720;
  const height = 112;
  const maximum = Math.max(...profile.map((point) => point.height_m), 1);
  const path = profile
    .map((point, index) => {
      const x = (index / (profile.length - 1)) * width;
      const y = height - 12 - (point.height_m / maximum) * (height - 28);
      return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <figure className="variation-terrain-preview">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Generated terrain profile">
        <path d={`${path} L${width},${height - 10} L0,${height - 10} Z`} />
        <line x1="0" y1={height - 10} x2={width} y2={height - 10} />
      </svg>
      <figcaption>Generated ridge placement and domain extent</figcaption>
    </figure>
  );
}

function VerticalProfilePlot({
  label,
  symbol,
  units,
  profile,
  domain,
  includeZero = false,
}: {
  label: string;
  symbol: string;
  units: string;
  profile: Array<{ height_m: number; value: number }>;
  domain?: [number, number];
  includeZero?: boolean;
}) {
  if (!profile.length) {
    return (
      <figure className="variation-profile-plot profile-unavailable">
        <figcaption>
          <strong>{label}</strong>
          <span>
            {symbol} ({units})
          </span>
        </figcaption>
        <p>Profile unavailable</p>
      </figure>
    );
  }
  const width = 160;
  const height = 190;
  const plot = { left: 28, right: 9, top: 10, bottom: 35 };
  const values = profile.map((point) => point.value);
  const heights = profile.map((point) => point.height_m);
  const rawMinimum = domain?.[0] ?? Math.min(...values, includeZero ? 0 : Number.POSITIVE_INFINITY);
  const rawMaximum = domain?.[1] ?? Math.max(...values, includeZero ? 0 : Number.NEGATIVE_INFINITY);
  const valuePadding = rawMaximum === rawMinimum ? Math.max(Math.abs(rawMaximum) * 0.08, 1) : 0;
  const minimum = rawMinimum - valuePadding;
  const maximum = rawMaximum + valuePadding;
  const maximumHeight = Math.max(...heights, 1);
  const x = (value: number) =>
    plot.left +
    ((value - minimum) / Math.max(maximum - minimum, Number.EPSILON)) *
      (width - plot.left - plot.right);
  const y = (heightM: number) =>
    height -
    plot.bottom -
    (heightM / maximumHeight) * (height - plot.top - plot.bottom);
  const path = profile
    .map((point, index) => `${index ? "L" : "M"}${x(point.value).toFixed(1)},${y(point.height_m).toFixed(1)}`)
    .join(" ");
  const zeroX = minimum <= 0 && maximum >= 0 ? x(0) : null;

  return (
    <figure className="variation-profile-plot">
      <figcaption>
        <strong>{label}</strong>
        <span>
          {symbol} ({units})
        </span>
      </figcaption>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${label} profile from ${formatProfileValue(minimum)} to ${formatProfileValue(maximum)} ${units}`}
      >
        <line className="profile-axis" x1={plot.left} y1={plot.top} x2={plot.left} y2={height - plot.bottom} />
        <line
          className="profile-axis"
          x1={plot.left}
          y1={height - plot.bottom}
          x2={width - plot.right}
          y2={height - plot.bottom}
        />
        {zeroX !== null ? (
          <line
            className="profile-zero"
            x1={zeroX}
            y1={plot.top}
            x2={zeroX}
            y2={height - plot.bottom}
          />
        ) : null}
        <path className="profile-line" d={path} />
        <text x={plot.left - 5} y={plot.top + 4} textAnchor="end">
          {(maximumHeight / 1000).toFixed(maximumHeight >= 10_000 ? 0 : 1)}
        </text>
        <text x={plot.left - 5} y={height - plot.bottom + 4} textAnchor="end">
          0
        </text>
        <text x={plot.left} y={height - 12} textAnchor="start">
          {formatProfileValue(minimum)}
        </text>
        <text x={width - plot.right} y={height - 12} textAnchor="end">
          {formatProfileValue(maximum)}
        </text>
      </svg>
    </figure>
  );
}

function requestPayload({
  parentSimulationId,
  simulationName,
  userQuestion,
  recipeId,
  runProfileId,
  controls,
}: {
  parentSimulationId: string;
  simulationName: string;
  userQuestion: string;
  recipeId: RecipeId;
  runProfileId: string;
  controls: RecipeControls;
}) {
  return {
    parent_simulation_id: parentSimulationId,
    simulation_name: simulationName,
    user_question: userQuestion.trim() || null,
    recipe_id: recipeId,
    run_profile_id: runProfileId,
    controls,
  };
}

function cloneControls(controls: RecipeControls): RecipeControls {
  return {
    ...controls,
    dry_ridge: controls.dry_ridge ? { ...controls.dry_ridge } : null,
    boulder_moist: controls.boulder_moist ? { ...controls.boulder_moist } : null,
  };
}

function shortProfileName(value: string) {
  return value.split("—")[1]?.trim() ?? value;
}

function profileCost(profile: RunCostProfile) {
  if (
    profile.expected_runtime_min_seconds === null ||
    profile.expected_runtime_max_seconds === null ||
    profile.expected_size_min_bytes === null ||
    profile.expected_size_max_bytes === null
  ) {
    return "Not characterized";
  }
  return `${durationRange(profile.expected_runtime_min_seconds, profile.expected_runtime_max_seconds)} · ${sizeRange(profile)}`;
}

function durationRange(minimum: number, maximum: number) {
  return minimum === maximum
    ? formatDuration(minimum)
    : `${formatDuration(minimum)}–${formatDuration(maximum)}`;
}

function sizeRange(profile: RunCostProfile) {
  if (profile.expected_size_min_bytes === null || profile.expected_size_max_bytes === null) {
    return "Not characterized";
  }
  return `${formatBytes(profile.expected_size_min_bytes)}–${formatBytes(profile.expected_size_max_bytes)}`;
}

function formatBytes(value: number | null) {
  if (value === null) return "Unknown";
  const gib = value / 1024 ** 3;
  if (gib >= 1) return `${gib.toFixed(gib >= 10 ? 0 : 2)} GB`;
  return `${Math.round(value / 1024 ** 2)} MB`;
}

function formatDuration(value: number | null) {
  if (value === null) return "Generated";
  if (value >= 3600) {
    const hours = Math.floor(value / 3600);
    const minutes = Math.round((value % 3600) / 60);
    return minutes ? `${hours} h ${minutes} min` : `${hours} h`;
  }
  if (value >= 60) return `${Math.round(value / 60)} min`;
  return `${Math.round(value)} s`;
}

function formatDistance(value: number) {
  return value >= 1000 ? `${(value / 1000).toFixed(1)} km` : `${Math.round(value)} m`;
}

function formatControlValue(value: number, step: number) {
  if (step >= 1) return value.toLocaleString();
  const digits = Math.max(1, Math.min(3, Math.ceil(-Math.log10(step))));
  return value.toFixed(digits);
}

function relationshipLabel(value: string | null) {
  if (!value) return "Change at least one control.";
  return value.replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase());
}

function differenceGroupLabel(group: string) {
  return group.replace(/(^|[ /])\w/g, (value) => value.toUpperCase());
}

function displayDifferenceValue(value: unknown) {
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toLocaleString() : Number(value.toPrecision(4)).toString();
  }
  if (typeof value === "boolean") return value ? "On" : "Off";
  if (value === null || value === undefined) return "Unknown";
  const text = String(value);
  const profile = text.match(/^mountain_waves_(?:dry|boulder)_(quick|standard|presentation|extended)_v1$/);
  if (profile) {
    return `${profile[1][0].toUpperCase()}${profile[1].slice(1)} profile`;
  }
  return text.replaceAll("_", " ");
}

function formatProfileValue(value: number) {
  const magnitude = Math.abs(value);
  if (magnitude > 0 && magnitude < 0.1) return value.toFixed(3);
  if (magnitude >= 100) return Math.round(value).toLocaleString();
  return Number(value.toPrecision(3)).toString();
}

async function responseMessage(response: Response, fallback: string) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || fallback;
  } catch {
    return fallback;
  }
}
