import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { SupercellsWorldDetail } from "./SupercellsWorld";
import "./SupercellsVariationEditor.css";

type HodographFamily = "straight" | "quarter_circle" | "half_circle";
type BuoyancyDistribution = "low_level_weighted" | "reference" | "deep_weighted";

type SupercellsControls = {
  hodograph_family: HodographFamily;
  shear_0_6_km_m_s: number;
  shear_0_2_km_m_s: number;
  turning_depth_km_agl: number;
  shear_6_12_km_m_s: number;
  upper_shear_direction_relative_deg: number;
  mean_wind_0_6_km_speed_m_s: number;
  mean_wind_0_6_km_direction_deg: number;
  surface_based_cape_j_kg: number;
  buoyancy_distribution: BuoyancyDistribution;
  lcl_height_m_agl: number;
  midlevel_rh_percent: number;
  cin_j_kg: number;
  thermal_perturbation_amplitude_k: number;
  thermal_horizontal_radius_km: number;
  thermal_vertical_radius_km: number;
  thermal_center_height_km_agl: number;
  thermal_center_x_km: number;
  thermal_center_y_km: number;
};

type NumericalRealization = {
  domain: string;
  grid: string;
  spacing: string;
  timestep_strategy: string;
  physics_source: string;
  exact_domain: {
    nx: number;
    ny: number;
    nz: number;
    dx_m: number;
    dy_m: number;
    dz_m: number;
    x_min_m: number;
    x_max_m: number;
    y_min_m: number;
    y_max_m: number;
    model_top_m: number;
    timestep_seconds: number;
  } | null;
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
  recipe_id: string;
  recipe_name: string;
  recipe_contract_version: string;
  controls: SupercellsControls;
  reference_controls: SupercellsControls;
  run_profiles: RunCostEstimate[];
  default_run_profile_id: string;
  can_create_variation: boolean;
  unavailable_reason: string | null;
};

type Difference = {
  path: string;
  label: string;
  before: unknown;
  after: unknown;
  units: string | null;
};

type ProfileLevel = {
  height_m: number;
  pressure_pa: number;
  theta_k: number;
  temperature_k: number;
  qv_g_kg: number;
  relative_humidity_percent: number;
  parcel_temperature_k: number;
  parcel_buoyancy_m_s2: number;
  u_m_s: number;
  v_m_s: number;
};

type VariationPreview = {
  reference_controls: Record<string, unknown>;
  parent_controls: Record<string, unknown>;
  requested_controls: Record<string, unknown>;
  achieved_controls: Record<string, unknown>;
  differences: Record<string, Difference[]>;
  relationship_classification: string | null;
  warnings: string[];
  blocking_errors: string[];
  diagnostics: {
    achieved_cape_j_kg: number;
    achieved_cin_j_kg: number;
    achieved_lcl_height_m_agl: number;
    achieved_midlevel_rh_percent: number;
    freezing_level_m_agl: number | null;
    hydrostatic_residual_pa: number;
    shear_0_1_km_m_s: number;
    shear_0_2_km_m_s: number;
    shear_0_3_km_m_s: number;
    shear_0_6_km_m_s: number;
    shear_6_12_km_m_s: number;
    mean_wind_0_6_km_speed_m_s: number;
    mean_wind_0_6_km_direction_deg: number;
    storm_relative_helicity_0_1_km_m2_s2: number;
    storm_relative_helicity_0_3_km_m2_s2: number;
    model_translation_u_m_s: number;
    model_translation_v_m_s: number;
    minimum_boundary_clearance_km: number;
    minimum_vertical_clearance_km: number;
    labels: string[];
  };
  sounding: ProfileLevel[];
  hodograph: Array<{ height_m: number; u_m_s: number; v_m_s: number }>;
  initiation: Record<string, number>;
  numerical_realization: NumericalRealization;
  observation_plan: ObservationPlan;
  useful_window_end_seconds: number;
  cost_estimate: RunCostEstimate;
};

type VariationPackage = {
  simulation_id: string;
  run_id: string;
  manifest_path: string;
  launch_review_snapshot_id: string;
};

