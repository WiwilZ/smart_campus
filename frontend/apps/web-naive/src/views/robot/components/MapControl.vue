<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { NButton, NCard, NCheckbox, NInput, NTag } from 'naive-ui';
import { message } from '#/adapter/naive';
import {
  getRobotNavigationMap,
  type RobotNavigationRect,
} from '#/api/robot-navigation';

interface Point {
  x: number;
  y: number;
}

interface Pose extends Point {
  yaw: number;
}

const props = defineProps<{
  robot: string;
}>();

const mapContainer = ref<HTMLDivElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const worldSize = ref(100);
const obstacles = ref<RobotNavigationRect[]>([]);
const costmapZones = ref<RobotNavigationRect[]>([]);
const mapLoading = ref(false);
const mapLoaded = ref(false);

const robotPose = ref<Pose>({ x: 22, y: 24, yaw: 0 });
const goalPose = ref<Pose | null>(null);
const initialPoseMode = ref(false);
const navStatus = ref<'idle' | 'navigating' | 'arrived'>('idle');
const followRobot = ref(true);

const showMap = ref(true);
const showCostmap = ref(true);
const showScan = ref(true);
const showGlobalPath = ref(true);
const showLocalPath = ref(true);
const showTrail = ref(true);

const inputX = ref('22');
const inputY = ref('24');

const globalPath = ref<Point[]>([]);
const localPath = ref<Point[]>([]);
const trail = ref<Point[]>([{ x: 22, y: 24 }]);
const scanPoints = ref<Point[]>([]);

const zoom = ref(6.2);
const viewCenter = ref<Point>({ x: 50, y: 50 });
const canvasWidth = ref(0);
const canvasHeight = ref(0);

const dragState = {
  active: false,
  moved: false,
  startClientX: 0,
  startClientY: 0,
  startCenterX: 0,
  startCenterY: 0,
};

let resizeObserver: ResizeObserver | null = null;
let frameHandle = 0;
let previousTimestamp = 0;

const statusLabel = computed(() => {
  if (initialPoseMode.value) {
    return '设置初始位姿';
  }
  return {
    arrived: '已到达',
    idle: '待命',
    navigating: '导航中',
  }[navStatus.value];
});

const statusType = computed<'warning' | 'success' | 'default' | 'info'>(() => {
  if (initialPoseMode.value) {
    return 'warning';
  }
  if (navStatus.value === 'arrived') {
    return 'success';
  }
  if (navStatus.value === 'navigating') {
    return 'info';
  }
  return 'default';
});

const sceneSummary = computed(() => {
  if (goalPose.value) {
    return `目标点 [${goalPose.value.x.toFixed(1)}, ${goalPose.value.y.toFixed(1)}]`;
  }
  if (initialPoseMode.value) {
    return '点击地图设置初始位姿';
  }
  return '点击地图设置导航目标';
});

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

async function loadMap(robotName: string) {
  mapLoading.value = true;
  try {
    const data = await getRobotNavigationMap(robotName);
    worldSize.value = data.worldSize;
    obstacles.value = data.obstacles;
    costmapZones.value = data.costmapZones;
    mapLoaded.value = true;
    renderScene();
  } catch {
    mapLoaded.value = false;
  } finally {
    mapLoading.value = false;
  }
}

function hashRobotName(name: string) {
  return [...name].reduce((total, char) => total + char.charCodeAt(0), 0);
}

function resetScene(robotName: string) {
  const hash = hashRobotName(robotName);
  const x = 18 + (hash % 24);
  const y = 18 + ((hash * 3) % 24);
  const yaw = (hash % 360) * (Math.PI / 180);

  robotPose.value = { x, y, yaw };
  goalPose.value = null;
  navStatus.value = 'idle';
  globalPath.value = [];
  localPath.value = [];
  trail.value = [{ x, y }];
  inputX.value = x.toFixed(1);
  inputY.value = y.toFixed(1);
  followRobot.value = true;
  initialPoseMode.value = false;
  updateViewCenter();
  refreshScan(0);
}

function updateViewCenter() {
  if (!followRobot.value) {
    return;
  }
  viewCenter.value = {
    x: robotPose.value.x,
    y: robotPose.value.y,
  };
}

