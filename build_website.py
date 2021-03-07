import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Template
from datetime import datetime

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
SEP = 150
K = 6
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
  current_elo = elo.copy()

  for p in wins.keys():
    for o in wins[p]:
      change = elo_change(current_elo[p], current_elo[o], 1)
      elo[p] += change
      elo[o] -= change

      record[p][0] += 1
      record[o][1] += 1

  for p in ties.keys():
    for o in ties[p]:
      change = elo_change(current_elo[p], current_elo[o], 0.5)
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


# get recent round info
def get_recent_round_info(round_num):
  round = log.loc[round_num-1].dropna()
  round['Date'] = str(round['Date'].date().month) + '/' + \
                  str(round['Date'].date().day) + '/' + \
                  str(round['Date'].date().year)

  round_info = [round['Course'], round['Date'], round['Temp'], round['Wind']]
  player_list = []
  score_list = []
  elo_change_list = []
  for p in players:
    if p in round:
      player_list.append(p)
      score_list.append(round[p])
      change = elo_history[p][round_num] - elo_history[p][round_num-1]
      if change >= 0:
        elo_change_list.append('+' + str(np.round(change, 1)))
      else:
        elo_change_list.append(str(np.round(change, 1)))

  scores = pd.DataFrame({"Player":player_list, "Score":score_list, "Change":elo_change_list})
  scores['Score'] = pd.to_numeric(scores['Score'], downcast='integer')
  scores = scores.sort_values('Score').reset_index(drop=True)

  return round_info, scores

n_rounds = log.shape[0]
round_info_1, scores_1 = get_recent_round_info(n_rounds)
round_info_2, scores_2 = get_recent_round_info(n_rounds-1)
round_info_3, scores_3 = get_recent_round_info(n_rounds-2)
# =================================================================


# =================================================================
# elo over time plot (image)
plot = pd.DataFrame(elo_history).plot(figsize=(10,5), marker='o')
plt.savefig('images/elo_change.png', bbox_inches='tight')
# =================================================================


# =================================================================
# GENERATE HTML PAGE
# =================================================================

# main page (index.html)
with open('templates/main-template.html', 'r') as file:
    template_text = file.read()

template = Template(template_text)

html = template.render(elo_main=elo_main.values,
                       last_update=datetime.now().strftime('%m-%d-%Y'),
                       course_1=round_info_1[0], date_1=round_info_1[1], round_1=scores_1.values,
                       course_2=round_info_2[0], date_2=round_info_2[1], round_2=scores_2.values,
                       course_3=round_info_3[0], date_3=round_info_3[1], round_3=scores_3.values)
with open("index.html", "w") as html_file:
    html_file.write(html)



# view all data page
with open('templates/all-data-template.html', 'r') as file:
    template_text = file.read()

template = Template(template_text)

log['Date'] = log['Date'].dt.date
for col in players:
   log[col] = log[col].apply(lambda x: int(x) if x == x else "")
html = template.render(log=log.values)
with open("info/all-data.html", "w") as html_file:
    html_file.write(html)
