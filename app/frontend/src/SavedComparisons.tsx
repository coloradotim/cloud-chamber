import { useCallback, useEffect, useState } from "react";

import type { ExploreWorldState } from "./ExploreStatePersistence";
import type {
  CompareDifference,
  CompareLinkModes,
  CompareWorldId,
  CompareWorldSlug,
} from "./WorldCompare.types";

import "./SavedComparisons.css";

export type SupercellsComparePresentation = {
  left: "scene" | "evidence";
  right: "scene" | "evidence";
};

export type SavedComparisonWorkspace = {
  schema_version: 1;
  world_id: CompareWorldId;
  left_simulation_id: string;
  right_simulation_id: string;
  left_state: ExploreWorldState;
  right_state: ExploreWorldState;
  links: CompareLinkModes;
  context_collapsed: boolean;
  supercells_presentation: SupercellsComparePresentation | null;
};

export type SavedComparisonRecord = {
  saved_comparison_id: string;
  title: string;
  scientific_question: string | null;
  created_at: string;
  updated_at: string;
  restoration_status: "healthy" | "partially_restorable" | "unavailable";
  restoration_message: string | null;
  captured_pair: {
    left_display_name: string;
    right_display_name: string;
    relationship: string;
    controlled_pair: boolean;
    controlled_pair_message: string;
    material_differences: CompareDifference[];
  };
  workspace: SavedComparisonWorkspace;
};

export type SavedComparisonEntry = {
  record: SavedComparisonRecord;
  dependencies: Array<{
    side: "left" | "right";
    simulation_id: string;
    display_name: string;
    available: boolean;
    availability_state: "available" | "missing" | "invalid" | "unavailable";
    availability_message: string;
    role: string | null;
    ownership: "built_in" | "user_created" | "unknown";
    protection_state: "protected" | "ordinary" | "unknown";
    repairability_state: "repairable" | "not_repairable" | "unknown";
  }>;
  effective_restoration_status: "healthy" | "partially_restorable" | "unavailable";
  effective_restoration_message: string | null;
};

