#!/usr/bin/env python
# coding=utf-8
import sys
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/score/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/enroll/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/extractor/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/common/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/conf/")
import re, os
import csv
import Levenshtein
from conf.setting import ROOT_DIR, STD_WMZY_SCH_NAME_FILE


class SchNameMatcher(object):
    """
    学校名称标准化匹配
    """
    def __init__(self):

        self.file_path = os.path.join(ROOT_DIR, STD_WMZY_SCH_NAME_FILE)
        self.std_sch_names = set()
        self.__read_std_sch_names()

    def __read_std_sch_names(self):
        with(open(self.file_path, newline='')) as sch_file:
            rows = csv.reader(sch_file, delimiter=',', )
            next(rows)
            for row in rows:
                std_name = row[0]
                alias_name = row[1]
                clean_name = re.sub("[^\u4e00-\u9fa5]+", "", std_name)
                if clean_name:
                    self.std_sch_names.add(clean_name)
                clean_name = re.sub("[^\u4e00-\u9fa5]+", "", alias_name)
                if clean_name:
                    self.std_sch_names.add(clean_name)

    def match_std_sch(self, sch_raw):
        """
        按照编辑比例计算一个sen是不是学校
        """
        # 删除所有非中文
        sen = re.sub("[^\u4e00-\u9fa5]+", "", sch_raw)
        if sen in self.std_sch_names:
            return sen

        for item in self.std_sch_names:
            if sen.startswith(item) or item.startswith(sen):
                return sen
        lis = [(sch, Levenshtein.distance(sen, sch)) for sch in self.std_sch_names]

        if lis:
            candi = min(lis, key=lambda x: x[1])
            ratio = 1 - candi[1] * 1.0 / max(len(sen), len(candi[0]))  # 不用改的
        else:
            ratio = 0.0

        if ratio > 0.75:
            return candi[0]
        else:
            return None

    def is_sch_name(self, sch_name_raw):
        # 取第一个全中文子字符串
        sch_name = re.sub("[^\u4e00-\u9fa5]", " ", sch_name_raw.strip()).strip().split(" ")[0]
        #  大学或者学院
        sch_name_suffix = ["大学", "学院", "分校", "校区", "学校", "书院"]
        for item in sch_name_suffix:
            if item in sch_name:
                if item in ["大学"] and sch_name.endswith(item) and len(sch_name) > len(item) * 3:
                    return True

                std_sch = self.match_std_sch(sch_name)
                if std_sch:
                    return True

        # 对院校名称太长被分割成两行的情况进行补充, 并过滤掉一大批短名称专业
        if len(sch_name) > 5:
            std_sch = self.match_std_sch(sch_name)
            if std_sch:
                return True
        return False

