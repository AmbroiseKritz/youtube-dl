
# coding: utf-8
from __future__ import unicode_literals
import re
import time

from .common import InfoExtractor
from ..utils import (js_to_json, parse_m3u8_attributes, int_or_none, strip_or_none, float_or_none)


class MediciIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?medici\.tv/(?P<language>[^/]+)/(?P<category>[^/]+)/(?P<id>[^?#&]+)'
    _TEST = {
        'url': 'https://www.medici.tv/en/operas/verdis-simon-boccanegra/',
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
                sub_url = sub_attr.get('URI').replace('.m3u8', '.webvtt')
                subtitles.setdefault(lang, []).append({
                    'url': sub_url,
                    'ext': 'srt',
                })
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

        subtitles = self.extract_subtitles(m3u8_doc)
        title = self._og_search_title(webpage)

        synopsis = self._html_search_regex(
            r'(?s)<div[^>]+id=["\']movie-synopsis[^>]+>(.+?)</div>', webpage,
            'description', fatal=False)

        program = self._html_search_regex(
            r'(?s)<ul[^>]+class=["\']program__list[^>]+>(.+?)</ul>', webpage,
            'program', fatal=False)

        description = synopsis + program
        chapters_raw = []

        chapters_html = self._search_regex(
            r'(?s)<ul class=["\']chapters__list["\']>(.+?)</ul>', webpage,
            'media_id', fatal=False)

        if chapters_html:
            for chapter_data in re.findall(r'(?s)<li.+?>(.+?)</li>', chapters_html):
                video_data = self._search_regex(r'(?s)pushGTMTrigger\(["\']gtm-movie-chapter-trigger["\'], ({.*?})\)', chapter_data, 'test')

                data = self._parse_json(video_data, video_id, js_to_json, fatal=False)

                start_time = float_or_none(self._search_regex(r'(?s)data-time=["\']([0-9,]+)["\']', chapter_data, 'start_time', default=None))

                chapter_name = data['chapter_work'] if not data['chapter_movement'] else data['chapter_work'] + ', ' + data['chapter_movement']
                chapters_raw.append({
                    'start_time': start_time,
                    'title': strip_or_none(chapter_name),
                })
        self.to_screen(chapters_raw)
        duration_parse = self._html_search_regex(
            r'(?s)<li[^>]+class=["\']film__meta__list__item--default[^>]+>Duration:(.+?)</li>', webpage,
            'duration', fatal=False)
        """ Beaurk """
        duration_strp = time.strptime(duration_parse, "%H h %M min")
        duration = duration_strp.tm_hour * 3600 + duration_strp.tm_min * 60

        chapters = []
        for num, chapter in enumerate(chapters_raw, start=0):
            if start_time is None:
                continue
            if num + 1 == len(chapters_raw):
                end_time = duration
            else:
                end_time = chapters_raw[num + 1]['start_time']
            chapters.append({
                'start_time': chapter['start_time'],
                'end_time': end_time,
                'title': chapter['title'],
            })
        self.to_screen(chapters)

        video_thumbnail = self._og_search_thumbnail(webpage)

        info_dict.update({
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': video_thumbnail,
            'chapters': chapters,
        })

        return info_dict
