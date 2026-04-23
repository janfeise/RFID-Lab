<template>
  <div class="console">
    <!-- Controls -->
    <div class="console__controls">
      <div class="console__playback">
        <button class="console__btn console__btn--primary">
          <span class="material-symbols-outlined">play_arrow</span>
        </button>
        <button class="console__btn">
          <span class="material-symbols-outlined">step_over</span>
        </button>
        <button class="console__btn console__btn--danger">
          <span class="material-symbols-outlined">refresh</span>
        </button>
      </div>

      <div class="console__divider"></div>

      <div class="console__params">
        <span class="console__label">Q 参数调节</span>
        <div class="console__slider-group">
          <input 
            type="range" 
            min="0" 
            max="15" 
            v-model="qValue"
            class="console__slider"
          >
          <div class="console__slider-labels">
            <span>Q=0</span>
            <span>Q=15</span>
          </div>
        </div>
        <div class="console__badge">Q={{ qValue }}</div>
      </div>

      <div class="console__signal">
        <div class="console__signal-info">
          <span class="console__label">信号强度</span>
          <div class="console__signal-bars">
            <div v-for="i in 4" :key="i" class="console__signal-bar" :class="{ 'console__signal-bar--active': i <= 3 }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Logs -->
    <div class="console__logs custom-scrollbar" ref="logRef">
      <div v-for="(log, index) in logEntries" :key="index" class="console__log-entry">
        <span class="console__log-time">[{{ log.time }}]</span>
        <span :class="['console__log-source', `console__log-source--${log.sourceType}`]">
          [{{ log.source }}]
        </span>
        <span :class="['console__log-msg', log.type ? `console__log-msg--${log.type}` : '']">
          {{ log.message }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const qValue = ref(4);
const logEntries = [
  { time: '14:20:01', source: '阅读器', sourceType: 'primary', message: '发送查询指令 (Q=4, Sel=0, Session=S0)' },
  { time: '14:20:01', source: 'TAG_482', sourceType: 'secondary', message: '插槽计数设置为 0。正在发送 RN16。' },
  { time: '14:20:01', source: 'TAG_911', sourceType: 'error', message: '插槽计数设置为 0。正在发送 RN16。' },
  { time: '14:20:01', source: '阅读器', sourceType: 'primary', type: 'error', message: '检测到冲突 (插槽 0)。重试盘存轮次。' },
  { time: '14:20:02', source: 'TAG_032', sourceType: 'outline', message: '插槽计数设置为 7。计数器递增。' },
  { time: '14:20:02', source: '阅读器', sourceType: 'primary', message: '广播 QueryRep 指令。' },
  { time: '14:20:03', source: 'TAG_482', sourceType: 'secondary', type: 'highlight', message: '收到确认 (ACK)。传输 EPC 数据: 300833B2DDD...' },
];
</script>

<style lang="scss" scoped>
.console {
  height: 256px;
  background-color: rgba(11, 19, 38, 0.5);
  backdrop-filter: blur(12px);
  border-top: 1px solid rgba(67, 70, 86, 0.1);
  display: flex;
  flex-direction: column;

  &__controls {
    height: 64px;
    background-color: rgba(23, 31, 51, 0.5);
    display: flex;
    align-items: center;
    padding: 0 var(--spacing-lg);
    gap: var(--spacing-xl);
  }

  &__playback {
    display: flex;
    gap: var(--spacing-sm);
  }

  &__btn {
    width: 40px;
    height: 40px;
    background-color: var(--surface-container-high);
    border-radius: var(--radius-md);
    color: var(--on-surface-variant);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;

    &:hover {
      color: var(--on-surface);
      background-color: var(--surface-container-highest);
    }

    &--primary {
      background-color: var(--primary-container);
      color: var(--on-primary);
      box-shadow: 0 0 20px rgba(46, 91, 255, 0.2);
    }

    &--danger {
      &:hover { color: var(--error); }
    }
  }

  &__divider {
    width: 1px;
    height: 32px;
    background-color: rgba(67, 70, 86, 0.2);
  }

  &__params {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
    max-width: 600px;
  }

  &__label {
    font-size: 11px;
    font-weight: 700;
    color: var(--outline);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    white-space: nowrap;
  }

  &__slider-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding-top: 8px;
  }

  &__slider {
    width: 100%;
    height: 4px;
    appearance: none;
    background: var(--surface-container-highest);
    border-radius: var(--radius-full);
    outline: none;

    &::-webkit-slider-thumb {
      appearance: none;
      width: 14px;
      height: 14px;
      background: var(--primary);
      border-radius: var(--radius-full);
      cursor: pointer;
      box-shadow: 0 0 10px rgba(46, 91, 255, 0.4);
    }
  }

  &__slider-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    font-size: 9px;
    color: var(--outline);
    font-family: 'Space Grotesk', sans-serif;
  }

  &__badge {
    background-color: rgba(46, 91, 255, 0.1);
    color: var(--primary);
    font-size: 11px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: var(--radius-sm);
  }

  &__signal {
    margin-left: auto;
  }

  &__signal-info {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }

  &__signal-bars {
    display: flex;
    gap: 2px;
  }

  &__signal-bar {
    width: 12px;
    height: 4px;
    background-color: rgba(184, 195, 255, 0.1);
    border-radius: var(--radius-full);
    
    &--active {
      background-color: var(--primary);
    }
  }

  &__logs {
    flex: 1;
    padding: var(--spacing-md) var(--spacing-lg);
    overflow-y: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__log-entry {
    display: flex;
    gap: var(--spacing-lg);
    opacity: 0.6;
  }

  &__log-time { color: var(--outline); font-family: 'Space Grotesk', sans-serif; width: 80px; }

  &__source {
    font-weight: 700;
    width: 100px;
    &--primary { color: var(--primary); }
    &--secondary { color: var(--secondary); }
    &--error { color: var(--error); }
    &--outline { color: var(--outline); }
  }

  &__log-msg {
    color: var(--outline);
    &--error { color: var(--error); }
    &--highlight { color: var(--on-surface); }
  }
}
</style>
