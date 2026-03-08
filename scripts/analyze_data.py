#!/usr/bin/env python3
"""
ROCKEDGE Data Analyzer
======================
毎週水曜 09:00 JST に GitHub Actions で自動実行
- ANDPADレポート・週次レポートのデータを集計
- 東京・埼玉エリアの不動産市場トレンドを分析
- TikTok/X投稿に使えるバズネタを抽出
- B2B向け提案データを生成
"""

import anthropic
import json
import os
import datetime
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

JST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(JST)

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
reports_dir = Path("reports")

# ─────────────────────────────────────────
# 既存データの読み込み
# ─────────────────────────────────────────
# 週次レポートのJSONサマリーを読み込む
latest_summary_file = reports_dir / "latest_summary.json"
weekly_summary = {}
if latest_summary_file.exists():
    weekly_summary = json.loads(latest_summary_file.read_text())

# 過去の分析データを読み込む（累積）
raw_file = data_dir / "raw_data.json"
raw_data = []
if raw_file.exists():
    raw_data = json.loads(raw_file.read_text())

# ─────────────────────────────────────────
# ROCKEDGEの実績データを追記
# ─────────────────────────────────────────
# ANDPADレポートから今週のデータを追加
andpad_data = weekly_summary.get("andpad", {})
if andpad_data:
    new_record = {
        "week": weekly_summary.get("week", NOW.strftime("%Y-%m-%d")),
        "completion_count": andpad_data.get("completion_count", 0),
        "payment_count": andpad_data.get("payment_count", 0),
        "site_survey_count": andpad_data.get("site_survey_count", 0),
        "total_payment": andpad_data.get("total_payment_amount", 0),
        "urgent_count": len(andpad_data.get("urgent_items", [])),
        "cases": andpad_data.get("cases", []),
    }
    # 重複チェックして追加
    existing_weeks = [r.get("week") for r in raw_data]
    if new_record["week"] not in existing_weeks:
        raw_data.append(new_record)
        raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2))

# データがない場合はサンプルを使用
if not raw_data:
    raw_data = [
        {"week": "2026-02-22", "completion_count": 8, "payment_count": 6,
         "site_survey_count": 4, "total_payment": 850000, "urgent_count": 1},
        {"week": "2026-03-01", "completion_count": 12, "payment_count": 9,
         "site_survey_count": 6, "total_payment": 1240000, "urgent_count": 2},
        {"week": "2026-03-08", "completion_count": 10, "payment_count": 8,
         "site_survey_count": 5, "total_payment": 980000, "urgent_count": 0},
    ]

# ─────────────────────────────────────────
# Claude による分析
# ─────────────────────────────────────────
prompt = f"""あなたはROCKEDGE Property Managementの専属データアナリストです。
宮尾大樹（不動産業界24年・ROCKEDGE取締役）のために分析レポートを作成します。

【会社概要】
- 株式会社ROCKEDGE Property Management（東京銀座・浦和サテライト）
- 業務：不動産売買・賃貸仲介・賃貸管理・リノベーション・家電量販店リフォームコーディネーター
- 強み：MATTERPORT 3D撮影・AIを活用した付加価値サービス
- 対象エリア：東京・埼玉（浦和・大宮・川口など）

【今週の集計データ】
{json.dumps(raw_data[-4:], ensure_ascii=False, indent=2)}

以下を分析してMarkdownレポートを作成してください：

1. **施工コーディネーター 実績分析**
   - 完工・入金・現調の週次トレンド
   - 入金金額の推移と予測
   - 繁忙期パターンの発見

2. **バズコンテンツネタ TOP3**（TikTok・X向け）
   - 衝撃的な数字・事実（不動産業界24年の視点から）
   - 「知らないと損する」系の情報
   - 各ネタにバズスコア（100点満点）を付ける

3. **今週の業務改善提案**
   - 効率化できるポイント
   - AIで自動化できる作業
   - 売上アップのチャンス

4. **来週の注目ポイント**
   - 先週と比べて注意すべき変化
   - フォローが必要な案件傾向

レポートはMarkdown形式で、絵文字を使って読みやすく作成してください。
"""

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)

report = message.content[0].text

# ─────────────────────────────────────────
# レポート保存
# ─────────────────────────────────────────
header = f"""# 📈 ROCKEDGE Data Analysis Report
**生成日時：{NOW.strftime('%Y年%m月%d日 %H:%M')} JST**
**対象：直近4週間の施工コーディネーター実績**

---

"""

output_file = data_dir / "analysis_report.md"
output_file.write_text(header + report, encoding="utf-8")
print(f"✅ 分析レポート保存: {output_file}")

# latest にもコピー
(data_dir / "latest_analysis.md").write_text(header + report, encoding="utf-8")

# バズネタだけ抽出してJSONで保存（create_content.py が使用）
buzz_prompt = f"""
以下の分析レポートからバズコンテンツネタだけを抽出してJSON形式で出力してください。

{report}

出力形式：
{{
  "buzz_topics": [
    {{
      "title": "ネタのタイトル",
      "hook": "冒頭の衝撃的な一文",
      "data_point": "使うデータ・数字",
      "score": バズスコア数値,
      "suitable_modes": ["tiktok", "x_post", "note"]
    }}
  ]
}}
JSONのみ出力。
"""

buzz_res = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=800,
    messages=[{"role": "user", "content": buzz_prompt}]
)

import re
buzz_text = re.sub(r"```json\n?|```\n?", "", buzz_res.content[0].text).strip()
try:
    buzz_data = json.loads(buzz_text)
    (data_dir / "buzz_topics.json").write_text(
        json.dumps(buzz_data, ensure_ascii=False, indent=2)
    )
    print(f"✅ バズネタ {len(buzz_data.get('buzz_topics', []))}件 保存")
except Exception as e:
    print(f"⚠️ バズネタJSON保存エラー: {e}")

print("✅ 分析完了！")
