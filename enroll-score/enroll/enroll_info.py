#!/usr/bin/env python
# coding=utf-8
import re


class SchEnrollInfo(object):
    SCORE_REGEX = "[\\+\\-]?[1-9]\\d{0,}\\.*\\d*"

    def __init__(self):
        self.code = None
        self.name = None
        self.enroll_count = None
        self.sch_addr = None
        self.wenli = None
        self.batch = None
        self.province = None
        self.enroll_year=None
        self.major_beizhu = None
        self.note = ""
        self.major_enroll_infos = []

    def copy_value(self, sch_enroll_info):
        if isinstance(sch_enroll_info, SchEnrollInfo):
            property_dict = sch_enroll_info.__dict__
            for k, v in property_dict.items():
                if self.__dict__.get(k) is None:
                    self.__dict__[k] = v


    def deal_sch_info_row(self, row, header_map, enroll_info_parser):
        self.code = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.CODE, header_map)
        self.name = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.NAME, header_map)

        code_raw = self.code if self.code else self.name
        if code_raw:
            code_res = re.match("[a-zA-Z\\d]*", code_raw.strip())
            if code_res:
                self.code = code_res.group(0)
                if self.name.startswith(self.code):
                    self.name = re.sub(self.code, "", self.name, 1)

        sch_split_flag = False
        self.enroll_count = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.ENROLL_COUNT, header_map)
        if self.enroll_count:
            enroll_count_res = re.search(u"[1-9]\\d*", self.enroll_count)
            self.enroll_count = enroll_count_res.group(0) if enroll_count_res else u""
        else:
            # 在学校名中获取计划数
            enroll_count_res = re.search("([1-9]\\d*(?=[人名]))", self.name)
            if enroll_count_res:
                self.enroll_count = enroll_count_res.group(1)
                sch_split_flag = True

        ## 从院校名称中提取办学地点
        self.sch_addr = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.SCH_ADDR, header_map)
        if not self.sch_addr and self.name:
            sch_addr_res = re.search("(?<=办学地点)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]+)", self.name)
            if sch_addr_res:
                self.sch_addr = sch_addr_res.group(1)
                sch_split_flag = True
        if sch_split_flag:
            self.name = re.split("\\s+", self.name.strip())[0]

    def add_sch_enroll_info(self, std_rows):
        if self.name or self.major_enroll_infos:
            if len(self.major_enroll_infos) == 0:
                self.major_enroll_infos.append(MajorEnrollInfo())
            # ["招生年份", "省份", "院校代码", "院校名称", "院校计划数", "校址", "专业名称", "专业名备注", "专业代码", "专业计划数", "学费", "学制","文理", "批次",
            # "平均分", "语种", "未处理内容"]
            for m in self.major_enroll_infos:
                std_rows.append([
                    self.enroll_year,
                    self.province,
                    self.code,
                    self.name,
                    self.enroll_count,
                    m.sch_addr if m.sch_addr else self.sch_addr,
                    m.name,
                    m.major_beizhu,
                    m.code,
                    m.enroll_count,
                    m.sch_fee,
                    m.edu_system,
                    m.wenli if m.wenli else self.wenli,
                    m.batch if m.batch else self.batch,
                    m.avg_score,
                    m.language,
                    m.note
                ])
        return std_rows


class MajorEnrollInfo(object):
    MAJOR_CODE_REGEX = u"\[*[a-zA-Z\\d]{2,}\]*"

    def __init__(self):
        self.code = None
        self.name = None
        self.major_beizhu = None
        self.enroll_count = None
        self.edu_system = None
        self.sch_fee = None

        self.wenli = None
        self.batch = None
        self.avg_score = None
        self.language = None
        self.sch_addr = None

        self.enroll_count_raw = None

        self.note = ""

    def deal_major_info_row(self, row, header_map, enroll_info_parser):

        self.code = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.CODE, header_map)
        self.name = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.NAME, header_map)

        if not self.code:
            code_raw =  self.name
            if code_raw:
                code_res = re.match("[a-zA-Z\\d]*", code_raw.strip())
                if code_res:
                    self.code = code_res.group(0)
                    if self.name.startswith(self.code):
                        self.name = re.sub(self.code, "", self.name, 1)

        self.enroll_count_raw = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.ENROLL_COUNT, header_map)
        if self.enroll_count_raw:
            enroll_count_res = re.search("[1-9]\\d*", self.enroll_count_raw)
            self.enroll_count = enroll_count_res.group(0) if enroll_count_res else ""

        self.sch_fee = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.SCH_FEE, header_map)
        self.edu_system = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.EDU_SYSTEM, header_map)
        self.wenli = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.WENLI, header_map)
        self.batch = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.BATCH, header_map)
        self.avg_score = enroll_info_parser.get_col_by_header_name(row, enroll_info_parser.AVG_SCORE, header_map)
        if self.avg_score:
            avg_score_res = re.search(SchEnrollInfo.SCORE_REGEX, self.avg_score)
            self.avg_score = avg_score_res.group(0) if avg_score_res else ""

        if not self.enroll_count:
            enroll_count_res = re.search("[1-9]\\d*(?=[人名])", self.sch_fee)
            if not enroll_count_res:
                enroll_count_res = re.search("[1-9]\\d*(?=[人名])", self.wenli)
            if enroll_count_res:
                self.enroll_count = enroll_count_res.group(0)

    def all_into_major_note(self, row):
        self.note = " ".join(row) if not self.note else self.note + "\n" + " ".join(row)

    def deal_major_note_row(self, row):
        self.all_into_major_note(row)

    def legal_major_enroll_info(self):
        if not self.name:
            return False
        if self.enroll_count_raw and not self.enroll_count:
            return False

        return True