function buildGlobalPath(start: Point, end: Point) {
  const midX = clamp((start.x + end.x) / 2 + (end.y - start.y) * 0.18, 8, 92);
  const midY = clamp((start.y + end.y) / 2 - (end.x - start.x) * 0.12, 8, 92);

  return [
    { ...start },
    { x: midX, y: start.y },
    { x: midX, y: midY },
    { ...end },
  ];
}

function segmentDistance(a: Point, b: Point) {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

function samplePolyline(points: Point[], stepDistance: number) {
  if (points.length < 2) {
    return points;
  }

  const [firstPoint, ...remainingPoints] = points;
  if (!firstPoint) {
    return points;
  }

  const sampled: Point[] = [{ ...firstPoint }];

  for (let index = 0; index < remainingPoints.length; index += 1) {
    const start = sampled[sampled.length - 1];
    const end = remainingPoints[index];
    if (!start || !end) {
      continue;
    }
    const distance = segmentDistance(start, end);
    const steps = Math.max(1, Math.ceil(distance / stepDistance));

    for (let step = 1; step <= steps; step += 1) {
      const t = step / steps;
      sampled.push({
        x: start.x + (end.x - start.x) * t,
        y: start.y + (end.y - start.y) * t,
      });
    }
  }

  return sampled;
}

function refreshLocalPath() {
  if (!goalPose.value || navStatus.value !== 'navigating') {
    localPath.value = [];
    return;
  }

  const dx = goalPose.value.x - robotPose.value.x;
  const dy = goalPose.value.y - robotPose.value.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 0.1) {
    localPath.value = [];
    return;
  }

  const normalX = dx / distance;
  const normalY = dy / distance;
  const lateral = {
    x: -normalY * 1.5,
    y: normalX * 1.5,
  };

  localPath.value = [
    { x: robotPose.value.x, y: robotPose.value.y },
    {
      x: robotPose.value.x + dx * 0.35 + lateral.x,
      y: robotPose.value.y + dy * 0.35 + lateral.y,
    },
    {
      x: robotPose.value.x + dx * 0.7,
      y: robotPose.value.y + dy * 0.7,
    },
    { x: goalPose.value.x, y: goalPose.value.y },
  ];
}

function refreshScan(timeSeconds: number) {
  const points: Point[] = [];

  for (let angleIndex = 0; angleIndex < 72; angleIndex += 1) {
    const angle = angleIndex * 0.11 + timeSeconds * 0.25;
    const baseRadius = 8 + Math.sin(angle * 2.4) * 1.2 + Math.cos(angle * 0.75) * 0.8;
    const obstacleInfluence = angleIndex % 12 === 0 ? -1.4 : 0.4;
    const radius = clamp(baseRadius + obstacleInfluence, 4.8, 12.5);

    points.push({
      x: clamp(robotPose.value.x + Math.cos(angle) * radius, 0, worldSize.value),
      y: clamp(robotPose.value.y + Math.sin(angle) * radius, 0, worldSize.value),
    });
  }

  scanPoints.value = points;
}

function updateNavigation(deltaSeconds: number) {
  if (navStatus.value !== 'navigating' || !goalPose.value) {
    refreshLocalPath();
    return;
  }

  const dx = goalPose.value.x - robotPose.value.x;
  const dy = goalPose.value.y - robotPose.value.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 0.6) {
    robotPose.value = {
      x: goalPose.value.x,
      y: goalPose.value.y,
      yaw: robotPose.value.yaw,
    };
    navStatus.value = 'arrived';
    localPath.value = [];
    message.success(`${props.robot} 已到达导航目标`);
    return;
  }

  const speed = 10;
  const step = Math.min(distance, speed * deltaSeconds);
  const normalX = dx / distance;
  const normalY = dy / distance;

  robotPose.value = {
    x: robotPose.value.x + normalX * step,
    y: robotPose.value.y + normalY * step,
    yaw: Math.atan2(normalY, normalX),
  };

  trail.value.push({ x: robotPose.value.x, y: robotPose.value.y });
  if (trail.value.length > 180) {
    trail.value.shift();
  }

  refreshLocalPath();
}

function worldToScreen(point: Point) {
  return {
    x: canvasWidth.value / 2 + (point.x - viewCenter.value.x) * zoom.value,
    y: canvasHeight.value / 2 + (point.y - viewCenter.value.y) * zoom.value,
  };
}

