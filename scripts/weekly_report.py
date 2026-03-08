#!/usr/bin/env python3
"""
ROCKEDGE Weekly Report Generator
毎週土曜 09:00 JST に GitHub Actions で自動実行
- Gmail から ANDPAD・重要メールを収集
- Claude API で分析・サマリー生成
- Markdown レポートをリポジトリに保存
"""

import os
import json
import base64
import datetime
import re
from pathlib import Path

import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_TOKEN_JSON  = os.environ["GMAIL_TOKEN_JSON"]

JST = datetime.timezone(datetime.timedelta(hours=9))
NOW  = datetime.datetime.now(JST)
WEEK_START = NOW - datetime.timedelta(days=7)

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def get_gmail_service():
    token_data = json.loads(GMAIL_TOKEN_JSON)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def get_message_body(msg):
    payload = msg.get("payload", {})
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return body[:2000]


def fetch_weekly_emails(service):
    after_epoch = int(WEEK_START.timestamp())
    queries = {
        "andpad":    f"after:{after_epoch} (subject:ANDPAD OR subject:完工 OR subject:入金 OR subject:現調 OR subject:着工)",
        "important": f"after:{after_epoch} is:important -from:noreply -from:no-reply -category:promotions",
        "github":    f"after:{after_epoch} from:notifications@github.com rockedge",
    }
    results = {}
    for key, q in queries.items():
        res = service.users().messages().list(userId="me", q=q, maxResults=30).execute()
        messages = res.get("messages", [])
        items = []
        for m in messages[:15]:
            detail = service.users().messages().get(userId="me", id=m["id"], format="full").execute()
            headers = {h["name"]: h["value"] for h in detail["payload"].get("headers", [])}
            items.append({
                "subject": headers.get("Subject", "(件名なし)"),
                "from":    headers.get("From", ""),
                "date":    headers.get("Date", ""),
                "body":    get_message_body(detail),
            })
        results[key] = items
    return results


def analyze_with_claude(emails: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    andpad_prompt = f"""
以下は今週（{WEEK_START.strftime('%m/%d')}〜{NOW.strftime('%m/%d')}）のANDPADメール一覧です。

{json.dumps(emails['andpad'], ensure_ascii=False, indent=2)}

以下のJSON形式で集計してください：
{{
  "total_count": 件数,
  "completion_count": 完工件数,
  "payment_count": 入金件数,
  "site_survey_count": 現調件数,
  "start_count": 着工件数,
  "total_payment_amount": 入金合計金額（数値、不明なら0）,
  "urgent_items": ["至急対応が必要な案件の説明"],
  "summary": "今週のANDPAD業務全体の50文字以内サマリー",
  "cases": [
    {{"customer": "顧客名", "work_type": "工事種別", "event": "完工|入金|現調|着工", "amount": 金額または0, "worker": "担当者名"}}
  ]
}}
JSONのみ出力。説明文不要。
"""

    important_prompt = f"""
以下は今週の重要メール一覧です。

{json.dumps(emails['important'][:10], ensure_ascii=False, indent=2)}

以下のJSON形式で分析してください：
{{
  "total_count": 件数,
  "action_required": ["要対応メールの件名と必要なアクション"],
  "highlights": ["今週の重要トピック（最大5件）"],
  "summary": "今週の重要メール全体の50文字以内サマリー"
}}
JSONのみ出力。
"""

    def safe_parse(text):
        cleaned = re.sub(r"```json\n?|```\n?", "", text).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {}

    andpad_res = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": andpad_prompt}]
    )
    important_res = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": important_prompt}]
    )

    return {
        "andpad":    safe_parse(andpad_res.content[0].text),
        "important": safe_parse(important_res.content[0].text),
    }


