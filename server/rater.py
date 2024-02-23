"""Rate all the peeps."""

import bisect
import itertools
import json

import pandas as pd
import requests
import trueskill

SMURFS = {
}

version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
champs = requests.get('https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json'.format(version)).json()
CHAMP_ICON_URL = 'https://ddragon.leagueoflegends.com/cdn/{}/img/champion/{{}}.png'.format(version)
champs_by_key = {int(champ['key']): champ for champ in champs['data'].values()}


def get_canonical_name(name):
  return SMURFS.get(name, name)


def parse_match(raw: str):
  """Parse relevant data from raw match string."""
  match = json.loads(raw)
  match_id = match['gameId']
  identities = {
      pid['participantId']: pid['player'] for pid in match['participantIdentities']
  }

  win_team, loss_team = (
      next(team['teamId'] for team in match['teams'] if team['win'] == result)
      for result in ('Win', 'Fail')
  )

  win, loss = (
      tuple(
        get_canonical_name(identities[p['participantId']]['summonerName'])
        for p in match['participants']
        if p['teamId'] == team
      )
      for team in (win_team, loss_team)
  )

  player_stats = {
      get_canonical_name(identities[p['participantId']]['summonerName']): {
          'win': p['stats']['win'],
          'champ': champs_by_key[p['championId']]['id'],
      }
      for p in match['participants']
  }

  return pd.Series({
      'match_id': match_id,
      'win': win,
      'loss': loss,
      'player_stats': player_stats,
  })


def compute_division_boundaries():
  divisions = [
      f'{tier} {division}' for tier in [
          'Boosted Animal',
          'Bonobo',
          'House Cat',
          'Pug',
          'Wolf',
          'Tiger',
          'Tiger Shark',
          'Blue Whale',
      ]
      for division in ['IV', 'III', 'II', 'I']
  ]
  division_boundaries = [(float('-inf'), divisions[0])]
  min_rating = trueskill.global_env().mu - 3 * trueskill.global_env().sigma
  max_rating = trueskill.global_env().mu + 3 * trueskill.global_env().sigma
  division_boundaries.extend((
      min_rating + i * (max_rating - min_rating) / (len(divisions) - 1),
      divisions[i + 1],
  ) for i in range(len(divisions) - 1))
  return division_boundaries


def find_division(boundaries, rating):
  return boundaries[bisect.bisect(boundaries, (rating, '')) - 1][1]


def compute_record(stats):
  win = sum(1 for game in stats if game and game['win'])
  loss = sum(1 for game in stats if game and not game['win'])
  return f'{win / (win + loss):.0%} ({win}W {loss}L)'


def compute_streak(stats):
  last_result = None
  count = 0
  for game in stats[::-1]:
    if game is not None:
      if last_result is None:
        last_result = game['win']
      if game['win'] == last_result:
        count += 1
      else:
        break
  result = 'W' if last_result else 'L'
  return f'{count}{result}'


def compute_ratings(matches):
  ratings = {}
  histories = {}
  new_player_history = []
  stats = {}
  new_player_stats = []

  for _, match in matches.iterrows():
    for name in set(itertools.chain(stats.keys(), match['player_stats'])):
      stats.setdefault(name, new_player_stats[:])
      if name in match['player_stats']:
        stats[name].append(match['player_stats'][name])
      else:
        stats[name].append(None)
    new_player_stats.append(None)

    new_ratings = trueskill.rate((
        {name: ratings.get(name, trueskill.Rating()) for name in match["win"]},
        {name: ratings.get(name, trueskill.Rating()) for name in match["loss"]},
    ))
    for new_rating in new_ratings:
      ratings.update(new_rating)

    new_player_history.append(trueskill.Rating())
    for name in ratings:
      histories.setdefault(name, new_player_history[:])
      histories[name].append(ratings[name])

  rows = [(name, rating, stats[name], histories[name]) for name, rating in ratings.items()]
  ratings = pd.DataFrame.from_records(
      rows, columns=["Name", "trueskill.Rating", "stats", "history"], index="Name"
  )
  ratings.index.name = None

  boundaries = compute_division_boundaries()
  ratings["μ"] = ratings["trueskill.Rating"].apply(lambda rating: rating.mu)
  ratings["σ"] = ratings["trueskill.Rating"].apply(lambda rating: rating.sigma)
  ratings["Rating"] = ratings["trueskill.Rating"].apply(
      lambda rating: trueskill.expose(rating)
  )
  ratings["Rank"] = ratings["Rating"].apply(
      lambda rating: find_division(boundaries, rating)
  )
  ratings["Record"] = ratings["stats"].apply(lambda stats: compute_record(stats))
  ratings["Streak"] = ratings["stats"].apply(lambda stats: compute_streak(stats))
  ratings["Champs"] = ratings["stats"].apply(lambda stats:
      tuple(game["champ"] for game in stats if game)
  )
  ratings.sort_values("Rating", ascending=False, inplace=True)

  return ratings


def rate(matches):
  trueskill.setup(backend='scipy', draw_probability=0)
  ratings = compute_ratings(matches)
  return ratings
