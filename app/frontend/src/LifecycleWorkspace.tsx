import { useEffect, useMemo, useState } from "react";

export type LifecycleOwnerId =
  | "trade_cumulus"
  | "mountain_waves"
  | "supercells"
  | "fun_with_soundings"
  | "legacy_unassigned";
export type LifecycleView = "activity" | "history";

type LifecycleFactState =
  | "not_applicable"
  | "unknown"
  | "absent"
  | "present"
  | "pending"
  | "passed"
  | "caveated"
  | "failed"
  | "conflict"
  | "missing"
  | "eligible"
  | "ineligible";

type LifecycleFacts = {
  scientific_work: LifecycleFactState;
  package: LifecycleFactState;
  attempt: LifecycleFactState;
  queue: LifecycleFactState;
  process: LifecycleFactState;
  expected_output: LifecycleFactState;
  technical_integrity: LifecycleFactState;
  ingest: LifecycleFactState;
  world_inspectability: LifecycleFactState;
  simulation_availability: LifecycleFactState;
  parent_eligibility: LifecycleFactState;
  retained_assets: LifecycleFactState;
};

type LifecycleAttempt = {
  attempt_id: string;
  run_id: string;
  relationship:
    | "initial"
    | "unchanged_retry"
    | "checkpoint_restart"
    | "alternate_observation_attempt"
    | "extension"
    | "later_backing_candidate";
  accepted_backing: boolean;
  manifest_path: string | null;
  lifecycle_state: string | null;
  queue_state: string | null;
  product_state: string | null;
  validation_status: string | null;
  result_id: string | null;
  output_artifact_count: number;
  size_bytes: number | null;
  retained_state: "retained" | "missing" | "conflict" | "unknown";
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  updated_at: string | null;
  message: string | null;
  failure_reason: string | null;
};

type LifecycleAction = {
  kind:
    | "run"
    | "cancel"
    | "ingest"
    | "explore"
    | "compare_parent"
    | "compare_reference"
    | "review"
    | "open_run_controls";
  label: string;
  run_id: string | null;
  manifest_path: string | null;
  result_id: string | null;
  world_id: string | null;
  simulation_id: string | null;
  target_simulation_id: string | null;
};

type LifecycleDifference = {
  category: string;
  label: string;
  before: unknown;
  after: unknown;
  units: string | null;
  material: boolean;
};

type LifecycleDependency = {
  kind: "saved_view" | "saved_comparison";
  dependency_id: string;
  title: string;
  relationship: string;
};

export type LifecycleRecord = {
  record_id: string;
  record_kind: "simulation" | "experiment";
  owner_id: LifecycleOwnerId;
  owner_label: string;
  simulation_id: string | null;
  experiment_id: string | null;
  world_id: string | null;
  recipe_id: string | null;
  recipe_version: string | null;
  parent_simulation_id: string | null;
  reference_simulation_id: string | null;
  display_name: string;
  question: string | null;
  role: string | null;
  case_id: string | null;
  differences: LifecycleDifference[];
  attempts: LifecycleAttempt[];
  facts: LifecycleFacts;
  trust_state: "trusted" | "caveated" | "failed" | "unassessed" | "unavailable";
  caveats: string[];
  tags: string[];
  notes: string | null;
  lifecycle_label: string;
  lifecycle_detail: string;
  activity_group:
    | "needs_attention"
    | "ready_to_run"
    | "queued"
    | "running"
    | "awaiting_validation_or_ingest"
    | "ready_to_inspect"
    | "available_with_caveats"
    | "recently_completed"
    | null;
  in_activity: boolean;
  created_at: string | null;
  updated_at: string | null;
  size_bytes: number | null;
  dependencies: LifecycleDependency[];
  actions: LifecycleAction[];
};

type LifecycleProjection = {
  schema_version: "1";
  generated_at: string;
  records: LifecycleRecord[];
  warnings: string[];
};

type HistoryFilters = {
  search: string;
  owner: LifecycleOwnerId | "all";
  lifecycle: string;
  availability: LifecycleFactState | "all";
  parentEligibility: LifecycleFactState | "all";
  retained: LifecycleFactState | "all";
  trust: LifecycleRecord["trust_state"] | "all";
  relationship: string;
  tag: string;
  date: "all" | "7" | "30" | "365";
  sort: "updated" | "created" | "name" | "lifecycle" | "size";
};

