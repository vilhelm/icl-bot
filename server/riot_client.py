"""Client to interface with Rito API."""

import os
from typing import Any, Dict, Optional

from absl import logging
import requests


def call(endpoint: str,
         api_key: str,
         params: Optional[Dict[str, Any]] = None,
         data: Optional[Any] = None,
         platform_id: str = 'americas'):
  """Helper function to call rito API.

  Note: Riot's API is a bit inconsistent on where to provide your request
  data. It can either be in the endpoint path, as URL params, or in the get
  body.

  Args:
    endpoint: Relative path to endpoint within Riot API.
      E.g., `/lol/match/v4/matches/{matchId}`
    api_key: Your secret API key to authenticate with Rito.
    params: Additional params to pass to the web request.
    data: Arbitrary data sent in the GET body. Used to specify constraints
      for tournament api.

  Returns:
    JSON response from Rito.

  Raises:
    RuntimeError: If request fails.
  """
  url = os.path.join(
      'https://%s.api.riotgames.com' % platform_id,
      endpoint)
  headers = {'X-Riot-Token': api_key}
  if not data:
    response = requests.get(url, params=params, headers=headers)
  else:
    response = requests.post(url, params=params, data=data, headers=headers)
  if response.status_code != requests.codes.ok:
    logging.info('Code: %', response.status_code)
    logging.info('Response: %s', response.content)
    raise RuntimeError('Failed request for: %s' % url)
  return response.json()
  
