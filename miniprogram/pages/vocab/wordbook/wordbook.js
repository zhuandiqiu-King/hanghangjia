const api = require('../../../utils/api')

Page({
  data: {
    bookId: 0,
    childId: 0,
    bookName: '',
    words: [],
    showAddModal: false,
    newEnglish: '',
    newChinese: '',
    newPhonetic: '',
  },

  onLoad(opts) {
    this.setData({
      bookId: parseInt(opts.book_id),
      childId: parseInt(opts.child_id),
    })
  },

  onShow() {
    this._loadBook()
  },

  _loadBook() {
    api.get(`/api/wordbooks/${this.data.bookId}`).then((data) => {
      this.setData({
        bookName: data.name,
        words: data.words || [],
      })
      wx.setNavigationBarTitle({ title: data.name })
    })
  },

  /** 显示/隐藏添加弹窗 */
  showAddWord() {
    this.setData({ showAddModal: true, newEnglish: '', newChinese: '', newPhonetic: '' })
  },

  hideAddModal() {
    this.setData({ showAddModal: false })
  },

  onInputEn(e) { this.setData({ newEnglish: e.detail.value }) },
  onInputCn(e) { this.setData({ newChinese: e.detail.value }) },
  onInputPh(e) { this.setData({ newPhonetic: e.detail.value }) },

  /** 添加单词 */
  addWord() {
    const en = this.data.newEnglish.trim()
    const cn = this.data.newChinese.trim()
    if (!en || !cn) {
      wx.showToast({ title: '请填写英文和中文', icon: 'none' })
      return
    }
    api.post(`/api/wordbooks/${this.data.bookId}/words`, {
      english: en,
      chinese: cn,
      phonetic: this.data.newPhonetic.trim() || null,
    }).then(() => {
      wx.showToast({ title: '添加成功', icon: 'success' })
      this.setData({ showAddModal: false })
      this._loadBook()
    })
  },

  /** 长按删除单词 */
  onWordLongPress(e) {
    const wordId = e.currentTarget.dataset.id
    const idx = e.currentTarget.dataset.idx
    const word = this.data.words[idx]
    wx.showActionSheet({
      itemList: ['删除该单词'],
      success: (res) => {
        if (res.tapIndex === 0) {
          api.del(`/api/words/${wordId}`).then(() => {
            wx.showToast({ title: '已删除', icon: 'success' })
            this._loadBook()
          })
        }
      },
    })
  },

  /** 拍照录入 */
  goToImport() {
    wx.navigateTo({
      url: `/pages/vocab/import/import?book_id=${this.data.bookId}`,
    })
  },

  /** 开始听写 */
  startDictation() {
    if (!this.data.words.length) {
      wx.showToast({ title: '请先添加单词', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/vocab/dictation/dictation?book_id=${this.data.bookId}&child_id=${this.data.childId}`,
    })
  },

  /** 跳转错题本 */
  goToMistakes() {
    wx.navigateTo({
      url: `/pages/vocab/mistakes/mistakes?child_id=${this.data.childId}&book_id=${this.data.bookId}`,
    })
  },
})
