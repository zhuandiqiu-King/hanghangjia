const api = require('../../../utils/api')

Page({
  data: {
    bookId: 0,
    step: 'photo', // photo | loading | confirm
    imageSrc: '',
    words: [],
  },

  onLoad(opts) {
    this.setData({ bookId: parseInt(opts.book_id) })
  },

  /** 选择图片 */
  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempPath = res.tempFiles[0].tempFilePath
        this.setData({ imageSrc: tempPath, step: 'photo' })
      },
    })
  },

  /** 开始识别 */
  startRecognize() {
    this.setData({ step: 'loading' })

    // 读取图片为 base64
    const fs = wx.getFileSystemManager()
    fs.readFile({
      filePath: this.data.imageSrc,
      encoding: 'base64',
      success: (res) => {
        const base64 = res.data
        api.request({
          url: '/api/vocab/ocr-words',
          method: 'POST',
          data: { image: base64 },
          timeout: 60000,
        }).then((data) => {
          const words = (data.words || []).map((w, i) => ({
            ...w,
            idx: i,
          }))
          if (!words.length) {
            wx.showToast({ title: '未识别到单词', icon: 'none' })
            this.setData({ step: 'photo' })
            return
          }
          this.setData({ words, step: 'confirm' })
        }).catch((err) => {
          console.error('识别失败', err)
          wx.showToast({ title: '识别失败，请重试', icon: 'none' })
          this.setData({ step: 'photo' })
        })
      },
      fail: () => {
        wx.showToast({ title: '读取图片失败', icon: 'none' })
        this.setData({ step: 'photo' })
      },
    })
  },

  /** 编辑英文 */
  onEditEn(e) {
    const idx = e.currentTarget.dataset.idx
    const words = [...this.data.words]
    words[idx].english = e.detail.value
    this.setData({ words })
  },

  /** 编辑中文 */
  onEditCn(e) {
    const idx = e.currentTarget.dataset.idx
    const words = [...this.data.words]
    words[idx].chinese = e.detail.value
    this.setData({ words })
  },

  /** 删除单词 */
  removeWord(e) {
    const idx = e.currentTarget.dataset.idx
    const words = this.data.words.filter((_, i) => i !== idx)
    this.setData({ words })
  },

  /** 重新拍照 */
  reChoose() {
    this.setData({ step: 'photo', imageSrc: '', words: [] })
  },

  /** 保存到单词本 */
  saveWords() {
    const valid = this.data.words.filter(w => w.english.trim() && w.chinese.trim())
    if (!valid.length) {
      wx.showToast({ title: '没有有效单词', icon: 'none' })
      return
    }

    const payload = valid.map(w => ({
      english: w.english.trim(),
      chinese: w.chinese.trim(),
      phonetic: (w.phonetic || '').trim() || null,
    }))

    api.post(`/api/wordbooks/${this.data.bookId}/words/batch`, {
      words: payload,
    }).then(() => {
      wx.showToast({ title: `已导入 ${payload.length} 个单词`, icon: 'success' })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }).catch((err) => {
      console.error('保存失败', err)
      wx.showToast({ title: '保存失败', icon: 'none' })
    })
  },
})
