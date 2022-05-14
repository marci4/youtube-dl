# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    determine_ext,
    parse_iso8601,
    YoutubeDLError
)


class SportDeutschlandIE(InfoExtractor):
    _VALID_URL = r'https?://sportdeutschland\.tv/(?P<id>(?:[^/]+/)?[^?#/&]+)'
    _TESTS = [{
        'url': 'https://sportdeutschland.tv/badminton/re-live-deutsche-meisterschaften-2020-halbfinals?playlistId=0',
        'info_dict': {
            'id': '5318cac0275701382770543d7edaf0a0',
            'ext': 'mp4',
            'title': 'Re-live: Deutsche Meisterschaften 2020 - Halbfinals - Teil 1',
            'duration': 16106.36,
        },
        'params': {
            'noplaylist': True,
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://sportdeutschland.tv/badminton/re-live-deutsche-meisterschaften-2020-halbfinals?playlistId=0',
        'info_dict': {
            'id': 'c6e2fdd01f63013854c47054d2ab776f',
            'title': 'Re-live: Deutsche Meisterschaften 2020 - Halbfinals',
            'description': 'md5:5263ff4c31c04bb780c9f91130b48530',
            'duration': 31397,
        },
        'playlist_count': 2,
    }, {
        'url': 'https://sportdeutschland.tv/freeride-world-tour-2021-fieberbrunn-oesterreich',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        data = self._download_json(
            'https://api.sportdeutschland.tv/api/stateless/frontend/assets/%s' % display_id,
            display_id) or {}
        title = data['name'].strip()
        asset_id = data['id']
        livestream = data['livestream']
        if not livestream:
            raise YoutubeDLError('No livestream for %s found.' % display_id)

        livestream_src = livestream['src']
        livestream_type = livestream['type']
        if livestream_type == "mux_live":
            token_data = self._download_json(
                'https://api.sportdeutschland.tv/api/frontend/asset-token/%s?type=%s&playback_id=%s' % (
                    asset_id, livestream_type, livestream_src),
                display_id, note='Determine asset access token.',
                errnote="Not able to get the asset access token.")
            token = token_data['token']
            video_url = 'https://stream.mux.com/%s.m3u8?token=%s' % (livestream_src, token)
        elif livestream_type == "smil":
            video_url = livestream_src
        else:
            raise YoutubeDLError('Unsupported livestream_type %s.' % livestream_type)
        ext = determine_ext(video_url)
        if ext == 'smil':
            formats = self._extract_smil_formats(video_url, asset_id)
        elif ext == 'm3u8':
            formats = self._extract_m3u8_formats(video_url, asset_id, live=True, fatal=False)
            if not formats:
                raise YoutubeDLError('Livestream %s is currently not live.' % display_id)
        else:
            formats = [{'url': video_url, }]
        self._sort_formats(formats)
        info = {
            'id': asset_id,
            'display_id': display_id,
            'title': title,
            'description': data.get('description'),
            'formats': formats,
            'thumbnail': data.get('image_url'),
        }
        timestamp = parse_iso8601(data.get('content_start_date'))
        if timestamp is not None:
            duration = parse_iso8601(data.get('content_end_date'))
            if duration is not None:
                info['duration'] = duration - timestamp
            info['timestamp'] = timestamp
        return info
