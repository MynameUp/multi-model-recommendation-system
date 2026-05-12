export function getAvatarPath(avatarName) {
  if (!avatarName || avatarName === '' || avatarName === 'null') {
    return require('@/assets/imgs/user.jpg') // 默认头像
  }
  if (avatarName.startsWith('http://') || avatarName.startsWith('https://')) {
    return avatarName
  }
  if (avatarName.startsWith('user_')) {
    // 拼接 Django 的媒体路径
    return `http://localhost:8000/media/${avatarName}` 
  }
  try {
    return require(`@/assets/imgs/${avatarName}`)
  } catch (error) {
    return require('@/assets/imgs/user.jpg')
  }
}
export function isValidAvatarName(avatarName) {
  return !(!avatarName || avatarName === '' || avatarName === 'null');
}