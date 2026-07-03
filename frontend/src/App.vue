<template>
  <el-container style="height: 100vh;">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background-color: #304156;">
      <div style="padding: 20px; color: #fff; text-align: center; font-size: 16px; font-weight: bold;">
        敏感信息巡检平台
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>风险仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/websites">
          <el-icon><Monitor /></el-icon>
          <span>巡检管理</span>
        </el-menu-item>
        <el-menu-item index="/leaks">
          <el-icon><Warning /></el-icon>
          <span>泄露记录</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>告警中心</span>
        </el-menu-item>
        <el-menu-item index="/rules">
          <el-icon><Setting /></el-icon>
          <span>规则管理</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>报表中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-main style="background-color: #f0f2f5;">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
// Element Plus 图标已在 main.js 中全局注册
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.el-menu {
  border-right: none !important;
}
</style>
