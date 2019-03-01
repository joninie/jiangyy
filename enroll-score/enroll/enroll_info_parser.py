#!/usr/bin/env python
# coding=utf-8
import sys
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/score/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/enroll/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/extractor/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/common/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/conf/")
import os
import re
import logging
import traceback
from pathlib import Path

from common.parser_error import ParserError
from common.pageable_parser import PageableParser
from enroll.enroll_info import SchEnrollInfo, MajorEnrollInfo
from extractor.name_matcher import SchNameMatcher
from util.file_util import writeXLS

logger = logging.getLogger("enroll_score_ocr_parser")


class EnrollHeaderParser(PageableParser):
    """
    解析文件表头
    """
    CODE_HEADER_REGEX = "院校专业代码"
    NAME_HEADER_REGEX = "院校专业名称"
    ENROLL_COUNT_HEADER_REGEX = "计划数"
    SCH_FEE_HEADER_REGEX = "学费"
    EDU_SYSTEM_HEADER_REGEX = "学制"
    WENLI_REGEX = "文理"
    BATCH_REGEX = "批次"
    AVG_SCORE_REGEX = "平均分"
    SCH_ADDR_REGEX = "办学地点"

    def __init__(self, file_path, page_column_count):
        super(EnrollHeaderParser, self).__init__(file_path, page_column_count)

        # 注意__change_header_name 方法中修改表头名称的顺序！
        self.content_header_regex = [EnrollInfoParser.CODE_HEADER_REGEX,
                                     EnrollInfoParser.NAME_HEADER_REGEX,
                                     EnrollInfoParser.ENROLL_COUNT_HEADER_REGEX,
                                     EnrollInfoParser.SCH_FEE_HEADER_REGEX,
                                     EnrollInfoParser.EDU_SYSTEM_HEADER_REGEX,
                                     EnrollInfoParser.WENLI_REGEX,
                                     EnrollInfoParser.BATCH_REGEX,
                                     EnrollInfoParser.AVG_SCORE_REGEX,
                                     EnrollInfoParser.SCH_ADDR_REGEX]  # 原始文件表头
        self.CODE = None
        self.NAME = None
        self.ENROLL_COUNT = None
        self.SCH_FEE = None
        self.EDU_SYSTEM = None

        self.WENLI = None
        self.BATCH = None
        self.AVG_SCORE = None
        self.SCH_ADDR = None

        self.content_header = [self.CODE,
                               self.NAME,
                               self.ENROLL_COUNT,
                               self.SCH_FEE,
                               self.EDU_SYSTEM,
                               self.WENLI,
                               self.BATCH,
                               self.AVG_SCORE,
                               self.SCH_ADDR]
        self.header_index_map = {}  # 原始文件表头下表映射
        self.name_matcher = SchNameMatcher()

    @staticmethod
    def is_empty_row(row=[]):
        """是否空行"""
        for item in row:
            e = re.sub("\\s+", "", item)
            if e:
                return False
        return True

    @staticmethod
    def get_col_by_header_name(row, header_name, header_index_map={}):
        if header_index_map.get(header_name) is not None:
            return row[header_index_map.get(header_name)]
        else:
            return ""

    def __set_content_header(self):
        """
        设置用户输入表头, 该表头名需与文件内容表头一致.
        清除空白字符
        """
        # if content_header and len(content_header) > 1:
        #     self.content_header = [i for i in content_header]
        #     for i in range(len(self.content_header)):
        #         self.content_header[i] = re.sub("\\s+", "", self.content_header[i])
        # else:
        for row in self.content_rows:
            items = set()
            header_row = []
            for item in row:
                e = re.sub("\\s+", "", item)
                items.add(e)
                header_row.append(e)

            for item in items:
                for index in range(len(self.content_header_regex)):
                    # 表头内容必须在同一行出现
                    if not self.content_header[index]:
                        res = re.search(self.content_header_regex[index], item)
                        self.content_header[index] = item if res else self.content_header[index]

            # 该表头行有缺陷，院校专业名称不存在
            if not self.content_header[self.content_header_regex.index(EnrollHeaderParser.NAME_HEADER_REGEX)]:
                continue
            # # 识别的表头个数少于单个院校专业的列数，可能存在不可识别的表头
            # if self.page_column_count and len(self.content_header) < self.page_column_count / 2:
            #     continue

            # 与content_header_regex 顺序保持一致
            self.CODE = self.content_header[0]
            self.NAME = self.content_header[1]
            self.ENROLL_COUNT = self.content_header[2]
            self.SCH_FEE = self.content_header[3]
            self.EDU_SYSTEM = self.content_header[4]
            self.WENLI = self.content_header[5]
            self.BATCH = self.content_header[6]
            self.AVG_SCORE = self.content_header[7]
            return header_row
        raise ParserError(ParserError.INPUT_ERROR_CODE,
                          "表头行定位失败,请规范文件表头.文件{0}".format(Path(self.file_path).name))

    def __set_header_index_map(self, header_row):
        """
        将用户设置的表头映射到文件对应的表头下表
        """
        for index in range(len(self.content_header)):
            item = self.content_header[index]
            if item:
                self.header_index_map[item] = header_row.index(item)

    def deal_content_header(self):
        """
        检验提供的表头信息
        """
        self.paging_content_rows()
        header_row = self.__set_content_header()
        self.__set_header_index_map(header_row)

    def is_header_row(self, row):
        """
        是否表头行
        """
        items = []
        # 对整行内容去除空白字符,不影响文件内容
        for item in row:
            e = re.sub(u"\\s+", u"", item)
            items.append(e)

        for item in self.content_header:
            if item in items:
                return True
        return False


