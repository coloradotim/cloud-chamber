import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { TradeCumulusWorldDetail } from "./TradeCumulusWorld";

type TradeCumulusControls = {
  surface_sensible_heat_flux_k_m_s: number;
  surface_moisture_flux_g_kg_m_s: number;
  sub_inversion_total_water_g_kg: number;
  inversion_base_m_agl: number;
  inversion_thickness_m: number;
  inversion_strength_k: number;
  free_tropospheric_rh_percent: number;
  cloud_layer_shear_m_s: number;
  cloud_layer_shear_direction_deg: number;
  cloud_layer_mean_u_m_s: number;
  cloud_layer_mean_v_m_s: number;
  large_scale_vertical_motion_m_s: number;
  temperature_tendency_k_day: number;
  total_water_tendency_g_kg_day: number;
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
  recipe_id: "canonical_bomex_trade_cumulus";
  recipe_name: string;
  recipe_contract_version: string;
  controls: TradeCumulusControls;
  canonical_reference_controls: TradeCumulusControls;
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
  material: boolean;
};

type ProfileLevel = {
  height_m: number;
  theta_l_k: number;
  total_water_g_kg: number;
  relative_humidity_percent: number;
  u_m_s: number;
  v_m_s: number;
};

type ForcingLevel = {
  height_m: number;
  vertical_motion_m_s: number;
  temperature_tendency_k_day: number;
  total_water_tendency_g_kg_day: number;
};

