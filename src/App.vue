<template>
  <div class="app-container">
    <AppHeader />
    <AppSidebar
      :collapsed="sidebarCollapsed"
      @start="modalVisible = true"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
    />

    <main
      class="main-workspace"
      :class="{ 'main-workspace--collapsed': sidebarCollapsed }"
    >
      <div class="workspace-layout">
        <LogicFlow
          :Q="config.qValue"
          :hasSlotZero="protocolState.hasSlotZero"
          @onQuery="onQuery"
          @onQueryRep="onQueryRep"
          @onSlotZero="onSlotZero"
          @onRN16Response="onRN16Response"
          @onAck="onAck"
        />
        <SimulationStage
          :tags="tags"
          :stage="protocolState.stage"
          :readerAcked="protocolState.readerAcked"
        />
        <StatsPanel :tags="tags" />
      </div>

      <ConsolePanel />
    </main>

    <!-- FAB -->
    <button class="fab" @click="modalVisible = true">
      <span class="material-symbols-outlined">add_box</span>
    </button>

    <InitModal :visible="modalVisible" @confirm="handleStartSimulation" />
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import AppHeader from "./layout/AppHeader.vue";
import AppSidebar from "./layout/AppSidebar.vue";
import LogicFlow from "./components/LogicFlow.vue";
import SimulationStage from "./components/SimulationStage.vue";
import StatsPanel from "./components/StatsPanel.vue";
import ConsolePanel from "./components/ConsolePanel.vue";
import InitModal from "./components/InitModal.vue";
import { Reader, Tag } from "./utils/core.js";

const modalVisible = ref(true); // 模态框初始态
const sidebarCollapsed = ref(false);
const config = reactive({}); // 存储仿真配置
const reader = ref(null); // 仿真中的 Reader 实例
const tags = reactive([]); // 仿真中的 Tag 实例列表

// 状态控制
const protocolState = reactive({
  hasSlotZero: false, // 是否有标签的 slot counter 为 0，用于控制 QueryRep 循环
  stage: null, // 阶段控制，用于判断是否有冲突（多个RN16响应），若只有一个RN16则进入ACK阶段
  readerAcked: false, // ACK确认后用于高亮 Reader
});

const initReader = (Q) => {
  return new Reader(Q);
};

const initTags = (count) => {
  for (let i = 0; i < count; i++) {
    tags.push(new Tag());
  }
};

const handleStartSimulation = (simulationConfig) => {
  Object.assign(config, simulationConfig);
  modalVisible.value = false;

  // 初始化 Reader 和 Tags
  reader.value = initReader(config.qValue);
  initTags(config.tagCount);
};

// Query(Q) 指令
const onQuery = () => {
  // 状态初始化
  resetState();

  tags.forEach((tag) => {
    tag.onQuery(config.qValue);
  });
};

// QueryRep() 指令
const onQueryRep = () => {
  // 状态初始化
  resetState();

  tags.forEach((tag) => {
    tag.onQueryRep();
  });
};

// 判断是否有标签的 slot counter 都为 0
const onSlotZero = () => {
  protocolState.readerAcked = false;

  const hasSlotZero = tags
    .map((tag) => {
      if (tag.isSlotZero()) {
        tag.hasResponded = true; // 进入响应状态，等待 RN16
        return true;
      }
      return false;
    })
    .includes(true);

  protocolState.hasSlotZero = hasSlotZero; // 默认为false，当有tag的slot counter为0时改为true，退出 QueryRep 循环，进入 RN16 响应阶段
  console.log("Slot Counter 是否为 0？", hasSlotZero);
};

// 响应 RN16
const onRN16Response = () => {
  const tagsRespond = []; // 收集所有响应 RN16 的标签
  tags.forEach((tag) => {
    const rn16Response = tag.respondRN16();
    if (rn16Response) {
      tagsRespond.push(rn16Response);
    }
  });

  const readerRes = reader.value.handleResponses(tagsRespond);
  if (readerRes) {
    console.log("Reader ACK Response:", readerRes);
    protocolState.stage = "ACK";
    protocolState.readerAcked = false;
    console.log("进入 ACK 阶段，等待 EPC 数据传输");
  } else if (tagsRespond.length > 1) {
    console.log("标签发生t冲突，进入 COLLISION 阶段");
    protocolState.stage = "COLLISION";
    protocolState.readerAcked = false;
  } else {
    // TODO
  }
};

const onAck = () => {
  // TODO：日志需输出 ACK 响应的 RN16 值，以便在 StatsPanel 中显示（下方控制台显示）
  protocolState.readerAcked = true;
};

/**
 * 辅助函数：初始化状态
 */
const resetState = () => {
  protocolState.hasSlotZero = false;
  protocolState.stage = null;
  protocolState.readerAcked = false;
};
</script>

<style lang="scss">
@use "./styles/main.scss";

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  transition: filter 0.3s ease;

  &--blurred {
    filter: blur(8px);
    pointer-events: none;
  }
}

.main-workspace {
  margin-left: 256px;
  margin-top: 64px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.28s ease;

  &--collapsed {
    margin-left: 72px;
  }
}

.workspace-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.fab {
  position: fixed;
  bottom: var(--spacing-xl);
  right: var(--spacing-xl);
  width: 56px;
  height: 56px;
  background-color: var(--primary-container);
  color: var(--on-primary);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-fab);
  box-shadow: 0 4px 30px rgba(46, 91, 255, 0.4);
  transition: all 0.3s;

  &:hover {
    transform: scale(1.05);
  }
  &:active {
    transform: scale(0.95);
  }

  span {
    font-size: 24px;
  }
}
</style>
