App({
  globalData: {
    currentFamilyId: null,
    currentFamilyName: '',
  },
  onLaunch() {
    wx.cloud.init({
      env: 'prod-0g02is9d648082af',
      traceUser: true,
    })
  },

  /** 加载当前家庭信息（登录后调用） */
  loadCurrentFamily() {
    const api = require('./utils/api')
    api.get('/api/family').then((families) => {
      if (!families || !families.length) return
      // 找当前激活的家庭
      const current = families.find((f) => f.id === this.globalData.currentFamilyId) || families[0]
      this.globalData.currentFamilyId = current.id
      this.globalData.currentFamilyName = current.name
    }).catch(() => {})
  },
})
