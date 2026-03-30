const api = require('../../utils/api')

const recorderManager = wx.getRecorderManager()

Page({
  data: {
    messages: [],
    inputValue: '',
    loading: false,
    scrollId: '',
    voiceMode: false,
    recording: false,
    hasRecordAuth: false,
  },

  onLoad() {
    recorderManager.onStart(() => {
      this._recorderStarted = true
      this.setData({ recording: true })
      if (this._pendingStop) {
        this._pendingStop = false
        recorderManager.stop()
      }
    })

    recorderManager.onStop((res) => {
      this._recorderStarted = false
      this.setData({ recording: false })
      if (res.duration < 1000) {
        wx.showToast({ title: '说话时间太短', icon: 'none' })
        return
      }
      this.handleVoiceFile(res.tempFilePath)
    })

    recorderManager.onError((err) => {
      console.error('录音失败', err)
      this._recorderStarted = false
      this._pendingStop = false
      this.setData({ recording: false })
    })
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '登录后才能使用此功能',
        confirmText: '去登录',
        cancelText: '返回',
        success(res) {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' })
          } else {
            wx.navigateBack()
          }
        },
      })
      return
    }
    if (!this.data.messages.length) {
      this.setData({
        messages: [{
          role: 'ai',
          content: '你好！我是夯夯 🏠\n有什么问题可以问我哦～\n比如生活常识、学习辅导、烹饪技巧等 😊',
        }],
      })
    }
  },

  onInput(e) {
    this.setData({ inputValue: e.detail.value })
  },

  toggleVoice() {
    const entering = !this.data.voiceMode
    if (entering) {
      this._checkRecordAuth().then((authorized) => {
        if (authorized) {
          this.setData({ voiceMode: true, hasRecordAuth: true })
        }
      })
    } else {
      this.setData({ voiceMode: false })
    }
  },

  _checkRecordAuth() {
    return new Promise((resolve) => {
      wx.getSetting({
        success: (res) => {
          if (res.authSetting['scope.record']) {
            resolve(true)
          } else if (res.authSetting['scope.record'] === false) {
            wx.showModal({
              title: '需要录音权限',
              content: '请在设置中开启录音权限，才能使用语音功能',
              confirmText: '去设置',
              success: (modalRes) => {
                if (modalRes.confirm) {
                  wx.openSetting({
                    success: (settingRes) => {
                      resolve(!!settingRes.authSetting['scope.record'])
                    },
                    fail: () => resolve(false),
                  })
                } else {
                  resolve(false)
                }
              },
            })
          } else {
            wx.authorize({
              scope: 'scope.record',
              success: () => resolve(true),
              fail: () => {
                wx.showToast({ title: '需要录音权限才能使用语音', icon: 'none' })
                resolve(false)
              },
            })
          }
        },
        fail: () => resolve(false),
      })
    })
  },

  startRecord() {
    if (this.data.loading || this.data.recording) return
    if (!this.data.hasRecordAuth) {
      this._checkRecordAuth().then((ok) => {
        if (ok) {
          this.setData({ hasRecordAuth: true })
          this._doStartRecord()
        }
      })
      return
    }
    this._doStartRecord()
  },

  _doStartRecord() {
    this._recorderStarted = false
    this._pendingStop = false
    recorderManager.start({
      duration: 60000,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000,
      format: 'mp3',
    })
  },

  stopRecord() {
    if (this._recorderStarted) {
      recorderManager.stop()
    } else {
      this._pendingStop = true
    }
  },

  async handleVoiceFile(filePath) {
    this.setData({ loading: true })

    try {
      const cloudPath = `voice/${Date.now()}-${Math.random().toString(36).slice(2)}.mp3`
      const uploadRes = await new Promise((resolve, reject) => {
        wx.cloud.uploadFile({
          cloudPath,
          filePath,
          success: resolve,
          fail: reject,
        })
      })

      const urlRes = await new Promise((resolve, reject) => {
        wx.cloud.getTempFileURL({
          fileList: [uploadRes.fileID],
          success: resolve,
          fail: reject,
        })
      })
      const audioUrl = urlRes.fileList[0].tempFileURL

      const data = await api.request({
        url: '/api/chat/voice',
        method: 'POST',
        data: { audio_url: audioUrl },
        timeout: 60000,
      })

      const userMsg = { role: 'user', content: data.text || '🎤 语音消息' }
      const aiMsg = { role: 'ai', content: data.reply }
      const updated = [...this.data.messages, userMsg, aiMsg]
      this.setData({
        messages: updated,
        loading: false,
        scrollId: `msg-${updated.length - 1}`,
      })
    } catch (err) {
      console.error('语音处理失败', err)
      const updated = [...this.data.messages, {
        role: 'ai',
        content: '语音识别失败，请重试或改用文字输入 😢',
      }]
      this.setData({
        messages: updated,
        loading: false,
        scrollId: `msg-${updated.length - 1}`,
      })
    }
  },

  async handleSend() {
    const msg = this.data.inputValue.trim()
    if (!msg || this.data.loading) return

    const messages = [...this.data.messages, { role: 'user', content: msg }]
    this.setData({
      messages,
      inputValue: '',
      loading: true,
      scrollId: `msg-${messages.length - 1}`,
    })

    try {
      const data = await api.request({
        url: '/api/chat',
        method: 'POST',
        data: { message: msg },
        timeout: 30000,
      })
      const updated = [...this.data.messages, { role: 'ai', content: data.reply }]
      this.setData({
        messages: updated,
        loading: false,
        scrollId: `msg-${updated.length - 1}`,
      })
    } catch (err) {
      console.error('AI 回复失败', err)
      const updated = [...this.data.messages, {
        role: 'ai',
        content: '抱歉，我暂时无法回复，请稍后再试 😢',
      }]
      this.setData({
        messages: updated,
        loading: false,
        scrollId: `msg-${updated.length - 1}`,
      })
    }
  },

  handleCopy(e) {
    const idx = e.currentTarget.dataset.idx
    const msg = this.data.messages[idx]
    wx.setClipboardData({
      data: msg.content,
      success() {
        wx.showToast({ title: '已复制', icon: 'success' })
      },
    })
  },
})
