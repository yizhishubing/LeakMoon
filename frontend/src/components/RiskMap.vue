<template>
  <div class="risk-map">
    <v-chart :option="option" autoresize style="height: 400px;" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'

// 注册 ECharts 组件（必须在 v-chart 使用前调用）
use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const props = defineProps({
  // 每项: { name: string, high: number, medium: number, low: number }
  data: { type: Array, required: true, default: () => [] },
})

// 堆叠柱状图配置：各网站风险等级分布
const option = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
  },
  legend: { data: ['高风险', '中风险', '低风险'] },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    data: props.data.map(d => d.name),
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '高风险',
      type: 'bar',
      stack: 'total',
      itemStyle: { color: '#f56c6c' },
      data: props.data.map(d => d.high),
    },
    {
      name: '中风险',
      type: 'bar',
      stack: 'total',
      itemStyle: { color: '#e6a23c' },
      data: props.data.map(d => d.medium),
    },
    {
      name: '低风险',
      type: 'bar',
      stack: 'total',
      itemStyle: { color: '#909399' },
      data: props.data.map(d => d.low),
    },
  ],
}))
</script>
