#!/usr/bin/env python
# coding=utf-8

import os
import logging
from multiprocessing import Process

from enroll_score_ocr_parser.conf.setting import ENROLL_CONF_FILE
from enroll_score_ocr_parser.enroll.enroll_info_parser import EnrollInfoParser
from enroll_score_ocr_parser.enroll.enroll_regex_parser import EnrollRegexParser

from enroll_score_ocr_parser.util.configuration import Configuration

formatter = logging.Formatter('%(asctime)-15s %(levelname)s %(filename)s  %(funcName)s %(lineno)d %(message)s')
logger = logging.getLogger("enroll_score_ocr_parser")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


def run_task(file_path, output_dir, page_column_count, sch_column_names, major_column_names, queue):

    logger.info("start task: 解析文件：%s", file_path)
    if sch_column_names or major_column_names:
        enroll_regex_parser = EnrollRegexParser(file_path, output_dir, page_column_count, sch_column_names,
                                                major_column_names)
        parser_result = enroll_regex_parser.deal_content_rows()
    else:
        enroll_info_parser = EnrollInfoParser(file_path, output_dir, page_column_count)
        parser_result = enroll_info_parser.deal_content_rows()
    if queue:
        queue.put(parser_result)
    logger.info("finish task: 解析文件：%s", file_path)
    return parser_result


def main():
    conf = Configuration(ENROLL_CONF_FILE)
    for section, section_props in conf.get_props().items():
        effective = section_props.get("effective")
        input_dir = section_props.get("input-dir")
        output_dir = section_props.get("output-dir")

        page_column_count = section_props.get("page-column-count")

        sch_column_names = section_props.get("sch-column-names")
        if sch_column_names:
            sch_column_names = sch_column_names.split(",")
        else:
            sch_column_names = []
        major_column_names = section_props.get("major-column-names")
        if major_column_names:
            major_column_names = major_column_names.split(",")
        else:
            major_column_names = []

        if page_column_count.isdigit():
            page_column_count = int(page_column_count)
        else:
            page_column_count = None

        effective = False if effective.lower() == "false" else True

        if effective:
            processes = []

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for root, _, fns in os.walk(input_dir):
                for fn in fns:
                    if fn.startswith(".") or fn.startswith("~"):
                        continue
                    file_path = os.path.join(root, fn)
                    process = Process(target=run_task, args=(file_path, output_dir, page_column_count, sch_column_names,
                                                             major_column_names, None))
                    process.start()
                    processes.append(process)

            for p in processes:
                p.join()


if __name__ == '__main__':
    main()



