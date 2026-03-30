const api = require('../../../utils/api')

const DIFFICULTY_MAP = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

Page({
  data: {
    recipes: [],
    page: 1,
    hasMore: true,
    loading: false,
    difficultyMap: DIFFICULTY_MAP,
  },

  onShow() {
    // 每次显示刷新
    this.setData({ page: 1, recipes: [], hasMore: true })
    this.loadFavorites()
  },

  loadFavorites() {
    if (this.data.loading || !this.data.hasMore) return
    this.setData({ loading: true })

    api.get(`/api/cooking/favorites?page=${this.data.page}&page_size=20`).then(res => {
      const newRecipes = this.data.recipes.concat(res)
      this.setData({
        recipes: newRecipes,
        hasMore: res.length >= 20,
        page: this.data.page + 1,
        loading: false,
      })
    }).catch(() => {
      this.setData({ loading: false })
    })
  },

  onRecipeTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/cooking/detail/detail?id=${id}` })
  },

  onLongPress(e) {
    const id = e.currentTarget.dataset.id
    const name = e.currentTarget.dataset.name
    wx.showActionSheet({
      itemList: ['取消收藏'],
      success: (res) => {
        if (res.tapIndex === 0) {
          api.del(`/api/cooking/favorites/${id}`).then(() => {
            const recipes = this.data.recipes.filter(r => r.id !== id)
            this.setData({ recipes })
            wx.showToast({ title: '已取消收藏', icon: 'success' })
          })
        }
      },
    })
  },

  onReachBottom() {
    this.loadFavorites()
  },
})