def build_markdown(analysis: dict, emails: dict) -> str:
    a = analysis.get("andpad", {})
    imp = analysis.get("important", {})
    week_label = f"{WEEK_START.strftime('%Y年%m月%d日')}〜{NOW.strftime('%m月%d日')}"

    cases = a.get("cases", [])
    if cases:
        case_table = "| 顧客名 | 工事種別 | イベント | 金額 | 担当者 |\n"
        case_table += "|--------|----------|----------|------|--------|\n"
        for c in cases:
            amt = f"¥{c.get('amount', 0):,}" if c.get('amount') else "—"
            case_table += f"| {c.get('customer','—')} | {c.get('work_type','—')} | {c.get('event','—')} | {amt} | {c.get('worker','—')} |\n"
    else:
        case_table = "_今週のANDPAD案件なし_\n"

    action_items = imp.get("action_required", [])
    action_md = "\n".join(f"- {item}" for item in action_items) if action_items else "_なし_"

    highlights = imp.get("highlights", [])
    highlight_md = "\n".join(f"- {h}" for h in highlights) if highlights else "_特記事項なし_"

    github_md = ""
    if emails.get("github"):
        github_md = "\n## ⚠️ GitHub Actions 通知\n\n"
        for m in emails["github"][:3]:
            github_md += f"- **{m['subject']}**\n"

    total_payment = a.get("total_payment_amount", 0)
    payment_str = f"¥{total_payment:,}" if total_payment else "集計中"

    urgent_lines = "\n".join(f"- ⚡ {item}" for item in a.get('urgent_items', []))
    if not urgent_lines:
        urgent_lines = "_なし_"

    report = f"""# 📊 ROCKEDGE Weekly Report
**対象期間：{week_label}**
生成日時：{NOW.strftime('%Y年%m月%d日 %H:%M')} JST

---

## 🏗️ ANDPAD 施工コーディネーター 週次サマリー

> {a.get('summary', '—')}

| 指標 | 件数 |
|------|------|
| 総メール数 | {a.get('total_count', 0)}件 |
| 完工報告 | {a.get('completion_count', 0)}件 |
| 入金報告 | {a.get('payment_count', 0)}件 |
| 現調実施 | {a.get('site_survey_count', 0)}件 |
| 着工連絡 | {a.get('start_count', 0)}件 |
| **今週入金合計** | **{payment_str}** |

### 今週の案件一覧

{case_table}

---

## 🔴 至急対応が必要な案件

{urgent_lines}

---

## 📬 重要メール サマリー

> {imp.get('summary', '—')}

### 要対応メール

{action_md}

### 今週のハイライト

{highlight_md}
{github_md}
---

## 📅 来週に向けて

- [ ] 上記「至急対応」案件のフォローアップ
- [ ] 入金未確認案件の確認
- [ ] 現調予定案件の日程調整
- [ ] ANDPAD 進捗更新

---
_このレポートは [ROCKEDGE AI OS](https://github.com/ai-money-lab/rockedge-ai-os) が自動生成しました_
"""
    return report


def main():
    print("📧 Gmail からメールを取得中...")
    service = get_gmail_service()
    emails = fetch_weekly_emails(service)

    andpad_count = len(emails.get("andpad", []))
    important_count = len(emails.get("important", []))
    print(f"  ANDPAD: {andpad_count}件 / 重要: {important_count}件")

    print("🤖 Claude で分析中...")
    analysis = analyze_with_claude(emails)

    print("📝 レポート生成中...")
    report_md = build_markdown(analysis, emails)

    filename = REPORT_DIR / f"weekly_{NOW.strftime('%Y-%m-%d')}.md"
    filename.write_text(report_md, encoding="utf-8")
    print(f"✅ レポート保存: {filename}")

    latest = REPORT_DIR / "latest.md"
    latest.write_text(report_md, encoding="utf-8")

    summary_json = {
        "generated_at": NOW.isoformat(),
        "week": f"{WEEK_START.strftime('%Y-%m-%d')} ~ {NOW.strftime('%Y-%m-%d')}",
        "andpad": analysis.get("andpad", {}),
        "important_count": important_count,
    }
    (REPORT_DIR / "latest_summary.json").write_text(
        json.dumps(summary_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print("✅ 完了！")


if __name__ == "__main__":
    main()
