import { type KeyboardEvent, type ReactNode, useId, useRef, useState } from "react";

export type ExploreSecondarySection = "science" | "notes" | "details";

export type ExploreSecondaryContent = Record<ExploreSecondarySection, ReactNode>;

export type ExploreContextMetric = {
  label: string;
  value: ReactNode;
};

export function IntegratedExploreWorkspace({
  worldName,
  simulationName,
  backLabel,
  onBack,
  onCompare,
  children,
}: {
  worldName: string;
  simulationName: string;
  backLabel?: string;
  onBack?: () => void;
  onCompare?: () => void;
  children: ReactNode;
}) {
  return (
    <section className="integrated-explore-workspace" aria-label={`${simulationName} Explore`}>
      <header className="integrated-explore-header">
        <div className="integrated-explore-identity">
          {onBack && (
            <button
              type="button"
              className="integrated-explore-back"
              aria-label={backLabel ?? `Back to ${worldName}`}
              onClick={onBack}
            >
              <span aria-hidden="true">&lsaquo;</span> {worldName}
            </button>
          )}
          <h2>{simulationName}</h2>
        </div>
        {onCompare && (
          <div className="integrated-explore-actions">
            <button type="button" onClick={onCompare}>
              Compare
            </button>
          </div>
        )}
      </header>
      {children}
    </section>
  );
}

export function ExploreInspector({
  id,
  children,
  collapsed: controlledCollapsed,
  onCollapsedChange,
  showCollapseControl = true,
}: {
  id?: string;
  children: ReactNode;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  showCollapseControl?: boolean;
}) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const collapsed = controlledCollapsed ?? internalCollapsed;

  function toggleCollapsed() {
    const next = !collapsed;
    if (controlledCollapsed === undefined) setInternalCollapsed(next);
    onCollapsedChange?.(next);
  }

  if (collapsed && !showCollapseControl) return null;

  return (
    <aside
      id={id}
      className={`explore-inspector${collapsed ? " explore-inspector-collapsed" : ""}`}
      aria-label="Context"
      data-collapsed={collapsed ? "true" : "false"}
    >
      <header className="explore-inspector-header">
        {!collapsed && <strong>Context</strong>}
        {showCollapseControl && (
          <button
            type="button"
            className="explore-inspector-toggle"
            aria-expanded={!collapsed}
            aria-label={collapsed ? "Show Context" : "Hide Context"}
            title={collapsed ? "Show Context" : "Hide Context"}
            onClick={toggleCollapsed}
          >
            <span aria-hidden="true">{collapsed ? "\u00ab" : "\u00bb"}</span>
          </button>
        )}
      </header>
      <div hidden={collapsed}>
        <section className="explore-inspector-panel" aria-label="Current scientific context">
          {children}
        </section>
      </div>
    </aside>
  );
}

export function ExploreContextContent({
  identity,
  question,
  explanation,
  selectedEvidence,
  whatToNotice,
  orientation,
  selectionPrompt,
}: {
  identity: string;
  question: string;
  explanation: ReactNode;
  selectedEvidence?: ReactNode;
  whatToNotice?: ReactNode;
  orientation: ExploreContextMetric[];
  selectionPrompt?: ReactNode;
}) {
  return (
    <section className="explore-context-content">
      <p className="eyebrow">{identity}</p>
      <h3>{question}</h3>
      {selectedEvidence}
      <div className="explore-context-explanation">{explanation}</div>
      {whatToNotice && (
        <section className="explore-context-notice" aria-label="What to notice now">
          <strong>What to notice now</strong>
          <div>{whatToNotice}</div>
        </section>
      )}
      <dl className="context-metrics">
        {orientation.map((metric) => (
          <div key={metric.label}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
          </div>
        ))}
      </dl>
      {selectionPrompt && <p className="context-selection-prompt">{selectionPrompt}</p>}
    </section>
  );
}

export function ExploreSelectedEvidence({
  eyebrow,
  title,
  states,
  metrics,
  onClear,
  className,
}: {
  eyebrow: string;
  title: string;
  states?: string[];
  metrics: ExploreContextMetric[];
  onClear: () => void;
  className?: string;
}) {
  return (
    <section
      className={`selected-region-inspector explore-selected-evidence${
        className ? ` ${className}` : ""
      }`}
      aria-label="Selected native-grid evidence"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h4>{title}</h4>
        </div>
        <button type="button" className="secondary-button" onClick={onClear}>
          Clear
        </button>
      </div>
      {states && states.length > 0 && (
        <div className="explore-context-state-row">
          {states.map((state) => (
            <span key={state} className="state-chip">
              {state}
            </span>
          ))}
        </div>
      )}
      <dl className="context-metrics">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function ExploreSecondarySections({
  sections,
  label = "Simulation support",
}: {
  sections: ExploreSecondaryContent;
  label?: string;
}) {
  const [activeSection, setActiveSection] = useState<ExploreSecondarySection>("science");
  const baseId = useId();
  const tabRefs = useRef<Partial<Record<ExploreSecondarySection, HTMLButtonElement | null>>>({});
  const orderedSections: ExploreSecondarySection[] = ["science", "notes", "details"];

  function selectSection(section: ExploreSecondarySection, focus = false) {
    setActiveSection(section);
    if (focus) tabRefs.current[section]?.focus();
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    section: ExploreSecondarySection,
  ) {
    const index = orderedSections.indexOf(section);
    let next: ExploreSecondarySection | undefined;
    if (event.key === "ArrowRight") {
      next = orderedSections[(index + 1) % orderedSections.length];
    } else if (event.key === "ArrowLeft") {
      next = orderedSections[(index - 1 + orderedSections.length) % orderedSections.length];
    } else if (event.key === "Home") {
      next = orderedSections[0];
    } else if (event.key === "End") {
      next = orderedSections[orderedSections.length - 1];
    }
    if (!next) return;
    event.preventDefault();
    selectSection(next, true);
  }

  return (
    <section className="explore-secondary-content" aria-label={label}>
      <nav className="explore-secondary-tabs" aria-label={`${label} sections`} role="tablist">
        {orderedSections.map((section) => (
          <button
            key={section}
            ref={(node) => {
              tabRefs.current[section] = node;
            }}
            type="button"
            id={`${baseId}-${section}-tab`}
            role="tab"
            className={activeSection === section ? "active-control" : ""}
            aria-selected={activeSection === section}
            aria-controls={`${baseId}-${section}-panel`}
            tabIndex={activeSection === section ? 0 : -1}
            onClick={() => selectSection(section)}
            onKeyDown={(event) => handleKeyDown(event, section)}
          >
            {section[0].toUpperCase() + section.slice(1)}
          </button>
        ))}
      </nav>
      {orderedSections.map((section) => (
        <section
          key={section}
          id={`${baseId}-${section}-panel`}
          className="explore-secondary-panel"
          role="tabpanel"
          aria-labelledby={`${baseId}-${section}-tab`}
          hidden={activeSection !== section}
        >
          {sections[section]}
        </section>
      ))}
    </section>
  );
}
