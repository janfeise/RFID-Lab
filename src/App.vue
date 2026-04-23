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
        />
        <SimulationStage :tags="tags" />
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
const reader = reactive({}); // 仿真中的 Reader 实例
const tags = reactive([]); // 仿真中的 Tag 实例列表

// 状态控制
const protocolState = reactive({
  hasSlotZero: false,
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
  Object.assign(reader, initReader(config.qValue));
  initTags(config.tagCount);
};

// Query(Q) 指令
const onQuery = () => {
  tags.forEach((tag) => {
    tag.onQuery(config.qValue);
  });
};

// QueryRep() 指令
const onQueryRep = () => {
  tags.forEach((tag) => {
    tag.onQueryRep();
  });
};

// 判断是否有标签的 slot counter 都为 0
const onSlotZero = () => {
  const hasSlotZero = tags
    .map((tag) => {
      if (tag.isSlotZero()) {
        tag.hasResponded = true; // 进入响应状态，等待 RN16
        return true;
      }
      return false;
    })
    .includes(true);

  protocolState.hasSlotZero = hasSlotZero;
};

// 响应 RN16
const onRN16Response = () => {
  tags.forEach((tag) => {
    tag.respondRN16(); // RN16 响应
  });
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
