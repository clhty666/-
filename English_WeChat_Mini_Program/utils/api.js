// utils/api.js
const API_BASE = 'http://127.0.0.1:5000'

// 封装请求方法
const request = (url, method, data) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: API_BASE + url,
      method: method,
      data: data,
      success: res => {
        if (res.data.code === 200) {
          resolve(res.data.data)
        } else {
          wx.showToast({ title: res.data.message, icon: 'none' })
          reject(res.data)
        }
      },
      fail: err => {
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      }
    })
  })
}

// API接口集合
export const api = {
//用户登录
  login: (wechatId) => request('/api/login', 'POST', { wechat_id: wechatId }),
//更新每日学习目标
  updateGoal: (wechatId, goal) => request('/api/user/goal', 'POST', { wechat_id: wechatId, daily_goal: goal }),

//获取可用词库
  getLibraries: () => request('/api/libraries', 'GET'),
//更新用户选择的词库
  updateLibrary: (wechatId, lib) => request('/api/user/library', 'POST', { wechat_id: wechatId, book_name: lib }),
//查看词库单词
  getLibraryWords: (bookId) => request('/api/library/words', 'GET', { book_id: bookId }),
  

//学习界面单词获取
  getWords: (wechatId) => request('/api/learn/words', 'GET', { 
    wechat_id: wechatId
  }),

  //生词本更改
  updateVocab: (wechatId, wordId, action) => request('/api/vocabulary', 'POST', { 
    wechat_id: wechatId, 
    word_id: wordId, 
    action: action 
  }),
  //生词本查看
  getVocabulary:(wechatId)=>request('/api/vocabulary','POST',{wechat_id: wechatId}),


  // 更新学习数据
  updateLearningStats: (wechatId, wordId) => request('/api/learning/stats', 'POST', {
    wechat_id: wechatId,
    word_id: wordId
  }),
  // 从学习数据中移除
  removeFromStats: (wechatId, wordId) => request('/api/learning/stats', 'DELETE', {
    wechat_id: wechatId,
    word_id: wordId
  }),






}