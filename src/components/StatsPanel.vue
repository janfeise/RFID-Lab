<template>
  <aside class="stats">
    <h3 class="stats__title">Tags 清单</h3>
    <div class="stats__table-container">
      <table class="stats__table">
        <thead>
          <tr>
            <th>id</th>
            <th>EPC</th>
            <th class="stats__text-center">slot counter</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, i) in props.tags" :key="item.id">
            <td>{{ i + 1 }}</td>
            <td :class="[`stats__id`]">{{ item.EPC }}</td>
            <td
              class="stats__text-center num-font"
              :class="{ 'stats__text--zero': item.slotCounter === 0 }"
            >
              {{ item.slotCounter !== null ? item.slotCounter : "null" }}
            </td>
            <td>
              <span :class="['stats__badge', `stats__badge--${item.status}`]">
                {{ item.status.toUpperCase() }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="stats__epc">
      <h3 class="stats__title">EPC 数据存储</h3>
      <div class="stats__epc-content mono-font">
        <div class="stats__epc-row">
          <span class="stats__epc-label"># 读取数据 01:</span>
          <span class="stats__epc-value">300833B2DDD9014000000000</span>
        </div>
        <div class="stats__epc-row stats__epc-row--empty">
          <span class="stats__epc-label"># 读取数据 02:</span>
          <span class="stats__epc-value">空（发生冲突）</span>
        </div>
        <div class="stats__epc-row stats__epc-row--empty">
          <span class="stats__epc-label"># 读取数据 03:</span>
          <span class="stats__epc-value">等待中...</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
});

watch(
  () => props.tags,
  (newTags) => {
    console.log("StatsPanel - Tags Updated:", newTags);
  },
  { deep: true },
);
</script>

<style lang="scss" scoped>
.stats {
  width: 350px;
  background-color: var(--surface-container-low);
  padding: var(--spacing-lg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);

  &__title {
    font-size: 12px;
    font-weight: 700;
    color: var(--outline);
    // text-transform: uppercase;
    letter-spacing: 0.1em;
    padding-left: var(--spacing-xs);
    margin-bottom: var(--spacing-md);
  }

  &__table-container {
    background-color: var(--surface-container-lowest);
    border-radius: var(--radius-sm);
    max-height: 400px;
    overflow-y: auto;

    // 隐藏默认滚动条，使用自定义滚动条
    &::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    &::-webkit-scrollbar-thumb {
      background-color: rgba(181, 183, 192, 0.2);
      border-radius: var(--radius-sm);
    }

    &::-webkit-scrollbar-thumb:hover {
      background-color: rgba(175, 179, 201, 0.4);
    }
  }

  &__table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;

    th {
      background-color: var(--surface-container-high);
      padding: var(--spacing-sm) var(--spacing-md);
      color: var(--outline);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 10px;
      text-align: left;
    }

    td {
      padding: var(--spacing-md);
      border-bottom: 1px solid rgba(67, 70, 86, 0.05);
    }
  }

  &__text--zero {
    color: var(--error);
    font-weight: 700;
  }

  &__text-center {
    text-align: center;
  }

  &__id {
    font-size: 8px;

    &--secondary {
      color: var(--secondary);
    }
    &--error {
      color: var(--error);
    }
    &--normal {
      color: var(--on-surface);
    }
  }

  &__badge {
    padding: 2px 6px;
    border-radius: var(--radius-xs);
    font-size: 9px;
    font-weight: 700;

    &--success {
      background-color: rgba(90, 218, 206, 0.1);
      color: var(--secondary);
    }
    &--error {
      background-color: rgba(255, 180, 171, 0.1);
      color: var(--error);
    }
    &--idle {
      background-color: rgba(67, 70, 86, 0.2);
      color: var(--outline);
    }

    &--ready {
      background-color: rgba(46, 91, 255, 0.1);
      color: var(--primary);
    }
  }
  &__epc {
    margin-top: var(--spacing-lg);
  }

  &__epc-content {
    background-color: var(--surface-container-lowest);
    border: 1px solid rgba(67, 70, 86, 0.15);
    border-radius: var(--radius-sm);
    padding: var(--spacing-md);
    font-size: 10px;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  &__epc-row {
    display: flex;
    gap: var(--spacing-sm);

    &--empty {
      opacity: 0.4;
    }
  }

  &__epc-label {
    font-family: "Noto Sans SC", sans-serif;
    font-weight: 700;
  }

  &__epc-value {
    color: var(--secondary);
  }
}
</style>
