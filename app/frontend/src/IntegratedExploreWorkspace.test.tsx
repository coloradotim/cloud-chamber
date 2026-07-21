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

    expect(
      screen.getByRole("heading", { name: "Trade Cumulus / Canonical BOMEX Baseline" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Back to Trade Cumulus" }));
    fireEvent.click(screen.getByRole("button", { name: "Compare" }));
    expect(onBack).toHaveBeenCalledOnce();
    expect(onCompare).toHaveBeenCalledOnce();
  });

  it("switches inspector sections and preserves the active section across collapse", () => {
    render(
      <ExploreInspector
        sections={{
          explain: <p>Authored explanation</p>,
          science: <p>Shallow-cloud evidence</p>,
          notes: <p>No note recorded</p>,
          details: <p>Technical provenance</p>,
        }}
      />,
    );

    expect(screen.getByText("Authored explanation")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Science" }));
    expect(screen.getByText("Shallow-cloud evidence")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Collapse inspector" }));
    expect(screen.getByLabelText("Explore inspector")).toHaveAttribute("data-collapsed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Open inspector" }));
    expect(screen.getByText("Shallow-cloud evidence")).toBeVisible();
  });
});
