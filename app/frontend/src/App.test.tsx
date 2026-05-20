import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders Cloud Chamber identity and CM1 distinction", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Cloud Chamber" })).toBeInTheDocument();
    expect(screen.getByText(/CM1 is the high-fidelity simulation engine/)).toBeInTheDocument();
    expect(screen.getByText("Scenario builder")).toBeInTheDocument();
  });
});
