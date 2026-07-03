import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

type CoordinateExtent = { min: number; max: number; units: string | null };

type ProvenancePayload = {
  source_model: string;
  run_id: string;
  result_id?: string;
  scenario_id: string;
  processing_method: string;
  rendering_method: string;
  provenance_label: string;
};

type VisualizableField = {
  raw_field_name: string;
  display_name: string;
  units: string | null;
};

type PointCloudResponse = {
  field: VisualizableField;
  coordinate_units: Record<string, string | null>;
  coordinate_extents: Record<string, CoordinateExtent>;
  points: Array<[number, number, number, number]>;
  stats: {
    source_count: number;
    returned_count: number;
    field_min_value: number | null;
    field_max_value: number | null;
    field_mean_value: number | null;
    field_finite_count: number;
    field_non_finite_count: number;
    min_value: number | null;
    max_value: number | null;
    active_z_min: number | null;
    active_z_max: number | null;
    downsampled: boolean;
    downsample_stride: number;
  };
  provenance: ProvenancePayload;
  caveats: string[];
};

type SliceResponse = {
  field: VisualizableField;
  selection: {
    orientation: "horizontal" | "vertical_x" | "vertical_y";
    selected_dimension: string;
    selected_index: number;
    selected_coordinate_value: number | string | null;
    level_coordinate_value: number | string | null;
    level_units: string | null;
    level_meters: number | null;
  };
};

type SelectedRegionRequest = {
  xIndex?: number;
  yIndex?: number;
  zIndex?: number;
};

type True3DViewerProps = {
  resultName: string;
  pointCloud: PointCloudResponse | null;
  fieldLabel: string;
  valueChannelLabel: string;
  activeSlice: SliceResponse | null;
  activeSliceLabel: string;
  showSlicePlane: boolean;
  selectedRegion: SelectedRegionRequest | null;
  coordinateSizes: { x: number; y: number; z: number };
  selectedTimeLabel: string;
  sceneTimeLabel: string;
  thresholdLabel: string;
  opacity: number;
  pointSize: number;
  status: string;
  provenanceLabel: string;
  noCloudMessage: string;
};

type SceneRefs = {
  scene: THREE.Scene;
  renderer: THREE.WebGLRenderer;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  animationFrame: number;
  resizeObserver: ResizeObserver | null;
};

type SceneBounds = {
  x: CoordinateExtent;
  y: CoordinateExtent;
  z: CoordinateExtent;
  xRange: number;
  yRange: number;
  zRange: number;
  maxRange: number;
};

type CameraPreset = "overview" | "top_down_xy" | "look_along_x" | "look_along_y";

type AxisLabel = {
  axis: "x" | "y" | "z";
  text: string;
  position: THREE.Vector3;
};

const DEFAULT_BOUNDS: SceneBounds = {
  x: { min: -3.2, max: 3.2, units: "km" },
  y: { min: -3.2, max: 3.2, units: "km" },
  z: { min: 0, max: 3, units: "km" },
  xRange: 6.4,
  yRange: 6.4,
  zRange: 3,
  maxRange: 6.4,
};

