const api = require('../../../utils/api')
const tts = require('../../../utils/tts')

const innerAudioCtx = wx.createInnerAudioContext()

Page({
  data: {
    childId: 0,
    bookId: 0,
    direction: 'en2cn',
    words: [],       // 本次听写的单词列表
    step: 'play',    // play | photo | checking | result
    playIdx: 0,
    imageSrc: '',
    results: [],
    correct: 0,
    total: 0,
  },

  _playTimer: null,

  onLoad(opts) {
    this.setData({
      childId: parseInt(opts.child_id),
      bookId: parseInt(opts.book_id),
      direction: opts.direction || 'en2cn',
    })
    // 单词列表从上一页传过来（存 storage）
    const words = wx.getStorageSync('photo_check_words') || []
    this.setData({ words, total: words.length })
    // 开始自动播报
    if (words.length) {
      setTimeout(() => this._playNext(0), 500)
    }
  },

  onUnload() {
    if (this._playTimer) clearTimeout(this._playTimer)
    innerAudioCtx.stop()
  },

  // ===== 播报 =====

  _playNext(idx) {
    if (idx >= this.data.words.length) return
    this.setData({ playIdx: idx })

    const word = this.data.words[idx]
    const text = this.data.direction === 'en2cn' ? word.english : word.chinese
    const lang = this.data.direction === 'en2cn' ? 'en_US' : 'zh_CN'

    tts.speak(innerAudioCtx, text, lang).then(() => {
      // 播放完后延迟播下一个
      innerAudioCtx.onEnded(() => {
        innerAudioCtx.offEnded()
        this._playTimer = setTimeout(() => {
          this._playNext(idx + 1)
        }, 2000)
      })
    }).catch(() => {
      // 降级：用 toast 显示
      wx.showToast({ title: `第${idx + 1}个: ${text}`, icon: 'none', duration: 2000 })
      this._playTimer = setTimeout(() => this._playNext(idx + 1), 2500)
    })
  },

  replayAll() {
    if (this._playTimer) clearTimeout(this._playTimer)
    this._playNext(0)
  },

  finishPlay() {
    if (this._playTimer) clearTimeout(this._playTimer)
    innerAudioCtx.stop()
    this.setData({ step: 'photo' })
  },

  // ===== 拍照 =====

  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({ imageSrc: res.tempFiles[0].tempFilePath })
      },
    })
  },

  startCheck() {
    this.setData({ step: 'checking' })

    const fs = wx.getFileSystemManager()
    fs.readFile({
      filePath: this.data.imageSrc,
      encoding: 'base64',
      success: (res) => {
        const wordsPayload = this.data.words.map(w => ({
          id: w.id,
          english: w.english,
          chinese: w.chinese,
        }))

        api.request({
          url: '/api/vocab/photo-check',
          method: 'POST',
          data: {
            image: res.data,
            words: wordsPayload,
            direction: this.data.direction,
          },
          timeout: 60000,
        }).then((data) => {
          this.setData({
            results: data.results || [],
            correct: data.correct || 0,
            total: data.total || 0,
            step: 'result',
          })
        }).catch((err) => {
          console.error('批改失败', err)
          wx.showToast({ title: '批改失败，请重试', icon: 'none' })
          this.setData({ step: 'photo' })
        })
      },
      fail: () => {
        wx.showToast({ title: '读取图片失败', icon: 'none' })
        this.setData({ step: 'photo' })
      },
    })
  },

  // ===== 结果修正 =====

  /** 切换对错状态 */
  toggleCorrect(e) {
    const idx = e.currentTarget.dataset.idx
    const results = [...this.data.results]
    results[idx].is_correct = !results[idx].is_correct
    const correct = results.filter(r => r.is_correct).length
    this.setData({ results, correct })
  },

  /** 编辑识别结果 */
  onEditAnswer(e) {
    const idx = e.currentTarget.dataset.idx
    const results = [...this.data.results]
    results[idx].user_answer = e.detail.value
    this.setData({ results })
  },

  /** 重新拍照 */
  rePhoto() {
    this.setData({ step: 'photo', imageSrc: '', results: [] })
  },

  /** 确认提交 */
  submitResults() {
    const { childId, bookId, direction, results } = this.data

    const submitData = results.map(r => ({
      word_id: r.word_id,
      answer: r.user_answer || '',
      is_correct: r.is_correct,
    }))

    wx.showLoading({ title: '提交中...' })
    api.request({
      url: `/api/children/${childId}/dictation/submit?book_id=${bookId}&mode=photo&direction=${direction}`,
      method: 'POST',
      data: { results: submitData },
    }).then((session) => {
      wx.hideLoading()
      const sessionData = encodeURIComponent(JSON.stringify(session))
      wx.redirectTo({
        url: `/pages/vocab/result/result?data=${sessionData}`,
      })
    }).catch(() => {
      wx.hideLoading()
      wx.showToast({ title: '提交失败', icon: 'none' })
    })
  },
})
