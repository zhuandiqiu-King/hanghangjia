const api = require('../../../utils/api')

// 分类配置
const CATEGORIES = {
  fresh:  { icon: '🥬', name: '生鲜果蔬', order: 1 },
  meat:   { icon: '🥩', name: '肉禽蛋奶', order: 2 },
  grain:  { icon: '🍚', name: '粮油调味', order: 3 },
  snack:  { icon: '🍪', name: '零食饮料', order: 4 },
  daily:  { icon: '🧴', name: '日用百货', order: 5 },
  other:  { icon: '📦', name: '其他',     order: 6 },
}

// 关键词 → 分类映射
const KEYWORD_MAP = {
  fresh: ['白菜','菠菜','生菜','西兰花','芹菜','韭菜','黄瓜','西红柿','番茄','土豆','茄子','辣椒','青椒','胡萝卜','萝卜','洋葱','大蒜','蒜','姜','葱','香菜','豆芽','玉米','南瓜','冬瓜','苹果','香蕉','橙子','橘子','葡萄','草莓','西瓜','桃子','梨','芒果','猕猴桃','柠檬','樱桃','蓝莓','荔枝','龙眼','菠萝','木瓜','柚子','火龙果','豆腐','豆角','蘑菇','香菇','金针菇'],
  meat: ['猪肉','牛肉','羊肉','鸡肉','鸭肉','排骨','五花肉','肉馅','肉','鸡翅','鸡腿','鸡蛋','鸭蛋','鹌鹑蛋','虾','鱼','虾仁','螃蟹','牛奶','酸奶','奶酪','黄油','鲜奶','纯奶'],
  grain: ['大米','米','面粉','面条','挂面','方便面','油','花生油','橄榄油','酱油','醋','盐','糖','白糖','冰糖','料酒','蚝油','豆瓣酱','番茄酱','芝麻酱','淀粉','味精','鸡精','八角','花椒','十三香','五香粉','咖喱'],
  snack: ['饼干','薯片','巧克力','糖果','坚果','瓜子','花生','蛋糕','面包片','可乐','雪碧','果汁','矿泉水','茶','咖啡','奶茶','冰淇淋','果冻','海苔','肉干','牛肉干','话梅','果脯'],
  daily: ['洗洁精','洗衣液','洗衣粉','柔顺剂','纸巾','卫生纸','抽纸','湿巾','牙膏','牙刷','洗发水','沐浴露','护手霜','洗手液','香皂','肥皂','垃圾袋','保鲜膜','保鲜袋','拖把','抹布','海绵','电池','灯泡','衣架'],
}

// 分类选项（供弹窗 picker 使用）
const CATEGORY_OPTIONS = Object.entries(CATEGORIES).map(([key, cfg]) => ({
  key, icon: cfg.icon, name: `${cfg.icon} ${cfg.name}`,
}))

const UNIT_OPTIONS = ['个', '斤', '克', '瓶', '盒', '袋', '包', '箱']

function guessCategory(name) {
  for (const [cat, keywords] of Object.entries(KEYWORD_MAP)) {
    if (keywords.some(kw => name.includes(kw))) return cat
  }
  return 'other'
}

function guessCategoryIndex(name) {
  const cat = guessCategory(name)
  const idx = CATEGORY_OPTIONS.findIndex(o => o.key === cat)
  return idx >= 0 ? idx : CATEGORY_OPTIONS.length - 1
}

