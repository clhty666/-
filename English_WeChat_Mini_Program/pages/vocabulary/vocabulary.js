// pages/vocabulary/vocabulary.js
import { api } from '../../utils/api'

Page({
  data: {
    vocabList: [],         // 生词本列表数据
    loading: true,        // 加载状态
    currentEditId: null   // 当前正在编辑的单词ID
  },

  onLoad() {
    this.loadVocabulary()
  },

  // 加载生词本数据
  async loadVocabulary() {
    const wechatId = getApp().globalData.wechatId
    if (!wechatId) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }

    //生词本查看
    try {
      const res = await api.getVocabulary(wechatId) 
      this.processData(res)
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 处理生词本数据
  processData(rawData) {
    const list = Object.entries(rawData).map(([headWord, details]) => ({
      headWord,  
      wordId: details.word_id,  
      addedTime: this.formatTime(details.added_time),
      nextReview: this.formatTime(details.next_review),
      isStarred: true           //一直显示收藏
      
    }))
    this.setData({ vocabList: list })
  },

  // 格式化时间
  formatTime(timestamp) {
    if (!timestamp) return '未设置'
    const date = new Date(timestamp)
    return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}`
  },

  // 处理删除操作
  handleEdit(e) {
    const wordId = e.currentTarget.dataset.wordId
    this.setData({ currentEditId: wordId })
    
    wx.showActionSheet({
      itemList: ['移出生词本'],
      success: (res) => {
        if (res.tapIndex === 0) {
          this.removeWord(wordId)
        } 
      }
    })
  },

  // 移出生词本
  async removeWord(wordId) {
    try {
      await api.updateVocab(getApp().globalData.wechatId, wordId, 'remove')
      this.loadVocabulary() // 刷新列表
      wx.showToast({ title: '移除成功' })
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

})