export function SupercellsVariationEditor({
  world,
  initialParentSimulationId,
  onCreated,
}: {
  world: SupercellsWorldDetail;
  initialParentSimulationId: string;
  onCreated: () => Promise<void> | void;
}) {
  const eligibleParents = useMemo(
    () => world.simulations.filter((simulation) => simulation.can_create_variation),
    [world.simulations],
  );
  const [parentSimulationId, setParentSimulationId] = useState(initialParentSimulationId);
  const [template, setTemplate] = useState<VariationTemplate | null>(null);
  const [controls, setControls] = useState<SupercellsControls | null>(null);
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

  useEffect(() => setParentSimulationId(initialParentSimulationId), [initialParentSimulationId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setStatus(null);
    setPackaged(null);
    void fetch(
      `/api/worlds/supercells/variation-template?${new URLSearchParams({
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
        setControls({ ...payload.controls });
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
      void fetch("/api/worlds/supercells/variations/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestPayload({
            parentSimulationId,
            simulationName: simulationName.trim() || "Untitled Supercells variation",
            userQuestion,
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
          if (sequence !== previewSequence.current) return;
          setPreview(payload);
          setError(null);
        })
        .catch((caught) => {
          if (sequence !== previewSequence.current) return;
          setPreview(null);
          setError(caught instanceof Error ? caught.message : "Unable to preview this variation.");
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

  function update<K extends keyof SupercellsControls>(key: K, value: SupercellsControls[K]) {
    setControls((current) => (current ? { ...current, [key]: value } : current));
  }

  function restoreParent() {
    if (!template) return;
    setControls({ ...template.controls });
    setRunProfileId(template.default_run_profile_id);
    setPackaged(null);
    setStatus("Parent controls and run profile restored.");
  }

  async function packageVariation() {
    if (!controls || !simulationName.trim()) return;
    setSubmitting(true);
    setError(null);
    setStatus("Writing the exact package and launch review...");
    try {
      const response = await fetch("/api/worlds/supercells/variations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestPayload({
            parentSimulationId,
            simulationName: simulationName.trim(),
            userQuestion,
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
    <section className="lab-content supercells-variation-editor" aria-labelledby="variation-title">
      <header className="variation-editor-header">
        <div>
          <p className="eyebrow">Create Variation</p>
          <h3 id="variation-title">Design a related Supercells Simulation</h3>
          <p>
            Set the environment and one deterministic thermal in physical units. Review the exact
            generated profiles before packaging or queueing CM1.
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={restoreParent}>
          Restore parent
        </button>
      </header>

      <div className="variation-editor-grid">
        <div className="variation-editor-main">
          <section className="variation-section variation-identity-section">
            <SectionTitle
              number="1"
              title="Simulation identity"
              copy="The Recipe follows the selected parent; the requested and achieved values remain explicit."
            />
            <div className="variation-identity-grid">
              <label>
                Parent Simulation
                <select
                  value={parentSimulationId}
                  disabled={Boolean(packaged)}
                  onChange={(event) => setParentSimulationId(event.target.value)}
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
                  maxLength={120}
                  placeholder="e.g. Drier high-shear storm"
                  disabled={Boolean(packaged)}
                  onChange={(event) => setSimulationName(event.target.value)}
                />
              </label>
              <label>
                Scientific question <span className="optional-label">optional</span>
                <input
                  value={userQuestion}
                  maxLength={500}
                  placeholder="What are you trying to learn?"
                  disabled={Boolean(packaged)}
                  onChange={(event) => setUserQuestion(event.target.value)}
                />
              </label>
            </div>
            <p className="variation-parent-source">{template.parent_configuration_source}</p>
          </section>

          <section className="variation-section">
            <SectionTitle
              number="2"
              title="Environment and initiation"
              copy="Quantitative controls are absolute targets. Unusual or failed storms remain valid outcomes."
            />
            <div className="supercells-control-families">
              <ControlFamily
                eyebrow="Wind environment"
                title="Shape and translate the hodograph"
                summary={`${formatNumber(controls.shear_0_6_km_m_s, 1)} m/s deep shear · ${formatNumber(controls.mean_wind_0_6_km_speed_m_s, 1)} m/s mean wind`}
              >
                <ChoiceControl
                  label="Hodograph family"
                  value={controls.hodograph_family}
                  choices={[
                    ["straight", "Straight"],
                    ["quarter_circle", "Quarter Circle"],
                    ["half_circle", "Half Circle"],
                  ]}
                  disabled={Boolean(packaged)}
                  onChange={(value) => update("hodograph_family", value as HodographFamily)}
                />
                <div className="supercells-control-grid">
                  <NumericControl
                    label="0–6 km shear"
                    value={controls.shear_0_6_km_m_s}
                    min={0}
                    max={80}
                    step={0.1}
                    units="m/s"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("shear_0_6_km_m_s", value)}
                  />
                  <NumericControl
                    label="0–2 km shear"
                    value={controls.shear_0_2_km_m_s}
                    min={0}
                    max={50}
                    step={0.1}
                    units="m/s"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("shear_0_2_km_m_s", value)}
                  />
                  <NumericControl
                    label="Turning depth"
                    value={controls.turning_depth_km_agl}
                    min={0.25}
                    max={8}
                    step={0.05}
                    units="km AGL"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("turning_depth_km_agl", value)}
                  />
                  <NumericControl
                    label="0–6 km mean wind"
                    value={controls.mean_wind_0_6_km_speed_m_s}
                    min={0}
                    max={50}
                    step={0.1}
                    units="m/s"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("mean_wind_0_6_km_speed_m_s", value)}
                  />
                  <NumericControl
                    label="Mean-wind direction"
                    value={controls.mean_wind_0_6_km_direction_deg}
                    min={0}
                    max={360}
                    step={1}
                    units="°"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("mean_wind_0_6_km_direction_deg", value)}
                  />
                </div>
                <details className="variation-advanced-controls">
                  <summary>Upper-level wind</summary>
                  <div className="supercells-control-grid">
                    <NumericControl
                      label="6–12 km shear"
                      value={controls.shear_6_12_km_m_s}
                      min={0}
                      max={50}
                      step={0.1}
                      units="m/s"
                      disabled={Boolean(packaged)}
                      onChange={(value) => update("shear_6_12_km_m_s", value)}
                    />
                    <NumericControl
                      label="Direction relative to 0–6 km shear"
                      value={controls.upper_shear_direction_relative_deg}
                      min={-180}
                      max={180}
                      step={1}
                      units="°"
                      disabled={Boolean(packaged)}
                      onChange={(value) => update("upper_shear_direction_relative_deg", value)}
                    />
                  </div>
                </details>
              </ControlFamily>

              <ControlFamily
                eyebrow="Thermodynamic environment"
                title="Set buoyancy, cloud base, moisture, and cap"
                summary={`${formatNumber(controls.surface_based_cape_j_kg, 0)} J/kg CAPE · ${formatNumber(controls.lcl_height_m_agl, 0)} m LCL`}
              >
                <ChoiceControl
                  label="Buoyancy distribution"
                  value={controls.buoyancy_distribution}
                  choices={[
                    ["low_level_weighted", "Low-level weighted"],
                    ["reference", "Reference"],
                    ["deep_weighted", "Deep weighted"],
                  ]}
                  disabled={Boolean(packaged)}
                  onChange={(value) =>
                    update("buoyancy_distribution", value as BuoyancyDistribution)
                  }
                />
                <div className="supercells-control-grid">
                  <NumericControl
                    label="Surface-based CAPE"
                    value={controls.surface_based_cape_j_kg}
                    min={0}
                    max={8_000}
                    step={1}
                    units="J/kg"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("surface_based_cape_j_kg", value)}
                  />
                  <NumericControl
                    label="LCL height"
                    value={controls.lcl_height_m_agl}
                    min={100}
                    max={4_000}
                    step={1}
                    units="m AGL"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("lcl_height_m_agl", value)}
                  />
                  <NumericControl
                    label="3–7 km mean RH"
                    value={controls.midlevel_rh_percent}
                    min={0}
                    max={100}
                    step={0.1}
                    units="%"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("midlevel_rh_percent", value)}
                  />
                  <NumericControl
                    label="CIN"
                    value={controls.cin_j_kg}
                    min={0}
                    max={500}
                    step={1}
                    units="J/kg"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("cin_j_kg", value)}
                  />
                </div>
              </ControlFamily>

              <ControlFamily
                eyebrow="Deterministic initiation"
                title="Place one thermal inside the resolved domain"
                summary={`${formatSigned(controls.thermal_perturbation_amplitude_k, 1)} K · ${formatNumber(controls.thermal_horizontal_radius_km, 1)} km radius`}
              >
                <div className="supercells-control-grid">
                  <NumericControl
                    label="Thermal perturbation"
                    value={controls.thermal_perturbation_amplitude_k}
                    min={-3}
                    max={12}
                    step={0.1}
                    units="K"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("thermal_perturbation_amplitude_k", value)}
                  />
                  <NumericControl
                    label="Horizontal radius"
                    value={controls.thermal_horizontal_radius_km}
                    min={0.5}
                    max={40}
                    step={0.1}
                    units="km"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("thermal_horizontal_radius_km", value)}
                  />
                  <NumericControl
                    label="Vertical radius"
                    value={controls.thermal_vertical_radius_km}
                    min={0.25}
                    max={10}
                    step={0.05}
                    units="km"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("thermal_vertical_radius_km", value)}
                  />
                  <NumericControl
                    label="Center height"
                    value={controls.thermal_center_height_km_agl}
                    min={0.25}
                    max={8}
                    step={0.05}
                    units="km AGL"
                    disabled={Boolean(packaged)}
                    onChange={(value) => update("thermal_center_height_km_agl", value)}
                  />
                </div>
                <details className="variation-advanced-controls">
                  <summary>Horizontal placement</summary>
                  <div className="supercells-control-grid">
                    <NumericControl
                      label="Center x"
                      value={controls.thermal_center_x_km}
                      min={-60}
                      max={60}
                      step={0.1}
                      units="km"
                      disabled={Boolean(packaged)}
                      onChange={(value) => update("thermal_center_x_km", value)}
                    />
                    <NumericControl
                      label="Center y"
                      value={controls.thermal_center_y_km}
                      min={-60}
                      max={60}
                      step={0.1}
                      units="km"
                      disabled={Boolean(packaged)}
                      onChange={(value) => update("thermal_center_y_km", value)}
                    />
                  </div>
                </details>
              </ControlFamily>
            </div>
            <ScientificPreview preview={preview} />
          </section>

          <section className="variation-section">
            <SectionTitle
              number="3"
              title="Run profile"
              copy="Resolution and observation density are explicit parts of the experiment."
            />
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
                    name="supercells-profile"
                    value={estimate.profile.profile_id}
                    checked={runProfileId === estimate.profile.profile_id}
                    disabled={Boolean(packaged)}
                    onChange={() => setRunProfileId(estimate.profile.profile_id)}
                  />
                  <span>
                    <strong>{estimate.profile.role}</strong>
                    <small>{shortProfileName(estimate.profile.profile_name)}</small>
                  </span>
                  <span
                    className={
                      estimate.disposition === "passes" ? "profile-cost" : "profile-cost blocked"
                    }
                  >
                    {profileCost(estimate.profile)}
                  </span>
                </label>
              ))}
            </div>
            {selectedProfile && (
              <div className="variation-profile-detail">
                <div>
                  <span>Numerical realization</span>
                  <strong>{selectedProfile.profile.numerical_realization.grid}</strong>
                  <small>{selectedProfile.profile.numerical_realization.spacing}</small>
                </div>
                <div>
                  <span>Observation plan</span>
                  <strong>
                    {formatDuration(selectedProfile.profile.observation_plan.duration_seconds)}
                  </strong>
                  <small>
                    {selectedProfile.profile.observation_plan.expected_history_count} saved outputs
                  </small>
                </div>
                <div>
                  <span>Expected local cost</span>
                  <strong>{profileCost(selectedProfile.profile)}</strong>
                  <small>{selectedProfile.profile.estimate_basis.replaceAll("_", " ")}</small>
                </div>
                <div>
                  <span>Lens support</span>
                  <strong>All three Supercells Lenses</strong>
                  <small>
                    {selectedProfile.profile.scientific_limitations[0] ??
                      "Native horizontal and vertical sections retained."}
                  </small>
                </div>
              </div>
            )}
          </section>
        </div>

        <aside className="variation-preview" aria-label="Variation review">
          <header>
            <div>
              <p className="eyebrow">Review</p>
              <h3>
                {previewing
                  ? "Resolving experiment..."
                  : `${differenceCount} material ${differenceCount === 1 ? "change" : "changes"}`}
              </h3>
            </div>
            {preview && !previewing && (
              <span
                className={
                  preview.blocking_errors.length
                    ? "technical-state unavailable"
                    : "technical-state available"
                }
              >
                {preview.blocking_errors.length ? "Blocked" : "Ready to package"}
              </span>
            )}
          </header>
          {preview && (
            <>
              <section className="variation-review-summary">
                <p className="variation-relationship">
                  {relationshipLabel(preview.relationship_classification)}
                </p>
                <AchievedSummary preview={preview} />
              </section>
              <DifferenceSummary differences={preview.differences} />
              {preview.warnings.map((warning) => (
                <p key={warning} className="variation-message variation-message-warning">
                  {warning}
                </p>
              ))}
              {preview.blocking_errors.map((blockingError) => (
                <p
                  key={blockingError}
                  className="variation-message variation-message-blocking"
                  role="alert"
                >
                  {blockingError}
                </p>
              ))}
              <section className="variation-budget">
                <dl>
                  <div>
                    <dt>Resolved storage</dt>
                    <dd>{profileSize(preview.cost_estimate.profile)}</dd>
                  </div>
                  <div>
                    <dt>Free after high estimate</dt>
                    <dd>{formatBytes(preview.cost_estimate.projected_free_space_bytes)}</dd>
                  </div>
                  <div>
                    <dt>Declared useful window</dt>
                    <dd>0-{formatDuration(preview.useful_window_end_seconds)}</dd>
                  </div>
                </dl>
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
                <small>The immediate disk and active-process gates run again before launch.</small>
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

function SectionTitle({ number, title, copy }: { number: string; title: string; copy: string }) {
  return (
    <div className="variation-section-title">
      <span>{number}</span>
      <div>
        <h4>{title}</h4>
        <p>{copy}</p>
      </div>
    </div>
  );
}

function ControlFamily({
  eyebrow,
  title,
  summary,
  children,
}: {
  eyebrow: string;
  title: string;
  summary: string;
  children: ReactNode;
}) {
  return (
    <section className="supercells-control-family">
      <header>
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h5>{title}</h5>
        </div>
        <span>{summary}</span>
      </header>
      {children}
    </section>
  );
}

function ChoiceControl({
  label,
  value,
  choices,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  choices: Array<[string, string]>;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className="supercells-choice-control">
      <span>{label}</span>
      <div role="group" aria-label={label}>
        {choices.map(([choice, display]) => (
          <button
            key={choice}
            type="button"
            className={value === choice ? "active-control" : ""}
            aria-pressed={value === choice}
            disabled={disabled}
            onClick={() => onChange(choice)}
          >
            {display}
          </button>
        ))}
      </div>
    </div>
  );
}

function NumericControl({
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
    <label className="supercells-numeric-control">
      <span>
        <strong>{label}</strong>
        <span>
          <input
            type="number"
            value={readableControlValue(value)}
            min={min}
            max={max}
            step="any"
            disabled={disabled}
            aria-label={`${label} value`}
            onChange={(event) => onChange(Number(event.target.value))}
          />
          <small>{units}</small>
        </span>
      </span>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        aria-label={label}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <small>
        {formatNumber(min, controlRangeDigits(step))} to{" "}
        {formatNumber(max, controlRangeDigits(step))} {units}
      </small>
    </label>
  );
}

function ScientificPreview({ preview }: { preview: VariationPreview | null }) {
  if (!preview) {
    return (
      <div className="supercells-science-preview placeholder">Resolving scientific profiles...</div>
    );
  }
  return (
    <section className="supercells-science-preview" aria-label="Resolved scientific profiles">
      <header>
        <div>
          <h5>Resolved scientific profiles</h5>
          <p>These exact backend profiles are written into the run package.</p>
        </div>
        <span>{preview.diagnostics.labels.join(" · ")}</span>
      </header>
      <div className="supercells-preview-grid">
        <HodographPlot preview={preview} />
        <ThermodynamicPlot preview={preview} />
        <ThermalPlot preview={preview} />
      </div>
    </section>
  );
}

function HodographPlot({ preview }: { preview: VariationPreview }) {
  const levels = preview.hodograph.filter((level) => level.height_m <= 12_000);
  const bounds = plotBounds(levels.flatMap((level) => [level.u_m_s, level.v_m_s]));
  const point = (u: number, v: number) =>
    `${plotCoordinate(u, bounds, 22, 218)},${240 - plotCoordinate(v, bounds, 22, 218)}`;
  return (
    <figure>
      <figcaption>
        <strong>Hodograph</strong>
        <span>u / v (m/s), surface to 12 km</span>
      </figcaption>
      <svg viewBox="0 0 240 240" role="img" aria-label="Resolved hodograph">
        <line x1="20" x2="220" y1="120" y2="120" />
        <line x1="120" x2="120" y1="20" y2="220" />
        <polyline
          className="hodograph-path"
          points={levels.map((level) => point(level.u_m_s, level.v_m_s)).join(" ")}
        />
        {levels
          .filter((level) => [0, 2_000, 6_000, 12_000].includes(level.height_m))
          .map((level) => (
            <g key={level.height_m}>
              <circle
                cx={plotCoordinate(level.u_m_s, bounds, 22, 218)}
                cy={240 - plotCoordinate(level.v_m_s, bounds, 22, 218)}
                r="4"
              />
              <text
                x={plotCoordinate(level.u_m_s, bounds, 22, 218) + 6}
                y={240 - plotCoordinate(level.v_m_s, bounds, 22, 218) - 5}
              >
                {level.height_m / 1_000} km
              </text>
            </g>
          ))}
      </svg>
      <div className="supercells-plot-metrics">
        <span>
          <strong>{formatNumber(preview.diagnostics.shear_0_6_km_m_s, 1)}</strong> m/s 0–6
        </span>
        <span>
          <strong>
            {formatSigned(preview.diagnostics.storm_relative_helicity_0_3_km_m2_s2, 0)}
          </strong>{" "}
          m²/s² SRH
        </span>
      </div>
    </figure>
  );
}

function ThermodynamicPlot({ preview }: { preview: VariationPreview }) {
  const levels = preview.sounding.filter((level) => level.height_m <= 14_000);
  const maxBuoyancy = Math.max(
    0.05,
    ...levels.map((level) => Math.abs(level.parcel_buoyancy_m_s2)),
  );
  const x = (value: number) => 120 + (value / maxBuoyancy) * 92;
  const y = (height: number) => 220 - (height / 14_000) * 196;
  const positive = levels.map(
    (level) => `${x(Math.max(level.parcel_buoyancy_m_s2, 0))},${y(level.height_m)}`,
  );
  const negative = levels.map(
    (level) => `${x(Math.min(level.parcel_buoyancy_m_s2, 0))},${y(level.height_m)}`,
  );
  return (
    <figure>
      <figcaption>
        <strong>Parcel buoyancy</strong>
        <span>Signed vertical distribution</span>
      </figcaption>
      <svg viewBox="0 0 240 240" role="img" aria-label="Resolved parcel buoyancy profile">
        <line x1="120" x2="120" y1="20" y2="220" />
        <polyline className="buoyancy-positive" points={positive.join(" ")} />
        <polyline className="buoyancy-negative" points={negative.join(" ")} />
        <line
          className="profile-reference-line"
          x1="20"
          x2="220"
          y1={y(preview.diagnostics.achieved_lcl_height_m_agl)}
          y2={y(preview.diagnostics.achieved_lcl_height_m_agl)}
        />
        <text x="24" y={y(preview.diagnostics.achieved_lcl_height_m_agl) - 5}>
          LCL {formatNumber(preview.diagnostics.achieved_lcl_height_m_agl, 0)} m
        </text>
      </svg>
      <div className="supercells-plot-metrics">
        <span>
          <strong>{formatNumber(preview.diagnostics.achieved_cape_j_kg, 0)}</strong> J/kg CAPE
        </span>
        <span>
          <strong>{formatNumber(preview.diagnostics.achieved_cin_j_kg, 0)}</strong> J/kg CIN
        </span>
      </div>
    </figure>
  );
}

function ThermalPlot({ preview }: { preview: VariationPreview }) {
  const domain = preview.numerical_realization.exact_domain;
  if (!domain) return null;
  const xSpanKm = (domain.x_max_m - domain.x_min_m) / 1_000;
  const scaleX = 210 / xSpanKm;
  const scaleZ = 170 / (domain.model_top_m / 1_000);
  const centerX = 120 + (preview.initiation.center_x_m / 1_000) * scaleX;
  const centerZ = 210 - (preview.initiation.center_height_m_agl / 1_000) * scaleZ;
  const radiusX = (preview.initiation.horizontal_radius_m / 1_000) * scaleX;
  const radiusZ = (preview.initiation.vertical_radius_m / 1_000) * scaleZ;
  return (
    <figure>
      <figcaption>
        <strong>Thermal and domain</strong>
        <span>Native x–z geometry</span>
      </figcaption>
      <svg viewBox="0 0 240 240" role="img" aria-label="Resolved thermal cross-section">
        <rect x="15" y="20" width="210" height="190" className="thermal-domain" />
        <line
          className="profile-reference-line"
          x1="15"
          x2="225"
          y1={210 - (15_000 / domain.model_top_m) * 190}
          y2={210 - (15_000 / domain.model_top_m) * 190}
        />
        <ellipse
          cx={centerX}
          cy={centerZ}
          rx={Math.max(radiusX, 2)}
          ry={Math.max(radiusZ, 2)}
          className={
            preview.initiation.amplitude_k > 0
              ? "thermal-warm"
              : preview.initiation.amplitude_k < 0
                ? "thermal-cold"
                : "thermal-neutral"
          }
        />
        <text x="20" y="33">
          20 km top
        </text>
        <text x="20" y="205">
          {formatNumber(preview.diagnostics.minimum_boundary_clearance_km, 1)} km clearance
        </text>
      </svg>
      <div className="supercells-plot-metrics">
        <span>
          <strong>{formatSigned(preview.initiation.amplitude_k, 1)}</strong> K
        </span>
        <span>
          <strong>{formatNumber(preview.initiation.horizontal_radius_m / 1_000, 1)}</strong> km
          radius
        </span>
      </div>
    </figure>
  );
}

function AchievedSummary({ preview }: { preview: VariationPreview }) {
  return (
    <dl className="supercells-achieved-summary">
      <div>
        <dt>0–6 km shear</dt>
        <dd>{formatNumber(preview.diagnostics.shear_0_6_km_m_s, 1)} m/s</dd>
      </div>
      <div>
        <dt>0–2 km shear</dt>
        <dd>{formatNumber(preview.diagnostics.shear_0_2_km_m_s, 1)} m/s</dd>
      </div>
      <div>
        <dt>CAPE / CIN</dt>
        <dd>
          {formatNumber(preview.diagnostics.achieved_cape_j_kg, 0)} /{" "}
          {formatNumber(preview.diagnostics.achieved_cin_j_kg, 0)} J/kg
        </dd>
      </div>
      <div>
        <dt>LCL / midlevel RH</dt>
        <dd>
          {formatNumber(preview.diagnostics.achieved_lcl_height_m_agl, 0)} m /{" "}
          {formatNumber(preview.diagnostics.achieved_midlevel_rh_percent, 0)}%
        </dd>
      </div>
      <div>
        <dt>Model translation</dt>
        <dd>
          {formatSigned(preview.diagnostics.model_translation_u_m_s, 1)},{" "}
          {formatSigned(preview.diagnostics.model_translation_v_m_s, 1)} m/s
        </dd>
      </div>
      <div>
        <dt>Hydrostatic residual</dt>
        <dd>{preview.diagnostics.hydrostatic_residual_pa.toExponential(1)} Pa</dd>
      </div>
    </dl>
  );
}

function DifferenceSummary({ differences }: { differences: Record<string, Difference[]> }) {
  const populated = Object.entries(differences).filter(([, items]) => items.length);
  if (!populated.length) return null;
  return (
    <div className="variation-difference-groups">
      {populated.map(([group, items]) => (
        <section key={group}>
          <header>
            <strong>{differenceGroupLabel(group)}</strong>
            <span>{items.length}</span>
          </header>
          <ul>
            {items.map((item) => (
              <li key={item.path}>
                <span>{item.label}</span>
                <strong>
                  {displayValue(item.before)} → {displayValue(item.after)}
                  {item.units ? ` ${item.units}` : ""}
                </strong>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function requestPayload({
  parentSimulationId,
  simulationName,
  userQuestion,
  runProfileId,
  controls,
}: {
  parentSimulationId: string;
  simulationName: string;
  userQuestion: string;
  runProfileId: string;
  controls: SupercellsControls;
}) {
  return {
    parent_simulation_id: parentSimulationId,
    simulation_name: simulationName,
    user_question: userQuestion.trim() || null,
    recipe_id: "idealized_isolated_supercell",
    run_profile_id: runProfileId,
    controls,
  };
}

function relationshipLabel(value: string | null): string {
  if (!value) return "No material variation yet";
  return value
    .replace("controlled_physical_variation", "Controlled physical variation")
    .replace("controlled_initiation_sensitivity", "Controlled initiation sensitivity")
    .replace("multi_factor_physical_variation", "Multi-factor physical variation")
    .replace("numerical_sensitivity", "Numerical sensitivity")
    .replace("mixed_variation", "Mixed physical and numerical variation")
    .replace("observation_only_attempt", "Observation-only attempt");
}

function shortProfileName(value: string): string {
  return value.split("—").slice(1).join("—").trim() || value;
}

function profileCost(profile: RunCostProfile): string {
  const runtime =
    profile.expected_runtime_min_seconds === null || profile.expected_runtime_max_seconds === null
      ? "Runtime uncharacterized"
      : `${formatDuration(profile.expected_runtime_min_seconds)}–${formatDuration(
          profile.expected_runtime_max_seconds,
        )}`;
  const size =
    profile.expected_size_min_bytes === null || profile.expected_size_max_bytes === null
      ? "size uncharacterized"
      : `${formatBytes(profile.expected_size_min_bytes)}–${formatBytes(
          profile.expected_size_max_bytes,
        )}`;
  return `${runtime} · ${size}`;
}

function profileSize(profile: RunCostProfile): string {
  if (profile.expected_size_min_bytes === null || profile.expected_size_max_bytes === null) {
    return "Uncharacterized";
  }
  return `${formatBytes(profile.expected_size_min_bytes)}–${formatBytes(
    profile.expected_size_max_bytes,
  )}`;
}

function differenceGroupLabel(group: string): string {
  const labels: Record<string, string> = {
    wind: "Wind environment",
    thermodynamics: "Thermodynamic environment",
    "stability/thermodynamics": "Thermodynamic environment",
    initiation: "Deterministic initiation",
    "forcing/initiation": "Deterministic initiation",
    numerical: "Numerical realization",
    "numerical realization": "Numerical realization",
    observation: "Observation plan",
    "observation plan": "Observation plan",
  };
  return labels[group] ?? group.replaceAll("_", " ");
}

function readableControlValue(value: number): number {
  if (Number.isInteger(value)) return value;
  return Number(value.toFixed(2));
}

function controlRangeDigits(step: number): number {
  if (step < 0.1) return 2;
  if (step < 1) return 1;
  return 0;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "Uncharacterized";
  if (seconds >= 3_600) return `${formatNumber(seconds / 3_600, 1)} hr`;
  return `${formatNumber(seconds / 60, 0)} min`;
}

function formatBytes(value: number | null): string {
  if (value === null) return "Unavailable";
  return `${formatNumber(value / 1024 ** 3, 1)} GB`;
}

function displayValue(value: unknown): string {
  if (typeof value === "number") return formatNumber(value, Math.abs(value) < 10 ? 2 : 1);
  if (typeof value === "string") return value.replaceAll("_", " ");
  return typeof value === "object" ? "changed contract" : String(value);
}

function formatNumber(value: number, digits: number): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatSigned(value: number, digits: number): string {
  return `${value > 0 ? "+" : ""}${formatNumber(value, digits)}`;
}

function plotBounds(values: number[]): [number, number] {
  const extent = Math.max(10, ...values.map((value) => Math.abs(value)));
  return [-extent * 1.1, extent * 1.1];
}

function plotCoordinate(
  value: number,
  bounds: [number, number],
  minimum: number,
  maximum: number,
): number {
  return minimum + ((value - bounds[0]) / (bounds[1] - bounds[0])) * (maximum - minimum);
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
