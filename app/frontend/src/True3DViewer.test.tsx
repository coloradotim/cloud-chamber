import { describe, expect, it } from "vitest";

import {
  cameraDistanceLimits,
  scalarPointPixelSize,
  updraftLensTextureData,
  windArrowLength,
} from "./True3DViewer.utils";

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

describe("True3DViewer wind arrow scaling", () => {
  it("maps the reference wind to eight percent of horizontal domain width", () => {
    expect(windArrowLength(1, 1, 6.4)).toBeCloseTo(0.512);
    expect(windArrowLength(0.5, 1, 6.4)).toBeCloseTo(0.256);
  });

  it("skips zero and invalid vectors", () => {
    expect(windArrowLength(0, 1, 6.4)).toBe(0);
    expect(windArrowLength(1, 0, 6.4)).toBe(0);
    expect(windArrowLength(Number.NaN, 1, 6.4)).toBe(0);
  });
});

describe("True3DViewer Updraft Lens texture", () => {
  it("uses the exact fixed-scale colors and missing-data color", () => {
    expect(
      Array.from(
        updraftLensTextureData(
          [
            [-1, 0],
            [1, null],
          ],
          2,
          2,
          -1,
          1,
        ),
      ),
    ).toEqual([
      0x21, 0x66, 0xac, 255, 0xf7, 0xf7, 0xf7, 255, 0xb2, 0x18, 0x2b, 255, 0x74, 0x7b, 0x80, 255,
    ]);
  });
});
