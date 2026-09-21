import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

const canvas = document.querySelector("#scene-canvas");
const viewport = document.querySelector("#viewport");
const loadingState = document.querySelector("#loading-state");
const loadingCopy = document.querySelector("#loading-copy");
const timeline = document.querySelector("#timeline");
const playPause = document.querySelector("#play-pause");
const restart = document.querySelector("#restart");
const fitViewButton = document.querySelector("#fit-view");
const speedSelect = document.querySelector("#playback-speed");
const componentList = document.querySelector("#component-list");
const showAll = document.querySelector("#show-all");
const sidePanel = document.querySelector("#side-panel");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.setClearColor(0x1b2529, 1);

const scene = new THREE.Scene();
// Keep geometry colors legible for large CAD assemblies; fitView still uses
// the scene bounds to set the camera and grid scale.
scene.fog = null;

const camera = new THREE.PerspectiveCamera(38, 1, 0.0001, 20);
camera.position.set(0.13, -0.15, 0.11);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;

scene.add(new THREE.HemisphereLight(0xffffff, 0x708088, 2.2));
const keyLight = new THREE.DirectionalLight(0xffffff, 3.2);
keyLight.position.set(0.8, -1.1, 1.4);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xffe4bf, 1.5);
fillLight.position.set(-0.8, 0.4, 0.6);
scene.add(fillLight);

const grid = new THREE.GridHelper(0.4, 24, 0x8b9aa1, 0xbfc9ce);
grid.rotation.x = Math.PI / 2;
grid.material.opacity = 0.28;
grid.material.transparent = true;
scene.add(grid);
scene.add(new THREE.AxesHelper(0.025));

const loader = new STLLoader();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const clock = new THREE.Clock();
const geometryCache = new Map();
const componentObjects = new Map();
const componentRows = new Map();
let workspacePathObject = null;

let manifest;
let currentTime = 0;
let currentCaseIndex = 0;
let playing = false;
let playbackSpeed = 1;
let selectedComponentId = null;

function issueComponentIds() {
  return new Set(
    manifest.issues.flatMap((issue) => issue.object_ids || []).filter((id) =>
      manifest.components.some((component) => component.component_id === id),
    ),
  );
}

function statusLabel(value) {
  return {
    completed: "Completed",
    completed_with_warnings: "Warnings",
    partial: "Partial",
  }[value] || value;
}

function createWorkspacePath() {
  const points = manifest.workspace?.path_m;
  if (!Array.isArray(points) || points.length < 2) return;
  const geometry = new THREE.BufferGeometry().setFromPoints(
    points.map((point) => new THREE.Vector3(point[0], point[1], point[2] || 0)),
  );
  const material = new THREE.LineBasicMaterial({
    color: 0xd35436,
    transparent: true,
    opacity: 0.9,
    depthTest: false,
    depthWrite: false,
  });
  workspacePathObject = manifest.workspace.path_closed
    ? new THREE.LineLoop(geometry, material)
    : new THREE.Line(geometry, material);
  workspacePathObject.name = manifest.workspace.path_label || "Constrained workspace";
  workspacePathObject.renderOrder = 10;
  scene.add(workspacePathObject);
}

function findBracket(times, time) {
  if (times.length < 2 || time <= times[0]) return [0, 0, 0];
  const last = times.length - 1;
  if (time >= times[last]) return [last, last, 0];
  let low = 0;
  let high = last;
  while (high - low > 1) {
    const middle = Math.floor((low + high) / 2);
    if (times[middle] <= time) low = middle;
    else high = middle;
  }
  return [low, high, (time - times[low]) / (times[high] - times[low])];
}

function sampleSeries(series, time, key) {
  if (!series) return null;
  const [left, right, weight] = findBracket(series.times_s, time);
  const values = series[key];
  return THREE.MathUtils.lerp(values[left], values[right], weight);
}

function applyComponentPose(component, time) {
  const object = componentObjects.get(component.component_id);
  if (!object) return;
  const trajectory = component.trajectory;
  if (!trajectory) {
    object.position.fromArray(component.initial_pose.position_m);
    object.quaternion.fromArray(component.initial_pose.orientation_xyzw);
    return;
  }
  const [left, right, weight] = findBracket(trajectory.times_s, time);
  const leftPosition = new THREE.Vector3().fromArray(trajectory.positions_m[left]);
  const rightPosition = new THREE.Vector3().fromArray(trajectory.positions_m[right]);
  object.position.lerpVectors(leftPosition, rightPosition, weight);
  const leftQuaternion = new THREE.Quaternion().fromArray(trajectory.orientations_xyzw[left]);
  const rightQuaternion = new THREE.Quaternion().fromArray(trajectory.orientations_xyzw[right]);
  object.quaternion.slerpQuaternions(leftQuaternion, rightQuaternion, weight).normalize();
}

