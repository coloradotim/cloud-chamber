import { type FormEvent, useEffect, useId, useState } from "react";

const MAX_SIMULATION_NOTE_CHARACTERS = 20_000;

type SimulationNoteRecord = {
  schema_version: number;
  world_id: string;
  simulation_id: string;
  text: string;
  created_at: string;
  updated_at: string;
};

type SimulationNoteResponse = {
  note: SimulationNoteRecord | null;
};

type NoteState = "loading" | "saved" | "unsaved" | "saving" | "failed";

export function SimulationNotes({
  worldId,
  simulationId,
  simulationName,
}: {
  worldId: string;
  simulationId: string;
  simulationName: string;
}) {
  const editorId = useId();
  const [draft, setDraft] = useState("");
  const [savedText, setSavedText] = useState("");
  const [state, setState] = useState<NoteState>("loading");
  const [message, setMessage] = useState("Loading note...");
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setDraft("");
    setSavedText("");
    setState("loading");
    setMessage("Loading note...");
    void loadSimulationNote(worldId, simulationId, controller.signal)
      .then((response) => {
        const text = response.note?.text ?? "";
        setDraft(text);
        setSavedText(text);
        setState("saved");
        setMessage(text ? "Saved" : "No note saved yet");
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setState("failed");
        setMessage(noteErrorMessage(caught, "Unable to load this Simulation note."));
      });
    return () => controller.abort();
  }, [reloadNonce, simulationId, worldId]);

  async function saveNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setMessage("Saving...");
    try {
      const response = await putSimulationNote(worldId, simulationId, draft);
      const text = response.note?.text ?? "";
      setDraft(text);
      setSavedText(text);
      setState("saved");
      setMessage(text ? "Saved" : "Note cleared");
    } catch (caught) {
      setState("failed");
      setMessage(noteErrorMessage(caught, "Unable to save this Simulation note."));
    }
  }

  async function clearNote() {
    setState("saving");
    setMessage("Clearing...");
    try {
      await putSimulationNote(worldId, simulationId, "");
      setDraft("");
      setSavedText("");
      setState("saved");
      setMessage("Note cleared");
    } catch (caught) {
      setState("failed");
      setMessage(noteErrorMessage(caught, "Unable to clear this Simulation note."));
    }
  }

  const loadFailed = state === "failed" && savedText === "" && draft === "";
  const saving = state === "saving";
  const dirty = draft !== savedText;

  return (
    <section className="simulation-notes" aria-labelledby={`${editorId}-title`}>
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Notebook</p>
          <h3 id={`${editorId}-title`}>Simulation notes</h3>
        </div>
        <span className={`simulation-note-state simulation-note-state-${state}`} role="status">
          {message}
        </span>
      </div>
      <p className="simulation-notes-description">
        Observations and questions for {simulationName}. This note stays with the Simulation.
      </p>
      {loadFailed ? (
        <div className="simulation-note-failure">
          <p role="alert">{message}</p>
          <button type="button" onClick={() => setReloadNonce((current) => current + 1)}>
            Retry
          </button>
        </div>
      ) : (
        <form className="simulation-notes-form" onSubmit={(event) => void saveNote(event)}>
          <label htmlFor={`${editorId}-editor`}>
            <span className="sr-only">Notes for {simulationName}</span>
            <textarea
              id={`${editorId}-editor`}
              aria-label={`Notes for ${simulationName}`}
              rows={10}
              maxLength={MAX_SIMULATION_NOTE_CHARACTERS}
              placeholder="Record observations, questions, or follow-up ideas."
              value={draft}
              disabled={state === "loading" || saving}
              onChange={(event) => {
                setDraft(event.target.value);
                setState("unsaved");
                setMessage("Unsaved changes");
              }}
            />
          </label>
          <div className="simulation-notes-actions">
            <button type="submit" disabled={!dirty || saving || state === "loading"}>
              {saving ? "Saving..." : "Save note"}
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={(!draft && !savedText) || saving || state === "loading"}
              onClick={() => void clearNote()}
            >
              Clear note
            </button>
            <small>
              {draft.length.toLocaleString()} / {MAX_SIMULATION_NOTE_CHARACTERS.toLocaleString()}
            </small>
          </div>
        </form>
      )}
    </section>
  );
}

async function loadSimulationNote(
  worldId: string,
  simulationId: string,
  signal?: AbortSignal,
): Promise<SimulationNoteResponse> {
  const response = await fetch(noteUrl(worldId, simulationId), { signal });
  if (!response.ok) {
    throw new Error(await responseMessage(response, "Unable to load this Simulation note."));
  }
  return (await response.json()) as SimulationNoteResponse;
}

async function putSimulationNote(
  worldId: string,
  simulationId: string,
  text: string,
): Promise<SimulationNoteResponse> {
  const response = await fetch(noteUrl(worldId, simulationId), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    throw new Error(await responseMessage(response, "Unable to save this Simulation note."));
  }
  return (await response.json()) as SimulationNoteResponse;
}

function noteUrl(worldId: string, simulationId: string): string {
  const worldSlug = worldId.replaceAll("_", "-");
  return `/api/worlds/${encodeURIComponent(worldSlug)}/simulations/${encodeURIComponent(
    simulationId,
  )}/note`;
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || fallback;
  } catch {
    return fallback;
  }
}

function noteErrorMessage(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}
