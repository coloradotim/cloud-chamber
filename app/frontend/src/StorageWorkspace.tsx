import { useEffect, useMemo, useState } from "react";

import "./StorageWorkspace.css";

type AssetComponent = {
  component: string;
  size_bytes: number;
  file_count: number;
  uncounted_file_count: number;
};
type AssetDependency = {
  kind: string;
  dependency_id: string;
  title: string;
  relationship: string;
  available: boolean;
};
type RetainedAsset = {
  asset_id: string;
  stable_name: string;
  owner_id: string;
  owner_label: string;
  asset_class: string;
  lifecycle_role: string;
  record_role: string | null;
  world_id: string | null;
  simulation_id: string | null;
  experiment_id: string | null;
  recipe_id: string | null;
  recipe_version: string | null;
  parent_simulation_id: string | null;
  reference_simulation_id: string | null;
  attempt_id: string | null;
  attempt_lifecycle_state: string | null;
  attempt_queue_state: string | null;
  attempt_process_state: string | null;
  attempt_validation_status: string | null;
  run_id: string | null;
  result_id: string | null;
  case_id: string | null;
  question: string | null;
  tags: string[];
  technical_path: string | null;
  size_bytes: number | null;
  partially_uncounted: boolean;
  uncounted_path_count: number;
  components: AssetComponent[];
  created_at: string | null;
  modified_at: string | null;
  last_used_at: string | null;
  built_in: boolean;
  accepted_backing: string;
  availability_state: string;
  protection_state: string;
  repairability_state: string;
  trust_state: string;
  caveats: string[];
  recreation_method: string | null;
  dependencies: AssetDependency[];
  required_for_explore: boolean;
  required_for_compare: boolean;
  required_for_parent_reuse: boolean;
  required_for_repair: boolean;
};
type UsageGroup = { id: string; label: string; size_bytes: number; asset_count: number };
type AssetInventory = {
  generated_at: string;
  runtime_home: string;
  total_usage_bytes: number;
  free_space_bytes: number;
  system_protected_bytes: number;
  ordinary_retained_bytes: number;
  temporary_bytes: number;
  uncounted_asset_count: number;
  warning_threshold_bytes: number;
  minimum_free_space_bytes: number;
  above_usage_warning: boolean;
  below_minimum_free_space: boolean;
  usage_by_owner: UsageGroup[];
  usage_by_class: UsageGroup[];
  state_counts: Record<string, number>;
  lifecycle_counts: Record<string, number>;
  trust_counts: Record<string, number>;
  assets: RetainedAsset[];
  performance: {
    cache_hit: boolean;
    scan_duration_ms: number;
    scanned_file_count: number;
    fingerprinted_path_count: number;
    fingerprint: string;
  };
  warnings: string[];
};
type RunCostProfile = {
  world_id: string;
  world_name: string;
  recipe_id: string;
  profile_id: string;
  profile_name: string;
  role: string;
  numerical_realization: {
    domain: string;
    grid: string;
    spacing: string;
    timestep_strategy: string;
    physics_source: string;
  };
  observation_plan: {
    duration_seconds: number | null;
    output_cadence_seconds: number | null;
    expected_history_count: number | null;
    retained_field_inventory: string[];
  };
  expected_runtime_min_seconds: number | null;
  expected_runtime_max_seconds: number | null;
  expected_size_min_bytes: number | null;
  expected_size_max_bytes: number | null;
  estimate_basis: string;
  confidence: string;
  cost_change_reasons: string[];
  scientific_limitations: string[];
  required_post_run_reserve_bytes: number;
};
type RunCostEstimate = {
  profile: RunCostProfile;
  current_free_space_bytes: number;
  projected_free_space_bytes: number | null;
  required_free_space_bytes: number | null;
  disposition: "passes" | "blocked";
  disposition_reason: string;
};
type LaunchReviewRecord = {
  snapshot: {
    snapshot_id: string;
    created_at: string;
    estimate: RunCostEstimate;
    review_free_space_bytes: number;
    warning_threshold_bytes: number;
    minimum_free_space_bytes: number;
    manifest_binding: {
      attempt_id: string;
      world_id: string;
      recipe_id: string;
      recipe_version: string;
      profile_id: string;
      specification_fingerprint: string;
    } | null;
  };
  immediate_prelaunch_checks: Array<{
    check_id: string;
    check_kind: "planning" | "launch";
    attempt_id: string | null;
    specification_fingerprint: string | null;
    checked_at: string;
    current_free_space_bytes: number;
    expected_size_high_bytes: number | null;
    required_post_run_reserve_bytes: number;
    projected_free_space_bytes: number | null;
    disposition: "passes" | "blocked";
    reason: string;
  }>;
};
type Filters = {
  search: string;
  owner: string;
  assetClass: string;
  state: string;
  lifecycle: string;
  trust: string;
  builtIn: string;
  dependents: string;
  backing: string;
  size: string;
  date: string;
  tag: string;
  sort: string;
};

