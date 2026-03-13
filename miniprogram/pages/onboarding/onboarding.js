const api = require('../../utils/api')
const { isEmojiAvatar, getEmoji, hasRealAvatar } = require('../../utils/avatar')

// 对话风格选项
const STYLE_OPTIONS = [
  { value: 'gentle', label: '温柔贴心' },
  { value: 'humorous', label: '幽默有趣' },
  { value: 'professional', label: '专业严谨' },
  { value: 'energetic', label: '元气满满' },
]

// 角色人设选项
const CHARACTER_OPTIONS = [
  { value: 'none', label: '无' },
  { value: 'cat', label: '🐱 小猫咪' },
  { value: 'rabbit', label: '🐰 小兔叽' },
  { value: 'dog', label: '🐶 小狗勾' },
  { value: 'bear', label: '🐻 小熊仔' },
  { value: 'fox', label: '🦊 小狐狸' },
  { value: 'penguin', label: '🐧 小企鹅' },
  { value: 'custom', label: '✏️ 自定义' },
]

Page({
  data: {
    nickname: '',
    avatarUrl: '',
    emojiAvatar: '😊',
    realAvatar: false,
    saving: false,
    // AI 偏好
    chatStyle: 'gentle',
    character: 'none',
    customCharacter: '',
    prefNickname: '',
    // 选项
    styleOptions: STYLE_OPTIONS,
    characterOptions: CHARACTER_OPTIONS,
    styleIndex: 0,
    characterIndex: 0,
    showCustomInput: false,
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

  // AI 偏好
  onStyleChange(e) {
    const idx = Number(e.detail.value)
    this.setData({ styleIndex: idx, chatStyle: STYLE_OPTIONS[idx].value })
  },

  onCharacterChange(e) {
    const idx = Number(e.detail.value)
    const char = CHARACTER_OPTIONS[idx].value
    this.setData({
      characterIndex: idx,
      character: char,
      showCustomInput: char === 'custom',
    })
  },

  onCustomCharInput(e) {
    this.setData({ customCharacter: e.detail.value })
  },

  onPrefNicknameInput(e) {
    this.setData({ prefNickname: e.detail.value })
  },

  // 保存全部信息
  async handleSave() {
    this.setData({ saving: true })
    try {
      const payload = {
        preferences: {
          chat_style: this.data.chatStyle,
          character: this.data.character,
          custom_character: this.data.customCharacter,
          nickname: this.data.prefNickname,
        },
      }
      // 有修改昵称才传
      if (this.data.nickname.trim()) {
        payload.nickname = this.data.nickname.trim()
      }
      // 有真实头像才传
      if (this.data.realAvatar && this.data.avatarUrl) {
        payload.avatar_url = this.data.avatarUrl
      }
      await api.put('/api/user/profile', payload)
      wx.setStorageSync('onboarding_done', true)
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

  // 跳过 — 使用默认值直接进首页
  handleSkip() {
    wx.setStorageSync('onboarding_done', true)
    wx.switchTab({ url: '/pages/home/home' })
  },
})
