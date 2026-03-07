# ROCKEDGE AI-OS on GitHub

完全自動化データ収集・マネタイズエンジン

## セットアップ（5分）

### Step 1: このリポジトリをフォーク or クローン
```
git clone https://github.com/YOUR_NAME/rockedge-ai-os.git
```

### Step 2: APIキーをSecretsに登録
GitHub リポジトリ → Settings → Secrets → New secret
- Name: `ANTHROPIC_API_KEY`
- Value: あなたのAPIキー

### Step 3: 完了
次の月曜AM9時に自動で週次レポートが生成される

---

## 手動実行

GitHub → Actions タブ → 実行したいワークフローを選択 → Run workflow

| ワークフロー | タイミング | 内容 |
|---|---|---|
| Weekly Report | 毎週月曜自動 | 週次レポート生成 |
| Content Creator | 手動実行 | TikTok台本・X投稿生成 |
| Data Analyzer | 毎週水曜自動 | データ分析レポート |

---

## ファイル構成

```
.github/workflows/
  weekly_report.yml     毎週月曜自動実行
  create_content.yml    手動: コンテンツ生成
  analyze_data.yml      毎週水曜自動実行
scripts/
  weekly_report.py      週次レポート生成
  create_content.py     コンテンツ生成
  analyze_data.py       データ分析
data/
  summary.json          KPI数値
  raw_data.json         収集データ
  latest_report.md      最新レポート（自動更新）
  analysis_report.md    最新分析（自動更新）
CLAUDE.md               AI-OS 神様プロンプト
```

---

## HIROKIのルーティン

| タイミング | やること | 場所 |
|---|---|---|
| 月曜朝 | latest_report.md を確認 | GitHub |
| コンテンツ必要時 | Content Creator を手動実行 | GitHub Actions |
| 月1回 | summary.json の数字を更新 | GitHub |

---

ROCKEDGE Property Management
