const api = require('../../../utils/api')

Page({
  data: {
    reminders: [],
    loading: true,
    watering: false,  // 批量浇水中
  },

  onShow() {
    this.loadReminders()
  },

  async loadReminders() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/reminders')
      this.setData({ reminders: data || [], loading: false })
    } catch (err) {
      console.error('加载提醒失败', err)
      this.setData({ loading: false })
    }
  },

  // 单个浇水
  async handleWaterOne(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.post(`/api/plants/${id}/water`)
      // 从列表中移除
      const reminders = this.data.reminders.filter(p => p.id !== id)
      this.setData({ reminders })
      wx.showToast({ title: '已浇水 💧', icon: 'success' })
    } catch (err) {
      console.error('浇水失败', err)
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 批量浇水
  handleWaterAll() {
    wx.showModal({
      title: '全部浇水',
      content: `确认给 ${this.data.reminders.length} 棵植物浇水吗？`,
      success: async (res) => {
        if (!res.confirm) return
        this.setData({ watering: true })
        try {
          const promises = this.data.reminders.map(p =>
            api.post(`/api/plants/${p.id}/water`)
          )
          await Promise.all(promises)
          this.setData({ reminders: [], watering: false })
          wx.showToast({ title: '全部浇完 🌈', icon: 'success' })
        } catch (err) {
          console.error('批量浇水失败', err)
          this.setData({ watering: false })
          this.loadReminders()  // 刷新看哪些成功了
        }
      },
    })
  },
})
