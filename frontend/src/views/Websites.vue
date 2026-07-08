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
            <el-button size="small" type="primary" @click="runCrawl(row.id)" :loading="row.loading">立即爬取</el-button>
            <el-button size="small" type="danger" @click="deleteSite(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="websites.length === 0" description="暂无巡检网站，请点击添加网站" />
    </el-card>

    <!-- 添加网站对话框 -->
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
      <el-divider>爬取深度说明</el-divider>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="深度 0">仅爬取首页，不进入任何子页面</el-descriptions-item>
        <el-descriptions-item label="深度 1">爬取首页 + 首页上的所有直接链接页面</el-descriptions-item>
        <el-descriptions-item label="深度 2">在深度1基础上，继续爬取第二层链接页面</el-descriptions-item>
        <el-descriptions-item label="深度 3">继续向下扩展至第三层链接</el-descriptions-item>
        <el-descriptions-item label="深度 4">继续向下扩展至第四层链接</el-descriptions-item>
        <el-descriptions-item label="深度 5">继续向下扩展至第五层链接（最大）</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWebsite">保存</el-button>
      </template>
    </el-dialog>

    <!-- 检测完成弹窗 -->
    <el-dialog v-model="resultDialogVisible" title="检测完成" width="600px" :close-on-click-modal="false">
      <div v-if="resultData">
        <el-result icon="success" :title="resultTitle" :sub-title="resultSubtitle">
          <template #extra>
            <el-tag type="success" size="large" style="margin-right: 8px;">
              爬取页面: {{ resultData.pages_crawled }}
            </el-tag>
            <el-tag type="danger" size="large" v-if="resultData.leaks_detected > 0" style="margin-right: 8px;">
              发现泄露: {{ resultData.leaks_detected }}
            </el-tag>
            <el-tag type="info" size="large" v-else>
              发现泄露: 0
            </el-tag>
          </template>
        </el-result>

        <el-divider />

        <div style="text-align: center; margin-bottom: 16px;">
          <el-button type="primary" size="small" @click="goToLeaks">查看泄露记录</el-button>
          <el-button size="small" @click="resultDialogVisible = false">关闭</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const websites = ref([])
const showDialog = ref(false)
const form = ref({ name: '', url: '', depth: 2, maxPages: 100 })

// 检测结果弹窗
const resultDialogVisible = ref(false)
const resultData = ref(null)

onMounted(fetchWebsites)

async function fetchWebsites() {
  try {
    const res = await fetch('/api/websites/')
    if (res.ok) websites.value = await res.json()
  } catch {
    ElMessage.warning('后端服务未连接，显示空列表')
  }
}

async function saveWebsite() {
  try {
    const res = await fetch('/api/websites/', {
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
  // 找到对应的网站行，设置 loading
  const site = websites.value.find(w => w.id === id)
  if (site) site.loading = true

  try {
    const res = await fetch(`/api/crawlers/run/${id}`, { method: 'POST' })
    const data = await res.json()

    // 弹出检测结果
    resultData.value = data
    resultDialogVisible.value = true
  } catch {
    ElMessage.error('后端服务未连接')
  } finally {
    if (site) site.loading = false
  }
}

function goToLeaks() {
  resultDialogVisible.value = false
  router.push('/leaks')
}

async function deleteSite(id) {
  try {
    await fetch(`/api/websites/${id}`, { method: 'DELETE' })
    ElMessage.success('删除成功')
    await fetchWebsites()
  } catch {
    ElMessage.error('删除失败')
  }
}
</script>