const DEFAULT_FILTERS: HistoryFilters = {
  search: "",
  owner: "all",
  lifecycle: "all",
  availability: "all",
  parentEligibility: "all",
  retained: "all",
  trust: "all",
  relationship: "all",
  tag: "all",
  date: "all",
  sort: "updated",
};

const ACTIVITY_GROUPS: Array<{
  id: NonNullable<LifecycleRecord["activity_group"]>;
  label: string;
}> = [
  { id: "needs_attention", label: "Needs attention" },
  { id: "running", label: "Running" },
  { id: "queued", label: "Queued" },
  { id: "ready_to_run", label: "Ready to run" },
  { id: "awaiting_validation_or_ingest", label: "Awaiting validation or ingest" },
  { id: "ready_to_inspect", label: "Ready to inspect" },
  { id: "available_with_caveats", label: "Available with caveats" },
  { id: "recently_completed", label: "Recently completed" },
];

export function LifecycleWorkspace({
  ownerIds,
  view: controlledView,
  showViewTabs = true,
  onViewChange,
  onExplore,
  onCompare,
  onOpenRunControls,
}: {
  ownerIds: LifecycleOwnerId[];
  view?: LifecycleView;
  showViewTabs?: boolean;
  onViewChange?: (view: LifecycleView) => void;
  onExplore: (record: LifecycleRecord) => void;
  onCompare?: (record: LifecycleRecord, targetSimulationId: string) => void;
  onOpenRunControls?: (record: LifecycleRecord) => void;
}) {
  const [internalView, setInternalView] = useState<LifecycleView>("activity");
  const view = controlledView ?? internalView;
  const [projection, setProjection] = useState<LifecycleProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [filters, setFilters] = useState<HistoryFilters>(DEFAULT_FILTERS);
  const [openRecordId, setOpenRecordId] = useState<string | null>(null);

  async function loadProjection() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/lifecycle");
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Activity and History are unavailable."));
      }
      const payload = (await response.json()) as LifecycleProjection;
      if (payload.schema_version !== "1" || !Array.isArray(payload.records)) {
        throw new Error("Activity and History returned an unsupported data contract.");
      }
      setProjection(payload);
    } catch (caught) {
      setProjection(null);
      setError(caught instanceof Error ? caught.message : "Activity and History are unavailable.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProjection();
  }, []);

  function changeView(nextView: LifecycleView) {
    if (controlledView === undefined) setInternalView(nextView);
    onViewChange?.(nextView);
  }

  const scopedRecords = useMemo(
    () => projection?.records.filter((record) => ownerIds.includes(record.owner_id)) ?? [],
    [ownerIds, projection],
  );
  const historyRecords = useMemo(
    () => filterAndSortHistory(scopedRecords, filters),
    [filters, scopedRecords],
  );
  const tags = useMemo(
    () => [...new Set(scopedRecords.flatMap((record) => record.tags))].sort(),
    [scopedRecords],
  );
  const relationships = useMemo(
    () =>
      [
        ...new Set(
          scopedRecords.flatMap((record) =>
            [record.parent_simulation_id, record.reference_simulation_id].filter(
              (value): value is string => Boolean(value),
            ),
          ),
        ),
      ].sort(),
    [scopedRecords],
  );

  async function runAction(record: LifecycleRecord, action: LifecycleAction) {
    if (action.kind === "explore") {
      onExplore(record);
      return;
    }
    if (action.kind === "compare_parent" || action.kind === "compare_reference") {
      if (action.target_simulation_id) onCompare?.(record, action.target_simulation_id);
      return;
    }
    if (action.kind === "open_run_controls") {
      onOpenRunControls?.(record);
      return;
    }
    if (action.kind === "review") {
      setOpenRecordId(record.record_id);
      document
        .getElementById(`lifecycle-details-${record.record_id}`)
        ?.scrollIntoView({ block: "nearest" });
      return;
    }
    const request = lifecycleActionRequest(action);
    if (!request) return;
    setActionStatus(`${action.label}: ${record.display_name}`);
    setError(null);
    try {
      const response = await fetch(request.url, request.init);
      if (!response.ok) {
        throw new Error(await responseMessage(response, `${action.label} could not complete.`));
      }
      setActionStatus(`${action.label} completed. Refreshing Activity and History...`);
      await loadProjection();
      setActionStatus(`${action.label} completed.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : `${action.label} could not complete.`);
      setActionStatus(null);
    }
  }

  return (
    <section className="lifecycle-workspace" aria-label="Activity and History">
      <header className="lifecycle-heading">
        <div>
          <p className="eyebrow">{view === "activity" ? "Activity" : "History"}</p>
          <h3>{view === "activity" ? "Current work" : "Retained scientific work"}</h3>
          <p>
            {view === "activity"
              ? "Work that can be run, inspected, or needs attention now."
              : "Simulations, Experiments, and every retained technical attempt."}
          </p>
        </div>
        <div className="lifecycle-heading-actions">
          {showViewTabs && (
            <nav className="lifecycle-view-tabs" aria-label="Lifecycle view">
              {(["activity", "history"] as LifecycleView[]).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={view === item ? "active-control" : ""}
                  aria-current={view === item ? "page" : undefined}
                  onClick={() => changeView(item)}
                >
                  {item === "activity" ? "Activity" : "History"}
                </button>
              ))}
            </nav>
          )}
          <button type="button" className="secondary-button" onClick={() => void loadProjection()}>
            Refresh
          </button>
        </div>
      </header>

      {loading && !projection && (
        <section className="status-panel" role="status">
          Loading Activity and History...
        </section>
      )}
      {error && (
        <section className="lifecycle-error" role="alert">
          <strong>Activity and History could not be loaded</strong>
          <span>{error}</span>
          <button type="button" onClick={() => void loadProjection()}>
            Retry
          </button>
        </section>
      )}
      {actionStatus && <p className="inline-status">{actionStatus}</p>}
      {projection?.warnings.map((warning) => (
        <p key={warning} className="inline-status" role="status">
          {warning}
        </p>
      ))}

      {projection && view === "activity" && (
        <ActivityView
          records={scopedRecords.filter((record) => record.in_activity)}
          openRecordId={openRecordId}
          onOpenRecord={setOpenRecordId}
          onAction={runAction}
        />
      )}
      {projection && view === "history" && (
        <>
          <HistoryToolbar
            filters={filters}
            records={scopedRecords}
            visibleCount={historyRecords.length}
            tags={tags}
            relationships={relationships}
            ownerIds={ownerIds}
            onChange={setFilters}
            onReset={() => setFilters(DEFAULT_FILTERS)}
          />
          {historyRecords.length ? (
            <div className="lifecycle-history-list">
              {historyRecords.map((record) => (
                <LifecycleCard
                  key={record.record_id}
                  record={record}
                  records={scopedRecords}
                  expanded={openRecordId === record.record_id}
                  onExpandedChange={(expanded) =>
                    setOpenRecordId(expanded ? record.record_id : null)
                  }
                  onAction={runAction}
                />
              ))}
            </div>
          ) : (
            <LifecycleEmpty
              title={scopedRecords.length ? "No records match these filters" : "History is empty"}
              body={
                scopedRecords.length
                  ? "Clear filters to return to the complete retained record."
                  : "No retained work is currently assigned to this owner."
              }
              actionLabel={scopedRecords.length ? "Clear filters" : undefined}
              onAction={scopedRecords.length ? () => setFilters(DEFAULT_FILTERS) : undefined}
            />
          )}
        </>
      )}
    </section>
  );
}

function ActivityView({
  records,
  openRecordId,
  onOpenRecord,
  onAction,
}: {
  records: LifecycleRecord[];
  openRecordId: string | null;
  onOpenRecord: (recordId: string | null) => void;
  onAction: (record: LifecycleRecord, action: LifecycleAction) => void;
}) {
  if (!records.length) {
    return (
      <LifecycleEmpty
        title="No current work"
        body="Nothing is queued, running, awaiting ingest, recently completed, or asking for attention."
      />
    );
  }
  return (
    <div className="lifecycle-activity-groups">
      {ACTIVITY_GROUPS.map((group) => {
        const matching = records.filter((record) => record.activity_group === group.id);
        if (!matching.length) return null;
        return (
          <section key={group.id} className="lifecycle-activity-group">
            <header>
              <h4>{group.label}</h4>
              <span>{matching.length}</span>
            </header>
            <div className="lifecycle-card-grid">
              {matching.map((record) => (
                <LifecycleCard
                  key={record.record_id}
                  record={record}
                  records={records}
                  expanded={openRecordId === record.record_id}
                  onExpandedChange={(expanded) => onOpenRecord(expanded ? record.record_id : null)}
                  onAction={onAction}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function LifecycleCard({
  record,
  records,
  expanded,
  onExpandedChange,
  onAction,
}: {
  record: LifecycleRecord;
  records: LifecycleRecord[];
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
  onAction: (record: LifecycleRecord, action: LifecycleAction) => void;
}) {
  const primaryActions = record.actions.filter((action) => action.kind !== "review");
  return (
    <article className={`lifecycle-card lifecycle-${record.activity_group ?? "history"}`}>
      <header>
        <div>
          <p className="eyebrow">
            {record.owner_label} ·{" "}
            {record.record_kind === "simulation" ? "Simulation" : "Experiment"}
          </p>
          <h4>{record.display_name}</h4>
        </div>
        <LifecycleBadge record={record} />
      </header>
      {record.parent_simulation_id && (
        <p className="lifecycle-relationship">
          Parent: <strong>{simulationDisplayName(record.parent_simulation_id, records)}</strong>
        </p>
      )}
      {record.question && <p className="lifecycle-question">{record.question}</p>}
      {record.differences.length > 0 && (
        <dl className="lifecycle-difference-summary">
          {record.differences.slice(0, 3).map((difference, index) => (
            <div key={`${difference.category}-${difference.label}-${index}`}>
              <dt>{difference.label}</dt>
              <dd>
                {formatValue(difference.before, difference.units)} to{" "}
                {formatValue(difference.after, difference.units)}
              </dd>
            </div>
          ))}
        </dl>
      )}
      <div className="lifecycle-state-line">
        <strong>{record.lifecycle_label}</strong>
        <span>{record.lifecycle_detail}</span>
      </div>
      <div className="lifecycle-card-meta">
        <span>{relativeDate(record.updated_at)}</span>
        <span>
          {record.attempts.length} attempt{record.attempts.length === 1 ? "" : "s"}
        </span>
        {record.facts.parent_eligibility !== "not_applicable" && (
          <span>{factLabel("Variation parent", record.facts.parent_eligibility)}</span>
        )}
      </div>
      {primaryActions.length > 0 && (
        <div className="button-row lifecycle-actions">
          {primaryActions.map((action) => (
            <button
              key={`${action.kind}-${action.target_simulation_id ?? ""}`}
              type="button"
              className={
                action.kind === "cancel"
                  ? "danger-button"
                  : action.kind === "explore" || action.kind === "run"
                    ? ""
                    : "secondary-button"
              }
              onClick={() => void onAction(record, action)}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
      <details
        id={`lifecycle-details-${record.record_id}`}
        className="lifecycle-details"
        open={expanded}
        onToggle={(event) => onExpandedChange(event.currentTarget.open)}
      >
        <summary>Technical details</summary>
        <LifecycleTechnicalDetails record={record} />
      </details>
    </article>
  );
}

function simulationDisplayName(simulationId: string, records: LifecycleRecord[]): string {
  return (
    records.find((candidate) => candidate.simulation_id === simulationId)?.display_name ??
    humanize(simulationId)
  );
}

function LifecycleTechnicalDetails({ record }: { record: LifecycleRecord }) {
  return (
    <div className="lifecycle-technical-content">
      <dl className="lifecycle-facts">
        {Object.entries(record.facts).map(([label, value]) => (
          <div key={label}>
            <dt>{humanize(label)}</dt>
            <dd className={`fact-${value}`}>{humanize(value)}</dd>
          </div>
        ))}
      </dl>
      <dl className="lifecycle-identifiers">
        <Identifier label="Record" value={record.record_id} />
        <Identifier label="Simulation" value={record.simulation_id} />
        <Identifier label="Experiment" value={record.experiment_id} />
        <Identifier label="Recipe" value={record.recipe_id} />
        <Identifier label="Case" value={record.case_id} />
        <Identifier label="Reference" value={record.reference_simulation_id} />
      </dl>
      {record.attempts.length > 0 && (
        <section className="lifecycle-attempts" aria-label="Technical attempts">
          <h5>Attempts</h5>
          {record.attempts.map((attempt) => (
            <article key={attempt.attempt_id}>
              <div>
                <strong>{attemptRelationshipLabel(attempt.relationship)}</strong>
                {attempt.accepted_backing && (
                  <span className="lifecycle-backing">Backing output</span>
                )}
              </div>
              <code>{attempt.run_id}</code>
              <span>
                {humanize(attempt.queue_state ?? attempt.lifecycle_state ?? "unknown")} ·{" "}
                {attempt.output_artifact_count.toLocaleString()} output artifacts
              </span>
              {attempt.failure_reason && <p role="alert">{attempt.failure_reason}</p>}
              {attempt.manifest_path && <code>{attempt.manifest_path}</code>}
            </article>
          ))}
        </section>
      )}
      {record.dependencies.length > 0 && (
        <section className="lifecycle-dependencies" aria-label="Saved state dependencies">
          <h5>Saved-state dependencies</h5>
          {record.dependencies.map((dependency) => (
            <p key={`${dependency.kind}-${dependency.dependency_id}`}>
              <strong>{dependency.title}</strong>
              <span>{dependency.relationship}</span>
            </p>
          ))}
        </section>
      )}
      {record.caveats.length > 0 && (
        <section className="lifecycle-caveats">
          <h5>Caveats</h5>
          <ul>
            {record.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </section>
      )}
      {record.tags.length > 0 && <p className="lifecycle-tags">Tags: {record.tags.join(", ")}</p>}
      {record.notes && (
        <section className="lifecycle-notes">
          <h5>Legacy note</h5>
          <p>{record.notes}</p>
        </section>
      )}
    </div>
  );
}

function HistoryToolbar({
  filters,
  records,
  visibleCount,
  tags,
  relationships,
  ownerIds,
  onChange,
  onReset,
}: {
  filters: HistoryFilters;
  records: LifecycleRecord[];
  visibleCount: number;
  tags: string[];
  relationships: string[];
  ownerIds: LifecycleOwnerId[];
  onChange: (filters: HistoryFilters) => void;
  onReset: () => void;
}) {
  const update = (patch: Partial<HistoryFilters>) => onChange({ ...filters, ...patch });
  const filtersActive = JSON.stringify(filters) !== JSON.stringify(DEFAULT_FILTERS);
  return (
    <section className="lifecycle-history-toolbar" aria-label="History filters">
      <div className="lifecycle-primary-filters">
        <label>
          <span>Search</span>
          <input
            type="search"
            value={filters.search}
            placeholder="name, question, tag, or technical ID"
            onChange={(event) => update({ search: event.target.value })}
          />
        </label>
        <label>
          <span>Sort</span>
          <select
            value={filters.sort}
            onChange={(event) => update({ sort: event.target.value as HistoryFilters["sort"] })}
          >
            <option value="updated">Recently updated</option>
            <option value="created">Recently created</option>
            <option value="name">Name</option>
            <option value="lifecycle">Lifecycle</option>
            <option value="size">Retained size</option>
          </select>
        </label>
        <p>
          {visibleCount} of {records.length}
        </p>
      </div>
      <details className="lifecycle-more-filters">
        <summary>More filters</summary>
        <div>
          {ownerIds.length > 1 && (
            <FilterSelect
              label="Owner"
              value={filters.owner}
              options={[
                ["all", "All owners"],
                ...ownerIds.map((owner) => [owner, ownerLabel(owner)] as [string, string]),
              ]}
              onChange={(value) => update({ owner: value as HistoryFilters["owner"] })}
            />
          )}
          <FilterSelect
            label="Lifecycle"
            value={filters.lifecycle}
            options={[
              ["all", "All lifecycle states"],
              ...[...new Set(records.map((record) => record.lifecycle_label))]
                .sort()
                .map((value) => [value, value] as [string, string]),
            ]}
            onChange={(lifecycle) => update({ lifecycle })}
          />
          <FilterSelect
            label="Availability"
            value={filters.availability}
            options={factOptions("All availability states")}
            onChange={(value) => update({ availability: value as HistoryFilters["availability"] })}
          />
          <FilterSelect
            label="Parent eligibility"
            value={filters.parentEligibility}
            options={factOptions("All eligibility states")}
            onChange={(value) =>
              update({ parentEligibility: value as HistoryFilters["parentEligibility"] })
            }
          />
          <FilterSelect
            label="Retained output"
            value={filters.retained}
            options={factOptions("All retained states")}
            onChange={(value) => update({ retained: value as HistoryFilters["retained"] })}
          />
          <FilterSelect
            label="Trust"
            value={filters.trust}
            options={[
              ["all", "All trust states"],
              ["trusted", "Trusted"],
              ["caveated", "Caveated"],
              ["failed", "Failed"],
              ["unassessed", "Unassessed"],
              ["unavailable", "Unavailable"],
            ]}
            onChange={(value) => update({ trust: value as HistoryFilters["trust"] })}
          />
          <FilterSelect
            label="Parent or reference"
            value={filters.relationship}
            options={[
              ["all", "All relationships"],
              ...relationships.map((value) => [value, humanize(value)] as [string, string]),
            ]}
            onChange={(relationship) => update({ relationship })}
          />
          <FilterSelect
            label="Existing tag"
            value={filters.tag}
            options={[
              ["all", "All tags"],
              ...tags.map((value) => [value, value] as [string, string]),
            ]}
            onChange={(tag) => update({ tag })}
          />
          <FilterSelect
            label="Updated"
            value={filters.date}
            options={[
              ["all", "Any date"],
              ["7", "Last 7 days"],
              ["30", "Last 30 days"],
              ["365", "Last year"],
            ]}
            onChange={(value) => update({ date: value as HistoryFilters["date"] })}
          />
        </div>
      </details>
      {filtersActive && (
        <button type="button" className="quiet-button" onClick={onReset}>
          Clear filters
        </button>
      )}
    </section>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<[string, string]>;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span>{label}</span>
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

function LifecycleBadge({ record }: { record: LifecycleRecord }) {
  const tone =
    record.activity_group === "needs_attention" || record.trust_state === "failed"
      ? "danger"
      : record.trust_state === "caveated" || record.lifecycle_label.includes("caveat")
        ? "warning"
        : record.lifecycle_label === "Running"
          ? "active"
          : "neutral";
  return <span className={`lifecycle-badge ${tone}`}>{record.lifecycle_label}</span>;
}

function LifecycleEmpty({
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
    <section className="lifecycle-empty">
      <h4>{title}</h4>
      <p>{body}</p>
      {actionLabel && onAction && (
        <button type="button" className="secondary-button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </section>
  );
}

function Identifier({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        <code>{value}</code>
      </dd>
    </div>
  );
}

function filterAndSortHistory(
  records: LifecycleRecord[],
  filters: HistoryFilters,
): LifecycleRecord[] {
  const query = filters.search.trim().toLocaleLowerCase();
  const cutoff =
    filters.date === "all"
      ? null
      : Date.now() - Number.parseInt(filters.date, 10) * 24 * 60 * 60 * 1_000;
  return records
    .filter((record) => {
      const searchable = [
        record.display_name,
        record.question,
        record.record_id,
        record.simulation_id,
        record.experiment_id,
        record.case_id,
        record.recipe_id,
        record.parent_simulation_id,
        record.reference_simulation_id,
        ...record.tags,
        ...record.attempts.flatMap((attempt) => [attempt.attempt_id, attempt.run_id]),
      ]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase();
      return (
        (!query || searchable.includes(query)) &&
        (filters.owner === "all" || record.owner_id === filters.owner) &&
        (filters.lifecycle === "all" || record.lifecycle_label === filters.lifecycle) &&
        (filters.availability === "all" ||
          record.facts.simulation_availability === filters.availability) &&
        (filters.parentEligibility === "all" ||
          record.facts.parent_eligibility === filters.parentEligibility) &&
        (filters.retained === "all" || record.facts.retained_assets === filters.retained) &&
        (filters.trust === "all" || record.trust_state === filters.trust) &&
        (filters.relationship === "all" ||
          record.parent_simulation_id === filters.relationship ||
          record.reference_simulation_id === filters.relationship) &&
        (filters.tag === "all" || record.tags.includes(filters.tag)) &&
        (cutoff === null ||
          Boolean(record.updated_at && new Date(record.updated_at).getTime() >= cutoff))
      );
    })
    .sort((left, right) => {
      if (filters.sort === "name") return left.display_name.localeCompare(right.display_name);
      if (filters.sort === "lifecycle")
        return left.lifecycle_label.localeCompare(right.lifecycle_label);
      if (filters.sort === "size") return (right.size_bytes ?? -1) - (left.size_bytes ?? -1);
      const field = filters.sort === "created" ? "created_at" : "updated_at";
      return (right[field] ?? "").localeCompare(left[field] ?? "");
    });
}

function lifecycleActionRequest(
  action: LifecycleAction,
): { url: string; init: RequestInit } | null {
  if (action.kind === "run" && action.manifest_path) {
    return {
      url: "/api/runs/queue",
      init: {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifest_path: action.manifest_path }),
      },
    };
  }
  if (action.kind === "cancel") {
    return { url: "/api/runs/cancel", init: { method: "POST" } };
  }
  if (action.kind === "ingest" && action.manifest_path) {
    return {
      url: "/api/results/ingest",
      init: {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifest_path: action.manifest_path }),
      },
    };
  }
  return null;
}

function factOptions(firstLabel: string): Array<[string, string]> {
  return [
    ["all", firstLabel],
    ["present", "Present"],
    ["pending", "Pending"],
    ["passed", "Passed"],
    ["caveated", "Caveated"],
    ["eligible", "Eligible"],
    ["ineligible", "Ineligible"],
    ["missing", "Missing"],
    ["failed", "Failed"],
    ["conflict", "Conflict"],
    ["unknown", "Unknown"],
    ["not_applicable", "Not applicable"],
  ];
}

function formatValue(value: unknown, units: string | null): string {
  const formatted =
    typeof value === "number"
      ? value.toLocaleString(undefined, { maximumFractionDigits: 4 })
      : typeof value === "string"
        ? value
        : JSON.stringify(value);
  return `${formatted ?? "unknown"}${units ? ` ${units}` : ""}`;
}

function relativeDate(value: string | null): string {
  if (!value) return "Time unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: date.getFullYear() === new Date().getFullYear() ? undefined : "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function factLabel(label: string, value: LifecycleFactState): string {
  return `${label}: ${humanize(value)}`;
}

function attemptRelationshipLabel(value: LifecycleAttempt["relationship"]): string {
  const labels: Record<LifecycleAttempt["relationship"], string> = {
    initial: "Initial attempt",
    unchanged_retry: "Unchanged retry",
    checkpoint_restart: "Checkpoint restart",
    alternate_observation_attempt: "Alternate observation attempt",
    extension: "Extension",
    later_backing_candidate: "Later backing candidate",
  };
  return labels[value];
}

function ownerLabel(owner: LifecycleOwnerId): string {
  const labels: Record<LifecycleOwnerId, string> = {
    trade_cumulus: "Trade Cumulus",
    mountain_waves: "Mountain Waves",
    supercells: "Supercells",
    fun_with_soundings: "Fun With Soundings",
    legacy_unassigned: "Legacy / unassigned",
  };
  return labels[owner];
}

function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase())
    .replace(/\bCm1\b/g, "CM1")
    .replace(/\bBomex\b/g, "BOMEX")
    .replace(/\bR(\d+) (\d+)\b/g, "r$1.$2")
    .replace(/\bV(\d+)\b/g, "v$1")
    .replace(/\bQuarter Circle\b/g, "Quarter-Circle")
    .replace(/\bStraight Line\b/g, "Straight-Line");
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}
