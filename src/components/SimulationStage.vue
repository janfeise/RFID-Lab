<template>
  <div class="stage">
    <!-- Background Grid -->
    <div class="stage__grid"></div>

    <!-- Ambiance -->
    <div class="stage__glow"></div>

    <!-- Central Reader -->
    <div
      class="stage__reader"
      :class="{ 'stage__reader--ack': props.readerAcked }"
    >
      <div class="stage__signal-wave stage__signal-wave--1"></div>
      <div class="stage__signal-wave stage__signal-wave--2"></div>

      <div class="stage__reader-core">
        <span class="material-symbols-outlined stage__reader-icon"
          >sensors</span
        >
        <span class="stage__reader-label">READER_01</span>
      </div>
    </div>

    <!-- Floating Tags -->
    <div
      v-for="(tag, i) in props.tags"
      :key="tag.EPC"
      class="stage__tag"
      :class="[
        `stage__tag--${tag.status}`,
        {
          'stage__tag--ack': tag.slotCounter === 0 && props.stage === 'ACK',
        },
      ]"
      :style="getTagPosition(tag, i)"
    >
      <div class="stage__tag-card">
        <div class="stage__tag-header">
          <span class="stage__tag-id">TAG_{{ i + 1 }}</span>
          <!-- <span class="stage__tag-id">{{ tag.EPC }}</span> -->
          <div class="stage__tag-indicator"></div>
        </div>
        <div
          class="stage__tag-slot"
          :class="{
            'stage__text--zero': tag.slotCounter === 0,
          }"
        >
          slot counter:
          {{ tag.slotCounter !== null ? tag.slotCounter : "null" }}
        </div>
        <div class="stage__tag-status">状态：{{ tag.status }}</div>
      </div>
      <div v-if="tag.status === 'success'" class="stage__tag-beam"></div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, computed } from "vue";

const props = defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
  stage: {
    type: String,
    default: null,
  },
  readerAcked: {
    type: Boolean,
    default: false,
  },
});

const tagPositions = reactive({});

const getTagKey = (tag, index) => {
  return tag?.EPC ?? `idx-${index}`;
};

const createRandomPosition = () => {
  return {
    top: `${Math.random() * 80 + 10}%`,
    left: `${Math.random() * 80 + 10}%`,
  };
};

const getTagPosition = (tag, index) => {
  const key = getTagKey(tag, index);
  if (!tagPositions[key]) {
    tagPositions[key] = createRandomPosition();
  }
  return tagPositions[key];
};

watch(
  () => props.tags.map((tag, index) => getTagKey(tag, index)),
  (keys) => {
    const current = new Set(keys);
    Object.keys(tagPositions).forEach((key) => {
      if (!current.has(key)) {
        delete tagPositions[key];
      }
    });
  },
  { immediate: true },
);

watch(
  () => props.stage,
  (newStage) => {
    if (newStage === "ACK") {
      // ACK阶段，说明只有一个 tag 响应
      console.log("进入 ACK 阶段，只有一个标签响应，准备高亮显示该标签");
    }
  },
);
</script>

<style lang="scss" scoped>
.stage {
  flex: 1;
  position: relative;
  overflow: hidden;
  background-color: var(--surface);
  display: flex;
  align-items: center;
  justify-content: center;

  &__grid {
    position: absolute;
    inset: 0;
    opacity: 0.03;
    background-image: radial-gradient(
      circle,
      var(--primary) 1px,
      transparent 1px
    );
    background-size: 40px 40px;
  }

  &__glow {
    position: absolute;
    width: 600px;
    height: 600px;
    background: radial-gradient(
      circle,
      rgba(184, 195, 255, 0.05) 0%,
      transparent 70%
    );
    filter: blur(120px);
  }

  &__reader {
    position: relative;
    z-index: 100;

    &--ack {
      .stage__reader-core {
        border-color: rgba(90, 218, 206, 0.8);
        box-shadow: 0 0 36px rgba(90, 218, 206, 0.45);
      }

      .stage__reader-icon,
      .stage__reader-label {
        color: var(--secondary);
      }

      .stage__signal-wave {
        border-color: rgba(90, 218, 206, 0.28);
      }
    }
  }

  &__reader-core {
    width: 96px;
    height: 96px;
    background-color: var(--surface-container-high);
    border: 2px solid rgba(184, 195, 255, 0.4);
    border-radius: var(--radius-md);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 30px rgba(46, 91, 255, 0.2);
  }

  &__reader-icon {
    font-size: 2.5rem;
    color: var(--primary);
    margin-bottom: var(--spacing-xs);
  }

  &__reader-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.3em;
    color: var(--primary);
    text-transform: uppercase;
    font-family: "Space Grotesk", sans-serif;
  }

  &__signal-wave {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border-radius: var(--radius-full);
    border: 2px solid rgba(184, 195, 255, 0.1);
    z-index: 5;

    &--1 {
      width: 256px;
      height: 256px;
      animation: ping-signal 2s infinite;
    }

    &--2 {
      width: 384px;
      height: 384px;
      animation: ping-signal 2s infinite;
      animation-delay: 1s;
    }
  }

  &__tag {
    position: absolute;
    width: 144px;
    z-index: 20;
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      z-index: 80;
    }
  }

  &__tag-card {
    padding: var(--spacing-md);
    background-color: rgba(34, 42, 61, 0.8);
    backdrop-filter: blur(12px);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(142, 144, 162, 0.2);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  &__tag-header {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: left;
    position: relative;
  }

  &__tag-id {
    font-size: 9px;
    font-family: "Space Grotesk", sans-serif;
    color: var(--outline);
  }

  &__tag-indicator {
    position: absolute;
    top: 0;
    right: 0;
    width: 6px;
    height: 6px;
    border-radius: var(--radius-full);
    background-color: var(--outline);
  }

  &__tag-slot {
    font-size: 10px;
    font-weight: 700;
    color: var(--on-surface);

    &.stage__text--zero {
      color: var(--error);
      font-weight: 700;
    }
  }

  &__tag-status {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--outline);
  }

  // Tag Status Overrides
  &--success {
    .stage__tag-card {
      border-color: rgba(90, 218, 206, 0.4);
      box-shadow: 0 0 15px rgba(90, 218, 206, 0.2);
    }
    .stage__tag-id,
    .stage__tag-status {
      color: var(--secondary);
    }
    .stage__tag-indicator {
      background-color: var(--secondary);
    }
  }

  &--collision {
    .stage__tag-card {
      border-color: rgba(255, 180, 171, 0.4);
      box-shadow: 0 0 15px rgba(255, 180, 171, 0.2);
    }
    .stage__tag-id,
    .stage__tag-status {
      color: var(--error);
    }
    .stage__tag-indicator {
      background-color: var(--error);
      animation: pulse-error 1s infinite;
    }
  }

  &__tag--ack {
    z-index: 999;

    .stage__tag-card {
      border-color: rgba(90, 218, 206, 0.7);
      box-shadow: 0 0 20px rgba(90, 218, 206, 0.35);
    }

    .stage__tag-id,
    .stage__tag-status,
    .stage__tag-slot {
      color: var(--secondary);
    }

    .stage__tag-indicator {
      background-color: var(--secondary);
      box-shadow: 0 0 8px rgba(90, 218, 206, 0.7);
    }
  }

  &__tag-beam {
    position: absolute;
    top: 100%;
    left: 50%;
    width: 1px;
    height: 64px;
    background: linear-gradient(
      to bottom,
      rgba(90, 218, 206, 0.4),
      transparent
    );
  }
}

@keyframes pulse-error {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

@keyframes ping-signal {
  0% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0.3;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}
</style>
