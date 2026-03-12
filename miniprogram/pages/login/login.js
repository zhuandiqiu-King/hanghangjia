const { login } = require('../../utils/auth')

Page({
  data: {
    loading: false,
    nickname: '',
    avatarUrl: '',
  },

  onLoad() {
    // 已登录直接跳首页
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/home/home' })
    }
  },

  // 选择微信头像
  onChooseAvatar(e) {
    const tempUrl = e.detail.avatarUrl
    if (!tempUrl) return
    // 上传到云存储获取永久链接
    const cloudPath = `avatars/${Date.now()}-${Math.random().toString(36).slice(2)}.jpg`
    wx.cloud.uploadFile({
      cloudPath,
      filePath: tempUrl,
      success: (res) => {
        // 获取可访问的 https 链接
        wx.cloud.getTempFileURL({
          fileList: [res.fileID],
          success: (urlRes) => {
            const url = urlRes.fileList[0].tempFileURL
            this.setData({ avatarUrl: url })
          },
          fail: () => {
            // 备用：直接用 fileID
            this.setData({ avatarUrl: res.fileID })
          },
        })
      },
      fail: (err) => {
        console.error('头像上传失败', err)
        // 退回使用临时路径
        this.setData({ avatarUrl: tempUrl })
      },
    })
  },

  // 昵称输入
  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value || '' })
  },

  handleLogin() {
    if (this.data.loading) return
    this.setData({ loading: true })
    console.log('开始登录...')

    const { nickname, avatarUrl } = this.data
    login(nickname, avatarUrl)
      .then((data) => {
        console.log('登录成功', data)
        wx.switchTab({ url: '/pages/home/home' })
      })
      .catch((err) => {
        console.error('登录失败详情:', err.message || err)
        wx.showToast({ title: '登录失败，请重试', icon: 'none' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },
})
