import { describe, expect, it } from "vitest";

import {
  axisAlignedPlaneOccludesPoint,
  cameraDistanceLimits,
  scalarPointPixelSize,
  updraftLensPlaneTextureData,
  updraftLensTextureData,
  windArrowLength,
} from "./True3DViewer.utils";
import { updraftLensDiscreteColor } from "./UpdraftLensSlice";

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
    const breakpoints = [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 2.0, 3.0, 5.0];
    const colors = [
      "#4b0082",
      "#0057d9",
      "#00c9d8",
      "#ffffff",
      "#00d63b",
      "#8fe000",
      "#ffe000",
      "#ff9800",
      "#ff3b00",
      "#c40000",
    ];
    const values = [
      [-1.01, -1.0, -0.1, 0],
      [0.1, 1.0, 5.0, null],
    ];
    const textureBytes = Array.from(updraftLensTextureData(values, 4, 2, breakpoints, colors));
    expect(textureBytes).toEqual([
      0x4b, 0x00, 0x82, 255, 0x00, 0x57, 0xd9, 255, 0xff, 0xff, 0xff, 255, 0xff, 0xff, 0xff, 255,
      0x00, 0xd6, 0x3b, 255, 0xff, 0xe0, 0x00, 255, 0xc4, 0x00, 0x00, 255, 0x74, 0x7b, 0x80, 255,
    ]);
    const sliceBytes = values.flatMap((row) =>
      row.flatMap((value) => {
        const color = updraftLensDiscreteColor(value, breakpoints, colors);
        return [
          Number.parseInt(color.slice(1, 3), 16),
          Number.parseInt(color.slice(3, 5), 16),
          Number.parseInt(color.slice(5, 7), 16),
          255,
        ];
      }),
    );
    expect(textureBytes).toEqual(sliceBytes);
  });

  it("burns a stable black cloud boundary into the higher-resolution plane texture", () => {
    const withBoundary = updraftLensPlaneTextureData(
      [[0, 0]],
      2,
      1,
      [-0.1],
      ["#ffffff", "#00d63b"],
      [[true, false]],
      true,
    );
    const withoutBoundary = updraftLensPlaneTextureData(
      [[0, 0]],
      2,
      1,
      [-0.1],
      ["#ffffff", "#00d63b"],
      [[true, false]],
      false,
    );
    const countBlackPixels = (data: Uint8Array) => {
      let count = 0;
      for (let index = 0; index < data.length; index += 4) {
        if (data[index] === 0x0b && data[index + 1] === 0x0c && data[index + 2] === 0x0c) {
          count += 1;
        }
      }
      return count;
    };
    expect(withBoundary.width).toBe(12);
    expect(withBoundary.height).toBe(6);
    expect(countBlackPixels(withBoundary.data)).toBeGreaterThan(0);
    expect(countBlackPixels(withoutBoundary.data)).toBe(0);
  });
});

describe("True3DViewer Lens occlusion", () => {
  const bounds = {
    x: { min: -1, max: 1 },
    y: { min: -1, max: 1 },
    z: { min: -1, max: 1 },
  };

  it("recognizes a point behind the bounded Lens plane", () => {
    expect(
      axisAlignedPlaneOccludesPoint({ x: 0, y: 0, z: 10 }, { x: 0, y: 0, z: -5 }, "z", 0, bounds),
    ).toBe(true);
    expect(
      axisAlignedPlaneOccludesPoint({ x: 0, y: 0, z: 10 }, { x: 4, y: 0, z: -5 }, "z", 0, bounds),
    ).toBe(false);
    expect(
      axisAlignedPlaneOccludesPoint({ x: 0, y: 0, z: 10 }, { x: 0, y: 0, z: 5 }, "z", 0, bounds),
    ).toBe(false);
  });
});
