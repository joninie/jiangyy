#!/usr/bin/env python
# coding=utf-8

import sys
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/score/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/enroll/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/extractor/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/common/")
import re
import logging
import traceback

from pathlib import Path
from common.parser_error import ParserError
from extractor.name_matcher import SchNameMatcher
from score.score_header_parser import ScoreHeaderParser
from score.score_info import SchScoreInfo, MajorScoreInfo
from util.file_util import writeXLS, writeXLSX

logger = logging.getLogger("enroll_score_ocr_parser")


class ScoreInfoParser(ScoreHeaderParser):
    NUM_REGEX = "[1-9]\\d*"
    SCORE_REGEX = "[\\+\\-]?\\d+\\.*\\d*"
    SELECT_SUBJECT_LEVEL_REGEX = "((?<=等级)[^\u4e00-\u9fa5a-dA-D]*([\u4e00-\u9fa5]*[a-dA-D]\\D*[a-dA-D]\\D*))"
    SELECT_SUBJECT_LEVEL_REGEX2 = "((必|选)测.*?等级.*?)"
    # 学校录取数据
    # SCH_SCORE_HEADER = ["招生年份", "省份", "院校名称", "院校代码", "招生年份", "计划数", "录取数", "最高分", "最低分", "平行志愿", "征求志愿",
    SCH_SCORE_HEADER = ["招生年份", "省份", "院校名称", "院校代码", "计划数", "录取数", "最高分", "最低分", "平行志愿", "征求志愿",
                        "服从志愿", "平均分", "最低分与分数线差值", "录取最低分位次", "平均分与分数线差值", "院校全称", "选测科目等级", "必测科目等级",
                        "科目要求", "批次", "文理", "分数段低分", "分数段高分", "分数段人数", "办学地点", "备注"]
    # 专业录取数据
    # MAJOR_SCORE_HEADER = ["招生年份", "省份", "院校名称", "院校代码", "选测科目等级要求", "必测科目等级要求", "院校计划数", "专业名称", "专业名备注", "专业代码", "招生年份", "计划数", "录取数", "最高分", "最低分",
    MAJOR_SCORE_HEADER = ["招生年份", "省份", "院校名称", "院校代码", "选测科目等级要求", "必测科目等级要求", "院校计划数", "专业名称", "专业名备注", "专业代码", "计划数", "录取数", "最高分", "最低分",
                          "平行志愿", "征求志愿", "服从志愿", "平均分", "最低分与分数线差值", "录取最低分位次",
                          "平均分与分数线差值",  "科目要求", "学制", "院校全称", "批次", "文理", "分数段低分", "分数段高分",
                          "分数段人数", "学费", "办学地点", "语种", "备注", "未处理内容"]

    # 文理
    WENLI_REGEX = "理工|文史|艺术综合"

    def __init__(self, file_path, output_dir, page_column_count, enroll_years, province):
        self.sch_score_info_year_map = {}
        super(ScoreInfoParser, self).__init__(file_path, page_column_count, enroll_years, province)
        self.output_dir = output_dir
        self.sch_score_header = ScoreInfoParser.SCH_SCORE_HEADER
        self.major_score_header = ScoreInfoParser.MAJOR_SCORE_HEADER
        self.sch_scores = [ScoreInfoParser.SCH_SCORE_HEADER]
        self.major_scores = [ScoreInfoParser.MAJOR_SCORE_HEADER]
        self.name_matcher = SchNameMatcher()
        self.province = province

        self.only_sch = False  # 只有学校招生计划,不校验学校名称有效性

    def __is_sch_score_row(self, row):

        header_index_map = self.get_header_index_map()
        if header_index_map.get(self.CODE_HEADER) is not None and \
                not ScoreHeaderParser.get_col_by_header_name(self.CODE_HEADER, row, header_index_map):
            return False

        sch_full_name_raw = ScoreHeaderParser.get_col_by_header_name(self.SCHOOL_FULL_NAME_HEADER, row, header_index_map)
        sch_name_raw = ScoreHeaderParser.get_col_by_header_name(self.NAME_HEADER, row, header_index_map)
        enroll_count_raw = ScoreHeaderParser.get_col_by_header_name(ScoreHeaderParser.ENROLL_COUNT_HEADER, row,
                                                                    header_index_map)

        sch_name = re.sub("[^\u4e00-\u9fa5]", " ", sch_name_raw).strip().split(" ")[0]

        sch_alias = ""
        name_array = sch_full_name_raw.split(" ")
        if name_array and len(name_array) >= 2:
            tmp = name_array[1]
            res = re.split("[:：]", tmp)
            sch_alias = res[1] if len(res) > 1 else sch_alias


        # 存在院校全称，院校简称
        # 如果专业组代码缺失，可以通过院校简称比对
        # 专业名称可能有识别错的，导致被学校简称包含。。
        # 不要使用
        if sch_full_name_raw and sch_name_raw and sch_name == sch_alias:
            return True

        return self.name_matcher.is_sch_name(sch_name) or self.name_matcher.is_sch_name(enroll_count_raw)

    def __is_content_header_row(self, row=[]):
        """
        是否表头行
        """
        items = []
        for item in row:
            if item:
                items.append(re.sub("\\s+", "", item))

        for c in self.content_header:
            if c and c in items:
                return True
        return False

    def __add_score_infos(self):
        """
        将学校专业录取数据添加输出列表中
        """
        for enroll_year in self.sch_score_info_year_map.keys():
            sch_score_info = self.sch_score_info_year_map.get(enroll_year)
            sch_scores, major_scores = sch_score_info.convent_to_array()
            if sch_scores:
                self.sch_scores += sch_scores
            if major_scores:
                self.major_scores += major_scores

    def fix_merge_cell(self,  *column_names):
        """
        院校全称
        上下单元格合并情况下，将上一行同列的内容复制到下一行
        """

        for column_name in column_names:
            code = ""

            header_index_map = list(self.header_index_year_map.values())[0]
            code_index = header_index_map.get(column_name)
            for row_index in range(len(self.content_rows)):
                row = self.content_rows[row_index]
                if self.empty_row(row) or self.__is_content_header_row(row):
                    continue
                tmp_code = ScoreHeaderParser.get_col_by_header_name(column_name, row, header_index_map)
                code = tmp_code if tmp_code else code

                if not row[code_index]:
                    row[code_index] = code

    def cell_mv(self, src_cell, dest_cell, row):
        """
        对文件内容某一行进行列移动
        """
        header_index_map = self.get_header_index_map()
        dest_cell_index = header_index_map.get(dest_cell)
        src_cell_raw = ScoreHeaderParser.get_col_by_header_name(src_cell, row, header_index_map)
        dest_cell_raw = ScoreHeaderParser.get_col_by_header_name(dest_cell, row, header_index_map)
        if not dest_cell_raw and src_cell_raw:
            dest_cell_raw = src_cell_raw
            row[dest_cell_index] = dest_cell_raw

    def row_expand(self, *header_names):
        """
        文件内容列拓展，添加列，并把列名添加到映射表中
        如果待拓展的列已经存在表头中，抛异常。
        """
        for h in header_names:
            if h in self.content_header:
                raise ParserError(ParserError.RUNTIME_ERROR_CODE,
                                  "拓展列 {} 已经存在，{}".format(h, Path(self.file_path).name))
        for row_index in range(len(self.content_rows)):
            row = self.content_rows[row_index]
            for header_name in header_names:
                if self.__is_content_header_row(row) and header_name not in self.content_header:
                    row.append(header_name)
                    self.content_header.append(header_name)
                    self.get_header_index_map()[header_name] = row.index(header_name)
                else:
                    row.append("")

    def deal_content_info(self):
        try:
            # 处理表头信息
            self.deal_header_info()

            select_subject_level = None


            # 2017上海录取数据出现专业组代码列，其中如果包含了院校全称，则拓展院校全称列
            if self.get_header_index_map().get(self.MAJOR_GROUP_CODE_HEADER) is not None:
                # 是否已经拓展院校全称列
                is_expanded = False
                # 将院校全称移动到对应的列
                for row_index in range(len(self.content_rows)):
                    row = self.content_rows[row_index]
                    if self.empty_row(row) or self.__is_content_header_row(row):
                        continue
                    sch_full_name = self.get_col_by_header_name(self.MAJOR_GROUP_CODE_HEADER, row, self.get_header_index_map())
                    # 专业组代码列出现中文，以院校全称处理
                    if sch_full_name and re.search("[\u4e00-\u9fa5]", sch_full_name):
                        if not is_expanded:
                            self.row_expand(self.SCHOOL_FULL_NAME_HEADER)
                            is_expanded = True
                        std_sch = self.name_matcher.match_std_sch(sch_full_name.strip().split(" ")[0])
                        if std_sch:
                            # 将院校全称从专业组代码列移动院校全称列
                            self.cell_mv(self.MAJOR_GROUP_CODE_HEADER, self.SCHOOL_FULL_NAME_HEADER, row)
                        elif row_index > 2: # 跳过表头
                            pre_row = self.content_rows[row_index-1]
                            pre_row[self.get_header_index_map().get(self.SCHOOL_FULL_NAME_HEADER)] += " " + sch_full_name
                self.fix_merge_cell(self.SCHOOL_FULL_NAME_HEADER)

            for row_index in range(len(self.content_rows)):

                if row_index == 350:
                    print(row_index)
                row = self.content_rows[row_index]

                # 空行/内容表头行不处理
                if self.empty_row(row) or self.__is_content_header_row(row):
                    continue

                header_index_map = self.get_header_index_map()
                name_raw = ScoreHeaderParser.get_col_by_header_name(self.NAME_HEADER, row, header_index_map)
                beizhu_raw = ScoreHeaderParser.get_col_by_header_name(self.NAME_HEADER, row, header_index_map)
                code_raw = ScoreHeaderParser.get_col_by_header_name(self.CODE_HEADER, row, header_index_map)
                major_group_code_raw = ScoreHeaderParser.get_col_by_header_name(self.MAJOR_GROUP_CODE_HEADER, row,
                                                                                header_index_map)
                subject_require_raw = ScoreHeaderParser.get_col_by_header_name(self.SUBJECT_REQUIRE_HEADER, row,
                                                                               header_index_map)

                # 学校/专业行
                sch_or_major_row = False

                #  会跳过专业组代码列包含的院校全称行
                if name_raw or code_raw:
                    # 江苏选测科目等级

                    # beizhu = re.findall(r'以下[\s\S]+', name_raw)
                    # if beizhu:
                    #     beizhu = beizhu[0]
                    #     name_dealed = name_raw.split(beizhu)[0].strip()
                    # else:
                    #     beizhu = ''

                    level_raw = ScoreInfoParser.get_col_by_header_name(self.NAME_HEADER, row, self.get_header_index_map())
                    if level_raw:
                        level_res = re.search(ScoreInfoParser.SELECT_SUBJECT_LEVEL_REGEX, level_raw)
                    #     if level_res:
                    #         select_subject_level = level_res.group(2)
                    #         continue
                    #     else:
                    #         # select_subject_level = re.findall(r'((必测|选测).*)', level_raw)
                    #         # if select_subject_level:
                    #         #     select_subject_level = select_subject_level[0]
                    #         #     if select_subject_level:
                    #         #         select_subject_level = select_subject_level[0]
                    #         #         name_raw = name_raw.split(select_subject_level)[0].strip()
                    #
                    #         select_subject_level = re.findall(r'..科目等级.*', name_raw)
                    #         if select_subject_level:
                    #             select_subject_level = select_subject_level[0]
                    #             name_dealed = name_dealed.split(select_subject_level)[0].strip()
                    #
                    #         else:
                    #             select_subject_level = ''
                    # else:
                    #     select_subject_level = ''

                    # 文理
                    wenli_res = re.match(ScoreInfoParser.WENLI_REGEX, name_raw)
                    if wenli_res:
                        # 将已有的专业输出
                        for enroll_year in self.enroll_years:
                            s = self.sch_score_info_year_map.get(enroll_year)
                            if s and s.major_score_infos:
                                self.__add_score_infos()
                                # 输出后将专业清空
                                for e in self.enroll_years:
                                    self.sch_score_info_year_map.get(e).major_score_infos = []
                                break

                        for enroll_year in self.enroll_years:
                            s = SchScoreInfo(self)
                            s.deal_sch_info_row(row, enroll_year)
                            sch_score_info = self.sch_score_info_year_map.get(enroll_year)
                            if sch_score_info:
                                sch_score_info.wenli = name_raw
                                sch_score_info.enroll_count = s.enroll_count
                                sch_score_info.people_count = s.people_count
                                sch_score_info.score_interval_dis = s.score_interval_dis
                            else:
                                self.sch_score_info_year_map[enroll_year] = s
                        continue


                    code_res = re.search("((?:^[a-zA-Z\\d]+)|(?:[a-zA-Z\\d]+$))", code_raw)
                    code_length = len(code_res.group(0)) if code_res else 0

                    if not code_raw and header_index_map.get(self.CODE_HEADER) is None:
                        code_res = re.search("((?:^[a-zA-Z\\d]+)|(?:[a-zA-Z\\d]+$))", name_raw)
                        code_length = len(code_res.group(0)) if code_res else 0

                    mgc_res = re.search("([a-zA-Z\\d]+)", major_group_code_raw)
                    mgc = mgc_res.group(1) if mgc_res else ""

                    # 存在专业组代码，并且专业组代码合法
                    # 学校名称是标准学校名
                    # 代码位数为4位及以上
                    if major_group_code_raw and len(mgc) > 1 or self.__is_sch_score_row(row) or code_length >= 4 or\
                            (not code_raw and subject_require_raw and name_raw):
                        self.__add_score_infos()
                        self.sch_score_info_year_map = {}
                        for enroll_year in self.enroll_years:
                            sch_score_info = SchScoreInfo(self)

                            global select_subject_level

                            sch_score_info.deal_sch_info_row(row, enroll_year)


                            beizhu, select_subject_level, name_dealed = sch_score_info.deal_jiangsu_sch_name(name_raw)
                            # sch_score_info.sch_name = name_raw
                            sch_score_info.sch_name = name_dealed
                            sch_score_info.province = self.province
                            sch_score_info.beizhu = beizhu
                            sch_score_info.subject_require = select_subject_level
                            sch_score_info.must_test_subjects, sch_score_info.select_test_subjects = sch_score_info.deal_jiangsu_require_subjects(select_subject_level)
                            # sch_score_info.province = self.province

                            # sch_score_info.select_subject_level = select_subject_level

                            # # 确定是学校名称了，就不需要再验证是否合法
                            # if sch_score_info.legal_score_info() or sch_score_info.legal_sch_info():
                            sch_or_major_row = True
                            self.sch_score_info_year_map[enroll_year] = sch_score_info
                        # select_subject_level = None
                    else:
                        for enroll_year in self.enroll_years:
                            major_score_info = MajorScoreInfo(self)


                            major_score_info.deal_major_info_row(row, enroll_year)

                            beizhu, select_subject_level1, name_dealed = major_score_info.deal_jiangsu_sch_name(name_raw)
                            major_score_info.beizhu = beizhu
                            major_name = major_score_info.major_name
                            major_beizhu = re.findall('[(（].*[)）]', major_name)
                            if major_beizhu:
                                major_beizhu = major_beizhu[0].strip()
                                major_name = major_name.strip(major_beizhu).strip()
                                major_score_info.major_name = major_name
                                major_score_info.major_beizhu = major_beizhu


                            major_score_info.select_subject_level = select_subject_level1
                            # major_score_info.subject_require = select_subject_level

                            select_subject_level = select_subject_level1 if select_subject_level1 else select_subject_level
                            major_score_info.must_test_subjects, major_score_info.select_test_subjects = major_score_info.deal_jiangsu_require_subjects(select_subject_level)





                            # major_score_info.beizhu = beizhu

                            # 验证是否合法的专业行，通过分数等
                            if major_score_info.legal_score_info() or major_score_info.legal_major_info():
                                sch_or_major_row = True
                                # 如果找不着对应年份的学校录取数据, 则添加空的学校信息
                                sch_score_info = self.sch_score_info_year_map.get(enroll_year)
                                if not sch_score_info:
                                    logger.warning("文件名%s, 第%d行, 专业行找不着对应年份的学校录取数据.", self.file_path, row_index + 1)
                                    self.sch_score_info_year_map[enroll_year] = SchScoreInfo(self)
                                self.sch_score_info_year_map.get(enroll_year).major_score_infos.append(major_score_info)

                #江苏2018年招生计划，专业备注说明：


                # 未被处理(不是学校或者专业)
                note = (" ".join(row)).strip()
                if not sch_or_major_row and note:
                    if len(list(self.sch_score_info_year_map.values())) < 1:
                        logger.warning("文件名%s, 第%d行, 备注行找不着学校专业录取数据.", self.file_path, row_index + 1)
                        self.sch_score_info_year_map[-1] = SchScoreInfo(self)
                    if not list(self.sch_score_info_year_map.values())[-1].major_score_infos:
                        list(self.sch_score_info_year_map.values())[-1].major_score_infos.append(
                            MajorScoreInfo(self))
                    list(self.sch_score_info_year_map.values())[-1].major_score_infos[-1].note += "\n" + "行数" + \
                                                                                                  str(row_index+1) + \
                                                                                                  " " + note

            self.__add_score_infos()

            src_file = Path(self.file_path).name.split(".")[0]
            sch_file = src_file + "-sch_info.xls"
            major_file = src_file + "-major_info.xls"
            writeXLSX(self.sch_scores,
                     str(Path(self.output_dir) / sch_file))
            writeXLSX(self.major_scores, str(Path(self.output_dir) / major_file))
            return 0, "文件{0}处理成功".format(Path(self.file_path).name)
        except ParserError as e:
            logger.exception(e)
            return e.error_code, e.message
        except Exception as e:
            logger.exception(e)
            return ParserError.RUNTIME_ERROR_CODE, "程序异常，处理文件{}".format(Path(self.file_path).name)

