#!/usr/bin/env python
# coding=utf-8

import re
import xlrd


class ScoreInfo(object):
    """
    计划数, 录取人数, 最高分, 最低分
    """

    def __init__(self, score_info_parser):

        self.score_info_parser = score_info_parser

        self.province = None
        self.must_test_subjects = None
        self.select_test_subjects = None

        self.enroll_year = None
        # 计划数
        self.enroll_count = None
        # 录取数
        self.people_count = None
        self.max_score = None
        self.min_score = None

        self.parallel_volunteer = None
        self.seek_volunteer = None
        self.obey_volunteer = None

        self.avg_score = None
        self.min_score_diff = None
        self.enroll_min_rank = None
        self.avg_score_diff = None

        self.enroll_count_raw = None
        self.people_count_raw = None
        self.max_score_raw = None
        self.min_score_raw = None

        self.parallel_volunteer_raw = None
        self.seek_volunteer_raw = None
        self.obey_volunteer_raw = None

        self.subject_require = None

        self.batch = None
        self.wenli = None

        self.beizhu = None


        # 分数分布，目前定义为'分数段区间'，(分数段低分，分数段高分，分数段人数)
        self.score_interval_dis = []

    def deal_score_info(self, row, enroll_year):
        """
        处理对应年份的录取数据
        """

        header_index_map = self.score_info_parser.get_header_index_map(enroll_year)

        _, self.enroll_year = self.deal_score_info_num(self.score_info_parser.ENROLL_YEAR_HEADER, row, enroll_year)
        if not self.enroll_year:
            self.enroll_year = enroll_year

        self.enroll_count_raw, self.enroll_count = \
            self.deal_score_info_num(self.score_info_parser.ENROLL_COUNT_HEADER, row, enroll_year)
        self.people_count_raw, self.people_count = \
            self.deal_score_info_num(self.score_info_parser.PEOPLE_COUNT_HEADER, row, enroll_year)

        self.max_score_raw, self.max_score = \
            self.deal_score_info_num(self.score_info_parser.MAX_SCORE_HEADER, row, enroll_year)

        self.min_score_raw, self.min_score = \
            self.deal_score_info_num(self.score_info_parser.MIN_SCORE_HEADER, row, enroll_year)

        self.parallel_volunteer_raw, self.parallel_volunteer = \
            self.deal_score_info_num(self.score_info_parser.PARALLEL_VOLUNTEER_HEADER, row, enroll_year)
        self.seek_volunteer_raw, self.seek_volunteer = \
            self.deal_score_info_num(self.score_info_parser.SEEK_VOLUNTEER_HEADER, row, enroll_year)
        self.obey_volunteer_raw, self.obey_volunteer = \
            self.deal_score_info_num(self.score_info_parser.OBEY_VOLUNTEER_HEADER, row, enroll_year)

        _, self.avg_score = self.deal_score_info_num(self.score_info_parser.AVG_SCORE_HEADER, row, enroll_year)
        _, self.min_score_diff = self.deal_score_info_num(self.score_info_parser.MIN_SCORE_DIFF_HEADER, row, enroll_year)
        _, self.enroll_min_rank = self.deal_score_info_num(self.score_info_parser.ENROLL_MIN_RANK_HEADER, row, enroll_year)
        _, self.avg_score_diff = self.deal_score_info_num(self.score_info_parser.AVG_SCORE_DIFF_HEADER, row, enroll_year)

        self.subject_require = self.score_info_parser.get_col_by_header_name(self.score_info_parser.SUBJECT_REQUIRE_HEADER,
                                                                             row, header_index_map)

        self.beizhu = self.score_info_parser.get_col_by_header_name(self.score_info_parser.NOTE_HEADER, row,
                                                                    header_index_map)

        batch_raw = self.score_info_parser.get_col_by_header_name(self.score_info_parser.BATCH_HEADER, row,
                                                                  header_index_map)
        self.batch = batch_raw if batch_raw and not self.batch else self.batch

        wenli_raw = self.score_info_parser.get_col_by_header_name(self.score_info_parser.WENLI_HEADER, row,
                                                                  header_index_map)
        self.wenli = wenli_raw if not self.wenli and wenli_raw else self.wenli


        # 录取分数分布
        score_interval_raw = self.score_info_parser.get_col_by_header_name(self.score_info_parser.PEOPLE_COUNT_DIS_HEADER,
                                                                            row, header_index_map)
        if score_interval_raw:
            intervals = score_interval_raw.split(";")
            for item in intervals:
                score, count = '', ''
                if not re.match("([1-9]\\d{2}:\\d+)", item):
                    try:
                        float(item)
                    except:
                        continue
                    t = xlrd.xldate_as_datetime(float(item), 0)
                    score = str((t.month - 1) * 31 + t.day * 24 + t.hour)
                    count = str(t.minute)
                else:
                    tmp = item.split(":")
                    score = tmp[0]
                    count = tmp[1] if len(tmp) > 1 else ''
                    count_res = re.search("[1-9]\\d*", count)
                    count = count_res.group(0) if count_res else count
                self.score_interval_dis.append((score, '', count))

        # ## 2016天津特殊处理
        # max_score_res = re.search("(?<=高分：)[1-9][\\d]*", self.max_score_raw)
        # self.max_score = max_score_res.group(0) if max_score_res else self.max_score
        #
        # avg_score_res = re.search("(?<=平均分：)[1-9][\\d]*", self.max_score_raw)
        # self.avg_score = avg_score_res.group(0) if avg_score_res else self.avg_score
        #
        # min_score_res = re.search("(?<=低分：)[1-9][\\d]*", self.max_score_raw)
        # self.min_score = min_score_res.group(0) if min_score_res else self.min_score

    def deal_score_info_num(self, col_name, row, enroll_year):
        """
        数字列提取数字
        """
        raw = self.score_info_parser.get_col_by_header_name(col_name, row, self.score_info_parser.get_header_index_map(enroll_year))
        res = re.search(self.score_info_parser.SCORE_REGEX, raw.strip())
        num = res.group(0) if res else ''
        return raw, num

    def legal_score_info(self):
        """
        合法的分数信息, 至少有一个数字列可以识别出数字
        """
        if self.enroll_count or self.people_count or self.max_score or self.min_score or self.parallel_volunteer or \
                self.obey_volunteer or self.seek_volunteer or self.avg_score or self.min_score_diff or \
                self.enroll_min_rank or self.avg_score_diff:
            return True
        return False


    def deal_jiangsu_sch_name(self, name_raw):

        beizhu = re.findall(r'以下[\s\S]+', name_raw)
        if beizhu:
            beizhu = beizhu[0]
            name_dealed = name_raw.split(beizhu)[0].strip()
        else:
            beizhu = ''
            name_dealed = name_raw

        select_subject_level = re.findall(r'..科目等级.*', name_dealed)
        if select_subject_level:
            select_subject_level = select_subject_level[0]
            name_dealed = name_dealed.split(select_subject_level)[0].strip()
        else:
            select_subject_level = ''
            name_dealed = name_raw
        return beizhu, select_subject_level, name_dealed

    def deal_jiangsu_require_subjects(self, require_subjects):
        must_test_subject = re.search(r'必测科目等级要求:([\s\S]+)', require_subjects)
        select_test_subject = re.search(r'选测科目等级要求:([\s\S]+)(\s+|必测)', require_subjects)
        if must_test_subject:
            must_test_subject = must_test_subject.group(1).strip()
        else:
            must_test_subject = ''
        if select_test_subject:
            select_test_subject = select_test_subject.group(1).strip()
        else:
            select_test_subject = ''
        return must_test_subject, select_test_subject



