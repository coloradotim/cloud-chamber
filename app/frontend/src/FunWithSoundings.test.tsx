import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FunWithSoundings } from "./FunWithSoundings";

describe("FunWithSoundings", () => {
  it("keeps the selected atmosphere visible while moving among the five jobs", () => {
    const onSectionChange = vi.fn();
    render(
      <FunWithSoundings
        activeSection="candidates"
        selectedAtmosphere={{
          station: "Denver / Stapleton",
          validTime: "Jul 22, 2026, 6:00 PM",
          source: "Cached recommendation",
          quality: "Valid",
          usableLevels: 84,
        }}
        onSectionChange={onSectionChange}
        onBackHome={vi.fn()}
      >
        <p>Candidate workspace</p>
      </FunWithSoundings>,
    );

    expect(screen.getByRole("heading", { name: "Fun With Soundings" })).toBeInTheDocument();
    expect(screen.getByText("Atmospheric workbench")).toBeInTheDocument();
    expect(screen.getByText("Not a Cloud World")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Denver / Stapleton" })).toBeInTheDocument();
    expect(screen.getByText("84")).toBeInTheDocument();
    expect(screen.getByText("Candidate workspace")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Build & Run/ }));
    expect(onSectionChange).toHaveBeenCalledWith("build");

    fireEvent.click(screen.getByRole("button", { name: /Explore/ }));
    expect(onSectionChange).toHaveBeenCalledWith("explore");
  });

  it("offers a direct recovery path when no atmosphere is selected", () => {
    const onSectionChange = vi.fn();
    render(
      <FunWithSoundings
        activeSection="build"
        selectedAtmosphere={null}
        onSectionChange={onSectionChange}
        onBackHome={vi.fn()}
      >
        <p>Build workspace</p>
      </FunWithSoundings>,
    );

    expect(screen.getByRole("heading", { name: "No atmosphere selected" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Find an atmosphere" }));
    expect(onSectionChange).toHaveBeenCalledWith("find");
  });
});
