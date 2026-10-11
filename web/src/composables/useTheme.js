import { ref, watch } from 'vue'

const STORAGE_KEY = 'lifelog-theme'
const DARK = 'dark'
const LIGHT = 'light'

function readInitial () {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === LIGHT || saved === DARK) return saved
  // 没有历史选择时跟随系统偏好。
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? LIGHT : DARK
}

function apply (value) {
  document.documentElement.dataset.theme = value
}

const theme = ref(readInitial())
apply(theme.value)

watch(theme, (value) => {
  apply(value)
  localStorage.setItem(STORAGE_KEY, value)
})

export function useTheme () {
  function toggle () {
    const root = document.documentElement
    // 只在这一次切换期间开启过渡，避免首屏渲染时也走动画。
    root.classList.add('theme-transition')
    window.setTimeout(() => root.classList.remove('theme-transition'), 260)
    theme.value = theme.value === DARK ? LIGHT : DARK
  }

  const label = () => (theme.value === DARK ? '日间模式' : '夜间模式')
  const icon = () => (theme.value === DARK ? '☀️' : '🌙')

  return { theme, toggle, label, icon }
}
