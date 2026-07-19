#!/bin/bash
# 彩華摄影档案 - 一键注册开机自启守护
# 用法：在 Finder 中双击本文件（会自动在终端里运行）
set -e

PLIST=~/Library/LaunchAgents/com.saika.photomanager.plist

echo "==> 正在注册开机自启守护进程..."

# 若端口已被占用（例如之前手动启动的），先释放，交给守护进程接管
lsof -ti:8765 2>/dev/null | xargs -r kill -9 2>/dev/null || true
sleep 1

# 先移除旧注册（若有），再注册
launchctl bootout "gui/$(id -u)/com.saika.photomanager" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

sleep 2

echo ""
echo "==> 状态检查："
curl -s -o /dev/null -w "   本地服务器 HTTP %{http_code}\n" http://localhost:8765/index.html
launchctl list | grep saika || true

echo ""
echo "✅ 完成！已设为：开机/登录自动启动 + 崩溃后自动重启。"
echo "   以后无需手动启动，重启 Mac 也会自动运行。"
echo "   访问地址：http://localhost:8765"
echo ""
echo "   如需卸载（移除自启）："
echo "   launchctl bootout gui/\$(id -u)/com.saika.photomanager"

# 停留一下，让用户看到结果（关闭窗口即可）
read -n 1 -s -r -p "按任意键关闭此窗口..."
