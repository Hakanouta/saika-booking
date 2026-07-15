#!/usr/bin/env python3
"""
彩華摄影档案 - 文件夹结构生成器
用法：
  python3 create_folders.py                     # 交互式创建
  python3 create_folders.py --from-json data.json # 从 JSON 批量创建
  python3 create_folders.py --list              # 列出已有项目
"""

import os
import json
import argparse
from datetime import datetime

BASE_DIR = os.path.expanduser("~/彩華摄影档案")

# 媒体类型对应的子文件夹模板
FOLDER_TEMPLATES_PHOTO = [
    "01_原图",
    "02_客人筛选",
    "03_调色",
    "04_成稿",
    "06_花絮",
]

FOLDER_TEMPLATES_VIDEO = [
    "05_视频/01_原片",
    "05_视频/02_选片",
    "05_视频/03_调色",
    "05_视频/04_成片",
    "06_花絮",
]

FOLDER_TEMPLATES_BOTH = [
    "01_原图",
    "02_客人筛选",
    "03_调色",
    "04_成稿",
    "05_视频/01_原片",
    "05_视频/02_选片",
    "05_视频/03_调色",
    "05_视频/04_成片",
    "06_花絮",
]

MEDIA_TYPE_MAP = {
    "照片": FOLDER_TEMPLATES_PHOTO,
    "视频": FOLDER_TEMPLATES_VIDEO,
    "照片视频": FOLDER_TEMPLATES_BOTH,
}


def sanitize(name):
    """清理文件夹名中的非法字符"""
    return (
        name.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )


def get_templates(media_type):
    """根据媒体类型返回对应的子文件夹模板"""
    return MEDIA_TYPE_MAP.get(media_type, FOLDER_TEMPLATES_PHOTO)


