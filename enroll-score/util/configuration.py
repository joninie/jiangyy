#!/usr/bin/env python
# coding=utf-8

import sys, os
import configparser
from enroll_score_ocr_parser.conf.setting import ROOT_DIR

class Configuration(object):
    '''
    读取配置文件
    '''
    def __init__(self, conf_file):
        self._properties = {}
        self._conf_path = os.path.join(ROOT_DIR, conf_file)
        self._parser = configparser.ConfigParser()

    def __cache(self):
        '''
        读取配置文件
        {
            "section":{
                "key":"value"
            }
        }
        '''
        self._parser.read(self._conf_path)
        for section in self._parser.sections():
            items = self._parser.items(section)
            for item in items:
                self._properties.setdefault(section, {})[item[0].strip()] = item[1].strip()

    def get_props(self):
        if not self._properties:
            self.__cache()
        return self._properties

    def get_section_props(self, section):
        return self.get_props().get(section) 

    def get_prop(self, section, prop_key):
        sec = self.get_props().get(section)
        return sec.get(prop_key) if sec else None


if __name__=='__main__':
    print(__name__)
    c = Configuration()
    print(c.get_props())