type VariationPreview = {
  requested_controls: TradeCumulusControls;
  resolved_controls: Record<ControlKey, number | null>;
  canonical_reference_controls: TradeCumulusControls;
  parent_controls: TradeCumulusControls;
  differences: Record<string, Difference[]>;
  relationship_classification: string | null;
  warnings: string[];
  blocking_errors: string[];
  diagnostics: {
    inversion_top_m_agl: number;
    model_top_m: number;
    sub_inversion_total_water_g_kg: number;
    free_tropospheric_rh_percent: number | null;
    cloud_layer_shear_m_s: number;
    cloud_layer_shear_direction_deg: number;
    cloud_layer_mean_u_m_s: number;
    cloud_layer_mean_v_m_s: number;
    initial_saturated_level_count: number;
    minimum_theta_gradient_k_km: number;
    labels: string[];
  };
  sounding_profile: ProfileLevel[];
  forcing_profile: ForcingLevel[];
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

type ControlKey = keyof TradeCumulusControls;

const CONTROL_META: Record<
  ControlKey,
  { label: string; units: string; min: number; max: number; step: number; digits: number }
> = {
  surface_sensible_heat_flux_k_m_s: {
    label: "Sensible heat flux",
    units: "K m s⁻¹",
    min: -0.02,
    max: 0.05,
    step: 0.001,
    digits: 3,
  },
  surface_moisture_flux_g_kg_m_s: {
    label: "Moisture flux",
    units: "g kg⁻¹ m s⁻¹",
    min: -0.1,
    max: 0.25,
    step: 0.001,
    digits: 3,
  },
  sub_inversion_total_water_g_kg: {
    label: "Sub-inversion total water",
    units: "g kg⁻¹",
    min: 0,
    max: 25,
    step: 0.1,
    digits: 1,
  },
  inversion_base_m_agl: {
    label: "Inversion base",
    units: "m AGL",
    min: 300,
    max: 4000,
    step: 10,
    digits: 0,
  },
  inversion_thickness_m: {
    label: "Inversion thickness",
    units: "m",
    min: 50,
    max: 2000,
    step: 10,
    digits: 0,
  },
  inversion_strength_k: {
    label: "Inversion strength",
    units: "K",
    min: -5,
    max: 20,
    step: 0.1,
    digits: 1,
  },
  free_tropospheric_rh_percent: {
    label: "Free-tropospheric humidity",
    units: "%",
    min: 0,
    max: 100,
    step: 1,
    digits: 0,
  },
  cloud_layer_shear_m_s: {
    label: "0–3 km vector shear",
    units: "m s⁻¹",
    min: 0,
    max: 50,
    step: 0.1,
    digits: 1,
  },
  cloud_layer_shear_direction_deg: {
    label: "Shear direction",
    units: "°",
    min: 0,
    max: 360,
    step: 1,
    digits: 0,
  },
  cloud_layer_mean_u_m_s: {
    label: "Layer-mean u wind",
    units: "m s⁻¹",
    min: -50,
    max: 50,
    step: 0.5,
    digits: 1,
  },
  cloud_layer_mean_v_m_s: {
    label: "Layer-mean v wind",
    units: "m s⁻¹",
    min: -50,
    max: 50,
    step: 0.5,
    digits: 1,
  },
  large_scale_vertical_motion_m_s: {
    label: "Peak vertical motion",
    units: "m s⁻¹",
    min: -0.05,
    max: 0.05,
    step: 0.001,
    digits: 3,
  },
  temperature_tendency_k_day: {
    label: "Temperature tendency",
    units: "K day⁻¹",
    min: -20,
    max: 10,
    step: 0.1,
    digits: 1,
  },
  total_water_tendency_g_kg_day: {
    label: "Total-water tendency",
    units: "g kg⁻¹ day⁻¹",
    min: -20,
    max: 10,
    step: 0.1,
    digits: 1,
  },
};

const DIFFERENCE_GROUPS = [
  "wind",
  "moisture",
  "stability/thermodynamics",
  "forcing/initiation",
  "numerical realization",
  "observation plan",
] as const;

export function TradeCumulusVariationEditor({
  world,
  initialParentSimulationId,
  onCreated,
}: {
  world: TradeCumulusWorldDetail;
  initialParentSimulationId: string;
  onCreated: () => Promise<void> | void;
}) {
  const eligibleParents = useMemo(
    () => world.simulations.filter((simulation) => simulation.can_create_variation),
    [world.simulations],
  );
  const [parentSimulationId, setParentSimulationId] = useState(initialParentSimulationId);
  const [template, setTemplate] = useState<VariationTemplate | null>(null);
  const [controls, setControls] = useState<TradeCumulusControls | null>(null);
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
      `/api/worlds/trade-cumulus/variation-template?${new URLSearchParams({
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
      void fetch("/api/worlds/trade-cumulus/variations/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestPayload({
            parentSimulationId,
            simulationName: simulationName.trim() || "Untitled Trade Cumulus variation",
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

  function updateControl(key: ControlKey, value: number) {
    setControls((current) => (current ? { ...current, [key]: value } : current));
  }

  function restoreParent() {
    if (!template) return;
    setControls({ ...template.controls });
    setRunProfileId(template.default_run_profile_id);
    setPackaged(null);
    setStatus("Parent Recipe controls restored.");
  }

  function restoreReferenceForcing() {
    if (!template) return;
    const reference = template.canonical_reference_controls;
    setControls((current) =>
      current
        ? {
            ...current,
            large_scale_vertical_motion_m_s: reference.large_scale_vertical_motion_m_s,
            temperature_tendency_k_day: reference.temperature_tendency_k_day,
            total_water_tendency_g_kg_day: reference.total_water_tendency_g_kg_day,
          }
        : current,
    );
  }

  function zeroForcing() {
    setControls((current) =>
      current
        ? {
            ...current,
            large_scale_vertical_motion_m_s: 0,
            temperature_tendency_k_day: 0,
            total_water_tendency_g_kg_day: 0,
          }
        : current,
    );
  }

  async function packageVariation() {
    if (!controls || !simulationName.trim()) return;
    setSubmitting(true);
    setError(null);
    setStatus("Writing the exact package and launch review...");
    try {
      const response = await fetch("/api/worlds/trade-cumulus/variations", {
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
    <section
      className="lab-content mountain-waves-variation-editor trade-cumulus-variation-editor"
      aria-labelledby="trade-variation-title"
    >
      <header className="variation-editor-header">
        <div>
          <p className="eyebrow">Create Variation</p>
          <h3 id="trade-variation-title">Design a related Trade Cumulus Simulation</h3>
          <p>
            Enter direct atmospheric and forcing targets, inspect the generated profile, then
            package the exact experiment before deciding whether to queue CM1.
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
              step="1"
              title="Simulation identity"
              detail="The Recipe follows the selected parent and cannot be silently changed."
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
                    <option key={parent.simulation_id} value={parent.simulation_id ?? ""}>
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
                  placeholder="e.g. Weak inversion with ascent"
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
            <SectionTitle
              step="2"
              title="Atmosphere and forcing"
              detail="Values are absolute physical targets; the generated profile proves what CM1 will receive."
            />
            <div className="variation-control-groups three-up">
              <ControlGroup title="Surface exchange">
                <RangeField
                  controlKey="surface_sensible_heat_flux_k_m_s"
                  value={controls.surface_sensible_heat_flux_k_m_s}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
                <RangeField
                  controlKey="surface_moisture_flux_g_kg_m_s"
                  value={controls.surface_moisture_flux_g_kg_m_s}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
              </ControlGroup>
              <ControlGroup title="Initial atmosphere">
                <RangeField
                  controlKey="sub_inversion_total_water_g_kg"
                  value={controls.sub_inversion_total_water_g_kg}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
                <RangeField
                  controlKey="inversion_base_m_agl"
                  value={controls.inversion_base_m_agl}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
                <RangeField
                  controlKey="inversion_strength_k"
                  value={controls.inversion_strength_k}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
                <RangeField
                  controlKey="free_tropospheric_rh_percent"
                  value={controls.free_tropospheric_rh_percent}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
              </ControlGroup>
              <ControlGroup title="Cloud-layer wind">
                <RangeField
                  controlKey="cloud_layer_shear_m_s"
                  value={controls.cloud_layer_shear_m_s}
                  template={template}
                  disabled={Boolean(packaged)}
                  onChange={updateControl}
                />
                <div className="variation-wind-summary">
                  <span>0–3 km layer mean</span>
                  <strong>
                    u {formatNumber(controls.cloud_layer_mean_u_m_s, 1)} · v{" "}
                    {formatNumber(controls.cloud_layer_mean_v_m_s, 1)} m s⁻¹
                  </strong>
                </div>
              </ControlGroup>
            </div>

            <details className="variation-advanced">
              <summary>Advanced profile structure</summary>
              <div className="variation-control-groups">
                <ControlGroup title="Inversion geometry">
                  <RangeField
                    controlKey="inversion_thickness_m"
                    value={controls.inversion_thickness_m}
                    template={template}
                    disabled={Boolean(packaged)}
                    onChange={updateControl}
                  />
                </ControlGroup>
                <ControlGroup title="Shear vector">
                  <RangeField
                    controlKey="cloud_layer_shear_direction_deg"
                    value={controls.cloud_layer_shear_direction_deg}
                    template={template}
                    disabled={Boolean(packaged) || controls.cloud_layer_shear_m_s === 0}
                    onChange={updateControl}
                  />
                </ControlGroup>
              </div>
            </details>

            <section className="variation-forcing-controls" aria-labelledby="forcing-title">
              <header>
                <div>
                  <h5 id="forcing-title">Large-scale forcing</h5>
                  <p>Signed peak targets retain the authored BOMEX vertical shapes.</p>
                </div>
                <div className="variation-convenience-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={Boolean(packaged)}
                    onClick={restoreReferenceForcing}
                  >
                    Restore reference forcing
                  </button>
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={Boolean(packaged)}
                    onClick={zeroForcing}
                  >
                    Zero forcing
                  </button>
                </div>
              </header>
              <div className="variation-control-groups three-up">
                {(
                  [
                    "large_scale_vertical_motion_m_s",
                    "temperature_tendency_k_day",
                    "total_water_tendency_g_kg_day",
                  ] as ControlKey[]
                ).map((key) => (
                  <ControlGroup key={key} title={CONTROL_META[key].label}>
                    <RangeField
                      controlKey={key}
                      value={controls[key]}
                      template={template}
                      disabled={Boolean(packaged)}
                      onChange={updateControl}
                      hideLabel
                    />
                  </ControlGroup>
                ))}
              </div>
            </section>

            <ScientificPreview preview={preview} />
          </section>

          <section className="variation-section">
            <SectionTitle
              step="3"
              title="Run profile"
              detail="Numerical realization and observation plan are explicit parts of the comparison."
            />
            <div className="variation-profile-options trade-profile-options" role="radiogroup">
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
                    name="trade-cumulus-profile"
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
                  <strong>
                    {preview?.numerical_realization.grid ??
                      selectedProfile.profile.numerical_realization.grid}
                  </strong>
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
                  <strong>
                    {profileCost(preview?.cost_estimate.profile ?? selectedProfile.profile)}
                  </strong>
                  <small>
                    {(
                      preview?.cost_estimate.profile.estimate_basis ??
                      selectedProfile.profile.estimate_basis
                    ).replaceAll("_", " ")}
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
                {previewing ? "Resolving experiment..." : `${differenceCount} material changes`}
              </h3>
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
                    <dt>Inversion</dt>
                    <dd>{formatDistance(preview.diagnostics.inversion_top_m_agl)} top</dd>
                  </div>
                  <div>
                    <dt>0–3 km shear</dt>
                    <dd>{preview.diagnostics.cloud_layer_shear_m_s.toFixed(1)} m s⁻¹</dd>
                  </div>
                  <div>
                    <dt>Free-tropospheric RH</dt>
                    <dd>
                      {preview.diagnostics.free_tropospheric_rh_percent === null
                        ? "Unavailable"
                        : `${preview.diagnostics.free_tropospheric_rh_percent.toFixed(0)}%`}
                    </dd>
                  </div>
                  <div>
                    <dt>Initial saturation</dt>
                    <dd>{preview.diagnostics.initial_saturated_level_count} profile levels</dd>
                  </div>
                </dl>
              </section>

              {preview.warnings.map((warning) => (
                <p key={warning} className="variation-message variation-message-warning">
                  {warning}
                </p>
              ))}
              {preview.blocking_errors.map((message) => (
                <p
                  key={message}
                  className="variation-message variation-message-blocking"
                  role="alert"
                >
                  {message}
                </p>
              ))}

              <DifferenceReview preview={preview} />

              <CostReview estimate={preview.cost_estimate} />

              {!packaged ? (
                <button
                  type="button"
                  disabled={!canPackage}
                  onClick={() => void packageVariation()}
                >
                  {submitting ? "Packaging..." : "Package variation"}
                </button>
              ) : (
                <section className="variation-packaged-state">
                  <p className="eyebrow">Packaged</p>
                  <strong>{packaged.run_id}</strong>
                  <small>Exact inputs and launch review are retained. CM1 has not started.</small>
                  <button type="button" disabled={queueing} onClick={() => void queuePackage()}>
                    {queueing ? "Queueing..." : "Queue CM1"}
                  </button>
                </section>
              )}
            </>
          )}
          {status && <p className="variation-message">{status}</p>}
          {error && (
            <p className="variation-message variation-message-blocking" role="alert">
              {error}
            </p>
          )}
        </aside>
      </div>
    </section>
  );
}

function SectionTitle({ step, title, detail }: { step: string; title: string; detail: string }) {
  return (
    <div className="variation-section-title">
      <span>{step}</span>
      <div>
        <h4>{title}</h4>
        <p>{detail}</p>
      </div>
    </div>
  );
}

function ControlGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="variation-control-group">
      <h5>{title}</h5>
      {children}
    </div>
  );
}

function RangeField({
  controlKey,
  value,
  template,
  disabled,
  onChange,
  hideLabel = false,
}: {
  controlKey: ControlKey;
  value: number;
  template: VariationTemplate;
  disabled: boolean;
  onChange: (key: ControlKey, value: number) => void;
  hideLabel?: boolean;
}) {
  const metadata = CONTROL_META[controlKey];
  const reference = template.canonical_reference_controls[controlKey];
  const parent = template.controls[controlKey];
  const difference = value - parent;
  const inputId = `trade-control-${controlKey}`;
  return (
    <label className="variation-range-field" htmlFor={inputId}>
      {!hideLabel && (
        <span>
          <strong>{metadata.label}</strong>
          <output htmlFor={inputId}>
            {formatNumber(value, metadata.digits)} {metadata.units}
          </output>
        </span>
      )}
      {hideLabel && (
        <output htmlFor={inputId}>
          {formatNumber(value, metadata.digits)} {metadata.units}
        </output>
      )}
      <div className="variation-range-inputs">
        <input
          id={inputId}
          type="range"
          min={metadata.min}
          max={metadata.max}
          step={metadata.step}
          value={value}
          disabled={disabled}
          onChange={(event) => onChange(controlKey, Number(event.target.value))}
        />
        <input
          type="number"
          aria-label={`${metadata.label} exact value`}
          min={metadata.min}
          max={metadata.max}
          step={metadata.step}
          value={value}
          disabled={disabled}
          onChange={(event) => {
            const next = Number(event.target.value);
            if (Number.isFinite(next)) onChange(controlKey, next);
          }}
        />
      </div>
      <small>
        Ref {formatNumber(reference, metadata.digits)} · Parent{" "}
        {formatNumber(parent, metadata.digits)} · Δ {formatSigned(difference, metadata.digits)}
      </small>
    </label>
  );
}

function ScientificPreview({ preview }: { preview: VariationPreview | null }) {
  if (!preview) {
    return <div className="scientific-preview-placeholder" aria-hidden="true" />;
  }
  const heights = preview.sounding_profile.map((level) => level.height_m);
  const forcingHeights = preview.forcing_profile.map((level) => level.height_m);
  return (
    <section className="variation-scientific-preview" aria-labelledby="profile-preview-title">
      <header>
        <div>
          <h5 id="profile-preview-title">Resolved scientific profiles</h5>
          <p>Complete generated atmosphere and forcing; height is shown in km AGL.</p>
        </div>
        <span>Exact package source</span>
      </header>
      <div className="variation-atmosphere-profiles trade-profile-plots">
        <ProfilePlot
          title="Potential temperature"
          units="θl (K)"
          heights={heights}
          series={[preview.sounding_profile.map((level) => level.theta_l_k)]}
          markers={[
            preview.resolved_controls.inversion_base_m_agl ??
              preview.requested_controls.inversion_base_m_agl,
            preview.diagnostics.inversion_top_m_agl,
          ]}
        />
        <ProfilePlot
          title="Total water"
          units="qt (g/kg)"
          heights={heights}
          series={[preview.sounding_profile.map((level) => level.total_water_g_kg)]}
          markers={[
            preview.resolved_controls.inversion_base_m_agl ??
              preview.requested_controls.inversion_base_m_agl,
            preview.diagnostics.inversion_top_m_agl,
          ]}
        />
        <ProfilePlot
          title="Relative humidity"
          units="RH (%)"
          heights={heights}
          series={[preview.sounding_profile.map((level) => level.relative_humidity_percent)]}
          referenceValue={100}
        />
        <ProfilePlot
          title="Horizontal wind"
          units="u / v (m/s)"
          heights={heights}
          series={[
            preview.sounding_profile.map((level) => level.u_m_s),
            preview.sounding_profile.map((level) => level.v_m_s),
          ]}
        />
        <ProfilePlot
          title="Vertical motion"
          units="w (m/s)"
          heights={forcingHeights}
          series={[preview.forcing_profile.map((level) => level.vertical_motion_m_s)]}
          referenceValue={0}
        />
        <ProfilePlot
          title="Thermodynamic forcing"
          units="K/day · g/kg/day"
          heights={forcingHeights}
          series={[
            preview.forcing_profile.map((level) => level.temperature_tendency_k_day),
            preview.forcing_profile.map((level) => level.total_water_tendency_g_kg_day),
          ]}
          referenceValue={0}
        />
      </div>
    </section>
  );
}

function ProfilePlot({
  title,
  units,
  heights,
  series,
  markers = [],
  referenceValue,
}: {
  title: string;
  units: string;
  heights: number[];
  series: number[][];
  markers?: number[];
  referenceValue?: number;
}) {
  const width = 140;
  const height = 170;
  const padding = { left: 23, right: 9, top: 8, bottom: 20 };
  const values = series.flat();
  if (!heights.length || !values.length) return null;
  const minimum = Math.min(...values, referenceValue ?? Infinity);
  const maximum = Math.max(...values, referenceValue ?? -Infinity);
  const span = Math.max(maximum - minimum, 1e-9);
  const top = Math.max(...heights);
  const x = (value: number) =>
    padding.left + ((value - minimum) / span) * (width - padding.left - padding.right);
  const y = (value: number) =>
    padding.top + (1 - value / Math.max(top, 1)) * (height - padding.top - padding.bottom);
  const colors = ["var(--color-accent-primary)", "#8b4f7d"];
  return (
    <figure className="variation-profile-plot">
      <figcaption>
        <strong>{title}</strong>
        <span>{units}</span>
      </figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title} profile`}>
        <line
          className="profile-axis"
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
        />
        <line
          className="profile-axis"
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
        />
        {referenceValue !== undefined && (
          <line
            className="profile-zero"
            x1={x(referenceValue)}
            y1={padding.top}
            x2={x(referenceValue)}
            y2={height - padding.bottom}
          />
        )}
        {markers.map((marker) => (
          <line
            key={marker}
            className="profile-marker"
            x1={padding.left}
            y1={y(marker)}
            x2={width - padding.right}
            y2={y(marker)}
          />
        ))}
        {series.map((valuesForSeries, index) => (
          <polyline
            key={index}
            points={valuesForSeries
              .map((value, point) => `${x(value)},${y(heights[point])}`)
              .join(" ")}
            fill="none"
            stroke={colors[index] ?? colors[0]}
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
        <text x={padding.left} y={height - 5}>
          {compactNumber(minimum)}
        </text>
        <text x={width - padding.right} y={height - 5} textAnchor="end">
          {compactNumber(maximum)}
        </text>
        <text x="2" y={padding.top + 6}>
          {(top / 1000).toFixed(1)}
        </text>
        <text x="8" y={height - padding.bottom}>
          0
        </text>
      </svg>
    </figure>
  );
}

function DifferenceReview({ preview }: { preview: VariationPreview }) {
  const rows = (Object.keys(CONTROL_META) as ControlKey[]).map((key) => {
    const meta = CONTROL_META[key];
    const reference = preview.canonical_reference_controls[key];
    const parent = preview.parent_controls[key];
    const child = preview.resolved_controls[key];
    return { key, meta, reference, parent, child };
  });
  return (
    <details className="variation-exact-review" open>
      <summary>Exact physical specification</summary>
      <div className="variation-exact-table">
        <div className="variation-exact-heading">
          <span>Target</span>
          <span>Reference</span>
          <span>Parent</span>
          <span>Child</span>
          <span>Δ</span>
        </div>
        {rows.map(({ key, meta, reference, parent, child }) => (
          <div key={key}>
            <strong>{meta.label}</strong>
            <span>{formatNumber(reference, meta.digits)}</span>
            <span>{formatNumber(parent, meta.digits)}</span>
            <span>{formatNumber(child, meta.digits)}</span>
            <span>{formatSigned(child === null ? null : child - parent, meta.digits)}</span>
            <small>{meta.units}</small>
          </div>
        ))}
      </div>
      <div className="variation-difference-groups">
        {DIFFERENCE_GROUPS.map((group) => {
          const differences = preview.differences[group] ?? [];
          if (!differences.length) return null;
          return (
            <section key={group}>
              <header>
                <strong>{group}</strong>
                <span>{differences.length}</span>
              </header>
            </section>
          );
        })}
      </div>
    </details>
  );
}

function CostReview({ estimate }: { estimate: RunCostEstimate }) {
  return (
    <section className="variation-budget">
      <dl>
        <div>
          <dt>Retained storage</dt>
          <dd>{storageRange(estimate.profile)}</dd>
        </div>
        <div>
          <dt>Free after high estimate</dt>
          <dd>{formatBytes(estimate.projected_free_space_bytes)}</dd>
        </div>
      </dl>
      <p className={estimate.disposition === "passes" ? "" : "blocked"}>
        {estimate.disposition_reason}
      </p>
    </section>
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
  controls: TradeCumulusControls;
}) {
  return {
    parent_simulation_id: parentSimulationId,
    simulation_name: simulationName,
    user_question: userQuestion.trim() || null,
    recipe_id: "canonical_bomex_trade_cumulus",
    run_profile_id: runProfileId,
    controls,
  };
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

function relationshipLabel(value: string | null): string {
  if (!value) return "No material variation yet";
  return value
    .replace("controlled_physical_variation", "Controlled physical variation")
    .replace("multi_factor_physical_variation", "Multi-factor physical variation")
    .replace("numerical_sensitivity", "Numerical sensitivity")
    .replace("mixed_variation", "Mixed physical and numerical variation")
    .replace("observation_only_attempt", "Observation-only attempt");
}

function shortProfileName(value: string): string {
  return value.split("—")[1]?.trim() ?? value;
}

function profileCost(profile: RunCostProfile): string {
  const runtime =
    profile.expected_runtime_min_seconds !== null && profile.expected_runtime_max_seconds !== null
      ? `${formatDuration(profile.expected_runtime_min_seconds)}–${formatDuration(
          profile.expected_runtime_max_seconds,
        )}`
      : "Uncharacterized";
  return `${runtime} · ${storageRange(profile)}`;
}

function storageRange(profile: RunCostProfile): string {
  if (profile.expected_size_min_bytes === null || profile.expected_size_max_bytes === null) {
    return "Uncharacterized";
  }
  return `${formatBytes(profile.expected_size_min_bytes)}–${formatBytes(
    profile.expected_size_max_bytes,
  )}`;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "Generated";
  if (seconds >= 3600) {
    const hours = seconds / 3600;
    return Number.isInteger(hours) ? `${hours} h` : `${hours.toFixed(1)} h`;
  }
  return `${Math.round(seconds / 60)} min`;
}

function formatDistance(meters: number): string {
  return meters >= 1000 ? `${(meters / 1000).toFixed(2)} km` : `${meters.toFixed(0)} m`;
}

function formatBytes(bytes: number | null): string {
  if (bytes === null) return "Unknown";
  return bytes >= 1024 ** 3
    ? `${(bytes / 1024 ** 3).toFixed(1)} GB`
    : `${Math.round(bytes / 1024 ** 2)} MB`;
}

function formatNumber(value: number | null | undefined, digits: number): string {
  return value === null || value === undefined || !Number.isFinite(value)
    ? "Unavailable"
    : value.toFixed(digits);
}

function formatSigned(value: number | null, digits: number): string {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  const normalized = Math.abs(value) < 10 ** -(digits + 1) ? 0 : value;
  return `${normalized > 0 ? "+" : ""}${normalized.toFixed(digits)}`;
}

function compactNumber(value: number): string {
  const magnitude = Math.abs(value);
  if (magnitude >= 100) return value.toFixed(0);
  if (magnitude >= 10) return value.toFixed(1);
  if (magnitude >= 1) return value.toFixed(2);
  return value.toFixed(3);
}