function updateMetrics() {
  const input = sampleSeries(manifest.metrics.input, currentTime, "velocities");
  const output = sampleSeries(manifest.metrics.output, currentTime, "velocities");
  const inputUnit = manifest.metrics.input_unit || "rad/s";
  const outputUnit = manifest.metrics.output_unit || "rad/s";
  const ratioMode = manifest.metrics.ratio_mode || "input_over_output";
  const ratioUnit = manifest.metrics.ratio_unit || ":1";
  document.querySelector("#input-speed").textContent = input === null ? "--" : `${input.toFixed(3)} ${inputUnit}`;
  document.querySelector("#output-speed").textContent = output === null ? "--" : `${output.toFixed(3)} ${outputUnit}`;
  const ratio = ratioMode === "output_over_input"
    ? (input === null || output === null || Math.abs(input) < 1e-10 ? null : Math.abs(output / input))
    : (input === null || output === null || Math.abs(output) < 1e-10 ? null : Math.abs(input / output));
  document.querySelector("#ratio-value").textContent =
    ratio === null ? "--" : `${ratio.toFixed(3)}${ratioUnit === ":1" ? ":1" : ` ${ratioUnit}`}`;
}

const physicsArrows = new THREE.Group();
scene.add(physicsArrows);
let physicsPanel;
function physicsCaseCount() {
  return manifest?.physics_case_count ?? manifest?.physics?.static_results?.length ?? 0;
}

function updateStaticCase(index) {
  const count = physicsCaseCount();
  if (!count) return;
  currentCaseIndex = Math.max(0, Math.min(count - 1, Math.round(index)));
  const record = manifest.physics.static_results[currentCaseIndex];
  for (const component of manifest.components) {
    const object = componentObjects.get(component.component_id);
    const pose = record.component_poses[component.component_id];
    if (object && pose) {
      object.position.fromArray(pose.position_m);
      object.quaternion.fromArray(pose.orientation_xyzw);
    }
  }
  timeline.value = count > 1 ? String(currentCaseIndex / (count - 1)) : "0";
  document.querySelector("#time-readout").textContent = String(currentCaseIndex + 1);
  document.querySelector("#time-readout").parentElement.lastChild.textContent = " (static case)";
  document.querySelector("#sample-readout").textContent = `Static case ${currentCaseIndex + 1} / ${count}`;
  updatePhysics(currentCaseIndex);
}

function expectedRatioLabel(metrics) {
  const unit = metrics.ratio_unit || ":1";
  return metrics.expected_ratio == null ? "--" : `${metrics.expected_ratio.toFixed(3)}${unit === ":1" ? ":1" : ` ${unit}`}`;
}

function updatePhysics(caseIndex) {
  const cases = manifest.physics?.static_results;
  if (!cases?.length) return;
  const record = cases[Math.max(0, Math.min(cases.length - 1, caseIndex))];
  for (const arrow of [...physicsArrows.children]) {
    physicsArrows.remove(arrow);
    arrow.line?.geometry.dispose(); arrow.cone?.geometry.dispose();
    arrow.line?.material.dispose(); arrow.cone?.material.dispose();
  }
  for (const load of record.load_wrenches || []) {
    const force = new THREE.Vector3(...load.force_n);
    const magnitude = force.length();
    if (magnitude <= 1e-12) continue;
    const arrow = new THREE.ArrowHelper(force.normalize(), new THREE.Vector3(...load.point_m),
      Math.min(0.12, 0.025 + magnitude * 0.0007), load.applied_by === "gravity" ? 0x436fa0 : 0xe55f2b, 0.012, 0.006);
    physicsArrows.add(arrow);
  }
  if (!physicsPanel) {
    physicsPanel = document.createElement("details");
    physicsPanel.style.cssText = "padding:12px;max-height:38vh;overflow:auto;font-size:12px";
    const summary = document.createElement("summary"); summary.textContent = "Static forces, frames and evidence";
    physicsPanel.append(summary); physicsPanel.append(document.createElement("pre"));
    sidePanel.append(physicsPanel);
  }
  physicsPanel.querySelector("pre").textContent = JSON.stringify({
    case: caseIndex + 1, status: record.status, acceptance_passed: manifest.physics.acceptance_passed, checks: manifest.physics.checks, scope: "Discrete static cases; no dynamic trajectory",
    holding: record.generalized_holding, units: record.generalized_units,
    support: record.support_wrench, loads: record.load_wrenches,
    source_sha256: record.evidence?.source_sha256,
  }, null, 2);
}

