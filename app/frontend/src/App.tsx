import "./App.css";

const productNote =
  "CM1 is the high-fidelity simulation engine; Cloud Chamber is the local experiment builder, run manager, and visualizer.";

export function App() {
  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">Local CM1 experiment lab</p>
        <h1>Cloud Chamber</h1>
        <p className="summary">
          Configure CM1 scenarios, manage local runs, ingest outputs, and prepare for beautiful
          scientific 3-D cloud visualization.
        </p>
      </section>

      <section className="module-grid" aria-label="Core modules">
        {[
          "Scenario builder",
          "Local CM1 run manager",
          "Result library",
          "3-D visualizer",
          "Preview explainer",
          "Data ingestion",
        ].map((module) => (
          <article className="module-card" key={module}>
            {module}
          </article>
        ))}
      </section>

      <p className="engine-note">{productNote}</p>
    </main>
  );
}
