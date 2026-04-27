<template>
  <div class="logic-flow">
    <h3 class="logic-flow__title">EPC GEN2 逻辑流程</h3>
    <div class="logic-flow__list">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="logic-flow__step-container"
      >
        <div
          class="logic-flow__step"
          :class="{ 'logic-flow__step--active': index === activeStep }"
          @click="handleClick(step)"
        >
          <span class="logic-flow__step-num">{{
            String(index + 1).padStart(2, "0")
          }}</span>
          <span class="logic-flow__step-text">{{ step.label }}</span>
          <span
            v-if="step.active"
            class="material-symbols-outlined logic-flow__step-icon"
            >arrow_forward</span
          >
        </div>
        <div
          v-if="index < steps.length - 1"
          class="logic-flow__connector"
        ></div>
      </div>
    </div>

    <div class="logic-flow__stats">
      <div class="logic-flow__stats-title">协议统计</div>
      <div class="logic-flow__stats-row">
        <span>当前 Q 值</span>
        <span class="num-font">2^{{ currentQ }} ({{ rangeCount }})</span>
      </div>
      <div class="logic-flow__stats-row">
        <span>盘存轮次</span>
        <span class="num-font">00142</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  Q: {
    type: Number,
    default: undefined,
  },
  hasSlotZero: {
    type: Boolean,
    default: false,
  },
  stage: {
    type: String,
    default: null,
  },
});

const emit = defineEmits([
  "onQuery",
  "onQueryRep",
  "onSlotZero",
  "onRN16Response",
  "onAck",
]);

const currentQ = computed(() => (typeof props.Q === "string" ? props.Q : 4));
const rangeCount = computed(() => 2 ** currentQ.value);
const QueryCommand = ref("onQuery"); // 由于查询指令有许多变体，这里用一个 ref 来统一管理事件名称

const activeStep = ref(0);
const steps = computed(() => [
  {
    id: 1,
    label:
      QueryCommand.value === "onQuery"
        ? `发送 Query(${props.Q}) 指令`
        : "发送 QueryRep 指令",
    action: QueryCommand.value,
  },
  { id: 2, label: "slot counter是否为 0？", action: "onSlotZero" },
  { id: 3, label: "RN16 响应", action: "onRN16Response" },
  { id: 4, label: "确认握手 (ACK)", action: "onAck" },
  { id: 5, label: "EPC 数据传输" },
]);

const handleClick = (step) => {
  if (step.action === "onSlotZero") {
    emit("onSlotZero");

    if (!props.hasSlotZero) {
      // 没有tag的slot counter为0 → 走 QueryRep（停留或循环）
      activeStep.value = 0; // 回到判断或停留
      QueryCommand.value = "onQueryRep"; // 切换到 QueryRep 指令
      return;
    }
  } else if (step.action) {
    emit(step.action);
  }

  if (activeStep.value < steps.value.length - 1) {
    activeStep.value += 1;
  } else {
    activeStep.value = 0;
  }
};

watch(
  () => props.hasSlotZero,
  (newVal) => {
    if (newVal) {
      activeStep.value = 2; // 有标签的slot counter 为 0 → 进入 RN16 响应
    }
  },
);

watch(
  () => props.stage,
  (newVal) => {
    if (newVal === "COLLISION") {
      activeStep.value = 0; // ACK阶段
    }
  },
);
</script>

<style lang="scss" scoped>
.logic-flow {
  width: 280px;
  background-color: var(--surface-container-low);
  padding: var(--spacing-lg);
  overflow-y: auto;
  border-right: 1px solid rgba(67, 70, 86, 0.1);

  // 自定义滚轮样式
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--outline-variant);
    border-radius: var(--radius-full);
    transition: background 0.2s ease;

    &:hover {
      background: var(--outline);
    }
  }

  &__title {
    font-size: 10px;
    font-weight: 700;
    color: var(--outline);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-lg);
  }

  &__list {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  &__step-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  &__step {
    width: 100%;
    padding: var(--spacing-md);
    background-color: var(--surface-container-highest);
    border: 1px solid rgba(142, 144, 162, 0.1);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    opacity: 0.6;
    transition: all 0.3s;

    &:hover {
      cursor: pointer;
    }

    &:not(.logic-flow__step--active) {
      &:hover {
        cursor: not-allowed;
      }
    }

    &--active {
      opacity: 1;
      background-color: rgba(46, 91, 255, 0.1);
      border-color: rgba(46, 91, 255, 0.4);
      box-shadow: 0 0 10px rgba(46, 91, 255, 0.1);

      .logic-flow__step-num {
        color: var(--primary);
        font-weight: 700;
      }

      .logic-flow__step-text {
        color: var(--primary);
        font-weight: 700;
      }
    }
  }

  &__step-num {
    font-size: 11px;
    color: var(--outline);
    font-family: "Space Grotesk", sans-serif;
  }

  &__step-text {
    font-size: 12px;
    color: var(--on-surface-variant);
  }

  &__step-icon {
    font-size: 14px;
    color: var(--primary);
    margin-left: auto;
  }

  &__connector {
    width: 1px;
    height: 16px;
    background-color: rgba(67, 70, 86, 0.3);
    margin: 4px 0;
  }

  &__stats {
    margin-top: var(--spacing-xl);
    padding: var(--spacing-md);
    background-color: var(--surface-container-lowest);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(142, 144, 162, 0.1);
  }

  &__stats-title {
    font-size: 11px;
    color: var(--secondary);
    font-weight: 700;
    margin-bottom: var(--spacing-md);
  }

  &__stats-row {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--outline);
    margin-bottom: var(--spacing-sm);

    .num-font {
      color: var(--on-surface);
      font-size: 12px;
    }
  }
}
</style>