class SchScoreInfo(ScoreInfo):
    """
    学校录取
    """

    def __init__(self, score_info_parser):

        super(SchScoreInfo, self).__init__(score_info_parser)

        self.sch_name = None
        self.sch_code = None
        self.sch_full_name = None
        self.sch_addr = None

        self.major_score_infos = []

    def deal_sch_info_row(self, row, enroll_year):
        self.deal_score_info(row, enroll_year)
        header_index_map = self.score_info_parser.get_header_index_map(enroll_year)

        sch_full_name_raw = self.score_info_parser.get_col_by_header_name(
            self.score_info_parser.SCHOOL_FULL_NAME_HEADER, row, header_index_map)

        if sch_full_name_raw:
            self.sch_full_name = sch_full_name_raw.strip().split(" ")[0]

        self.sch_code = self.score_info_parser.get_col_by_header_name(self.score_info_parser.CODE_HEADER, row,
                                                                      header_index_map)
        self.sch_name = self.score_info_parser.get_col_by_header_name(self.score_info_parser.NAME_HEADER, row,
                                                                      header_index_map)

        major_group_code = self.score_info_parser.get_col_by_header_name(self.score_info_parser.MAJOR_GROUP_CODE_HEADER,
                                                                         row, header_index_map)

        # 从专业组代码或者学校名称中获取学校代码
        if not self.sch_code:
            if major_group_code:
                self.sch_code = major_group_code
            else:
                code_res = re.search("((?:^[a-zA-Z\\d]+)|(?:[a-zA-Z\\d]+$))", self.sch_name)
                self.sch_code = code_res.group(0) if code_res and not self.sch_code else self.sch_code
                self.sch_name = re.sub(self.sch_code,  "", self.sch_name, 1)

        # 学校名称位于计划数中
        if not self.score_info_parser.name_matcher.is_sch_name(self.sch_name) and \
                self.score_info_parser.name_matcher.is_sch_name(self.enroll_count_raw):
            self.sch_name = self.enroll_count_raw

        sch_addr_raw = self.score_info_parser.get_col_by_header_name(self.score_info_parser.SCH_ADDR_HEADER, row,
                                                                      header_index_map)
        self.sch_addr = sch_addr_raw if not self.sch_addr and sch_addr_raw else self.sch_addr

        # 在一整行中获取院校名称
        content = " ".join(row)
        if self.sch_name.isdigit():
            self.sch_name = None
        if not self.sch_name:
            res = re.search("[\\s]*([\\D]+(?:大学|学院|校区|分校)?[\u4e00-\u9fa5]*)\\D*([1-9]\\d{,2}(?=[人名])?)?", content)
            self.sch_name = res.group(1) if res else self.sch_name
            # 在一整行中获取计划数
            if not self.enroll_count and res:
                self.enroll_count = res.group(2) if res else self.enroll_count
        # 修复学校代码
        if self.sch_code:
            res = re.search("((?:^[a-zA-Z\\d]+)|(?:[a-zA-Z\\d]+$))", self.sch_code)
            self.sch_code = res.group(1) if res else self.sch_code

    def convent_to_array(self):
        """
        学校下专业录取数据转学校录取数据sch_scores和专业录取数据major_scores
        """
        sch_scores = []
        major_scores = []
        # if self.legal_score_info():

        if not self.score_interval_dis:
            self.score_interval_dis = [("", "", "")]
        for sch_score_interval in self.score_interval_dis:
            sch_scores.append([
                self.enroll_year,
                self.province,
                self.sch_name,
                self.sch_code,
                self.enroll_count,
                self.people_count,
                self.max_score,
                self.min_score,
                self.parallel_volunteer,
                self.seek_volunteer,
                self.obey_volunteer,

                self.avg_score,
                self.min_score_diff,
                self.enroll_min_rank,
                self.avg_score_diff,
                self.sch_full_name,
                self.select_test_subjects,
                self.must_test_subjects,
                self.subject_require,
                self.batch,
                self.wenli,
                sch_score_interval[0],
                sch_score_interval[1],
                sch_score_interval[2],
                self.sch_addr,
                self.beizhu
            ])
        for m in self.major_score_infos:
            if not m.score_interval_dis:
                m.score_interval_dis = [("", "", "")]
            for major_score_interval in m.score_interval_dis:
                major_scores.append([
                    self.enroll_year,
                    self.province,
                    self.sch_name,
                    self.sch_code,
                    m.select_test_subjects,
                    m.must_test_subjects,

                    self.enroll_count,
                    m.major_name,
                    m.major_beizhu,

                    m.major_code,
                    m.enroll_count,
                    m.people_count,
                    m.max_score,
                    m.min_score,
                    m.parallel_volunteer,
                    m.seek_volunteer,
                    m.obey_volunteer,
                    m.avg_score,
                    m.min_score_diff,
                    m.enroll_min_rank,
                    m.avg_score_diff,
                    self.subject_require,
                    m.edu_system,
                    self.sch_full_name,

                    m.batch if m.batch else self.batch,
                    m.wenli if m.wenli else self.wenli,
                    major_score_interval[0],
                    major_score_interval[1],
                    major_score_interval[2],
                    m.sch_fee,
                    self.sch_addr,
                    m.language,
                    m.beizhu,
                    m.note
                ])
        return sch_scores, major_scores

    def legal_sch_info(self):
        """
        """
        if self.score_info_parser.get_header_index_map().get(self.score_info_parser.CODE_HEADER) is not None and \
                not self.sch_code:
            return False
        return True


