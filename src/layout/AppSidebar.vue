<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <button
      class="sidebar__collapse-btn"
      type="button"
      :aria-label="collapsed ? '展开侧边栏' : '折叠侧边栏'"
      @click="emit('toggle-collapse')"
    >
      <span class="material-symbols-outlined">
        {{ collapsed ? "chevron_right" : "chevron_left" }}
      </span>
    </button>

    <div class="sidebar__user">
      <div class="sidebar__user-avatar">
        <span class="material-symbols-outlined">person</span>
      </div>
      <div class="sidebar__user-info" v-show="!collapsed">
        <div class="sidebar__username">Tilex</div>
        <div class="sidebar__status">状态：在线</div>
      </div>
    </div>

    <nav class="sidebar__nav">
      <a
        v-for="link in navLinks"
        :key="link.id"
        href="#"
        class="sidebar__nav-link"
        :class="{ 'sidebar__nav-link--active': link.active }"
      >
        <span class="material-symbols-outlined">{{ link.icon }}</span>
        <span v-show="!collapsed">{{ link.label }}</span>
      </a>
    </nav>

    <div class="sidebar__footer">
      <!-- <button class="sidebar__action-btn" @click="$emit('start')">
        开始传输
      </button> -->
    </div>
  </aside>
</template>

<script setup>
defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["start", "toggle-collapse"]);

const navLinks = [
  { id: 1, label: "lab 1", icon: "radar", active: true },
  // { id: 2, label: '阅读器配置', icon: 'settings_input_component', active: false },
  // { id: 3, label: '标签盘存', icon: 'style', active: false },
  // { id: 4, label: '逻辑流程', icon: 'account_tree', active: false },
  // { id: 5, label: '统计分析', icon: 'query_stats', active: false },
];
</script>

<style lang="scss" scoped>
.sidebar {
  width: 256px;
  background-color: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(16px);
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  padding-top: 80px;
  z-index: var(--z-nav);
  display: flex;
  flex-direction: column;
  transition: width 0.28s ease;

  &--collapsed {
    width: 72px;

    .sidebar__user {
      justify-content: center;
      padding-left: 0;
      padding-right: 0;
    }

    .sidebar__nav-link {
      justify-content: center;
      padding-left: 0;
      padding-right: 0;
    }

    .sidebar__nav-link--active {
      border-right-width: 3px;
    }

    .sidebar__footer {
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
    }
  }

  &__collapse-btn {
    position: absolute;
    top: 88px;
    right: -14px;
    width: 28px;
    height: 28px;
    border-radius: var(--radius-full);
    background-color: rgba(15, 23, 42, 0.96);
    border: 1px solid rgba(184, 195, 255, 0.35);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.25s ease;

    &:hover {
      transform: scale(1.06);
      box-shadow: 0 0 12px rgba(46, 91, 255, 0.35);
    }

    span {
      font-size: 20px;
    }
  }

  &__user {
    padding: 0 var(--spacing-lg) var(--spacing-xl);
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  &__user-avatar {
    width: 40px;
    height: 40px;
    background-color: var(--surface-container-highest);
    border: 1px solid rgba(184, 195, 255, 0.2);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--primary);
  }

  &__username {
    font-size: 0.875rem;
    font-weight: 900;
    color: var(--primary);
  }

  &__status {
    font-size: 10px;
    font-weight: 700;
    color: var(--secondary);
    letter-spacing: 0.1em;
  }

  &__nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__nav-link {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-lg);
    color: var(--outline);
    font-size: 0.875rem;
    font-weight: 700;
    transition: all 0.3s;
    white-space: nowrap;
    overflow: hidden;

    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
      color: var(--on-surface);
    }

    &--active {
      background-color: rgba(46, 91, 255, 0.1);
      color: var(--primary);
      border-right: 4px solid var(--primary-container);
    }
  }

  &__footer {
    padding: var(--spacing-lg);
  }

  &__action-btn {
    width: 100%;
    background-color: var(--primary-container);
    color: var(--on-primary);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    box-shadow: 0 0 15px rgba(46, 91, 255, 0.3);
    transition: all 0.3s;

    &:hover {
      filter: brightness(1.2);
      transform: translateY(-2px);
    }
  }
}
</style>
