<template>
  <div v-if="visible" class="modal-overlay">
    <div class="modal">
      <header class="modal__header">
        <h2 class="modal__title">
          <span class="material-symbols-outlined">settings_suggest</span>
          Lab 1 初始化配置
        </h2>
      </header>

      <div class="modal__content">
        <!-- Reader Count -->
        <div class="modal__field">
          <label class="modal__label">阅读器数量</label>
          <div class="modal__input-static">
            <span class="material-symbols-outlined">sensors</span>
            <span class="num-font font-bold">1</span>
          </div>
        </div>

        <!-- Q Value -->
        <div class="modal__field">
          <div class="modal__field-header">
            <label class="modal__label">Q 值设定</label>
            <span class="modal__value-badge">{{ qValue }}</span>
          </div>
          <div class="modal__slider-container">
            <input
              type="range"
              min="0"
              max="15"
              v-model="qValue"
              class="modal__slider"
            />
            <div class="modal__slider-labels">
              <span>0</span>
              <span>15</span>
            </div>
          </div>
        </div>

        <!-- Tag Count -->
        <div class="modal__field">
          <label class="modal__label">标签数量</label>
          <div class="modal__input-wrapper">
            <input
              type="number"
              v-model="tagCount"
              class="modal__input"
              placeholder="输入模拟标签总数..."
            />
            <span class="material-symbols-outlined modal__input-icon"
              >style</span
            >
          </div>
          <p class="modal__help-text">建议范围：1 - 256</p>
        </div>
      </div>

      <footer class="modal__footer">
        <button
          class="modal__submit-btn"
          @click="$emit('confirm', { qValue, tagCount })"
        >
          <span class="material-symbols-outlined">play_circle</span>
          开始仿真
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  visible: Boolean,
});

defineEmits(["confirm"]);

const qValue = ref(4);
const tagCount = ref(10);
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  background-color: rgba(11, 19, 38, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  width: 100%;
  max-width: 440px;
  background-color: var(--surface-container-high);
  border: 1px solid rgba(67, 70, 86, 0.3);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  animation: modal-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

  &__header {
    background-color: rgba(46, 91, 255, 0.1);
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid rgba(67, 70, 86, 0.2);
  }

  &__title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--primary);
    letter-spacing: 0.1em;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);

    span {
      font-size: 1.25rem;
    }
  }

  &__content {
    padding: var(--spacing-lg);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  &__label {
    font-size: 10px;
    font-weight: 700;
    color: var(--outline);
    text-transform: uppercase;
    letter-spacing: 0.15em;
  }

  &__input-static {
    display: flex;
    align-items: center;
    cursor: not-allowed;
    gap: var(--spacing-md);
    background-color: var(--surface-container-low);
    padding: 12px var(--spacing-md);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(67, 70, 86, 0.1);
    color: rgba(218, 226, 253, 0.5);

    span:first-child {
      font-size: 14px;
    }
  }

  &__input-tag {
    margin-left: auto;
    font-size: 10px;
    background-color: var(--surface-container-highest);
    padding: 2px 8px;
    border-radius: var(--radius-sm);
  }

  &__field-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__value-badge {
    background-color: rgba(46, 91, 255, 0.1);
    color: var(--primary);
    font-weight: 700;
    font-family: "Space Grotesk", sans-serif;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
  }

  &__slider-container {
    padding-top: 8px;
  }

  &__slider {
    width: 100%;
    height: 6px;
    appearance: none;
    background: var(--surface-container-highest);
    border-radius: var(--radius-full);
    outline: none;

    &::-webkit-slider-thumb {
      appearance: none;
      width: 18px;
      height: 18px;
      background: var(--primary);
      border-radius: var(--radius-full);
      cursor: pointer;
      box-shadow: 0 0 15px rgba(46, 91, 255, 0.4);
    }
  }

  &__slider-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    font-size: 10px;
    color: var(--outline);
    font-family: "Space Grotesk", sans-serif;
  }

  &__input-wrapper {
    position: relative;
  }

  &__input {
    width: 100%;
    background-color: var(--surface-container-low);
    border: 1px solid rgba(67, 70, 86, 0.2);
    border-radius: var(--radius-sm);
    padding: 12px var(--spacing-md);
    color: var(--on-surface);
    font-family: "Space Grotesk", sans-serif;
    outline: none;
    transition: all 0.3s;

    &:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 1px var(--primary);
    }
  }

  &__input-icon {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(142, 144, 162, 0.4);
    font-size: 18px;
  }

  &__help-text {
    font-size: 10px;
    color: rgba(142, 144, 162, 0.6);
    font-style: italic;
  }

  &__footer {
    padding: var(--spacing-lg);
    padding-top: 0;
  }

  &__submit-btn {
    width: 100%;
    background-color: var(--primary);
    color: var(--on-primary);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    font-weight: 900;
    letter-spacing: 0.15em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    box-shadow: 0 4px 20px rgba(46, 91, 255, 0.4);
    transition: all 0.3s;

    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
    &:active {
      transform: translateY(1px);
    }

    span {
      font-size: 20px;
    }
  }
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
