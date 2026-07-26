import { describe, expect, it } from "vitest";

import {
  mountainWavesCuratedView,
  mountainWavesInitialView,
  resolveCuratedView,
  supercellsCuratedView,
  tradeCumulusCuratedView,
} from "./exploreCuratedDefaults";

describe("authored Explore defaults", () => {
  it("uses stable product identities and modeled coordinates without backing run IDs", () => {
    const trade = tradeCumulusCuratedView("trade_cumulus_canonical_bomex", "updraft_lens");
    const mountain = mountainWavesCuratedView(
      "mountain_waves_boulder_moist_reference",
      "wave_cloud",
    );
    const supercell = supercellsCuratedView(
      "supercells_quarter_circle_reference",
      "rotating_updraft",
    );

    expect(trade).toMatchObject({
      worldId: "trade_cumulus",
      simulationId: "trade_cumulus_canonical_bomex",
      modeledTimeSeconds: 12_060,
      plane: { orientation: "vertical_x", coordinateKm: 2.366666555404663 },
    });
    expect(mountain).toMatchObject({
      worldId: "mountain_waves",
      simulationId: "mountain_waves_boulder_moist_reference",
      modeledTimeSeconds: 7_200,
      geometry: "expanded",
      viewport: "focus",
    });
    expect(supercell).toMatchObject({
      worldId: "supercells",
      simulationId: "supercells_quarter_circle_reference",
      modeledTimeSeconds: 4_440,
      plane: { orientation: "horizontal", coordinateKm: 3.1666669845581055 },
    });
    expect(JSON.stringify({ trade, mountain, supercell })).not.toMatch(
      /resultId|runId|result_id|run_id/,
    );
  });

  it("keeps distinct authored defaults for every implemented Mountain Waves view", () => {
    expect(mountainWavesInitialView("mountain_waves_dry_ridge")).toBe("wave_structure");
    expect(mountainWavesInitialView("mountain_waves_boulder_moist_reference")).toBe("wave_cloud");
    expect(
      mountainWavesCuratedView(
        "mountain_waves_boulder_moist_reference",
        "field",
        "relative_humidity",
      ),
    ).toMatchObject({
      viewId: "field",
      fieldId: "relative_humidity",
      fixedScaleId: "mountain_waves_relative_humidity_v1",
      overlays: {
        horizontalWind: false,
        cloudPoints: false,
        cloudBoundary: false,
        saturationContour: false,
        potentialTemperatureContours: false,
      },
    });
    expect(
      mountainWavesCuratedView("mountain_waves_boulder_moist_reference", "wave_structure"),
    ).toMatchObject({
      overlays: {
        horizontalWind: true,
        potentialTemperatureContours: true,
      },
    });
    expect(
      mountainWavesCuratedView("mountain_waves_boulder_moist_reference", "wave_cloud"),
    ).toMatchObject({
      overlays: {
        horizontalWind: true,
        cloudPoints: true,
        cloudBoundary: true,
        saturationContour: true,
        potentialTemperatureContours: false,
      },
      cloudOpacity: 0.68,
      cloudPointSizePx: 11,
    });
  });

  it("keeps independent accepted presentations for all three Supercells Lenses", () => {
    const rotating = supercellsCuratedView(
      "supercells_quarter_circle_reference",
      "rotating_updraft",
    );
    const cloud = supercellsCuratedView(
      "supercells_quarter_circle_reference",
      "cloud_precipitation",
    );
    const lowLevel = supercellsCuratedView(
      "supercells_quarter_circle_reference",
      "low_level_interactions",
    );

    expect(rotating).toMatchObject({
      evidenceOrientation: "plan",
      cameraPreset: "look_along_y",
      visibleLayerIds: ["storm_cloud_body", "rising_core", "cyclonic_rotation", "updraft_helicity"],
    });
    expect(cloud).toMatchObject({
      evidenceOrientation: "xz",
      plane: { orientation: "vertical_x", coordinateKm: 0.75 },
      visibleLayerIds: ["hydrometeor_categories"],
      sceneOpacity: 0.9,
      scenePointSize: 0.9,
    });
    expect(lowLevel).toMatchObject({
      evidenceOrientation: "plan",
      cameraPreset: "low_level",
      visibleLayerIds: [
        "low_level_vertical_motion",
        "accumulated_surface_rain",
        "precipitating_condensate",
        "model_relative_wind",
      ],
    });
  });
});

