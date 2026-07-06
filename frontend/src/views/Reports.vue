<template>
  <div style="padding: 20px;">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>报表中心</span>
          <el-button type="primary" size="small" @click="showDialog = true">生成报表</el-button>
        </div>
      </template>

      <el-table :data="reports" stripe>
        <el-table-column prop="title" label="报表标题" show-overflow-tooltip />
        <el-table-column prop="report_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.report_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'generated' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="downloadReport(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="reports.length === 0" description="暂无报表，请点击生成报表" />
    </el-card>

    <!-- 生成报表对话框 -->
    <el-dialog v-model="showDialog" title="生成报表" width="400px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报表标题">
          <el-input v-model="form.title" placeholder="请输入报表标题" />
        </el-form-item>
        <el-form-item label="报表类型">
          <el-select v-model="form.type" style="width: 100%;">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="generateReport">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const reports = ref([])
const showDialog = ref(false)
const form = ref({ title: '', type: 'daily' })

async function generateReport() {
  // TODO: 调用后端报表生成 API
  ElMessage.success('报表生成中...')
  showDialog.value = false
}

function downloadReport(row) {
  // TODO: 下载报表文件
  ElMessage.info('下载功能开发中')
}
</script>
