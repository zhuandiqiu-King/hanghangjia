const { login } = require('../../utils/auth')

Page({
  data: {
    loading: false,
    agreed: false,
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/home/home' })
    }
  },

  toggleAgree() {
    this.setData({ agreed: !this.data.agreed })
  },

  showPrivacy() {
    wx.showModal({
      title: '隐私政策',
      content: '夯夯家尊重并保护用户隐私。我们仅收集提供服务所必需的信息（微信昵称、头像），不会向第三方分享您的个人数据。您的数据仅用于家庭管理功能，可随时在"我的"页面中删除账号及相关数据。',
      showCancel: false,
      confirmText: '我知道了',
    })
  },

  showUserAgreement() {
    wx.showModal({
      title: '用户服务协议',
      content: '欢迎使用夯夯家。本小程序为家庭生活管理工具，提供浇水提醒、购物清单、烹饪助手等功能。使用本服务即表示您同意遵守相关法律法规，不得利用本服务从事违法活动。我们保留修改服务内容的权利。',
      showCancel: false,
      confirmText: '我知道了',
    })
  },

  handleLogin() {
    if (this.data.loading) return
    if (!this.data.agreed) {
      wx.showToast({ title: '请先阅读并同意协议', icon: 'none' })
      return
    }
    this.setData({ loading: true })

    login('', '')
      .then((data) => {
        console.log('登录成功', data)
        // 加载家庭信息
        const app = getApp()
        app.loadCurrentFamily()
        // 新用户且未完成过引导 → 跳引导页
        const onboardingDone = wx.getStorageSync('onboarding_done')
        if (data.is_new_user && !onboardingDone) {
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
