"""Discord bot for interacting with inhouse API."""

import asyncio
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
from discord import app_commands
from discord.ext import commands
from disputils import BotEmbedPaginator
import grpc

from protos import inhouse_pb2
from protos import inhouse_pb2_grpc
from server import game_manager

_DISCORD_TOKEN = flags.DEFINE_string('discord_token', '', 'Discord API Token.')
_INHOUSE_SERVER_ADDRESS = flags.DEFINE_string(
    'inhouse_server_address',
    'localhost:50051',
    'host:port for inhouse server.',
)
_MATCH_STORAGE_DIR = flags.DEFINE_string('match_storage_dir', 'data/summer-2021',
    'Directory in which to store match results.')


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
          self._active_messages[channel.id].id != message.id):
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

  @commands.hybrid_command(help='Start inhouse if 5 or more peeps interested.')
  async def inhouse(self, ctx):
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

  @commands.command(help='Get match results for a completed inhouse code.')
  async def match_results(self, ctx, code):
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

  @commands.hybrid_command(help='Flip a coin.')
  async def swords(self, ctx):
    coin_side = 'heads' if random.random() >= 0.5 else 'tails'
    await ctx.send('Swords flips a coin, it lands on %s!' % coin_side)

  @commands.command(help='Show the leaderboard.')
  async def leaderboard(self, ctx):
    leaderboard = self._manager.get_leaderboard()
    embeds = []
    embed = discord.Embed(title='Leaderboard')
    position = 0
    for _, player in leaderboard.iterrows():
      position += 1
      embed.add_field(name=f'{position}: {player["name"]}', value=_format_player(player), inline=False)
      if len(embed.fields) >= 10:
        embeds.append(embed)
        embed = discord.Embed(title='Leaderboard')
    if len(embed.fields):
      embeds.append(embed)
    paginator = BotEmbedPaginator(ctx, embeds)
    await paginator.run()


def _format_player(player):
  return '{rating:.2f} {wins}W {losses}L {kills}/{deaths}/{assists} ({kda:.1f})'.format(**player.to_dict())


async def setup(bot):
  channel = grpc.insecure_channel(_INHOUSE_SERVER_ADDRESS.value)
  inhouse_stub = inhouse_pb2_grpc.InhouseStub(channel)
  manager = game_manager.GameManager(_MATCH_STORAGE_DIR.value)

  await bot.add_cog(Inhouse(bot, inhouse_stub, manager))


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  intents = discord.Intents.default()
  intents.message_content = True

  bot = commands.Bot(
      intents=intents,
      command_prefix='!',
      description='Bot for organizing inhouses.',
  )
  asyncio.run(setup(bot))
  bot.run(_DISCORD_TOKEN.value)


if  __name__ == '__main__':
  app.run(main)
