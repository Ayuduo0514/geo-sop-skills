"""
GEO 意图词库 → 飞书多维表格 同步脚本
支持：首次全量写入（create） + 同品牌增量更新（update）

用法：
  python sync_to_feishu.py <intent-library.md> [--mode create|update] [--config config.json]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# --- Feishu API ---

BASE_URL = "https://open.feishu.cn/open-apis"


def feishu_request(method, path, token=None, body=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"[ERROR] Feishu API {method} {path}: {e.code} {error_body}", file=sys.stderr)
        sys.exit(1)


def get_tenant_token(app_id, app_secret):
    resp = feishu_request("POST", "/auth/v3/tenant_access_token/internal", body={
        "app_id": app_id,
        "app_secret": app_secret,
    })
    if resp.get("code") != 0:
        print(f"[ERROR] Auth failed: {resp}", file=sys.stderr)
        sys.exit(1)
    return resp["tenant_access_token"]


def list_records(token, app_token, table_id, page_size=100):
    """获取表格全部记录"""
    records = []
    page_token = None
    while True:
        path = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size={page_size}"
        if page_token:
            path += f"&page_token={page_token}"
        resp = feishu_request("GET", path, token=token)
        if resp.get("code") != 0:
            print(f"[ERROR] List records: {resp}", file=sys.stderr)
            sys.exit(1)
        items = resp.get("data", {}).get("items", [])
        records.extend(items)
        if not resp["data"].get("has_more"):
            break
        page_token = resp["data"]["page_token"]
    return records


def batch_create_records(token, app_token, table_id, records):
    """批量新增记录"""
    # Feishu batch_create limit: 500 per call
    batch_size = 500
    created = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        resp = feishu_request("POST",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            token=token,
            body={"records": [{"fields": r} for r in batch]},
        )
        if resp.get("code") != 0:
            print(f"[ERROR] Batch create: {resp}", file=sys.stderr)
            sys.exit(1)
        created += len(batch)
    return created


def update_record(token, app_token, table_id, record_id, fields):
    """更新单条记录"""
    resp = feishu_request("PUT",
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
        token=token,
        body={"fields": fields},
    )
    if resp.get("code") != 0:
        print(f"[WARN] Update record {record_id}: {resp}", file=sys.stderr)
        return False
    return True


# --- Level descriptions ---

LEVEL_MAP = {
    "L1": "L1 认知层",
    "L2": "L2 探索层",
    "L3": "L3 评估层",
    "L4": "L4 决策层",
    "L5": "L5 口碑层",
}

# L3/L4/L5 = 高（直接触发品牌推荐），L1/L2 = 中（漏斗入口）
LEVEL_PRIORITY = {
    "L1": "中", "L2": "中",
    "L3": "高", "L4": "高", "L5": "高",
}


def expand_level(raw):
    """把 L1 / L2/L3 等展开为带说明的层级"""
    parts = re.split(r'[/、]', raw.strip())
    return " / ".join(LEVEL_MAP.get(p.strip(), p.strip()) for p in parts)


def level_priority(raw):
    """按层级决定优先级：多层取最高"""
    parts = re.split(r'[/、]', raw.strip())
    priorities = [LEVEL_PRIORITY.get(p.strip(), "中") for p in parts]
    return "高" if "高" in priorities else "中"


# --- Markdown Parser ---

def parse_intent_library(md_path):
    """解析意图词库 markdown，每个词拆成独立行返回"""
    text = Path(md_path).read_text(encoding="utf-8")

    # 找到词库主表
    table_match = re.search(r'####\s*词库主表\s*\n(.*?)(?=\n---|\n####|\Z)', text, re.DOTALL)
    if not table_match:
        print("[ERROR] 找不到「词库主表」", file=sys.stderr)
        sys.exit(1)

    table_text = table_match.group(1)
    rows = []
    for line in table_text.strip().split('\n'):
        line = line.strip()
        if not line.startswith('|') or '---' in line or '层级' in line:
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) < 8:
            continue

        level, label, precise, longtail, questions, scene, priority, source = cells[:8]
        level_expanded = expand_level(level)

        def _make_row(word, word_type):
            return {
                "关键词": word,
                "层级": level_expanded,
                "词类型": word_type,
                "优先级": level_priority(level),
                "场景类型": scene,
                "意图标签": label,
                "品牌": "",  # 由 main() 注入
                "来源渠道": source,
            }

        # 精准词
        for w in precise.split('、'):
            w = w.strip()
            if w:
                rows.append(_make_row(w, "精准词"))

        # 长尾词
        for w in longtail.split('、'):
            w = w.strip()
            if w:
                rows.append(_make_row(w, "长尾词"))

        # 询问句
        for w in re.split(r'[？?]', questions):
            w = w.strip()
            if w:
                rows.append(_make_row(w + "？", "询问句"))

    return rows


# --- Sync Logic ---

def sync_create(token, config, records):
    """首次全量写入"""
    app_token = config["feishu"]["bitable_app_token"]
    table_id = config["feishu"]["table_id"]
    count = batch_create_records(token, app_token, table_id, records)
    print(f"[OK] 全量写入完成：{count} 条记录")


def sync_update(token, config, new_records):
    """增量更新：按 意图标签+关键词 upsert"""
    app_token = config["feishu"]["bitable_app_token"]
    table_id = config["feishu"]["table_id"]

    # 拉取现有记录，用 意图标签+关键词 做复合键
    existing = list_records(token, app_token, table_id)
    existing_map = {}
    for r in existing:
        f = r["fields"]
        key = (f.get("意图标签", ""), f.get("关键词", ""))
        if key[0] and key[1]:
            existing_map[key] = r

    new_keys = {(r["意图标签"], r["关键词"]) for r in new_records}
    created, updated, stale = 0, 0, 0

    # Upsert
    to_create = []
    for rec in new_records:
        key = (rec["意图标签"], rec["关键词"])
        if key in existing_map:
            record_id = existing_map[key]["record_id"]
            if update_record(token, app_token, table_id, record_id, rec):
                updated += 1
        else:
            to_create.append(rec)

    if to_create:
        created = batch_create_records(token, app_token, table_id, to_create)

    # 标记失效词（旧表有、新生成没有的）
    for key, r in existing_map.items():
        if key not in new_keys:
            record_id = r["record_id"]
            update_record(token, app_token, table_id, record_id, {"优先级": "待复审"})
            stale += 1

    print(f"[OK] 增量更新完成：新增 {created}，更新 {updated}，标记待复审 {stale}")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="GEO 意图词库 → 飞书多维表格同步")
    parser.add_argument("input", help="意图词库 markdown 文件路径")
    parser.add_argument("--mode", choices=["create", "update"], default="create",
                        help="create=全量写入，update=增量更新（默认 create）")
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.json"),
                        help="配置文件路径")
    args = parser.parse_args()

    # 加载配置
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] 配置文件不存在：{config_path}", file=sys.stderr)
        sys.exit(1)
    config = json.loads(config_path.read_text(encoding="utf-8"))

    for key in ["app_id", "app_secret", "bitable_app_token", "table_id"]:
        if not config["feishu"].get(key):
            print(f"[ERROR] config.json 中 feishu.{key} 为空", file=sys.stderr)
            sys.exit(1)

    # 解析词库
    records = parse_intent_library(args.input)

    # 从文件名提取品牌名并注入每条记录
    brand = Path(args.input).stem.replace("-intent-library", "")
    for r in records:
        r["品牌"] = brand
    print(f"[INFO] 品牌：{brand}，解析到 {len(records)} 条意图词")

    # 认证
    token = get_tenant_token(config["feishu"]["app_id"], config["feishu"]["app_secret"])

    # 同步
    if args.mode == "create":
        sync_create(token, config, records)
    else:
        sync_update(token, config, records)


if __name__ == "__main__":
    main()
