import { describe, expect, it } from "vitest";

import { cameraDistanceLimits, scalarPointPixelSize } from "./True3DViewer.utils";

describe("True3DViewer scalar point sizing", () => {
  it("uses the UI point-size value as a bounded screen-pixel size", () => {
    expect(scalarPointPixelSize(11)).toBe(11);
    expect(scalarPointPixelSize(3)).toBe(3);
    expect(scalarPointPixelSize(18)).toBe(18);
    expect(scalarPointPixelSize(0)).toBe(3);
    expect(scalarPointPixelSize(42)).toBe(18);
    expect(scalarPointPixelSize(Number.NaN)).toBe(11);
  });
});

describe("True3DViewer camera limits", () => {
  it("scales orbit distance for large deep-convection domains", () => {
    expect(cameraDistanceLimits(6.4)).toEqual({ minDistance: 1.5, maxDistance: 40 });
    const largeDomainLimits = cameraDistanceLimits(120);
    expect(largeDomainLimits.minDistance).toBeCloseTo(1.8);
    expect(largeDomainLimits.maxDistance).toBe(360);
  });
});
