const { login } = require('../../utils/auth')

Page({
  data: {
    loading: false,
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/home/home' })
    }
  },

  handleLogin() {
    if (this.data.loading) return
    this.setData({ loading: true })

    login('', '')
      .then((data) => {
        console.log('登录成功', data)
        // 仅新用户跳引导页，老用户直接进首页
        if (data.is_new_user) {
          wx.redirectTo({
            url: '/pages/onboarding/onboarding',
            fail: () => wx.switchTab({ url: '/pages/home/home' }),
          })
        } else {
          wx.switchTab({
            url: '/pages/home/home',
            fail: () => wx.reLaunch({ url: '/pages/home/home' }),
          })
        }
      })
      .catch((err) => {
        console.error('登录失败:', err.message || err)
        wx.showModal({
          title: '登录失败',
          content: '网络连接超时，可能是服务正在启动，请稍后重试',
          showCancel: false,
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },
})
