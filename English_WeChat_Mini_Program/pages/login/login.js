// pages/login/login.js
import { api } from '../../utils/api'

Page({
  data: {
    inputId: '' // 输入框绑定的微信ID
  },

  // 输入框输入事件
  handleInput(e) {
    this.setData({ inputId: e.detail.value })
  },

  // 登录按钮点击
  async handleLogin() {
    if (!this.data.inputId) {
      wx.showToast({ title: '请输入微信ID', icon: 'none' })
      return
    }

    wx.showLoading({ title: '登录中...' })
    try {
      const res = await api.login(this.data.inputId)
      getApp().globalData.wechatId = this.data.inputId
      getApp().globalData.dailyGoal = res.daily_goal
      getApp().globalData.selectedLib = res.selected_libraries
      
      wx.switchTab({ url: '/pages/index/index' })
    } finally {
      wx.hideLoading()
    }
  }

  /*bindGetUserInfo: function (e) {
    if (e.detail.errMsg === "getPhoneNumber:ok") {
         //用户按了允许授权按钮
         var that = this;
           wx.login({
             success(loginRes) {
               if (loginRes.code) {
                   let code = loginRes.code;
                   // 登录  -  start
                   let data = {
                     code: code,
                     iv: e.detail.iv, 
                     image: that.userInfo.avatarUrl,
                     encrypteData: e.detail.encryptedData,
                   }
                   // loading start
                   wx.showLoading({
                     title: '登录中...',
                   })
 
                   // 调用你的登录接口将用户收据发送给服务器
                   login(data).then(res => {
                     wx.hideLoading()
                     if(res.data.code === 0){
                       let dataString = JSON.stringify(res.data.data)
                       wx.setStorage({key: 'token', data: res.data.data.token})
                       wx.setStorage({key: 'userInfo', data: dataString})
       
                       wx.showToast({
                         title: '登录成功',
                         icon: 'success',
                         duration: 2500
                       })
                       let timer = setTimeout(() => {
                         clearTimeout(timer);
                         timer = null
                         app.onLaunch()
                         wx.reLaunch({
                           url: '/pages/index/index',
                         })
                       }, 2000);
                     }
                   }, err => {
                        wx.hideLoading()
                        wx.showToast({
                          title: res.data.message,
                          icon: 'none',
                          duration: 2500
                        })
                      });
                   // 登录  -  end
               }
             }
         })
     } else {
         wx.switchTab({
              url: '/pages/login/login'
          })
     }
 }
*/
})