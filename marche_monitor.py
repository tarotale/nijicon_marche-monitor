import requests
import json
import os

# --- 環境変数（GitHub Secretsから取得） ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
CREATOR_ID = "2c_ichimiyayui"
LIST_API = f"https://api.marche-yell.com/api/public/products?creator_marche_id={CREATOR_ID}&limit=20&page=1"
DB_FILE = "last_inventory.json"

def send_line(message):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

def get_detail(p_id):
    url = f"https://api.marche-yell.com/api/public/products/{p_id}?creator_marche_id={CREATOR_ID}"
    try:
        res = requests.get(url, timeout=10)
        return res.json()
    except: return None

# --- (前略：設定部分はそのまま) ---

def main():
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            last_data = json.load(f)

    try:
        res = requests.get(LIST_API, timeout=10)
        products = res.json().get('data', [])
        current_data = {}

        print(f"取得した商品数: {len(products)}") # ログで確認用

        for p in products:
            p_id = str(p.get('id'))
            title = p.get('title', '不明')
            detail = get_detail(p_id)
            if not detail: continue

            stock = detail.get('limit_quantity', 0) - detail.get('sold_quantity', 0)
            current_data[p_id] = {"title": title, "stock": stock}

            # 【テスト用】前回のデータに関わらず、見つけた商品をすべて通知する
            msg = f"\n✅【接続テスト】一宮ゆい\n{title}\n在庫: {stock}個\nhttps://marche-yell.com/{CREATOR_ID}/products/{p_id}"
            
            send_line(msg)
            print(f"テスト通知送信中: {title}")

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Error: {e}")

# --- (後略) ---

if __name__ == "__main__":
    main()
