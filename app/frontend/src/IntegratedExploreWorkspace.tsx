import { type ReactNode, useState } from "react";

export type ExploreInspectorSection = "explain" | "science" | "notes" | "details";

type InspectorSections = Record<ExploreInspectorSection, ReactNode>;

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
        <div>
          <p className="eyebrow">Explore</p>
          <h2>
            <span>{worldName}</span>
            <span> / </span>
            <span>{simulationName}</span>
          </h2>
        </div>
        {(onBack || onCompare) && (
          <div className="integrated-explore-actions">
            {onBack && (
              <button type="button" className="secondary-button" onClick={onBack}>
                {backLabel ?? `Back to ${worldName}`}
              </button>
            )}
            {onCompare && (
              <button type="button" onClick={onCompare}>
                Compare
              </button>
            )}
          </div>
        )}
      </header>
      {children}
    </section>
  );
}

export function ExploreInspector({ sections }: { sections: InspectorSections }) {
  const [activeSection, setActiveSection] = useState<ExploreInspectorSection>("explain");
  const [collapsed, setCollapsed] = useState(false);
  const labels: Array<{ id: ExploreInspectorSection; label: string }> = [
    { id: "explain", label: "Explain" },
    { id: "science", label: "Science" },
    { id: "notes", label: "Notes" },
    { id: "details", label: "Details" },
  ];

  return (
    <aside
      className={`explore-inspector${collapsed ? " explore-inspector-collapsed" : ""}`}
      aria-label="Explore inspector"
      data-collapsed={collapsed ? "true" : "false"}
    >
      <header className="explore-inspector-header">
        <strong>Inspector</strong>
        <button
          type="button"
          className="secondary-button"
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Open inspector" : "Collapse inspector"}
          onClick={() => setCollapsed((current) => !current)}
        >
          {collapsed ? "Open" : "Collapse"}
        </button>
      </header>
      <div hidden={collapsed}>
        <nav className="explore-inspector-tabs" aria-label="Explore inspector sections">
          {labels.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              className={activeSection === id ? "active-control" : ""}
              aria-pressed={activeSection === id}
              onClick={() => setActiveSection(id)}
            >
              {label}
            </button>
          ))}
        </nav>
        {labels.map(({ id, label }) => (
          <section
            key={id}
            className="explore-inspector-panel"
            aria-label={`${label} inspector`}
            hidden={activeSection !== id}
          >
            {sections[id]}
          </section>
        ))}
      </div>
    </aside>
  );
}
