"""Inhouse Server.

This is the backend server for InterCompany League In-houses.

Allows creation of tournament codes and stores completed game data.
"""
from concurrent import futures
import json
import time

from absl import app
from absl import flags
from absl import logging
import grpc
from grpc_reflection.v1alpha import reflection

from protos import inhouse_pb2
from protos import inhouse_pb2_grpc
from server import riot_client

_ONE_DAY_IN_SECONDS = 24 * 60 * 60

flags.DEFINE_string('host', 'localhost', 'Host to bind server.')
flags.DEFINE_integer('port', '50051', 'Port to bind server.')

flags.DEFINE_string('riot_api_key', '', 'Tournament API key for rito.')

FLAGS = flags.FLAGS


class InhouseServicer(inhouse_pb2_grpc.InhouseServicer):
  """Implements Inhouse service."""

  def __init__(self, api_key: str):
    self._api_key = api_key

  def GetCodes(self, request, context):
    codes = riot_client.call('lol/tournament/v4/codes',
        api_key=self._api_key,
        params={'count': request.count, 'tournamentId': '1637307'},
        data='{"mapType": "SUMMONERS_RIFT","pickType": "TOURNAMENT_DRAFT","spectatorType": "ALL","teamSize": 5,"metadata": ""}')
    response = inhouse_pb2.GetCodeResponse(codes=codes)
    return response

  def GetGameStats(self, request, context):
    match_ids = riot_client.call(
        f'lol/match/v4/matches/by-tournament-code/{request.code}/ids',
        api_key=self._api_key,
        platform_id='na1')
    response = inhouse_pb2.GetGameStatsResponse()
    for match_id in match_ids:
      stats = riot_client.call(
          f'lol/match/v4/matches/{match_id}/by-tournament-code/{request.code}',
          api_key=self._api_key,
          platform_id='na1')
      response.stats.append(json.dumps(stats))
    return response


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  authority = '%s:%s' % (FLAGS.host, FLAGS.port)
  server.add_insecure_port(authority)
  SERVICE_NAMES = (
      inhouse_pb2.DESCRIPTOR.services_by_name['Inhouse'].full_name,
      reflection.SERVICE_NAME,
  )
  reflection.enable_server_reflection(SERVICE_NAMES, server)

  inhouse_pb2_grpc.add_InhouseServicer_to_server(
      InhouseServicer(FLAGS.riot_api_key), server)

  logging.info('Starting inhouse server at %s', authority)
  server.start()
  try:
    while True:
      time.sleep(_ONE_DAY_IN_SECONDS)
  except KeyboardInterrupt:
    server.stop(0)


if __name__ == '__main__':
  app.run(main)
