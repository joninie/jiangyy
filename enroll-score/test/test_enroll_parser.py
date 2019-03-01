#!/usr/bin/env python
# coding=utf-8

import re
import unittest
from enroll_score_ocr_parser.enroll.enroll_regex_parser import EnrollRegexParser


class TestEnrollRegexParser(unittest.TestCase):

    def test_enroll_regex_parser(self):
        sch_enroll_infos = "8001国防科技大学(北京)22人"
        sch_column_names = ["院校代码", "院校名称", "计划数"]

        enroll_regex_parser = EnrollRegexParser(None, None, 0, sch_column_names, None)
        enroll_regex_parser.generate_regex()

        sch_res = re.match(enroll_regex_parser.sch_regex, sch_enroll_infos)
        self.assertEqual(sch_res.groups(), ("8001", "国防科技大学(北京)", "22", "人"))

    def test_enroll_major_regex(self):

        major_enroll_infos = "11网电指挥与工程(电子对抗技术与指挥）2人 5年   (体检标准要求：其他专业合格）"
        major_column_names = ["专业代码", "专业名称", "计划数", "学制"]

        enroll_regex_parser = EnrollRegexParser(None, None, 0, None, major_column_names)
        enroll_regex_parser.generate_regex()

        major_res = re.match(enroll_regex_parser.major_regex, major_enroll_infos)
        self.assertEqual(major_res.groups(), ("11", "网电指挥与工程(电子对抗技术与指挥）", "2", "5年", "   (体检标准要求：其他专业合格）"))


if __name__ == '__main__':
    unittest.main()
