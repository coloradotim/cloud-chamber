const DEFAULT_SCALAR_POINT_PIXEL_SIZE = 11;
const MIN_SCALAR_POINT_PIXEL_SIZE = 3;
const MAX_SCALAR_POINT_PIXEL_SIZE = 18;
const DEFAULT_MAX_RANGE = 6.4;

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
