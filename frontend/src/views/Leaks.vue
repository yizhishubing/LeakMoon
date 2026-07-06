<template>
  <div style="padding: 20px;">
    <el-card>
      <template #header>
        <div style="display: flex; gap: 10px; align-items: center;">
          <span>泄露记录</span>
          <el-input v-model="searchQuery" placeholder="搜索URL或类型" style="width: 250px;" clearable />
          <el-select v-model="severityFilter" placeholder="严重程度" clearable style="width: 150px;">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </div>
      </template>

      <el-table :data="filteredLeaks" stripe>
        <el-table-column prop="severity" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'" size="small">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="data_type" label="类型" width="120" />
        <el-table-column prop="rule_name" label="命中规则" width="200" />
        <el-table-column prop="matched_text" label="匹配内容" width="150" />
        <el-table-column prop="source_url" label="来源URL" show-overflow-tooltip />
        <el-table-column prop="detected_at" label="检测时间" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_verified === 1 ? 'success' : row.is_verified === 2 ? 'info' : 'warning'">
              {{ row.is_verified === 0 ? '待确认' : row.is_verified === 1 ? '已确认' : '误报' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="confirmLeak(row)">确认</el-button>
            <el-button size="small" type="info" @click="markFalsePositive(row)">误报</el-button>
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="泄露详情" width="600px">
      <el-descriptions :column="1" border v-if="currentLeak">
        <el-descriptions-item label="来源URL">{{ currentLeak.source_url }}</el-descriptions-item>
        <el-descriptions-item label="泄露类型">{{ currentLeak.data_type }}</el-descriptions-item>
        <el-descriptions-item label="匹配内容">{{ currentLeak.matched_text }}</el-descriptions-item>
        <el-descriptions-item label="上下文前缀">{{ currentLeak.context_before }}</el-descriptions-item>
        <el-descriptions-item label="上下文后缀">{{ currentLeak.context_after }}</el-descriptions-item>
        <el-descriptions-item label="检测时间">{{ currentLeak.detected_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { leakApi } from '@/api'

const leaks = ref([])
const searchQuery = ref('')
const severityFilter = ref('')
const detailVisible = ref(false)
const currentLeak = ref(null)

// 前端过滤：搜索URL或类型 + 严重程度筛选
const filteredLeaks = computed(() => {
  let result = leaks.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(l => l.source_url.toLowerCase().includes(q) || l.data_type.includes(q))
  }
  if (severityFilter.value) {
    result = result.filter(l => l.severity === severityFilter.value)
  }
  return result
})

onMounted(fetchLeaks)

async function fetchLeaks() {
  try {
    leaks.value = await leakApi.list()
  } catch {
    console.error('获取泄露记录失败')
  }
}

async function confirmLeak(row) {
  await leakApi.verify(row.id, { is_verified: 1 })
  ElMessage.success('已确认')
  await fetchLeaks()
}

async function markFalsePositive(row) {
  await leakApi.verify(row.id, { is_verified: 2, note: '误报' })
  ElMessage.info('已标记为误报')
  await fetchLeaks()
}

function viewDetail(row) {
  currentLeak.value = row
  detailVisible.value = true
}
</script>
