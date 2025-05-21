// pages/settings/settings.js
import { api } from '../../utils/api'

Page({
  data: {
    newGoal: 20  // 临时存储新目标值
  },
  onLoad() {
    this.setData({
      newGoal: getApp().globalData.dailyGoal
    })
  },
  // 输入框变化处理
  handleInput(e) {
    this.setData({
      newGoal: e.detail.value
    })
  },
  // 提交修改
  async submitGoal() {
    const wechatId = getApp().globalData.wechatId
    const newGoal = parseInt(this.data.newGoal)
    if (isNaN(newGoal) || newGoal < 1 || newGoal > 1000) {
      wx.showToast({ title: '请输入新的每日目标', icon: 'none' })
      return
    }
    wx.showLoading({ title: '更新中...' })
    try {
      await api.updateGoal(wechatId, newGoal)
      getApp().globalData.dailyGoal = newGoal
      wx.showToast({ title: '目标更新成功' })
      wx.navigateBack()
      getApp().globalData.dailyGoal = newGoal

      
    } catch (err) {
      console.error('更新目标失败:', err)
    } finally {
      wx.hideLoading()
    }
  }
})