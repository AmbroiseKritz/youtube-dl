
# coding: utf-8
from __future__ import unicode_literals
import re


from .common import InfoExtractor
from ..utils import (js_to_json, parse_m3u8_attributes)


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

    def _get_subtitles(self, m3u8_doc):
        subtitles = {}
        for line in m3u8_doc.splitlines():
            if 'TYPE=SUBTITLES' in line:
                sub_attr = parse_m3u8_attributes(line)
                lang = sub_attr.get('LANGUAGE')
                self.to_screen(sub_attr)
                sub_url = sub_attr.get('URI').replace('.m3u8', '.webvtt')
                subtitles.setdefault(lang, []).append({
                    'url': sub_url,
                    'ext': 'srt',
                })
        self.to_screen(subtitles)
        return subtitles

    def _real_extract(self, url):

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        jw_config = self._parse_json(
            self._search_regex(
                r'(?s)JWPlayerManager\(.*?(?P<options>{[^;]+}).*?;',
                webpage, 'jw config', group='options'),
            video_id, transform_source=js_to_json)

        info_dict = self._parse_jwplayer_data(jw_config, video_id, require_title=False)

        m3u8_url = info_dict['formats'][0]['manifest_url']

        m3u8_doc, _ = self._download_webpage_handle(
            m3u8_url, video_id,
            note='Downloading m3u8 information',
            errnote='Failed to download m3u8 information')

        formats = self._parse_m3u8_formats(
            m3u8_doc, m3u8_url, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        subtitles = self.extract_subtitles(m3u8_doc)
        title = self._og_search_title(webpage)
        description = self._html_search_meta('description', webpage)
        video_thumbnail = self._og_search_thumbnail(webpage)

        info_dict.update({
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': video_thumbnail
        })

        return info_dict