def create_project_folder(year, date, client, character="", ip="", media_type="照片", base_dir=None):
    """创建一个摄影项目的文件夹结构"""
    base = base_dir or BASE_DIR
    year_dir = os.path.join(base, str(year))
    os.makedirs(year_dir, exist_ok=True)

    # 生成文件夹名: 日期_客人CN_角色_IP_媒体类型
    parts = [date, client]
    if character:
        parts.append(character)
    if ip:
        parts.append(ip)
    parts.append(media_type)
    folder_name = sanitize("_".join(parts))
    project_dir = os.path.join(year_dir, folder_name)
    os.makedirs(project_dir, exist_ok=True)

    # 根据媒体类型选择对应模板
    templates = get_templates(media_type)

    # 创建子文件夹
    created = []
    for sub in templates:
        sub_path = os.path.join(project_dir, sub)
        os.makedirs(sub_path, exist_ok=True)
        created.append(sub_path)

    # 创建元数据文件
    meta = {
        "date": date,
        "clientCN": client,
        "character": character,
        "ip": ip,
        "mediaType": media_type,
        "year": year,
        "createdAt": datetime.now().isoformat(),
        "folderPath": project_dir,
        "structure": templates,
    }
    meta_path = os.path.join(project_dir, "project.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return project_dir, created, meta_path


def interactive():
    """交互式创建项目文件夹"""
    print("=" * 50)
    print("  彩華摄影档案 - 文件夹结构生成器")
    print("=" * 50)
    print()

    date = input("拍摄日期 (YYYY-MM-DD): ").strip()
    if not date:
        print("❌ 日期不能为空")
        return

    client = input("客人CN: ").strip()
    if not client:
        print("❌ 客人CN不能为空")
        return

    character = input("角色 (可选): ").strip()
    ip = input("IP (可选): ").strip()

    print()
    print("交付物类型:")
    print("  1. 仅照片")
    print("  2. 仅视频")
    print("  3. 照片+视频")
    media_choice = input("请选择 (1/2/3, 默认1): ").strip()
    media_type_map = {"1": "照片", "2": "视频", "3": "照片视频"}
    media_type = media_type_map.get(media_choice, "照片")

    year = date[:4] if len(date) >= 4 else str(datetime.now().year)
    templates = get_templates(media_type)

    print(f"\n📁 将在 ~/彩華摄影档案/{year}/ 下创建项目文件夹...")
    print(
        f"   文件夹名: {date}_{client}"
        f"{'_'+character if character else ''}"
        f"{'_'+ip if ip else ''}"
        f"_{media_type}"
    )
    print(f"\n   将创建以下子文件夹:")
    for t in templates:
        print(f"     📁 {t}")

    confirm = input("\n确定创建? (y/n): ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    project_dir, created, meta_path = create_project_folder(
        year, date, client, character, ip, media_type
    )

    print(f"\n✅ 项目文件夹已创建!")
    print(f"   📂 {project_dir}")
    print(f"   📄 元数据: {meta_path}")
    print(f"\n接下来的步骤:")
    if media_type in ("照片", "照片视频"):
        print(f"   1. 将原图放入 → 01_原图/")
        print(f"   2. 客人选图后放入 → 02_客人筛选/")
        print(f"   3. 调色完成后放入 → 03_调色/")
        print(f"   4. 客人修脸后成稿放入 → 04_成稿/")
    if media_type in ("视频", "照片视频"):
        print(f"   5. 视频原片放入 → 05_视频/01_原片/")
        print(f"   6. 选片后放入 → 05_视频/02_选片/")
        print(f"   7. 调色后放入 → 05_视频/03_调色/")
        print(f"   8. 成片放入 → 05_视频/04_成片/")
    print(f"   后在管理系统中创建对应项目记录")


def from_json(json_file):
    """从 JSON 文件批量创建"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    for item in data:
        date = item.get("shootDate") or item.get("date", "")
        if not date:
            print(f"⚠️  跳过 (无日期): {item.get('clientCN', 'unknown')}")
            continue
        year = date[:4]
        client = item.get("clientCN", "unknown")
        character = item.get("character", "")
        ip = item.get("ip", "")

        # 从 deliverables 推导 media_type
        deliverables = item.get("deliverables", ["照片"])
        if "照片" in deliverables and "视频" in deliverables:
            media_type = "照片视频"
        elif "视频" in deliverables:
            media_type = "视频"
        else:
            media_type = "照片"

        project_dir, created, meta_path = create_project_folder(
            year, date, client, character, ip, media_type
        )
        print(f"✅ {client} → {project_dir}")

    print(f"\n共创建 {len(data)} 个项目文件夹")


def list_projects():
    """列出已有项目"""
    if not os.path.exists(BASE_DIR):
        print("📭 尚无项目（~/彩華摄影档案/ 目录不存在）")
        return

    for year_dir in sorted(os.listdir(BASE_DIR)):
        year_path = os.path.join(BASE_DIR, year_dir)
        if not os.path.isdir(year_path):
            continue
        projects = [
            d for d in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, d))
        ]
        print(f"\n📅 {year_dir} ({len(projects)} 个项目)")
        for p in sorted(projects):
            p_path = os.path.join(year_path, p)
            meta_path = os.path.join(p_path, "project.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                print(f"   📁 {p}")
                print(
                    f"      客户: {meta.get('clientCN', '?')} | "
                    f"角色: {meta.get('character', '-')} | "
                    f"IP: {meta.get('ip', '-')} | "
                    f"类型: {meta.get('mediaType', '?')}"
                )
            else:
                print(f"   📁 {p} (无元数据)")


def main():
    parser = argparse.ArgumentParser(description="彩華摄影档案文件夹生成器")
    parser.add_argument("--from-json", help="从 JSON 文件批量创建")
    parser.add_argument("--list", action="store_true", help="列出所有已有项目")
    parser.add_argument("--base-dir", help="自定义根目录（默认 ~/彩華摄影档案）")
    args = parser.parse_args()

    if args.base_dir:
        global BASE_DIR
        BASE_DIR = os.path.expanduser(args.base_dir)

    if args.list:
        list_projects()
    elif args.from_json:
        from_json(args.from_json)
    else:
        interactive()


if __name__ == "__main__":
    main()
