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
from util.file_util import readXLS_R1



logger = logging.getLogger("enroll_score_ocr_parser")

class PageableParser(object):
    """
    文件内容分页处理， 原始内容为self.content_rows， 分页后的内容为paged_content_rows
    """
    def __init__(self, file_path, page_column_count, province):
        self.file_path = file_path
        # 每页的列数
        self.page_column_count = page_column_count
        # 原始文件内容, 分页后取__paged_content_rows
        self.content_rows = []
        # 分页后的内容
        self.__paged_content_rows = []

    def __read_content_rows(self):
        self.content_rows = readXLS_R1(self.file_path)

    def paging_content_rows(self):
        self.__read_content_rows()

        if not self.content_rows:
            raise ParserError(ParserError.INPUT_ERROR_CODE,
                              "文件内容为空，{}".format(Path(self.file_path).name))
        # 需要分页， 内容的列数为每一页列数的整数倍
        if self.page_column_count:
            if self.content_rows and len(self.content_rows[0]) % self.page_column_count == 0:
                logger.info("对文件%s内容分页处理，内容列数%d，分页列数%d。", self.file_path, len(self.content_rows[0]),
                            self.page_column_count)
                page_count = int(len(self.content_rows[0]) / self.page_column_count)
                page_raws = []
                for i in range(page_count):
                    page_raws.append([])
                for row in self.content_rows:
                    if not self.empty_row(row):
                        for page_index in range(page_count):
                            page_raws[page_index].append(row[self.page_column_count*page_index:self.page_column_count*(page_index + 1)])
                    else:
                        for i in range(len(page_raws)):
                            self.__paged_content_rows += page_raws[i]
                            page_raws[i] = []
                for i in range(len(page_raws)):
                    self.__paged_content_rows += page_raws[i]
                    page_raws[i] = []
                # 将分页后的内容覆盖content_rows
                self.content_rows = self.__paged_content_rows
                if not self.content_rows:
                    raise ParserError(ParserError.RUNTIME_ERROR_CODE,
                                      "分页后文件内容为空，{0}".format(Path(self.file_path).name))
            else:
                raise ParserError(ParserError.INPUT_ERROR_CODE,
                                  "分页参数{0}不能整除文件列数，文件名{1}".format(self.page_column_count,
                                                                  Path(self.file_path).name))

    @staticmethod
    def empty_row(row=[]):
        for item in row:
            if re.sub("\\s+", "", item):
                return False
        return True
