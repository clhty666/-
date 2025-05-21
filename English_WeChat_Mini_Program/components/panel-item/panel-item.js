// components/panel-item/panel-item.js
Component({
  properties: {
    title: String,
    data: Array
  },

  data: {
    processedData: []
  },
  observers: {
    'data': function(newVal) {
      this.processData(newVal)
    }
  },
  methods: {
    processData(rawData) {
      const processed = (rawData || []).map(item => {
        const displayText = this.getDisplayText(item)
        return {
          ...item,
          collapsed: true,  // 默认折叠状态
          displayText: displayText
        }
      })
      this.setData({ processedData: processed })
    },
    getDisplayText(item) {
      switch (this.properties.title) {
        case '翻译': 
          return item || ''
        case '例句':
          return item || ''
        case '短语':
          return item || ''
        case '同根词':
          return item || ''
        default:
          return ''
      }
    },
    toggleCollapse(e) {
      const index = e.currentTarget.dataset.index
      const key = `processedData[${index}].collapsed`
      this.setData({
        [key]: !this.data.processedData[index].collapsed
      })
    }
  }
})