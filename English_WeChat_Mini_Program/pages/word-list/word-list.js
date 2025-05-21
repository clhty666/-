// pages/word-list/word-list.js
import { api } from '../../utils/api'

Page({
  data: {
    words: [],
    isLoading: true
  },

  onLoad(options) {
    this.bookId = options.book_id
    this.loadWords()
    console.log('接收到的参数:', options)  // 查看控制台是否有book_id
    if (!options.book_id) {
      wx.showToast({ title: '参数缺失', icon: 'none' })
    }
  },

  async loadWords() {
    try {
      const res = await api.getLibraryWords(this.bookId)
      this.setData({ 
        words: res,
        isLoading: false
      })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ isLoading: false })
    }
  }
})