export function True3DViewer({
  resultName,
  pointCloud,
  fieldLabel,
  valueChannelLabel,
  activeSlice,
  activeSliceLabel,
  showSlicePlane,
  selectedRegion,
  coordinateSizes,
  selectedTimeLabel,
  sceneTimeLabel,
  thresholdLabel,
  opacity,
  pointSize,
  status,
  provenanceLabel,
  noCloudMessage,
}: True3DViewerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const axisLabelLayerRef = useRef<HTMLDivElement | null>(null);
  const refs = useRef<SceneRefs | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [cameraStatus, setCameraStatus] = useState("Camera ready");

  const boundsKey = boundsSignature(pointCloud);
  const bounds = useMemo(() => sceneBoundsFromSignature(boundsKey), [boundsKey]);
  const axisLabels = useMemo(() => axisLabelDefinitions(bounds), [bounds]);
  const selectedPoint = useMemo(
    () => selectedRegionPoint(selectedRegion, coordinateSizes, bounds),
    [bounds, coordinateSizes, selectedRegion],
  );

  const resetCamera = useCallback(() => {
    applyCameraPreset("overview", refs.current, bounds);
    setCameraStatus("Camera reset to shallow-cumulus overview");
  }, [bounds]);

  const setCameraPreset = useCallback((preset: CameraPreset) => {
    applyCameraPreset(preset, refs.current, bounds);
    setCameraStatus(cameraPresetStatus(preset));
  }, [bounds]);

  const zoomCamera = useCallback((direction: "in" | "out") => {
    setCameraStatus(direction === "in" ? "Camera zoomed in" : "Camera zoomed out");
    const current = refs.current;
    if (!current) return;
    const scale = direction === "in" ? 0.82 : 1.18;
    current.camera.position.multiplyScalar(scale);
    current.controls.update();
  }, []);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;
    if (shouldSkipWebGLInitialization()) {
      setRenderError("WebGL renderer unavailable in this test browser.");
      return undefined;
    }

    let mounted = true;
    try {
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xeaf5f9);
      const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1000);
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.domElement.className = "true3d-canvas";
      mount.appendChild(renderer.domElement);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.screenSpacePanning = true;
      controls.minDistance = 1.5;
      controls.maxDistance = 40;
      controls.mouseButtons = {
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN,
      };
      applyCameraPreset("overview", { camera, controls }, bounds);

      const resize = () => {
        if (!mounted) return;
        const width = Math.max(1, mount.clientWidth);
        const height = Math.max(1, mount.clientHeight);
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      };
      resize();

      const resizeObserver =
        typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
      resizeObserver?.observe(mount);
      window.addEventListener("resize", resize);

      const animate = () => {
        controls.update();
        renderer.render(scene, camera);
        positionAxisLabels(axisLabelLayerRef.current, renderer.domElement, camera, axisLabels);
        const current = refs.current;
        if (current) current.animationFrame = window.requestAnimationFrame(animate);
      };

      refs.current = {
        scene,
        renderer,
        camera,
        controls,
        animationFrame: window.requestAnimationFrame(animate),
        resizeObserver,
      };
      setRenderError(null);

      return () => {
        mounted = false;
        window.removeEventListener("resize", resize);
        const current = refs.current;
        refs.current = null;
        if (!current) return;
        window.cancelAnimationFrame(current.animationFrame);
        current.resizeObserver?.disconnect();
        current.controls.dispose();
        disposeScene(current.scene);
        current.renderer.dispose();
        current.renderer.domElement.remove();
      };
    } catch (error) {
      setRenderError(
        error instanceof Error ? error.message : "Unable to initialize the Three.js renderer.",
      );
      return undefined;
    }
  }, [axisLabels, bounds]);

  useEffect(() => {
    const current = refs.current;
    if (!current) return;
    rebuildScene(current.scene, {
      bounds,
      pointCloud,
      activeSlice,
      activeSliceLabel,
      showSlicePlane,
      selectedPoint,
      opacity,
      pointSize,
    });
  }, [
    activeSlice,
    activeSliceLabel,
    bounds,
    opacity,
    pointCloud,
    pointSize,
    selectedPoint,
    showSlicePlane,
  ]);

  return (
    <section className="true3d-viewer" aria-label="True 3-D scalar field viewer">
      <div className="true3d-scene-header">
        <div>
          <p className="eyebrow">True 3-D scene</p>
          <h3>{resultName}</h3>
        </div>
        <p className="state-chip">{status}</p>
      </div>

      <div className="true3d-scene-frame">
        <div
          ref={mountRef}
          className="true3d-canvas-mount"
          role="img"
          aria-label="Interactive Three.js scene showing a CM1 scalar field, domain bounds, slice plane, and selected point"
        />
        <div className="true3d-scene-label true3d-scene-label-context">
          <strong>{fieldLabel}</strong>
          <span>{sceneTimeLabel || selectedTimeLabel}</span>
          <span>Threshold {thresholdLabel}</span>
        </div>
        {pointCloud && (
          <div className="true3d-field-legend" aria-label="3-D field color legend">
            <span>{pointCloud.field.display_name}</span>
            <div className="true3d-field-legend-row">
              <small>{fieldLegendMinimum(pointCloud)}</small>
              <span
                className={`true3d-field-ramp true3d-field-ramp-${scalarRampKey(
                  pointCloud.field.raw_field_name,
                )}`}
              />
              <small>{fieldLegendMaximum(pointCloud)}</small>
            </div>
          </div>
        )}
        <div
          ref={axisLabelLayerRef}
          className="true3d-axis-label-layer"
          aria-label="3-D axis tick labels"
        >
          {axisLabels.map((label, index) => (
            <span
              key={`${label.axis}-${label.text}-${index}`}
              className={`true3d-axis-label true3d-axis-label-${label.axis}`}
              data-axis-label-index={index}
            >
              {label.text}
            </span>
          ))}
        </div>
        {showSlicePlane && activeSlice && (
          <p className="true3d-slice-label">Slice plane: {activeSliceLabel}</p>
        )}
        {selectedPoint && (
          <p className="true3d-selected-point-label">
            Selected point: x {formatCoordinate(selectedPoint.x, bounds.x.units)}, y{" "}
            {formatCoordinate(selectedPoint.y, bounds.y.units)}, z{" "}
            {formatCoordinate(selectedPoint.z, bounds.z.units)}
          </p>
        )}
        {renderError && (
          <p className="true3d-render-error" role="status">
            Three.js renderer unavailable: {renderError}
          </p>
        )}
        {(!pointCloud || pointCloud.points.length === 0) && (
          <div className="true3d-empty-state">
            <p className="eyebrow">3-D scalar layer</p>
            <h4>{noCloudMessage}</h4>
            <p>The domain and slice plane remain visible so the result does not look broken.</p>
          </div>
        )}
      </div>

      <div className="true3d-controls" aria-label="3-D camera controls">
        <div className="true3d-control-section">
          <span>Camera</span>
          <div className="true3d-preset-buttons" aria-label="3-D camera presets">
            <button type="button" onClick={() => setCameraPreset("overview")}>
              Overview
            </button>
            <button type="button" onClick={() => setCameraPreset("top_down_xy")}>
              Top-down x-y
            </button>
            <button type="button" onClick={() => setCameraPreset("look_along_x")}>
              Look along x
            </button>
            <button type="button" onClick={() => setCameraPreset("look_along_y")}>
              Look along y
            </button>
          </div>
        </div>
        <div className="true3d-control-section">
          <span>View</span>
          <div className="true3d-preset-buttons" aria-label="3-D view actions">
            <button type="button" onClick={() => zoomCamera("in")}>
              Zoom in
            </button>
            <button type="button" onClick={() => zoomCamera("out")}>
              Zoom out
            </button>
            <button type="button" onClick={resetCamera}>
              Reset camera
            </button>
          </div>
        </div>
        <p>{cameraStatus}. Drag to orbit, right-drag to pan, scroll to zoom.</p>
      </div>
      <p className="true3d-provenance" aria-label="3-D provenance labels">
        {valueChannelLabel} CM1-derived visualization-ready scalar points and native-grid slice
        plane; rendered with direct Three.js. {provenanceLabel}
      </p>
    </section>
  );
}

