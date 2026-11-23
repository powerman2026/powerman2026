import json
import subprocess
from collections import Counter
from html import escape
from pathlib import Path

def query(fields, cursor=None):
    args = ["gh", "api", "graphql", "-f", "query=" + fields]
    if cursor:
        args += ["-f", "cursor=" + cursor]
    return json.loads(subprocess.check_output(args))["data"]["user"]

user = query('{user(login:"powerman2026"){pullRequests{totalCount} issues{totalCount} contributionsCollection{totalCommitContributions contributionCalendar{weeks{contributionDays{date contributionCount contributionLevel}}}}}}')
languages = Counter()
colors = {}
stars = 0
cursor = None
while True:
    repos = query('query($cursor:String){user(login:"powerman2026"){repositories(first:100,after:$cursor,ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false){pageInfo{endCursor hasNextPage} nodes{stargazerCount name}}}}', cursor)["repositories"]
    for repo in repos["nodes"]:
        stars += repo["stargazerCount"]
        sizes = json.loads(subprocess.check_output(["gh", "api", "repos/powerman2026/" + repo["name"] + "/languages"]))
        languages.update(sizes)
    if not repos["pageInfo"]["hasNextPage"]:
        break
    cursor = repos["pageInfo"]["endCursor"]

activity = user["contributionsCollection"]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 360" font-family="system-ui,sans-serif"><rect width="860" height="360" rx="14" fill="#ffffff"/>']
def label(x, y, value, size=15, color="#344054", bold=False):
    weight = 650 if bold else 400
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(value))}</text>')

label(26, 39, "powerman2026 的 GitHub 统计", 21, "#0969da", True)
label(448, 39, "常用语言", 21, "#0969da", True)
for i, (name, value) in enumerate([("公开原创仓库获星", stars), ("近一年提交", activity["totalCommitContributions"]), ("发起的 PR", user["pullRequests"]["totalCount"]), ("提出的 Issue", user["issues"]["totalCount"])]):
    label(26, 78 + 30*i, name)
    label(260, 78 + 30*i, value, bold=True)
items = languages.most_common(4)
remaining = sum(languages.values()) - sum(n for _, n in items)
if remaining:
    items.append(("其他", remaining))
offset = 0
for i, ((name, count), color) in enumerate(zip(items, ["#0969da","#e3b341","#d85d39","#8250df","#319487"])):
    pct = 100 * count / sum(languages.values())
    y = 70 + 25*i
    svg.append(f'<circle cx="453" cy="{y-5}" r="5" fill="{color}"/>')
    label(465, y, f"{name}  {pct:.1f}%", 14)
    svg.append(f'<circle cx="753" cy="118" r="55" fill="none" stroke="{color}" stroke-width="15" pathLength="100" stroke-dasharray="{pct} {100-pct}" stroke-dashoffset="{-offset}" transform="rotate(-90 753 118)"/>')
    offset += pct
weeks = activity["contributionCalendar"]["weeks"]
label(26, 218, "近一年贡献日历", 18, "#0969da", True)
palette = dict(zip(["NONE","FIRST_QUARTILE","SECOND_QUARTILE","THIRD_QUARTILE","FOURTH_QUARTILE"], ["#eff2f5","#aceebb","#4ac26b","#2da44e","#116329"]))
from datetime import date
for x, week in enumerate(weeks):
    for day in week["contributionDays"]:
        row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        svg.append(f'<rect x="{26+x*15}" y="{238+row*15}" width="12" height="12" rx="3" fill="{palette[day["contributionLevel"]]}"><title>{day["date"]} · {day["contributionCount"]} 次贡献</title></rect>')
Path("assets/stats.svg").write_text("".join(svg) + "</svg>\n")
