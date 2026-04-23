<template>
  <header class="header">
    <div class="header__left">
      <h1 class="header__logo">RFID 实验集</h1>
      <nav class="header__nav">
        <a
          v-for="item in navItems"
          :key="item.id"
          href="#"
          class="header__nav-item"
          :class="{ 'header__nav-item--active': item.active }"
        >
          {{ item.label }}
        </a>
      </nav>
    </div>
    <div class="header__right">
      <button class="header__action-btn">
        <span class="material-symbols-outlined">terminal</span>
      </button>
      <button class="header__action-btn">
        <span class="material-symbols-outlined">sensors</span>
      </button>
      <button class="header__action-btn">
        <span class="material-symbols-outlined">settings</span>
      </button>
    </div>
  </header>
</template>

<script setup>
const navItems = [
  // { id: 1, label: "lab 1", active: true },
  // { id: 2, label: "深度分析", active: false },
  // { id: 3, label: "历史记录", active: false },
];
</script>

<style lang="scss" scoped>
.header {
  height: 64px;
  background-color: rgba(11, 19, 38, 0.8);
  backdrop-filter: blur(20px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--spacing-lg);
  position: fixed;
  top: 0;
  width: 100%;
  z-index: var(--z-app-bar);
  box-shadow: 0 4px 20px rgba(46, 91, 255, 0.1);

  &__left {
    display: flex;
    align-items: center;
    gap: var(--spacing-xl);
  }

  &__logo {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: var(--primary-container);
    font-family: "Noto Sans SC", sans-serif;
  }

  &__nav {
    display: flex;
    gap: var(--spacing-lg);
  }

  &__nav-item {
    color: var(--outline);
    font-size: 0.875rem;
    font-weight: 700;
    padding-bottom: var(--spacing-xs);
    transition: color 0.3s;

    &:hover {
      color: var(--on-surface);
    }

    &--active {
      color: var(--primary);
      border-bottom: 2px solid var(--primary-container);
    }
  }

  &__right {
    display: flex;
    gap: var(--spacing-md);
  }

  &__action-btn {
    padding: var(--spacing-sm);
    color: var(--outline);
    border-radius: var(--radius-sm);
    transition: all 0.3s;

    &:hover {
      background-color: rgba(46, 91, 255, 0.1);
      color: var(--primary);
    }
  }
}
</style>
