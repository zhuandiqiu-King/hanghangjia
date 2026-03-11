App({
  globalData: {
    baseUrl: '', // 云托管环境不需要域名，使用相对路径即可
  },

  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.redirectTo({ url: '/pages/login/login' })
    }
  },
})
