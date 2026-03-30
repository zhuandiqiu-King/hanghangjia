const api = require('../../utils/api')

Page({
  data: {
    loggedIn: false,
    nickname: '',
    familyName: '',
    dateText: '',
    todayTasks: [],
    weekDone: 0,
    weekPending: 0,
    familyMembers: 1,
  },

  onLoad() {
    this._setDate()
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.setData({ loggedIn: true })
      this._loadProfile()
      this._loadTodayTasks()
    } else {
      this.setData({ loggedIn: false, nickname: '', familyName: '我的家', todayTasks: [] })
    }
  },

  /** 设置日期文案 */
  _setDate() {
    const days = ['日', '一', '二', '三', '四', '五', '六']
    const now = new Date()
    const m = now.getMonth() + 1
    const d = now.getDate()
    const w = days[now.getDay()]
    this.setData({ dateText: `${m}月${d}日 周${w}` })
  },

  /** 加载用户信息 */
  _loadProfile() {
    api.get('/api/user/profile')
      .then((data) => {
        this.setData({
          nickname: data.nickname || '',
          familyName: data.family_name || '我的家',
          familyMembers: data.family_members || 1,
        })
      })
      .catch(() => {})
  },

  /** 加载今日任务（先从浇水提醒获取） */
  _loadTodayTasks() {
    api.get('/api/reminders')
      .then((data) => {
        const plants = data.plants || data || []
        const tasks = plants.map((p, i) => ({
          id: `water_${p.id || i}`,
          icon: '💧',
          name: `给${p.name || p.nickname || '植物'}浇水`,
          done: false,
          type: 'watering',
          plantId: p.id,
        }))
        this.setData({
          todayTasks: tasks,
          weekPending: tasks.filter(t => !t.done).length,
          weekDone: 0,
        })
      })
      .catch(() => {
        this.setData({ todayTasks: [] })
      })
  },

  /** 切换任务完成状态 */
  toggleTask(e) {
    const idx = e.currentTarget.dataset.idx
    const tasks = [...this.data.todayTasks]
    tasks[idx].done = !tasks[idx].done
    const done = tasks.filter(t => t.done).length
    const pending = tasks.filter(t => !t.done).length
    this.setData({
      todayTasks: tasks,
      weekDone: done,
      weekPending: pending,
    })
  },

  /** 跳转登录 */
  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  /** 快捷入口跳转 */
  goTo(e) {
    const url = e.currentTarget.dataset.url
    if (url.indexOf('/pages/tools/') === 0) {
      wx.switchTab({ url })
    } else {
      wx.navigateTo({ url })
    }
  },

  /** 跳转 AI 聊天 */
  goToChat() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '登录后才能使用 AI 聊天，是否前往登录？',
        confirmText: '去登录',
        success(res) {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' })
          }
        },
      })
      return
    }
    wx.navigateTo({ url: '/pages/chat/chat' })
  },
})