function updateTime(time) {
  if (physicsCaseCount()) return updateStaticCase(time);
  currentTime = Math.max(manifest.start_time_s, Math.min(manifest.end_time_s, time));
  for (const component of manifest.components) applyComponentPose(component, currentTime);
  const duration = manifest.end_time_s - manifest.start_time_s;
  timeline.value = duration > 0 ? String((currentTime - manifest.start_time_s) / duration) : "0";
  document.querySelector("#time-readout").textContent = currentTime.toFixed(3);
  const frame = Math.min(
    manifest.sample_count,
    Math.max(1, Math.round(Number(timeline.value) * (manifest.sample_count - 1)) + 1),
  );
  document.querySelector("#sample-readout").textContent = manifest.physics ? `Static case ${frame} / ${manifest.sample_count}` : `Frame ${frame} / ${manifest.sample_count}`;
  updateMetrics();
}

function setPlaying(value) {
  playing = physicsCaseCount() ? false : value;
  playPause.innerHTML = playing ? "&#10074;&#10074;" : "&#9654;";
  playPause.title = playing ? "Pause" : "Play";
  playPause.setAttribute("aria-label", playPause.title);
  clock.getDelta();
}

function fitView() {
  const bounds = new THREE.Box3();
  for (const object of componentObjects.values()) {
    if (object.visible) bounds.expandByObject(object);
  }
  if (bounds.isEmpty()) return;
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const span = Math.max(size.x, size.y, size.z, 0.03);
  controls.target.copy(center);
  camera.position.copy(center).add(new THREE.Vector3(span * 1.35, -span * 1.55, span * 1.05));
  camera.near = Math.max(span / 1000, 0.00001);
  camera.far = Math.max(span * 25, 2);
  camera.updateProjectionMatrix();
  // Keep large CAD assemblies readable after fit-to-view.  The original
  // fixed fog range is appropriate for small mechanism examples but washes
  // out metre-scale gantries once the camera is moved farther away.
  if (scene.fog) {
    scene.fog.near = Math.max(span * 1.5, 0.7);
    scene.fog.far = Math.max(span * 6.0, 2.4);
  }
  controls.update();
  grid.position.z = bounds.min.z - span * 0.05;
  grid.scale.setScalar(Math.max(0.2, span / 0.4 * 2.2));
}

function setSelected(componentId) {
  selectedComponentId = componentId;
  for (const [id, object] of componentObjects) {
    const selected = id === componentId;
    object.traverse((child) => {
      if (child.isMesh && child.material && "emissive" in child.material) {
        child.material.emissive.set(selected ? 0x1c6c63 : 0x000000);
        child.material.emissiveIntensity = selected ? 0.5 : 0;
      }
    });
    componentRows.get(id)?.classList.toggle("selected", selected);
  }
  const component = manifest.components.find((item) => item.component_id === componentId);
  const section = document.querySelector("#selection-section");
  section.hidden = !component;
  if (component) {
    document.querySelector("#selection-name").textContent = component.display_name;
    document.querySelector("#selection-id").textContent = component.component_id;
  }
}

function createComponentRow(component, object) {
  const row = document.createElement("label");
  row.className = `component-row${component.asset_url ? "" : " missing"}`;
  row.classList.toggle("issue", issueComponentIds().has(component.component_id));
  row.title = component.asset_url ? component.component_id : `${component.component_id} (mesh unavailable)`;
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = true;
  checkbox.addEventListener("change", () => {
    object.visible = checkbox.checked;
    showAll.checked = [...componentRows.values()].every((item) => item.querySelector("input").checked);
  });
  const swatch = document.createElement("span");
  swatch.className = "component-swatch";
  swatch.style.background = component.color;
  const label = document.createElement("span");
  label.className = "component-label";
  label.textContent = component.display_name;
  row.append(checkbox, swatch, label);
  row.addEventListener("click", (event) => {
    if (event.target !== checkbox) setSelected(component.component_id);
  });
  componentList.append(row);
  componentRows.set(component.component_id, row);
}

async function loadGeometry(url) {
  if (!geometryCache.has(url)) geometryCache.set(url, loader.loadAsync(url));
  return geometryCache.get(url);
}

async function createComponent(component) {
  const group = new THREE.Group();
  group.name = component.component_id;
  group.userData.componentId = component.component_id;
  let mesh;
  if (component.asset_url) {
    const geometry = await loadGeometry(component.asset_url);
    if (!geometry.attributes.normal) geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    mesh = new THREE.Mesh(
      geometry,
      new THREE.MeshBasicMaterial({
        color: component.color,
        transparent: false,
        opacity: 1,
        depthWrite: true,
        side: THREE.DoubleSide,
      }),
    );
    mesh.scale.setScalar(manifest.asset_length_scale_m);
  } else {
    const geometry = new THREE.OctahedronGeometry(0.0025, 0);
    mesh = new THREE.Mesh(
      geometry,
      new THREE.MeshBasicMaterial({ color: 0x8f7a72, wireframe: true, transparent: true, opacity: 0.45 }),
    );
  }
  mesh.userData.componentId = component.component_id;
  group.add(mesh);
  scene.add(group);
  componentObjects.set(component.component_id, group);
  createComponentRow(component, group);
  applyComponentPose(component, currentTime);
}

