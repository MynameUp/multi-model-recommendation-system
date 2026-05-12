/**
 * 新闻问答辅助工具函数
 */

/**
 * 格式化问答时间
 */
export function formatQATime(timeStr) {
  if (!timeStr) return ''

  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }

  // 小于1小时
  if (diff < 3600000) {
    return Math.floor(diff / 60000) + '分钟前'
  }

  // 小于24小时
  if (diff < 86400000) {
    return Math.floor(diff / 3600000) + '小时前'
  }

  // 大于24小时
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hour}:${minute}`
}

/**
 * 截断文本
 */
export function truncateText(text, maxLength = 100) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * 高亮关键词
 */
export function highlightKeywords(text, keywords) {
  if (!text || !keywords || keywords.length === 0) {
    return text
  }

  let highlighted = text
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword})`, 'gi')
    highlighted = highlighted.replace(regex, '<span class="highlight">$1</span>')
  })

  return highlighted
}
