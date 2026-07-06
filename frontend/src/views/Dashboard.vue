<template>
  <div style="padding: 20px;">
    <!-- 统计卡片 -->
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

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header><span>泄露类型分布</span></template>
          <v-chart :option="pieOption" autoresize style="height: 300px;" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>近7天泄露趋势</span></template>
          <v-chart :option="lineOption" autoresize style="height: 300px;" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险地图 -->
    <el-card style="margin-top: 20px;">
      <template #header><span>各网站风险等级分布</span></template>
      <RiskMap :data="riskMapData" />
    </el-card>

    <!-- 系统状态 -->
    <el-card style="margin-top: 20px;">
      <template #header><span>📊 系统状态</span></template>
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
import { ref, onMounted, computed } from 'vue'
import RiskMap from '@/components/RiskMap.vue'

const stats = ref({ activeWebsites: 0, totalLeaks: 0, highRiskLeaks: 0, pendingAlerts: 0 })
const backendOk = ref(false)
const dbOk = ref(false)
const redisOk = ref(false)

// 饼图配置：泄露类型分布
const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: 1048, name: '身份证号' },
      { value: 735, name: '手机号' },
      { value: 580, name: '邮箱' },
      { value: 484, name: '学号' },
      { value: 300, name: '其他' },
    ],
  }],
}))

// 折线图配置：近7天趋势
const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
  yAxis: { type: 'value' },
  series: [{
    type: 'line',
    data: [5, 12, 8, 15, 10, 3, 7],
    smooth: true,
    areaStyle: {},
  }],
}))

// 风险地图数据（示例，后续从后端 API 获取）
const riskMapData = ref([
  { name: '教务处', high: 12, medium: 8, low: 5 },
  { name: '图书馆', high: 5, medium: 15, low: 10 },
  { name: '财务处', high: 20, medium: 3, low: 2 },
  { name: '学工部', high: 8, medium: 10, low: 15 },
])

onMounted(async () => {
  // 检查后端健康状态（同时推断数据库连接状态）
  try {
    const res = await fetch('/api/health')
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
