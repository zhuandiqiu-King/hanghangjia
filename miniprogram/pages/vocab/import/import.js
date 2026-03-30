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

  /** 压缩图片并上传到云存储，返回临时访问 URL */
  _uploadImage(src) {
    return new Promise((resolve, reject) => {
      // 先压缩
      wx.compressImage({
        src,
        quality: 60,
        success: (compRes) => { resolve(compRes.tempFilePath) },
        fail: () => { resolve(src) },
      })
    }).then((filePath) => {
      return new Promise((resolve, reject) => {
        const cloudPath = 'ocr-temp/' + Date.now() + '-' + Math.random().toString(36).slice(2, 8) + '.jpg'
        wx.cloud.uploadFile({
          cloudPath,
          filePath,
          success: (res) => resolve(res.fileID),
          fail: (err) => reject(err),
        })
      })
    }).then((fileID) => {
      return new Promise((resolve, reject) => {
        wx.cloud.getTempFileURL({
          fileList: [fileID],
          success: (res) => {
            const fileItem = res.fileList[0]
            if (fileItem.status === 0 && fileItem.tempFileURL) {
              resolve({ url: fileItem.tempFileURL, fileID })
            } else {
              reject(new Error('获取临时 URL 失败'))
            }
          },
          fail: (err) => reject(err),
        })
      })
    })
  },

  /** 开始识别 */
  startRecognize() {
    this._clearPollTimer()
    this.setData({ step: 'loading' })

    this._uploadImage(this.data.imageSrc).then(({ url, fileID }) => {
      // 记录 fileID 以便后续清理
      this._tempFileID = fileID
      return api.post('/api/vocab/ocr-tasks', {
        image_url: url,
      })
    }).then(({ task_id }) => {
      return this._pollOCR(task_id)
    }).then((words) => {
      const normalized = (words || []).map((w, i) => ({
        ...w,
        idx: i,
      }))
      if (!normalized.length) {
        wx.showToast({ title: '未识别到单词', icon: 'none' })
        this.setData({ step: 'photo' })
        return
      }
      this.setData({ words: normalized, step: 'confirm' })
    }).catch((err) => {
      console.error('识别失败', err)
      const msg = (err && err.message) ? err.message : '识别失败，请重试'
      wx.showToast({ title: msg.length > 7 ? '识别失败，请稍后重试' : msg, icon: 'none' })
      this.setData({ step: 'photo' })
    })
  },

  /** 轮询后端 OCR 任务 */
  _pollOCR(taskId, attempt = 0) {
    const MAX_ATTEMPTS = 20
    return new Promise((resolve, reject) => {
      const poll = () => {
        api.get(`/api/vocab/ocr-tasks/${taskId}`).then((task) => {
          if (!task) {
            reject(new Error('任务不存在'))
            return
          }
          if (task.status === 'success') {
            resolve(task.words || [])
            return
          }
          if (task.status === 'error') {
            reject(new Error(task.error || '识别失败'))
            return
          }
          if (attempt >= MAX_ATTEMPTS) {
            reject(new Error('识别超时，请稍后重试'))
            return
          }
          attempt += 1
          this._pollTimer = setTimeout(poll, 1500)
        }).catch(reject)
      }
      poll()
    })
  },

  _clearPollTimer() {
    if (this._pollTimer) {
      clearTimeout(this._pollTimer)
      this._pollTimer = null
    }
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

  onUnload() {
    this._clearPollTimer()
  },
})
