const api = require('../../../utils/api')
const tts = require('../../../utils/tts')

const innerAudioCtx = wx.createInnerAudioContext()
const recorderManager = wx.getRecorderManager()

Page({
  data: {
    bookId: 0,
    childId: 0,
    step: 'setup', // setup | doing
    // 设置
    direction: 'en2cn',
    mode: 'text',
    range: 'all',
    randomCount: 10,
    totalWords: 0,
    mistakeCount: 0,
    allWordIds: [],
    // 听写进行中
    words: [],
    currentIdx: 0,
    currentAnswer: '',
    answers: [],
    inputFocus: false,
    recording: false,
    voiceStatus: '', // playing | recording | recognizing
  },

  _voiceTimer: null,
  _stopped: false, // 页面已卸载标记

  onLoad(opts) {
    this.setData({
      bookId: parseInt(opts.book_id),
      childId: parseInt(opts.child_id),
    })
    if (opts.mistakes_only === '1') {
      this.setData({ range: 'mistakes' })
    }
    this._loadBookInfo()
    this._loadMistakeCount()
    this._initRecorder()
    this._initAudioEndListener()
  },

  onUnload() {
    this._stopped = true
    if (this._voiceTimer) clearTimeout(this._voiceTimer)
    innerAudioCtx.stop()
    innerAudioCtx.offEnded()
  },

  _loadBookInfo() {
    api.get(`/api/wordbooks/${this.data.bookId}`).then((data) => {
      const words = data.words || []
      this.setData({
        totalWords: words.length,
        allWordIds: words.map(w => w.id),
      })
    })
  },

  _loadMistakeCount() {
    api.get(`/api/children/${this.data.childId}/mistakes`).then((list) => {
      this.setData({ mistakeCount: list.length })
    }).catch(() => {})
  },

  _initRecorder() {
    recorderManager.onStop((res) => {
      this.setData({ recording: false })
      if (this._stopped) return
      // 点了"不会"触发的 stop
      if (this._skipAfterStop) {
        this._skipAfterStop = false
        this.setData({ currentAnswer: '' })
        this.nextWord()
        return
      }
      if (res.duration < 500) {
        // 录音太短，视为没说话，重播当前单词
        if (this.data.mode === 'voice') {
          this.setData({ voiceStatus: 'playing' })
          setTimeout(() => this.playWord(), 800)
        }
        return
      }
      this.setData({ voiceStatus: 'recognizing' })
      this._recognizeVoice(res.tempFilePath)
    })
    recorderManager.onError(() => {
      this.setData({ recording: false, voiceStatus: '' })
    })
  },

  /** TTS 播放结束后，语音模式自动开始录音 */
  _initAudioEndListener() {
    innerAudioCtx.onEnded(() => {
      if (this._stopped || this.data.mode !== 'voice' || this.data.step !== 'doing') return
      setTimeout(() => this._autoStartRecord(), 300)
    })
  },

  /** 自动开始录音 */
  _autoStartRecord() {
    if (this._stopped || this.data.recording) return
    wx.authorize({
      scope: 'scope.record',
      success: () => {
        this.setData({ recording: true, voiceStatus: 'recording' })
        recorderManager.start({
          duration: 5000,
          sampleRate: 16000,
          numberOfChannels: 1,
          encodeBitRate: 48000,
          format: 'mp3',
        })
      },
      fail: () => {
        wx.showToast({ title: '需要录音权限', icon: 'none' })
      },
    })
  },

  // ===== 设置 =====

  setDirection(e) { this.setData({ direction: e.currentTarget.dataset.val }) },
  setMode(e) { this.setData({ mode: e.currentTarget.dataset.val }) },
  setRange(e) { this.setData({ range: e.currentTarget.dataset.val }) },
  onCountInput(e) { this.setData({ randomCount: parseInt(e.detail.value) || 10 }) },

  startDictation() {
    const { childId, direction, mode, range, randomCount, allWordIds } = this.data
    const params = { mode, direction }

    if (range === 'mistakes') {
      params.mistakes_only = true
    } else if (range === 'all') {
      params.word_ids = allWordIds
    } else if (range === 'random') {
      params.word_ids = allWordIds
      params.count = randomCount
    }

    if (!params.word_ids && !params.mistakes_only) {
      wx.showToast({ title: '没有可听写的单词', icon: 'none' })
      return
    }

    wx.showLoading({ title: '准备中...' })
    api.post(`/api/children/${childId}/dictation/start`, params).then((data) => {
      wx.hideLoading()
      if (!data.words || !data.words.length) {
        wx.showToast({ title: '没有可听写的单词', icon: 'none' })
        return
      }

      // 拍照批改模式：跳转到 photo-check 页
      if (mode === 'photo') {
        wx.setStorageSync('photo_check_words', data.words)
        wx.navigateTo({
          url: `/pages/vocab/photo-check/photo-check?child_id=${childId}&book_id=${this.data.bookId}&direction=${direction}`,
        })
        return
      }

      this.setData({
        words: data.words,
        currentIdx: 0,
        currentAnswer: '',
        answers: [],
        step: 'doing',
        inputFocus: mode === 'text',
      })
      setTimeout(() => this.playWord(), 500)
    }).catch((err) => {
      wx.hideLoading()
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    })
  },

  // ===== 听写进行中 =====

  /** 播放当前单词 TTS（通过后端 edge-tts） */
  playWord() {
    const word = this.data.words[this.data.currentIdx]
    if (!word) return
    const text = this.data.direction === 'en2cn' ? word.english : word.chinese
    const lang = this.data.direction === 'en2cn' ? 'en_US' : 'zh_CN'

    if (this.data.mode === 'voice') {
      this.setData({ voiceStatus: 'playing' })
    }
    tts.speak(innerAudioCtx, text, lang).catch(() => {
      wx.showToast({ title: text, icon: 'none', duration: 2000 })
      // TTS 失败时，语音模式也要触发录音
      if (this.data.mode === 'voice') {
        setTimeout(() => this._autoStartRecord(), 1500)
      }
    })
  },

  onAnswerInput(e) {
    this.setData({ currentAnswer: e.detail.value })
  },

  nextWord() {
    if (this._voiceTimer) clearTimeout(this._voiceTimer)

    const { currentIdx, words, currentAnswer, answers, mode } = this.data
    const word = words[currentIdx]
    const newAnswers = [...answers, { word_id: word.id, answer: currentAnswer.trim() }]

    if (currentIdx < words.length - 1) {
      this.setData({
        answers: newAnswers,
        currentIdx: currentIdx + 1,
        currentAnswer: '',
        inputFocus: false,
        voiceStatus: '',
      })
      setTimeout(() => {
        this.setData({ inputFocus: mode === 'text' })
        this.playWord()
      }, 300)
    } else {
      this.setData({ voiceStatus: '' })
      this._submitResults(newAnswers)
    }
  },

  /** 不会：记空答案，跳到下一个 */
  skipWord() {
    if (this._voiceTimer) clearTimeout(this._voiceTimer)
    // 如果正在录音，先停掉
    if (this.data.recording) {
      this._skipAfterStop = true
      recorderManager.stop()
      return
    }
    this.setData({ currentAnswer: '' })
    this.nextWord()
  },

  _submitResults(answers) {
    const { words, direction, childId, bookId, mode } = this.data

    const results = answers.map((a) => {
      const word = words.find(w => w.id === a.word_id)
      if (!word) return { ...a, is_correct: false }

      const expected = direction === 'en2cn' ? word.chinese : word.english
      const userAns = a.answer.toLowerCase().trim()
      const exp = expected.toLowerCase().trim()
      const is_correct = userAns.length > 0 && (userAns === exp || exp.includes(userAns))

      return { word_id: a.word_id, answer: a.answer, is_correct }
    })

    wx.showLoading({ title: '提交中...' })
    api.request({
      url: `/api/children/${childId}/dictation/submit?book_id=${bookId}&mode=${mode}&direction=${direction}`,
      method: 'POST',
      data: { results },
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

  // ===== 语音输入 =====

  /** 手动停止录音（用户提前结束） */
  stopRecording() {
    if (this.data.recording) {
      recorderManager.stop()
    }
  },

  /** 语音识别：上传云存储 → 获取临时URL → 后端识别 */
  _recognizeVoice(filePath) {
    const cloudPath = `voice/${Date.now()}-${Math.random().toString(36).slice(2)}.mp3`

    wx.cloud.uploadFile({
      cloudPath,
      filePath,
      success: (uploadRes) => {
        wx.cloud.getTempFileURL({
          fileList: [uploadRes.fileID],
          success: (urlRes) => {
            const audioUrl = urlRes.fileList[0].tempFileURL
            api.request({
              url: '/api/chat/voice',
              method: 'POST',
              data: { audio_url: audioUrl },
              timeout: 30000,
            }).then((data) => {
              if (this._stopped) return
              const text = (data.text || '').replace(/[。，！？,.!?]/g, '').trim()
              // 说了"不会"等跳过关键词
              if (text && /^(不会|不知道|跳过|过|pass)$/i.test(text)) {
                this.setData({ currentAnswer: '', voiceStatus: '' })
                this.nextWord()
                return
              }
              if (text) {
                this.setData({ currentAnswer: text, voiceStatus: '' })
                // 识别成功，1.5秒后自动下一个
                if (this._voiceTimer) clearTimeout(this._voiceTimer)
                this._voiceTimer = setTimeout(() => this.nextWord(), 1500)
              } else {
                // 没识别到内容，自动重播当前单词
                wx.showToast({ title: '没听清，再来一次', icon: 'none', duration: 1000 })
                this.setData({ voiceStatus: '' })
                setTimeout(() => this.playWord(), 1200)
              }
            }).catch(() => {
              this.setData({ voiceStatus: '' })
              wx.showToast({ title: '识别失败', icon: 'none', duration: 1000 })
              setTimeout(() => this.playWord(), 1200)
            })
          },
          fail: () => {
            this.setData({ voiceStatus: '' })
            wx.showToast({ title: '上传失败', icon: 'none' })
          },
        })
      },
      fail: () => {
        this.setData({ voiceStatus: '' })
        wx.showToast({ title: '上传失败', icon: 'none' })
      },
    })
  },
})
