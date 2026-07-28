import type { ReactNode } from "react";

export type FunWithSoundingsSection = "find" | "candidates" | "build" | "activity" | "explore";

export type SelectedAtmosphereSummary = {
  station: string;
  validTime: string;
  source: string;
  quality: string;
  usableLevels: number;
};

const SECTIONS: Array<{
  id: FunWithSoundingsSection;
  label: string;
  description: string;
}> = [
  {
    id: "find",
    label: "Find Soundings",
    description: "Find a cached atmosphere or load an IGRA station file.",
  },
  {
    id: "candidates",
    label: "Candidates",
    description: "Screen, compare, and keep atmospheric candidates.",
  },
  {
    id: "build",
    label: "Build & Run",
    description: "Configure a bounded experiment and create its package.",
  },
  {
    id: "activity",
    label: "Activity & History",
    description: "Track current work and return to retained Experiments.",
  },
  {
    id: "explore",
    label: "Explore",
    description: "Inspect completed, ingested sounding experiments.",
  },
];

export function FunWithSoundings({
  activeSection,
  selectedAtmosphere,
  children,
  onSectionChange,
  onBackHome,
}: {
  activeSection: FunWithSoundingsSection;
  selectedAtmosphere: SelectedAtmosphereSummary | null;
  children: ReactNode;
  onSectionChange: (section: FunWithSoundingsSection) => void;
  onBackHome: () => void;
}) {
  return (
    <section className="soundings-workbench" aria-labelledby="soundings-workbench-title">
      <nav className="world-breadcrumb" aria-label="Breadcrumb">
        <button type="button" onClick={onBackHome}>
          Cloud Chamber
        </button>
        <span aria-hidden="true">/</span>
        <span>Fun With Soundings</span>
      </nav>

      <header className="soundings-workbench-header">
        <div>
          <p className="eyebrow">Atmospheric workbench</p>
          <h2 id="soundings-workbench-title">Fun With Soundings</h2>
          <p>
            Begin with an observed atmosphere, ask a bounded question, and follow the experiment
            from source evidence through retained output.
          </p>
        </div>
        <div className="soundings-workbench-identity" aria-label="Workbench identity">
          <span>Observed or user-supplied atmosphere</span>
          <strong>Not a Cloud World</strong>
        </div>
      </header>

      <nav className="soundings-job-nav" aria-label="Fun With Soundings sections">
        {SECTIONS.map((section, index) => (
          <button
            key={section.id}
            type="button"
            className={section.id === activeSection ? "active-control" : ""}
            aria-current={section.id === activeSection ? "page" : undefined}
            onClick={() => onSectionChange(section.id)}
          >
            <span>{index + 1}</span>
            <strong>{section.label}</strong>
          </button>
        ))}
      </nav>

      {activeSection !== "activity" &&
        activeSection !== "explore" &&
        (selectedAtmosphere || activeSection !== "find") && (
          <section
            className={`selected-atmosphere-strip${
              selectedAtmosphere ? " has-selected-atmosphere" : ""
            }`}
            aria-label="Selected atmosphere"
          >
            <div>
              <p className="eyebrow">Selected atmosphere</p>
              {selectedAtmosphere ? (
                <>
                  <h3>{selectedAtmosphere.station}</h3>
                  <p>
                    {selectedAtmosphere.validTime} · {selectedAtmosphere.source}
                  </p>
                </>
              ) : (
                <>
                  <h3>No atmosphere selected</h3>
                  <p>Choose a sounding in Find Soundings to continue.</p>
                </>
              )}
            </div>
            {selectedAtmosphere ? (
              <dl>
                <div>
                  <dt>Quality</dt>
                  <dd>{selectedAtmosphere.quality}</dd>
                </div>
                <div>
                  <dt>Usable levels</dt>
                  <dd>{selectedAtmosphere.usableLevels.toLocaleString()}</dd>
                </div>
              </dl>
            ) : (
              <button
                type="button"
                className="secondary-button"
                onClick={() => onSectionChange("find")}
              >
                Find an atmosphere
              </button>
            )}
          </section>
        )}

      <div className="soundings-job-content">{children}</div>
    </section>
  );
}
