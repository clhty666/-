// pages/index/index.js
import { api } from '../../utils/api'

Page({
  data: {
    userInfo: {  // 初始化为空对象而不是null
      wechatId: '',
      dailyGoal: '',
      selectedLib: ''
    }
  },

  onShow() {
    this.loadUserInfo()
  },

  // 加载用户信息
  async loadUserInfo() {
    const app = getApp()
    this.setData({
      userInfo: {
        wechatId: app.globalData.wechatId,
        dailyGoal: app.globalData.dailyGoal,
        selectedLib: app.globalData.selectedLib
      }
    })
  },
  // 跳转到生词本页面
  goToVocab() {
    wx.navigateTo({ url: '/pages/vocabulary/vocabulary' })
  },
  // 跳转到词库选择
  goToLibrary() {
    wx.navigateTo({ url: '/pages/library/library' })
  },
  // 跳转到每日目标设置
  goToSettings() {
    wx.navigateTo({ url: '/pages/settings/settings' })
  },
  // 退出登录
  logout() {
    getApp().globalData.wechatId = null
    wx.reLaunch({ url: '/pages/login/login' })
  }
})