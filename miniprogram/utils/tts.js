/**
 * TTS 语音合成工具
 * 通过后端 edge-tts 接口实现，替代微信同声传译插件
 */
const api = require('./api')
const fs = wx.getFileSystemManager()

/**
 * 将文本转为语音并播放
 * @param {wx.InnerAudioContext} audioCtx - 音频上下文
 * @param {string} text - 要朗读的文本
 * @param {string} lang - 语言：en_US 或 zh_CN
 * @returns {Promise} 播放开始后 resolve
 */
function speak(audioCtx, text, lang) {
  return api.get(`/api/tts?text=${encodeURIComponent(text)}&lang=${lang}`).then((data) => {
    if (!data.audio) {
      return Promise.reject(new Error('无音频数据'))
    }
    // base64 解码写入临时文件
    const tempPath = `${wx.env.USER_DATA_PATH}/tts_${Date.now()}.mp3`
    fs.writeFileSync(tempPath, data.audio, 'base64')
    audioCtx.src = tempPath
    audioCtx.play()
    return tempPath
  })
}

module.exports = { speak }