function shouldSkipWebGLInitialization(): boolean {
  return typeof navigator !== "undefined" && navigator.userAgent.toLowerCase().includes("jsdom");
}

function rebuildScene(
  scene: THREE.Scene,
  {
    bounds,
    pointCloud,
    activeSlice,
    activeSliceLabel,
    showSlicePlane,
    selectedPoint,
    opacity,
    pointSize,
  }: {
    bounds: SceneBounds;
    pointCloud: PointCloudResponse | null;
    activeSlice: SliceResponse | null;
    activeSliceLabel: string;
    showSlicePlane: boolean;
    selectedPoint: { x: number; y: number; z: number } | null;
    opacity: number;
    pointSize: number;
  },
) {
  disposeScene(scene);
  scene.add(new THREE.AmbientLight(0xffffff, 0.78));
  const key = new THREE.DirectionalLight(0xffffff, 1.2);
  key.position.set(bounds.xRange * 0.6, bounds.zRange, bounds.yRange * 0.8);
  scene.add(key);

  scene.add(domainFloorGrid(bounds));
  scene.add(domainBox(bounds));
  scene.add(axisLines(bounds));
  scene.add(axisTickMarks(bounds));

  if (pointCloud?.points.length) {
    scene.add(cloudPointLayer(pointCloud, bounds, opacity, pointSize));
  }

  if (showSlicePlane && activeSlice) {
    scene.add(slicePlane(activeSlice, activeSliceLabel, bounds));
  }

  if (selectedPoint) {
    scene.add(selectedPointMarker(selectedPoint, bounds));
  }
}

