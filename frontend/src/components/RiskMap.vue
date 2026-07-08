<template>
  <div class="risk-map">
    <v-chart :option="option" autoresize style="height: 400px;" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const props = defineProps({
  data: { type: Array, required: true, default: () => [] },
})

const option = computed(() => {
  const names = props.data.map(d => d.name)
  return {
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
      data: names.length > 0 ? names : ['暂无数据'],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '高风险',
        type: 'bar',
        stack: 'total',
        itemStyle: { color: '#f56c6c' },
        data: names.length > 0 ? props.data.map(d => Number(d.high)) : [0],
      },
      {
        name: '中风险',
        type: 'bar',
        stack: 'total',
        itemStyle: { color: '#e6a23c' },
        data: names.length > 0 ? props.data.map(d => Number(d.medium)) : [0],
      },
      {
        name: '低风险',
        type: 'bar',
        stack: 'total',
        itemStyle: { color: '#909399' },
        data: names.length > 0 ? props.data.map(d => Number(d.low)) : [0],
      },
    ],
  }
})
</script>
