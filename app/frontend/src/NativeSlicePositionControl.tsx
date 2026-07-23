export type NativeSlicePlane = "horizontal" | "vertical_x" | "vertical_y";

export function NativeSlicePositionControl({
  id,
  ariaLabel,
  plane,
  positionIndex,
  positionCount,
  positionLabel,
  indexLabel,
  onPositionChange,
  onReset,
  resetLabel = "Reset position",
  compact = false,
}: {
  id: string;
  ariaLabel: string;
  plane: NativeSlicePlane;
  positionIndex: number;
  positionCount: number;
  positionLabel: string;
  indexLabel: string;
  onPositionChange: (positionIndex: number) => void;
  onReset?: () => void;
  resetLabel?: string;
  compact?: boolean;
}) {
  const lastPosition = Math.max(0, positionCount - 1);
  const clampedPosition = Math.min(lastPosition, Math.max(0, positionIndex));
  const [previousLabel, nextLabel] =
    plane === "horizontal" ? ["Move down", "Move up"] : ["Move back", "Move forward"];

  function move(offset: number) {
    onPositionChange(Math.min(lastPosition, Math.max(0, clampedPosition + offset)));
  }

  return (
    <>
      <label
        className={`native-slice-position-range${
          compact ? " native-slice-position-range-compact" : ""
        }`}
        htmlFor={id}
      >
        <span className={compact ? "sr-only" : ""}>Position</span>
        <input
          id={id}
          aria-label={ariaLabel}
          type="range"
          min={0}
          max={lastPosition}
          step={1}
          value={clampedPosition}
          disabled={positionCount <= 1}
          onChange={(event) => onPositionChange(Number(event.currentTarget.value))}
        />
        <span className="slice-position-label">
          <span>{positionLabel}</span>
          <small>{indexLabel}</small>
        </span>
      </label>
      <div className="button-row slice-move-buttons">
        <button type="button" disabled={clampedPosition === 0} onClick={() => move(-1)}>
          {previousLabel}
        </button>
        <button type="button" disabled={clampedPosition === lastPosition} onClick={() => move(1)}>
          {nextLabel}
        </button>
        {onReset && (
          <button
            type="button"
            className={compact ? "native-slice-position-reset" : ""}
            aria-label={resetLabel}
            title={resetLabel}
            onClick={onReset}
          >
            {compact ? <span aria-hidden="true">{"\u21ba"}</span> : resetLabel}
          </button>
        )}
      </div>
    </>
  );
}
