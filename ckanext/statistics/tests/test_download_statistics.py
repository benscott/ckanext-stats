#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-statistics
# Created by the Natural History Museum in London, UK

import ckan.plugins
import nose
import paste.fixture
import pylons
import pylons.test
import os
from collections import OrderedDict

from ckanext.statistics.lib.download_statistics import DownloadStatistics

eq_ = nose.tools.eq_

backfill_fn = u'data-portal-backfill.json'


class TestBackfillStatistics(object):
    @classmethod
    def setup_class(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)
        if not ckan.plugins.plugin_loaded(u'statistics'):
            ckan.plugins.load(u'statistics')

    @classmethod
    def teardown_class(cls):
        ckan.plugins.unload(u'statistics')

    @staticmethod
    def _backfill_fn_exists():
        fp = os.path.join(os.path.dirname(os.path.dirname(__file__)), u'data',
                          backfill_fn)
        return os.path.exists(fp)

    def test_no_backfill_json_file(self):
        backfill_stats = DownloadStatistics.backfill_stats(None)
        eq_(backfill_stats, {})

    def test_not_empty_if_file_given(self):
        backfill_stats = DownloadStatistics.backfill_stats(
            backfill_fn) if self._backfill_fn_exists() else {}
        assert self._backfill_fn_exists(), u'{0} does not exist'.format(
            backfill_fn)
        assert isinstance(backfill_stats, dict), u'is not a dictionary'
        assert len(backfill_stats) > 0, u'is empty'

    def test_filter_by_year(self):
        backfill_stats = {}
        yr = 2018
        while len(backfill_stats.keys()) == 0 and yr > 2013:
            yr -= 1
            backfill_stats = DownloadStatistics.backfill_stats(backfill_fn,
                                                               year = yr)
        assert len(backfill_stats.keys()) > 0, u'no results'
        assert all(
            [k.endswith('/{0}'.format(yr)) for k in backfill_stats.keys()])

    def test_filter_by_month(self):
        backfill_stats = {}
        mnth = 0
        while len(backfill_stats.keys()) == 0 and mnth < 12:
            mnth += 1
            backfill_stats = DownloadStatistics.backfill_stats(backfill_fn,
                                                               month = mnth)
        assert len(backfill_stats.keys()) > 0, u'no results'
        assert all(
            [k.startswith(u'{0}/'.format(mnth)) for k in backfill_stats.keys()])


class TestMerge(object):
    @classmethod
    def setup_class(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)
        if not ckan.plugins.plugin_loaded(u'statistics'):
            ckan.plugins.load(u'statistics')
        cls.ckan_stats = DownloadStatistics.ckanpackager_stats()
        cls.backfill_stats = DownloadStatistics.backfill_stats(backfill_fn)
        cls.merged_stats = DownloadStatistics.merge(cls.ckan_stats,
                                                    cls.backfill_stats)

    @classmethod
    def teardown_class(cls):
        ckan.plugins.unload(u'statistics')

    def test_ordereddict_output(self):
        assert isinstance(self.merged_stats,
                          OrderedDict), u'merge result is {0}, ' \
                                        u'not OrderedDict'.format(
            type(self.merged_stats))

    def test_all_keys_present(self):
        bf_keys_in_merge = [(k in self.merged_stats.keys()) for k in
                            self.backfill_stats.keys()]
        ck_keys_in_merge = [(k in self.merged_stats.keys()) for k in
                            self.ckan_stats.keys()]
        assert all(
            ck_keys_in_merge), u'not all ckanpackager keys are present in the ' \
                               u'merged output'
        assert all(
            bf_keys_in_merge), u'not all backfill keys are present in the merged output'

