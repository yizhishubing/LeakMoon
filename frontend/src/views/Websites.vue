<template>
  <div style="padding: 20px;">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>巡检网站管理</span>
          <el-button type="primary" @click="openAddDialog">添加网站</el-button>
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
        <el-table-column label="操作" width="250" align="center">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" type="primary" @click="runCrawl(row.id)" :loading="row.loading">爬取</el-button>
              <el-button size="small" type="warning" @click="openEditDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="websites.length === 0" description="暂无巡检网站，请点击添加网站" />
    </el-card>

    <!-- 添加/编辑网站对话框 -->
    <el-dialog v-model="showDialog" :title="isEditing ? '编辑网站' : '添加网站'" width="500px">
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const websites = ref([])
const showDialog = ref(false)
const isEditing = ref(false)
const editId = ref(null)
const form = ref({ name: '', url: '', depth: 2, maxPages: 100 })

// 检测结果弹窗
const resultDialogVisible = ref(false)
const resultData = ref(null)
const resultTitle = computed(() => {
  if (!resultData.value) return ''
  return resultData.value.leaks_detected > 0
    ? '检测完成，发现泄露信息'
    : '检测完成，未发现泄露信息'
})
const resultSubtitle = computed(() => {
  if (!resultData.value) return ''
  return `共爬取 ${resultData.value.pages_crawled} 个页面`
})

onMounted(fetchWebsites)

async function fetchWebsites() {
  try {
    const res = await fetch('/api/websites/')
    if (res.ok) websites.value = await res.json()
  } catch {
    ElMessage.warning('后端服务未连接，显示空列表')
  }
}

function openAddDialog() {
  isEditing.value = false
  editId.value = null
  form.value = { name: '', url: '', depth: 2, maxPages: 100 }
  showDialog.value = true
}

function openEditDialog(row) {
  isEditing.value = true
  editId.value = row.id
  form.value = {
    name: row.name,
    url: row.url,
    depth: row.depth,
    maxPages: row.max_pages,
  }
  showDialog.value = true
}

async function saveWebsite() {
  try {
    let res
    if (isEditing.value) {
      // 编辑：PUT
      res = await fetch(`/api/websites/${editId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    } else {
      // 新增：POST
      res = await fetch('/api/websites/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    }

    if (res.ok) {
      ElMessage.success(isEditing.value ? '编辑成功' : '添加成功')
      showDialog.value = false
      await fetchWebsites()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '保存失败')
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

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定要删除该网站吗？此操作不可恢复。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const res = await fetch(`/api/websites/${id}`, { method: 'DELETE' })
    if (res.ok) {
      ElMessage.success('删除成功')
      await fetchWebsites()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '删除失败')
    }
  } catch (action) {
    // 用户取消删除，不报错
    if (action !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>