describe("curated-default resolver", () => {
  it("resolves modeled time and a non-default physical plane exactly", () => {
    const definition = supercellsCuratedView(
      "supercells_quarter_circle_reference",
      "cloud_precipitation",
    );
    const result = resolveCuratedView(definition, {
      availableViewIds: ["cloud_precipitation"],
      availableFieldIds: ["total_condensate"],
      availableScaleIds: ["supercell_total_condensate_v2"],
      availableLayerIds: ["hydrometeor_categories"],
      availableOverlayIds: ["vertical_velocity"],
      timesSeconds: [4_320, 4_440, 4_560],
      planeCoordinatesKm: [-0.75, 0, 0.75, 1.5],
      planeNativeIndices: [21, 22, 23, 24],
    });

    expect(result).toMatchObject({
      status: "applied",
      value: {
        timeIndex: 1,
        planePositionIndex: 2,
        planeNativeIndex: 23,
      },
    });
  });

  it("reports a bounded partial resolution when only nearest saved coordinates exist", () => {
    const definition = tradeCumulusCuratedView("trade_cumulus_more_moisture", "updraft_lens");
    const result = resolveCuratedView(definition, {
      availableViewIds: ["updraft_lens"],
      availableFieldIds: ["ql", "w"],
      availableScaleIds: ["trade_cumulus_updraft_velocity_v1"],
      availableOverlayIds: ["cloud_boundary", "horizontal_wind", "vertical_velocity"],
      timesSeconds: [13_800, 14_040],
      planeCoordinatesKm: [1.5, 1.7],
      planeNativeIndices: [70, 73],
    });

    expect(result.status).toBe("partially_incompatible");
    expect(result.value).toMatchObject({ timeIndex: 0, planeNativeIndex: 73 });
    expect(result.incompatibilities).toHaveLength(2);
  });

  it("fails visibly without silently substituting a missing scale or view", () => {
    const definition = mountainWavesCuratedView(
      "mountain_waves_boulder_moist_reference",
      "wave_cloud",
    );
    const result = resolveCuratedView(definition, {
      availableViewIds: ["field"],
      availableFieldIds: ["w", "cloud_liquid", "relative_humidity"],
      availableScaleIds: ["unexpected_dynamic_scale"],
      availableOverlayIds: [
        "horizontal_wind",
        "cloud_points",
        "cloud_boundary",
        "saturation_contour",
      ],
      timesSeconds: [7_200],
    });

    expect(result).toMatchObject({
      status: "technical_fallback",
      value: null,
    });
    expect(result.incompatibilities).toEqual([
      "view wave_cloud is unavailable",
      "scale mountain_waves_vertical_velocity_v1 is unavailable",
    ]);
  });

  it("makes an unauthored Simulation a visible technical fallback", () => {
    const result = resolveCuratedView(null, { timesSeconds: [0, 60] });

    expect(result.status).toBe("technical_fallback");
    expect(result.message).toContain("No authored curated view");
  });

  it("uses technical fallback for coordinates beyond the authored compatibility bounds", () => {
    const definition = tradeCumulusCuratedView("trade_cumulus_more_moisture", "updraft_lens");
    const capabilities = {
      availableViewIds: ["updraft_lens"],
      availableFieldIds: ["ql", "w"],
      availableScaleIds: ["trade_cumulus_updraft_velocity_v1"],
      availableOverlayIds: ["cloud_boundary", "horizontal_wind", "vertical_velocity"],
    };

    const farTime = resolveCuratedView(definition, {
      ...capabilities,
      timesSeconds: [0, 120],
      planeCoordinatesKm: [1.6333333253860474],
    });
    const farPlane = resolveCuratedView(definition, {
      ...capabilities,
      timesSeconds: [13_920],
      planeCoordinatesKm: [-3.2, -3],
    });

    expect(farTime).toMatchObject({ status: "technical_fallback", value: null });
    expect(farTime.message).toContain("time is outside");
    expect(farPlane).toMatchObject({ status: "technical_fallback", value: null });
    expect(farPlane.message).toContain("plane is outside");
  });

  it("fails closed when Trade cloud evidence or required Lens overlays are absent", () => {
    const trade = tradeCumulusCuratedView("trade_cumulus_canonical_bomex", "updraft_lens");
    const missingCloud = resolveCuratedView(trade, {
      availableViewIds: ["updraft_lens"],
      availableFieldIds: ["w"],
      availableScaleIds: ["trade_cumulus_updraft_velocity_v1"],
      availableOverlayIds: ["cloud_boundary", "horizontal_wind", "vertical_velocity"],
      timesSeconds: [12_060],
      planeCoordinatesKm: [2.366666555404663],
    });
    const mountain = mountainWavesCuratedView(
      "mountain_waves_boulder_moist_reference",
      "wave_cloud",
    );
    const missingMountainOverlay = resolveCuratedView(mountain, {
      availableViewIds: ["wave_cloud"],
      availableFieldIds: ["w", "cloud_liquid", "relative_humidity"],
      availableScaleIds: ["mountain_waves_vertical_velocity_v1"],
      availableOverlayIds: ["horizontal_wind", "cloud_points", "cloud_boundary"],
      timesSeconds: [7_200],
    });
    const supercell = supercellsCuratedView(
      "supercells_quarter_circle_reference",
      "low_level_interactions",
    );
    const missingSupercellOverlay = resolveCuratedView(supercell, {
      availableViewIds: ["low_level_interactions"],
      availableFieldIds: ["winterp"],
      availableScaleIds: ["supercell_low_level_vertical_velocity_v1"],
      availableLayerIds: [
        "low_level_vertical_motion",
        "accumulated_surface_rain",
        "precipitating_condensate",
        "model_relative_wind",
      ],
      availableOverlayIds: ["vertical_velocity", "accumulated_surface_rain", "model_relative_wind"],
      timesSeconds: [4_440],
      planeCoordinatesKm: [1.1666667461395264],
    });

    expect(missingCloud.incompatibilities).toContain("field ql is unavailable");
    expect(missingMountainOverlay.incompatibilities).toContain(
      "overlay saturation_contour is unavailable",
    );
    expect(missingSupercellOverlay.incompatibilities).toContain(
      "overlay low_level_precipitating_condensate is unavailable",
    );
  });

  it("authors Trade direct Field around the active supported scene and slice fields", () => {
    const definition = tradeCumulusCuratedView("trade_cumulus_more_moisture", "field", "qv", "th");

    expect(definition).toMatchObject({
      viewId: "field",
      sceneFieldId: "qv",
      sliceFieldId: "th",
      cloudFieldId: null,
      requirements: {
        requiredFieldIds: ["qv", "th"],
      },
    });
  });
});
