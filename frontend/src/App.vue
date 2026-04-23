<template>
  <router-view />
</template>

<script setup lang="ts">
// 现在 token 永不过期（100 年），不再需要定期检查
// 用户只需在主动退出登录时才会失去认证状态
</script>

