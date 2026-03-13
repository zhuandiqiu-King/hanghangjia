/**
 * emoji 头像工具函数
 * 后端为未设置头像的用户生成 "emoji:🐱" 格式的默认头像
 */

/**
 * 判断是否为 emoji 默认头像
 * @param {string} url
 * @returns {boolean}
 */
function isEmojiAvatar(url) {
  return typeof url === 'string' && url.startsWith('emoji:')
}

/**
 * 从 emoji 头像 URL 中提取 emoji
 * @param {string} url - 如 "emoji:🐱"
 * @returns {string} - 如 "🐱"
 */
function getEmoji(url) {
  if (!isEmojiAvatar(url)) return '😊'
  return url.slice(6) || '😊'
}

/**
 * 判断是否有真实头像（非 emoji、非空）
 * @param {string} url
 * @returns {boolean}
 */
function hasRealAvatar(url) {
  return !!url && !isEmojiAvatar(url)
}

module.exports = { isEmojiAvatar, getEmoji, hasRealAvatar }
