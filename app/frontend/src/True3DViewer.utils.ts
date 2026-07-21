import { updraftLensDiscreteColor } from "./UpdraftLensSlice";

const DEFAULT_SCALAR_POINT_PIXEL_SIZE = 11;
const MIN_SCALAR_POINT_PIXEL_SIZE = 3;
const MAX_SCALAR_POINT_PIXEL_SIZE = 18;
const DEFAULT_MAX_RANGE = 6.4;
const UPDRAFT_LENS_TEXTURE_CELL_SCALE = 6;

type Point3 = { x: number; y: number; z: number };
type Axis3 = keyof Point3;

export function scalarPointPixelSize(pointSize: number): number {
  const resolved = Number.isFinite(pointSize) ? pointSize : DEFAULT_SCALAR_POINT_PIXEL_SIZE;
  return Math.min(MAX_SCALAR_POINT_PIXEL_SIZE, Math.max(MIN_SCALAR_POINT_PIXEL_SIZE, resolved));
}

export function cameraDistanceLimits(maxRange: number): {
  minDistance: number;
  maxDistance: number;
} {
  const resolvedMaxRange = Number.isFinite(maxRange) && maxRange > 0 ? maxRange : DEFAULT_MAX_RANGE;
  return {
    minDistance: Math.max(1.5, resolvedMaxRange * 0.015),
    maxDistance: Math.max(40, resolvedMaxRange * 3),
  };
}

export function axisAlignedPlaneOccludesPoint(
  camera: Point3,
  point: Point3,
  planeAxis: Axis3,
  planeCoordinate: number,
  planeBounds: Record<Axis3, { min: number; max: number }>,
): boolean {
  const denominator = point[planeAxis] - camera[planeAxis];
  if (Math.abs(denominator) < Number.EPSILON) return false;
  const amount = (planeCoordinate - camera[planeAxis]) / denominator;
  if (amount <= 0 || amount >= 1) return false;
  const intersection = {
    x: camera.x + (point.x - camera.x) * amount,
    y: camera.y + (point.y - camera.y) * amount,
    z: camera.z + (point.z - camera.z) * amount,
  };
  return (Object.keys(planeBounds) as Axis3[]).every(
    (axis) =>
      intersection[axis] >= planeBounds[axis].min && intersection[axis] <= planeBounds[axis].max,
  );
}

export function windArrowLength(
  magnitudeMps: number,
  referenceMps: number,
  domainWidth: number,
  domainFraction = 0.08,
): number {
  if (
    !Number.isFinite(magnitudeMps) ||
    magnitudeMps <= 0 ||
    !Number.isFinite(referenceMps) ||
    referenceMps <= 0 ||
    !Number.isFinite(domainWidth) ||
    domainWidth <= 0
  ) {
    return 0;
  }
  const fraction = Number.isFinite(domainFraction) && domainFraction > 0 ? domainFraction : 0.08;
  return (magnitudeMps / referenceMps) * domainWidth * fraction;
}

export function updraftLensTextureData(
  values: Array<Array<number | null>>,
  width: number,
  height: number,
  breakpoints: number[],
  colors: string[],
): Uint8Array {
  const resolvedWidth = Math.max(1, Math.trunc(width));
  const resolvedHeight = Math.max(1, Math.trunc(height));
  const data = new Uint8Array(resolvedWidth * resolvedHeight * 4);
  for (let zIndex = 0; zIndex < resolvedHeight; zIndex += 1) {
    for (let xIndex = 0; xIndex < resolvedWidth; xIndex += 1) {
      const offset = (zIndex * resolvedWidth + xIndex) * 4;
      const [red, green, blue] = hexColorChannels(
        updraftLensDiscreteColor(values[zIndex]?.[xIndex] ?? null, breakpoints, colors),
      );
      data[offset] = red;
      data[offset + 1] = green;
      data[offset + 2] = blue;
      data[offset + 3] = 255;
    }
  }
  return data;
}

export function updraftLensPlaneTextureData(
  values: Array<Array<number | null>>,
  width: number,
  height: number,
  breakpoints: number[],
  colors: string[],
  cloudMask: boolean[][],
  showCloudBoundary: boolean,
): { data: Uint8Array; width: number; height: number } {
  const sourceWidth = Math.max(1, Math.trunc(width));
  const sourceHeight = Math.max(1, Math.trunc(height));
  const textureWidth = sourceWidth * UPDRAFT_LENS_TEXTURE_CELL_SCALE;
  const textureHeight = sourceHeight * UPDRAFT_LENS_TEXTURE_CELL_SCALE;
  const data = new Uint8Array(textureWidth * textureHeight * 4);
  const cloudy = (row: number, column: number) => Boolean(cloudMask[row]?.[column]);

  for (let row = 0; row < sourceHeight; row += 1) {
    for (let column = 0; column < sourceWidth; column += 1) {
      const baseColor = hexColorChannels(
        updraftLensDiscreteColor(values[row]?.[column] ?? null, breakpoints, colors),
      );
      for (let cellY = 0; cellY < UPDRAFT_LENS_TEXTURE_CELL_SCALE; cellY += 1) {
        for (let cellX = 0; cellX < UPDRAFT_LENS_TEXTURE_CELL_SCALE; cellX += 1) {
          const boundaryPixel =
            showCloudBoundary &&
            cloudy(row, column) &&
            ((cellX === 0 && !cloudy(row, column - 1)) ||
              (cellX === UPDRAFT_LENS_TEXTURE_CELL_SCALE - 1 && !cloudy(row, column + 1)) ||
              (cellY === 0 && !cloudy(row - 1, column)) ||
              (cellY === UPDRAFT_LENS_TEXTURE_CELL_SCALE - 1 && !cloudy(row + 1, column)));
          const [red, green, blue] = boundaryPixel ? [0x0b, 0x0c, 0x0c] : baseColor;
          const textureX = column * UPDRAFT_LENS_TEXTURE_CELL_SCALE + cellX;
          const textureY = row * UPDRAFT_LENS_TEXTURE_CELL_SCALE + cellY;
          const offset = (textureY * textureWidth + textureX) * 4;
          data[offset] = red;
          data[offset + 1] = green;
          data[offset + 2] = blue;
          data[offset + 3] = 255;
        }
      }
    }
  }
  return { data, width: textureWidth, height: textureHeight };
}

function hexColorChannels(color: string): [number, number, number] {
  const value = Number.parseInt(color.slice(1), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}
