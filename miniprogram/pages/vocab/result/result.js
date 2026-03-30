Page({
  data: {
    total: 0,
    correct: 0,
    accuracy: 0,
    scoreMsg: '',
    results: [],
    wrongCount: 0,
  },

  onLoad(opts) {
    try {
      const session = JSON.parse(decodeURIComponent(opts.data))
      const total = session.total || 0
      const correct = session.correct || 0
      const accuracy = total > 0 ? Math.round(correct / total * 100) : 0
      const wrongCount = total - correct

      let scoreMsg = ''
      if (accuracy === 100) scoreMsg = '太棒了！全对！'
      else if (accuracy >= 80) scoreMsg = '很不错，继续加油！'
      else if (accuracy >= 60) scoreMsg = '还可以，再练练就好了'
      else scoreMsg = '需要多复习哦～'

      this.setData({
        total,
        correct,
        accuracy,
        scoreMsg,
        results: session.results || [],
        wrongCount,
      })
    } catch (e) {
      console.error('解析结果失败', e)
    }
  },

  goBack() {
    wx.navigateBack({ delta: 2 })
  },

  retryWrong() {
    // 返回上一页重新听写（暂时返回单词本）
    wx.navigateBack({ delta: 2 })
  },
})