class MajorScoreInfo(ScoreInfo):
    """
    专业录取
    """

    def __init__(self, score_info_parser):
        super(MajorScoreInfo, self).__init__(score_info_parser)
        self.major_name = None
        self.major_beizhu = None
        self.major_code = None
        self.select_subject_level = None
        self.edu_system = None
        self.sch_fee = None
        self.language = None


        # 未处理内容
        self.note = ""

    def deal_major_info_row(self, row, enroll_year):
        self.deal_score_info(row, enroll_year)
        header_index_map = self.score_info_parser.get_header_index_map(enroll_year)
        self.major_name = self.score_info_parser.get_col_by_header_name(self.score_info_parser.NAME_HEADER, row, header_index_map)
        self.major_code = self.score_info_parser.get_col_by_header_name(self.score_info_parser.CODE_HEADER, row, header_index_map)

        self.edu_system = self.score_info_parser.get_col_by_header_name(self.score_info_parser.EDU_SYSTEM_HEADER, row, header_index_map)
        self.sch_fee = self.score_info_parser.get_col_by_header_name(self.score_info_parser.SCH_FEE_HEADER, row, header_index_map)
        self.language = self.score_info_parser.get_col_by_header_name(self.score_info_parser.LANGUAGE_HEADER, row, header_index_map)

        # 从专业组代码或者学校名称中获取学校代码
        if not self.major_code:
            code_res = re.search("((?:^[a-zA-Z\\d]+)|(?:[a-zA-Z\\d]+$))", self.major_name)
            self.major_code = code_res.group(0) if code_res else self.major_code
            self.major_name = re.sub(self.major_code, "", self.major_name, 1)

        # 修复专业代码
        if self.major_code:
            code_res = re.search("((?:^[a-zA-Z\\d]+)|(?:[a-zA-Z\\d]+$))", self.major_code)
            self.major_code = code_res.group(0) if code_res else self.major_code

    def deal_major_note_row(self, row):
        self.note = self.note + "\n" + " ".join(row) if self.note else " ".join(row)

    def legal_major_info(self):
        # 存在专业代码列，专业代码解析出来为空
        if self.score_info_parser.get_header_index_map().get(self.score_info_parser.CODE_HEADER) is not None and \
                not self.major_code:
            return False

        # # 只有专业名称的时候
        # if self.major_name and not self.enroll_count_raw and not self.people_count_raw and not self.max_score_raw and \
        #         not self.min_score_raw:
        #     return True
        return False

