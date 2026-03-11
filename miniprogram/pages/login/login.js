const { login } = require('../../utils/auth')

Page({
  data: {
    loading: false,
  },

  onLoad() {},

  handleLogin() {
    if (this.data.loading) return
    this.setData({ loading: true })

    // 获取用户信息后登录
    wx.getUserProfile({
      desc: '用于显示用户昵称和头像',
      success: (profileRes) => {
        const { nickName, avatarUrl } = profileRes.userInfo
        login(nickName, avatarUrl)
          .then(() => {
            wx.redirectTo({ url: '/pages/index/index' })
          })
          .catch((err) => {
            console.error('登录失败', err)
            // getUserProfile 失败时也尝试无昵称登录
            this.loginWithoutProfile()
          })
      },
      fail: () => {
        // 用户拒绝授权，仍可无昵称登录
        this.loginWithoutProfile()
      },
    })
  },

  loginWithoutProfile() {
    login('', '')
      .then(() => {
        wx.switchTab({ url: '/pages/index/index' })
      })
      .catch((err) => {
        console.error('登录失败', err)
        wx.showToast({ title: '登录失败，请重试', icon: 'none' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },
})
