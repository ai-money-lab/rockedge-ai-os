name: ROCKEDGE Content Creator

on:
  workflow_dispatch:
    inputs:
      theme:
        description: 'テーマ (例: 家賃, ストレス, 婚活)'
        required: true
        default: '家賃'
      mode:
        description: 'モード (tiktok / x_post / note)'
        required: true
        default: 'tiktok'

jobs:
  create_content:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install anthropic
      - name: Create Content
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          THEME: ${{ github.event.inputs.theme }}
          MODE: ${{ github.event.inputs.mode }}
        run: python scripts/create_content.py
      - uses: actions/upload-artifact@v4
        with:
          name: content-${{ github.event.inputs.theme }}-${{ github.event.inputs.mode }}
          path: data/latest_content.md
