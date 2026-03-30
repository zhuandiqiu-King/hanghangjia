/**
 * 网络请求封装，通过云托管内网调用
 * - 自动带 token
 * - 401 时静默重新登录并重试，失败再弹窗提示
 */
const SERVICE_NAME = 'flask-h72v'
const DEFAULT_TIMEOUT = 30000 // 30秒，兼容容器冷启动

// 静默重登状态（防止多个请求同时触发）
let _refreshingToken = null

/**
 * 静默重新登录：wx.login → 后端换 token
 */
function _silentLogin() {
  if (_refreshingToken) return _refreshingToken

  _refreshingToken = new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          reject(new Error('wx.login 失败'))
          return
        }
        // 直接调 callContainer，不走 request（避免循环）
        wx.cloud.callContainer({
          config: { env: 'prod-0g02is9d648082af' },
          service: SERVICE_NAME,
          path: '/api/auth/login',
          method: 'POST',
          header: { 'Content-Type': 'application/json' },
          data: { code: loginRes.code, nickname: '', avatar_url: '' },
          success(res) {
            if (res.statusCode === 200 && res.data && res.data.token) {
              wx.setStorageSync('token', res.data.token)
              resolve(res.data.token)
            } else {
              reject(new Error('静默登录失败'))
            }
          },
          fail: reject,
        })
      },
      fail: reject,
    })
  }).finally(() => {
    _refreshingToken = null
  })

  return _refreshingToken
}

/**
 * 发起请求（内部实现）
 */
function _doRequest(options, token) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json', ...options.header }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    const params = {
      config: { env: 'prod-0g02is9d648082af' },
      service: SERVICE_NAME,
      path: options.url,
      method: options.method || 'GET',
      header,
      data: options.data,
      success(res) {
        if (res.statusCode === 401) {
          reject({ _is401: true })
          return
        }
        if (res.statusCode >= 400) {
          const detail = res.data && res.data.detail ? res.data.detail : '请求失败'
          reject(new Error(detail))
          return
        }
        resolve(res.data)
      },
      fail(err) {
        console.error('callContainer fail', err)
        reject(err)
      },
    }

    params.timeout = options.timeout || DEFAULT_TIMEOUT

    wx.cloud.callContainer(params)
  })
}

/**
 * 主请求函数：401 自动静默重登 + 重试
 */
function request(options) {
  const token = wx.getStorageSync('token') || ''

  return _doRequest(options, token).catch((err) => {
    // 非 401 错误直接抛出
    if (!err || !err._is401) throw err

    // 401：尝试静默重登
    return _silentLogin()
      .then((newToken) => {
        // 用新 token 重试原请求
        return _doRequest(options, newToken)
      })
      .catch(() => {
        // 静默登录也失败，弹窗让用户手动登录
        wx.removeStorageSync('token')
        return new Promise((_, reject) => {
          wx.showModal({
            title: '登录已过期',
            content: '请重新登录以继续使用',
            confirmText: '去登录',
            cancelText: '稍后再说',
            success(res) {
              if (res.confirm) {
                wx.redirectTo({ url: '/pages/login/login' })
              }
            },
          })
          reject(new Error('登录已过期，请重新登录'))
        })
      })
  })
}

function get(url) {
  return request({ url, method: 'GET' })
}

function post(url, data) {
  return request({ url, method: 'POST', data })
}

function put(url, data) {
  return request({ url, method: 'PUT', data })
}

function del(url) {
  return request({ url, method: 'DELETE' })
}

module.exports = { request, get, post, put, del }
