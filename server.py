#!/usr/bin/env python3
"""
彩華摄影档案 - 本地服务器
启动后直接在浏览器访问 http://localhost:8765
网页会自动检测到本地服务器，可从 ~/彩華摄影档案/ 直接读取图片，无需上传。

用法：
  python3 server.py              # 启动服务器
  python3 server.py --port 9000  # 自定义端口
"""

import http.server
import json
import os
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.expanduser("~/彩華摄影档案")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PORT = 8765

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}

# 媒体类型对应的子文件夹模板
FOLDER_TEMPLATES_PHOTO = [
    "01_原图", "02_客人筛选", "03_调色", "04_成稿", "06_花絮",
]
FOLDER_TEMPLATES_VIDEO = [
    "05_视频/01_原片", "05_视频/02_选片", "05_视频/03_调色", "05_视频/04_成片", "06_花絮",
]
FOLDER_TEMPLATES_BOTH = [
    "01_原图", "02_客人筛选", "03_调色", "04_成稿",
    "05_视频/01_原片", "05_视频/02_选片", "05_视频/03_调色", "05_视频/04_成片", "06_花絮",
]
MEDIA_TYPE_MAP = {
    "照片": FOLDER_TEMPLATES_PHOTO,
    "视频": FOLDER_TEMPLATES_VIDEO,
    "照片视频": FOLDER_TEMPLATES_BOTH,
}


def sanitize(name):
    """清理文件夹名中的非法字符"""
    return (name.replace("/", "_").replace("\\", "_").replace(":", "_")
            .replace("*", "_").replace("?", "_").replace('"', "_")
            .replace("<", "_").replace(">", "_").replace("|", "_"))


def get_templates(media_type):
    return MEDIA_TYPE_MAP.get(media_type, FOLDER_TEMPLATES_PHOTO)


