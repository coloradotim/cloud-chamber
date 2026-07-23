import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SimulationNotes } from "./SimulationNotes";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SimulationNotes", () => {
  it("loads, reports unsaved changes, saves, reloads, and clears a stable Simulation note", async () => {
    let savedText = "Existing observation.";
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === "PUT") {
        const body = JSON.parse(String(init.body)) as { text: string };
        savedText = body.text.trim();
      }
      return new Response(
        JSON.stringify({
          note: savedText
            ? {
                schema_version: 1,
                world_id: "supercells",
                simulation_id: "supercells_quarter_circle_reference",
                text: savedText,
                created_at: "2026-07-23T00:00:00Z",
                updated_at: "2026-07-23T00:00:00Z",
              }
            : null,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const view = render(
      <SimulationNotes
        worldId="supercells"
        simulationId="supercells_quarter_circle_reference"
        simulationName="Quarter-Circle Supercell"
      />,
    );

    const editor = await screen.findByRole("textbox", {
      name: "Notes for Quarter-Circle Supercell",
    });
    expect(editor).toHaveValue("Existing observation.");
    fireEvent.change(editor, { target: { value: "Updated observation." } });
    expect(screen.getByRole("status")).toHaveTextContent("Unsaved changes");
    fireEvent.click(screen.getByRole("button", { name: "Save note" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Saved"));

    view.unmount();
    render(
      <SimulationNotes
        worldId="supercells"
        simulationId="supercells_quarter_circle_reference"
        simulationName="Quarter-Circle Supercell"
      />,
    );
    expect(
      await screen.findByRole("textbox", { name: "Notes for Quarter-Circle Supercell" }),
    ).toHaveValue("Updated observation.");

    fireEvent.click(screen.getByRole("button", { name: "Clear note" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Note cleared"));
    expect(screen.getByRole("textbox")).toHaveValue("");
  });

  it("contains a note-specific load failure without hiding other Explore content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ detail: "The saved Simulation note is unreadable." }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );

    render(
      <div>
        <p>Science remains available.</p>
        <SimulationNotes
          worldId="mountain_waves"
          simulationId="mountain_waves_boulder_moist_reference"
          simulationName="Boulder Windstorm"
        />
      </div>,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The saved Simulation note is unreadable.",
    );
    expect(screen.getByText("Science remains available.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });

  it("keeps an unsaved note editable when saving fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ note: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "The Simulation note could not be saved." }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <SimulationNotes
        worldId="trade_cumulus"
        simulationId="trade_cumulus_canonical_bomex"
        simulationName="Canonical BOMEX Baseline"
      />,
    );

    const editor = await screen.findByRole("textbox", {
      name: "Notes for Canonical BOMEX Baseline",
    });
    fireEvent.change(editor, { target: { value: "Keep this draft." } });
    fireEvent.click(screen.getByRole("button", { name: "Save note" }));

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "The Simulation note could not be saved.",
      ),
    );
    expect(editor).toHaveValue("Keep this draft.");
    expect(editor).toBeEnabled();
    expect(screen.getByRole("button", { name: "Save note" })).toBeEnabled();
  });

  it("does not retain another Simulation's note when identity changes", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            note: {
              schema_version: 1,
              world_id: "mountain_waves",
              simulation_id: "mountain_waves_boulder_moist_reference",
              text: "Boulder note.",
              created_at: "2026-07-23T00:00:00Z",
              updated_at: "2026-07-23T00:00:00Z",
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Simulation unavailable." }), {
          status: 404,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const view = render(
      <SimulationNotes
        worldId="mountain_waves"
        simulationId="mountain_waves_boulder_moist_reference"
        simulationName="Boulder Windstorm"
      />,
    );
    expect(await screen.findByRole("textbox", { name: "Notes for Boulder Windstorm" })).toHaveValue(
      "Boulder note.",
    );

    view.rerender(
      <SimulationNotes
        worldId="mountain_waves"
        simulationId="mountain_waves_dry_ridge"
        simulationName="Dry Ridge"
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Simulation unavailable.");
    expect(screen.queryByText("Boulder note.")).not.toBeInTheDocument();
  });
});
