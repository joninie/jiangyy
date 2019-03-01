#!/usr/bin/env python
# coding=utf-8

import os
import unittest
from enroll_score_ocr_parser.score.score_info_parser import ScoreInfoParser
from enroll_score_ocr_parser.util.file_util import readXLS_R1


class TestScoreParser(unittest.TestCase):

    def test_score_parser(self):
        # file_path, output_dir, page_column_count, enroll_years
        file_name = '本科A批录取院校各专业录取情况统计表(文史).xlsx'
        output_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(output_dir, file_name)

        score_info_parser = ScoreInfoParser(file_path, output_dir, 0, [2017])
        score_info_parser.deal_content_info()

        contents = readXLS_R1(file_path.replace(".xlsx", "-major_info.xls"))
        self.assertEqual(contents[0],
                         ["院校名称", "院校代码", "院校计划数", "专业名称", "专业代码", "招生年份", "计划数", "录取数", "最高分",
                          "最低分", "平行志愿", "征求志愿", "服从志愿", "选测科目等级", "平均分", "最低分与分数线差值",
                          "录取最低分位次", "平均分与分数线差值",  "科目要求", "学制", "院校全称", "批次", "文理", "分数段低分",
                          "分数段高分","分数段人数", "学费", "办学地点", "语种", "备注", "未处理内容"])

        self.assertEqual(contents[1],
                         ['北京大学', '', '6', '哲学类', '', '2017', '1', '1', '868',
                          '868', '5', '', '', '', '868', '',
                          '', '', '', '', '', '', '', '',
                          '', '', '', '', '', '', ''])

        contents = readXLS_R1(file_path.replace(".xlsx", "-sch_info.xls"))

        self.assertEqual(contents[0],
                         ["院校名称", "院校代码", "招生年份", "计划数", "录取数", "最高分", "最低分", "平行志愿", "征求志愿",
                          "服从志愿", "平均分", "最低分与分数线差值", "录取最低分位次", "平均分与分数线差值", "院校全称",
                          "科目要求", "批次", "文理", "分数段低分", "分数段高分", "分数段人数", "办学地点", "备注"])

        sch_info = contents[1]

        sch_name = sch_info[0]
        sch_enroll_count = sch_info[3]
        sch_people_count = sch_info[4]
        max_score = sch_info[5]
        min_score = sch_info[6]
        parallel_volunteer = sch_info[7]
        avg_score = sch_info[10]

        self.assertEqual((sch_name, sch_enroll_count, sch_people_count, max_score, min_score, parallel_volunteer, avg_score),
                         ("北京大学", "6", "11", "930", "868", "", "881"))


if __name__ == '__main__':
    unittest.main()