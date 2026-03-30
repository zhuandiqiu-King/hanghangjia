const api = require('../../../utils/api')

Page({
  data: {
    children: [],
    currentChild: null,
    wordbooks: [],
  },

  onShow() {
    this._loadChildren()
  },

  /** 加载小朋友列表 */
  _loadChildren() {
    api.get('/api/children').then((list) => {
      this.setData({ children: list })
      // 自动选中第一个或恢复上次选中
      const lastId = wx.getStorageSync('current_child_id')
      const match = list.find(c => c.id === lastId)
      if (match) {
        this.selectChild({ currentTarget: { dataset: { id: match.id } } })
      } else if (list.length) {
        this.selectChild({ currentTarget: { dataset: { id: list[0].id } } })
      } else {
        this.setData({ currentChild: null, wordbooks: [] })
      }
    }).catch((err) => {
      const msg = (err && err.message) || ''
      if (msg.indexOf('请先加入一个家庭') !== -1) {
        wx.showModal({
          title: '尚未加入家庭',
          content: '使用背单词功能需要先创建或加入一个家庭，是否前往设置？',
          confirmText: '去设置',
          cancelText: '稍后',
          success(res) {
            if (res.confirm) {
              wx.switchTab({ url: '/pages/profile/profile' })
            }
          },
        })
      } else {
        wx.showToast({ title: msg || '加载失败', icon: 'none' })
      }
    })
  },

  /** 选择小朋友 */
  selectChild(e) {
    const id = e.currentTarget.dataset.id
    const child = this.data.children.find(c => c.id === id)
    if (!child) return
    wx.setStorageSync('current_child_id', id)
    this.setData({ currentChild: child })
    this._loadWordbooks(id)
  },

  /** 加载单词本 */
  _loadWordbooks(childId) {
    api.get(`/api/children/${childId}/wordbooks`).then((list) => {
      this.setData({ wordbooks: list })
    })
  },

  /** 添加小朋友 */
  showAddChild() {
    const avatars = ['👦', '👧', '🧒', '👶', '🧒🏻']
    wx.showModal({
      title: '添加小朋友',
      placeholderText: '请输入名字',
      editable: true,
      success: (res) => {
        if (!res.confirm || !res.content || !res.content.trim()) return
        const name = res.content.trim()
        const avatar = avatars[Math.floor(Math.random() * avatars.length)]
        api.post('/api/children', { name, avatar }).then(() => {
          wx.showToast({ title: '添加成功', icon: 'success' })
          this._loadChildren()
        })
      },
    })
  },

  /** 新建单词本 */
  showAddBook() {
    if (!this.data.currentChild) return
    wx.showModal({
      title: '新建单词本',
      placeholderText: '例如：Unit 1',
      editable: true,
      success: (res) => {
        if (!res.confirm || !res.content || !res.content.trim()) return
        const childId = this.data.currentChild.id
        api.post(`/api/children/${childId}/wordbooks`, {
          name: res.content.trim(),
        }).then(() => {
          wx.showToast({ title: '创建成功', icon: 'success' })
          this._loadWordbooks(childId)
        })
      },
    })
  },

  /** 进入单词本详情 */
  goToBook(e) {
    const bookId = e.currentTarget.dataset.id
    const childId = this.data.currentChild.id
    wx.navigateTo({
      url: `/pages/vocab/wordbook/wordbook?book_id=${bookId}&child_id=${childId}`,
    })
  },

  /** 长按删除单词本 */
  onBookLongPress(e) {
    const bookId = e.currentTarget.dataset.id
    const bookName = e.currentTarget.dataset.name
    wx.showModal({
      title: '删除单词本',
      content: `确定删除「${bookName}」吗？所有单词将被清除。`,
      confirmColor: '#e74c3c',
      success: (res) => {
        if (!res.confirm) return
        api.del(`/api/wordbooks/${bookId}`).then(() => {
          wx.showToast({ title: '已删除', icon: 'success' })
          this._loadWordbooks(this.data.currentChild.id)
        })
      },
    })
  },
})
