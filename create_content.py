name: ROCKEDGE Data Analyzer

on:
  schedule:
    - cron: '0 0 * * 3'  # 毎週水曜（データ分析日）
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install anthropic
      - name: Analyze Data
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/analyze_data.py
      - uses: actions/upload-artifact@v4
        with:
          name: analysis-report
          path: data/analysis_report.md
      - name: Commit Analysis
        run: |
          git config user.name "ROCKEDGE AI-OS"
          git config user.email "ai-os@rockedge.jp"
          git add data/
          git diff --staged --quiet || git commit -m "Data Analysis $(date +%Y-%m-%d)"
          git push
