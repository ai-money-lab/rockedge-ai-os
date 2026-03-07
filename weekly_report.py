name: ROCKEDGE Weekly Report

on:
  schedule:
    - cron: '0 0 * * 1'  # 毎週月曜 AM9:00 JST (UTC 0:00)
  workflow_dispatch:       # 手動実行ボタン

jobs:
  generate_report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install anthropic

      - name: Generate Weekly Report
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/weekly_report.py

      - name: Save Report
        uses: actions/upload-artifact@v4
        with:
          name: weekly-report
          path: data/latest_report.md

      - name: Commit Report to Repo
        run: |
          git config user.name "ROCKEDGE AI-OS"
          git config user.email "ai-os@rockedge.jp"
          git add data/
          git diff --staged --quiet || git commit -m "Weekly Report $(date +%Y-%m-%d)"
          git push
