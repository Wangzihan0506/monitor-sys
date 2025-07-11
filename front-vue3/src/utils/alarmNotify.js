import { ElNotification } from 'element-plus'

/**
 * 统一告警弹窗工具
 * @param {Object} options
 * @param {String} options.title 标题
 * @param {String} options.message 消息内容
 * @param {String} options.type 类型 error/warning/info/success
 * @param {String} [options.image] 图片base64或url
 * @param {String} [options.audio] 音频url
 * @param {Number} [options.duration] 持续时间ms
 */
export function alarmNotify({ title = '告警', message, type = 'error', duration = 4000 }) {
  let msgContent
  if (typeof message === 'string') {
    msgContent = `<div>${message}</div>`
  } else if (typeof message === 'function') {
    // VNode/h 传递
    msgContent = message
  } else {
    msgContent = `<div>${String(message)}</div>`
  }
  ElNotification({
    title,
    message: msgContent,
    type,
    duration,
    position: 'top-right',
    dangerouslyUseHTMLString: typeof msgContent === 'string',
    showClose: true,
  })
} 