function screenToWorld(clientX: number, clientY: number) {
  if (!canvasRef.value) {
    return null;
  }

  const rect = canvasRef.value.getBoundingClientRect();
  const x = viewCenter.value.x + (clientX - rect.left - rect.width / 2) / zoom.value;
  const y = viewCenter.value.y + (clientY - rect.top - rect.height / 2) / zoom.value;

  return {
    x: clamp(x, 0, worldSize.value),
    y: clamp(y, 0, worldSize.value),
  };
}

function setGoalFromWorld(point: Point) {
  goalPose.value = { ...point, yaw: 0 };
  globalPath.value = buildGlobalPath(robotPose.value, point);
  refreshLocalPath();
}

function commitInitialPose(point: Point) {
  robotPose.value = { ...point, yaw: robotPose.value.yaw };
  trail.value = [{ x: point.x, y: point.y }];
  inputX.value = point.x.toFixed(1);
  inputY.value = point.y.toFixed(1);
  initialPoseMode.value = false;
  navStatus.value = 'idle';
  refreshLocalPath();
  refreshScan(0);
  message.success(`已设置初始位姿 [${point.x.toFixed(1)}, ${point.y.toFixed(1)}]`);
}

function handleCanvasMouseDown(event: MouseEvent) {
  dragState.active = true;
  dragState.moved = false;
  dragState.startClientX = event.clientX;
  dragState.startClientY = event.clientY;
  dragState.startCenterX = viewCenter.value.x;
  dragState.startCenterY = viewCenter.value.y;
}

function handleCanvasMouseMove(event: MouseEvent) {
  if (!dragState.active) {
    return;
  }

  const deltaX = event.clientX - dragState.startClientX;
  const deltaY = event.clientY - dragState.startClientY;
  if (Math.abs(deltaX) > 2 || Math.abs(deltaY) > 2) {
    dragState.moved = true;
  }

  if (!dragState.moved) {
    return;
  }

  followRobot.value = false;
  viewCenter.value = {
    x: clamp(dragState.startCenterX - deltaX / zoom.value, 0, worldSize.value),
    y: clamp(dragState.startCenterY - deltaY / zoom.value, 0, worldSize.value),
  };
}

function handleCanvasMouseUp(event: MouseEvent) {
  if (!dragState.active) {
    return;
  }

  dragState.active = false;
  const point = screenToWorld(event.clientX, event.clientY);
  if (!point || dragState.moved) {
    return;
  }

  if (initialPoseMode.value) {
    commitInitialPose(point);
    return;
  }

  setGoalFromWorld(point);
}

function handleCanvasWheel(event: WheelEvent) {
  event.preventDefault();

  const worldBefore = screenToWorld(event.clientX, event.clientY);
  const factor = event.deltaY > 0 ? 0.9 : 1.1;
  zoom.value = clamp(zoom.value * factor, 3, 14);

  if (!worldBefore || !canvasRef.value) {
    return;
  }

  const rect = canvasRef.value.getBoundingClientRect();
  const pointerX = event.clientX - rect.left - rect.width / 2;
  const pointerY = event.clientY - rect.top - rect.height / 2;

  viewCenter.value = {
    x: clamp(worldBefore.x - pointerX / zoom.value, 0, worldSize.value),
    y: clamp(worldBefore.y - pointerY / zoom.value, 0, worldSize.value),
  };
  followRobot.value = false;
}

function resetView() {
  followRobot.value = true;
  zoom.value = 6.2;
  updateViewCenter();
}

function sendGoal() {
  if (!goalPose.value) {
    message.warning('请先点击地图设置导航目标');
    return;
  }

  navStatus.value = 'navigating';
  followRobot.value = true;
  globalPath.value = buildGlobalPath(robotPose.value, goalPose.value);
  refreshLocalPath();
  message.success(
    `已下发导航目标 [${goalPose.value.x.toFixed(1)}, ${goalPose.value.y.toFixed(1)}]`,
  );
}

function clearGoal() {
  goalPose.value = null;
  globalPath.value = [];
  localPath.value = [];
  navStatus.value = 'idle';
}

function setInitialPose() {
  const x = Number.parseFloat(inputX.value);
  const y = Number.parseFloat(inputY.value);

  if (Number.isNaN(x) || Number.isNaN(y)) {
    message.error('请输入有效的坐标');
    return;
  }

  commitInitialPose({
    x: clamp(x, 0, worldSize.value),
    y: clamp(y, 0, worldSize.value),
  });
}

function toggleInitialPoseMode() {
  initialPoseMode.value = !initialPoseMode.value;
}

