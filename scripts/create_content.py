import anthropic
import os
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
theme = os.environ.get("THEME", "家賃")
mode = os.environ.get("MODE", "tiktok")

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

if mode == "tiktok":
    prompt = f"""CREATOR MODE: TikTok台本を生成してください。
テーマ: {theme}に関する日本人のリアルデータ調査

以下の構成で台本を作成:
0-3秒: フック（衝撃の数字か事実）
3-20秒: データの提示
20-28秒: 意外な結論
28-30秒: CTA（診断ツールへ誘導）

必ずA/Bパターン2つ生成すること。
ハッシュタグ10個も追加。"""

elif mode == "x_post":
    prompt = f"""CREATOR MODE: Xポストを生成してください。
テーマ: {theme}に関する日本人のリアルデータ

1行目: 衝撃の数字で始まる
2-4行: データの解説
5行: 診断ツールへの誘導
ハッシュタグ3-5個

A/Bパターン2つ生成すること。"""

else:
    prompt = f"""CREATOR MODE: note記事の下書きを生成してください。
テーマ: {theme}に関する調査レポート

タイトル、リード文、データ解説3セクション、まとめを含めること。"""

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1500,
    messages=[{"role": "user", "content": prompt}]
)

content = message.content[0].text
output_file = data_dir / "latest_content.md"
output_file.write_text(content, encoding="utf-8")
print(content)
