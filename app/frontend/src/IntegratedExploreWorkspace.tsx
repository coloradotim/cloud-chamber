import { type ReactNode, useState } from "react";

type InspectorSections = {
  explain: ReactNode;
  notes: ReactNode;
  details: ReactNode;
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

export function ExploreInspector({ sections }: { sections: InspectorSections }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <aside
        className={`explore-inspector${collapsed ? " explore-inspector-collapsed" : ""}`}
        aria-label="Explore inspector"
        data-collapsed={collapsed ? "true" : "false"}
      >
        <header className="explore-inspector-header">
          {!collapsed && <strong>Context</strong>}
          <button
            type="button"
            className="explore-inspector-toggle"
            aria-expanded={!collapsed}
            aria-label={collapsed ? "Open inspector" : "Collapse inspector"}
            title={collapsed ? "Open inspector" : "Collapse inspector"}
            onClick={() => setCollapsed((current) => !current)}
          >
            <span aria-hidden="true">{collapsed ? "\u00ab" : "\u00bb"}</span>
          </button>
        </header>
        <div hidden={collapsed}>
          <section className="explore-inspector-panel" aria-label="Context inspector">
            {sections.explain}
          </section>
        </div>
      </aside>
      <section className="explore-secondary-content" aria-label="Simulation notebook and details">
        <section aria-label="Simulation notebook">{sections.notes}</section>
        <section aria-label="Simulation technical details">{sections.details}</section>
      </section>
    </>
  );
}
