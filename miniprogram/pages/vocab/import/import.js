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

  /**
   * 缩小图片尺寸并压缩质量，返回 base64 字符串
   * 最长边限制 1200px，JPEG quality 70
   */
  _resizeAndEncode(src) {
    const MAX_SIDE = 1200
    return new Promise((resolve, reject) => {
      wx.getImageInfo({
        src,
        success: (info) => {
          let w = info.width, h = info.height
          if (w > MAX_SIDE || h > MAX_SIDE) {
            const ratio = Math.min(MAX_SIDE / w, MAX_SIDE / h)
            w = Math.round(w * ratio)
            h = Math.round(h * ratio)
          }
          const canvas = wx.createOffscreenCanvas({ type: '2d', width: w, height: h })
          const ctx = canvas.getContext('2d')
          const img = canvas.createImage()
          img.onload = () => {
            ctx.drawImage(img, 0, 0, w, h)
            const dataURL = canvas.toDataURL('image/jpeg', 0.7)
            // 去掉 data:image/jpeg;base64, 前缀
            const base64 = dataURL.replace(/^data:image\/\w+;base64,/, '')
            resolve(base64)
          }
          img.onerror = () => reject(new Error('图片加载失败'))
          img.src = src
        },
        fail: () => reject(new Error('获取图片信息失败')),
      })
    })
  },

  /** 开始识别 */
  startRecognize() {
    this.setData({ step: 'loading' })

    this._resizeAndEncode(this.data.imageSrc).then((base64) => {
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
    }).catch((err) => {
      console.error('图片处理失败', err)
      wx.showToast({ title: '图片处理失败', icon: 'none' })
      this.setData({ step: 'photo' })
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