export function SavedComparisonsCollection({
  worldSlug,
  onOpen,
}: {
  worldSlug: CompareWorldSlug;
  onOpen: (savedComparisonId: string) => void;
}) {
  const [entries, setEntries] = useState<SavedComparisonEntry[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setMessage(null);
    try {
      const response = await fetch(`/api/worlds/${worldSlug}/saved-comparisons`);
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Saved Comparisons could not be loaded."));
      }
      const payload = (await response.json()) as { saved_comparisons?: unknown };
      if (!Array.isArray(payload.saved_comparisons)) {
        throw new Error("Saved Comparison library returned an invalid response.");
      }
      setEntries(sortSavedComparisons(payload.saved_comparisons as SavedComparisonEntry[]));
      setStatus("ready");
    } catch (caught) {
      setEntries([]);
      setStatus("error");
      setMessage(
        caught instanceof Error ? caught.message : "Saved Comparisons could not be loaded.",
      );
    }
  }, [worldSlug]);

  useEffect(() => {
    void load();
  }, [load]);

  async function deleteRecord(entry: SavedComparisonEntry) {
    if (!window.confirm(`Delete "${entry.record.title}"? This cannot be undone.`)) return;
    setMessage("Deleting Saved Comparison...");
    try {
      const response = await fetch(
        `/api/worlds/${worldSlug}/saved-comparisons/${entry.record.saved_comparison_id}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Saved Comparison was not deleted."));
      }
      setEntries((current) =>
        current.filter(
          (item) => item.record.saved_comparison_id !== entry.record.saved_comparison_id,
        ),
      );
      setMessage("Saved Comparison deleted.");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Saved Comparison was not deleted.");
    }
  }

  async function updateRecord(
    entry: SavedComparisonEntry,
    update: { title: string; scientific_question: string | null },
  ) {
    setMessage("Updating Saved Comparison...");
    try {
      const response = await fetch(
        `/api/worlds/${worldSlug}/saved-comparisons/${entry.record.saved_comparison_id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(update),
        },
      );
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Saved Comparison was not updated."));
      }
      const updated = (await response.json()) as SavedComparisonEntry;
      setEntries((current) =>
        sortSavedComparisons(
          current.map((item) =>
            item.record.saved_comparison_id === updated.record.saved_comparison_id ? updated : item,
          ),
        ),
      );
      setEditingId(null);
      setMessage("Saved Comparison updated.");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Saved Comparison was not updated.");
    }
  }

  if (status === "loading") {
    return <section className="saved-comparison-status">Loading Saved Comparisons...</section>;
  }
  if (status === "error") {
    return (
      <section className="world-load-failure" aria-label="Saved Comparisons unavailable">
        <div>
          <h3>Saved Comparisons could not be loaded</h3>
          <p role="alert">{message}</p>
        </div>
        <button type="button" onClick={() => void load()}>
          Retry
        </button>
      </section>
    );
  }

  return (
    <section className="saved-comparison-library" aria-labelledby="saved-comparisons-title">
      <header className="world-section-heading">
        <div>
          <p className="eyebrow">Saved Comparisons</p>
          <h3 id="saved-comparisons-title">Return to a scientific examination</h3>
          <p>
            Each entry preserves both views and their coordination. Opening one reads current
            retained output.
          </p>
        </div>
        <span>{entries.length} saved</span>
      </header>
      {message && (
        <p className="saved-comparison-message" role="status">
          {message}
        </p>
      )}
      {entries.length === 0 ? (
        <div className="saved-comparison-empty">
          <h4>No Saved Comparisons yet</h4>
          <p>Open Compare, arrange both Simulations, stop playback, then save the examination.</p>
        </div>
      ) : (
        <div className="saved-comparison-list">
          {entries.map((entry) =>
            editingId === entry.record.saved_comparison_id ? (
              <SavedComparisonEdit
                key={entry.record.saved_comparison_id}
                entry={entry}
                onCancel={() => setEditingId(null)}
                onSave={(update) => void updateRecord(entry, update)}
              />
            ) : (
              <SavedComparisonRow
                key={entry.record.saved_comparison_id}
                entry={entry}
                onOpen={() => onOpen(entry.record.saved_comparison_id)}
                onEdit={() => setEditingId(entry.record.saved_comparison_id)}
                onDelete={() => void deleteRecord(entry)}
              />
            ),
          )}
        </div>
      )}
    </section>
  );
}

export function SaveComparisonControl({
  worldSlug,
  workspace,
  disabled,
  saveAsNew,
  onSaved,
}: {
  worldSlug: CompareWorldSlug;
  workspace: SavedComparisonWorkspace;
  disabled: boolean;
  saveAsNew: boolean;
  onSaved: (entry: SavedComparisonEntry) => void;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [question, setQuestion] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`/api/worlds/${worldSlug}/saved-comparisons`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          scientific_question: question.trim() || null,
          workspace,
        }),
      });
      if (!response.ok) {
        throw new Error(await responseMessage(response, "Comparison could not be saved."));
      }
      const entry = (await response.json()) as SavedComparisonEntry;
      onSaved(entry);
      setOpen(false);
      setTitle("");
      setQuestion("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Comparison could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="secondary-button"
        disabled={disabled}
        title={disabled ? "Stop playback and wait for both views to finish loading." : undefined}
        onClick={() => setOpen(true)}
      >
        {saveAsNew ? "Save as new comparison" : "Save comparison"}
      </button>
      {open && (
        <div className="saved-comparison-dialog-backdrop" role="presentation">
          <section
            className="saved-comparison-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="save-comparison-title"
          >
            <form onSubmit={(event) => void submit(event)}>
              <header>
                <p className="eyebrow">Saved Comparison</p>
                <h3 id="save-comparison-title">Name this examination</h3>
                <p>The current live workspace will be preserved as a new immutable snapshot.</p>
              </header>
              <label>
                <span>Title</span>
                <input
                  autoFocus
                  required
                  maxLength={120}
                  value={title}
                  onChange={(event) => setTitle(event.currentTarget.value)}
                />
              </label>
              <label>
                <span>Scientific question</span>
                <textarea
                  rows={3}
                  maxLength={2_000}
                  value={question}
                  onChange={(event) => setQuestion(event.currentTarget.value)}
                />
              </label>
              {error && <p role="alert">{error}</p>}
              <footer>
                <button
                  type="button"
                  className="secondary-button"
                  disabled={saving}
                  onClick={() => setOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" disabled={saving || !title.trim()}>
                  {saving ? "Saving..." : "Save comparison"}
                </button>
              </footer>
            </form>
          </section>
        </div>
      )}
    </>
  );
}

