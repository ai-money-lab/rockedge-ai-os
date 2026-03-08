#!/usr/bin/env python3
"""
ROCKEDGE Content Creator
========================
手動実行（GitHub Actions workflow_dispatch）
- テーマ × モードでROCKEDGE専用コンテンツを生成
- TikTok台本・X投稿・note記事に対応
- analyze_data.py のバズネタも活用
"""

import anthropic
import os
import json
import datetime
import re
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

JST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(JST)

# 環境変数からテーマ・モードを取得
theme = os.environ.get("THEME", "不動産投資")
mode  = os.environ.get("MODE", "tiktok")

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# ─────────────────────────────────────────
# バズネタデータを読み込む（analyze_data.py が生成）
# ─────────────────────────────────────────
buzz_file = data_dir / "buzz_topics.json"
buzz_context = ""
if buzz_file.exists():
    buzz_data = json.loads(buzz_file.read_text())
    topics = buzz_data.get("buzz_topics", [])
    relevant = [t for t in topics if mode in t.get("suitable_modes", [])]
    if relevant:
        buzz_context = f"\n【今週のバズネタ候補（参考）】\n{json.dumps(relevant[:3], ensure_ascii=False, indent=2)}\n"

# ─────────────────────────────────────────
# ROCKEDGEのペルソナ設定
# ─────────────────────────────────────────
ROCKEDGE_PERSONA = """
あなたはROCKEDGE Property Managementの宮尾大樹のコンテンツクリエイターです。

【ペルソナ】
- 不動産業界24年のプロ
- ROCKEDGE取締役（東京銀座・浦和拠点）
- MATTERPORT 3D撮影で物件の付加価値を提供
- AIを活用した最先端の不動産サービスを展開
- 東京・埼玉（浦和・大宮・川口）エリアに精通

【コンテンツスタイル】
- 業界24年のリアルな経験談を数字で語る
- 「知らないと損する」視点で視聴者に価値を提供
- 押し付けでなく、プロとして自然にROCKEDGEの強みを伝える
- 難しい不動産用語を分かりやすく解説
- ネガティブな業界慣習もオープンに話す（信頼感UP）

【NGワード】
- 「最高」「超」「やばい」などの俗語
- 根拠のない断言（「絶対儲かる」等）
- 競合他社の名指し批判
"""

# ─────────────────────────────────────────
# テーマ別コンテキスト
# ─────────────────────────────────────────
THEME_CONTEXT = {
    "不動産投資": "東京・埼玉エリアの投資用不動産、利回り、キャッシュフロー、出口戦略",
    "物件紹介": "MATTERPORT 3D内覧、物件の魅力の伝え方、購入・賃貸の判断基準",
    "リノベーション": "中古物件のリノベ事例、コスト感、業者選びのポイント",
    "賃貸管理": "オーナー目線の管理のコツ、入居者トラブル対処法、空室対策",
    "家電量販店リフォーム": "でんきちのリフォームコーディネート、水回り・設備工事の実態",
    "MATTERPORT": "3D撮影の活用方法、遠隔内覧の価値、物件成約率アップの秘訣",
    "業界裏話": "不動産業界24年で見てきたリアル、業者の選び方、騙されない方法",
    "市場分析": "東京・埼玉の価格動向、2026年の不動産市場予測、エリア別比較",
    "B.A.D GYM": "岩崎ビル2F、52坪のフィットネスジム開業計画、ベンチプレス世界王者との取り組み",
}

context = THEME_CONTEXT.get(theme, f"{theme}に関するROCKEDGEの専門知識")

