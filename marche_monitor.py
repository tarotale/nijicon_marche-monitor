import requests
import json
import os

# --- 環境変数 ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
CREATOR_ID = "2c_ichimiyayui"

# URL
LIST_API = f"https://api.marche-yell.com/api/public/products?creator_marche_id={CREATOR_ID}"
DB_FILE = "last_inventory.json"

def send_line(message):
    if not LINE_TOKEN or not USER_ID:
        print("LINE設定が不足しています")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def get_detail(p_id, headers):
    url = f"https://api.marche-yell.com/api/public/products/{p_id}?creator_marche_id={CREATOR_ID}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        # 詳細APIも「product」という単数形のキーに入っている可能性があるため考慮
        data = res.json()
        return data.get('product') if 'product' in data else data
    except Exception as e:
        print(f"詳細取得エラー(ID:{p_id}): {e}")
        return None

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://marche-yell.com",
        "Referer": f"https://marche-yell.com/{CREATOR_ID}/"
    }

    try:
        print(f"アクセス開始: {LIST_API}")
        res = requests.get(LIST_API, headers=headers, timeout=15)
        res.raise_for_status()
        
        raw_res = res.json()
        
        # 【重要】ここを data から products に修正しました
        products = raw_res.get('products', [])
        print(f"取得した商品数: {len(products)}")

        current_data = {}

        for p in products:
            p_id = str(p.get('id'))
            title = p.get('title', '不明')
            
            # リストAPIの時点で在庫情報(limit/sold)が含まれている場合があるため、まずそれを試す
            limit = p.get('limit_quantity')
            sold = p.get('sold_quantity')

            # もしリストに在庫情報がなければ、詳細APIを叩く
            if limit is None or sold is None:
                detail = get_detail(p_id, headers)
                if detail:
                    limit = detail.get('limit_quantity', 0)
                    sold = detail.get('sold_quantity', 0)
                else:
                    limit, sold = 0, 0

            stock = limit - sold
            current_data[p_id] = {"title": title, "stock": stock}

            # テスト送信
            msg = f"\n✅【接続テスト】一宮ゆい\n{title}\n在庫: 残り {stock} / 全 {limit}個\nhttps://marche-yell.com/{CREATOR_ID}/products/{p_id}"
            print(f"通知送信中: {title}")
            send_line(msg)

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"メイン処理でエラー発生: {e}")

if __name__ == "__main__":
    main()