function boundsSignature(pointCloud: PointCloudResponse | null): string {
  const extents = pointCloud?.coordinate_extents;
  const x = extents?.xh ?? extents?.x ?? DEFAULT_BOUNDS.x;
  const y = extents?.yh ?? extents?.y ?? DEFAULT_BOUNDS.y;
  const z = extents?.zh ?? extents?.z ?? DEFAULT_BOUNDS.z;
  return [
    x.min,
    x.max,
    x.units ?? "",
    y.min,
    y.max,
    y.units ?? "",
    z.min,
    z.max,
    z.units ?? "",
  ].join("|");
}

function sceneBoundsFromSignature(signature: string): SceneBounds {
  const [xMin, xMax, xUnits, yMin, yMax, yUnits, zMin, zMax, zUnits] = signature.split("|");
  const x = { min: Number(xMin), max: Number(xMax), units: xUnits || null };
  const y = { min: Number(yMin), max: Number(yMax), units: yUnits || null };
  const z = { min: Number(zMin), max: Number(zMax), units: zUnits || null };
  const xRange = range(x);
  const yRange = range(y);
  const zRange = range(z);
  return { x, y, z, xRange, yRange, zRange, maxRange: Math.max(xRange, yRange, zRange) };
}

function domainBox(bounds: SceneBounds): THREE.Object3D {
  const geometry = new THREE.BoxGeometry(bounds.xRange, bounds.zRange, bounds.yRange);
  const edges = new THREE.EdgesGeometry(geometry);
  const material = new THREE.LineBasicMaterial({ color: 0x3f6f85, transparent: true, opacity: 0.75 });
  return new THREE.LineSegments(edges, material);
}

function domainFloorGrid(bounds: SceneBounds): THREE.Group {
  const group = new THREE.Group();
  const floor = -bounds.zRange / 2;
  const xMin = -bounds.xRange / 2;
  const xMax = bounds.xRange / 2;
  const yMin = -bounds.yRange / 2;
  const yMax = bounds.yRange / 2;
  const minorMaterial = new THREE.LineBasicMaterial({
    color: 0x82aabf,
    transparent: true,
    opacity: 0.34,
  });
  const majorMaterial = new THREE.LineBasicMaterial({
    color: 0x6b9ab2,
    transparent: true,
    opacity: 0.6,
  });
  const zeroMaterial = new THREE.LineBasicMaterial({
    color: 0x426f86,
    transparent: true,
    opacity: 0.82,
  });

  for (const value of gridTickValues(bounds.x, 0.5)) {
    const x = centeredCoordinate(value, bounds.x);
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, floor, yMin),
      new THREE.Vector3(x, floor, yMax),
    ]);
    group.add(new THREE.Line(geometry, gridLineMaterial(value, minorMaterial, majorMaterial, zeroMaterial)));
  }

  for (const value of gridTickValues(bounds.y, 0.5)) {
    const y = centeredCoordinate(value, bounds.y);
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(xMin, floor, y),
      new THREE.Vector3(xMax, floor, y),
    ]);
    group.add(new THREE.Line(geometry, gridLineMaterial(value, minorMaterial, majorMaterial, zeroMaterial)));
  }

  return group;
}

function axisLines(bounds: SceneBounds): THREE.Group {
  const group = new THREE.Group();
  const origin = new THREE.Vector3(-bounds.xRange / 2, -bounds.zRange / 2, -bounds.yRange / 2);
  const xEnd = new THREE.Vector3(bounds.xRange / 2, -bounds.zRange / 2, -bounds.yRange / 2);
  const yEnd = new THREE.Vector3(-bounds.xRange / 2, -bounds.zRange / 2, bounds.yRange / 2);
  const zEnd = new THREE.Vector3(-bounds.xRange / 2, bounds.zRange / 2, -bounds.yRange / 2);
  group.add(axisLine(origin, xEnd, 0x2f7fb5));
  group.add(axisLine(origin, yEnd, 0x4f8f7a));
  group.add(axisLine(origin, zEnd, 0xa76f24));
  return group;
}