function updateCanvasSize() {
  if (!mapContainer.value || !canvasRef.value) {
    return;
  }

  const rect = mapContainer.value.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;

  canvasWidth.value = rect.width;
  canvasHeight.value = rect.height;
  canvasRef.value.width = Math.floor(rect.width * ratio);
  canvasRef.value.height = Math.floor(rect.height * ratio);

  const context = canvasRef.value.getContext('2d');
  if (context) {
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
}

function drawLine(
  context: CanvasRenderingContext2D,
  points: Point[],
  options: {
    color: string;
    dash?: number[];
    lineWidth: number;
  },
) {
  if (points.length < 2) {
    return;
  }

  context.save();
  context.beginPath();
  context.setLineDash(options.dash ?? []);
  context.strokeStyle = options.color;
  context.lineWidth = options.lineWidth;

  const [firstPoint] = points;
  if (!firstPoint) {
    context.restore();
    return;
  }

  const start = worldToScreen(firstPoint);
  context.moveTo(start.x, start.y);

  points.slice(1).forEach((point) => {
    const screen = worldToScreen(point);
    context.lineTo(screen.x, screen.y);
  });

  context.stroke();
  context.restore();
}

function drawMapLayer(context: CanvasRenderingContext2D) {
  context.fillStyle = '#0f172a';
  context.fillRect(0, 0, canvasWidth.value, canvasHeight.value);

  context.save();
  context.strokeStyle = 'rgba(148, 163, 184, 0.15)';
  context.lineWidth = 1;

  for (let grid = 0; grid <= worldSize.value; grid += 5) {
    const verticalStart = worldToScreen({ x: grid, y: 0 });
    const verticalEnd = worldToScreen({ x: grid, y: worldSize.value });
    context.beginPath();
    context.moveTo(verticalStart.x, verticalStart.y);
    context.lineTo(verticalEnd.x, verticalEnd.y);
    context.stroke();

    const horizontalStart = worldToScreen({ x: 0, y: grid });
    const horizontalEnd = worldToScreen({ x: worldSize.value, y: grid });
    context.beginPath();
    context.moveTo(horizontalStart.x, horizontalStart.y);
    context.lineTo(horizontalEnd.x, horizontalEnd.y);
    context.stroke();
  }

  context.restore();

  obstacles.value.forEach((obstacle) => {
    const topLeft = worldToScreen({ x: obstacle.x, y: obstacle.y });
    const bottomRight = worldToScreen({
      x: obstacle.x + obstacle.width,
      y: obstacle.y + obstacle.height,
    });

    context.fillStyle = '#334155';
    context.fillRect(
      topLeft.x,
      topLeft.y,
      bottomRight.x - topLeft.x,
      bottomRight.y - topLeft.y,
    );
    context.strokeStyle = '#64748b';
    context.lineWidth = 1.2;
    context.strokeRect(
      topLeft.x,
      topLeft.y,
      bottomRight.x - topLeft.x,
      bottomRight.y - topLeft.y,
    );
  });
}

function drawCostmapLayer(context: CanvasRenderingContext2D) {
  costmapZones.value.forEach((zone) => {
    const topLeft = worldToScreen({
      x: zone.x,
      y: zone.y,
    });
    const bottomRight = worldToScreen({
      x: zone.x + zone.width,
      y: zone.y + zone.height,
    });

    context.fillStyle = 'rgba(239, 68, 68, 0.14)';
    context.fillRect(
      topLeft.x,
      topLeft.y,
      bottomRight.x - topLeft.x,
      bottomRight.y - topLeft.y,
    );
  });
}

function drawTrailLayer(context: CanvasRenderingContext2D) {
  if (trail.value.length < 2) {
    return;
  }

  const sampledTrail = samplePolyline(trail.value, 0.8);
  drawLine(context, sampledTrail, {
    color: 'rgba(56, 189, 248, 0.45)',
    lineWidth: 2,
  });
}

function drawGoalLayer(context: CanvasRenderingContext2D) {
  if (!goalPose.value) {
    return;
  }

  const screen = worldToScreen(goalPose.value);
  context.save();
  context.strokeStyle = '#ef4444';
  context.lineWidth = 2;
  context.beginPath();
  context.arc(screen.x, screen.y, 9, 0, Math.PI * 2);
  context.stroke();

  context.beginPath();
  context.moveTo(screen.x - 13, screen.y);
  context.lineTo(screen.x + 13, screen.y);
  context.moveTo(screen.x, screen.y - 13);
  context.lineTo(screen.x, screen.y + 13);
  context.stroke();
  context.restore();
}

function drawRobotLayer(context: CanvasRenderingContext2D) {
  const screen = worldToScreen(robotPose.value);
  const radius = 9;

  context.save();
  context.translate(screen.x, screen.y);
  context.rotate(robotPose.value.yaw);

  context.beginPath();
  context.fillStyle = '#22c55e';
  context.arc(0, 0, radius, 0, Math.PI * 2);
  context.fill();

  context.beginPath();
  context.moveTo(12, 0);
  context.lineTo(-7, -6);
  context.lineTo(-7, 6);
  context.closePath();
  context.fillStyle = '#bbf7d0';
  context.fill();
  context.restore();
}

function drawScanLayer(context: CanvasRenderingContext2D) {
  if (!scanPoints.value.length) {
    return;
  }

  context.save();
  context.fillStyle = 'rgba(34, 211, 238, 0.85)';
  scanPoints.value.forEach((point) => {
    const screen = worldToScreen(point);
    context.beginPath();
    context.arc(screen.x, screen.y, 1.7, 0, Math.PI * 2);
    context.fill();
  });
  context.restore();
}

function drawAxisOverlay(context: CanvasRenderingContext2D) {
  context.save();
  context.strokeStyle = 'rgba(148, 163, 184, 0.35)';
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(canvasWidth.value / 2 - 10, canvasHeight.value / 2);
  context.lineTo(canvasWidth.value / 2 + 10, canvasHeight.value / 2);
  context.moveTo(canvasWidth.value / 2, canvasHeight.value / 2 - 10);
  context.lineTo(canvasWidth.value / 2, canvasHeight.value / 2 + 10);
  context.stroke();
  context.restore();
}

function renderScene() {
  if (!canvasRef.value) {
    return;
  }

  const context = canvasRef.value.getContext('2d');
  if (!context) {
    return;
  }

  context.clearRect(0, 0, canvasWidth.value, canvasHeight.value);

  if (showMap.value) {
    drawMapLayer(context);
  } else {
    context.fillStyle = '#020617';
    context.fillRect(0, 0, canvasWidth.value, canvasHeight.value);
  }

  if (showCostmap.value) {
    drawCostmapLayer(context);
  }
  if (showTrail.value) {
    drawTrailLayer(context);
  }
  if (showGlobalPath.value) {
    drawLine(context, globalPath.value, {
      color: '#60a5fa',
      dash: [8, 6],
      lineWidth: 2,
    });
  }
  if (showLocalPath.value) {
    drawLine(context, localPath.value, {
      color: '#22c55e',
      lineWidth: 2.5,
    });
  }
  if (showScan.value) {
    drawScanLayer(context);
  }
  drawGoalLayer(context);
  drawRobotLayer(context);
  drawAxisOverlay(context);
}

function animate(timestamp: number) {
  if (!previousTimestamp) {
    previousTimestamp = timestamp;
  }

  const deltaSeconds = (timestamp - previousTimestamp) / 1000;
  previousTimestamp = timestamp;

  updateNavigation(deltaSeconds);
  refreshScan(timestamp / 1000);
  updateViewCenter();
  renderScene();
  frameHandle = window.requestAnimationFrame(animate);
}

watch(
  () => props.robot,
  async (robotName) => {
    resetScene(robotName);
    await loadMap(robotName);
  },
  { immediate: true },
);

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    updateCanvasSize();
    renderScene();
  });

  if (mapContainer.value) {
    resizeObserver.observe(mapContainer.value);
  }

  updateCanvasSize();
  renderScene();
  frameHandle = window.requestAnimationFrame(animate);
});

