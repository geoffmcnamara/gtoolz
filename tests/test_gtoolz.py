#!/usr/bin/env python3
"""
purpose: to run quick demos (aka tests) on selected gtoolz functions or features
options: none
returns: nothing
notes: this is a continual work in progress (WIP)
author: geoff.mcnamara@gmail.com
date: 20230220
"""

# import pytest
import types
# from inspect import getmembers, isfunction
import inspect
# from my_project import my_module
from gtoolz import dbug, printit, gclr, askYN, get_columns
import gtoolz
from gtoolz import *

dir_l = dir(gtoolz)
# dbug(dir_l, 'ask')

demos_l = [item for item in dir_l if "_demo" in item]
scr_cols = int(get_columns() * .8)
ans = gselect(demos_l, width=scr_cols, centered=True)
globals()[ans]()

if ans == "all":
    for func in dir_l:
        if '_demo' in str(func):
            dbug(f"Testing: function: {func}()...")
            globals()[func]()
            # eval_this = f"{func}()"
            # eval(eval_this)

# 
# functions_list = inspect.getmembers(gtoolz, inspect.isfunction)
# dbug(functions_list)
# 
# 
# print([getattr(gtoolz, a) for a in dir(gtoolz)
#   if isinstance(getattr(gtoolz, a), types.FunctionType)])
# 
# # import ast
# # source = open(<filepath_to_parse>).read()
# # functions = [f.name for f in ast.parse(source).body
#              # if isinstance(f, ast.FunctionDef)]
# 
# 
# dbug()
# 
# 
# def test_print(capsys):
#     print("test string")
#     captured = capsys.readouterr()
#     assert captured.out == "test string\n"
# 
# # def test_printit(capsys):
# #     printit("msg", 'boxed')
# #     out = capsys.readouterr()
# #     assert out.out == '''
# #      ┌─────┐
# #      │ msg │
# #      └─────┘'''
# 
# def test_gclr(capsys):
#    red =  gclr("red", txt="red")
#    print(red)
# 
# 
# print(dir(__file__))
