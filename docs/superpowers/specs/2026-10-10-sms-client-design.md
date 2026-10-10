# Ubuntu 短信客户端设计

用户已确认聊天中的方案，并要求开始开发。目标是用 Python 在 Ubuntu 显示已有 PHP 服务器的短信，代码仅写入 Ubuntu 目录，不修改 PHP。

## 功能

- Python 3.10+ / PySide6 原生桌面应用，中文界面。
- 首次启动输入服务器根地址或 appapi 接口地址、Token，保存后自动加载；设置可以修改。
- 请求 GET `appapi/index.php?action=list`，使用 `Authorization: Bearer` 和兼容请求头 `X-API-Token`，Token 不进入 URL。
- 按 `received_at DESC, id DESC` 显示，最新短信位于首页顶部。每 10 秒自动刷新，可手动刷新。
- 仿照 smslist.php，按日期分组、白色气泡、设备标签、来源号码、完整时间。
- 对包含“验证码”的短信提取 4–8 位数字，优先选择关键词附近，排除长号码及链接；在正文高亮，可复制验证码或全文。
- http(s) 和 www 链接可在系统浏览器打开，手机号码可交给系统 tel 处理器；不执行其他协议。
- 每页 50 条、本地分页，避免全部短信创建 UI 导致卡顿。
- 无短信、首次加载、网络失败、Token 无效均有中文状态。刷新失败保留已有短信。

## 实现边界

`core.py` 负责地址、短信解析、HTML 安全转义、验证码、配置。`network.py` 使用 Qt 异步网络请求与超时。`ui.py` 负责配置窗口、气泡和分页。`__main__.py` 提供启动入口。

配置默认保存在 `$XDG_CONFIG_HOME/sms-forward-client/config.json`，未设置时使用 `~/.config/sms-forward-client/config.json`。配置目录权限 0700、文件权限 0600，原子替换。Token 本地明文保存，不进入日志或短信界面。

服务器端返回整个列表，客户端本地分页；没有真实地址和 Token 时，以本地 HTTP 测试服务器验证接口契约。验证覆盖配置读写、链接安全、验证码、排序、认证请求、错误和界面复制/分页。
