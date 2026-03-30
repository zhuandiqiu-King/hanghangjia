const api = require('../../../utils/api')

Page({
  data: {
    loading: true,
    frequentList: [],
    selectedIds: [],
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true, selectedIds: [] })
    try {
      const list = await api.get('/api/shopping/frequent')
      const frequentList = list.map(item => ({ ...item, selected: false }))
      this.setData({ frequentList, loading: false })
    } catch (err) {
      console.error('加载常买清单失败', err)
      this.setData({ loading: false })
    }
  },

  // 勾选/取消勾选
  toggleSelect(e) {
    const id = e.currentTarget.dataset.id
    const list = this.data.frequentList.map(item => {
      if (item.id === id) return { ...item, selected: !item.selected }
      return item
    })
    const selectedIds = list.filter(i => i.selected).map(i => i.id)
    this.setData({ frequentList: list, selectedIds })
  },

  // 单个快速加入
  async handleQuickAdd(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.post('/api/shopping/frequent/add-to-list', { item_ids: [id] })
      wx.showToast({ title: '已加入清单', icon: 'none' })
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 批量加入
  async handleBatchAdd() {
    const ids = this.data.selectedIds
    if (ids.length === 0) return
    try {
      const result = await api.post('/api/shopping/frequent/add-to-list', { item_ids: ids })
      wx.showToast({ title: result.message || '已添加', icon: 'none' })
      // 清除选中状态
      const list = this.data.frequentList.map(item => ({ ...item, selected: false }))
      this.setData({ frequentList: list, selectedIds: [] })
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 删除常买商品
  handleDelete(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '删除',
      content: '从常买清单中移除？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.del(`/api/shopping/frequent/${id}`)
            this.loadData()
          } catch (err) {
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      },
    })
  },
})