onBeforeUnmount(() => {
  if (resizeObserver && mapContainer.value) {
    resizeObserver.unobserve(mapContainer.value);
  }
  resizeObserver?.disconnect();
  window.cancelAnimationFrame(frameHandle);
});
</script>

<template>
  <NCard size="small" title="导航地图 / RViz 视图" class="h-full">
    <template #header-extra>
      <div class="flex items-center gap-2 text-xs">
        <NTag :bordered="false" :type="statusType">
          {{ statusLabel }}
        </NTag>
        <NTag :bordered="false" type="success">
          {{ robot }}
        </NTag>
      </div>
    </template>

    <div class="space-y-3">
      <div class="flex flex-wrap items-center gap-2">
        <NInput v-model:value="inputX" placeholder="X" size="small" style="width: 76px" />
        <NInput v-model:value="inputY" placeholder="Y" size="small" style="width: 76px" />
        <NButton size="small" @click="setInitialPose">设置初始位姿</NButton>
        <NButton size="small" :type="initialPoseMode ? 'warning' : 'default'" @click="toggleInitialPoseMode">
          {{ initialPoseMode ? '取消点选初始位姿' : '点选初始位姿' }}
        </NButton>
        <NButton size="small" type="primary" :disabled="!goalPose" @click="sendGoal">
          发送导航目标
        </NButton>
        <NButton size="small" :disabled="!goalPose" @click="clearGoal">清除目标</NButton>
        <NButton size="small" @click="resetView">重置视图</NButton>
      </div>

      <div class="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-slate-500">
        <NCheckbox v-model:checked="showMap">地图</NCheckbox>
        <NCheckbox v-model:checked="showCostmap">代价地图</NCheckbox>
        <NCheckbox v-model:checked="showScan">激光扫描</NCheckbox>
        <NCheckbox v-model:checked="showGlobalPath">全局路径</NCheckbox>
        <NCheckbox v-model:checked="showLocalPath">局部路径</NCheckbox>
        <NCheckbox v-model:checked="showTrail">历史轨迹</NCheckbox>
        <NCheckbox v-model:checked="followRobot">跟随机器人</NCheckbox>
      </div>

      <div
        ref="mapContainer"
        class="relative h-[460px] w-full overflow-hidden rounded-md border border-slate-200 bg-slate-950"
      >
        <canvas
          ref="canvasRef"
          class="absolute inset-0 h-full w-full cursor-crosshair"
          @mousedown="handleCanvasMouseDown"
          @mousemove="handleCanvasMouseMove"
          @mouseup="handleCanvasMouseUp"
          @mouseleave="handleCanvasMouseUp"
          @wheel="handleCanvasWheel"
        />

        <div class="pointer-events-none absolute left-3 top-3 rounded bg-slate-900/70 px-3 py-2 text-[11px] text-slate-200 backdrop-blur">
          <div>左键点击：{{ initialPoseMode ? '设置初始位姿' : '设置目标点' }}</div>
          <div>拖动画布：平移视图</div>
          <div>滚轮：缩放</div>
          <div>{{ mapLoading ? '地图加载中...' : mapLoaded ? '地图已从后端加载' : '地图加载失败，显示空画布' }}</div>
        </div>

        <div class="pointer-events-none absolute bottom-3 right-3 rounded bg-slate-900/70 px-3 py-2 text-[11px] text-slate-200 backdrop-blur">
          <div>缩放 {{ zoom.toFixed(1) }}x</div>
          <div>视图中心 [{{ viewCenter.x.toFixed(1) }}, {{ viewCenter.y.toFixed(1) }}]</div>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 text-xs text-slate-600 xl:grid-cols-3">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-3">
          <div class="mb-1 font-medium text-slate-700">机器人状态</div>
          <div>位姿: [{{ robotPose.x.toFixed(1) }}, {{ robotPose.y.toFixed(1) }}]</div>
          <div>朝向: {{ (robotPose.yaw * 57.3).toFixed(1) }}°</div>
          <div>导航: {{ statusLabel }}</div>
        </div>

        <div class="rounded-md border border-slate-200 bg-slate-50 p-3">
          <div class="mb-1 font-medium text-slate-700">目标 / 视图</div>
          <div>{{ sceneSummary }}</div>
          <div>跟随机器人: {{ followRobot ? '开启' : '关闭' }}</div>
          <div>轨迹点数: {{ trail.length }}</div>
        </div>

        <div class="rounded-md border border-slate-200 bg-slate-50 p-3">
          <div class="mb-1 font-medium text-slate-700">图层状态</div>
          <div>全局路径: {{ showGlobalPath ? '显示' : '隐藏' }}</div>
          <div>局部路径: {{ showLocalPath ? '显示' : '隐藏' }}</div>
          <div>扫描点: {{ showScan ? scanPoints.length : 0 }} 个</div>
          <div>障碍物: {{ obstacles.length }} 个</div>
        </div>
      </div>
    </div>
  </NCard>
</template>
