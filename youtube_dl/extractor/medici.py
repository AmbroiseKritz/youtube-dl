
# coding: utf-8
from __future__ import unicode_literals
import re


from .common import InfoExtractor
from ..utils import js_to_json


class MediciIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?medici\.tv/(?P<language>[^/]+)/(?P<category>[^/]+)/(?P<id>[^?#&]+)'
    _TEST = {
        'url': 'http://www.medici.tv/#!/daniel-harding-frans-helmerson-verbier-festival-music-camp',
        'md5': '004c21bb0a57248085b6ff3fec72719d',
        'info_dict': {
            'id': '3059',
            'ext': 'mp4',
            'title': 'Daniel Harding conducts the Verbier Festival Music Camp \u2013 With Frans Helmerson',
            'description': 'md5:322a1e952bafb725174fd8c1a8212f58',
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20170408',
        },
    }

    def _real_extract(self, url):

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        jw_config = self._parse_json(
            self._search_regex(
                r'(?s)JWPlayerManager\(.*?(?P<options>{[^;]+}).*?;',
                webpage, 'jw config', group='options'),
            video_id, transform_source=js_to_json)

        self.to_screen(jw_config)
        info_dict = self._parse_jwplayer_data(jw_config, video_id, require_title=False)

        self.to_screen(info_dict)

        """ info_dict.update({
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
        }) """
        return info_dict
