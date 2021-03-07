import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Template

# =================================================================
# CALCULATIONS
# =================================================================

# =================================================================
# read file
file_path = "Disc Golf Log.xlsx"
sheet_name = "Log"

log = pd.read_excel(file_path, sheet_name=sheet_name)
# =================================================================


# =================================================================
# elo parameters
B = 10
SEP = 100
K = 4
START = 100

# player setup
players = ['Jack', 'Tanner', 'Rohan', 'Nick', 'Josh', 'Luke']
elo = {p : START for p in players}
record = {p : [0, 0, 0] for p in players}
# =================================================================


# =================================================================
# calculation helper functions
def elo_change(e1, e2, result):
  assert result==0 or result==1 or result==0.5
  expected = 1 / (1 + B**( (e2-e1)/SEP ))
  return K*(result - expected)


def get_wins(round_no):
  round = log.iloc[round_no-1]
  round = round[players]

  wins = {}
  for p in players:
    wins[p] = list(round[round > round[p]].index)

  return wins


def get_ties(round_no):
  round = log.iloc[round_no-1]
  round = round[players]

  ties = {}
  for p in players:
    ties[p] = list(round[round == round[p]].index)

  for p in ties.keys():
    if p in ties[p]:
      ties[p].remove(p)

  return ties


def update_elo(round_no):
  wins = get_wins(round_no)
  ties = get_ties(round_no)

  for p in wins.keys():
    for o in wins[p]:
      change = elo_change(elo[p], elo[o], 1)
      elo[p] += change
      elo[o] -= change

      record[p][0] += 1
      record[o][1] += 1

  for p in ties.keys():
    for o in ties[p]:
      change = elo_change(elo[p], elo[o], 0.5)
      elo[p] += change
      record[p][2] += 1


def get_record_info(p):
  r = record[p]
  record_disp = '-'.join([str(i) for i in r])
  if sum(r) == 0:
    win_pct = 0
  else:
    win_pct = (r[0] + 0.5*r[2]) / sum(r)
    win_pct = np.round(win_pct, 3)
  return record_disp, win_pct
# =================================================================


# =================================================================
# compute elo, records
elo_history = {p : [elo[p]] for p in players}
for i in log.index:
  update_elo(i+1)

  for p in players:
    elo_history[p].append(elo[p])

order = sorted(elo, key=elo.get, reverse=True)
rank = {order[i]: i+1 for i in range(len(order))}
# =================================================================


# =================================================================
# generate display tables
elo_list = []
rank_list = []
record_list = []
win_pct_list = []

for p in players:
  elo_list.append(np.round(elo[p],1))
  rank_list.append(rank[p])
  record_disp, win_pct = get_record_info(p)
  record_list.append(record_disp)
  win_pct_list.append(np.round(win_pct, 3))

elo_main = pd.DataFrame({"Rank":rank_list, "Player":players, "Rating":elo_list,
                         "Record":record_list, "Win %":win_pct_list})

elo_main = elo_main.sort_values("Rank")
elo_main = elo_main.reset_index(drop=True)
# =================================================================


# =================================================================
# elo over time plot (image)
plot = pd.DataFrame(elo_history).plot(figsize=(12,6), marker='o', title='Elo Change')
plt.savefig('elo_change.png', bbox_inches='tight')
# =================================================================


# =================================================================
# GENERATE HTML PAGE
# =================================================================

template = Template(
"""
<h1>Purdue Disc Golf</h1>

<table style="border-collapse: collapse; width: 100%; height: 34px;" border="1">
<tbody>

<tr>
  <td style="width: 12%;"><strong>Rank</strong></td>
  <td style="width: 22%;"><strong>Player</strong></td>
  <td style="width: 22%;"><strong>Rating</strong></td>
  <td style="width: 22%;"><strong>Record</strong></td>
  <td style="width: 22%;"><strong>Win %</strong></td>
</tr>

{% for rank, player, rating, record, pct in elo_main %}
  <tr>
    <td>{{rank}}</td>
    <td>{{player}}</td>
    <td>{{rating}}</td>
    <td>{{record}}</td>
    <td>{{pct}}</td>
  </tr>
{% endfor %}

</tbody>
</table>

<p>
  Work is still in progress for this page. New updates and features are coming soon.
  All calculations are subject to change until further testing is done.
</p>

<h2>Ratings Change Over Time<h2>
<img src="elo_change.png">

""")


html = template.render(elo_main=elo_main.values)
with open("index.html", "w") as html_file:
    html_file.write(html)
