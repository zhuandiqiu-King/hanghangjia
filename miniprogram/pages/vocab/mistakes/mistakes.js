const api = require('../../../utils/api')

Page({
  data: {
    childId: 0,
    bookId: 0,
    mistakes: [],
  },

  onLoad(opts) {
    this.setData({
      childId: parseInt(opts.child_id),
      bookId: parseInt(opts.book_id || 0),
    })
  },

  onShow() {
    this._loadMistakes()
  },

  _loadMistakes() {
    api.get(`/api/children/${this.data.childId}/mistakes`).then((list) => {
      this.setData({ mistakes: list })
    })
  },

  /** 全部重听 */
  retryAll() {
    if (!this.data.mistakes.length) return
    wx.navigateTo({
      url: `/pages/vocab/dictation/dictation?book_id=${this.data.bookId}&child_id=${this.data.childId}&mistakes_only=1`,
    })
  },

  /** 长按删除 */
  onLongPress(e) {
    const id = e.currentTarget.dataset.id
    wx.showActionSheet({
      itemList: ['从错题本移除'],
      success: (res) => {
        if (res.tapIndex === 0) {
          api.del(`/api/children/${this.data.childId}/mistakes/${id}`).then(() => {
            wx.showToast({ title: '已移除', icon: 'success' })
            this._loadMistakes()
          })
        }
      },
    })
  },
})
