#!/usr/bin/env python
# coding=utf-8
import sys
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/score/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/enroll/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/extractor/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/common/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/conf/")
import re
import logging
from pathlib import Path

from common.parser_error import ParserError
from common.pageable_parser import PageableParser

logger = logging.getLogger("enroll_score_ocr_parser")


class ScoreHeaderParser(PageableParser):

    NAME_HEADER = "院校专业名称"
    CODE_HEADER = "院校专业代码"
    ENROLL_COUNT_HEADER = "计划数"
    PEOPLE_COUNT_HEADER = "录取数"
    MAX_SCORE_HEADER = "最高分"
    MIN_SCORE_HEADER = "最低分"
    PARALLEL_VOLUNTEER_HEADER = "平行志愿"
    SEEK_VOLUNTEER_HEADER = "征求志愿"
    OBEY_VOLUNTEER_HEADER = "服从志愿"
    ENROLL_YEAR_HEADER = "年份"
    AVG_SCORE_HEADER = "平均分"
    MIN_SCORE_DIFF_HEADER = "最低分与分数线差值"
    ENROLL_MIN_RANK_HEADER = "录取最低分位次"
    AVG_SCORE_DIFF_HEADER = "平均分与分数线差值"
    MAJOR_GROUP_CODE_HEADER = "专业组代码"
    SUBJECT_REQUIRE_HEADER = "科目要求"
    EDU_SYSTEM_HEADER = "学制"
    SCHOOL_FULL_NAME_HEADER = "院校全称"
    BATCH_HEADER = "批次"
    PEOPLE_COUNT_DIS_HEADER = "录取数分布"

    SCH_FEE_HEADER = "学费"
    WENLI_HEADER = "文理"
    SCH_ADDR_HEADER = "办学地点"
    LANGUAGE_HEADER = "语种"
    NOTE_HEADER = "备注"

    def __init__(self, file_path, page_column_count, enroll_years, province):
        if enroll_years is None:
            enroll_years = []
        super(ScoreHeaderParser, self).__init__(file_path, page_column_count, province)

        self.file_path = file_path
        self.enroll_years = []  # 录取年份列表
        self.header_index_year_map = {}
        self.content_header = []

        self.header_regex = [ScoreHeaderParser.NAME_HEADER,
                             ScoreHeaderParser.CODE_HEADER,
                             ScoreHeaderParser.ENROLL_COUNT_HEADER,
                             ScoreHeaderParser.PEOPLE_COUNT_HEADER,
                             ScoreHeaderParser.MAX_SCORE_HEADER,
                             ScoreHeaderParser.MIN_SCORE_HEADER,
                             ScoreHeaderParser.PARALLEL_VOLUNTEER_HEADER,
                             ScoreHeaderParser.SEEK_VOLUNTEER_HEADER,
                             ScoreHeaderParser.OBEY_VOLUNTEER_HEADER,
                             ScoreHeaderParser.ENROLL_YEAR_HEADER,
                             ScoreHeaderParser.AVG_SCORE_HEADER,
                             ScoreHeaderParser.MIN_SCORE_DIFF_HEADER,
                             ScoreHeaderParser.ENROLL_MIN_RANK_HEADER,
                             ScoreHeaderParser.AVG_SCORE_DIFF_HEADER,
                             ScoreHeaderParser.MAJOR_GROUP_CODE_HEADER,
                             ScoreHeaderParser.SUBJECT_REQUIRE_HEADER,
                             ScoreHeaderParser.EDU_SYSTEM_HEADER,
                             ScoreHeaderParser.SCHOOL_FULL_NAME_HEADER,
                             ScoreHeaderParser.BATCH_HEADER,
                             ScoreHeaderParser.PEOPLE_COUNT_DIS_HEADER,
                             ScoreHeaderParser.SCH_FEE_HEADER,
                             ScoreHeaderParser.WENLI_HEADER,
                             ScoreHeaderParser.SCH_ADDR_HEADER,
                             ScoreHeaderParser.LANGUAGE_HEADER,
                             ScoreHeaderParser.NOTE_HEADER]

        # 读取年份表头
        self.__set_year_header(enroll_years)

    def __set_year_header(self, enroll_years=None):
        """
        用户输入录取年份
        """
        if enroll_years is None:
            enroll_years = []

        if enroll_years:
            for year in enroll_years:
                self.enroll_years.append(year)

    def deal_year_header(self):
        """
        用户没有提供录取年份, 从文件内容获取
        """
        if not self.enroll_years:
            for row in self.content_rows:
                years = re.findall(u"20\\d{2}(?=年)", re.sub("\\s+", "", "".join(row)))
                if len(years) > 0:
                    for year in years:
                        self.enroll_years.append(year)
                    break
        if not self.enroll_years:
            raise ParserError(ParserError.INPUT_ERROR_CODE, "设置录取年份失败，文件{0}".format(Path(self.file_path).name))

    def __set_content_header(self):
        """
        通过预定义表头设置表头名称
        """

        for row in self.content_rows:
            header_row = []
            items = set()
            for item in row:
                e = re.sub("\\s+", "", item)
                items.add(e)
                header_row.append(e)

            for item in items:
                for index in range(len(self.header_regex)):
                    # 表头内容必须在同一行出现
                    if self.header_regex[index] == item and item not in self.content_header:
                        self.content_header.append(item)

            if ScoreHeaderParser.NAME_HEADER not in self.content_header:
                continue

            # if self.page_column_count and len(self.content_header) < self.page_column_count:
            #     continue

            return header_row
        raise ParserError(ParserError.INPUT_ERROR_CODE,
                          "表头行定位失败，请规范文件表头行，文件{0}".format(Path(self.file_path).name))

    def deal_header_info(self):
        """
        初始化表头信息
        """
        # 分页
        self.paging_content_rows()
        # 年份
        self.deal_year_header()
        # 设置表头名称
        content_header_row = self.__set_content_header()
        # 设置表头下标
        self.__set_header_index_year_map(content_header_row)

    def __set_header_index_year_map(self, header_row=None):
        """
        分录取年份设置表头下标映射表
        """
        if header_row is None:
            header_row = []
        try:

            for item in self.content_header:
                if not item:
                    continue
                # 只出现一次
                if header_row.count(item) == 1:
                    for y in self.enroll_years:
                        self.header_index_year_map.setdefault(y, {})
                        self.header_index_year_map.get(y)[item] = header_row.index(item)
                else:  # 出现两次
                    start_index = 0
                    for index in range(len(self.enroll_years)):
                        self.header_index_year_map.setdefault(self.enroll_years[index], {})
                        # 第一年从下标0开始匹配，第二年开始从下标(start_index + 1)开始匹配
                        start_index = header_row.index(item, start_index if index == 0 else start_index + 1)
                        self.header_index_year_map.get(self.enroll_years[index])[item] = header_row.index(item,
                                                                                                          start_index)
        except Exception as e:
            logger.exception(e)
            raise ParserError(ParserError.INPUT_ERROR_CODE,
                              "分录取年份设置表头下标映射表失败.文件{0}".format(Path(self.file_path).name))
        if len(self.header_index_year_map) != len(self.enroll_years):
            raise ParserError(ParserError.INPUT_ERROR_CODE,
                              "分录取年份设置表头下标映射表失败.文件{0}".format(Path(self.file_path).name))

    def get_header_index_map(self, enroll_year=None):
        """
        录取年份表头下标映射表
        """
        if enroll_year:
            return self.header_index_year_map.get(enroll_year)
        else:
            return list(self.header_index_year_map.values())[0]

    @staticmethod
    def get_col_by_header_name(header_name, row, header_index_map):
        """
        获取单元格内容
        """
        if header_index_map.get(header_name) is not None:
            return row[header_index_map.get(header_name)]

        return ""