# ─────────────────────────────────────────
# モード別コンテンツ生成
# ─────────────────────────────────────────
if mode == "tiktok":
    prompt = f"""{ROCKEDGE_PERSONA}
{buzz_context}
テーマ：{theme}
コンテキスト：{context}

以下の構成でTikTok台本を2パターン（A/B）作成してください。

【構成】
- 0〜3秒：フック（視聴者が止まる衝撃的な一言・数字）
- 3〜20秒：データ・事実の提示（具体的な数字を必ず入れる）
- 20〜28秒：意外な結論・プロならではの視点
- 28〜30秒：CTA（「他にも知りたい方はフォロー」等・売り込みNG）

【ルール】
- 読み上げやすい話し言葉（句読点で自然な間を作る）
- 各パターン60〜90秒で読める長さ
- ハッシュタグ10個（#不動産投資 #ROCKEDGE #宮尾大樹 等を含める）

出力形式：
## パターンA
**フック：**（冒頭の一言）
**台本：**（全文）
**ハッシュタグ：**

## パターンB
**フック：**（冒頭の一言）
**台本：**（全文）
**ハッシュタグ：**
"""

elif mode == "x_post":
    prompt = f"""{ROCKEDGE_PERSONA}
{buzz_context}
テーマ：{theme}
コンテキスト：{context}

以下の構成でX（Twitter）投稿を2パターン（A/B）作成してください。

【構成】
- 1行目：衝撃的な数字・事実で始まる（絵文字OK）
- 2〜4行：データの解説（簡潔に）
- 5行目：ROCKEDGEならではの視点・アドバイス
- 最後：ハッシュタグ3〜5個

【ルール】
- 140文字×3ツイートのスレッド形式
- 「1/3」「2/3」「3/3」で番号付け
- 引用リツイートされやすい「保存したくなる」内容

出力形式：
## パターンA
1/3 （本文）
2/3 （本文）
3/3 （本文）
ハッシュタグ：

## パターンB
（同様）
"""

elif mode == "note":
    prompt = f"""{ROCKEDGE_PERSONA}
{buzz_context}
テーマ：{theme}
コンテキスト：{context}

以下の構成でnote記事を作成してください。

【構成】
1. タイトル（クリックされやすい・数字を入れる）
2. リード文（200文字・読者の悩みに共感）
3. 本文（見出し3〜5個・各500〜800文字）
   - 業界24年のリアルな経験談
   - 具体的な数字・事例
   - 読者が今日から使えるアドバイス
4. まとめ（ROCKEDGEへの自然な導線・押し売りNG）

【ルール】
- 全体2000〜3000文字
- 専門用語は必ず解説
- 「不動産のプロが教える」視点を一貫して維持
"""

else:
    prompt = f"""{ROCKEDGE_PERSONA}
テーマ：{theme}
コンテキスト：{context}

ROCKEDGEのSNS・マーケティングに使えるコンテンツを作成してください。
"""

# ─────────────────────────────────────────
# コンテンツ生成
# ─────────────────────────────────────────
print(f"🎨 コンテンツ生成中... テーマ：{theme} / モード：{mode}")

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=2500,
    messages=[{"role": "user", "content": prompt}]
)

content = message.content[0].text

# ─────────────────────────────────────────
# 保存
# ─────────────────────────────────────────
header = f"""# 🎬 ROCKEDGE Content: {theme} × {mode.upper()}
**生成日時：{NOW.strftime('%Y年%m月%d日 %H:%M')} JST**
**テーマ：{theme} | モード：{mode}**

---

"""

output_file = data_dir / "latest_content.md"
output_file.write_text(header + content, encoding="utf-8")

# テーマ・日付別にも保存
safe_theme = re.sub(r'[^\w\s-]', '', theme).strip().replace(' ', '_')
dated_file = data_dir / f"content_{safe_theme}_{mode}_{NOW.strftime('%Y%m%d')}.md"
dated_file.write_text(header + content, encoding="utf-8")

print(f"✅ コンテンツ保存: {dated_file}")
print("\n" + "="*50)
print(f"テーマ：{theme} / モード：{mode}")
print("="*50)
print(content[:500] + "...\n（全文はファイルを確認）")
