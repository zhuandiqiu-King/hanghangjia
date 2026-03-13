const api = require('../../utils/api')
const { isEmojiAvatar, getEmoji, hasRealAvatar } = require('../../utils/avatar')

Page({
  data: {
    nickname: '',
    avatarUrl: '',
    emojiAvatar: '😊',
    realAvatar: false,
    saving: false,
  },

  onLoad() {
    this.loadProfile()
  },

  async loadProfile() {
    try {
      const data = await api.get('/api/user/profile')
      const url = data.avatar_url || ''
      this.setData({
        nickname: data.nickname || '',
        avatarUrl: url,
        emojiAvatar: isEmojiAvatar(url) ? getEmoji(url) : '😊',
        realAvatar: hasRealAvatar(url),
      })
    } catch (err) {
      console.error('加载用户信息失败', err)
    }
  },

  // 选择微信头像
  onChooseAvatar(e) {
    const tempUrl = e.detail.avatarUrl
    if (!tempUrl) return
    const cloudPath = `avatars/${Date.now()}-${Math.random().toString(36).slice(2)}.jpg`
    wx.cloud.uploadFile({
      cloudPath,
      filePath: tempUrl,
      success: (res) => {
        wx.cloud.getTempFileURL({
          fileList: [res.fileID],
          success: (urlRes) => {
            const url = urlRes.fileList[0].tempFileURL
            this.setData({ avatarUrl: url, realAvatar: true })
          },
          fail: () => {
            this.setData({ avatarUrl: res.fileID, realAvatar: true })
          },
        })
      },
      fail: (err) => {
        console.error('头像上传失败', err)
        this.setData({ avatarUrl: tempUrl, realAvatar: true })
      },
    })
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value || '' })
  },

  async handleSave() {
    const { nickname, avatarUrl } = this.data
    if (!nickname.trim()) {
      wx.showToast({ title: '请输入昵称', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    try {
      await api.put('/api/user/profile', {
        nickname: nickname.trim(),
        avatar_url: avatarUrl || undefined,
      })
      wx.showToast({ title: '设置成功', icon: 'success' })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/home/home' })
      }, 800)
    } catch (err) {
      console.error('保存失败', err)
      wx.showToast({ title: '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  handleSkip() {
    wx.switchTab({ url: '/pages/home/home' })
  },
})
