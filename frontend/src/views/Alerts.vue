<template>
  <div style="padding: 20px;">
    <el-card>
      <template #header>
        <div style="display: flex; gap: 10px; align-items: center;">
          <span>告警中心</span>
          <el-select v-model="statusFilter" placeholder="告警状态" clearable style="width: 150px;">
            <el-option label="待发送" value="pending" />
            <el-option label="已发送" value="sent" />
            <el-option label="已确认" value="acknowledged" />
            <el-option label="已处理" value="resolved" />
          </el-select>
        </div>
      </template>

      <el-table :data="filteredAlerts" stripe>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="channel" label="渠道" width="80" />
        <el-table-column prop="recipient" label="接收者" width="200" show-overflow-tooltip />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="sent_at" label="发送时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'acknowledged' && row.status !== 'resolved'" size="small" type="primary" @click="acknowledgeAlert(row)">确认</el-button>
            <el-button v-if="row.status === 'acknowledged'" size="small" type="success" @click="resolveAlert(row)">处理</el-button>
            <el-button v-if="row.error_message" size="small" type="info" @click="viewError(row)">错误</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 错误详情对话框 -->
    <el-dialog v-model="errorVisible" title="发送失败详情" width="500px">
      <el-alert :title="currentAlert?.error_message" type="error" :closable="false" show-icon />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { alertApi } from '@/api'

const alerts = ref([])
const statusFilter = ref('')
const errorVisible = ref(false)
const currentAlert = ref(null)

// 前端过滤：按状态筛选
const filteredAlerts = computed(() => {
  if (!statusFilter.value) return alerts.value
  return alerts.value.filter(a => a.status === statusFilter.value)
})

// 状态标签样式
function statusTagType(status) {
  const map = { pending: 'warning', sent: 'success', acknowledged: 'primary', resolved: 'info' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { pending: '待发送', sent: '已发送', acknowledged: '已确认', resolved: '已处理' }
  return map[status] || status
}

onMounted(fetchAlerts)

async function fetchAlerts() {
  try {
    alerts.value = await alertApi.list()
  } catch {
    console.error('获取告警列表失败')
  }
}

async function acknowledgeAlert(row) {
  await alertApi.acknowledge(row.id)
  ElMessage.success('告警已确认')
  await fetchAlerts()
}

async function resolveAlert(row) {
  await alertApi.resolve(row.id)
  ElMessage.success('告警已处理')
  await fetchAlerts()
}

function viewError(row) {
  currentAlert.value = row
  errorVisible.value = true
}
</script>