def create_project_folder(year, date, client, character="", ip="", media_type="照片"):
    """创建一个摄影项目的文件夹结构，返回 (项目目录, 创建的子目录列表, 元数据路径)"""
    year_dir = os.path.join(BASE_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)
    parts = [date, client]
    if character:
        parts.append(character)
    if ip:
        parts.append(ip)
    parts.append(media_type)
    folder_name = sanitize("_".join(parts))
    project_dir = os.path.join(year_dir, folder_name)
    os.makedirs(project_dir, exist_ok=True)
    templates = get_templates(media_type)
    created = []
    for sub in templates:
        sub_path = os.path.join(project_dir, sub)
        os.makedirs(sub_path, exist_ok=True)
        created.append(sub_path)
    meta = {
        "date": date, "clientCN": client, "character": character, "ip": ip,
        "mediaType": media_type, "year": year,
        "createdAt": datetime.now().isoformat(),
        "folderPath": project_dir, "structure": templates,
    }
    meta_path = os.path.join(project_dir, "project.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return project_dir, created, meta_path


class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/projects':
            self._api_projects()
        elif path == '/api/files':
            self._api_files(query.get('path', [''])[0])
        elif path == '/api/image':
            self._api_image(query.get('path', [''])[0])
        elif path == '/api/check':
            self._json({'ok': True, 'baseDir': BASE_DIR, 'localIP': self._get_local_ip()})
        elif path == '/api/bookings':
            self._api_bookings_list()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/save-select-page':
            self._api_save_select_page()
        elif path == '/api/create-folder':
            self._api_create_folder()
        elif path == '/api/booking-submit':
            self._api_booking_submit()
        elif path == '/api/booking-delete':
            self._api_booking_delete()
        else:
            self._send_text(404, 'Not found')

    def _get_local_ip(self):
        """获取本机局域网 IP"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'

    # ---------- API endpoints ----------

    def _api_projects(self):
        """列出所有项目及其子文件夹"""
        projects = []
        if not os.path.isdir(BASE_DIR):
            self._json(projects)
            return

        for year in sorted(os.listdir(BASE_DIR)):
            year_path = os.path.join(BASE_DIR, year)
            if not os.path.isdir(year_path):
                continue
            for name in sorted(os.listdir(year_path)):
                proj_path = os.path.join(year_path, name)
                if not os.path.isdir(proj_path):
                    continue

                # 读取 project.json
                meta = {}
                meta_file = os.path.join(proj_path, 'project.json')
                if os.path.isfile(meta_file):
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                    except Exception:
                        pass

                # 列出子文件夹
                subfolders = []
                image_counts = {}
                for item in sorted(os.listdir(proj_path)):
                    item_path = os.path.join(proj_path, item)
                    if os.path.isdir(item_path):
                        subfolders.append(item)
                        # 统计图片数
                        count = sum(
                            1 for f in os.listdir(item_path)
                            if os.path.isfile(os.path.join(item_path, f))
                            and os.path.splitext(f)[1].lower() in IMAGE_EXTS
                        )
                        if count > 0:
                            image_counts[item] = count
                    # 也统计嵌套子文件夹（如 05_视频/01_原片）
                    elif '/' in item:
                        pass

                # 检查嵌套文件夹
                for item in sorted(os.listdir(proj_path)):
                    item_path = os.path.join(proj_path, item)
                    if os.path.isdir(item_path):
                        for sub in sorted(os.listdir(item_path)):
                            sub_path = os.path.join(item_path, sub)
                            if os.path.isdir(sub_path):
                                combined = f"{item}/{sub}"
                                count = sum(
                                    1 for f in os.listdir(sub_path)
                                    if os.path.isfile(os.path.join(sub_path, f))
                                    and os.path.splitext(f)[1].lower() in IMAGE_EXTS
                                )
                                if count > 0:
                                    image_counts[combined] = count

                rel_path = os.path.relpath(proj_path, BASE_DIR)
                projects.append({
                    'name': name,
                    'year': year,
                    'relPath': rel_path,
                    'subfolders': subfolders,
                    'imageCounts': image_counts,
                    'meta': meta,
                })

        self._json(projects)

    def _api_files(self, rel_path):
        """列出指定文件夹中的图片文件"""
        target = os.path.join(BASE_DIR, rel_path)
        abs_target = os.path.abspath(target)
        abs_base = os.path.abspath(BASE_DIR)

        if not abs_target.startswith(abs_base):
            self._json({'error': '路径不在允许范围内'}, 403)
            return
        if not os.path.isdir(target):
            self._json({'error': '文件夹不存在'}, 404)
            return

        files = []
        for f in sorted(os.listdir(target)):
            f_path = os.path.join(target, f)
            if not os.path.isfile(f_path):
                continue
            ext = os.path.splitext(f)[1].lower()
            is_image = ext in IMAGE_EXTS
            files.append({
                'name': f,
                'size': os.path.getsize(f_path),
                'isImage': is_image,
                'ext': ext,
                'relPath': os.path.join(rel_path, f),
            })

        self._json({'files': files, 'total': len(files), 'imageCount': sum(1 for f in files if f['isImage'])})

    def _api_image(self, rel_path):
        """代理 serving 单张图片"""
        target = os.path.join(BASE_DIR, rel_path)
        abs_target = os.path.abspath(target)
        abs_base = os.path.abspath(BASE_DIR)

        if not abs_target.startswith(abs_base):
            self._send_text(403, '路径不在允许范围内')
            return
        if not os.path.isfile(target):
            self._send_text(404, '文件不存在')
            return

        ext = os.path.splitext(target)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.webp': 'image/webp',
            '.bmp': 'image/bmp', '.gif': 'image/gif',
            '.tiff': 'image/tiff',
        }
        content_type = content_types.get(ext, 'application/octet-stream')

        try:
            with open(target, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._send_text(500, str(e))

    def _api_save_select_page(self):
        """保存选图页 HTML 到服务器，返回可访问的 URL"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0 or content_length > 100 * 1024 * 1024:
            self._json({'error': '文件太大或为空'}, 400)
            return

        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            filename = data.get('filename', 'select.html')
            html = data.get('html', '')

            # 清理文件名
            filename = os.path.basename(filename)
            if not filename.endswith('.html'):
                filename += '.html'

            # 保存到 select_pages 目录
            save_dir = os.path.join(APP_DIR, 'select_pages')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(html)

            local_ip = self._get_local_ip()
            port = self.server.server_address[1]
            local_url = f'http://{local_ip}:{port}/select_pages/{urllib.parse.quote(filename)}'

            # 自动生成索引页
            self._generate_select_index()

            self._json({'ok': True, 'url': local_url, 'filename': filename})
        except Exception as e:
            self._json({'error': str(e)}, 500)

    def _api_create_folder(self):
        """根据网页项目信息一键创建本地文件夹结构"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0 or content_length > 64 * 1024:
            self._json({'error': '请求体为空或过大'}, 400)
            return

        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            date = (data.get('date') or '').strip()
            client = (data.get('client') or '').strip()
            if not date or not client:
                self._json({'error': '日期和客户CN不能为空'}, 400)
                return

            character = (data.get('character') or '').strip()
            ip = (data.get('ip') or '').strip()
            media_type = data.get('mediaType') or '照片'
            if media_type not in MEDIA_TYPE_MAP:
                media_type = '照片'

            year = date[:4] if len(date) >= 4 else str(datetime.now().year)
            project_dir, created, meta_path = create_project_folder(
                year, date, client, character, ip, media_type
            )

            self._json({
                'ok': True,
                'folderName': os.path.basename(project_dir),
                'path': project_dir,
                'created': len(created),
            })
        except Exception as e:
            self._json({'error': str(e)}, 500)

    def _api_booking_submit(self):
        """接收客户预约表单，保存为 JSON 文件"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0 or content_length > 64 * 1024:
            self._json({'error': '请求体为空或过大'}, 400)
            return

        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)

            # 必填字段校验
            client_name = (data.get('clientName') or '').strip()
            if not client_name:
                self._json({'error': '请填写称呼'}, 400)
                return

            # 生成唯一文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = sanitize(client_name)
            filename = f'{timestamp}_{safe_name}.json'

            # 保存到 bookings 目录
            bookings_dir = os.path.join(APP_DIR, 'bookings')
            os.makedirs(bookings_dir, exist_ok=True)

            save_path = os.path.join(bookings_dir, filename)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._json({
                'ok': True,
                'message': '预约提交成功',
                'filename': filename,
            })
        except Exception as e:
            self._json({'error': str(e)}, 500)

    def _api_bookings_list(self):
        """列出所有待处理的预约"""
        bookings_dir = os.path.join(APP_DIR, 'bookings')
        if not os.path.isdir(bookings_dir):
            self._json([])
            return

        bookings = []
        for f in sorted(os.listdir(bookings_dir), reverse=True):
            if not f.endswith('.json'):
                continue
            path = os.path.join(bookings_dir, f)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                stat = os.stat(path)
                import time as t
                bookings.append({
                    'filename': f,
                    'data': data,
                    'mtime': t.strftime('%Y-%m-%d %H:%M', t.localtime(stat.st_mtime)),
                    'mtimeISO': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception:
                pass

        # 按提交时间倒序排列（最新的在前面）
        bookings.sort(key=lambda b: b.get('data', {}).get('submittedAt', ''), reverse=True)
        self._json(bookings)

    def _api_booking_delete(self):
        """建档后删除待处理预约"""
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length) if length else b''
            data = json.loads(raw.decode('utf-8')) if raw else {}
            fn = data.get('filename', '')
            if not fn or '/' in fn or '\\' in fn or not fn.endswith('.json'):
                self._json({'ok': False, 'error': 'invalid filename'})
                return
            bookings_dir = os.path.join(APP_DIR, 'bookings')
            fp = os.path.join(bookings_dir, fn)
            if os.path.isfile(fp):
                os.remove(fp)
                self._json({'ok': True})
            else:
                self._json({'ok': False, 'error': 'not found'})
        except Exception as e:
            self._json({'ok': False, 'error': str(e)})

    def _generate_select_index(self):
        """在 select_pages/ 目录生成 index.html，列出所有选图页"""
        save_dir = os.path.join(APP_DIR, 'select_pages')
        if not os.path.isdir(save_dir):
            return

        pages = []
        for f in sorted(os.listdir(save_dir), reverse=True):
            if f.endswith('.html') and f != 'index.html':
                stat = os.stat(os.path.join(save_dir, f))
                import time
                pages.append({
                    'filename': f,
                    'name': f.replace('.html', ''),
                    'size_kb': round(stat.st_size / 1024),
                    'mtime': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime)),
                })

        rows = ''.join([
            f'<a class="card" href="{urllib.parse.quote(p["filename"])}">'
            f'<div class="card-name">{p["name"]}</div>'
            f'<div class="card-meta">{p["mtime"]} · {p["size_kb"]}KB</div>'
            f'</a>'
            for p in pages
        ]) if pages else '<div class="empty">暂无选图页</div>'

        index_html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>彩華摄影 - 选图页列表</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"PingFang SC",sans-serif;background:#FAFAFA;color:#1A1A1A}}
