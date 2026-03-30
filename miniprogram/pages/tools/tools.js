Page({
  data: {
    categories: [
      {
        id: 'task',
        name: '任务管理',
        icon: '📋',
        tools: [
          {
            id: 'plants',
            name: '浇水提醒',
            icon: '💧',
            desc: '植物浇水管理',
            active: true,
            url: '/pages/plant/index/index',
          },
          {
            id: 'study_plan',
            name: '学习计划',
            icon: '📖',
            desc: '制定学习目标',
            active: false,
          },
          {
            id: 'shopping',
            name: '购买清单',
            icon: '🛒',
            desc: '家庭购物清单',
            active: true,
            url: '/pages/shopping/index/index',
          },
        ],
      },
      {
        id: 'resource',
        name: '资源管理',
        icon: '📁',
        tools: [
          {
            id: 'album',
            name: '家庭相册',
            icon: '📷',
            desc: '共享家庭照片',
            active: false,
          },
          {
            id: 'finance',
            name: '财务记账',
            icon: '💰',
            desc: '家庭收支管理',
            active: false,
          },
        ],
      },
      {
        id: 'study',
        name: '学习工具',
        icon: '📚',
        tools: [
          {
            id: 'vocabulary',
            name: '背单词',
            icon: '🔤',
            desc: '单词听写与复习',
            active: true,
            url: '/pages/vocab/index/index',
          },
          {
            id: 'math',
            name: '口算练习',
            icon: '🔢',
            desc: '数学口算训练',
            active: false,
          },
        ],
      },
      {
        id: 'life',
        name: '生活工具',
        icon: '🏠',
        tools: [
          {
            id: 'cooking',
            name: '烹饪助手',
            icon: '🍳',
            desc: '菜谱与烹饪指导',
            active: true,
            url: '/pages/cooking/index/index',
          },
        ],
      },
    ],
  },

  handleTap(e) {
    const id = e.currentTarget.dataset.id
    let target = null
    for (const cat of this.data.categories) {
      target = cat.tools.find(t => t.id === id)
      if (target) break
    }
    if (!target) return
    if (!target.active) {
      wx.showToast({ title: '功能开发中，敬请期待', icon: 'none' })
      return
    }
    // 需要登录才能使用工具
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '登录后才能使用该功能，是否前往登录？',
        confirmText: '去登录',
        success(res) {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' })
          }
        },
      })
      return
    }
    wx.navigateTo({ url: target.url })
  },
})
