"""
Safe AI search connector skeleton. Implement connectors by supplying API keys
via environment variables or config files. This module provides a small
abstraction to call external safe search providers.
"""
import os
import requests

class ConnectorError(Exception):
    pass

class BaseConnector:
    def search(self, query):
        raise NotImplementedError()

class BingConnector(BaseConnector):
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('BING_SEARCH_API_KEY')
        if not self.api_key:
            raise ConnectorError('Bing API key not configured')
    def search(self, query):
        # safe wrapper
        url = 'https://api.bing.microsoft.com/v7.0/search'
        headers = {'Ocp-Apim-Subscription-Key': self.api_key}
        params = {'q': query, 'count': 10}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()

def get_connector(name='bing'):
    if name == 'bing':
        return BingConnector()
    raise ConnectorError('Unknown connector')
