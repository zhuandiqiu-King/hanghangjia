Component({
  properties: {
    plant: { type: Object, value: {} },
  },

  data: {
    statusText: '',
    statusClass: '',
  },

  lifetimes: {
    attached() {
      this.updateStatus()
    },
  },

  observers: {
    plant() {
      this.updateStatus()
    },
  },

  methods: {
    updateStatus() {
      const p = this.data.plant
      if (!p || !p.next_watering_date) return
      const today = new Date().toISOString().slice(0, 10)
      const next = p.next_watering_date
      if (next < today) {
        this.setData({ statusText: '需要浇水', statusClass: 'status-overdue' })
      } else if (next === today) {
        this.setData({ statusText: '今天浇水', statusClass: 'status-today' })
      } else {
        this.setData({ statusText: `${next} 浇水`, statusClass: 'status-ok' })
      }
    },

    onTap() {
      this.triggerEvent('tap', { id: this.data.plant.id })
    },
  },
})