function SavedComparisonRow({
  entry,
  onOpen,
  onEdit,
  onDelete,
}: {
  entry: SavedComparisonEntry;
  onOpen: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const { record } = entry;
  return (
    <article className="saved-comparison-row">
      <div className="saved-comparison-row-main">
        <div className="saved-comparison-title-line">
          <h4>{record.title}</h4>
          <RestorationChip status={entry.effective_restoration_status} />
        </div>
        <p className="saved-comparison-pair">
          {record.captured_pair.left_display_name} <span>and</span>{" "}
          {record.captured_pair.right_display_name}
        </p>
        {record.scientific_question && <p>{record.scientific_question}</p>}
        <div className="saved-comparison-meta">
          <span>{record.captured_pair.relationship}</span>
          <span>Updated {formatDate(record.updated_at)}</span>
        </div>
        {entry.effective_restoration_message && (
          <p className="saved-comparison-restoration-note">{entry.effective_restoration_message}</p>
        )}
      </div>
      <div className="saved-comparison-actions">
        <button type="button" onClick={onOpen}>
          Open
        </button>
        <button type="button" className="secondary-button" onClick={onEdit}>
          Edit
        </button>
        <button type="button" className="danger-button" onClick={onDelete}>
          Delete
        </button>
      </div>
    </article>
  );
}

function SavedComparisonEdit({
  entry,
  onCancel,
  onSave,
}: {
  entry: SavedComparisonEntry;
  onCancel: () => void;
  onSave: (update: { title: string; scientific_question: string | null }) => void;
}) {
  const [title, setTitle] = useState(entry.record.title);
  const [question, setQuestion] = useState(entry.record.scientific_question ?? "");
  return (
    <form
      className="saved-comparison-edit"
      onSubmit={(event) => {
        event.preventDefault();
        onSave({ title, scientific_question: question.trim() || null });
      }}
    >
      <label>
        <span>Title</span>
        <input
          required
          maxLength={120}
          value={title}
          onChange={(event) => setTitle(event.currentTarget.value)}
        />
      </label>
      <label>
        <span>Scientific question</span>
        <textarea
          rows={2}
          maxLength={2_000}
          value={question}
          onChange={(event) => setQuestion(event.currentTarget.value)}
        />
      </label>
      <div>
        <button type="submit" disabled={!title.trim()}>
          Save details
        </button>
        <button type="button" className="secondary-button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function RestorationChip({
  status,
}: {
  status: SavedComparisonEntry["effective_restoration_status"];
}) {
  return (
    <span className={`saved-comparison-status-chip ${status}`}>
      {status === "healthy"
        ? "Ready"
        : status === "partially_restorable"
          ? "Adjusted"
          : "Unavailable"}
    </span>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? "unknown"
    : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}

function sortSavedComparisons(entries: SavedComparisonEntry[]): SavedComparisonEntry[] {
  return [...entries].sort(
    (left, right) =>
      new Date(right.record.updated_at).valueOf() - new Date(left.record.updated_at).valueOf(),
  );
}
