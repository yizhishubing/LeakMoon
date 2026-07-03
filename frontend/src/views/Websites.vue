<template>
  <div style="padding: 20px;">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>巡检网站管理</span>
          <el-button type="primary" @click="showDialog = true">添加网站</el-button>
        </div>
      </template>

      <el-table :data="websites" stripe>
        <el-table-column prop="name" label="网站名称" width="150" />
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
        <el-table-column prop="depth" label="爬取深度" width="100" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="runCrawl(row.id)">立即爬取</el-button>
            <el-button size="small" type="danger" @click="deleteSite(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="websites.length === 0" description="暂无巡检网站，请点击添加网站" />
    </el-card>

    <el-dialog v-model="showDialog" title="添加网站" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="网站名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="form.url" placeholder="https://example.edu.cn" />
        </el-form-item>
        <el-form-item label="爬取深度">
          <el-input-number v-model="form.depth" :min="0" :max="5" />
        </el-form-item>
        <el-form-item label="最大页数">
          <el-input-number v-model="form.maxPages" :min="10" :max="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWebsite">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const websites = ref([])
const showDialog = ref(false)
const form = ref({ name: '', url: '', depth: 2, maxPages: 100 })

onMounted(fetchWebsites)

async function fetchWebsites() {
  try {
    const res = await fetch('http://localhost:8000/api/websites/')
    if (res.ok) websites.value = await res.json()
  } catch {
    ElMessage.warning('后端服务未连接，显示空列表')
  }
}

async function saveWebsite() {
  try {
    const res = await fetch('http://localhost:8000/api/websites/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    if (res.ok) {
      ElMessage.success('添加成功')
      showDialog.value = false
      form.value = { name: '', url: '', depth: 2, maxPages: 100 }
      await fetchWebsites()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '添加失败')
    }
  } catch {
    ElMessage.error('后端服务未连接')
  }
}

async function runCrawl(id) {
  try {
    const res = await fetch(`http://localhost:8000/api/crawlers/run/${id}`, { method: 'POST' })
    const data = await res.json()
    ElMessage.info(data.message || `爬取触发成功`)
  } catch {
    ElMessage.error('后端服务未连接')
  }
}

async function deleteSite(id) {
  try {
    await fetch(`http://localhost:8000/api/websites/${id}`, { method: 'DELETE' })
    ElMessage.success('删除成功')
    await fetchWebsites()
  } catch {
    ElMessage.error('删除失败')
  }
}
</script>