function axisLine(start: THREE.Vector3, end: THREE.Vector3, color: number): THREE.Line {
  const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
  const material = new THREE.LineBasicMaterial({ color, linewidth: 2 });
  return new THREE.Line(geometry, material);
}

function axisTickMarks(bounds: SceneBounds): THREE.Group {
  const group = new THREE.Group();
  const tickLength = Math.max(0.08, bounds.maxRange * 0.018);
  const floor = -bounds.zRange / 2;
  const xMin = -bounds.xRange / 2;
  const yMin = -bounds.yRange / 2;

  for (const value of majorTickValues(bounds.x)) {
    const x = centeredCoordinate(value, bounds.x);
    group.add(axisLine(new THREE.Vector3(x, floor, yMin), new THREE.Vector3(x, floor, yMin - tickLength), 0x2f7fb5));
  }
  for (const value of majorTickValues(bounds.y)) {
    const y = centeredCoordinate(value, bounds.y);
    group.add(axisLine(new THREE.Vector3(xMin, floor, y), new THREE.Vector3(xMin - tickLength, floor, y), 0x4f8f7a));
  }
  for (const value of majorTickValues(bounds.z)) {
    const z = centeredCoordinate(value, bounds.z);
    group.add(axisLine(new THREE.Vector3(xMin, z, yMin), new THREE.Vector3(xMin - tickLength, z, yMin), 0xa76f24));
  }
  return group;
}

function axisLabelDefinitions(bounds: SceneBounds): AxisLabel[] {
  const labelOffset = Math.max(0.18, bounds.maxRange * 0.035);
  const floor = -bounds.zRange / 2;
  const xMin = -bounds.xRange / 2;
  const yMin = -bounds.yRange / 2;
  const labels: AxisLabel[] = [];

  for (const value of labeledTickValues(bounds.x)) {
    labels.push({
      axis: "x",
      text: `x ${formatSignedCoordinate(value, bounds.x.units)}`,
      position: new THREE.Vector3(centeredCoordinate(value, bounds.x), floor, yMin - labelOffset),
    });
  }
  for (const value of labeledTickValues(bounds.y)) {
    labels.push({
      axis: "y",
      text: `y ${formatSignedCoordinate(value, bounds.y.units)}`,
      position: new THREE.Vector3(xMin - labelOffset, floor, centeredCoordinate(value, bounds.y)),
    });
  }
  for (const value of majorTickValues(bounds.z)) {
    labels.push({
      axis: "z",
      text: `z ${formatSignedCoordinate(value, bounds.z.units)}`,
      position: new THREE.Vector3(xMin - labelOffset, centeredCoordinate(value, bounds.z), yMin),
    });
  }
  return labels;
}

function positionAxisLabels(
  layer: HTMLDivElement | null,
  canvas: HTMLCanvasElement,
  camera: THREE.Camera,
  labels: AxisLabel[],
) {
  if (!layer) return;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const cameraDirection = new THREE.Vector3();
  camera.getWorldDirection(cameraDirection);

  labels.forEach((label, index) => {
    const element = layer.querySelector<HTMLElement>(`[data-axis-label-index="${index}"]`);
    if (!element) return;
    const projected = label.position.clone().project(camera);
    const cameraToLabel = label.position.clone().sub(camera.position);
    const inFrontOfCamera = cameraToLabel.dot(cameraDirection) > 0;
    const x = (projected.x * 0.5 + 0.5) * width;
    const y = (-projected.y * 0.5 + 0.5) * height;
    const visible =
      inFrontOfCamera &&
      projected.z >= -1 &&
      projected.z <= 1 &&
      x >= -24 &&
      x <= width + 24 &&
      y >= -24 &&
      y <= height + 24;
    element.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
    element.style.opacity = visible ? "1" : "0";
  });
}

