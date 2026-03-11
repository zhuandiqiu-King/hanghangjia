/**
 * Token 存取 + 微信登录流程
 */
const { post } = require('./api')

function getToken() {
  return wx.getStorageSync('token') || ''
}

function setToken(token) {
  wx.setStorageSync('token', token)
}

function clearToken() {
  wx.removeStorageSync('token')
}

/**
 * 完整登录流程：wx.login → POST /api/auth/login → 存 token
 * @param {string} nickname
 * @param {string} avatarUrl
 */
function login(nickname, avatarUrl) {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          reject(new Error('wx.login 失败'))
          return
        }
        post('/api/auth/login', {
          code: loginRes.code,
          nickname: nickname || '',
          avatar_url: avatarUrl || '',
        })
          .then((data) => {
            setToken(data.token)
            resolve(data)
          })
          .catch(reject)
      },
      fail: reject,
    })
  })
}

module.exports = { getToken, setToken, clearToken, login }
