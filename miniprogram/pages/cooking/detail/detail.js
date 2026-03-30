const api = require('../../../utils/api')

const DIFFICULTY_MAP = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

const CATEGORY_MAP = {
  home: '家常菜', quick: '快手菜', soup: '汤羹', breakfast: '早餐',
  cold: '凉菜', baking: '烘焙', baby: '宝宝餐', diet: '减脂餐',
}

// 食材分类关键词（用于加入购物清单时自动分类）
const INGREDIENT_CATEGORY_KEYWORDS = {
  fresh: ['白菜', '菠菜', '西兰花', '黄瓜', '土豆', '胡萝卜', '西红柿', '番茄', '茄子', '青椒', '蒜苗', '葱', '姜', '蒜', '洋葱', '芹菜', '生菜', '香菜', '木耳', '蘑菇', '玉米', '豆腐', '苹果', '香蕉'],
  meat: ['猪肉', '牛肉', '鸡肉', '鸡胸', '鸡翅', '排骨', '五花肉', '里脊', '牛腩', '虾', '鱼', '鲫鱼', '鸡蛋', '鸭蛋', '牛奶', '火腿'],
  grain: ['大米', '面粉', '面条', '吐司', '燕麦', '小米', '酱油', '老抽', '醋', '盐', '糖', '冰糖', '料酒', '蚝油', '豆瓣酱', '甜面酱', '番茄酱', '淀粉', '花椒', '八角', '桂皮', '辣椒', '花椒粉', '食用油', '香油', '辣椒油'],
}

Page({
  data: {
    recipe: null,
    ingredientGroups: [],
    difficultyMap: DIFFICULTY_MAP,
    categoryMap: CATEGORY_MAP,
    showShoppingModal: false,
    shoppingItems: [], // 勾选的食材
  },

  onLoad(options) {
    if (options.id) {
      this.loadRecipe(options.id)
    }
  },

  loadRecipe(id) {
    wx.showLoading({ title: '加载中' })
    api.get(`/api/cooking/recipes/${id}`).then(res => {
      // 按 group_name 分组食材
      const groups = {}
      ;(res.ingredients || []).forEach(ing => {
        const group = ing.group_name || '主料'
        if (!groups[group]) groups[group] = []
        groups[group].push(ing)
      })
      const ingredientGroups = Object.keys(groups).map(name => ({
        name,
        items: groups[name],
      }))

      this.setData({ recipe: res, ingredientGroups })
      wx.setNavigationBarTitle({ title: res.name })
      wx.hideLoading()
    }).catch(err => {
      wx.hideLoading()
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    })
  },

  onFavoriteTap() {
    const recipe = this.data.recipe
    if (!recipe) return

    if (recipe.is_favorited) {
      api.del(`/api/cooking/favorites/${recipe.id}`).then(() => {
        this.setData({
          'recipe.is_favorited': false,
          'recipe.favorite_count': recipe.favorite_count - 1,
        })
      })
    } else {
      api.post(`/api/cooking/favorites/${recipe.id}`).then(() => {
        this.setData({
          'recipe.is_favorited': true,
          'recipe.favorite_count': recipe.favorite_count + 1,
        })
      })
    }
  },

  startCooking() {
    wx.navigateTo({
      url: `/pages/cooking/stepmode/stepmode?id=${this.data.recipe.id}`,
    })
  },

  // 缺料加购物清单
  showAddShopping() {
    const items = []
    this.data.ingredientGroups.forEach(group => {
      group.items.forEach(ing => {
        items.push({
          name: ing.name,
          amount: ing.amount,
          checked: true,
        })
      })
    })
    this.setData({ showShoppingModal: true, shoppingItems: items })
  },

  hideShoppingModal() {
    this.setData({ showShoppingModal: false })
  },

  toggleShoppingItem(e) {
    const idx = e.currentTarget.dataset.idx
    const key = `shoppingItems[${idx}].checked`
    this.setData({ [key]: !this.data.shoppingItems[idx].checked })
  },

  confirmAddShopping() {
    const selected = this.data.shoppingItems.filter(i => i.checked)
    if (selected.length === 0) {
      wx.showToast({ title: '请至少选择一项', icon: 'none' })
      return
    }

    const items = selected.map(i => ({
      name: i.name,
      quantity: i.amount || '',
      category: this.guessCategory(i.name),
    }))

    api.post('/api/cooking/add-to-shopping', { items }).then(res => {
      wx.showToast({ title: res.detail || '已添加', icon: 'success' })
      this.setData({ showShoppingModal: false })
    }).catch(err => {
      wx.showToast({ title: err.message || '添加失败', icon: 'none' })
    })
  },

  guessCategory(name) {
    for (const [cat, keywords] of Object.entries(INGREDIENT_CATEGORY_KEYWORDS)) {
      if (keywords.some(kw => name.includes(kw))) return cat
    }
    return 'other'
  },
})
