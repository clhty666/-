// pages/learn/learn.js
import { api } from '../../utils/api'

Page({
  data: {
    currentWord: {  // 初始化空对象而不是null
      word_id: '',
      head_word: '',
      is_starred: false,
      sentences: [],
      phrases: [],
      related_words: [],
      translations: []
      
    },     // 当前单词数据
    showDetails: false,    // 是否显示详细信息
    wordQueue: [],         // 单词队列
    isLastWord: false      // 是否是最后一个单词
  },

  onLoad() {
    this.initLearning()
  },
  // 初始化学习数据
  async initLearning() {
    try {
      const words = await this.fetchLearningWords()
      if (words.length === 0) {
        wx.showToast({ title: '今日学习已完成', icon: 'none' })
        wx.navigateBack()
        return
      }
      // 检查 word_id 是否存在
      if (words.length > 0 && !words[0].hasOwnProperty('word_id')) {
        wx.showToast({ title: '数据格式错误', icon: 'none' });
        return;
      }
      this.setData({
        wordQueue: words,
        currentWord: words[0],
        isLastWord: words.length === 1
      })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // 获取学习单词列表
  async fetchLearningWords() {
    const wechatId = getApp().globalData.wechatId
    const res = await api.getWords(wechatId)
    // 过滤无效数据
    return res.filter(word => !!word.word_id);
  },

  // 点击页面显示详细信息
  handleTap() {
    if (!this.data.showDetails) {
      this.setData({ showDetails: true })
    }
  },
  //发音接口
  playAudio(e) {
    const word = e.currentTarget.dataset.word;
    const type = e.currentTarget.dataset.type;
    const audioUrl = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=${type}`;
    const audioCtx = wx.createInnerAudioContext();
    audioCtx.src = audioUrl;
    audioCtx.play();
    
    audioCtx.onError((err) => {
      console.error('播放失败:', err);
      wx.showToast({ title: '播放失败', icon: 'none' });
    });
  },

  // 处理收藏按钮点击
  async toggleStar() {
    const { currentWord } = this.data
    const action = currentWord.is_starred ? 'remove' : 'add'
    
    try {
      await api.updateVocab(getApp().globalData.wechatId, currentWord.word_id, action)
      currentWord.is_starred = !currentWord.is_starred
      this.setData({ currentWord })
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 处理记住/忘记按钮
  async handleAction(e) {
    const actionType = e.currentTarget.dataset.type
    const { currentWord, wordQueue } = this.data
  
    try {
      // 记住逻辑
      if (actionType === 'remember') {
        
        await api.updateLearningStats(
          getApp().globalData.wechatId, 
          currentWord.word_id
          
        )
      } 
      // 忘记逻辑
      else {
        await api.removeFromStats(getApp().globalData.wechatId, currentWord.word_id)
          .catch(err => {
            if (err.message?.includes('not in stats')) return
            throw err
          })
        this.data.wordQueue.push(currentWord) // 重新加入队列末尾
      }
  
      // 推进到下一个单词
      const newQueue = wordQueue.slice(1)
      if (newQueue.length === 0) {
        wx.showToast({ title: '今日学习完成！', icon: 'none' })
        wx.navigateBack()
        return
      }
  
      this.setData({
        currentWord: newQueue[0],
        wordQueue: newQueue,
        showDetails: false,
        isLastWord: newQueue.length === 1
      })
    } catch (err) {
      wx.showToast({ title: '操作失败，请重试', icon: 'none' })
    }
  }


})