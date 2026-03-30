const api = require('../../../utils/api')

Page({
  data: {
    recipe: null,
    steps: [],
    currentStep: 0,
    totalSteps: 0,
    startX: 0,
  },

  onLoad(options) {
    // 保持屏幕常亮
    wx.setKeepScreenOn({ keepScreenOn: true })

    if (options.id) {
      this.loadRecipe(options.id)
    }
  },

  onUnload() {
    // 退出时关闭屏幕常亮
    wx.setKeepScreenOn({ keepScreenOn: false })
  },

  loadRecipe(id) {
    api.get(`/api/cooking/recipes/${id}`).then(res => {
      const steps = (res.steps || []).sort((a, b) => a.step_number - b.step_number)
      this.setData({
        recipe: res,
        steps,
        totalSteps: steps.length,
        currentStep: 0,
      })
    })
  },

  prevStep() {
    if (this.data.currentStep > 0) {
      this.setData({ currentStep: this.data.currentStep - 1 })
    }
  },

  nextStep() {
    if (this.data.currentStep < this.data.totalSteps - 1) {
      this.setData({ currentStep: this.data.currentStep + 1 })
    } else {
      // 最后一步，完成
      this.onComplete()
    }
  },

  onComplete() {
    wx.showToast({
      title: '做好啦！',
      icon: 'success',
      duration: 1500,
    })
    setTimeout(() => {
      wx.navigateBack()
    }, 1500)
  },

  exitStepMode() {
    wx.navigateBack()
  },

  // 滑动手势
  onTouchStart(e) {
    this.setData({ startX: e.touches[0].clientX })
  },

  onTouchEnd(e) {
    const endX = e.changedTouches[0].clientX
    const diff = endX - this.data.startX
    if (Math.abs(diff) < 50) return // 滑动距离太小忽略

    if (diff > 0) {
      this.prevStep()
    } else {
      this.nextStep()
    }
  },
})
