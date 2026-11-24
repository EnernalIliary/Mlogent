"""Chinese/English consent copy. Identity metadata is escaped by the renderer."""

TEXT = {
    '连接授权 · Mlogent MCP': 'Authorize connection · Mlogent MCP',
    '了解 Mlogent ↗': 'About Mlogent ↗',
    '把工具，': 'Give the tools',
    '交给': 'to ',
    '你的助手。': 'your assistant.',
    '你正在连接 Mlogent MCP。': 'You are connecting to Mlogent MCP.',
    '确认请求来自你正在使用的客户端，': 'Check that this request comes from your client,',
    '然后输入已有的授权口令继续。': 'then choose an available sign-in method below.',
    '面向 Mindustry 的逻辑与蓝图工具链': 'Logic and blueprint tools for Mindustry',
    '可使用的工具由账号权限决定。连接成功后，你的客户端将返回对话或配置界面。': 'Available tools depend on your account permissions. After connecting, return to your client’s conversation or settings.',
    '确认这次连接': 'Confirm this connection',
    ' 请求访问 Mlogent MCP。请核对下方回调地址是否属于你的客户端。': ' requests access to Mlogent MCP. Check that the callback below belongs to your client.',
    'RETURN TO / 回调地址': 'RETURN TO / CALLBACK',
    'REQUESTED SCOPE / 请求范围': 'REQUESTED SCOPE',
    '授权口令': 'Authorization passphrase',
    '输入你的授权口令': 'Enter your authorization passphrase',
    '使用你已有的授权口令，或向服务管理员获取。此处不是设置新密码。': 'Use an existing authorization passphrase or obtain one from the administrator. You are not creating a new password here.',
    '授权并连接': 'Authorize and connect',
    '暂不连接，返回首页': 'Cancel and return to the homepage',
    '继续后，客户端将按你账号的现有权限访问工具。若不是你发起的连接，请关闭此页。': 'The client will access tools using your account’s existing permissions. Close this page if you did not start this request.',
    '使用 GitHub 登录': 'Sign in with GitHub',
    '使用 GitHub 基础身份登录。新用户使用 reader 权限档。': 'Sign in with your GitHub identity. New users receive the reader profile.',
    '不读取你的仓库。': 'Your repositories are not accessed.',
    '使用 Google 登录': 'Sign in with Google',
    '使用 Google 基础身份登录。新用户使用 reader 权限档。': 'Sign in with your Google identity. New users receive the reader profile.',
    '仅请求基本身份和已验证邮箱，不读取 Gmail 或云端硬盘。': 'Only basic identity and verified email are requested, not Gmail or Drive.',
    '已验证：': 'Verified: ',
    '。请确认上方客户端和回调地址，再继续授权。': '. Check the client and callback above before authorizing.',
    '已登录用户': 'Signed-in user',
    'GitHub 登录未完成，请重试。': 'GitHub sign-in was not completed. Please try again.',
    'Google 登录未完成，请重试。': 'Google sign-in was not completed. Please try again.',
    '暂时无法完成 GitHub 身份验证，请重新发起连接。': 'GitHub identity verification is temporarily unavailable. Restart the connection from your client.',
    '暂时无法完成 Google 身份验证，请重新发起连接。': 'Google identity verification is temporarily unavailable. Restart the connection from your client.',
    '登录凭据无效或已过期，请重新登录。': 'Sign-in credentials are invalid or expired. Please sign in again.',
}


def choose(requested=None, headers=None):
    if requested in ('zh', 'en'):
        return requested
    header = (headers or {}).get('Accept-Language', 'zh')
    # Use the first language preference. Other languages get the English fallback.
    return 'zh' if str(header).split(',', 1)[0].strip().lower().startswith('zh') else 'en'


def tr(value, language):
    return TEXT.get(value, value) if language == 'en' else value


def template(value, language):
    if language != 'en':
        return value
    for original in sorted(TEXT, key=len, reverse=True):
        value = value.replace(original, TEXT[original])
    return value.replace('lang="zh-CN"', 'lang="en"')


def provider_markup(value, language):
    # Only substitute static label text, never hidden OAuth parameter values.
    if language != 'en':
        return value
    for original in sorted(TEXT, key=len, reverse=True):
        value = value.replace('>' + original, '>' + TEXT[original])
        value = value.replace(original + '</p>', TEXT[original] + '</p>')
    return value
