"""Discord bot for interacting with inhouse API."""

import io
import os
import random
import re
import threading
import datetime

from absl import app
from absl import flags
from absl import logging
import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils import manage_commands
import grpc

from protos import inhouse_pb2
from protos import inhouse_pb2_grpc
from server import game_manager

flags.DEFINE_string('discord_token', '', 'Discord API Token.')
flags.DEFINE_string('inhouse_server_address', 'localhost:50051',
    'host:port for inhouse server.')
flags.DEFINE_string('match_storage_dir', 'data/summer-2021',
    'Directory in which to store match results.')

FLAGS = flags.FLAGS


class Inhouse(commands.Cog):
  """Trigger inhouse if enough people react."""

  def __init__(self,
               bot: commands.Bot,
               server: inhouse_pb2_grpc.InhouseStub,
               manager: game_manager.GameManager):
    self.bot = bot
    self._server = server
    self._manager = manager
    # Dict of channel.id => message that can be reacted to trigger code.
    self._active_messages = {}
    self._lock = threading.RLock()


  @commands.Cog.listener()
  async def on_reaction_add(self, reaction, user):
    """If 5 peeps react to the message, then we trigger a new code."""
    message = reaction.message
    channel = message.channel

    with self._lock:
      if (channel.id not in self._active_messages or
          self._active_messages[channel.id] != message):
        return

      all_users = set()
      for reaction in message.reactions:
        users = await reaction.users().flatten()
        all_users.update(users)

      logging.info('Reaction to valid message: %s users', len(all_users))

      if len(all_users) >= 5:
        logging.info('Generating code')
        del self._active_messages[channel.id]
        response = self._server.GetCodes(inhouse_pb2.GetCodeRequest(count=1))
        await channel.send('Code: %s' % response.codes[0])

  @cog_ext.cog_slash(name="inhouse", description='Start inhouse if 5 of more peeps response.')
  async def inhouse(self, ctx: SlashContext):
    with self._lock:
      should_create_message = True

      if ctx.channel.id in self._active_messages:
        # If existing message is >1 hour old, go ahead and create a new one.
        active_message = self._active_messages[ctx.channel.id]
        time_difference = datetime.datetime.utcnow() - active_message.created_at
        should_create_message = time_difference.total_seconds() > 60 * 60

      if should_create_message:
        self._active_messages[ctx.channel.id] = await ctx.send(
            'React if interested in playing')

  @cog_ext.cog_slash(
      name='match_results',
      description='Get match results for a completed inhouse code.',
      options=[manage_commands.create_option(
          name='code',
          description='The Rito tourney code.',
          option_type=3,
          required=True
      )]
  )
  async def match_results(self, ctx: SlashContext, code: str):
    logging.info('code: %s', code)
    try:
      response = self._server.GetGameStats(
          inhouse_pb2.GetGameStatsRequest(code=code))
      filename = f'{code}.json'
      with open(os.path.join(FLAGS.match_storage_dir, filename), 'w') as f:
        f.write(response.stats[-1])
      await ctx.send(
          f'Match Results: {code}',
          file=discord.File(io.StringIO(response.stats[-1]), filename))
    except Exception as e:
      logging.error(e)
      await ctx.send(f'Failed to fetch match results for code: {code}')

  @cog_ext.cog_slash(name='swords', description='Flip a coin.')
  async def swords(self, ctx: SlashContext):
    coin_side = 'heads' if random.random() >= 0.5 else 'tails'
    await ctx.send('Swords flips a coin, it lands on %s!' % coin_side)

  @cog_ext.cog_slash(name='leaderboard', description='Show the leaderboard.')
  async def leaderboard(self, ctx: SlashContext):
    leaderboard = self._manager.get_leaderboard()
    await ctx.send(str(leaderboard))


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  channel = grpc.insecure_channel(FLAGS.inhouse_server_address)
  inhouse_stub = inhouse_pb2_grpc.InhouseStub(channel)

  bot = commands.Bot(
      command_prefix='!',
      description='Bot for organizing inhouses.')
  slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)
  manager = game_manager.GameManager(FLAGS.match_storage_dir)
  bot.add_cog(Inhouse(bot, inhouse_stub, manager))
  bot.run(FLAGS.discord_token)


if  __name__ == '__main__':
  app.run(main)
