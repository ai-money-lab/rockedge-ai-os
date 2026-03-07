import anthropic
import json
import os
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

raw_file = data_dir / "raw_data.json"
raw_data = []
if raw_file.exists():
    raw_data = json.loads(raw_file.read_text())

if not raw_data:
    raw_data = [
        {"area": "東京23区", "rent": 9.5, "age": "30代", "verdict": "高い"},
        {"area": "埼玉", "rent": 6.2, "age": "20代", "verdict": "適正"},
        {"area": "横浜", "rent": 8.1, "age": "40代", "verdict": "適正"},
    ]

prompt = f"""ANALYST MODE: 以下のデータを分析してください。

データ件数: {len(raw_data)}件
データ: {json.dumps(raw_data[:20], ensure_ascii=False)}

以下を日本語で実行:
1. 基本統計（平均・中央値・最大最小）
2. セグメント別比較（地域・年代）
3. 最も意外な発見
4. バズスコア算出（衝撃性40+自己関連性30+シェア欲求30）
5. TikTokで使えるトップ3インサイト
6. B2Bで売れるデータの価値評価
"""

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)

report = message.content[0].text
output_file = data_dir / "analysis_report.md"
output_file.write_text(report, encoding="utf-8")
print(report)
