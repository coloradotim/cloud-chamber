import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ExploreInspector, IntegratedExploreWorkspace } from "./IntegratedExploreWorkspace";

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

  it("keeps current context primary and places notes and details in secondary content", () => {
    render(
      <ExploreInspector
        sections={{
          explain: <p>Authored explanation</p>,
          notes: <p>No note recorded</p>,
          details: <p>Technical provenance</p>,
        }}
      />,
    );

    expect(screen.getByText("Authored explanation")).toBeVisible();
    expect(screen.getByLabelText("Simulation notebook")).toHaveTextContent("No note recorded");
    expect(screen.getByLabelText("Simulation technical details")).toHaveTextContent(
      "Technical provenance",
    );
    fireEvent.click(screen.getByRole("button", { name: "Collapse inspector" }));
    expect(screen.getByLabelText("Explore inspector")).toHaveAttribute("data-collapsed", "true");
    expect(screen.getByLabelText("Simulation notebook")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Open inspector" }));
    expect(screen.getByText("Authored explanation")).toBeVisible();
  });
});