function populateIssues() {
  if (!manifest.issues.length && !manifest.missing_asset_component_ids.length) return;
  const section = document.querySelector("#issues-section");
  const list = document.querySelector("#issues-list");
  section.hidden = false;
  for (const issue of manifest.issues) {
    const item = document.createElement("div");
    item.className = "issue-item";
    item.textContent = `${issue.code}: ${issue.message}`;
    list.append(item);
  }
  if (manifest.missing_asset_component_ids.length) {
    const item = document.createElement("div");
    item.className = "issue-item";
    item.textContent = `${manifest.missing_asset_component_ids.length} component meshes unavailable`;
    list.append(item);
  }
}

async function initialize() {
  try {
    manifest = await fetch("./viewer.json").then((response) => {
      if (!response.ok) throw new Error(`viewer.json: HTTP ${response.status}`);
      return response.json();
    });
    currentTime = manifest.start_time_s;
    document.title = `${manifest.title} | KinCheck`;
    document.querySelector("#viewer-title").textContent = manifest.title;
    document.querySelector("#viewer-subtitle").textContent = `${manifest.assembly_id} / ${manifest.scenario_id}`;
    const status = document.querySelector("#motion-status");
    status.textContent = statusLabel(manifest.motion_status);
    status.classList.toggle("warning", manifest.motion_status !== "completed");
    document.querySelector("#backend-label").textContent = [manifest.backend.id, manifest.backend.version].filter(Boolean).join(" ");
    document.querySelector("#expected-ratio").textContent =
      expectedRatioLabel(manifest.metrics);
    document.querySelector("#timeline-start").textContent = `${manifest.start_time_s.toFixed(3)} s`;
    document.querySelector("#timeline-end").textContent = `${manifest.end_time_s.toFixed(3)} s`;

    let loaded = 0;
    for (const component of manifest.components) {
      await createComponent(component);
      loaded += 1;
      loadingCopy.textContent = `Loading geometry ${loaded} / ${manifest.components.length}`;
    }
    createWorkspacePath();
    populateIssues();
    if (physicsCaseCount()) {
      playPause.disabled = true; speedSelect.disabled = true;
      document.querySelector("#viewer-subtitle").textContent += " · static cases, no time integration";
      document.querySelector("#timeline-start").textContent = "Case 1";
      document.querySelector("#timeline-end").textContent = `Case ${physicsCaseCount()}`;
    }
    updateTime(physicsCaseCount() ? 0 : manifest.start_time_s);
    fitView();
    loadingState.hidden = true;
  } catch (error) {
    loadingCopy.textContent = `Viewer failed: ${error.message}`;
    console.error(error);
  }
}

playPause.addEventListener("click", () => setPlaying(!playing));
restart.addEventListener("click", () => { setPlaying(false); updateTime(physicsCaseCount() ? 0 : manifest.start_time_s); });
fitViewButton.addEventListener("click", fitView);
speedSelect.addEventListener("change", () => { playbackSpeed = Number(speedSelect.value); });
timeline.addEventListener("input", () => {
  setPlaying(false);
  updateTime(physicsCaseCount()
    ? Number(timeline.value) * (physicsCaseCount() - 1)
    : manifest.start_time_s + Number(timeline.value) * (manifest.end_time_s - manifest.start_time_s));
});
showAll.addEventListener("change", () => {
  for (const [id, row] of componentRows) {
    const checkbox = row.querySelector("input");
    checkbox.checked = showAll.checked;
    componentObjects.get(id).visible = showAll.checked;
  }
});
document.querySelector("#toggle-panel").addEventListener("click", () => sidePanel.classList.toggle("open"));
window.addEventListener("keydown", (event) => {
  if (event.code === "Space" && event.target === document.body) {
    event.preventDefault();
    setPlaying(!playing);
  }
});
canvas.addEventListener("pointerdown", (event) => {
  const bounds = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
  pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects([...componentObjects.values()], true)[0];
  if (hit) setSelected(hit.object.userData.componentId);
});

function resize() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

new ResizeObserver(resize).observe(viewport);

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.1);
  if (playing && manifest) {
    let next = currentTime + delta * playbackSpeed;
    if (next >= manifest.end_time_s) next = manifest.start_time_s;
    updateTime(next);
  }
  controls.update();
  renderer.render(scene, camera);
}

resize();
animate();
initialize();
