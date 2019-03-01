#!/usr/bin/env python
# coding=utf-8

import sys
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/score/")
sys.path.append("/home/jiangyy/workspace/enroll-score-ocr-parser/enroll/")
# # sys.path.append(sys.path[0]+"/../")
# # sys.path.append(sys.path[0]+"/../../")
# # sys.path.append(sys.path[0]+"/../../../")
import logging
from pathlib import Path
from multiprocessing import Process, Queue

from score.score_info_parser import ScoreInfoParser
from enroll.enroll_info_parser import EnrollInfoParser
from enroll.enroll_regex_parser import EnrollRegexParser


formatter = logging.Formatter('%(asctime)-15s %(levelname)s %(filename)s  %(funcName)s %(lineno)d %(message)s')
root_logger = logging.getLogger("enroll_score_ocr_parser")
root_logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
root_logger.addHandler(ch)


def score_task(file_path, output_dir, page_column_count, queue, enroll_years=[], province=''):

    root_logger.info("start task：解析文件%s, 年份参数%s", file_path, ",".join(enroll_years))
    score_info_parser = ScoreInfoParser(file_path, output_dir, page_column_count, enroll_years, province)
    score_info_parser.only_sch_name = False
    deal_result = score_info_parser.deal_content_info()
    if queue:
        queue.put(deal_result)
    root_logger.info("finish task: 解析文件%s, 年份参数%s", file_path, ",".join(enroll_years))


def enroll_task(file_path, output_dir, page_column_count, enroll_year, queue, sch_column_names, major_column_names, province):

    root_logger.info("start task: 解析文件：%s", file_path)
    parser_result = ""
    if sch_column_names or major_column_names:
        enroll_regex_parser = EnrollRegexParser(file_path, output_dir, page_column_count, enroll_year, sch_column_names,
                                                major_column_names, province)
        parser_result = enroll_regex_parser.deal_content_rows()
    else:
        enroll_info_parser = EnrollInfoParser(file_path, output_dir, enroll_year, page_column_count, province)
        parser_result = enroll_info_parser.deal_content_rows()
    if queue:
        queue.put(parser_result)
    root_logger.info("finish task: 解析文件：%s", file_path)
    return parser_result


def list_files(input_dir):
    file_paths = []
    input_path = Path(input_dir)
    if input_path.exists():
        if input_path.is_dir():
            input_paths = input_path.iterdir()
            for p in input_paths:
                file_name = p.name
                if not file_name.startswith("."):
                    file_paths.append(str(p))
        else:
            file_paths.append(str(input_path))
    return file_paths


def set_log_file_handler(output_dir):
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir()
    file_handler = logging.FileHandler(str( output_path / Path("enroll_score_ocr_parser.log")))
    file_handler.setFormatter(formatter)
    logger = logging.getLogger("enroll_score_ocr_parser")
    logger.addHandler(file_handler)


def enroll_parser(input_dir, output_dir, page_column_count, enroll_year, sch_column_names, major_column_names, province):
    """
    当院校、专业招生计划内容都在一列时使用
    :param input_dir: 输入文件目录
    :param output_dir: 输出文件目录
    :param page_column_count: 单个院校、专业列数
    :param enroll_year: 招生年份
    :param sch_column_names: 院校招生信息内容实体名称列表，如 ["院校代码","院校名称","计划数","校址","批次"]"
    :param major_column_names: 专业招生信息内容实体名称列表，如 ["专业代码","专业名称","计划数","文理","学制","学费"]
    :param province: 省份
    :return:
    """
    set_log_file_handler(output_dir)
    file_paths = list_files(input_dir)
    processes = []
    queue = Queue()
    for enroll_file in file_paths:
        process = Process(target=enroll_task, args=(enroll_file, output_dir, page_column_count, enroll_year, queue, sch_column_names, major_column_names, province))
        processes.append(process)
        process.start()

    for p in processes:
        p.join()

    feedback_msg = []
    while not queue.empty():
        feedback_msg.append(queue.get())
    return feedback_msg


def score_parser(input_dir, output_dir, page_column_count, enroll_years=[], province=''):
    """
    院校、专业招生计划或者录取分数内容比较规则时使用，每个实体（名称，代码，计划数，录取数等）被分割到不同的单元格中。
    :param input_dir:
    :param output_dir:
    :param page_column_count:
    :param enroll_years: 年份列表
    :param province: 省份
    :return:
    """
    set_log_file_handler(output_dir)
    score_files = list_files(input_dir)
    processes = []
    queue = Queue()
    for score_file in score_files:
        process = Process(target=score_task, args=(score_file, output_dir, page_column_count, queue, enroll_years, province))
        processes.append(process)
        process.start()
    for p in processes:
        p.join()

    feedback_msg = []
    while not queue.empty():
        feedback_msg.append(queue.get())
    return feedback_msg


# if __name__ == '__main__':
#     msg = enroll_parser("/home/janze/PycharmProjects/OCR文件/17浙江招生",
#                   "/home/janze/PycharmProjects/OCR-format/17浙江招生",
#                   6)
#     # msg = score_parser("/home/janze/PycharmProjects/OCR文件/2016上海录取",
#     #                    "/home/janze/PycharmProjects/OCR-format/2016上海录取",
#     #                    None,
#     #                    ['2013', '2014', '2015'])
#     for i in msg:
#         print(i)

#--------------------------------------------------------------
if __name__ == '__main__':
    # msg = score_parser("/home/jiangyy/文档/ocr格式化/v1.0/江苏/2018江苏招生专科-输入_cp.xlsx",
    #                    "/home/jiangyy/文档/ocr格式化/2018江苏招生专科-format.xlsx",
    #                    None,
    #                    enroll_years=['2018'],
    #                    province='江苏')


    msg = enroll_parser("/home/jiangyy/文档/ocr格式化/v1.0/ocr格式化范例（2017江西招生）.xlsx",
                  "/home/jiangyy/文档/ocr格式化/v1.0/江西招生（2017）_输出.xlsx",
                page_column_count=1,
                enroll_year = '2017',
                  sch_column_names = ['院校代码', '院校名称', '计划数', '校址'],
                  major_column_names = ['专业代码', '专业名称', '计划数', '学费'],
                  province='江西')

    # msg = enroll_parser("/home/jiangyy/文档/ocr格式化/云南招生2017.xlsx",
    #               "/home/jiangyy/文档/ocr格式化/云南招生（2017）_输出.xlsx",
    #             page_column_count=1,
    #             enroll_year = '2017',
    #               sch_column_names = ['院校代码', '院校名称', '计划数'],
    #               major_column_names = ['专业代码', '专业名称', '学费', '计划数', '学制'],
    #               province='云南')

    for i in msg:
        print(i)