function cloudPointLayer(
  pointCloud: PointCloudResponse,
  bounds: SceneBounds,
  opacity: number,
  pointSize: number,
): THREE.Points {
  const positions = new Float32Array(pointCloud.points.length * 3);
  const colors = new Float32Array(pointCloud.points.length * 3);
  const min = pointCloud.stats.min_value ?? 0;
  const max = pointCloud.stats.max_value ?? min + 1;
  pointCloud.points.forEach((point, index) => {
    const mapped = mapCoordinate(point[0], point[1], point[2], bounds);
    positions[index * 3] = mapped.x;
    positions[index * 3 + 1] = mapped.y;
    positions[index * 3 + 2] = mapped.z;
    const intensity = normalize(point[3], min, max);
    const color = scalarPointColor(pointCloud.field.raw_field_name, intensity, point[3]);
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: Math.max(0.035, pointSize * 0.008),
    vertexColors: true,
    transparent: true,
    opacity,
    depthWrite: false,
    sizeAttenuation: true,
  });
  return new THREE.Points(geometry, material);
}

function scalarPointColor(
  fieldName: string,
  intensity: number,
  value: number,
): { r: number; g: number; b: number } {
  if (fieldName === "rain") {
    return {
      r: 0.18 + intensity * 0.2,
      g: 0.45 + intensity * 0.28,
      b: 0.74 + intensity * 0.18,
    };
  }
  if (fieldName === "qr") {
    return {
      r: 0.28 + intensity * 0.38,
      g: 0.44 + intensity * 0.32,
      b: 0.86 + intensity * 0.1,
    };
  }
  if (fieldName === "qv") {
    return {
      r: 0.24 + intensity * 0.22,
      g: 0.58 + intensity * 0.34,
      b: 0.76 + intensity * 0.1,
    };
  }
  if (fieldName === "dbz") {
    return radarReflectivityColor(value);
  }
  return {
    r: 0.24 + intensity * 0.55,
    g: 0.66 + intensity * 0.3,
    b: 0.78 + intensity * 0.18,
  };
}

function radarReflectivityColor(dbz: number): { r: number; g: number; b: number } {
  const stops = [
    { value: 0, color: { r: 0.15, g: 0.38, b: 0.78 } },
    { value: 10, color: { r: 0.18, g: 0.72, b: 0.82 } },
    { value: 20, color: { r: 0.22, g: 0.66, b: 0.26 } },
    { value: 30, color: { r: 0.96, g: 0.86, b: 0.2 } },
    { value: 40, color: { r: 0.93, g: 0.36, b: 0.12 } },
    { value: 50, color: { r: 0.76, g: 0.1, b: 0.12 } },
    { value: 60, color: { r: 0.66, g: 0.18, b: 0.74 } },
  ];
  if (!Number.isFinite(dbz)) return stops[0].color;
  if (dbz <= stops[0].value) return stops[0].color;
  for (let index = 1; index < stops.length; index += 1) {
    const lower = stops[index - 1];
    const upper = stops[index];
    if (dbz <= upper.value) {
      const amount = (dbz - lower.value) / (upper.value - lower.value);
      return {
        r: lower.color.r + (upper.color.r - lower.color.r) * amount,
        g: lower.color.g + (upper.color.g - lower.color.g) * amount,
        b: lower.color.b + (upper.color.b - lower.color.b) * amount,
      };
    }
  }
  return stops[stops.length - 1].color;
}

function scalarRampKey(fieldName: string): string {
  if (fieldName === "qr" || fieldName === "rain") return "rain";
  if (fieldName === "qv") return "qv";
  if (fieldName === "dbz") return "dbz";
  return "qc";
}

function fieldLegendMinimum(pointCloud: PointCloudResponse): string {
  if (pointCloud.field.raw_field_name === "dbz") return "0 dBZ";
  return formatValue(pointCloud.stats.min_value, pointCloud.field.units);
}

function fieldLegendMaximum(pointCloud: PointCloudResponse): string {
  if (pointCloud.field.raw_field_name === "dbz") return "60+ dBZ";
  return formatValue(pointCloud.stats.max_value, pointCloud.field.units);
}

