import requests
import json
import os
from datetime import datetime, timedelta

# --- 設定 ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
DB_FILE = "2c_last_inventory.json"

TARGET_CREATORS = [
    {"id": "2c_ichimiyayui", "name": "一宮ゆい"},
    {"id": "2c_yagiharuka", "name": "八木遥叶"},
    {"id": "2c_matobakarin", "name": "的場華鈴"},
    {"id": "2c_hirutaairi", "name": "蛭田愛梨"},
    {"id": "2c_kawabatayu", "name": "川端優"},
    {"id": "2c_itomai", "name": "伊藤舞依"},
    {"id": "2c_kuriharamay", "name": "栗原舞優"},
    {"id": "2c_maejimaano", "name": "前嶋杏乃"},
    {"id": "2c_yamatoao", "name": "大和明桜"},
    {"id": "2c_ishihamamei", "name": "石浜芽衣"},
    {"id": "2c_obayashiyuik", "name": "尾林結花"},
    {"id": "2c_kumamotomari", "name": "隈本茉莉奈"},
    {"id": "2c_aoyamauta", "name": "青山詩"},
]

def convert_to_jst_full(utc_str):
    if not utc_str: return "0000-00-00 00:00"
    try:
        dt_utc = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        dt_jst = dt_utc + timedelta(hours=9)
        return dt_jst.strftime("%Y-%m-%d %H:%M")
    except:
        return "0000-00-00 00:00"

def send_line(message):
    if not LINE_TOKEN: return
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                last_data = json.load(f)
            except:
                last_data = {}

    current_all_data = last_data.copy()

    for creator in TARGET_CREATORS:
        c_name = creator["name"]
        c_id = creator["id"]
        
        list_api = f"https://api.marche-yell.com/api/public/products?creator_marche_id={c_id}&limit=50"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            res = requests.get(list_api, headers=headers, timeout=15)
            res.raise_for_status()
            products = res.json().get('products', [])
            
            for p in products:
                p_id = str(p.get('id'))
                title = p.get('title', '不明')
                start_jst = convert_to_jst_full(p.get('sales_start_at'))
                limit = p.get('limit_quantity', 0)
                stock = limit - p.get('sold_quantity', 0)
                db_key = f"{c_id}_{p_id}"
                
                msg = ""
                if db_key not in last_data:
                    msg = f"🌈【虹コン/新着】{c_name}\n📝 {title}\n📅 開始: {start_jst}\n📦 在庫: {stock}/{limit}\n🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                elif stock > 0 and last_data[db_key].get('stock', 0) == 0:
                    msg = f"🔄【虹コン/復活】{c_name}\n📝 {title}\n📦 残り {stock}個！\n🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                
                if msg:
                    send_line(msg)

                current_all_data[db_key] = {
                    "name": c_name,
                    "title": title, 
                    "stock": stock, 
                    "limit": limit,
                    "start": start_jst,
                    "creator_id": c_id
                }
        except Exception as e:
            print(f"Error ({c_name}): {e}")

    # JSON保存
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(current_all_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
