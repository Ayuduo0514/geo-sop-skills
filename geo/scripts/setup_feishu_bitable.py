"""
一次性初始化脚本：创建飞书多维表格 + 8 个字段，回填 config.json
"""
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "https://open.feishu.cn/open-apis"
CONFIG_PATH = Path(__file__).parent / "config.json"


def api(method, path, token=None, body=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read())
    except HTTPError as e:
        print(f"[ERROR] {method} {path}: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    if result.get("code") != 0:
        print(f"[ERROR] API response: {result}", file=sys.stderr)
        sys.exit(1)
    return result


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    app_id = config["feishu"]["app_id"]
    app_secret = config["feishu"]["app_secret"]

    # 1. 获取 tenant token
    resp = api("POST", "/auth/v3/tenant_access_token/internal", body={
        "app_id": app_id, "app_secret": app_secret
    })
    token = resp["tenant_access_token"]
    print(f"[OK] Token acquired")

    # 2. 创建多维表格
    resp = api("POST", "/bitable/v1/apps", token=token, body={
        "name": "GEO意图词库",
        "folder_token": "",  # 放在"我的空间"根目录
    })
    app_token = resp["data"]["app"]["app_token"]
    print(f"[OK] Bitable created: app_token={app_token}")

    # 3. 创建数据表 + 字段
    priority_options = [
        {"name": "高", "color": 0},
        {"name": "中", "color": 1},
        {"name": "低", "color": 2},
        {"name": "待复审", "color": 3},
    ]
    word_type_options = [
        {"name": "精准词", "color": 0},
        {"name": "长尾词", "color": 1},
        {"name": "询问句", "color": 2},
    ]
    fields = [
        {"field_name": "关键词", "type": 1},
        {"field_name": "层级", "type": 1},
        {"field_name": "词类型", "type": 3, "property": {"options": word_type_options}},
        {"field_name": "场景类型", "type": 1},
        {"field_name": "优先级", "type": 3, "property": {"options": priority_options}},
        {"field_name": "意图标签", "type": 1},
        {"field_name": "品牌", "type": 1},
        {"field_name": "来源渠道", "type": 1},
    ]

    resp = api("POST", f"/bitable/v1/apps/{app_token}/tables", token=token, body={
        "table": {
            "name": "意图词库",
            "fields": fields,
        }
    })
    table_id = resp["data"]["table_id"]
    print(f"[OK] Table created: table_id={table_id}")

    # 4. 删除默认的"数据表"
    try:
        tables_resp = api("GET", f"/bitable/v1/apps/{app_token}/tables", token=token)
        for t in tables_resp["data"]["items"]:
            if t["table_id"] != table_id:
                api("DELETE", f"/bitable/v1/apps/{app_token}/tables/{t['table_id']}", token=token)
                print(f"[OK] Deleted default table: {t['table_id']}")
    except Exception:
        pass  # 非关键，忽略

    # 5. 回填 config
    config["feishu"]["bitable_app_token"] = app_token
    config["feishu"]["table_id"] = table_id
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] config.json updated")

    # 输出表格链接
    url = f"https://feishu.cn/base/{app_token}"
    print(f"\n[DONE] 多维表格已创建，打开查看：{url}")


if __name__ == "__main__":
    main()