function slicePlane(slice: SliceResponse, label: string, bounds: SceneBounds): THREE.Group {
  const group = new THREE.Group();
  let mesh: THREE.Mesh;
  if (slice.selection.orientation === "horizontal") {
    mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(bounds.xRange, bounds.yRange),
      slicePlaneMaterial(),
    );
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = centeredCoordinate(sliceCoordinate(slice), bounds.z);
  } else if (slice.selection.orientation === "vertical_x") {
    mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(bounds.xRange, bounds.zRange),
      slicePlaneMaterial(),
    );
    mesh.position.z = centeredCoordinate(sliceCoordinate(slice), bounds.y);
  } else {
    mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(bounds.yRange, bounds.zRange),
      slicePlaneMaterial(),
    );
    mesh.rotation.y = Math.PI / 2;
    mesh.position.x = centeredCoordinate(sliceCoordinate(slice), bounds.x);
  }
  mesh.name = `Slice plane: ${label}`;
  group.add(mesh);
  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(mesh.geometry),
    new THREE.LineBasicMaterial({ color: 0xb7791f, transparent: true, opacity: 0.9 }),
  );
  edges.position.copy(mesh.position);
  edges.rotation.copy(mesh.rotation);
  group.add(edges);
  return group;
}

function slicePlaneMaterial(): THREE.MeshBasicMaterial {
  return new THREE.MeshBasicMaterial({
    color: 0xf2b75c,
    transparent: true,
    opacity: 0.24,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
}

function selectedPointMarker(
  selectedPoint: { x: number; y: number; z: number },
  bounds: SceneBounds,
): THREE.Group {
  const group = new THREE.Group();
  const mapped = mapCoordinate(selectedPoint.x, selectedPoint.y, selectedPoint.z, bounds);
  const radius = Math.max(0.045, bounds.maxRange * 0.016);
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 18, 18),
    new THREE.MeshBasicMaterial({ color: 0xd97706 }),
  );
  sphere.position.set(mapped.x, mapped.y, mapped.z);
  group.add(sphere);
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(radius * 1.5, radius * 2.2, 32),
    new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0.72,
      side: THREE.DoubleSide,
    }),
  );
  ring.position.copy(sphere.position);
  ring.rotation.x = Math.PI / 2;
  group.add(ring);
  return group;
}

function applyCameraPreset(
  preset: CameraPreset,
  refs: Pick<SceneRefs, "camera" | "controls"> | null,
  bounds: SceneBounds,
) {
  if (!refs) return;
  const distance = Math.max(bounds.xRange, bounds.yRange, bounds.zRange) * 1.65;
  if (preset === "top_down_xy") {
    refs.camera.position.set(0, distance, 0.001);
    refs.camera.up.set(0, 0, -1);
  } else if (preset === "look_along_x") {
    refs.camera.position.set(distance, bounds.zRange * 0.22, 0);
    refs.camera.up.set(0, 1, 0);
  } else if (preset === "look_along_y") {
    refs.camera.position.set(0, bounds.zRange * 0.22, distance);
    refs.camera.up.set(0, 1, 0);
  } else {
    refs.camera.position.set(bounds.xRange * 0.85, bounds.zRange * 0.8, bounds.yRange * 1.18);
    refs.camera.up.set(0, 1, 0);
  }
  refs.controls.target.set(0, 0, 0);
  refs.controls.update();
}

function cameraPresetStatus(preset: CameraPreset): string {
  const labels: Record<CameraPreset, string> = {
    overview: "Camera set to shallow-cumulus overview",
    top_down_xy: "Camera set to top-down x-y view",
    look_along_x: "Camera looking along the x axis",
    look_along_y: "Camera looking along the y axis",
  };
  return labels[preset];
}

function disposeScene(scene: THREE.Scene) {
  while (scene.children.length > 0) {
    const child = scene.children.pop();
    if (child) disposeObject(child);
  }
}

function disposeObject(object: THREE.Object3D) {
  object.traverse((child) => {
    const maybeMesh = child as THREE.Mesh | THREE.Points | THREE.LineSegments;
    const geometry = maybeMesh.geometry as THREE.BufferGeometry | undefined;
    geometry?.dispose();
    const material = maybeMesh.material as THREE.Material | THREE.Material[] | undefined;
    if (Array.isArray(material)) {
      material.forEach((entry) => entry.dispose());
    } else {
      const mapped = material as (THREE.Material & { map?: THREE.Texture }) | undefined;
      mapped?.map?.dispose();
      material?.dispose();
    }
  });
}

