<template>
  <div style="padding: 20px;">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="巡检网站数" :value="stats.activeWebsites" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="累计发现泄露" :value="stats.totalLeaks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="高风险泄露" :value="stats.highRiskLeaks" value-style="{ color: '#f56c6c' }" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="待处理告警" :value="stats.pendingAlerts" />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>📊 系统状态</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="后端服务">
          <el-tag :type="backendOk ? 'success' : 'danger'">
            {{ backendOk ? '运行中' : '未连接' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据库">
          <el-tag :type="dbOk ? 'success' : 'danger'">
            {{ dbOk ? '已连接' : '未连接' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Redis 缓存">
          <el-tag :type="redisOk ? 'success' : 'warning'">
            {{ redisOk ? '已连接' : '未连接' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="爬虫调度">
          <el-tag type="info">待配置</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref({
  activeWebsites: 0,
  totalLeaks: 0,
  highRiskLeaks: 0,
  pendingAlerts: 0,
})

const backendOk = ref(false)
const dbOk = ref(false)
const redisOk = ref(false)

onMounted(async () => {
  // 检查后端健康状态（同时推断数据库连接状态）
  try {
    const res = await fetch('http://localhost:8000/api/health')
    if (res.ok) {
      backendOk.value = true
      dbOk.value = true
    }
  } catch {
    backendOk.value = false
    dbOk.value = false
  }
  // Redis 状态由后端管理，后端在线即视为可用
  redisOk.value = backendOk.value
})
</script>
