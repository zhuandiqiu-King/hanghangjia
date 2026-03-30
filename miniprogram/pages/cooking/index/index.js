const api = require('../../../utils/api')

const CATEGORY_LIST = [
  { id: 'home', name: '家常菜', icon: '🏠' },
  { id: 'quick', name: '快手菜', icon: '⚡' },
  { id: 'soup', name: '汤羹', icon: '🍲' },
  { id: 'breakfast', name: '早餐', icon: '🌅' },
  { id: 'cold', name: '凉菜', icon: '🥗' },
  { id: 'baking', name: '烘焙', icon: '🍞' },
  { id: 'baby', name: '宝宝餐', icon: '👶' },
  { id: 'diet', name: '减脂餐', icon: '🥑' },
]

const DIFFICULTY_MAP = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

Page({
  data: {
    categories: CATEGORY_LIST,
    recipes: [],
    keyword: '',
    activeCategory: '',
    page: 1,
    hasMore: true,
    loading: false,
    difficultyMap: DIFFICULTY_MAP,
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '登录后才能使用此功能',
        confirmText: '去登录',
        cancelText: '返回',
        success(res) {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' })
          } else {
            wx.navigateBack()
          }
        },
      })
      return
    }
    // 每次显示刷新（可能收藏状态变了）
    this.setData({ page: 1, recipes: [], hasMore: true })
    this.loadRecipes()
  },

  loadRecipes() {
    if (this.data.loading || !this.data.hasMore) return
    this.setData({ loading: true })

    let url = `/api/cooking/recipes?page=${this.data.page}&page_size=20`
    if (this.data.keyword) url += `&keyword=${encodeURIComponent(this.data.keyword)}`
    if (this.data.activeCategory) url += `&category=${this.data.activeCategory}`

    api.get(url).then(res => {
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

  onSearch(e) {
    this.setData({
      keyword: e.detail.value,
      page: 1,
      recipes: [],
      hasMore: true,
    })
    this.loadRecipes()
  },

  onCategoryTap(e) {
    const id = e.currentTarget.dataset.id
    this.setData({
      activeCategory: this.data.activeCategory === id ? '' : id,
      page: 1,
      recipes: [],
      hasMore: true,
    })
    this.loadRecipes()
  },

  onRecipeTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/cooking/detail/detail?id=${id}` })
  },

  onFavoriteTap(e) {
    const id = e.currentTarget.dataset.id
    const recipe = this.data.recipes.find(r => r.id === id)
    if (!recipe) return

    if (recipe.is_favorited) {
      api.del(`/api/cooking/favorites/${id}`).then(() => {
        this.updateRecipeFavorite(id, false)
      })
    } else {
      api.post(`/api/cooking/favorites/${id}`).then(() => {
        this.updateRecipeFavorite(id, true)
      })
    }
  },

  updateRecipeFavorite(id, favorited) {
    const recipes = this.data.recipes.map(r => {
      if (r.id === id) {
        return {
          ...r,
          is_favorited: favorited,
          favorite_count: r.favorite_count + (favorited ? 1 : -1),
        }
      }
      return r
    })
    this.setData({ recipes })
  },

  goFavorites() {
    wx.navigateTo({ url: '/pages/cooking/favorites/favorites' })
  },

  onReachBottom() {
    this.loadRecipes()
  },
})