function selectedRegionPoint(
  selectedRegion: SelectedRegionRequest | null,
  sizes: { x: number; y: number; z: number },
  bounds: SceneBounds,
): { x: number; y: number; z: number } | null {
  if (
    selectedRegion?.xIndex === undefined ||
    selectedRegion.yIndex === undefined ||
    selectedRegion.zIndex === undefined
  ) {
    return null;
  }
  return {
    x: coordinateFromIndex(selectedRegion.xIndex, sizes.x, bounds.x),
    y: coordinateFromIndex(selectedRegion.yIndex, sizes.y, bounds.y),
    z: coordinateFromIndex(selectedRegion.zIndex, sizes.z, bounds.z),
  };
}

function coordinateFromIndex(index: number, size: number, extent: CoordinateExtent): number {
  if (!Number.isFinite(index) || size <= 0) return (extent.min + extent.max) / 2;
  return extent.min + ((index + 0.5) / size) * range(extent);
}

function mapCoordinate(
  x: number,
  y: number,
  z: number,
  bounds: SceneBounds,
): { x: number; y: number; z: number } {
  return {
    x: centeredCoordinate(x, bounds.x),
    y: centeredCoordinate(z, bounds.z),
    z: centeredCoordinate(y, bounds.y),
  };
}

function centeredCoordinate(value: number, extent: CoordinateExtent): number {
  const midpoint = (extent.min + extent.max) / 2;
  return Number.isFinite(value) ? value - midpoint : 0;
}

function sliceCoordinate(slice: SliceResponse): number {
  const coordinate = slice.selection.selected_coordinate_value ?? slice.selection.level_coordinate_value;
  const numeric = typeof coordinate === "number" ? coordinate : Number(coordinate);
  return Number.isFinite(numeric) ? numeric : 0;
}

function range(extent: CoordinateExtent): number {
  const value = extent.max - extent.min;
  return Number.isFinite(value) && value > 0 ? value : 1;
}

function majorTickValues(extent: CoordinateExtent): number[] {
  const min = Math.ceil(extent.min);
  const max = Math.floor(extent.max);
  const values: number[] = [];
  for (let value = min; value <= max; value += 1) {
    values.push(Object.is(value, -0) ? 0 : value);
  }
  if (values.length > 0) return values;
  return [extent.min, extent.max];
}

function gridTickValues(extent: CoordinateExtent, spacing: number): number[] {
  const first = Math.ceil(extent.min / spacing) * spacing;
  const values: number[] = [];
  for (let value = first; value <= extent.max + spacing * 0.001; value += spacing) {
    values.push(roundTick(Object.is(value, -0) ? 0 : value));
  }
  return values;
}

function gridLineMaterial(
  value: number,
  minorMaterial: THREE.LineBasicMaterial,
  majorMaterial: THREE.LineBasicMaterial,
  zeroMaterial: THREE.LineBasicMaterial,
): THREE.LineBasicMaterial {
  if (Math.abs(value) < 0.0001) return zeroMaterial;
  return Math.abs(value - Math.round(value)) < 0.0001 ? majorMaterial : minorMaterial;
}

function roundTick(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function labeledTickValues(extent: CoordinateExtent): number[] {
  const ticks = majorTickValues(extent);
  return ticks.filter((value) => value === 0 || Math.abs(value) === Math.max(...ticks.map(Math.abs)));
}

function normalize(value: number, min: number, max: number): number {
  if (!Number.isFinite(value) || max <= min) return 0.5;
  return Math.min(Math.max((value - min) / (max - min), 0), 1);
}

function formatCoordinate(value: number, units: string | null): string {
  return `${formatCompactNumber(value)}${units ? ` ${units}` : ""}`;
}

function formatValue(value: number | null, units: string | null): string {
  if (value === null) return "Unavailable";
  if (Math.abs(value) > 0 && Math.abs(value) < 0.001) {
    return `${value.toExponential(3)}${units ? ` ${units}` : ""}`;
  }
  return `${formatCompactNumber(value)}${units ? ` ${units}` : ""}`;
}

function formatSignedCoordinate(value: number, units: string | null): string {
  const rounded = formatCompactNumber(value);
  const signed = value > 0 ? `+${rounded}` : rounded;
  return `${signed}${units ? ` ${units}` : ""}`;
}

function formatCompactNumber(value: number): string {
  const rounded = Math.abs(value) >= 10 ? value.toFixed(1) : value.toFixed(2);
  return rounded.replace(/\.?0+$/, "");
}
