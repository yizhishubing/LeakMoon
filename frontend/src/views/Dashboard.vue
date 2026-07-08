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
import { ref, onMounted, computed, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import RiskMap from '@/components/RiskMap.vue'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  PieChart,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const stats = ref({ activeWebsites: 0, totalLeaks: 0, highRiskLeaks: 0, pendingAlerts: 0 })
const backendOk = ref(false)
const dbOk = ref(false)
const redisOk = ref(false)

// 图表数据
const pieData = ref([])
const trendData = ref({ dates: [], counts: [] })
const riskMapData = ref([])

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: pieData.value.length > 0 ? pieData.value.map(d => ({ name: d.name, value: d.value })) : [
      { value: 0, name: '暂无数据' },
    ],
  }],
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: trendData.value.dates.length > 0 ? trendData.value.dates : ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
  yAxis: { type: 'value' },
  series: [{
    type: 'line',
    data: trendData.value.counts.length > 0 ? trendData.value.counts : [0, 0, 0, 0, 0, 0, 0],
    smooth: true,
    areaStyle: {},
  }],
}))

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    if (res.ok) {
      backendOk.value = true
      dbOk.value = true
      redisOk.value = true
      await loadDashboardData()
    }
  } catch {
    backendOk.value = false
    dbOk.value = false
    redisOk.value = false
  }
})

async function loadDashboardData() {
  try {
    const statsRes = await fetch('/api/dashboard/stats')
    if (statsRes.ok) stats.value = await statsRes.json()

    const typesRes = await fetch('/api/dashboard/leak-types')
    if (typesRes.ok) pieData.value = await typesRes.json()

    const trendRes = await fetch('/api/dashboard/leak-trend?days=7')
    if (trendRes.ok) trendData.value = await trendRes.json()

    const riskRes = await fetch('/api/dashboard/risk-map')
    if (riskRes.ok) {
      const riskData = await riskRes.json()
      riskMapData.value = riskData.map(r => ({
        name: r.name,
        high: Number(r.high),
        medium: Number(r.medium),
        low: Number(r.low),
      }))
    }
  } catch (e) {
    console.error('加载仪表盘数据失败:', e)
  }
}
</script>
