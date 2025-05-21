// pages/library/library.js
import { api } from '../../utils/api'

Page({
  data: {
    libraries: [],       // 所有可用词库
    selectedLib: ''      // 当前选中词库
  },

  onLoad() {
    this.loadLibraries()
    this.getCurrentLib()
  },

  // 加载所有词库
  async loadLibraries() {
    try {
      const libraries = await api.getLibraries()
      this.setData({ libraries })
    } catch (err) {
      console.error('加载词库失败:', err)
    }
  },

  // 获取当前选择的词库
  async getCurrentLib() {
    const app = getApp()
    this.setData({ selectedLib: app.globalData.selectedLib })
  },
  // 选择词库
  async selectLibrary(e) {
    const libName = e.currentTarget.dataset.lib
    const wechatId = getApp().globalData.wechatId    
    wx.showLoading({ title: '更新中...' })
    try {
      await api.updateLibrary(wechatId, libName)
      getApp().globalData.selectedLib = libName
      this.setData({ selectedLib: libName })
      wx.showToast({ title: '词库更新成功' })
      wx.navigateBack()
    } catch (err) {
      console.error('更新词库失败:', err)
    } finally {
      wx.hideLoading()
    }
  },

  // 跳转逻辑
  handleViewWords(e) {
    const bookId = e.currentTarget.dataset.id
    if (!bookId) {
      wx.showToast({ title: '无效词库ID', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/word-list/word-list?book_id=${bookId}`
    })
  }
})