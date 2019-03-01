#!/usr/bin/env python
# coding=utf-8


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class ParserError(Error):
    """Exception raised for errors in the input.

    Attributes:
        error_code -- 错误码
        message -- explanation of the error
    """
    INPUT_ERROR_CODE = 1  # 用户输入异常
    RUNTIME_ERROR_CODE = 2  # 程序处理异常

    def __init__(self, error_code, message):
        self.error_code = error_code
        self.message = message