.container{{max-width:600px;margin:0 auto;padding:20px}}
.header{{text-align:center;padding:24px 0 16px;border-bottom:2px solid #1A1A1A;margin-bottom:20px}}
.header .logo{{font-size:22px;font-weight:900;letter-spacing:2px}}
.header .sub{{font-size:11px;color:#999;letter-spacing:3px;margin-top:4px}}
.card{{display:block;background:#fff;border-radius:10px;padding:16px;margin-bottom:10px;text-decoration:none;color:#1A1A1A;box-shadow:0 1px 3px rgba(0,0,0,.04);transition:.15s}}
.card:hover{{box-shadow:0 2px 8px rgba(0,0,0,.08);transform:translateY(-1px)}}
.card-name{{font-size:14px;font-weight:600}}
.card-meta{{font-size:11px;color:#999;margin-top:4px}}
.empty{{text-align:center;padding:40px;color:#999;font-size:13px}}
.tip{{text-align:center;font-size:11px;color:#bbb;padding:12px}}
</style></head><body><div class="container">
<div class="header"><div class="logo">SAIKA · 彩華</div><div class="sub">PHOTOGRAPHY</div></div>
{rows}
<div class="tip">点击打开选图页 · 长按可复制链接分享给客户</div>
</div></body></html>'''

        with open(os.path.join(save_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)

    # ---------- helpers ----------

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, code, message):
        body = message.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        # 静默日志，只在出错时打印
        if args and '404' in str(args[1]):
            super().log_message(format, *args)


def main():
    # 云平台（Render / Railway 等）通过 PORT 环境变量指定端口；本地默认 8765
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    os.makedirs(BASE_DIR, exist_ok=True)

    print("=" * 50)
    print("  彩華摄影档案 - 本地服务器")
    print("=" * 50)
    print(f"  档案目录: {BASE_DIR}")
    print(f"  访问地址: http://localhost:{port}")
    print(f"  按 Ctrl+C 停止")
    print()
    print("  启动后打开浏览器访问上方地址即可。")
    print("  网页会自动检测到本地服务器，")
    print("  可从档案文件夹直接读取图片，无需上传。")
    print("=" * 50)
    print()

    server = http.server.HTTPServer(('0.0.0.0', port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()


if __name__ == '__main__':
    main()
