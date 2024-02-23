from absl import app
from absl import flags

from server import game_manager

_MATCH_STORAGE_DIR = flags.DEFINE_string('match_storage_dir', 'data/summer-2021',
    'Directory in which to store match results.')


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  manager = game_manager.GameManager(_MATCH_STORAGE_DIR.value)
  leaderboard = manager.get_leaderboard()

  print(leaderboard)


if __name__ == '__main__':
  app.run(main)
