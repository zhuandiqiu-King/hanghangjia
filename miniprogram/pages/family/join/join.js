const api = require('../../../utils/api')

Page({
  data: {
    status: 'loading', // loading | success | error
    familyName: '',
    errorMsg: '',
  },

  onLoad(options) {
    const code = options.code || ''
    if (!code) {
      this.setData({ status: 'error', errorMsg: '邀请码无效' })
      return
    }
    this.joinFamily(code)
  },

  async joinFamily(code) {
    // 先确保已登录
    const token = wx.getStorageSync('token')
    if (!token) {
      // 跳转登录，登录后回来
      wx.redirectTo({ url: `/pages/login/login?redirect=/pages/family/join/join&code=${code}` })
      return
    }

    try {
      const res = await api.post('/api/family/join', { invite_code: code })
      const app = getApp()
      app.globalData.currentFamilyId = res.id
      app.globalData.currentFamilyName = res.name
      this.setData({
        status: 'success',
        familyName: res.name,
      })
    } catch (err) {
      this.setData({
        status: 'error',
        errorMsg: err.message || '加入失败',
      })
    }
  },

  goHome() {
    wx.switchTab({ url: '/pages/home/home' })
  },
})
