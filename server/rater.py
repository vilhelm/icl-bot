from absl import app
from absl import flags

from server import game_manager

flags.DEFINE_string('storage_dir', 'data/summer-2021', 'Path to directory where matches are stored.')

FLAGS = flags.FLAGS


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  manager = game_manager.GameManager(FLAGS.storage_dir)
  leaderboard = manager.get_leaderboard()

  print(leaderboard)

  leaderboard = manager.get_leaderboard()

  print(leaderboard)


if __name__ == '__main__':
  app.run(main)