class EnrollInfoFormat(object):
    pass


class EnrollInfoParser(EnrollHeaderParser):

    """
    招生信息内容解析
    """
    CODE_REGEX = u"[a-zA-Z\\d]{}"

    def __init__(self, file_path, output_dir, page_column_count):
        
        super(EnrollInfoParser, self).__init__(file_path, page_column_count)

        self.std_header = ["院校名称", "院校代码", "院校计划数", "校址", "专业名称", "专业代码", "专业计划数", "学费", "学制",
                           "文理", "批次", "平均分", "语种", "未处理内容"]  # 输出文件表头

        self.format_rows = []  # 格式化文件内容
        self.std_rows = [self.std_header]  # 输出文件内容
        self.output_dir = output_dir
        self.sch_row_format = None
        self.major_enroll_info_function = None
        self.name_matcher = SchNameMatcher()

    def cell_mv(self, src_cell, dest_cell, row):
        """
        对文件内容某一行进行列移动
        """
        header_index_map = self.header_index_map
        dest_cell_index = header_index_map.get(dest_cell)
        src_cell_raw = EnrollHeaderParser.get_col_by_header_name( row, src_cell, header_index_map)
        dest_cell_raw = EnrollHeaderParser.get_col_by_header_name(row, dest_cell, header_index_map)
        if not dest_cell_raw and src_cell_raw:
            dest_cell_raw = src_cell_raw
            row[dest_cell_index] = dest_cell_raw



    def deal_content_rows(self):
        try:

            self.deal_content_header()

            sch_enroll_info = SchEnrollInfo()
            for row in self.content_rows:
                # 17甘肃 特殊处理
                # self.cell_mv(EnrollHeaderParser.CODE_HEADER_REGEX, EnrollHeaderParser.NAME_HEADER_REGEX, row)

                # 学校内容行特殊处理, 函数名在conf/enroll_config.ini 中sch-row-format-function 指定, 函数对象在enroll_info.py 中定义
                if self.sch_row_format is not None:
                    row = self.sch_row_format(row, self.header_index_map, self)
                name_raw = EnrollInfoParser.get_col_by_header_name(row, self.NAME, self.header_index_map)
                enroll_count_raw = EnrollInfoParser.get_col_by_header_name(row, self.ENROLL_COUNT, self.header_index_map)
                sch_fee_raw = EnrollInfoParser.get_col_by_header_name(row, self.SCH_FEE, self.header_index_map)
                edu_system_raw = EnrollInfoParser.get_col_by_header_name(row, self.EDU_SYSTEM, self.header_index_map)
                wenli_raw = EnrollHeaderParser.get_col_by_header_name(row, self.WENLI, self.header_index_map)
                batch_raw = EnrollHeaderParser.get_col_by_header_name(row, self.BATCH, self.header_index_map)
                avg_score_raw = EnrollHeaderParser.get_col_by_header_name(row, self.AVG_SCORE, self.header_index_map)
                code_raw = EnrollInfoParser.get_col_by_header_name(row, self.CODE_REGEX, self.header_index_map)
                code_res = re.match("([a-zA-Z\\d]+)", code_raw if code_raw else name_raw)
                code_length = len(code_res.group(1)) if code_res else 0

                if self.is_header_row(row) or self.is_empty_row(row):
                    continue
                # 学校行
                if self.name_matcher.is_sch_name(name_raw) or code_length >= 4:
                    self.std_rows = sch_enroll_info.add_sch_enroll_info(self.std_rows)
                    sch_enroll_info = SchEnrollInfo()
                    sch_enroll_info.deal_sch_info_row(row, self.header_index_map, self)
                elif name_raw and (enroll_count_raw or sch_fee_raw or edu_system_raw or wenli_raw or batch_raw or avg_score_raw):
                    major_enroll_info = MajorEnrollInfo()
                    major_enroll_info.deal_major_info_row(row, self.header_index_map, self)
                    sch_enroll_info.major_enroll_infos.append(major_enroll_info)
                else:
                    # 作为上一行的备注
                    if sch_enroll_info and len(sch_enroll_info.major_enroll_infos) > 0:
                        major_enroll_info = sch_enroll_info.major_enroll_infos[-1]
                        major_enroll_info.note = "\n" + " ".join(row) if self.note else " ".join(row)

            if sch_enroll_info.name or len(sch_enroll_info.major_enroll_infos) > 0:
                self.std_rows = sch_enroll_info.add_sch_enroll_info(self.std_rows)

            writeXLS(self.std_rows,
                     os.path.join(self.output_dir, os.path.basename(self.file_path).split(".")[0] + ".xls"))
            return 0, "文件{0}处理成功".format(Path(self.file_path).name)
        except ParserError as e:
            logger.exception(e.message)
            return e.error_code, e.message
        except Exception as e:
            logger.exception(e)
            return ParserError.RUNTIME_ERROR_CODE, "程序异常，处理文件{}".format(Path(self.file_path).name)