const DEFAULT_FILTERS: Filters = {
  search: "",
  owner: "all",
  assetClass: "all",
  state: "all",
  lifecycle: "all",
  trust: "all",
  builtIn: "all",
  dependents: "all",
  backing: "all",
  size: "all",
  date: "all",
  tag: "",
  sort: "size",
};

export function StorageWorkspace() {
  const [inventory, setInventory] = useState<AssetInventory | null>(null);
  const [estimates, setEstimates] = useState<RunCostEstimate[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [launchReview, setLaunchReview] = useState<LaunchReviewRecord | null>(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [budgetStatus, setBudgetStatus] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([fetchAssetInventory(false), fetchRunCostCatalog()])
      .then(([nextInventory, nextEstimates]) => {
        if (!active) return;
        setInventory(nextInventory);
        setEstimates(nextEstimates);
        setSelectedProfileId(nextEstimates[0]?.profile.profile_id ?? "");
      })
      .catch((caught) => {
        if (active) setError(errorMessage(caught, "Storage could not be loaded."));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedEstimate =
    estimates.find((item) => item.profile.profile_id === selectedProfileId) ?? null;
  const visibleAssets = useMemo(
    () => filterAndSortAssets(inventory?.assets ?? [], filters),
    [filters, inventory?.assets],
  );

  async function refreshInventory() {
    setRefreshing(true);
    setError(null);
    try {
      const [nextInventory, nextEstimates] = await Promise.all([
        fetchAssetInventory(true),
        fetchRunCostCatalog(),
      ]);
      setInventory(nextInventory);
      setEstimates(nextEstimates);
    } catch (caught) {
      setError(errorMessage(caught, "Storage could not be refreshed."));
    } finally {
      setRefreshing(false);
    }
  }

  async function recordLaunchReview() {
    if (!selectedProfileId) return;
    setBudgetStatus("Recording budget review...");
    try {
      const record = await postJson<LaunchReviewRecord>("/api/storage/launch-reviews", {
        profile_id: selectedProfileId,
      });
      setLaunchReview(record);
      setBudgetStatus("Planning snapshot recorded.");
    } catch (caught) {
      setBudgetStatus(errorMessage(caught, "Budget review could not be recorded."));
    }
  }

  async function recheckLaunchBudget() {
    if (!launchReview) return;
    setBudgetStatus("Rechecking current free space...");
    try {
      const record = await postJson<LaunchReviewRecord>("/api/storage/launch-reviews/preflight", {
        snapshot_id: launchReview.snapshot.snapshot_id,
      });
      setLaunchReview(record);
      setBudgetStatus(record.immediate_prelaunch_checks.at(-1)?.reason ?? "Budget checked.");
    } catch (caught) {
      setBudgetStatus(errorMessage(caught, "The launch budget could not be checked."));
    }
  }

  if (loading) {
    return (
      <section className="storage-page storage-state-panel" aria-label="Storage">
        <p className="eyebrow">Storage</p>
        <h2>Reading retained assets</h2>
        <p>Cloud Chamber is loading cached asset identities and current disk facts.</p>
      </section>
    );
  }

  if (!inventory) {
    return (
      <section className="storage-page storage-state-panel" aria-label="Storage">
        <p className="eyebrow">Storage</p>
        <h2>Storage is unavailable</h2>
        <p role="alert">{error ?? "The retained-asset inventory could not be read."}</p>
        <button type="button" onClick={() => void refreshInventory()}>
          Retry
        </button>
      </section>
    );
  }

  return (
    <section className="storage-page" aria-labelledby="storage-title">
      <header className="storage-page-heading">
        <div>
          <p className="eyebrow">Global utility</p>
          <h2 id="storage-title">Storage</h2>
          <p>Retained scientific assets, their dependencies, and launch budget.</p>
        </div>
        <button
          type="button"
          className="secondary-button"
          disabled={refreshing}
          onClick={() => void refreshInventory()}
        >
          {refreshing ? "Refreshing..." : "Refresh inventory"}
        </button>
      </header>

      {error && (
        <p className="storage-alert" role="alert">
          {error}
        </p>
      )}
      {inventory.warnings.length > 0 && (
        <p className="storage-alert" role="status">
          {inventory.warnings.join(" ")}
        </p>
      )}

      <StorageOverview inventory={inventory} />

      {selectedEstimate && (
        <LaunchBudgetPanel
          estimates={estimates}
          selectedEstimate={selectedEstimate}
          selectedProfileId={selectedProfileId}
          launchReview={launchReview}
          status={budgetStatus}
          onProfileChange={(profileId) => {
            setSelectedProfileId(profileId);
            setLaunchReview(null);
            setBudgetStatus(null);
          }}
          onRecord={() => void recordLaunchReview()}
          onRecheck={() => void recheckLaunchBudget()}
        />
      )}

      <section className="storage-collection" aria-labelledby="storage-assets-title">
        <div className="storage-section-heading">
          <div>
            <p className="eyebrow">Inventory</p>
            <h3 id="storage-assets-title">Retained assets</h3>
          </div>
          <span className="storage-result-count">
            {visibleAssets.length} of {inventory.assets.length}
          </span>
        </div>
        <StorageFilters filters={filters} assets={inventory.assets} onChange={setFilters} />
        {visibleAssets.length === 0 ? (
          <div className="storage-empty">
            <h4>No assets match these filters</h4>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setFilters(DEFAULT_FILTERS)}
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="storage-asset-list" aria-label="Retained asset list">
            {visibleAssets.map((asset) => (
              <AssetRow key={asset.asset_id} asset={asset} />
            ))}
          </div>
        )}
      </section>
    </section>
  );
}

function StorageOverview({ inventory }: { inventory: AssetInventory }) {
  return (
    <section className="storage-overview" aria-labelledby="storage-overview-title">
      <div className="storage-section-heading">
        <div>
          <p className="eyebrow">Current disk</p>
          <h3 id="storage-overview-title">Retained locally</h3>
        </div>
        <span className="storage-updated">
          Inventory {inventory.performance.cache_hit ? "loaded from cache" : "scanned"} ·{" "}
          {formatDateTime(inventory.generated_at)}
        </span>
      </div>
      <dl className="storage-metric-row">
        <StorageMetric label="Retained usage" value={formatBytes(inventory.total_usage_bytes)} />
        <StorageMetric label="Free disk" value={formatBytes(inventory.free_space_bytes)} />
        <StorageMetric
          label="System-protected"
          value={formatBytes(inventory.system_protected_bytes)}
        />
        <StorageMetric
          label="Ordinary retained"
          value={formatBytes(inventory.ordinary_retained_bytes)}
        />
        <StorageMetric
          label="Usage warning"
          value={formatBytes(inventory.warning_threshold_bytes)}
          warning={inventory.above_usage_warning}
        />
        <StorageMetric
          label="Minimum free"
          value={formatBytes(inventory.minimum_free_space_bytes)}
          warning={inventory.below_minimum_free_space}
        />
      </dl>
      {inventory.above_usage_warning && (
        <p className="storage-alert" role="status">
          Retained usage has reached the configured {formatBytes(inventory.warning_threshold_bytes)}{" "}
          warning threshold.
        </p>
      )}
      <UsageBars groups={inventory.usage_by_owner} total={inventory.total_usage_bytes} />
      <div className="storage-summary-columns">
        <UsageList title="By owner" groups={inventory.usage_by_owner} />
        <UsageList title="By asset class" groups={inventory.usage_by_class} />
        <StateSummary inventory={inventory} />
      </div>
    </section>
  );
}

function LaunchBudgetPanel({
  estimates,
  selectedEstimate,
  selectedProfileId,
  launchReview,
  status,
  onProfileChange,
  onRecord,
  onRecheck,
}: {
  estimates: RunCostEstimate[];
  selectedEstimate: RunCostEstimate;
  selectedProfileId: string;
  launchReview: LaunchReviewRecord | null;
  status: string | null;
  onProfileChange: (profileId: string) => void;
  onRecord: () => void;
  onRecheck: () => void;
}) {
  const profile = selectedEstimate.profile;
  const latestCheck = launchReview?.immediate_prelaunch_checks.at(-1) ?? null;
  const disposition = latestCheck?.disposition ?? selectedEstimate.disposition;
  return (
    <section className="storage-budget" aria-labelledby="storage-budget-title">
      <div className="storage-section-heading">
        <div>
          <p className="eyebrow">Run planning</p>
          <h3 id="storage-budget-title">Launch budget</h3>
        </div>
        <span className={`storage-disposition ${disposition}`}>{disposition}</span>
      </div>
      <div className="storage-budget-layout">
        <div className="storage-budget-profile">
          <label>
            World run profile
            <select
              value={selectedProfileId}
              onChange={(event) => onProfileChange(event.target.value)}
            >
              {groupEstimates(estimates).map(([worldName, items]) => (
                <optgroup key={worldName} label={worldName}>
                  {items.map((item) => (
                    <option key={item.profile.profile_id} value={item.profile.profile_id}>
                      {item.profile.profile_name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>
          <p className="storage-budget-confidence">{profile.confidence}</p>
          <details>
            <summary>Numerical realization and observation plan</summary>
            <dl className="storage-technical-grid">
              <Detail label="Recipe" value={profile.recipe_id} />
              <Detail label="Grid" value={profile.numerical_realization.grid} />
              <Detail label="Spacing" value={profile.numerical_realization.spacing} />
              <Detail label="Timestep" value={profile.numerical_realization.timestep_strategy} />
              <Detail
                label="Duration"
                value={formatDuration(profile.observation_plan.duration_seconds)}
              />
              <Detail
                label="Saved output"
                value={
                  profile.observation_plan.expected_history_count === null
                    ? "Configuration-dependent"
                    : `${profile.observation_plan.expected_history_count} histories`
                }
              />
              <Detail
                label="Retained fields"
                value={profile.observation_plan.retained_field_inventory.join(", ")}
              />
            </dl>
          </details>
        </div>
        <dl className="storage-budget-facts">
          <StorageMetric
            label="Expected runtime"
            value={formatRange(
              profile.expected_runtime_min_seconds,
              profile.expected_runtime_max_seconds,
              formatDuration,
            )}
          />
          <StorageMetric
            label="Expected retained size"
            value={formatRange(
              profile.expected_size_min_bytes,
              profile.expected_size_max_bytes,
              formatBytes,
            )}
          />
          <StorageMetric label="Estimate basis" value={humanize(profile.estimate_basis)} />
          <StorageMetric
            label="Current free space"
            value={formatBytes(
              latestCheck?.current_free_space_bytes ?? selectedEstimate.current_free_space_bytes,
            )}
          />
          <StorageMetric
            label="Required safety margin"
            value={formatBytes(profile.required_post_run_reserve_bytes)}
          />
          <StorageMetric
            label="Projected free after completion"
            value={formatMaybeBytes(
              latestCheck?.projected_free_space_bytes ??
                selectedEstimate.projected_free_space_bytes,
            )}
            warning={disposition === "blocked"}
          />
        </dl>
      </div>
      <p className={`storage-budget-reason ${disposition}`}>
        {latestCheck?.reason ?? selectedEstimate.disposition_reason}
      </p>
      <p className="storage-budget-scope">
        This planning snapshot records the profile and current disk budget. A CM1 launch must use a
        separate snapshot bound to its exact packaged attempt.
      </p>
      <div className="storage-budget-actions">
        <button type="button" onClick={onRecord}>
          Record budget review
        </button>
        {launchReview && (
          <button type="button" className="secondary-button" onClick={onRecheck}>
            Recheck current budget
          </button>
        )}
        {launchReview && (
          <span>
            Planning snapshot {launchReview.snapshot.snapshot_id.slice(0, 8)} ·{" "}
            {formatDateTime(launchReview.snapshot.created_at)}
          </span>
        )}
      </div>
      {status && (
        <p className="storage-budget-status" role="status">
          {status}
        </p>
      )}
    </section>
  );
}

function StorageFilters({
  filters,
  assets,
  onChange,
}: {
  filters: Filters;
  assets: RetainedAsset[];
  onChange: (filters: Filters) => void;
}) {
  const update = (patch: Partial<Filters>) => onChange({ ...filters, ...patch });
  const owners = uniqueOptions(assets.map((asset) => [asset.owner_id, asset.owner_label]));
  const classes = uniqueOptions(
    assets.map((asset) => [asset.asset_class, classLabel(asset.asset_class)]),
  );
  const lifecycles = uniqueOptions(
    assets
      .filter((asset) => asset.attempt_lifecycle_state)
      .map((asset) => [
        asset.attempt_lifecycle_state as string,
        humanize(asset.attempt_lifecycle_state as string),
      ]),
  );
  const trustStates = uniqueOptions(
    assets.map((asset) => [asset.trust_state, humanize(asset.trust_state)]),
  );
  return (
    <div className="storage-filter-bar">
      <div className="storage-primary-filters">
        <label>
          Search
          <input
            type="search"
            value={filters.search}
            placeholder="name, World, Simulation, run, question"
            onChange={(event) => update({ search: event.target.value })}
          />
        </label>
        <SelectFilter
          label="Owner"
          value={filters.owner}
          onChange={(owner) => update({ owner })}
          options={[["all", "All owners"], ...owners]}
        />
        <SelectFilter
          label="Asset"
          value={filters.assetClass}
          onChange={(assetClass) => update({ assetClass })}
          options={[["all", "All asset classes"], ...classes]}
        />
        <SelectFilter
          label="Sort"
          value={filters.sort}
          onChange={(sort) => update({ sort })}
          options={[
            ["size", "Largest first"],
            ["name", "Stable name"],
            ["modified", "Recently modified"],
            ["owner", "Owner"],
            ["state", "Protection / availability"],
            ["lifecycle", "Attempt lifecycle"],
            ["trust", "Trust"],
            ["dependents", "Most dependents"],
          ]}
        />
      </div>
      <details className="storage-more-filters">
        <summary>More filters</summary>
        <div>
          <SelectFilter
            label="Protection / availability"
            value={filters.state}
            onChange={(state) => update({ state })}
            options={[
              ["all", "All states"],
              ["protected", "System-protected"],
              ["ordinary", "Ordinary"],
              ["temporary", "Temporary attempt"],
              ["missing", "Missing"],
              ["invalid", "Invalid"],
              ["conflicted", "Conflicted"],
              ["potentially_repairable", "Potentially repairable"],
            ]}
          />
          <SelectFilter
            label="Attempt lifecycle"
            value={filters.lifecycle}
            onChange={(lifecycle) => update({ lifecycle })}
            options={[["all", "All lifecycle states"], ...lifecycles]}
          />
          <SelectFilter
            label="Trust"
            value={filters.trust}
            onChange={(trust) => update({ trust })}
            options={[["all", "All trust states"], ...trustStates]}
          />
          <SelectFilter
            label="Ownership"
            value={filters.builtIn}
            onChange={(builtIn) => update({ builtIn })}
            options={[
              ["all", "Built-in and user-created"],
              ["yes", "Built-in only"],
              ["no", "User-created only"],
            ]}
          />
          <SelectFilter
            label="Dependents"
            value={filters.dependents}
            onChange={(dependents) => update({ dependents })}
            options={[
              ["all", "With or without dependents"],
              ["yes", "Has dependents"],
              ["no", "No dependents"],
            ]}
          />
          <SelectFilter
            label="Backing"
            value={filters.backing}
            onChange={(backing) => update({ backing })}
            options={[
              ["all", "Any backing relationship"],
              ["accepted", "Accepted backing"],
              ["alternate", "Alternate / nonbacking"],
            ]}
          />
          <SelectFilter
            label="Size"
            value={filters.size}
            onChange={(size) => update({ size })}
            options={[
              ["all", "All sizes"],
              ["small", "Under 100 MB"],
              ["medium", "100 MB to 1 GB"],
              ["large", "1 GB or larger"],
              ["unknown", "Uncounted"],
            ]}
          />
          <SelectFilter
            label="Modified"
            value={filters.date}
            onChange={(date) => update({ date })}
            options={[
              ["all", "Any date"],
              ["7d", "Past 7 days"],
              ["30d", "Past 30 days"],
              ["365d", "Past year"],
            ]}
          />
          <label>
            Existing tag
            <input
              value={filters.tag}
              placeholder="exact or partial tag"
              onChange={(event) => update({ tag: event.target.value })}
            />
          </label>
          <button
            type="button"
            className="secondary-button"
            onClick={() => onChange(DEFAULT_FILTERS)}
          >
            Clear filters
          </button>
        </div>
      </details>
    </div>
  );
}

function SelectFilter({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[][];
  onChange: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </label>
  );
}

function AssetRow({ asset }: { asset: RetainedAsset }) {
  const state = assetState(asset);
  return (
    <article className={`storage-asset-row state-${state}`}>
      <header>
        <div>
          <p className="eyebrow">
            {asset.owner_label} · {classLabel(asset.asset_class)}
          </p>
          <h4>{asset.stable_name}</h4>
          {asset.question && <p>{asset.question}</p>}
        </div>
        <div className="storage-asset-size">
          <strong>{formatMaybeBytes(asset.size_bytes)}</strong>
          <span className={`storage-state-chip ${state}`}>{stateLabel(asset)}</span>
        </div>
      </header>
      <div className="storage-asset-meta">
        <span>{humanize(asset.lifecycle_role)}</span>
        {asset.attempt_lifecycle_state && (
          <span>Lifecycle: {humanize(asset.attempt_lifecycle_state)}</span>
        )}
        <span>Trust: {humanize(asset.trust_state)}</span>
        {asset.accepted_backing === "accepted" && <span>Accepted backing</span>}
        {asset.accepted_backing === "alternate" && <span>Alternate attempt</span>}
        {asset.dependencies.length > 0 && (
          <span>
            {asset.dependencies.length} dependent{" "}
            {asset.dependencies.length === 1 ? "record" : "records"}
          </span>
        )}
        {asset.modified_at && <span>Modified {formatDateTime(asset.modified_at)}</span>}
        {asset.partially_uncounted && (
          <span>
            Partially uncounted · {asset.uncounted_path_count} unreadable{" "}
            {asset.uncounted_path_count === 1 ? "path" : "paths"}
          </span>
        )}
      </div>
      <details className="storage-asset-details">
        <summary>Technical details</summary>
        <div className="storage-asset-detail-grid">
          <dl className="storage-technical-grid">
            <Detail label="Asset ID" value={asset.asset_id} />
            <Detail label="Record role" value={humanize(asset.record_role ?? "not recorded")} />
            <Detail label="Attempt relationship" value={humanize(asset.lifecycle_role)} />
            <Detail
              label="Attempt lifecycle"
              value={humanize(asset.attempt_lifecycle_state ?? "not recorded")}
            />
            <Detail
              label="Queue state"
              value={humanize(asset.attempt_queue_state ?? "not recorded")}
            />
            <Detail
              label="Process state"
              value={humanize(asset.attempt_process_state ?? "not recorded")}
            />
            <Detail
              label="Validation"
              value={humanize(asset.attempt_validation_status ?? "not recorded")}
            />
            <Detail label="Run ID" value={asset.run_id ?? "Not applicable"} />
            <Detail label="Simulation" value={asset.simulation_id ?? "Not applicable"} />
            <Detail label="Experiment" value={asset.experiment_id ?? "Not applicable"} />
            <Detail label="Recipe" value={asset.recipe_id ?? "Unknown"} />
            <Detail label="Case" value={asset.case_id ?? "Unknown"} />
            <Detail label="Trust" value={humanize(asset.trust_state)} />
            <Detail label="Repairability" value={humanize(asset.repairability_state)} />
            <Detail label="Local path" value={asset.technical_path ?? "Unavailable"} />
            <Detail label="Last used" value={asset.last_used_at ?? "Not recorded"} />
          </dl>
          <section>
            <h5>Components</h5>
            {asset.components.length > 0 ? (
              <ul className="storage-component-list">
                {asset.components.map((component) => (
                  <li key={component.component}>
                    <span>
                      {humanize(component.component)} · {component.file_count} files
                      {component.uncounted_file_count > 0
                        ? ` · ${component.uncounted_file_count} unreadable`
                        : ""}
                    </span>
                    <strong>{formatBytes(component.size_bytes)}</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No local bytes can be counted.</p>
            )}
          </section>
          <section>
            <h5>Dependent records</h5>
            {asset.dependencies.length > 0 ? (
              <ul className="storage-dependency-list">
                {asset.dependencies.map((dependency) => (
                  <li
                    key={`${dependency.kind}-${dependency.dependency_id}-${dependency.relationship}`}
                  >
                    <strong>{dependency.title}</strong>
                    <span>{dependency.relationship}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No durable dependents are recorded.</p>
            )}
          </section>
        </div>
        {asset.caveats.length > 0 && <p className="storage-caveats">{asset.caveats.join(" ")}</p>}
      </details>
    </article>
  );
}

function UsageBars({ groups, total }: { groups: UsageGroup[]; total: number }) {
  return (
    <div className="storage-usage-bar" aria-label="Retained usage by owner">
      {groups
        .filter((group) => group.size_bytes > 0)
        .map((group, index) => (
          <span
            key={group.id}
            className={`owner-${index % 5}`}
            title={`${group.label}: ${formatBytes(group.size_bytes)}`}
            style={{ width: `${total > 0 ? (group.size_bytes / total) * 100 : 0}%` }}
          />
        ))}
    </div>
  );
}

function UsageList({ title, groups }: { title: string; groups: UsageGroup[] }) {
  return (
    <section>
      <h4>{title}</h4>
      <ul className="storage-usage-list">
        {groups.map((group) => (
          <li key={group.id}>
            <span>
              {group.label} · {group.asset_count}
            </span>
            <strong>{formatBytes(group.size_bytes)}</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}

function StateSummary({ inventory }: { inventory: AssetInventory }) {
  return (
    <section className="storage-state-summary">
      <h4>Protection and availability</h4>
      <ul className="storage-usage-list">
        {Object.entries(inventory.state_counts).map(([state, count]) => (
          <li key={state}>
            <span>{humanize(state)}</span>
            <strong>{count}</strong>
          </li>
        ))}
        {inventory.uncounted_asset_count > 0 && (
          <li>
            <span>Bytes unavailable</span>
            <strong>{inventory.uncounted_asset_count}</strong>
          </li>
        )}
      </ul>
      <h4>Attempt lifecycle</h4>
      <CountList counts={inventory.lifecycle_counts} emptyLabel="No attempts recorded" />
      <h4>Trust</h4>
      <CountList counts={inventory.trust_counts} emptyLabel="No trust facts recorded" />
    </section>
  );
}

function CountList({
  counts,
  emptyLabel,
}: {
  counts: Record<string, number>;
  emptyLabel: string;
}) {
  const entries = Object.entries(counts);
  return (
    <ul className="storage-usage-list">
      {entries.length === 0 ? (
        <li>
          <span>{emptyLabel}</span>
        </li>
      ) : (
        entries.map(([state, count]) => (
          <li key={state}>
            <span>{humanize(state)}</span>
            <strong>{count}</strong>
          </li>
        ))
      )}
    </ul>
  );
}

function StorageMetric({
  label,
  value,
  warning = false,
}: {
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <div className={warning ? "warning" : ""}>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function filterAndSortAssets(assets: RetainedAsset[], filters: Filters): RetainedAsset[] {
  const search = filters.search.trim().toLocaleLowerCase();
  const tag = filters.tag.trim().toLocaleLowerCase();
  const now = Date.now();
  const filtered = assets.filter((asset) => {
    const haystack = [
      asset.stable_name,
      asset.owner_label,
      asset.simulation_id,
      asset.experiment_id,
      asset.question,
      asset.run_id,
      asset.result_id,
      asset.case_id,
      asset.asset_id,
      asset.record_role,
      asset.lifecycle_role,
      asset.attempt_lifecycle_state,
      asset.attempt_queue_state,
      asset.attempt_process_state,
      asset.attempt_validation_status,
      asset.trust_state,
      ...asset.tags,
    ]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase();
    return (
      (!search || haystack.includes(search)) &&
      (filters.owner === "all" || asset.owner_id === filters.owner) &&
      (filters.assetClass === "all" || asset.asset_class === filters.assetClass) &&
      (filters.state === "all" || assetState(asset) === filters.state) &&
      (filters.lifecycle === "all" ||
        asset.attempt_lifecycle_state === filters.lifecycle) &&
      (filters.trust === "all" || asset.trust_state === filters.trust) &&
      (filters.builtIn === "all" || asset.built_in === (filters.builtIn === "yes")) &&
      (filters.dependents === "all" ||
        asset.dependencies.length > 0 === (filters.dependents === "yes")) &&
      (filters.backing === "all" || asset.accepted_backing === filters.backing) &&
      matchesSize(asset.size_bytes, filters.size) &&
      matchesDate(asset.modified_at, filters.date, now) &&
      (!tag || asset.tags.some((candidate) => candidate.toLocaleLowerCase().includes(tag)))
    );
  });
  return filtered.sort((left, right) => {
    if (filters.sort === "name") return left.stable_name.localeCompare(right.stable_name);
    if (filters.sort === "modified")
      return (right.modified_at ?? "").localeCompare(left.modified_at ?? "");
    if (filters.sort === "owner") return left.owner_label.localeCompare(right.owner_label);
    if (filters.sort === "state") return stateLabel(left).localeCompare(stateLabel(right));
    if (filters.sort === "lifecycle")
      return (left.attempt_lifecycle_state ?? "").localeCompare(
        right.attempt_lifecycle_state ?? "",
      );
    if (filters.sort === "trust") return left.trust_state.localeCompare(right.trust_state);
    if (filters.sort === "dependents") return right.dependencies.length - left.dependencies.length;
    return (right.size_bytes ?? -1) - (left.size_bytes ?? -1);
  });
}

function matchesSize(size: number | null, filter: string): boolean {
  if (filter === "all") return true;
  if (filter === "unknown") return size === null;
  if (size === null) return false;
  if (filter === "small") return size < 100 * 1024 ** 2;
  if (filter === "medium") return size >= 100 * 1024 ** 2 && size < 1024 ** 3;
  return size >= 1024 ** 3;
}

function matchesDate(value: string | null, filter: string, now: number): boolean {
  if (filter === "all") return true;
  if (!value) return false;
  const days = filter === "7d" ? 7 : filter === "30d" ? 30 : 365;
  return now - Date.parse(value) <= days * 24 * 60 * 60 * 1000;
}

function assetState(asset: RetainedAsset): string {
  if (asset.availability_state !== "retained") return asset.availability_state;
  if (asset.protection_state === "system_protected") return "protected";
  if (asset.protection_state === "temporary") return "temporary";
  if (["repairable", "rerunnable"].includes(asset.repairability_state))
    return "potentially_repairable";
  return "ordinary";
}

function stateLabel(asset: RetainedAsset): string {
  return humanize(assetState(asset));
}

function classLabel(value: string): string {
  return (
    {
      simulation_output: "Simulation output",
      experiment_output: "Experiment output",
      attempt: "Attempt",
      package_logs: "Package and logs",
      derived_cache: "Derived cache",
      source_asset: "Source asset",
      durable_metadata: "Durable metadata",
    }[value] ?? humanize(value)
  );
}

function groupEstimates(estimates: RunCostEstimate[]): Array<[string, RunCostEstimate[]]> {
  const grouped = new Map<string, RunCostEstimate[]>();
  estimates.forEach((estimate) => {
    grouped.set(estimate.profile.world_name, [
      ...(grouped.get(estimate.profile.world_name) ?? []),
      estimate,
    ]);
  });
  return [...grouped.entries()];
}

function uniqueOptions(values: string[][]): string[][] {
  return [...new Map(values.map(([value, label]) => [value, label])).entries()];
}

async function fetchAssetInventory(refresh: boolean): Promise<AssetInventory> {
  const response = await fetch(`/api/storage/assets${refresh ? "?refresh=true" : ""}`);
  if (!response.ok)
    throw new Error(await responseError(response, "Storage inventory unavailable."));
  return response.json() as Promise<AssetInventory>;
}

async function fetchRunCostCatalog(): Promise<RunCostEstimate[]> {
  const response = await fetch("/api/storage/run-cost-profiles");
  if (!response.ok)
    throw new Error(await responseError(response, "Run-cost profiles unavailable."));
  const payload = (await response.json()) as { estimates: RunCostEstimate[] };
  return payload.estimates;
}

async function postJson<T>(url: string, body: object): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await responseError(response, "Request failed."));
  return response.json() as Promise<T>;
}

async function responseError(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

function errorMessage(value: unknown, fallback: string): string {
  return value instanceof Error ? value.message : fallback;
}

function formatBytes(value: number): string {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let display = value;
  let index = 0;
  while (display >= 1024 && index < units.length - 1) {
    display /= 1024;
    index += 1;
  }
  return `${display >= 10 || index === 0 ? display.toFixed(0) : display.toFixed(1)} ${units[index]}`;
}

function formatMaybeBytes(value: number | null): string {
  return value === null ? "Uncharacterized" : formatBytes(value);
}

function formatDuration(value: number | null): string {
  if (value === null) return "Configuration-dependent";
  if (value >= 3600) {
    const hours = value / 3600;
    return `${Number.isInteger(hours) ? hours.toFixed(0) : hours.toFixed(1)} h`;
  }
  if (value >= 60) return `${Math.round(value / 60)} min`;
  return `${value} s`;
}

function formatRange(
  minimum: number | null,
  maximum: number | null,
  formatter: (value: number) => string,
): string {
  if (minimum === null || maximum === null) return "Uncharacterized";
  return `${formatter(minimum)} to ${formatter(maximum)}`;
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) return value;
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function humanize(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
