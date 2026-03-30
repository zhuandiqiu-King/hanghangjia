const api = require('../../utils/api')
const { clearToken } = require('../../utils/auth')
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
    loggedIn: false,
    nickname: '',
    avatarUrl: '',
    emojiAvatar: '😊',
    realAvatar: false,
    // 偏好
    chatStyle: 'gentle',
    character: 'none',
    customCharacter: '',
    prefNickname: '',
    // 选项
    styleOptions: STYLE_OPTIONS,
    characterOptions: CHARACTER_OPTIONS,
    styleIndex: 0,
    characterIndex: 0,
    // 浇水提醒
    reminderEnabled: false,
    reminderTime: '06:30',
    // 家庭
    currentFamilyName: '',
    // 状态
    showCustomInput: false,
    loading: true,
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.setData({ loggedIn: true })
      this.loadProfile()
      this.loadFamilyInfo()
    } else {
      this.setData({ loggedIn: false, loading: false })
    }
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  async loadFamilyInfo() {
    try {
      const families = await api.get('/api/family')
      const app = getApp()
      // 找当前家庭
      const current = families.find((f) => f.id === app.globalData.currentFamilyId) || families[0]
      if (current) {
        app.globalData.currentFamilyId = current.id
        app.globalData.currentFamilyName = current.name
        this.setData({ currentFamilyName: current.name })
      }
    } catch (err) {
      console.error('加载家庭信息失败', err)
    }
  },

  goFamily() {
    wx.navigateTo({ url: '/pages/family/index/index' })
  },

  async loadProfile() {
    const token = wx.getStorageSync('token')
    if (!token) return
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/user/profile')
      const prefs = data.preferences || {}
      const styleIdx = STYLE_OPTIONS.findIndex(o => o.value === (prefs.chat_style || 'gentle'))
      const charIdx = CHARACTER_OPTIONS.findIndex(o => o.value === (prefs.character || 'none'))
      const url = data.avatar_url || ''

      this.setData({
        nickname: data.nickname || '',
        avatarUrl: url,
        emojiAvatar: isEmojiAvatar(url) ? getEmoji(url) : '😊',
        realAvatar: hasRealAvatar(url),
        chatStyle: prefs.chat_style || 'gentle',
        character: prefs.character || 'none',
        customCharacter: prefs.custom_character || '',
        prefNickname: prefs.nickname || '',
        styleIndex: styleIdx >= 0 ? styleIdx : 0,
        characterIndex: charIdx >= 0 ? charIdx : 0,
        showCustomInput: prefs.character === 'custom',
        reminderEnabled: !!prefs.reminder_enabled,
        reminderTime: prefs.reminder_time || '06:30',
        loading: false,
      })
    } catch (err) {
      console.error('加载用户信息失败', err)
      this.setData({ loading: false })
    }
  },

  // 修改头像
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
          success: async (urlRes) => {
            const url = urlRes.fileList[0].tempFileURL
            this.setData({ avatarUrl: url, realAvatar: true })
            // 同步到后端
            try {
              await api.put('/api/user/profile', { avatar_url: url })
              wx.showToast({ title: '头像已更新', icon: 'success' })
            } catch (err) {
              console.error('头像保存失败', err)
            }
          },
          fail: () => {
            this.setData({ avatarUrl: res.fileID, realAvatar: true })
          },
        })
      },
      fail: (err) => {
        console.error('头像上传失败', err)
        wx.showToast({ title: '上传失败', icon: 'none' })
      },
    })
  },

  // 修改昵称
  handleEditNickname() {
    wx.showModal({
      title: '修改昵称',
      editable: true,
      placeholderText: '请输入新昵称',
      success: async (res) => {
        if (!res.confirm || !res.content) return
        const name = res.content.trim()
        if (!name) return
        try {
          await api.put('/api/user/profile', { nickname: name })
          this.setData({ nickname: name })
          wx.showToast({ title: '昵称已更新', icon: 'success' })
        } catch (err) {
          wx.showToast({ title: '修改失败', icon: 'none' })
        }
      },
    })
  },

  // 对话风格选择
  onStyleChange(e) {
    const idx = Number(e.detail.value)
    const style = STYLE_OPTIONS[idx].value
    this.setData({ styleIndex: idx, chatStyle: style })
  },

  // 角色人设选择
  onCharacterChange(e) {
    const idx = Number(e.detail.value)
    const char = CHARACTER_OPTIONS[idx].value
    this.setData({
      characterIndex: idx,
      character: char,
      showCustomInput: char === 'custom',
    })
  },

  // 自定义角色描述
  onCustomCharInput(e) {
    this.setData({ customCharacter: e.detail.value })
  },

  // 称呼方式输入
  onPrefNicknameInput(e) {
    this.setData({ prefNickname: e.detail.value })
  },

  // 浇水提醒开关
  onReminderSwitch(e) {
    const enabled = e.detail.value
    if (enabled) {
      // 开启时请求订阅消息授权
      wx.requestSubscribeMessage({
        tmplIds: ['-1sJJ5rAhggfgcpjAEVx6ZwONBRGYnFema_WBSdZRbA'],
        success: () => {
          this.setData({ reminderEnabled: true })
          this._saveReminderPrefs(true, this.data.reminderTime)
        },
        fail: () => {
          // 用户拒绝授权也允许开启（后端仍可记录偏好）
          this.setData({ reminderEnabled: true })
          this._saveReminderPrefs(true, this.data.reminderTime)
        },
      })
    } else {
      this.setData({ reminderEnabled: false })
      this._saveReminderPrefs(false, this.data.reminderTime)
    }
  },

  // 提醒时间选择
  onReminderTimeChange(e) {
    const time = e.detail.value
    this.setData({ reminderTime: time })
    if (this.data.reminderEnabled) {
      this._saveReminderPrefs(true, time)
    }
  },

  // 保存提醒偏好到后端
  async _saveReminderPrefs(enabled, time) {
    try {
      const prefs = {
        reminder_enabled: enabled,
        reminder_time: time,
      }
      await api.put('/api/user/profile', { preferences: prefs })
      wx.showToast({ title: enabled ? '提醒已开启' : '提醒已关闭', icon: 'success' })
    } catch (err) {
      console.error('保存提醒设置失败', err)
      wx.showToast({ title: '保存失败', icon: 'none' })
    }
  },

  // 点击保存按钮
  async handleSave() {
    await this.savePreferences()
    wx.showToast({ title: '设置已保存', icon: 'success' })
  },

  // 保存偏好到后端
  async savePreferences() {
    const token = wx.getStorageSync('token')
    if (!token) return
    const prefs = {
      chat_style: this.data.chatStyle,
      character: this.data.character,
      custom_character: this.data.customCharacter,
      nickname: this.data.prefNickname,
    }
    try {
      await api.put('/api/user/profile', { preferences: prefs })
    } catch (err) {
      console.error('保存偏好失败', err)
    }
  },

  // 关于我们
  handleAbout() {
    wx.showModal({
      title: '关于夯夯家',
      content: '夯夯家 v2.0.0\n一款 AI 驱动的家庭生活助手\n🏠 让生活更美好',
      showCancel: false,
    })
  },

  // 退出登录
  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定退出登录吗？',
      success: (res) => {
        if (!res.confirm) return
        clearToken()
        wx.redirectTo({ url: '/pages/login/login' })
      },
    })
  },
})
