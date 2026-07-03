<template>
  <div style="padding: 20px;">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>检测规则管理</span>
          <el-button type="primary" size="small" @click="reloadRules">重新加载规则</el-button>
        </div>
      </template>
      <el-table :data="rules" stripe>
        <el-table-column prop="name" label="规则名称" width="200" />
        <el-table-column prop="data_type" label="类型" width="120" />
        <el-table-column prop="severity" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'" size="small">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const rules = ref([])

onMounted(fetchRules)

async function fetchRules() {
  try {
    const res = await fetch('http://localhost:8000/api/rules/')
    if (res.ok) rules.value = await res.json()
  } catch {
    ElMessage.warning('后端服务未连接')
  }
}

async function reloadRules() {
  try {
    await fetch('http://localhost:8000/api/rules/reload', { method: 'POST' })
    ElMessage.success('规则已重新加载')
    await fetchRules()
  } catch {
    ElMessage.error('规则重载失败')
  }
}
</script>
