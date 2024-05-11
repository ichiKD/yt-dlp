import datetime as dt
import re
import urllib.parse
import urllib.request
import json

from .common import InfoExtractor
from ..utils import (
    dict_get,
    traverse_obj,
)


class FanslyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?fansly\.com/live/(\d+|[A-Za-z0-9_]+)'

    def __init__(self):
        self.header = {
            'authority': 'apiv3.fansly.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en;q=0.8,en-US;q=0.7',
            # Apprently authorization token is needed
            'authorization': 'NjQxMzE0MzU3NjkwNTA3MjY0OjE6MjozNWJhMDVhMWVmY2M2ZjY4Njg2NGU5ZjY3NzMxOTc',  # Replace with your actual auth token
            'origin': 'https://fansly.com',
            'referer': 'https://fansly.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

    def _real_extract(self, url):
        username = self._extract_id_or_username(url)
        stream_url = None
        if (username.isdigit()):
            print(f"the username is {username}")
            stream_url = f'https://apiv3.fansly.com/api/v1/streaming/channel/{username}?ngsw-bypass=true'
        else:
            account_url = f'https://apiv3.fansly.com/api/v1/account?usernames={username}&ngsw-bypass=true'
            user_data = self._get_account_data(account_url)
            stream_url = f'https://apiv3.fansly.com/api/v1/streaming/channel/{user_data["response"][0]["id"]}?ngsw-bypass=true'
        data = self._get_stream_data(stream_url)
        print("The data is", data)
        formats = [{'url': traverse_obj(data, ('response', 'stream', 'playbackUrl')), }]
        print({
            'id': traverse_obj(data, ('response', 'accountId')),
            'title': username,
            'is_live': True,
            'formats': formats,
        })

        return {
            'id': traverse_obj(data, ('response', 'accountId')),
            'title': username,
            'is_live': True,
            'formats': formats,
        }

    def _extract_id_or_username(self, url):
        pattern = r'\/live\/(\d+)|\/live\/([A-Za-z0-9_]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1) or match.group(2)
        else:
            return ""

    def _get_account_data(self, account_url):
        req = urllib.request.Request(account_url, headers=self.header)
        with urllib.request.urlopen(req) as response:
            json_data = json.load(response)
            if not dict_get(json_data, 'success') or len(dict_get(json_data, 'response')) == 0:
                print('Error: could not retrieve account data')
                exit()
            metadata = {
                "success": dict_get(json_data, 'success'),
                "response": [{
                    "id": traverse_obj(json_data, ('response', 0, 'id')),
                    "username": traverse_obj(json_data, ('response', 0, 'username')),
                    "avatar": {
                        "id": traverse_obj(json_data, ('response', 0, 'avatar', 'id')),
                        "mimetype": traverse_obj(json_data, ('response', 0, 'avatar', 'mimetype')),
                        "location": traverse_obj(json_data, ('response', 0, 'avatar', 'location')),
                        "variants": [
                            {
                                "id": traverse_obj(json_data, ('response', 0, 'avatar', 'variants', 0, 'id')),
                                "mimetype": traverse_obj(json_data, ('response', 0, 'avatar', 'variants', 0, 'mimetype')),
                                "location": traverse_obj(json_data, ('response', 0, 'avatar', 'variants', 0, 'location')),
                                "locations": [{
                                    "locationId": traverse_obj(json_data, ('response', 0, 'avatar', 'variants', 0, 'locations', 0, 'locationId')),
                                    "location": traverse_obj(json_data, ('response', 0, 'avatar', 'variants', 0, 'locations', 0, 'location')),
                                }]
                            }
                        ]
                    }}]
            }
            return metadata

    def _get_stream_data(self, stream_url):
        req = urllib.request.Request(stream_url, headers=self.header)
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            last_fetched = traverse_obj(data, ('response', 'stream', 'lastFetchedAt'))
            current_time = int(dt.datetime.now().timestamp() * 1000)
            playbackUrl = traverse_obj(data, ('response', 'playbackUrl'))
            if current_time - last_fetched > 4 * 60 * 1000 or playbackUrl is False:
                return {"success": False, "response": None}
            else:
                metadata = {
                    "success": dict_get(data, 'success'),
                    "response": {
                        "id": traverse_obj(data, ('response', 'id')),
                        "accountId": traverse_obj(data, ('response', 'accountId')),
                        "playbackUrl": traverse_obj(data, ('response', 'playbackUrl')),
                        "stream": {
                            "id": traverse_obj(data, ('response', 'stream', 'id')),
                            "title": traverse_obj(data, ('response', 'stream', 'title')),
                            "status": traverse_obj(data, ('response', 'stream', 'status')),
                            "lastFetchedAt": traverse_obj(data, ('response', 'stream', 'lastFetchedAt')),
                            "startedAt": traverse_obj(data, ('response', 'stream', 'startedAt')),
                            "playbackUrl": traverse_obj(data, ('response', 'stream', 'playbackUrl')),
                        },
                    }
                }
                return metadata
