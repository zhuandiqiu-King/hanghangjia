const api = require('../../utils/api')

Page({
  data: {
    messages: [],     // { role: 'user'|'ai', content: string }
    inputValue: '',
    loading: false,   // AI 回复中
    scrollId: '',     // 滚动锚点
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    // 首次进入显示欢迎语
    if (!this.data.messages.length) {
      this.setData({
        messages: [{
          role: 'ai',
          content: '你好！我是植物精灵 🌱\n有什么家庭生活问题可以问我哦～\n比如植物养护、家居清洁、烹饪技巧等 😊',
        }],
      })
    }
  },

  onInput(e) {
    this.setData({ inputValue: e.detail.value })
  },

  // 发送消息
  async handleSend() {
    const msg = this.data.inputValue.trim()
    if (!msg || this.data.loading) return

    // 添加用户消息
    const messages = [...this.data.messages, { role: 'user', content: msg }]
    this.setData({
      messages,
      inputValue: '',
      loading: true,
      scrollId: `msg-${messages.length - 1}`,
    })

    try {
      const data = await api.post('/api/chat', { message: msg })
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

  // 长按复制
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
