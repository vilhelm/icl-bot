"""Manages inhouse games."""

import collections
import dataclasses
import glob
import json
import threading

import pandas as pd
import trueskill


"""Data class for holding player information."""
@dataclasses.dataclass
class Player:
  name: str = ''
  rating: trueskill.Rating = dataclasses.field(default_factory=trueskill.Rating)
  wins: int = 0
  losses: int = 0
  kills: int = 0
  deaths: int = 0
  assists: int = 0
  unique_champs: set = dataclasses.field(default_factory=set)

  """Converts player object to a pandas series."""
  def to_series(self) -> pd.Series:
    return pd.Series({
        'name': self.name,
        'rating': trueskill.expose(self.rating),
        'wins': self.wins,
        'losses': self.losses,
        'kills': self.kills,
        'deaths': self.deaths,
        'assists': self.assists,
        'kda': (self.kills + self.assists) / (self.deaths or 1),
        'champs': self.unique_champs,
    })


class GameManager(object):

  # Dictionary of `smurf` to `main` to merge peeps.
  # TODO(josephroth): Use underlying account id to merge peeps instead of a
  # fixed list here. Will still need to indicate preferred name.
  _SMURFS = {
  }

  def __init__(self, storage_dir: str):
    self._storage_dir = storage_dir
    # Don't parse the same match multiple times.
    self._observed_match_ids = set()
    self._lock = threading.RLock()
    self._players = collections.defaultdict(Player)
    self._matches = pd.DataFrame()

  """Loads all matches from storage_dir.
  
  Updates `self._players` and `self._matches` with newly discovered results.
  """
  def _load_matches(self):
    new_matches = []
    for filename in glob.glob(f'{self._storage_dir}/*.json'):
      with open(filename) as f:
        match = json.load(f)
      match_id = match['gameId']
      with self._lock:
        if match_id in self._observed_match_ids:
          continue
        self._observed_match_ids.add(match_id)
        new_matches.append(self._parse_match(match))
    self._matches = pd.concat([self._matches] + new_matches)  #.sort_values('match_id')

  def _get_canonical_name(self, name):
    return self._SMURFS.get(name, name)

  """Parses the relevant information from Rito match results dict.

  Stores aggregate stats into the Player objects for all participants.

  Note: We can't update the player rating here since the matches are not
  necesarily parsed in time order. So we parse all matches first and then order
  by match_id in order to process player ratings later.

  Args:
    match: Dictionary of parsed Rito match result json.

  Returns:
    Pandas series containing the match_id, list of winners, and list of losers.
  """
  def _parse_match(self, match: dict) -> pd.Series:
    match_id = match['gameId']

    identities = {
        pid['participantId']:
            self._get_canonical_name(pid['player']['summonerName'])
        for pid in match['participantIdentities']
    }

    winners = []
    losers = []

    with self._lock:
      for p in match['participants']:
        summoner_name = identities[p['participantId']]
        player = self._players[summoner_name]
        player.name = summoner_name
        if p['stats']['win']:
          winners.append(summoner_name)
          player.wins += 1
        else:
          losers.append(summoner_name)
          player.losses += 1
        player.kills += p['stats']['kills']
        player.deaths += p['stats']['deaths']
        player.assists += p['stats']['assists']
        player.unique_champs.add(p['championId'])

    return pd.Series({
        'match_id': match_id,
        'winners': winners,
        'losers': losers,
    }, name=match_id)

  def _update_player_ratings(self, updates):
    with self._lock:
      for name, new_rating in updates.items():
        self._players[name].rating = new_rating

  """Gets the leaderboard.

  We compute this on the fly from the entirety of the matches. We do this on the fly
  since the dataset is relatively small and sometimes people enter the same match
  multiple times or in the wrong order, so we can filter them out before computation.
  """
  def get_leaderboard(self):
    self._load_matches()

    with self._lock:
      trueskill.setup(backend='scipy', draw_probability=0)
      for player in self._players.values():
        player.rating = trueskill.Rating()

      for _, match in self._matches.iterrows():
        win_update, loss_update = trueskill.rate((
            {name: self._players[name].rating for name in match['winners']},
            {name: self._players[name].rating for name in match['losers']},
        ))
        self._update_player_ratings(win_update)
        self._update_player_ratings(loss_update)

      leaderboard = pd.DataFrame(
          [p.to_series() for p in self._players.values()]
      ).sort_values('rating', ascending=False)
    return leaderboard

