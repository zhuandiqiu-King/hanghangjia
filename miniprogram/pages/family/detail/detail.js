const api = require('../../../utils/api')
const { isEmojiAvatar, getEmoji, hasRealAvatar } = require('../../../utils/avatar')

Page({
  data: {
    familyId: null,
    family: null,
    members: [],
    isAdmin: false,
    loading: true,
  },

  onLoad(options) {
    this.setData({ familyId: Number(options.id) })
  },

  onShow() {
    this.loadDetail()
  },

  async loadDetail() {
    try {
      const data = await api.get(`/api/family/${this.data.familyId}`)
      const members = (data.members || []).map((m) => ({
        ...m,
        isEmoji: isEmojiAvatar(m.avatar_url),
        emoji: getEmoji(m.avatar_url),
        realAvatar: hasRealAvatar(m.avatar_url),
      }))
      this.setData({
        family: data,
        members,
        isAdmin: data.my_role === 'admin',
        loading: false,
      })
    } catch (err) {
      console.error('加载家庭详情失败', err)
      this.setData({ loading: false })
    }
  },

  // 邀请成员 — 生成邀请码后分享
  async handleInvite() {
    try {
      const res = await api.post(`/api/family/${this.data.familyId}/invite`)
      this._inviteCode = res.invite_code
      // 触发转发分享
      wx.showModal({
        title: '邀请成功',
        content: `邀请码：${res.invite_code}\n有效期 24 小时\n\n点击右上角 ··· 按钮将本页分享给家人即可加入`,
        showCancel: false,
      })
    } catch (err) {
      wx.showToast({ title: '生成邀请码失败', icon: 'none' })
    }
  },

  // 分享小程序卡片
  onShareAppMessage() {
    const code = this._inviteCode || ''
    const name = this.data.family ? this.data.family.name : '我的家庭'
    return {
      title: `邀请你加入「${name}」`,
      path: `/pages/family/join/join?code=${code}`,
      imageUrl: '',
    }
  },

  // 移除成员
  handleRemove(e) {
    const userId = e.currentTarget.dataset.uid
    const nickname = e.currentTarget.dataset.name
    wx.showModal({
      title: '移除成员',
      content: `确定移除 ${nickname} 吗？`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/api/family/${this.data.familyId}/members/${userId}`)
          wx.showToast({ title: '已移除', icon: 'success' })
          this.loadDetail()
        } catch (err) {
          wx.showModal({
            title: '操作失败',
            content: err.message || '移除成员失败',
            showCancel: false,
          })
        }
      },
    })
  },

  // 转让管理员
  handleTransfer(e) {
    const userId = e.currentTarget.dataset.uid
    const nickname = e.currentTarget.dataset.name
    wx.showModal({
      title: '转让管理员',
      content: `确定将管理员转让给 ${nickname} 吗？转让后你将变为普通成员。`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.post(`/api/family/${this.data.familyId}/transfer`, {
            target_user_id: userId,
          })
          wx.showToast({ title: '已转让', icon: 'success' })
          this.loadDetail()
        } catch (err) {
          wx.showToast({ title: '转让失败', icon: 'none' })
        }
      },
    })
  },

  // 退出家庭
  handleLeave() {
    wx.showModal({
      title: '退出家庭',
      content: '确定退出该家庭吗？退出后将无法看到共享内容。',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.post(`/api/family/${this.data.familyId}/leave`)
          wx.showToast({ title: '已退出', icon: 'success' })
          // 刷新全局家庭信息
          const families = await api.get('/api/family')
          const app = getApp()
          if (families.length) {
            app.globalData.currentFamilyId = families[0].id
            app.globalData.currentFamilyName = families[0].name
          }
          wx.navigateBack()
        } catch (err) {
          wx.showModal({
            title: '无法退出',
            content: err.message || '退出失败',
            showCancel: false,
          })
        }
      },
    })
  },

  // 解散家庭
  handleDissolve() {
    wx.showModal({
      title: '解散家庭',
      content: '确定解散该家庭吗？所有植物将转移到你的个人空间。此操作不可撤销。',
      confirmColor: '#E74C3C',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/api/family/${this.data.familyId}`)
          wx.showToast({ title: '已解散', icon: 'success' })
          const families = await api.get('/api/family')
          const app = getApp()
          if (families.length) {
            app.globalData.currentFamilyId = families[0].id
            app.globalData.currentFamilyName = families[0].name
          }
          wx.navigateBack()
        } catch (err) {
          wx.showToast({ title: '解散失败', icon: 'none' })
        }
      },
    })
  },

  // 修改家庭名
  handleRename() {
    wx.showModal({
      title: '修改家庭名称',
      editable: true,
      placeholderText: this.data.family.name,
      success: async (res) => {
        if (!res.confirm || !res.content || !res.content.trim()) return
        try {
          await api.put(`/api/family/${this.data.familyId}`, {
            name: res.content.trim(),
          })
          wx.showToast({ title: '已修改', icon: 'success' })
          this.loadDetail()
        } catch (err) {
          wx.showToast({ title: '修改失败', icon: 'none' })
        }
      },
    })
  },
})
