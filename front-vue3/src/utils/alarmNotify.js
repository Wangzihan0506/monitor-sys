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
export function alarmNotify({ title = '告警', message, type = 'error', image = '', audio = '', duration = 4000 }) {
  ElNotification({
    title,
    message: () => {
      return (
        `<div>${message}</div>` +
        (image ? `<img src='${image}' alt='告警截图' style='max-width:200px;max-height:120px;margin-top:8px;'/>` : '') +
        (audio ? `<audio src='${audio}' controls style='margin-top:8px;width:200px;'></audio>` : '')
      )
    },
    type,
    duration,
    position: 'top-right',
    dangerouslyUseHTMLString: true,
    showClose: true,
  })
} 