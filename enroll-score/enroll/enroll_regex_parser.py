#!/usr/bin/env python
# coding=utf-8
import sys
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/score/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/enroll/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/extractor/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/common/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/conf/")
import re, logging
import traceback
from pathlib import Path
from util.file_util import writeXLSX
from common.pageable_parser import PageableParser
from common.parser_error import ParserError
from enroll.enroll_info import SchEnrollInfo
from enroll.enroll_info import MajorEnrollInfo

logger = logging.getLogger("enroll_score_ocr_parser")


class EnrollRegexParser(PageableParser):
    """
    招生计划所有内容在一列
    """
    # SCH_CODE_REGEX = "([\\[\\(［【]*[\\da-zA-Z]{3,}[\\]】\\)］]*)"
    SCH_CODE_REGEX = "([\\da-zA-Z]{3,})"
    # 匹配英文学校名
    SCH_NAME_REGEX = "[\\s]*([^\\d\\(（\\[{〔<【]+(?:大学|学院|校区|分校|学校)(?:[\\(（\\[{〔<【][\\S]+[\\)）\\]}］>】])?(?:[^\\s\\d]*))"

    BATCH_REGEX = "[\\s\\S]*([本专]科第*[一二三]批)?"
    SCH_ADDR_REGEX = "((?:(?:(?<=[校地][址点])|(?<=[校地][址点][^\u4e00-\u9fa5])|(?<=所在地)|(?<=所在地[^\u4e00-\u9fa5]))[\u4e00-\u9fa5]{2,})|(?:[\u4e00-\u9fa5]{2,7}[省市区][\\S]*))"
    # 不够稳
    # SCH_ADDR_REGEX = re.search("((?:(?:(?<=[校地][址点])|(?<=所在地)(?<=[^\u4e00-\u9fa5])?)[\u4e00-\u9fa5]+)|(?:[\u4e00-\u9fa5]{2,7}[省市区]))")
    # 文理规则单独使用时不可加可有可无"?"规则
    # 在院校、专业规则中加
    WENLI_REGEX = "((?:文史|理工|艺术综合|体育[(（][文理][)）])(?:类|[^\u4e00-\u9fa5\\d])?)"

    MAJOR_CODE_REGEX = "([\\[［\\(【]*[\\da-zA-Z]{1,3}[\\]】\\)］]*)"
    # MAJOR_NAME_REGEX = "[\\s]*([^\\d\\s\\(（【［<{\\[]{2,}(?:[\\(（【［<{\\[][^\\)）】］>\\]]+[\\)）】］>\\]])*)"
    MAJOR_NAME_REGEX = "[\\s]*([^\\d\\s\\(（【［<{\\[]{2,}(?:[\\(（【［<{\\[][^\\s\\)）】］>\\]]+[\\)）】］>\\]])*)"
    # ENROLL_COUNT_REGEX = "(?:\\D*((?:(?<!\\d)[1-9]\\d{,3}\\s*(?=[人名]))|(?:(?<!\\d)[1-2]\\d{3}(?!\\s*[\\d元年号]))|(?:(?<!\\d)[1-9]\\d{,2}(?!\\s*[\\d元年号]))))?"
    ENROLL_COUNT_REGEX="(?:\\D*((?:(?<!\\d)[1-9]\\d{,3}\\s*(?=[人名]))|(?:(?<![\\+\\d])[1-2]\\d{3}(?![\\d\\+元年分号]))|(?:(?<![\\+\\d])[1-9]\\d{,2}(?![\\d\\+元分年号]))))?"
    EDU_SYSTEM_REGEX = "(?:\\D*((?:[2-8](?:\\s*年))|(?:[2-8](?!\\s*[人名号分\\+\\.\\da-zA-Z]))|(?:[1-9](?:\\+[1-9])+)))?"
    SCH_FEE_REGEX = "(?:\\D*((?:(?<=学费)(?:[\\D]?)\\d{3,})|(?:\\d{3,}(?![人名年号分])(?:元)?(?:/[学\\s]*年)?)|(?:[1-9](?:.[\\d]+)?万)))?"
    LANGUAGE_REGEX = "(?<=语种)(?:[^\u4e00-\u9fa5]*)([\u4e00-\u9fa5]+)"
    MAJOR_BEIZHU_REGEX = "([(<（][\s\S]+[)>）、])"
    OTHERS_REGEX = "([\\s\\S]*)"

    SCH_CODE_HEADER = "院校代码"
    SCH_NAME_HEADER = "院校名称"
    SCH_ADDR_HEADER = "校址"
    BATCH_HEADER = "批次"
    WENLI_HEADER = "文理"

    MAJOR_CODE_HEADER = "专业代码"
    MAJOR_NAME_HEADER = "专业名称"
    MAJOR_BEIZHU_HEADER = "专业备注"

    ENROLL_COUNT_HEADER = "计划数"
    EDU_SYSTEM_HEADER = "学制"
    SCH_FEE_HEADER = "学费"
    LANGUAGE_HEADER = "语种"

    OTHERS_HEADER = "未处理内容"

    REGEX_MAPPING = {
        SCH_CODE_HEADER:     SCH_CODE_REGEX,
        SCH_NAME_HEADER:     SCH_NAME_REGEX,
        SCH_ADDR_HEADER:     SCH_ADDR_REGEX,
        BATCH_HEADER:        BATCH_REGEX,
        WENLI_HEADER:        WENLI_REGEX,
        MAJOR_CODE_HEADER:   MAJOR_CODE_REGEX,
        MAJOR_NAME_HEADER:   MAJOR_NAME_REGEX,
        MAJOR_BEIZHU_HEADER: MAJOR_BEIZHU_REGEX,
        ENROLL_COUNT_HEADER: ENROLL_COUNT_REGEX,
        EDU_SYSTEM_HEADER:   EDU_SYSTEM_REGEX,
        SCH_FEE_HEADER:      SCH_FEE_REGEX,
        LANGUAGE_HEADER:     LANGUAGE_REGEX,
        OTHERS_HEADER:       OTHERS_REGEX
    }

    def __init__(self, file_path, output_dir, page_column_count, enroll_year, sch_column_names, major_column_names, province):
        super(EnrollRegexParser, self).__init__(file_path, page_column_count, province)
        self.file_path = file_path
        self.output_dir = output_dir
        self.page_column_count = page_column_count
        self.sch_column_names = sch_column_names
        self.major_column_names = major_column_names

        self.enroll_year = enroll_year
        self.province = province

        # 学校行实体类型正则
        self.sch_regex = ""
        # 学校行实体类型
        self.sch_regex_header = []

        # 专业行正则
        self.major_regex = ""
        # 专业行实体类型
        self.major_regex_header = []

        self.std_rows = [["招生年份", "省份", "院校代码", "院校名称", "院校计划数", "校址", "专业名称", "专业名备注", "专业代码", "专业计划数", "学费", "学制",
                          "文理", "批次", "平均分", "语种", "未处理内容"]]

    def generate_regex(self):

        self.sch_column_names = [] if not self.sch_column_names else self.sch_column_names
        self.major_column_names = [] if not self.major_column_names else self.major_column_names

        if self.sch_column_names and type(self.sch_column_names) == list:
            for col in self.sch_column_names:
                v = EnrollRegexParser.REGEX_MAPPING.get(col)
                if not v:
                    raise ParserError(ParserError.INPUT_ERROR_CODE, "院校招生信息内容实体名称<{}>不能识别".format(col))

                # 文理规则为可有可无
                if col == EnrollRegexParser.WENLI_HEADER:
                    self.sch_regex += "[^文理]*" + v + "?"
                    self.sch_regex_header.append(col)
                elif col in [EnrollRegexParser.SCH_ADDR_HEADER, EnrollRegexParser.LANGUAGE_HEADER]:
                    # 校址单独处理
                    pass
                else:
                    self.sch_regex += v if not self.sch_regex else  v
                    # re.search("(?:((?:\\D*(?<!\\d)[1-2]\\d{3}(?![\\d元]))|(?:(?<!\\d)[1-9]\\d{,2}(?![\\d元]))(?=[人名])?))?")
                    self.sch_regex_header.append(col)
            self.sch_regex += EnrollRegexParser.OTHERS_REGEX

        elif self.sch_column_names and type(self.sch_column_names) != list:
            raise ParserError(ParserError.INPUT_ERROR_CODE, "院校招生信息内容实体名称必填并以','（英文逗号）隔开。")

        if self.major_column_names and type(self.major_column_names) == list:
            for col in self.major_column_names:
                v = EnrollRegexParser.REGEX_MAPPING.get(col)
                if not v:
                    raise ParserError(ParserError.INPUT_ERROR_CODE, "专业招生信息内容实体名称<{}>不能识别".format(col))
                # 文理规则为可有可无
                if col == EnrollRegexParser.WENLI_HEADER:
                    self.major_regex += "[^文理]*" + v + "?"
                    self.major_regex_header.append(col)
                elif col in [EnrollRegexParser.SCH_ADDR_HEADER, EnrollRegexParser.LANGUAGE_HEADER]:
                    # 以防校址出现在专业行中，校址单独处理
                    pass
                else:
                    self.major_regex += v if not self.major_regex else v
                    self.major_regex_header.append(col)
            self.major_regex += EnrollRegexParser.OTHERS_REGEX
            # print(self.major_regex)
        elif self.major_column_names and type(self.major_column_names) != list:
            raise ParserError(ParserError.INPUT_ERROR_CODE, "专业招生信息内容实体名称必填并以','（英文逗号）隔开。")

    def is_sch_or_major_header(self, header):
        if header and (header in self.major_column_names + self.sch_column_names):
            return True
        return False

    def is_sch_row(self, content):
        if content and self.sch_regex:
            res = re.match(self.sch_regex, content)
            if res:
                return True, res.groups()
        return False, [None for i in range(len(self.sch_column_names) + 1)]

    def is_major_row(self, content):
        if content and self.major_regex:
            res = re.match(self.major_regex, content)
            if res:
                return True, res.groups()
        return False, (None for i in range(len(self.major_column_names) + 1))

    def is_wenli_row(self, content):
        wenli, enroll_count = None, None
        if content:
            wenli_res = re.match(self.WENLI_REGEX, content)
            if wenli_res and wenli_res.group(1):
                wenli = wenli_res.group(1)
                enroll_count_res = re.search(self.ENROLL_COUNT_REGEX, content)
                if enroll_count_res:
                    enroll_count = enroll_count_res.group(1)
                return True, wenli, enroll_count

        return False, wenli, enroll_count

    def is_sch_addr_row(self, content):
        sch_addr = None
        if content:
            # "(?:(?:地[址点])|(?:[学院]校所在地)|(?:校址))(?:[^\u4e00-\u9fa5]*)([\\S]+)"
            res = re.search(EnrollRegexParser.SCH_ADDR_REGEX, content)
            if res and res.group(1):
                sch_addr = res.group(1)
                return True, sch_addr
        return False, sch_addr

    @staticmethod
    def get_sch_addr(content):
        sch_addr = None
        if content:
            res = re.search(EnrollRegexParser.SCH_ADDR_REGEX, content)
            sch_addr = res.group(1) if res else sch_addr
        return sch_addr

    def is_language_row(self, content):
        language = None
        if content:
            res = re.search(self.LANGUAGE_REGEX, content)
            if res and res.group(1):
                language = res.group(1)
                return True, language
        return False, language

    @staticmethod
    def get_language(content):
        language = None
        if content:
            res = re.search(EnrollRegexParser.LANGUAGE_REGEX, content)
            language = res.group(1) if res else language
        return language

    @staticmethod
    def get_major_beizhu(content):
        major_beizhu = None
        if content:
            res = re.search(EnrollRegexParser.MAJOR_BEIZHU_REGEX, content)
            major_beizhu = res.group(1) if res else major_beizhu
        return major_beizhu

    @staticmethod
    def get_edu_system(content, province):
        """
        提取学制
        :param content: 行内容
        :param province:　省份，江西省出现学制解析错误
        :return: 学制
        """
        edu_system = None
        if content:
            res = re.search("(?:[^一二三四五六七八九十]*([一二三四五六七八九十]\\s*年))", content)
            if not res:
                if province == '江西':
                    res = re.search(r'(\d)年', content)
                else:
                    res = re.search(EnrollRegexParser.EDU_SYSTEM_REGEX, content)
            edu_system = res.group(1) if res else edu_system
        return edu_system

    def is_enroll_count_row(self, content):
        enroll_count = None
        if content:
            # res = re.match("(?:(?:计划)?招生)" + EnrollRegexParser.ENROLL_COUNT_REGEX, content)
            regex = EnrollRegexParser.ENROLL_COUNT_REGEX[0:-1] if EnrollRegexParser.ENROLL_COUNT_REGEX.endswith("?") else \
                    EnrollRegexParser.ENROLL_COUNT_REGEX
            res = re.search( regex, content)
            if res and res.group(1):
                enroll_count = res.group(1)
                return True, enroll_count
        return False, enroll_count

    def is_sch_fee(self, content):
        sch_fee = None
        res = re.search(self.SCH_FEE_REGEX, content)
        if res and res.group(1):
            sch_fee = res.group(1)
            return True, sch_fee
        return False, sch_fee

    def deal_sch_contents(self, sch_contents):
        sch_enroll_info = SchEnrollInfo()

        sch_header = [EnrollRegexParser.SCH_NAME_HEADER,
                      EnrollRegexParser.SCH_CODE_HEADER,
                      EnrollRegexParser.ENROLL_COUNT_HEADER,
                      EnrollRegexParser.WENLI_HEADER,
                      EnrollRegexParser.BATCH_HEADER]

        c = []
        for h in sch_header:
            if h in self.sch_regex_header:
                c.append(sch_contents[self.sch_regex_header.index(h)])
            else:
                c.append(None)

        sch_enroll_info.name = c[sch_header.index(EnrollRegexParser.SCH_NAME_HEADER)]
        sch_enroll_info.code = c[sch_header.index(EnrollRegexParser.SCH_CODE_HEADER)]
        sch_enroll_info.enroll_count = c[sch_header.index(EnrollRegexParser.ENROLL_COUNT_HEADER)]
        sch_enroll_info.wenli = c[sch_header.index(EnrollRegexParser.WENLI_HEADER)]
        sch_enroll_info.batch = c[sch_header.index(EnrollRegexParser.BATCH_HEADER)]
        # 未处理内容
        sch_enroll_info.note = sch_contents[-1] if sch_contents[-1] is not None else ""

        return sch_enroll_info


    def legal_sch_enroll_info(self, sch_enroll_info):
        """
        解析后的学校信息是否合法
        """
        # 存在学校代码，则学校代码非空
        if EnrollRegexParser.SCH_CODE_HEADER in self.sch_column_names and not sch_enroll_info.code:
            return False

        # 学校名称非空
        if not sch_enroll_info.name:
            return False

        return True

    def deal_major_contents(self, major_contents):
        major_enroll_info = MajorEnrollInfo()

        major_header = [EnrollRegexParser.SCH_CODE_HEADER,
                        EnrollRegexParser.SCH_NAME_HEADER,
                        EnrollRegexParser.MAJOR_NAME_HEADER,
                        EnrollRegexParser.MAJOR_BEIZHU_HEADER,
                        EnrollRegexParser.MAJOR_CODE_HEADER,
                        EnrollRegexParser.ENROLL_COUNT_HEADER,
                        EnrollRegexParser.EDU_SYSTEM_HEADER,
                        EnrollRegexParser.SCH_FEE_HEADER,
                        EnrollRegexParser.WENLI_HEADER,
                        EnrollRegexParser.BATCH_HEADER]
        c = []
        for h in major_header:
            if h in self.major_regex_header:
                c.append(major_contents[self.major_regex_header.index(h)])
            else:
                c.append(None)
        sch_code = c[major_header.index(EnrollRegexParser.SCH_CODE_HEADER)]
        sch_name = c[major_header.index(EnrollRegexParser.SCH_NAME_HEADER)]
        major_enroll_info.name = c[major_header.index(EnrollRegexParser.MAJOR_NAME_HEADER)]
        major_enroll_info.major_beizhu = c[major_header.index(EnrollRegexParser.MAJOR_BEIZHU_HEADER)]
        major_enroll_info.code = c[major_header.index(EnrollRegexParser.MAJOR_CODE_HEADER)]
        major_enroll_info.enroll_count = c[major_header.index(EnrollRegexParser.ENROLL_COUNT_HEADER)]
        major_enroll_info.edu_system = c[major_header.index(EnrollRegexParser.EDU_SYSTEM_HEADER)]
        major_enroll_info.sch_fee = c[major_header.index(EnrollRegexParser.SCH_FEE_HEADER)]
        major_enroll_info.wenli = c[major_header.index(EnrollRegexParser.WENLI_HEADER)]
        major_enroll_info.batch = c[major_header.index(EnrollRegexParser.BATCH_HEADER)]
        major_enroll_info.note = major_contents[-1] if major_contents[-1] is not None else ""
        return major_enroll_info, sch_code, sch_name


    def legal_major_enroll_info(self, major_enroll_info):
        """
        解析后的专业是否合法
        """
        # 存在专业代码，则专业代码非空
        if EnrollRegexParser.MAJOR_CODE_HEADER in self.major_column_names and not major_enroll_info.code:
            return False

        # 专业名称非空
        if not major_enroll_info.name:
            return False

        return True

    # 清洗内容
    def clear_content(self, content):
        tmp = content
        if content:
            tmp = content.replace("丨", "1").replace("〇", "0").replace("无/年", "元/年").replace("天/年", "元/年")
        return tmp.strip()

    def deal_content_rows(self):
        try:

            self.paging_content_rows()
            self.generate_regex()

            sch_enroll_info = SchEnrollInfo()
            for row_index in range(len(self.content_rows)):
                sch_enroll_info.enroll_year = self.enroll_year
                sch_enroll_info.province = self.province
                row = self.content_rows[row_index]
                for cel_index in range(len(row)):
                    row[cel_index] = row[cel_index].strip()

                if not "".join(row).strip():
                    continue

                content = self.clear_content(" ".join(row))

                if row_index == 40:
                    logger.debug(row_index)


                # 学校行
                is_sch, sch_contents = self.is_sch_row(content)
                if is_sch:
                    sch_tmp = self.deal_sch_contents(sch_contents)
                    if self.legal_sch_enroll_info(sch_tmp):
                        if (EnrollRegexParser.SCH_NAME_HEADER in self.sch_regex_header or \
                            EnrollRegexParser.SCH_CODE_HEADER in self.sch_regex_header) and \
                                sch_enroll_info.code == sch_tmp.code and sch_enroll_info.name and \
                                sch_enroll_info.name == sch_tmp.name and \
                                not sch_tmp.wenli and not sch_tmp.enroll_count and \
                                (not sch_enroll_info.sch_addr or sch_tmp.sch_addr) and \
                                (not sch_enroll_info.batch or sch_enroll_info.batch):
                            sch_enroll_info.copy_value(sch_tmp)
                        else:
                            if sch_enroll_info.name or sch_enroll_info.major_enroll_infos:
                                sch_enroll_info.add_sch_enroll_info(self.std_rows)
                                del sch_enroll_info

                            sch_enroll_info = sch_tmp

                        if not sch_enroll_info.sch_addr and EnrollRegexParser.SCH_ADDR_HEADER in self.sch_column_names:
                            sch_enroll_info.sch_addr = EnrollRegexParser.get_sch_addr(content)

                        # 4271湖南师范大学 湖南省长沙市岳麓区麓山路36号 8
                        # 这种情况需要 major_regex 不能识别出计划数， ENROLL_COUNT_REGEX 第一个\\D* 使后面的规则从'36号'开始匹配
                        if not sch_enroll_info.enroll_count and EnrollRegexParser.ENROLL_COUNT_HEADER in self.sch_column_names:
                            tmp_content = content.replace(sch_enroll_info.code, "", 1).replace(sch_enroll_info.name
                                                                                               , "", 1)
                            _, sch_enroll_info.enroll_count = self.is_enroll_count_row(tmp_content)
                        continue

                # 专业行
                is_major, major_contents = self.is_major_row(content)
                if is_major:
                    major_enroll_info, sch_code, sch_name = self.deal_major_contents(major_contents)
                    if self.legal_major_enroll_info(major_enroll_info):
                        if not major_enroll_info.language and self.LANGUAGE_HEADER in self.major_column_names:
                            major_enroll_info.language = EnrollRegexParser.get_language(content)
                        if not major_enroll_info.wenli and sch_enroll_info.wenli:
                            major_enroll_info.wenli = sch_enroll_info.wenli
                        if not major_enroll_info.batch and sch_enroll_info.batch:
                            major_enroll_info.batch = sch_enroll_info.batch
                        # 校址
                        if EnrollRegexParser.SCH_ADDR_HEADER in self.major_column_names:
                            major_enroll_info.sch_addr = EnrollRegexParser.get_sch_addr(content)

                        # 学制
                        if EnrollRegexParser.EDU_SYSTEM_HEADER in self.major_column_names and \
                                not major_enroll_info.edu_system:
                            major_enroll_info.edu_system = EnrollRegexParser.get_edu_system(content)
                        if not major_enroll_info.major_beizhu and major_enroll_info.name:
                            major_beizhu = EnrollRegexParser.get_major_beizhu(major_contents[1])
                            major_enroll_info.major_beizhu = major_beizhu
                            major_enroll_info.name = major_contents[1].strip(major_beizhu)
                            # major_enroll_info.major_beizhu = major_contents[1]
                            # major_enroll_info.sch_name
                        if not sch_enroll_info:
                            sch_enroll_info = SchEnrollInfo()

                        sch_enroll_info.major_enroll_infos.append(major_enroll_info)
                        continue
                # 文理 计划数
                is_sch_wenli, sch_wenli, enroll_count = self.is_wenli_row(content)
                if is_sch_wenli and sch_wenli and enroll_count is not None:
                    if sch_enroll_info and sch_enroll_info.name and len(sch_enroll_info.major_enroll_infos) > 0:
                        sch_enroll_info.add_sch_enroll_info(self.std_rows)
                        sch_enroll_info.major_enroll_infos = []
                    sch_enroll_info.wenli = sch_wenli
                    sch_enroll_info.enroll_count = enroll_count
                    continue


                deal_flag = False
                undeal_content = content

                # 计划数在某一行中
                is_enroll_count, enroll_count = self.is_enroll_count_row(content)
                if is_enroll_count :
                    if sch_enroll_info.enroll_count is None:
                        sch_enroll_info.enroll_count = enroll_count
                    elif sch_enroll_info.major_enroll_infos and sch_enroll_info.major_enroll_infos[-1].enroll_count is None:
                        sch_enroll_info.major_enroll_infos[-1].enroll_count = enroll_count
                    deal_flag = True

                # 学费独占一行
                is_sch_fee, sch_fee = self.is_sch_fee(content)

                if is_sch_fee and sch_fee and sch_enroll_info.major_enroll_infos and \
                        sch_enroll_info.major_enroll_infos[-1].name and \
                        not sch_enroll_info.major_enroll_infos[-1].sch_fee:
                    sch_enroll_info.major_enroll_infos[-1].sch_fee = sch_fee
                    deal_flag = True

                # 语种在某一行中
                is_language, language = self.is_language_row(content)
                if is_language and sch_enroll_info.major_enroll_infos and \
                        sch_enroll_info.major_enroll_infos[-1].name and \
                        not sch_enroll_info.major_enroll_infos[-1].language:
                    sch_enroll_info.major_enroll_infos[-1].language = language
                    undeal_content = undeal_content.replace(language, "", 1)
                    deal_flag = True

                # 校址在某一行中
                is_sch_addr, sch_addr = self.is_sch_addr_row(content)
                if is_sch_addr:
                    if not sch_enroll_info.sch_addr:
                        sch_enroll_info.sch_addr = sch_addr
                        undeal_content = undeal_content.replace(sch_addr, "", 1)

                    if sch_enroll_info.major_enroll_infos and sch_enroll_info.major_enroll_infos[-1].name and \
                            not sch_enroll_info.major_enroll_infos[-1].sch_addr:
                        sch_enroll_info.major_enroll_infos[-1].sch_addr = sch_addr
                    deal_flag = True

                # 中文数字学制
                if sch_enroll_info.major_enroll_infos and sch_enroll_info.major_enroll_infos[-1].name and \
                        sch_enroll_info.major_enroll_infos[-1].edu_system is None:
                    edu_system = EnrollRegexParser.get_edu_system(content, self.province)
                    if edu_system:
                        sch_enroll_info.major_enroll_infos[-1].edu_system = edu_system
                        deal_flag = True

                if deal_flag and not undeal_content:
                    continue

                if not sch_enroll_info:
                    sch_enroll_info = SchEnrollInfo()
                if not sch_enroll_info.major_enroll_infos:
                    sch_enroll_info.major_enroll_infos = [MajorEnrollInfo()]
                sch_enroll_info.major_enroll_infos[-1].note += "\n" + "行数" + str(row_index + 1) + " " + " ".join(row)

            if sch_enroll_info:
                sch_enroll_info.add_sch_enroll_info(self.std_rows)

            src_file = Path(self.file_path).name.split(".")[0]
            major_file = src_file + ".xls"
            output_path = Path(self.output_dir)
            if not output_path.exists():
                output_path.mkdir()
            writeXLSX(self.std_rows, str(output_path / major_file))
            return 0, "文件{0}处理成功".format(Path(self.file_path).name)
        except ParserError as e:
            logger.exception(e.message)
            return e.error_code, e.message
        except Exception as e:
            traceback.print_exc(e)
            logger.exception(e)
            return ParserError.RUNTIME_ERROR_CODE, "程序异常，处理文件{}".format(Path(self.file_path).name)
