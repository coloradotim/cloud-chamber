import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  ExploreContextContent,
  ExploreInspector,
  ExploreSecondarySections,
  IntegratedExploreWorkspace,
} from "./IntegratedExploreWorkspace";

describe("IntegratedExploreWorkspace", () => {
  it("leads with stable product identity and bounded actions", () => {
    const onBack = vi.fn();
    const onCompare = vi.fn();
    render(
      <IntegratedExploreWorkspace
        worldName="Trade Cumulus"
        simulationName="Canonical BOMEX Baseline"
        onBack={onBack}
        onCompare={onCompare}
      >
        <p>Coordinated views</p>
      </IntegratedExploreWorkspace>,
    );

    expect(screen.getByRole("heading", { name: "Canonical BOMEX Baseline" })).toBeInTheDocument();
    expect(screen.queryByText("Trade Cumulus / Canonical BOMEX Baseline")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Back to Trade Cumulus" }));
    fireEvent.click(screen.getByRole("button", { name: "Compare" }));
    expect(onBack).toHaveBeenCalledOnce();
    expect(onCompare).toHaveBeenCalledOnce();
  });

  it("keeps one context-sensitive sidebar that collapses independently", () => {
    render(
      <ExploreInspector
        children={
          <ExploreContextContent
            identity="Updraft Lens"
            question="Where is air rising through cloud?"
            explanation={<p>Warm colors show rising air.</p>}
            selectedEvidence={<p>Selected cell evidence</p>}
            orientation={[{ label: "Model time", value: "1,200 s" }]}
          />
        }
      />,
    );

    expect(screen.getByText("Selected cell evidence")).toBeVisible();
    expect(screen.getByLabelText("Context")).toHaveAttribute("data-collapsed", "false");
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Hide Context" }));
    expect(screen.getByLabelText("Context")).toHaveAttribute("data-collapsed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Show Context" }));
    expect(screen.getByText("Warm colors show rising air.")).toBeVisible();
  });

  it("places Science, Notes, and Details in one accessible below-workspace navigator", () => {
    render(
      <ExploreSecondarySections
        sections={{
          science: <p>Selected native evidence</p>,
          notes: <p>Simulation notes</p>,
          details: <p>Run lineage</p>,
        }}
      />,
    );

    const tablist = screen.getByRole("tablist", { name: "Simulation support sections" });
    expect(screen.getByRole("tab", { name: "Science" })).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("tab", { name: "Notes" }));
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Simulation notes");
    fireEvent.keyDown(screen.getByRole("tab", { name: "Notes" }), { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: "Details" })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(screen.getByRole("tab", { name: "Details" }), { key: "Home" });
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Selected native evidence");
    expect(screen.getByRole("tab", { name: "Science" })).toHaveAttribute("aria-selected", "true");
    expect(tablist).toBeVisible();
  });
});
