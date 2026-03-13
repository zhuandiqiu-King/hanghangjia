const { login } = require('../../utils/auth')

Page({
  data: {
    loading: false,
  },

  onLoad() {
    // 已登录直接跳首页
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/home/home' })
    }
  },

  handleLogin() {
    if (this.data.loading) return
    this.setData({ loading: true })

    // 一键登录，不传昵称和头像（后端自动生成）
    login('', '')
      .then((data) => {
        console.log('登录成功', data)
        if (data.is_new_user) {
          // 新用户 → 引导填写个人信息
          wx.redirectTo({ url: '/pages/onboarding/onboarding' })
        } else {
          wx.switchTab({ url: '/pages/home/home' })
        }
      })
      .catch((err) => {
        console.error('登录失败:', err.message || err)
        wx.showToast({ title: '登录失败，请重试', icon: 'none' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },
})
