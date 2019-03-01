#!/usr/bin/env python
# coding=utf-8

import logging
from pathlib import Path
from multiprocessing import Process
from enroll_score_ocr_parser.conf.setting import SCORE_CONF_FILE
from enroll_score_ocr_parser.score.score_info_parser import ScoreInfoParser
from enroll_score_ocr_parser.util.configuration import Configuration

formatter = logging.Formatter('%(asctime)-15s %(levelname)s %(filename)s  %(funcName)s %(lineno)d %(message)s')
logger = logging.getLogger("enroll_score_ocr_parser")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


def run_task(file_path, output_dir, page_column_count, queue, enroll_years=[]):

    logger.info("start task：解析文件%s, 年份参数%s", file_path, ",".join(enroll_years))
    score_info_parser = ScoreInfoParser(file_path, output_dir, page_column_count, enroll_years)
    score_info_parser.only_sch_name = True
    deal_result = score_info_parser.deal_content_info()
    if queue:
        queue.put(deal_result)
    logger.info("finish task: 解析文件%s, 年份参数%s", file_path, ",".join(enroll_years))


def main():
    conf = Configuration(SCORE_CONF_FILE)
    for section, section_props in conf.get_props().items():
        effective = section_props.get("effective")
        excel_dir = section_props.get("input-dir")
        enroll_years = section_props.get("enroll-years")
        output_dir = section_props.get("output-dir")
        page_column_count = section_props.get("page-column-count")

        enroll_years = enroll_years.split(u",")
        file_paths = []
        effective = False if effective.lower() == "false" else True

        output_path = Path(output_dir)
        if not output_path.exists():
            output_path.mkdir()
        if page_column_count.isdigit():
            page_column_count = int(page_column_count)
        else:
            page_column_count = None
        if effective:
            input_dir = Path(excel_dir)

            if input_dir.exists():
                if input_dir.is_dir():
                    input_paths = input_dir.iterdir()
                    for file_path in input_paths:
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            file_paths.append(file_path)
                elif input_dir.is_file() and not input_dir.name.startswith("."):
                    file_paths.append(input_dir)
        processes = []
        for file_path in file_paths:
            process = Process(target=run_task, args=(file_path, output_dir, page_column_count, None, enroll_years))
            processes.append(process)
            process.start()
        for process in processes:
            process.join()

if __name__ == '__main__':
    main()