Page({
  data: {
    loading: true,
    inputValue: '',
    listId: null,
    unboughtItems: [],
    boughtItems: [],
    categoryGroups: [],
    // 弹窗
    showAddModal: false,
    unitOptions: UNIT_OPTIONS,
    categoryOptions: CATEGORY_OPTIONS,
    form: {
      name: '',
      quantityNum: '',
      unitIndex: 0,
      price: '',
      categoryIndex: 5, // 默认"其他"
      note: '',
    },
    // AI 智能拆分
    showSmartModal: false,
    smartItems: [],
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/api/shopping/current')
      const items = res.items || []
      this.processItems(items)
      this.setData({ listId: res.id, loading: false })
    } catch (err) {
      console.error('加载购物清单失败', err)
      this.setData({ loading: false })
    }
  },

  // 将商品分为未买/已买，未买按分类分组
  processItems(items) {
    const unbought = items.filter(i => !i.is_bought)
    const bought = items.filter(i => i.is_bought)

    // 按分类分组
    const groups = Object.entries(CATEGORIES).map(([key, cfg]) => ({
      key,
      icon: cfg.icon,
      name: cfg.name,
      order: cfg.order,
      items: unbought.filter(i => i.category === key),
    })).sort((a, b) => a.order - b.order)

    this.setData({
      unboughtItems: unbought,
      boughtItems: bought,
      categoryGroups: groups,
    })
  },

  onInput(e) {
    this.setData({ inputValue: e.detail.value })
  },

  // 快速添加（逗号分隔）
  async handleQuickAdd() {
    const raw = this.data.inputValue.trim()
    if (!raw) return

    // 支持中英文逗号、顿号分隔
    const names = raw.split(/[,，、]/).map(s => s.trim()).filter(Boolean)
    if (names.length === 0) return

    const items = names.map(name => ({
      name,
      category: guessCategory(name),
    }))

    this.setData({ inputValue: '' })
    try {
      await api.post('/api/shopping/items', { items })
      wx.showToast({ title: `已添加 ${items.length} 件`, icon: 'none' })
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '添加失败', icon: 'none' })
    }
  },

  // 标记已买
  async handleBuy(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.put(`/api/shopping/items/${id}/buy`)
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 取消已买
  async handleUnbuy(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.put(`/api/shopping/items/${id}/unbuy`)
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 删除商品
  handleDelete(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个商品吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.del(`/api/shopping/items/${id}`)
            this.loadData()
          } catch (err) {
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      },
    })
  },

  // 归档已买
  handleArchive() {
    wx.showModal({
      title: '清空已买',
      content: '已买的商品将归入历史记录，确定清空吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.post('/api/shopping/archive')
            wx.showToast({ title: '已清空', icon: 'none' })
            this.loadData()
          } catch (err) {
            wx.showToast({ title: err.message || '操作失败', icon: 'none' })
          }
        }
      },
    })
  },

  // 一键复制清单
  handleCopyList() {
    const groups = this.data.categoryGroups.filter(g => g.items.length > 0)
    let text = '📋 购物清单\n'
    for (const g of groups) {
      text += `\n${g.icon} ${g.name}\n`
      for (const item of g.items) {
        let line = `○ ${item.name}`
        if (item.quantity) line += `  ${item.quantity}`
        if (item.price) line += `  ¥${item.price}`
        text += line + '\n'
      }
    }
    wx.setClipboardData({
      data: text,
      success: () => wx.showToast({ title: '已复制', icon: 'none' }),
    })
  },

  // ---- 添加商品弹窗 ----

  openAddModal() {
    this.setData({
      showAddModal: true,
      form: { name: '', quantityNum: '', unitIndex: 0, price: '', categoryIndex: 5, note: '' },
    })
  },

  closeAddModal() {
    this.setData({ showAddModal: false })
  },

  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
    // 名称变化时自动推测分类
    if (field === 'name') {
      this.setData({ 'form.categoryIndex': guessCategoryIndex(e.detail.value) })
    }
  },

  onUnitChange(e) {
    this.setData({ 'form.unitIndex': Number(e.detail.value) })
  },

  onCategoryChange(e) {
    this.setData({ 'form.categoryIndex': Number(e.detail.value) })
  },

  async handleFormAdd() {
    const { form, unitOptions, categoryOptions } = this.data
    const name = (form.name || '').trim()
    if (!name) {
      wx.showToast({ title: '请输入商品名称', icon: 'none' })
      return
    }
    const quantity = form.quantityNum ? `${form.quantityNum}${unitOptions[form.unitIndex]}` : null
    const price = form.price ? parseFloat(form.price) : null
    const category = categoryOptions[form.categoryIndex].key

    try {
      await api.post('/api/shopping/items', {
        items: [{ name, quantity, price, category, note: form.note || null }],
      })
      wx.showToast({ title: '已添加', icon: 'none' })
      this.closeAddModal()
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '添加失败', icon: 'none' })
    }
  },

  // ---- AI 智能拆分 ----

  async handleSmartAdd() {
    const text = this.data.inputValue.trim()
    if (!text) {
      wx.showToast({ title: '请先输入内容，如"做红烧肉需要什么"', icon: 'none' })
      return
    }
    wx.showLoading({ title: 'AI 分析中...' })
    try {
      const res = await api.post('/api/shopping/smart-add', { text })
      wx.hideLoading()
      if (!res.items || res.items.length === 0) {
        wx.showToast({ title: 'AI 未识别出商品', icon: 'none' })
        return
      }
      const smartItems = res.items.map(i => ({ ...i, checked: true }))
      this.setData({ showSmartModal: true, smartItems })
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || 'AI 拆分失败', icon: 'none' })
    }
  },

  toggleSmartItem(e) {
    const index = e.currentTarget.dataset.index
    const key = `smartItems[${index}].checked`
    this.setData({ [key]: !this.data.smartItems[index].checked })
  },

  closeSmartModal() {
    this.setData({ showSmartModal: false, smartItems: [] })
  },

  async handleSmartConfirm() {
    const selected = this.data.smartItems.filter(i => i.checked)
    if (selected.length === 0) {
      wx.showToast({ title: '请至少选择一个商品', icon: 'none' })
      return
    }
    try {
      await api.post('/api/shopping/items', {
        items: selected.map(i => ({
          name: i.name,
          quantity: i.quantity || null,
          category: i.category || 'other',
        })),
      })
      wx.showToast({ title: `已添加 ${selected.length} 件`, icon: 'none' })
      this.setData({ inputValue: '' })
      this.closeSmartModal()
      this.loadData()
    } catch (err) {
      wx.showToast({ title: '添加失败', icon: 'none' })
    }
  },

  // ---- 页面跳转 ----

  goHistory() {
    wx.navigateTo({ url: '/pages/shopping/history/history' })
  },

  goFrequent() {
    wx.navigateTo({ url: '/pages/shopping/frequent/frequent' })
  },
})
