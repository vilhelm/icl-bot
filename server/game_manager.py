"""Manages inhouse games."""

import collections
import glob
import json

import pandas as pd
import trueskill


"""Data class for holding player information."""
class Player(object):

  def __init__(self):
    self.rating = trueskill.Rating()
    self.wins = 0
    self.losses = 0


class GameManager(object):

  # Dictionary of `smurf` to `main` to merge peeps.
  _SMURFS = {
      'MagaHero': 'Fiddlestocks',
  }

  def __init__(self, storage_dir: str):
    self._storage_dir = storage_dir

  """Loads matches from storage_dir."""
  def _load_matches(self):
    matches = []
    for filename in glob.glob(f'{self._storage_dir}/*.json'):
      with open(filename) as f:
        match = json.load(f)
      matches.append(self._parse_match(match))
    return pd.DataFrame.from_records(matches).drop_duplicates(
        subset=['match_id']).sort_values('match_id')

  def _get_canonical_name(self, name):
    return self._SMURFS.get(name, name)

  """Parses the relevant information from a raw json match result from Rito."""
  def _parse_match(self, match):
    match_id = match['gameId']
    identities = {
        pid['participantId']: pid['player'] for pid in match['participantIdentities']
    }

    win_team, loss_team = (
        next(team['teamId'] for team in match['teams'] if team['win'] == result)
        for result in ('Win', 'Fail')
    )

    winners, losers = (
        tuple(
          self._get_canonical_name(identities[p['participantId']]['summonerName'])
          for p in match['participants']
          if p['teamId'] == team
        )
        for team in (win_team, loss_team)
    )

    return pd.Series({
        'match_id': match_id,
        'winners': winners,
        'losers': losers,
    })

  def _update_player_ratings(self, players, updates):
    for name, new_rating in updates.items():
      players[name].rating = new_rating

  """Gets the leaderboard.

  We compute this on the fly from the entirety of the matches. We do this on the fly
  since the dataset is relatively small and sometimes people enter the same match
  multiple times or in the wrong order, so we can filter them out before computation.
  """
  def get_leaderboard(self):
    matches = self._load_matches()

    trueskill.setup(backend='scipy', draw_probability=0)
    players = collections.defaultdict(Player)

    for _, match in matches.iterrows():
      win_update, loss_update = trueskill.rate((
          {name: players[name].rating for name in match['winners']},
          {name: players[name].rating for name in match['losers']},
      ))
      self._update_player_ratings(players, win_update)
      for name in match['winners']:
        players[name].wins += 1
      self._update_player_ratings(players, loss_update)
      for name in match['losers']:
        players[name].losses += 1

    rows = [(name, trueskill.expose(p.rating), p.wins, p.losses) for name, p in players.items()]
    leaderboard = pd.DataFrame.from_records(
        rows, columns=['name', 'rating', 'wins', 'losses'], index='name')
    leaderboard.sort_values('rating', ascending=False, inplace=True)
    return leaderboard

