import anthropic
import json
import os
from datetime import datetime
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

summary_file = data_dir / "summary.json"
summary = {}
if summary_file.exists():
    summary = json.loads(summary_file.read_text())

total_data = summary.get("total_data", 0)
last_week_data = summary.get("last_week_data", 0)
total_posts = summary.get("total_posts", 0)
est_revenue = summary.get("est_revenue", 0)

prompt = f"""You are the DIRECTOR AI of ROCKEDGE AI-OS.
Generate a weekly report for HIROKI in Japanese.

Current stats:
- Total data collected: {total_data} entries
- New data this week: {last_week_data} entries  
- Total posts published: {total_posts}
- Estimated monthly revenue: {est_revenue} yen

Generate a detailed weekly report in Japanese with:
1. Highlight (1 sentence)
2. Numbers summary
3. What AI auto-executed this week (3 items)
4. One YES/NO question for HIROKI
5. Next week plan
"""

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)

report = message.content[0].text
output_file = data_dir / "latest_report.md"
output_file.write_text(report, encoding="utf-8")
print(report)
