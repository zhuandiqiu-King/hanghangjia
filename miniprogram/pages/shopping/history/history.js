const api = require('../../../utils/api')

Page({
  data: {
    loading: true,
    historyList: [],
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const list = await api.get('/api/shopping/history')
      const historyList = list.map(item => ({
        ...item,
        expanded: false,
        dateStr: item.archived_at ? this.formatDate(item.archived_at) : '未知日期',
      }))
      this.setData({ historyList, loading: false })
    } catch (err) {
      console.error('加载历史记录失败', err)
      this.setData({ loading: false })
    }
  },

  formatDate(dateStr) {
    const d = new Date(dateStr)
    const m = d.getMonth() + 1
    const day = d.getDate()
    const h = d.getHours().toString().padStart(2, '0')
    const min = d.getMinutes().toString().padStart(2, '0')
    return `${m}月${day}日 ${h}:${min}`
  },

  toggleCard(e) {
    const id = e.currentTarget.dataset.id
    const list = this.data.historyList.map(item => {
      if (item.id === id) return { ...item, expanded: !item.expanded }
      return item
    })
    this.setData({ historyList: list })
  },

  async handleRebuy(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '一键重买',
      content: '将此次购物清单中的商品重新加入当前清单？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await api.post(`/api/shopping/history/${id}/rebuy`)
            wx.showToast({ title: result.message || '已添加', icon: 'none' })
          } catch (err) {
            wx.showToast({ title: '操作失败', icon: 'none' })
          }
        }
      },
    })
  },
})
