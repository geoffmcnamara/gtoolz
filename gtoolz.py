#!/usr/bin/env python3
# vim: set syntax=none nospell:
# ruff: noqa: E501, E731
# #####################
# Script name: gtoolz.py
# Created by: geoff.mcnamara@gmail.com
# Created on: 2018
# Purpose: this is a quick-n-dirty set of tools that might be useful
# ... much room for improvment and lots of danger points - not recommended for anything you care about  # noqa
# ... use this file in anyway and all your data could be at risk ;)
# ... lots of debugging code still remains and legacy code that should be removed  # noqa
# ... this file is constantly changing so nothing should depend on it ;)
# ... depends on python3!
# Notes:
#   I do a lot of financial analysis. These tools were designed to help me view financial data easily.
#   I love pandas until it comes to the index and data handling - truthfully, I get lost. So I have build
#   pretty much everything around a "list of lists" or rather, rows of columns. I can visualize and manipulate
#   a list-of-lists with relative ease. THe function that converts data to an lol (or other primary formats) is cleverly
#   called cnvrt() and is the heart of these tools. However, typically the goal is to produce a table that can be displayed
#   in various layouts so the most called for function is gtable(). This function, gtable(), uses cnvrt so you can pass almost
#   any type of data to it and it will display a decent readable table for the user. There are a myraid other functions but many of them
#   are in support of gtable or helping me develope code (the function dbug() or called_from() is liberally peppered into everything).
#   If you are looking for speed, efficiency, and stability then you are in the wrong place.
# LICENSE = MIT
# WARNING: Use at your own risk!
#          Side effects include but not limited to: severe nosebleeds and complete loss of data.
#          This file is subject to frequent change!
# Please contact me anytime. I willingly accept compliments and I tolerate complaints (most of the time).
# Requires: docopt, and others
# #####################################
# To see an overview:
# python3 -m pydoc nicetools
# #####################################
# to have access:
# in bash --- export PYTHONPATH="${PYTHONPATH}:~/dev/python/gmodules"
# or add this to your code
# import sys
# sys.path.append("~/dev/python/gmodules")  # or wherever you 
# #####################################

# ### IMPORTS ### #
import os
import sys
import shutil
import glob
import re
import subprocess
from datetime import datetime  # , date
# from math import ceil
import math
# from urllib.request import urlopen
import inspect
from inspect import getframeinfo, currentframe
from docopt import docopt
import time
# import requests
import threading
# import configparser
import itertools
# import pandas as pd
# import sqlite3
import functools  # used by func_call() wrapper
import ast


# ### DUNDERS ### #
__version__ = '0.1.6a0 ' + __file__  # VERSION

# ### GLOBALS ### #
dtime = datetime.now().strftime("%Y%m%d-%H%M")
FULL_PATH_SCRIPT = __file__
SCRIPT = os.path.basename(__file__)
styles_d = {'normal': '0', 'bold': '1', 'bright': 1, 'dim': '2', 'italic': '3', 'underline': '4', 'blink': '5', 'fast_blink': '6', 'reverse': '7', 'crossed_out': '9'}
fg_colors_d = {'black': "30",
        'red': "31",
        'green': "32",  # I don't like "their" green, should be "my" green (;38) instead or even better is rgb(0,215,0)
        'yellow': '33',
        'blue': '34',
        'magenta': '35',
        'cyan': '36',
        'white': '37',
        'normal': '38',
        'bold normal': '39',
        }
        # 'red!' : 'rgb(255,0,0)'}
bg_colors_d = {'black': "40",
        'red': "41",
        'green': "42",
        'yellow': "43",
        "blue": "44",
        'magenta': "45",
        "cyan": "46",
        'white': "47",
        'normal': '48',
        'normal1': '49'}

PRFX = "\x1b["
RESET = PRFX + "0m"
# BLACK = PRFX + '38;2;199;0;0m'

FUNC_CALLS = []

# ############### #
# ### CLASSES ### #
# ############### #

# ############
class Tracker:
    # ########
    """
    purpose: Tracks calls to "wrapped" functions and records func.__name__ args(truncated) kwargs(truncated) elapsed time taken as duration
    requires:
        - Wrap each function that you want to track with @Tracker
        - Where desired you call Tracker.dump() to printout all the recorded func calls 
             - once it is off Tracker does no recording from that point on
             - consider if you also want to comment out any Tracker.dump() calls
        - You can turn off Tracker using Tracker.kill() This effectively tells any Tracker call to just return and perform no actions (makes it easy to just ignore @Tracker wrappers
    options:
        - Tracker.kill(): bool=False  # (toggle) turns off Tracker 
        - Tracker.prnt(): bool=False  # (toggle) if you run Tracker.prnt() it toggles printing Tracker history as it goes
    returns:
    notes:
        - WIP
        - 20260106-0656
    """
    _func_calls = []
    _my_kill = False
    _prnt = False
    def __init__(self, func):
        # Store the function for later use
        self.func = func
        self.count = 0
        self.func_calls = []
        # self.called_from = called_from('v')
        functools.update_wrapper(self, func)
    def __call__(self, *args, **kwargs):
        # Increment state
        start_time = time.perf_counter()
        self.count += 1
        # dbug(f"Tracker: {self.func.__name__=} {args=} {kwargs=}")
        # dbug(inspect.stack())
        caller_frame = inspect.stack()[1]
        # dbug(caller_frame)
        # caller_locals = caller_frame.f_locals()
        # dbug(caller_locals)
        caller_file = os.path.basename(caller_frame.filename)
        caller_func = caller_frame.function
        caller_lineno = caller_frame.lineno
        if caller_func in [None, '', '?', '<module>']:
            # orig_caller_func = caller_func
            caller_file = os.path.basename(inspect.stack()[1][1])
            caller_func = inspect.stack()[1][3]
            caller_lineno = inspect.stack()[1][2]
            # dbug(f"{orig_caller_func=} {caller_func=}")
        if caller_func == "__call__":
            caller_func = "Tracker.__call__"
        call_info = {
            'name': self.func.__name__,
            'caller_file': caller_file,
            'caller_func': caller_func,
            'caller_lineno': caller_lineno,
            'args': str(args).replace("\n", ""),
            'kwargs': str(kwargs).replace("\n", ""),
            'count': self.count,
            }
        if self._prnt and not self._my_kill:
            # printit(inspect.stack(), 'boxed', title="Tracker", footer=dbug('here'), box_clr='red!')
            printit(f"[red!]Tracker[/]: called_from: [{caller_file}:[yellow!]{caller_func}:{caller_lineno}[/]] args:{str(call_info['args']):.30}...kwargs: {str(call_info['kwargs']):.40}...[red]starting[/]...")
        if self._my_kill:
            # dbug(self._my_kill)
            result = self.func(*args, **kwargs)  # <-- run the func
            return result
        end_time = time.perf_counter()
        duration = end_time - start_time
        result = self.func(*args, **kwargs)  # <-- run the func
        if self._prnt:
            printit(f"[red!]Tracker[/]: called_from: [{caller_file}:[yellow!]{caller_func}:{caller_lineno}[/]] [red]Result:[/] [cyan]{str(result):.100}[/]... elapsed: [yellow!]{duration:6f}[/]")
        if self._my_kill:
            Tracker._func_calls.append(call_info)
        call_info['result'] = f"{str(result):.10}..."
        return result
    @classmethod
    def kill(cls):
        if cls._my_kill:
            cls._my_kill = False
        else:
            cls._my_kill = True
    @classmethod
    def prnt(cls):
        # dbug(cls.prnt)
        if cls._prnt:
            cls._prnt = False
        else:
            cls._prnt = True
        # dbug(cls.prnt)
    @classmethod
    def dump(cls):
        if not cls._func_calls:
             dbug("No calls recorded...")
        else:
            # printit(cls._func_calls,'boxed', title=f"Tracker {called_from('v')}", footer="Tracker: "+dbug('here'), box_clr='red!') 
            lines = []
            for num, call in enumerate(cls._func_calls, 1):
                args_str = f"{str(call['args']):.20}...".replace("/n"," ")
                kwargs_str = f"{str(call['kwargs']):.20}...".replace("/n"," ")
                duration_str = f"{call['duration']:.6f}"
                # box = boxed(f"{i}.) {call['name']}({str(call['args']):20},{str(call['kwargs']):20})...", title=f"Tracker: {i}. {call['name']}() {duration_str}", footer=dbug('here'))
                line = f"{num:3} [red!]Tracker:[/] [yellow!]{call['name']:25}[/] Called_from:[[yellow!]{call['caller_file']}:{call['caller_func']}:{call['caller_lineno']}[/]] {args_str=} {kwargs_str=} return: {call['result']} duration: [yellow!]{duration_str}[/] <---"
                lines.append(line)
            printit(lines, 'boxed', 'prnt', title="[red!]Tracker[/] func_calls", footer="Tracker "+dbug('here'), box_clr='red!')
    # ### EOB class Tracker: ###  ### ##


# ############
class Spinner:
    # ########
    """
    purpose: prints a spinner in place
    input: msg="": str style='bar': ellipsis, pipe, box, vbar, growing_bar, missing_box, solid_box,  arrow, clock, bar, balloons, moon, dot, braille, pulse
        prog|progressive|progress: bool
        color: str|list
        txt_color: str
        elspsed: bool
    requires:
        import sys
        import threading
        import itertools
    return: None
    use:
        with Spinner("Working...", style='bar')
            long_proc()
        with Spinner("Doing long work...", style='vbar', progressive=True,  colors=shades('red'))
               for x in range(100):
                   time. sleep(1)
    """
    def __init__(self, message="", *args, delay=0.2, style="pipe", **kwargs):
        # """--== debugging ==--"""
        # dbug(f"class: Spinner {funcname()} style: {style} args: {args} kwargs: {kwargs}")
        # dbug(args)
        # dbug(kwargs)
        # """--== config ==--"""
        txt_color = arg_val(["text_color", "txt_color", "text_clr", "txt_clr"], args, kwargs, dflt="")
        self.color = arg_val(["color", 'spinner_clr', 'spinner_color', 'clr'], args, kwargs, dflt="")
        self.colors = arg_val(["colors", "clrs", "spinner_colrs", "spinner_clrs"], args, kwargs, dflt=[])
        txt_color = arg_val(["txt_color", 'txt_clr'], args, kwargs, dflt="")
        # self.TXT_COLOR = sub_color(txt_color)
        self.TXT_COLOR = gclr(txt_color)
        self.elapsed = arg_val(['elapsed', 'elapse', "time", "timed"], args, kwargs, dflt=False)
        # dbug(self.elapsed)
        time_color = arg_val(["time_color", 'time_clr', 'elapsed_clr', 'elapsed_time_clr', 'elapsed_color', 'elapse_color', 'elapse_clr'], args, kwargs, dflt=txt_color)
        # dbug(time_color)
        self.time_color = time_color
        # self.TIME_COLOR = sub_color(time_color)
        self.TIME_COLOR = gclr(time_color)
        # self.elapsed_time = 0
        self.etime = arg_val(["etime", "show_elapsed", 'elpased_time', 'elapsed', 'time'], args, kwargs, dflt=False)
        self.centered = arg_val(['center', 'centered'], args, kwargs, dflt=False)
        # self.RESET = sub_color('reset')
        self.RESET = gclr('reset')
        self.start_time = time.time()
        # dbug(self.etime)
        self.style = style = kvarg_val(["style", 'type'], kwargs, dflt=style)
        # dbug(self.style)
        self.prog = arg_val("prog", args, kwargs, dflt=True)
        self.style_len = kvarg_val(["length", "width"], kwargs, dflt=4)
        # """--== set default ==--"""
        # dbug(f"{self.colors=} {self.color=}")
        self.COLOR = gclr(self.color)
        if not self.color and isinstance(self.color, str):
            # dbug(f"hmmmm... {self.colors=} {self.color=}")
            self.color = self.colors
        if isinstance(self.colors, str):
            # just to make sure it is a list before going forward
            self.colors = [self.colors]
        # dbug(f"{self.colors=} {self.color=}")
        spinner_chrs = ['.', '.', '.', '.']  # the default will be ellipsis
        # self.prog = True  # the default
        # """--== SEP_LINE ==--"""
        if style in ('ellipsis', 'elipsis', 'elipses', 'ellipses'):  # for the spelling challenged like me
            spinner_chrs = ['.', '.', '.', '.']
            # spinner_chrs = ['.' * self.style_len]
            self.style_len = len(spinner_chrs)
            self.prog = True
            # dbug(f"Style: {self.style} prog: {self.prog} style_len: {self.style_len} color: {self.color} time_color: {self.time_color}")
        if style == "pipe":
            spinner_chrs = ['/', '-', '\\', '|']
            self.prog = False
        if style == "arrow":
            # spinner_chrs = ['⬍', '⬈', '⮕', '⬊', '⬍', '⬋', '⬅', '⬉']
            spinner_chrs = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]
            self.prog = False
        if style == 'clock':
            spinner_chrs = ['🕛', '🕧', '🕐', '🕜', '🕑', '🕝', '🕒', '🕞', '🕓', '🕟', '🕔', '🕠', '🕕', '🕡', '🕖', '🕢', '🕗', '🕣', '🕘', '🕤', '🕙', '🕥', '🕚', '🕦']
            self.style_len = len(spinner_chrs)
            self.prog = False
        if style == 'moon':
            spinner_chrs = ['🌑', '🌘', '🌗', '🌖', '🌕', '🌔', '🌓', '🌒']
            self.prog = False
        if style == 'vbar':
            spinner_chrs = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃', '▂', '▁']  # , '_']
            self.style_len = len(spinner_chrs)
        if style in ('growing_bar', 'pump'):
            spinner_chrs = ['\u258F', '\u258E', '\u258D', '\u258C', '\u258B', '\u258A', '\u2589', '\u2588', '\u2589', '\u258A', '\u258B', '\u258C', '\u258D', '\u258E', '\u258F', ' ']
            self.prog = False
        if style == 'bar':
            spinner_chrs = ['█', '█', '█', '█', '█']
            self.prog = True
            self.style_len = 20
        if style == 'braille':
            spinner_chrs = ['⣾', '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽']
            self.prog = False
        if style == 'dot':
            spinner_chrs = ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈']
            self.prog = False
        if style == 'box' or style == 'boxes':
            spinner_chrs = ['◰', '◳', '◲', '◱']
            self.prog = False
        if style == 'solid_box' or style == 'solid_boxes':
            spinner_chrs = ['\u2598', '\u259D', '\u2597', '\u2596']
            self.prog = False
        if style == 'missing_box' or style == 'hole_boxes':
            spinner_chrs = ['\u259F', '\u2599', '\u259B', '\u259C']
            self.prog = False
        if style == 'balloons':
            spinner_chrs = ['.', 'o', 'O', '@', '*']
            self.prog = False
        if style == 'pulse':
            spinner_chrs = ['.', 'o', 'O', 'o']
            self.prog = False
        if style == 'batball':
            spinner_chrs = ['q', 'p', 'b']
            self.prog = False
        # """--== SEP_LINE ==--"""
        if len(self.colors) > 4:  # arbitrary
            self.style_len = len(self.colors)
            # dbug(self.style_len)
        # dbug(self.style_len)
        # """--== SEP_LINE ==--"""
        # self.style_len = len(spinner_chrs)
        self.chr_cnt = 1
        self.clr_cnt = 0
        self.spinner = itertools.cycle(spinner_chrs)
        self.delay = kvarg_val("delay", kwargs, dflt=delay)
        self.busy = False
        self.spinner_visible = False
        message = printit(message, "str", 'noprnt', color=txt_color)
        # dbug(type(message))
        # dbug(message)
        if self.centered:
            add_shift = 0
            spinner_len = 1
            if self.prog:
                # spinner_len = len(escaped(spinner_chrs))
                spinner_len = parse_codes(spinner_chrs, 'nclen')
            if self.etime:
                add_shift = 2
            shift = -(spinner_len + add_shift)
            # dbug(f"{message=} {shift=}")
            message = printit(message, 'centered', prnt=False, rtrn_type="str", color=txt_color, shift=shift)
        sys.stdout.write(message)
    # """--== SEP_LINE ==--"""
    def write_next(self):
        # write the next chr in spinner_chrs
        with self._screen_lock:
            if not self.spinner_visible:
                # dbug(self.colors)
                if len(self.colors) > 1:
                    color = self.colors[self.clr_cnt]
                    # dbug(color)
                    # self.COLOR = sub_color(color)
                    self.COLOR = gclr(color)
                    # dbug(f"color: {color} chr_cnt: {self.clr_cnt} repr(self.COLOR): {repr(self.COLOR)}")
                    self.clr_cnt += 1
                    if self.clr_cnt > len(self.colors) - 1:
                        self.clr_cnt = 0
                spinner_chr = self.COLOR + str(next(self.spinner)) + self.RESET
                if self.style == 'clock':
                    if self.chr_cnt >= self.style_len:
                        self.chr_cnt = 0
                    else:
                        self.chr_cnt += 1
                if self.style == 'clock':
                    spinner_chr_len = parse_codes(spinner_chr, 'nclen')
                    # if nclen(spinner_chr) > 1:
                    if spinner_chr_len > 1:
                        # I have absolutely no idea why this is needed but it is. Believe me I beat this to death - it causes a 'blink'
                        # dbug(f"self.style: {self.style} self.chr_cnt: {self.chr_cnt} self.style_len: {self.style_len} spinner_chr: {spinner_chr} nclen(spinner_chr)) {nclen(spinner_chr)}")
                        sys.stdout.write('  ')
                    else:
                        # dbug(f"self.style: {self.style} self.chr_cnt: {self.chr_cnt} self.style_len: {self.style_len} spinner_chr: {spinner_chr} nclen(spinner_chr)) {nclen(spinner_chr)}")
                        sys.stdout.write(spinner_chr)
                else:
                    # dbug(f"self.style: {self.style} self.chr_cnt: {self.chr_cnt} self.style_len: {self.style_len} spinner_chr: {spinner_chr} nclen(spinner_chr)) {nclen(spinner_chr)}")
                    sys.stdout.write(spinner_chr)
                # sys.stdout.write(spinner_chr)
                self.spinner_visible = True
                sys.stdout.flush()
                # """--== SEP_LINE ==--"""
    def spin_backover(self, cleanup=False):
        with self._screen_lock:
            # _self_lock is the thread
            if self.spinner_visible:
                if not self.prog:
                    # backover chr if not prog (progressive)
                    # dbug(f"self.style: {self.style} self.chr_cnt: {self.chr_cnt} self.style_len: {self.style_len}")
                    sys.stdout.write('\b')
                else:
                    self.chr_cnt += 1
                    if self.chr_cnt > self.style_len-2:
                        # if we hit the len of style_len... print elapsed time... then...
                        if self.etime:
                            elapsed_time = round(time.time() - self.start_time, 2)
                            elapsed_time = f"{elapsed_time:>6}"  # if we go over 999 seconds we will be in trouble with the length
                            # dbug(elapsed_time)
                            sys.stdout.write(f" {self.TIME_COLOR}{elapsed_time}{self.RESET}")
                            # time.sleep(self.delay)
                            # sys.stdout.write("\b" * (len(escaped(str(elapsed_time))) + 1))
                            sys.stdout.write("\b" * (parse_codes(elapsed_time, 'nclen') + 1))
                            # sys.stdout.write(self.RESET)
                            sys.stdout.flush()
                        while self.chr_cnt > 1:
                            # while chr_cnt is more than 1... back over
                            self.chr_cnt -= 1
                            sys.stdout.write("\b")
                            sys.stdout.write(" ")
                            sys.stdout.write("\b")
                            time.sleep(self.delay)
                            sys.stdout.flush()
                        sys.stdout.write(" ")
                        sys.stdout.write("\b")
                        sys.stdout.flush()
                        time.sleep(self.delay)
                        # self.chr_cnt = 0
                if self.style in ('clock', 'moon'):
                    sys.stdout.write('\b')
                sys.stdout.write('\x1b[?25l')  # Hide cursor
                self.spinner_visible = False
                if cleanup:
                    sys.stdout.write(' ')              # overwrite spinner with blank
                    sys.stdout.write('\r')             # move to next line
                    sys.stdout.write("\x1b[?25h")      # Restore cursor
                sys.stdout.flush()
                # """--== SEP_LINE ==--"""
    def spin_proc(self):
        while self.busy:
            self.write_next()
            if self.etime and not self.prog:
                elapsed_time = round(time.time() - self.start_time, 2)
                elapsed_time = f"{elapsed_time:>6}"  # this is to assure proper back over length - if we go over 999 seconds we are in trouble with the length
                sys.stdout.write(f" {self.TIME_COLOR}{elapsed_time}{self.RESET}")
                # dbug(len(elapsed_time))
                # time.sleep(self.delay)
                # sys.stdout.write("\b" * (len(escaped(elapsed_time)) + 1))
                sys.stdout.write("\b" * (parse_codes(elapsed_time, 'nclen') + 1))
            time.sleep(self.delay)
            self.spin_backover()
            # """--== SEP_LINE ==--"""
    def __enter__(self):
        try:
            if sys.stdout.isatty():
                self._screen_lock = threading.Lock()
                self.busy = True
                self.thread = threading.Thread(target=self.spin_proc)
                self.thread.start()
        except Exception as Error:
            dbug(Error)
            pass
        # """--== SEP_LINE ==--"""
    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.busy = False
        if sys.stdout.isatty():
            self.spin_backover(cleanup=True)
            sys.stdout.write('\r')
            sys.stdout.flush()
            print()  # ??? tries to force the cursor to the next line
        else:
            sys.stdout.write("\x1b[?25h")  # Restore cursor
            sys.stdout.write('\r')
            sys.stdout.flush()
            time.sleep(0.2)
            print()  # ??? tries to force the cursor to the next line
    # ### class Spinner: ### #



# #########################
class Transcript:
    # #####################
    """
    purpose: Transcript - direct print output to a file, in addition to terminal. It appends the file target
    requires:
        import sys
        class Transcript
        def transcript_start
        def transcript_stop
    usage:
        import transcript
        transcript.start('logfile.log')
        print("inside file")
        transcript.stop()
        print("outside file")
    """
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.logfile = open(filename, "a")
        # """--== SEP_LINE ==--"""
    def write(self, message):
        self.terminal.write(message)
        self.logfile.write(message)
        # """--== SEP_LINE ==--"""
    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass
    # ### class Transcript: ### #


# #######################################
class ThreadWithReturn(threading.Thread):
    # ###################################
    """
    purpose: threaded commands...
    requires:
        import threading
    usage:
        run_cmd_threaded(cmd)
        which does this ...
        dbug("Just getting started...")
        cmd = "~/ofrd.sh"
        t1 = ThreadWithReturn(target=run_cmd, args=(cmd,))
        t1.start()
        dbug("Done")
        result = t1.join()
        dbug(result)
    """
    def __init__(self, *init_args, **init_kwargs):
        threading.Thread.__init__(self, *init_args, **init_kwargs)
        self._return = None
        # """--== SEP_LINE ==--"""
    def run(self):
        self._return = self._target(*self._args, **self._kwargs)
        # """--== SEP_LINE ==--"""
    def join(self):
        threading.Thread.join(self)
        return self._return


# #############
class SQLiteDB:
    # #########
    """
    purpose: instance of an object to manage an SQLite db
    requires: db.connection(dbname)  # ie "mydatabase.db"
    options:
    use:
        - db = SQLiteDB(dbname_filename)
        - db.connection(dbname)
        - db.create_table(tablename, columns)  # first col 'id' will be created 
                                               # eg: columns = "col1 TEXT, col2 INT, col3 REAL, col4 BLOB, NUMERIC,..."
                                               # or {'col1': 'TEXT', 'col2', 'text', 'col3': 'numeric', ...}
                                               # or ['col1', 'col2', 'col3', ....]  # everything will be made NUMERIC
        - db.show_tables() or db.get_tables()
        - db.insert(tablename: str, data: dict | lol)  # data = {col: val, ...} 
                                               # If a table already exists you can submit just data
        - db.update(tablename, data, where)   
        - db.delete(tablename, where):
        - db.fetchall(tablename, query)
        - db.fetchone(tablename, query)
        - db.get_colnames(tablename)
        - db.execute(tablename, query)
        - db.drop_table(tablename)
        - db.close()
    notes:
        - WIP - use at your own risk!
        - this code  added 2025 and is in need of severe refactoring!
    """
    import sqlite3
    def __init__(self, dbname="", tablename="", columns="", *args, **kwargs):
        """
        purpose: init an sqlite database
        requires: dbname
        options: tablename, columns
        returns: None
        notes:
            - WIP
        """
        # """--== Config ==--"""
        self.dbfile = ""
        dbname = arg_val(['dbname', 'db'], args, kwargs, dflt=dbname)
        dbname_dtype = data_type(dbname)
        if 'sqlite' in dbname_dtype:
            self.dbfile = dbname
            self.dbname = rootname(dbname)
        else:
            dbfile = arg_val(["dbfile", "file", "filename", "fname"], args, kwargs, dflt=self.dbfile)
        if dbname == "help":  # special call for help
            printit(SQLiteDB.__doc__, 'boxed', title='SQLiteDB help', footer=dbug('here'))
            return
        self.dbfile = os.path.expanduser(self.dbfile)
        tablename = arg_val(["table", "tablename", "tbl"], args, kwargs, dflt=tablename)
        columns = arg_val(["cols", "columns", "colnames"], args, kwargs, dflt=columns)
        # dbug(f"{self.dbfile=} {self.dbname=} {tablename=} {columns=} {called_from('verbosr')}")
        # """--== SEP_LINE ==--"""
        # dbug(dbname)
        dbfile_dtype = data_type(self.dbfile)
        if 'empty' in dbfile_dtype:
            dbug(f"{self.dbfile=} appears to be empty {called_from('verbose')}... returning...")
            return
        if 'sqlite' not in dbfile_dtype:
            dbug(f"{self.dbfile=} appears to not be an sqlite file {called_from('verbose')}... returning...")
            return
        if not os.path.splitext(dbname)[1] != '':
            dbname = os.path.basename(os.path.expanduser(dbname))
        if not dbname.endswith(".db"):
            # dbug(f"adding '.db' to dbname: {dbname}")
            self.dbname = dbname
            dbfile = dbname + ".db"
        else:
            # dbug(f"dbname: {dbname} endswith(.db)")
            dbfile = dbname
            self.dbname = rootname(dbname)
        # dbug(dbname)
        # dbug(dbfile)
        self.dbfile = os.path.expanduser(dbfile)
        self.conn = None
        self.tables = []
        if tablename != "" and columns != "":
            dbug(f"Using tablename: {tablename} columns: {columns}")
            self.create_table(tablename, columns)
            self.tables.append(tablename)
        # dbug(f"dbfile exists?: {file_exists(dbfile)} self.tables: {self.tables}")
        # if not file_exists(dbfile):
            # dbug("Unable to find {dbfile=} {called_from('verbose')} ...returning...")
            # return
        # dbug(f"{dbfile=} {dbname=} {tablename=} {columns=} {called_from('verbose')}")
    # """--== SEP_LINE ==--"""
    def connect(self):
        import sqlite3
        # dbug(self.dbfile)
        self.conn = sqlite3.connect(self.dbfile)  # this is crucial!
        # dbug(f"{self.dbfile=} {self.dbname=} {called_from('verbose')}", 'ask')
    conn = connect
    # """--== show tables ==--"""
    def show_tables(self):
        """
        purpose: does the same as get_tables
        requires:
        options:
        returns:
        notes:
            - WIP
            - 20251014-1656
        """
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        my_tables = cursor.fetchall()
        # dbug(my_tables)
        rtrn = []
        for tbl in my_tables:
            rtrn.append(tbl[0])
        return rtrn 
    # """--== get_tables alias ==--"""
    get_tables = show_tables
    # """--== create table ==--"""
    def create_table(self, tablename, colnames, *args, **kwargs):
        """
        purpose: create a table for existing self.dbname/file
        requires: 
            - tablename
            - colnames
        options:
        returns: None
        notes:
            - WIP
        """
        # """--== Config ==--"""
        # """--== Convert/Init/Validate ==--"""
        if isempty(tablename):
            dbug(f"tablename: {tablename} appears empty... returning")
            return
        if isempty(colnames):
            dbug(f"colnames: {colnames=} appears empty {called_from('v')}... returning")
            return
        # """--== SEP_LINE ==--"""
        # dbug(called_from())
        if tablename in self.tables:
            dbug("Table exists ...returning")
            return
        else:
            # dbug(self.tables)
            my_tables = self.get_tables()
            # dbug(my_tables)
            if len(self.tables) > 0 and tablename in my_tables[0]:
                # dbug(f"Found tablename: {tablename} in my_tables[0]: {my_tables[0]}... returning...")
                self.tables.append(tablename)
                return
        # dbug(self.tables, 'ask')
        # dbug(called_feom())
        # untried: colnames colname can include type eg: ["name NOT NULL UNIQUE", "age", "gender"]
        # dbug(colnames)
        if isinstance(colnames, str):
            # assuming it already has the proper construction...
            pass
        if isinstance(colnames, list):
            if "id" in colnames:
                dbug("Found colname... what to do... I suggest removing it in order to replace it!")
                colnames.remove("id") 
            # dbug(columns)
            colnames = [colname.strip().replace(" ", "_") for colname in colnames if not colname.isspace()]
            # dbug(colnames)
            columns_s =  [str(col) + " NUMERIC" if len(str(col)) == 1 else str(col) for col in colnames]
            columns_s =  ", ".join(colnames)
            # dbug(columns_s)
        if isinstance(colnames, dict):
            my_cols = ""
            for k, v in colnames.items()[:-1]:
                if k == "id":
                    continue  # eliminate if as we will replace it below
                my_cols += f"{k} {v}, "
            my_cols += f"{k} {v};"
            columns_s = my_cols
        # dbug(columns_s)
        if "id" not in colnames:
            indx_col = "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            columns = indx_col + columns_s
        # query = f"CREATE TABLE IF NOT EXISTS {tablename} ({indx_col}{columns})"
        query = f"CREATE TABLE IF NOT EXISTS {tablename} ({columns})"
        self.execute(query)
        if tablename not in self.tables:
            self.tables.append(tablename)
    # """--== execute ==--"""
    # needed for the other queries below
    def execute(self, query, params=None):
        """
        purpose: this executes an sqlite "query" against a sqlite database
        requires: query
        options:
        returns: usually a dict (row of col,val) pairs
        notes:
            - this is where the rubber hits the road
            - WIP
        """
        # dbug(query)
        # dbug(params)
        # dbug(called_from())
        if isempty(query):
            # dbug(f"query: {query} can not be empty.... returning...")
            return
        else:
            if not query.endswith(";"):
                query += ";"
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        if params:
            # params is the values that feed into the placeholder question marks... see insert()
            cursor.execute(query, params)
        else:
            # dbug(f"Trying query: {query} {called_from()}")
            try:
                cursor.execute(query)
                self.conn.commit()
                # dbug(f"query: {query}  executed successfully? returning cursor: {cursor}")
                return cursor
            except Exception as Error:
                dbug(f"query: {query} failed {called_from()} Error: {Error}....please investigate...")
                return None
        # self.conn.commit()
        # dbug(f"query: {query}  executed successfully? returning cursor: {cursor}")
        # return cursor
    # """--== get_colnames ==--"""
    def get_colnames(self, tablename=""):
        """
        purpose: retrieve columns for tablename: str=self.tables[0]
        requires:
        options:
            - tablename
        returns: colnames: list
        notes:
          - WIP
        """
        # dbug(f"{self.dbfile=} {self.dbname=} {tablename=} {called_from('verbose')}")
        if tablename == "":
            tablename = rootname(self.dbname)
            self.tablename = tablename
            # dbug(tablename)
        # dbug(called_from())
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {tablename} LIMIT 1;"
        try:
            cursor.execute(query)
        except Exception as Error:
            dbug(f"{Error=} {query=} {self.dbfile=} {self.dbname=} {called_from('verbose')} returning...")
            return
        # dbug(r)
        colnames =  [member[0] for member in cursor.description]
        # dbug(my_l)
        return colnames
    # """--== fetchone ==--"""
    def fetchone(self, query, params=None):
        """
        purpose: grab first matching record and return a dictionary of {col:val,...}
        requires: 
            - query
        options:
        returns:
        notes:
          - WIP
        """
        # dbug(f"{query=} {called_from('verbose')}")
        # dbug(self.tablename)
        m = re.search("SELECT (.*?) FROM (.*?) ", query)
        # dbug(m.groups())
        selected_cols = m.group(1)
        this_tablename = m.group(2)
        # dbug(this_tablename)
        if isempty(this_tablename) and not isempty(self.tablename):
            tablename = self.tablename
            # dbug(tablename)
        tablename = this_tablename
        if selected_cols == "*":
            # dbug(tablename)
            selected_cols = self.get_colnames(tablename)
            # dbug(selected_cols)
        else:
            selected_cols = selected_cols.split(",")
        # dbug(selected_cols)
        # dbug(this_tablename)
        # dbug(tablename)
        # dbug(query)
        try:
            cursor = self.execute(query, params)
            row_t = cursor.fetchone()
        except Exception as Error:
            dbug(f"{Error=} with {query=} {called_from('verbose')}")
            return
        # dbug(row_t)
        if row_t is not None:
            row_l = list(row_t)
            # dbug(row_l)
        else:
            row_l = None
            return None
        # dbug(type(selected_cols))
        # dbug(selected_cols)
        # dbug(type(row_l))
        row_d = dict(zip(selected_cols, row_l))
        # dbug(f"Returning row_d: {row_d}")
        return row_d
    # """--== fetchall ==--"""
    def fetchall(self, query="", params=None):
        """
        purpose:
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        colnames = []
        if query == "":
            tablename = rootname(self.dbname)
            # dbug(tablename)
            query = f"SELECT * FROM {tablename};"
            colnames = self.get_colnames()
        # dbug(tablename)
        # dbug(query)
        # dbug(params)
        cursor = self.execute(query, params)
        rows_lot = cursor.fetchall()
        rows_lol = [list(row) for row in rows_lot]
        if not isempty(colnames):
            # probably because no query so we used rootname(self.dbname) and got all records above
            rows_lol.insert(0, colnames)
        return rows_lol
        # return cursor.fetchall()
    # """--== insert ==--"""
    def insert(self, tablename="", data={}, *args, **kwargs):
        """
        purpose: to add data
        requires:
            - tablename: str (optional if one exists)
            - data: dict   # {col:val,...} 
        options:
        notes:
        """
        # dbug(called_from())
        # dbug(tablename)
        # dbug(data)
        # """--== Config ==--"""
        tablename = arg_val(['table', 'tablename', 'tname', 'tbl'], args, kwargs, dflt=tablename)
        colnames =  arg_val(['colnames', 'columns'], args, kwargs, dflt=None)
        data =  arg_val(['data'], args, kwargs, dflt=data)
        # """--== Convert/Init ==--"""
        dtype = data_type(data)
        # dbug(dtype)
        if dtype in ("empty"):
            dbug(f"data appears empty data: {data} {called_from()}...")
        # dbug(self.tables)
        if dtype in ('lol'):
            colnames = data[0]
            if colnames[0].lower() in ("id", "index", "indx"):
                colnames = colnames[1:]
                data = [row[1:] for row in data] 
        if not isempty(colnames):
            colnames_s = ', '.join(colnames)
        if isinstance(tablename, dict) and isempty(data):
            # dbug("User provided data instead of a tablename so I will switch that")
            data = tablename
            if len(self.tables) > 0:
                dbug(self.tables)
                tablename = self.tables[0]
            else:
                dbug("tablename and data appear to be empty ...returning...") 
                return
        if isempty(self.tables):
            tablename = rootname(self.dbname)
            if isempty(colnames):
                dbug(f"Creating table with create_table(tablename:{tablename}), colnames:{colnames}<==empty? dtype: {dtype} {called_from('verbose')}...")
                # return
            self.create_table(tablename, colnames=colnames)
        # dbug(tablename)
        # """--== Process ==--"""
        # make sure that id is removed as the table autoincrements an initial column with the 'id' index
        # dbug(data)
        if dtype in ('lol'):
            for row in data:
                if colnames == row:
                    continue
                vals_s = ', '.join(f'"{item}"' for item in row)
                query = f"INSERT INTO {tablename} ({colnames_s}) VALUES ({vals_s})"
                self.execute(query)
        if dtype in ('dov'):
            if "id" in data:
                data.pop("id")
            data = {f"'{k}'" if k[0].isdigit() else k: v for k, v in data.items()}  # double quote if first char is a digit as sqlite doesn't like colnames that start with a digit
            # placeholders = ', '.join(['?'] * len(data))
            vals = list(data.values())
            vals_s = ', '.join(f'"{item}"' for item in vals)
            colnames_s = ', '.join(data.keys())
            query = f"INSERT INTO {tablename} ({colnames_s}) VALUES ({vals_s})"
            self.execute(query)
        if isempty(colnames_s) or isempty(vals_s):
            dbug("A problem occurred with the submitted data; please investigate...returning...")
            return
    # """--== update ==--"""
    def update(self, tablename, data, where):
        """
        purpose:
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        # dbug(data)
        # dbug(called_from())
        # dbug(where)
        # dbug(tablename)
        # """--== validate ==--"""
        if isempty(tablename) or not isinstance(tablename, str):
            dbug("We need a tablename: {tablename} ... returning...")
            return
        if isinstance(data, dict):
            data = {f"'{k}'" if k[0].isdigit() else k: v for k, v in data.items()} # deal with colnames that start with a digit
        if "id" in data:
            data.pop("id")
        # dbug(data)
        set_q = ', '.join([f"{key} = ?" for key in data.keys()])
        where = where.replace("WHERE", "")
        query = f"UPDATE {tablename} SET {set_q} WHERE {where}"
        # dbug(query)
        self.execute(query, tuple(data.values()))
    # """--== either ==--"""
    def either(self, tablename="", data={}, where_q="", *args, **kwargs):
        """
        purpose:
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        # dbug(data)
        prnt = arg_val(['prnt','print','show','verbose'], args, kwargs, dflt=False)
        data = {f"'{k}'" if k[0].isdigit() else k: v for k, v in data.items()}
        # dbug(data, 'ask')
        # purpose is to update a record if it exists, or insert one if it doesn't
        # validate - requires data that has the one less len(get_colnames(table) - one less because of 'id'
        if where_q.startswith("WHERE"):
            where_q = where_q.replace("WHERE", "")
        my_q = f"SELECT * FROM {tablename} WHERE {where_q};"
        # dbug(my_q)
        r = self.fetchone(my_q)
        # dbug(r)
        if r is not None:
            # dbug(f"where_q: {where_q} data: {data}")
            self.update(tablename, data, where_q)
            if prnt:
                dbug(f"Updated tablename: {tablename} with data {data} {where_q}")
        if r is None:
            # dbug(f"data: {data}")
            self.insert(tablename, data)
            if prnt:
                dbug(f"Inserted into tablename: {tablename} with data {data}...")
        # dbug('ask')
    # """--== delete (record[s]) ==--"""
    def delete(self, tablename, where):
        """
        purpose:
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        if "WHERE " in where:
            where = where.replace("WHERE ", "")
        query = f"DELETE FROM {tablename} WHERE {where}"
        # dbug(query)
        self.execute(query)
    # """--== modify column ==--"""
    def mod_col(self, table, old_colname, new_colname, new_type):
        """
        purpose:
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        dbug("WIP !!!! UNFINISHED - UNTESTED !!! WIP") #
        # """--== SEP_LINE ==--"""
        # -- Drop the column
        # q = f"alter table target_table drop target_col;"
        # self.execute(q)
    # """--== drop_table ==--"""
    def drop_table(self, tablename):
        """
        purpose:
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        query = f"DROP table IF EXISTS {tablename};"
        self.execute(query)
        return
    # """--== close ==--"""
    def close(self):
        """
        purpose: closes the db connection
        requires:
        options:
        returns:
        notes:
          - WIP
        """
        if self.conn:
            self.conn.close()
            self.conn = None
    # ### EOB class SQLiteDB: ### #


# ################# #
# ### FUNCTIONS ### #
# ################# #


# ############################################
def get_sqlite_rows(dbfname, *args, **kwargs):
    # ########################################
    """
    purpose: uses fetchall to get colnames and all records from sqlite db file
    requires:
    options:
    returns: a list of list (aka lol or rows of columns, first row is colnames)
    notes:
        - WIP
        - 20251027-0842
    """
    import sqlite3
    # """--== Config ==--""" #
    tablename = arg_val(["tablename", "tname", "tblname"], args, kwargs, dflt=rootname(dbfname))
    # dbug(f"{dbfname=} {tablename=}")
    # """--== convert and validate ==--""" #
    # dbug(f"{os.getcwd()=} {called_from('v')}")
    dbfname = os.path.expanduser(dbfname)
    # dbug(f"{dbfname=} {tablename=}")
    # dbfname = os.path.abspath(dbfname)
    # dbug(f"{dbfname=} {tablename=}")
    # dbug(os.getcwd())
    if not file_exists(dbfname):
        dbug(f"Failed to find {dbfname=}... returning...")
        return
    # """--== Process ==--""" #
    conn = sqlite3.connect(dbfname)
    cursor = conn.cursor()
    query = f"SELECT * FROM {tablename}"
    cursor.execute(query)
    rows_t = cursor.fetchall()
    conn.close()
    rows = [list(row) for row in rows_t]
    colnames = [description[0] for description in cursor.description]
    rows.insert(0, colnames)
    # btw: select seq from sqlite_sequence where name="table_name" to get last primary key
    # """--== Returning ==--""" #
    # gtable(rows, 'prnt', 'hdr', title='debugging', footer=dbug('here'), col_limit=8)
    return rows
    # ### EOB def get_sqlite_rows(dbfname, *args, **kwargs): ### #


# ##################################################
def put_sqlite_rows(data, dbfname, *args, **kwargs):
    # ##############################################
    """
    purpose: put/writes out all submittes data (typically an lol) to an sqlite db file
    requires:
        - data: lol (but cnvrt is used to try and turn lots of data types into an lol)
    options:
        - bak: bool  # creates a backup file in same dir with datetime stamp extension
        - arch: dict # creates timestamped backup file in ARCH/ dir using {'days':x, 'files':x, 'arch_dir': 'ARCHIVE') format - see arch.__docs__
    returns: True or False ie successful or failed
    notes:
        - WIP
        - 20251027-0800
    """
    import sqlite3
    # """--== Config ==--""" #
    prnt = arg_val(['prnt', 'print', 'show'], args, kwargs, dflt=False)
    bak_b = arg_val(['bak', 'backup', 'bakup'], args, kwargs, dflt=False)
    arch_d = arg_val(['arch', 'archive'], args, kwargs, dflt={})
    tablename = arg_val(['tablename', 'table','tblname'], args, kwargs, dflt=rootname(dbfname))
    # """--== Process ==--""" #
    # dbug(f"{dbfname=} {called_from('v')}")
    # dbug(f"{prnt=} {bak_b=}")
    dbfname = os.path.expanduser(dbfname)
    # dbug(dbfname)
    abs_dbfname = os.path.abspath(dbfname)
    # dbug(f"{abs_dbfname=} {called_from('v')}")
    # """--== bak ==--""" #
    if bak_b and file_exists(dbfname):
        dbfname_bak = abs_dbfname + "." + datetime.now().strftime("%Y%m%d-%H%M")
        shutil.copy(abs_dbfname, dbfname_bak)
        if prnt:
            dbug(f"{abs_dbfname=} has been backed up to {dbfname_bak=}")
    # """--== arch ==--""" #
    if isinstance(arch_d, dict):
        days = files = 0
        if 'days' in arch_d:
            days = arch_d['days']
        if 'files' in arch_d:
            files = arch_d['files']
        # dbug(f"{dbfname=} {prnt=} {called_from('v')}")
        # dbug(f"{os.getcwd()=}")
        arch(abs_dbfname, prnt=prnt, days=days, files=files)
        # dbug(f"{os.getcwd()=}")
        if prnt:
            dbug(f"{dbfname=} has been copied to an ARCHive")
    # """--== SEP_LINE ==--""" #
    lol = cnvrt(data)
    # dbug(len(lol), 'ask')
    colnames = data[0]
    colnames = [str(col) for col in colnames]
    # dbug(colnames)
    colnames_no_id = [str(col) for col in colnames if col.lower() != "id"]
    colnames_bld_tbl_s = " TEXT, ".join(colnames_no_id)
    colnames_wrkg_s = ", ".join(colnames_no_id)
    # dbug(colnames_bld_tbl_s, 'ask')
    # dbug(colnames_wrkg_s, 'ask')
    tablename = rootname(dbfname)
    # """--== SEP_LINE ==--""" #
    try:
        conn = sqlite3.connect(abs_dbfname)
        cursor = conn.cursor()
    except Exception as Error:
        dbug(f"{Error=} {abs_dbfname=} ... returning...",'ask')
        return False
    query = f"DROP TABLE IF EXISTS {tablename}"
    cursor.execute(query)
    query = f"CREATE TABLE IF NOT EXISTS {tablename} (id INTEGER PRIMARY KEY, {colnames_bld_tbl_s})"
    # dbug(f"Created {tablename=}")
    cursor.execute(query)
    # """--== SEP_LINE ==--""" #
    # First drop table if it exists
    # Insert data into the table
    cnt = 0
    for row in lol[1:]:
        wrkg_vals_s = ", ".join([f"'{colval}'" for colval in row[1:]])
        try:
            if colnames[0].lower() in ('id', 'indx', 'key', 'index'):
                query = f"INSERT INTO {tablename} ({colnames_wrkg_s}) VALUES ({wrkg_vals_s})"
            else:
                query = f"INSERT INTO {tablename} ('id', {colnames_wrkg_s}) VALUES ({int(row[0])}, {wrkg_vals_s})"
            # dbug(query, 'ask')
            cursor.execute(query)
            cnt += 1
        except Exception as Error:
            dbug(f"{Error=} {query=}")
            # query = f"INSERT INTO {tablename} ({colnames_wrkg_s}) VALUES ({wrkg_vals_s})"
            # cursor.execute(query)
            return False
    # dbug(cnt) 
    conn.commit()
    conn.close()
    return True
    # ### EOB def put_sqlite_rows(data, dbfname, *args, **kwargs): ### #


# ############################
def fix_lang(*args, **kwargs):
    # ########################
    """
    purpose: fix systems that have failed to properly set LANG or PYTHONIOENCODING yo UTF-8
    requires: none
    options: none
    returns: none
    notes:
        - WIP
        - 20250807-1017
        - should add this to the beginning of a script (if needed)
    """
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    return


# #############
def timeit(f):
    # ########
    """
    purpose: (wrapper) developer tool to measure time spent in a function and count of function calls
    requires: placement as a decorate directly before the funcion name
    options: none
    returns: prints count of function calls, function name, limited args and kwargs, and the elapsed time 
    use: @timeit
         def func():
             ...
    notes:
        - this breaks dbug() and called_from() in the wrapped function
        - WIP
    """
    # return f # uncomment this to bypass any work or printing here - comment it for debugging... a quick-n-dirty toggle
    # from functools import wraps
    # @wraps(f)  # this preserves traceback doc etc for the wrapped func
    # dbug(called_from())
    import traceback
    traceback.print_exc()
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        my_args = ','.join(str(y) for x in args for y in x if len(x) > 0)
        my_func = f"{f.__name__:<25}"
        # my_args = str(*args)[:25]
        my_args = " ".join([str(arg) for arg in args])[:25]
        my_kwargs = " ".join([f"{key}={value}" for key, value in kwargs.items()])
        # dbug(my_kwargs)
        all_args = f"{my_args:25}, {my_kwargs[:25]}"
        wrapper.calls += 1
        elapsed = end-start
        wrapper.tot_time += elapsed 
        printit(f"calls: {wrapper.calls:3} func: [yellow]{my_func}[/]({all_args:50}) elapsed: [yellow! on black!]{elapsed:>2.4f}[/] total_time: {wrapper.tot_time:>3.4f}")
        return result
    wrapper.calls = 0
    wrapper.tot_time = 0
    return wrapper
    # ### EOB def timeit(f): ### #


# ################
def funcname(n=0):
    # ############
    """
    purpose: returns current function name - primarily used for debugging
    """
    return sys._getframe(n + 1).f_code.co_name


# ###########
def lineno():
    # #######
    """
    purpose: returns current line number - primarily used for debugging
    """
    cf = currentframe()
    return str(cf.f_back.f_lineno)
 

# ###############################
def called_from(*args, **kwargs):
    # ###########################
    """
    purpose: to grab and display where a function was called from
    requires: none
    options: 
        - prnt: bool=False
        - brief: bool=False
        - func_only: bool=False
        - levels: int    # how far back to track
        - color: bool  # will colorize called file as cyan and func:lineno as yellow!
    returns: str
        - default: f"called from: {function_name}:{line_number}"
        - brief:   f"{function_name}:{line_number}"
    notes:
    """
    import inspect
    # from inspect import getframeinfo, stack
    # from inspect import stack
    # """--== Config ==--"""
    # prnt = arg_val(['prnt', 'print', 'show'], args, kwargs, dflt=False)
    func_only = arg_val(['func', 'funcname'], args, kwargs, dflt=False)
    brief_b = True
    if any([item in ['brief','short','silent','b','s'] for item in args]):
        brief_b = True
    # brief_b = arg_val(['brief', 'short', 'silent', "b", "s"], args, kwargs, dflt=True, opposites=['verbose', 'v', 'long'])

    if any([item in ['verbose','v'] for item in args]):
        brief_b = False
    # levels = arg_val(['levels', 'lvls','level','lvl'], args, kwargs, dflt=0)
    levels = 0
    levels_l = ['levels', 'lvls','level','lvl']
    for key in levels_l:
        if key in kwargs:
            levels = kwargs[key]
    matching_values = [kwargs[k] for k in levels_l if k in kwargs]
    if matching_values:
        print(f"{matching_values=}")
    color_b = any([item in ['color','clr'] for item in args])
    # color_b = arg_val(['color', 'clr'], args, kwargs, dflt=False)
    # """--== SEP_LINE ==--"""
    # """--== Init ==--"""
    history = []
    msg = ""
    # """--== Process ==--"""
    this_stack = inspect.stack()
    # dbug(stack[1][1])  # file name
    stack_num = 1
    for stack_num in range(2, len(this_stack)):  # start as 1 because 0 is itself 
        caller_filename = os.path.basename(this_stack[stack_num][1])
        caller_funcname = this_stack[stack_num][3]
        caller_lineno = this_stack[stack_num][2]
        if "__call__" in caller_funcname or "<module>" in caller_funcname or "?" in caller_funcname or "None" in caller_funcname:
            # dbug(f"skipping: {stack_num=} {caller_funcname=}")
            continue
        # dbug(f"{caller_filename}:{caller_funcname}:{caller_lineno} {stack_num=}")
        break
    # dbug(f"{caller_filename}:{caller_funcname}:{caller_lineno} {stack_num=} {len(msg)-len(msg.lstrip())=}")
    if brief_b:
        if not color_b:
            msg = f"{caller_filename}:{caller_funcname}:{caller_lineno}"
        else:
            msg = f"[cyan!]{caller_filename}[/]:[yellow!]{caller_funcname}:{caller_lineno}[/]"
    if not brief_b:
        msg = f" called_from: {caller_filename}:{caller_funcname}:{caller_lineno}"
    if func_only:
        msg = caller_funcname
    # if prnt:
        # print(msg)
    history = []
    for i in range(1, min(len(this_stack), levels + 1)):  # <-- carefull here
        # printit(stack, 'boxed', title="debugging stack", footer=dbug('here'), box_clr='red!')  # debugging only
        function_name = this_stack[i].function
        file_name = os.path.basename(this_stack[i][1])
        line_number = this_stack[i][2]
        # dbug(f"{function_name=} {file_name=} {line_number=}", 'ask')
        if function_name in [None, '', '?', '<module>']:
            file_name = os.path.basename(this_stack[1][1])
            function_name = this_stack[1][3]
            line_number = this_stack[1][2]
        if function_name == "__call__":
            function_name = "Tracker.__call__"
        # dbug(stack[i])
        if color_b:
            history.append(f"[cyan]{file_name}[/]:[yellow!]{function_name}:{line_number}[/]")
        else:
            history.append(f"{file_name}:{function_name}:{line_number}")
        # dbug(f"just appended history line {color_b=} {levels=} {prnt=} ...")
    # """--== SEP_LINE ==--""" #
    # caller = ""
    # dbug(caller)
    # printit(stack, 'boxed', title="debugging stack", footer=dbug('here'), box_clr='red!')  # debugging only
    #call_hits = 0
    #if len(history) > 1:
    #    for num, ln in enumerate(history):
    #        # dbug(f"Checking {ln=} {num=}")
    #        if "__call__" in ln:
    #            call_hits += 1
    #            # dbug(f"Found __call__ in {ln=} {num=} {len(history)=}")
    #            try:
    #                caller = f"[{history[num+1]}"
    #            except Exception:  #  as Error:
    #                # dbug(Error)
    #                pass
    #            # go back to the function before Tracker
    #if caller == "":
    #    try:
    #        caller = f"[{history[1]}]"
    #    except Exception as Error:
    #        dbug(f"{Error=} {history=} {stack=}")
    #        msg = f"{caller_filename}:{caller_funcname}:{caller_lineno}"
    ## caller = stack
    #if call_hits > 0 and call_hits < 2:
    #    if not brief_b:
    #        msg = f" Called from: {caller}"
    #    else:
    #        msg = caller
    if levels > 1:
        printit(history, 'boxed', title=f"called_from(levels={levels})", footer=dbug('here'), box_clr='red!')
    # """--== returning ==--""" #
    # dbug(f"returning {msg=}")
    return msg
    # ### EOB def called_from(*args, **kwargs): ### #


# ##############################################
def ddbug(msg="", *args, ask=False, exit=False):
    # ##########################################
    """
    purpose: this is for use by dbug only... as dbug can't call itself
    requires: nothings, but typically is used with a user supplied (f_string type) message
    options: 
        - ask: bool    # stop and ask the user if they want to continue
        - exit: bool   # tells debug to immediately exit when 'ask' is used (above) or the default is to continue after the user responds to 'ask' with "y"es.
    note: this is a very limited form of dbug() only used to avoid dbug calling itself recursively
    """
    # """--== Debugging ==--"""
    # print(f"funcname: {funcname()}")
    # print(f"ask: {ask}")
    # """--== SEP_LINE ==--"""
    # dbug = DBUG if DBUG else 1
    # my_centered = True if 'center' in args else False
    # my_centered = True if 'centered' in args else centered
    ask = True if 'ask' in args else False
    exit_b = True if 'exit' in args else False
    # dbug(f"ask:  {ask} exit_b: {exit_b}")
    # cf = currentframe()
    filename = str(inspect.getfile(currentframe().f_back))
    filename = os.path.basename(filename)
    fname = str(getframeinfo(currentframe().f_back).function)
    fname = os.path.basename(fname)
    lineno = str(inspect.currentframe().f_back.f_lineno)
    msg = f"*** DDBUG ***: [{filename}; {fname} (..): {lineno} ] {msg}"
    try:
        print(msg)
    except Exception as e:
        print(f"print({msg}) failed Error: {e}")
        print(msg)
    if ask:
        askYN()  # this will ask "Continue:" ... should exit with 'n'
    if exit_b:
        sys.exit()
    return msg
    # ### EOB def ddbug(msg="", *args, ask=False, exit=False): ### #


def tracebak(*args, **kwargs):
    """
    purpose:
    requires:
    options:
    returns:
    notes:
        - WIP
        - 20251115-0623
    """
    title = arg_val(['title'], args, kwargs, dflt="")
    footer = arg_val(['footer'], args, kwargs, dflt="")
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    import traceback
    tb = traceback.format_stack()
    # printit(tb, 'boxed', bxclr="red!", title=title, footer=footer)
    tb_l = tb[:-1]
    printit(tb_l, 'boxed', bxclr="red!", title=title, footer=footer)
    if ask_b:
        askYN()
    return


# ############
def dbug(xvar="", *args, **kwargs):
    # ########
    """
    purpose: display DEBUG file, function, linenumber and your msg of local variable content
    required: xvar: str ... can be a local variable, a python statement, a string, a list
    options:
        - ask: bool          # forces a breakpoint, stops execution ans asks the user before continuing
            - timeout: int=0 # you can use a timeout option which works with the ask option
        - here|noprnt: bool  # will only return the DEBUG info (file, function. linenumber) as a string without printing - typically used like this boxed("my box", footer=dbug('here'))
        - boxed: bool        # boxes debug output
        - box_color: str     # declares box_color default is 'red! on grey40'
        - color: str         # declares text output color
        - nocolor: bool
        - centered: bool     # centers the debug output
        - lst: bool          # forces printing the variable contents as a list (like printit()) - allows displaying ansii codes properly
        - tbl: bool          # forces printing the variable contents as a table...
        - titled: bool       # only works when 'boxed'... puts the DEBUG info into the title of a box  This should probably be the default...
        - footered: bool     # only works when 'boxed'... puts the DEBUG info into footer of a box
    returns: 
        - prints out debug info (unless 'here'|'noprnt' option invoked)
    notes:
        - the 'lst' feature like 'tbl' below can be sketchy and may not work as expected
        - the 'tbl' feature is not fully tested
    """
    # if "rgb" in xvar:
        # ddbug(f"{xvar=} {called_from('verbose')}")
    # """--== Local Imports ==--"""
    # """--== Config ==--"""
    prnt = arg_val(['prnt'], args, kwargs, dflt=True)
    if not prnt:
        # ddbug(f"{prnt=} so we are bailing out...{called_from('v')}")
        return
    center_b = arg_val(['center', 'centered'], args, kwargs)
    # ddbug(f"center_b: {center_b}")
    box_b = arg_val(['box', 'boxed'], args, kwargs, dflt=False)
    # ddbug(f"{box_b=}")
    color = kvarg_val('color', kwargs, dflt='')
    nocolor = arg_val(['nocolor', 'noclr'], args, kwargs, dflt=False)
    # box_color = kvarg_val('box_color', kwargs, dflt="red! on black")
    box_color = arg_val(['box_color', 'box_clr', 'bxclr'], args, kwargs, dflt="red! on grey40")
    # ddbug(f"{box_color=}")
    DBUG = arg_val(['dbug', 'DBUG'], args, kwargs, dflt=True)  # True unless specified as False
    if not DBUG:
        # DBUG by default above is True
        # the idea here is if dbug looks like this: {where DBUG is True or > 0) dbug(..., dbug=DBUG) then this func will honor the value of DBUG (ie True or False)
        # this should ease the pain for change ... now you can do this
        # DBUG = arg_val('dbug', args)
        # and then dbug(f"whatever here", dbug=DBUG)
        # ddbug(f"DBUG: {DBUG} therefore I am returning [empty handed sort of speak]")
        # further... you could put DBUG = 0 (or False) in GLOBAL vars and use docopts to turn on or off DBUG
        return
    EXIT = arg_val('exit', args, kwargs, dflt=False)
    ask_b = arg_val('ask', args, kwargs, dflt=False)
    warn_b = arg_val(["warn", "warning"], args, kwargs, dflt=False)
    info_b = arg_val(["info"], args, kwargs, dflt=False)
    error_b = arg_val(['err', 'error'], args, kwargs, dflt=False)
    lineno_b = arg_val(['lineno_b', 'lineno', 'line_no', 'line_number'], args, kwargs, dflt=False)
    here_b = arg_val(['here', 'noprnt','xprnt','noprint'], args, kwargs, dflt=False)
    title = kvarg_val("title", kwargs, dflt="")
    footered_b = arg_val(['footered', 'footerred'], args, kwargs, dflt=False)
    footer = kvarg_val("footer", kwargs, dflt="")
    list_b = arg_val(["lst", "list"], args, kwargs, dflt=False)  # print the list in lines if xvar contains a list (like printit for dbug)
    noblanks_b = arg_val(["noblanks", "no_blanks"], args, kwargs, dflt=False)
    if box_b:
        list_b = True
    table_b = arg_val(["tbl", "table"], args, kwargs, dflt=False)  # print the input as a table
    titled_b = arg_val("titled", args, kwargs, dflt=True)  # consider making this the default - this adds the debug_info to the box title
    timeout = arg_val(['timeout'], args, kwargs, dflt=0)
    # ddbug(f"{called_from('v')}")
    # """--== Init ==--"""
    global PRFX  # PRFX = "\x1b["
    global RESET
    if box_color != "red! on grey40":
        box_b = True
    # """--== SEP_LINE ==--"""
    if str(xvar) == 'lineno':
        lineno_b = True
    if str(xvar) == 'here':
        here_b = True
    if str(xvar) == 'ask':
        ask_b = True
        # see below where msg_literal gets changed when it is == 'ask'
    # fullpath filename
    i_filename = str(inspect.getfile(currentframe().f_back))
    filename = os.path.basename(i_filename)  # filename without path
    fname = str(getframeinfo(currentframe().f_back).function)  # fname = function name
    lineno = str(inspect.currentframe().f_back.f_lineno)
    if lineno_b:
        return lineno
    if here_b:
        return f"DEBUG: [{filename}:{fname}:{lineno}]"
    # this inconsistently holds what we want for the most part ...just wrong format - you would have to put this directly into your code and include a msg
    # ie eg:  <frame at 0x7f4d6e4b25e0, file '~/././t.py', line 3000, code tdbug>
    frame = inspect.currentframe().f_back
    def do_prnt(rtrn_msg, *args, ask=ask_b, footer=footer, title=title, titled_b=titled_b, **kwargs):  # , ask=ask_b, centered=center_b:
        # ddbug(f"rtrn_msg: {rtrn_msg} {called_from('verbose')}")
        # ddbug(f"{title=}")
        rtrn_msg = clr_coded(rtrn_msg)
        to_prnt = f"{rtrn_msg}"
        if "\n" in to_prnt:
            # ddbug(f"to_prnt: {to_prnt}")
            to_prnt = "\n" + to_prnt
        COLOR_CODE = rgb(250,0,0, prfx=True)
        # COLOR_CODE = gclr(rgb(250,0,0, prfx=True)
        LVL = "DEBUG"
        if warn_b:
            COLOR_CODE = rgb(250,250,0, prfx=True)
            LVL = "WARN"
        if info_b:
            COLOR_CODE = rgb(250,250,250, prfx=True)
            LVL = "INFO"
        if error_b:
            COLOR_CODE = rgb(250,0,0, prfx=True)
            LVL = "ERR"
        if nocolor:
            COLOR_CODE = ""
        # ddbug(f"{rtrn_msg=}")
        if box_b:
            to_prnt = f"{rtrn_msg}"
            if rtrn_msg.startswith("\n"):
                # dbug(f"lstrip newline from {rtrn_msg=}")
                to_prnt = to_prnt.lstrip("\n")
            # ddbug(f"{called_from('v')=}") 
            my_title = f"{COLOR_CODE + LVL + RESET}: [{filename}:{fname}:{lineno}]"
            my_footer = ""
            if not isempty(title):
                # dbug(title)
                my_title += " " + title
            if not isempty(footer):
                my_footer += footer
            # ddbug(f"titled: {titled}")
            if titled_b or footered_b:
                # ddbug(to_prnt)
                if not box_b:
                    phrases = to_prnt.split(']')
                    # ddbug(f"phrases: {phrases=}")
                    # ddbug(f"{type(phrases[1])=}")
                    if titled_b:
                        my_title += " " + phrases[0] + "]"
                        to_prnt = phrases[1]
                        # this is such a kludge ... arghhh TODO !!!!!
                        if not isinstance(phrases[1], list):
                            # ddbug(f"splitting {phrases[1]=} on newlines")
                            work_l = phrases[1].split("\n")
                        else:
                            work_l = phrases[1]
                        tst_first_line = work_l[0].strip()
                        tst_first_line = tst_first_line.rstrip(":")
                        # ddbug(f"to_prnt: {to_prnt}")
                    if footered_b:
                        if not isempty(footer):
                            footer = f"{footer}"
                        my_footer = footer + " " + phrases[0] + "] " + footer
                        to_prnt = phrases[1]
            # ddbug(f"to_prnt: {to_prnt}")
        else:
            to_prnt = f"{COLOR_CODE + LVL + RESET}: [{filename}:{fname}:{lineno}] {rtrn_msg}"
        if box_b:
            # dbug(f"{my_title=} {title=}")
            to_prnt = boxed(to_prnt, color=color, box_color=box_color, title=my_title, footer=my_footer)
        if center_b:
            to_prnt = centered(to_prnt)
        # ddbug(f"repr(to_prnt): {repr(to_prnt)}")
        printit(to_prnt)  # this is where the rubber hits the road???
        # """--== now decide how to end or exit ==--"""
        # ddbug("{ask_b=}")
        if ask_b:
            # ddbug(f"ask_b: {ask_b}")
            if not askYN("Continue?: ", "y", centered=center_b, timeout=timeout):
                sys.exit()
            # ddbug('ask')
        if EXIT:
            sys.exit()
        return to_prnt
        # ### EOB def do_prnt(rtrn_msg, *args, ask=ask_b, **kwargs):  # , ask=ask_b, centered=center_b): ### #
    # """--== serious work here below ==--"""
    # print(f"Here you go: {inspect.getframeinfo(frame)}")
    line_literal = inspect.getframeinfo(frame).code_context[0].strip()  # the literal string including dbug(...)
    msg_literal = re.search(r"\((.*)?\).*", line_literal).group(1)  # ?non-greedy search
    if msg_literal.replace("'", "") == 'ask' or msg_literal.replace('"', '') == "ask":
        # ddbug(f"msg_literal: {msg_literal} args: {args}")
        ask_b = True
        rtrn_msg = ""
        to_prnt = f"DEBUG: [{filename}:{fname}:{lineno}] {rtrn_msg}\nContinue: "
        # ddbug(f"timeout: {timeout}")
        # ddbug(f"{ask_b=}")
        if not askYN(f"{to_prnt}", timeout=timeout):
            sys.exit()
        return
    all_args = msg_literal.split(",")
    msg_literal = all_args[0]
    # """--== SEP_LINE ==--"""
    lvars = inspect.currentframe().f_back.f_locals
    (f"msg_literal: {msg_literal}")
    if msg_literal.startswith('f"') or msg_literal.startswith("f'"):
        to_prnt = do_prnt(xvar, args, ask=ask_b, footered_b=footered_b, title_b=titled_b, title=title)
        return to_prnt
    if msg_literal.startswith('"') or msg_literal.startswith("'"):
        # ddbug(f"msg_literal: {msg_literal}")
        # ddbug(f"{ask_b=}")
        msg_literal = msg_literal[1:-1]
    # ddbug(f"msg_literal: {msg_literal} lvas: {lvars}")
    # """--== table? WIP ==--"""
    dtype = data_type(xvar)
    if table_b:
        if dtype in ('lol','df','json','dod','dol'):
            # ddbug(f"dtype: {dtype}")
            if isempty(box_color):
                box_color = "red"
            try:
                gtable(xvar, 'prnt', center=center_b, title=title + f' [red]DEBUG[/]: {msg_literal}', footer=footer + " " + called_from(), box_color=box_color),
            except Exception as Error:
                ddbug(f"Error: {Error}")
            return
    # """--== EOB table? ==--"""
    found = False
    if msg_literal in lvars:
        # ddbug(f"Looks like this msg_literal: {msg_literal} is in lvars")
        found = True
    # dtype = data_type(xvar)
    # ddbug(f"{dtype=} {xvar=}", 'ask')
    if dtype == 'str' and "\n" in xvar:
        xvar = xvar.split("\n")
        # ddbug(f"{noblanks_b=}")
        if noblanks_b:
            xvar = [line for line in xvar if line]
        # ddbug(f"{xvar=}")
        dtype = data_type(xvar)
    for k, v in lvars.items():
        # ddbug(f"lvars: {lvars}")
        # ddbug(f"testing msg_literal: {msg_literal} against k: {k}")
        if msg_literal == k or found:  # in loop below we might break out and thereby miss testing if in lvars, hence the found value
            # ddbug(f"looks like msg_literal: {msg_literal} == k: {k}")
            try:
                if "\n" in str(xvar) and list_b:
                    xvar = xvar.split("\n")
                    xvar = [x for x in xvar if x != ""]
            except Exception as Error:
                ddbug(f"{Error=}")
                pass
            # so this is in the local vars so lets build it as a string
            # ddbug(f"{msg_literal=} xvar: {xvar=}")
            if isinstance(xvar, list) and list_b:
                # ddbug(f"xvar: {xvar} islol(xvar): {islol(xvar)} islos(xvar[0]): {islos(xvar[0])} xvar[0]: {xvar[0]}")
                if "\n" in xvar and isinstance(xvar, str):
                    # ddbug(f"splitting {xvar=} on newlines")
                    xvar = xvar.split("\n")
                # ddbug(f"{dtype=}")
                # if islol(xvar) or dtype == "lom" or  dtype == "los" or dtype == "lod" or dtype == "loD":
                if data_type(xvar, ['lol']) or dtype == "lom" or  dtype == "los" or dtype == "lod" or dtype == "loD":
                    # my_prnt = f"[red!]DEBUG[/]: [{filename}:{fname}:{lineno}] {msg_literal}"
                    my_prnt = f"[red!]DEBUG[/]: [{filename}:{fname}:{lineno}]"
                    footer += msg_literal
                    # ddbug(f"{my_prnt=}")
                    # ddbug(f"{footer=}")
                    printit(xvar, box_color=box_color, title=my_prnt + " " + title, boxed=True, footer=footer, centered=center_b)
                    # printit(xvar, 'boxed', title="We are in dbug()", footer="~986")
                    # ddbug(f"{ask_b=}")
                    if ask_b:
                        if not askYN("Continue?: ", "y"):
                            return
                    return
            rtrn_msg = f"{msg_literal}: {xvar}"
            # ddbug(f"{rtrn_msg=}")
            if rtrn_msg.startswith("\n"):
                # dbug(f"lstrip newline from {rtrn_msg=}")
                rtrn_msg = rtrn_msg.lstrip("\n")
            # ddbug(f"args: {args}")
            # ddbug(f"msg_literal: {msg_literal} xvar: {xvar}")
            # do_prnt(rtrn_msg, args, ask=ask_b, footered=footered, titled=titled)
            to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b)
            # ddbug(f"{ask_b=}")
            return to_prnt
        else:
            # not match to a local var
            # ddbug(f" ---- xvar: {xvar} is not in lvars")
            if isinstance(xvar, list) and list_b:
                # ddbug(f"mmmm looks like this is a list xvar: {xvar}")
                # if islol(xvar):
                if data_type(xvar, 'lol'):
                    lines1 = []
                    for elem in xvar:
                        # ddbug(f"type(elem): {type(elem)}")
                        if isinstance(elem, str):
                            # ddbug(f"elem: {elem} is a string")
                            lines1.append("\n".join(elem))
                        # """--== SEP_LINE ==--"""
                        # if islos(elem):
                        if data_type(elem, 'los'):
                            for ln in elem:
                                # ddbug(f"ln: {ln} is a string")
                                # lines1.append("\n".join(ln))
                                lines1.append(ln)
                    xvar = lines1
                    # ddbug(f"xvar: {xvar}")
                xvar = "\n" + "\n".join(xvar)
            # ddbug(f"msg_literal: {msg_literal} k: {k}")
        # rtrn_msg = f"{msg_literal}: {xvar}"
        rtrn_msg = f"{xvar}"
        # ddbug(f"rtrn_msg: {rtrn_msg}")
        # ddbug(f"doing do_prnt now with msg_literal: {msg_literal} xvar: {xvar}")
        # these next 2 lines killed a dbug that has msg_literal like dbug(len(msg))
        # do_prnt(rtrn_msg, args, ask=ask_b, footered=footered, titled=titled)
        # return
    # ddbug(f"msg_literal: {msg_literal} {rtrn_msg=}")
    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(xvar, pd.DataFrame) or isinstance(xvar, pd.core.series.Series):
            rtrn_msg = f"{msg_literal}: {xvar}"
            to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b)
            return to_prnt # yes, this return is needed otherwise bool prnts 2x
    # except Exception as e:
        # ddbug(f"Error: {e}")
    # ddbug(f"msg_literal: {msg_literal}")
    if msg_literal != xvar or not isinstance(msg_literal, str):
        # ddbug(f"msg_literal: {msg_literal}")
        if isinstance(xvar, type):
            rtrn_msg = f"{msg_literal}: {xvar}"
            to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b)
            return to_prnt # yes, this return is needed otherwise bool prnts 2x
        try:
            if re.search(r'^f["].*"$', msg_literal) or re.search("^'.*'$", msg_literal):
                # catches an f-strg (assumes that it is an f-str
                rtrn_msg = xvar  # default to this
                to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b)
                return to_prnt
            else:
                # ddbug(f"msg_literal: {msg_literal} xvar: {xvar} {rtrn_msg=}")
                # if msg_literal == 'ask':
                if msg_literal.replace("'", "") == 'ask' or msg_literal.replace('"', '') == "ask":
                    rtrn_msg = ""
                    # ddbug(f"rtrn_msg: {rtrn_msg}")
                else:
                    if boxed:
                        rtrn_msg = xvar
                        # ddbug(f"{footer=}")
                        footer += f"{msg_literal=}"
                    else:
                        rtrn_msg = f"{msg_literal}: {xvar}"
                # ddbug(f"{rtrn_msg=} {footered_b=}")
                to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b, footer=footer)
                return to_prnt
        except Exception as Error:
            rtrn_msg = f"{msg_literal}: {xvar}"
            ddbug(f"rtrn_msg: {rtrn_msg} Error: {Error}")
            to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b)
            return to_prnt
        return
    rtrn_msg = f"{msg_literal}"
    to_prnt = do_prnt(rtrn_msg, args, ask=ask_b, footered_b=footered_b, titled_b=titled_b)
    return to_prnt
    # ### EOB def dbug(): ### #


# #############################
def transcript_start(filename, *args, **kwargs):
    # ##########################
    """
    Start class Transcript(object=filename),
    appending print output to given filename
    """
    prnt = arg_val(["prnt", 'printit', 'show'], args, kwargs, dflt=False)
    centered_b = arg_val(['centered'], args, kwargs, dflt=False)
    if prnt:
        printit(f"Starting transcript out to {filename}", centered=centered_b)
    sys.stdout = Transcript(filename)


# ########################
def transcript_stop(*args, **kwargs):
    # ###################
    """
    Stop class Transcript() and return print functionality to normal
    """
    prnt = arg_val(["prnt", 'printit', 'show'], args, kwargs, dflt=False)
    centered_b = arg_val(['centered'], args, kwargs, dflt=False)
    sys.stdout.logfile.close()
    sys.stdout = sys.stdout.terminal
    if prnt:
        printit("Stopping transcript out", centered=centered_b)
    return


# #######################################
def kvarg_val(key, kwargs_d={}, *args, **kwargs):
    # ###################################
    """
    purpose: return a value given by a key=value pair using a matching key (in key list if desired)
        NOTE: key can be a string or a list of strings
    options:
        - key provided can be a string or a list of strings
        - dflt="Whatever default value you want - can be a string, list, int, float... whatever" <-- this is optional, if not declared "" is returned
        - if "required" is in the args list or "required=True" is in kwargs dictionary then this becomes a required value
    returns str(key_val) or default_val(which is "" if none is provided)
    notes
        - If any key in the list is set = to a value, that value is returned
        - see: arg_val which process both args and kvargs and returns bool_val
    useage: used in function to get a value from a kwargs ky=value pair
        - eg:
            def my_function(*args, **kwargs):
                txt_center = kvarg_val(["text_center", "txt_cntr", "txtcntr"], kwargs, dflt=1)
        - so if you call my_function(txt_center=99) then txt_center will be set to 99
        - input key(string), kvargs_d(dictionary of key,vals), default(string; optional)
        - this is being deprecated. Use arg_val() instead to gain consistency  
    """
    # """--== Debugging ==--"""
    # print(f"funcname: {funcname()}")
    # print(f"args: {args}")
    # print(f"kwargs: {kwargs}")
    # print(f"key: {key}")
    # print(f"kwargs_d: {kwargs_d}")
    # """--== Init ==--"""
    required = False
    if "required" in args:
        required = True
    mydflt = ""
    if 'dflt' in kwargs:
        mydflt = kwargs['dflt']
        # ddbug(f"dflt: {mydflt}")
        # print(f"dflt: {mydflt} this is in kvarg_val()")
    # """--== Validate ==--"""
 ### required option ### #
    if 'required' in list(kwargs.keys()):
        # dbug(key)
        # dbug(kwargs_d)
        found_flag = False
        for my_k in kwargs_d.keys():
            dbug("checking my_k: {my_k}")
            if my_k in key:
                found_flag = True
                ddbug(f"Found on key: {key} my_k: {my_k}")
        if not found_flag:
            dbug(f"Note: A value for a key: {key} was declared required: [{required}] for this operation. No value was provided")
    # my_val = ""
    my_val = mydflt
    # my_default = ""
    # dbug
    if not isinstance(kwargs_d, dict):
        dbug(f"Supplied kwargs_d: {kwargs_d} MUST be a dictionary! {called_from()} ... Returning...")
        return
    # """--== Convert ==--"""
    if isinstance(key, list):
        keys = key
    else:
        keys = [key]
    # """--== Process ==--"""
    for k in keys:
        # dbug(keys)
        # dbug(k)
        # test each key in list
        if k in kwargs_d:
            # dbug(type(k))
            # dbug(f"k: {k} is in kvargs_d: {kvargs_d}")
            my_val = kwargs_d[k]
            # convert a string into a boolean when needed
            if isinstance(my_val, str):
                if my_val == "False":
                    # dbug(f"Converting my_val: {my_val} to False")
                    my_val = False
                if my_val == "True":
                    # dbug(f"Converting my_val: {my_val} to True")
                    my_val = True
    # print(f"Returning my_val: {my_val}")
    # ans = input("Hit anything this is the end of lvarg_val()")
    return my_val
    # ### EOB def kvarg_val(key, kwargs_d={}): ### #


# ###########################################
def arg_val(key_l, args_l, kvargs={}, **kwargs):
    # #######################################
    """
    purpose: look at args and kwargs with a list of possible option strings and return the default True or False
    requires:
        - key_l: str | list  # this is the string or list of strings to check args and kwargs against
    options:
        - default | dflt: bool  # the default value to return
        - opposite | opposites: str | list  # a list of opposites only affects key found in args_l 
            eg: prnt = arg_val(["print", "prnt"], args, kwargs, dflt=True, opposites=['noprnt', 'no_prnt', 'no_print'])
    return True or False
    Notes:
        Warning: do not use dbug in this func - use ddbug to avoid recursion
        key_l can be a str or list
        args_l must be provided
        kvargs is optional
        used to see if a string or a list of stings might be declared true
            by being in args or seeing it has a bool value set in kvargs
        aka: arg_val() <-- this alias is probably going to replace kvarg_val()
    use:
        DBUG = arg_val('dbug', args, kvargs)
        or
        DBUG = arg_val(['dbug', 'DBUG'], args, kvargs)
    """
    # import types
    # import keyword
    import builtins
    # """--== Debugging ==--"""
    # cf = called_from('v')
    # if "boxed" in cf:
        # ddbug(f"{called_from()=}", 'ask')
    # ddbug(f"args_l: {args_l}")
    # ddbug(f"{kvargs=}")
    # ddbug(f"kwargs: {kwargs}")
    # """--== SEP_LINE ==--""" #
    # if "boxed" in args_l or "boxed" in kvargs or "boxed" in kwargs:
        # print(f"Submitted: {key_l=} {args_l=} {kvargs=} {kwargs=}")
    bool_v = ""
    dflt = ""
    rtrn = None
    kv_val = None
    # kw_val = None
    # opposites = ""  # just for now below we go through the kwargs and change this if requested
    # required = False
    # """--== converts ==--""" #
    if isinstance(args_l, dict) and kvargs == {}:
        # ddbug(f"user only supplied a dict and did not supply {args_l=} so fix this {kvargs=}")
        kvargs = args_l
        args_l = []
        # ddbug(f"Set {args_l=}, {kvargs=}")
    if isinstance(key_l, str):
        key_l = [key_l]  # convert to list
    # """--== default, opposites, required ==--""" #
    for k in ('dflt', 'default'):
        if k in kwargs:
            dflt = kwargs[k]
            rtrn = dflt  # <-- important/crucial
            # print(f"Found {k=} {dflt=} {key_l=} {kvargs=} {kwargs=} for now {rtrn=}")
    # """--== opposites or required ==--""" #
    if len(kwargs) > 0:  # trying to sut down on work load here
        for k in ('opposite', 'opposites'):
            if k in kwargs:
                # ddbug(f"Found {k=} in {kwargs=} {dflt=} {called_from('v')}")
                my_opposites = kwargs[k]
                if isinstance(my_opposites, str):
                    my_opposites = [my_opposites]
                for user_elem in args_l:
                    if user_elem in my_opposites and user_elem not in kvargs:
                        # if user_elem == "lst_b": # specific debug
                            # ddbug(f"{dflt=} {args_l=} {user_elem=} {kvargs=} {rtrn=}")
                        rtrn = not dflt
                        return rtrn
                for user_elem in kvargs:
                    if user_elem in my_opposites or user_elem in args_l and user_elem not in kvargs:
                        # if user_elem == "lst_b": # specific debug
                            # ddbug(f"{dflt=} {args_l=} {user_elem=} {kvargs=} {rtrn=}")
                        rtrn = not dflt
                        return rtrn
    # """--== process kvargs ==--""" #
    if kvargs:
        # first matching key, return the value dflt here is the fallback ie a prioritized lookup
        kv_val = next((kvargs[k] for k in key_l if k in kvargs), dflt)
        rtrn = kv_val
        # if 'lst_b' in kvargs and 'lst_b': # secific debug
            # dbug(f"Using {kvargs=} while {dflt=} and set {rtrn=} {kv_val=} {key_l=}")
    # """--== process args_l ==--""" #
    for k in key_l:
        if k in args_l:
            bool_v = True
            rtrn = bool_v
            break
    # """--== return and debug ==--""" #
    # msg = f"\nSubmitted: {key_l=} {args_l=} {kvargs=} {kwargs=}\nRETURNING: with {key_l=} = {rtrn=}"
    # msg = msg.replace("\n", " - ")
    # ddbug(f"{msg=}")
    # if 'lst_b' in kvargs: # specific debug
        # dbug(f"{args_l=} {kvargs=}")
    return rtrn
    # ### EOB def arg_val(key_l, args_l, kvargs={}, **kwargs): ### #

# alias 
# - this is being deprecated. Use arg_val() instead to gain consistency  
bool_val = arg_val



# ####################################################
def write_file(contents=[], fname="",*args, **kwargs):
    # ###############################################
    """
    purpose: can write data to a file typically as a csv file (or a .dat file) - creates a new file or appends an existing file
    requires:
        - contents: list | str | lol
        - fname: str   
    options:
        - colnames: list (adds hdr line if not currently there) NOTE: this will make append=True
        - comment_lines: str | list
        - bak: bool      # make a backup file
        - arch: dict     # see arch() - this passes fname and arch options to arch (options must be a dict)
        - indx: bool     # not used yet - future flag for adding an index col (first column) or not
        - prnt: bool     # turns on print
        - boxed: bool    # boxes the output
        - title: str
        - footer: str
        - box_color: str # color the box
        - ask: bool      # ask before actually writing data to file (before overwriting the file)
        - append: bool   # whether to append data - the default=False whereby submitted data will overwrite the file
        - dat: bool      # default: False - this is a special flag to declare that the first line (hdr) is made a comment starting it with "#"
        - raw: bool      # default: False - ignore trying to move comments around, just write the data to a file
    returns: bool        # true if successful write
    Notes:
        - only use this to write a data file = either csv (or a dat file which is a csv file with the header commented)
        - data should be a list of lists (rows of cols) if file type is dat (or csv)
        - assumes first line is comma delimited colnames or use colnames option (in a dat file the first line will be commented)
        - all comments will go to/near the top
        - if the file ends with the ".dat" extension it will be treated as a 'dat' file
        - if the file endswith ".db" and the contents are an lol it will be saved as an sqlite file
    """
    # """--== Debugging ==--"""
    # dbug(f"funcname: {funcname()} called_from: {called_from()}")
    # dbug(fname)
    # dbug(contents)
    # dbug(contents[:3])
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    prnt = arg_val(["print", "prnt", "show", "verbose"], args, kwargs, dflt=False)
    centered_b = arg_val(['centered', 'center', 'cntr'], args, kwargs, dflt=False)
    # if prnt:
        # dbug(f"funcname(): {funcname()} called_from(): {called_from()} prnt: {prnt} <-- change this after testing")
    boxed_b = arg_val(['boxed', 'box'], args, kwargs, dflt=False)
    title = arg_val(['title'], args, kwargs, dflt="")
    footer = arg_val(['footer'], args, kwargs, dflt="")
    box_clr = arg_val(['box_clr', 'box_color'], args, kwargs, dflt="")
    ask_b = arg_val(["ask"], args, kwargs, dflt=False)
    # id_flag = arg_val(["orig_id_flag", "id_flag", "indx", "idx", "id"], args, kwargs, dflt=False)
    bak_b = arg_val(["bak", "backup", "back", "bakup"], args, kwargs, dflt=True)
    # comment_lines = kvarg_val(["comment_lines"], kwargs, dflt=[])
    colnames = arg_val(["colnames", "col_names", "cols", "header", "hdr"], args, kwargs, dflt=[])
    append_b = arg_val(["append", "a", 'add'], args, kwargs, dflt=False)
    # dbug(append_b)
    dat_b = arg_val(["dat", 'dat_file'], args, kwargs, dflt=False)
    csv_b = arg_val(["csv", 'csv_file'], args, kwargs, dflt=False)
    raw_b = arg_val(["raw"], args, kwargs, dflt=False)
    arch_d = arg_val(["arch"], args, kwargs, dflt={})
    dict_b = arg_val(["dict", "dictionary"], args, kwargs, dflt={})
    # """--== Local Import(s) ==--"""
    import shutil
    import csv  # built-in
    from gtoolz import file_exists
    # import pandas as pd
    # """--== Init ==--"""
    if isinstance(contents, str):
        contents = contents.split("\n")
    comment_lines = []    # comments lines read from the file if it exists
    # file_type = "csv"   # this will either be a 'csv' or a 'dat' based on file name extension
    # raw_lines = []
    delimiter = ","
    if fname.endswith(".db") and data_type(contents, 'lol'):
        # dbug(f"{fname=} {prnt=} {called_from('v')}",'ask')
        r = put_sqlite_rows(contents, fname, prnt=prnt, arch={'days':30, 'files':25})
        return r
    if fname.endswith(".dat"):
        dat_b = True
    if fname.endswith(".csv") and not raw_b:
        csv_b = True
    # """--== Convert ==--"""
    # convert all contents to a list of either lines or rows(list of lists)
    # dbug(contents)
    if 'pandas' not in sys.modules:
        import pandas as pd
        if isinstance(contents,  pd.DataFrame):
            contents = cnvrt(contents)
    # dbug(contents[:2])
    if isinstance(contents, str):
        # dbug(repr(contents))
        if contents.startswith("[") and contents.endswith("]") and "," in contents:
            dbug("looks like a list that got turned into a string incorrectly... converting it back...I need an example here and more info")
            # data = eval(data)
            contents = [str(contents[1:-1])]
        if file_exists(contents):
            with open(fname, "r") as f:
                contents = f.readlines()
            # contents = cat_file(contents)
            # dbug(contents, 'ask')
            # dbug(type(contents))
            for line in contents:
                # grab comment lines
                if line.startswith("#"):
                    comment_lines.append(line)
    # if islod(contents):
    if data_type(contents, 'lod'):
        contents=cnvrt(contents)
    if isempty(contents):
        dbug("Contents appears to be empty... returning...")
        return
    # """--== bak / ARCH ==--"""
    if bak_b:
        bak_fname = fname + ".bak"
        if file_exists(bak_fname):
            shutil.copy(bak_fname, fname + ".prev")
            # dbug(fname)
            shutil.copy(fname, fname + ".bak")
        # dbug(f"File: {fname} has been backed up to: {fname}.bak called_from: {called_from()}", 'centered')   # start looking here
    if not isempty(arch_d):
        arch_d(fname, **arch_d)
    # """--== Write Contents ==--"""
    verb = "print"
    if file_exists(fname):
        verb = "overwrite"
    if ask_b:
        # dbug(f"funcname(); {funcname()} called_from(): {called_from()}")
        if not askYN(f"Do you want to {verb} the contents to {fname=}: ", "y"):
            return
    # dbug(raw_b)
    # dbug(append_b)
    if raw_b:
        # dbug(f"{len(contents)=} {data_type(contents)=} {contents[:2]=}")
        # dbug(append_b, 'ask')
        if append_b:
            with open(fname, "a") as f:
                f.writelines(contents) # this adds "\n" to each sting in a list of strings
        else:
            # dbug(f"{data_type(contents)=} {contents[:2]=} {islol(contents)=} {called_from('v')}")
            for n,line in enumerate(contents[:-1]):
                # 20241012 this is needed!
                if not line.endswith("\n"):
                    # dbug(line)
                    line += "\n"
                    # dbug(repr(line))
                    contents[n] = line
            # if isinstance(contents, list):
            #     # contents = "".join(contents)
            # # dbug(f"Going to write to fname: {fname}")
            with open(fname, "w") as f:
                f.writelines(contents)
    # """--== data (.dat or .csv) file?  ==--"""
    if dat_b or csv_b and not raw_b:
        # uses builtin csv tool(s)
        # dbug(f"dat_b: {dat_b} csv_b: {csv_b}")
        if dict_b:
            dbug(f"dictionary csv delimiter: [{delimiter}]")
            mywriter = csv.DictWriter(fname, fieldnames=colnames)
            mywriter.writeheader()
            mywriter.writerows(contents)
        else:
            # dbug(f"simple csv delimiter: [{delimiter}] type(contents): {type(contents)}")
            with open(fname, "w", encoding='utf-8', newline='') as csvfile:
                # mywriter = csv.writer(csvfile, delimiter=delimiter)  # , quotechar='"', quoting=csv.QUOTE_ALL)
                mywriter = csv.writer(csvfile)
                for row in contents:
                    mywriter.writerow(row)
            # dbug(f"go check fname: {fname}", 'ask', 'boxed')
        # """--== SEP_LINE ==--"""
    else:
        contents = [line if line.endswith('\n') else line + '\n' for line in contents]
        contents[-1] = contents[-1].rstrip("\n")
        with open(fname, "w") as f:
            f.writelines(contents)
    # """--== returning ==--"""
    if prnt:
        printit(f"The file fname: {fname} has been {verb}n ... with new_contents...", centered=centered_b, boxed=boxed_b, title=title, footer=footer, box_color=box_clr, prnt=prnt)
    # """--== SEP_LINE ==--"""
    # dbug(f"Returning contents[:2]: {contents[:2]}", 'ask')
    return contents
    # ### EOB def write_file() ### #


# #########################################
def isempty(my_var):  # , *args, **kwargs):
    # #####################################
    """
    purpose: tests if a variable is empty ie len(my_var) == 0 or my_var is None etc
    requires:
        - my_var: str
    options: None
    returns: bool
    """
    # """--== local imports ==--"""
    # import pandas as pd
    # """--== Debugging ==--"""
    # dbug(my_var)
    # ddbug(f"type(my_var): {type(my_var)}")
    # """--== Config ==--""" #
    # """--== Validation ==--"""
    if isinstance(my_var, dict):
        if len(my_var) == 0:
            return True
    # """--== Process ==--"""
    if isinstance(my_var, bool):
        # ddbug(f"{my_var=} is bool returning False because it has a value {called_from('v')}")
        return False
    # ddbug(f"type(my_var): {type(my_var)}")
    if 'pandas' in sys.modules:
        # ddbug("we found pandas module")
        try:
            import pandas as pd
            # if "pandas" in str(type(my_var)):  # this appears to work
                # ddbug("Looks like a pandas ... ")
            if isinstance(my_var, (pd.DataFrame,pd.core.series.Series)):
                # ddbug("this is a pandas")
                my_empty = my_var.empty
                # dbug(my_empty,'ask')
                return my_empty
        except Exception: 
            if isinstance(my_var, (pd.DataFrame,pd.core.series.Series)):
                # ddbug("this is a pandas")
                my_empty = my_var.empty
                # dbug(my_empty,'ask')
                return my_empty
    if my_var is None:
        return True
    # if "none" == str(my_var).lower().strip():
        # ddbug(f"Hit! {my_var=} lower() is none {called_from('v')} I don't like this")
        # return True
    if isinstance(my_var, list):
        # ddbug(f"type(my_var): {type(my_var)} {called_from('verbose')} my_var: {my_var}")
        if len(my_var) == 0:
            # ddbug("Returning: True")
            return True
        for elem in my_var:
            if isempty(elem):
                # dbug(f"{elem=}")
                continue
            # dbug(elem)
            if len(str(elem)) == 0:
                pass
                # dbug(elem,'ask')
            else:
                # dbug(elem)
                return False
        return True
        # for item in my_var:
        #     dbug(item)
        #     if all([isempty(elem) for elem in item]):
        #         dbug("found all elems empty... returning True")
        #         return True
    # ddbug(type(my_var))
    if isinstance(my_var, str):
        if my_var.lower().startswith("__none__") or len(my_var) == 0:
            # yes, consider this empty
            return True
        if my_var.strip() == '[]':
            # special case when web returns json data at str == "[]"
            return True
    try:
        r = bool(my_var)
    except Exception as Error:
        dbug(Error)
        dbug(type(my_var))
        # data_type(my_var)
        dbug(my_var.empty)
        dbug(my_var.info)
        return True
    return not r 
    # ### EOB def isempty(my_var):  # , *args, **kwargs): ### #


# #######################################
def gselect(selections, *args, **kwargs):
    # ###################################
    """
    purpose: menu type box for selecting by index, key, or value
    required:
    - selections: list | dictionary
        - note/caution: if a simple list of lists with every row being equal to 2 in length... then attempts will be made to convert it to a simple dictionary
    options:
        - prompt: str        # no need to include ": "
        - rtrn: str='value'  # can be 'k|key' or 'v|val|value' or "i" | "int" <-- tells gselect 
                               whether you want it to return a key or a value from a supplied list or dictionary or just user input (default)
                             # if "i"|"int" is invoked then the value of the key will return as an integer (as opposed to a string)
                This is an important option and allows control over what gets returned. See the Notes below.
        - show: str="k"      # "k|key" or 'v|val|value' <-- tells gselect whether to display a list of keys or a list of values
        - indx: bool         # whether to index (place a number before) each selection shown
        - quit: bool=False   # <-- add "q)uit" to the prompt and will do a sys.exit() if ans in ("q","Q","exit")
        - multi: bool        # <-- allows multiple selections and returns them as a list
        - all: bool=False    # to allow the user to use "a" to select all multi-choices
        - default|dflt='':   # allows you to /declare a default if enter is hit
        - cols: int=1        # default is 1 column for displaying selections
        - title: str=""
        - footer: str=""
        - color: str=""
        - box_color: str=""
        - sep: str          # default=" " but can be changed to whatever you want eg: sep="    "
        - width: int|str=0  # if this is an integer it will provide the width in columns for the gselect. 
                            # If it is a string it *must* have a "%" sign in it. The width will then become the percentage of the available screen columns 
        - cols: int=1
        - col_limit: int    # limits col length noth keys and values
        - colnames: list    # Column names to use in the header
        - timeout: int      # question will timeout after declared seconds with the default as the answer
    returns: str | list  -- either key(s) or value(s) as a *string* <---IMPORTANT  or list (if multiple), your choice
    Notes:
        - to understand this function know first that everything is turned into a dictionary first. A list would become a dictionary with  the keys being 1,2,3...
        while the original list would become the keys - this understanding will help with determining the rtrn and show options (key | val)
        - a dictionary remains as keys and values
        - with a simple list by default it will return the value in the list - if you want the menu number then use rtrn='k' option!!!
    examples:
    > tsts = [{1: "one", 2: "two", 3: "three"},["one", "two", "three"], {"file1": "path/to/file1", "file2": "path/to/file2"} ]
    > for tst in tsts:
    ...     ans = gselect(tst, rtrn="v")
    ...     ans = gselect(tst, rtrn="k")
    -----------
    To run a function using gselect - write code similar to this:
        selections = {"Clean up files": 'clean', "Copy file": 'copyfile'}
        ans = gselect(selections, rtrn="v", quit=True)
        globals()[ans]()  # this will run the function name returned .. eg: clean() or copyfile() obviously you can do a lot with this
    """
    # """--== dbug ==--"""
    # dbug(f"{called_from('v')} {args} {kwargs=}")
    # dbug(selections)
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    prompt = arg_val("prompt", args, kwargs, dflt="Please select")
    centered_b = arg_val(["center", "centered"], args, kwargs, dflt=False)
    # quiet_b = arg_val(["quiet", "silent"], args, kwargs, dflt=True)
    shift = arg_val(["shift", "shft"], args, kwargs, dflt=0)  # only works with centered option
    title = arg_val("title", args, kwargs, dflt=" Selections ")
    footer = arg_val("footer", args, kwargs, dflt="")
    default = arg_val(["dflt", "default"], args, kwargs, dflt="")
    # dbug(default)
    width = arg_val(["width", "w", "length", "len", "l"], args, kwargs, dflt=0)
    box_color = arg_val(["box_color", "bxclr", "box_clr", "bx_clr"], args, kwargs, dflt="bold white on rgb(60,60,60)")
    cols = arg_val(["cols", "columns"], args, kwargs, dflt=1)
    # sep = kvarg_val(["sep"], kwargs, dflt=f" {vc} ")
    color = arg_val(["color"], args, kwargs, dflt="white on rgb(20,20,30)")
    quit = arg_val(["quit", "exit"], args, kwargs, dflt=False)
    rtrn_type = arg_val(["rtrn"], args, kwargs, dflt="v")  # can be key|k or value|v|val or ''
    show_type = arg_val(['show', 'show_type', 'shw', 'shw_type', 'display'], args, kwargs, dflt="v")
    index_b = arg_val(["indx", "idx", "index", "indexes", 'number'], args, kwargs, dflt=False)
    multi_b = arg_val(["choose", "choices", "multi", "multiple"], args, kwargs, dflt=False)
    allow_all_b = arg_val(["all", "allow_all"], args, kwargs, dflt=True)  
    colnames = arg_val(['colnames', 'col_names', 'columns'], args, kwargs, dflt=["Choice", "Name"])
    sep = arg_val(["sep", "separation"], args, kwargs, dflt=" ")
    col_limit = arg_val(["col_limit"], args, kwargs, dflt=0)
    timeout = arg_val(['timeout', 'time'], args, kwargs, dflt=0)
    shadowed_b = arg_val(['shadowed', 'shadow'], args, kwargs, dflt=False)
    # """--== Validate ==--"""
    if selections is None:
        dbug(f"Please provide valid {selections=} {called_from('v')} returning")
        return None
    if len(selections) == 0:
        dbug(f"Nothing to process ... {selections=} {called_from('v')}... returning")
        return None
    if isinstance(selections, str):
        dbug(f"{selections=} can not be a string. They must be either a list or dictionay.. {called_from('v')} ...returning")
        return None
    # """--== Init ==--"""
    dtype = data_type(selections)
    submitted_selections = selections
    selections_d = {}
    orig_keys = []
    orig_vals = []
    # lines = []
    keys = []
    vals = []
    # dict_submitted = False
    # """--== Convert to dict... Type Mngmt ==--"""
    # dbug(f"{submitted_selections=} {dtype=}")
    if dtype in ('lol'):  # don't add 'los' to this list
        # dbug(selections[:2], 'ask')
        for row in selections:
            selections_d[row[0]] = row[1]
            orig_vals.append(row[1])
            # dbug(f"{orig_vals=} {selections=}")
    if dtype in ('dov'):
        # dbug(f"dtype: {dtype} should be 'dov'... selections: {selections} show_type: {show_type}")
        orig_keys = list(submitted_selections.keys())
        orig_vals = list(submitted_selections.values())
        # dbug(orig_vals)
        if index_b:
            if show_type == "v":
                # dbug(show_type)
                for indx, val in enumerate(orig_vals, start=1): 
                    # dbug(f"indx: {indx}, val: {val}")
                    selections_d[indx] = val
            if show_type == "k":
                for indx, key in enumerate(orig_keys, start=1): 
                    selections_d[indx] = key
        else:
            selections_d = selections
        # dbug(selections_d)
        # dbug('ask')
    # dbug(dtype)
    if dtype in ('list', 'los', "lom", "block"):
        orig_vals = submitted_selections
        # show_type = "v"
        index_b = True
        for indx, item in enumerate(selections, start=1):
            selections_d[indx] = item
        # dbug(selections_d, 'ask')
    # dbug(f"{selections_d=}  {dtype=} {called_from()}")
    selections_d = cnvrt(selections, rtrn="dov")
    # dbug(f"{selections_d=}  {dtype=} {called_from()}")
    # dbug(selections_d)
    # dbug(f"dtype: {dtype} {called_from()}")
    # """--== Fixes ==--"""
    keys = [str(key) for key in selections_d.keys()]
    vals = [str(val) for val in selections_d.values()]
    # """--== Process ==--"""
    # """--== get width ==--"""
    if "%" in str(width):
        scr_cols = get_columns()
        width = width.replace("%", "")
        width = int(scr_cols * (int(width)/100))
    # dbug(width, 'xask')
    # """--== determine prompt ==--"""
    if quit:
        prompt = prompt + " or q)uit"
    if default != "":
        prompt += f" default: [{default}] "
    if prompt.endswith(":") or prompt.endswith(": "):
        prompt = prompt.rstrip()
        prompt = prompt.rstrip(":")
    if allow_all_b and multi_b:
        prompt += " OR a)ll" 
    prompt += ": "
    # """--== SEP_LINE ==--"""
    # dbug(f"{multi_b=} {default=}", 'ask')
    # dbug(lines)
    selected_l = []
    selected_ans_l = []
    footer_l = []
    ans = "none"
    while ans not in ("q", "Q"):
        # dbug(f"{ans=} {default=}")
        if multi_b:
            if footer == "":
                footer = " Please add selections one at a time. "
                # if allow_all_b:
                    # footer += "Or a)ll"
        # dbug(selections_d)
        # dbug(shadowed_b)
        # dbug(selections_d)
        # dbug(f"{colnames=} {cols=} {width=} {sep=} {col_limit=}")
        # dbug(selections_d, 'ask')
        gtable(selections_d, 'prnt', 'hdr', centered=centered_b, pivot=True, colnames=colnames, cols=cols,
               title=title, footer=footer, width=width, box_color=box_color, shadowed=shadowed_b, sep=sep,
               col_limit=col_limit, col_colors=[""])
        if multi_b:
            # printit(f"Selected: {selected_l}", centered=centered_b, color=color)
            printit(f"Selected: {selected_ans_l}{RESET}", centered=centered_b, color=color)
        if centered_b:
            ans = cinput(prompt, center=centered_b, shift=shift, quit=quit, dflt=default, timeout=timeout)
        else:  # not centered
            # ans = cinput(prompt, centered=False, timeout=timeout)
            ans = cinput(prompt, centered=False, timeout=timeout, dflt=default)
            # if str(ans) == "":
                # ans = default
        # dbug(f"{ans=} {default=}")
        if str(ans).lower() == "a":
            # dbug(f"{rtrn_type=}")
            selected_ans_l = vals
            if rtrn_type.lower() in ('k', 'keys', 'key'):
                return keys
            if rtrn_type.lower() in ('v', 'vals', 'values', 'val'):
                return vals
        if ans in ("q", "Q", "exit", ""):
            # dbug(f"here now {ans=} {multi_b=} {default=} {ans=} {timeout=}", 'ask')
            if multi_b and len(selected_l) > 0:
                ans = selected_l
            # dbug(f"{ans=}", 'ask')
            print()  # reduce chance of misalignment of next screen print
            return ans
        if str(ans) in (""):
            # dbug("here now")
            if str(ans) == "":
                ans = default
        selected = ans
        selected_ans_l.append(ans)
        # dbug(f"{selected=} {ans=} {default=} {rtrn_type=} {keys} {vals=} {dtype=}", 'ask')
        # orig_ans = ans
        # dbug(f"{ans=} {rtrn_type=} {selected=} {multi_b=} {default=}", 'ask')
        if rtrn_type.lower() in ('k', 'keys', 'key'):
            # dbug(dtype)
            # dbug(f"{dtype=} {ans=} {rtrn_type=} {keys=}")
            if dtype in ('los', 'list'):
                if ans in keys:  # if ans is in selection keys (might be index)
                    # dbug(f"{selected=} {ans=} {default=} {rtrn_type=} {keys} {vals=}", 'ask')
                    # selected = keys[int(ans) - 1]
                    selected = keys[int(selected) - 1]
                    # dbug(selected)
            if dtype in ('dov', 'dict'):
                # dbug(f"{selected=} {ans=} {default=} {rtrn_type=} {keys} {vals=}", 'ask')
                if ans in keys:  # if ans is in selection keys (might be index)
                    # dbug(ans)
                    # selected = orig_keys[int(ans) - 1]
                    selected_keys_indx = keys.index(ans)
                    # selected = orig_keys[int(selected) - 1]
                    selected = orig_keys[selected_keys_indx]
                    # dbug(selected)
                if ans in vals:  # if ans is in selection keys (might be index)
                    selected_vals_indx = vals.index(ans)
                    selected = orig_keys[selected_vals_indx]
        else:  # rtrn_type is value (not keys)
            # dbug(f"{rtrn_type=} {vals=} {ans=} {selected=} {keys=} {orig_vals=} {index_b=} {dtype=}")
            if ans in keys and ans not in orig_vals:
                # dbug(f"{rtrn_type=} {vals=} {ans=} {keys=} {orig_vals=} {index_b=}")
                # if not isnumber(ans):
                if not isnumber(selected):
                    rtrn_type = "k"
                # ans = keys.index(ans)
                ans = keys.index(selected)
                # dbug(f"{ans=} {selected=}")
            # if ans in keys:  #  or index_b:  # if ans is in selection keys (might be index)
            if selected in keys:  #  or index_b:  # if ans is in selection keys (might be index)
                # dbug(f"{selected=} {orig_vals=} selected in keys={selected in keys:=}" )
                if isnumber(selected):
                    selected = orig_vals[int(selected) - 1]
                else:
                    # selected = orig_vals[vals.index(ans)]
                    selected_key_indx = keys.index(selected)
                    # selected = orig_vals[vals.index(selected)]
                    selected = orig_vals[selected_key_indx]
                # dbug(f"{selected=} {orig_vals=}")
            else:
                # dbug(f"{rtrn_type=} {ans=} {orig_vals=}")
                if rtrn_type == "v":
                    if isinstance(ans, int):
                        if int(keys[0]) == 1:
                            selected = orig_vals[int(ans) - 1]
                        else:
                            selected = orig_vals[int(ans)]
            # dbug(f"{selected=} {rtrn_type=} {ans=}")
        ans = str(ans)
        footer_l.append(ans)
        footer = f" Selected: {footer_l} "
        # dbug(ans)
        selected_l.append(selected)
        if not multi_b:
            break
    # dbug(f"here now {multi_b=} {default=} {ans=} {selected=}", 'ask')
    # """--== Returning ==--"""
    selected = selected_l
    if selected_l == []:
        selected = ans 
    if len(selected_l) == 1:
        # dbug(selected_l)
        selected = selected_l[0]
    # dbug(f"Returning: {selected} {default=} {multi_b=}")
    return selected
    # ### EOB def gselect(selections, *args, **kwargs): ### #


# #########################################
def cfg_val(keys=[], section="", cfg_d={}, *args, dflt="", **kwargs):
    # #####################################
    """
    purpose: to retrieve cfg val from a config_dictionary (section, key-value pair) while allowing different key name requests to get a specific key
        note: originally this was written to be called after cfg_d = handleCFG(filename)
                also if the user mixes up the order of the agements this function will attempt to figure it out
    requires:
        keys list | str  # the desired key val(s) out of a cfg_d dictionary
        section: str     # the section name to extract key vals from
                 # OR if the user only submits keys and cfg_d (which is just the section dictionary)  instead of keys, section, cfg_d (full cfg dictionary with all the scrions)
        keys: str        # if keys = a filename that exists then the syntax for this will be cfg_val(filename, section, key)
        section: str     # section name
        cfg_d: str       # again if keys is a filename this will be regarded as the key name to retreive the value
    options:
        - if section == "" or section not found then a  section named 'default' will be used
        - dflt: str|int|bool|whatever  # allows a fall-back value if none found in cfg_d (see notes below)
            if you need to type the value make sure you provide a default eg page_size = int(cfg_val(['page_lenght', 'pg_size', 'page'], sectionname, cfg_d, dflt=30))
    returns: none or default or user supplied value
    notes: if section == 'DEFAULT' | 'Default' | 'default' | 'dflt' | "" then it will be processed as 'default' section;
            This might seem like it defeats the purpose of the dflt option but it allows a cfg_d['default'] value to take precedent and allow a return even if no
                matching key(s) can be found
    use:
        cfg_d = handleCFG("/path/to/api.cfg")
        api_key = cfg_val(["api", "key", "api_key"], 'testpypi', cfg_d, dflt="1234")
        # above will find the api_key if it is defined in the file with any of the names in the list for section='testpypi'
        # or
        theme = cfg_val(["theme", "style"], 'default', cfg_d, dflt="1234")
    """
    # TODO: this needs serious refactoring
    # TODO: add an option for case insensitive key(s) match to keys in cfg_d[sections]
    # """--== Debug ==--""" #
    # dbug(called_from())
    # dbug(keys)
    # dbug(section)
    # dbug(args)
    # dbug(kwargs)
    # # """--== Config ==--"""
    section = arg_val(["section"], args, kwargs, dflt=section)
    cfg_d = arg_val(["filename", "cnfg", "config", "cnfg_d", "cfg", "cfg_d"], args, kwargs, dflt=cfg_d)
    keys = arg_val(["keys", "key"], args, kwargs, dflt=keys)
    keys_dtype = data_type(keys)
    section_dtype = data_type(section)
    # dbug(section_dtype)
    cfg_d_dtype = data_type(cfg_d)
    # dbug(cfg_d_dtype)
    # dbug(f"{keys=} {keys_dtype=} {section=} {section_dtype=} {cfg_d=} {cfg_d_dtype=}")
    # """--== when the user changes the order to look like handleCFG ie cfg_d section keys ==--""" #
    # dbug(data_type(keys))
    # dbug(f"{keys_dtype=} {keys=} {section_dtype=} {section=} {cfg_d_dtype=}")
    if keys_dtype in ('str') and section_dtype in ('los') and cfg_d_dtype in ('dod', 'doD', 'file'):  # user gave section, keys, cfg_d
        if keys in cfg_d:
            rtrn = cfg_val(section, keys,  cfg_d)
            return rtrn
    if keys_dtype in ('dict', 'file', 'doD', 'dod'): # user gave cfg_d first
        # dbug("note: normal syntax is keys: (str, list), section: (str), cfg_d: (file, dict)")
        # dbug(f"calling cfg_val({cfg_d=}, {section=}, {keys=})")
        rtrn = cfg_val(cfg_d, section, keys)
        return rtrn
    # """--== Init ==--""" #
    # dbug(cfg_d)
    rtrn_val = dflt
    # dbug(f"{rtrn_val=} {dflt}", 'ask')
    # """--== Validation ==--""" #
    if isempty(cfg_d) and isinstance(section, str):
        # dbug(type(section))
        dbug(f"No {cfg_d=}  provided and {section=} returning... {called_from('verbose')} syntax = cfg_val(['key1', 'key2'], section, cfg_d)...")
        return
    """--== fixes/convert ==--"""
    if keys_dtype in ('str', 'string'):
        keys = [keys.strip()]  # make it a list
    keys = [str(key).strip() for key in keys]  # now strip off ws
    # dbug(f"{rtrn_val=} {dflt}", 'ask')
    if isinstance(section, dict) and cfg_d == {}:
        cfg_d = section  # because section is a dictionary
        rtrn_val = ""
        # cfg_d = section
        for key in keys:
            # dbug(f"chkg for key: {key} in cfg_d: {cfg_d}")
            if key in cfg_d:
                dbug("we got a hit!")
                rtrn_val = cfg_d[key]
                # dbug(f"found key: {key} in cfg_d: {cfg_d} with val: {rtrn_val}")
                break
            else:
                for k,v in cfg_d.items():
                    if key in v:  # v may be a dictionary is k is a section
                        # dbug("But got a hit in section {k=} so we will use it")
                        rtrn_val = cfg_d[k][key]
                        break
        # dbug(f"{rtrn_val=} {dflt}", 'ask')
        if rtrn_val == "":
            rtrn_val == dflt
        if isinstance(rtrn_val, str) and rtrn_val.startswith("[") and rtrn_val.endswith("]"):
            # this is string that needs converstion to a list
            rtrn_val = re.sub(r'[\[\]]', "", rtrn_val.strip()).split(",")
            rtrn_val = [str(elem).strip() for elem in rtrn_val]
        # dbug(rtrn_val)
        # dbug(f"{rtrn_val=} {dflt}", 'ask')
        return rtrn_val
    # dbug(f"{rtrn_val=} {dflt}", 'ask')
    if isinstance(section, str):
        if section not in cfg_d:
            my_section = 'default'
    if isinstance(keys, str) and isinstance(section, str) and isinstance(cfg_d, str):
        # dbug(f"This must be file: {keys}, section: {section}, and key: {cfg_d}")
        filename = keys
        key = cfg_d
        rtrn_val = ""
        if file_exists(filename):
            cfg_d = handleCFG(filename)
            # dbug(cfg_d)
            rtrn_val = cfg_val(key, section, cfg_d)
            # dbug(rtrn_val)
        else:
            dbug(f"filename: {filename} was not found")
        # dbug(rtrn_val)
        # dbug(f"{rtrn_val=} {dflt}", 'ask')
        return rtrn_val
    # my_section = section
    # dbug(my_section)
    # dbug(cfg_d)
    # dbug(f"{rtrn_val=} {dflt}", 'ask')
    if str(section).lower() in ("", 'default', 'dflt'):
        # dbug("force section to be 'default' as it appears to be the section requested")
        my_section = 'default'
    # """--== Convert ==--"""
    if isinstance(keys, str):
        # dbug(f"turn a string keys: {keys} into a list")
        keys = [keys]
    if cfg_d_dtype in ('file'):
        cfg_d = handleCFG(cfg_d)
    # """--== SEP_LINE ==--"""
    rtrn = ""
    new_cfg_d = {}
    # dbug(f"{data_type(cfg_d)=}")
    for my_section, vals in cfg_d.items():
        my_section = str(my_section).lower()
        # dbug(f"Make sure my_section: {my_section} is 'default' if needed")
        # dbug(f"{rtrn_val=} {dflt=}", 'ask')
        if my_section in ("", 'default', 'dflt'):
            # dbug("Grabbing vals for key: default")
            new_cfg_d["default"] = vals
        else:
            # dbug(f"Grabbing vals for key: {my_section}")
            new_cfg_d[my_section] = vals
    cfg_d = new_cfg_d
    # dbug(cfg_d)
    # """--== Process ==--"""
    for key in keys:
        try:
            # dbug(f"grab the actual key: {key} value from user declared section if present")
            rtrn = cfg_d[section][key]
            break
        except Exception:
            try:
                # dbug(f"grab the default 'key': {key} if present")
                rtrn = cfg_d['default'][key]
                break
            except Exception:
                dbug(f"{rtrn_val=} {dflt}", 'ask')
                rtrn = dflt
    if isinstance(rtrn, str):
        if "," in str(rtrn):
            rtrn = rtrn.split(",")  # rtrn becomes a list
            rtrn = [x.strip() for x in rtrn]  # clean each elem up
    if isinstance(rtrn, list):
        # dbug(f"{rtrn=} {called_from('verbose')} {cfg_d=}")
        if rtrn[0][0] == "[" and rtrn[-1][-1] == "]":
            new_rtrn = []
            for elem in rtrn:
                if elem.startswith("["):
                    elem = elem[1:]
                if elem.endswith("]"):
                    elem = elem[:-1]
                new_rtrn.append(elem)
            rtrn = new_rtrn
    # dbug(rtrn)
    if not rtrn and dflt:
        rtrn = dflt
    rtrn = dequote(rtrn)
    # dbug(f"{rtrn_val=} {dflt}", 'ask')
    # dbug(f"Returning {rtrn=}  {type(rtrn)=}")
    return rtrn
    # ### EOB def cfg_val(keys, section, cfg_d, dflt=""): ### #


# ###########################
def docvars(*args, **kwargs):
    # #######################
    """
    purpose: wrapper for function to allow variable substitution within its doc
    I use this in front on a function I call handleOPTS(args)
    which works with the module docopts
    Thank you to stackoverflow.com: answered Apr 25 '12 at 1:54 senderle
    this is a very useful way to allow variables in your __doc__ strings
    wrap a function with this and use if this way
    eg:
    @docvars(os.path.basename(__file__), anotherarg, myarg="abcd")
    def myfunc():
        \"""
        Usage: {0} [-hijk]\"

        Notes:
             anotherarg: {1}
             myarg: {myarg}
        \"""
        return \"Done\"
    """
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*args, **kwargs)
        return obj
    return dec
    # ### EOB def docvars(*args, **kwargs): ### #


# ###########################
def getssid(*args, **kwargs):
    # #######################
    """
    purpose: to get the wifi SSID currently being used
    requires: nothing
    options:
        - prnt: bool
        - boxed: bool
        - centered: bool
        - netseg: bool    $ will return a list of two elements [ssid, netseg] (assumes a 255.255.255.0 mask so it adds ".*" at the end - useful with nmap)
    returns: SSID: str (or list as explained above see: netseg)
    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # from gtoolz import run_cmd, arg_val
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    boxed_b = arg_val(['boxed'], args, kwargs, dflt=False)
    centered_b = arg_val(['centered'], args, kwargs, dflt=False)
    box_clr = arg_val(['box_clr', 'bxclr', 'box_color'], args, kwargs, dflt=False)
    with_netseg = arg_val(["netseg"], args, kwargs, dflt=False)
    # """--== SEP_LINE ==--"""
    ssid = None
    # cmd = 'iwgetid'
    # if you know the <interface>.... iw dev <interface> link | awk '/SSID/{print $2}'
    cmd = 'nmcli  -t -f active,ssid dev wifi|grep yes|sed s/yes://g'
    # dbug(cmd)
    try:
        out = run_cmd(cmd)
        # dbug(out)
        # ssid = out.split('"')[1]
        ssid = out.rstrip("\n")
        # dbug(ssid)
    except Exception as Error:
        dbug(Error)
    if prnt:
        printit(f"Connected to wifi SSID: {ssid}", boxed=boxed_b, centered=centered_b, box_clr=box_clr)
    if with_netseg:
        # """--== get netseg ==--"""
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # yes, this is needed
        # dbug(s.getsockname())
        # dbug(s.getsockname()[0])
        netseg = s.getsockname()[0].rsplit(".", 1)[0] + ".*"  # The second argument 1 indicates that we want to split the string only once, at the last occurrence of the delimiter.
        # dbug(netseg)
        s.close()
        return [ssid, netseg]
    # """--== SEP_LINE ==--"""
    return ssid


# ##################################
def fix_msgs(msgs, *args, **kwargs):
    # ##############################
    """
    purpose: 'fix' an internal multiline msg = \"""  line1\n    line2\n   etc\"""  to remove preceding spaces - only works if spaces are used and not tabs (TODO)
    options:
        - lst: bool                        # option to force return msg to be a list (default is str)
        - strip_blanks: bool=False         # removes blank lines - this affects ALL blank line
        - strip_prepost_blanks: bool=True  # strips first and last line is it is blank 
    returns: 
        - msgs as a string if 'lst' not invoked without the preceding 4x" " 
    notes: 
        - this is primarily for development work - it removes preceding whitespace for every line in msgs
    """
    # """--== Config ==--"""
    lst = arg_val(["lst", "list"], args, kwargs, dflt=False)
    strip_blanks = arg_val(['strip_blanks', 'no_blanks', 'noblanks','stripblanks'], args, kwargs, dflt=False, opposite=["allow_blanks","blanks","allow"])
    # dbug(f"{kwargs=} {strip_blanks=} {called_from('v')}", 'ask')
    strip_prepost_blanks = arg_val(['strip_prepost_blanks', 'striprepostpblanks', 'strip_pre_post_blanks'], args, kwargs, dflt=True)
    # """--== SEP_LINE ==--"""
    # dtype = data_type(msgs)
    # dbug(dtype)
    if isempty(msgs):
        return msgs
    # """--== Convert ==--""" #
    if isinstance(msgs, str):
        lines = msgs.split("\n")
    # """--== SEP_LINE ==--""" #
    # printit(lines, 'boxed', title='raw msg', footer=dbug('here'))  # debugging only
    # dbug(repr(lines))
    # """--== SEP_LINE ==--""" #
    if strip_prepost_blanks:
        # dbug(strip_prepost_blanks)
        if  lines[0].strip() == "":  # if it is blank or all whitespace
            # dbug(f"removing {lines[0]=} because it is blank and strip_prepost_blanks is True")
            lines = lines[1:]
        if  lines[-1].strip() == "":  # if it is blank or all whitespace
            # dbug(f"removing {lines[-1]=} because it is essentially blank and stip_prepost_blanks is True")
            lines = lines[:-1]
    # dbug(repr(lines))
    # """--== whitespace length ??? ==--""" #
    min_ws_len = 999  # arbitrary large int min whitespace length
    for line in lines:
        if line:  # not blank
            pre_line_len = len(line)
            post_line_len = len(line.lstrip())
            delta = pre_line_len - post_line_len
            if delta < min_ws_len:
                min_ws_len = delta
    # dbug(f"{min_ws_len=}")
    pre_ws = min_ws_len * " "
    msgs = [re.sub(f"^{pre_ws}", "", ln) for ln in lines]
    # dbug(repr(lines))
    # """--== SEP_LINE ==--""" #
    if strip_blanks:
        # dbug(f"stripping blank lines {len(msgs)=}")
        msgs  = [line for line in msgs if line]
        # dbug("done stripping blank lines {len(msgs)=}")
    if not lst:
        msgs = "\n".join(msgs)
    return msgs
    # ### EOB def fix_msgs(msgs, *args, **kwargs): ### #

# alias
fix_msg = fix_msgs
fix_docstring = fix_msgs

# #################################
def dequote(elem, *args, **kwargs):
    # #############################
    """
    purpose: quick-n-dirty remove surrounding quotes
    requires:
    options:
    returns:
    notes:
        - WIP
        - 20250813-1045
    """
    # dbug(f"{elem=} {type(elem)=}")
    if not isinstance(elem, str):
        return elem
    if isempty(elem):
        return ""
    # if elem[0] in ("'",'"') and elem[-1] == elem[0]:
    if isinstance(elem, str):
        # dbug(elem)
        while elem[0] in ("'",'"') and elem[-1] == elem[0]:
            # dbug(f"dequote repr(elem): {repr(elem)}")
            elem = elem[1:-1]
            if isempty(elem):
                break
    # dbug(f"returning {elem=} {type(elem)=}")
    return elem


# ##########################################################
def hl_substring(text, substring="", color_code='\033[91m'):
    # ######################################################
    """
    purpose: color highlight a substring wihin a string
    requires:
    options:
    returns:
    notes:
        - WIP
        - 20260305-0933
    """
    # from gtoolz import parse_codes, RESET
    if text.lower().strip() == 'test':
        text = " This is a test string"
        substring = 'test'
    """Highlights a substring in text using ANSI color codes."""
    # ANSI escape codes for yellow background and black text (adjust as needed)
    highlight_start = '\033[43;30m'
    highlight_end = '\033[m'
    # Use re.sub with re.IGNORECASE flag
    # re.escape is used to handle any special regex characters in the substring; \\g<0> is a back-reference that refers to the entire matched substring, preserving its original case
    pattern = r"{}".format(re.escape(substring))
    highlighted_string = re.sub( pattern, f"{highlight_start}\\g<0>{highlight_end}", text, flags=re.IGNORECASE)
    # dbug(f"{parse_codes(highlighted_string)=}")
    return highlighted_string
    # ### EOB def hl_substring(text, substring="", color_code='\033[91m'): ### #


# #########################
def handleCFG(cfg_file="", section="", key="", *args, **kwargs):
    # #############ec#######
    """
    purpose:  if no cfg_file given it will find the default and return cfg_d (dictionary of dictioanries: cfg.sections; cfg.elem:vals)
    input: cfg_file: str
    options:
        - section: str
        - key: str
    defaults: cfg_file if it exists is: {myappname.basename}.cfg
    returns: cfg_d: dod (dictionary of dictionaries - cfg.sections with key, val pairs)
        if fname is a markdown file (extension='.md') then return = {'fm_d': front_matter_dict, 'md_content': raw_content as a str} 
    use:
        cfg_d = handleCFG("/my/path/to/myapp.cfg")
        try:
            title = cfg_d['menu']['title']
        except:
            title = ""
    """
    # TODO add global section that over-rides all of similar values
    # dbug(funcname())
    # dbug(cfg_file)
    # dbug(args)
    # dbug(kwargs)
    # """--== Imports ==--"""
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "print", "show", "verbose"], args, kwargs, dflt=False)
    my_section = kvarg_val('section', kwargs, dflt=section)
    my_key = kvarg_val(['key'], kwargs, dflt=key)
    dflt = kvarg_val(['dflt'], kwargs, dflt=None)
    # dbug(f"my_section: {my_section} my_key: {my_key}")
    file_type = arg_val(["type", "file_type"], args, kwargs, dflt="")  # can be used to force the type (be careful with this)
    # dbug(file_type)
    # """--== Init ==--"""
    if cfg_file in ('pnt','print','show','verbose'):
        prnt=True
        cfg_file = ""
    my_type = "ini"
    cfg_d = {}
    yaml_content = toml_content = ""
    # """--== Convert ==--"""
    dtype = data_type(cfg_file)
    # dbug(f"{dtype=} {cfg_file[:35]=}")
    if isinstance(cfg_file, dict):
        # dbug(f"cfg_file: {cfg_file} is probably already a dictionary so assume the user wants the section: {my_section} and key: {my_key}")
        cfg_d = cfg_file
        # dbug(cfg_d)
        # dbug(args)
        # dbug(kwargs)
        # user passed the cfg_d back probably with a section and key
        if len(my_key) > 0:
            try:
                if isinstance(my_key, str):
                    key = [my_key.strip()]
                for k in key:
                    k = k.strip()
                    # dbug(f"Chkg k: {k}")
                    rtrn = cfg_d[my_section][k]
                # rtrn = cfg_d[section][key]
                dbug(f"Returning {rtrn}")
                return rtrn
            except Exception:
                # dbug(cfg_d)
                # dbug(f"Exception Error: {repr(Error)}")
                dbug(f"Returning {dflt}")
                return dflt
    if isinstance(cfg_file, str):
        # dbug("ummm we are here", 'ask')
        if "file" in dtype:
            # dbug(f"force cfg_file to be a list")
            cfg_file = os.path.expanduser(cfg_file)
            # bname = os.path.splitext(cfg_file)[0]
            ext = cfg_file.split(".")[-1]
            my_type = ext  # <--- here we set my_type = file extention
        if "str" in dtype:
            if "\n" in cfg_file:  #let us see if this is frontmatter submitted as a str
                chk_l = cfg_file.split("\n")
                chk_l = [line for line in chk_l if line.strip()] # take out blank lines
                if chk_l[0] == chk_l[-1] and "---" in chk_l[0] or "+++" in chk_l:
                    my_type = "md"
                    # dbug(f"just changed {my_type=}")
    if isinstance(cfg_file, list):
        # dbug(f"cfg_file: {cfg_file} is apparently a list...")
        cfg_files = cfg_file
        cfg_d = {}
        for f in cfg_files:
            # dbug(f"processing file: {f} my_type: {my_type} cfg_d: {cfg_d}")
            # dbug(f)
            ext = os.path.splitext(f)[1]
            my_type = ext.lstrip(".")
            my_cfg = handleCFG(f)
            # dbug(my_cfg)
            cfg_d.update(my_cfg)
    # dbug(cfg_d, 'ask')
        # dbug(f"Returning cfg_d: {cfg_d}", 'ask')
        # return cfg_d
    # dbug(cfg_file)
    # dbug(cfg_files)
    # dbug(f"{my_type=}")  # <-- defines how to handle
    # dbug(f"{my_type=} {file_type=}", 'ask')
    # """--== Validate ==--"""
    if not file_exists(cfg_file) and 'file' in my_type:
        if prnt:
            dbug(f"Failed to find cfg_file: [{cfg_file}] ... please investigate...")
        return None
    if cfg_file == "":
        # dbug()
        inspect_filename = str(inspect.getfile(currentframe().f_back))
        inspect_filename = inspect_filename.replace("/./", "/")
        bname = inspect_filename.split(".")[0]
        # dbug(bname)
        types = ['env', 'ini', 'cfg', 'conf', 'toml', 'json', 'yaml', 'md']
        cfg_file = []
        for my_type in types:
            cfg_file.append(bname + "." + my_type)
        # dbug(cfg_file)
        # dbug(f"No cfg_filename provided cfg_file: [{cfg_file}]")
        cfg_files = []
        for f in cfg_file:  # max length of all columns
            # dbug("Test each file to see if it exists...")
            if file_exists(f):
                f = f.replace("/./", "/")
                cfg_files.append(f)
        # dbug(cfg_files)
        # cfg_file = cfg_files
        if all([file_exists(f) for f in cfg_file]):
            if prnt:
                dbug(f"cfg_file not found (cfg_file: {cfg_file})... returning None ...")
        # cfg_file = os.path.splitext(__file__)[0]
        # cfg_file += ".cfg"
        if prnt:
            dbug(cfg_file)
        if len(cfg_files) == 0:
            dbug("No cfg_file(s)... returning...")
            if askYN(f"Would you like to edit one: {bname}.toml", "y", 'centered'):
                do_edit(bname + ".toml")
            return None
        else:
            # dbug("Begin handleCFG(cfg_files) ... one or more cfg_files")
            cfg_d = handleCFG(cfg_files)
            # dbug(cfg_d)
            # dbug(f"returning {cfg_d=}", 'noask')
            return cfg_d
    # dbug(f"{my_type=} {file_type=} {cfg_d=}", 'ask')
    # """--== Markdown (aka md or markdown) ==--""" #
    if my_type.lower() == 'md' or file_type == 'md':  # type allows forcing the my_type
        # dbug(f"{my_type=} {data_type(cfg_file)=}")
        md_d = {}
        fm_d = {}
        this_content_l = []
        stat = None
        # dbug("Extract fm from content ... make cfg_d['file']['content'] = everything past the front-matter")
        # pure_content_l = purify(cfg_file, 'lst')
        # content_l = cat_file(cfg_file, 'lst')
        if 'file' not in data_type(cfg_file):
            content_l = cfg_file.split("\n")
            # dbug(content_l, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
            while content_l and not content_l[0].strip(): # remove leading blank lines
                content_l.pop(0)
            # dbug(content_l, 'prnt', 'boxed', 'ask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        else:
            with open(cfg_file, "r") as f:
                content_l = f.readlines()
        # dbug(data_type(content_l))
        # dbug(content_l, 'boxed', 'ask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        # dbug(content_l, 'ask')
        if my_type != file_type:  # file is probably not an ".md" file but we have been asked to treat it like one
            # dbug(f"{my_type=} {content_l=}")
            if not re.search(r'^\s*--+', content_l[0]):
                stat = 'content'  # it there is no front matter, just set stat = content
                # dbug("just set {stat=}")
        for line in content_l:
            # dbug(f"{stat=} {line=}")
            if stat != 'content':
                line = purify(line).strip()
            if re.search(r"^--+$", line) or re.search(r"^\+\++$", line) or re.search(r"^\=\==$", line):
                if stat is None:
                    stat = "frontmatter"
                    continue
                if stat == 'frontmatter':
                    stat = 'content'
                    # dbug(f"{line=} Must be the end of frontmatter so set {stat=} and continue")
                    continue
            if stat == 'frontmatter':
                # dbug(f"{stat=} {line=}")
                if ":" in line or "=" in line:
                    # dbug(line)
                    key, value = re.split("[:=]", line, maxsplit=1)
                    key = key.strip()
                    value = value.strip()
                    value = dequote(value.strip())
                    # dbug(value)
                    try:
                        if len(value) > 5:  # arbitrary
                            if value[0] == "{" and value[-1] == "}":
                                # import ast
                                value = ast.literal_eval(value)
                                # dbug(value)
                    except Exception as Error:
                        dbug(f"{Error=} {called_from('v')} {value=}")
                    fm_d[key.strip()] = value
                    # dbug(f"{value=} {md_d=} {fm_d[key.strip()]=}")
                else:
                    continue
            if stat == 'content':
                this_content_l.append(line)
        # dbug(fm_d)
        # kvcols(fm_d, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        # """--== EOB for line in content_l  ==--""" #
        md_d['fm_d'] = fm_d
        if fm_d:
            md_content = "".join(this_content_l)  # turn it into a string - it is currently a list of strings with newlines!?
        else:
            md_content = "".join(content_l)  # turn it into a string
        # dbug(md_content, 'prnt', 'boxed', 'ask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        md_d['md_content'] = md_content
        # else:
            # md_d['md_content'] = "\n".join(content_l)
        # if "---" in content_l[0]:
        #     # dbug("looks like yaml")
        #     my_type = 'yaml'
        # if "+++" in content_l[0]:
        #     # dbug("looks like toml")
        #     my_type = 'toml'
        # sec_sep = content_l[0]
        # """--== return ==--""" #
        # dbug(f"{cfg_file=} returning {md_d=} {my_type=}")
        return md_d
    # """--== env type ==--""" #
    # dbug(f"{called_from('verbose')}", 'ask')
    if my_type.lower() == 'env':
        content_l = purify(cfg_file, 'lst')
        # dbug(content_l)
        cfg_d = {'env':{}}
        for ln in content_l:
            if re.search(r'[=:]', ln):
                # dbug(ln)
                var, value = re.split("[=:]", ln, maxsplit=1)
                value = dequote(value)
                # dbug(f"{var=} {value=}")
                cfg_d['env'][var] = value
                # dbug(cfg_d, 'ask')
    # """--== cfg file (CFG File CFG_FILE) ==--""" #
    if my_type.lower() in ("ini", "cfg", "conf"):
        # dbug(f"{my_type=} {cfg_file=} {called_from('v')}")
        # """--== experiment my way instead of configparser ==--""" #
        lines = cat_file(cfg_file, 'lst', purify=True)
        if not lines:
            dbug("Apologies... found nothing in {cfg_file=}... returning...")
            return
        lines = [line for line in lines if re.search(r"\[.*?\]|[=:]", line)]
        # dbug(lines)
        section = ""
        # my_dname = ""
        multi_line = ""
        cfg_d = {}
        section_pat = r"^\s*\[(.*?)\]\s*$"   # <-- section pattern
        if not any(re.search(section_pat, line) for line in lines):
            # if no [section] exists insert [default] as first line
            lines.insert(0, "[default]")
        # dbug(lines, 'boxed')
        for line in lines:  # <-- start for loop
            line = line.strip()
            if not line:  # if line is blank
                continue
            section_match = re.search(section_pat, line)
            if section_match:
                # dbug(m.group(1))
                section = section_match.group(1).lower()
                cfg_d[section] = {}
            else:
                if section:
                    phrases = []
                    value = ""
                    # dbug(f"{line=} {multi_line=} {key=} {value=}")
                    if multi_line:
                        multi_line += line
                    # if not multi_line and line.endswith(("]","}")):
                    #     dbug(f"{line=} {multi_line=}")
                    #     value = multi_line 
                    #     multi_line = ""
                    #     # dbug(f"end of {multi_line=} {value=} {line=}")
                    #     continue
                    # dbug(f"processing {section=} {line=} {multi_line=} {value=}")
                    if not multi_line:
                        phrases = re.split(r"[=:]", line, maxsplit=1)  # <-- note the maxsplit
                    # dbug(f"{line=} {phrases=}")
                    if len(phrases) > 1:  # <-- we found a "=" or ":" symbol but there may be more 
                        key = phrases[0].strip()
                        value = phrases[1]
                        value = dequote(value)
                        value = value.strip()
                        # dbug(f"{line=} {multi_line=} {key=} {value=}")
                        if multi_line and value.endswith(("}","]")):
                            value = multi_line
                            multi_line = ""
                            # dbug(f"{line=} {multi_line=} {key=} {value=}", 'ask')
                        if value.startswith(("{","[")):
                            if not value.endswith(("}", "]")):
                                multi_line += value
                                # dbug(f"{line=} {multi_line=} {key=} {value=}", 'ask')
                                if not multi_line.endswith(("}","]")):
                                    # dbug(f"{line=} {multi_line=} {key=} {value=}", 'ask')
                                    continue
                                else:
                                    # dbug(f"{line=} {multi_line=} {key=} {value=}", 'noask')
                                    value = multi_line
                                    multi_line = ""
                                    # dbug(f"{line=} {multi_line=} {key=} {value=}", 'ask')
                        # dbug(f"{line=} {multi_line=} {key=} {value=}", 'ask')
                    else:
                        if multi_line:
                            value = multi_line + line
                            if value.endswith("}"):
                                multi_line = ""
                            else:
                                continue
                        else:
                            value 
                        # dbug(f"{line=} {multi_line=} {key=} {value=}", 'ask')
                    # dbug(f"{line=} {multi_line=} {key=} {value=} {section=}", 'ask')
                    # value = ast.literal_eval(value)
                    cfg_d[section][key] = value
                    # dbug(f"{cfg_d[section][key]=}")
                    # dbug("Looping back for another line...============================")
        # """--== SEP_LINE ==--""" #
        # dbug(cfg_d)
        for k,v in cfg_d[section].items():
            # dbug(f"chkg {k=} {v=}") 
            if ( str(v).startswith("[") and str(v).endswith("]") ) or ( str(v).startswith("{") and str(v).endswith("}") ):
                my_v = ast.literal_eval(v)
                # dbug(f"{v=} {type(v)=}{my_v=} {type(my_v)=}")
                cfg_d[section][k] = my_v
        # gtable(cfg_d, 'prnt' , 'ask', title='debugging', footer=dbug('here'))
    # """--== json ==--""" #
    if my_type.lower() == 'json':
        import json
        # dbug("begin to do json")
        json_content = cat_file(cfg_file, rtrn='str')
        # dbug(json_content)
        # dbug(data_type(json_content))
        # if not isinstance(json_content, str):
            # json_dtype = data_type(json_content)
            # dbug(json_dtype)
            # dbug(json_content)
            # dbug('ask')
        # dbug(json_content)
        if isinstance(json_content, list):
            json_content = "\n".join(json_content)
        cfg_d = json.loads(json_content)
        # dbug(f"do_json cfg_d: {cfg_d}")
    # """--== yaml ==--""" #
    if my_type.lower() == 'yaml':
        import yaml
        # dbug(cfg_file)
        yaml_content = cat_file(cfg_file, rtrn='str')
        if isinstance(yaml_content, list):
            yaml_content = "\n".join(yaml_content)
        cfg_d = yaml.safe_load(yaml_content)
        # dbug(f"do_yaml cfg_d: {cfg_d}")
    # """--== toml ==--""" #
    if my_type.lower() == 'toml':
        # dbug("Importing toml")
        import toml
        if not toml_content:
            cfg_d = toml.load(cfg_file)  # , _dict=dict) #  f=f|[f,f,...]
        else:
            cfg_d = toml.load(toml_content)  # , _dict=dict) #  f=f|[f,f,...]
        # or toml.loads(s, _dict=dict) s=string  _dict specifies return class
        # dbug(f"toml cfg_d: {cfg_d}", 'ask')
    # """--== SEP_LINE ==--"""
    # dbug(cfg_d, 'ask')
    if my_section != "":
        if my_section in list(cfg_d.keys()):
            cfg_d = cfg_d[my_section]
        else:
            dbug(f"my_section:{my_section} not found in list(cfg_d.keys():{list(cfg_d.keys())}")
            return
    if my_key != "":
        # kv_cols(cfg_d, 4, 'prnt', title="debugging", footer=dbug('here'))
        if my_key in cfg_d:
            cfg_d = cfg_d[my_key]  # assumes section done above
        else:
            dbug(f"Failed to find my_key: {my_key}")
            return
    # dbug(f"Returning: {cfg_d} using file: {cfg_file} my_type: {my_type} EOB")
    # """--== Now let's turn what looks like a list into a python list ==--""" #
    # dbug(f"{cfg_d=} is a dict {called_from('verbose')}")
    pat = r'(\[.*?\])'
    if isinstance(cfg_d, dict):
        # dbug(f"{cfg_d=} is a dict {called_from('verbose')}")
        pat = r'(\[.*?\])'
        new_cfg_d = {}
        for k, v in cfg_d.items():
            new_val = {}
            if isinstance(v, dict):
                # dbug(v)
                for my_k, my_v in v.items():
                    # dbug(f"{pat=} {my_v=}")
                    mtch = re.search(pat, str(my_v))
                    if mtch:
                        my_l = str(my_v)[1:-1].split(",")
                        my_v = [elem.strip() for elem in my_l]
                    new_val[my_k] = my_v
            else:
                new_val = v
            new_cfg_d[k] = new_val
        # dbug(new_cfg_d, 'ask')
        cfg_d = new_cfg_d
    if isinstance(cfg_d, str):
        # dbug(f"{cfg_d=} is a str {called_from('verbose')}")
        mtch = re.search(pat, cfg_d)
        if mtch:
            cfg_d = eval(mtch.group(1))
    # """--== Return ==--""" #
    # dbug(f"returning {cfg_d=}")
    return cfg_d
    # ### EOB def handleCFG(cfg_file=""): ### #


def browseit(url="http://localhost/", *args, **kwargs):
    """
    purpose: opens the url/file in your browser
    requires: url: str  # can be content or a filename
    options: 
        - fname: str    # filename to save html to
        - prnt: bool=False
        - edit: bool=False
        - use_py: bool=False  # two ways to browse using your web-browser (perhaps better for remote) or using python http.server (perhaps better for local)
            - single: bool=False  # set the python browse to close as soon as the user leaves the open broswed page
    returns: none
    notes: none
    """
    # """--== Imports ==--"""
    import webbrowser
    import http.server
    import socketserver
    # """--== Debugging ==--"""
    dbug(f"{args=} {kwargs=} {called_from('v')}")
    # """--== Config ==--""" #
    prnt = arg_val(["prnt", "print", "show", "verbose"], args, kwargs, dflt=False)
    fname = arg_val(["fname","file","filename"], args, kwargs, dflt="tmp.html")
    use_py_b = arg_val(['use_py', 'py', 'python'], args, kwargs, dflt=False)
    edit_b = arg_val(['edit'], args, kwargs, dflt=False)
    single_b = arg_val(['single'], args, kwargs, dflt=True)
    # """--== Validation ==--""" #
    if isempty(url):
        dbug(f"{url=} appears to be empty...{called_from('v')}... returning...")
        return
    # """--== Process ==--"""
    # webbrowser.open_new(url)
    # dtype = data_type(url)
    # dbug(dtype)
    if not file_exists(url) and "\\:\\/\\/" not in url:
        # dbug("treat as html text")
        if isinstance(url, list):
            url = "\n".join(url)
        with open(fname, 'w') as f:
            # dbug(f"writing to {fname=}")
            f.write(url)
        if prnt:
            cat_file(fname, 'prnt')
        url = fname
    dbug(f"{url=} {use_py_b=} {called_from('v')} ")
    if edit_b:
        do_edit(fname)
    if not use_py_b:
        webbrowser.open(url, new=0)
    if use_py_b:
        PORT = 8000
        # Create the request handler (this is what python -m http.server uses under the hood)
        Handler = http.server.SimpleHTTPRequestHandler
        # Set up the server to listen on all interfaces (0.0.0.0) at your specified port
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Serving HTTP on local network at http://localhost:{PORT}")
            try:
                # Keep the server running forever until manually interrupted
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped running.")
        # PORT = 8000
        # class MyHandler(http.server.SimpleHTTPRequestHandler):
        #     def do_GET(self):
        #         # Redirect the root request to your specific filename
        #         if self.path == '/':
        #             self.path = url
        #         return super().do_GET()
        # with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        #     dbug(f"Serving foobar.html at [yellow!] http://localhost:{PORT} [/]", 'boxed')
        #     if single_b:
        #         httpd.handle_request()
        #     else:
        #         httpd.serve_forever()


@docvars(os.path.basename(__file__))
def handleOPTS(args):
    """
    Usage:
        {0} -h
        {0} -T <func> [<fargs>...]
        {0} -E
        {0} --version
        {0} --docs
        {0} <cmd> [<fargs>...]
        {0} --arch

    Options
        -h, --help             Help
        -v, --version          Prints version
        -T <func> [<fargs>]    runs specified func with optional args=fargs, primarily for development
        -E                     edit this file
        --docs                 allows to user to display the doc for selected function
        <cmd> [farg farg] ...] function arg, arg, arg ... (when used at command line, ie: {0}-cli, prnt is always assumed to be true)

    """
    # dbug(args, 'ask')
    if args['-T']:
        """
        This is to test a single function
        Put this in Usage section:
          {0} -T <funcname> [<fargs>...]
        You can use this while you are editing... in vim: <ESC>:! ./% -T your_function <args>
        """
        # dbug(funcname())
        # dbug(args)
        if isinstance(args['-T'], bool):
            fname = args['<func>']
        else:
            fname = args['-T']
        def get_args(string):
            # dbug(f"fname(): {fname} string: {string}")
            if isinstance(string, str):
                my_args = string.split(',')
                my_args = [my_arg.strip() for my_arg in my_args]
            else:
                my_args = []
            new_args = []
            my_kwargs = {}
            for my_arg in my_args:
                if '=' in my_arg:
                    key, val = my_arg.split('=')
                    my_kwargs[key.strip()] = val.strip()
                    # dbug(my_kwargs)
                else:
                    new_args.append(my_arg)
            # dbug(f"Returning my_args: {new_args} and my_kwargs: {my_kwargs}")
            rtrn_d = {'args': new_args, 'kwargs': my_kwargs}
            return rtrn_d
        # fargs = "".join(fargs)
        fargs = args['<fargs>']
        if isinstance(fargs, list):
            # for arg in fargs:
            fargs = "".join(fargs)  # turn it into a str 
        args_d = get_args(fargs)
        # dbug(args_d)
        # dbug(args_d)
        # dbug(f"{fname=}")
        if args_d is None:
            globals()[fname]()
        else:
            if args_d['kwargs'] is None:
                globals()[fname](*args_d['args'])
            else:
                globals()[fname](*args_d['args'], **args_d['kwargs'])
        # dbug('ask')
        do_close()
        # """--== SEP_LINE ==--"""
    # """--== edit __file__ ==--"""
    if "-E" in sys.argv:
        global FULL_PATH_SCRIPT
        # dbug(FULL_PATH_SCRIPT, 'ask')
        do_edit(FULL_PATH_SCRIPT)  # I do not know why but in this module __file__ get lost... ???
        do_close()
    if args['--docs']:
        get_mod_docs()
    # dbug("Returning None")
    return None
    # ### EOB def handleOPTS(args): ### #


def get_args(arg_s):
    """
    purpose: parses string into *args and **kwargs
    notes: called by do_cli()
    """
    if isempty(arg_s):
        arg_s = ""
    if isinstance(arg_s, list):
        arg_s = ",".join(arg_s)
    if not isinstance(arg_s, str):
        dbug(f"args_s: {arg_s} should be a string type(args_s): {type(arg_s)}")
        return
    args_l = arg_s.split(",")
    new_args_l = []
    new_kwargs_d = {}
    for arg in args_l:
        if "=" in arg:
            # dbug(arg)
            key, val = arg.split("=")
            key = key.strip()
            # if key.endswith("'") and key.startswih("'"):
            #     key = key.strip("'")
            if val.startswith('"') and val.endswith('"'):
                val = val.strip('""')
            # dbug(val)
            if val.startswith("'") and val.endswith("'"):
                val = val.strip("'")
            # dbug(key)
            # dbug(val)
            new_kwargs_d[key] = val
        else:
            # dbug(arg)
            arg = arg.strip()
            # dbug(arg)
            if arg.startswith('"') and arg.endswith('"'):
                arg = arg.strip('""')
            # dbug(arg)
            if arg.startswith("'") and arg.endswith("'"):
                arg = arg.strip("'")
            # dbug(arg)
            arg = arg.strip()
            # """--== deal with a possible list ==--"""
            if arg.startswith('['):
                arg_l = [arg.lstrip("[")]
                continue
            if arg.endswith("]"):
                arg_l.append(arg.rstrip("]"))
                # dbug(arg_l)
                arg = arg_l
            # dbug(arg)
            # """--== EOB ==--"""
            new_args_l.append(arg)
    rtrn_d = {'args': new_args_l, 'kwargs': new_kwargs_d}
    # dbug(f"Returning rtrn_d: {rtrn_d}")
    return rtrn_d
    # ### EOB def get_args(arg_s): ### #


# ############################
def centered(msgs, *args, **kwargs):
    # ########################
    """
    purpose: calculates screen placement for msgs: list|str
    options:
        length=columns: int
        shift=0: int
        'str'|'string'=False: bool
        'lst'|'list'=True: bool
    returns: line|lines
    note: replaces deprecated centerit()
    """
    # this function needs serious refactoring 20240630
    # """--== Debugging ==--"""
    # dbug(called_from('v'))
    # dbug(msgs)
    # dbug(kwargs)
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    shift = kvarg_val('shift', kwargs, dflt=0)
    length = kvarg_val(['length'], kwargs, dflt=0)  # canvas columns instead of screen columns
    width = kvarg_val(["width"], kwargs, dflt=0)  # rarely used; different from length which is for canvas instead of screen columns
    # dbug(f"length: {length} width: {width}")
    if width > length:
        length = width
    # dbug(f"length: {length} width: {width}")
    lst = arg_val(['lst', 'list'], args, kwargs, dflt=True)
    string_b = arg_val(['str', 'string'], args, kwargs, dflt=False)
    pad = kvarg_val(["pad"], kwargs, dflt=" ")
    # dbug(f"pad: [{pad}]")
    # margin = 0
    # """--== Validation ==--"""
    if msgs is None:
        dbug(f"msgs: {msgs} appear to be empty... {called_from('verbose')} returning")
        return None
    if not isinstance(shift, int):
        shift = 0
    if not isinstance(length, int):
        length = 0
    if isinstance(msgs, str) and "\n" not in msgs:
        margin = ' ' * int((length-len(msgs))/2) 
        msgs = margin + msgs + margin
        if len(msgs) < length:
            msgs = msgs + ' ' * (length - len(msgs))
        # dbug(len(msgs))
        # dbug(length)
        # dbug(msgs)
        string_b = True
    # """--== Init ==--"""
    # dtype = data_type(msgs)
    # dbug(dtype)
    # reset = sub_color("reset")
    if length == 0:
        # dbug(shift)
        # scr_columns = get_columns(shift=shift)
        scr_columns = get_columns()
        # dbug(scr_columns)
        # scr_columns = get_columns(shift=0)
        # dbug(scr_columns)
        length = scr_columns
    l_pad_len = 0
    # """--== Process ==--"""
    if isinstance(msgs, str):
        msgs = [msgs]
    msgs_max_len = maxof(msgs)
    # dbug(msgs_max_len)
    if msgs_max_len > int(width) and int(width) > 10:  # arbitrary
        # msgs = wrapit(msgs, length=int(width))
        msgs = gwrap(msgs, length=int(width))
    lines = []
    # dbug(msgs)
    for line in msgs:
        # dbug(line)
        # line_dtype = data_type(line)
        # dbug(line_dtype)
        # dbug(len(line))
        if isinstance(line, list) and len(line) == 1:
            # dbug(line_dtype,'ask')
            # looks like printit will center a title and footer line and it will be a single elem in a list???
            # so this fixes it but it really should be fixed in printit... TODO
            # hmmm tried doing this in printit and it breaks things
            line = line[0]
            lines.append(line)
            # dbug(f"Just appended line: [{line}]")
        else:
            # dbug(f"{len(line)=} {line=} {nclen(line)=} {length=} {scr_columns=}")
            if isinstance(line, str):
                # dbug(length)
                # dbug(length)
                line_len = parse_codes(line, 'nclen')
                l_pad_len = (length - line_len) // 2
                # dbug(f"{len(line)=} {line=} {nclen(line)=} {length=} {scr_columns=} {shift=} {l_pad_len=}")
                # dbug(f"{l_pad_len=} before {shift=} {nclen(line)=}")
                l_pad_len += shift  # remember that shift will most likely be a negative value
                # dbug(f"{l_pad_len=} after {shift=} {nclen(line)=}")
                l_pad = pad * l_pad_len
                # dbug(line)
                # dbug(f"{l_pad=}")
                # ruleit()
                line = l_pad + line
                # dbug(line)
                lines.append(line)
            # else:
                # dbug(f"WHAT is this {line=} {line_dtype=}")
            # dbug(len(line))
    if not lst or string_b:
        rtrn = "".join(lines)
    else:
        rtrn = lines
    # dbug(lines)
    if prnt:
        printit(rtrn)
    # dbug(f"{called_from('verbose')}",'ask')
    return rtrn
    # ### EOB def centered(msgs): ### #


# #############
def ruleit(*args, **kwargs):
    # #########
    """
    purpose: This is for development purposes
        It draws a rule across the screen and that is all it does
        It fails to prepare your meals or schedule your week\'s agenda, sorry.
    options:
        - width: int     # default=0     - truncates at this len otherwise it is screen length
        - cntr: bool     # default=False - provide center info
        - prnt: bool     # default=True  -  whether to print
    returns: printed ruler line with tick marks and marker numbers below
    """
    # """--== Config ==--"""
    width = kvarg_val(["width", "w", "length", "l"], kwargs, dflt=0)
    cntr = arg_val(["cntr", "center"], args, kwargs, dflt=False)
    prnt = arg_val(["prnt", "print"], args, kwargs, dflt=True)
    # """--== Init ==--"""
    line = ""
    tick_line = ""
    mark_line = ""
    # lines = []
    new_lines = []
    if width == 0:
        columns = get_columns()
        cols = int(columns)
    else:
        cols = int(width)
    cntr = cols / 2
    # iters = int(floor(int(cols)) / 10)
    my_iters = cols // 10
    # dbug(my_iters)
    markers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    # """--== Process ==--"""
    print(RESET)  # get rid of any lingering color
    # diff = int(columns) % 10
    diff = int(cols) % 10
    for i in range(0, my_iters):
        for x in range(0, 10):
            actual_num = (i * 10) + x + 1
            # dbug(f"i: {i} x: {x} actual number: {actual_num}")
            if prnt:
                marker = markers[x]
                if actual_num == cntr:
                    marker = gclr("red", text=marker, reset=True)
                print(marker, end="")
            line += str(markers[x])
    for i in range(0, diff):
        # dbug(i)
        if prnt:
            print(markers[i], end="")
        line += str(markers[i])
    if prnt:
        print()
    for i in range(0, my_iters):
        for x in range(0, 10):
            # dbug(x)
            if x == 9:
                if prnt:
                    print("|", end="")
                tick_line += "|"
            else:
                if prnt:
                    print(" ", end="")
                tick_line += " "
    if prnt:
        print()
    cnt = 10
    new_lines.append(line)
    new_lines.append(tick_line)
    for i in range(0, my_iters):
        for x in range(0, 10):
            if x == 0:
                pad = " "
                # dbug(cnt)
                # dbug(str(cnt))
                padding = 10 - len(str(cnt))
                # dbug(padding)
                fill = padding * pad
                # dbug(f"fill: [{fill}]")
                if prnt:
                    print(fill + str(cnt), end="")
                mark_line += fill + str(cnt)
                cnt += 10
                if cnt > width:
                    break
    # dbug(mark_line)
    new_lines.append(mark_line)
    if prnt:
        print()
    if cntr:
        # cntr = cols / 2
        printit(f"cols/length: {cols} The center is: {cntr} marked in red", 'centered', width=width)
        return cntr
    return new_lines
    # ### EOB def ruleit(): ### #


# ######################################
def do_close(msg="", *args, **kwargs):
    # ##################################
    """
    purpose: to provide a boxed closing message default msg is below
    options:
        - box_clr: str           # color of main box
        - quote: str             # should a random quote from filename provided be included
        - quoote_box_color: str  # box color for quote default="White! on black"
        - centered: bool         # center the output on the screen
        - shadowed: bool         # should the box(es) be shadowed
        - figlet: bool           # use figlet to decorate msg
    returns: None
    # dflt_msg = "Enjoy!"
    input msg or it uses dflt_msg
    options: 'center' | 'centered' color='red' rc=return code to exit with
    >>> do_close()
        ======
        Enjoy!
        ======
    """
    # TODO merge this with do_logo() and call it do_msg?
    # """--== Debugging ==--"""
    # dbug(funcname)
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    quote = kvarg_val('quote', kwargs, dflt="")
    quote_box_color = kvarg_val(["qbox_clr", "quote_box_color", "quote_box_clr"], kwargs, dflt="white! on black")
    centered = arg_val(['center', 'centered'], args, kwargs, dflt=True)
    txt_center = kvarg_val(['txt_center', 'txt_cntr', 'text_center', 'cntr_txt', 'txt_centered'], kwargs, dflt=0)
    color = kvarg_val(['color', 'clr'], kwargs, dflt="")
    shadowed = arg_val(['shadow', 'shadowed'], args, kwargs)
    box_color = kvarg_val(["box_clr", 'box_color', "bx_clr", "bxclr", 'boxclr'], kwargs, dflt="")
    figlet = arg_val(['figlet'], args, kwargs)
    footer = kvarg_val(['footer', 'ftr'], kwargs, dflt="")
    exit_b = arg_val(['exit', 'quit', 'ext'], args, kwargs, dflt=True)
    # """--== Init ==--"""
    dflt_msg = "Wanted: Software Developer. Python experience is a plus. Pay commensurate with skill set. Apply within."
    # dflt_msg = "All is well that ends well!"
    # """--== Process ==--"""
    if msg == "":
        msg = dflt_msg
    if figlet:
        from pyfiglet import figlet_format
        msg = figlet_format(msg, width=1000)
    if footer == "":
        footer = f"{RESET}{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    # dbug("going to printit")
    printit(msg + RESET, 'boxed', footer=footer, center=centered, shadow=shadowed, box_color=box_color, color=color, txt_center=txt_center)
    # dbug('ask')
    if quote != "":
        # quote needs to be a path/filename -- path can include "~/" for $HOME
        # dbug(quote)
        if isinstance(quote, str):
            file = os.path.expanduser(quote)
        else:
            dbug(f"quote: {quote} must be a valid filename: str containing quote lines", 'centered')
            return None
        quote_msg = get_random_line(file)
        if isempty(quote_msg):
            quote_msg = f"No quote found from quote: {quote}"
        # quote_msg = wrapit(quote_msg, length=80)
        quote_msg = gwrap(quote_msg, length=80)
        printit(quote_msg, 'boxed', title=" Quote ", box_color=quote_box_color, centered=centered, shadow=shadowed, color=color)
    if exit_b:
        sys.exit()
    # ### EOB def do_close(msg="", *args, **kwargs): ### #


# ###################################
def convert_temp(temp, convert2="f"):
    # ###############################
    """
    purpose: convert from Celsius to Fahrenheit or vice versa
    expects: a string with either an ending.lower() of "f" or "c" to declare what to return
    returns: rounded(converted_temp)
        always returns a string with 2 places (including 0s)
    """
    temp = str(temp)
    if convert2.lower() == "f":
        # this seems counter intuitive but it tells the func that the float(temp) is currently Celcius so convert it
        temp = temp + "c"
    if convert2.lower() == "c":
        # this seems counter intuitive but it tells the func that the float(temp) is currently Fahrenheit so convert it
        temp = temp + "f"
    if temp.lower().endswith("f"):
        # convert to Celcius
        temp = float(temp[:-1])
        temp_C = (temp - 32) / 1.8
        converted_temp = temp_C
        temp_C = round(float(converted_temp), 2)
        return(f"{converted_temp:.2f}")
    if temp.lower().endswith("c"):
        # convert to Fahrenheit
        temp = float(temp[:-1])
        temp_F = (temp * 1.8) + 32
        converted_temp = temp_F
        converted_temp = round(float(converted_temp), 2)
        return(f"{converted_temp:.2f}")
    else:
        dbug("temp must end with [CcFf] or declare ForC=[FfCc]")
        return None
    # ### EOB def convert_temp(temp, convert2="f"): ### #


# #############################################
def do_logo(content="", *args, **kwargs):
    # #########################################
    """
    purpose: presents a boxed logo for the begining of a program
    requires: nothing but you should provide some default content: str|list
    options: 
        - content: str | list,  # can be a file name - by default this looks in /usr/local/etc/logo.nts 
        - prnt: bool, 
        - figlet: bool, 
        - center: bool, 
        - center_txt: int  # default=0 <--you may want to change this... number of lines to center text within the logo box
        - shadow: bool, 
        - box_color: str, 
        - color: str, 
        - fotune: bool <-- requires the fortune app
        . quote: str   <-- requires a filename with quote lines within it - one line from the file will be randomly selected
    if content = "" and /usr/local/etc/logo.nts does not exist then we use "Your Organization Name"
    if content == "" then open default file: /usr/local/etc/logo.nts
    if content is a filename then use the lines in that file
    if content is a str and not a file then use pyfiglet to turn it into ascii letters of print lines
    """
    # dbug(f"{called_from('v')} {content=}")
    # dbug(args)
    # dbug(kwargs)
    # dbug(center)
    # """--== Config ==--"""
    center = arg_val(['center', 'cntr', 'centered'], args, kwargs, dflt=True)
    center_txt = kvarg_val(['cntr_txt', 'center_txt', 'center_text', 'cntr_txt', 'txt_cntr', 'cntrtxt', 'txtcntr'], kwargs, dflt=0)
    # dbug(center_txt)
    shadow = arg_val(['shadow', 'shadowed'], args, kwargs, dflt=False)
    quote = kvarg_val('quote', kwargs, dflt="")
    fortune = arg_val('fortune', args, kwargs)
    color = kvarg_val('color', kwargs)
    box_color = kvarg_val(['box_color', 'box_clr', 'bxclr', 'boxclr'], kwargs)
    prnt = arg_val('prnt', args, kwargs, dflt=True)
    title = kvarg_val('title', kwargs, dflt="")
    footer = kvarg_val('footer', kwargs, dflt="")
    figlet = arg_val('figlet', args, kwargs, dflt=False)
    # """--== Convert ==--"""
    if "\n" in content:
        content = content.split('\n')
    if isinstance(content, list):
        lines = content
    else:
        lines = [content]
    # dbug(lines)
    if isinstance(content, str) and content == "":
        filename = "/usr/local/etc/logo.nts"
        if file_exists(filename):
            with open(filename) as f:
                lines = [line.rstrip() for line in f]
        else:
            lines = ["Your Organization Name", dtime]
    else:
        if isinstance(content, str) and file_exists(content):
            dbug(content)
            with open(content) as f:
                lines = [line.rstrip() for line in f]
        else:
            # dbug(lines)
            if figlet:
                # dbug("found pyfiglet")
                try:
                    from pyfiglet import figlet_format
                    lines = figlet_format(content, width=1000)
                except Exception:
                    pass
            # else:
            #     lines.append(content)
    if len(lines) < 1:
        dbug(f"Problem: nothing to print lines: {lines}")
    if isinstance(lines, str):
        lines = lines.split("\n")
    # """--== Process ==--"""
    lines = printit(lines, 'boxed', box_color=box_color, title=title, footer=footer, color=color, shadow=shadow, prnt=False, center_txt=center_txt)
    if fortune:
        cmd = "fortune -s"
        out = run_cmd(cmd)
        if isempty(out):
            out = f"Nothing returned fron cmd: {cmd}... please check."
        f_box = printit(out, "boxed", title=" Fortune ", prnt=False, box_color=box_color, color=color, shadow=shadow)
    if quote != "":
        # quote needs to be a path/filename -- path can include "~/" for $HOME
        if isinstance(quote, str):
            file = os.path.expanduser(quote)
        else:
            dbug(f"quote: {quote} must be a valid filename: str containing quote lines", 'centered')
            return None
        quote_msg = get_random_line(file)
        # quote_msg = wrapit(quote_msg, length=80)
        quote_msg = gwrap(quote_msg, length=80)
        if isempty(quote_msg):
            quote_msg = f"Nothing returned from quote: {quote}"
        q_box = printit(quote_msg, 'boxed', title=" Quote ", prnt=False, shadow=shadow, box_color=box_color, color=color)
    if quote or fortune:
        lines.append("   ")
    if quote and fortune:
        columns = [f_box, q_box]
        boxes_l = gcolumnize(columns, color=color)  # color affects the 'fill color'
        boxes = boxed(boxes_l, box_color=box_color, color=color, shadow=shadow, top_pad=1, bottom_pad=1, cbtr_txt=99)
        # dbug(lines)
        # printit(boxes)
        # dbug('ask')
        lines.extend(boxes)
    else:
        if fortune:
            lines.extend(f_box)
        if quote:
            lines.extend(q_box)
    if prnt:
        printit(lines, center=center)
    # dbug("returning...", 'ask')
    return lines
    # ### EOB def do_logo(content="", *args, hchr="-", prnt=True, figlet=False, center=True, box=True, shadow=False, color='red', **kwargs): ### #


# #########
def cls():
    # #####
    """
    purpose: Clears the terminal screen.
    returns: None
    """
    import platform
    # Clear command as function of OS
    command = "-cls" if platform.system().lower() == "windows" else "clear"
    # Action
    os.system(command)
    # print(ansi.clear_screen()) # this works but puts it at the same cursor position
    # location


# ########################
def askYN(msg="Continue", *args, dflt="y", auto=False, **kwargs):
    # ####################
    """
    purpose: using msg as a prompt, this will ask for a simple Yes or No response and return a bool
        Typically used with an "if " statement but can simply be used as: askYN()
    options:
        - centered: bool
        - boxed: bool          # puts only the prompt in a box with a reply prompt centered under it
        - timeout: int=0: int  # how long to wait in seconds
        - auto: bool
        - exit: bool
        - quit: bool           # if response is in  ("q". "Q") an sys.exit() is executed
        - dflt: str="y"        # the default is "y"
        - auto: bool           #  var can be used to automatically invoke the default
        - shift: int           # will shift prompt left (neg) or right (pos)
    returns: bool  # True or False
    useage: 
        askYN()
         Continue [y]: True
    or
    if askYN("Do you want to save this file?", "n"):
        do_save_file()
    """
    # """--== Debugging ==--"""
    # dbug(f"funcname(): {funcname}")
    # dbug(f"msg: {msg}")
    # dbug(f"args: {args}")
    # dbug(f"kwargs: {kwargs}")
    # """--== Config ==--"""
    dflt = kvarg_val(["default", "dflt"], kwargs, dflt=dflt)
    if len(args) > 0:
        if args[0] in ["n", "N", "Y", "y"]:
            dflt = args[0]
    color = kvarg_val(['color', 'clr'], kwargs, kwargs, dflt="")
    center_b = arg_val(['center', 'centered'], args, kwargs, dflt=False)
    shadow_b = arg_val(['shadow', 'shadowed'], args, kwargs, dflt=False)
    boxed_b = arg_val(['box', 'boxed'], args, kwargs, dflt=False)
    # dbug(center)
    auto = True if 'auto' in args else auto
    # dbug(auto)
    quit_b = arg_val(['quit'], args, kwargs, dflt=False)
    exit_b = arg_val(['exit'], args, kwargs, dflt=False)
    timeout = arg_val(["timeout"], args, kwargs, dflt=0)
    # dbug(timeout)
    shift = kvarg_val(["shift"], kwargs, dflt=10)  # dflt is arbitrary
    # """--== Init ==--"""
    shift = int(shift)
    # """--== Validate ==--"""
    if isnumber(timeout):
        timeout = int(timeout)
    if not isinstance(timeout, int):
        timeout = 0
    # dbug(timeout)
    # """--== Process ==--"""
    # dbug(repr(msg))
    if dflt.upper() == "Y" or dflt.upper() == "YES":
        dflt_msg = " [Y]/n "
    else:
        dflt_msg = " y/[N] "
    if center_b:
        # dbug(msg)
        # dbug(center)
        # dbug(auto)
        if auto:
            ans = dflt
            # dbug(f"setting ans: {ans}")
        else:
            # dbug(RESET)
            # prompt = RESET + msg + dflt_msg  # <--- this is just weird how it acts... sometimes prints out \x1b[0
            prompt = msg + dflt_msg
            # dbug(prompt)
            if boxed_b:
                dbug("we are here")
                printit(prompt, centered=center_b, boxed=boxed_b)
                ans = cinput(dflt_msg + " -> ", shift=-shift, timeout=timeout)
            else:
                # dbug(repr(prompt))
                ans = cinput(prompt, timeout=timeout)
    else:
        # dbug(msg)
        if auto:
            ans = dflt
            # dbug(f"setting ans: {ans}")
        else:
            # ddbug(f"timeout: {timeout}", 'ask')
            if timeout > 0:
                ans = cinput(msg + dflt_msg, timeout=timeout, centered=center_b)
                # t.cancel()
            else:
                if isinstance(msg, list):
                    msg = "".join(msg)
                if isinstance(dflt_msg, list):
                    dflt_msg = "".join(dflt_msg)
                # dbug(RESET)
                prompt = RESET + msg + dflt_msg
                # dbug(f"{msg=} {prompt=}")
                # dbug(timeout)
                if boxed_b:
                    dbug(prompt)
                    ans = cinput(boxed(prompt), centered=center_b, timeout=timeout) 
                    dbug("blah ta")
                else:
                    # dbug(f"{prompt=} {center_b=}")
                    ans = cinput(prompt, centered=center_b, timeout=timeout)
    if ans.upper() == "":
        ans = dflt

    if quit_b and ans in ('q', 'Q'):
        printit("Exiting as requested", shadow=shadow_b, center=center_b, box_color="red on black", color=color)
        sys.exit()
    if msg != "":
        # dbug(msg)
        if msg == "Continue" and ans.lower() == "n":
            printit("Exiting at user request...")
            sys.exit()
        if quit_b or exit_b:
            # if quit is true and user hits 'q' then exit out as requested
            printit("Exiting as requested", shadow=shadow_b, center=center_b, box_color="red on black", color=color)
            if ans.lower() in ('q', 'quit'):
                sys.exit()
        if ans.upper() == "Y":
            return True
    return False
    # ### EOB def askYN(msg="Continue", dflt="y", *args, center=False, auto=False, timeout=0):  ### #


# ###########################
def get_dtime_format(s_date, *args, **kwargs):
    # #######################
    """
    purpose:  returns the format of a date-time stamp string
    requires: string of the data to be analyzed eg (s_date = rows[0][0] ie "20250101-0945"
    options:  none
    returns   detected date pattern in strftime format eg "%Y%m%d-%H%M"
    notes:
        - useful for date series in dataframes or plotting (matlibplot)
    """
    # """--== Config ==--""" #
    prnt = arg_val(['prnt', 'print', 'verbose', 'show'], args, kwargs, dflt=True, opposite=['quiet','noprnt'])
    # """--== Convert ==--""" #
    if isinstance(s_date, float):
        s_date = int(s_date)
    if isinstance(s_date, int):
        s_date = str(s_date)
    # in case it is still numpy int or whatever...
    add_this = ""
    if str(s_date).endswith(","):
        add_this = ","
        s_date = s_date.strip(",")
    s_date = str(s_date)
    s_date = s_date.strip("\n")
    # examples        20240620,  20-06-2024,  2024-06-20, 30340620-07:53, 2024-06-20 07:53,  203406020-07:53, 2024-06-20 07:53:01,  2024-06-20 07:53:01-5:00, Jan 1, 2026
    date_patterns = ["%Y", "%Y%m%d", "%d-%m-%Y", "%Y-%m-%d", "%Y%m%d-%H%M", "%Y-%m-%d %H:%M", "%Y%m%d-%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z", "%m/%d/%Y", "%Y%m%d %H:%M", "%b %d, %Y", "%n %e, %Y"]
    for pattern in date_patterns:
        try:
            datetime.strptime(s_date, pattern).date()
            # r = datetime.strptime(s_date, pattern).date()
            # dbug(f"r: {r} pattern: {pattern}")
            return pattern + add_this
        except Exception:  # as Error:
            # dbug(f"pattern: {pattern=}\nFailed against\ns_date: {s_date=} {Error=}")
            continue
    # if we got here something went wrong...
    if prnt:
        dbug(f"Date: [{s_date}] is not in expected format. {called_from('v')} Searched date_patterns: {date_patterns}")
    return None
    # ### EOB def get_dtime_format(s_date): ### #

# alias
date_fmt = get_dtime_format
dt_fmt = get_dtime_format
get_dfmt = get_dtime_format


# ########################
def cat_file(fname, *args, prnt=False, lst=False, **kwargs):
    # ####################
    """
    purpose: reads a file and return lines or rows_lol (list of list) or as a df (dataframe)
    options:
    -    prnt: bool,         # prints out the file contents
    -    lst: bool,          # returns a list of lines or you could use: txt.split('\n') to make it a list
    -    csv: bool,          # treat the file as a csv (or for me, a dat file)
    -    dat: bool,          # this one will seem strange, it treats the first line as a commented out header line
    -    xlsx: bool,         # returns df of a spreadsheet file
    -    hdr: bool,          # whether to include header line or header data in the return
    -    df: bool,           # return a df
    -    delimiter: str      # delimiter to use for a csv, or dat file
    -    rtrn: str='lst'     # (can be "str", "string", "lst", "list", "df"
    -    nums: bool          # forces all numbers to be returned as floats instead of str - useful for plotting
    -    index: bool         # adds id numbers to csv data
    -    purify: bool        # default=False - strips off all comments (except first line on a ".dat" file)
    -    blanks: bool        # default=False - whether to include blank lines - yes, the default is to remove blank lines
    returns: text of a file as a str (default)
        - or returns a list if requested by 'lst' option
        - or rows_lol (if it is a csv: bool file)
        - or returns a df if requested by 'df' option
    Note: if the result df has the header/colnames repeated in row[0] then make sure you included 'hdr' or hdr=True
    """
    # """--== debugging ==--"""
    # dbug(f"funcname: {funcname()}({fname}) called_from: {called_from()}")
    # dbug(fname)
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False) #, opposite=['noprnt', 'noprint'])
    # dbug(f"{prnt=} {called_from('v')}", 'ask')
    csv_b = arg_val(['csv', 'csv_file', 'csvfile'], args, kwargs, dflt=False)
    dat_b = arg_val(['dat', 'datfile', 'dat_file'], args, kwargs, dflt=False)
    xlsx = arg_val('xlsx', args, kwargs, dflt=False)
    # dbug(f"prnt:{prnt} {called_from('verbose')}")
    boxed_b = arg_val(['box', 'boxed', 'bx', 'bxd'], args, kwargs, dflt=False)
    box_clr = arg_val(['box_clr', 'box_color'], args, kwargs, dflt="")
    centered_b = arg_val(['centered', 'center', 'cntr'], args, kwargs, dflt=False)
    # dbug(f"prnt: {prnt} boxed_b: {boxed_b} cemtered_b: {centered_b}")
    title = kvarg_val("title", kwargs, dflt="")
    footer = kvarg_val("footer", kwargs, dflt="")
    # hdr_b = arg_val('hdr', args, kwargs, dflt=False)
    # dbug(hdr_b)
    df_b = arg_val('df', args, kwargs, dflt=False)  # rtrn as df?
    # dbug(df_b)
    lst_b = arg_val(['lst', 'list', 'lol'], args, kwargs, dflt=False)
    rtrn_type = kvarg_val(['rtrn', 'rtrn_type'], kwargs, dflt='lst')  # rtrn value is  df or str  same as above, just another way to do it
    purify_b = arg_val(['purify', 'decomment', 'pure', 'uncomment'], args, kwargs, dflt=False)  # 20240123 changed to False
    # dbug(purify_b)
    # nums_b = arg_val(["nums", "numbers", 'num', 'number'], args, kwargs, dflt=False)
    # delimiter = kvarg_val(["delim", "delimiter"], kwargs, dflt=",")
    index_b = arg_val(["index", "indexes", "idx", "indx"], args, kwargs, dflt=False)
    blanks = arg_val(["blank", "blanks"], args, kwargs, dflt=True)
    raw_b = arg_val(['raw'], args, kwargs, dflt=False)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)  # this used for remote file xfer
    # dbug(raw_b)
    # dbug(f"config: {lst_b=} {raw_b=} {rtrn_type=} {dat_b=} {csv_b=}")
    # """--== Init ==--"""
    if lst_b:
        rtrn_type = 'lst'
    lines = []
    rows_lol = []
    # new_rows = []
    dtype = data_type(fname)
    # dbug(dtype)
    # if "dat_file" in dtype and not raw_b:
        # dat_b = True
    # dbug(f"{dtype=} {dat_b=}")
    # """--== Validation ==--"""
    if isempty(fname):
        dbug(f"fname: {fname} appears to be empty {called_from('verbose')}... returning")
        return None
    # if dtype in ('dat_file'):
        # rtrn_type = 'list'
    # if fname.endswith(".csv"):  # this might be dangerous!
    # dbug(csv_b)
    if "csv_file" in dtype:
        csv_b = True
    # dbug(csv_b)
    if ":" in fname:
        # remote file xfer
        # dbug(f"remote fname: {fname} {called_from()}")
        host, myfname = fname.split(":")
        cmd = f"scp {fname} ./{myfname}"
        printit(f"Please be patient... cmd: {cmd} ... this may take some time ...", centered=centered)
        run_cmd(cmd)
        data_lol = cnvrt(f"./{myfname}")  # make sure does not have a colon in it or this will recurse
        # dbug(data_lol[:3])
        if ask_b:
            if askYN(f"Data has been collected. Do you want to remove the local file: ./{myfname}", "n"):
                os.remove(f"./{fname}")
        return data_lol
    # dbug(f"{fname=} {csv_b=} {dat_b=}")
    # """ Process  """
    # dbug(fname)
    fname = os.path.expanduser(fname)
    if isinstance(fname, str) and not file_exists(fname):
        if prnt:
            dbug(f"Ooops... {fname=} not found... returning None {called_from('v')}...")
        return None
    # dbug(f"{fname=} {rtrn_type=} {lst_b=}")
    # if fname.endswith(".dat"):
    #     # dbug(f"this file fname: {fname}  may be a .dat file")
    #     dat_b = True
    # """--== local functions ==--"""
    def my_purify(file_hndl):
        for line in file_hndl:
            line = line.split("#")[0].strip()
            if line:
                yield line
                # """--== SEP_LINE ==--""" #
    # """--== SEP_LINE ==--"""
    # if raw_b and not csv_b:
    #     with open(fname, 'r') as f:
    #         if lst_b:
    #             contents = f.readlines()
    #             # dbug(contents[:3], 'ask')
    #         else:
    #             contents = f.read()
    #             # dbug(contents, 'ask')
    #     # dbug(f"returning contents[:2]: {contents[:2]}")
    #     return contents
    # """--== SEP_LINE ==--""" #
    # dbug(f"csv_b: {csv_b} dat_b: {dat_b} raw_b: {raw_b} rtr_type: {rtrn_type} <--is it str? {dtype=}")
    if 'empty' == dtype:
        dbug(f"{fname=} appears empty... {called_from('v')}... returning...")
        return
    if "sqlite" in dtype:
        # dbug(f"{fname=} is an sql file {dtype=}", 'ask') 
        # db = SQLiteDB(fname)
        # my_lol = db.fetchall()
        my_lol = get_sqlite_rows(fname)
        # dbug(my_lol, 'ask', 'lst')
        # dbug(called_from('verbose'))
        # dbug(my_lol[:3], 'ask')
        return my_lol
    # """--== SEP_LINE ==--""" #
    if ( "csv" in dtype or (csv_b or dat_b) ) and not raw_b:  #  or rtrn_type not in ("str", "string"):
        # dbug(f"This is being treated as a csv or a dat file: {fname} dtype: {dtype} csv_b: {csv_b} dat_b: {dat_b} {raw_b=} ...", 'ask')
        # my_rows = []
        # if dtype in ('cat_file'):
            # dbug(dtype)
        with open(fname, "r", newline='\n') as csvfile:
            lines = csvfile.readlines()
        # dbug(len(lines))
        if lines[0].startswith("#"):
            # dbug(lines[0])
            lines[0] = lines[0].lstrip("#")
        # dbug(lines[0])
        # dbug(lines[:3])
        my_rows = get_elems(lines)
        # dbug(my_rows[:3])
        if my_rows[0][0].startswith("#"):
            # get rid of commented lines?
            my_rows[0][0] = my_rows[0][0].lstrip("#").strip()
            # dbug(my_rows[0])
            # dbug(my_rows[1][0])
        # dbug(f"{my_rows[:3]=}")
        # dbug(data_type(my_rows))
        # dbug(type(my_rows[1]))
        if data_type(my_rows, ['los']):
            if my_rows[1].rstrip("\n").strip() != "" and my_rows[1][0].startswith('\"'):
                # dbug(my_rows[1][0])
                my_rows[1][0] = my_rows[1][0].lstrip('\"')
                # dbug(my_rows[1][0])
        # gtable(my_rows[:5], 'prnt', 'hdr', title="debugging", footer=dbug('here'), select_cols=my_rows[0][:10], col_limit=25)
        # dbug(my_rows, 'ask', 'lst')
        # dbug(f"returning my_rows type(my_rows: {type(my_rows)} data_type(my_rows): {data_type(my_rows)}", 'boxed')
        # gtable(my_rows[:10], 'prnt', title="debugging", footer=dbug('here'), select_cols=my_rows[0][:10], col_limit=25)
        if df_b:
            # dbug(df_b)
            # dbug(my_rows[:2])
            if 'pandas' not in sys.modules:
                import pandas as pd
            df = pd.DataFrame(my_rows)
            if index_b:
                df = df.reset_index()
            df = df.rename(columns=df.iloc[0]).drop(df.index[0])
            df = df.set_index(list(df)[0])
            # dbug(f"Returning df: {df[:2]}", 'ask')
            return df
        else:
            # dbug(f"Do not return a df index_b: {index_b} rtrn_type: {rtrn_type} {my_rows[:3]=}")
            if index_b:
                # dbug(rows_lol[:4])
                # dbug(my_rows[:4])
                if dat_b:
                    rows_lol = [[n] + row for n, row in enumerate(my_rows, start=0)]
                    rows_lol[0][0] = 'id'
                    rows = rows_lol
                else:
                    rows_lol = [[n] + row for n, row in enumerate(rows_lol, start=1)]
                    rows = rows_lol
                # dbug(rows_lol[:4])
            # dbug("Returning rows_lol[:2: {row_lol[:2]}", 'ask')
        if rtrn_type in ("string", "str"):
            # dbug(f"{rtrn_type=} converting to a string... this is a time sink...")
            # gtable(my_rows[:10], 'prnt', title="debugging", footer=dbug('here'), select_cols=my_rows[0][:10], col_limit=25)
            # dbug(f"{rtrn_type=} {called_from('verbose')}")
            if data_type(my_rows, ('lol')):
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerows(my_rows) # finally - this is a single csv string with linefeeds
                return output.getvalue()
            else:
                rows = "\n".join(my_rows)
                return rows
        else:
            # dbug(rtrn_type)
            rows = my_rows
        # gtable(rows, 'prnt', title="debugging", footer=dbug('here'), select_cols=rows[0][:10], col_limit=25)
        # dbug(f"Returning rows type(rows): {type(rows)}")
        if not blanks:
            rows = [row for row in rows if row.rstrip("\n") != ""]
        # dbug("returning rows")
        # gtable(rows, 'prnt', title="debugging", footer=dbug('here'), select_cols=rows[0][:10], col_limit=25)
        return rows
    if raw_b:
        # dbug(f"Processing {raw_b=} {lst_b=} {rtrn_type=}")
        with open(fname, "r", newline='\n') as f:
            # dbug(f"{lst_b=}")
            if not lst_b:
                text = f.read()
                # dbug(type(text))
            else:
                text = f.readlines()
        # if isinstance(text, str):
            # dbug("winner")
        dtype = data_type(text)
        # dbug(f"{dat_b=} {csv_b=} {dtype=}")
    # """--== SEP_LINE ==--""" #
    if xlsx:
        df = pd.read_excel(fname)
        return df
    # """--== treat this as just a text file ==--"""
    with open(fname, "r") as file:
        text = file.read()
    if prnt:
        text = printit(text, boxed=boxed_b, centered=centered_b, title=title, footer=footer, box_clr=box_clr)
    # else:
    #     # dbug(box_clr)
    #     text = printit(text, boxed=boxed_b, centered=centered_b, title=title, footer=footer, prnt=prnt, box_clr=box_clr)
    if isinstance(text, list) and rtrn_type == 'str':
        text = "\n".join(text)
    if lst_b or purify_b:
        # dbug(f"text): [{text}]")
        # dbug(lst_b)
        # dbug(purify_b)
        if isinstance(text, str):
            text_l = text.splitlines()
        else:
            text_l = text
        if purify_b:
            # dbug(text_l)
            text_l = purify(text_l, blanks=blanks)
            # dbug(blanks, 'ask')
        if not blanks:
            text_l = [line for line in text_l if line.rstrip("\n") != ""]
        if not lst_b:
            text = "\n".join(text_l)
        else:
            text = text_l
        # dbug(f"Returning text: {text}", 'ask')
        # return text
    # """--== SEP_LINE ==--"""
    # dbug(f"Returning {text=} {type(text)=} {rtrn_type=}", 'ask')
    return text
    # ### EOB def cat_file(fname, *args, prnt=False, lst=False, **kwargs): ### #


# ###############################
def file_exists(file, my_type="file", *args, **kwargs):
    # ###########################
    """
    purpose: returns bool if the file (or directory - see options) exists or is it executable
    options:
        type: str  # Note: type can be "file" or "dir" (if it isn't file the assumption is dir)
                    if type == "x" or "X" then the return bool will depend on if the file is executable
    returns: False if it does not exist, otherwise, it returns the file size! <-- Important!
    note:
        if it is a file but it is empty ... it returns 0 instead of False
    """
    # ddbug(f"{funcname()=} {called_from('verbose')}")
    # dbug(args)
    # dbug(kwargs)
    # """--== SEP_LINE ==--""" #
    prnt = arg_val(["prnt", "print", "show", "verbose"], args, kwargs, dflt=False)
    if my_type in ('prnt', 'print', 'show', 'verbose'):
        prnt = my_type
        my_type = 'file'
    # dbug(f"{prnt=} {called_from('verbose')}")
    my_type = arg_val(["type", "pmytype", "my_type"], args, kwargs, dflt=my_type)
    # """--== SEP_LINE ==--""" #
    if isempty(file):
        # dbug(f"No filename {file=} supplied... {called_from('v')} returning")
        return False
    # """--== SEP_LINE ==--""" #
    rtrn = False
    if my_type == "file":
        try:
            file = os.path.expanduser(file)
            if os.path.exists(file) and os.path.isfile(file):
                # dbug(f"{ignore_empty=}")
                rtrn = os.path.getsize(file)
        except Exception as e:
            print("Exception: " + str(e))
            rtrn = False
        if prnt:
           ddbug(f"Returning {file=} {rtrn=}") 
        return rtrn
    if my_type in ('X', 'x', 'executable'):
        try:
            if os.path.isfile(file):  # , X_OK)
                rtrn = True
        except Exception as e:
            print("Exception: " + str(e))
            rtrn = False
        if prnt:
            ddbug(f"Returning {file=}  {rtrn=}")
        return rtrn
    if my_type == 'dir':
        # check file or dir
        rtrn = os.path.exists(file)
        if prnt:
            dbug("Returning {rtrn=}")
        return os.path.exists(file)
    # to move a file use: os.rename(source, target)
    # or shutil.move(source, target)
    rtrn = True
    if prnt:
        dbug("Returning {file=} {rtrn=}")
    return rtrn


# ####################
def purify(content, *args, **kwargs):
    # ################
    """
    purpose: de-comments a file, aka removes all comments denoted by "#" ...
    input: 
        content: list | filename | str   # content can be a line (string), a list of lines (strings), of a filename
    options:
        - dat_b: bool     # converts first (commented line) into a non-commented line rather than eliminating it as a comment
        - partials: bool  # default=True - remove partial sentence comments eg "this line is a partial # with a trailing comment"
        - blanks: bool    # default=False - whether to allow blanks
    return lines: list (de-commented lines/purified)
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(content)
    # """--== SEP_LINE ==--"""
    # DONE make this simply purify() and accept, filename, lines: list, or line: str for "purifying" (decommenting)
    # """--== Config ==--"""
    dat_b = arg_val(["dat", "dat_file", "datfile"], args, kwargs, dflt=False)
    purify_b = arg_val(["purify", "purify_b", "decomment"], args, kwargs, dflt=True)  # this might seem strange but there is an occasion
    # where I need this to NOT strip comments (except first line of a '.dat' file)
    # This is not defined int the function doc above because it is probably never needed
    # this dat_b option is primarily for me (the author) - I have legacy ".dat" files that have a commented first line which has column names for a csv type file
    # this dat_b option will preserve that first line but decomment it - it is not listed above because it simply for me
    partials_b = arg_val(["partial", "partials", "truncate"], args, kwargs, dflt=True)
    blanks = arg_val(["blanks", "blanks"], args, kwargs, opposite=["noblank", "noblanks", "no_blanks", "no_blank"], dflt=False)
    # dbug(blanks)
    # """--== Init ==--""" #
    purified_line = None
    purified_lines = []
    # """--== function(s) ==--"""
    def purify_line(line):
        purified_line = None
        # purified_line = line.split('#')[0].strip()  # TODO make this an re.split(r'(?<!\\)#', str)
        # line = line.strip()
        if isinstance(line, str):
            line = line.rstrip("\n")
            purified_line = re.split(r'(?<!\\)#', line)[0]  # TODO make this an re.split(r'(?<!\\)#', str)
        # dbug(f"Returning purified_line: [{purified_line}] type(purified_line): {type(purified_line)}")
        return purified_line
    # """--== Process ==--"""
    if isinstance(content, str):
        file = content  # renamed just for clarity
        file = os.path.expanduser(file)
        if file_exists(file):
            # dbug(f"assuming this is a filename: {file} and it exists")
            with open(file, "r") as myfile:
                if os.path.getsize(file) == 0:
                    dbug(f"file: {file} appears to be empty... returning...")
                    return None
                file_lines = myfile.readlines()
                # dbug(len(file_lines))
                # dbug(file_lines[:3], 'ask')
                for num, line in enumerate(file_lines):
                    # dbug(f"processing line: {line}")
                    # dbug(dat_b)
                    if num == 0 and dat_b:
                        if line.startswith("#"):
                            # remove the '^#\s'  but leave the line
                            # dbug(line)
                            line = re.sub(r"^#\s", "", line)
                            # dbug(line)
                    # """--== OK not the first line of a dat file ==--"""
                    line = line.rstrip('\n')
                    # dbug(line)
                    # purified_lines.append(line)
                    # continue
                    line = line.rstrip('\n')
                    # if num == 0:
                    #     line = line.lstrip("#")
                    if purify_b and partials_b:  # default is to purify but in the case of gtable data(lol) this may be False
                        purified_line = purify_line(line)
                        if isempty(purified_line):
                            continue
                    else:
                        # dbug(line)
                        purified_line = line
                    # dbug(purified_line)
                    if (purified_line.isspace() or purified_line.rstrip("\n") == '') and not blanks:
                        # skip a blank line - this is part of purify # TODO, ??? make this an option???
                        continue
                    # dbug(f"Adding purified_line: {purified_line}")
                    purified_lines.append(purified_line)
        else:
            # assuming this is a simple string or a single line
            # dbug(line)
            line = purify_line(content)
            # dbug(line)
            return line
    # """--== SEP_LINE ==--"""
    # dbug(purify_b)
    # dbug(purified_lines[:3])
    # dbug(blanks)
    if isinstance(content, list):
        # dbug(f"This is a list:[:3]: {list[:3]}", 'ask')
        for line in content:
            # dbug(line)
            if blanks and isempty(line):
                # dbug("Empty?", 'ask')
                purified_lines.append("  ")  # wow - this solution was not easy
            else:
                # line = line.rstrip("\n")
                if purify_b:
                    if isinstance(line, str) and line.startswith("#"):
                        # dbug("got a full comment line so skip it entirely - trust me this is needed as purify_line cannot return None")
                        continue
                    purified_line = purify_line(line)
                    purified_lines.append(purified_line)
                    # dbug(purified_line)
                else:
                    purified_lines.append(line)
        if not blanks:
            # dbug(blanks, 'ask')
            purified_lines = [line for line in purified_lines if line != ""]  # get rid of blank lines
            # dbug(purified_lines, 'ask', 'lst')
        # dbug(purified_lines, 'lst')
    # """--== SEP_LINE ==--"""
    # dbug(f"Returning lines[:3]: {purified_lines[:3]}")
    return purified_lines
    # ### EOB def purify() ### #


# alias purify
purify_file = purify


# ###################################
def ireplace(s, indices=[], char="|"):
    # ###############################
    """
    purpose: index replace
    To get indices use eg:
        iter = re.finditer(rf"{c}", s)
        indices = [m.start(0) for m in iter]
        # next line removes first two and last two indices - just an example
        indices = indices[2:-2]
    then use this func with:
        s: is the string to do the replacements
        indices: list of indexed positions
        char: is the char to replace with
    """
    s_l = list(s)
    if len(indices) > 0:
        for i in indices:
            s_l[i] = char
        s = "".join(s_l)
    return s


# ########################################
def matched_lines(filename, pattern, upto=1):
    # ####################################
    """
    purpose: return: just the first matched line(s) from a filename using pattern
    required:
        - filename: str
        - pattern: str
    options:
        - upto: int default=1  # How many matching lines to return
    returns: matching lines: list
    """
    # """--== debugging ==--"""
    # dbug(f"{funcname()} called_from: {called_from()}")
    # dbug(filename)
    # dbug(pattern)
    # """--== SEP_LINE ==--"""
    if isinstance(filename, list):
        lines = filename
    if isinstance(filename, str) and " " in filename:
        lines = [filename]
    if isinstance(filename, str) and " " not in filename:
        filename = os.path.expanduser(filename)
        if not file_exists(filename):
            dbug(f"Failed to find file: {filename}... please investigate... called_from: {called_from()} returning")
            return
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    matched_l = []
    # line_n = 1
    for num, line in enumerate(lines, start=1):
        # dbug(f"Processing num:{num} line: {line} of {len(lines)}")
        if isinstance(line, list):
            line = ",".join(line)
        r = re.match(pattern, line)
        if r:
            # dbug(f"pattern: {pattern} hit on line: line: {line}")
            matched_l.append(line.rstrip("\n"))
            if len(matched_l) >= upto:
                # dbug(f"returning matched_l[:3]: {matched_l[:3]}")
                return matched_l
        # line_n += 1
    # dbug(f"returning matched_l[:3]: {matched_l[:3]}")
    return matched_l
    # ### EOB def matched_lines(filename, pattern, upto=1): ### #


# alias
# first_matched_line = matched_lines


# ######################################
def x_items(my_d, x=2, *args, **kwargs):
    # ##################################
    """
    purpose: returns a limited number of dictionary items - primarily used for development (debugging)
    requires
    options:
        -x: int     # default=2 number of items (pairs of key/value) to return 
    returns: dict
    # TODO this needs a better name
    """
    dbug(f"Who uses this? funcname: {funcname}")
    return {k: my_d[k] for k in list(my_d)[:x]}


# ###############################
def pivot(data, *args, **kwargs):
    # ###########################
    """
    purpose to pivot data
    requires: data: list of lists | dict
    options:
        - hdr|header|colnames: bool  # default=False  if true will put ["Key", "Value"] as first row of an lol
    returns: data as list of lists
    note: 
        - this is kind of an expansion on transpose in that turns a dictionary into rows of key, value pairs
        - name id gpivoty to avoid conflicts with pandas pivot
    """
    # """--== Config ==--"""
    hdr_b = arg_val(["hdr", "header", "colnames", "hdr_b"], args, kwargs, dflt=False)
    dtype = data_type(data)
    # dbug(dtype)
    # """--== Convert ==--"""
    if dtype in ('df'):
        data = cnvrt(data)
        dtype = data_type(data)
    # """--== Validate ==--"""
    # dbug(islol(data))
    # if not islol(data) and not isinstance(data, dict):
    # if dtype not in ('lol', 'lob', 'dov', 'dom', 'lon'):
    if not isinstance(data, (dict, list)):
        dbug(f"type(data): {type(data)} dtype: {dtype} should be an list of lists (lol) or a dictionary... called_from: {called_from()}", 'ask')
        return
    # """--== SEP_LINE ==--"""
    # dbug(f"{funcname()}: called_from: {called_from()}")
    # """--== SEP_LINE ==--"""
    if isinstance(data, dict):
        # dbug("turn every key, value pair into a row in a lol")
        my_lol = []
        if hdr_b:
            my_lol = [['Key', 'Value']]
        for k, v in data.items():
            # dbug(f"adding [{k},{v}] ")
            my_lol.append([k,v])
        # dbug(my_lol)
        return(my_lol)
    # list(map(list, zip(*msg_l))  # to pivot??? need to research this line - TODO
    transposed_lol = list()
    for i in range(len(data[0])):
        row = list()
        for sublist in data:
            row.append(sublist[i])
        transposed_lol.append(row)
    data = transposed_lol
    return data


# #####################################
def kvcols(data_d={}, *args, **kwargs):
    # #################################
    """
    purpose: data (dictionary) is chunked into columns
    requires:
        - data: dict
    options:
        - cols: int           # default=2
        - prnt: bool          # default=False
        - centered: bool      # default=False
        - more: see below
        - ask: bool
    notes: this is a rewrite of kv_cols() and uses gtable()

    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # dbug(data_d)
    # dbug(cols)
    # dbug(args)
    # dbug(kwargs)
    # """--== Imports ==--"""
    # from math import ceil
    # """--== Config ==--"""
    cols = kvarg_val(['cols', 'columns'], kwargs, dflt=2)
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    centered_b = arg_val(['cntrd', 'cntr', 'center', 'centered'], args, kwargs, dflt=False)
    title = kvarg_val(['title'], kwargs, dflt="")
    mstr_title = kvarg_val(['mstr_title'], kwargs, dflt="")
    footer = kvarg_val(['footer', 'foot'], kwargs, dflt="")
    mstr_footer = kvarg_val(['mstr_footer', 'mstr_foot'], kwargs, dflt="")
    boxed_b = arg_val(["boxed", "box"], args, kwargs, dflt=False)
    pivot_b = arg_val(["pivot", "transform"], args, kwargs, dflt=True)
    box_clr = kvarg_val(['box_color', 'box_clr', '_bx_clr'], kwargs, dflt="")
    mstr_box_clr = kvarg_val(['master_box_color', 'mstr_box_clr', 'mstr_bx_clr', 'mstr_box_color'], kwargs, dflt="")
    col_limit = kvarg_val(["col_limit", 'col_max'], kwargs, dflt=99)  # arbitrary but can't be 0
    # dbug(f"col_limit: {col_limit} {called_from('verbose')}")
    human = arg_val(["human", "H", "h"], args, kwargs, dfault=False)
    rnd = arg_val(["rnd", "round"], args, kwargs, dfault=False)
    neg = arg_val('neg', args, kwargs, dflt=False)  # if a list is supplied here the syntax is [colname, colname, colanme...]
    colnames = kvarg_val(['colnames'], kwargs, dflt=['Key', 'Value'])
    ask_b = arg_val(["ask"], args, kwargs, dflt=False)
    # """--== Convert ==--"""
    dtype = data_type(data_d)
    # dbug(dtype)
    # """--== Validation ==--"""
    if dtype in ("doD"):
        dbug("This is a dictionary of different sized dictionaries... returning")
        return
    if dtype in ('dov'):
        # dbug("Test to make sure no key is empty")
        if any(key == '' for key in data_d):
            dbug(f"At least one key in data_d: {data_d} appears empty... returning....")
            return 
    if not isnumber(cols):
        dbug(f"The second argument cols: {cols} must be an integer... called_from: {called_from()}")
        return
    cols = int(cols)
    # """--== Init ==--"""
    # dbug(f"{data_d=} {called_from('verbose')}")
    if isempty(data_d):
        dbug(f"It appears {data_d=} empty {called_from('v')} ... returning...")
        return
    # dtype(f"{data_type(data_d)=} {called_from('v')}")
    # dbug(data_d)
    data_lol = cnvrt(data_d, human=human, rnd=rnd, neg=neg, pivot=pivot_b, col_limit=col_limit, colnames=colnames)
    # dbug(dtype)
    # dbug(data_lol)
    # place holder
    # """--== Process ==--"""
    # dbug(colnames)
    # data_lol = pivot(data_lol)  # done above
    # size = math.ceil(len(data_lol)/int(cols)) 
    # chunks = chunkit(data_lol, size) 
    # tables = []
    my_title = title
    my_footer = footer
    if boxed_b:
        if isempty(mstr_title):
            mstr_title = title
            my_title = ""
        if isempty(mstr_footer):
            mstr_footer = footer
            my_footer = ""
    rtrn = gtable(data_lol, 'hdr', prnt=False,  centered=False, colnames=colnames, title=my_title, footer=my_footer, box_clr=box_clr, cols=cols)
    if prnt:
        printit(rtrn, boxed=boxed_b, ask=ask_b, centered=centered_b, title=title, footer=footer, box_clr=mstr_box_clr) 
    # """--== Return ==--""" #
    # rtrn = printit(rtrn, centered=centered_b, prnt=prnt, boxed=boxed_b, title=mstr_title, footer=mstr_footer, box_clr=mstr_box_clr)
    return rtrn
    # ### EOB def kvcols(data_d={}, *args, **kwargs): ### #


def rowscols_cols(lol, cols, *args, **kwargs):
    """
    purpose: this takes a longish lol - namely, rows of columns and allows
        you to split those rows into X columns. This is most likely used to split
        up rows of columns for gtables so an option include colnames to add to the
        top of each new column of rows cols:
        This is an experiment but I think it could be useful
    Here is a simple visual
    row_of_cols
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
    |      |     |    |
    +------+-----+----+
   split_tables = rowscols_cols(row_of_cols, 2)
    +------+-----+----+ +------+-----+----+
    |      |     |    | |      |     |    |
    +------+-----+----+ +------+-----+----+
    |      |     |    | |      |     |    |
    +------+-----+----+ +------+-----+----+
    |      |     |    | |      |     |    |
    +------+-----+----+ +------+-----+----+
    |      |     |    |
    +------+-----+----+
    TODO? - having seconds thoughts that this should be part of gtables...
    """
    dbug(f"{funcname()} called_from: {called_from()} ... Who uses this?", 'ask')
    # import math
    colnames = ["IP", "Hostname", "Status", "Ports"]
    rows_len = len(lol)
    dbug(rows_len)
    half = math.ceil(rows_len / cols)
    dbug(half)
    chunks = chunkit(lol, half)
    dbug(len(chunks))
    boxes = []
    for chunk in chunks:
        box = gtable(chunk, 'hdr', colnames=colnames)
        boxes.append(box)
        printit(box)
    dbug(len(boxes))
    col_blocks = gcolumnize(boxes)
    return(col_blocks)
    # ### EOB def rowscols_cols(lol, cols, *args, **kwargs): ### #


# #################################
def key_swap(orig_key, new_key, d):
    # #############################
    """
    purpose: switch or change the keyname (a single key)  on an element in a dictionary - replace a key in a dict
    args:
        orig_key  # original key name
        new_keyA  # new key name
        d         # dictionay to change
    returns: the altered dictionary
    note: ignores everything if orig_key not found and just returns the original dict
    """
    # dbug(f"orig_key: {orig_key} new_key: {new_key}")
    if orig_key in list(d.keys()):
        d[new_key] = d.pop(orig_key)
    return d
    # END def keys_swap(orig_key, new_key, d):


# ########################################################
def gcolumnize(msg_l="", *args, **kwargs):
    # ####################################################
    """
    purpose: This will columnize (vertically) a list or a list of blocks or strings
    input: msg_l: list|lol
    options:
        - width|length=0: int              # max width or use cols below
        - cols: int=2                      # number of desired columns
        - sep|sep_chrs|sepchrs=' | ': str  # string or character to use between columns eg: sep=f" {chr(9475)} "
                                           # if sep='solid' then sep = f" {chr(9475} " box_color will be used for the color of this separation chr
        - prnt|print|show = False: bool
        - boxed: bool                      # box the output
        - box_color: str                   # color to use for box border
        - centered = False: bool  # only invoked if prnt == True
        - title = "": str   # only invoked if prnt == True
        - color: str
        - footer = "": str  # only invoked if prnt == True
        - positions: list   # list of either triplets or lists with 3 values, (row, col, position)
                --- position can easily be declared as 1-9 -> see gblock().__doc__
        - ask: bool                        # ask to continue before return
    returns: lines: list # suitable for printit()
    notes:
    - This is a *SLOW* process!
    - handles simple lists or a list of blocks/boxes (a list of lines)
    - If it is a list of lists (like several boxes made up of lines ) then
        it will list them next to each other
        Further is it is a list or rows with a list of boxes for each row then this will try to accomodate
    - a sep option example: sep=f" {chr(9475)} "
    eg
    box1 = +------+
           | box1 |
           +------+
    box2 = +------+
           | box2 |
           +------+
    boxes = box1 + box2
    lines = gcolumnize(boxes)
    printit(lines)
        +------+  +------+
        | box1 |  | box2 |
        +------+  +------+
              or
    box1 = +------+
           | box1 |
           +------+
    box2 = +------+
           | box2 |
           | box2 |
           +------+
    box3 = +----------------+
           | box3 box3 box3 |
           +----------------+
    box4 = +------+
           | box4 |
           | box4 |
           | box4 |
           | box4 |
           +------+
    row1 = [box1, box2]
    row2 = [box3, box4]
    lines = gcolumnize([row1, row2]
    printit(lines)
      or
    mylist = ["One potato", "Two potato", "Three potato", "Four", "Now close the door"]
    lines = gcolumnize(mylist, width=40)
    printit(lines)
    One potato    Four
    Two potato    Now close the door
    Three potato
    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # dbug(msg_l)
    # dbug(args)
    # dbug(kwargs)
    # for box in msg_l:
    #     printit(box)
    if msg_l in ('tst', 'test', 'demo'):
        # this works - in vim you can use: :! ./%  -T gcolumnize 'tst'  
        import gtoolz_tsts
        gtoolz_tsts.gcolumnize_tst()  # runs tests for gcolumnize
        return
    # """--== Config ==--"""
    pad = kvarg_val(["pad", "fill"], kwargs, dflt=" ")
    sep_chrs = arg_val(['sep', 'sepchr', 'sepchrs', 'sep_chr', 'sep_chrs'], args, kwargs, dflt=" ")
    if sep_chrs is True:
        sep_chrs = f" {chr(9475)} "
    # dbug(type(sep_chrs))
    # dbug(sep_chrs)
    # cntr_cols = kvarg_val(["cntr_cols", "center_cols", "cols_cntr", "cols_center"], kwargs, dflt=[])
    # my_lol = msg_l
    prnt = arg_val(['prnt', 'print', 'show'], args, kwargs, dflt=False)
    # dbug(prnt)
    boxed_b = arg_val(['boxed', 'box', 'boxed_b'], args, kwargs, dflt=False)
    # dbug(boxed_b)
    # dbug(boxed_b)
    # boxed = boxed_b
    # dbug(boxed_b)
    box_color = kvarg_val(['box_color', 'box_clr', 'border_color', 'border_style', 'bxclr', 'boxclr'], kwargs, dflt="")  # white! on grey(50)?
    # dbug(box_color)
    color = kvarg_val(["color", "clr", "txt_clr"], kwargs, dflt="")                                   # white! ?
    centered_b = arg_val(['center', 'centered', 'cntr', 'cntrd'], args, kwargs, dflt=False)
    # dbug(centered_b)
    title = kvarg_val(['title'], kwargs, dflt="")
    footer = kvarg_val(['footer'], kwargs, dflt="")
    # aligned = arg_val(["cols", 'aligned', "evencols"], args, kwargs, dflt=False)
    width = kvarg_val(["width", "length"], kwargs, dflt=0)
    # dbug(width)
    cols = kvarg_val(["cols", "size", "columns", "col"], kwargs, dflt=2)  # col is here for typo's - if i did it once I will do it again
    # dbug(cols)
    # height = kvarg_val(["height", "rows"], kwargs, dflt=0)
    # positions = kvarg_val(["positions"], kwargs, dflt=[])
    # dbug(my_lol, 'ask')
    # dbug(color)
    test_b = arg_val(['test'], args, kwargs, dflt=False)
    # recursing = arg_val(["recurse","recursing"], args, kwargs, dflt=False)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    # """--== Validate ==--"""
    if test_b:
        from gtoolz_tsts import gcolumnize_tst
        gcolumnize_tst()
    if isempty(msg_l):
        dbug(f"msg_l: {msg_l} appears to be empty... {called_from('verbose')}... returning...")
        return
    # dbug(msg_l)
    # """--== Init ==--"""
    msg_l_dtype = data_type(msg_l)  # this will change as things get converted
    # dbug(f"{msg_l_dtype=} {called_from('v')} {len(msg_l)=} {cols=} {prnt=}")
    COLOR = gclr(color)
    BOX_COLOR = gclr(box_color)
    # dbug(f"{COLOR=}")
    scr_col_len = get_columns()  # get the number of columns on the terminal screen
    lines = []
    if sep_chrs.lower() ==  "solid":
        # dbug(box_color)
        # sep_chrs = f"{sub_color(box_color)} {chr(9475)} {RESET} "
        sep_chrs = f"{gclr(box_color)} {chr(9475)} {RESET} "
        # dbug(repr(sep_chrs))
    sep_chrs = BOX_COLOR + sep_chrs + RESET
    # """--== Convert ==--"""
    if str(width).endswith("%"):
        amnt = width.rstrip("%")
        pamnt = int(amnt)/100
        width = int(int(scr_col_len) * pamnt)
        # """--== SEP_LINE ==--""" #
    if msg_l_dtype in ("lom"):
        # dbug(f"Lets deal with the possibility that one or more elems is not a block of lines {msg_l_dtype=} {called_from('v')}")
        new_msg_l = []
        for msg in msg_l:
            msg_dtype = data_type(msg)
            if msg_dtype == "empty":
                continue
            # dbug(f"{msg_dtype=} {called_from('v')}") 
            # printit(msg, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
            if isinstance(msg, str):
                if "\n" in msg:
                    msg = msg.split("\n")
                msg = gblock(msg)  # this works but might be overkill
                if not isinstance(msg, list):
                    # dbug(f"perhaps {msg=} is a single line, turn it into a list")
                    msg = [msg]
            # else:
                # msg = str(msg)
                # printit(msg, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
            new_msg_l.append(msg)
            # """--== SEP_LINE ==--""" #
        #if data_type(new_msg_l, ('lob')):
        #    msg_l = new_msg_l
        #    msg_l_dtype = 'lob'
        #    # dbug("we did it")
        msg_l = new_msg_l
        # """--== SEP_LINE ==--""" #
    if msg_l_dtype in ('block'):
        # dbug(f"this actually might not be a box but rather lines all having the same len {prnt=}")
        msg_l_dtype = 'los'
    # dbug(msg_l)
    new_msg_l = []
    # dbug(f"{msg_l_dtype=}")
    # """--== lob ==--""" #
    if msg_l_dtype in ('lob'):
        # dbug(f"{msg_l_dtype=} {len(msg_l)=} {cols=} {called_from('v')} {prnt=}", 'ask')
        if len(msg_l) > cols:  
            # dbug(f"we need to break this up because {len(msg_l)=} > {cols=}")
            my_lines = []
            prnt_blks = []
            for blk_num, blk in enumerate(msg_l, start=1):
                # dbug(blk)
                prnt_blks.append(blk)
                remainder = blk_num % cols
                if remainder == 0:
                    # dbug(f"OK print and reset {len(msg_l)=} {cols=} {len(prnt_blks)=}")
                    # dbug("now recurse")
                    this_lines = gcolumnize(prnt_blks, cols=cols, prnt=False)  # recursing
                    # printit(this_lines, 'boxed', title='debugging', footer=dbug('here'))
                    my_lines += this_lines
                    # printit(my_lines, 'boxed', title='debugging', footer=dbug('here'))
                    prnt_blks = []  # reset to []
            if remainder > 0:
                # dbug(f"{blk_num} {len(msg_l)=} {cols=} {prnt=} {called_from('v')}")
                my_lines += gcolumnize(msg_l[blk_num-1:], cols=cols)  # recursing
            lines = my_lines
            # printit(my_lines, prnt=prnt, boxed=boxed_b, centered=centered_b, box_color=box_color, color=color, title=title, footer=footer)
            # return my_lines
    # """--== if not a los ==--""" #
    # dbug(f"{cols=} {len(msg_l)=}")
    if msg_l_dtype not in ('los', 'lon'):
        for msg in msg_l:
            # dbug(f"{msg=} {data_type(msg)=}")
            if isinstance(msg, list) and not isempty(msg):
                new_msg = []
                for line in msg:
                    # if line is None:  # How does this happen? Got me, but we are dealing with it.
                    if isempty(line): # is None:  # How does this happen? Got me, but we are dealing with it.
                        # dbug(f"skipping {msg=}")
                        continue
                    new_msg.append(line)
                new_msg_l.append(new_msg)
            msg_l = new_msg_l
    # dbug(f"{cols=} {len(msg_l)=}")
    new_msg_l = []
    for msg in msg_l:
        # dbug(f"{data_type(msg)=} {msg_l_dtype=} do not confuse these two")
        # if isempty(msg):
        #     # get rid of empty msg
        #     # dbug(f"appending msg: {msg}")
        #     continue
        if data_type(msg, 'lob') and len(msg) == 1:
            # dbug("turning a list of a single block into a single block")
            msg = msg[0]
            # dbug(data_type(msg))
        if data_type(msg, 'lob') and len(msg) > 1:
            # dbug(f"flattening {data_type(msg)=} {msg=} which is a list with sublists")
            msg = [item for sublist in msg for item in sublist]  # magik trick I learned on-line
            # dbug(data_type(msg))
        if data_type(msg, 'los'):
            msg = gblock(msg)
        new_msg_l.append(msg)
        msg_l = new_msg_l
    msg_l_dtype = data_type(msg_l)  # this will change as things get converted
    # dbug(f"{cols=} {msg_l_dtype=}", 'ask')
    # dbug(cols)
    msg_l_dtype = data_type(msg_l)
    # dbug(f"{cols=} {msg_l_dtype=} {len(msg_l)=} {prnt=}")
    #dbug(len(msg_l))
    #dbug(msg_l)
    # dbug(msg_l_dtype)
    #if 'block' in dtype:
    #    cols = 1
    #if cols > len(msg_l):
    #    cols = len(msg_l)
    # """--== EOB if all([islos(elem) for elem in msg_l]): ==--"""
    # if not islol(my_lol):
    # if not islol(msg_l):
    # dtype = data_type(msg_l)
    # dbug(msg_l_dtype)
    if  msg_l_dtype not in ('lol', 'lob', 'lom'):  # do not add 'los' here!
        # dbug(f"Simple list cols: {cols} msg_l_dtype: {msg_l_dtype} len(msg_l: {len(msg_l)}", 'ask')
        # dbug("calling columned()")
        # if isempty(msg_l):
            # dbug(f"msg_l: {msg_l} {called_from()}")
        lines = columned(msg_l, width=width, cols=cols, box_color=box_color, color=color, centered=centered_b, sep=sep_chrs)
        if not isempty(lines):
            printit(lines, prnt=prnt, ask=ask_b, boxed=boxed_b, centered=centered_b, box_color=box_color, color=color, title=title, footer=footer)
            # dbug(f"Returning lines[:3]: {lines[:3]}")
        return lines
    if msg_l_dtype in ('los'):
        lines = columned(msg_l, width=width, cols=cols, box_color=box_color, color=color, centered=centered_b, sep=sep_chrs)
        printit(lines)
        dbug('ask')
        pass
    # """--== SEP_LINE ==--"""
    if all([data_type(item, 'lob') for item in msg_l]):
        # dbug("this is probabaly a list of rows with boxes in each row - ie lolob")
        msg_l = [row for row in msg_l if not isempty(row)]  # first attempt to clean out empty rows
        lines = []
        max_width = 0
        row_line_sets = []
        for row in msg_l:
            # dbug("processing row")
            # dbug(row, 'lst')
            # printit(row[0])
            row_dtype = data_type(row)
            # dbug(row_dtype)
            if row_dtype in ("empty"):  # second test for an empty row. eg: ['']
               continue
            # dbug(len(row))
            dbug("now recurse")
            row_lines = gcolumnize(row)  # recursing
            # dbug(row_lines, 'lst')
            # printit(row_lines)
            for line in row_lines:
                # dbug("processing line: {line}")
                line_len = parse_codes(line, 'nclen')
                # if nclen(line) > max_width:
                if line_len > max_width:
                    # dbug("reseting max_width")
                    # max_width = nclen(line)
                    max_width = line_len
            row_line_sets.append(row_lines)
        # dbug(max_width)
        for row_lines in row_line_sets:
            # this centers the row_lines (row of boxes) into the largest row length (max_width)
            # dbug("calling gblock()")
            lines += gblock(row_lines, length=max_width, position=5)
            # dbug(len(lines))
        # return
    if msg_l_dtype in ('lob') and lines == []:
        # dbug("This is a single row of boxes")
        cols = len(msg_l)
        max_height = 0
        col_widths = []
        for col, box in enumerate(msg_l):
            # this takes some time
            if len(box) > max_height:
                max_height = len(box)  # num of lines
            # printit(box)
            # ruleit()
            col_widths.append(maxof(box))
            # dbug(max_height)
        # """--== SEP_LINE ==--"""
        if max_height > 80:  # experimentally arbitrary
            dbug(f"Please be patient ... lots of lines to format... (current {max_height=}) {called_from('v')}...")
        # """--== SEP_LINE ==--"""
        # dbug(col_widths)
        # dbug(f"cols: {cols} max_height: {max_height}")
        lines = []
        for line_no in range(max_height):
            # this takes more time
            # start_time = time.time()
            new_line = ""
            for box_num, box in enumerate(msg_l):
                # box_dtype = data_type(box)
                # dbug(box_dtype)
                # dbug(type(box))
                # dbug(box[line_no])
                # dbug(f"line_no: {line_no} len(box): {len(box)}")
                if box_num > 0:
                    new_line += sep_chrs
                if line_no >= len(box):
                    # dbug(line_no)
                    # dbug("building new_line")
                    new_line += COLOR + pad * col_widths[box_num]
                else:
                    this_dtype = data_type(box)
                    # dbug(this_dtype)
                    if this_dtype in ("lob"):
                        new_line = box
                    else:
                        new_line += box[line_no]
                # dbug(new_line)
            lines.append(new_line)
            # dbug(f"elepsed: {time.time()-start_time}")
    if isempty(lines):
        dbug(f"{lines=} is empty {called_from('verbose')}")
        return
    if msg_l_dtype in ('lom'):
        for item in msg_l:
            printit(item)
    if prnt:
        # lines_dtype = data_type(lines)
        # dbug(f"We are here lines_dtype: {lines_dtype}")
        printit(lines, prnt=prnt, ask=ask_b, boxed=boxed_b, centered=centered_b, box_color=box_color, color=color, title=title, footer=footer)
    # if isempty(lines):
        # dbug(f"lines empty... called_from: {called_from()}")
    # dbug(len(lines))
    if ask_b:
        dbug(f"Shall we continue?... {len(lines)=} {called_from('v')}...", 'ask')
    return lines
    # ### EOB def gcolumnize(boxes, width=0): ### #


# for now, create and alias (TODO)
# gcolumnized = gcolumnize


# #######################################
def matrix(rows=None, cols=None, *args, **kwargs):
    # ##################################
    """
    purpose: initialize a matirx (ie array)
    required: rows/dim1: int, cols/dim2: int
    options:
        - dflt_val: str=None   # default "value" to initialize each "cell" to
        - rndm: list|tuple     # fill in vals with  random integers between [start_num, end_num]
        - colnames: list       # this will add yor colnames
        - colnums: bool        # this will make colmanes = ["col1", "col2", "col3"....]
    returns: 
        - 2 dim initialized array/matrix ie a list of lists (lol) or rows of columns
    """
    # """--== Config ==--"""
    dflt_val = arg_val(['dflt', 'dflt_val'], args, kwargs, dflt=None)
    rndm = arg_val(['rndm', 'random'], args, kwargs, dflt=None)
    colnames = arg_val(['colnames', 'columns'], args, kwargs, dflt=None)
    colnums = arg_val(['colnums', 'addcols', "addcolnums"], args, kwargs, dflt=None)
    # """--== SEP_LINE ==--"""
    my_lol = []
    # row col array
    if isinstance(rndm, (list, tuple)):
        import random
        start, end = rndm
        # dbug(f"start: {start} end: {end}")
        my_lol = [[random.randint(start, end) for _ in range(cols)] for r in range(rows)]
    else:    
        my_lol = [[dflt_val for c in range(cols)] for r in range(rows)]
    if colnums:
        colnames = ["col" + str(_) for _ in range(1, int(cols) + 1)]
    if not isempty(colnames):
        if len(colnames) != int(cols):
            dbug("Not adding colnames because the number does not eqaul the number of columns...")
        else:
            my_lol.insert(0, colnames)
    return my_lol
    # ### EOB def matrix(rows, cols, *args, **kwargs): ### #


# #################################
def sayit(msg="", *args, prnt=True, **kwargs):
    # #############################
    """
    purpose: This will use computer voice (espeak) to "say" the msg
    options
    - prnt: will print as well  # this is very limited
    - gender: str               # m | f
    - volume: float             # 0 - 1
    - rate: int                 # default = 150
    - tone: int                 # 1 - 5  <-- this does not seem to do anything???
    - engine: TBD
    returns: None
    notes:
    """
    # """--== Imports ==--"""
    import importlib.util
    poss_modules = ['piper', 'gtts', 'pyttsx3', 'python-espeak']
    for this_module in poss_modules:
        spec = importlib.util.find_spec(this_module) #
        if spec:
            # dbug(f"we win with {this_module=}")
            # dbug(this_module)
            break
        # else:
            # dbug(f"no such {this_module=}")
    # dbug(this_module)
    if not this_module:
        dbug("No suitable module found")
        return
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "print"], args, kwargs)
    rate = kvarg_val(['rate'], kwargs, dflt=150)
    volume = kvarg_val(['vol', 'volume'], kwargs, dflt=0.8)
    gender = kvarg_val(['gender'], kwargs, dflt="m")
    tone = kvarg_val(['tone', 'tonal'], kwargs, dflt=3)
    # """--== Init ==--"""
    if not msg:  # for testing or demo
        msg = "All the world's a stage; and all the men and women merely players"
        printit(msg, 'boxed', title="No msgs was supplied so doing a demo", footer=dbug('here'), box_clr="red!")
        # dbug(msg)
    if this_module == 'piper':
        import wave  # builtin
        from piper import PiperVoice, SynthesisConfig
        out_file = 'test.wav'
        # syn_config = SynthesisConfig(length_scale=1.5, volume=0.8) # Example configuration
        voice = PiperVoice.load("/home/geoffm/Downloads/en_US-joe-medium.onnx")
        syn_config = SynthesisConfig(
            volume=volume,         # volume
            length_scale=1.0,      # speed adjustment
            noise_scale=1.0,       # more audio variation
            noise_w_scale=1.0,     # more speaking variation
            normalize_audio=False, # use raw audio from voice - I don't hear the difference
        )
        with wave.open(out_file, "wb") as wav_file:
            # voice.synthesize_wav(msg, wav_file)
            voice.synthesize_wav(msg, wav_file, syn_config=syn_config)
        # voice.synthesize_wav(..., syn_config=syn_config)
        try:
            import playsound3
        except Exception as Error:
            dbug(f"{Error=} ... please install playsound3...")
            return
        playsound3.playsound(out_file)
        dbug("Done with piper...")
    if this_module == 'pyttsx3':
        # needs libespeak1 -- sudo apt install libespeak1
        # been having trouble with this one
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)   # rate is w/m
        engine.setProperty('volume', volume)
        engine.setProperty('voice', f'english-us+{gender}{tone}')
        # """--== Debugging ==--"""
        # """--== Process ==--"""
        engine.say(msg)
        engine.runAndWait()
    if prnt:
        printit(msg)
    # """--== Alternative ==--"""
    # google text to speach - sounds more realistic but only one voice (now) per language
    # to use CMI = gtts-cli | mpg123 -
    if this_module == 'gtts':
        # dbug(f"{this_module=}")
        from gtts import gTTS
        tts = gTTS(msg, lang='en', slow=False)
        filename = "output.mp3"
        tts.save(filename)
        # dbug(f"Saved? {filename=}")
        # """--== SEP_LINE ==--"""
        try:
            import playsound3
        except Exception as Error:
            dbug(f"{Error=} ... please install playsound3...")
            return
        playsound3.playsound(filename)
    return
    # ### EOB def sayit(msg, *args, prnt=True, **kwargs): ### #


# ################################
def printit(msg, *args, **kwargs):
    # ############################
    """
   purpose: prepares and prints (option) msg: str|list and can put in unicode color box, centered in terminal and with color
   required: msg: str|list (can contain color codes (see below)
   options:
        "boxed" | boxed=False  # prepares a box around msg
        "centered" | centered=False  # centers horizontally msg on a termial screen
        "shadowed" | shadowed=True  # adds a shadow typically around a box
        "prnt" | prnt=True  # print line(s) or just return them as a str
           (useful for input(printit("What do you want? ", 'centered', prnt=False, rtrn_type="str")))
        txt_center: int  # tells how many lines from the top to center within a list of lines
        txt_right: int  # tells how many lines from the top to justify to the right within a list of lines
        box_color: str  # eg "blink red on black"
        color: str  # eg "bold yellow on rgb(40,40,40)"
        title: str  # puts a title at top of a box
        footer: str  # puts a footer at the bottom of a box
           style: str  # to select box style - not fully functional yet
        shift: int  # how far to the left (neg) or to right (pos) to shift a centered msg
        width: int  # forces msg to fit in this width using text wrap 
        rtrn_type: "list" | "str"  # default is list
        function is pretty extensive...
        no_blanks: bool=False    # removes any blank lines if set to True
        ask: bool  # allows for asking about stopping after the printing - good for debugging when needed 
    notes:
        - This function will decode color "tags"
           eg msg = "my  message[blink red on black]whatever goes here[/]. The end or close tag will reset color")
    returns: msgs  # list [default] or str depending on rtrn_type
    """
    # """--== Debugging ==--"""
    # if "test" in msg or any("msg" in ln for ln in msg):
        # ddbug(f"{msg=} {funcname()} {called_from('verbose')} {args=} {kwargs=}")
    # ddbug(f"args: {args}")
    # ddbug(f"kwargs: {kwargs}")
    # """--== Config ==--"""
    centered_b = arg_val(['centered', 'center','cntr','cntrd'], args, kwargs, dflt=False)
    # if isinstance(msg, str) and len(msg)-len(msg.lstrip()) > 0 and centered_b: # for debugging
        # ddbug(f"{centered_b=} {called_from('v')}")
    txt_center = kvarg_val(['text_center', 'txt_center', 'txt_centered', 'txt_cntr', 'txt_cntrd', 'lines_centered', 'center_txt', 'cntr_txt'], kwargs, dflt=0)
    txt_right = kvarg_val(['txt_right'], kwargs, dflt=0)
    # ddbug(f"txt_center: {txt_center}")
    # if not isinstance(mycentered, bool):
    #     txt_center = mycentered
    my_prnt = arg_val('prnt', args, kwargs, dflt=True, opposites=['noprnt', 'no_prnt', 'no_print'])
    # ddbug(f"prnt: {prnt} {called_from()} {prnt=}")
    boxed_b = arg_val(['box', 'boxed'], args, kwargs, dflt=False)
    # if "test" in msg:
        # ddbug(f"{msg=} {boxed_b=} {called_from('v')} {my_prnt=}")
    box_color = kvarg_val(['box_color', 'box_clr', 'boxclr', 'border_color', 'border_style', 'bx_clr', 'bxclr'], kwargs, dflt="")
    # ddbug(f"{box_color=} {called_from('v')} {kwargs=}")
    title = kvarg_val(['title'], kwargs, dflt="")
    # ddbug(f"{title=}")
    footer = kvarg_val(['footer'], kwargs, dflt="")
    color = kvarg_val(['color', 'txt_color', 'text_style'], kwargs, dflt="")
    # dbug(color)
    # color_coded = arg_val(['clr_coded', 'colorized', 'color_coded', 'colored', 'coded'], args, kwargs, dflt=False)
    ignore_clr = arg_val(['ignore_clr'], args, kwargs, dflt=False)
    shadow = arg_val(['shadow', 'shadowed'], args, kwargs, dflt=False)
    style = kvarg_val(['style', 'box_style'], kwargs, dflt="round")
    width = kvarg_val(['width', 'length'], kwargs, dflt=0)
    # ddbug(f"width: {width}")
    columnize = arg_val(['columnize', 'columns'], args, kwargs, dflt=False)
    pad = kvarg_val(['pad'], kwargs, dflt=" ")
    shift = kvarg_val('shift', kwargs, dflt=0)
    # dbug(shift)
    rtrn_type = kvarg_val(['rtrn_type', 'rtrn'], kwargs, dflt='list')
    str_b = arg_val(["str", "string"], args, kwargs, dflt=False)
    if str_b:
        rtrn_type = "str"
    # end = kvarg_val('end', kwargs, dflt="\n")
    noblanks_b = arg_val(['noblank', 'noblanks','skipblanks', 'no_blanks', 'skip_blanks'], args, kwargs, dflt=False)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    # """--== Validate ==--"""
    # if isempty(msg):
    if not msg:
        dbug(f"Nothing to print msg: {msg} {called_from('verbose')}")
        return
    if not isinstance(columnize, bool):
        columnize = False
    #if not isinstance(width, int):
    #    width = 0
    # """--== Init ==--"""
    # ddbug(f"width: {width}")
    if isinstance(width, str) and width.endswith("%"):
        scr_cols = get_cols()
        scr_prcnt = int(width.replace("%", ""))/100
        width = math.ceil(scr_cols * scr_prcnt)
    else:
        width = int(width)
    title_len = 0
    footer_len = 0
    # """--== Convert (msgs to list) ==--"""
    # dbug(color)
    if 'pandas' in str(type(msg)):
        # dbug("pandas")
        msg = str(msg)
    if isinstance(msg, tuple):
        msgs = list(msg)
    if msg is None or len(str(msg)) == 0:
        # dbug(f"Nothing to do, msg is empty? ... msg: {msg}")
        return None
    if isinstance(msg, list):
        msgs = msg
    if isinstance(msg, float) or isinstance(msg, int):
        msg = str(msg)
    # dbug(type(msg))
    if isinstance(msg, str):
        # dbug(msg)
        if "\n" in msg or "\\n" in msg:
            # dbug(msg)
            # dbug("Splitting up msg on \n")
            msgs = msg.split("\n")
        else:
            # dbug(msg)
            msgs = [msg]
        # ddbug(f"columnize: {columnize}")
        # ddbug(f"width: {width}", 'ask')
        if not columnize and width > 0:
            msgs = gwrap(msgs, width-2)
            # ddbug(msgs)
        # dbug(msgs)
    if isinstance(msg, dict):
        # wip?
        msgs = []
        for k, v in msg.items():
            msgs.append(f"k: {k} v: {v}")
    if not isinstance(msgs, list):
        dbug(f"Failed to convert msg to list ...: type(msg): {type(msg)}... returning")
        return
    if noblanks_b:
        msgs = [msg for msg in msgs if not isempty(msg)]
        # dbug(msgs)
    # """--== Process ==--"""
    # ddbug(f"repr(msgs): {repr(msgs)}")
    color_coded = False  # init color_coded before test
    # color_coded = True  # init color_coded before test
    # ddbug(f"{ignore_clr=}")
    if not ignore_clr:
        for msg in msgs:
            # this is not fully tested, but seems to work... until we curl wttr....
            if re.search(r"\[.+?\].+\[/]", str(msg)):
                # ddbug(f"msg: {msg} appears to be color_coded")
                color_coded = True
    # ddbug(f"{color_coded=}")
    if color_coded:
        # ddbug("xlate_clr_codes on msgs")
        msgs = [clr_coded(msg) for msg in msgs]
    # for m in msgs:  # for debugging only
        # dbug(m)
    if columnize:
        msgs = gcolumnize(msg, width=width)
    # ddbug(f"{RESET}msgs: {msgs}")
    # ddbug(f"{color_coded=}")
    if boxed_b:
        title = str(title)
        # dbug(f"running boxed {msgs=} {footer=} {color=} {txt_center=} {style=} {pad=}")
        # ddbug(f"{ignore_clr=} {box_color=}")
        msgs = boxed(msgs, title=title, footer=footer, color=color, box_color=box_color, txt_center=txt_center, txt_right=txt_right, width=width, style=style, pad=pad, prnt=False, ignore_clr=ignore_clr)
        # dbug("print of boxed is finished")
    else:
        # ddbug(f"{RESET}msgs: {msgs} color: {color} boxed_b: {boxed_b}")
        if not isempty(color):
            # ddbug(f"working on repr(color): {repr(color)}")
            # COLOR = sub_color(color)  # TODO fix this so that it is not needed
            COLOR = gclr(color)  # TODO fix this so that it is not needed
            msgs = [COLOR + str(msg) for msg in msgs]
        # ddbug(f"boxed_b: {boxed_b}")
        # ddbug(f"{RESET}msgs: {msgs}")
        if title:
            title_len = parse_codes(title, 'nclen')
            # ddbug(f"{title=} {title_len=}")
        # if nclen(title) > 0:
        if title_len > 0:
            # ddbug(f"title: {title}")
            msgs.insert(0, title)
            # dbug(f"Just inserted title: {title} prnt: {prnt} msgs: {msgs}")
        if footer:
            footer_len = parse_codes(footer, 'nclen')
        # if nclen(footer) > 0:
        if footer_len > 0:
            msgs.append(footer)
        # ddbug(f"{RESET}msgs: {msgs}")
    # ddbug(f"msgs: {msgs}")
    if shadow:
        msgs = shadowed(msgs)
    # ddbug(f"{RESET}msgs: {msgs}")
    if centered_b:
        if isempty(msgs):
            dbug(f"msgs: {msgs} appears to be empty... {called_from()} returning....")
            return
        if boxed_b:
            msgs = centered(msgs, shift=shift)
        else:
            msgs = centered(msgs, shift=shift, width=width)
        # ddbug(f"{repr(msgs)=}")
    # dbug(prnt)
    # prnt = True
    if my_prnt:
        # dbug(boxed_b)
        # dbug(prnt)
        for ln in msgs:
            # ddbug(f"ln: [{ln}]")
            if not isempty(ln):
                # ddbug(f"{ln=}")
                print(ln)
        # [print(ln) for ln in msgs]
    # dbug(rtrn_type)
    if rtrn_type in ('str', 'string', 's'):
        # NOTE: If you made this invisible (not prnt) then you may want to add this option as well rtrn_type="str"
        # there are times when you want no prnt but still return lines (like in gcolumnize) so these two options need to be used carefully
        msgs = "\n".join(msgs)  # cinput() needs this to be a str
    if ask_b:
        # dbug(f"Stopping here to ask {ask_b=}")
        askYN()  # stop and ask if requested - developer may want to use this for debugging
    ask_b = None
    # dbug(boxed_b)
    # ddbug(f"prnt: {prnt} returning msgs: {msgs}")
    return msgs
    # #### EOB def printit(msg, *args, **kwargs): ### #


# ###################
def clr_coded(msg_s, *args, **kwargs):
    # ###############
    """
    purpose: takes any msg string containing tags for colors and decodes them into a colorized string
    options: 
        - prnt|dbug|verbose|show: bool|kwarg  DEFAULT=False
    requires: msg_s: str
    returnd: colorized string
    note: 
        - this uses gclr()
        - decodes a string - replace\\[color\\].*[\\/] with code and a RESET
    """
    # """--== Debugging ==--"""
    # ddbug(f"{called_from()}")
    # if 'STZ' in msg_s:
        # ddbug(f"{msg_s=} {called_from('verbose')}")
    # ddbug(f"args: {args}")
    # """--== Config ==--"""
    prnt = arg_val(['debug', 'dbug', 'verbose', 'prnt', 'show'], args, kwargs, dlft=False)
    test_b = arg_val(['tst', 'test'], [], kwargs, dflt=False)  # forces needing test=True to invoke this
    # """--== determine and insert reset ==--""" #
    this_reset = RESET
    val_s = str(msg_s)
    pat = r"(\x1b\[[\d\;]+m)"
    regex = re.findall(pat, str(val_s))
    if regex:
        this_reset = regex[0]
    # """--== untested ==--"""
    if test_b:
        import gtoolz_tsts
        gtoolz_tsts.clr_coded_tst()
        return
    if isinstance(msg_s, list):
        # this is not fully tested...
        new_l = [clr_coded(line) for line in msg_s]
        return new_l
    # """--== Init ==--"""
    # msg_s = str(msg_s).replace(r"[/]", RESET)
    msg_s = str(msg_s).replace(r"[/]", this_reset)
    colors = ['red', 'red!', 'black', 'black!', 'white', 'white!', 'grey', 'gray', 'cyan', 'cyan!',
              'magenta','magenta!', 'green','green!', 'blue', 'blue!', 'yellow', 'yellow!', 'brown', 'purple']
    pattern   = r'\[([ a-zA-Z!\(\0-9)]*)?\]'  # [(specific chars) ] # find anything that starts with \[ followed by any char that is not \[ upto \] grab substring group() between \[ and \]
    # """--== Process ==--"""
    match = re.findall(pattern, msg_s)
    if not match:
        # dbug(f"returning... no clr_coded tags found... {match=}")
        return msg_s
    # if resp:  # debugging only
        # ddbug(f"{resp=} this should be a list of what we want to test for colors")
    colors_set = set(colors)
    for color in match:
        # ddbug(f"{color=}")
        # dbug(f"{gclr(color)}color")
        clr_code = ''
        string_set = set(color.lower().split())
        if 'rgb' in color:
            # dbug(f"{color=} {called_from('verbose')}")
            clr_code = gclr(color)
        if string_set.intersection(colors_set):
            try:
                # ddbug(f"{color=} {called_from('verbose')}", 'ask')
                clr_code = gclr(color)
            except Exception as Error:
                if prnt:
                    ddbug(f"Error: {Error} ...please check your color tag")  # perhaps make this an option like kv_val
                pass
        # rplc_s = "[" + color + "]"
        rplc_s = "[" + color + "]"
        if not isempty(clr_code):
            msg_s = msg_s.replace(rplc_s, clr_code)
    if prnt:
        ddbug(f"returning repr(msg_s): {repr(msg_s)}")
    # """--== return ==--""" #
    # if 'STZ' in msg_s:
        # ddbug(f"{repr(msg_s)=}")
    return msg_s 
    # ### EOB def clr_coded(msg_s): ### #


# #################################################
def gclr(color='normal', text="", *args, **kwargs):
    # #############################################
    """
    Purpose: to return color code + text (if any) 
    requires:
        - color: str = 'normal'  # examples: gclr('red on black'), glcr('bold green on normal'), gclr('bold yellow! on red'), gclr('blink red on black') 
                                 # my_str = gclr("my [yellow!]yellow![/] is better than your yellow")
                                 # my_blue_str = gclr('rgb(0.0.180)', "this string is blueish")
                                 # ansi_code_for_bluish = gclr(0,0,180)  # yes this will work
    options:
        - text: str = ""         # if "" then the color code alone is returned 
        - reset: bool            # adds a color reset after the text
    returns: ansi color coded text
    notes:
        - color is the first argument because you may just want to return the color code only
        - uses xlate_clr()
    """
    # """--== Debug ==--"""
    # ddbug(f"funcname(): {funcname()}")
    # ddbug(f"We are in gclr(color: {color}) {text=} {called_from('v')} ")
    # dbug(f"{color=} {called_from('verbose')}")
    # """--== Validate ==--"""
    # this *should* never happen
    # """--== Config ==--"""
    reset_b = arg_val('reset', args, kwargs, dflt=False)  # add a RESET to the end of text
    text = arg_val(['text', 'txt', 'msg', 'message'], args, kwargs, dflt=text)  
    # prfx_b = arg_val(['prefex', 'prfx'], args, kwargs, dflt=True)
    bg_b = arg_val(['bg'], args, kwargs, dflt=False)
    rgb_b = arg_val(['rgb'], args, kwargs, opposites=['norgb'], dflt=True)
    # """--== Validate ==--""" #
    if isempty(color):  # and isempty(text):
        # ddbug(f"No repr(color): {repr(color)} was provided")  # repr(text): {repr(text)}... returning ...\"\"")
        return  ""
    # """--== Convert ==--""" #
    if isinstance(color, list) and len(color) == 3:
        color = f"rgb({color[0]},{color[1]},{color[2]})"
        text = ""
    if len(args) == 1 and isinstance(args[0], int) and isinstance(color, int) and isinstance(text, int):
        color = f"rgb({color},{text},{args[0]})"  # turn this into an rgb string - this is ugly but it seems to work
        text = ""
    # """--== Init ==--"""
    rtrn = ""
    orig_color = color
    STYLE_CODES = ""
    FG_CODE = ""
    BG_CODE = ""
    # PRFX2 = PRFX
    # fgbg_num = 38
    # if bg_b:
        # fgbg_num = 48
    # reset = prfx = ""
    # color = color.lower()
    fg = ''
    # bg = ''
    if text:
        color = color.strip()
    # ddbug(f"{color=} {text=}")
    text = str(text)
    # """--== Convert ==--"""
    if color == RESET:
        # ddbug(f"{color=} {text=} Looks like a RESET")
        return color  # we are done here
    # """--== rgb ==--""" #
    def this_rgb(color, *args, **kwargs):
        # ###############################
        # """--== Config ==--""" #
        prfx_b = arg_val(['prfx'], args, kwargs, dflt=True)
        # fg_b = arg_val(['fg'], args, kwargs, dflt=True)
        bg_b = arg_val(['bg'], args, kwargs, dflt=False)
        reset_b = arg_val(['reset'], args, kwargs, dflt=False)
        raw_b = arg_val(['raw'], args, kwargs, dflt=False)
        # dbug(f"{color=} {called_from('verbose')}", 'ask')
        # """--== Init ==--""" #
        prfx = ""
        if prfx_b:
            prfx = PRFX
        fgbg_num = 38
        if bg_b:
            fgbg_num = 48
        reset = prfx = ""
        if reset_b:
            reset = RESET
        if raw_b:
            end_with = ""
        else:
            end_with = "m"
        old_rgb_call_pat = r"^(\d+),\s*(\d+),\s*(\d+)$"
        old_rgb_match = re.search(old_rgb_call_pat, color)
        if old_rgb_match:
            r, g, b = map(int, old_rgb_match.groups())
            ansi_text = f"{prfx}{fgbg_num};2;{r};{g};{b}m"
            dbug(f"returning {ansi_text=}")
            return ansi_text  # because we are done
        if rgb_b:
            if reset_b:
                reset = RESET
            if prfx_b:
                prfx = PRFX
            my_text = color
            # dbug(f"{my_text=}")
            rgb_pat = r"rgb\((\d+),\s*(\d+),\s*(\d+)\)"
            match = re.search(rgb_pat, my_text)
            if match:
                # dbug(f"we have a match... {rgb_pat=} in {my_text=}")
                r, g, b = map(int, match.groups())
                rtrn = f"{prfx}{fgbg_num};2;{r};{g};{b}{end_with}"
                ansi_text = re.sub(rgb_pat, rtrn, dequote(my_text))
                # dbug(ansi_text)
                color = ansi_text + reset
            # dbug(f"{color=}")
        # dbug(f"returning {color=}")
        return color
        # ### EOB def this_rgb(color, *args, **kwargs) ### #
    # ddbug(f"{color=} {text=}")
    # """--== eob rgb ==--""" #
    clr = color
    if isinstance(clr, list):
        new_clr_l = []
        for my_clr in clr:
            my_clr_code = gclr(my_clr)
            new_clr_l.append(my_clr_code)
        # dbug(repr(new_clr_l))
        # """--== SEP_LINE ==--""" #
    # if clr.startswith(PRFX):
        # # dbug("clr starts with PRFX assuming it is already coded")
        # return clr
    # this is not fully tested, but seems to work... until we curl wttr....
    # dbug(f"{color=}")
    # """--== clr_coded ==--""" #
    if re.search(r"\[.+?\].+?\[/]", str(color)):
        # dbug(f"{color=} appears to be color_coded so making color=text and making color=''")
        # text = color
        # color = ""
        ansi_text = clr_coded(color)
        # dbug(f"returning {ansi_text=}")
        return ansi_text
    # if re.search(r"\[.+?\].+\[/\]", str(text)):
        # # dbug(f"Now {text=} is being checked for clr_coded tags text: {text} appears to be color_coded")
        # text = clr_coded(text)
        # return text
    # """--== Process ==--"""
    codes_l = parse_codes(color)['codes']
    codes_l = [code for code in codes_l if code != '']
    # assuming at this point that we were handed a color name to turn into ansi code
    clr = parse_codes(clr, 'escaped')
    if reset_b and not clr:
        return RESET
    if color == "":
        ddbug(f"color: {color} text: {text}.. returning just text...")
        return clr + text
    if color.lower() == 'reset' or color.lower() == 'normal':
        # ddbug(f"color: {color} text: {text}.. returning RESET ({repr(RESET)}) and text")
        return RESET + text
    # if PRFX in color:
        # dbug(f"Found either PRFX or PRFX2 in color: {repr(color)}")
        # ddbug(f"color: {color} text: {text}.. returning")
        # return color + text
    # ddbug(f"color: {color}", 'ask')
    # """--== Pull out and xlate STYLE ==--"""
    # dbug(f"{color=} {STYLE_CODES=}")
    if "fast_blink" in color or "flash" in color or "fast blink" in color or 'blink' in color:
        # dbug("we have to do this special case first - otherwise 'blink' will get pulled out incorrectly from 'fast_blink'")
        # STYLE_CODES += f"{PRFX}{styles_d['fast_blink']}m"
        STYLE_CODES += f"{styles_d['fast_blink']};"
        color = color.replace("fast_blink", "")
        color = color.replace("fast blink", "")
        color = color.replace("blink", "")
        color = color.replace("flash", "")
        # dbug(repr(STYLE_CODES))
    # ddbug(f"color: {color} {STYLE_CODES=}")
    for s in styles_d:
        # ddbug(f"chkg for style: {s} which was found in {styles_d=} in fg_color: {color}...")
        if s in color:
            # ddbug(f"found s: {s} in color: {color}")
            if s == "bold":
                continue
            fg = fg.replace(s, "").strip()
            # print(f"s: {s}")
            if s != 'normal':
                # STYLE_CODES += f"{PRFX}{styles_d[s]}m"
                STYLE_CODES += f"{styles_d[s]};"
            color = color.replace(s, "")  # pull out style
            # ddbug(f"STYLE_CODES: {repr(STYLE_CODES)}")
    # ddbug(f"{color=} {text=} ")
    # """--== Process split fg from bg ==--"""
    if color.startswith("on "):
        color = 'normal ' + color  # make fg = normal
        # print(f"myDBUG: funcname: {funcname()} lineno: {lineno()} color is now: {color}")
    # """--== Split color into fgbg_l ==--"""
    fg_color = bg_color = ""  # init these first
    fgbg_color = color.split(" on ")  # create a fgbg list split on " on "
    fg_color = fgbg_color[0]
    if len(fgbg_color) > 1:
        bg_color = fgbg_color[1]
    # ddbug(f"color: {color} splits into fg_color: {fg_color} and bg_color: {bg_color} {called_from('verbose')}", 'ask')
    # """--== Process FG_CODE ==--"""
    xlated_fg_color = xlate_clr(fg_color)
    # if xlated_fg_color == fg_color:
    #     dbug(f"no change {fg_color=}")
    # else:
    #     dbug(f"{xlated_fg_color=} {fg_color=}")
    # dbug(xlated_fg_color)
    FG_CODE = this_rgb(xlated_fg_color, prfx=True, bg=bg_b)  # prfx is true so that parse_codes below will work
    # dbug(FG_CODE)
    fg_color = parse_codes(FG_CODE, 'escaped')
    # dbug(fg_color)
    fg_color = fg_color.strip()
    # dbug(f"{fg_color=}")
    if fg_color:
        # dbug(fg_color)
        if fg_color.startswith("rgb("):
            FG_CODE = rgb(fg_color, prfx=True)
            inside_s = re.sub(r"rgb(\*?))", "\\1")
            dbug(inside_s)
            dbug(FG_CODE, 'ask')
        try:
            # fg_code = fg_colors_d[fg_color]  # fg_colors do not need "38"
            FG_CODE = fg_colors_d[fg_color] + "m"  # fg_colors do not need "38"
            # dbug(f"{FG_CODE=}", 'ask')
            # dbug(f"{FG_CODE}color{RESET}")
            FG_CODE = FG_CODE.lstrip(';')
        except Exception:  # as Error:
            # sometimes the code submitted is really wrong so just return - especially trying to parse out color coded msgs
            # dbug(f"Error: {Error} returning... {color=} repr(fg_color): {repr(fg_color)} failed {called_from('verbose')}...", 'noask')
            return orig_color # return it unchanged
    FG_CODE = FG_CODE.strip()  # trust me here if there was a style or just user included space we need to strip it off
    # ddbug(f"Test fg_color: [{fg_color}] {RESET}{PRFX}{FG_CODE}This should be in assigned fg_color {RESET}Here is the repr(FG_CODE): {repr(FG_CODE)}")
    # dbug(f"{FG_CODE=}")
    # """--== Process BG ==--"""
    # dbug(bg_color)
    xlated_bg_color = xlate_clr(bg_color)
    # dbug(xlated_bg_color)
    BG_CODE = this_rgb(xlated_bg_color, prfx=True, bg=True)  # prfx is true so that parse_codes below will work
    bg_color = parse_codes(BG_CODE, 'escaped')
    if bg_color:
        try:
            # dbug(f"{color=} {bg_color=}")
            BG_CODE = bg_colors_d[bg_color] + "m"  # bg_colors do not need "48"
            # dbug(f"{BG_CODE=}")
            # dbug(f"{BG_CODE}color{RESET}")
            BG_CODE = BG_CODE.lstrip(';')
        except Exception as Error:
            # sometimes the code submitted is really wrong so just return - especially trying to parse out color coded msgs
            # dbug(f"Error: {Error} returning... {bg_color=}) {repr(bg_color)=} failed {called_from('verbose')}...")
            return orig_color
    BG_CODE = BG_CODE.strip()  # just to make sure
    # ddbug(f"{color=} {text=} Test {bg_color=} {BG_CODE=} This should be in assigned bg_color {RESET} Here is the {repr(BG_CODE)=}")
    # """--== assemble everything together ==--""" #
    if FG_CODE.startswith(PRFX):
        # dbug(f"{FG_CODE=}")
        FG_CODE = FG_CODE.replace(PRFX, "")
    # dbug(f"{FG_CODE=}")
    FG_CODE = FG_CODE.rstrip("m")
    # dbug(f"{FG_CODE=}")
    if BG_CODE:
        FG_CODE += ";"
        BG_CODE = BG_CODE.lstrip(PRFX)
        if BG_CODE.startswith(PRFX):
            dbug(f"{BG_CODE=}")
            BG_CODE = BG_CODE.replace(PRFX, "")
    # ddbug(f"{color=} {text=} {rtrn=} {PRFX=} {STYLE_CODES=} {FG_CODE=} {BG_CODE=}")
    CODE = STYLE_CODES + FG_CODE + BG_CODE
    # ddbug(f"{CODE=}")
    if CODE != "":
        CODE = PRFX + STYLE_CODES + FG_CODE + BG_CODE
        CODE = CODE.rstrip(";")
        if not CODE.endswith("m"):
            CODE += "m"
    # ddbug(f"{CODE=}")
    rtrn = CODE + text
    # dbug(f"{rtrn}testtext{RESET}")
    # if " " in STYLE_CODES + FG_CODE + BG_CODE:
    #     rtrn = STYLE_CODES.replace(" ", "")
    #     rtrn = FG_CODE.replace(" ", "")
    #     rtrn = BG_CODE.replace(" ", "")
    # ddbug(f"{color=} {text=} {rtrn=}", 'ask')
    # if "on" in rtrn:
        # dbug(f"Problem: found 'on ' in rtrn: {rtrn}", 'ask')
    if reset_b:
        # dbug(reset_b)
        rtrn = rtrn + RESET
    # """--== Returning ==--""" #
    # ddbug(f"Returning {rtrn} {rtrn=}")  # ,'ask')
    return rtrn
    # ### EOB def gclr(color='normal', text=""): ### #


# ########################
def shades(color='white', num=16, *args, **kwargs):
    # ####################
    """
    purpose: returns a list of increasing intensity color shades
    requires = color: str|list
    options:
    -   num=16  <-- number to divide into 255 ~ the number of color intensities
    -   start: int=40  # start color value (0-255)
    -   rtrn: bool="colors"  # if you submit rtrn='code' or rtrn='codes' the ansi codes will be returned
    returns list # of ncreasing colors
    """
    # """--== debug ==--""" #
    # ddbug(f"{called_from('v')} {args=} {kwargs=}")
    # """--== Config ==--""" #
    color = arg_val(['color', 'shades'], args, kwargs, dflt=color)
    num = arg_val(["num", "length"], args, kwargs, dflt=num)
    rtrn_type = arg_val(['rtrn', 'rtrn_type'], args, kwargs, dflt='colors')
    start = arg_val(['start', 'start_val', 'min', 'min_val'], args, kwargs, dflt=40)
    # bg_b = arg_val(['bg'], args, kwargs, dflt=False)  # WIP TODO
    # """--== Init ==--""" #
    # dbug(f"{color=} {called_from('v')}")
    if "2" in color:  # convert (old) color_strings eg 'green2red'
        color = color.split('2')
    rtrn = []
    colors = []
    # my_color = ""
    # bg_color = ""
    if " on " in color:
        fg_color = color.split()[0]
        # bg_color = color.split()[2]  # TODO
        my_shades = fg_color 
    else:
        my_shades = color 
    # dbug(f"{my_shades=} {color=}")
    # """--== tri-color ==--""" #
    # dtype = data_type(my_shades)
    # dbug(f"{my_shades=} {dtype=}")
    # dbug(type(my_shades))
    if len(my_shades) == 3 and isinstance(my_shades, list):  # <-- tri-color start here
        # dbug(f"tri-color {my_shades=}")
        half_num = int(num / 2)
        clr1 = my_shades[0]
        clr2 = my_shades[1]
        clr3 = my_shades[2]
        # """--== 1st half ==--""" #
        shades1 = shades([clr1, clr2], half_num)
        # """--== 2nd half ==--""" #
        shades2 = shades([clr2, clr3], half_num)
        colors = shades1 + shades2
        clr_codes = [gclr(shade) for shade in colors]
        rtrn = clr_codes
        return rtrn  
    # """--== bi-color ==--""" #
    # dbug(my_shades)
    max_val = 255
    if len(my_shades) == 2:
        start_val = 0
    else:
        start_val = start
    diff = max_val - start_val
    # step = diff // num - 1
    # step = math.ceil(diff / num - 1)
    step = math.ceil(diff / num)
    # dbug(f"{step=} {num=} {diff=} {start_val=} {max_val=} {my_shades=}")
    if isinstance(my_shades, str):
        my_shades = [my_shades]
    shade_rgb = {
            'min_vals': [start_val, start_val, start_val],
            'black': [0,0,0],
            'white': [255,255,255],
            'red': [255,0,0],
            'r': [255,0,0],
            'green': [0,255,0],
            'g': [0,255,0],
            'blue': [0,0,255],
            'b': [0,0,255],
            'yellow': [255,255,0],
            'cyan': [0,255,255],
            'magenta': [255,0,255],
        }
    if len(my_shades) == 1:
        my_shades.append('min_vals')
        # dbug(my_shades)
    # dbug(my_shades)
    my_shades_rgb = [shade_rgb.get(item, item) for item in my_shades]
    # dbug(my_shades_rgb)
    my_shades = my_shades_rgb
    # dbug(my_shades, 'ask')
    # """--== SEP_LINE ==--""" #
    my_rgb = my_shades_rgb[0]
    trgt_rgb = my_shades_rgb[1]
    # dbug(f"{my_rgb=} {trgt_rgb=}  everything should be reset now")
    for n in range(1,num):
        # dbug(f"{n=} appending {my_rgb=} to colors {trgt_rgb=} {step=} {num=}")
        # dbug(f"{colors=} {called_from('v')}")
        colors.append(my_rgb.copy())
        # tst_l = [gclr(clr)+"#" for clr in colors]
        # dbug(f"Test: {''.join(tst_l)}")
        # """--== for color [0] ==--""" #
        if my_rgb[0] > trgt_rgb[0]:
            my_rgb[0] = my_rgb[0] - step 
            # dbug(f"{my_rgb[0]=} > {trgt_rgb[0]=} so decreasing by {step=} {my_rgb=}")
        if my_rgb[0] < trgt_rgb[0]:
            my_rgb[0] = my_rgb[0] + step
            # dbug(f"{my_rgb=} < {trgt_rgb[0]=} so increasing by {step=} {my_rgb=}")
        # """--== for color [1] ==--""" #
        if my_rgb[1] > trgt_rgb[1]:
            my_rgb[1] = my_rgb[1] - step
            # dbug(f"{my_rgb[1]=} > {trgt_rgb[1]=} so decreasing by {step=} {my_rgb=}")
        if my_rgb[1] < trgt_rgb[1]:
            my_rgb[1] = my_rgb[1] + step
            # dbug(f"{my_rgb[1]=} < {trgt_rgb[1]=} so increasing by {step=} {my_rgb=}")
        # """--== for color [2] ==--""" #
        if my_rgb[2] > trgt_rgb[2]:
            my_rgb[2] = my_rgb[2] - step
            # dbug(f"{my_rgb[2]=} > {trgt_rgb[2]=} so decreasing by {step=} {my_rgb=}")
        if my_rgb[2] < trgt_rgb[2]:
            my_rgb[2] = my_rgb[2] + step
            # dbug(f"{my_rgb[2]=} < {trgt_rgb[2]=} so increasing by {step=} {my_rgb=}")
    # dbug(f"And finally {n=} appending {my_rgb=} to colors {trgt_rgb=} {step=} {num=}")
    colors.append(my_rgb.copy())
    """--== SEP_LINE ==--""" #
    if rtrn_type in ('codes', 'code'):
        # dbug(colors)
        for c in colors:
            C_CODE = gclr(c)
            # dbug(f"{repr(C_CODE)=}", 'ask')
            rtrn.append(C_CODE)
        # rtrn = [dbug(gclr(clr)) for clr in colors]
        # rtrn = [gclr(clr, bg=bg_b) for clr in colors]
        # dbug("returning {rtrn=}, 'ask'")
        return rtrn
    if rtrn_type in ('clr', 'color', 'colors', 'clrs'):
        # dbug(f"returning {colors=}")
        return colors
    # dbug(f"{rtrn_type=} not sure how to handle this")
    return
    # ### EOB def shades(color, num=16): ### #


# ################################################################################################
def rgb(r=80, g=80, b=140, text="", *args, **kwargs):
    # ############################################################################################
    """
    purpose: translated rgb(r,g,b) text into ansii color CODE
    required: input: r, g, b, text
        r: int = 80
        g: int = 80
        b: int = 140
    options:
        - bg: bool = False # if set to true the color is applied to bg
        - text: str
        - prfx: bool=False
        - raw: bool=False   # no Prefix or ending 'm' - used internally by gclr()
    returns: rgb color coded text
    """
    # """--== Debugging ==--"""
    # ddbug(f"{called_from('v')} {args=} {kwargs=}")
    # """--== Config ==--"""
    text = arg_val(['text', 'txt'], args, kwargs, dflt=text)
    raw_b = arg_val(['raw'], args, kwargs, dflt=False)
    prfx_b = arg_val(['prfx', 'prefix', 'prfx_b'], args, kwargs, dflt=False)
    reset_b = arg_val(['reset'], args, kwargs, dflt=False)
    bg = arg_val(['bg',], args, kwargs, dflt=False)
    fg = arg_val(['fg',], args, kwargs, dflt=True)
    # ddbug(f"{raw_b=} {prfx_b=} {reset_b=} {fg=} {bg=}{RESET}")
    # """--== Init ==--""" #
    if isinstance(r, list) and len(r) == 3:
        # dbug(r)
        g = r[1]
        b = r[2]
        r = r[0]  # yep, you have to do this last
    rtrn = ""
    fgbg_num = ""
    reset = ""
    if isinstance(r, list) and len(r) == 3:
        g = r[1]
        b = r[2]
        r = r[1]
    if isinstance(r, str):
        dbug(f"{r=} is a string", 'ask')
    # """--== Process ==--"""
    # ddbug(f"{r=}")
    r = int(r)
    g = int(g)
    b = int(b)
    # if not raw_b:
        # RESET = PRFX + "0m"
    if fg and not bg:
        fgbg_num = 38
    # if prfx_b and not fg and not bg:
        # fgbg_num = 38
    if bg:
        # ddbug(bg)
        fgbg_num = 48
    prfx = ""
    end_with = "m"
    if reset_b:
        reset = RESET
    # reset = RESET
    if prfx_b:
        prfx = PRFX
    if raw_b:
        reset = ""
        end_with = ""
    rtrn += f"{prfx}{fgbg_num};2;{r};{g};{b}{end_with}{text}{reset}"
    # """--== Returning ==--""" #
    # ddbug(f"Returning {repr(rtrn)=}")
    return rtrn
    # ### EOB def rgb(r=80, g=80, b=140, text="", fg=False, bg=False, prfx=False, reset=False): ### #


# ####################################
def xlate_clr(color, *args, **kwargs):
    # ################################
    """
    purpose: translates special color names to rgb(r,g,b) for processing
    requires: special color eg:
    - greyXX | grayXX  # where XX is a precent gradient of gray from 0,0,0 for black! to 255,255,255 white
    - white!           # solid 255,255,255 white
    - black!           # solid 0,0,0 black
    - red!             # solid bright 255,0,0 red
    - green!           # solid bright 0,255,0 green
    - blue!            # solid bright 0,0,255 blue
    - yellow!          # solid bright 255,255,0 yellow
    - magenta!         # solid bright 255,0,255 magenta
    - cyan!            # solid bright 0,255,255 cyan
    returns: rgb(r,g,b) text string instead of supplied color
    """
    # """--== Debugging ==--"""
    # dbug(color)
    # """--== Config ==--"""
    rgb_b = arg_val(["all", "rgb"], args, kwargs, dflt=False)
    # --== Xlate special colors to rgb() ==--
    grey_tone = re.search(r"(gr[ea]y)(\d+)", color)
    # dbug(grey_tone)
    if grey_tone:
        grey_word = grey_tone[1]
        grey_tone = grey_tone.group(2)
        r = g = b = int(grey_tone)
        grey_color = f"rgb({r}, {g}, {b})"
        color = re.sub(f"{grey_word}{grey_tone}", grey_color, color)
        # ddbug(f"grey_color: {grey_color} TEST {RESET} repr(grey_color): [{repr(grey_color)}] {RESET} repr(color): {repr(color)} {RESET}")
    # """--== SEP_LINE ==--"""
    rgx = re.search(r"gr[ea]y", color)
    # If it is just "grey" or "gray"
    if rgx:
        # dbug(f"color: {color}")
        r = g = b = 100
        rgb_color = f"rgb({r},{g},{b})"
        color = re.sub(r"gr[ea]y", rgb_color, color)
        # dbug(f"repr(color): {repr(color)}")
    # dbug(f"color: {color} repr(color): {repr(color)} text: {text}")
    if 'bold' in color:
        color = color.replace("bold", "").strip() + "!"
    if 'white!' in color:
        r = g = b = 255
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('black!', myrgb)
    if 'black!' in color:
        r = g = b = 0
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('black!', myrgb)
    if 'red!' in color:
        r = 255
        g = 0
        b = 0
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('red!', myrgb)
    if 'green' in color:
        # doing this because the defailt green is more of a washed out brown
        r = 0
        g = 215
        b = 0
    if 'brown' in color:
        r = 150
        g = 75
        b = 0
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('brown', myrgb)
        # dbug(f"{color=} {r=} {g=} {b=}")
    if 'purple' in color:
        r = 128
        g = 0
        b = 128
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('purple', myrgb)
    if 'green!' in color:
        r = 0
        g = 255
        b = 0
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('green!', myrgb)
    if 'blue!' in color:
        r = 0
        g = 0
        b = 255
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('blue!', myrgb)
    if 'yellow!' in color or 'bold yellow' in color:
        r = 255
        g = 255
        b = 0
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('yellow!', myrgb)
    if 'magenta!' in color:
        r = 255
        g = 0
        b = 255
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('magenta!', myrgb)
    if 'cyan!' in color:
        r = 0
        g = 255
        b = 255
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('cyan!', myrgb)
    if 'white!' in color:
        r = 255
        g = 255
        b = 255
        myrgb = f"rgb({r},{g},{b})"
        color = color.replace('white!', myrgb)
    if rgb_b:
        if "white" == color:
            r = 255
            g = 255
            b = 255
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
        if "black" == color:
            r = 40
            g = 40
            b = 40
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
        if "red" == color:
            r = 205
            g = 0
            b = 0
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
        if "green" == color:
            r = 0
            g = 205
            b = 0
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
        if "blue" == color:
            r = 0
            g = 0
            b = 205
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
        if "cyan" == color:
            r = 0
            g = 255
            b = 255
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
        if "magenta" == color:
            r = 255
            g = 0
            b = 255
            myrgb = f"rgb({r},{g},{b})"
            color = color.replace('white!', myrgb)
    # ddbug(f"repr(color): {repr(color)}")
    return color
    # ### EOB def xlate_clr(color, *args, **kwargs): ### #


# ####################
def escape_ansi(line, *args, **kwargs):
    # ################
    """
    purpose: Removes ansii codes from a string (line)
    requires:
        line: str | list(of strings/lines)
    returns: "cleaned no_code" line(s)/string(s)
    notes:
        TODO: allow option to return clr_codes[1], nocode(elem), clr_codes[2]
        see: split_codes()
        aka: name should be escape_ansii
    """
    # """--== debugging`` ==--"""
    # ddbug(f"repr(line): {repr(line)}")
    # dbug(type(line))
    # """--== Validate ==--"""
    if isempty(line):
        # ddbug(f"line: [{line}]")
        return line
    # """--== SEP_LINE ==--"""
    if isinstance(line, list):
        new_lines = []
        for ln in line:
            new_lines.append(escape_ansi(ln))
        return new_lines
    # """--== Converts ==--"""
    line = str(line)  # this is needed
    # line = gclr("", line)  # this converts color coded strings to ansii coded first before stripping those codes below
    line = gclr(line)  # this converts color coded strings to ansii coded first before stripping those codes below
    # """--== Process ==--"""
    # ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    ansi_escape = re.compile(r'\x1b[^m]*m')  # suggested by chatGPT
    # ansi_escape2 = re.compile(r"\[\d+.*?m")  # not needed???????
    # ansi_escape2 = re.compile(r"(?:\x1b[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    # ansi_escape3 = re.compile(r"(?:\033[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    ncline = ""
    if isinstance(line, list):
        new_lines = []
        for new_line in line:
            if not isinstance(new_line, str):
                # dbug(new_line)
                new_lines.append(new_line)
            else:
                if isinstance(new_line, list):
                    if len(new_line) == 0:
                        new_line.append(" ")
                        # dbug(f"length of newline was 0 so now new_line: [{repr(new_line)}]... continuing...")
                        continue
                # new_lines.append(ansi_escape.sub("", new_line))
                new_line = ansi_escape.sub("", new_line)
                new_line = re.compile(r"\[\d+.*m")
                # new_line = ansi_escape.sub("", ncline)
                # dbug(new_line)
                # new_line = ansi_escape2.sub("", ncline)
                # dbug(new_line)
                new_lines.append(new_line)
                # new_lines.append(escape_ansi(new_line))
        ddbug(new_lines)
        return new_lines
    if isinstance(line, str):
        # rgx = re.findall(ansi_escape, line)
        # dbug(rgx)
        ncline = ansi_escape.sub("", line)
    return ncline
    # ### EOB def escape_ansi(line, *args, **kwargs): ### #

# ##############
def nclen(line, *args, **kwargs):
    # ##########
    """
    purpose: finds the length of a string minus any ansi-codes and returns that length
    returns: length
    note: (no_color) len of line (length w/o ansii codes)
    """
    # """--== Debugging ==--"""
    # ddbug(f"funcname(): {funcname()} called_from: {called_from()}")
    # ddbug(line)
    # dbug(type(line))
    # dbug(len(line))
    # my_dbug = False
    # """--== Config ==--"""
    # """--== Inits ==--"""
    nclen = 0
    # """--== Converts ==--"""
    line = str(line)
    # dbug(repr(line))
    # """--== Process ==--"""
    nc_line = escape_ansi(line)
    # dbug(repr(nc_line))
    my_len = 0
    for char in nc_line:
        my_len += 1
        if ord(char) > 60000:
            my_len += -1
    nclen = my_len
    # ddbug(f"returning nclen: {nclen}")
    return nclen


# ####################################
def parse_codes(msg, rtrn_type='dict', *args, **kwargs):
    # ################################
    """
    purpose: grab all ansi_codes from a string and return them - see below 
    requires:
        - msg: str      # line string that may or may not contain ansi_codes, codes are separated from the message string
    options:
        - rtrn: str     # default='dict'  a dictionary will be returned = {'codes': ['code1', 'code2', 'code3'...], 'strings': 'str1', 'str2', 'str3', 'str4',...]} 
                        # rtrn='list' returns the list of codes
                        # rtrn='string'|'str' returns string(s) joined as one string without codes
                        # rtrn='nclen'|'len' returns only thr length of the (joined) string without and codes
    returns:
        - default = {'codes': ['code1', 'code2',...], 'strings': 'str1', 'str2', ...]}
        - rtrn='list' = ['code1', 'code2', ...]
        - rtrn='string' = "".joined(['str1', 'str2', ...])
        - rtrn='len' = len("".joined(['str1', 'str2', ...]))
    notes:
        - this replaces the decrecated split_codes(), escape_ansi(), and nclen()
        - WIP
        - 20250826-1606
    """
    # """--== Local Import(s) ==--""" #
    # from gtoolz import clr_coded
    # """--== Config ==--""" #
    # ddbug(f"{rtrn_type=} {called_from('v')} {msg=}")
    rtrn_type = arg_val(["rtrn", "type", "rtrntype","rtrn_type"], args, kwargs, dflt=rtrn_type)
    # ddbug(f"{rtrn_type=}")
    # """--== Init ==--""" #
    # ddbug(f"{repr(msg)=}")
    rtrn = None
    # pat = r"\x1b\[[0-9;]+m"
    pat = r"\x1b\[[0-9;]*m"
    # ddbug(f"{pat=}")
    msg = str(msg)  # needed
    # """--== Convert ==--""" #
    msg = clr_coded(msg)  # translate any color code tags to ansi first
    # ddbug(f"{repr(msg)=}")
    # """--== Process ==--""" #
    codes_l = re.findall(pat, msg)
    if not codes_l:
        codes_l = ["",""]
        elems_l = [msg]
    else:
        elems_l = re.split(pat, msg)  # <--- fails but why? but needed...
    # ddbug(f"{elems_l=}")
    if len(elems_l) > 2:
        elems_l = [elem for elem in elems_l if elem]
        # dbug(f"tearing off each blank end {elems_l=}")
    # """--== Prepare rtrn ==--""" #
    if rtrn_type in ('dict', "d", "dictionary"):  # default
        rtrn = {'codes': codes_l, 'strings': elems_l}
    if rtrn_type in ('list', 'lst', 'l'):
        rtrn = codes_l
    if rtrn_type in ('string', 'str', 'joined', 'stripped', 'nocode', 'escaped', 'escape'):
        rtrn = "".join(elems_l)
    if rtrn_type in ('nclen', 'len', 'length'):
        rtrn = len("".join(elems_l))
        # dbug(type(rtrn))
    # ddbug(f"{rtrn_type=}")
    # """--== return ==--""" #
    # dbug(f"{rtrn_type=} {rtrn=} {repr(msg)=}" )
    return rtrn
    # ### EOB def parse_codes(msg, rtrn_type='dict', *args, **kwargs): ### #


# def pclen(*args, **kwargs):
#     msg = '\\x1b[m'
#     msg = gclr('reset')
#     dbug(f"{parse_codes(msg, 'escaped')=} {parse_codes(msg)=} {parse_codes(msg, 'nclen')=} {nclen(msg)=}", 'ask')
#     gline(RESET)
#     msg = RESET
#     dbug(f"{repr(msg)=} {parse_codes(msg, 'nclen')=} {gclr(msg)=} {gline(msg)=}")
#     dbug('ask')


# # ##################################
# def sub_color(clr, *args, **kwargs):
#     # ##############################
#     """
#     purpose: substiture ansi color CODE for given color
#     returns ansi-CODE
#     note: uses gclr()
#     """
#     # dbug(called_from())
#     # dbug(f"clr: {clr} repr(clr): {repr(clr)}")
#     # """--== Config ==--""" #
#     rset_b = arg_val(['reset', 'rst', 'rset'], args, kwargs, dflt=False)
#     # """--== Convert ==--""" #
#     if isinstance(clr, list):
#         new_clr_l = []
#         for my_clr in clr:
#             my_clr_code = sub_color(my_clr)
#             new_clr_l.append(my_clr_code)
#         # dbug(repr(new_clr_l))
#         return new_clr_l
#     if clr.startswith(PRFX):
#         # dbug("clr starts with PRFX assuming it is already coded")
#         return clr
#     # """--== SEP_LINE ==--""" #
#     if rset_b and clr == "":
#         return RESET
#     clr = parse_codes(clr, 'escaped')
#     if clr.upper() == "RESET" or clr.upper() == "NORMAL":
#         return RESET
#     COLOR_CODE = gclr(text="", color=clr)  # <-- rubber hits the road
#     # dbug(f"clr: {clr} COLOR_CODE [test]: {COLOR_CODE}[test] {repr(COLOR_CODE)}{RESET}")
#     return COLOR_CODE
#     # ### EOB def sub_color(clr, *args, **kwargs): ### #


def gwrap(text="", width=999, *args, **kwargs):
    """
    purpose:  experiment that splits line{s} of text into words/phrases.chunks not exceeding width
    requires:
        - text: str|list
        - width: int
    options:
        - prnt: bool
        - boxed: bool
        - title: str
        - footer: str
        - centered: bool
        - blanks: bool=False  # should blank lines be maintained
    returns: list of lines all with length less than or equal to stipulated width
    notes:
        - WIP
        - 20251117
    """
    # """--== debugging ==--""" #
    # dbug(f"{text=} {width=} {called_from()}")
    # """--== Config ==--""" #
    text = arg_val(['text', 'lines', 'content'], args, kwargs, dflt=text)
    width = arg_val(['width', 'length', 'len'], args, kwargs, dflt=width)
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    title = arg_val(['title'], args, kwargs, dflt="")
    footer = arg_val(['footer'], args, kwargs, dflt="")
    boxed_b = arg_val(['boxed', 'box'], args, kwargs, dflt=False)
    centered_b = arg_val(['cnetered', 'cneter', 'cntr'], args, kwargs, dflt=False)
    blanks_b = arg_val(['blanks','blank'], args, kwargs, dflt=False)
    # """--== Init/Convert (to a list) ==--""" #
    # text_dtype = data_type(text) 
    # dbug(text_dtype)
    if isinstance(text, str):
        text = [text]
    # dbug(text)
    processed_lines = []
    # text_dtype = data_type(text) 
    # dbug(text_dtype, 'ask')
    # """--== Process ==--""" #
    for line_num, line in enumerate(text):
        # dbug(f"Processing {line_num=} {line=} {processed_lines=}")
        if line.strip() == "" and blanks_b:
            # dbug("Preserve blanks...")
            processed_lines.append(" ")
            continue
            # """--== SEP_LINE ==--""" #
        bld_s = ""
        # dbug(f"{line=} {nclen(line)=}")
        # dbug(f"processing {line=}")
        words_l = line.split()
        # dbug(words_l)
        word_num = 0  # keep this! in case words_l is 0, trust me
        for word_num, word in enumerate(words_l):
            # dbug(f"processing {word=} {bld_s=} {processed_lines=}")
            if nclen(word) > width:
                # dbug(f"{word=} is too long {width=}...need to chunkit...{processed_lines=}")
                chunks = chunkit(word, width)
                # dbug(f"{chunks=} {bld_s=}",'ask')
                for chunk_num,chunk in enumerate(chunks):
                    to_add = f" {chunk}"
                    poss_line = (bld_s + to_add).strip()
                    if nclen(poss_line) < width:
                        bld_s = poss_line
                        if chunk_num + 1 == len(chunks):
                            # dbug(f"We must be at the end appending {poss_line=} and resetting {bld_s=}")
                            processed_lines.append(poss_line)
                            bld_s = ""
                        # dbug(f"{processed_lines=}... continuing to next chunk")
                        continue
                    else:
                        # dbug(f"appending {bld_s=} {nclen(bld_s)=} {to_add=}", 'ask')
                        # processed_lines.append(bld_s)
                        processed_lines.append(to_add.strip())
                        # bld_s = to_add.strip()
                    # dbug(f"{processed_lines=}")
            else:
                to_add = f" {word}"
                poss_line = (bld_s + to_add).strip()
                # dbug(f"{poss_line=} {nclen(poss_line)=} {width=}")
                if nclen(poss_line) < width:
                    # dbug(f"{poss_line=} {nclen(poss_line)=}")
                    bld_s = poss_line
                    if word_num + 1 == len(words_l):
                        # dbug(f"We must be at the end appending {poss_line=} restetting {bld_s=}")
                        processed_lines.append(poss_line)
                        bld_s = ""
                    continue
                else:
                    # dbug(f"appending({bld_s=}) {nclen(bld_s)=}", 'ask')
                    processed_lines.append(bld_s.strip())
                    bld_s = to_add.strip()
                # dbug(f"appending({bld_s=}) {nclen(bld_s)=}", 'ask')
                # processed_lines.append(bld_s)
                # bld_s = ""
        # dbug(f"{word_num=} {len(words_l)=}")
        if word_num + 1 == len(words_l):
            # dbug(f"we are on the next to the last elem {bld_s=} {to_add=} of {text=}")
            if bld_s:
                # dbug(f"Appending {bld_s=} to processed_lines")
                processed_lines.append(bld_s)
    # for line in processed_lines:
        # dbug(f"{line=} {nclen(line)=}")
    if prnt:
        # boxed_b = True  # for debugging
        printit(processed_lines, prnt=True, centered=centered_b, boxed=boxed_b, title=title + f"{width=}", footer=footer+dbug('here') )
    # """--== returning ==--""" #
    return processed_lines


# def OLDgwrap(text="", length=60, *args, **kwargs):
#     '''
#     purpose: to wrap standard text (words) and tries to preserve ansi colors - each line returnd being less than or equal to the declared length
#     requires:
#         - text: str
#         - length: int=60
#     options:
#         - prnt: bool=False       # primarily for testing
#         - boxed: bool=False
#         - centered: bool=False
#         - title: str=""
#         - footer: str=""
#         - box_color: str=""
#         - blanks: bool=False     # whether to leave blanks lines in           
#     returns:
#         - list of strings
#     note: 20241021 - this is a test function to replace wrapit()
#     '''
#     # """--== Imports ==--"""
#     # from gtoolz import nclen, RESET, clr_coded
#     # """--== Debugging ==--"""
#     # dbug(f"length: {length} {called_from()}", 'ask')
#     # dbug(args)
#     # dbug(kwargs)
#     # """--== Config ==--"""
#     prnt = arg_val("prnt", args, kwargs, dflt=False)  # make this True for debugging
#     boxed_b = arg_val(["box", "boxed"], args, kwargs, dflt=True)
#     title = arg_val(["title"], args, kwargs, dflt="")
#     footer = arg_val(["footer"], args, kwargs, dflt="")
#     centered_b = arg_val(["center", "centered", "cntr"], args, kwargs, dflt=False)
#     box_color = arg_val(["bxclr", "box_color", "box_clr", "boxclr"], args, kwargs, dflt="")
#     text = kvarg_val("text", kwargs, dflt=text)
#     blanks_b = arg_val(['blanks', 'blank'], args, kwargs, dflt=False) # because normally you are wrapping to reduce space used
#     # """--== Debugging ==--"""
#     # dbug(text)
#     # dbug(f"length: {length} {called_from()}", 'ask')
#     # """--== Validate ==--"""
#     if not isinstance(length, int):
#         dbug(f"Length (2nd argument) must be an integer length: {length} {called_from()}... returning...")
#         return
#     # if isempty(text):
#         # dbug(f"Submitted text is apparently empty ...{called_from()}")
#         # return
#     # """--== Init ==--"""
#     new_lines = []
#     # """--== Convert ==--"""
#     dtype = data_type(text)
#     # dbug(dtype, 'ask')
#     if dtype in ('lom', 'los'):
#         for elem in text:
#             # dbug(f"{elem=}")
#             this_l = gwrap(elem, length=length, blanks=blanks_b)
#             new_lines += this_l
#         if prnt:
#             # dbug(box_color)
#             printit(new_lines, boxed=boxed_b, centered=centered_b, title=title, footer=footer, box_color=box_color)
#             # printit(rtrn_l, 'boxed', title=f"debugging rtrn_l length: {length}", footer=dbug('here'))
#         return new_lines
#     # """--== working on a single line ie sentence ==--""" #
#     # ws_indxs = [i for i, char in enumerate(text) if char.isspace()]
#     # ws_indxs.append(len(text))
#     # last_ws = 0
#     # pre_last_ws = 0
#     # leftover_text = text
#     # for num, indx in enumerate(ws_indxs):
#     #     while last_ws < nclen(text):
#     #         dbug()
#     #         if indx > length:
#     #             pre_last_ws = indx
#     #             dbug()
#     #             my_phrase = leftover_text[pre_last_ws:ws_indxs[num-1]] 
#     #             dbug(my_phrase)
#     #         last_ws = indx
#     #         leftover_text = text[last_ws:]
#     # dbug(f"{pre_last_ws=} {last_ws=} {leftover_text=}",'ask')
#     # dbug(f"{ws_indxs=} {length=}", 'ask')
#     # dbug(f"{text=} {dtype=}")
#     my_text = clr_coded(text, 'noprnt')  # to translate color coded text
#     if isinstance(my_text, str):
#         lines = my_text.split("\n")
#     if isinstance(my_text, list):
#         if len(my_text) == 1:
#             # assumes ???
#             # dbug(data_type(my_text[0]))
#             lines = my_text[0]
#         else:
#             lines = my_text
#     # """--== Process ==--"""
#     # dbug(lines)
#     for line in lines:
#         blank_line = None
#         # dbug(blanks_b)
#         if line.strip() == "" and blanks_b:
#             this = " " + line
#             line[:length] # this is all ws so trim it to become a blank line fpr later
#             blank_line = this
#             # dbug(f"{blank_line=}")
#         # dbug(f"{line=}")
#         if not isinstance(line, str):
#             dbug(f"Bailing out line: {line} is not a string {called_from()}", 'ask')
#             return
#         prev_ws = 0
#         last_ws = 0
#         my_lines = []
#         my_last_line = ""
#         left_over = ""
#         # dbug(line)
#         for num, char in enumerate(line):
#             # dbug("this is kludgy but seems to work for now--it took a good deal of work to hammer this out")
#             my_codes = []
#             if len(my_lines) > 1:
#                 # dbug(my_lines[-1])
#                 my_last_line = my_lines[-1]
#             last_code = ""
#             # dbug(f"nclen(line): {nclen(line)} prev_ws: {prev_ws} last_ws: {last_ws} length: {length} num: {num}")
#             if char == " ":
#                 # dbug(f"continuing char == space OR num: {num} > length: {length}")
#                 last_ws = num
#                 continue
#             # dbug(f"nclen(line): {clen(line)} prev_ws: {prev_ws} last_ws: {last_ws} length: {length} num: {num}")
#             if num > 0:
#                 my_line = line[prev_ws:num]
#             else:
#                 my_line = line
#             my_line_len = parse_codes(my_line, 'nclen')
#             # dbug(f"{line=} {my_line=} {prev_ws=} {num=} {my_line_len=}")
#             # if nclen(line[prev_ws:num]) >= length:
#             if my_line_len >= length:
#                 # dbug(f"{my_line=} {nclen(my_line)=} {length=} {prev_ws=} {last_ws=} char {num=}")
#                 if last_ws == 0: # or my_line_len >= length:
#                     # dbug("ws not found we need to split this line... setting last_ws to length.")
#                     last_ws = length
#                 if prev_ws == last_ws:
#                     dbug(f"{prev_ws=} == {last_ws=}")
#                     last_ws += length
#                 dbug(f"so trim {line=} [{prev_ws=}:{last_ws=}] {my_text=}")
#                 my_text = line[prev_ws:last_ws].strip()
#                 # dbug(f"{my_text=} {nclen(my_text)=} {prev_ws=} {last_ws=} {length=}")
#                 # dbug(f"{my_line=} {nclen(my_line)=} {length=} {prev_ws=} {last_ws=} char {num=}")
#                 my_text_len = parse_codes(my_text, 'nclen')
#                 if my_text_len > 0 or (my_text_len > length and last_code == ""):
#                     # dbug(f"{my_last_line=} {nclen(my_last_line)=}")
#                     if len(my_lines) > 0:
#                         # my_codes = split_codes(my_last_line, 'all')
#                         my_codes = parse_codes(my_last_line, 'list')
#                         if len(my_codes) > 0:
#                             # dbug(my_codes[-1])
#                             last_code = my_codes[-1]
#                     # dbug(f"appending last_code: {last_code} and my_text: {my_text}")
#                     my_lines.append(last_code + my_text)
#                     last_code = ""  # re-init
#                 else:
#                     continue
#                 prev_ws = last_ws
#             left_over = line[prev_ws:].strip() # TODO do we want to do this?
#             # dbug(f"{length=} {line=} {prev_ws=} char num: {num=} {left_over=}")
#         left_over_len = parse_codes(left_over, 'nclen')
#         # if nclen(left_over) > 1:
#         if left_over_len > 0:
#             my_lines.append(left_over)
#         if blank_line is not None:
#             my_lines = [blank_line]
#         new_lines += my_lines
#     if prnt:
#         # dbug(text)
#         printit(new_lines, boxed=boxed_b, centered=centered_b, title=title, footer=footer, box_color=box_color)
#     # dbug(f"length: {length} returning new_lines len(new_lines): {len(new_lines)}")
#     # dbug('ask')
#     return new_lines
#     # ### EOB OLD def gwrap(text="", *args, **kwargs) ### #


def get_columns(*args, **kwargs):  # aka def scr_cols
    """
    purpose: gets screen/terminal cols AND, OR rows
    options:
        - rows: str    # return screen rows only
        - both: str    # return both cols, rows 
    returns int(columns)| int(rows: bool) | int(cols), int(rows) both: bool
    notes:
        - aka scr_dims()
        - I will likely rename this going forward to scr_dims()
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    shift = kvarg_val("shift", kwargs, dflt=0)
    rows_b = arg_val("rows", args, kwargs, dflt=False)
    both_b = arg_val("both", args, kwargs, dflt=False)
    # """--== Init ==--"""
    columns = 200
    num_rows = 40
    # """--== Validate ==--"""
    if not isinstance(shift, int):
        shift = 0
    # """--== Process ==--"""
    try:
        num_rows, columns = os.popen("stty size", "r").read().split()
    except Exception as e:
        print(f"Error: {e}")
    # print(f"returning columns: {columns}")
    if rows_b:
        return int(num_rows)
    if both_b:
        return int(columns), int(num_rows)
    columns = int(columns)
    # dbug(columns)
    # dbug(shift)
    columns = columns + int(shift)
    # dbug(f"Returning columns: {columns}", 'ask')
    return int(columns)
    # ### EOB def get_columns(*args, **kwargs): ### #



# alias
get_cols = get_columns
# scr_cols = get_columns # best to not do this as scr_cols get used often as a var
scr_dims = get_columns('both')


def replace_all(msg, with_d):
    """
    purpose: replaces every string in a dict key with dict value in a string
        with_d eg: {'\t', '  ', 'foo', 'bar'}
    example use could be to replace foul words with less offensive terms
    returns: str
    TODO need more doc info here
    """
    for i, j in with_d.iteritems():
        msg = msg.replace(i, j)
    return msg

def my_boxed(msgs, *args, **kwargs):
    # dbug(called_from())
    prnt = arg_val(["prnt"], args, kwargs, dflt=False)
    width = arg_val(["width", 'length'], args, kwargs, dflt=999)
    title = arg_val(["title"], args, kwargs, dflt="")
    footer = arg_val(["footer"], args, kwargs, dflt="")
    centered_b = arg_val(["centered"], args, kwargs, dflt=False)
    # blanks = arg_val(['blanks'], args, kwargs, dflt=True)
    # """--== SEP_LINE ==--""" #
    dbug(prnt)
    footer_len = nclen(footer)
    dbug(f"{footer_len=} {width=}")
    if "\n" in msgs:
        msgs = msgs.split("\n")
    # if isinstance(msgs, list):
    #     new_msgs = []
    #     for msg in msgs:
    #         # dbug(msg)
    #         # if msg.strip() == "":
    #             # dbug(msg)
    #             # msg = "X"
    #         # dbug(f"Append {msg=}")
    #         new_msgs.append(msg)
    # else:
    new_msgs = msgs
    dbug(msgs)
    r = gwrap(msgs,999)
    dbug(repr(r))
    rtrn = printit(gwrap(new_msgs, width), 'boxed', prnt=prnt, title=title, footer=footer, centered=centered_b)
    return rtrn


# ##############################################################################
def boxed(msgs="", *args, **kwargs):
    # ##########################################################################
    """
    purpose: draw a unicode box around msgs
    args: msgs: str|list
    options:
        centered: bool  # centers box on the screen
        prnt: bool      # default is False
        txt_center: int | list | tuple  # num of lines from top to center in the box - if list or tuple lines between first int and second int (inclusive) will be centered
        txt_right: int | list | tuple   # num of lines from top to justify to the right within the box- if list or tuple lines between first int and second int (inclusive) will be right justified
        color: str  # text color
        box_color: str  # color of border
        title, footer: str # goes in topline or bottom line centered of box
        width: int forces the width size defaults to # text gets wrapped to fit
        shadowed: bool # adds a shadow right and bottom
        pad: str       # defaults to " "
        top_pad: int   # number of lines to leave blank from the top
        bottom_pad: int   # number of lines to leave blank from the bottom up
        blanks: bool      # default is True - whether or not to include blank lines
        ... some other options; see below
    returns boxed lines: list
    NOTES: this function does not print - it returns the box lines
    """
    # """--== local imports ==--"""
    # """--== Debugging ==--"""
    # dbug(called_from())
    # dbug(msgs)
    # dbug(args)
    # dbug(kwargs)
    # dbug(f"{repr(msgs)=}")
    # """--== Config ==--"""
    padmin = kvarg_val(['padmin'], kwargs, dflt=1)
    color = kvarg_val(['color'], kwargs, dflt="")
    # ddbug(f"{color=}")
    title = kvarg_val(['title'], kwargs, dflt="")
    footer = kvarg_val(['footer'], kwargs, dflt="")
    style = kvarg_val(['style'], kwargs, dflt="single")
    centered_b = arg_val(["centered", "center", "cntrd", "cntr"], args, kwargs, dflt=False)
    prnt = arg_val(['prnt', 'print'], args, kwargs, dflt=False)
    shadowed_b = arg_val(["shadow", "shadowed"], args, kwargs, dflt=False)
    my_txt_center = 0
    txt_center = kvarg_val(["txt_center", "text_center", 'center_txt', 'centered_txt', 'cntr_txt', 'txt_cntr', 'txtcntrd', 'txt_cntrd'], kwargs, dflt=my_txt_center)
    # dbug(txt_center)
    strip_b = arg_val(['strip'], args, kwargs, dflt=True, opposites=['nostrip', 'no_strip'])
    # no_strip = arg_val(["nostrip", "no_strip"], args, kwargs, opposites=["strip"], dflt=False)  # default is to strip, used by {box_num=}gtable when centering columns
    txt_right = kvarg_val(["txt_right", "text_right", 'right_txt', 'rght_txt'], kwargs, dflt=0)
    # dbug(txt_right)
    box_color = kvarg_val(['bclr', 'bxclr', 'box_color', 'border_color', 'box_clr', 'border_clr', 'bx_clr', 'boxclr'], kwargs, dflt="")
    # dbug(f"{box_color=} {called_from('v')}", 'ask')
    shadow = kvarg_val(['shadow', 'shadowed'], kwargs, dflt=False)
    pad = kvarg_val(['pad'], kwargs, dflt=" ")
    # dbug(pad)
    top_pad = kvarg_val("top_pad", kwargs, dflt=0)  # "semi" (ie " ") blank lines to add at top
    bottom_pad = kvarg_val(["bottom_pad", "bot_pad", "botpad"], kwargs, dflt=0)  # "semi" (ie " ") blank lines to add to the bottom
    width = kvarg_val(["width", "w", "length", "l"], kwargs, dflt=0)
    # dbug(width)
    blanks_b = arg_val(['blank', 'blanks'], args, kwargs, dflt=True)
    # dbug(blanks_b)
    ask_b = arg_val("ask", args, kwargs, dflt=False)
    ignore_clr = arg_val(["ignore_clr_codes", "ignore_clr"], args, kwargs, dflt=False)  # TODO
    # ddbug(f"{ignore_clr=}")
    # """--== Init ==--"""
    # dbug(f"{type(msgs)=} {msgs=} ")
    if "%" in str(width):
        width = width.replace("%", "")
        scr_cols = get_columns()
        # dbug(scr_cols)
        width = int(scr_cols * (int(width)/100))
        # dbug(width)
    lines = []
    # PRFX = "\x1b["
    box_chrs = get_boxchrs(box_style=style)
    tl, hc, ts, tr, vc, ls, rs, ms, bl, bs, br = box_chrs
    try:
        pad = gclr(color) + str(pad)
    except Exception as Error:
        dbug(f"{color=} {Error=}")
    # """--== Validate ==--"""
    # dbug("Validating")
    # dbug(f"Validating {type(msgs)=} {msgs=} ")
    # if isempty(msgs):
    if not msgs:
        # dbug(f"msgs appears to be None or empty... msgs: {msgs}")
        # rtrn_box = printit("Nothing to print...", 'boxed', title=title, footer=footer + f" {dbug('here')}")
        return None
    # dbug(f"{msgs=}")
    # ddbug(f"{ignore_clr=}")
    # """--== Convert ==--"""
    dtype = data_type(msgs)
    # dbug(dtype)
    # dbug(f"{type(msgs)=} {msgs=} {dtype=}")
    # ddbug(f"{ignore_clr=}")
    if dtype in ("str"):
        msgs = msgs.split("\n")
    if dtype in ('file'):
        msgs = cat_file(msgs, 'lst')
    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(msgs, pd.DataFrame):
            msgs = printit(msgs, 'noprnt', ignore_clr=ignore_clr)
    if isinstance(msgs, list):
        # dbug(f"msgs: {msgs} is a list")
        new_msgs = []
        for msg in msgs:
            # dbug(f"working on repr(msg): [{repr(msg)}]")
            # dbug(f'replace blank lines with "  " msg: [{msg}]')
            # dbug(f"\n[msg]")
            # ruleit()
            # dbug(nclen(msg))
            # ddbug(f"{ignore_clr=} {msg=}")
            msg_len = parse_codes(msg, 'nclen')
            # if nclen(msg) == 0:
            if msg_len == 0:
                if not blanks_b:
                    # dbug(f"not accepting blanks... skipping {msg=}")
                    # msg = ""
                    continue
                else:
                    # continue
                    # dbug(f"replacing msg [{msg}] with '  ' ...")
                    msg = "  "
            # dbug(f"appending msg: [{repr(msg)}] new_msgs")
            new_msgs.append(msg)
        msgs = new_msgs
    if len(msgs) < 1:
        dbug(f"msgs: {msgs} appears empty... returning...")
        return
    if isinstance(msgs, int) or isinstance(msgs, float):
        msgs = str(msgs)
    # dbug(f"{type(msgs)=} {msgs=}")
    if isinstance(msgs, str) and "\n" in str(msgs):
        msgs = msgs.splitlines()
        # dbug(f"msgs: {msgs}")
    # dbug(type(msgs))
    # ddbug(f"{ignore_clr=} {msg=}")
    if isinstance(msgs, str):
        # dbug(type(msgs))
        if '\t' in msgs:
            msgs = msgs.replace('\t', '  ')
        # dbug(f"msgs: {msgs} type(msgs): {type(msgs)}")
        if '\n' in msgs:
            msgs = msgs.split('\n')
            # dbug(msgs)
        else:
            # cast it to list
            msgs = [msgs]
            # dbug(msgs)
    # dbug(f"{type(msgs)=} {msgs=}")
    if isinstance(msgs, list):
        msgs = [str(x) for x in msgs]
        msgs = [msg.replace('\t', '  ') for msg in msgs if msg != ""]  # replace tabs with spaces this took a while to figure out!
        # for msg in msgs:
        #     dbug(f"[{msg}]")
        if not blanks_b:
            new_msgs = []
            for msg in msgs:
                msg_len = parse_codes(msg, 'nclen')
                # if nclen(msg) == 0:
                if msg_len == 0:
                    continue
                # if escaped(msg).isspace():
                if parse_codes(msg, 'escaped').isspace():
                    continue
                new_msgs.append(msg)
            msgs = new_msgs
    # dbug(msgs)
    # ddbug(f"{ignore_clr=}")
    # dbug(f"{type(msgs)=} {msgs=}")
    # """--== Process ==--"""
    # dbug("Starting Process")
    max_msg_len = 0
    # dbug(f"{msgs=} {called_from('verbose')}")
    maxof_msgs = maxof(msgs)
    # dbug(maxof_msgs)
    max_msg_len = maxof_msgs
    title_len = parse_codes(title, 'nclen')
    # if nclen(title) > max_msg_len:
    if title_len > max_msg_len:
        # if len(title) is longer than max_msg_len...
        # max_msg_len = nclen(title)
        max_msg_len = title_len
    footer_len = parse_codes(footer, 'nclen')
    # if nclen(footer) > max_msg_len:
    if footer_len > max_msg_len:
        # if len(footer) is longer than max_msg_len...
        # max_msg_len = nclen(footer)
        max_msg_len = footer_len
    # dbug(max_msg_len)
    columns = get_columns()
    # ddbug(f"{ignore_clr=}")
    # dbug(width)
    # dbug(f"{type(msgs)=} {msgs=}")
    if width == 0:
        # dbug(width)
        reduce_by = 6  # is this arbitrary/or established by experiment?
        if shadow:
            reduce_by += 2
        if max_msg_len >= int(columns):
            max_msg_len = int(columns) - reduce_by
        width = (max_msg_len + 2 + (2 * padmin))  # or declared which makes max_msg_len = width - 2 - (2 * padmin)
        if width >= int(columns):
            width = int(columns) - reduce_by
    # ddbug(f"{ignore_clr=}")
    msg = title
    # dbug(width)
    topline = gline(width, lc=tl, rc=tr, fc=hc, msg=title, center=True, box_color=box_color, color=color)
    # dbug(topline)
    lines.append(topline)
    new_lines = []
    # """--== SEP LINE ==--"""
    # dbug(f"{type(msgs)=} {msgs=}")
    # printit(gwrap(msgs, width-4), 'boxed', title='debugging', footer=dbug('here'))
    # dbug('ask')
    # dbug("Looping through msgs")
    # ddbug(f"{ignore_clr=}")
    for m in msgs:
        # dbug(nclen(m))
        # dbug(width)
        working_width = (width - 4)
        # dbug(f"{working_width=} {m=}")
        m_len = parse_codes(m, 'nclen')
        # if nclen(m) > (width - 4) and m is not None:
        if m_len > (width - 4) and m is not None:
            wrapped_lines = gwrap(m, length=int(working_width), color=color)  # I discovered that the -x is needed for extra measure
            # ddbug(f"{m=}",'ask')
            if wrapped_lines is not None:
                for line in wrapped_lines:
                    if line is not None:
                        new_lines.append(line)
        else:
            # dbug(f"m: [{m}]")
            new_lines.append(m)
    # """--== SEP LINE ==--"""
    # dbug(f"{type(msgs)=} {msgs=}")
    # ddbug(f"{ignore_clr=}")
    # dbug(lines)
    if top_pad > 0:
        for n in range(top_pad):
            # adds semi blank lines at the top... spaces are needed because other functions will drop completely blank lines
            # this can be useful if you gcolumize boxes and then want to combine them into another 'parent' box
            # dbug(f"top line pad requested top_pad: {top_pad}")
            new_lines.insert(0, "   ")
    if bottom_pad > 0:
        for n in range(bottom_pad):
            new_lines.append("    ")
    # dbug(f"for cnt, msg in new_lines new_lines[:2]: {new_lines[:2]}")
    for cnt, msg in enumerate(new_lines):
        just = 'left'
        if txt_center != 0:
            cntr_start = 0
            if isinstance(txt_center, int):
                cntr_end = txt_center
            if isinstance(txt_right, (list, tuple)):
                cntr_start = txt_center[0]
                cntr_end = txt_center[1]
            if cnt >= cntr_start and cnt <= cntr_end:
                just = 'center'
                if strip_b:
                    msg = msg.strip()
            # dbug(f"here now {msg=}")
        # else:
            # doline_center = False
        if txt_right != 0:
            rght_start = 0
            if isinstance(txt_right, int):
                rght_end = txt_right
            if isinstance(txt_right, (list, tuple)):
                rght_start = txt_right[0]
                rght_end = txt_right[1]
            if cnt >= rght_start and cnt <= rght_end:
                just = 'right'
                msg = msg.strip()
        if msg.startswith(PRFX) and not msg.endswith(RESET):
            # dbug(repr(RESET))
            msg = msg + RESET
        # dbug(repr(msg))
        # ddbug(f"{msg=}")
        # dbug(pad)
        # line = gline(width, lc=vc, rc=vc, fc=" ", pad=pad, msg=msg.replace("\n", ""), box_color=box_color, center=doline_center, color=color)
        line = gline(width, lc=vc, rc=vc, fc=" ", pad=pad, msg=msg.replace("\n", ""), box_color=box_color, just=just, color=color, ignore_clr=ignore_clr)
        # dbug(line)
        # dbug(repr(line))
        lines.append(line)
    # dbug(f"{type(msgs)=} {msgs=}")
    # bottomline = doline(width, echrs=[bl, br], hchr=hc, footer=footer, box_color=box_color, color=color, center=True)
    # dbug(f"{box_color=} {color=} {hc=} {br=}", 'ask')
    bottomline = gline(width, lc=bl, rc=br, fc=hc, msg=footer, box_color=box_color, color=color, center=True)
    # dbug(bottomline)
    lines.append(bottomline)
    # if any("test" in ln for ln in lines):
        # dbug(f"{msgs=} {prnt=} {centered_b=} {called_from('v')}")
    # ddbug(f"{ignore_clr=}")
    # prnt = 1
    lines = printit(lines, prnt=prnt, centered=centered_b, shadowed=shadowed_b, txt_centered=txt_center, box_color=box_color, ignore_clr=ignore_clr)
    if ask_b:
        askYN()
    # ddbug(txt_center, 'ask')
    # if any(["test" in ln for ln in lines]):
    #     dbug("Winner winner gonna have soup for dinner")
    #     printit(lines, 'ask')  # debugging only
    #     dbug()
    return lines
    # ### EOB def boxed(msgs, *args, ..., **kwargs): ### #


# ##################################
def gline(*args, **kwargs):
    # ##############################
    """
    purpose: prints a line with msg with lots of options 
    requires: width: int OR msg: str
    options:
        - prnt: bool=Flase    # prints the output if True
        - width: int=0        # first argument ..this can be the simple string 'sep' to produce a separator line with width=60.
        - msg|title: str=""   # default=""  msg has to be a key=val pair! eg: gline(60, msg="My Message", just='center')
        - fc: str             # default=" " fill string/character (char(s) used to fill all surrounding space default: lc=rc=fc)
        - lc: str             # default=fc  left/edge/corner (char(s) for left corner ie first charater(s))
        - rc: str             # default=lc  right/edge/corner (char(s) for right corner ie last charcter(s))
        - pad: str            # default=""  string/character(s) on each side of msg
        - lpad: str           # default=pad
        - rpad: str           # default=lpad
        - box_color: str
        - color: str
        - lfill_color: str
        - rfill_color: str
        - just: str       # default = "left"|"l" but can be declared "center"|"c" or 'right'|"r"
    returns: line: str
    notes: this is used in boxed and several other functions - this is why prnt is default False
    """
    # dbug(f"{called_from('v')} {args=} {kwargs=}")
    # """--== Config ==--"""
    # this is so messy but it is to deal with old code that required width as the first arg
    prnt = arg_val(["print", "prnt", "show", "verbose"], args, kwargs, dflt=False)
    centered_b = arg_val(["centered", "center"], args, kwargs, dflt=False)  # this is so broken - it centers the text (just="c") and it centers the line only if printed TODO would need fixes all over
    msg = arg_val(['msg', 'message', 'title', 'text'], args, kwargs, dflt="")
    width = arg_val(['width', 'length', 'len'], args, kwargs, dflt=60)
    fc = arg_val(['fc', 'fill_chr', 'hc', 'fill'], args, kwargs, dflt=" ")
    just = kvarg_val(["just", "justification", 'justify'], kwargs, dflt='ljust')
    if len(args) > 0 and isnumber(args[0]):
        width = args[0]
    if len(args) > 0 and not isnumber(args[0]):
        # dbug("Set defaults for a simple string")
        msg = args[0]
        prnt = True
        fc="="
        just="c"
    # dbug(f"{width=} {msg=} {centered_b=} {fc=} {width=} {just=}")
    # """--== Special dealing with args[0] not being width ==--""" #
    # first... if this is a SPECIAL CALL simple text to be centered between fc="="
    # if isempty(args) and not isnumber(args[0]):
    # if isempty(args) and not isnumber(width) or len(args) > 0 and not isnumber(args[0]):
    # if isempty(args) or not isnumber(args[0]):
    #     # msg = width
    #     width = arg_val(['width', 'length', 'len'], args, kwargs, dflt=60)
    #     dbug(f"This is simple text {width=} {msg=} to be centered and fc='=' with width=60 by default")
    #     gline(width=width, msg=msg, fc="=", just="c", prnt=True, centered=centered_b)
    #     # dbug(f"Returning {width=} {msg=}")
    #     return
    # """--== SEP_LINE ==--""" #
    if len(args) > 0 and isnumber(args[0]):
        width = args[0]
    # dbug(f"{width=} {msg=} {called_from('v')}")
    # width = arg_val(['width', 'length', 'len'], args, kwargs, dflt=width)
    # msg = arg_val(['msg', 'message', 'title', 'text'], args, kwargs, dflt="")
    if isempty(kwargs) and not isnumber(width) and len(args) == 1:
        # dbug("this is simple text to be centered and fc='=' with width=60 by default - used as seperation line")
        gline(60, msg=width, fc="=", just="c", prnt=True)
        # dbug(f"Returning {width=} {msg=}", 'ask')
        return
    # dbug(f"{width=} {msg=}", 'ask')
    if '\n' in str(msg):
        dbug(f"{parse_codes(msg, 'nclen')} {called_from('verbose')}")
    # dbug(repr(msg))
    # fc = arg_val(['fc', 'fill_chr', 'hc', 'fill'], args, kwargs, dflt=" ")
    lc = arg_val(['lc', 'ec', 'echr'], args, kwargs, dflt=fc)
    rc = arg_val(['rc', 'tr', 'br', 're'], args, kwargs, dflt=lc)
    # dbug(f"{fc=} {lc=} {rc=}")
    boxed_b = arg_val(["boxed", "box"], args, kwargs, dflt=False)
    # title = kvarg_val(['title'], kwargs, dflt="")  # see msg above
    footer = kvarg_val(['footer'], kwargs, dflt="")
    box_color = arg_val(['box_color', 'box_clr', 'bxclr'], args, kwargs, dflt="")
    # dbug(f"{box_color=}")
    # color = kvarg_val(['color'], kwargs, dflt="reset")
    color = arg_val(['color'], args, kwargs, dflt="")
    # dbug(f"{color=} {kwargs=}")
    # dbug(f"Config... color: [{color}color_coded]{sub_color('reset')})")
    pad = kvarg_val(['pad'], kwargs, dflt="")
    lpad = kvarg_val(['lpad'], kwargs, dflt=pad)
    lfill_color = kvarg_val(['lfill_color'], kwargs, dflt=color)
    rpad = kvarg_val(['rpad'], kwargs, dflt=pad)
    rfill_color = kvarg_val(['rfill_color'], kwargs, dflt=color)
    # the order here for just is important
    # dbug(f"msg: {msg} just: {just}")
    if centered_b:
        # change just(ification) to 'center' - the bool val centered_ gets ignored after this
        just = 'c'
    just = kvarg_val(['ljust'], kwargs, dflt=just)
    ignore_clr = arg_val(['ignore_clr'], kwargs, dflt=False)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    # dbug(ignore_clr)
    # """--== SEP_LINE ==--""" #
    # dbug(f"{repr(msg)=} {parse_codes(msg, 'nclen')=} {called_from('v')} {prnt=}")
    if isinstance(width, str) and not width.endswith("%"):
        # in case the user gets the args mixed up
        msg = width
        # dbug(msg)
        width = 60  # arbitrary
        if fc == " ":
            fc = "="
        just = "center"
        prnt = True
        if msg in ["sep", " sep ", "separator", " separator "]:
            msg = pad + msg + pad
            # special call for separation line typically used in debugging... this is an ugly kludge
            # title_len = len(title)
            if not ignore_clr:
                msg_len = parse_codes(msg, 'nclen')
            else:
                msg_len = len(msg)
            my_width = 60
            # if int(title_len) > int(my_width):
            if int(msg_len) > int(my_width):
                # my_width = title_len + 10  # arbitrary
                my_width = msg_len + 10  # arbitrary
                fc = "="
            # print(msg.center(my_width, fc))
            # rtrn = gline(width=my_width, msg=" Separation Line ", just="c", prnt=False, centered=centered_b, boxed=boxed_b, fc="=", title=title, footer=footer)
            rtrn = gline(width=my_width, msg=" Separation Line ", just="c", prnt=False, ask=ask_b, centered=centered_b, boxed=boxed_b, fc="=", footer=footer)
            # dbug(rtrn)
            # dbug(f"Returning {width=} {msg=} {rtrn=}", 'ask')
            return rtrn
    # dbug(f"{repr(msg)=} {parse_codes(msg, 'nclen')=} {called_from('verbose')}")
    # """--== Init ==--"""
    if "%" in str(width):
        width = width.replace("%", "")
        scr_cols = get_columns()
        # dbug(scr_cols)
        width = int(scr_cols * (int(width)/100))
        # dbug(width)
    msg = str(msg)  # deals with int, floats, bool, etc
    llen = 0
    rlen = 0
    # """--== Process ==--"""
    if color == "":
        # color = 'reset'
        COLOR = RESET
    else:
        # ddbug(f"{color=}")
        COLOR = gclr(color)
        # ddbug(f"{repr(COLOR)=}")
    if box_color == 'reset':
        # box_color = 'reset'
        box_color = RESET
    # else:
        # BOX_COLOR = gclr(box_color)
    # dbug(box_color)
    BOX_COLOR = gclr(box_color)
    # dbug(BOX_COLOR+"is this color")
    # dbug(repr(BOX_COLOR))
    if lfill_color != "" or lfill_color != RESET:
        LFILL_COLOR = gclr(lfill_color)
    RFILL_COLOR = gclr(rfill_color)
    # dbug(f"{repr(RFILL_COLOR)}={rfill_color}")
    # """--== color_coded??? ==--"""
    # msg = clr_coded(msg)
    # dbug(msg)
    # dbug(f"{repr(msg)=} {parse_codes(msg, 'nclen')=} {called_from('verbose')}")
    if not ignore_clr:
        msg = gclr(msg)  # this does clr codes
    # dbug(f"{repr(msg)=} {parse_codes(msg, 'nclen')=} {called_from('verbose')}")
    # """--== eob color_coded ==--"""
    msg_len = parse_codes(msg, 'nclen')
    # if nclen(msg) > 0:
    if msg_len > 0:
        # nc_msg = escaped(msg)
        msg = lpad + msg + RFILL_COLOR + rpad
        # dbug(f"msg: [{msg}]")
    msg_len = parse_codes(msg, 'nclen')
    # dbug(f"{msg=}")
    flen = width - msg_len - len(rc) - len(lc)
    if just in ('center', "c", 'cntr'):
        llen = rlen = (flen // 2)
        diff = flen - (llen + rlen)
        rlen += diff
        # dbug(f"just: {just} width: {width} msg_len: {msg_len} diff: {diff} =  flen: {flen} - ( llen: {llen} - rlen: {rlen} )")
    if just in ('ljust', 'left', 'l'):
        # llen = len(lpad)
        llen = 0  # lpad has already been applied
        rlen = flen  # - len(rpad)  # ???? not sure about this.... 20220803
        # dbug(f"just: {just} width: {width} msg_len: {msg_len}  llen: {llen} = len(lpad): {len(lpad)}  rlen: {rlen} = flen: {flen} - len(lpad): {len(lpad)} len(rpad): {len(rpad)}")
    if just in ('rjust', 'right', 'r'):
        rlen = 0
        llen = flen
    # if nclen(msg) > 0:
    if msg_len > 0:
        # dbug(f"{fc=}{repr(msg)=} {llen=} {rlen=}")
        if fc == ' ':  # then treat it as a pad... use COLOR instead of BOX_COLOR
            LFILL_COLOR = RFILL_COLOR = COLOR
            line = BOX_COLOR +  lc + RESET + LFILL_COLOR + (fc * llen) +  COLOR + msg +  (fc * rlen) +  RESET +  BOX_COLOR + rc + RESET  # You need RESETs because COLORs may be blank
            # line = BOX_COLOR +  lc + RESET + LFILL_COLOR + (fc * llen) +  COLOR + msg + RESET + RFILL_COLOR + (fc * rlen) +  RESET +  BOX_COLOR + rc + RESET  # You need RESETs because COLORs may be blank
        else:
            line =  BOX_COLOR + lc + RESET + BOX_COLOR + (fc * llen) + RESET + COLOR + msg + RESET + BOX_COLOR + (fc * rlen) + rc + RESET
            # # LFILL_COLOR = RFILL_COLOR = COLOR
            # line =  BOX_COLOR + lc + RESET + BOX_COLOR + (fc * llen) + RESET + COLOR + msg + RESET + BOX_COLOR + (fc * rlen) + rc + RESET
            line =  BOX_COLOR + lc + RESET + BOX_COLOR + (fc * llen) + RESET + COLOR + msg + RESET + BOX_COLOR + (fc * rlen) + RESET + BOX_COLOR + rc + RESET
    else:
        # dbug(f"{msg=} appears empty ...{fc=} ex: top_line or bottom_line of a box")
        if fc and fc != " ":
            line = BOX_COLOR +  lc + (fc * llen) + (fc * rlen) + rc + RESET
            # line = BOX_COLOR +  lc + COLOR + (fc * llen) + (fc * rlen) + rc + RESET
        else:
            line = BOX_COLOR + lc + RESET + COLOR + (fc * llen) + (fc * rlen) + BOX_COLOR + rc + RESET
        # dbug(f"{msg=} appears to be empty")
    if prnt:
        printit(line, centered=centered_b, boxed=boxed_b, ask=ask_b, box_clr=box_color, footer=footer, ignore_clr=ignore_clr)
    # """--== returning ==--""" #
    # dbug(f"Returning {line=} {msg=} {parse_codes(msg, 'nclen')=} {fc=} {width=} {prnt=}")
    return line
    # ### EOB def gline(width=0, *args, **kwargs): ### #


# ###################################
def isnumber(elem, *args, **kwargs):
    # ##############################
    """
    purpose: determines if elem is a number even if it is a percent, or negative, or is 2k or 4b or 10M etc
             or test for stricktly float
    required:
        - elem: int or float or a list of elem- variable to be tested. If a list is submitted than all must pass or False will be returned
    options:
        - float:  bool   # default=False  specifically test if this a float
        - human:  bool   # default=False  the submission after stripping off "human" symbols like "M" or "G" or "%" etc
        - european: bool # default=False  whether commas are allowed
        - prnt: bool     # default=False  will show failure info
    returns: True|False
    notes: tests... pos, neg, floats, int, scientific, B(illion), T(trillions), G(ig.*) Kb(ytes|its), Mb(ytes)
        Can be used on financial data which often includes M(illions) or B(illions) if human option included
    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # dbug(elem)
    # dbug(elem, 'ask')
    # dbug(number)
    # dbug(args)
    # dbug(kwargs)
    # dbug(repr(x))
    # dbug(type(x))
    # """--== Config ==--"""
    float_b = arg_val(["flt", "float"], args, kwargs, dflt=False)
    human = arg_val(["human", "H", "h"], args, kwargs, dfault=False)
    european = arg_val(["european", "europ"], args, kwargs, dflt=False)
    prnt = arg_val(["prnt", "show", 'verbose', 'print'], args, kwargs, dflt=False)
    # """--== Validate ==--"""
    if elem is None:
        # dbug(x)
        if prnt:
            dbug(f"elem: {elem} failed as a number")
        return False
    #"""--== Init ==--"""
    # orig_number = elem
    # number = escaped(str(elem)).strip()  # strip off any ansi codes/color codes
    number = parse_codes(str(elem), 'escaped').strip()  # strip off any ansi codes/color codes
    # number = number.lstrip("-")
    # """--== recycle ==--""" #
    if isinstance(elem, list):
        # dbug(f"elem: {elem}")
        for item in elem:
            if not isnumber(item, human=human, float=float):
                if prnt:
                    dbug(f"item: {item} failed as a number")
                return False  # at least one failed
        return True  # they all passed
    # """--== Process ==--"""
    # number = escaped(number).strip()
    number = parse_codes(number, 'escaped').strip()
    if "e-" in number:
        # dbug(f"number: {number} might be scientific or just bogus, either way we are skipping it and calling it a False number")
        return False
    if not any(char.isdigit() for char in number):
        return False
    number = re.sub("[BGMKT%e]$", "", number)  # clean off Human symbols
    # dbug(f"{orig_number=} {number=}", 'ask')
    if european:
        number = number.replace(",", "")
    if float_b:
        try:
            float(number)
            return True
        except ValueError:
            if prnt:
                dbug(f"number: {number} failed as a float")
            return False
    # number = escaped(str(number)).strip()
    number = parse_codes(str(number), 'escaped').strip()
    # dbug(x)
    number = str(number).strip()
    if number.startswith(("-", "+")):
        number = number.lstrip(r"[+-]")
    number = number.replace('.', '', 1).replace(",", "").replace("e-", "", 1)  # .replace("%", "", 1)
    # dbug(repr(x))
    r = number.isdigit()  # the final test!
    # """--== Returning ==--""" #
    # if "3.77" in str(orig_number) or "T" in str(orig_number):  # debugging only
        # dbug(f"{orig_number=} {number=} {elem=} ...Returning: {r=} {called_from('verbose')}", 'ask')
    return r
    # ### EOB def isnumber(x, *args, **kwargs): ### #


# ###################################################
def get_boxchrs(box_style="single", *args, **kwargs):
    # ###############################################
    """
    purpose: given a box_style (ansi, single, solid, double) will return a set of chars for creating a box
    input: box_style: str
    return:
        [tl, hc, ts, tr, vc, ls, rs, ms, bl, bs, br]  as a list in the order shown
    Note: boxed() uses this
        tl = top_left, hc=horizontal_char, ts=top_separator, tr=top_right, vc=vertical_char,
        ls=left_separator, rs=right_separator, ms=middle_separator
        bl=bottom_left, bs=bottom_sep, br=bottom_right
    aka: box_type, boxchrs
    """
    box_color = kvarg_val("box_color", kwargs, dflt="")
    # reset = sub_color('reset')
    reset = RESET
    box_chrs = [9484, 9472, 9516, 9488, 9474, 9500, 9508, 9532, 9492, 9524, 9496]
    if box_style == 'none':
        box_chrs = [" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " "]
    if box_style == 'ascii':
        box_chrs = ["+", "=", "=", "+", "|", "|", "|", "|", "+", "=", "+"]
    if box_style == "single":
        # box_chrs = [tl, hc, ts, tr, vc, le, re, ms, bl, bs, br]
        box_chrs = [9484, 9472, 9516, 9488, 9474, 9500, 9508, 9532, 9492, 9524, 9496]
    if box_style == "solid":
        box_chrs = [9487, 9473, 9523, 9491, 9475, 9507, 9515, 9547, 9495, 9531, 9499]
    if box_style == "double":
        box_chrs = [9556, 9552, 9574, 9559, 9553, 9568, 9571, 9580, 9562, 9577, 9565]
    box_chrs = [chr(n) for n in box_chrs]
    if box_color != "":
        # you should avoid this becuase every char gets wrapped with color codes
        box_chrs = [box_color + c + reset for c in box_chrs]
    # Note: these are printed with chr(XXXX)
    # tl, hc, ts, tr, vc, ls, rs, ms, bl, bs, br = box_chrs
    return box_chrs


def flattenit(my_l):
    """
    purpose: "flattens nested lists
    options: none
    returns: list
    note: see flatten_d() to flatten a dict of dict (dod)
    """
    flatlist = []
    for elem in my_l:
        # dbug(f"Working on elem: {elem}")
        # if type(elem) == list:
        if isinstance(elem, list):
            # dbug(f"flattening elem: {elem}")
            flatlist += flattenit(elem)
        else:
            flatlist.append(elem)
        # dbug(f"Now flatlist: {flatlist}", 'ask')
    # dbug(flatlist)
    return flatlist
    # ### EOB def flattenit(my_l): ### #


# ###############################################
def flatten_d(my_d, colname="", *args, **kwargs):
    # ###########################################
    """
    purpose: takes a dictionary of dictionaries and flattens it into a list of lists
    requires:
        - a dictionary of dictionaries
            eg {"AMD": {'previousClose': 11.32, 'open': 112.89, "bid": 116.11, "ask": 116.18},
            "NVDA": {'previousClose': 424.05, 'open': 430.33, "bid": 444.40, "ask": 444.50},
            ...}
        - the column name for the first level
    options:
        - prnt: bool       # default=False - pront gtable of the rows before returning - primarily used for debugging
        - centered: bool   # default=False - only works when print option is True; this will center the gtable
        - title: str       # default=""    - only works when print option is True; adds a title
        - footer: str      # default=False - only works when print option is True; adds a footer
    returns: rows of columns ie data in the form of a list of list, aka an lol
    """
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "print", "show", "verbose"], args, kwargs, dflt=False)
    centered_b = arg_val(['center', "centered", "cntr"], args, kwargs, dflt=False)
    title = kvarg_val(["title"], kwargs, dflt="")
    footer = kvarg_val(["footer"], kwargs, dflt="")
    # """--== Process ==--"""
    rows = []
    for key, value in my_d.items():
        row = []
        if rows == []:
            colnames_l = list(value.keys())
            colnames_l.insert(0, colname)
            rows.append(colnames_l)
        if isinstance(value, dict):
            row.append(key)
            for sub_k, sub_v in value.items():
                row.append(sub_v)
        rows.append(row)
    if prnt:
        gtable(rows, 'prnt', 'hdr', centered=centered_b, title=title, footer=footer)
    return rows


# #####################################
def fixlol(my_lol=[], *args, **kwargs):
    # #################################
    """
    purpose: makes the length or every "row" in a list of lists the same number of elements (length)
             and trims off all white space (with or without a newline) to the option blank value (default is None, see options)
    options:
        - length: int             # defaults to the length of the first row ie len(my_lol[0]) for all subsequent rows (it will truncate a row)
        - blank: str=" "          # defaults to " " but can be any string eg blank="..."  - this replaces a blank line with the declared str
        - transpose|pivot: bool   # default=False - if set to True the lol will be transposed or pivoted before returning
        - check: bool             # returns only True (all rows are the same length) or False (not all rows are the same length)
    returns: fixed lol with all rows the same length (number of elements)
    notes:
        - used by gtable with option "fix"
        - used by gcolumnize
    """
    # """--== Debugging ==--"""
    # dbug(f"{funcname()} called_from: {called_from()}")
    # dbug(my_lol[:3])
    # """--== Config ==--"""
    # max_lst = max(my_lol, key=len)
    # length = len(max_lst)
    # length = len(my_lol[0])
    length = max(len(x) for x in my_lol)
    # length = kvarg_val(["len", "length"], kwargs, dflt=len(my_lol[0]))  # num of colnames(ie my_lol[0]) or what is declared
    length = kvarg_val(["len", "length"], kwargs, dflt=length)  # num of colnames(ie my_lol[0]) or what is declared
    length = int(length)
    blanks = kvarg_val(["blank", "blanks", "pad"], kwargs, dflt=" ")
    pivot_b = arg_val(["pivot", "pivot_b", "transpose", "pvt"], args, kwargs, dflt=False)
    chk_b = arg_val(['chk', 'check','test','tst'], args, kwargs, dflt=False)
    # dbug(f"chk_b:{chk_b}", 'ask')
    # """--== Validate ==--"""
    # dbug(my_lol)
    if isempty(my_lol):
        dbug(f"User supplied my_lol: {my_lol} is empty... called_from: {called_from()} returning")
        return
    new_lol = []
    dtype = data_type(my_lol)
    if dtype == "loD":
        # dbug(f"Running fix_loD on {my_lol=} {data_type(my_lol)=} {called_from('v')}")
        my_lol = fix_loD(my_lol)
        dtype = data_type(my_lol)
        # dbug(f"{dtype=}", 'ask')
    if not islol(my_lol):
        # dbug(f"my_lol does not appear to be an lol {dtype=}... {called_from('v')}...")
        # dbug(my_lol, 'boxed')
        if isinstance(my_lol, list):
            for row in my_lol:
                new_row = []
                # dbug(f"{row=}")
                if isinstance(row, list):
                    for item in row:
                        dbug(f"{item=}")
                        new_row.append(str(item))
                    new_lol.append(new_row)
        this_lol = [row[:20] for row in new_lol]
        # gtable(this_lol, 'prnt', 'boxed', 'hdr', 'noask', col_limit=10, title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        # this_lol = [row[21:40] for row in new_lol]
        # gtable(this_lol, 'prnt', 'boxed', 'hdr', 'noask', col_limit=10, title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        # this_lol = [row[41:60] for row in new_lol]
        # gtable(this_lol, 'prnt', 'boxed', 'hdr', 'noask', col_limit=10, title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        # this_lol = [row[61:80] for row in new_lol]
        # gtable(this_lol, 'prnt', 'boxed', 'hdr', 'noask', col_limit=10, title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        # this_lol = [row[81:] for row in new_lol]
        # gtable(this_lol, 'prnt', 'boxed', 'hdr', 'ask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        for row in this_lol:
            dbug(row, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
            dbug(f"{len(row)=} {len(this_lol[0])=}")
            for elem in row:
                printit(elem, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        dtype = data_type(my_lol)
        if dtype != "lol":
            # dbug(my_lol)
            # dbug(f"{dtype=} {called_from('v')}", 'ask')
            return my_lol
    cols_len = len(my_lol[0])
    if not chk_b and all(len(row) == cols_len for row in my_lol):
        # dbug(f"No work needed... Looks like all the rows are == row[0] len(my_lol[0]):{len(my_lol[0])} {called_from('verbose')}")
        dtype = data_type(my_lol)
        # if dtype != "lol":
            # dbug(f"{dtype=}", 'ask')
        return my_lol
    # else:
    #     dbug(f"Work is needed as the lengths vary {called_from('verbose')}....")
    #     for n, row in enumerate(my_lol):
    #         if len(row) != cols_len:
    #             dbug(f"{n} row: {row} len(row):{len(row)} != cols_len:{cols_len}")
    # """--== Process ==--"""
    my_lol = [row for row in my_lol if row]  # get rid of blank rows
    my_lol = [row[:length] for row in my_lol]  # truncate all rows first
    if chk_b:
        # dbug("chkg lengths")
        len_firstrow = len(my_lol[0])
        if not all([len(row) == len_firstrow for row in my_lol]):
            cnt = 0
            for row in my_lol:
                if len(row) != len_firstrow:
                    dbug(f"row:{row} has diff len from len_firstrow: {len_firstrow}")
                    cnt += 1
            dbug(f"Error cnt: {cnt} out of rows: {len(my_lol)} do not have the same length as the firstrow")
            # dbug(f"problem with lengths of rows... {called_from('verbose')} ...returning False", 'ask')
            dtype = data_type(my_lol)
            dbug(f"{dtype=}", 'ask')
            return False
        dbug("Everything looks good {called_from('verbose')}... returning True")
        dtype = data_type(my_lol)
        if dtype != "lol":
            dbug(f"{dtype=}", 'ask')
        return True
    else:  # debugging only
        len_firstrow = len(my_lol[0])
        # if not all([len(row) == len_firstrow for row in my_lol]):
        #     dbug(f"problem with lengths of rows... {called_from('verbose')}", 'ask')
    # now pad each row with None
    for num, row in enumerate(my_lol):
        # dbug("make sure there are enough cols")
        while len(row) < length:
            # dbug(f"{len(row)=} {length=}")
            try:
                my_lol[num].append(blanks)
            except Exception as Error:
                dbug(f"{Error=} {data_type(my_lol)=} {islol(my_lol)=} {my_lol=} {called_from('v')}")
        new_row = []
        for n, col in enumerate(row):
            if len(row) > length:
                dbug(f"Row number: {n} truncating row len(row) to the length of the first row: length: {length}")
                new_row = row[length]
            if str(col).isspace():
                # if it is all white space just make it what blanks are suppose to be
                # dbug(f"replacing col: {col} with blanks: {blanks}")
                col = blanks
            else:
                # peel away all white space on either side - this allow easier matching for filterby and sortby patterns etc
                col = str(col).strip()
            new_row.append(col)
        row = new_row
    if pivot_b:
        # list(map(list, zip(*msg_l))  # to pivot??? 
        my_lol = pivot(my_lol)
    dtype = data_type(my_lol)
    if dtype != "lol":
        dbug(f"{dtype=}", 'ask')
    return my_lol
    # ### EOB def fixlol(my_lol=[], *args, **kwargs): ### #


# ###########################################
def drop_col(data, pattern, *args, **kwargs):
    # #######################################
    """
    purpose: drop a col if all values match pattern(s)
               OR
            if any column name matches a provided pattern (in this case it works the same as filter_cols
    requires: 
        - data: lol         # first row must be colnames
        - pattern: st|list
    options:
        - none       
    returns: lol
    notes:
        - WIP
        - this calls filter_cols which might as well be named exclude_cols
    """
    # """--== debugging ==--""" #
    # dbug(f"{called_from()=} {data=} {pattern=}")
    # dbug(len(data[0])
    # dbug(data[0])
    # dbug(pattern)
    # """--== config ==--"""
    # colnames = arg_val(["colnames", "columns"], args, kwargs, dflt=[])
    # """--== validate ==--"""
    if isempty(data):
        dbug(f"data: {data} appears to be empty...{called_from('verbose')}...")
        return
    # if isempty(pattern):
    #     dbug(f"pattern: {pattern} appears to be empty...{called_from('verbose')}...")
    #     return data
    if any([len(row)!=len(data[0]) for row in data]):
        dbug(data,'lst')
        dbug("Problem with data...",'ask')
        return
    # """--== convert ==--"""
    # dtype = data_type(data)
    # dbug(f"{dtype=} {called_from('v')}")
    if not data_type(data, 'lol'):
        data = cnvrt(data)
    if isinstance(pattern, str):
        pattern = [pattern]
    colnames = data[0]
    if any([col=="" for col in colnames]):
        new_colnames = []
        for num,col in enumerate(colnames):
            if str(col).strip()=="":
                col = f"col{num}"
                if "" in pattern:
                    pattern.append(f"col{num}")
            new_colnames.append(col)
        colnames = new_colnames
        data[0] = colnames
    colnames = data[0]
    colnames = [parse_codes(colname, 'escaped') for colname in colnames]
    # dbug(pattern)
    # dbug(colnames)
    # """--== process ==--"""
    drop_cols = []
    for indx, col in enumerate(colnames):
        col_values = []
        for row in data[1:]:
            try:
                col_values.append(row[indx])
            except Exception as Error:
                dbug(Error)
                dbug(data,'lst')
                dbug(row,'ask')
        # col_values = [escaped(row[indx]) for row in data[1:]]
        # dbug(col_values)
        for pat in pattern:
            # dbug(f"{pat=}")
            try:
                if all(re.search(str(val), str(pat)) for val in col_values):
                    # dbug(col)
                    drop_cols.append(col)
            except Exception:  #  as Error:
                # dbug(Error)
                pass
            if pat == col:
                drop_cols.append(col)
    # dbug(drop_cols,'ask')
    # gtable(data, 'prnt', 'hdr', title="debugging", footer=dbug('here'))
    my_data = filter_cols(data, drop_cols)
    # dbug(my_data)
    # dbug(my_data[0])
    # """--== return ==--"""
    # gtable(my_data, 'prnt', 'hdr', title="debugging", footer=dbug('here'))
    return my_data
    # ### EOB def drop_col(data, pattern, *args, **kwargs): ### #


# ###################################################
def select_rows(data, selectrows_d, *args, **kwargs):
    # ###############################################
    """
    purpose: selects specific rows where the value in a column name one member of a provided list
        - eg select rows from a long  list ofcuerrencies where the 'Symbol'  matches one from a provided list eg {'Symbol': ["USD-JPY", 'GBP=USD', 'EUR-USD', 
    requires:
        - data: lol           # list or row/columns oe a list of lists
        - selectrows_d: dict  # {'colname1': [pattern1,pattern2,...], colname2: [pattern1, [pattern2,...]} 
           - consider: if you want the colnames row included then incluse the colname itself in the patterns
    options:
        - prnt: str | bool
    returns:
        - lol
    notes:
        - WIP
    """
    # dbug(called_from('verbose'))
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "print", "show", "verbose"], args, kwargs, dflt=False)
    # """--== Validate ==--"""
    if not data_type(data, 'lol'):
        dbug(f"data must be an lol {data_type(data)}")
        return
    if not isinstance(selectrows_d, dict):
        dbug("selectrows_d must be a dictionary or colnames: [pattern, ...]")
        return
    # """--== Init ==--"""
    # selectrows_d = {}
    # """--== Process ==--"""
    colnames = data[0]
    new_rows = []
    for row in data:
        # dbug(row, 'ask')
        for colname, pat_l in selectrows_d.items():
            if colname not in colnames:
                dbug(f"Failed to find {colname=} in {colnames=}... {called_from('verbose')} ...returning")
                return
            col_indx = colnames.index(colname)
            # dbug(col_indx)
            for pat in pat_l:
                # dbug(f'pat: {pat} row[col_indx]: {row[col_indx]}')
                if pat in str(row[col_indx]):
                    # dbug(row)
                    new_rows.append(row)
                    break
    gtable(new_rows,  'hdr', 'centered', prnt=prnt, title='debugging', footer=f"{dbug('here')} {called_from('verbose')}", drop_col='nan', neg=True)
    # """--== return ==--"""
    return new_rows
    # ### EOB def select_rows(data, selectrows_d, *args, **kwargs): ### #


# #############################################
def filter_cols(my_data, pat, *args, **kwargs):
    # #########################################
    """
    purpose: accepts data as rows of columns and uses (list or string) pattern(s) to exclude or drop columns where colname matches pattern
    requires: 
        - data: list of lists        # 
        - pat: list or str           # pattern(s) is treated as a regex (uses re.search...)
    options: none
    returns: lol (list of rows minus cols excluded based on pattern(s))
    notes:
        - WIP
        - should rename this to exclude_cols
    """
    # from gtoolz import cnvrt, isempty, called_from
    # """--== Debugging ==--"""
    # dbug(called_from('verbose'))
    # """--== Validate ==--"""
    if isempty(my_data):
        dbug(f"my_data appears empty {called_from('verbose')}")
        return
    if isempty(pat):
        return my_data
    # """--== Convert ==--"""
    dtype = data_type(my_data)
    # dbug(dtype)
    # be careful here this can easily become a fatal recursion
    if dtype != 'lol':
        # dbug(f"Submitted data must be a list of lists (lol) data_type(my_data): {dtype} {called_from('verbose')}")
        my_data = cnvrt(my_data)
        dtype = data_type(my_data)
        # return
    # else:
        # my_table = my_data
    if isinstance(pat, str):
        # dbug(f"turned pat: {pat} into a list")
        pat = [pat]
    # """--== Init ==--"""
    exclude_idxs = []
    colnames = my_data[0]
    # colnames= [str(escaped(colname)) for colname in colnames]
    colnames= [str(parse_codes(colname, 'escaped')) for colname in colnames]
    my_lol = []
    if isinstance(pat, str):
        pat = [pat]
    # """--== SEP_LINE ==--"""
    for rgx in pat: 
        rgx = str(rgx)
        # dbug(rgx)
        # dbug(colnames)
        exclude_idxs += [indx for indx, col in enumerate(colnames) if re.search(rgx, str(col))]
    # dbug(exclude_idxs)
    # for indx in exclude_idxs:  # debugging
        # dbug(colnames[indx])
    if exclude_idxs == []:
        return my_data
    for row in my_data:
        new_row = []
        for indx, col in enumerate(row):
            if indx not in exclude_idxs:
                new_row.append(col)
        my_lol.append(new_row)
    # dbug(len(my_lol))
    # dbug(f"returning my_lol without cols which might have pat: {pat} in it")
    return my_lol


# ###################################
def cnvrt(data, *args, **kwargs):
    # ###############################
    """
    purpose: accepts any type of "data" (ie str|list|pandas|list of dictionaries|csv_file_name etc) and converts to a list of lists (ie lol)
    options:
        - colnames: list|str      # list of colnames or string eg: "firstline"|"firstrow" declares that the firstrow is already the colnames
        - delimeter: char         #  if a filename is su:wqpplied (assumes a csv type file) this delimiter will be used to separate column values
        - fix: bool=True          # will "fix" all the rows of an lol to the length (number of columns or elements) of the first row 
        - blanks: str|None        # default=None blanks sets the string for elements added in row when fix option is used
        - index: bool             # default=False
        - purify: bool            # default=True - strips off comments (purifies based on the '#' symbol) before processing
        - selected: list          # list of colnames to include
        - sortby: str|tuple|list  # colname to sortby (default ascending) if the string has a comma then it will be split into a list first with colname and order(ascend or descend)
                                  # if sortby is a tuple, or list, or contains a comma and second elem is in ("desc", 'descend', 'reverse', 'rev')
                                  # then sorting will be reversed
        - filterby: dict          # dictionary with {'colname': 'pattern'} for rows to include
        - filterout: dict         # dictionary with {'colname': 'pattern'} for rowa to exclude
        - excluded_cols: str|list # pattern(s) used to exclude columns 
        - cols_limit: int         # sets max column size
        - no_prcnt: bool          # default=False - whether to strip off percent symbol
        - ci: bool=False          # case insensite, only applies to filterby
        - human: bool|list        # convert  numbers to a human readable number eg 6.35B - list of colnames or bool=all 
        - rtrn: str               # default = 'lol' ie list of lists... other options eg rtrn='df', rtrn="lod" (list of dictionaries)
        - neg: bool | list        # colors neg numbers to default red, if it is a list of column names then only those columns will be colorized
        - drop_col: str|list      # pattern(s) where if every value in a column matches pattern(s) then drop the column eg drop_col=['nan', 'NaN']
        - tail" int               # if this int is > 0 then the first row (colnames) will remain and the last tail rows of the lol will be retained
    returns: 
        - default: a list of lists (rows of columns) with the first row having colnames
    notes: 
        - problem if a "#" is in a line, it will truncate it as it thinks the ramaining part of the line is a comment # TODO need to fix this
        - TODO: change this to just cnvrt and use it to create df, lol, lod, dod etc ...  DONE but untested and the func should be renamed to cnvrt or cnvrt_data...
            - there is an alias defined below for this function to 'cnvrt'
    """
    # """--== Debugging ==--"""
    # dbug(f"{called_from('v')} {data=}", 'ask')
    # dbug(type(data))
    # dbug(f"data[:3]: {data[:3]} {called_from()}")
    # dbug(data)
    # dbug(args)
    # dbug(kwargs)
    # """--== Import ==--"""
    # import pandas as pd
    # """--== Config ==--"""
    prnt = arg_val(['prnt','verbose','print','show'], args, kwargs, opposites=['quiet'], dflt=False)
    colnames = kvarg_val(["colnames"], kwargs, dflt=[])
    # dbug(f"supplied colnames: {colnames}")
    delimiter = kvarg_val(["delim", "delimiter"], kwargs, dflt=",")
    # fix_b = arg_val("fix", args, kwargs, dflt=False)
    fix_b = arg_val("fix", args, kwargs, dflt=True)
    blanks = kvarg_val(["blank", "blanks"], kwargs, dflt=" ")
    index_b = arg_val(["indx", 'index', "indexes"], args, kwargs, dflt=False)
    purify_b = arg_val(["purify", "purify_b", "decomment"], args, kwargs, dflt=True)
    selected_cols = kvarg_val(["selected_cols", "selected", "fields", "cols", 'select'], kwargs, dflt=[])  # TODO
    # dbug(selected_cols)
    excluded_cols = kvarg_val(['excluded_cols', 'excludedcols', 'xcld_cols', 'excdcols', 'exclude', 'excluded', 'exclude_cols', 'filter_cols'], kwargs, dflt=[])
    # dbug(excluded_cols)
    filterby = kvarg_val(["filterby"], kwargs, dflt={})  # 
    filterout = kvarg_val(["filterout"], kwargs, dflt={})  #
    sortby = kvarg_val(["sortby", "orderby"], kwargs, dflt="")  # 
    # dbug(sortby)
    col_limit = kvarg_val(["col_limit", 'col_size', 'col_max', "collimit", "colmax"], kwargs, dflt=0)
    wrap_b = arg_val(['wrap', 'wrapit'], args, kwargs, dflt=False)
    strip_b = arg_val(['wrap', 'wrapit'], args, kwargs, dflt=False)
    # dbug(wrap_b)
    ci_b = arg_val(["case_insensitive", "ci", "ignore_case", "ic", "ci_b"], args, kwargs, dflt=False)
    pivot_b = arg_val(['pivot', 'pivot_b', 'invert', 'transpose'], args, kwargs, dflt=False)
    # dbug(pivot_b)
    human = arg_val(['human', 'H', 'h'], args, kwargs, dflt=False)
    # dbug(human)
    # rnd = arg_val(['rnd', 'round'], args, kwargs, dflt=False)
    rnd = kvarg_val(['rnd', 'round'], kwargs, dflt="")
    # dbug(rnd)
    neg = arg_val(['neg'], args, kwargs, dflt=False)
    # dbug(f"{neg=} {called_from('v')}")
    my_dropcol = arg_val(['dropcol', 'drop_col', 'drop_cols', 'drop_cols'], args, kwargs, dflt=[])
    rtrn_type = kvarg_val(['rtrn', 'rtrn_type', 'rtn'], kwargs, dflt='lol')  # TODO this is WIP to make this a universal cnvrt() func
    interval = arg_val(['interval'], args, kwargs, dflt=0) 
    tail = arg_val(['tail', 'last'], args, kwargs, dflt=0)
    # """--== Validate ==--"""
    if isempty(data):
        dbug(f"data: {data} seems to be empty... {called_from('verbose')} returning...")
        return
    # """--== Init ==--"""
    dtype = data_type(data)  # this is essential!
    # dbug(f"{dtype=} {data=} {called_from('v')}")
    post_selected = []
    lol = []
    usr_colnames = []
    orig_colnames = []
    if not isempty(colnames):
        usr_colnames = colnames
        # dbug(usr_colnames)
    my_fname = ""
    # """--== deal with doD misaligned dictionaries ==--"""
    # if dtype in ("doD"):
    #     # dbug(f"Not sure how to best handle this dtype: {dtype} as the dictionaries are different sizes... so I am printing each included Dictionary as a table w/title=key")
    #     for k,v in data.items():
    #         gtable(v, 'prnt', 'hdr', title=k, footer=dbug('here'), colnames=colnames)
    #     return
    # """--== deal with lol no conversion needed ==--"""
    # if dtype == 'lol':
    if 'lol' in dtype:
        lol = data
        # dbug(lol[:3])
    # """--== deal with str which maybe a filename using cat_file ==--"""
    # if dtype in ('fname', 'sqlite_file', 'file', 'dat_file', 'csv_file'):
    if 'file' in dtype:
        my_fname = data  # now this can be used later... see: rtrn_type = 'sqlite' below
        # dbug(f"First test for fname? data: {data} dtype: {dtype} called_from: {called_from()}")
        rows_lol = cat_file(data, delim=delimiter, purify=purify_b)
        # dbug(rows_lol[:2])
        lol = [[str(item).strip() for item in row] for row in rows_lol]  # just in case; csv files don't properly handle this
        dtype = data_type(lol)
    # """--== deal with json ==--"""
    # dbug(f"{dtype=} testing for json {called_from('v')} ...", 'ask')
    if  "json" in dtype:
        dtype = "json"
        dbug(f"Looks like json data {dtype=} we need to test to see if this is a list with a single dict entry {data=}", 'ask')
        import json
        r = json.loads(data)
        if isinstance(r, list) and len(r) == 1:
            data = r[0]
        else:
            # dbug("further research needed...")
            dtype = (data_type(r))
            if 'dict' in dtype or  'dod' in dtype:
                # dbug("this is acceptible as a json dict", 'ask')
                data = r
            else:
                if not isempty(r):
                    dbug(f"What kind of json is this? {r=} {data_type(r)=} {called_from()}", 'ask')
                    if 'lol' in dtype:
                        return r
    # dbug(f"dtype: {dtype} data_type(lol): {data_type(lol)} lol[:2]: {lol[:2]} {called_from()}")
    # dbug(f"{lol=}")
    # """--== deal with df ==--"""
    flag_done = False
    # if dtype in ('df'):
    if 'df' in dtype:
        df = data
        # if 'pandas' not in sys.modules:
        try:
            import pandas as pd
        except Exception as Error:
            dbug(Error)
        if isinstance(df, pd.core.series.Series):
            df = df.to_frame()
        has1col = len(df.columns) == 1
        hasindex = not isinstance(df.index, pd.RangeIndex)  # this is black magic
        def indx_consecutive(df):
            """Checks if the DataFrame index is consecutive."""
            # dbug(df.head(), 'ask')
            index_values = df.index.values.tolist()
            if not all([isnumber(val) for val in index_values]):
                return False
            # dbug(index_values)
            if len(index_values) == 0:
                # dbug(len(index_values))
                return True
            expected_index = range(index_values[0], index_values[-1] + 1)
            return list(index_values) == list(expected_index)
        # dbug(df.info)
        # dbug(df.head())
        if has1col and hasindex:
            # dbug(f"do we care about has1col: {has1col} hasindex: {hasindex}")
            # ddbug(f"type(df):{type(df)}")
            lol = [[df.index[n], str(item)] for n,item in enumerate(df[df.columns[0]].to_list())]
            # lol.insert(0, ['-key-', '-val-'])
            # dbug(lol)
            # dbug(orig_colnames)
            # gtable(lol, 'prnt', title=f"debugging has1col: {has1col} and hasindex: {hasindex}", footer=dbug('here'))
            # dbug(lol[:3])
            # dbug('ask')
            flag_done = True  # I do not like this but it is needed below...
        else:
            # df = data  # now df = data I really don't like this TODO
            indexname = df.index.name
            if not isempty(indexname) and ("date" in indexname.lower() or "time" in indexname.lower()):
                df.reset_index(inplace=True)  # turn the index into first column
            # dbug(indexname)
            if isempty(indexname) or indexname == "id":
                df.index.name = "id"
                indexname = df.index.name
                if index_b:
                    df = df.reset_index()
            # dbug(orig_colnames)
            # """--== rubber hits the road here ==--"""
            if not index_b:
                # dbug(f"hasindex: {hasindex} index_b: {index_b}")
                df = df.reset_index(drop=True)  # avoid using inplace=True
                lol = df.values.tolist()  # rubber hits the road
            else:
                # dbug(f"hasindex: {hasindex} index_b: {index_b} make sure the index gets included into the df.tolist()")
                df_reset = df.reset_index()  # puts in the standard df index and moves current index to col1
                lolwindex = df_reset.values.tolist()
                # dbug("now strip out the first col")
                lol = [row[1:] for row in lolwindex]
                # dbug(lol[:2], 'ask')
                # dbug(f"after index added lol[:3]: {lol[:3]}")
                # orig_colnames = lol[0]
        # dbug(lol[:3])
        if not flag_done:
            orig_colnames = list(df.columns.tolist())
            lol.insert(0, orig_colnames)
            # dbug(lol[:3])
        # dbug(lol[:3])
        # gtable(lol[:3], 'prnt', 'hdr', title=f"debugging has1col: {has1col} and hasindex: {hasindex}", footer=dbug('here'))
        if not isempty(orig_colnames):
            if not isempty(colnames):
                dbug(f"hmmm there was already orig_colnames {orig_colnames} this is all so kludgy colnames: {colnames} usr_colnames: {usr_colnames} pivot_b: {pivot_b}...")
                dbug(f"but colnames: {colnames} is not empty so inserting... is this needed?")
                lol.insert(0, colnames)
    # dbug(dtype)
    # dbug(lol[:3])
    # printit(" ".join(lol[1]), 'boxed', title='debugging', footer=dbug('here'))
    # """--== deal with dict ==--"""
    if data_type(data, ['dom', 'dov']):
        # dbug(data)
        # dbug(data_type(data))
        # dbug(f"{dtype=} we should do simple work here")
        lol = [list(data.keys()),list(data.values())]
    # dbug(lol[:3])
    # dbug(lol)
    # dbug(f"dtype: {dtype} data_type(lol): {data_type(lol)} lol[:2]: {lol[:2]} {called_from()}")
    # """--== deal with dol ==--"""
    # if dtype in ('dol'):
    if 'dol' in dtype:
        # I don't like this but ....
        # test for a dictionary with all lists having the same length
        first_val = next(iter(data.values()))
        if all([len(v)==len(first_val) for v in data.values()]):
            # dbug("all values have the same length TODO TODO TODO!!!!!!", 'ask')
            colnames = list(data.keys())
            lol = list(zip(*list(data.values())))
            lol = [list(elem) for elem in lol]
            lol.insert(0, colnames)
        else:
            # dbug(f"moving on with old code {called_from('verbose')} yes this gets used...")
            for k, v in data.items():
                if len(v) == 2:  # turn it into a dict
                    this_d = {}
                    this_d[v[0]] = v[1] 
                    data[k] = this_d   
            dtype = data_type(data)  # ie a 'dod' so it can get processed next
        # dbug(dtype)
    # do this before lod
    # """--== deal with dod ==--"""
    # if dtype in ('dod'):
    if 'dod' in dtype:
        # dbug("first lets make data a list of dictionaries")
        my_lod = []  # Initialize - we are going to first convert this to an lod
        for k, v in data.items():
            # dbug(f"k: {k} v: {v}")
            this_dict = {'name': k}
            this_dict |= v  # updating a dictionary with another dictionary 'in place' ie '|=' 
            my_lod.append(this_dict)
        if not isempty(selected_cols):
            selected_cols.insert(0, 'name')
        data = my_lod
        dtype = 'lod'  # this is needed to trigger next section for dealing with lod
        # dbug(f"data: {data}\ncolnames: {colnames}\nselected_cols: {selected_cols}")
    # """--== deal with a lod ==--"""
    # if isinstance(data, list) and isinstance(data[0], dict):
    if 'lod' in dtype or 'loD' in dtype:
        # dbug("each dictionary in the list is probabaly a dov? ie simple dict or key: value pairs")
        new_lol = []
        for n, elem_d in enumerate(data):  # because it is a list
            # dbug(elem_d)
            elem_keys = list(elem_d.keys())
            if not colnames:
                colnames = elem_keys
            # dbug(colnames)
            if isempty(usr_colnames):
                lol = colnames
            # dbug(elem_d.keys())
            new_row = []
            # for key in elem_keys.items():
            for key, val in elem_d.items():
                if key not in colnames:
                    # dbug(f"adding key: {key}")
                    colnames.append(key)
                new_row.append(val)
            new_lol.append(new_row)
            # dbug(colnames)
            # dbug(data_type(elem_d))
            # if data_type(elem_d, 'dov') and n == 0:
        if not isempty(usr_colnames):
            colnames = [usr_colnames]
        new_lol.insert(0,colnames)
        # vals = list(elem_d.values())
        # lol.append(vals)
        # dbug(lol[:2], 'ask')
        # if dtype in ('loD'):
        if 'loD' in dtype:
            # dbug(f"fixing lol {dtype=} {lol=} {called_from('v')}",'ask')
            lol = fixlol(lol)
            dtype = data_type(lol)
            if dtype != "lol":
                dbug(f"Please investigate...{dtype=} {lol=} {called_from('v')}", 'ask')
        # dbug(new_lol)
        lol = new_lol
    # dbug(dtype)
    # dbug(lol[:2])
    # """--== deal with simple list ==--"""
    # dbug(f"dtype: {dtype} data_type(lol): {data_type(lol)} lol[:2]: {lol[:2]} {called_from()}")
    # dbug('ask')
    if isempty(lol):
        lol = data
    if not isempty(lol) and isinstance(lol, list) and isinstance(lol[0], (str, int, float)):
        # dtype = data_type(lol)
        # dbug(dtype, 'ask')
        lol = [(lol)]  # lol maybe a simple list so turn it into an lol with one row
    # dbug(lol[:2])
    # """--== deal with numpy's ==--"""
    if 'ndarray' in str(type(lol)):
        dtype = data_type(lol)
        # import numpy as np
        lol = lol.tolist()
    # """--== deal with sqlite ==--"""
    # this got done in cat_file
    # """--== get rid of long whitespace values ==--"""
    # dbug("here now")
    # dbug(dtype)
    # might/should? consider using fxlol() here TODO
    # dbug(lol)
    lol = [row for row in lol if any(str(item).strip() for item in row)]  # remove blank or all whitespace items using reverse logic
    # dbug(f"{len(lol)=}")  # {[row[0] for row in lol]=}", 'ask')
    # if dtype == 'lol' and fix_b:
        # lol = fixlol(lol)
        # dbug(f"{dtype=} {len(lol)=} {called_from('v')} {len(lol[0])=}", 'ask')
        # for row in lol:
            # if len(row) != len(lol[0]):
                # dbug(f"{len(lol[0])=} {len(row)=} {row=}", 'ask')
        # dbug(f"{len(lol)=} {[row[0] for row in lol]=}", 'ask')
    if len(lol) == 0:
        # dbug(f"It appears that this list of lists has no data {lol=}... returning...{called_from('v')}")
        return lol
    new_lol = []
    for row in lol:
        new_row = []
        for col in row:
            if str(col).isspace():
                # dbug(col)
                col = blanks
            new_row.append(col)
        new_lol.append(new_row)
    lol = new_lol
    # dbug(lol)
    # dbug(neg)
    # dbug(f"{dtype=} {called_from('v')}")
    if dtype in ('los','block'):
        if len(lol) == 1 and data_type(lol[0]) in ('los', 'block'):
            # dbug("Ah Ha!")
            lol = lol[0]
        # dbug(f"lol: {lol}")
        my_lol = []
        for num, elem in enumerate(lol, start=1):
            my_lol.append([num, elem])
        lol = my_lol
        # dbug(f"STOP {lol=} {dtype=}", 'ask')
    # dbug(lol[:2])
    # """--== fix for dat file if firstline has title (all elems endwith ':') ==--"""
    # if islol(lol) and not isempty(lol):
    # dbug(f"{dtype=} {called_from('v')}")
    # dbug(data_type(lol))
    if data_type(lol, 'lol') and not isempty(lol):
        if all([str(elem).endswith(':') for elem in lol[0]]):
            # dbug("OK, we got here")
            lol[0] = [item.rstrip(':') for item in lol[0]]
            # if title == "":
            #     title = lol[0][0]
            #     dbug(title)
            # lol[0] = lol[0][1:]
    # dbug(lol[:3])
    # printit(" ".join(lol[1]), 'boxed', title='debugging', footer=dbug('here'))
    # """--== EOB ==--"""
    # dbug(lol[:2])
    # """--== fix_blanks? ==--"""
    if islol(lol) and fix_b:
        # dbug(lol[:3])
        lol = fixlol(lol, blanks=blanks)
    # dbug(lol[:3])
    # dbug(sortby)
    # dbug(lol[:3])
    # """--== pre raw cnvrt validation ==--"""
    if isempty(lol):
        dbug(f"lol: {lol} appears to be empty...{called_from('v')} returning...")
        return
    if isempty(lol[0]):
        dbug(f"lol[0]: {lol[0]} appears to be empty... lol: {lol}...returning...")
        return
    if isempty(lol[0][0]) and isempty(lol[0][-1]):
        dbug(f"lol[0][0]: {lol[0][0]} appears to be empty... lol: {lol}...returning...")
        return
    # """--== pre-raw... now make sure colnames has been done ==--"""
    # dbug(f"{data_type(lol)} {lol[0]=} {called_from('v')}")
    orig_colnames = lol[0]
    # dbug(f"{orig_colnames} {called_from('v')}")
    if isempty(colnames):
        colnames = orig_colnames
        # dbug(colnames)
    # dbug(pivot_b)
    if not pivot_b:
        # dbug(f"pivot_b: {pivot_b} usr_colnames: {usr_colnames} lol[0]: {lol[0]} TODO: this needs work")
        if not isempty(usr_colnames):  # and len(colnames) == len(lol[0]):
            if usr_colnames != lol[0] and len(colnames) == len(lol[0]):
                lol.insert(0, colnames)
            else:
                # dbug(f"usr_colnames: {colnames} orig_colnames: {orig_colnames}, lol[0]: {lol[0]} pivot_b: {pivot_b}")
                lol[0] = usr_colnames
            colnames = lol[0]
    # dbug(colnames)
    # dbug(f"orig_colnames: \n{orig_colnames} \ncolnames: \n{colnames} \nlol[0]: \n{lol[0]}")
    # """--== pre-raw... now manage tail if it is set ==--"""
    if not isempty(tail):
        tail_data = lol[-tail:]
        tail_data.insert(0, colnames)
        lol = tail_data
    # """--== raw_lol is now complete without sortby, filterby, selected, and pivot or colnames ==--"""
    # dbug(f"{len(lol)=} {lol[:3][0]=}")
    # dbug(f"{len(lol)=} {[row[0] for row in lol]=}", 'ask')
    dtype = data_type(lol)
    # """--== neg, rnd, human ==--"""
    # dbug(f"human:{human} rnd:{rnd} pivot_b:{pivot_b}")
    # dbug(neg)
    # printit(" ".join(lol[1]), 'boxed', title='debugging', footer=dbug('here'))
    if not pivot_b:  # the problem is the colnames
        # if isinstance(human, list):
        if not isempty(rnd) or not isempty(human) or not isempty(neg):
            # note: rnd can be a dict or int or bool
            rnd_l = []
            if isinstance(rnd, dict):
                rnd_l = list(rnd.keys())
            # note: human can be list or bool
            # dbug(f"note: neg: {neg} can be a list or bool")
            # dbug(f"neg: {neg} human: {human} rnd: {rnd}")
            new_lol = []
            for row in lol:
                new_row = []
                for col_num, elem in enumerate(row):
                    orig_elem = elem
                    # prefix = suffix = ""
                    # codes_l = split_codes(elem)
                    codes_l = parse_codes(elem, 'list')
                    # dbug(f"{codes_l=} {my_codes_l=}", 'ask')
                    prefix = codes_l[0]
                    suffix = codes_l[-1]
                    # dbug(repr(prefix))
                    # elem = escaped(elem)
                    elem = parse_codes(elem, 'escaped')
                    # dbug(elem)
                    # dbug(repr(suffix))
                    # dbug(f"chkg colnames[col_num]: {colnames[col_num]} in human: {human} elem: {elem}")
                    if isnumber(elem, 'human'):  # whether it is human readable or not
                        # dbug(f"human:{human} elem:{elem}", 'ask')
                        my_human = my_neg = ""
                        # my_rnd = ""
                        my_rnd = rnd
                        if isinstance(human, bool) and human:
                            my_human = human
                        if isinstance(rnd, bool) and rnd:
                            my_rnd = rnd
                        if isinstance(neg, bool) and neg:
                            my_neg = neg
                        # dbug(neg)
                        # dbug(type(neg))
                        if isinstance(human, list) or isinstance(neg, list) or not isempty(rnd_l):
                            # dbug(f"{col_num=} {colnames=} {human=} {neg=}")
                            if len(colnames) == len(orig_colnames):
                                # dbug("we are here")
                                if isinstance(human, list):
                                    # dbug(f"chkg colnames[{col_num}]: {colnames[col_num]} in human: {human}")
                                    if colnames[col_num] in human:
                                        # dbug(f"human: {human} colnames[{col_num}]: {colnames[col_num]}")
                                        my_human = True
                            if isinstance(human, list) and (orig_colnames[col_num] in human or colnames[col_num] in human):
                                my_human = True
                                # dbug(my_human, 'ask')
                            if isinstance(neg, list) and (orig_colnames[col_num] in neg or colnames[col_num] in neg):
                                # dbug(f"{neg=} {col_num=} {colnames[col_num]=}")
                                my_neg = True
                                # dbug(my_neg)
                            if orig_colnames[col_num] in rnd_l:
                                my_rnd = rnd[orig_colnames[col_num]]  # get the val
                        # dbug(f"elem: {elem} my_human: {my_human} my_rnd: {my_rnd}  my_neg: {my_neg} {human=} {neg=}")
                        elem = cond_num(elem, human=my_human, rnd=my_rnd, neg=my_neg)
                        # dbug(elem)
                    elem = prefix + str(elem) + suffix  # put the color codes back
                    if not isnumber(elem) and len(codes_l) > 2:  # more the a prefix and a suffix ie embedded ansi codes
                        # dbug(f"{orig_elem=} this is so embedded color codes are retained - like with pbar elems")
                        elem = orig_elem
                    row[col_num] = elem
                    new_row.append(elem)
                new_lol.append(new_row)
            lol = new_lol
            # dbug(lol)
    else:  # ie: pivot_b is True
        # dbug(f"Run {lol[:2]=} {data_type(lol)=} through cnvrt now before it gets pivoted {pivot_b=} but with human and rnd params/args and no pivot... kudgy but works")
        lol = cnvrt(lol, human=human, rnd=rnd, neg=neg)  # we do this because pivot changes the colnames
    # printit(" ".join(lol[1]), 'boxed', title='debugging', footer=dbug('here'))
    # """--== sortby ==--"""
    # dbug(f"{len(lol)=} {lol[:3]=}")
    # sortby must be before selected or col_limit
    # dbug(sortby)
    if sortby != '':
        # dbug("this is first in gtable because it may sortby: {sortby} on a colname that might get removed in next blocks")
        # """--== sep_line ==--"""
        sortby_l = []
        # dbug(sortby)
        reverse = False
        if "," in sortby:
            sortby_l = sortby.split(",")
        if ":" in sortby:
            sortby_l = sortby.split(",")
        if isinstance(sortby, (tuple|list)):
            sortby_l = list(sortby)
        if not isempty(sortby_l):
            sortby = sortby_l[0].strip()
            sortby_action = sortby_l[1].strip().lower()
            # dbug(sortby_action)
            if sortby_action in ("rev", "decend", 'r', "d", "decending", "reverse"):
                reverse = True
        # dbug(sortby)
        # dbug(reverse, 'ask')
        # """--== sep_line ==--"""
        if sortby in (lol[0]) and not isempty(sortby):
            sortby_i = lol[0].index(sortby)
        else:
            dbug(f"sortby: {sortby} not found in lol[0] colnames: {colnames} {called_from()}")
            sortby = ""
        # dbug(len(lol[0]))
        # dbug(sortby_i)
        hdr = lol[0]
        # dbug(lol[:2])
        my_lol = lol[1:]
        if isinstance(sortby, int):
            sortby_i = int(sortby)
            # dbug(sortby_i)
        if isinstance(sortby, str) and not isempty(sortby):
            # dbug(hdr)
            # dbug(sortby)
            sortby_i = hdr.index(sortby)
            # dbug(f"sortby: {sortby} sortby_i: {sortby_i}")
            # dbug(sortby_i)
        else:
            if not isempty(sortby):
                sortby_i = int(sortby)
            else:
                sortby_i = 0
            # dbug(sortby_i)
        if isnumber(my_lol[0][sortby_i]):
            for row in my_lol:
                str(row[sortby_i]).replace("%", "")
                if not isnumber(row[sortby_i]):
                    # dbug(row)
                    # dbug("Can not sort this")
                    row[sortby_i] = 0
            # my_lol = sorted(my_lol, key=lambda x: float(escaped(x[sortby_i])), reverse=reverse)
            my_lol = sorted(my_lol, key=lambda x: float(parse_codes(x[sortby_i], 'escaped').replace("%","")), reverse=reverse)
        else:
            # my_lol = sorted(my_lol, key=lambda x: str(escaped(x[sortby_i])).lower(), reverse=reverse)
            my_lol = sorted(my_lol, key=lambda x: str(parse_codes(x[sortby_i], 'escaped')).lower(), reverse=reverse)
        lol = [hdr] + my_lol
    # """--== filterby ==--"""
    # dbug(f"{len(lol)=} {lol[:3]=}")
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)}", 'ask')
    if filterby != {}:
        # dbug(filterby)
        if not isinstance(filterby, dict):  # or len(filterby) != 1:
            # TODO WIP hmmm need to fix this so multiple filters can be applied 20231101 might have fixed this???
            # dbug(f"filterby: {filterby} len(filterby): {len(filterby)} filterby must be a dictionary of (one key: value pair) " + "{colname: pattern\\} ... returning")
            return None
        for k, v in filterby.items():
            # dbug(f"Processing k: {k} type(k): {type(k)} and v: {v}")
            # psuedo
            # if k (ie col) is not a tuple (expected) Note: you can not us a list as a key in a dictionary but you can us a tuple
            if isinstance(k, str):
                cols =[k]
            else:
                cols = k  # if k is a tuple already
            # then turn k into a list (not expected but perhaps useful in special circumstances - [maybe use in fin ops to see is a keyword is part of  one col or another or another...]
            # then check for pat in each col / k in the the list of cols / k's <- which means turning this next section into a for loop eg for my_col in k.items()
            new_lol = []
            # dbug(type(cols))
            # dbug(cols)
            for my_col in cols:  # tuple or list
                # dbug(f"Working with my_col: {my_col}")
                filterby_col = my_col
                filterby_pattern = v
                # if filterby_col not in lol[0]:
                if filterby_col not in orig_colnames:
                    # dbug(filterby)
                    # dbug(lol[0])
                    dbug(f"{filterby_col=} not found in {orig_colnames=} {called_from('verbose')}")
                else:
                    filterby_i = lol[0].index(filterby_col)  # filterby col index number
                    # dbug(filterby_i)
                    if filterby_i is None:
                        dbug(f"Failed to find filterby_col: {filterby_col} in hdr: {lol[0]}")
                    # """--== convert filterby ==--"""
                    # filterby_pattern = list(filterby_d.values())[0]
                    pat = ""  # init pat; default: non-regex
                    pat = filterby_pattern  # now we have a regex search
                    # """--== process ==--"""
                    # new_lol = []
                    # filterby_str = filterby_str.lower()
                    for n,row in enumerate(lol[1:]):
                        try:
                            elem = str(row[filterby_i])
                        except Exception as Error:
                            dbug(f"Filterby index failed on row: {row} Error: {Error}")
                        # dbug(f"chkg searching elem: {elem} for pat: {pat}")
                        # match_results = re.search(pat, escaped(elem),)
                        match_results = re.search(pat, parse_codes(elem, 'escaped'),)
                        if ci_b:  # try case insensitive match?  default ci_b is false
                            match_results = re.search(pat, elem, re.IGNORECASE)
                        # if re.search(pat, elem):
                        if match_results:
                            # dbug(f"appending row: {row}")
                            new_lol.append(row)
                            continue
                    # dbug(f"finished {n} rows of len(lol): {len(lol)}", 'ask')
                    # dbug(new_lol)
            if len(new_lol) == 0:
                # dbug(colnames)
                # dbug(filterby)
                if prnt:
                    dbug(f"No matching records found using pattern: {filterby_pattern} on column: {filterby_col} new_lol[:3] {new_lol[:3]} called_from: {called_from()} ...returning...", centered=centered)
                return None
            new_lol.insert(0, lol[0])
            lol = new_lol
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # dbug(f"{len(lol)=} {lol[:3]=}")
    # """--== filterout ==--"""
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)}", 'ask')
    if filterout != {}:
        # dbug(filterout)
        if not isinstance(filterout, dict):  # or len(filterout) != 1:
            # TODO WIP hmmm need to fix this so multiple filters can be applied 20231101 might have fixed this???
            # dbug(f"filterout: {filterout} len(filterout): {len(filterout)} filterout must be a dictionary of (one key: value pair) " + "{colname: pattern\\} ... returning")
            return None
        for k, v in filterout.items():
            # dbug(f"Processing k: {k} type(k): {type(k)} and v: {v}")
            # psuedo
            # if k (ie col) is not a tuple (expected) Note: you can not us a list as a key in a dictionary but you can us a tuple
            if isinstance(k, str):
                cols =[k]
            else:
                cols = k  # if k is a tuple already
            # then turn k into a list (not expected but perhaps useful in special circumstances - [maybe use in fin ops to see is a keyword is part of  one col or another or another...]
            # then check for pat in each col / k in the the list of cols / k's <- which means turning this next section into a for loop eg for my_col in k.items()
            new_lol = []
            # dbug(type(cols))
            # dbug(cols)
            for my_col in cols:  # tuple or list
                # dbug(f"Working with my_col: {my_col}")
                filterout_col = my_col
                filterout_pattern = v
                if filterout_col not in lol[0]:
                    # dbug(filterout)
                    # dbug(lol[0])
                    dbug(f"filterout_col: {filterout_col} not found in orig_colnames ie: {orig_colnames} called from: {called_from()}")
                else:
                    filterout_i = lol[0].index(filterout_col)  # filterout col index number
                    # dbug(filterout_i)
                    if filterout_i is None:
                        dbug(f"Failed to find filterout_col: {filterout_col} in hdr: {lol[0]}")
                    # """--== convert filterout ==--"""
                    # filterout_pattern = list(filterout_d.values())[0]
                    pat = ""  # init pat; default: non-regex
                    pat = filterout_pattern  # now we have a regex search
                    # """--== process ==--"""
                    # new_lol = []
                    # filterout_str = filterout_str.lower()
                    for n,row in enumerate(lol[1:]):
                        try:
                            elem = str(row[filterout_i])
                        except Exception as Error:
                            dbug(f"Filterby index failed on row: {row} Error: {Error}")
                        # dbug(f"chkg searching elem: {elem} for pat: {pat}")
                        # match_results = re.search(pat, escaped(elem),)
                        match_results = re.search(pat, parse_codes(elem, 'escaped'),)
                        if ci_b:  # try case insensitive match?  default ci_b is false
                            match_results = re.search(pat, elem, re.IGNORECASE)
                        # if re.search(pat, elem):
                        if not match_results:  # where the rubber hits the road
                            # dbug(f"appending row: {row}")
                            new_lol.append(row)
                            continue
                    # dbug(f"finished {n} rows of len(lol): {len(lol)}", 'ask')
                    # dbug(new_lol)
            if len(new_lol) == 0:
                # dbug(colnames)
                # dbug(filterout)
                dbug(f"No matching records found using pattern: {filterout_pattern} on column: {filterout_col} new_lol[:3] {new_lol[:3]} called_from: {called_from()} ...returning...", centered=centered)
                return None
            new_lol.insert(0, lol[0])
            lol = new_lol
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # """--== selected ==--"""
    # dbug(lol, 'lst', 'ask')
    # dbug(f"selected_cols: {selected_cols} {called_from()}", 'ask')
    if selected_cols != []:
        selected_cols = [colname.strip() for colname in selected_cols]
        missing_cols_l = [item for item in selected_cols if item not in lol[0]]
        if len(missing_cols_l) > 0:
            if pivot_b:
                post_selected = selected_cols
                # dbug(f"pivot_B: {pivot_b}, selected_cols: {selected_cols} colnames: {colnames} lol[0]: {lol[0]}")
            else:
                dbug(f"Here is a list of missing selected cols missing from colnames {called_from('v')} \nmissing selected_cols: [red!]{missing_cols_l}[/]\n  colnames available lol[0]: {lol[0]}\n{called_from('v')}" )
                return None
        else:
            # next line is foo-magic: nest list comprehension. Inner loop builds a row of selected cols, outer loop appends each row which builds an lol of columns and rows
            for ln in lol:
                # is ln = row?
                for col in selected_cols:
                    # dbug(f"{col=}")
                    # colnames = lol[0]
                    indx = lol[0].index(col)
                    if  indx > len(ln):
                        dbug(f"STOP {col=} \n{lol[0]=}\n{ln=}\n {len(ln)=} {indx=} ",'ask')
            new_lol = [[ln[lol[0].index(i)] for i in selected_cols] for ln in lol]
            # """--== SEP_LINE ==--"""
            # dbug(new_lol)
            # dbug(f"pivot_b: {pivot_b}\n new_lol[:2]: {lol[:2]}\n selected_cols: {selected_cols}\n colnames: {colnames}\n usr_colnames: {usr_colnames}")
            lol = new_lol
        # dbug(lol[:3])
    # dbug(f"lol[:2]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # """--== excluded ==--"""
    # excluded cols
    if len(excluded_cols) > 0 and data_type(lol, 'lol'):
        # make sure you test for ecluded_cols, otherwise you could end up with a fatal recursion
        lol = filter_cols(lol, excluded_cols)
    # """--== col_limit ==--"""
    # """--== limit length of each elem to max_col_len ==--"""
    # but first TODO 
    # my_colnames = [str(colname).strip() for colname in lol[0]]
    if col_limit > 0 or wrap_b:
        max_col_len = col_limit
        if max_col_len == 0:
            for row in lol:
                max_elem_len = max(len(str(elem)) for elem in row)
                if max_elem_len > max_col_len:
                    max_col_len = max_elem_len
            # dbug(max_col_len)
        new_lol = []
        # dbug(max_col_len)
        for row in lol:
            # truncate elems in each row if needed
            new_row = []
            for elem in row:
                # dbug(f"Working of row: {row} elem: {elem}")
                if strip_b:
                    # stip off all whitespace
                    elem = str(elem).strip()
                if wrap_b:
                    # dbug("wrap if needed")
                    if isinstance(elem, str):
                        if max_col_len == 0:
                            max_col_len = 299
                        elem_len = parse_codes(elem, 'nclen')
                        # if nclen(str(elem)) > max_col_len - 5:  # for padding
                        if elem_len > max_col_len - 5:  # for padding
                            # elem = wrapit(str(elem), length=int(max_col_len - 5))
                            elem = gwrap(str(elem), length=int(max_col_len - 5))
                    else:
                        if max_col_len == 0:
                            max_col_len = 299
                        # elem = str(elem)
                        elem_len = parse_codes(elem, 'nclen')
                        # if nclen(str(elem)) > max_col_len - 5:  # for padding
                        if elem_len > max_col_len - 5:  # for padding
                            # elem = wrapit(str(elem), length=int(max_col_len - 5))
                            elem = gwrap(str(elem), length=int(max_col_len - 5))
                elem = str(elem).strip()  # get rid of leading or trailing spaces
                # if nclen(elem) > max_col_len:
                elem_len = parse_codes(elem, 'nclen')
                # if nclen(elem) > max_col_len:
                if elem_len > max_col_len:
                    if not isnumber(elem) and not isinstance(elem, dict):
                        elem = elem[:max_col_len]  # trim it if necessary
                new_row.append(elem)
                # dbug(new_row)
            new_lol.append(new_row)
            # End of loop for adding elems to this row
        lol = new_lol
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # """--== fixlol ==--"""
    # lol = fixlol(lol)  # fix all the lengths 20250512 not sure if this is needed
    # """--== pivot ==--"""
    # dbug(dtype)
    if pivot_b:
        # dbug(f"before pivot\n colnames: {colnames}\n lol[:2]: {lol[:2]}\n usr_colnames: {usr_colnames}\n selected_cols: {selected_cols}")
        # dbug(colnames)
        col1_name = colnames[0]
        # dbug(col1_name)
        my_colnames = [col1_name] + selected_cols
        # dbug(my_colnames)
        lol = pivot(lol)  # <-- where the rubber hits the road
        # dbug(f"after pivot rows={len(lol)} cols={len(lol[0])}\n colnames: {colnames}\n lol[:2]: {lol[:2]}\n usr_colnames: {usr_colnames}\n selected_cols: {selected_cols}")
        # dbug(lol[:3])
        # colnames = lol[0]
        # dbug(colnames)
        if not isempty(usr_colnames):
            # dbug(usr_colnames)
            if len(lol[0]) == len(usr_colnames):
            # if len(lol) == len(usr_colnames):
                colnames = usr_colnames
                lol.insert(0, usr_colnames)
                # dbug(f"usr_colnames: {usr_colnames} inserted")
            else:
                # dbug(usr_colnames)
                # dbug(lol[0])
                dbug(f"Problem... pivot_b: {pivot_b} len(lol[0]):{len(lol[0])} != len(usr_colnames):{len(usr_colnames)} {called_from('verbose')} rows={len(lol)}... skipping inserting colnames")
                dbug(lol[:3])
                # dbug(lol[:2], 'lst')
        if len(post_selected) > 0:
            selected_cols = [colname.strip() for colname in selected_cols]
            missing_cols_l = [item for item in selected_cols if item not in lol[0]]
            post_selected = [colname.strip() for colname in selected_cols]
            missing_postcols_l = [item for item in post_selected if item not in lol[0]]
            if len(missing_cols_l) > 0 or len(missing_postcols_l) > 0:
                dbug(f"Here is a list of missing selected cols: {missing_cols_l} missing from colnames: {colnames}\n and missing from post pivot colnames: \n  colnames available lol[0]: {lol[0]} {called_from()}" )
                return None
            else:
                my_colnames = lol[0]
                # dbug(my_colnames)
                lol = [[ln[lol[0].index(i)] for i in post_selected] for ln in lol]
                lol.insert(0, my_colnames)
        # dbug(f"after pivot\n colnames: {colnames}\n lol[0]: {lol[:2]}\n usr_colnames: {usr_colnames}\n selected_cols: {selected_cols}")
        colnames = my_colnames 
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # """--== post-pivot neg, rnd, human ==--"""
    if pivot_b:
        orig_colnames = lol[0]
        # if isinstance(human, list):
        if not isempty(rnd) or not isempty(human) or not isempty(neg):
            # note: rnd can be a dict or int or bool
            rnd_l = []
            if isinstance(rnd, dict):
                rnd_l = list(rnd.keys())
            # note: human can be list or bool
            # dbug(f"note: neg: {neg} can be a list or bool")
            # dbug(f"neg: {neg} human: {human} rnd: {rnd}")
            new_lol = []
            for row in lol:
                new_row = []
                for col_num, elem in enumerate(row):
                    # dbug(f"chkg colnames[col_num]: {colnames[col_num]} in human: {human} elem: {elem}")
                    if isnumber(elem, 'human'):  # whether it is human readable or not
                        my_human = my_neg = ""
                        # my_rnd = ""
                        my_rnd = rnd
                        if isinstance(human, bool) and human:
                            my_human = human
                        if isinstance(rnd, bool) and rnd:
                            my_rnd = rnd
                        if isinstance(neg, bool) and neg:
                            my_neg = neg
                        # dbug(neg)
                        # dbug(type(neg))
                        if isinstance(human, list) or isinstance(neg, list) or not isempty(rnd_l):
                            if len(colnames) == len(orig_colnames):
                                # dbug("we are here")
                                if isinstance(human, list):
                                    # dbug(f"chkg colnames[{col_num}]: {colnames[col_num]} in human: {human}")
                                    if colnames[col_num] in human:
                                        # dbug(f"human: {human} colnames[{col_num}]: {colnames[col_num]}")
                                        my_human = True
                            if isinstance(human, list) and orig_colnames[col_num] in human:
                                my_human = True
                                # dbug(my_human, 'ask')
                            if isinstance(neg, list) and orig_colnames[col_num] in neg:
                                my_neg = True
                                # dbug(my_neg)
                            if orig_colnames[col_num] in rnd_l:
                                my_rnd = rnd[orig_colnames[col_num]]  # get the val
                        # dbug(f"elem: {elem} my_human: {my_human} my_rnd: {my_rnd}  my_neg: {my_neg}")
                        elem = cond_num(elem, human=my_human, rnd=my_rnd, neg=my_neg)
                        # dbug(elem)
                    row[col_num] = elem
                    new_row.append(elem)
                new_lol.append(new_row)
            lol = new_lol
            # dbug(lol)
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # """--== drop_col ==--"""
    if not isempty(my_dropcol):
        lol = drop_col(lol, my_dropcol)
    """--== interval ==--"""
    if interval > 0:
        # this block grabs the first two rows and inserts them back in after intervals are done (in the appropriate order)
        # consider:
        # if isempty(colnames):  # make all this conditional on an empty colnames (which means there is probably one already in the lol
        #     then grab lol[0] (as below) and then add it back in (as further below)
        possible_colnames = lol[0]
        first_data_row = lol[1]
        last_data_row = lol[-1]
        lol = lol[interval-1::interval]
        lol.insert(0,first_data_row)  # leaving colnames alone
        lol.append(last_data_row)
        lol.insert(0,possible_colnames)
        # dbug(lol[:3])
    # """--== return by rtrn_type ==--"""
    my_rtrn = lol  # the default is lol
    # dbug(f'debugging rtrn_type={rtrn_type} selected_cols:{selected_cols}')
    if rtrn_type in ('lol'):
        # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)}", 'ask')
        my_rtrn = lol
    if rtrn_type in ('df'):
        # TODO fix this
        if len(colnames) ==  0 and 0:
            dbug(colnames)
            colnames = lol[0]
            df = pd.DataFrame(lol[1:])
            first_row_length = len(df.iloc[0])
            dbug(df.iloc[0])
            dbug(f"first_row_length: {first_row_length} len(colnames): {len(colnames)}")
            df.columns = colnames
            dbug(df.info())
            dbug(df)
            # df = df.rename(columns={'oldName1': 'newName1', 'oldName2': 'newName2'})
            my_rtrn = df
        else:
            my_rtrn = pd.DataFrame(lol)
            # dbug(my_rtrn)
    if rtrn_type in ('lod'):
        # dbug(f"{called_from('verbose')}")
        my_lod = []
        for row in lol[1:]:
            new_row = dict(zip(lol[0], row))
            # dbug(new_row)
            my_lod.append(new_row)
        # ddbug(f"data_type(my_lod):{data_type(my_lod)}")
        # dbug(my_lod, 'ask')
        my_rtrn = my_lod
    if rtrn_type in ('dod'):
        # I suspect this will never be needed
        my_dod = {}
        for row in my_lol[1:]:
            # use the first row as colnames for keys in all other rows
            my_key = row[0]
            # dbug(my_key)
            for col in row[1:]:
                my_d = dict(zip(my_lol[0][1:], row[1:]))
            my_dod[my_key] = my_d
        # dbug(my_dod)
        my_rtrn = my_dod
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()} my_rtrn: {my_rtrn}", 'ask')
    if rtrn_type in ('dov', 'dict', 'dod'):
        # dbug(f"dtype: {dtype} lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
        my_rtrn = {}
        if dtype in ("los"):
            # dbug(f"lol: {lol} dtype: {dtype}")
            if len(lol) == 1:
                # dbug(len(lol))
                for num, elem in enumerate(lol[0], start=1):
                    my_rtrn[num] = elem 
            # dbug("fake it by creating an index number of each string")
            for indx, my_string in enumerate(lol, start=1):
                my_rtrn[indx] = my_string[0]
            # dbug(my_rtrn)
        if all(len(elem) == 2 for elem in lol):
            # dbug("this is a key and value dictionary?")
            for elem in lol:
                my_rtrn[elem[0]] = elem[1]  
        if my_rtrn == {}:
            # this creates a dod with row num as the id 
            # dbug(f"len(lol):{len(lol)} rtrn_type:{rtrn_type} lol:{lol}")
            colnames = lol[0]
            for n, row in enumerate(lol[1:]):
                row_d = {}
                for num,col in enumerate(row):
                    row_d[colnames[num]] = col
                # this creates a dod with row num as the id ie: a dod 
                my_rtrn[str(n)] = row_d
            # dbug(f"my_rtrn: {my_rtrn} len(my_rtrn):{len(my_rtrn)}")
            if len(my_rtrn) == 1 and rtrn_type not in ('dod'):
                my_rtrn = my_rtrn['0']  # this is a simple dov (the len(lol) was likely 2)
                # dbug(my_rtrn)
        if len(lol) > 2 and isempty(my_rtrn):
            dbug("Unable to convert to a dictionary of values (dov) as there are more than 2 rows in the cnvrt'ed lol")
            my_rtrn = None
        # dbug(my_rtrn)
    if rtrn_type in ("sqlite", "sql"):
        if my_fname != "":
            db_fname = os.path.splitext(os.path.expanduser(my_fname))[0] + ".db"  # remove ".dat" and add ".db"
        else:
            db_fname = cinput("What filename do you want to use for the sqlite db [it should end with '.db.]: ")
        # """--== prepare lol for sql ==--"""
        # assumes first row is the colnames!!!
        if "id" in lol[0]:
          # remove id column if it exists in the lol
          id_indx = lol[0].index("id")
          my_lol = [[row[i] for i in range(len(row)) if i != id_indx] for row in lol]  # removing id column if it exists
        # """--== fix colnames if needed ==--"""
        colnames = my_lol[0]
        colnames = [str(colname).strip().replace(" ", "_") for colname in colnames] # cleaning up spaces in colnames
        # """--== load into sqlite file/db ==--"""
        # db_fname = cinput("What filename do you want to use for the sqlite db [it should end with '.db.]: ")
        # db_fname = os.path.splitext(os.path.expanduser(usr_dbname))[0] + ".db"  # remove ".dat" and add ".db"
        tablename = rootname(db_fname)
        db = SQLiteDB(db_fname, tablename=tablename, colnames=colnames)
        # dbug(my_lol)
        for row_l in my_lol[1:]:
            row_d = zip(colnames, row_l)
            row_d = dict(zip(colnames, row_l))
            # dbug(f"Inserting row_d: {row_d}")
            db.insert(tablename, row_d)
        db.close()
        # """--== sqlite file created ==--"""
    if rtrn_type in ("yml", "yaml"):
        my_rtrn = yaml.dump(lol, default_flow_style=False)
    if rtrn_type in ("json"):
        my_rtrn = json.dumps(lol, indent=4)
    # """--== Returning ==--""" #
    # dbug(f"returning: my_rtrn: {my_rtrn}")
    # dbug(f"dtype: {dtype} data_type(my_rtrn): {data_type(my_rtrn)} rtrn_type: {rtrn_type} returning my_rtrn: {my_rtrn}i {called_from()}")
    # dbug(f"lol[:3]: {lol[:3]} len(lol): {len(lol)} {called_from()}", 'ask')
    # gtable(my_rtrn, 'prnt', 'hdr', cnvrt_b=False, title=f"debugging {called_from()}", footer=dbug('here'), col_limit=25, wrap=True)
    # dbug(f"rtrn_type:{rtrn_type} actual data_type(my_rtrn):{data_type(my_rtrn)}")
    # dbug(f"my_rtrn:{my_rtrn} {called_from('verbose')}")
    return my_rtrn
    # ### EOB def cnvrt(data, *args, **kwargs): # ###


def fix_loD(data_list, fill_value="nan"):
    # dbug(f"working on a list of dict {data_type(data_list)=} {called_from('v')} {data_list[:3]=}")
    if not data_list:
        return []
    # If the first few items are strings representing headers,
    # you can treat index 0 as your column names and the rest as data rows:
    columns = []
    valid_dicts = []
    for idx, item in enumerate(data_list):
        if isinstance(item, dict):
            valid_dicts.append(item)
        elif isinstance(item, str):
            # Collecting the standalone strings as columns
            columns.append(item)
        else:
            print(f"Unexpected item type at index {idx}: {type(item)}")
    if not valid_dicts and columns:
        dbug("If you only had a list of header strings, return them as the header row...")
        return [columns]
    # Otherwise, build the uniform matrix from valid dicts
    if not valid_dicts:
        dbug("I've got nothing here")
        return []
    all_columns = list(dict.fromkeys(col for d in valid_dicts for col in d))
    matrix = [[d.get(col, fill_value) for col in all_columns] for d in valid_dicts]
    matrix.insert(0, all_columns)
    # dbug(f"returning matrix {data_type(matrix)=}",'ask')
    return matrix


# #########################################################################
def gtable(lol, *args, **kwargs):
    # #####################################################################
    """
    purpose: returns lines or displays a colorized table from a list_of_lists, df, or dictionary
    required:
        - lol: list_of_lists | pandas_data_frame | str: csv_filename # this gives lots of flexibility
    input: rows: str|list|dict|list_of_lists|list_of_dicts|dataframe
    options:
        - color: str,
        - box_style: 'single', 'double', 'solid',
        - box_color: str,
        - header|hdr: bool,  # header | hdr   # highlights the colnames
        - end_hdr: bool      # adds highlighted hdr/colnames to the bottom of the table
        - colnames: list | str,  'firstrow' | 'firstline' | 'keys'
        - col_colors: list,   # gtable will use this list of colors to set each column, repeats if more cols than colors
        - neg: bool | list,
        - nan: str,
        - alt: bool_val,
        - alt_color: str,      # default = "on grey"
        - title: str,
        - footer: str,
        - boxed: bool=False,   # default=False, but if True the table itself will be boxed and the title and footer will be used on the "master" box
        - index: bool,         # default=False
        - box_style: str,
        - max_col_len|col_limit|col_len...: int,  default=299 (arbitrary)
        - human: bool| list,   # if bool all numbers will get "humanized", if list syntax = [colname, colname...] and ony those colnames will get "humanized"
        - rnd: int | dict,     # if int all numbers will be rounded to rnd value,  if dict syntax is {colname, round_val, colname, round_val}
                                keep in mind if round_val = 0 it will turn that colname into all integers
                                if round > 0 then all the column values will have that many decimal places
        - sortby: str,list,tuple  # str = colname to sort by (default is ascending but you can include a comma and "rev" or "d" etc eg: sortby="mycol,rev")
                                  # or use a list (or tuple) = [colname, "rev"] for reverse sort ("rev" can be "desc"|"r"|"d"|"reverse")` 
        - filterby: dict {'field': 'pattern'}  # Note: the default is to search the column for matches of rows to keep
                                               # where the column "contains" the string pattern
        - filterout: dict {'field': 'pattern'}  # Note: the default is to search the column for matches of rows to exclude
        - ci|ic: bool          # will make filterby case insensitive (ci) or ignore case (ic) default=False
        - select_cols: list    # specify which columns to include - table will be in same order 
                    or dict      or it can be a remap dictionary eg {'column_one': "col1", 'column_four': 'col4'} <-- the table will change column_one to col1 and column_four to col4
                                    if a column is not named it will not be included and the order of the selected_cols will be as declared
        - excluded_cols: list  # specify which columns to exclude - or use drop_col (as it will perform a drop if the colname matches or if all the column values match)
        - drop_col: str|list   # pattern(s) where if every value in a column matches pattern(s) then drop the column eg drop_col=['nan', 'NaN']
        - write_csv: str,
        - skip: bool           # tells gtable to skip lines of the wrong length - be careful w/this
        - cell_pad=' ': str    # you can set the padding char(s)
        - strip: bool          # strip all white space off of ever element in every row
        - blanks: str          # you can declare how blank cells (blank elements in a row) should appear
        - fix: bool            # default=False - if true then every row of the data will be made the length of the first row
        - ignore: bool         # default=False builds the table even if the number of columns is different on the rows - makes it easier to troublshoot
        - cols: int            # split a table into several tables or columns (aka chunks) - very useful with long tables
        - width: int=0         # if width is provided the number of cols will adjust to fit tables into desired width (it can be a str with x% of screen width)
        - sep: str             # default=" "  this is the string between columns (only effective with the cols option > 1)
        - lol: bool            # default=False - will return the conditioned lol (rows of columns) instead of the default printable lines
        - no_hdr: bool         # removes header/colnames row from the table
        - purify: bool         # default=False - assumes provided data (lol) has all ready been purified
        - no_prcnt: bool       # default=False - whether to strip off percent symbol
        - conditions: list     # WIP (Work in Progress) see: function def data_conditions(data, conditions)
        - pivot: bool          # will try to pivot a list (or dictionary) - only works if num of rows is 2 and num of elems in each row are equal
        - rtrn: str            # if rtrn='lol' or rtrn='data' then this function will return converted data only
        - interval: int        # you can just print every X row by setting interval=X, the first_row and the last_row are preserved
        - seplines: list       # list of positions to place sep_line (separation lines) eg if data=[[row1],[row2],[row3]] using seplines=[-2] will put a sep_line before the last row(row3)             
        - row_limit: int=None  # this will limit the number of rows upto row_limit *after* sorting
        - ask: bool=False      # primarily for developers - ask whether to contiue before return
        - hl_pat: list         # list of match patterns... if a match is found to any elem in the row the entire row will be highlightd with hl_clr
        - hl_clr: str="yellow! on black!"
        - html_fname: str=""   # if provided an html file of this gtable will be generated in the file (styles included in html)
    returns lines: list
    notes:
        - if colnames="firstrow" then the firstrow will be extracted and used for the header
        - if colnames="keys" and we are passed a dictionary then the colnames will be the dictionary keys
        - TODO: add head: int and tail: in
        - I frequenly use this function for financial data analysis or csv files
    """
    # """--== debugging ==--"""
    # dbug(f"{called_from('verbose')} {lol=}")
    # dbug(lol)
    # dbug(lol[:3])
    # dbug(len(lol))
    # dbug(islol(lol))
    # dbug(args)
    # dbug(kwargs)
    # dbug(type(lol))
    # dbug(type(lol))
    # """--== Config ==--"""
    color = arg_val('color', args, kwargs, dflt="")
    # dbug(f"{color=}")
    lfill_color = kvarg_val("lfill_color", kwargs, dflt=color)
    # rfill_color = kvarg_val("rfill_color", kwargs, dflt=color)
    box_color = arg_val(['box_color', 'border_color', 'box_clr', 'boxclr', 'bxclr'], args, kwargs, dflt="bold white on rgb(40,40,40)")
    # dbug(f"{box_color=}")
    header = arg_val(['header', 'headers', 'hdr'], args, kwargs, dflt=False)
    end_hdr = arg_val(['end_hdr', "endhdr", 'hdr_last'], args, kwargs, dflt=False)
    # dbug(header)
    # header_color
    header_color = kvarg_val(['header_color', 'hdr_color'], kwargs, dflt="white! on grey40")
    colnames = kvarg_val(["col_names", "colnames"], kwargs, dflt=[])
    # if not isempty(colnames): dbug(colnames)
    # NOTE: if colnames (str) in ("firstrow", "first_row", "firstline", "first_line" then use firstline as colnames
    selected_cols = kvarg_val(['selected_cols', 'selectedcols', 'slctd_cols', 'slctdcols', 'select', 'selected', 'select_cols'], kwargs, dflt=[])
    # dbug(selected_cols)
    excluded_cols = kvarg_val(['excluded_cols', 'excludedcols', 'xcld_cols', 'excdcols', 'exclude', 'excluded', 'filter_cols', 'exclude_cols', 'exclude_col'], kwargs, dflt=[])
    my_dropcol = arg_val(['dropcol', 'drop_col', "drop_cols","dropcols"], args, kwargs, dflt=[])
    # dbug(my_dropcol, 'ask')
    centered_b = arg_val(['center', 'centered', 'cntr', 'cntrd'], args, kwargs, dflt=False)
    # dbug(centered_b)
    shadowed = arg_val(['shadow', 'shadowed'], args, kwargs, dflt=False)
    prnt = arg_val(['prnt', 'print', 'prn'], args, kwargs, dflt=False)
    rjust_cols = kvarg_val(['rjust_cols'], kwargs, dflt=[])
    # col_colors = kvarg_val(['col_colors', 'colors', "col_color", 'col_clrs', 'col_clr'], kwargs, dflt=["white!", "cyan", "red", "green", "blue!", "red!", "green!", "yellow!"])
    col_colors = kvarg_val(['col_colors', 'colors', "col_color", 'col_clrs', 'col_clr'], kwargs, dflt=["white!", "cyan", "red", "green", "rgb(0,0,225)", "red!", "green!", "yellow!"])
    # col_colors = kvarg_val(['col_colors', "col_color"], kwargs, dflt=[])
    # dbug(col_colors)
    title = kvarg_val('title', kwargs, dflt="")
    # dbug(title)
    footer = kvarg_val('footer', kwargs, dflt="")
    index_b = arg_val(['indexes', 'index', 'idx', 'id', 'indx'], args, kwargs, dflt=False)
    box_style = kvarg_val(['style', 'box_style'], kwargs, dflt='single')
    alt_color = kvarg_val(['alt_color', 'alt_clr', "altclr"], kwargs, dflt="on rgb(40,40,40)")
    # alt_color = kvarg_val(['alt_color', 'alt_clr', "altclr"], kwargs, dflt="on rgb(55,25,55)")
    if len(alt_color.split()) > 2 and not alt_color.strip().startswith("on"):
        alt_color = "on " + alt_color
    alt = arg_val('alt', args, kwargs, dflt=False)
    max_col_len = kvarg_val(['max_col', 'max_col_len', 'col_limit', 'max_limit', 'max_len', 'col_len', 'limit_col'], kwargs, dflt=299)  # arbitrary
    # dbug(f"{max_col_len=} {called_from('v')}")
    max_col_len = int(max_col_len)
    wrap_b = arg_val(["wrap", "wrapit"], args, kwargs, dflt=False)
    # dbug(wrap_b)
    neg = arg_val('neg', args, kwargs, dflt=False)  # if a list is supplied here the syntax is [colname, colname, colanme...]
    # dbug(neg)
    rnd = kvarg_val(['rnd', 'round'], kwargs, dflt="")
    # dbug(rnd)
    human = arg_val(['h', 'human', "H"], args, kwargs, dflt=False)
    # dbug(human)
    # nan = kvarg_val(['nan'], kwargs, dflt="")
    sortby = kvarg_val(["sortby", "sort_by", "sorton", "sort_on", "sort", 'sorted_by', 'sortedby'], kwargs, dflt='')
    # sortby_n = kvarg_val(["sortbyn", "sort_byn", "sortby_n", "sortby_n", "sort_n"], kwargs, dflt='')
    filterby_d = kvarg_val(['filterby', 'filter_by'], kwargs, dflt={})  # {column_to_search: pattern}
    filterout_d = kvarg_val(['filterout', 'filter_out'], kwargs, dflt={})  # {column_to_search: pattern}
    excluded_cols = arg_val(['excluded_cols', 'excludedcols', 'xcld_cols', 'excdcols', 'exclude', 'excluded', 'filter_cols', 'exclude_cols', 'exclude_col'], args, kwargs, dflt=[])
    # dbug(excluded_cols)
    ci_b = arg_val(["case_insensitive", "ci", "ignorecase", "ignore_case", "ic", 'ci_b'], args, kwargs, dflt=True)
    # ci_b = arg_val(["case_insensitive", "ci"], args, kwargs, dflt=False)
    # rgx_b = arg_val(["rgx", "regex", "exact", 'rgex'], args, kwargs, dflt=False)  # forces a regex search using supplied filterby pattern
    write_csv = kvarg_val(["write_csv", 'csv_file'], kwargs, dflt='')  # write a csv file with gtable data
    write_out = kvarg_val(["write_out", 'out_file'], kwargs, dflt='')  # write table out to file
    cell_pad = kvarg_val(['cell_pad', 'cellpad', 'pad'], kwargs, dflt=' ')
    strip_b = arg_val(['strip'], args, kwargs, dflt=False)
    # delimiter = kvarg_val(["delimiter", "delim"], kwargs, dflt=",")  # only needed if lol is a filename and not the default
    blanks = kvarg_val(["blank", "blanks"], kwargs, dflt="")
    skip = arg_val(['skip'], args, kwargs, dflt=False)  # skip non-compliant lines/rows?
    # ignore_b = arg_val(['ignore'], args, kwargs, dflt=False)  # skip non-compliant lines/rows?
    cols = kvarg_val(["cols", "columns", "chunks", "splits"], kwargs, dflt=1)
    # dbug(cols)
    # dbug(kwargs)
    width = kvarg_val(['width', 'w'], kwargs, dflt=0)
    # dbug(f"width: {width} cols: {cols} {called_from()}")
    sep = kvarg_val(["sep", "separation"], kwargs, dflt="")
    cols_limit = kvarg_val(["cols_limit", "max_cols", "max_cols"], kwargs, dflt=0)
    lol_b = arg_val(["lol", 'data'], args, kwargs, dflt=False)
    rtrn = kvarg_val(["rtrn", "return", "rtrn_type"], kwargs, dflt="")
    if rtrn in ("lol", 'data'):
        lol_b = True
    # reverse_b = arg_val(["rev", "rvsd", "reverse", "reversed"], args, kwargs, dflt=False)  # TODO - ie lol.reverse()
    nohdr_b = arg_val(["nohdr", "no_hdr", "nocolnames"], args, kwargs, dflt=False)  # removes first line (hdr/colnames) from table
    fix_b = arg_val(['fix'], args, kwargs, dflt=False)  # make all rows same number of columns as first row
    # dbug(fix_b)
    purify_b = arg_val(["purify", "purify_b", "decomment"], args, kwargs=False)  # assumes that provided data has already been "purified" ie decommented
    conditions = kvarg_val(["conditions", "conditions_lol", "triggers", "conditionals"], kwargs, dflt=[])  # WIP
    boxed_b = arg_val(['box', 'boxed'], args, kwargs, dflt=False)
    mstr_box_clr = kvarg_val(['mstr_clr', 'mstr_box_clr', 'mstrbxclr'], kwargs, dflt="")
    pivot_b = arg_val(['pivot', 'invert'], args, kwargs, dflt=False)
    # cnvrt_b = arg_val(['cnvrt_b'], args, kwargs, dflt=True)  # THIS IS STRICKLY FOR TESTING!! see the end of cnvrt()
    interval = arg_val(['interval'], args, kwargs, dflt=0) 
    seplines = arg_val(['seplines', 'sepline', 'sep_line', 'sep_lines'], args, kwargs, dflt=None) 
    row_limit = arg_val(['row_limit', 'rows_limit', 'rows'], args, kwargs, dflt=None)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    # hl_rows = arg_val(['hl', 'hl_row', 'hl_rows'], args, kwargs, dflt={})  # TODO has to be an exact match to any elem in row
    hl_pats = arg_val(['hl', 'hl_pats', 'hl_pat', 'hl_row', 'hl_line', 'hl'], args, kwargs, dflt=[])  # TODO has to be an exact match to any elem in row
    hl_clr = arg_val(['hl_pclr', 'hl_color'], args, kwargs, dflt="yellow! on black!")  # TODO has to be an exact match to any elem in row
    html_fname = arg_val(['html_fname', 'htmlfname', 'html', 'html_filename', 'htmlfile'], args, kwargs, dflt="")
    # """--== Validate ==--"""
    if isempty(filterby_d):
        filterby_d = {}
    # printit(lol[:3], 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
    dtype = data_type(lol)
    if dtype in ('bool', 'int', 'float'):
        dbug(f"Single entity... {lol=} {dtype=}  returning...")
        return
    if dtype == 'str':
        dbug(f"Single entity... {lol=} {dtype=}  returning ... {called_from('v')}")
        if lol.startswith("{") and lol.endswith("}"):
            dbug("Wait here... let me check this...")
        return 
    if isempty(filterout_d):
        filterout_d = {}
    # dbug(dtype)
    # if dtype in ("lol"):
    #     dbug(f"dtype: {dtype} lol[:2]: {lol[:2]} {called_from()}")
    # else:
    #     dbug(f"dtype: {dtype} len(lol): {len(lol)} {called_from()}")
    if not isinstance(selected_cols, list) and not isinstance(selected_cols, dict):
        dbug(f"selected_cols: {selected_cols} must be a list or a dictionary ... please investigate... returning...")
        return
    if not isinstance(filterby_d, dict):
        dbug(f"filterby must be a dictionary called_from: {called_from()}")
        return None
    if not isinstance(filterout_d, dict):
        dbug(f"filterout must be a dictionary called_from: {called_from()}")
        return None
    # dbug(lol[:2])
    if isempty(lol):
        dbug(f"Submission is empty... called_from: {called_from()} returning...", center=centered_b)
        return None
    no_prcnt = arg_val(["strip_percent", "strip_prcnt", "no_prcnt", "no_percent"], args, kwargs, dflt=False)
    if int(max_col_len) < 1:
        # dbug("setting col_len to 999")
        max_col_len = 299  # arbitrary - also what default is above
    if not isempty(rnd) and not isnumber(rnd) and not isinstance(rnd, dict):
        dbug(f"rnd: {rnd} option has to an int or a dictionary")
    # """--== Init ==--"""
    scr_cols = int(get_columns())
    cols = int(float(cols))
    if boxed_b:
        mstr_title = title
        title = ""
        mstr_footer = footer
        footer = ""
        my_txt_center = 99
    cell_pad = str(cell_pad)
    # RESET = sub_color('reset')
    # COLOR = sub_color(color)
    # RESET = sub_color('reset')
    COLOR = gclr(color)
    # dbug(COLOR + "COLOR")
    if box_color == "":
        box_color = 'reset'
    # BOX_COLOR = sub_color(box_color)
    # HEADER_COLOR = sub_color(header_color)
    BOX_COLOR = gclr(box_color)
    # dbug(f"{BOX_COLOR=}")
    HEADER_COLOR = gclr(header_color)
    box_chrs = get_boxchrs(box_style)
    tl, hc, ts, tr, vc, ls, rs, ms, bl, bs, br = box_chrs
    # dbug(f"{vc=}")
    lines = []
    max_elem_lens = []  # init... will hold max len for each col
    # cell_pad = " "  # add before and after @ elem - this has to come after sub_color(color)
    max_width = 0
    # rnd_l = []
    # stats_b = arg_val(['stats'], args, kwargs, dflt=False)  # causes recursion!
    # """--== SEP_LINE ==--""" #
    # dbug(f"{wrap_b=}")
    # """--== col_colors fix ==--"""
    if isinstance(col_colors, str):
        col_colors = [col_colors]  # make it a list
    # """--== Convert to lol ==--"""
    dtype = data_type(lol)
    if dtype is None:
        dbug(lol)
    # dbug(f"We are here now {dtype=} {lol=} {called_from('v')}", 'ask')
    # dbug(lol[0])
    # """--== first deal with dtype of str ==--"""
    # if isinstance(lol , str):
    # dbug(dtype)
    if "str" in dtype and 'json' not in dtype:
        if lol.lower() == "demo":
            # """--== begin gtable DEMO ==--"""
            import random
            lol = [["Column 1", "Column 2", "Column 3", "Column 4"]]
            demo_lines = ["This was a demo", "Hope this is useful"]
            numbers = [random.randint(0,100) for _ in range(100)]
            chunks = chunkit(numbers, 4)
            for chunk in chunks:
                if len(chunk) == len(lol[0]):
                    lol.append(chunk)
            options = {'prnt': True, 'hdr': True, 'centered': True, 'cols':3, 'sep': "   "}
            my_ops=', '.join(['{}={!r}'.format(k, v) for k, v in options.items()])
            printit([my_ops, "data = 100 random integers between 0-100"], 'boxed', 'centered', title="options used with gtable(data) below")
            gtable(lol, **options, title=" gtable()")
            data_stats(lol, **options)
            printit(demo_lines, **options, boxed=True, title="Quick-n-Dirty Demo")
            demo_code = from_to(__file__, begin="begin gtable DEMO", end="end gtable DEMO") 
            printit(fix_msgs(demo_code), 'boxed', 'centered', title="The code to produce above")
            # """--== end gtable DEMO ==--"""
            return
        # else:
            # dbug(f"Submitted data: {data_type(lol)=} appears to be a string instead of a data set.... {called_from('verbose')}... returning")
    # dbug(f"{lol=}")
    # """--== deal with doD ==--""" #
    # dbug(dtype)
    if dtype in ("doD", "dod"):
        # dbug(f"Not sure how to best handle {dtype=} as the dictionaries are different sizes... so I am printing each included Dictionary as a table w/title=key")
        tables = []
        for k,v in lol.items():
            if v:
                table = gtable(v, prnt=prnt, hdr=header, title=f"{title} {k}", footer=footer, colnames=colnames, pivot=pivot, col_limit=max_col_len)
                tables.append(table)
            else:
                dbug(f"it appears that the value associated with key:{k} is empty... {called_from('v')}...")
        # dbug('ask')
        return tables
    # """--== now cnvrt data set to an lol, selecting, filtering, setting col_limit, pivoting etc ==--"""
    # dbug(f"special test {lol[-1][-1]=}")
    # dbug(f"We are here now {dtype=} {colnames=} {lol[:3]=}", 'ask')
    if wrap_b:
        # dbug(f"{dtype=} lol: {lol} if {wrap_b=} is True then don't {max_col_len=} length yet")
        # dbug(f"{colnames=} {called_from('v')}")
        lol = cnvrt(lol, colnames=colnames, fix=fix_b, indx=index_b, blanks=blanks, purify=purify_b,
                        filterby=filterby_d, filterout=filterout_d, ci_b=ci_b, sortby=sortby, no_prcnt=no_prcnt,
                        pivot=pivot_b, selected_cols=selected_cols, excluded_cols=excluded_cols,
                        human=human, rnd=rnd, neg=neg)
        # dbug(lol,'ask')
    else:
        # dbug(f"We are here now {dtype=} {colnames=} getting ready to convert {lol=} {wrap_b=} {selected_cols=} {called_from('v')}", 'ask')
        # dbug(wrap_b)
        # dbug(selected_cols)
        # dbug(f"{lol} {called_from('verbose')}")
        # dbug(f"{lol[:3]=} {called_from('verbose')}")  # it may not be an lol yet
        # dbug(f"{colnames=} {called_from('v')}") 
        lol = cnvrt(lol, colnames=colnames, fix=fix_b, indx=index_b, blanks=blanks, purify=purify_b,
                        filterby=filterby_d,  filterout=filterout_d, ci_b=ci_b, sortby=sortby, no_prcnt=no_prcnt,
                        pivot=pivot_b, col_limit=max_col_len, selected_cols=selected_cols, excluded_cols=excluded_cols,
                        human=human, rnd=rnd, neg=neg)
        # dbug(f"We are back now from cnvrt() {lol[:3]=}", 'ask')
        # printit(" ".join(lol[1]), 'boxed', title="debugging", footer=dbug('here'))
    # dbug(colnames)
    # dbug(f"{dtype=}->cnvrt()->{data_type(lol)} is done pivot:{pivot_b} wrap:{wrap_b} colnames:{colnames}<--all done lol[0]:{lol[0]} len(lol):{len(lol)} max row elems {len(max(lol, key=nclen))}", 'noask')
    # dbug(f"special test {lol[-1][-1]=}")
    # """--== post cnvrt validation ==--"""
    # dbug(lol[:3], 'ask')
    if isempty(lol):
        dbug(f"No data ie: [lol: {lol}] found {called_from('v')}... returning")
        return
    """--== row_limit ==--"""
    if isnumber(row_limit):
        lol = lol[:int(row_limit)]
    """--== interval ==--"""
    if interval > 1:  # arbitrary kind of
        # this block grabs the first two rows and inserts them back in after intervals are done (in the appropriate order)
        # consider:
        # if isempty(colnames):  # make all this conditional on an empty colnames (which means there is probably one already in the lol
        #     then grab lol[0] (as below) and then add it back in (as further below)
        # dbug(len(lol))
        possible_colnames = lol[0]
        first_data_row = lol[1]
        last_data_row = lol[-1]
        lol = lol[interval-1::interval]
        # dbug(len(lol))
        lol.insert(0,first_data_row)  # leaving colnames alone
        lol.append(last_data_row)
        lol.insert(0,possible_colnames)
    # dbug(lol[:3])
    # """--== drop_col ==--"""
    if not isempty(my_dropcol):
        lol = drop_col(lol, my_dropcol)
    # """--== conditionals ==--"""
    # dbug(f"We are here now {lol[:4]=}", 'ask')
    # dbug(f"colnames: {colnames} lol[0]: {lol[0]} pivot_b: {pivot_b}")
    if not isempty(conditions):
        # dbug(f"colnames: {colnames} lol[0]: {lol[0]} ... cnvrt is done with pivot: {pivot_b}")
        # dbug(len(lol))
        lol = conditionals(lol, conditions, pivot=pivot_b, colnames=colnames)
    # """--== try to prevent hdr and record 1 duplicate ==--"""
    # this is kind of a kludge but I don't know a better way (yet 20250116) it does not take into account selected_cols???
    colnames = [colname[:max_col_len] for colname in colnames]  # truncate colname if too long
    # dbug(f"colnames: {colnames}")
    # dbug(f"  lol[0]: {lol[0]}")
    if not isempty(colnames):
        # dbug(f"step one colnames: {colnames} is not empty lol[:2]: {lol[:2]} {called_from()}")
        if colnames == lol[0] and len(lol) > 1:
            # dbug("colnames was provided so trimming off hdr in lol")
            lol = lol[1:]
    # """--== set colnames if not set ==--"""
    # if not isempty(colnames) and not isempty(selected_cols):
    #     colnames = selected_cols
    # # # dbug(lol[:3])
    # dbug(f"lol[:2]:{lol[:2]}", 'ask')
    # # dbug(len(lol[0]))
    # """--== fix for colnames - this might be necessary if multi cols (chuncks) is needed ==--"""
    # dbug(lol[0])
    if not isempty(colnames) and selected_cols != lol[0]:
        # dbug(f"this is after cnvrt - and this needed for multi-col cols: {cols} inserting colnames: {colnames} as they do not equal lol[0]: {lol[0]}")
        lol.insert(0, colnames)
    # dbug(colnames)
    # dbug(f"lol[:2]:{lol[:2]}", 'ask')
    # """--== mark sortby colname with and arrow ==--"""
    if not isempty(sortby):
        # dbug(f"This marks the sortby: {sortby} col by adding an arrow... it works but I might not keep it {called_from()}")
        # """--== make provision for and handle reverse:bool ==--"""
        sortby_l = []
        reverse = False
        if "," in sortby:
            sortby_l = sortby.split(",")
        if ":" in sortby:
            sortby_l = sortby.split(",")
        if isinstance(sortby, (tuple|list)):
            sortby_l = list(sortby)
        if not isempty(sortby_l):
            sortby = sortby_l[0].strip()
            sortby_action = sortby_l[1].strip().lower()
            # dbug(sortby_action)
            if sortby_action in ("rev", "decend", 'r', "d", "decending", "reverse"):
                reverse = True
        # dbug(sortby)
        # dbug(reverse)
        # """--== sep_line ==--"""
        if sortby in (lol[0]):
            # dbug(sortby)
            sortby_i = lol[0].index(sortby)
            if not reverse:
                # dbug(sortby_i)
                lol[0][sortby_i] = lol[0][sortby_i] + " ↓"
            else:
                lol[0][sortby_i] = lol[0][sortby_i] + " ↑"
        else:
            dbug(f"sortby: {sortby} not found in lol[0] colnames: {colnames} {called_from()}")
            sortby = ""
        # dbug(lol[0][sortby_i])
    # dbug(f"special test {lol[-1][-1]=}")
    # dbug(f"lol[:2]:{lol[:2]}", 'ask')
    # """--== save my_hdr to use later for endhdr ==--"""
    # if not isempty(lol):
    #     my_hdr = lol[0]  # needed in case end_hdr is called for but not hdr
    # else:
    #     dbug(f"No data in lol... filterby: {filterby_d} ... called_from: {called_from()} ... returning...")
    #     return
    # """--== if nohdr_b ==--"""
    if nohdr_b:
        lol = lol[1:]
    # """--== set maxes ==--"""
    max_row_lines = []
    for row in lol:
        max_row_lines.append(1)  # initializes a max_row_lines number for each row default = 1
    # dbug(lol[:3])
    # """--== limit length of each elem to max_col_len or wrap elements ==--"""
    # max_col_lengths = [nclen(max(str(column), key=len)) for column in zip(*lol)]  # <-- Important!
    # max_col_lens = [nclen(max(str(column), key=len)) for column in zip(*lol)]  # <-- Important!
    # The above needs to be here - trust me
    # dbug(max_col_lengths, 'ask')
    new_lol = []
    for row in lol:
        # dbug(f"{row=}")
        # truncate elems in each row if needed
        new_row = []
        for elem in row:
            # dbug(f"Working of {row=} {elem=}")
            if strip_b:
                # stip off all whitespace
                elem = str(elem).strip()
            if wrap_b:
                # dbug(f"{wrap_b=} if needed {elem=} {type(elem)=} {max_col_len=}")
                if isinstance(elem, str):
                    if max_col_len == 0:
                        max_col_len = 299  # arbitrary also the default above
                    elem_len = parse_codes(elem, 'nclen')
                    # dbug(f"{elem=} {elem_len=} {max_col_len=}")
                    # dbug(f"{elem_len=} {max_col_len -5=}")
                    # if nclen(str(elem)) > max_col_len - 5:  # for padding
                    my_padding = 7 # discovered experimentally
                    if elem_len > (max_col_len - my_padding):  # account for padding
                        # dbug(elem)
                        # dbug(f"{elem=} {max_col_len=}")
                        elem = gwrap(elem, length=int(max_col_len - my_padding)) 
                        elem = gblock(elem)  # <-- rubber hits the road... here we fill/pad each line_element
                        # dbug(f"{elem=}", 'boxed', title=f"{max_col_len=} {nclen(elem)=}")
                # else:
                    # dbug(f"{elem=}", 'boxed', title=f"{max_col_len=} {nclen(elem)=}")
            if isinstance(elem, dict):
                elem = str(elem)
            if isinstance(elem, list):
                elem = flattenit(elem)  # just in case elem is a nested list
            if isinstance(elem, list):
                # dbug(f"this is a multi_line elem: {elem}")
                new_elem = []
                for item in elem:
                    # should test len(item) here? and wrapit if  needed
                    item = str(item).replace("\n", "")
                    if len(str(item)) > max_col_len:
                        # dbug(max_col_len)
                        item = str(item)[:max_col_len]  # <--trim it if it is too long
                    new_elem.append(item)
                if len(new_elem) == 1:
                    new_elem = new_elem[0]
                elem = new_elem
                # dbug(new_elem)
                # dbug(type(new_elem))
            else:
                # elem is not a list type
                elem_len = parse_codes(elem, 'nclen')
                # if nclen(elem) > max_col_len:
                if elem_len > max_col_len:
                    if not isnumber(elem) and not isinstance(elem, dict):
                        elem = elem[:max_col_len]  # <--trim it if necessary
            new_row.append(elem)
        new_lol.append(new_row)
        # End of loop for adding elems to this row
    lol = new_lol
    # max_col_lengths = [nclen(max(str(column), key=len)) for column in zip(*lol)]
    # dbug(max_col_lengths, 'ask')
    # """--== deal with first row being None ,1 ,2, 3, e/tc ==--"""
    # TODO make this part of cnvrt which is coming up in future lines ??? or since mult col might play into this
    # dbug(lol)
    # dbug(isempty(lol))
    if isempty(lol):
        dbug(f"{lol=} {called_from('verbose')}")
        return
    if isempty(lol[0][0]) and isempty(lol[0][-1]):
        # not sure about this yet ... was a df maybe??
        lol = lol[1:]  # drop that first row - assumes second row is colnames
        # Removing element from list of lists
        del_col = 0
        [j.pop(del_col) for j in lol]  # does the drop "in-place"
    # dbug(lol[:3])
    # dbug("ok here we are", 'ask')
    # dbug(max_elem_lens)
    num_cols = len(lol[0])
    if not all(len(row) == num_cols for row in lol):
        # dbug(f"not all rows are the same length as num_cols: {num_cols} lol[0]:{lol[0]} ... running lol through fixlol() {called_from('verbose')}")
        # for n, row in enumerate(lol):
        #     if len(row) != num_cols:
        #         dbug(f"{n}.) {row} len(row):{len(row)} num_cols: {num_cols}")
        lol = fixlol(lol)
    max_lengths = [0] * num_cols
    for row in lol:
        for i, elem in enumerate(row):
            # max_lengths[i] = max(max_lengths[i], nclen(elem))
            try:
                max_lengths[i] = max(max_lengths[i], parse_codes(elem, 'nclen'))
            except Exception as Error:
                dbug(f"{Error=} {row=} {i=} {elem=} {called_from('v')}", 'xask')
    # dbug(f"num_cols: {num_cols} max_lengths: {max_lengths}")
    # """--== Local Functions ==--"""
    # #####################
    def _bld_row_line(row):
        # #################
        # dbug(f"{row=} used in multi_line")
        lfill_color = color
        for col_num, elem in enumerate(row):
            if col_num == 0:
                msg = ""
            mycolor = color  # the default passed as a Config option above
            if col_colors != []:
                # dbug("now change mycolor to appropriate col_colors")
                color_num = col_num % len(col_colors)
                col_color = col_colors[color_num]
                # dbug(col_color)
                mycolor = col_color
                myCOLOR = gclr(col_color)
            if alt:
                # now add in alt color
                line_num = row_num
                if header:
                    line_num = row_num + 1
                if line_num % 2:
                    myCOLOR = gclr(mycolor)
            elem_len = parse_codes(elem, 'nclen')
            # fill_len = max_elem_lens[col_num] - nclen(elem)
            fill_len = max_elem_lens[col_num] - elem_len  # <-- fill_len
            # dbug(f"{max_elem_lens[col_num]=} {elem=} {fill_len=}")
            fill = " " * fill_len
            myfill = fill
            mypad = cell_pad
            elem = str(elem)
            # dbug(repr(elem))
            if col_num in rjust_cols or isnumber(elem, 'human'):
                # right justify this elem
                justified_elem = myCOLOR + myfill + str(elem)
            else:
                # left justify this elem
                justified_elem = str(elem) + myCOLOR + myfill
            if col_num + 1 == len(row):
                # this is the last column
                add_this = mypad + justified_elem + mypad
                # dbug(f"{repr(myCOLOR)=} {myCOLOR}myCOLOR")
                msg += myCOLOR + add_this
                # marker_line += hc * nclen(add_this)
                # rfill_color = mycolor
                rfill_color = myCOLOR
            else:
                # this is not the last column
                add_this = mypad + justified_elem + myCOLOR + mypad
                # dbug(f"{repr(myCOLOR)=} {myCOLOR}myCOLOR")
                msg += myCOLOR + add_this + RESET + BOX_COLOR + vc + RESET
                # dbug(f"{msg=}")
                if col_num == 0:
                    lfill_color = mycolor
            if col_num == len(row) - 1:
                # this is the last col_num (column)
                rfill_color = mycolor
                # dbug(f"{repr(myCOLOR)=} {myCOLOR}myCOLOR {repr(rfill_color)=} {rfill_color}rfill_color")
                # dbug(f"mycolor: {mycolor} lfill_color: {lfill_color} rfill_color: {rfill_color}")
                line = gline(max_width, lc=vc, msg=msg, pad="", rc=vc, box_color=box_color, color=mycolor, lfill_color=lfill_color, rfill_color=rfill_color)
                # dbug(f"{line=}")
                lines.append(line)
        # printit(msg, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        return msg
        # ### EOB def _bld_row_line(row): ### #
    # dbug(lol[:3])
    # """--== Process ==--"""
    # dbug(f"This is after cnvrt? pivot_b: {pivot_b} colnames: {colnames} lol[0]: {lol[0]}")
    if pivot_b and isempty(colnames):
        # dbug(f"pivot_b: {pivot_b} num_rows: {len(lol)} num_cols: {len(lol[0])} colnames: {colnames} lol[0]: {lol[0]}")
        colnames = ["-key-", "-val-"]
    if colnames == []:
        colnames = lol[0]
        colnames = [str(elem).strip() for elem in colnames]
    num_cols = len(lol[0])
    # # """--== At this point lol is fully ready??!! ==--"""
    # # dbug("ok here we are", 'ask')
    # """--== Recurse if needed - multi cols ==--"""
    # dbug(width)
    if width > 0 and cols == 0:
        # dbug(f"This is a crazy kludge but it seems to work. The idea is to get the length of top line a single full table and use it to calc cols from given width: {width}")
        if title != "no_recurse" or width > 0 and cols > 0:
            # dbug(f"width: {width} cols: {cols} title: {title}")
            top_line = gtable(lol[:3], 'noprnt', title="no_recurse")[0]
            # dbug(f"[{top_line}]")
            top_line_len = parse_codes(top_line, 'nclen')
            # tbl_width = nclen(top_line) + 4  # the 2 is for sep/padding distance
            tbl_width = top_line_len + 4  # the 2 is for sep/padding distance
            # dbug(tbl_width)
            cols = math.floor(int(width) / tbl_width)
            # dbug(f"width: {width} cols: {cols} title: {title}")
    if cols > 1:
        max_my_table_len = 0
        # dbug(f"user wants multiple cols: {cols}")
        if len(lol) > 200:  # arbitrary
            dbug(f"Lots of rows to columnize ... please be patient...{called_from('v')}")
        if cols > cols_limit and cols_limit > 1:
            cols = cols_limit
        # dbug(lol)
        if pivot_b:
            len_orig_lol = len(lol) - 1  # removing colnames/hdr from count
            if cols > len_orig_lol:
                cols = len_orig_lol
        size = math.ceil((len(lol) / cols))
        # dbug(size)
        # dbug(f"len(lol): {len(lol)} cols: {cols} cols_limit: {cols_limit} size: {size}")
        # lols_l = chunkit(lol_no_hdr, size)
        colnames = lol[0] 
        # lols_l = []
        # for n,row in enumerate(lol[1:]):
            # this_lol = []
        if size < 2:
            # cols=1
            lols_l = [lol] 
        else:
            # start_time = time.time()
            # lols_l = chunk_generator(lol[1:], size)
            lols_l = chunkit(lol[1:], size)
        # dbug('ask')
        tbls = []
        # dbug(lol[:3])
        for my_lol in lols_l:
            # gtable(my_lol[:3], 'prnt', 'hdr', 'ask', colnames=colnames, title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
            if isempty(my_lol) or len(my_lol) < 1:
               continue
            # dbug(my_lol[:3])
            # gtable(my_lol, 'hdr', 'prnt', 'ask', endhdr=end_hdr)  # , colnames=colnames, col_limit=max_col_len,  title=title, footer=footer, col_colors=col_colors, box_clr=box_color)
            my_table = gtable(my_lol, 'hdr', 'noprnt', endhdr=end_hdr, colnames=colnames, col_limit=max_col_len,  title=title, footer=footer, col_colors=col_colors, box_clr=box_color,
                              hl_pats=hl_pats)
            # printit(my_table, 'boxed', title="debugging", footer=dbug('here'))
            if my_table is None:
               continue
            tbls.append(my_table)
            sep_len = parse_codes(sep, 'nclen')
            # my_table_len = maxof(my_table) + nclen(sep)
            # my_table_len = nclen(my_table[0]) + nclen(sep)
            my_table_len = parse_codes(my_table[0], 'nclen') + sep_len
            if my_table_len > max_my_table_len:
                max_my_table_len = my_table_len
            # elapsed_time = time.time() - start_time
            # dbug(elapsed_time)
        lines = gcolumnize(tbls, sep=sep, centered=centered_b, cols=cols)
        scr_cols = int(get_columns())
        max_ln_len = parse_codes(lines[0], 'nclen')
        if max_ln_len > scr_cols and prnt:
            num_cols = len(lol[0])
            num_rows = len(lol)
            pivot_msg = ""
            if num_rows < num_cols:
                pivot_msg = f"You may want to consider the pivot option as num_rows: {num_rows} < num_cols: {num_cols}."
            suggested_cols_msg = ""
            suggested_cols = math.floor(scr_cols/max_my_table_len)
            if suggested_cols < cols:
                suggested_cols_msg = f"You might try reducing the number of cols: {cols} perh  aps try cols = {suggested_cols}"
                dbug(f"The length/width of table: {max_ln_len} is greater than the available screen columns: {scr_cols}. Called_from: {called_from()}. {pivot_msg} col_limit: {max_col_len} {suggested_cols_msg}... returning")
            # dbug(f"Try cols = {suggested_cols}")
            # dbug(f"Returning None ... {called_from()}... prnt: {prnt} col_limit: {max_col_len}", 'ask')
            return None
        if boxed_b:
            dbug(f"Sending to boxed strip=False my_txt_center: {my_txt_center} centered_b: {centered_b}")
            my_txt_center = 99
            # lines = gblock(lines)
            # dbug("printing lines")
            # dbug(centered_b)
            lines = boxed(lines, centered_txt=my_txt_center, strip=False, title=mstr_title, footer=mstr_footer, box_clr=mstr_box_clr)
        # print(lines[0])
        # ruleit()
        lines = printit(lines, prnt=prnt, centered=centered_b)
        # dbug(f"returning lines {called_from('verbose')}")
        return lines
        # ### EOB if cols > 1: ### #
    # """--== get max_elem_lens[col] length for each col ==--"""
    # Now get max length for each column - in a series of steps using the FINISHED lol[0]
    num_cols = len(lol[0])
    for idx in range(num_cols):
        if not isinstance(lol[0][idx], str):
            hdr_elem = str(lol[0][idx])
        hdr_elem = lol[0][idx]
        # initializes a max_elem_len for each col using row one (lol[0])
        if isinstance(hdr_elem, list):
            hdr_elem = hdr_elem[0]
        else:
            hdr_elem = str(lol[0][idx])
        hdr_elem_len = parse_codes(hdr_elem, 'nclen')
        # hdr_elem_len = nclen(hdr_elem)
        max_elem_lens.append(hdr_elem_len)
    # dbug(max_elem_lens)
    # dbug(lol[:3])
    # dbug("ok here we are", 'ask')
    # """--== next step getting finished maxes ==--"""
    new_lol = []
    for row_num, row in enumerate(lol):
        # dbug(f"{row=} this is just the data")
        new_row = []
        # for each row in lol... get length
        # calc max_elem_lens for each col
        if row == []:
            # skip a blank or empty row
            continue
        # dbug(f"chkg row=")
        if hl_pats: 
            if isinstance(hl_pats, str):
                hl_pats = [hl_pats]  # turn it into a list
            for pat in hl_pats:
                # dbug(pat)
                # if pat in row:  
                if any([re.search(pat, elem) for elem in row]):  # rows are being looped above
                    row = [gclr(hl_clr) + elem + RESET for elem in row]
        for col_num, elem in enumerate(row):
            # for each elem in row
            # dbug(len(row))
            my_elem = elem
            if not isinstance(elem, list):
                if "\n" in str(my_elem):
                    my_elem = str(elem).split("\n")
            # dbug(elem)
            # """--== Is this a multi_line row? ==--"""
            # dbug(type(my_elem))
            # dbug(len(my_elem))
            # dbug(my_elem)
            if isinstance(my_elem, list):
                # dbug("for measuring length purposes only", 'ask')
                if len(my_elem) > 1:
                    max_row_lines[row_num - 1] = len(elem)  # sets the max_row_lines number to len of my_elem list - makes it multi_line
                    my_elem = max(my_elem, key=lambda item: parse_codes(my_elem, 'nclen'))  # this makes my_elem the longest str in the list
                    # dbug(my_elem)
                    my_elem_len = parse_codes(my_elem, 'nclen')
                    # dbug(my_elem_len)
                    # if nclen(my_elem) > max_elem_lens[col_num]:
                    if my_elem_len > max_elem_lens[col_num]:
                        # max_elem_lens[col_num] = nclen(my_elem) + 2  # adding some padding
                        max_elem_lens[col_num] = my_elem_len + 2  # adding some padding
                        # dbug(f"just set max_elem_lens[col_num] + 2 (padding) = {max_elem_lens[col_num]}")
            # now set max_elem_lens[col_num] for each elem
            # dbug(f"max_elem_lens[{col_num}]: {max_elem_lens[col_num]} nclen(str(my_elem)): {nclen(str(my_elem))}")
            # dbug(f"col_num: {col_num} len(lol[0]: {len(lol[0])})")
            if col_num >= len(lol[0]) and skip:
                continue
            if len(row) > len(max_elem_lens):
                dbug(max_row_lines)
                dbug(f"len(row): {len(row)} len(max_elem_lens): {len(max_elem_lens)}")
                dbug(max_elem_lens)
                dbug(col_num)
                dbug(row)
                dbug(elem)
                dbug(max_elem_lens[col_num])
                dbug('ask')
            my_elem_len = parse_codes(my_elem, 'nclen')  # yes, we need to do this here
            if my_elem_len > max_elem_lens[col_num]:
            # if nclen(str(my_elem)) > max_elem_lens[col_num]:
                # if this fails it is because the lol is not built correctly - wrong num of cols?
                # max_elem_lens[col_num] = nclen(str(my_elem))  # set max col width
                max_elem_lens[col_num] = my_elem_len  # set max col width
                # dbug(f"elem: {my_elem} len(my_elem): {len(str(my_elem))} max_elem_lens[{col_num-1}]: {max_elem_lens[col_num-1]}")
            new_row.append(elem)
        new_lol.append(new_row)
    lol = new_lol
    # dbug(lol[:3])
    title_len = parse_codes(title, 'nclen')
    # if nclen(title) + 4 > max_width:
    if title_len + 4 > max_width:
        # max_width = nclen(title) + 4
        max_width = title_len + 4
    footer_len = parse_codes(footer, 'nclen')
    # if nclen(footer) + 4 > max_width:
    if footer_len + 4 > max_width:
        # max_width = nclen(footer) + 4
        max_width = footer_len + 4
    # ### """--== Build Table ==--""" ### #
    for row_num, row in enumerate(lol):
        # dbug(f"row_num: {row_num} row: {" ".join(row)}", title="debugging")
        msg = ""
        # """--== is this a multi_line row, if so then make it multi_line ==--"""
        # TODO isnt this done by cnvrt now? 202240919
        # dbug(f"This might be a multi_line row: {row}")
        if max_row_lines[row_num - 1] > 1:
            # dbug(f"this is a multi_line row... row_num: {row_num} row: {row}")
            elem_line_num = 0  # init
            for add_row_num in range(max_row_lines[row_num - 1]):
                # dbug("add new_line rows")
                new_row = []  # init
                for elem_num, elem in enumerate(row):
                    # for each elem in row - is it a list type ?
                    # dbug(elem)
                    if isinstance(elem, list):  # muti-line
                        # dbug("start adding multi_line rows...  this is a multi_line elem (it is of list type)")
                        if add_row_num < len(elem):
                            new_elem = elem[add_row_num]
                    else:
                        # elem is not multi_line (ie not a list)
                        if add_row_num > 0:
                            # elem is not type list  and we are past the first row so just add the blank elem
                            new_elem = " "
                        else:
                            elem = str(elem)
                            new_elem = elem[:max_elem_lens[elem_num]]
                            elem_line_num = 0
                    new_row.append(new_elem)
                # this is one of the multi_line rows to add - there will be max_row_lines added
                elem_line_num += 1
                last_msg = _bld_row_line(new_row)
                # dbug(last_msg)
            # dbug(f"End loop for adding multi_line rows last_msg: {last_msg}")
        # """--== deal with hdr ==--"""
        if row_num == 0 and header:
            # dbug(f"Working on header row: {row} header: {header}", 'ask')
            hdr_line = vc
            for col_num, elem in enumerate(row):
                if isinstance(elem, list):
                    # msg_len = nclen(max(elem, key=len))  # uses the longest str in a list
                    msg_len = parse_codes(max(elem, key=len), 'nclen')  # uses the longest str in a list
                else:
                    # msg_len = nclen(elem)
                    msg_len = parse_codes(elem, 'nclen')
                fill_len = max_elem_lens[col_num] - msg_len
                # """--== SEP_LINE ==--"""
                # dbug(COLOR + "COLOR")
                if header:
                    # First row and header is true
                    this_COLOR = HEADER_COLOR
                    elem_len = parse_codes(elem, 'nclen')
                    rfill = lfill = " " * ((max_elem_lens[col_num] - elem_len) // 2)
                    elem = str(elem)
                    justified_elem = rfill + elem + lfill
                    rfill_len = parse_codes(rfill, 'nclen')
                    lfill_len = parse_codes(lfill, 'nclen')
                    # if nclen(rfill) + nclen(lfill) < fill_len:
                    if rfill_len + lfill_len < fill_len:
                        # diff = (fill_len) - (nclen(lfill) + nclen(rfill))
                        diff = (fill_len) - (lfill_len + rfill_len)
                        diff_fill = " " * diff
                        justified_elem += diff_fill
                    if col_num == len(row) - 1:
                        # dbug("NOT the last column")
                        msg += this_COLOR + cell_pad + justified_elem + cell_pad
                    else:
                        # dbug("last column")
                        # dbug(f"{repr(this_COLOR)=} {this_COLOR}this_COLOR")
                        msg += this_COLOR + cell_pad + justified_elem + cell_pad + BOX_COLOR + vc
                # dbug(COLOR + "COLOR")
            hdr_line = gline(max_width, lc=vc, msg=msg, pad="", rc=vc, box_color=box_color, color=COLOR, lfill_color=lfill_color)
            # dbug(f"{hdr_line=}")
            lines.append(hdr_line)
            # dbug(f"{parse_codes(hdr_line, 'nclen')=}")
            last_msg = msg
            # dbug(last_msg)
        else:
            # dbug(f"not the first row: {row}  and not header")
            msg = ""
            # """--== is this a multi_line row, if so then make it multi_line ==--"""
            if max_row_lines[row_num - 1] == 1:
                # dbug(f"Not sure what we have here row: {row}")
                for col_num, elem in enumerate(row):
                    # dbug(elem)
                    if col_num == 0:
                        msg = ""
                    mycolor = color  # the default passed as a Config above
                    if col_colors != []:
                        # now change mycolor to appropriate col_colors
                        color_num = col_num % len(col_colors)
                        col_color = col_colors[color_num]
                        mycolor = col_color
                        # myCOLOR = sub_color(col_color)
                        myCOLOR = gclr(col_color)
                    if alt:
                        # now add in alt color
                        line_num = row_num
                        if header:
                            line_num = row_num + 1
                        if line_num % 2:
                            mycolor = mycolor + " " + alt_color
                            # dbug(mycolor)
                            # myCOLOR = sub_color(mycolor)
                            myCOLOR = gclr(mycolor)
                            # dbug(f"{repr(myCOLOR)=} {myCOLOR}myCOLOR", 'ask')
                    elem_len = parse_codes(elem, 'nclen')
                    # fill_len = max_elem_lens[col_num] - nclen(elem)
                    fill_len = max_elem_lens[col_num] - elem_len
                    fill = " " * fill_len
                    # dbug(f"[{fill=}]")
                    myfill = myCOLOR + fill
                    mypad = cell_pad
                    # dbug(f"{col_num=} {max_elem_lens[col_num]=} {elem_len=} {fill_len=} [{myfill=}] [{mypad=}]")
                    elem = str(elem)
                    if col_num in rjust_cols or isnumber(elem.strip("%BGMK+-")):
                        # right justify this elem
                        # dbug(f"Right justify elem: {elem}")
                        justified_elem = myfill + str(elem)
                    else:
                        # left justify this elem
                        justified_elem = str(elem) + myfill
                    if col_num + 1 == len(row):
                        # dbug(f"This is the last column with {msg=}")
                        add_this = mypad + justified_elem + mypad
                        # dbug(add_this)
                        # dbug(msg)
                        msg += myCOLOR + add_this
                        # dbug(msg)
                        # marker_line += hc * nclen(add_this)
                        rfill_color = mycolor
                        # dbug(msg)
                        # dbug(f"{col_num=} {len(row)=} {max_elem_lens[col_num]=} {elem_len=} {fill_len=} [{myfill=}] [{mypad=}] {msg=}")
                        # dbug(f"{msg=}")
                    else:
                        # dbug(f"This is not the last column with {msg=}")
                        add_this = mypad + justified_elem + mypad
                        # dbug(split_codes(str(elem)))
                        if isnumber(elem, 'human') and 0:
                            codes_l = parse_codes(elem, 'list')
                            if codes_l[0] > 0:
                                dbug("the first_code/prefix_code not empty that is == ''")
                                # dbug(len(split_codes(elem)[0]))
                                myCOLOR = ""
                        # dbug(f"elem: {elem} myCOLOR: {repr(myCOLOR)} add_this: {add_this} {parse_codes(elem)=}")
                        # dbug(repr(BOX_COLOR))
                        msg += myCOLOR + add_this + RESET + BOX_COLOR + vc + RESET
                        # dbug(f"{msg=}")
                        # dbug(f"{msg}")
                        if col_num == 0:
                            lfill_color = mycolor
                        # dbug(msg)
                    if col_num == len(row) - 1:
                        # dbug(f"{msg=}")
                        # dbug("This is the last column {col_num=} and {msg=} should be well formed to submit to gline")
                        # dbug(msg)
                        rfill_color = mycolor
                        if len(str(msg)) > 1:
                            last_msg = msg
                        # dbug(f"{msg=}")
                        msg = gclr(msg)
                        # dbug(f"{msg=}")
                        # dbug(f"Submitting {msg=} to gline now")
                        # print(repr(msg))
                        # dbug(f'gline({max_width=}, lc={vc=}, msg={repr(msg)=}, pad="", rc={vc=}, box_color={box_color=}, color={mycolor=}, lfill_color={lfill_color=}, rfill_color={rfill_color=}) {called_from("verbose")}')
                        line = gline(max_width, lc=vc, msg=msg, pad="", rc=vc, box_color=box_color, color=mycolor, lfill_color=lfill_color, rfill_color=rfill_color)
                        # dbug(f"{line}")
                        lines.append(line)
                # === EOB for col_num, elem in enumerate(row): === #
            # === EOB if max_row_lines[row_num - 1] == 1: === #
        # === EOB else, if row_num == 0 and header: === #
    # === EOB for row_num, row in enumerate(lol): === #
    # """--== marker line ==--"""
    if end_hdr and header:
        lines.append(hdr_line)
    # add a sep_line after this header line
    marker_line = ""
    # last_msg = escaped(last_msg)
    last_msg = parse_codes(last_msg, 'escaped')
    for ch in last_msg:
        # we are changing every ch to a hc except vc will get a "@" marker. result eg: -----@---@-------@------
        if ch == vc:
            c = "@"  # This is just an arbitrary marker for proper positioning
        else:
            c = hc
        marker_line += c
    # marker_line = gline(max_width, lc=ls, msg=marker_line, hc=hc, rc=rs, box_color=box_color, color=box_color)  # color=box_color because the msg is part of the box
    # marker_line = escaped(gline(max_width, msg=marker_line, fc=hc, lc=tl, rc=tr))
    marker_line = parse_codes(gline(max_width, msg=marker_line, fc=hc, lc=tl, rc=tr), 'escaped')
    marker_line = marker_line[1:-1]  # strip off beginning and ending vc
    # """--== sep_line ==--"""
    sep_line = marker_line.replace("@", ms)
    sep_line = gline(max_width, lc=ls, msg=sep_line, hc=hc, rc=rs, box_color=box_color, color=box_color)  # color=box_color because the msg is part of the box
    if header:
        # insert the sep_line right under the hdr_line
        lines.insert(1, sep_line)
    if end_hdr:
        lines.insert(-1, sep_line)
    # """--== marker_line ==--"""
    # """--== top_line ==--"""
    top_line = ""
    msg = title
    # dbug(title)
    # dbug(COLOR + title)
    # msg_len = nclen(msg)
    msg_len = parse_codes(msg, 'nclen')
    my_marker_line = marker_line.replace("@", ts)
    my_marker_line = tl + my_marker_line + tr
    # dbug(f"{my_marker_line=} {msg_len=}")
    if msg_len > 0:
        # my_marker_line_len = nclen(my_marker_line)
        my_marker_line_len = parse_codes(my_marker_line, 'nclen')
        # dbug(f"{my_marker_line_len=} {msg=} {msg_len}")
        # dbug(my_marker_line_len)
        non_title_len = my_marker_line_len - msg_len
        lside_len = rside_len = non_title_len // 2
        lside = my_marker_line[:lside_len]
        diff = my_marker_line_len - (lside_len + msg_len + rside_len)
        rside_len = rside_len + diff
        rside = my_marker_line[(my_marker_line_len - rside_len):]
        # dbug(COLOR + "COLOR")
        top_line = BOX_COLOR + lside + COLOR + msg + RESET + BOX_COLOR + rside + RESET
    else:
        top_line = BOX_COLOR + my_marker_line + RESET
    # dbug(top_line)
    # lines[0] = top_line
    lines.insert(0, top_line)
    # """--== bot_line ==--"""
    bot_line = ""
    msg = footer
    # msg_len = nclen(msg)
    msg_len = parse_codes(msg, 'nclen')
    my_marker_line = marker_line.replace("@", bs)
    my_marker_line = bl + my_marker_line + br
    # my_marker_line_len = nclen(my_marker_line)
    my_marker_line_len = parse_codes(my_marker_line, 'nclen')
    if msg_len > 0:
        non_title_len = my_marker_line_len - msg_len
        side_len = non_title_len // 2
        lside = my_marker_line[:side_len]
        diff = my_marker_line_len - ((side_len * 2) + msg_len)
        side_len = side_len + diff
        rside = my_marker_line[my_marker_line_len-side_len:]
        bot_line = BOX_COLOR + lside + COLOR + msg + BOX_COLOR + rside + RESET
        # dbug(bot_line)
        # dbug(f"{diff=} {msg_len=} {side_len=} {rside=}")
    else:
        bot_line = BOX_COLOR + my_marker_line + RESET
    lines.append(bot_line)
    if boxed_b:
        lines = boxed(lines, centered_txt=my_txt_center, title=mstr_title, footer=mstr_footer, box_clr=mstr_box_clr)
    # """--== SEP_LINE ==--""" #
    # lines = printit(lines, prnt=prnt, centered=centered_b, shadowed=shadowed)
    # """--== SEP_LINE ==--""" #
    new_lines = lines
    if write_csv != "":
        CSV_FILE = write_csv
        with open(CSV_FILE, 'w', newline='\n') as f:
            # if we used import csv then use next 2 lines
            # writer = csv.writer(f)
            # writer.writerows(rows)
            for row in lol:
                f.write(",".join(row))
                f.write("\n")
            f.write(f'\n# This file was written out: {dtime} \n')
        # printit(f"Done writing csv file: {CSV_FILE}")
    if len(new_lines) == 0:
        dbug(f"Returning None {called_from('verbose')}")
        return None
    if write_out != "":
        with open(write_out, 'w', newline='\n') as f:
            for line in new_lines:
                f.write(line + "\n")
    # dbug(lol[:2])
    # """--== insert sep lines ==--""" #
    # dbug(len(new_lines))
    if seplines:
        for position in seplines:
            if position < 0:
                position = len(new_lines) + position
            # dbug(position)
            new_lines.insert(position, sep_line)
    # dbug(f"Returning new_lines prnt: {prnt}")
    # """--== Returning ==--""" #
    if html_fname:
        htmltable(lol, fname=html_fname, title=title, footer=footer)
    if lol_b: # if user just want the data (lol)
        # dbug(f"Returning lol[:3]: {lol[:3]}"
        return lol
    if prnt:
        printit(new_lines, prnt=prnt, centered=centered_b, shadowed=shadowed)
        # if stats_b or 1: # this recurses!!! 
        #     dbug(stats_b)
        #     data_stats(lol, 'prnt', centered=centered_b)
    if ask_b:
        askYN()
    return new_lines
    # ### EOB def gtable( ... ) ### #


# ###############################################
def add_cols(data, new_cols={}, *args, **kwargs):
    # ###########################################
    """
    purpose: add new columns to a list of lists (rows of columns) based on other column values
    requires:
        - data: list of lists (lol)   # this lol must have the colnames as the first row!
        - new_cols: dict              # syntax: eg: new_cols={'new_colname': '(col(colnameX) + col(colnameY)) - col(colnameZ)', 'another_new_colname', 'col(colnameA) * 3'}
    options:
        - prnt: bool=False            # prints gtable with new_lol data
        - title: str                  # only used if prnt os True
        - footer: str                 # only used if prnt os True
        - centered: bool=False        # only used if prnt os True
    returns: new_list_of_lists  (rows of columns) with new added columns
    notes:
        - the new_cols dictionary syntax is critical
            - {'new_colname': 'formula with as python would treat it after substituting col(col1) with its value from each row of data' '
               - formula eg: ''(col(colname1) + col(colname2) * col(colname3))'
               - 
        - created 20240819
    """
    # """--== debugging ==--""" #
    # dbug(f"{called_from('v')} {new_cols=}")
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    new_cols_d = kvarg_val(['new_cols', 'new_col', 'add_cols', 'add_col'], kwargs, dflt=new_cols)
    title = kvarg_val(['title'], kwargs, dflt="")
    footer = kvarg_val(['title'], kwargs, dflt="")
    centered_b = arg_val(['centered', 'center', 'cntr', 'cntrd'], args, kwargs, dflt=False)
    # """--== Validation ==--"""
    dtype = data_type(data)
    # if not islol(data) or isempty(data):
    if dtype not in ('lol') or isempty(data):
        dbug("data is not an lol... returning...")
        return
    if not isinstance(new_cols, dict) or isempty(new_cols):
        dbug("new_cols is not a dict... returning...")
        return
    # """--== Init ==--"""
    orig_colnames = data[0]
    new_colnames = list(new_cols_d.keys())
    my_lol = [orig_colnames + new_colnames]
    # """--== Process ==--"""
    for row in data[1:]:
        new_row = row
        add_row = ["to_calc"] * len(new_colnames)
        for new_col, formula in new_cols.items():
            indx = new_colnames.index(new_col)
            # build a new elem for that new_col
            matches = re.compile('\\((\\w+)\\)').findall(formula)
            for match in matches:
                this_indx = orig_colnames.index(match)
                my_val = row[this_indx]
                if isnumber(my_val):
                    my_val = float(my_val)
                formula = formula.replace(f'col({match})', str(my_val))
            # dbug(formula)
            new_elem = eval(formula)
            # dbug(new_elem)
            # dbug(f"new_col: {new_col} my_val: {new_elem}")
            # add new_elem value
            add_row[indx] = new_elem
        new_row += add_row
        # dbug(new_row, 'ask')
        my_lol.append(new_row)
    # dbug(my_lol[:5])
    if prnt:
        if footer == "":
            footer = dbug('here')
        gtable(my_lol, 'hdr', 'endhdr', prnt=prnt, title=title, centered=centered_b, footer=footer)
    # """--== return ==--"""
    return my_lol
    # ### EOB def add_cols(data, new_cols={}, *args, **kwargs): ### #



def nestlvl(lst, *args, **kwargs):
    """
    purpose: gets the level of nested lists
    requires: lst
    options:
        - verbose: bool    # returns a string providing the possible nature of the provided list (lst)
    returns: int
    notes: used by htmltable and gcolumnize (TODO)
        This helps determine rows and columns of boxes (cell dimension=1) or tables (cell dimension=2)
    """
    # """--== Config ==--"""
    verbose = arg_val(["verbose"], args, kwargs, dflt=False)
    # """--== SEP_LINE ==--"""
    # rocs is row(s) of cols ... ie data table
    add_this = 1
    if not isinstance(lst, list) and not isinstance(lst, dict):
        return 0
    if isinstance(lst, dict):
        # dbug("We found a dictionary")
        add_this += 1
    if isempty(lst):
        return
    if not lst:
        dbug(f"Nothing to process... lst: {lst}... returning...")
        return 1
    # dbug(my_max)
    # dbug(last_type)
    rtrn = max(nestlvl(item) for item in lst) + add_this
    if verbose:
        nestlvl_types = ['blank', 'box', 'a table or row of boxes', 'a row of tables or multi-row of boxes', 'multirow of tables', '???']
        rtrn = nestlvl_types[rtrn] + f" nestlvl: {rtrn}"
    return rtrn
    # ### EOB def nestlvl(lst, *args, **kwargs): ### #


# ###################################
def htmltable(data, *args, **kwargs):
    # ###############################
    """
    purpose: create HTML code: returning data as an html table
    required: 
        - data: lol|df|str(filename or url)    # data will get cnvrt'd to an lol - expects the first line/row to be the header elements 
    options: 
        - title: str
        - footer: str
        - footer: str
        - width: int|str     # provides width of holding box - can be a percent eg: width=80%
        - col_colors: list   # default (see code)
        - page_cntr: bool    # if true the box with the table will be centered on the web page
        - show: bool=False   # primarily for debugging; open the returning html code in a browser and prints html code out boxed and will  browse the code 
        - browse: bool=False # browse the code 
        - pivot: bool=False  # whether to pivot data
        - colnames: list   
        - style: bool=True   # writes a generic html style section for <table> and other html table entities (but see class option)
        - class: str         # you can declare your own html table style class name ie '<table class="{class}">
        - filename: str      # if filename is  declared then html code will be written to filename
        - font_sixe: str     # size of font default = 1em
        - col_limit: int
        - font_size: str='1em' # font size
    returns: 
        - str  # html code with a box (which is a single table cell or rows of tables) holding a table or tables of all the data provided
        - list of html strings # if only a url was supplied then a list of tables is assumed from that url... this list is each table as an html table 
                               # this gives the user more options on how to treat each table
    notes: this is still limited in features but seems to be useful
        You can also submit rows and or cols of tables(ie list-of-lists) or further do something like this
        Syntax:
            - htmltable(lol1)                      # a single table
            - htmltable([lol1, lol2])              # a single row with two tables
            - htmltable([[lol1, lol2], [lol3]])    # one row with two tables, and a second row with one table
            - htmltable([[lol1], [lol2], [lol3]])  # three rows with one tables in each row
        html_code = htmltable([{'table': my_lol, 'options': {'title': 'Title for my_lol'}}, {'table': my_lol2, 'options': {'title': "Title my_lol2"}}],
                            [{'table': my_lol3}, 'options': {'title': "Title for my_lol3", 'footer': dbug('here')}]
                        ])
        browseit(html_code)
    """
    # """--== Config ==--"""
    show = arg_val(["show", "debug", "prnt"], args, kwargs, dflt=False)
    browse = arg_val(["browse"], args, kwargs, dflt=False)
    end_hdr = arg_val(["end_hdr"], args, kwargs, dflt=False)
    col_colors = kvarg_val(['col_colors', 'colors', "col_color"], kwargs, dflt=["white!", "cyan", "rgb(255,120,120)", "green!", "rgb(120,120,255)", "red!", "green!", "yellow!"])
    width = kvarg_val(['width'], kwargs, dflt="")
    title = kvarg_val(["title"], kwargs, dflt="")
    # dbug(title)
    footer = kvarg_val(["footer"], kwargs, dflt="")
    # dbug(footer)
    page_cntr = arg_val(["pg_cntr", 'page_cntr', 'page_center', 'centered'], args, kwargs, dflt=False)
    styles_b = arg_val(["styles", "style", "include_style"], args, kwargs, dflt=True)
    pivot_b = arg_val(["pivot"], args, kwargs, dflt=False)
    my_class = arg_val(['class', 'classname', 'class_name'], args, kwargs, dflt="")
    colnames = arg_val(['colname', 'column_names', 'colnames'], args, kwargs, dflt=None)
    filename = arg_val(['file', 'filename', 'fname'], args, kwargs, dflt="")
    col_limit = arg_val(['col_limit'], args, kwargs, dflt=0)
    font_size = arg_val(['font_size', 'fontsize'], args, kwargs, dflt='1em')
    # """--== Validate ==--""" #
    # dtype = data_type(data)
    # dbug(f"{dtype=} {called_from()} {data=}")
    if isempty(data):
        dbug(f"Submitted {data=} appears to be empty {called_from('v')} ... returning...")
        return 
    # """--== Convert ==--"""
    # htmltable now launching cnvrt 
    # if not isinstance(data, dict):
    if isinstance(data, str) and data.startswith("http"):
        tables = get_html(data, 'tables')
        html_tbls = []
        for table in tables:
            html_tbls.append(htmltable(table))
        return html_tbls
    data = cnvrt(data, pivot=pivot_b)  # <-- cnvrt
    # dbug(data)
    if colnames:
        # dbug(colnames)
        data.insert(0, colnames)
    # dbug(data)
    # """--== Init ==--"""
    html = ""
    multitable_flag = False
    multirow_flag = False
    nlvl = nestlvl(data)
    if nlvl > 2:
        multitable_flag = True
    if nlvl > 3:
        multirow_flag = True
    # dbug(f"nlvl: {nlvl} multitable_flag: {multitable_flag} multirow_flag: {multirow_flag}")
    # """--== SEP_LINE ==--"""
    # dbug(f"{title=} {footer=}")
    # or include <link href="./htmltable.css" ref="stylesheet">
    styles = f"""\n
    <style>\n
        .mycanvass {{
            background-color: #000;
        }}
        table {{
          color: white;
          border-collapse: collapse;
          border-top: 1px solid white;
          border-bottom: 1px solid white;
          border-right: 1px solid white;
          border-left: 1px solid white;
          //width: 100%;
          font-size: {font_size};
        }}
        td {{
          padding: 8px;
          padding-top: 1px;
          padding-bottom: 1px;
          margin: 2px;
          //text-align: left;
          border-left: 1px solid white;
          border-right: 1px solid white;
          // border-bottom: 1px solid #DDD;
          white-space: nowrap;
        }}
        .hdr-row {{
           border-top: 1px solid white;
           background-color: #444;
        }}
        .first-row {{
           border-top: 1px solid white;
        }}
        .bottom-row {{
            border-bottom: 1px solid white;
         }}
        .last-row {{
            //border-right: 1px solid white;
            border-bottom: 1px solid white;
            //border-left: 1px solid white;
        }}
        .first-col {{
            background-color: #045;
            color: white;
        }}
        .last-col {{
            border-right: 1px solid white;
        }}
        .table-hover tr:hover {{
            background-color: #448;
        }}
        .table-center {{
            margin-left: auto;
            margin-right: auto;
        }}
    </style>\n
    """
    box_style = "background-color: rgb(0,0,0); overflow: hidden;"  # this is the beginning of an HTML table style 
    if not isempty(width):
        # dbug(box_style)
        box_style += f" width: {width};"
    # dbug(col_colors)
    col_colors = [xlate_clr(clr, 'rgb') for clr in col_colors]
    # dbug(col_colors)
    # dbug(col_colors)
    if page_cntr:
        html += "\n<center id='page_cntr'>\n"
    # """--== Functions (Internal) ==--"""
    def _do_table(data, *args, **kwargs):
        # """--== Inner Table ==--"""
        # dbug(funcname())
        # dbug(type(data))
        # """--== config ==--"""
        my_title = kvarg_val(["title", "caption"], kwargs, dflt="")
        my_footer = kvarg_val(["footer"], kwargs, dflt="")
        # """--== Init ==--"""
        table_html = ""
        # """--== convert ==--"""
        if isinstance(data, dict):
            # dbug("separate data from options (title\, footer\, etc...)")
            #  eg: data = {'table': data, 'options': {'title': "my title", 'footer': 'my footer'}}
            my_data = data['table']
            my_options = data['options']
            if 'title' in my_options:
                my_title = my_options['title']
            else:
                my_title = ""
            if 'footer' in my_options:
                my_footer = my_options['footer']
            else:
                my_footer = ""
            # dbug(my_footer)
            rtrn_code = _do_table(my_data, title=my_title, footer=my_footer)
            # dbug("Returning my_data")
            return rtrn_code
        # """--== SEP_LINE ==--"""
        # do a title
        if my_title:
            table_html += f"\n<table class='table-center' id='{my_title}' class='{my_class}'>"
            table_html += f"\n<caption>{my_title}</caption>\n"
            if not my_footer:
                my_footer = "&nbsp"
        # dbug(data)
        for row_num, my_row in enumerate(data):
            this_row = ""
            this_row += f"  <tr id={row_num}>"
            row_class = ""
            if row_num == 0:  # hdr-row
                row_class += " hdr-row"
                # dbug(my_row, 'ask')
            if row_num == 1:  # first_data_row
                row_class += " first-row"
            if (row_num + 1) == len(data):  # last row
                # dbug(row_num)
                # dbug(len(data))
                row_class += " last_row "
            # dbug(my_row)
            for col_num, elem in enumerate(my_row):
                elem = parse_codes(elem, 'str')  # sanitize elem
                if col_limit > 0:   
                    elem = str(elem)[:col_limit]
                # style = "background-color: black;"
                style = ""
                # col_color = col_color.replace("!", "")
                # dbug(col_color)
                if row_num == 0:
                    style += " text-align: center; "
                    col_color = "white!"
                else:
                    color_num = col_num % len(col_colors)
                    col_color = col_colors[color_num]
                col_color = xlate_clr(col_color, 'rgb')
                style += f"color: {col_color};" 
                col_class = ""
                if col_num == 0:  # first cell
                    col_class += " first-col"
                if col_num == len(my_row) - 1:  # last cell
                    col_class += " last-col"
                this_row += f"    <td style='{style}' class='{row_class}{col_class}'>{elem}</td>"
            this_row += f"\n  </tr id={row_num}>\n"
            if 'hdr-row' in row_class:
                # set this in case it is needed later
                my_hdr_row = this_row
            table_html += this_row
        if end_hdr:
            table_html += my_hdr_row
        table_html += f"</table id={my_title}>\n"
        # do a footer
        # dbug(footer)
        if my_footer:
            table_html += f"<center id='footer'>\n    {my_footer}\n</center id='footer'>\n"
        return table_html
        # """--== EOB Inner Table ==--"""
    # """--== Process ==--"""
    # """--== Outer Table(s) ==--"""
    # dbug(multirow_flag, 'ask')
    # dbug(data)
    if multirow_flag:
        for row in data:
            html += f"<table class='table-center' style='{box_style} border: none;'>\n"
            html += "  <tr id=multi_row>\n"
            for table in row:
                html += "    <td id='outer' style='border: none;'>"
                html += "\n<center>\n"
                # dbug(table)
                html += _do_table(table)
                html += "\n</center>\n"
                html += "    </td id='outer'>"
            html += "  </tr id=multi_row>\n"
        html += "</table>\n"
    else:
        # dbug("not multirow")
        html += f"<table  class='table-center' style='{box_style} border: none;'>\n"
        # html += "  <tr id=multi_row>\n"
        # html += "  <tr id=outer_not_multi_row>\n"
        # start a single row
        html += f"<table class='table-center' style='{box_style} border: none;'>\n"
        if multitable_flag:
            for table in data:
                html += "\n    <td id='outer' style='border: none;'>"
                # html += "\n<center>\n"
                html += _do_table(table)
                # html += "\n</center>\n"
                html += "\n    </td id='outer'>"
        else:
            # not multitable
            html += "    <td>\n"
            # html += "<center>\n"
            html += _do_table(data, title=title, footer=footer)
            # html += "\n</center>\n"
            html += "    </td>"
        # stop a single row
        html += "\n  </tr id=outer_non-multitable>\n"
    # html += f"<center><p>{footer}</p></center>\n"
    html += "</center>\n</table id='outer'>\n"
    if page_cntr:
        html += "</center id='page_cntr'>\n"
    if styles_b:
        # dbug("adding in styles first")
        html = styles + html
    # """--== SEP_LINE ==--"""
    if show or browse:
        browseit(html)
        printit(html, 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')
    # """--== SEP_LINE ==--""" #
    if filename:
        # dbug (f"do we have permission ? {called_from('v')} {filename=}")
        try:
            with open(filename, "w") as f:
                f.writelines(html)
        except Exception as Error:
            dbug(f"{Error=} - unable to write file {filename=} {called_from('v')} please investigate ...")
        # dbug(f"Wrote out {filename=}")
    # """--== SEP_LINE ==--""" #
    # dbug("Returning: html")
    return html
    # ### EOB def htmltable(data, *args, **kwargs): ### #


def chunkit(data, size, *args, **kwargs):
    """
    purpose: break a list or a dictionanry into a list of chunks - each chunk having size=size
    requires: 
        - data: list (eg boxes), size: int
    options:
        - full: bool=False   # puts empty "cells" to make all "list chunks" the same number of elems
        - cols: bool=False   # turn size into number of chunks or cols
            note: you can do this yourself eg size = len(data) // cols  # where cols = number of columns <-- this method would probably less confusing
    returns: 
        - list of lists(chunks)
    note: 
        uses: in a dashboard columns of boxes - see gcolumnize and in gtables
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(data)
    # dbug(type(data))
    # dbug(size)
    # """--== Config ==--"""
    full_b = arg_val(["full", "even", "equal"], args, kwargs, dflt=False)
    cols_b = arg_val(["cols", "chunks", "columns"], args, kwargs, dflt=False)
    # """--== Init ==--"""
    dtype = data_type(data)
    # dbug(dtype)
    if cols_b:
        size = len(data) // size
    # dbug(cols_b)
    # dbug(size)
    # """--== Validate ==--"""
    if 'empty' in dtype:
        dbug("data appears empty... returning...")
        return
    if size == 0:
        arb_num = 20
        dbug(f"size: {size} should not be 0 ... changing to arbitrary arb_num: {arb_num}")
        size = arb_num  # blatantly arbitrary
    if not isinstance(data, (str, list, dict)):
        dbug("Submitted variable must be a list or a dictionary ... returning...")
        return
    # """--== Convert ==--"""
    if isinstance(data, dict):
        # dbug(f"type(data): {type(data)} is a dictionary... converting to pivoted lol {called_from('v')}")
        data = cnvrt(data, 'pivot')
        # dbug(f"{data=}")
    size = int(size)
    # """--== Process ==--"""
    # dbug(data)
    # dbug(dtype)
    # dbug(size)
    if 'lob' in dtype:
        # Ummm .. this might be useful for all dtypes TODO
        new_list = [data[i:i + size] for i in range(0, len(data), size)]
        # dbug(f"returning new_list {called_from('verbose')}")
        return new_list
    def divide_chunks(data, size):
        # this works for an lol but not for a lob (yet)
        # looping till we reach length data
        # if size < 1:  # this should never happen
            # dbug(f"size: {size} should NOT be 0 {called_from('v')}")
        # dbug(data)
        for i in range(0, len(data), size):
            # i_dtype = data_type(i)
            # dbug(i_dtype)
            # dbug(f"i: {i} size: {size}")
            end = i + size
            # dbug(end)
            yield data[i:end]
    rtrn = list(divide_chunks(data, size))
    # """--== SEP_LINE ==--"""
    if full_b:
        new_rtrn = []
        for elem in rtrn:
            if len(elem) < size:
                diff = size - len(elem)
                for x in range(diff):
                    if isinstance(elem, list):
                        elem.append([""])
                    if isinstance(elem, str):
                        elem.append("")
            new_rtrn.append(elem)
        rtrn = new_rtrn
    return rtrn
    # ### EOB def chunkit(data, size, *args, **kwargs): ### #


# ############################
def splitit(s, delimiter=" ", *args, **kwargs):
    # ########################
    """
    purpose: given a string (s), split it using delimiter which can be a string or regex
    requires: import re
    input:
        - s: str  # string to split
        - delimiiter=" ": str  # this can be a regex
    options: none
    returns: phrases: list  # string split into elements
    notes:
        eg:
            delimiter = r"[\"|\'] +[-–—―] +"  # amazingly all those dashes are different symbols...
            phrases = splitit('"A great city is not to be confounded with a populous one" - Aristotle', )
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(s)
    # dbug(delimiter)
    # """--== Config ==--"""
    delimiter = kvarg_val(["delim", "delimiter", 'pat', 'pattern'], kwargs, dflt=delimiter)
    # """--== Validate ==--"""
    # if type(s) != str or len(s) == 0:
    if not isinstance(s, str) or len(s) == 0:
        dbug(f"Nothing to work with s: {s} delimiter: [{delimiter}]")
        return None
    # """--== Process ==--"""
    phrases = re.split(delimiter, s)
    # dbug(f"Returning phrases: {phrases}")
    return phrases


# #################
def cond_num(elem, *args, **kwargs):
    # #############
    """
    purpose: this conditions (colorizes, rounds, and adds commas and unit indicators) elems if they are numbers
    input: elem
    options: 
        -   neg_color: str"=red on black!",
        -   pos_color: str="green! on black!"
        -   color: bool         # will color the number ... default red for negative and green for positive
        -   rnd: int            # if rnd == "" nothing will be done, if 'rnd' included as an option the default will be round to 2 places
                if rnd is 0 it will make elem an integer,
                if rnd > 0 then that will be used for the number of places to round
        -   human: bool         # adds reduces large numbers to 10000000 to 1M etc
        -   uncond: bool        # un-condition numbers and strip off ansi-codes default is False
        -   nan: str            # allows you to change "nan" or "NaN" to any string you want. default=""
        -   no_prcnt: bool      # default=False - whether to strip off percent symbol
        -   commas: bool        # will put commas into the number appropriate - do not use with option human
        -   pcnt: bool          # will add % symbol after value
    returns: elem (conditioned; colored)
    use:
        -   for n, row in enumerate(lol):
        -       ...
        -       if neg:
        -           row = [cond_num(elem) for elem in row]
        -       # table.add_row(*row)
        -       table_lol.append(*row)
    NOTE: 
        -    this may return an elem with a different length
        -    also note that this function is different from data_conditions()
        -     aka: color_neg(elem)
    """
    # dbug(f"{funcname()} called_from: {called_from()} elem: {elem}")
    # dbug(elem)
    # dbug(repr(elem))
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    clr_b = arg_val(["neg", "color", "clr", "colorize", "pos"], args, kwargs, dflt=False)  # "neg" and 'pos'are remanants of past code
    rnd = kvarg_val(['round', 'rnd'], kwargs, dflt="")
    # dbug(rnd)
    # neg_color = kvarg_val(['neg_color'], kwargs, dflt='red! on rgb(0,0,0)')
    neg_color = kvarg_val(['neg_color'], kwargs, dflt='red! on black!')
    # pos_color = kvarg_val(['pos_color'], kwargs, dflt='green! on rgb(0,0,0)')
    pos_color = kvarg_val(['pos_color'], kwargs, dflt='green! on black!')
    human = arg_val(["human", "h"], args, kwargs, dflt=False)
    nan = kvarg_val(["nan", "NaN"], kwargs, dflt="")
    rset = arg_val(['rset', 'reset'], args, kwargs, dflt=False)  # DO NOT change this to True - trust me!
    no_prcnt = arg_val(["strip_percent", "strip_prcnt", "no_prcnt", "no_percent"], args, kwargs, dflt=False)
    commas_b = arg_val(["comma", "commas"], args, kwargs, dflt=False)
    pcnt_b = arg_val(["pcnt", "%", 'percent', 'prcnt'], args, kwargs, dflt=False)
    uncond_b = arg_val(['uncond', 'u', 'un','un-cond','uncondition', 'nonhuman', 'nohuman'], args, kwargs, dflt=False)
    # """--== uncond if requested ==--"""
    if uncond_b:
        # elem = escaped(str(elem)).strip()
        elem = parse_codes(str(elem), 'escaped').strip()
        if isnumber(elem):
            elem = str(elem)
            if elem.endswith("T"):
                elem = elem.rstrip("T")
                elem = float(elem) * 1000000000000
            elem = str(elem)
            if elem.endswith("B"):
                elem = elem.rstrip("B")
                elem = float(elem)
                elem = elem * 1000000000
            elem = str(elem)
            if elem.endswith("M"):
                elem = elem.rstrip("M")
                elem = float(elem)
                elem = elem * 1000000
            elem = str(elem)
            if elem.endswith("K") or elem.endswith("k"):
                elem = elem.lower().rstrip("k")
                elem = float(elem)
                elem = elem * 1000
            elem = str(elem)
            if elem.endswith("G"):
                elem = elem.rstrip("G")
                elem = float(elem)
                elem = elem * 1000000000
            if "," in elem:
                # dbug("replacing comma in {elem=}")
                elem = elem.replace(",","")
            if "%" in elem:
                elem = elem.replace("%", "")
            return float(elem)
        else:
            return elem
    # """--== Convert ==--"""
    if 'rnd' in args:
        rnd = 2
    if 'numpy' in str(type(elem)):
        elem = elem.item()
    # """--== Init ==--"""
    prefix = ""
    suffix = ""
    elem_val = elem
    # orig_elem = elem
    elem = str(elem)
    # dbug(elem)
    # elem_CODES = split_codes(elem)
    # dbug(elem_CODES)
    # my_elem_CODES = split_codes(elem, 'elem')
    # splitcodes_d = split_codes(elem, 'dict')
    splitcodes_d = parse_codes(elem, 'dict')
    # my_elem_CODES = splitcodes_d['codes']
    # dbug(my_elem_CODES)
    # if '\x1b[0m' in elem:
        # dbug('ask')
    # dbug(elem)
    # elem = my_elem_CODES['elems']
    elem = splitcodes_d['strings'][0]  # assumes there is only one
    if '\x1b[0m' in elem:
        dbug(f"Arggg.. repr(elem): {repr(elem)} {called_from('verbose')}")
    # dbug(repr(elem))
    # elem_CODES = [my_elem_CODES['prefix'], my_elem_CODES['suffix']]
    elem_CODES = [splitcodes_d['codes'][0],splitcodes_d['codes'][-1]]  # I do not like doing this
    # dbug(elem_CODES)
    # if '\x1b[0m' in my_elem_CODES['suffix']:
        # dbug('ask')
    # dbug(my_elem_CODES)
    # if elem_CODES[0] != "":
        # dbug(elem_CODES)
    # last_msg = ""
    # RESET = sub_color('reset')
    if clr_b:
        # elem = escaped(elem)
        elem = parse_codes(elem, 'escaped')
        # dbug(f"pos_color: {pos_color} neg_color: {neg_color}")
        # NEG_COLOR = sub_color(neg_color)
        # NEG_COLOR = sub_color(neg_color)
        NEG_COLOR = gclr(neg_color)
        # POS_COLOR = sub_color(pos_color)
        POS_COLOR = gclr(pos_color)
        # dbug(f"{NEG_COLOR}NEG_COLOR{RESET} repr(NEG_COLOR): {repr(NEG_COLOR)}")
        # dbug(f"{POS_COLOR}POS_COLOR{RESET}")
    else:
        elem = str(elem)
        NEG_COLOR = ""
        POS_COLOR = ""
    # NOTE! IMPORTANT! If you want a number to be treated like a string, ie ignored here, precede it with an underscore (_) or surround it with [] or someother means
    #   or set neg to False in table or rnd="", human=""
    # dbug(elem)
    if nan != "":
        if str(elem).lower() == "nan":
            elem = str(nan)
    # strip off percent symbol
    if no_prcnt:
        elem = elem.replace("%", "")
    # dbug(elem)
    # strip off any human symbols except "-"
    had_commas = False
    if "," in elem:
        had_commas = True
        elem = elem.replace(",", "")
    suffix = ""
    tst_elem = elem.strip("%BGMKT+")
    # dbug(repr(elem))
    if isnumber(tst_elem) and not str(elem).startswith("_"):
        # dbug(f"{elem=} {tst_elem=}")
        suffix = prefix = ""
        if str(elem).endswith("T"):
            elem = elem.replace("T", "")
            suffix = "T"
        if str(elem).endswith("G"):
            elem = elem.replace("G", "")
            suffix = "G"
        if str(elem).endswith("B"):
            elem = elem.replace("B", "")
            if float(elem) > 1000 and float(elem) < 1000000:
                elem = float(elem)/1000
                suffix = "T"
            else:
                suffix = "B"
        if str(elem).endswith("M"):
            elem = elem.replace("M", "")
            suffix = "M"
        if str(elem).endswith("K"):
            elem = elem.replace("K", "")
            suffix = "K"
        if str(elem).endswith("%"):
            elem = elem.replace("%", "")
            suffix = "%"
        if str(elem).startswith("+"):
            prefix = "+"
            elem = elem.lstrip("+")
        # dbug(elem)
        # elem_val = escaped(elem) # making sure
        elem_val = parse_codes(elem, 'escaped') # making sure
        # dbug(elem_val)
        # dbug(rnd)
        if rnd == 0:
            elem_val = str(int(float(elem_val)))  # needs to be str for next test
        if isnumber(rnd) and rnd > 0:
            # dbug("rnd scale is declared: {rnd}")
            elem_val = str(round(float(elem_val), rnd))
        if clr_b:  # and not re.search(r"[BGMKT]", elem_val):
            if "." in str(elem_val):  
                # this must be a float number
                clean_val = elem_val.replace(",", "").replace("%", "")
                elem_val = float(clean_val)
            else:
                # not a float number
                if isnumber(elem):
                    try:
                        elem_val = int(elem_val)
                    except Exception as Error:
                        dbug(f"elem: {elem} elem_val: {elem_val} Error: {Error}")
            # dbug(f"chkg elem_val: {elem_val} for pos/neg")
            if elem_val < 0 or (elem_val == 0 and str(elem_val).startswith("-")):
                prefix = NEG_COLOR
                # dbug(f"setting {NEG_COLOR}color{RESET} for elem_val: {elem_val} elem: {elem")
            else:
                prefix = POS_COLOR
                # dbug(f"POS_COLOR: {POS_COLOR} {repr(POS_COLOR)}")
        # dbug(elem_val)
        # dbug(repr(elem))
        if human:
            # dbug(f"working on humanizing elem_val: {elem_val} suffix: {suffix}")
            if not str(elem_val).endswith(("B", "M", "K", "G", "T", "Kb", "Mb", "%", "$")):
                if float(elem_val) >= 1000000000000:
                    # dbug(f"elem_val: {elem_val} is over a trillion")
                    elem_val = float(elem_val) / 1000000000000
                    elem_val = str(round(elem_val, 2)) + "T"
            if not str(elem_val).endswith(("B", "M", "K", "G", "T", "Kb", "Mb", "%")):
                if float(elem_val) >= 1000000000:
                    elem_val = float(elem_val) / 1000000000
                    elem_val = str(round(elem_val, 2)) + "B"
            if not str(elem_val).endswith(("B", "M", "K", "G", "T", "Kb", "Mb", "%")):
                try:
                    if float(elem) >= 1000000:
                        elem_val = float(elem_val) / 1000000
                        elem_val = str(round(elem_val, 2)) + "M"
                except Exception as Error:
                       dbug(f"Error: {Error} elem_val: {elem_val} repr(elem_val): {repr(elem_val)}")
            if not str(elem_val).endswith(("B", "M", "K", "G", "T", "Kb", "Mb", "%", "$")):
                if float(elem_val) >= 1000:
                    # dbug(elem_val)
                    elem_val = float(elem_val) / 1000
                    elem_val = round(float(elem_val),2)  # just round it now... you can thank me later
                    # if isnumber(rnd) and int(rnd) > 0:
                        # elem_val = str(round(elem_val, rnd))
                    elem_val = str(elem_val) + "K"
                    # dbug(elem_val)
            if "," in str(elem_val):
                elem_val = str(elem_val).replace(",", "")
                elem_val = "'" + elem_val + "'"
            if str(elem_val).replace(".", "").isnumeric():
                elem_val = f"{float(elem_val):,}"
            # dbug(f"Done umanizing elem_val: {elem_val}")
        if isnumber(elem_val) and commas_b:
            # dbug(elem_val)
            elem_val = f"{float(elem_val):,}"
        # dbug(repr(elem))
        # elem = prefix + str(elem_val) + suffix
    # dbug(elem_CODES)
    # dbug(repr(elem))
    if had_commas and isnumber(elem, 'human'):  # note: this will not allow "human" numbers to pass through
        # dbug(elem)
        # dbug(type(elem))
        if not str(elem).endswith(("B", "M", "K", "G", "T", "Kb", "Mb", "%", "$")):
            elem = f"{float(elem):,}"
    if pcnt_b:
        elem = f"{float(elem)}%"
    # """--== this where we apply needed changes and restore needed symbols ==--"""
    # the order here is important #
    elem = prefix + str(elem_val) + suffix  # this needs to be the last thing done
    elem = elem_CODES[0] + elem + elem_CODES[1]
    if rset:
        # this seems to work 20240323 adds reset only if escape codes exist
        # dbug(rset)
        # if len(elem) > len(escaped(elem)):
        if len(elem) > len(parse_codes(elem, 'escaped')):
            # dbug("Adding RESET")
            elem += RESET
    # """--== returning ==--"""
    # dbug(f"Returning elem: [{elem}{RESET}]")  # , 'ask')
    return elem
    # ###  EOB def cond_num(elem, *args, **kwargs): ### #


# alias for above
# cond_num = color_neg
color_neg = cond_num


# ########################################
def data_conditions(data, conditions_lol):
    # ####################################
    """
    purpose: change color of elements that meet conditions
    requires: 
        data (an lol [list of lists] ie rows of columns)
        conditions_lol: [[compare1_colname, operator, compare2_colname, {"colname": "color"}], ...] <-- syntax of conditions_lol
          Please note: the third element is what I will call 'action' and it can be either a tuple (shown above) or a dictionary shown below
            Also the compareX_colname can be a (non-string) number... ie an int or a float
          - operator: str    # can be "<", "lt", "<=", "le", ">", "gt", ">=", "ge", "==", "eq", "="
          - action: dict|tuple  # this is the third condition element which names the colname to be changed and then the color to change it to
    returns: new data set with colorized element values
          - eg new_lol = data_conditions(data_lol, ["cmp1_colname', 'operator', 'cmp2_colname', ('colname', 'color'))
          - conditions_lol = [['cmp1_colname', 'op', 'cmp2_colname', ('colname', 'color_action')], ...]
    notes:
      - eg: [["lpr", ">=", "trgt", {"lpr": "green!"}], ["cp", "<", "lpr", {"lpr": "red!"}]
      - eg: [["lpr", ">=", 30, {"lpr": "green!"}], ["cp", "<", "lpr", {"lpr": "red!"}]
      - this function may get deprecated (see conditionals() as a replacement)
    """
    # """--== Debugging ==--"""
    # dbug(f"funcname: {funcname()} called from: {called_from()}")
    # dbug(data[:3])
    # dbug(conditions_lol)
    # dbug('ask')
    dbug(f"[red!]STOP[/] you should use consitionals() instead! {called_from()}", 'ask') 
    # """--== Validate ==--"""
    if isempty(data):
        # dbug("data appears to be empty... returning None")
        return None
    # """--== Convert ==--"""
    dtype = data_type(data)
    # """--== make data an lol ==--"""
    if dtype not in ('lol'):
        #  make sure we are dealing with an lol
        data = cnvrt(data)
    # """--== make data a lod ==--"""
    # colnames = data_lol[0]
    # data_lod = [dict(zip(colnames, row)) for row in data_lol] 
    # dbug(data_lod)
    # """--== SEP_LINE ==--"""
    if isinstance(conditions_lol, list) and dtype not in ('lol'):  # not islol(conditions_lol):
        # dbug(f"converting to list of lists")
        conditions_lol = [[conditions_lol]]  # making sure it is an lol
    colnames = data[0]
    # """--== Init ==--"""
    rows_lol = data  # TODO change (eliminate this)
    colnames = rows_lol[0]
    new_rows = [rows_lol[0]]
    # """--== Process ==--"""
    for row in rows_lol[1:]:
        my_row = row
        # dbug(my_row)
        # dbug(conditions_lol)
        for condition in conditions_lol:
            # dbug(condition)
            cmp1_colname = condition[0]
            if cmp1_colname not in colnames and not isinstance(cmp1_colname, (int, float)):
                dbug(f"cmp1_colname: {cmp1_colname} not found in colnames: {colnames}... returning")
                return
            op = condition[1]
            cmp2_colname = condition[2]
            if cmp2_colname not in colnames and not isinstance(cmp2_colname, (int, float)):
                dbug(f"cmp2_colname: {cmp2_colname} not found in colnames: {colnames}... returning")
                return
            action = condition[3]
            cmp1_indx = colnames.index(cmp1_colname)
            if isinstance(cmp1_colname, (int, float)):
                cmp1_val = float(cmp1_colname)
            else:
                # cmp1_val = escaped(row[cmp1_indx])
                cmp1_val = parse_codes(row[cmp1_indx], 'escaped')
            try:
                if isinstance(cmp2_colname, (int, float)):
                    cmp2_val = float(cmp2_colname)
                else:
                    cmp2_indx = colnames.index(cmp2_colname)
                    # cmp2_val = escaped(row[cmp2_indx])
                    cmp2_val = parse_codes(row[cmp2_indx], 'escaped')
            except Exception:
                if isnumber(cmp2_colname):
                    cmp2_val = float(cmp2_colname)
                    # dbug(f"cmp2_val: {cmp2_val} Error: {Error}")
            # dbug(action)
            if isinstance(action, dict):
                action_col = list(action.keys())[0]
                action_val = action[action_col]
                # dbug(action_col, action_val)
            if isinstance(action, (list, tuple)):
                action_col = action[0]
                action_val = action[1]
            if not isinstance(action, (list, tuple, dict)):
                dbug(f"action: {action} type(action): {type(action)} must be a dictionary ... returning...")
                return None
            if action_col not in colnames:
                dbug(f"action_col: {action_col} not found in colnames: {colnames}... returning")
                return
            action_indx = colnames.index(action_col)
            # dbug(action_indx)
            # action_val = escaped(row[action_indx])
            # my_val = escaped(row[action_indx])
            my_val = parse_codes(row[action_indx], 'escaped')
            # dbug(action_val)
            action_clr = action_val
            # dbug(action_clr)
            # dbug(row)
            if isnumber(cmp1_val) and isnumber(cmp2_val):
                cmp1_val = float(cmp1_val)
                cmp2_val = float(cmp2_val)
                new_elem = row[action_indx]
                if op in ('<', 'lt'):
                    if cmp1_val < cmp2_val:
                        new_elem = gclr(action_clr) + my_val
                        # dbug(f"{cmp1_colname} {op} {cmp2_colname}")
                        # dbug(f"{cmp1_val}  {op} {cmp2_val} = {new_elem}")
                        # my_row[action_indx] = new_elem
                elif op in ('<=', 'le'):
                    if cmp1_val < cmp2_val:
                        new_elem = gclr(action_clr) + action_val
                        # dbug(f"{cmp1_val}  {op} {cmp2_val} = {new_elem}")
                        # my_row[action_indx] = new_elem
                elif op in ('>', 'gt'):
                    # dbug(f'op: {op} cmp1_val: {cmp1_val} cmp2_val: {cmp2_val}')
                    if cmp1_val > cmp2_val:
                        new_elem = gclr(action_clr) + my_val
                        # dbug(f"{cmp1_val}  {op} {cmp2_val} = {new_elem}")
                        # my_row[action_indx] = new_elem
                elif op in ('>=', 'ge'):
                    if cmp1_val >= cmp2_val:
                        new_elem = gclr(action_clr) + action_val
                        # dbug(f"{cmp1_val}  {op} {cmp2_val} = {new_elem}")
                        # my_row[action_indx] = new_elem
                elif op in ('==', 'eq', "="):
                    if cmp1_val == cmp2_val:
                        # dbug(f"{cmp1_val}  {op} {cmp2_val} = {new_elem}")
                        new_elem = gclr(action_clr) + action_val
                else:
                    dbug(f"Not sure what to do with op: {op}... returning None")
                    return None
                my_row[action_indx] = new_elem
                # dbug(new_elem)
                # dbug(my_row[action_indx])
                # """--== SEP_LINE ==--"""
            # return row
        new_rows.append(my_row)
    return new_rows
    # ### EOB def data_conditions(data, conditions_lol): ### #

# alias
data_cond = data_conditions


# ##################################################
def conditionals(data, my_conditions, *args, **kwargs):
    # ##############################################
    """
    purpose: to apply conditions to all rows after colnames
    requires:
        - data: list          # list of rows (of columns) or some other variations of data (it will get converted to an lol for processing and return)
        - my_conditions: list # list of conditions (see usage)
    options:
        - prnt: bool
        - pivot: boot
    usage:
        - syntax of a condition: str   # if condition /then color_coded  or calc equals column
            - 'if col(xxx) = 5 then [yellow]col(yyy)[/]'  # if/then condition color coding example
            - 'col(xxx) * 4 equals col(yyy)'              # calc equals condition example (if col(yyy) does not exist it will be added to the data)
            - 'col(xxx) < 1.5 then delete                 # this will delete a row that matches the condition of col(xxx) < 1.5 it acts as a conditional filter on data
            - "'A' in col(fml_sr) then [green!]col(fml_sr)[/]"  # if an 'A' ins in the col(fml_sr) value then make it green
            - see the notes below!!!
    notes:
        - this function literally does eval() on the left side of the equation for every row and (after the col(XXX) has been replaced with that the val held in that column)
            - as a somewhat non-intuitive example ... lets say you have two columns named "Key" and "Value" and lets say
              you want to make the value flash green when the key is "PE_Ratio" here is the condition to use
                     "'col(Key)' == 'PE_Ratio' and col(Value) < 15 then [flash green]col(Value)[/]"
                or another example:
                     "col(price) < col(trgt) and 'col(action)' == 'put' then [flash green]col(price)[/]"
        - this replaces data_conditions() and add_cols() which will get deprecated
        - I struggle with the name for this function
        - if there are (nested) parentheses in the colname then double ecape the ().
            - for example colname is 'RSI (14)' then use something like this for the condition: 'col(RSI \\(14\\)) > 70 then [red!]col(RSI \\(14\\))[/]', 
    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    footer = kvarg_val(['footer'], kwargs, dflt="")
    title = kvarg_val(['title'], kwargs, dflt="")
    centered_b = arg_val(['cntrd', 'centered', 'cntr', 'center'], args, kwargs, dflt=False)
    pivot_b = arg_val(['pivot'], args, kwargs, dflt=False)
    # colnames = arg_val(['colnames', 'columns'], args, kwargs, dflt=[])
    # dbug(colnames)
    # """--== Validate ==--"""
    if isempty(data):
        dbug(f"data appears empty - called_from: {called_from()} ... returning...")
        return None
    # """--== Convert ==--"""
    if not data_type(data, 'lol'):
        data_lol = cnvrt(data)
    else:
        data_lol = data
    if isinstance(my_conditions, str):
        my_conditions = [my_conditions]
    # dbug(my_conditions, 'lst')
    # """--== convert old data_conditions syntax to this syntax ==--"""
    new_lol = []
    for cond in my_conditions:
        # dbug(cond)
        new_cond = cond
        if len(cond) == 4:
            if cond[1] == "=":
                # dbug(cond[1])
                cond[1] = "=="
                # dbug(cond[1], 'ask')
            new_cond = f"if col({cond[0]}) {cond[1]} col({cond[2]}) then "
            if isinstance(cond[3], dict):
              for k,v in cond[3].items():
                  add_this = f"[{v}]col({k})[/]"
            if isinstance(cond[3], (tuple, list)):
              add_this = f"[{cond[3][1]}]col({cond[3][0]})[/]"
            new_cond += add_this
        # dbug(new_cond)
        new_lol.append(new_cond)
    my_conditions = new_lol
    # dbug(my_conditions, 'lst', 'ask')
    # """--== make data a lod ==--"""
    # dbug(data_lol)
    # if isempty(colnames):
    colnames = data_lol[0]
    # """--== deal with pivot ==--"""
    # dbug(pivot_b)
    if pivot_b:
        # dbug("I am not terribly pleased with this strategy but it seems to work-we undo pivot and run conditionals, then redo pivot")
        # colnames = [row[0] for row in data_lol]    
        undo_pvt_lol = pivot(data_lol)
        # dbug(undo_pvt_lol[0])
        cond_lol = conditionals(undo_pvt_lol, my_conditions)
        rtrn_lol = pivot(cond_lol)
        return rtrn_lol
    # orig_colnames = colnames
    # dbug(f"colnames: {colnames} orig_colnames: {orig_colnames}") 
    # """--== Init ==--"""
    phrases = []
    trgt = ""
    # new_columns = []
    new_lol = [data_lol[0]]
    # """--== Process ==--"""
    data_lol = fixlol(data_lol)
    # dbug(colnames)
    for row in data_lol[1:]:
        skip_row_flag = False
        orig_row = row
        # dbug(f"======= handlng row: {row} colnames: {colnames} ============")
        new_row = row
        # add_row = ['to_calc'] * len(colnames)  # init new row to add
        for cond_num, condition in enumerate(my_conditions):
            # dbug(condition)
            orig_condition = condition  # this is for debugging
            # """--== loop init ==--"""
            cmp = ""
            raw_condition = ""
            # formula = ""
            # new_col = ""
            indxs = []
            new_colname = ""
            # """--== escaped parens kludge ==--"""
            # this is a kludge for (double) escaped nested parens "(" ")" ie col(foo \\(what_ever\\) bar)
            condition = condition.replace('\\(', '_[_')
            condition = condition.replace('\\)', '_]_')
            #condition = condition.replace('"', '')
            #condition = condition.replace("'", '')
            condition = condition.replace("if ","")
            # dbug(condition)
            # kludge continues below
            # """--== pattern matches ==--"""
            pattern = r"col\((.*?)\)"
            matches = re.compile(pattern).findall(condition)
            # dbug(matches)
            # """--== loop for each match found in this condition ==--"""
            # this substitutes the true value of each col(XXX) in the condition #
            for num, match in enumerate(matches, start=1):
                this_indx = None
                my_val = None
                # dbug(type(my_val))
                if match[0] in ('"', "'") and  match[0] == match[-1]:
                    # dbug(f"Need to dequote this match: {match}")
                    match = match[1:-1]
                    # dbug(match, 'ask')
                # kludge for escaped () continued
                if "_[_" in match:
                    # dbug(match, 'ask')
                    match = match.replace("_[_", "(")
                    match = match.replace("_]_", ")")
                    # dbug(match)
                    condition = condition.replace("_[_", "(")
                    condition = condition.replace("_]_", ")")
                    # dbug(condition)
                if match in colnames:
                    # dbug(f"match: {match} colnames: {colnames}")
                    this_indx = colnames.index(match)
                    # dbug(f"match: {match} colnames: {colnames} this_indx: {this_indx}")
                    # dbug(f"{new_row=} {this_indx=} {match=}")
                    try:
                        this_val = str(new_row[this_indx]).strip()  # I have seen leading spaces which caused a prob - just get rid of leading/trailing spaces
                    except Exception as Error:
                        dbug(f"{Error=} {match=} {colnames=} {this_indx=} {new_row=} ")
                    # my_val = escaped(this_val)
                    my_val = parse_codes(this_val, 'escaped')
                    # dbug(my_val)
                else:
                    # if ' equals ' not in condition:
                    #     dbug(f"I do not recognize this col to match: {match} and there is not ' equals ' in the condition: {condition}...\npossible colnames: {data_lol[0]}\ncontinuing on...")
                    #     return
                    # dbug(f"match: {match}... establishing a new_colname called match: {match}")
                    new_colname = match
                    colnames.append(new_colname)
                    this_indx = colnames.index(new_colname)
                if  my_val == "None":
                    my_val = 0
                if len(new_row) < len(colnames):
                    # my_val = "no_value"
                    my_val = ""
                    new_row.append(my_val)
                indxs.append(this_indx)  # the last indx will be the trgt or rslt indx
                # my_val = escaped(new_row[this_indx])
                if my_val is not None and "None" in str(my_val):
                    dbug(orig_condition)
                    dbug(my_val, 'ask')
                if my_val is None:
                      dbug(my_val, 'ask')
                if "%" in str(my_val):
                    # this is a kludge because I "condition" numbers that have % in them
                    regex = re.findall('([-]?\\d+[.\\d]+)?%', my_val)  # seems to work
                    if len(regex) > 0:
                        if regex[0] is not None:
                            my_val = regex[0]
                            # dbug(my_val)
                    else:
                        dbug("regex failed???")
                # dbug(my_val)
                # if  "_" in str(my_val):
                    # my_val = 0
                if isempty(my_val):  # or my_val == "-":
                    my_val = 0
                if isnumber(my_val, 'human'):
                    # if isnumber(my_val):
                    my_val = re.sub('[TBMKk%,]+', "", str(my_val))
                    my_val = float(my_val)
                if my_val is None or my_val == "None":
                      dbug(my_val, 'ask')
                if my_val is not None and "None" in str(my_val):
                    dbug(orig_condition)
                    dbug(my_val, 'ask')
                raw_condition = condition.replace(f'col({match})', str(my_val))
                # """--== clean and split ==--"""
                condition = raw_condition.replace("if ", "")
                if " then " in condition:
                    phrases = condition.split(" then ")
                    # dbug(phrases)
                if ' equals ' in condition:
                    # phrases = raw_condition.split(" equals ")
                    phrases = condition.split(" equals ")
                    # dbug(phrases)
                if len(phrases) < 2:
                    dbug(f"Perhaps you forgot the word 'then' or 'equals' in the condition: {condition}... continuing on...")
                    continue
                cmp = phrases[0]  # <-- note only phrases[0]
                # dbug(cmp)
                if ' in ' in cmp:
                    # dbug(f"found ' in ' inc {cmp=} {condition=}")
                    # new_cmp = ""
                    my_words = cmp.split(" in ")
                    my_words = [w.strip() for w in my_words]
                    # dbug(my_words)
                    new_words = []
                    for my_word in my_words:
                        if  my_word[0] == my_word[-1] and my_word[0] in ("'",'"'):
                            # dbug(f"my_word:{my_word} ...we have a winner")
                            my_word = my_word[1:-1]
                            # dbug(f"my_word:{my_word} ...we have fixed it")
                        new_words.append(my_word)
                    cmp = f"'{new_words[0]}' in '{new_words[1]}'" # then {new_words[2]}"
                    # dbug(cmp, 'ask')
                if '==' in cmp:
                    # new_cmp = ""
                    my_words = cmp.split("==")
                    my_words = [w.strip() for w in my_words]
                    # dbug(my_words)
                    new_words = []
                    for my_word in my_words:
                        if  my_word[0] == my_word[-1] and my_word[0] in ("'",'"'):
                            # dbug(f"my_word:{my_word} ...we have a winner")
                            my_word = my_word[1:-1]
                            # dbug(f"my_word:{my_word} ...we have fixed it")
                        new_words.append(my_word)
                    cmp = f"'{new_words[0]}' in '{new_words[1]}'" # then {new_words[2]}"
                    # cmp = f"{my_words[0]} == {my_words[1]}"
                    # dbug(cmp, 'ask')
                if len(phrases) == 2:
                    trgt = phrases[1]
                    # dbug(trgt)
            # """--== now run the rslt test or calc ==--"""
            # cmp = escaped(cmp)
            cmp = parse_codes(cmp, 'escaped')
            rslt = False
            # dbug(cmp)
            try:
                rslt = eval(f"{cmp}")  # <--- where the rubber hits the road
                # dbug(f"cmp: {cmp} rslt: {rslt} {called_from('v')}")
            except Exception as Error:
                # dbug(f"Failed to eval(cmp) cmp: {cmp} rslt: {rslt} this might be expected")
                # dbug(orig_condition)
                # dbug(raw_condition)
                # dbug(condition)
                # dbug(phrases)
                # dbug(f"cmp: {cmp}  {Error=} {colnames=} {called_from('v')}", 'xask')  # this is noisey
                continue
            # """--== replace the trgt in new_row with new value ==--"""
            trgt_indx = indxs[-1]  # this assumes that the target is the last column value
            # dbug(indxs)
            # dbug(colnames)
            # dbug(trgt_indx)
            if ' then ' in condition:
                if rslt:  # if the rslt is True ie eval(cmp) is True...  then replace the trgt in the row with new_val
                    if trgt in ('delete', 'skip', 'remove', 'ignore', 'filter'):
                        # dbug(f"We should skip the row where this condition ie delete,skip,remove,etc is true rslt: {rslt}")
                        skip_row_flag = True 
                        # new_row = ""
                    else:
                        # dbug(trgt)
                        codes_l = parse_codes(trgt, 'list')
                        prefix = codes_l[0]
                        suffix = codes_l[-1]
                        orig_trgt = parse_codes(orig_row[trgt_indx], 'escaped')
                        # if isinstance(trgt, str) and trgt[0] == trgt[-1] and trgt[0] in ("'",'"'):
                            # new_val = dequote(trgt)
                        # else:
                            # new_val = f"{prefix}{orig_trgt}{suffix}"
                        new_val = f"{prefix}{orig_trgt}{suffix}"
                        # new_val = f"{orig_trgt}"
                        new_row[trgt_indx] = new_val  # the last indx is the trgt or rslt indx
                        # dbug(f"cmp: {cmp} new_val: {new_val} repr(new_val): {repr(new_val)}")
                        # dbug(new_row)
            if ' else ' in condition:
                # my_action = condition.split(" else ")[1]
                my_action = trgt.split(" else ")[1]
                # this_trgt = my_action[1]
                # dbug(f"{condition=} {rslt=} {my_action=} {trgt=} {trgt_indx=}")
                # dbug(indxs)
                # dbug(trgt_indx)
                # dbug(f"{colnames[trgt_indx]=}")
                # dbug(rslt)
                if not rslt:
                    codes_l = parse_codes(my_action, 'list')
                    prefix = codes_l[0]
                    suffix = codes_l[-1]
                    orig_trgt = parse_codes(orig_row[trgt_indx], 'escaped')
                    if isinstance(my_action, str) and my_action[0] == my_action[-1] and my_action[0] in ("'",'"'):
                        # dbug("Whew, this took a while", 'ask')
                        new_val = dequote(my_action)
                    else:
                        new_val = f"{prefix}{orig_trgt}{suffix}"
                    # dbug(new_val)
                    new_row[trgt_indx] = new_val  # the last indx is the trgt or rslt indx
                    # dbug(f"cmp: {cmp} new_val: {new_val} repr(new_val): {repr(new_val)}")
                    # dbug(new_row)
                # dbug("stop stop stop", 'ask')
            if ' equals ' in condition:
                new_val = rslt
                new_row[trgt_indx] = new_val
        # """--== add the new_row into new_lol ==--"""
        if not skip_row_flag:
            new_lol.append(new_row)
            # printit(" ".join(new_row), 'boxed', title="debugging", footer=dbug('here'))
    # """--== return ==--"""
    if prnt:  # or 1:  # is for debugging
        if footer == "":
            footer = dbug('here')
        gtable(new_lol, 'hdr', 'prnt', title=title, centered=centered_b, footer=footer, col_clr='white')
    return new_lol
    # ### EOB def conditionals(data, conditions, *args, **kwargs): ### #


# ####################################
def get_random_line(file, prnt=False, *args, **kwargs):
    # ################################
    """
    purpose: grabs one random line from a file
    requires:
        - file: str|list  # can be a filename or it can be a list of lines or a string with newlines
        import random
        file: str | list  # can be a filename or it can be a list of lines
    returns: line
    Note: file has all comments removed first (purified)
    """
    # """--== Imports ==--"""
    import random
    # """--== Validation  ==--"""
    if isinstance(file, str):
        file = os.path.expanduser(file)
        if not file_exists(file):
            dbug(f"Failed to find file: {file} or lines {called_from('verbose')}")
            return
    if isinstance(file, list):
        contents_l = purify_file(file)
    else:
        contents_l = purify_file(file)
    # """--== Process ==--"""
    # dbug(len(contents_l))
    line = random.choice(contents_l)
    if prnt:
        lines = boxed(line, title=" Choosen lines ")
        printit(centered(lines))
    return line
    # ### EOB def get_random_line(file, prnt=False): ### #


# #########################################
def run_cmd_threaded(cmd, *args, **kwargs):
    # #####################################
    """
    purpose: runs a cmd as a thread
    options:
        - lst: bool  # returned output lines will be put into a list rather than a str
    return: output from cmd
    Note: Please, be aware that a result will be returned only after this finishes
    so put it "later" rather than "sooner" in your app
      - does not currently return error msgs
    """
    # """--== Debugging ==--"""
    # dbug("who uses this?")
    # """--== Config ==--"""
    lst = arg_val(['lst', 'list'], args, kwargs, dflt=False)
    # """--== Process ==--"""
    t = ThreadWithReturn(target=run_cmd, args=(cmd,))
    t.start()
    result = t.join()
    if lst:
        result = result.split("\n")
    return result

# #################################
def run_cmd(cmd, *args, **kwargs):
    # #############################
    """
    purpose: runs cmd and returns output
      eg: out = run_cmd("uname -o",False)
      # now you can print the output from the cmd:
      print(f"out:{out}")
    options:
        - lst: bool         # ouput will return as a list of line rather than a str
        - rc_only: bool     # returns the cmd return code instead of output
        - error: bool       # also returns error added onto the standard output of cmd
        - both|rc: bool     # returns (output, rc)
        - runas: str        # you can declare who to run the cmd as
        - prnt: bool        # print output - returns None
        - fork: bool        # run as external interactive process
        - blanks: bool=True # include blankline
        - list_b: bool      # return output as a list
        - rtrn_type: str="" # if rtrn_type == "dict" then a dictionary will be returned {'stdout': stdout, 'stderr": stderr, "rc":rc}
    returns: output from command
    Note: if runas == sudo then the command will be run with sudo...
      - this function strips out all ansi code and filters all errors
      - does not currently return error msgs
      - as it is today 20221201 you lose color output - use os.system(cmd) instead for simple output or use 'prnt' option
      - there is what seems to be unnecessary code but it is to keep this backwards compatible
    """
    prnt = arg_val(['prnt', 'verbose', 'show', 'print'], args, kwargs, dflt=False)
    rc_only_b = arg_val(['rc_only', 'return_rc', 'rtrn_rc'], args, kwargs, dflt=False)
    all_b = arg_val(['both', "rc", "all"], args, kwargs, dflt=False)
    both_b = arg_val(['both'], args, kwargs, dflt=False)
    runas = arg_val(["runas", "sudo"], args, kwargs, dflt="")
    error_b = arg_val(["errors", "err", "errs", "error"], args, kwargs, dflt=False)
    background_b = arg_val(["bg", 'nohup', 'background'], args, kwargs, dflt=False)
    fork_b = arg_val(['fork'], args, kwargs, dflt=False)
    blanks_b = arg_val(["blanks"], args, kwargs, dflt=True, opposites=["noblanks", "skipblanks"])
    lst_b = arg_val(['list', 'lst'], args, kwargs, default=False)
    rtrn_type = arg_val(['rtrn', 'rtrn_type'], args, kwargs, dflt="")
    # """--== SEP_LINE ==--""" #
    out = ""
    if runas != "":
        if runas == 'sudo':
            cmd = f"sudo {cmd}"
        else:
            cmd = f"sudo -u {runas} {cmd}"
    if background_b:
        cmd += " &"
    if not blanks_b:
        lst_b = True
    # """--== here be the meat | rubber hits the road==--""" #
    r = subprocess.run(cmd, capture_output=True, shell=True, text=True, start_new_session=fork_b)
    r_d = {'stdout':r.stdout,'stderr':r.stderr,'rc':r.returncode}
    # """--== assemble out ==--""" #
    if lst_b or not blanks_b:
        r_d['stdout'] = r_d['stdout'].split("\n")
        r_d['stderr'] = r_d['stderr'].split("\n")
        r_d['rc'] = [f"{r_d['rc']=}"]
        if not blanks_b:
            r_d['stdout'] = [line for line in r_d['stdout'] if line.strip()]
            r_d['stderr'] = [line for line in r_d['stderr'] if line.strip()]
            # dbug(r_d['stdout'], 'boxed', 'noask')
            # dbug(r_d['stderr'], 'boxed', 'ask')
    out = r_d['stdout']  # unless it get changed below 
    if both_b:
        out_s = r_d['stdout']
        rc = r_d['rc']
        return out_s, rc
    if all_b:
        if lst_b:
            out = r_d['stdout'] + r_d['stderr'] + r_d['rc']
        else:
            out = f"{r_d['stdout']} {r_d['stderr']=} {r_d['rc']=}" 
    if error_b:
        out = r_d['stderr']
    if rc_only_b:
        out = r_d['rc']
    if rtrn_type == "dict":
        out = r_d
    return(out)
    # ### EOB def run_cmd(cmd, *args, **kwargs): ### #


# # ###########################################
# def run_cmd(command_string, *args, **kwargs):
#     # #######################################
#     """
#     purpose: runs cmd and returns output
#       eg: out = run_cmd("uname -o",False)
#       # now you can print the output from the cmd:
#       print(f"out:{out}")
#     options:
#         - lst: bool         # ouput will return as a list of line rather than a str
#         - rc_only: bool     # returns the cmd return code instead of output
#         - error: bool       # also returns error added onto the standard output of cmd
#         - both|rc: bool     # returns (output, rc)
#         - runas: str        # you can declare who to run the cmd as
#         - prnt: bool        # print output - returns None
#         - fork: bool        # run as external interactive process
#         - blanks: bool=True # include blankline
#         - list_b: bool      # return output as a list
#     returns: output from command
#     Note: if runas == sudo then the command will be run with sudo...
#       -  this function strips out all ansi code and filters all errors
#       - does not currently return error msgs
#       - as it is today 20221201 you lose color output - use os.system(cmd) instead for simple output or use 'prnt' option
#       - TODO: refactor this so it has one return
#     """
#     # dbug(funcname)
#     # dbug(cmd)
#     # """--== local imports ==--""" #
#     import shlex
#     # """--== Config ==--"""
#     prnt = arg_val(['prnt', 'verbose', 'show', 'print'], args, kwargs, dflt=False)
#     # return_l = arg_val(['list', 'lines', 'lst'], args, kwargs)
#     rc_only_b = arg_val(['rc_only', 'return_rc', 'rtrn_rc'], args, kwargs, dflt=False)
#     both_b = arg_val(['both', "rc"], args, kwargs, dflt=False)
#     runas = arg_val(["runas", "sudo"], args, kwargs, dflt="")
#     errors_b = arg_val(["errors", "err", "errs", "error"], args, kwargs, dflt=False)
#     background_b = arg_val(["bg", 'nohup', 'background'], args, kwargs, dflt=False)
#     fork_b = arg_val(['fork'], args, kwargs, dflt=False)
#     blanks_b = arg_val(["blanks"], args, kwargs, dflt=True, opposites=["noblanks", "skipblanks"])
#     list_b = arg_val(['list', 'lst'], args, kwargs, default=False)
#     # """--== Init ==--"""
#     # out = ""
#     if runas != "":
#         if runas == 'sudo':
#             cmd = f"sudo {command_string}"
#         else:
#             cmd = f"sudo -u {runas} {command_string}"
#     if background_b:
#         cmd += " &"
#     # """--== SEP_LINE ==--""" #
#     if fork_b:
#         shlex_args = shlex.split(cmd)
#         # start_new_session=True keeps the child alive if the parent exits
#         subprocess.Popen(
#             shlex_args,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             start_new_session=True
#         )
#     # Split the command string by '|' and parse each part into a list
#     commands = [shlex.split(part.strip()) for part in command_string.split('|')]
#     processes = []
#     prev_stdout = None
#     try:
#         for i, cmd in enumerate(commands):
#             # is_last = (i == len(commands) - 1)
#             # Every process pipes its stdout to the next,  and the last one pipes to the parent (Python)
#             dbug(f"{cmd=} using subprocess.Popen with options...")
#             p = subprocess.Popen(
#                 cmd,
#                 stdin=prev_stdout,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 text=True  # Returns strings instead of bytes
#             )
#             p.wait()
#             if not p.stdout and not p.stderr:
#                 dbug("Can we fix this?")
#             processes.append(p)
#             # Close the previous process's pipe in the parent to avoid hangs
#             if prev_stdout:
#                 prev_stdout.close()
#             prev_stdout = p.stdout
#         # Capture results from the final process
#         stdout, stderr = processes[-1].communicate()
#         returncode = processes[-1].returncode
#         # Optionally: Check if any upstream processes failed
#         # for p in processes:
#         #     if p.wait() != 0:
#         #         # handle internal pipe failure here if needed
#         if prnt:
#             dbug(f"{stdout=} {stderr=} {returncode=}")
#         if list_b:
#             stdout = stdout.split("\n")
#             if not blanks_b:
#                 stdout = [line for line in stdout if line]
#         if rc_only_b:
#             return returncode
#         if both_b:
#             return stdout, returncode
#         if errors_b:
#             return stdout + " - " + stderr
#         # return stdout, stderr, returncode
#         return stdout
#     except FileNotFoundError as e:
#         return None, f"Command not found: {str(e)}", 127
#     except Exception as e:
#         return None, str(e), -1
#     # return rtrn
#    # ### EOB def run_cmd(cmd, *args, prnt=False, runas="", **kwargs): ### #

# alias
runcmd = run_cmd


def grep_lines(lines, pattern, *args, **kwargs):
    """
    purpose: searches lines (or file if lines is a filename) for pattern
    options:
    -    ic: bool (insensitive case)
    -        rtrn_bool=False: bool    #  (whether to rtrn lines [default] or bool result)
    -        csv: bool                # will convert a list of lists to a list of csv style lines before searching
    -                                 #   and but returns the line as a list, just the way we got it
    returns: matched line(s) (or True False if rtrn_bool is True)
    Note: if only one line is matched then it will return that one line otherwise it will return a list of matched_lines
    """
    # used in do_watch and maybe others
    # dbug(called_from())
    # dbug(pattern)
    # """--== Config ==--"""
    ic = arg_val(['ic', 'ci', 'case_insensitive', 'ignore_case'], args, kwargs)
    rtrn_b = arg_val(['rtrn_bool', 'rtrn_d', 'bool', 'rtrn'], args, kwargs, dflt=False)
    csv_b = arg_val(['csv'], args, kwargs, dflt="")
    # """--== Xlate filename to lines ==--"""
    if isinstance(lines, str):
        # dbug(lines)
        lines = cat_file(lines, 'lst', 'raw')
        # dbug(len(lines))
    # """--== Process ==--"""
    matched_lines = []
    for line in lines:
        line = str(line)
        # dbug(line)
        # this might have been taken from a list of list (lol) so convert the list to a csv style line
        if csv_b or isinstance(line, list):
            # dbug(line)
            csv_b = True
            orig_line = line
            # dbug(orig_line)
            line = [str(elem) for elem in line]
            line = ", ".join(line)
        if ic:
            # ignore case
            rex_b = re.search(pattern, line, re.I)
        else:
            # case sensitive
            # dbug(pattern)
            # dbug(line)
            rex_b = re.search(pattern, line)
            # dbug(rex_b)
        if rex_b:
            # dbug(f"rex_b: {rex_b} pattern: {pattern}")
            # use the regex set above
            if csv_b:
                matched_lines.append(orig_line)
            else:
                matched_lines.append(line)
    # dbug(matched_lines)
    if rtrn_b:
        if len(matched_lines) > 0:
            return True
        else:
            return False
    if len(matched_lines) == 1:
        matched_lines = [matched_lines[0]]
    if len(matched_lines) == 0:
        matched_lines = None
    return matched_lines


# ###############################
def list_files(dirs, file_pat="*", *args, **kwargs):
    # ###########################
    """
    purpose: prints a list of enumerated basename filenames (sorted by name)
    input:
        dirs=list|str
    options:
        pattern: str|list = "*"  # glob pattern
        return_msgs<bolean> = False
        prnt<bolean> = False
        dirs: bool               # include dirs
        dir_only: bool           # only dirs
        links: bool              # include links
        mtime: bool              # with mtime
        recurse: bool             # recursive BUT (currently ignores pattern (assumes all)
    returns:
        a sorted list of those names
        or
        return_msgs and sorted names
    use: 
        - list_files("/tmp")
        - list_files(["./my_dir, /tmp], 'recurs', dirs=False) 
    """
    # """--== Debugging ==--"""
    # dbug(f"{funcname()} called_from: {called_from()}")
    # dbug(dirs)
    # dbug(file_pat)
    # dbug(args)
    # dbug(kwargs)
    # dbug(file_pat)
    # """--== Config ==--"""
    ptrns = kvarg_val(['file_pat', 'patterns', 'pattern', 'ptrn', 'ptrns', 'pat'], kwargs, dflt=[file_pat])
    links = arg_val('links', args, kwargs, dflt=False)  # should links be followed
    dirs_b = arg_val(["dirs_b", "dirs"], args, kwargs, dflt=False)
    dirs_only = arg_val(["dirsonly", "dirs_only", "dironly", "dir_only"], args, kwargs, dflt=False)
    sortby = kvarg_val(['sortby'], kwargs, dflt='name')
    mtime = arg_val(["with_mtime", "with_mdate", "mtime", "long", "ll"], args, kwargs, dflt=False)
    recurs_b = arg_val(["recurs", "r", "recurse", "recursive"], args, kwargs, dflt=False)
    # dbug(with_mtime)
    # """--== Inits ==--"""
    msgs = []
    files_l = []
    # """--== Converts ==--"""
    if isinstance(ptrns, str):
        ptrns = [ptrns]
    if isinstance(dirs, str):
        dirs = dirs.split()
    # """--== Process ==--"""
    if recurs_b:
        for dir in dirs:
            for root, dirs, files, in os.walk(dir):
                for file in files:
                    # for pat in ptrns:
                        # dbug(pat)
                    # dbug(os.path.join(root, file))
                    files_l.append(os.path.join(root, file))
                for dir in dirs:
                    # dbug(dirs_b)
                    if dirs_b:
                        # dbug(os.path.join(root, dir))
                        files_l.append(os.path.join(root, dir))
        files_l = [elem.replace("//","/") for elem in files_l]  # cleanup
        # """--== returning ==--""" #
        # dbug(files_l)
        return files_l
    for ptrn in ptrns:
        for dir in dirs:
            dir = os.path.expanduser(dir)
            pathname = f"{dir}/{ptrn}"
            # dbug(f"{pathname=} {file_pat=}")
            for n, file in enumerate(glob.glob(pathname)):
                if dirs_b:
                    if os.path.isdir(file):
                        files_l.append(file)
                        # d_l = os.listdir(file)
                        # dbug(d_l)
                        continue
                # dbug(f"Checking file: {file} in pathname: {pathname}")
                if os.path.islink(file):
                    # dbug(f"File: {file} found in dir: {dir} is a link.... skipping...")
                    if links:
                        files_l.append(file)
                    else:
                        continue
                # abs_file = f"{dir}/{file}"
                # dbug(f"Found file {file} appending to files_l: {files_l}")
                if not dirs_only:
                    if os.path.isfile(file):
                        files_l.append(file)
                        msgs.append("{:>2})  {}".format(n, file))
            if sortby.lower() == 'name':
                files_l = sorted(files_l)
            if sortby.lower() in ("date", "mtime", "mdate"):
                files_with_mtime = [(f, os.path.getmtime(f)) for f in files_l]
                files_mtime_l = sorted(files_with_mtime, key=lambda x: x[1])
                if mtime:
                    len_mdate = 19
                    max_len = maxof(files_mtime_l) - (len_mdate + 4)
                    new_files_l = []
                    for file in files_mtime_l:
                        mdate = datetime.fromtimestamp(file[1])
                        mdate = str(mdate)[:len_mdate]
                        new_files_l.append(f"{file[0]:{max_len}} {mdate}")
                    files_l = new_files_l
                    # dbug(files_l, 'ask')
            if len(files_l) > 0:
                msg = "Found these files:"
                for f in files_l:
                    msg += f"\n   {f}"
    # if return_msgs:
    #     return msgs, names
    # else:
    return files_l
    # ### EOB def list_files(dirs, file_pat="*", *args, **kwargs): ### #


# #########################
def select_file(path="./", pattern="*", *args, **kwargs):
    # ######################
    """
    purpose: select a file (or dir) from using pattern(s)
        prints a file list and then asks for a choice
    required: 
        - path: str|list  (defaults to "./")
    options:
        - pattern|pat: str|list
        - prompt: str
        - mtime: bool                 # include mtime in listing
        - centered|center: bool|str
        - dirs: bool                  # include dirs
        - dirs_only: bool             # only directories
        - shadow: bool
        - title: str
        - footer: str
        - sortby: str                 # default='name - or choose "mtime" | "mdate" |"date" then this will sortby mtime
        - width=0
        - timeout: int                # question times out after declared seconds with "" as answer
    use: f = select_file("/home/user","*.txt")
    returns filename selected
    Note: this uses list_files() and gselect()
    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # prnt=True, color="", boxed=False, box_color="", title="", footer="", shadow=False, center=False, displaywidth=0, rtrn="value", **kwargs):
    # """--== Config ==--"""
    ptrns = kvarg_val(['pattern', 'patterns', 'pat', 'ptrn', 'ptrns'], kwargs, dflt=pattern)
    # prnt = arg_val(["prnt", "print"], args, kwargs, dflt=True)
    color = kvarg_val(["color", 'clr'], kwargs, dflt="")
    # boxed = kvarg_val(["boxed", "box"], kwargs, dflt=False)
    box_color = arg_val(['box_color', 'box_clr', 'bx_clr'], args, kwargs, dflt="")
    # dbug(f"{box_color=}")
    title = kvarg_val("title", kwargs, dflt="")
    footer = kvarg_val("footer", kwargs, dflt="")
    colnames = kvarg_val("colnames", kwargs, dflt=["Select", "File"])
    # dbug(colnames)
    shadow = arg_val(["shadow", "shadowed"], args, kwargs, dflt=False)
    centered = arg_val(["center", 'centered'], args, kwargs, dflt=False)
    width = kvarg_val(["width", 'display_width', 'displaywidth', 'length'], kwargs, dflt=0)
    prompt = kvarg_val('prompt', kwargs, dflt="Please select file: ")
    mtime = arg_val(['ll', 'long', 'long_list', 'mtime', 'with_mtime'], args, kwargs, dftt=False)
    # choose = arg_val(['choose', 'select', 'pick'], args, kwargs, dflt=True)
    dirs_b = arg_val(['dirs_b', 'dirs', 'dir'], args, kwargs, dflt=False)
    dirs_only = arg_val(['dirs_only', 'dirsonly', 'dironly', 'dir_only', 'only_dirs'], args, kwargs, dflt=False)
    sortby = kvarg_val(['sortby'], kwargs, dflt='name')
    cols = kvarg_val(['cols'], kwargs, dflt=0)
    basefiles_b = arg_val(['base','basefiles', 'basenames', 'show_base', 'show_basefiles'], args, kwargs, dflt=True)
    rtrn_type = kvarg_val(['rtrn', 'rtrn_type', 'rtrntype', 'return_type'], kwargs, default="")
    dflt = kvarg_val(["dflt", "default"], kwargs, dflt="")
    timeout = arg_val(['timeout', 'time'], args, kwargs, default=0)
    # dbug(kwargs)
    # dbug(f"{ptrns=} {path=}")
    # """--== Process ==--"""
    if isnumber(dflt):
        dflt = int(dflt)
    # dbug(f"{path=} {ptrns=} {dirs_b=} {dirs_only=} {sortby=} {mtime=} {dflt=}")
    file_l = list_files(path, ptrns=ptrns, dirs_b=dirs_b, dirs_only=dirs_only, sortby=sortby, with_mtime=mtime)
    # dbug(file_l)
    # dbug(file_l)
    # if not choose:
    #     # just use list_files() instead
    #     return file_l
    files_lol = []
    base_files_lol = []
    select_files_d = {}
    for num, file in enumerate(file_l, start=1):
        files_lol.append([num, file])
        base_files_lol.append([num, os.path.basename(file)])
        select_files_d[os.path.basename(file)] = file
    # dbug(cols)
    select_files = files_lol
    if basefiles_b:
        # dbug(basefiles_b)
        select_files = base_files_lol
    # dbug(f"{select_files=} {prompt=}")
    if isempty(select_files):
        # dbug(f"No {select_files=} found for {path=} [ptrns=) {called_from('v')} ...returning")
        return
    ans = gselect(select_files, 'prnt', rtrn="v", cols=cols, colnames=colnames, color=color, box_color=box_color,
                  shadow=shadow, width=width, centered=centered, prompt=prompt, title=title, footer=footer, dflt=dflt, timeout=timeout)
    # dbug(ans, 'noask')
    if isinstance(ans, list):
        ans = ans[1]  # ans is a list with [indx, root filename] - we want the root filename
        # dbug(ans, 'ask')
    # if str(ans).lower() in ("q", "quit", ""):
    if str(ans).lower() in ("q", "quit"):
        # dbug(f"No file selected... returning {called_from()}", centered=centered)
        return
    if rtrn_type in ('base', 'baseonly', 'basename', 'short'):
        ans = os.path.basename(ans)
    else:
        # dbug(f"{ans=} {select_files_d=}")
        if ans in select_files_d:
            ans = select_files_d[ans]
    # dbug(f"Returning ans: {ans}",'ask')
    return ans
    # ### EOB def select_file(path="./", *args, pattern="*", **kwargs): # ###


# #################################
def select_files(*args, **kwargs):
    # #############################
    """
    purpose:
    requires:
    options:
    returns:
    notes:
        - WIP
    """
    # """--== local imports ==--""" #
    import pathlib
    import re
    # """--== test ==--""" #
    if args and args[0] in ("tst", "test"):
        kwargs = {'dirs':["./"], 'includes': [".*\\.png$|.*\\.jp.*g$", ".*\\.py$"], 'exclude':""}  #[".*template.*"]} #,".*index\\..*","__.*__"]}
    # """--== Config ==--""" #
    prnt = arg_val(["prnt", 'print', 'show'], args, kwargs, dflt=False)
    dirs = arg_val(['dirs', "dir"], args, kwargs, dflt=[])
    includes = arg_val(["pat","pattern","include","includes"], args, kwargs, dflt=".*")
    excludes = arg_val(['exclude','excludes'], args, kwargs, dflt="")
    # """--== Converts ==--""" #
    if isinstance(dirs, str):
        dirs = [dirs]
    if isinstance(includes, list):
        includes = "|".join(includes)
    if isinstance(excludes, list):
        excludes = "|".join(excludes)
    # """--== Process ==--""" #
    include_rgx = re.compile(rf'{includes}', re.IGNORECASE)
    exclude_rgx = re.compile(rf'{excludes}', re.IGNORECASE)
    selected_files = []
    for d in dirs:
        path = pathlib.Path(d)
        if not path.exists():
            continue
        for file in path.iterdir():
            if file.is_file():
                name = file.name
                # dbug(f"Chkg {name=}")
                is_included = include_rgx.search(name)
                is_excluded = excludes and exclude_rgx.search(name)
                if is_included and not is_excluded:
                    selected_files.append(str(file))
                elif is_included and is_excluded:
                    if prnt:
                        dbug(f"Excluded: {name=}")
            else:
                continue # must be a directory
    if not selected_files:
        dbug(f"Nothing found in {dirs=} using {includes=} and {excludes=}")
        return
    # """--== Returning ==--""" #
    if prnt:
        # printit(selected_files, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
        gcolumnize(selected_files, cols=4, sep=True, prnt=True, boxed=True, box_clr="red")
        dbug(f"Files in {dirs=} using {includes=} and {excludes=}")
    return selected_files
    # ### EOB def select_files(*args, **kwargs): ### #

# ##################################
def reduce_line(line, max_len, pad):
    # ##############################
    """
    purpose: reduce a line to no more than max_len with and no broken words
        then return the reduced_line, and remaining_line
    returns: tuple - this_line(reduced) and the remaining part of the line
    Note - this is used in wrapit()
    """
    this_line = ""
    remaining_line = ""
    msg_len = len(line)
    msg = line
    if msg_len + pad > max_len:
        # dbug("msg: " + msg)
        # dbug(f"msg_len [{msg_len}] > max_len [{max_len}] and pad: {pad}")
        words = msg.split(" ")
        word_cnt = len(words)
        cnt = 0
        for word in words:
            # dbug("word: " + word)
            # dbug("len(this_line): " + str(len(this_line)))
            if len(this_line) + pad + len(word) + 4 > max_len:
                remaining_line = " ".join(words[cnt:])
                break
            else:
                cnt += 1
                # dbug("adding word: " + word)
                if len(this_line) == 0:
                    this_line += word
                else:
                    this_line += " " + word
                if cnt > word_cnt:
                    break
        # dbug("this_line: " + this_line)
        # dbug("remaining_line: " + remaining_line)
    return this_line, remaining_line
    # ### EOB def reduce_line(line, max_len, pad): ### #


# ########################
def do_edit(file, *args, **kwargs):
    # ####################
    """
    purpose: launches vim editor with file
        a quick-n-dirty utility to edit a file
    options:
        - lnum: line number
        - sudo: bool=False
    Initiate edit on a file - with lineno if provided
    notes: alias includes file_edit
    """
    # """--== Config ==--""" #
    lnum = arg_val(["lnum", "line", "lnumber", "lno"], args, kwargs, dflt=0)
    sudo_b = arg_val(["sudo"], args, kwargs, dflt=False)
    # """--== SEP_LINE ==--""" #
    if lnum:
        # cmd = f"vim {file} +{str(lnum)}"
        cmd = "vim " + file + " " + str(lnum)
        if sudo_b:
            cmd = f"sudo {cmd}"
        # dbug(cmd, 'ask')
    else:
        if file is None:
            dbug(f"No file name: {file}")
            return
        cmd = "vim " + str(file)
        if sudo_b:
            cmd = f"sudo {cmd}"
        # dbug(cmd, 'ask')
    try:
        r = subprocess.call(cmd, shell=True)
    except Exception:
        # this is unlikely and really not a solution because fails on syntax occur on compilation
        cmd = f"vimit {file}"
        r = subprocess.call(cmd, shell=True)
    # print(f"{cmd}")
    return r
    # ### EOB def do_edit(file, lnum=0): ### #``

# alias
file_edit=do_edit


# ##################################
def cinput(prompt, *args, **kwargs):
    # ##############################
    """
    aka: centered input
    purpose: gets input from user using provided promt - centers the prompt on the screen
    options:
        - shift: int              # allows you to shift the position of the prompt (from the center) eg shift=-5
        - quit|exit|close: bool   # will quit with do_close() if availaable or just sys.exit()
        - dflt: str               # you can provide a default if user hits only <ENTER> 
        - show_dflt: bool=True    # if you set this to false the dflt will not show
        - timeout: int            # question will timeout after declared seconds with dlft as the answer
        - centered: bool          # default is true but can be set to False which makes it act like input but with the options provided here
    returns: user response
    """
    # """--== Debugging ==--"""
    # dbug(f"{called_from('v')} {prompt=}")
    # """--== Config ==--"""
    prnt = arg_val(["prnt", 'print', 'show'], args, kwargs, dflt=False)
    quit_b = arg_val(['quit', 'exit', 'close'], args, kwargs, dflt=False)
    shift = kvarg_val('shift', kwargs, dflt=0)
    dflt_s = kvarg_val(["default", "dflt"], kwargs, dflt="")
    show_dflt = kvarg_val(["show_default", "show_dflt"], kwargs, dflt=True)
    timeout = arg_val(["timeout", "time"], args, kwargs, dflt=0)
    centered_b = arg_val(["centered", 'center', 'cntr'], args, kwargs, dflt=True, opposites=['nocntr','no_center','nocenter','no_cntr'])
    # """--== Process ==--"""
    if prompt == "":
        prompt = "Hit Enter to continue..." + dflt_s
    # dbug(prompt)
    prompt = printit(prompt, prnt=False, centered=centered_b, rtrn='str', shift=shift)
    if timeout > 0:
        import select
        # Note: select returns 3 objects (is_readable,is_writable, return_errors) as it is designed for lots of different kinds of input (like testing sockets)
        print(prompt, end='', flush=True)
        # input = sys.stdin.readline().strip()
        r,w,e = select.select([sys.stdin], [], [], timeout)
        if (r):  # this is needed - trust me
            # Read the input and print result
            ans = sys.stdin.readline().strip()
        # Run else when time is over
        else:
            # printit(f"Sorry, time: {timeout} is up...", centered=centered_b)
            print(" ")
            ans = dflt_s
        # return ans
    else:
        import readline
        if show_dflt:
            readline.set_startup_hook(lambda: readline.insert_text(dflt_s))
        try:
            ans = input(prompt) or dflt_s
        finally:
            readline.set_startup_hook(None) # reset it back to normal
    # dbug(f"{ans=} {dflt_s=} {called_from('v')}")
    if str(ans).strip() == "":
        ans = dflt_s
    if quit_b and ans in ("q", "Q", ""):
        # dbug(quit_b)
        try:
            do_close("[red]Exiting[/] as requested...", 'centered')
        except Exception:
            sys.exit()
    if prnt:
        dbug(f"returning ans:{ans}")
    return ans
    # ### EOB def cinput(prompt, *args, **kwargs): ### #


# ##############################################
def pbar(amnt, full_range=100, *args, bar_width=40, show_prcnt=True, **kwargs):
    # ##########################################
    """
    purpose: displays a percentge bar
    args: 
        - amnt: float|int|list(of 3)|tuple (of 3) # (prcnt or actual value - if it is a list|tuple of 3 numbers they will be sorted and
                                                     low is assumed to be list[0]|tuple[0]
                                                     actual is assumed to be list[1]|tuple[1]
                                                     high is assumed to be list[2]|tuple[2]
                                                     full_range is assumed to be high - low
    options: 
        - full_range: int=100 | list      # default is 100 but if you submit this the prcnt will be based on it
          - note: if full_range is provided as a list or a tuple with a low and a high then the full range will be the difference 
                  and you can add the low and the high to the suffix with show_highlow: bool
        - boxed: bool
            - title: str
            - footer: str
            - box_clr: str
        - centered: bool
        - bar_width=40: int   # declares width of bar
        - color: str          # text color
        - done_color:         # color of done portion
        - undone_color:       # color of undone portion
        - done_chr: str       # done character
        - undone_chr: str     # undone character
        - prompt: str         # prompt (before the bar)
        - suffix: str         # suffix (after the bar)
        - show_low-high: bool # add to suffix "low: {l}" but this requires full range to be a list or tuple - see above
        - brackets=["[", "]"]: list
        - show_prcnt=True: bool  # include the percentage at the end
        - prnt=False: bool  # False to allow use in dashboards  # you can tell this to not print so you can include in in a box etc
    returns: percent bar line as a str
    notes:
        - aliased to prcnt_bar(...) (may get deprecated)
    """
    # """--== Debugging ==--"""
    # dbug(f"{called_from('v')} {amnt=} {full_range=} {args=} {kwargs=}")
    # """--== pre_INIT ==--""" #
    if isinstance(amnt, (list, tuple)):
        if len(amnt) == 3:
            args += (full_range,)
    # """--== Config ==--"""
    full_range = kvarg_val(["full_range", "total", "tot"], kwargs, dflt=full_range)
    bar_width = kvarg_val(["bar_width", 'length', 'width', 'len'], kwargs, dflt=bar_width)
    color = kvarg_val(['color'], kwargs, dflt="")
    done_color = kvarg_val(['done_color', 'done_clr'], kwargs, dflt=color)
    # done_chr = u'\u2588'   # █ <-- full, solid shadow
    # done_chr = "\u2593"    # ▓ <-- full, light shadow
    # done_chr = "\u2592"    # ▒ <-- full, medium shadow
    # done_chr = "\u2591"    # ░ <-- full, dark shadow
    # done_chr = "\u2584"    # ▄ <-- Lower five eighths block
    # done_chr = "\u2585"    # ▆ <-- Lower five eighths block
    # done_chr = "\u2582"    # ▂ <-- lower 1/4 block
    done_chr = "\u2586"      # ▆ <-- 3/4, solid block
    # done_chr = "\u2586"    # ▆ <-- 3/4 high solid block
    done_chr = kvarg_val(['done_chr', 'chr'], kwargs, dflt=done_chr)
    undone_color = kvarg_val(['undone_color', 'undone_clr', 'fill_color', 'fill_clr'], kwargs, dflt="")
    undone_chr = "\u2015"    # ― <-- horizontal line
    undone_chr = kvarg_val(['fill', 'fc', 'undone_chr'], kwargs, dflt=undone_chr)
    # done_color = sub_color(done_color + " on rgb(255,255,255)")
    # done_chr = done_color + done_chr
    prompt = kvarg_val(["prefix", 'prompt'], kwargs, dflt="")
    suffix = kvarg_val(["suffix", 'ending', 'end_with'], kwargs, dflt="")
    brackets = kvarg_val(["brackets"], kwargs, dflt=["[", "]"])
    show_prcnt = arg_val(["show_prcnt", 'prnct', 'percent'], args, kwargs, dflt=show_prcnt)
    prnt = arg_val(["prnt", 'print', 'show'], args, kwargs, dflt=False)
    centered_b = arg_val(["centered", 'center'], args, kwargs, dflt=False)
    boxed_b = arg_val(['boxed', 'box'], args, kwargs, dflt=False)
    title = kvarg_val('title', kwargs, dflt="")
    footer = kvarg_val('footer', kwargs, dflt="")
    box_clr = kvarg_val(['box_clr', 'box_color'], kwargs, dflt="")
    show_highlow = arg_val(['show_hl', 'show_highlow', 'show_lh', 'show_lowhigh', 'show_range', 'show_rng', 'hl', 'lh', 'range', 'rng', 'shwlh'], args, kwargs, dflt=False)
    shade_clrs = arg_val(["shades", "shade_clrs", 'shade_clr'], args, kwargs, dflt="")  # TODO WIP
    # """--== Init ==--"""
    actual = None
    if isinstance(amnt, (list, tuple)):
        if len(amnt) == 3:
            try:
                amnt = [float(num) for num in amnt]
                tmp_vals = sorted(amnt)
            except Exception as Error:
                dbug(f"{Error=} {amnt=} {called_from('v')}")
                return
            # dbug(tmp_vals)
            low = round(float(tmp_vals[0]), 2)
            actual = round(float(tmp_vals[1]), 2)
            high = round(float(tmp_vals[2]), 2)
            amnt = tmp_vals[1]
            full_range = round(high - low, 2)
            # dbug(f"{args=} {kwargs=}")
            # dbug(f"{low=} {actual=} {high=} {full_range=} {bar_width=} {amnt=}")
        else:
            dbug(f"If amnt is a list or tuple it must include 3 numbers {amnt=} ... returning...")
            return
    else:
        if isnumber(full_range):
            low = 0
            high = full_range
    # dbug(f"{color=} {done_color=} {undone_color=} {shade_clrs=} {amnt=}")
    if "2" in shade_clrs:  # this should get deprecated
        shade_clrs = shade_clrs.split('2')
    RESET = gclr('reset')  # yes, this is needed
    if not boxed_b and not isempty(title) and isempty(prompt):
        prompt = title
    if isinstance(full_range, (list, tuple)):
        low = full_range[0]
        high = full_range[1]
        full_range = float(high) - float(low)
        actual = float(amnt)
        amnt = round(float(amnt) - float(low), 2)
    else:
        amnt = parse_codes(amnt, 'str')
        actual = float(amnt)
        actual = round(actual, 2)
    COLOR = gclr(color)
    DONE_COLOR = gclr(done_color)
    UNDONE_COLOR = gclr(undone_color)
    if color == "" and done_color == "" and undone_color == "" and shade_clrs == "":
        RESET = ""
    # """--== Converts ==--"""
    if isinstance(amnt, str):
        amnt = amnt.replace("*", "")
    # """--== Process ==--"""
    # amnt = float(escaped(amnt))
    # dbug("Wait here, I'll be right back...{amnt=}", 'ask')
    if isnumber(amnt):  # by this line it should be a number
        amnt = float(parse_codes(amnt, 'escaped'))
        amnt = round(amnt, 2)
        if full_range == 100:
            low = 0
            high = 100
    else:
        dbug(f"{amnt=} does not appear to be a number {called_from('v')}")
        return
    full_range = round(float(full_range), 2)
    # dbug(f"{low=} {actual=} {high=} {full_range=} {bar_width=}")
    # dbug(actual)
    diff = actual - low
    try:
        # prcnt = float(amnt / full_range)  # <-- rubber hits the road here
        prcnt = diff / full_range  # <-- rubber hits the road here
        prcnt = round(prcnt, 2)
    except Exception as Error:
        dbug(f"{Error=} prcnt calc failed...{diff=}  ({amnt=} - {low=}) / {full_range=}... returning None", 'ask')
        return None
    # dbug(f"{amnt=} {full_range=} {low=} {actual=} {high=} {prcnt=} {bar_width=}", 'ask')
    # done_len = int(prcnt / 100 * bar_width)
    done_len = int(prcnt * bar_width)
    done_len = math.ceil(prcnt * bar_width)
    undone_len = int(bar_width - done_len)
    # dbug(f"{done_len=} {undone_len=}")
    done_fill = DONE_COLOR + done_chr * done_len
    undone_fill = UNDONE_COLOR + (undone_chr * undone_len)
    # dbug(f"{DONE_COLOR=} {done_fill=} {UNDONE_COLOR=}")
    # dbug(undone_fill)
    bar = done_fill + undone_fill   # <--bar
    # dbug(f"{bar=}")
    # """--== SEP_LINE ==--""" #
    if isinstance(shade_clrs, list) and (len(shade_clrs) == 2 or len(shade_clrs) == 3):
        DONE_COLOR = ""
        UNDONE_COLOR = ""
        this_shades = shades(shade_clrs, len(bar), prfx=True, rtrn='codes')
        bar_l = [clr_code + bar[n] for n,clr_code in enumerate(this_shades)]
        bar = "".join(bar_l)
        # dbug(bar)
    # """--== SEP_LINE ==--""" #
    # dbug(repr(COLOR))
    # dbug(repr(RESET))
    bar = COLOR + brackets[0] + RESET + bar + RESET + COLOR + brackets[1]
    # dbug(bar)
    rtrn = bar
    if show_highlow:
        suffix += f" low: {low} {actual=} high: {high}"
    if show_prcnt:
        prcnt = " " + str(math.ceil(prcnt * 100)) + "%"
        rtrn = COLOR + prompt + RESET + bar + RESET + UNDONE_COLOR + COLOR + f"{prcnt:>4}" + suffix
    # dbug(f"prnt: {prnt} centered_b: {centered_b} boxed_b: {boxed_b}")
    if boxed_b:
        rtrn = printit(RESET + rtrn + RESET, prnt=prnt, centered=centered_b, boxed=boxed_b, box_clr=box_clr, txt_centered=99, title=title, footer=footer)
    else:
        rtrn = printit(RESET + rtrn + RESET, prnt=prnt, centered=centered_b, rtrn='str', txt_centered=99, title=title, footer=footer)
    # dbug(rtrn, 'ask')
    return rtrn
    # ### EOB def pbar(amnt, full_range=100, *args, bar_width=40, show_prcnt=True, **kwargs): ### #


# alias
do_prcnt_bar = pbar  # for back compatibility
# prcnt_bar = pbar
# percent_bar = pbar


# #############################################
def progress(progress, *args, **kwargs):
    # #########################################
    """
    purpose: displays a progress bar typically used within a loop
    options:
       - width
       - prompt
       - color
       - done_color
       - undone_color
       - prnt: bool         # default=True
       - COLOR
       - DONE_COLOR
       - UNDONE_COLOR
       - RESET
       - done_chr
       - undone_chr
       - status
       - centered: bool
       - shift:
    returns: None
    usage:
        # prcnt = 0.20
        # progress(prcnt, width=60)
        Percent: [############------------------------------------------------] 20%
        # or
        for i in range(100):
            time.sleep(0.1)
            progress(i/100.0, width=60)
        Percent: [############################################################] 99%
        # or
        prices = []
        for n, sym in enumerate(syms, start=1):
            price = get_price(sym)
            prices.append(price)
            progress(n/len(syms), width=60, prompt=f"Working on prices {n:2}/{len(syms)}... ", status=f"Finished {sym:5}")
        print()
        print(prices)
        # or
        syms = ["AMD", "NVDA", "MSFT", "AMZN", "GOOGL", "CSCO", "NWL", "MET", "LLY", "QCOM"]
        prices = []
        chk_l = syms
        chkd_l = []
        for n, sym in enumerate(syms, start=1):
            price = round(random.uniform(0.01, 800),2)
            time.sleep(.2)
            prices.append(price)
            line = progress(n/len(syms), 'centered', 'noprnt', width=60, prompt=f"Working on {n:2}/{len(syms)}: ", status=f"Finshed {sym:5} ")
            chkd_l.append(sym)
            lines = chklst(chk_l, chkd_l, 'boxed', 'centered', cols=5, title="Syms", footer=dbug('here'))
            lines.append(line)
            cls()
            printit(lines)
        printit(f"prices: {prices}", 'centered', 'boxed', title="These prices are random", footer=dbug('here'))
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # """--== Config ==--"""
    width = kvarg_val(['bar_width', 'length', 'width'], kwargs, dflt=40)  # Modify this to change the length of the progress bar  # noqa
    prompt = kvarg_val(['prompt', 'prefix'], kwargs, dflt="")
    color = kvarg_val(['color', 'text_color', 'txt_color', 'txt_clr'], kwargs, dflt="")
    done_color = kvarg_val(['done_color'], kwargs, dflt="")
    undone_color = kvarg_val(['fill_color', 'fcolor', 'fclr', 'undone_color'], kwargs, dflt="")
    prnt = arg_val(['print', 'prnt'], args, kwargs, opposites=["noprnt", "no_prnt", "noprint", "no_print"], dflt=True)
    # COLOR = sub_color(color)
    # DONE_COLOR = sub_color(done_color)
    # UNDONE_COLOR = sub_color(undone_color)
    COLOR = gclr(color)
    DONE_COLOR = gclr(done_color)
    UNDONE_COLOR = gclr(undone_color)
    # RESET = sub_color('reset')
    # FILL_COLOR = sub_color(fill_color)
    # done_chr = u'\u2588'   # █ <-- full, solid shadow
    # done_chr = "\u2593"    # ▓ <-- full, light shadow
    # done_chr = "\u2592"      # ▒ <-- full, medium shadow
    # done_chr = "\u2591"    # ░ <-- full, dark shadow
    # done_chr = "\u2584"    # ▄ <-- Lower five eighths block
    # done_chr = "\u2585"    # ▆ <-- Lower five eighths block
    done_chr = "\u2586"      # ▆ <-- 3/4, solid block
    # done_chr = "\u2586"    # ▆ <-- 3/4 high solid block
    # done_chr = "\u2582"    # ▂ <-- lower 1/4 block
    done_chr = kvarg_val(['done_chr', 'chr'], kwargs, dflt=done_chr)
    undone_color = kvarg_val(['undone_color', 'undone_clr', 'fill_color', 'fill_clr'], kwargs, dflt="")
    undone_chr = "\u2015"    # ― <-- horizontal line
    undone_chr = kvarg_val(['fill', 'fc', 'undone_chr'], kwargs, dflt=undone_chr)
    # done_color = sub_color(done_color + " on rgb(255,255,255)")
    # done_chr = done_color + done_chr
    undone_chr = kvarg_val(['fill_chr', 'fc', 'undone_chr'], kwargs, dflt=" ")
    status = kvarg_val(['status', 'done_msg', 'done_txt', 'done_text', 'post_prompt', 'suffix'], kwargs, dflt="")
    center_b = arg_val(["centered", "center"], args, kwargs, dflt=False)
    shift = kvarg_val("shift", kwargs, dflt=0)
    # elapsed_b = arg_val(["elapsed", "elpsdd"], args, kwargs, dflt=False)  # TODO
    # """--== SEP_LINE ==--"""
    if isinstance(progress, int):
        progress = float(progress)
    # """--== SEP_LINE ==--"""
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
        if prnt:
            sys.stdout.write('\x1b[?25h')  # retore cursor
            sys.stdout.flush()
    if progress >= 1:
        progress = 1
        if prnt:
            status = f"{status}\r\n"
            status += "\x1b[?25h"          # Restore cursor
            sys.stdout.write('\x1b[?25h')  # retore cursor
            sys.stdout.flush()
        # dbug(status)
    done_len = int(round(width * progress))
    done_fill = done_chr * done_len + RESET
    undone_fill = undone_chr * (width - done_len) + RESET
    shift = abs(shift)
    prcnt = progress * 100
    # """--== SEP_LINE ==--"""
    if center_b:
        scr_cols = int(get_columns())
        prompt_len = parse_codes(prompt, 'nclen')
        status_len = parse_codes(status, 'nclen')
        # full_txt_len = width + nclen(prompt) + nclen(status)
        full_txt_len = width + prompt_len + status_len
        lfill = " " * ((scr_cols - full_txt_len) // 2)
        prompt = lfill + prompt
        # ruleit()
    txt = COLOR + f"\r{prompt}[{RESET}" + DONE_COLOR + f"{done_fill}" + RESET + UNDONE_COLOR + f"{undone_fill}" + COLOR + f"] {prcnt:.2f}%"
    txt = txt + f" {status}" + RESET
    # """--== SEP_LINE ==--"""
    if prnt:
        sys.stdout.write('\x1b[?25l')  # Hide cursor
        sys.stdout.write(txt)
        sys.stdout.flush()
    # dbug(txt)
    return txt
    # ### EOB def progress(progress, *args, **kwargs): ### #


# ################################
def from_to(filename, *args, include="none", **kwargs):
    # ############################
    """
    NOTE: do not use from=`xxx` ... instead use:begin=`xxx`, end=`yyy`
    purpose: returns lines from a *file* from BEGIN pattern to END pattern" (between BEGIN and END)
    required:
        - filename: str|list  # filename to parse or content (ie lines of text)
                              # Note: if filename is a string with no "\n" imbedded then extract the substring between bing and end pattern
        - begin: str          # pattern in line to begin with
        - end: str            # pattern in line to end with
    options:
    -  include: can be equal to "none", top|begin|start, bottom|end, or 'both'
    --    include='top' will include the begin pattern line, (also: 'top' '| 'before' | 'begin')
    --    include='bottom' will include the end pattern line  )also: 'after' | 'end')
    --    include='both' will include top and end pattern matching lines
    returns: lines between (or including) begin pattern and end pattern from filename (or a list of lines)
    note: begin is used here because 'from' is a python keyword
    """
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "show"], args, kwargs, dflt=False)  # primarily for debugging
    begin = kvarg_val(['begin', 'after', 'from', 'beg'], kwargs, dflt="")  # you can not use 'from' a variable name because it is a keyword
    # dbug(begin)
    end = kvarg_val(['end', 'to', 'before', 'upto'], kwargs, dflt="")
    # dbug(end)
    # """--== Debuging ==--"""
    # dbug(args)
    # dbug(kwargs)
    # dbug(filename)
    if prnt:
        dbug(f"{begin=} {end=}")
    # """--== Init ==--"""
    include = include.lower()  # can be 'top', 'bottom', or both to include the {begin} and or {after}
    lines = []
    return_lines = []
    start_flag = False
    # dbug(f"begin: [{begin}] end: [{end}]")
    # askYN()
    # """--== Convert ==--"""
    orig_dtype = data_type(filename)
    # dbug(f"{orig_dtype=}")
    # if orig_dtype in  ('str') and "\n" not in filename:  # making sure it is not a real filename
    if 'str' in orig_dtype and "\n" not in filename:  # making sure it is not a real filename
        # dbug(f"Treat {filename=} {data_type(filename)=} single string and extract what is between begin and end patterns")
        combined_regex = fr"{begin}(.*?){end}"
        # dbug(f"{begin=} {end=}")
        match = re.search(combined_regex, filename)
        if match:
            extracted_substring = match.group(1)
            if prnt:
                dbug(f"Extracted substring: {extracted_substring} {begin=} {end=} {combined_regex=}")
            return extracted_substring
        else:
            dbug("No match found.")
            return 
    if "\n" in filename:
        filename = filename.split("\n")
    if isinstance(filename, list):
        lines = filename
    else:
        # lines = cat_file(filename, 'lst')
        with open(os.path.expanduser(filename)) as fp:
            lines = fp.readlines()
    # dbug(lines)
    # """--== Process ==--"""
    for line in lines:
        # dbug(line)
        line = line.rstrip("\n")
        beg_regex = re.search(begin, line)
        end_regex = re.search(end, line)
        # dbug(f"chkg line: {line} begin: {begin} end: {end}")
        # if end in line and start_flag:
        if end_regex and start_flag:
            if prnt:
                dbug(f"{line=} {end=} {end_regex=} {start_flag=}")
            # askYN()
            if include in ("bottom", "end", "both", "after", 'all'):
                return_lines.append(line)
                if prnt:
                    dbug(f"Added [{line}]")
            if prnt:
                dbug(return_lines, 'boxed')
            return_lines = [line.strip() for line in return_lines]
            return return_lines
        if start_flag:
            return_lines.append(line)
            # dbug(f"Added [{l}]")
        # if begin in line:
        if beg_regex:
            # dbug(f"Found {begin} in {line}")
            start_flag = True
            if include in ("top", "start", "begin", "both", "before", 'all'):
                return_lines.append(line)
                # dbug(f"Added [{line}]")
            else:
                continue
    if prnt:
        dbug(return_lines, 'boxed')
    return return_lines  # return lines if end not found
    # ### END def from_to(filename, begin, end): ### #


# # ############################################################
# def new_add_content(file, new_content="", *args, **kwargs):
#     # ########################################################
#     """
#     NEW add_content WIP
#     purpose: will add content to a file at a specified point in the file (after=pattern or before=pattern) or position=n)
#     Required:
#         file: str
#         content: str | list | dict
#     Options:
#         after: str     = pattern
#         before: str    = pattern
#         replace: str   = pattern
#         position: int  = ##
#         if none of those,  content is appended to the end of the file
#         if content is a dictionary the values will be considered data content and the keys() will be the heade/colnamesand if the header is also included
#             The header will be added to the begining of the file (if it does not already exist)
#     notes: I wrote this because I am constantly building csv files with a header line
#         used_to_be: add_line()
#         (also consider add_or_replace() function)
#     """
#     # dbug(f"new_{funcname()} {called_from()} WIP - this function just (20240405) replaced told_add_content", 'centered')
#     # dbug(args)
#     # dbug(kwargs)
#     dbug(new_content)
#     dbug(f"This needs to be to be factored with similar funcs. Funcname: {funcname()} Called_from: {called_from()}... everything should come here and then rename to add_content")
#     # """--== Config ==--"""
#     prnt = arg_val(["prnt", "print", "verbose", "show"], args, kwargs, dflt=False)
#     my_add_content = kvarg_val(["new_content", "add", "insert", "new", "add_content"], kwargs, dflt=new_content)
#     # show = kvarg_val('show', kwargs, dflt=False)
#     # dbug(prnt)
#     boxed_b = arg_val(["box", 'boxed'], args, kwargs, dflt=False)
#     centered_b = arg_val(["center", 'centered', "cntr", "cntrd"], args, kwargs, dflt=False)
#     position = kvarg_val('position', kwargs, dflt=None)
#     after = kvarg_val("after", kwargs, dflt="")
#     before = kvarg_val("before", kwargs, dflt="")
#     replace = kvarg_val(["replace", "delete"], kwargs, dflt="")
#     backup = kvarg_val("backup", kwargs, dflt=False)
#     header = kvarg_val(['header', 'hdr', 'colnames'], kwargs, dflt=[])
#     # dbug(header)
#     # """--== Init ==--"""
#     file_content = []
#     dbug(my_add_content)
#     new_content = []
#     # dbug(position)
#     pattern = replace
#     # """--== psuedo ==--"""
#     psuedo = """file_contents|contents : might be:
#         - a list of strings (aka lines) return: a string with newlines 
#         - or it might be a lol (rows of columns) [the lol may come from a csv list and will result in a csv list] return: a string with quotes, commas, and newlines"""
#     printit(psuedo, 'boxed', 'centered', title="psuedo notes", footer=dbug('here'))
#     # """--== Functions ==--"""
#     def insert_line(contents, my_add_content, *args, position=None, **kwargs):
#         """
#         purpose: add my_add_content into contents at position
#         requires: 
#             - contents:
#             - my_add_content
#         optional:
#             - position: int default=None  # None is equivalent to 'end of contents'
#             - replace: str=regex_pattern
#         returns: new_contents: list
#         notes:
#         """
#         """
#         # note:
#         # before_pos
#         # after_pos
#         """
#         # debug #
#         dbug(contents)
#         dbug(my_add_content)
#         dbug(position)
#         ### configs ###
#         after = kvarg_val("after", kwargs, dflt="")
#         ### inits ###
#         len_orig_contents = len(contents)
#         new_contents = []
#         if contents is None:
#             contents = []
#         if position is None:
#             position = len(contents)
#         # if replace == "":
#             # pattern = replace
#         ### converts ###
#         dbug(contents)
#         if isinstance(contents, str):
#             contents = contents.split("\n")
#         dbug(contents)
#         if isinstance(my_add_content, str):
#             # this turns it into a list
#             my_add_content = my_add_content.split("\n")  # make it a list
#         dbug(my_add_content)
#         dbug(contents)
#         ### process ###
#         if isempty(contents) and position is None:
#             contents = my_add_content
#             return contents
#         dbug(repr(my_add_content))
#         # if isinstance(my_add_content, list) and len(my_add_content) == 1:
#             # dbug(len(my_add_content))
#             # my_add_content = "\n".join(my_add_content)
#         dbug(position)
#         if position is None:
#             position = len(contents)
#             dbug(f"just set position to {position}")
#         dbug(position)
#         # dbug(f"position: {position} my_add_content: {my_add_content}")
#         dbug(contents)
#         previous_line = ""
#         ### for loop ###
#         for line_num, line in enumerate(contents, start=0):
#             if re.search(before, line):
#                 position = line_num - 1
#             if re.search(after, line):
#                 position = line_num + 1
#             dbug(f"### for loop ### line_num: {line_num} line: {line} position: {position}")
#             line = line.rstrip("\n")  # makes sure they all will be the same - they all will get newlines after the insertion
#             new_contents.append(line)
#             # dbug(f"position: {position} line_num: {line_num} len_orig_contents): {len_orig_contents}" )
#             if position == line_num:  #  or re.search(pattern, line): # or position >= len_orig_contents:
#                 dbug(f"OK, now adding my_add_content: {my_add_content} position: {position} line_num: {line_num} len_orig_contents: {len_orig_contents}")
#                 for my_line in my_add_content:
#                     # expects my_add_content to be list even if it is a single line (which is most likely)
#                     dbug(f"adding my_line: {my_line}")
#                     new_contents.append(my_line)
#             if after != "" and after in previous_line: 
#                 new_contents.append(line)
#                 continue
#             previous_line = line
#         # contents.insert(position, my_add_content)
#         if isempty(contents):
#             # deal with empty contents (which will get ignored in loop above)
#             for my_line in my_add_content:
#                 # expects my_add_content to be list even if it is a single line (which is most likely)
#                 dbug(f"adding my_line: {my_line}")
#                 new_contents.append(my_line)
#         dbug(f"returning contents: {new_contents}")
#         return new_contents
#     # """--=== EOB def insert_line(contents, my_add_content, *args, position=None, **kwargs): ==--"""
#     # """--== Process ==--"""
#     dbug(my_add_content)
#     # """--== read file (if exists) ==--"""
#     if file_exists(file):
#         file_content = cat_file(file)
#         dbug(file_content, 'boxed')  # , 'lst')
#     # """--== if content is dictionary ==--"""
#     if isinstance(my_add_content, dict):
#         # turn the dict into a string of lines using the values, set colnames/header=keys
#         content_d = {str(key): str(value) for key, value in my_add_content.items()}
#         my_vals = [f'"{elem}"' for elem in content_d.values()]
#         # dbug(my_vals)
#         my_add_content = ",".join(my_vals)
#         header = ",".join(content_d.keys())
#         # dbug(my_add_content)
#         # dbug(header)
#     # """--== now make sure my_add_content is a list ==--"""
#     if isinstance(my_add_content, str):
#         # this turns it into a list, process everything as a list
#         my_add_content = my_add_content.split("\n")  # make it a list
#     dbug(my_add_content)
#     # dbug(file_content)
#     # """--== handle backup ==--"""
#     if backup:
#         if file_exists(file):
#             import shutil
#             bak_ext = "-" + datetime.now().strftime("%Y%m%d-%H%M%S")
#             trgt_file = file + bak_ext
#             # shutil.copy(file, trgt_file)
#             shutil.copyfile(file, trgt_file)
#             if prnt:
#                 dbug(f"Backed up file: {file} to {trgt_file}")
#         else:
#             if prnt:
#                 dbug(f"file: {file} does not exist yet ... backup skipped...")
#     # """--== arrange content  ==--"""
#     # """--== 1st assure header is first ==--"""
#     # dbug(header)
#     if not isempty(header):
#         if isinstance(header, list):
#             # make sure header is a str
#             header = ",".join(header)
#             # dbug(header)
#         first_line = ""
#         if len(file_content) > 0:
#             first_line = file_content[0]
#         if header not in first_line:
#             # header does not match first_line
#             dbug(f"Header not found ... so inserting header: {header} at position 0")
#             file_content.insert(0, header)
#             # dbug(file_content)
#         else:
#             dbug(f"Header: {header} already exists in the first_line: {first_line}")
#     # dbug(new_content)
#     # """--== now add content ==--"""
#     # now add content where it is suppose to go
#     # dbug(f"doing insert_line with my_add_content: {my_add_content}")
#     new_content = insert_line(file_content, my_add_content, position=position,
#                               pattern=pattern, before=before, after=after, replace=replace)  # <== rubber hits the road here
#     # dbug(new_content)
#     # dbug('ask')
#     # """--== write new file ==--"""
#     if isinstance(new_content, list):
#         # dbug("assuring new_content lines all have a newline then convert to str")
#         new_content = [line if line.endswith("\n") else line + "\n"  for line in new_content]
#         new_content = "".join(new_content)
#         # dbug(new_content, 'ask')
#     # dbug(new_content)
#     # if not file_exists(file):
#     f = open(file, "w")
#     # dbug(f"Writing new_content: {new_content}")
#     if isinstance(new_content, list):
#         new_content = [line if line.endswith("\n") else line + "\n"  for line in new_content]
#         new_content = "".join(new_content)
#     # dbug(new_content, 'ask')
#     f.write(new_content)
#     f.close()
#     # """--== SEP_LINE ==--"""
#     printit(cat_file(file), prnt=prnt, boxed=boxed_b, centered=centered_b, title=f"cat file: {file} contents {funcname()}()", footer=dbug('here'))
#     return new_content
#     # ### def new_add_content(file, content="", header="", **kwargs): ### #


# ###############
def sorted_add(content, line, after="", before="", **kwargs):
    # ###########
    """
    purpose: to insert a line between two patterns in a sorted way
        insert line into filename between after and before patterns
        the patterns need to be regex ie: r"pattern"
        assumes the block from after to before is sorted
    required:
        content str | list  # can be a filename or a str with line breaks or a list of lines
        line: str            # line to be inserted
    options:
        after: str           # if not blank and if a line contains this pattern it will be used for the start of the sort process (can be a regex)
        before: str          # if not blank tnd if a line contains this pattern it will be used for the end of the sort process (can be a regex)
    returns: new_lines
    usage:
        eg:
            line = 'Insert this line (alphabetically) after "^-alt" but before "^-[a-zA-Z0-9] within block'
            filename = "~/t.f"
            after = r"^-alt"
            before = r"^-[a-zA-Z0-9]"
            lines = sorted_add(filename, line, after, before)
            printit(lines)
    notes:
        - This sorting algorithm is pretty specific and may not be useful for others. I use to insert a new line for historical stock data.
        - This function may get deprecated. The function addit() may take its place
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(content)
    dbug(f"This needs to be to be factored with similar funcs. Funcname: {funcname()} Called_from: {called_from()} ... move to add_content...", 'ask')
    # """--== Config ==--"""
    before = kvarg_val(["before", "end", "stop"], kwargs, dflt=before)
    after = kvarg_val(["after", "begin", "start"], kwargs, dflt=after)
    # dbug(f"after: {after} before: {before}")
    # """--== Init ==--"""
    lines = []
    new_lines = []
    begin = after
    end = before
    beg_regex_b = False
    end_regex_b = False
    # TODO if after and before are empty just use the whole file
    # tst_lines = from_to(filename, begin=after, end=before)
    insert_line = line
    # dbug(insert_line)
    # srch_block = False
    inserted = False
    # """--== Validation ==--"""
    if not isinstance(content, (list, str)):
        dbug("First argument must be a filename (str) or a list of lines... returning...")
        return None
    if isinstance(content, str) and file_exists(content):
        lines = cat_file(content, lst=True)
    if isinstance(content, list):
        lines = content
    # dbug(lines)
    # """--== SEP_LINE ==--"""
    # last_line = "0"
    # end_flag = False
    for ln in lines:
        # dbug(f"now chkg ln: {ln} beg_regex_b: {beg_regex_b} end_regex_b: {end_regex_b} begin: {begin} end: {end}")
        # if this is the first line then definately both beg_regex_b end_regex_b will be false
        if beg_regex_b and not end_regex_b:
            # dbug(f"now chkg ln: {ln} for end_regex beg_regex_b: {beg_regex_b} end_regex_b: {end_regex_b} beg: {beg} end: {end}")
            end_regex_b = re.search(end, ln)  # sets to None or True
            if end_regex_b and not inserted:
                # dbug(f"found end: {end} in ln: {ln}")
                new_lines.append(insert_line)
                inserted = True
                # dbug(f"Inserted: {insert_line}")
            if not end_regex_b and not inserted:
                if len(ln) > 0:
                    # case insensitive
                    if insert_line.lower() < ln.lower():
                        # dbug(f"insert_line: \n{insert_line}\n <\nln: {ln}")
                        new_lines.append(insert_line)
                        inserted = True
                        # dbug(f"Inserted: {insert_line}")
        else:
            beg_regex_b = re.search(begin, ln)
        # dbug(f"beg_regex_b: {beg_regex_b} end_regex_b: {end_regex_b}")
        # last_line = ln
        new_lines.append(ln)
    # dbug(f"Done with loop through lines. last ln: {ln} for end_regex beg_regex_b: {beg_regex_b} end_regex_b: {end_regex_b}")
    # dbug(f"returning new_lines type(new_lines): {type(new_lines)}")
    # dbug(new_lines, 'boxed', 'lst', 'ask')
    return new_lines
    # ### EOB def sorted_add() ### #


# @Tracker
# ######################################################
def addit(contents="", new_contents="", *args, **kwargs):
    # ##################################################
    """
    purpose: will insert or replace new_contents where you want it
    requires:
        - contents: str, list   # can be a filename or a list of strings
        - new_contents: str
    options:
        - prnt: bool=False           # primarily for debugging
        - after: str=""              # pattern match where replace or insert will occur in lines after the match
        - before: str=""             # pattern match where replace or insert will occur in line before the match
        - replace: str=""            # replaces line that matches
        - either: str=""             # will replace if pattern matches or insert if no match is found
        - sort: bool=False or int    # insert wiill occur in sort(ASCENDING) order for lines between after(or beginning of file) and before(or end of file) If this is set to an
                                     #     integer then the sort will be the first sort integer characters
        - write: bool=True           # whether to write out contents to filename
        - bak: bool=False            # whether to create a backup file
        - arch: dict={}              # you can have addit call arch() with options (archops) eg: archops={'limit': 300, 'days': 30, arch_dir="MY_ARCHIVE"} 
    retruns: new content as a list of lines
    usage:
        eg:
            - addit("/my/path/to/file.name", "content to add or replace with", after="^whatever here", before="^whatever else here", replace="^this line should get replaced")
    notes:
        - this takes the place of add_or_replace() which is being deprecated
        - if replace is declared and a match does not currently exist the add_content will be added
        - drafted on 20240814 lots of tweaks since... I almost trust it now
    """
    # """--== debugging ==--""" #
    # dbug(f"{called_from('v')}")
    # dbug(f"{args=} {kwargs=}")
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print'], args, kwargs, dflt=False)
    # prnt = 1  #  debugging
    contents = kvarg_val(['content', 'contents'], kwargs, dflt=contents)
    filename = kvarg_val(['filename', 'fname', 'file'], kwargs, dflt="")
    new_contents = kvarg_val(['add_content', 'add_contents', 'new', 'new_content', 'new_contents', 'insert'], kwargs, dflt=new_contents)
    sort_b = arg_val(['sort', 'sorted'], args, kwargs, dflt=False)
    bak_b = arg_val(['bak', 'backup'], args, kwargs, dflt=False)
    arch_d = kvarg_val(['arch', 'archive', 'archops', 'arch_ops'], kwargs, dflt=None)  # dictionary of options
    write_b = arg_val(['write', 'write_file'], args, kwargs, dflt=True, opposites=['nowrite'])
    after = kvarg_val(['after', 'begin', 'start'], kwargs, dflt="")
    before = kvarg_val(['before', 'end'], kwargs, dflt="")
    replace = kvarg_val(['replace', 'pat', 'pattern', 'rplc'], kwargs, dflt="")
    either = kvarg_val(['either'], kwargs, dflt="")
    # """--== Debugging ==--"""
    # dbug(f"funcname(): {funcname()} called_from: {called_from()}", 'ask')
    # dbug(new_contents)
    # dbug(contents)
    # dbug(replace)
    # dbug(either)
    # """--== Validation ==--"""
    # dbug(data_type(new_contents))
    # all file cat/write option should be raw
    if isempty(contents):
        dbug("No contents were provided... returning...")
        return
    if isempty(new_contents):
        dbug("No add_contents were provided... returning...")
        return
    # dbug(data_type(new_contents))
    if not isinstance(replace, str):
        dbug(f"replace: {replace} must be a string/pattern... returning...")
        return
    if arch_d is not None and not isinstance(arch_d, dict):
        dbug(f"arch: {arch_d} must be a dictionary called_from: {called_from()}... returning...")
        return
    # """--== Init ==--"""
    cur_dir = os.getcwd()
    after_pos = 0
    replace_pos = None
    if isempty(replace) and not isempty(either):  # yes, this is correct!
        replace = either
    inserted = False
    sort_len = 9999  # arbitrary
    # """--== Convert ==--"""
    if not isempty(filename) and not file_exists(filename):
        # dbug(f"got here filename: {filename} file_exists(): {file_exists(filename)}")
        filename = contents
        # dbug(filename)
        contents = cat_file(filename, 'raw', 'lst')
        # contents = []
        # dbug(len(contents))
    # dbug(f"{filename=}")
    if isinstance(contents, str) and isempty(filename):
        # dbug(f"{contents=} {filename=}")
        if file_exists(contents):
            filename = contents
            contents = cat_file(filename, 'raw', 'lst')
            # contents = cat_file(filename, 'raw')
            # dbug(len(contents))
    if isinstance(contents, str):
        contents = contents.rstrip("\n")
        if "\n" in contents: # if there are embedded newlines
            contents = contents.split("\n")
    # dbug(contents, 'noask')
    if not isempty(filename): 
        # a filename was provided
        if file_exists(filename):
            contents = cat_file(filename, 'raw', 'lst')
        # dbug(contents[:2])
    if isinstance(new_contents, dict):
        # assuming we just want the values added
        if isempty(contents):
            contents = ",".join(map(str,new_contents))  # contents must be a dict here
            contents = [contents]  # turn this into a list of (one) string(s)
            # dbug(f"{contents=}", 'ask')
        new_contents = ",".join(f'"{v}"' if "," in str(v) else str(v) for v in new_contents.values())
        # dbug(new_contents, 'ask')
    # if not isinstance(new_contents, str):
        # dbug(f"{new_contents=} must be a string... returning {called_from('v')}...")
        # return
    if isinstance(new_contents, list) and all([isinstance(elem, str) for elem in new_contents]):
        new_contents = new_contents.rstrip("\n")  # don't want ending newlines
    contents = [line.rstrip("\n") for line in contents]  # make sure all lines are stripped of ending newline
    # """--== Process ==--"""
    before_pos = len(contents)  # don't put this in the init section
    # """--== first let handle arch_d | bak_b ==--"""
    if not isempty(arch_d):
        arch(filename, **arch_d)
    if bak_b and not isempty(filename):
        filesize = os.path.getsize(filename)
        limit = 100
        if filesize > 10:  # arbitrary
          try:
              shutil.copy(filename, f"{filename}.bak")
              if prnt:
                  if prnt:
                      dbug(f"Copied [{filename}] to {filename}.bak")
          except Exception as e:
              if prnt:
                  dbug(f"Something went wrong? Error: {e}")
        else:
          dbug(f"Not backing up as filesize: {filesize} is less than limit: {limit}")
    # """--== SEP_LINE ==--"""
    # dbug(contents[:3])
    # dbug(new_contents)
    if isempty(after) and isempty(before) and isempty(replace) and not sort_b:
        # dbug(f"just add the new_contents {called_from('v')}")
        contents += [new_contents]  # assumes new_contents is a str?
        inserted = True
    else:
        for num, line in enumerate(contents):
            line = str(line)
            if not isempty(after):
                after_regx = re.search(after, line)
                if after_regx:
                    after_pos = num 
                    # dbug(f"Found regex search for after: [{after}] at after_pos: {after_pos}")
            if not isempty(before):
                before_regx = re.search(before, line)
                if before_regx:
                    before_pos = num
                    # dbug(f"Found regex search for before: [{before}] at before_pos: {before_pos}")
            if not isempty(replace):  # keep in mind replace is equal to either - see Init section
                # dbug(f"replace: {replace} called_from: {called_from()}")
                replace_regx = re.search(replace, line)
                if replace_regx:
                    replace_pos = num
        if not isempty(before) and before_pos > len(contents) - 1:
            dbug(f"Apparently no match to before: {before} before_pos: {before_pos} len(constents): {len(contents)}", 'ask')
    # dbug(new_contents)
    if before_pos < after_pos:
        dbug(f"We have a problem as before_pos: {before_pos} comes prior to after_pos: {after_pos}", 'ask')
    # dbug(f"after_pos: {after_pos} before_pos: {before_pos}")
    # dbug(f"{data_type(contents)=} {contents[:3]=}")
    # """--== do add content ==--"""
    fromto = contents[after_pos:before_pos]
    # dbug(fromto, 'lst')
    # dbug(f"{data_type(contents)=} {contents[:3]=}", 'ask')
    # dbug(new_contents)
    for num, line in enumerate(fromto):
        line = str(line)
        # dbug(f"chkg line: {line} num: {num}")
        if isempty(replace):
            if not isempty(after) and not sort_b:
                contents.insert(after_pos + 1, new_contents)
                # dbug(f"just added ad_contents: {new_contents} num: {num}")
                inserted = True
                break
            if before != "" and not sort_b:
                contents.insert(before_pos, new_contents)
                inserted = True
                # content_added = True
                # dbug(f"just added ad_contents: {new_contents} num: {num}")
                break
        else:
            # dbug(f"{replace=} pattern {line=} {replace_pos=}")
            replace_regx = re.search(replace, line)
            if replace_regx:
                # dbug(replace)
                # dbug(after_pos)
                # dbug(num)
                replace_pos = after_pos + num 
                # dbug(f"{replace=} pattern {line=} {replace_pos=}")
                break
    # dbug(new_contents)
    if not isempty(replace) and isinstance(replace_pos, int) and not inserted:
        contents[replace_pos] = new_contents
        inserted = True
    if not isempty(either) and not inserted:
        contents.insert(before_pos, new_contents)
        inserted = True
    # dbug(f"after_pos: {after_pos} before_pos: {before_pos} inserted: {inserted}")
    # dbug(f"{data_type(contents)=} {contents[:3]=}", 'ask')
    # """--== the real work to add starts here ==--""" #
    # """ we want to deal with a list of line strings """ #
    # """--== sort ==--"""
    if sort_b:
        if isnumber(sort_b):
            sort_len = int(sort_b)
        beg_contents = contents[:after_pos + 1]
        unsorted_block = contents[after_pos + 1:before_pos + 1]
        # unsorted_block = contents[after_pos + 1:before_pos]
        # printit(unsorted_block, 'boxed', tile="unsorted", footer=dbug('here'))
        new_lines = []
        # inserted = False
        for ln in unsorted_block:
            if not inserted:
                if len(ln) > 0:
                    if new_contents.lower()[:sort_len] <= ln.lower()[:sort_len]:  # <-- TODO how to handle color codes
                        #new_lines.insert(len(new_lines) - 1, new_contents)
                        new_lines.insert(len(new_lines), new_contents)  # I put this back in 20241121
                        inserted = True
            new_lines.append(ln)
        if not inserted:
            # dbug(inserted)
            new_lines.append(new_contents)
            inserted = True
        sorted_block = new_lines
        # dbug("chk now", 'ask')
        end_contents = contents[before_pos + 1:]
        # add 'em up #
        contents = beg_contents + sorted_block + end_contents
    os.chdir(cur_dir)  # this is important!
    # dbug(inserted)
    # dbug(f"{data_type(contents)=} {contents[:3]=}")
    # """--== write_b (default=True) ==--"""
    # import csv  # just don't use this !!!
    # import io
    # dbug(filename)
    # dbug(data_type(contents))
    # dbug(contents[:3])
    # contents = fixlol(contents)
    # dbug(data_type(contents))
    # if data_type(contents, ['lol','lom']):
    #     # if you value your sanity do NOT use this csv code!
    #     output = io.StringIO()
    #     writer = csv.writer(output)
    #     writer.writerows(contents)
    #     csv_l = output.getvalue()
    #     dbug(csv_l[:4], 'ask')
    # dbug(f"{contents[:3]=} {data_type(contents)=}", 'ask')
    if write_b and not isempty(filename):
        # dbug(contents[:3])
        # dbug(f"{write_b=} {filename=} {data_type(contents)=} {len(contents)=} {filename=}")
        write_file(contents, filename, raw=True, ask=False)
        # with open(filename,"r") as f:  # for debugging only
            # dbug(len(f.readlines()))   # This would give length of files.
        # dbug(f"{funcname()} called_from: {called_from()} file was written to filename: {filename} len(contents): {len(contents)}... chkit?", 'ask')
    # """--== Return ==--"""
    # dbug(f"returning contents: {contents[:3]}")
    if not inserted:
        dbug(f"new_content was NOT added or inserted... please investigate...{called_from('v')}")
    return contents
    # ### EOB def addit(contents="", new_contents="", *args, **kwargs): ### #


# #####################################
def arch(filename="", *args, **kwargs):
    # #################################
    """
    purpose: to archive files for backup into an ARCH (archive) dir
    requires: filename
    options:
        - prnt: bool        # verbose runtime info
        - boxed: bool=False # will box a status message
        - days: int         # number of days we keep - any file older than 'days' will be deleted
        - files: int        # number of files to keep (you can define both days and files if you desire) 
        - archdir: str      # default='ARCH' - name of the directory to use - it is assumed that this will be off of the filename's dir
        - stats: bool       # presents a final dbug stat info line
        - bak: bool         # creates a copy of the file.name in the same directory a file.name.bak
        - box_clr: str="yellow! on black!"  # just as it says
    returns bool            # True is successful
    useage:
        eg
        - arch(my_file.name, days=5, files=4, arch_dir='ARCHIVE')
    notes:
        WARNING: be careful here: if you provide the wrong option you might DELETE unintended files!!! or corrupt files <-- WARNING WARNING WARNING
        - if you set files=0 then no archive file will be created
        WIP 20240814
    """
    # import time
    # import shutil
    # from gtoolz import file_exists
    # """--== Debugging ==--"""
    # dbug(f"{funcname()} {called_from('verbose')}")
    # dbug(kwargs)
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    day_limit = kvarg_val(['days', 'age', 'day_limit'], kwargs, dflt=0)
    file_limit = arg_val(['files', 'keep', 'limit', 'num', 'number', 'file_limit'], args, kwargs, dflt=None)
    seconds_limit = kvarg_val(['seconds', 'ttl'], kwargs, dflt=0)
    arch_dir = kvarg_val(['arch_dir', 'archdir', 'dir'], kwargs, dflt='ARCH')
    stats_b = arg_val(['stats'], args, kwargs, dflt=False)
    bak_b = arg_val(['bak', 'back', 'bakup', 'backup'], args, kwargs, dflt=False)
    boxed_b = arg_val(['box', 'boxed'], args, kwargs, dflt=False)
    centered_b = arg_val(['center', 'centered'], args, kwargs, dflt=False)
    # arch_b = kvarg_val(['arch'], args, kwargs, dflt=False)  # this is a WIP
    box_clr = arg_val(['box_clr', 'cox_color'], args, kwargs, dflt="yellow! on black!")
    # """--== Init ==--""" #
    file_table = None
    orig_dir = os.getcwd()
    if file_limit == 0:
        file_limit = None
    rtrn = None
    # """--== Validation ==--"""
    if not file_exists(filename) or os.stat(filename).st_size == 0:
        if prnt:
            dbug(f"Filename: {filename} either does not exist or is empty... returning...")
        return rtrn
    # """--== Init ==--"""
    stat_msg = []
    rtrn = False
    abs_filename = os.path.abspath(filename)
    # dbug(f"{abs_filename=} {called_from('v')} {prnt=}")
    filename_dir = os.path.abspath(os.path.dirname(filename))
    # dbug(filename_dir)
    # root_filename = rootname(filename)
    # dbug(root_filename)
    # """--== Process ==--"""
    # cur_dtime = datetime.now().strftime("%Y%m%d-%H%M%S")                         
    cur_dtime = datetime.now().strftime("%Y%m%d-%H%M")                         
    os.chdir(filename_dir)  # just to be safe
    # basename = os.path.basename(filename)
    # dbug(basename, 'ask')
    # dbug(os.getcwd())
    # """--== bak file ==--"""
    if bak_b:
        bak_filename = filename + ".bak"
        shutil.copyfile(filename, bak_filename) 
    # """--== arch file ==--"""
    full_arch_dir = f"{filename_dir}/{arch_dir}/"
    # dbug(full_arch_dir)
    if not file_exists(full_arch_dir, type='dir'):
        if askYN(f"Archive dir: {full_arch_dir} does not exist... do you want to create it?", "y"):
            os.mkdir(full_arch_dir)
        else:
            dbug("User does not want to create the archive dir... returning...")
            return rtrn
    arch_filename = os.path.basename(filename) + f"-{cur_dtime}"
    full_arch_filename = f"{full_arch_dir}/{arch_filename}"
    if prnt:
        stat_msg.append(f"Copying filename: {abs_filename} to arch_name: {full_arch_filename}")
    shutil.copyfile(abs_filename, full_arch_filename) 
    # """--== now remove any over the age limit in arch_dir ==--"""
    os.chdir(full_arch_dir)  # just to be safe
    # dbug(list_of_files)
    # """--== SEP_LINE ==--"""
    os.chdir(filename_dir)  # just to be safe
    file_l = []
    directory = os.getcwd()
    # dbug(directory)
    # for filename in os.listdir(directory):
    base_filename = os.path.basename(filename)
    # dbug(base_filename)
    for filename in glob.glob(f"{full_arch_dir}/{base_filename}*"):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_l.append((filepath, os.path.getmtime(filepath)))
    # Sort files by modification time (oldest first)
    file_l.sort(key=lambda x: x[1])
    rev_file_l = file_l[::-1]
    # for stats
    rev_files_len = len(rev_file_l)
    if stats_b:
        my_l = [elem[0] for elem in rev_file_l]
        file_table = gcolumnize(my_l, 2, 'boxed', 'sep', 'noprnt', title=f"Matching files to {base_filename}* {len(my_l)=}", footer=dbug('here'), box_clr=box_clr, centered=centered_b)
    # """--== SEP_LINE ==--"""
    file_cnt = 0
    current_time = time.time()
    day_seconds = 86400
    # day_seconds = 5  # for testing only!!!
    # list_of_files = os.listdir()
    for file in rev_file_l:
        file_cnt += 1
        # dbug(file)
        file_location = os.path.join(os.getcwd(), file[0])
        file_time = os.stat(file_location).st_mtime
        seconds_diff = current_time - file_time
        if day_limit > 0 and  (file_time < current_time - day_seconds*day_limit):
            os.remove(file_location)
            if prnt:
               stat_msg.append(f" Deleting : {file} exceded day limit")
        if file_limit is not None and file_cnt > file_limit:
            os.remove(file_location)
            if prnt:
               stat_msg.append(f" Deleting : {file} exceded file limit")
        if seconds_limit > 0 and seconds_diff > seconds_limit:
            os.remove(file_location)
            stat_msg.append(f" Deleting : {file} exceded seconds limit")
    # """--== stats ==--"""
    os.chdir(full_arch_dir)  # just to be safe
    list_of_files = glob.glob(f"{base_filename}*")
    cur_file_len = len(list_of_files)
    if cur_file_len > rev_files_len:
        # looks like thigs were successful
        rtrn = True
    if stats_b:  #  or prnt:
        stat_msg.append(f"ARCH file created: {arch_filename} Number of original archived files: {rev_files_len} Current number of saved files: {cur_file_len}")
        stat_msg.append(f"{day_limit=} {file_limit=} {seconds_limit=}")
    # """--== returning ==--"""
    os.chdir(orig_dir)
    # dbug("Returning None")
    if prnt:
        printit(stat_msg, boxed=boxed_b, centered=centered_b, box_clr=box_clr, footer=dbug('here'), txt_centered=99)
        if file_table:
            printit(file_table, boxed=True, centered=centered_b, box_clr=box_clr, footer=dbug('here'))
    return rtrn
    # ### EOB def arch(filename="", *args, **kwargs): # ###


# ###############
def try_it(func, *args, attempts=1, **kwargs):
    # ###########
    """
    This is BROKEN BROKEN BROKEN - TODO
    This is a wrapper function for running any function that might fail
    - this will report the error and move on
    use:
        @try_it
        def my_func():
            print("if this failed an error would be reported ")
        my_func()
    """
    def inner(*args, **kwargs):
        rsps = func(*args, **kwargs)
        return rsps
    r = inner(*args, **kwargs)
    # dbug(f"returning {r}")
    return r


# ##############################
def max_width_lol(input_table):
    # ##########################
    """
    purpose: to determin max_width for each "column" in a list of lists
        this is a way of truncating "columns"
    returns: column sizes
    """
    # dbug(type(input_table))
    # dbug(input_table)
    columns_size = [0] * len(input_table[0])
    last_row_len = len(input_table[0])
    for row in input_table:
        if len(row) < last_row_len:
            dbug("WARNING: Found inconsistent row lengths... returning")
            dbug(f"last_row_len: {last_row_len} this row len: {len(row)}")
            dbug(row)
            dbug(f"First row len: {len(input_table[0])}")
            return
        # dbug(len(row))
        # dbug(type(row))
        for j, column_element in enumerate(row):
            columns_size[j] = max(columns_size[j], len(str(column_element)))
    return columns_size


# ####################
def comma_split(my_s, *args, **kwargs):
    # ################
    """
    purpose: split a line/str (or list of lines) using commas unless the comma is embedded in quotes
    returns: list (or list of lists) of comma separated elements
    notes: this is a kludge but it works for me
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(args)
    # dbug(kwargs)
    # """--== Recurse if my_s is a list ==--"""
    if isinstance(my_s, list):
        # we will need to recurse...
        # dbug(my_s[:3])
        new_l = []
        for ln in my_s:
            # dbug(ln)
            new_ln = comma_split(ln)
            # dbug(new_ln, 'ask')
            new_l.append(new_ln)
    # """--== Process ==--"""
    # new_l = re.split(r'(?:,\s*)(?=(?:[^"]*"[^"]*")*[^"]*$)', my_s)
    # dbug(new_l)
    if isinstance(my_s, str):
        my_s = my_s.strip('\"')
        my_s = my_s.strip('\'')
        # this breaks if a single quote mark is embedded in an element - even if it is embedded in a quote bound string TODO - your need to escape it? to avoid this issue?
        comma_pat = re.compile(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)")
        split_result = comma_pat.split(my_s)
        # dbug(split_result)
        new_l = []
        for elem in split_result:
            elem = elem.strip()
            # dbug(elem)
            if elem.startswith('"') and elem.endswith('"'):
                # dbug(elem)
                elem = elem.strip('"')
                # dbug(elem)
            if elem.startswith("'") and elem.endswith("'"):
                # dbug(elem)
                elem = elem.strip("'")
                # dbug(elem)
            if "'" in elem and "," in elem:
                elems = elem.split(",")
                new_l.extend(elems)
            else:
                new_l.append(elem)
    return new_l
    # ### EOB def comma_split(my_s): ### #



def comma_join(data, *args, **kwargs):
    """
    purpose: given a list of elems or list or lists (of elems
            this function will turn each row into a proper comma delimited string or line
            The reason for this function is to take a list and make *sure* it is a proper csv list - with quoted elems as needed
    options:
        - newlines = bool - False  # to be used if you want to add a newline to the end of the line(s)
    returns: a list of comma delimited strings (lines) typically used for csv
    notes: this has not been fully tested yet
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(data)
    # dbug(data[:3])
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    newline_b = arg_val(["newlines", "newline"], args, kwargs, dflt=False)
    # """--== Init ==--"""
    line = ""
    elems = []
    # """--== Convert ==--"""
    if isinstance(data, str):
        dbug("Nothing to do ... comma_join needs a list...")
        return
    # if islol(data):
    if data_type(data, 'lol'):
        dbug(f"data[:3] {data[:3]} appears to be an lol")
        rtrn_l = []
        for row in data:
            new_ln = comma_join(row, newline=newline_b)
            rtrn_l.append(new_ln)
        return rtrn_l
    # dbug(data)
    # """--== SEP_LINE ==--"""
    # data must be a simple row of elems... ie a list
    for elem in data:
        # dbug(elem)
        elem = str(elem)
        if "," in elem or "'" in elem:
            elem.replace('"', '\\"')
            elem.replace("'", "\\'")
            elem = '"' + elem + '"'
        # dbug(f"adding elem: {elem}")
        elems.append(elem)
    # dbug(elems)
    line = ", ".join(elems)
    # dbug(line)
    if newline_b:
        # dbug(newlines)
        if not line.endswith("\n"):
            line = str(line) + "\n"
    # dbug(f"Returning line: {line}... type(line): {type(line)}")
    return line
    # ### EOB def comma_join(data, *args, **kwargs): ### #


# ##################################
def get_elems(lines, *args, index=False, col_limit=20, **kwargs):
    # ##############################
    """
    purpose: designed to split a list of lines on delimiter - respects quoted elements that may contain "," even if that is the delimiter
        - wip - this does the same thing as comma_split but adds a few options TODO
    requires:
        lines (as a list)
    options:
        - delimiter: str     # (default is a comma)
        - col_limit: bool    # max column size default=0 - if 0 no truncation occurs otherwise all elems are limited to col_limit
        - index: bool        # will insert an index (line numbers starting with 0)  # not used yet TODO
        - lst: bool          # assumes a single line (ie: lines = str) so it returns a list of elemes from that line
                             #      instead of a list_of_elems for multiple lines (ie an lol)
    Returns:
        an array: list of list (lol - lines of elements aka rows and columns)
        aka rows_lol
    Notes: be carefull - if a "#" is encountered it will be treated as the begining of a comment
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(lines[:3])
    # dbug(index)
    # dbug(col_limit)
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    prnt = arg_val(['prnt'], args, kwargs, dflt=False)
    delimiter = kvarg_val(["delim", 'delimiter'], kwargs, dflt=",")
    col_limit = kvarg_val(["col_limit", 'collimit' 'colmax', 'col_max'], kwargs, dflt=0)  # not used yet TODO
    index = kvarg_val(["index", 'indx', 'idx'], kwargs, dflt="")  # not used yet TODO
    # dbug(delimiter)
    lst_b = arg_val(["list", "lst"], args, kwargs, dflt=False)
    # """--== Imports ==--"""
    # import pyparsing as pp
    # """--== Init ==--"""
    my_array = []
    # """--== Convert ==--"""
    # make it a list of lines
    if isinstance(lines, dict):
        # treat keys as column names and values as data
        lines = [list(lines.keys()), list(lines.values())]  # now this is a lol
        dbug(lines)
    if isinstance(lines, str):
        lines = lines.rstrip("\n")
        # dbug(lines)
        lines = [lines]
        # dbug(lines, 'ask')
    # """--== Validate ==--"""
    # if islol(lines):
    if data_type(lines, 'lol'):
        # dbug(f"lines: {lines} is already an lol")
        return lines
    # dbug(lines[0], 'ask')
    # I discovered an issue: if some lines were not elems of a list but other lines were, hence below code
    if isinstance(lines, list) and delimiter == ",":  # the default delimiter is ","
        new_lines = []
        for line in lines:
            # dbug(line)
            if line.startswith("#"):
                if prnt:
                    dbug(f"line: {line}\n...appears to be a comment... skipping...")
                continue
            if isinstance(line, str) and "," in line:
                # dbug(repr(line))
                # dbug(line[0])
                COMMA_MATCHER = re.compile(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)")
                elems = COMMA_MATCHER.split(line)
                # dbug(elems)
                for i, elem in enumerate(elems):
                    elem = elem.strip()  # get rif of leading or trailing whitespace
                    if isempty(elem):
                        continue
                    # this is an example of removing double quoted elem: [elem[1:-1] if elem[0] in ("'", '"') else elem for elem in colnames]
                    if elem[0] in ("'",'"') and elem[-1] == elem[0]:
                        # dbug(f"dequote repr(elem): {repr(elem)}")
                        elem = elem[1:-1]
                    elems[i] = elem
                # dbug(new_line)
            else:
                # assuming this is like a ".dat" file
                elems = line.split()
            new_lines.append(elems)
        if len(new_lines) == 1 and isinstance(new_lines[0], list):
            new_lines = new_lines[0]
            # dbug(new_lines, 'ask')
        return new_lines
    if "," not in lines[0] and "," in delimiter:
        # dbug(f"delimiter: [{delimiter}] not found in lines[0]: {lines[0]} reverting to a whitespace ")
        delimiter = " "
        if delimiter not in lines[0]:
            dbug(f"delimiter: [{delimiter}] not found in lines[0]: {lines[0]} reverting to a whitespace ")
    # """--== SEP_LINE ==--"""
    if delimiter == " ":
        new_rows = []
        for line in lines:
            elems = line.split()
            # dbug(elems)
            # new_line = ",".join(line.split())
            new_rows.append(elems)
        delimiter = ","
        my_array = new_rows
        # dbug(my_array[:2])
    else:
        # dbug(lines[:3], 'ask')
        my_array = comma_split(lines)
        # dbug(my_array[:3], 'ask')
    # """--== Process ==--"""
    if index:
        for n, row in enumerate(my_array):
            # dbug(f"n: {n}")
            row.insert(0, str(n))
    if lst_b:
        # this all may change to testing if len(my_array) == 1 then do this
        my_array = my_array[0]
    # """--== SEP_LINE ==--"""
    new_array = []
    for row in my_array:
        my_row = []
        for elem in row:
            if elem.startswith('"') and elem.endswith('"'):
                elem = elem.strip()
                # dbug(elem)
                elem = elem.strip('"')
                # dbug(elem)
            if elem.startswith("'") and elem.endswith("'"):
                # dbug(elem)
                elem = elem.strip("'")
                # dbug(elem)
            my_row.append(elem)
            if col_limit > 0:
                elem = elem[:col_limit]
        new_array.append(my_row)
    # dbug(new_array)
    if index:
        new_array = [row.insert(n) for n, row in enumerate(new_array)]
        # dbug(new_array)
    # """--== SEP_LINE ==--"""
    # dbug(f"Returning my_array: {new_array}")
    return new_array  # aka rows_lol
    # ### EOB def get_elems(lines, *args, index=False, col_limit=20, **kwargs): ### #


# #############################################
def retry(howmany, *exception_types, **kwargs):
    # #########################################
    """
    purpose: a wrapper to retry a function x (howmany) times
    notes: there is a module called retrying that deserves more research and it provides a wrapper function called @retry()
    useage: eg:
        @retry(5, MySQLdb.Error, timeout=0.5)
        def the_db_func():
            # [...]
            pass
    This is untested - completely expimental
    It is essentially the same as:
    for attempts in range(3):
        try:
            do_work()
            break
        except Exception as e:
            print(f"Attempts: {attempts}. We broke with error: {e}")
    """
    try:
        import decorator
    except Exception as e:
        dbug(f"Failed to import decorator Error: {e}")
    timeout = kwargs.get('timeout', 0.0)  # seconds
    @decorator.decorator
    def tryit(func, *fargs, **fkwargs):
        for _ in range(howmany):
            try:
                return func(*fargs, **fkwargs)
            except exception_types or Exception:
                if timeout is not None:
                    time.sleep(timeout)
    return tryit


# ###############################################
# def get_html(url, rtrn_type="", *args, **kwargs):
def get_html(url, *args, **kwargs):
    # ###########################################
    """
    purpose: uses requests and Beautiful soup to get raw text, soup object, or tables using provided url
    requires: url
    options:
        - rtrn_type: str=""    # can be: 'raw', 'lst' or 'list' or 'tables'
            - raw
            - lst|list
            - tables
        - prnt: bool=False
        - centered: bool=False
        - table: bool=False    # makes the rtrn_type = 'tables'
            if prnt is True:
                - col_limit: int=45
        - ask: bool=False  # only works with show/prnt=True
        - add_cols: bool=False  # only works with show/prnt=True, adds colnames ie ["col1", "col2", "col3,...]
    returns: depends on rtrn_type
    notes:
        - WIP
        - 20251112-1744
        - replaces get_html_tables and get_html_text
    """
    # """--== imports ==--""" #
    import requests
    from bs4 import BeautifulSoup
    import feedparser
    import brotli
    # import lxml
    # you will also need brotli and lxml
    # """--== SEP_LINE ==--""" #
    # dbug(f"{called_from('v')} {args=} {kwargs=}")
    # """--== Config ==--""" #
    prnt = arg_val(['prnt','show', 'print', 'verbose'], args, kwargs, dflt=False)
    fname = arg_val(['fname', 'filename', 'file'], args, kwargs, dflt="")
    # rtrn_type = arg_val(['rtrn', 'rtrntype', 'rtrn_type', 'return_type'], args, kwargs, dflt=rtrn_type)
    rtrn_type = arg_val(['rtrn', 'rtrntype', 'rtrn_type', 'return_type'], args, kwargs, dflt="text")
    # dbug(rtrn_type, 'ask')
    centered_b = arg_val(['centered', 'cntr', 'center'], args, kwargs, dflt=False)
    tables_b = arg_val(["tables", "table", "tbls", "tbl"], args, kwargs, dflt=False)
    if tables_b:
        rtrn_type = 'tables'
    params = arg_val(['params'], args, kwargs, params={})
    col_limit = arg_val(['col_limit'], args, kwargs, dflt=45)
    limit_cols = arg_val(['limit_cols'], args, kwargs, dflt=12)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    add_cols = arg_val(['add_cols','addcols'], args, kwargs, dflt=False)
    # """--== debugging ==--""" #
    # dbug(f"{prnt=} {called_from('v')} {url=} {rtrn_type=} {fname=}")
    # """--== Init ==--""" #
    if rtrn_type in ('show', 'prnt', 'verbose', 'print'):
        # fix for user putting this in as second arg
        prnt = True
        rtrn_type = 'text'
    rtrn = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        }
    # """--== Process ==--""" #
    # url_dtype = data_type(url)
    # dbug(f"{url_dtype=} {rtrn_type=} {called_from('v')}", 'noask')
    # dbug(f"trying to get response from {url=}")
    response = None
    # dbug(f"{rtrn_type=}")
    if rtrn_type not in ("rss") or rtrn_type == "":
        # dbug(f"{rtrn_type=}", 'ask')
        try:
            s = requests.Session()
            s.max_rejects = 60
            response = s.get(url, params=params, headers=headers, timeout=40)  # <-- rubber hits the road
        except Exception as Error:
            dbug(f"{Error=} {url=} {called_from('v')} {rtrn_type=} ...")
            return
        # dbug(f"{rtrn_type=} {called_from('v')}", 'noask')
        # """--== html code status ==--""" #
        if response.status_code != 200:
            code_def = html_codes(code=response.status_code)
            if prnt:
                dbug(f"[red!]{response.status_code=}[/]\n[yellow!]{code_def=}[/]\nurl:{url} {called_from('v')} {response.encoding=}... returning...", 'boxed')
            return
        # dbug(f"Looks good so far {response.status_code=} {url=}")
        if prnt:
            dbug(f"{prnt=} {response.status_code=} {rtrn_type=} {url=} {called_from('v')}")
        # dbug(f"{url_dtype=} {rtrn_type=} {called_from('v')}", 'noask')
        # """--== encoding ==--""" #
        # dbug(response.headers.get('Content-Encoding'))  # if this is 'br' then you need to get pip install brotli (do this) or brotlicffi (full integration-don't do brotlicffi!)
        if response.headers.get('Content-Encoding') == "br":
            try:
                import brotli
            except Exception as Error:
                dbug(f"{Error=} this site is encoded with brotli - you need to get pip install brotli (do this) or brotlicffi (full integration-don't do brotlicffi!")
                return
        encode = response.encoding
        if encode != 'utf-8':
            response.encoding = response.apparent_encoding
    if response is None:
        dbug(f"{response=} {url=} {called_from('v')} {rtrn_type=}")
    # """--== rtrn_type text ==--""" #
    # dbug(rtrn_type, 'ask')
    if rtrn_type in ('','text', 'raw', 'json', 'txt'):
        # dbug(f"we are here {rtrn_type=} {called_from('v')}")
        text = response.text
        # dbug(text)
        dtype = data_type(text)
        # dbug(f"we are here {url=} {dtype=} {rtrn_type=} {called_from('v')}")
        # dbug(f"{dtype=} {rtrn_type=}")
        # if rtrn_type == 'json' or dtype == 'json':
        if 'json' in dtype:
            import json
            text = json.loads(text)
            # dbug(f"Converted str to data: {data_type(text)=}")
        if prnt:
            dbug(text)
        if isempty(text):
            dbug(f"{response.status=}")
        # dbug(f"Returning text as {data_type(text)=}")
        return text
        # rtrn = text
    else:
        if rtrn_type not in ("rss"):
            # dbug(f"we are here {rtrn_type=} {called_from('v')}")
            # soup = BeautifulSoup(response.text, 'html_parser')  # fails, even tried istalling html parser
            try:
                soup = BeautifulSoup(response.text, 'lxml')
            except Exception as Error:
                dbug(f"{Error=} {url=}  {called_from('v')}")
                return
    # dbug(f"{url_dtype=} {rtrn_type=} {called_from('v')}" 'noask')
    # """--== rtrn_type soup ==--""" #
    if rtrn_type in ('soup'):
        # dbug(f"we are here {rtrn_type=} {called_from('v')} returning: {type(soup)=}")
        if not soup:
            dbug(f"{url=} does not return {soup=} {rtrn_type=}")
        return soup
    # """--== rtrn_type paragraphs ==--""" #
    if rtrn_type in ('p', 'paragraphs'):  # not used?
        # dbug(f"we are here {rtrn_type=} {called_from('v')}")
        paragraphs = soup.find_all(['p', 'div', 'tr', 'br'])
        text = '\n'.join([p.get_text() for p in paragraphs])
        if "\n" in text:
            text_l = text.split("\n")
            text_l = [ln for ln in text_l if ln.strip()]
            rtrn = "\n".join(text_l)
    # """--== rtrn_type list ==--""" #
    if str(rtrn_type) in ("list", 'lst'):
        # dbug(f"we are here {rtrn_type} {called_from('v')}")
        text = soup.get_text()
        text = text.splitlines()
        rtrn = [line for line in text if line.strip()]
    # """--== rtrn_type tables ==--""" #
    if rtrn_type in ('table', 'tables'):
        dtype = data_type(response.text)
        # dbug(f"we are here {rtrn_type} {dtype=} {url=}{called_from('v')}")
        # if dtype == 'json':
        if 'json' in dtype:
            import json
            my_data = json.loads(response.text)
            # dbug(my_data)
            if askYN(f"Found json data {dtype=} - do you want me to try gtable? ", "y"):
                tbl = gtable(my_data, 'noprnt', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
                if prnt:
                    printit(tbl)
            if not my_data:
                dbug(f"{url=} fails for {rtrn_type=}")
            return
        # dbug('ask')
        # dbug(f"{rtrn_type=}")
        html_tables = soup.find_all("table") 
        if not html_tables and prnt:
            dbug(f"Response was good for {url=} but soup failed for tables...{len(html_tables)=} {called_from('v')}", 'noask', box_clr="flash red!")
        else:
            tables = []
            data = []
            for tbl_num, table in enumerate(html_tables):  # Corrected syntax error here
                if isempty(table):
                    dbug(f"Found an empty table {tbl_num=}")
                    continue
                data = []
                for row in table.find_all('tr'):
                    # 1. Build the row data in a single, clean pass
                    row_data = [cell.get_text("|", strip=True) for cell in row.find_all(['th', 'td'])]
                    # 2. Skip completely empty structural spacer rows
                    if row_data:
                        data.append(row_data)
                # gtable(data, 'prnt', 'hdr', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
                if not isempty(data):
                    data = fixlol(data, blanks="--")  # Converts empty cell elements to "--" so drop_col ignores them
                if any([len(row) != len(data[0]) for row in data]):
                    data = fixlol(data)
                if isempty(data):
                    continue
                try:
                    # Now drop_col will only target columns that are purely "--", "nan", or "NaN"
                    data = drop_col(data, pattern=["", "--", "nan", "NaN"])
                except Exception as Error:
                    dbug(f"{Error=} {data=} {isempty(data)=}", 'ask')
                if isempty(data):  # because the above may leave us with an empty data table
                     continue
                # gtable(data, 'prnt', 'hdr', 'noask', title=f"debugging {called_from('v')}", footer=dbug('here'), box_clr='red!')  # debugging only
                tables.append(data)
    # dbug(len(tables), 'ask')
    rtrn = tables
    # dbug(len(tables))
    # """--== rtrn_type rss ==--""" #
    if rtrn_type in ("rss"):
        # dbug("here now")
        feed = feedparser.parse(url)
        # dbug(f"OK playing like this is rss now.... {feed.bozo=} {feed.version=}")
        if not feed.bozo:
            my_rss_lol = cnvrt(feed.entries)
            if prnt:
                colnames = my_rss_lol[0]
                # dbug(colnames)
                gtable(my_rss_lol, 'prnt', 'hdr', 'endhdr', 'noask', colnames=colnames, title=f"debugging {called_from('v')}", footer=dbug('here') + f" {len(my_rss_lol)=}", box_clr='red!', wrap=False, col_limit=10)  # debugging only
            rtrn = my_rss_lol
        else:
            dbug(f"{url=} does NOT appear to be a valid {rtrn_type=} {called_from('v')}... returning...")
            return
        # bailing out - our work is done here
        return rtrn
    # dbug(f"{dtype=} {data_type(text)=}")
    # """--== fname ==--""" #
    if fname: # if user gave fname then write out the text to fname
        with open(fname, "w") as f:
            f.write(text)
        if prnt:
            dbug(f"{fname=} written...")
    # """--== prnt ==--""" #
    # dbug(f"{data_type(rtrn)=}")
    if prnt:
        # dbug("Here we are")
        if rtrn_type in ('table', 'tables'):
            if isempty(rtrn):
                printit(f"{url=} rtrn appears empty",'boxed', 'noask', title=f"debugging {called_from('v')} {rtrn=}", footer=dbug('here'), box_clr='red!')  # debugging only
            else:
                for tbl_num, data in enumerate(rtrn, start=1):
                    if add_cols:
                        colnames = []
                        # dbug(data)
                        for n in range(len(data[0])):
                            colnames.append(f"col{n+1}")
                        data.insert(0,colnames)
                    data = [row[:limit_cols] for row in data]
                    gtable(data, 'prnt', 'hdr', centered=centered_b, title=f"debugging {url[:80]=}... {tbl_num} of {len(tables)=}", footer=dbug('here') + " " + called_from('v'), col_limit=col_limit, wrap=True, box_clr="red!")
        else:
            printit(rtrn, 'boxed' , title=f'[yellow!]{url=}[/]', footer=dbug('here'))
        if ask_b:
            dbug('ask')
    # dbug(len(tables))
    # """--== returning ==--""" #
    # dbug(f"{data_type(rtrn)=}")
    # if data_type(rtrn, 'lolols'):
    #     if all([data_type(my_lol, ('lol')) for my_lol in rtrn]):
    #         for lol in rtrn:
    #             gtable(lol, 'prnt', title='debugging', footer=dbug('here'), pivot=False, col_limit=25)
    # if data_type(rtrn, ('lol')):
    #     dbug(rtrn)
    #     if len(rtrn) == 2:
    #         pivot_b = True
    #     else:
    #         pivot_b = False
    #     dbug(pivot_b)
    #     gtable(rtrn, 'prnt', title='debugging', footer=dbug('here'), pivot=pivot_b, col_limit=25)
    # dbug(f"returning rtrn {called_from('v')}")
    return rtrn
    # ### EOB def get_html(url, *args, **kwargs): ### #

# aliases
get_html_text = get_html

def get_html_qnd(*args, **kwargs):
    url = 'https://api.stlouisfed.org/fred/series/observations?series_id=SP500&observation_start=2023-07-22&observation_end=2026-07-21&api_key=d0f42c58c8b07d10be50c923240f143a&file_type=json'
    r = get_html(url) 
    dbug(r)


# ########################################################################
def get_html_tables(url="", *args, **kwargs):
    # ####################################################################
    """
    purpose: to pull/scrape all tables off an url
    required:  url
    requires:
        import requests
        from bs4 import BeautifulSoup
    options:
        - show|prnt: bool  # default=False ... whether to print the tables
    returns: list(s) of list
    notes:
        This should be depracated in favor of get_html(... rtrn_type='tables',...)
    """
    dbug(f"This function has been deprecated - use gt_html(url, rtrn_type='tables') {called_from('v')} ... returning...", 'boxed')
    return
    # """--== imports ==--"""
    # import requests
    # if "bs4" not in sys.modules:
    #     dbug("bs4 (BeautifulSoup is needed for this capability... returning...")
    #     return
    # try:
    #     from bs4 import BeautifulSoup
    # except Exception as Error:
    #     dbug(Error)
    #     # dbug('ask')
    #     return
    # """--== Config ==--""" #
    prnt = arg_val(["prnt", "print", "show", "verbose"], args, kwargs, dflt=False)
    rtrn_type = arg_val(["rtrn", "rtrn_type"], args, kwargs, dflt='tables')
    # """--== Debugging ==--"""
    dbug(f"{url=} {called_from('v')} {prnt=} should be calling get_html(url, 'tables') instead")
    # dbug(url)
    # """--== experimental ==--""" #
    # dbug(f"{args=} {kwargs=} {rtrn_type=}")
    # tables = get_html(url, *args, rtrn_type=rtrn_type, **kwargs)
    # return tables
    # ### EOB def get_html_tables(url="", *args, **kwargs): ### #
    


# #################################
def display_in_cols(lst, cols=0, reverse="", on="value"):
    # #############################
    """
    deprecated as gtable may take it's place
    input: takes a list or a dict and prints in order across cols
    options:
        order default for list is is as-is
        if it is a dict
            you can sort "on" default "value" or on "key"
            , or reverse=True or reverse=False
    returns: lines (sorted if dict)
    example:
    # >>> lst = [*range(1,20)]
    # >>> display_in_cols(lst)
    then print lines eg printit(lines)
    """
    # import math
    # dbug(lst)
    # dbug(type(lst))
    if isinstance(lst, dict):
        from collections import OrderedDict
        my_lst = []
        # so this is a dict, lets change it to a list and continue on, but sort it first
        if on == "value":
            on = 1
        else:
            # sort based on key
            on = 0
        if reverse:
            my_sd = {k: v for k, v in sorted(lst.items(), key=lambda item: item[on], reverse=True)}
            # dbug(my_sd)
        if not reverse:
            # dbug(f"Sorting dict: {lst}")
            # my_sd = {k: v for k, v in sorted(lst.items(), key=lambda item: item[on], reverse=False)}
            my_sd = OrderedDict(sorted(lst.items(), key=lambda t: t[0]))
            # dbug(my_sd)
        if reverse == "":
            my_sd = lst
        # lst = []
        # dbug(my_sd)
        max_k = len(max(lst.keys(), key=len))
        vals = list(lst.values())
        vals = [str(elem) for elem in vals]
        max_v = len(max(vals, key=len))
        # dbug(f"max_k: {max_k} max_v: {max_v}")
        for k, v in my_sd.items():
            # dbug(f"k: {k} v: {v}")
            msg = f"[{k:<{max_k}}]: {v:>{max_v}} "
            my_lst.append(msg)
        lst = my_lst
        # dbug(my_lst)
    tot_num = len(lst)
    screen_cols = get_columns()
    # dbug(lst)
    if cols == 0 or cols == "":
        # dbug(max_len)
        max_elem_len = len(max(lst, key=len))
        # dbug(max_elem_len)
        if screen_cols > max_elem_len:
            # cols = math.floor(screen_cols / max_elem_len)
            cols = math.ceil(screen_cols / max_elem_len)
        else:
            cols = max_elem_len
    col = 0
    rows_num = math.ceil(tot_num / cols)
    # dbug(tot_num)
    # dbug(rows_num,ask=True)
    # matrix_tot = cols * rows_num
    max_elem_len = len(max(lst, key=len))
    rows = []
    for num in range(0, tot_num):
        # dbug(f"Processing num: {num}")
        row = []
        this = 0
        col = 0
        # for col in range(cols):
        while col < cols:
            # dbug(f"Processing col: {col} tot cols: {cols} current col:{col}")
            this = num + (rows_num * col)
            col += 1
            if this >= tot_num:
                this_e = " " * max_elem_len
            else:
                elem = lst[this]
                if len(elem) > max_elem_len:
                    elem = elem[max_elem_len:]
                if len(elem) < max_elem_len:
                    elem = elem + " " * (max_elem_len - len(elem))
                this_e = elem
            row.append(this_e)
        # dbug(row,ask=True)
        rows.append(row)
        col += 1
        if len(rows) >= rows_num:
            break
    lines = []
    for r in rows:
        lines.append("".join(r))
    return lines
    # ### EOB def display_in_cols(lst, cols=0, reverse="", on="value"): ### #


# #######################
def shadowed(lines=[], style=4, color="grey"):
    # ###################
    """
    purpose: adds shadowing typically to a box
    requires:
    input: lines as a list
    output: lines as a list
    Use this to see all the styles:
        msg = "this is \nmy message"
        for n in range(0,5):
            printit(centered(shadowed(boxed(msg + f"\nstyle: {n}"),style=n)))
    """
    # RESET = sub_color('reset')
    if isinstance(lines, str):
        lines = lines.split('\n')
    styles = []
    # the terminal you use significantly influences this!
    # top_right, vertical, bottom_left, horizontal, bottom_right
    #            .... tr[0] ,      v[1],    bl[2] ,     h[3] ,      br[4]]
    styles.append([chr(9699), chr(9608), chr(9701), chr(9608), chr(9608)])
    styles.append([chr(9617), chr(9617), chr(9617), chr(9617), chr(9617)])
    styles.append([chr(9618), chr(9618), chr(9618), chr(9618), chr(9618)])
    styles.append([chr(9619), chr(9619), chr(9619), chr(9619), chr(9619)])
    styles.append([chr(9612), chr(9612), chr(9600), chr(9600), chr(9624)])
    styles.append([chr(9608), chr(9608), chr(9600), chr(9600), chr(9600)])
    styles.append([chr(9608), chr(9608), chr(9600), chr(9600), chr(9624)])
    #
    shadow_chrs = []
    shadow_chrs = styles[style]
    new_lines = []
    cnt = 0
    # color = sub_color(color)
    color = gclr(color)
    for line in lines:
        if cnt == 0:
            # width = len(escaped(line))
            width = len(parse_codes(line, 'escaped'))
            line = line + " "  # add a space to help when centering
        if cnt == 1:
            # shadow_chrs[0] = chr(9612)
            line = line + color + shadow_chrs[0] + RESET
        if cnt > 1:
            # shadow_chrs[1] = chr(9612)
            line = line + color + shadow_chrs[1] + RESET
        new_lines.append(line)
        cnt += 1
    # now add bottom shadow line
    new_lines.append(" " + color + shadow_chrs[2] + shadow_chrs[3] * (width - 2) + shadow_chrs[4] + RESET)
    return new_lines
    # ### EOB def shadowed(lines=[], style=4, color="grey"): ### #


# ###################################################################
def add_or_replace(filename, action="end", pattern="", new_line="", *args, backup=True, **kwargs):
    # ###############################################################
    """
    purpose: Adds or replaces a line in a file where pattern occurs
    required: 
        - filename, 
        - action: str [before | after | replace | either | end | del] ,
            # action: before|after|replace|either|end  # 'either' will replace if it is found or add at the end if it is not)
            # action: del | delete AND  new_line == "" (default when not provided) then the line that matches pattern will be deleted
        - pattern: str 
        - new_line: str
    options:
        -   backup: bool=True,
        -   ask: bool=False,
        -   prnt: bool=False
        -   centered: bool=False,
        -   shadowed: bool=False
        -   lst: bool   # default=False - determines if return new_content should be a list instead of a string
        -   write: bool
        -   backup: bool
    returns: 
        -  new_contents as a string (unless 'lst' option is True)
    notes:
        - THIS FUNCTION is being deprecated and is replaced by addit()
        - consider using re.escape(pattern) before submission to this function (all special characters need to be escaped eg (+,],[,^,$,... etc)
        - NOTE: aka by alias as add_replace - should probably reverse these in favor o brevity TODO - also combine with sorted_add and new_add_content
    """
    dbug(f"funcname: {funcname()} called_from: {called_from()} - this being deprecated and replaced with addit()")
    # dbug(filename)
    # dbug(type(filename))
    # dbug(action)
    # dbug(f"raw pattern: {pattern}")
    # dbug(repr(pattern))
    # dbug(new_line)
    # dbug('ask')
    dbug(f"This needs to be to be re-factored with similar funcs. like new_add_content... Funcname: {funcname()} Called_from: {called_from()}")
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print', 'show', 'verify', 'verbose'], args, kwargs, dflt=False)
    ask = arg_val('ask', args, kwargs, dflt=False)
    # dbug(f'ask: {ask}')
    shadow_b = arg_val('shadowed', args, kwargs, dflt=False)
    center_b = arg_val('centered', args, kwargs, dflt=False)
    prnt = arg_val(['prnt', 'print', 'show', 'verify', 'verbose'], args, kwargs, dflt=False)
    backup = arg_val(["bak", "backup", "bakup"], args, kwargs, dflt=backup)
    write_b = arg_val(["write"], args, kwargs, dflt=True)
    lst = arg_val(["lst", "list"], args, kwargs, dflt=False)
    # """--== Init ==--"""
    linenum = 0
    # cnt = 0
    pattern_found = False
    content_lines = []
    new_content_l = []
    new_content = ""
    if action in ("either", "both"):
        action = "either"
    # startswith_pattern = ""
    # """--== Convert to content_lines ==--"""
    if isinstance(filename, str):
        if file_exists(filename):
            # dbug(type(filename))
            # dbug(filename)
            with open(filename, "r") as f:
                content_lines = f.readlines()
            content_lines = [line.rstrip("\n") for line in content_lines]
            # dbug(content_lines[:3])
        else:
            if "\n" in filename:
                # dbug("Splitting up filename")
                content_lines = filename.split("\n")
                filename = None
            else:
                dbug(f"Not sure what to do with filename: {filename} - perhaps the file does not exist..")
                return None
    elif isinstance(filename, list):
        # dbug("assuming this is a list of lines")
        # dbug(filename)
        content_lines = filename
        # dbug(content_lines)
        # dbug('ask')
        filename = None  # this will get chkd below
        backup = False
        write_b = False
    else:
        # dbug(type(filename))
        dbug(f"The filename: {filename} is not an acceptible name or list of contents ... returning")
        return None
    # dbug(content_lines[:5], 'lst')
    # """--== Process ==--"""
    # """--== Backup if file and requested ==--"""
    import shutil
    if backup and not isempty(filename):
        # dbug(filename)
        filesize = os.path.getsize(filename)
        # dbug(filesize, 'ask')
        limit = 100
        if filesize > 10:  # arbitrary
            try:
                shutil.copy(filename, f"{filename}.bak")
                if prnt:
                    # dbug(prnt)
                    # dbug(f"Copied [{filename}] to {filename}.bak", 'centered')
                    if prnt:
                        dbug(f"Copied [{filename}] to {filename}.bak")
            except Exception as e:
                if prnt:
                    dbug(f"Something went wrong with backup? Error: {e}")
        else:
            dbug(f"Not backing up as filesize: {filesize} is less than limit: {limit}")
            return None
    # """--== WIP Process ==--"""
    # dbug("WIP")
    # dbug(action)
    if action == "end":
        new_content_l = content_lines.append(new_line)
        if prnt:
            dbug(f"Added new_line: {new_line} to content...")
        # we are basically done here
    else:
        # """--== Check if pattern_found ==--"""
        # """--== find out if pattern_found first ==--"""
        for line in content_lines:
            # dbug(f"Looking for pattern: {pattern}\nline: {line}")
            try:
                if re.search(pattern, line):
                    # dbug(f"Winner found pattern: {pattern} in line: {line}")
                    pattern_found = True
                    break
            except Exception as Error:
                dbug(f"pattern: {pattern}\nline: {line}\nError: {Error}\nreturning...")
                return
        # dbug(f"pattern: {pattern}_found in line: {line}")
        # """--== EOB pattrn_found ==--"""
        # add to the end if not pattern_found and not ( replace or end)
        if not pattern_found:
            # action == end was taken care of above... to avoid going through this loop
            if action in ("either"):
                # dbug("Adding new_line to new_content_l")
                content_lines.append(new_line)
                new_content_l = content_lines
                if prnt:
                    dbug(f"Added new_line as pattern: {pattern} was not found: {new_line} to content...")
        else:  # pattern_found == True
            for line in content_lines:
                # dbug(f"Now checking line: {line}")
                if re.search(pattern, line):
                    # dbug(f"Pattern: {pattern} matches line: {line}")
                    # before
                    if action in ("delete", "del") and new_line == "":
                        # dbug(f"Eliminating line: {line}")
                        continue
                    if action in ("before"):
                        # dbug(action)
                        new_content_l.append(new_line)
                        new_content_l.append(line)
                        # dbug(f"Just added new_line: {new_line} and line: {line}")
                    # after
                    if action in ("after"):
                        new_content_l.append(line)
                        new_content_l.append(new_line)
                    # either or replace 
                    if action in ("either", "replace"):
                        if prnt:
                            dbug(f"Replacing line: {line} with {new_line}")
                        new_content_l.append(new_line)
                else:
                    if prnt:
                        dbug(f"Appending line: {line}")
                    new_content_l.append(line)
            if prnt:
                dbug(f"Added new_line: {new_line} to content...")
    # """--== SEP_LINE ==--"""
    # prepare new_conent for file write if filename not None
    if filename is not None and write_b:
        new_content = "\n".join(new_content_l)
        new_content.rstrip("\n")  # get rif of an ending "\n"
        # dbug(f"We would write new_content to filename: {filename}")
        if isempty(new_content):
            dbug("Nothing to write... returning...")
            return None
        if ask:
            if askYN(f"Shall we overwrite filename: {filename} with new content len(new_content): {len(new_content)}?", "y", centered=center_b):
                dbug(new_content)
                writing_file = open(filename, "w")
                writing_file.write(new_content)
                writing_file.close()
                if prnt:
                    dbug(f"File: {filename} has been ovverwritten")
        else:
            writing_file = open(filename, "w")
            writing_file.write(new_content)
            writing_file.close()
            if prnt:
                dbug("File: {filename} has been ovverwritten")
        if prnt:
            printit(f"Linenum: {linenum} line: {line} was replaced in {filename}", centered=center_b, shadow=shadow_b)
        # """--== SEP_LINE ==--"""
    # printit(new_content_l, 'boxed', title="debugging Returning new_content_l", footer=dbug('here'))
    # dbug("check check check", 'ask')
    if lst:
        # dbug(f"Returning: new_content_l[:10]: {new_content_l[:10]}")
        return new_content_l
    else:
        if isempty(new_content):
            new_content = "\n".join(new_content_l)
            new_content.rstrip("\n")  # get rif of an ending "\n"
        # dbug(f"Returning new_content: {new_content}")
        return new_content
    dbug("Did we get here - we should not have")
    # return con\bobtents
    # ### def add_or_replace(filename, action, pattern, new_line, backup=True): ### #

# alias
add_replace = add_or_replace



# ###############################################
def regex_col(file_lines, pat="", col=7, sep=""):
    # ###########################################
    """
    purpose: regex for a pattern in a word|column
        file_lines can be a filename or lines (list)
    returns: lines where pat matches col number word ie words[col]
    notes:    col starts at 0 to be consistent with coding standards
    """
    if isinstance(file_lines, list):
        lines = file_lines
    else:
        # assume it is a filename
        with open(file_lines) as f:
            lines = f.readlines()
    ret_lines = []
    # """--== SEP_LINE ==--"""
    for line in lines:
        # dbug(f"chkg line: {line}")
        if sep != "":
            words = line.split(sep)
            dbug(words)
        else:
            words = line.split()
        if len(words) > col:
            if re.search(pat, words[col]):
                ret_lines.append(line)
    # printit(ret_lines)
    return ret_lines
    # ### EOB def regex_col(pat="",col=7,sep=""): ### #


# #####################
def rootname(filename, *args, **kwargs):
    # #################
    """
    purpose: returns the root name of a full filename (not path, no extension)
    input: filename: str
    options:
        - base: bool         # returns simple basename only
        - full_base:_bool    # returns absolute path w/basename only
        - dir: bool          # return just the absolute path w/o the basename.ext
    returns: ROOT_NAME: str
    """
    # """--== Config ==--"""
    dir = arg_val(['dir'], args, kwargs, dflt=False)
    base = arg_val(['base', 'basename'], args, kwargs, dflt=False)
    full_base = arg_val(['fbase', 'fbasename', 'full_base', 'full_basename'], args, kwargs, dflt=False)
    # """--== Validation ==--"""
    if isempty(filename):
        return
    # """--== Convert ==--""" #
    if isinstance(filename, list) and len(filename) == 1:
        filename = filename[0]
    # """--== SEP_LINE ==--"""
    if not isinstance(filename, str):
        dbug(f"{filename=} must be a string... {called_from('verbose')}")
        return
    REALNAME = os.path.realpath(filename)
    DIRNAME = os.path.dirname(REALNAME)
    FULL_BASENAME = os.path.splitext(REALNAME)[0]
    BASENAME = os.path.basename(REALNAME)
    ROOTNAME = os.path.splitext(BASENAME)[0]
    if dir:
        return DIRNAME
    if base:
        return BASENAME
    if full_base:
        return FULL_BASENAME
    else:
        return ROOTNAME


# #################################
def islol(my_lol, *args, **kwargs):
    # #############################
    """
    purpose: quick and dirty test for a variable to see if it is a list of lists
    requires:
        - my_lol: anything=None
    options:
        - prnt: bool=False
        - roc: bool=False  # further tests to see if all the "rows" have the same number of elems as the first row
    returns: bool
    notes:
        - WIP
        - 20260402-0746
    """
    # """--== Config ==--""" #
    prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    roc_b = arg_val(['roc', 'rac', 'rows'], args, kwargs, dflt=False)
    # """--== Init ==--""" #
    rtrn = False
    # """--== Process ==--""" #
    if all([isinstance(row, list) for row in my_lol]) and all([all([isinstance(elem, (str, int, float, bool, dict)) for elem in row]) for row in my_lol]):  # <-- good magic happens here
        rtrn = True
        if roc_b:
            if all([len(row) == len(my_lol[0]) for row in my_lol]):
                dbug(f"This appears to be rows of columns {rtrn=}", prnt=prnt)
            else:
                dbug(f"This does NOT appear to be rows of columns {rtrn=}", prnt=prnt)
                rtrn = False
    # """--== Returning ==--""" #
    # dbug(f"{my_lol=} {rtrn=}", prnt=prnt)
    return rtrn
    # ### EOB def islol(my_lol, *args, **kwargs): ### #


# ###################################
def data_type(data, expected="", *args, **kwargs):
    # ###############################
    """
    purpose: determine data type
    requires: data
    options:
        - expected: str|list|tuple     # will return True of False
    returns: str | bool
    useage:
        dtype = data_type(data)
        if dtype in ('dod', 'lod'):
            do_something() 
        or
        if data_type(data, ('lod', 'dod')):
            do_something()
    notes:
        One of these strings will be returned (if not using expected option where a True or False will be returned)
        - str         # yes, a simple string (consider in might have newline chars in it)
        - file        # an existing filename (subset of str)
        - sqlite_file # subset of fname (subset of file)
        - csv_file    # subset of fname (subset of file that endswith(".csv")
        - dat_file    # subset of fname (subset of file that endswith(".dat")
        - json        # a json string (subset of str)
        - los         # list of strings - a simple list
        - block       # this is a subset of a list of strings in that every string is the same (nocode-see parse_codes('xxx', 'nclen')) length; actually a subset of los
        - lol         # list of lists - commonly rows of columns
        - lolols      # list of lists-of-lists - commonly a collection of list-of-lists
        - lob         # list list with every sublist is a "block" <--blocks is a list of strings that are all the same length... be careful here... false positives are a real possibility
        - lod         # list of dictionaries with the same structure
        - loD         # list of dictionaries with different structures
        - lom         # list of mixed element types
        - numpy       # a numpy type
        - df          # a DataFrame
        - dov         # a simple dictionary of keys and values - dict of values
        - dod         # dictionary of dictionaries
        - doD         # dictionary of dictionaries of different sizes
        - dol         # dictionary of lists
        - dom         # dictionary of mixed value types
        - class       # a "class" object
        - int         # an integer of course
        - float       # a float number of course
        - number      # this is a number string eg '4' or '4.0'
    """
    # """--== Local Imports ==--"""
    # from gtoolz import isempty
    if 'pandas' in sys.modules:
        import pandas as pd
    # """--== Debugging ==--"""
    # dbug(f"{called_from('v')} {data=}")
    # dbug(type(data))
    # dbug(data)
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'show', 'verbose'], args, kwargs, dflt=False)
    expected = kvarg_val(["expected", "expected_val"], kwargs, dflt=expected)
    # ddbug(f"expected: {expected}")
    if expected == 'prnt':  # in case the user forgets that expected is the second arg
        prnt = True
        expected=""
    else:
        prnt = arg_val(['prnt', 'print', 'show', 'verbose'], args, kwargs, dflt=False)
    # dbug(prnt)
    block_b = arg_val(['block', 'blk', 'block_b'], args, kwargs, dflt=False)  # what does this do?
    # """--== Convert ==--"""
    if not isempty(expected) and isinstance(expected, str):
        # dbug(f"expected: {expected} gets pupulated as a list here")
        expected = [expected]
    # """--== Validation ==--"""
    if isempty(data):
        if not isempty(expected):
            return False
        else:
            # dbug(f"Provided data: {data} must not be empty... called_from: {called_from()}")  #  and be a list or a dictionary... type(data): {type(data)}")
            return "empty"
    # """--== Init ==--"""
    # ddbug(f"{data=} {called_from('v')}", 'ask')
    dtype = None
    # this_dtype = type(data).__name__  # yes, __name__ is needed here to get the data type as a name
    # ddbug(inspect.isclass(data))
    # ddbug(f"{this_dtype=}")
    # if "class" in str(this_dtype):
    # """--== SEP_LINE ==--""" #
    # dbug(data, 'ask')
    # ddbug(f"{dtype=} {data=} {called_from('v')}")
    # Ensure we are checking a flat list of individual items, NOT a 2D matrix
    if isinstance(data, list) and len(data) > 0 and not isinstance(data[0], (list, tuple)):
        if all([isnumber(elem) for elem in data]):
            new_l = []
            for x in data:
                if isinstance(x, (int, float, str)): # Drop 'list' from here too!
                    new_l.append(str(x))
            data = new_l
    # if isinstance(data, list) and all([isnumber(elem) for elem in data]):
    #     # dbug("fix a list for analyzing - make sure all elems are str")
    #     new_l = []
    #     for x in data:
    #         if isinstance(x, (int, list, float, str)) :
    #             new_l.append(str(x))
    #     data = new_l
    # ddbug(f"{data=} {called_from('v')}", 'ask')
    # if isinstance(data, list):
    #     if all([isinstance(elem, list) for elem in data]):
    #         dbug("so far this is a list of list)")
    #         for elem in data:
    #             if isinstance(elem, list) and all([isinstance(item, list) for item in elem]):
    #                 dbug(f"this could be a chunked lol or a  lolols  {called_from('v')}", 'ask')
    #                 dtype = 'lolols'
    #                 return dtype
    # """--== SEP_LINE ==--""" #
    # ddbug(f"{data=} {called_from('v')}", 'ask')
    # ddbug(f"{dtype=} {data=} {called_from('v')}")
    # if all([isinstance(elem, (float, int)) for elem in data]):
       # dbug("WINNER")
    # askYN()
    if isinstance(type(data), type):
        if not isinstance(data, (bool, list, str, dict, tuple)):
            # ddbug(f"{type(data)=}")
            # ddbug(f"{data=} this is kludgy but oh well... data must be a class of {type(data)=}")
            dtype = "class"
    # ddbug(f"dtype: {dtype} {called_from()}")
    # ddbug(f"{dtype=} {data=} {called_from('v')}", 'ask')
    # """--== Process ==--"""
    if isinstance(data, bool):
        # dbug(f"Found a bool {data=}")
        dtype = 'bool'
    # ddbug(f"{dtype=} {data=} {called_from('v')}")
    # dbug(f"starting to process data type for data: {data} {called_from()}")
    # ddbug(f"{dtype=} {data=} {called_from('v')}", 'ask')
    if isnumber(data):
        dtype = type(data).__name__
        # dbug(f"{data=} {type(data)=} {type(data).__name__=}", 'ask')
        if isinstance(data, str):
            dtype = ("str","number")
    if isinstance(data, str) and dtype is None:
        # dbug(f"tstg {data=} str {called_from('v')}", 'ask')
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
            r'localhost|' # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if re.match(url_pattern, data):
            dtype = ("str","url")
            # dbug(f"{dtype=} {called_from('v')}")
        # ddbug(data, 'ask')
        if file_exists(data):
            # dbug(f"Found file {data}")
            dtype = 'file'
            cmd = f"file {data}"
            # dbug(cmd)
            out = run_cmd(cmd)
            # dbug(out)
            if "empty" in out:
                dtype = ("str","file","empty_file")
                # dbug(dtype)
            if "SQLite" in out:
                dtype = ("str","file","sqlite_file")
            if data.endswith(".csv"):
                dtype = ("str","file","csv_file")
            if data.endswith(".dat"):
                dtype = ("str","file","dat_file")
        else:
            if not dtype:
                # ddbug(f"Did not find a filename for data: {data} dtype: {dtype} {called_from('verbose')}")
                dtype = 'str'
                # we need to test to see if this ia json data
                # ddbug("testing for json syntax")
                try:
                    import json
                    json.loads(data)
                    dtype = ("str","json")
                    # ddbug(f"r: {r}")
                except Exception:
                    # ddbug("Not json worthy")
                    dtype = 'str'  # dtype remains str of unknown subtype so far - needs research
    # ddbug(f"{dtype=} {data=} {called_from('v')}", 'ask')
    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(data, (pd.DataFrame,pd.core.series.Series)):
            dtype = "df"
    # ddbug(f"{dtype=} {data=} {called_from('v')}", 'ask')
    if isinstance(data, dict):
        dtype = 'dom'  # dictionary of mixed
        # vals = list(data.values())
        # dbug(vals)
        if all(map(lambda x: isinstance(x, (str, int, float, list)), list(data.values()))):
            dtype = 'dov'  # dict of values
        if all(map(lambda x: isinstance(x, dict), list(data.values()))):
            dtype = 'dod'
            last_len = 0
            for k,v in data.items():
                my_len = len(v)
                if last_len == 0:
                    last_len = my_len
                if my_len == last_len:
                    continue
                else:
                    dtype = 'doD'
                    # dbug(f"{RESET}problem my_len: {my_len} last_len: {last_len} dtype: {dtype}")
                    break
        if all(map(lambda x: isinstance(x, list), list(data.values()))):
            dtype = 'dol'
            # if len(data) == 1:
            #     dbug(len(data))
            #     first_value = next(iter(data.values()))
            #     if all([isinstance(my_elem, dict) for my_elem in first_value]):
            #         dtype = 'dol1d'  # dictionary with list of 1
            #         dbug(f"This is a special circumstance dtype: {dtype} {called_from('verbose')} - it is a list with one element that is a list of dictionaries... you may want to use 'next(iter(data.vaules()))'  here...")
            return dtype
    # ddbug(f"{dtype=} {data=} {called_from()}", 'ask')
    # this is a special case where website return json data is a string == "[]"
    if isinstance(data, str):
        # ddbug(f"data: *{data}* {called_from('verbose')}")
        if data == "[]":
            dtype = "empty"
            return dtype
    if isinstance(data, list):
        # ddbug(f"{len(data)=} {data=}")
        data = [item for item in data if not isempty(str(item))]  # cleanup data getting rid of empty items
        if len(data) == 0:
            dtype = "empty"
            # ddbug(f"{len(data)=} {data=}")
            return dtype
        for my_x in data:
            # ddbug(f"{my_x=} {called_from('verbose')}")
            my_x_len = parse_codes(my_x, 'nclen')
            # if nclen(my_x) < 1:
            if my_x_len < 1:
                # dbug(f"This is empty or all ansi code {nclen(my_x)=} problem {len(my_x)=} {repr(my_x)=} len(data): {len(data)} dtype: {dtype} dat_type(my_x): {data_type(my_x)}")
                continue
        # ddbug(f"{data=} {called_from('v')} so far: {dtype=}", 'ask')
        dtype = 'lom'  # list of mixed until proven otherwise
        # ddbug(f"{data=} {called_from('v')} so far: {dtype=}", 'ask')
        # dbug(f"dtype: {dtype} {called_from('verbose')}")
        # if all(isinstance(item, list) for item in data if not isempty(item)):
        if all(isinstance(item, list) for item in data):
            # ddbug(f"every elem of the list is a list {called_from()}" 'ask')
            # dtype = 'lol'  # start with this in this section
            # """--== WIP ==--"""
            # dbug(f"so far {dtype=}")
            if all([data_type(item, 'lol') for item in data]):
                dtype = 'lolols'
                # ddbug(f"dtype: {dtype} {called_from('v')}", 'ask')
            # """--== SEP_LINE ==--"""
            if len(data) < 2:
                # dbug("only has one (or 0) elems")
                # if all(nclen(line) == nclen(data[0][0]) for line in data[0]):
                if all(parse_codes(line, 'nclen') == parse_codes(data[0][0], 'nclen') for line in data[0]):
                    # dbug("This is a list containing a single block (los with all having the same length)")
                    dtype = "lob"
                else:
                    if isinstance(data[0], str):
                        # dbug(f"this data[0]: {data[0]} dtype: {dtype} is a list with a single string {called_from()}")
                        dtype = "los"
                    block_b = False
            else:
                # dbug(f"len(data): {len(data)} is this a list of blocks (blocks here means all the strings are the same length (nclen <-- no-color or no-code length) {called_from()}")
                for block in data:
                    # if not isempty(block):
                        # printit(data, 'prnt', 'boxed', title="debugging", footer=dbug('here')) 
                    # else:
                       # # dbug("found an empty 'block")
                       # continue
                    for line_s in block:
                        block_b = True  # until proven false below
                        # if isempty(line_s):
                        #     # dbug("found an empty line_s")
                        #     continue
                        # if not nclen(line_s) == nclen(block[0]):
                        line_s_len = parse_codes(line_s, 'nclen')
                        block0_len = parse_codes(block[0], 'nclen')
                        # if not nclen(line_s) == nclen(block[0]):
                        if not line_s_len == block0_len:
                            # dbug(f"line_s: {line_s} is not == nclen(block[0]): {nclen(block[0])} block[0]: {block[0]}")
                            block_b = False
                            break
                    if not block_b:
                        break
                if block_b:
                    dtype = "lob"
                else:
                    # dbug(f"{block_b=} {dtype=}")
                    if all([isinstance(item, list) for item in data]):
                        for item in data:
                            if all([isinstance(elem, (str, int, float)) for elem in item]) and len(item) == len(data[0]):
                               # dbug("good so far")
                               lol_b = True
                            else:
                               lol_b = False
                            # dbug(lol_b)
                        if lol_b:
                            dtype = 'lol'
        else:
            if all([isnumber(elem) for elem in data]):
                block_b = False
                dtype = 'lon'
                # ddbug(f"{dtype=} {called_from('v')}")
            # dbug(nclen(data))
            # printit(data[0])
            # dbug(repr(data[0]))
            # dbug(data_type(data[0]))
            # my_lens = []
            # for item in data:
            #     item_len = nclen(item)
            #     my_lens.append(item_len)
            # ddbug(my_lens)
            # dbug('ask')
        # ddbug(f"{dtype=} {called_from('v')}", 'ask')
        if all(isinstance(item, dict) for item in data):
            dtype = 'lod'
            first_keys = list(data[0].keys())
            if not all(list(item.keys()) == first_keys for item in data):
                # dbug("all dictionaries but of different structures")
                dtype = 'loD'
            # ddbug(f"{data}")
            # ddbug(f"dtype:{dtype}", 'ask')
        # if all([isinstance(item, (str, int, float)) for item in data]):
        if all([isinstance(item, str) for item in data]):
            # ddbug(f"Every item in data: {data} is a string or number {called_from('v')}")
            dtype = 'los'
            if all([isnumber(elem) for elem in data]):
                block_b = False
                dtype = 'lon'
                # ddbug(f"{dtype=} {called_from('v')}")
            else:
                # if len(data) > 1 and all([nclen(i) == nclen(data[0]) for i in data]):
                if len(data) > 1 and all([parse_codes(i, 'nclen') == parse_codes(data[0], 'nclen') for i in data]):
                    # dbug(f"this is a list of equal (nc)length strings, ie a block or box {called_from()}")
                    dtype = 'block' # this is a list of equal (nc)length strings, ie a block or box 
    if 'ndarray' in str(type(data)):
        # dbug("This remains untested 20240902... if it works remove this message.")
        dtype = 'numpy'
    # ddbug(f"dtype: {dtype} called_from: {called_from()}")
    if len(expected) > 0:
        # ddbug(f"dtype: {dtype} called_from: {called_from()}")
        rtrn_b = False
        if dtype in expected:
            rtrn_b = True
        # ddbug(f"Returning rtrn_b: {rtrn_b} dtype: {dtype} expected: {expected} called_from: {called_from()}")
        return rtrn_b
    if prnt:
        dbug(f"Returning dtype: [yellow!]{dtype}[/] {called_from('verbose')} for data: {data}")
    # """--== debugging ==--"""
    # if dtype in 'loD':
        # ddbug(f"returning dtype: {dtype} {called_from('verbose')}")
    # """--== Returning ==--"""
    # ddbug(f"returning dtype: {dtype} {called_from('verbose')}")
    return dtype
    # ### EOB def data_type(data, *args, **kwargs): ### #


# ##############
def maxof(my_l, *args, **kwargs):
    # ##########
    """
    purpose: returns length of longest member of a list (after escaped codes are removed)
    required: list or list_of_lists (lol)
    options:
        - length|len|max_len|elem_len: bool       # default=True longest length is returned
        - height|rows|max_height|row_len: bool    # default=False largest number of elements in list
                                                    (typically the number of lines in a list of strings)
        - elems: bool                             # default=False in a list of lists this will rerturn
                                                    the greatest number of elements in each member of a list (see note below)
        - lst: bool                               # default=False returns a list which will be the max length(s) or height(s) of each elem in a list
    returns: 
        - int max length of eleemes
    note: saves me from having to look up how to do this all the time and works with lists or lists of list
        - sometimes I need to know the number of rows in cols (lol of rows in cols
                ie: cols_lol = [row1, row2], [row1, row2, row3], [row1, row2]] ... maxof(cols_lol): 3
    """
    # """--== Debugging ==--"""
    # dbug(called_from())
    # dbug(my_l)
    # dbug(args)
    # dbug(kwargs)
    # """--== Validate ==--"""
    if isempty(my_l):
        # dbug(my_l)
        return 0
    # """--== Config ==--"""
    height_b = arg_val(["height", "max_height", "rows", "row_len"], args, kwargs, dflt=False)
    length_b = arg_val(["length", "max_len", "len", 'elem_len', 'elems', 'cols'], args, kwargs, dflt=False)
    elems_b = arg_val(["number", "num", "items", "elems", "max_num_elems", 'max_elems'], args, kwargs, dflt=False)
    lst_b = arg_val(['lst', 'list'], args, kwargs, dflt=False)
    # """--== Init ==--"""
    max_height = 0
    max_len = 0
    max_elems = 0
    max_lens = []
    max_heights = []
    elems = []
    # """--== Process ==--"""
    # if islol(my_l):
    # dbug(f"{my_l=} {called_from('verbose')}")
    if data_type(my_l, ['lol']):
        # dbug(f"this is an lol height_b: {height_b} length_b: {length_b} elems_b: {elems_b} lst_b: {lst_b}", 'ask')
        if elems_b:
            # dbug(elems_b)
            height_b = True
            length_b = False
            elems_b = True
        if not height_b and not length_b:
            if not elems_b:
                length_b = True
        # """--== is lol ==--"""
        # eg height is number of rows, length is number of cols
        for elem in my_l:
            if isinstance(elem, list):
                max_len = max(parse_codes(x, 'nclen') for x in elem)
                # dbug(elem)
            elems.append(len(elem))
            # if islos(elem):
            if data_type(elem, 'los'):
                # dbug(elem)
                # max_len = max(nclen(x) for x in elem)
                max_len = max(parse_codes(x, 'nclen') for x in elem)
                max_lens.append(max_len)
                max_heights.append(len(elem))
            else:
                # dbug(elem)
                max_lens.append(len(elem))
            if height_b:
                if len(elem) > max_height:
                    max_height = len(elem)
        # dbug(f"this is an lol height_b: {height_b} length_b: {length_b} elems_b: {elems_b} lst_b: {lst_b} max_elems: {max_elems} max_len: max_elems")
        # dbug(f"my_l is an lol max_len: {max_len}")
    else:
        # """--== not lol ==--"""
        length_b = True
        if isinstance(my_l, list):
            # max_len = max(nclen(elem) for elem in my_l)
            max_len = max(parse_codes(elem, 'nclen') for elem in my_l)
            # dbug(max_len)
        if isinstance(my_l, str):
            my_l_len = parse_codes(my_l, 'nclen')
            # max_len = nclen(my_l)
            max_len = my_l_len
        # dbug(f"type(my_l): {type(my_l)} must NOT be lol ...max_len: {max_len}")
    if elems_b:
        # dbug(f"for ref max_height: {max_height} max_len: {max_len}i max_heights: {max_heights}")
        rtrn = max_elems
    if height_b:
        # dbug(max_height)
        rtrn = max_height
    if length_b:
        rtrn = max_len
    if lst_b:
        if length_b:
            rtrn = max_lens
        if height_b:
            rtrn = max_heights
        if elems_b:
            rtrn = elems
    # dbug(f"Returning max_len: {max_len}")
    return rtrn


# #################################
def gblock(msgs_l, *args, **kwargs):
    # #############################
    """
    purpose: justifies using nclen all strngs in msgs_l and maximizes each string length to the longest string - all lines will be the same length (nclen - no-color len)
    required: msgs_l: list   # list of strings
    options:
        - height: int
        - length | width: int
        - pad: str                          # char to use for fill - the color option will affect this pad/fill character
        - position=1: str | list | int  # eg: 'right center' or 'left top' (default) or [top, left] or 'middle bottom' or 1 (default) or 5 or 9 ... etc
                      left              | center             | right
                    +-------------------+--------------------+--------------------+
            top     |  1                |   2                | 3                  |
                    | ['top','left']    |['top','center']    | ['top','right']    |
            ------  +-------------------|--------------------|--------------------+
            middle  |  4                |   5                | 6                  |
                    | ['middle','left'] | [middle','center'] | ['middle','right'] |
            ------  +-------------------|--------------------|--------------------+
            bottom  |  7                |   8                | 9                  |
                    | ['bottom','left'] | [bottom','center'] | ['bottom','right'] |
            ------  +-------------------|--------------------|--------------------+
        - centered: bool
        - boxed: bool
        - color: str
        - box_color: str
        - title: str
        - footer: str
        - txt_center: int                 # this is important as it will center from the top txt_center number of lines within the created block
                                          # typically you would use txt_center=99 to center all the lines within the block
    returns: 
        - a list of lines all the same length with strings justified - a new box with the dimensions given
    notes:
        - this function is designed place a block/box in a position in a larger box or to combine rows and columns into a type of dashboard.
        - described above is the original design ie: to handle one box (list of strings) 
        - this (below) enhancement if fragile and not fully tested but is great for building dashboards
             I have modified/enhanced this to allow for building columns and or rows *but* it is difficult to describe how it works
        Best to give examples - assumes box(x) below is a list of strongs of the same length
        gblock([box1, box2])                  # will build two columns into one block
        gblock([box1, [box2, box3]])          # will build one row of two columns with the second column having 2 rows (box2 over box3)
        gblock([[box1], [box2]])              # will build two rows - box1 over box2
        gblock([[box1, box2], [box3, box4]])  # will build two columns with the first column holding box1 over box2 while the second column will hold box 3 over box4
    """
    # TODO: add col_limit to truncate elems if needed
    # """--== debugging ==--"""
    # dbug(f"{funcname()} {called_from()}")
    # dbug(msgs_l[:2])
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    width = kvarg_val(["width", "length", "w"], kwargs, dflt=0)
    height = kvarg_val(["height", "h", 'rows'], kwargs, dflt=0)
    position = kvarg_val(["just", "justify", "position", "pos"], kwargs, dflt=1)  # can be str | list
    positions = kvarg_val(["positions"], kwargs, dflt=[1, 2, 3])  # list ... applies when msgs_l is actually an list of lists of boxes
    pad = kvarg_val(["pad", "fill"], kwargs, dflt=" ")
    prnt = arg_val(["prnt", "print", "show"], args, kwargs, dflt=False)
    boxed_b = arg_val(['boxed', 'box'], args, kwargs, dflt=False)
    centered_b = arg_val(['centered', 'center'], args, kwargs, dflt=False)
    txt_center = kvarg_val(["text_center", "text_centered", "lines_centered", "txt_center", 'txt_centered'], kwargs, dflt=0)
    title = kvarg_val(['title'], kwargs, dflt="")
    footer = kvarg_val(['footer'], kwargs, dflt="")
    box_color = kvarg_val(["box_color", 'box_clr'], kwargs, dflt="white! on black")
    color = kvarg_val(["color", 'clr'], kwargs, dflt="")
    centered = arg_val(["centered", 'ccentered'], args, kwargs, dflt=False)
    # possiblilities: left, center, right, top, middle, bottom
    # """--== Validations ==--"""
    if msgs_l is None:
        dbug(f"Returning... nothing to work with.... msgs_l: {msgs_l}")
        return
    for elem in msgs_l:
        if elem is None:
            dbug(f"This list contains some elements that are None... elem: {elem}   Returning...")
            return
    my_group = []
    group = msgs_l
    # if any([islos(x) for x in group]) and islol(group):
    if any([data_type(x, 'los') for x in group]) and data_type(group, 'lol'):
        # dbug("This must be a group of cols as some elems are a list of strings (los)")
        for x in group:
            # if islol(x):
            if data_type(x, 'lol'):
                # found a column with more than one box so lets treat it that way
                x = gblock(sum(x, []))  # , txt_center=txt_center)
                my_group.append(x)
            else:
                my_group.append(x)
        msgs_l = my_group
    # """--== Init ==--"""
    pad = str(pad)
    justify = ""
    vjust = 'top'
    pad = gclr(color) + pad  # this is used for fill
    # if all([islol(elem) for elem in msgs_l]):
    if all([data_type(elem, 'lol') for elem in msgs_l]):
        # dbug("This must contain rows")
        new_msgs_l = []
        for elem in msgs_l:
            # dbug(f"This must be a row ... elem: {elem} ")
            # if all([islos(item) for item in elem]):
            if all([data_type(item, ('lol')) for item in elem]):
                # dbug("This must be a list containing a list of strings (los)")
                # convert this to rows by adding them on top of each other
                if len(elem) == 1:
                    for item in elem:
                        new_msgs_l += item
                else:
                    new_msgs_l += gcolumnize(elem)
            else:
                # dbug(islos(elem))
                dbug(f"Problem elem: {elem}", 'ask')
        msgs_l = new_msgs_l
    # """--== Convert ==--"""
    if isinstance(msgs_l, str) and "\n" in msgs_l:
        msgs_l = msgs_l.split("\n")
    # """--== SEP_LINE ==--"""
    # if islol(msgs_l):
    dtype = data_type(msgs_l)
    # dbug(dtype)
    # if data_type(msgs_l, 'lol'):
    if dtype in ('lol', 'lob'):
        if dtype in ('lob'):
            # dbug(f"dtype: {dtype} side by side boxes - ie a row")
            for box in msgs_l:
                # printit(box)
                row = gcolumnize(msgs_l, lenght=width)  # , height=height)
                lines = printit(row, boxed=boxed_b, centered=centered_b, title=title, footer=footer, box_color=box_color, color=color, prnt=prnt, txt_center=txt_center)
            # dbug("returning my_lines")
            return lines
        else:
            # dbug(f"dtype: {dtype} Must be 'stacked' lines or boxes or more complicated...")
            new_msgs_l = []
            for item in msgs_l:
                # dbug(len(item))
                # dbug(type(item))
                item_dtype = data_type(item)
                if item_dtype in ('los'):
                    # dbug(item_dtype)
                    item = gblock(item)
                # else:
                    # dbug(item_dtype)
                # printit(item, 'boxed', title="item", footer=dbug('here'))
                new_msgs_l.append(item)
            my_lines = gcolumnize(new_msgs_l, prnt=prnt, title=title, footer=footer, centered=centered_b)
            # printit(new_msgs_l, 'boxed', title="debugging boxed", footer=dbug('here'))
            # dbug(f"stop {called_from()}", 'ask')
            return(new_msgs_l)
            return my_lines
        # dbug("Treating msgs_l as a lol ... not a simple list? ", 'ask' )
        # if any([islol(elem) for elem in msgs_l]):
        if any([data_type(elem, ('lol')) for elem in msgs_l]):
            dbug(f"dtype: {dtype} at least one elem is an lol {called_from()}")
            #     # dbug(f"Rows of Columns?")
            #     # if any([islol(elem) for elem in msgs_l]):
            #     if 1:
            my_lines = []
            for msg in msgs_l:
                dbug(msg)
                if len(msg) > 1:
                    my_lines += gblock(gcolumnize(msg), length=width)  # , height=height)
            my_lines = printit(my_lines, boxed=boxed_b, centered=centered_b, title=title, footer=footer, box_color=box_color, color=color, prnt=prnt, txt_center=txt_center)
            dbug("returning my_lines")
            return my_lines
        else:
            dbug(f"dtype: {dtype} side by side boxes - ie a row")
            for box in msgs_l:
                printit(box)
                row = gcolumnize(msgs_l, lenght=width)  # , height=height)
                lines = printit(row, boxed=boxed_b, centered=centered_b, title=title, footer=footer, box_color=box_color, color=color, prnt=prnt, txt_center=txt_center)
                return lines
        # """--== SEP_LINE ==--"""
        dbug("Do we ever get here?", 'ask')
        if len(positions) == 0:
            positions = [1, 2, 3]  # a number for each box, default is left top for all
        # make 3 columns
        col_left_len = 0    # find length of anything in 1,4,7  ie  left column
        col_center_len = 0
        col_right_len = 0
        col1_box = []
        col2_box = []
        col3_box = []
        boxes_lol = msgs_l
        length = width
        for box in boxes_lol:
            if maxof(box) > length:
                length = maxof(box)
            if len(box) > height:
                height = len(box)
        # dbug("length: {length} height: {height}", 'ask')
        for box_num, box in enumerate(boxes_lol):
            # this middle col will fill any empty space in the (2, 5, 8) block below
            pos = positions[box_num]
            if int(pos) in (1, 4, 7):
                col1_box = gblock(box, length=col_left_len, height=height, position=pos, pad=pad)
            if int(pos) in (3, 6, 9):
                col3_box = gblock(box, length=col_center_len, height=height, position=pos, pad=pad)
            if int(pos) in (2, 5, 8):
                # prepare to fill any empty space
                my_length = length - (col_left_len + col_right_len)
                col2_box = gblock(box, length=my_length, height=height, position=pos, pad=pad)
        # dbug(txt_center)
        row_box = printit(gcolumnize([col1_box, col2_box, col3_box]),
                         width=length,
                         height=height,
                         boxed=boxed_b,
                         centered=centered_b,
                         title=title,
                         footer=footer,
                         box_color=box_color,
                         color=color,
                         prnt=prnt,
                         txt_center=txt_center)
        msgs_l = row_box
        max_len = maxof(msgs_l)
        screen_width = get_columns() - 4
        if max_len >= screen_width:
            dbug(f"It appears that the requested content length {max_len} exceeds theavailable terminal screen width {screen_width}")
            # dbug(msgs_l, 'lst')
            return None
        return row_box
    # """--== SEP_LINE ==--"""
    # dbug(f"Now place the box in the proper position msgs_l: {msgs_l}")
    if isinstance(msgs_l, str):
        msgs_l = [msgs_l]
    msg_len = maxof(msgs_l)
    msg_height = len(msgs_l)
    max_len = msg_len
    max_height = msg_height
    if width > msg_len:
        max_len = width
    if height > msg_height:
        max_height = height
    # deal with position being either str | list
    if str(position) == "1":
        position = ['top', 'left']
    if str(position) == "2":
        position = ['top', 'center']
    if str(position) == "3":
        position = ['top', 'right']
    if str(position) == "4":
        position = ['middle', 'left']
    if str(position) == "5":
        position = ['middle', 'center']
    if str(position) == "6":
        position = ['middle', 'right']
    if str(position) == "7":
        position = ['bottom', 'left']
    if str(position) == "8":
        position = ['bottom', 'center']
    if str(position) == "9":
        position = ['bottom', 'right']
    if 'left' in position:
        justify = 'left'
    if 'center' in position:
        justify = 'center'
    if 'right' in position:
        justify = 'right'
    # """--== build left, center, or right justified "box" ==--"""
    # """--== now build horizontal justification ==--"""
    new_msgs = []
    for msg in msgs_l:
        msg_len = parse_codes(msg, 'nclen')
        # diff = max_len - nclen(msg)
        diff = max_len - msg_len
        fill = pad * diff
        if justify == 'left':
            try:
                msg = str(msg) + fill
            except Exception as Error:
                dbug(Error)
        if justify == 'center':
            fill = pad * (diff // 2)
            msg = fill + msg + fill
            msg_len = parse_codes(msg, 'nclen')
            # if nclen(msg) != max_len:
            if msg_len != max_len:
                # diff = max_len - nclen(msg)
                diff = max_len - msg_len
                msg += pad * diff
        if justify == 'right':
            fill = pad * diff
            msg = fill + msg
        new_msgs.append(msg)
        msgs_l = new_msgs
    # """--== deal with position being either str | list """
    if 'top' in position:
        vjust = 'top'
    if 'middle' in position:
        vjust = 'middle'
    if 'bottom' in position:
        vjust = 'bottom'
    # """--== now build vertical justification ==--"""
    diff = max_height - msg_height
    above_lines = 0
    below_lines = 0
    if vjust == 'top':
        below_lines = diff
    if vjust == 'bottom':
        above_lines = diff
    if vjust == 'middle':
        above_lines = diff // 2
        below_lines = diff - above_lines
    blank_line = pad * max_len
    top_lines = [blank_line] * above_lines
    bottom_lines = [blank_line] * below_lines
    new_lines2 = top_lines + msgs_l + bottom_lines
    # dbug(new_lines2)
    # """--== SEP_LINE ==--"""
    max_len = maxof(new_lines2, 'len')
    screen_width = get_columns() - 4
    # dbug(f"max_len: {max_len} screen_width: {screen_width}")
    if max_len >= screen_width:
        # dbug(f"It appears that the requested content length {max_len} exceeds the (approx) terminal screen available width {screen_width}", 'boxed', 'centered')
        # new_lines2 = wrapit(new_lines2, length=screen_width)
        new_lines2 = gwrap(new_lines2, length=screen_width)
        for ln in new_lines2:
            ln_len = parse_codes(ln, 'nclen')
            # if nclen(ln) > screen_width:
            if ln_len > screen_width:
                dbug(f"This line is too long: [{ln}]")
    # """--== SEP_LINE ==--"""
    rtrn_lines = None
    if not isempty(new_lines2):
        rtrn_lines = printit(new_lines2, boxed=boxed_b, centered=centered, title=title, footer=footer, box_color=box_color, color=color, prnt=prnt, pad=pad, txt_center=txt_center)
    # dbug("Returning rtrn_lines")
    return rtrn_lines
    # ### EOB def gblock(msgs_l, *args, **kwargs): ### #


# #####################################################
def find_file_in_dirs(filename, dirs_l=[], prnt=False):
    # #################################################
    """
    purpose: this is for future use as something like find_file_in_dirs(filename, dirs_l)
    notes: if dirs_l is empty it defaults to ["./"]
    """
    found_file = ""
    if dirs_l == []:
        dirs_l = ["./", os.path.dirname(__file__)]
    poss_dirs = dirs_l
    # dbug(poss_dirs)
    for dir in poss_dirs:
        # dbug(dir)
        if dir.endswith("/"):
            tst_for_file = dir + filename
        else:
            tst_for_file = dir + "/" + filename
        # dbug(f"Looking for: {tst_for_file}", "ask")
        if os.path.isfile(tst_for_file):
            found_file = tst_for_file
            if prnt:
                printit(f"Found file: {found_file} ...", "center")
            break
    return found_file
    # ### EOB def find_file_in_dirs(filename, dirs_l=[], prnt=False): ### #


def usr_input(prompt="Your input: ", *args, **kwargs):
    """
    # consider usr_update() first!
    purpose: allow user input with editing - see usr_update() as that is likely what you want
    options::
        - prompt: str = "Your input: "
        - edit: bool
        - dft: str
        - centered: bool
        - shift: int
        - update: dict
        - length: int = 0       # all lines will display with the same length
        - timeout: int      # question will timeout after declared seconds with the default as the answer
    returns: edit or input data as str or dict if update option
    Notes: 
        - this function is typically called by usr_update()
        - see usr_update()
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(args)
    # dbug(kwargs)
    # """--== Import ==--"""
    # import readline
    # """--== Config ==--"""
    centered_b = arg_val(["centered", "center", "cntr"], args, kwargs, dflt=False)
    # dbug(f"{centered_b=} {called_from=}")
    shift = kvarg_val(["shift", "shft"], kwargs, dflt=0)
    # dbug(shift)
    prompt = kvarg_val("prompt", kwargs, dflt=prompt)
    default = kvarg_val(["dflt", 'default'], kwargs, dflt=None)
    edit_b = arg_val(["edit", "editable", 'edt'], args, kwargs, dflt=False)  # TODO eliminate this option - not working
    update = kvarg_val(["update"], kwargs, dflt={})
    max_val_len = kvarg_val(["max_v", "max_v_len", "max_val", "max_val_len"], kwargs, dflt=0)
    noedit_b = arg_val(["noedit", "no_edit", "noinput", "no_input"], args, kwargs, dflt=False)
    timeout = arg_val(["timeout"], args, kwargs, dflt=0)
    # """--== Validate ==--"""
    if edit_b and default is None and len(update) == 0:
        dbug("Edit has been invoked but there is no default|dflt which is needed or make default='' ...")
        return None
    # dbug(f"edit: {edit} update: {update} centered: {centered_b} shift: {shift} default={default}")
    # """--== Init ==--"""
    if prompt is None:
        prompt = "none"
    # if default is None or default == "":
        # default = " "
    default = str(default)
    edit_text = default
    if edit_b and len(update) == 0:
        # dbug("We are here ... why?")
        if prompt == "Your input: ":
            dbug(f"Change prompt? why? {edit_text=}")
            prompt = "Edit as needed: "
        # edit_text = default
        if edit_text == "":
            return ""
    # """--== Process ==--"""
    # dbug(f"{prompt=} {centered_b=} {shift=}")
    # """--== standard input ==--"""
    # if not edit_b and len(update) == 0:
    if len(update) == 0:
        # dbug(f"prompt: {prompt} shift: {shift} max_val_len: {max_val_len} nclen(default): {nclen(default)}")
        default_msg = ""
        if len(default) > 0:
            default_msg = f"[{default:>{max_val_len}}]: "
            if prompt.endswith(": ") and not edit_b:
                prompt = prompt.rstrip(": ") + default_msg
        if centered_b:
            shift = shift - (max_val_len // 2)
            # dbug(f"{prompt=} {shift=} {centered_b=} {len(prompt) - len(prompt.lstrip())=}",'ask')
            prompt = centered(prompt, shift=shift)
            # dbug(f"{prompt=}")
        if noedit_b:
            dbug('no edit {prompt=} {centered_b=} {prompt=} {shift=}')
            printit(prompt)
            dbug("We just ran printit({prompt=}",'ask')
            return default
        if edit_b:
            response = cinput(prompt, 'nocenter', timeout=timeout, dflt=default)
        else:
            response = cinput(prompt, 'nocenter', timeout=timeout) or default
        # dbug(response,'ask')
    # """--== update dictionary values ==--"""
    if len(update) > 0:
        # dbug(f"hmmm this calls usr_update {centered_b=}")
        response = usr_update(update, centered=centered_b, shift=shift, edit=edit_b)
        # response = usr_update(update, shift=shift, edit=edit_b)
        return update
    # """--== edit default input ==--"""
    # changed cinput - dont need this anymore
    # # dbug(f"edit: {edit_b} update: {update} centered: {centered_b} shift: {shift} default={default}")
    # if edit_b:
    #     # dbug(f"edit: {edit_b} update: {update} centered: {centered_b} shift: {shift} default={default} noedit_b: {noedit_b} prompt: {prompt}")
    #     readline.set_startup_hook(lambda: readline.insert_text(edit_text))
    #     # note: This hook allows you to execute custom code just before the Readline library prints the first prompt and begins reading input for a new line. None removes the hook
    #     shift = shift - (max_val_len // 2)
    #     response = ""
    #     try:
    #         if centered_b:
    #             # ruleit(center=True)  # debugging
    #             prompt = centered(prompt, shift=shift)[0]
    #         if noedit_b:
    #             dbug("yes, you may want to display the question but not allow an edit...")
    #             # dbug(prompt + default)
    #             printit(prompt + default)
    #             return default
    #         dbug(prompt)
    #         response = cinput(prompt, timeout=timeout)
    #         dbug("stop",'ask')
    #     finally:
    #         if edit_b:
    #             # dbug(f"why {edit_b=}.. readline.set_startup_hook ????")
    #             readline.set_startup_hook(None)  # resetting readline
    #             # note: This hook allows you to execute custom code just before the Readline library prints the first prompt and begins reading input for a new line. None removes the hook
    # """--== determine default ==--"""
    if not edit_b and len(default) > 0:
        # dbug(f"edit: {edit_b}  providing dflt: {default} if empty response: {response} default={default}")
        if response is None:
            response = ""
        if default is None:
            default = ""
        default_len = parse_codes(default, 'nclen')
        # if response == "" and nclen(default) > 1:
        if response == "" and default_len > 1:
            response = default
    # """--== Returning ==--""" #
    return response
    # ### EOB def usr_input(*args, **kwargs): ### #


# ###########################################
def usr_update(my_d, *args, **kwargs):
    # #######################################
    """
    purpose: given a dict, and a list of keys to change - allow user update(s) to values in  my_d dictionary
        go through the list of keys to fix and prompt user for new value, present the current value as default
    args: my_d: dict        # dict to have updated
    options:
          - fix: list       # default=[]      - list of keys to prompt user for change; if empty, use all the my_d keys
          - centered: bool  # default=False   - whether to center everything on the screen
          - no_edits: list  # default=[]      - list of keys that are presented but not editable - note: case sensitive exact match is required here
          - quit: bool      # default=False   - whether to immediately quit on an entry of "q" or "Q", or "quit"
          - textedit: list  # default=[]      - the list contains any keys that you want to use for your external text editor to modify or input the value
                                                This option is useful for very long text value changes.
          - timeout: int    # question will timeout after declared seconds with the default as the answer
          - col_limit: 0    # limits how much shows for value
          - editable: bool=False  # presents every valuse as an editable default
    returns: my_d (with user updates)
    Notes:
        - what is in the passed dict values is what will be presented as the default.
        - aka: user_edit()
        - normally usr_update() calls this function
        - this function calls usr_input(), ie: it superceded usr_input
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    # max_size = kvarg_val(["max", " max_size"], kwargs, dflt=40)
    fix_l = kvarg_val(["fix", "fix_list", "fix_l", "to_fix", "fix_lst", "update", "to_update", "update_lst"], kwargs, dflt=[])
    edit_b = arg_val(["edit", "editable", "edit_txt", "edit_text"], args, kwargs, dflt=False)  # TODO omitting this option
    centered_b = arg_val(["center", "centered", "cntr"], args, kwargs, dflt=False)
    noedits_l = kvarg_val(["noedits", "no_edits", "excludes", 'except', 'noedit', 'no_edit', 'skip'], kwargs, dflt=[])  
                # which keys will not be allowed editing of any form but will be presented/displayed
    quit_b = arg_val(["quit", "q", "exit"], args, kwargs, dflt=False)
    chunks_b = arg_val(["chunks"], args, kwargs, dflt=False)
    texteditor_l = kvarg_val(["texteditor", "tedit", "tedit_l", "tedits","textedit"], kwargs, dflt=[])
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    timeout = arg_val(['timeout'], args, kwargs, dflt=0)
    # dbug(centered_b)
    # col_limit = arg_val(["col_limit"], args, kwargs, dflt=0)
    # """--== Init ==--"""
    texteditor_l = [dequote(elem) for elem in texteditor_l]
    if quit_b:
        printit("Accept, Update or q)uit", centered=centered_b)
    prompt = "Please enter new value for: "
    scr_cols = get_cols()
    fix_d = {}
    if len(fix_l) == 0:
        # fix_l was not supplied so make it equal to list(my_d.keys())
        fix_l = list(my_d.keys())
    for k in fix_l:
        # put in values from supplied my_d
        fix_d[k] = my_d[k]  # give fix_d[k] the value from my_d[k]
    # dbug(texteditor_l)
    non_textedit_d = {k:v for k,v in fix_d.items() if k not in texteditor_l}
    # dbug(non_textedit_d)
    max_k = maxof(list(fix_d.keys()))
    # max_v = maxof(list(fix_d.values()))
    max_v = maxof(list(non_textedit_d.values()))
    # if col_limit == 0:
        # col_limit = scr_cols - nclen(prompt) - max_k - 55 # arbitrary
    # dbug(col_limit)
    if (max_k + max_v) > scr_cols:
        # dbug(max_k)
        # if chunks_b or max_v > col_limit:
        if chunks_b:
            prompt_len = parse_codes(prompt, 'nclen')
            # max_v = scr_cols - (nclen(prompt) + 10)  # arbitrary
            max_v = scr_cols - (prompt_len + 10)  # arbitrary
        else:
            dbug(f"Not enough room on the screen... consider the 'chunks' option to break up large values into smaller chunks or use textedit option. {called_from('v')}")
            return
    new_d = my_d.copy()
    # """--== Process ==--"""
    for k, v in fix_d.items():
        # dbug(f"k: {k} v: {v}")
        if v == "":  # this actually will get taken care of in usr_input but doing it anyway
            v = " "
        # dbug(f"chkg is k: {k} in noedits_l: {noedits_l}")
        if k in noedits_l:
            noedit = True
            # dbug(f"making noedit: {noedit} k: {k}")
        else:
            noedit = False
            # dbug(f"k: {k} not found in noedits_l: {noedits_l}")
        if k in texteditor_l:
            (f"Found {k=} in {texteditor_l=}")
            # import texteditor
            if ask_b:
                if askYN(f"Do you want to use an external editor to provide a value for {k}? :", "y", centered=centered_b): 
                    v = tedit(v)
            else:
                v = tedit(v)
            noedit = True
        # dbug(f"chkg nclen(v): {nclen(v)}")
        v_len = parse_codes(v, 'nclen')
        if v_len > max_v and chunks_b:  # or v_len > col_limit:
            # dbug(prompt)
            printit(v, 'boxed', title=f"This line will be broken into chunks (len: {max_v}) for editing.", footer=dbug('here'), centered=centered_b)
            # my_lines = wrapit(v, length=max_v)
            my_lines = gwrap(v, length=max_v)
            lines_d = {}
            for num, line in enumerate(my_lines):
                # dbug(f"adding line: {line} to lines_d")
                lines_d[num] = line
            # new_lines = usr_update(lines_d, 'edit', quit=quit, centered=centered_b)
            new_lines = usr_update(lines_d, 'edit')
            # dbug(new_lines)
            ans = " ".join(list(new_lines.values()))
            new_d[k] = ans
            printit(ans, 'boxed', title="New replacement added", footer=dbug('here'), centered=centered_b)
            continue
        my_prompt = prompt + f"[{k:<{max_k}}]: "
        v = str(v)[:max_v]
        # dbug(f"{my_prompt=}")
        ans = usr_input(edit=edit_b, prompt=my_prompt, centered=centered_b, dflt=v, max_v=max_v, noedit=noedit, timeout=timeout)
        ans = str(ans)
        if quit_b:
            if ans in ("q", "Q", "quit"):
                # do_close(center=True, box_color="red on black")
                break
        new_d[k] = ans
    # dbug(f"Returning my_d: {new_d}")
    return new_d
    # ### EOB def usr_update(my_d, fix_l=[], *args, **kwargs): ### #


# #######################################
def tedit(input_txt="", *args, **kwargs):
    # ###################################
    """
    purpose: do a text edit in an editor and return edited text
    requires:
        - input_txt
    options:
        - editor: str="vim"                # editor can be your choice
        - tmp_file: str="/tmp/tedit.tmp"   # this is the declared "temp" file for editing - it is not removed
        - ask: bool=False                  # ask the user before forking to the editor - allows the user to bypass this edit
        - centered: bool=False
    returns: edited text post editor()
    notes:
        - used by usr_update()
        - WIP
    """
    from gtoolz import arg_val, run_cmd
    # """--== Config ==--"""
    input_txt = arg_val(["input_txt", "input", "text"], args, kwargs, dflt=input_txt)
    editor = arg_val(["editor"], args, kwargs, dflt="vim")
    tmp_file = arg_val(["tmp_file", "temp", "temp_file"], args, kwargs, dflt="/tmp/tedit.tmp")
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    centered_b = arg_val(['centered', 'centered', 'center', 'cntr'], args, kwargs, dflt=False)
    # """--== SEP_LINE ==--"""
    if ask_b:
        if askYN(f"Do you want to use editor: {editor} to edit the input text? ", "y", centered=centered_b):
            pass
        else:
            return input_txt
    # """--== do edit and read file ==--"""
    with open(tmp_file, "w") as f:
        f.writelines(input_txt)
    # dbug(f"tmp_file: {tmp_file} written to")
    cmd = f"{editor} {tmp_file}"
    # dbug(f"now run_cmd({cmd})")
    run_cmd(cmd, 'fork')
    # edit_file(tmp_file)
    # dbug(f"now read tmp_file: {tmp_file}")
    with open(tmp_file, 'r') as f:
        new_lines = f.readlines()
    # """--== return new text ==--"""
    # dbug(new_lines)
    return new_lines
    # ### EOB def tedit(input_txt="", *args, **kwargs): ### #


# #############################################
def remap_keys(data, remap_d, *args, **kwargs):
    # #########################################
    """
    purpose: remaps keys names AND can select only the key,value pairs you want (in the order specified) (ie option: 'mapped_only')
    requires:
        - data: lol          # typically a list of rows with each row = columns values - first row will be key names (ie column names) data will be converted to an lol if possible
        - my_d: dict|lol     # a dictionary of key-value pairs or a df (DataFrame which will get converted to an lol ie: cnvrt(df)
        - remap_d: dict      # a dictionary holding mapping for orig_keys: to new_key pairs
        - remap_d: list      # will reorder the dictionary in accordance with the list order
        - rtrn_type: str     # 'dict', 'dov' or 'lol'
    options:
        - mapped_only: bool=True  # returns a dictionary of only the remap_d key:value pairs if True (default) "all" or "full" will retutn all keys (changed and unchanged)
        - rnd: int           # rounds out numbers to rnd scale
    returns: 
        - my_d (remapped and optionally selected pairs)
    notes: 
        - remap_d should be a dict {orig_key: new_key, ...} but can be a list only (assumes and sets mapped_only=Truei ie: replaces)
        - This is a very useful function that allows you to pick/select columns from a given dictionary in your order and rename any keys as well
        - I use this a lot when I download financial data from a web api
    created:
        - 20220423 gwm
        - TODO rename this remap_data
    """
    # dbug(data)
    # dbug(len(remap_d))
    # """--== Config ==--"""
    mapped_only_b = arg_val(["mapped_only", "mapped", 'selected', 'selected_only'], args, kwargs, opposites=['replace', 'replace_only', 'rplc', 'rplc_onyl', 'all', 'full'],  dflt=True)
    # dbug(mapped_only_b)
    # rnd = kvarg_val("rnd", kwargs, dflt=0)
    # ask_b = arg_val(['ask'], args, kwargs, dflt=False)
    rtrn_type = arg_val(['ask'], args, kwargs, dflt="")
    # """--== Validate ==--"""
    if isempty(data):
        # dbug(f"data {data} appears to be empty and {remap_d=} ... called_from: {called_from()} returning...")
        # return  # don't return as it might be that a dictionary is just getting initialized
        if remap_d:
            # dbug(f"This is a special case where data is empty but we got a remap_d - so just build an appropriate dictionary with all values = '-'")
            my_dict = {key: "-" for key in list(remap_d.keys())}
            return my_dict
        else:
            dbug(f"data {data} appears to be empty and remap_d appears empty... called_from: {called_from()} returning...")
    if isempty(remap_d):
        dbug("Consider running bld_remap(trgt_data, src_data) which guides you trough creating remap_d maybe helpful for large data sets... returning...")
        return
    # """--== Init ==--"""
    new_lol = []
    dtype = data_type(data)
    # dbug(dtype)
    # """--== Convert ==--"""
    if not rtrn_type:
        # dbug(f"setting rtrn_type to dtype:{dtype}")
        rtrn_type = dtype
    if isinstance(remap_d, list):
        new_d = {}
        for elem in remap_d:
            new_d[elem] = elem
        remap_d = new_d
        mapped_only_b = True
    # dbug(data)
    # dbug(len(data))
    # dtype = data_type(data)
    # dbug(dtype)
    # dbug(data,'ask')
    my_data = cnvrt(data)
    # dbug(my_data,'ask')
    # dbug(remap_d)
    # dbug(my_data)
    # my_data_dtype = data_type(my_data)
    # dbug(my_data_dtype)
    # gtable(my_data, 'prnt', title="cnvrt(data)", footer=dbug('here'))
    # dbug('ask')
    # dbug(my_d_dtype)
    if isinstance(my_data, list) and isinstance(my_data[0], dict):
        # dbug(my_d_dtype)
        new_l = []
        for elem in my_data:
            new_l.append(remap_keys(elem, remap_d))
        # dbug(f"Retturning new_l: {new_l}")
        return(new_l)
    # newkeys_l = list(remap_d.values())
    # dbug(remap_d)
    # """--== Process ==--"""
    if dtype in ('lol') or 1:
        # dbug("starting")
        if data_type(my_data, ['lol', 'lob']):  # it should be because it got cnvrt()'d above 
            # dbug(mapped_only_b)
            orig_colnames = my_data[0]
            if mapped_only_b:
                for row_num,  row in enumerate(my_data):
                    # dbug(f"row: {row} row_num:{row_num}")
                    new_row = []
                    for k, v in remap_d.items():
                        # dbug(f"k:{k} v:{v} orig_colnames:{orig_colnames}")
                        if row_num == 0:
                            # dbug(f"add colname v:{v} regardless of whether it is in the orig data or not")
                            newcol_val = v
                        if k in orig_colnames:
                            # dbug(f"k:{k} was found in orig_colnames:{orig_colnames}")
                            if row_num > 0:
                                newcol_val = row[orig_colnames.index(k)]
                            # dbug(f"appending newcol_val:{newcol_val} to new_row")
                            new_row.append(newcol_val)
                        else:
                            # dbug(f"add col that isnt in the orig but is in remap_d k:{k} v:{v}")
                            if row_num == 0:
                                new_row.append(v)
                            else:
                                new_row.append("none")
                    # dbug(f"appending new_row:{new_row} row_num:{row_num}")
                    new_lol.append(new_row)
                    # dbug(new_lol[0])
                # new_lol = newkeys_l
                # new_lol = fixlol(new_lol)
            else:
                # dbug("mapped_only_b must be false so we want to get everything just remap colnames")
                for k, v in remap_d.items():
                    if k in orig_colnames:
                        orig_colnames[orig_colnames.index(k)] = v
                new_lol = [orig_colnames]
                new_lol.extend(my_data[1:])
                # dbug(new_lol[0])
        # gtable(new_lol, 'prnt', 'hdr', title="returning new_lol", footer=dbug('here'))
        # dbug(rtrn_type)
        if rtrn_type in ('dom', 'dov', 'dod'):
            # dbug(new_lol)
            my_d = cnvrt(new_lol, rtrn_type='dov')
            # t1 = gtable(my_d, 'noprnt', 'hdr', title=f'debugging cnvrt mapped_only_b:{mapped_only_b} len(my_d):{len(my_d)} this is what would be',
                        # footer=dbug('here'), pivot=True, colnames=["key","val"])
            # kvcols(my_d, cols=3, prnt=True, title="debug returning my_d", footer=dbug('here'))
            return my_d
        # dbug(new_lol)
        # gtable(new_lol, 'prnt', 'hdr', title='debugging', footer=dbug('here'), pivot=True) 
    return new_lol
    # ### EOB def remap_keys(my_data, remap_d, *args, **kwargs): ### #


# #####################################################
def bld_plug_map(trgt_data, src_data, *args, **kwargs):
    # #################################################
    """
    purpose: asks for user input to build a dictionary of {src_colname: trgt_colname, ...}
    requires:
        - trgt_data: dict
        - src_data: dict
    options:
        - plug_map: dict
    returns: constructed dictionary ie "plug_map" for plugmation()
    notes:
        - use trgt_data.update(remap_keys(src_data, plug_map)) now trgt_data is fully updated
    """
    from gtoolz import cls, cinput
    # """--== Config ==--"""
    plug_map_d = arg_val(['plug_map', 'plug_map_d'], args, kwargs, dflt={})
    dbug(plug_map_d)
    # """--== Process ==--"""
    action_msg_box = boxed(["Syntax: value FROM SRC colname TO TRGT value colname", "Select the source column holding the value you want to be inserted and also the Target colname where the value will be replaced.",
                           "Delimiter can be a space, comma, semi-colon, or a colon",
                            "For example: Entering 1,1 will take value for first (1) Source Colname choice and insert that value into Target Column list first (1)"],
                           width=40, bxclr="white! on black", title="Action", footer=dbug('here'))
    while True:
        cls()
        trgt_box = gtable(trgt_data, footer=dbug('here'), pivot=True, colnames=["Trgt Key", "Current Value"], hdr=True, title="Original trgt_data", cols=2)
        src_box = gtable(src_data, footer=dbug('here'), pivot=True, colnames=["Src Key", "Value"], hdr=True, title="Proposed src_data", cols=2)
        gcolumnize([src_box, trgt_box], 'prnt', 'centered')
        trgt_selections_lol = [["Choice", "Trgt Colnames"]]
        for choice, col in enumerate(list(trgt_data.keys()), start=1):
            trgt_selections_lol.append([choice, col])
        trgt_selections_lol.append([choice + 1, "[red]Create Colname[/]"])
        trgt_cols_box = gtable(trgt_selections_lol, 'noprnt', hdr=True, cols=2, title="Target", footer=dbug('here'))
        # """--== SEP_LINE ==--"""
        src_selections_lol = [["Choice", "Src Colnames"]]
        for choice, col in enumerate(list(src_data.keys()), start=1):
            src_selections_lol.append([choice, col])
        src_cols_box = gtable(src_selections_lol, 'noprnt', hdr=True, cols=2, title="Source", footer=dbug('here'))
        plug_map_l = [f"{k}->{v}" for k,v in plug_map_d.items()]
        action_box = boxed(["[yellow! on black]   src --> trg   [/]"] + plug_map_l, txt_cntrd=99, title="Current Plug Map", footer=dbug('here'), bxclr="yellow! on black!")
        # printit(action_box, 'centered')
        double_action_box = boxed(action_msg_box + action_box, 'noprnt', title="Action Info", footer=dbug('here'), txt_cntrd=99)
        # dbug('ask')
        gcolumnize([src_cols_box, double_action_box, trgt_cols_box], 'prnt', centered=True)
        # trgt_selection = gselect(trgt_selections, prompt="This trgt key will be used to plug a new value from the source data: ", colnames=["Choice", "Column Name"])
        # """--== sep_line ==--"""
        ans = cinput("Enter: source colname choice, target colname choice\nFor example: 1,1\nYour selections [q]uit: ")
        # dbug(ans)
        if ans in ("q", "Q"):
            if askYN("Are you sure you are finished?: ", "n", 'centered'):
                break
            else:
                continue
        try:
            src_indx, trgt_indx = re.split('[,;: ] *', ans)
        except Exception:
            dbug("The input did not meet expected syntax, try again...", 'centered', 'ask')
            continue
        src_selected = src_selections_lol[int(src_indx)][1]
        # dbug(f"trgt_indx: {trgt_indx} len(trgt_selections_lol): {len(trgt_selections_lol)}")
        if int(trgt_indx) + 2 > len(trgt_selections_lol):
            trgt_selected = cinput("Assuming you want this value to go into a new trgt colname; please enter new colname: ")
        else:
            trgt_selected = trgt_selections_lol[int(trgt_indx)][1]
        # dbug(f"{src_selected}->{trgt_selected}", 'ask')
        plug_map_d[src_selected] = trgt_selected
        # dbug(plug_map_d)
    return plug_map_d


# ###############################
def gplot(data, *args, **kwargs):
    # ###########################
    """
    purpose: simplied plot tool - eliminates dataframes (which I swear is the bane of my existence)
    requires: 
        - data: lol|str(filename)    # cnvrt is run on data if it is not an lol, assumes first column is a time series
    options:
        - display: bool=True    # whether to show the plot or not
        - title: str="My Title"
        - footer: str=""
        - text: str             # adds text in a box on the display
        - selected: list=[]     # all columns if blank
        - mvgavg: bool          # adds moving avgs for 50 and 200
        - minmax: bool          # annotates min and max values
        - endpoints: bool       # annotates start and end values
        - hlines: dict          # draws and labels a horizonal line eg: {'target': 50, 'cost': 25}
        - savefile: str         # filename to save plot image eg: 'myplot.png'
        - show: bool            # defualt=True whether to display or show() the plot to the screen
    returns:
        - converted data as an lol
    notes:
        - WIP
        - no subplots (yet)
        - if you ssh to a server and need to build a graph add this to the top of your python script
            # 
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            #
    """
    """--== debug ==--"""
    # dbug(f"{called_from()} {data[:30]=}" )
    # === local imports === #
    # import matplotlib
    # matplotlib.use('Agg')  # for headless servers
    # matplotlib.use('TKAgg')  # Or 'GTK3Agg' if you have PyQt installed use: export MPLBACKEND=GTK4Agg
    # matplotlib.use('GTK4Agg')  # Or 'GTK3Agg' if you have PyQt installed use: export MPLBACKEND=GTK4Agg
    import matplotlib.pyplot as plt
    # plt.use('GTK3Agg')  # untested
    # Check if it worked
    # assert(plt.get_backend() == 'GTK3Agg')
    import matplotlib.dates as mdates
    import matplotlib.gridspec as gridspec
    # import numpy as np
    from datetime import datetime
    # === Config === #
    show = arg_val(['show', 'display'], args, kwargs, dflt=True)
    show = arg_val(['prnt', 'print', 'show', 'display'], args, kwargs, dflt=True, opposite=['noshow', 'noprnt', 'nodisplay'])
    title = arg_val(['title'], args, kwargs, dflt="My Title")
    footer = arg_val(['footer'], args, kwargs, dflt="")
    selected = arg_val(['selected', 'selections', 'select'], args, kwargs, dflt=[])
    box_text = arg_val(['text', 'box_text', 'bxtxt'], args, kwargs, dflt="")
    hlines = arg_val(["trgt", "target", 'strike', "line", "hline", "hlines"], args, kwargs, dflt={})  # must be a dictionary
    mavg = arg_val(['mavg', 'ma', 'mvgavg', 'mavgs', 'mvgavgs'], args, kwargs, dflt=False)
    subplot_name = arg_val(['subplot'], args, kwargs, dflt=False)
    savefile = arg_val(['savefile', 'save', 'saveto', 'save_to', 'file', 'fname', 'filename'], args, kwargs, dflt="")
    minmax = arg_val(['minmax', 'maxmin', 'mm', 'min', 'max', 'hl', 'max_min', 'min_max'], args, kwargs, dflt=False)
    endpoints = arg_val(['endpoints', 'startend', 'startstop', 'endpts'], args, kwargs, dflt=False)
    ask_b = arg_val(['ask', 'ask_b'], args, kwargs, dflt=None)  # TODO WIP
    # dbug(f"{ask_b=} {args=} {kwargs=} {called_from('v')}", 'ask')
    # === local function(s) === #
    if not show:
        import matplotlib
        matplotlib.use('Agg')  # for headless servers
    # #################################################
    def calculate_moving_average(col_data, window_size):
        # #############################################
        if len(col_data) < window_size:
            raise ValueError("Data length must be greater than or equal to the window size")
        first_val = col_data[0]
        moving_averages = [first_val] * (window_size - 1)
        # dbug(moving_averages)
        for i in range(len(col_data) - window_size + 1):
            window = col_data[i: i + window_size]
            column_values = [float(val) for val in window]
            average = sum(column_values) / window_size
            moving_averages.append(average)
        return moving_averages
        # ### EOB def calculate_moving_average(col_data, window_size): ### #
    # === Validate === #
    if isempty(data):
        dbug(f"Submitted data: [{data}] appears to be empty {called_from('verbose')}... returning...")
        return
    # === Convert === #
    orig_dtype = data_type(data)
    # dbug(orig_dtype)
    if 'lol' in orig_dtype:
        # dbug(f"{data=} {called_from('v')}")
        data = cnvrt(data)
        # dbug(data[:3])
        # dtype = data_type(data)
    # ### dtfmt fixes ### #
    dtfmt = dt_fmt(data[1][0])  # returns None if not a recognized date format
    if dtfmt:
        data = [row for n,row in enumerate(data) if get_dfmt(row[0], prnt=False) == dtfmt or n == 0]
    else:
        dbug("Unrecognized date-time format..")
        return
    # ### end of dtfmt fixes ### #
    # dbug(f"{dtfmt=} {dtype=} {data=} {called_from('v')}")
    # === Init === #
    # subplot_name = "1209c"  # debugging
    # footer = "my footer"  # debugging
    colnames = data[0]
    if isempty(selected):
        selected = colnames[1:]
    rows = data[1:]
    # """--== remove rows with non-numbers in selected colnames ==--""" #
    # this seems to work 20250528
    # dbug(len(rows))
    orig_rows_len = len(rows)
    this_colnames = rows[0]
    for col in selected:
        # dbug(col)
        if col in selected[1:]:  # first col may be a date/time 
            indx = colnames.index(col)
            rows = [row for row in rows if isnumber(row[indx])]
    rows.insert(0,this_colnames)
    rslt_rows_len = len(rows)
    if rslt_rows_len < orig_rows_len:
        bad_rows = orig_rows_len - rslt_rows_len
        dbug(f"We removed {bad_rows} bad_rows of data", centered=centered)
    # gtable(rows, 'prnt', 'hdr', 'endhdr', title='debugging', footer=dbug('here'))
    # dbug(len(rows))
    # """--== EOB tst: remove rows with non-numbers in selected colnames==--""" #
    # === X Axis === #
    if dtfmt:
        try:
            dates = [datetime.strptime(str(row[0]), dtfmt) for row in rows]
        except Exception as Error:
            dbug(f"{dtfmt=} {Error=}")
            for row in rows:
                try:
                    dbug(f"{row[0]=} {datetime.strptime(str(row[0]), dtfmt)=}") 
                except Exception as Error:
                    dbug(f"{Error=} {dtfmt=} {row[0]=}")
    else:
        dates = [row[0] for row in rows]
    # === Y Plot lists === #
    col_d = {}
    subplot_l = []
    maxs_l = []
    mins_l = []
    # """--== SEP_LINE ==--""" #
    # dbug(selected)
    for n, col in enumerate(colnames[1:], start=1):
        # dbug(f"found {col=} in {selected=}")
        if col in selected:
            col_d[col] = [float(str(row[n]).replace(",","")) for row in rows if isnumber(row[n])]
            try:
                maxs_l.append(max(col_d[col]))
            except Exception as Error:
                dbug(f"{Error=} {col=} {col_d[col]=} You may need to 'clean' the data by removing some columns.... returning...")
                return
            mins_l.append(min(col_d[col]))
            # === Moving Averages === #
            if mavg:
                col_d['ma50'] = calculate_moving_average(col_d[col], 50)
                col_d['ma200'] = calculate_moving_average(col_d[col], 200)
        if col == subplot_name:
            subplot_l = [float(row[n].replace(",","")) for row in rows]
    top_plt_max = max(maxs_l)
    top_plt_min = min(mins_l)
    # === Establish figure and axes objects === #
    # figure size
    fig = plt.figure(figsize=(15, 8))
    if subplot_name:
        gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])
    else:
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 0])  # no subplot
    # top_plt = fig.add_subplot(2,1,1) # row , col (grid), pos
    top_plt = fig.add_subplot(gs[0])
    # top_plt.plot(,)
    # ax = plt.subplots(2, 1, figsize=(15, 8))  # rows, cols for subplots; width, height for both figure and axes objects
    plt.ticklabel_format(style='plain')  # gets rid of the le6 and fixes Y scale numbers but only affects top chart
    # == plot lines == #
    for col in list(col_d.keys()):
        top_plt.plot(dates, col_d[col], label=col)
    # """--== labels & title ==--"""
    # plt.xlabel("Time")
    plt.xlabel(colnames[0])
    plt.ylabel("values")
    plt.title(title)
    # """--== format & rotate dates ==--"""
    if dtfmt:
        # dbug(dtfmt)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Format x-axis dates
        plt.gcf().autofmt_xdate()  # Rotate date labels for better readability
    # else:
    # === hlines === #
    # hlines = {"tst": 1000000}
    if hlines:
        # dbug(hlines)
        diff = top_plt_max - top_plt_min
        v_offset = (diff/100)
        for k, v in hlines.items():
            # if not v: # if no value just skip
                # continue
            hline_label = f"{k}={v}"
            hline = float(v)
            if hline:
                # ymin, ymax = plt.gca().get_ylim()
                # diff = ymin - ymax
                # dbug(diff)
                # v_offset = ((ymax-ymin)/10)
                # v_offset = 0.1
                # dbug(v_offset)
                if float(hline) > 0:
                    max_val = max(col_d[col])
                    max_indx = col_d[col].index(max_val)
                    plot_l = [hline] * len(dates)
                    top_plt.plot(dates, plot_l , label=hline_label)
                    # plt.annotate(f'{hline_label}', xy=(dates[int(len(dates)/2)], hline), xytext=(5, v_offset), textcoords='offset points', ha='left', va='center',
                    # top_plt.annotate(f'{hline_label}', xy=(dates[max_indx], hline), xytext=(dates[max_indx], hline + v_offset), 
                    # dbug(dates[0])
                    top_plt.annotate(f'{hline_label}', xy=(dates[0], hline), xytext=(dates[0], hline + v_offset)) #, 
                        # arrowprops=dict(facecolor='black', arrowstyle='->'))
    # """--== Subplot ==--"""
    if subplot_name:
        # dbug(len(subplot_l))
        # bot_plt = fig.add_subplot(2,1,2)  # bot_loc, rowspan=1, colspan=1)
        bot_plt = fig.add_subplot(gs[1])  # bot_loc, rowspan=1, colspan=1)
        # bot_plt = plt.subplot2grid(grid, bot_loc, rowspan=1, colspan=1)
        bot_plt.fill_between(dates, subplot_l, label=subplot_name, color="blue", facecolor='grey')
        # bot_plt.plot(dates, subplot_l, label=subplot_name )  #, color="blue", facecolor='grey')
        bot_plt.legend(loc="upper right")
        # dbug("well we tried")
        plt.subplots_adjust(hspace=0.4)  # experimentally determined
    # === Annotate endpoints === #
    if endpoints:
        for col in list(col_d.keys()):
            top_plt.annotate(f'{col_d[col][-1]}', xy=(dates[-1], col_d[col][-1]), xytext=(5, 0),
                    textcoords='offset points', ha='left', va='center')
        for col in list(col_d.keys()):
            top_plt.annotate(f'{col_d[col][0]}', xy=(dates[0], col_d[col][0]), xytext=(-5, 0),
                    textcoords='offset points', ha='left', va='center')
    # === Annotate minmax === #
    # dbug(minmax)
    if minmax:
        # ymin, ymax = plt.gca().get_ylim()
        # dbug(ymin)
        # dbug(ymax)
        # v_offset = (ymax-ymin)/10
        # dbug(v_offset)
        # max_val = max(col_d[col])
        # min_val = min(col_d[col])
        diff = top_plt_max - top_plt_min
        v_offset = diff/10
        # dbug(v_offset)
        for col in list(col_d.keys()):
            if col.startswith("ma"):
                continue  # skip moving averages
            max_val = max(col_d[col])
            # dbug(max_val)
            max_indx = col_d[col].index(max_val)
            min_val = min(col_d[col])
            # dbug(max_val)
            min_indx = col_d[col].index(min_val)
            # dbug(max_indx)
            if subplot_name:
                box_text += f"max: {max_val} min: {min_val}\n"
            # else:
            if 1:
                top_plt.annotate(f'Max: ({max_val})', xy=(dates[max_indx], max_val), xytext=(dates[max_indx], max_val - v_offset),
                     arrowprops=dict(facecolor='black', arrowstyle='->'))
                min_val = min(col_d[col])
                # dbug(min_val)
                min_indx = col_d[col].index(min_val)
                # dbug(max_indx)
                top_plt.annotate(f'Min: ({min_val})', xy=(dates[min_indx], min_val), xytext=(dates[min_indx], min_val + v_offset),
                     arrowprops=dict(facecolor='black', arrowstyle='->'))
    # === add text box (using axes coordinates) === #
    if box_text:
        if isinstance(box_text, str):
            if "\\n" in box_text:  # sometimes this is what gets passed to us
                box_text = box_text.split("\\n")
        if isinstance(box_text, list):
            box_text = "\n".join(box_text)
        props = dict(boxstyle='round', facecolor='wheat', alpha=1.0)
        if box_text.endswith("\n"):
            box_text = box_text.rstrip("\n")
        top_plt.text(0.01, 0.97, box_text, transform=top_plt.transAxes, fontsize=10, verticalalignment='top', bbox=props)
    # === add grid lines === #
    top_plt.grid(True)
    if subplot_name:
        bot_plt.grid(True)
    # == add legend == #
    top_plt.legend(loc='upper center')
    top_plt.legend(loc='upper center')
    # === footer === #
    if footer:
        plt.figtext(0.5, 0.01, footer, ha='center', fontsize=11)
    # === pull the trigger save & show === #
    # plt.tight_layout()  # recommended for subplots
    if savefile: # NOTE!!!! this has to be called BEFORE plt.show !
          plt.savefig(f"{savefile}")
    if show:  # default is True
        plt.show()
    # dbug(ask_b)
    if ask_b:
        askYN()
    # == debug and return == #
    return data
    # == EOB def gplot(data, *args, **kwargs): == #


# ####################################
def quick_plot(data, *args, **kwargs):
    # ################################
    """n
    purpose: quick display of data in  a file or in dataframe
        displays a plot on a web browser if requested
    required: data: df | str (filename: csv or dat filename) | list (of lists)
    options:
        - centered: bool
        - title: str
        - footer: str
        - choose: bool             # invokes gselect multi mode to allow selections of columns to display in the plot (graph)
        - selections: list         # you can declare what columns to plot
        - web: bool                # displays to your browser instead of a plot figure
        - dat: bool | str          # I sometimes use a commented firstline for headers -
                                   # using 'dat' declares this to be true, if character is used ie dat=":"
                                   # then that will be used as the delimiter
        - type: str                # default=line, bar, barh, hist, box, kde, density, area, pie, scatter, hexbin
        - colnames: list | str     # default = [] if it is a str="firstrow" then the firstrow obviously will be treated as colnames
        - mavgs: bool              # 50 day and 200 day moving averages added to plot
        - box_text: str | list     # string or lines to add to a box in fuger default=""
        - subplot: str             # sub plot with area under filled using colname = subplot
        - save_file: str           # name of file to save the plot figure to.  default=""
        - delimiter: str           # assumes a filename for data (above) and use delimiter to seperate elements in each line of the file
        - hlines: dict             # dictionary eg: {"target": 44, "strike": 33, ...} can be one or several
        - pblines: bool            # pullback_lines - only useful for stock history charts
        - rnd: int                 # round numbers to int - only useful if show or prnt is invoked for gtable display (see option show | prnt)
        - show | prnt: bool        # shows/prints a limited (see tail option) amount of data in a table centered (for debugging or checking)
        - tail: int                # for the last n rows of the df default=15
        - fix: bool                # fix will convert all lines/rows to have same number of columns as the first line in a list of lists
    # returns: df
    returns:
        - lol  # list of rows each of which is a list of columns
    notes: 
        - if a filename is used as data it will get "purified" by removing all comments first (except the first line of a dat file.)
            tail, title and footer only affect the gtable if show is True
        - this function turns all column names into lower case to avoid choice or selection issues
        - TODO might add a "capitalize" option to make all colnames capitalized... 20240201
    notes:
        - this will be depracated for gplot()
    """
    # """--== debugging ==--"""
    # dbug(called_from())
    # dbug(data)
    # dbug(data[:3])
    # dbug(type(data))
    # dbug(f"type(data): {type(data)}")
    # dbug(args)
    # dbug(kwargs)
    # """--== Imports ==--"""
    import matplotlib.pyplot as plt
    import plotly.express as px
    # import pandas as pd
    # """--== prep ==--"""
    try:
        plt.close()  # close any plt window
        # plt.clf()  # clear and existing plots
    except Exception as Error:
        dbug(f"Problem with plt... Error: {Error}")
        return
    # """--== Config ==--"""
    show = arg_val(["show"], args, kwargs, dflt=False)
    show=1
    choose = arg_val(["choose", "multi", 'multiple'], args, kwargs, dflt=False)
    selections = kvarg_val(["selections", "select", "choices", "selected"], kwargs, dflt=[])
    selections = [selection.lower() for selection in selections]  # my preference and avoids case confusion later
    # dbug(f"selections: {selections} {called_from()}")
    title = kvarg_val("title", kwargs, dflt="")
    footer = kvarg_val("footer", kwargs, dflt="")
    tail = kvarg_val("tail", kwargs, dflt=15)
    centered_b = arg_val(["centered", "center"], args, kwargs, dflt=True)
    web_b = arg_val(['web', 'browser'], args, kwargs, dflt=False)
    colnames = kvarg_val(['colnames', 'col_names', 'columns'], kwargs, dflt=[])
    firstrow_b = arg_val(["firstrow", "first", "firstline"], args, kwargs, dflt=False)
    # dbug(colnames)
    # kind = kvarg_val(['kind', 'type', 'style'], kwargs, dflt='line')  # line, bar, barh, hist, box, kde, density, area, pie, scatter, hexbin
    dat = kvarg_val(["dat"], kwargs, dflt=False)
    dat = arg_val(["dat"], args, kwargs, dflt=dat)  # this needs to be here in combination w/above
    mavgs = arg_val(["mavgs", "mavg", "moving_avgs"], args, kwargs, dflt=False)
    box_text = kvarg_val(["box_text", 'box_txt', "text", "txt"], kwargs, dflt="")
    savefile = kvarg_val(["save", "savefile", "save_file"], kwargs, dflt="")
    hlines = kvarg_val(["trgt", "target", 'strike', "line", "hline", "hlines"], kwargs, dflt=0)  # must be a dictionary
    subplot = kvarg_val(["subplot", "sub_plot", "sub"], kwargs, dflt="")
    subplot = subplot.lower()  # this avoids case confusion later
    # dbug(subplot)
    pb_lines = arg_val(["pb_lines", "pblines", "pullback_lines", "plines"], args, kwargs, dflt=False)  # only useful for stock history charts
    delimiter = kvarg_val(["delim", "delimiter", "dlmtr"], kwargs, dflt=",")
    # index_b = arg_val(["index", "indexes", "idx"], args, kwargs, dflt=False)
    rnd = kvarg_val(["rnd", "round"], kwargs, dflt=0)
    fix_b = arg_val(['fix', 'fix_b'], args, kwargs, dflt=True)
    ask_b = arg_val(['ask'], args, kwargs, dflt=False)  # TODO WIP
    # """--== Inits ==--"""
    selections_l = []
    hline_name = "HLine"
    simple_list = False
    # """--== Convert to df ==--"""
    # dbug(data)
    # dbug(type(data), 'ask')
    # dtype = data_type(data, 'prnt')
    if 'pandas' not in sys.modules:
        import pandas as pd
    if isinstance(data, pd.DataFrame):
        df = data
        # dbug(df.head(2))
        # dbug(colnames)
        # dbug(df.info())
        src = "df"
    if isinstance(data, str):
        dbug(f"data: {data} is probably a path/filename")
        if file_exists(data):
            dbug("assuming it is a csv file")
            # df = pd.read_csv(data, thousands=',', comment="#", header=0, on_bad_lines='warn', engine='python', infer_datetime_format=True)
            # dbug(dat)
            # df = cat_file(data, 'df', 'hdr', dat=dat, nums=True, delim=delimiter, index=index)
            dbug(data)
            df = cat_file(data, 'df')
            dbug(df[:3])
            dat = False
            df = cat_file(data, 'df', 'hdr', dat=dat, nums=True, delim=delimiter, index=False)
            # dbug(df[:3])
            # dbug(df.info())
            src = f"File: {data}"
        else:
            dbug(f"file: {data} appears to not exist... returning")
            return
    # dbug(type(data), 'ask')
    if isinstance(data, dict):
        df = pd.DataFrame.from_dict(data)
        if colnames in ('firstrow', 'first_row', 'firstline', 'first_line'):
            colnames = data[0]
            data = data[1:]
        src = "df"
        # dbug(src)
    # dbug(colnames)
    if isinstance(data, list):
        # dbug(data)
        if not isinstance(data[0], list):
            # dbug("This must be a simple list")
            simple_list = True
            # colnames.insert(0, "Index")
            # dbug(colnames)
            # dbug(data[:2])
        if isinstance(data[0], list):
            # dbug("data must be a list of lists")
            # this is an lol so...
            if colnames in ("firstrow", "first", "firstline") or dat or firstrow_b:
                colnames = data[0]
            if fix_b:
                # fix all the line lengths if needed
                cnvrt(data, 'fix')
            data = data[1:]
        df = pd.DataFrame(data)
        # dbug(df.head(2))
        # dbug(df.index.name)
        if colnames != []:
            # dbug(df)
            # dbug(colnames)
            if colnames in ("firstrow", "firstline", "rowone", "first"):
                colnames = df.iloc[0].tolist()  # first row for the header/colnames
            df.columns = colnames
        src = "list"
        # if colnames[0] != df.index.name:
        if not simple_list:
            # this therefore should be a lol
            df = df.set_index(colnames[0])  # set the index to the first column
    # """--== Process ==--"""
    dbug(df.head(3))
    dbug(colnames)
    if colnames != []:
        if colnames in ("firstrow", 'firstline', "first", "rowone"):
            # dbug(df)
            colnames = list(df.iloc[0])
            # dbug(colnames)
            df.columns = colnames
            # dbug(colnames)
            df = df.iloc[1:]
            # dbug(df.head(2))
        # dbug(colnames)
        if not simple_list:
            # dbug(f"Check the number of supplied colnames (len(colnames): {len(colnames)}), should be {len(df.columns)}")
            colnames = df.columns.to_list()
            colnames = [colnames.lower() for colnames in colnames]  # my preference and makes the colnames more predictable
            # df
            # colnames.insert(0, df.index.name)
        else:
            df.columns = colnames
    # dbug(f"Now all conversions done including colnames: {colnames}  df:{df}")
    colnames = df.columns.to_list()
    dbug(f"colnames: {colnames}")  # index_l: {df.index.to_list()}")
    colnames = [colnames.lower() for colnames in colnames]  # my preference and makes the colnames more predictable
    # dbug(colnames)
    df_colnames = df.columns.to_list()
    rename_d = dict(zip(df_colnames, colnames))
    df.rename(columns=rename_d, inplace=True)
    # now all colnames are lowercase
    if df.index.name is not None:
        # dbug(f"inserting colnames: {colnames}")
        new_index_name = df.index.name.lower()  # my preference
        df.index.name= new_index_name
        colnames.insert(0, new_index_name)  # now insert the index name as the first colname
    # now the index name has been changed to lowercase
    # gtable(df.head(int(tail)), 'hdr', 'prnt', title=title + f" df.head({tail}) index name is now lower case", footer=footer, centered=centered_b, rnd=rnd)
    if show:
        footer = f"{footer} Source: {src} "
        df = df.round(3)  # TODO make this a config option??
        if show:
            footer = footer + " " + dbug('here')
        # gtable(df.head(int(tail)), 'hdr', 'prnt', title=title + f" df.head({tail})", footer=footer, centered=centered_b, rnd=rnd)
        gtable(df.tail(int(tail)), 'hdr', 'prnt', title=title + f" df.tail({tail})", footer=footer, centered=centered_b, rnd=rnd)
    # dbug(df.head(3))
    # dbug(colnames)
    # dbug(df.columns.to_list())
    # """--== SEP_LINE ==--"""
    choices_l = colnames[1:]
    # dbug(choices_l)
    if selections != []:
        if isinstance(selections, str):
            selections = [selections]
        selections_l = selections
        # dbug(f"selections: {selections} selections_l: {selections_l}")
    else:
        # dbug(colnames)
        selections_l = colnames[1:]
    # dbug(selections_l)
    if choose:
        selected_l = []
        selections_l = gselect(choices_l, centered=centered_b, width=140, title=title, rtrn="v", prompt="Add the desired column", footer=f"Selected: {selected_l}", quit=True, multi=True, dflt="q")
        if selections_l == []:
            return df
    if selections_l == []:
        if colnames[0] == df.index.name:
            selections_l = colnames[1:]
        else:
            selections_l = colnames
    # dbug(selections_l)
    # ### moving avgs ### #
    if mavgs:
        # dbug(f"selections_l: {selections_l} mavgs: {mavgs} colnames: {colnames}")
        df["50ma"] = df[selections_l[0]].rolling(window=50, min_periods=0).mean()
        df["200ma"] = df[selections_l[0]].rolling(window=200, min_periods=0).mean()
        selections_l.append("50ma")
        selections_l.append("200ma")
        df = df.dropna()  # inplace=True)
        # last_50ma = round(df["50ma"].iloc[-1], 2)
        # last_200ma = round(df["200ma"].iloc[-1])
    # """--== hlines ==--"""
    if isinstance(hlines, dict):
        for k, v in hlines.items():
            if isempty(v):
                continue
            hline_name = k
            hline = float(v)
            if hline != "":
                if float(hline) > 0:
                    # dbug(len(df))
                    hline_col = []
                    for x in range(len(df)):
                        hline_col.append(hline)
                    df[hline_name] = hline_col
                    selections_l.append(hline_name)
    # """--== SEP_LINE ==--"""
    df = df.reset_index()  # inplace=True)
    if web_b:
        # """--== for browser display ==--"""
        fig = px.line(df, x=colnames[0], y=selections_l, title=title)
        # dbug("Doing fig.show()")
        fig.show()
    else:
        # dbug("Not a web request")
        if "date" in str(colnames[0]).lower() or "time" in str(colnames[0]).lower():
            if colnames[0] != df.index.name:
                my_df = df.set_index(colnames[0])
            else:
                my_df = df
        else:
            # dbug(df)
            my_df = df
        for col in colnames[1:]:  # cut out the date/time/x scale
            if col in selections_l:
                my_df[col] = my_df[col].astype(float)
                # dbug("attepted fix here")
        # """--==  fix dateseries on first column if it has time or date in the name ==--"""
        # dbug(f"colnames: [{colnames[0]}]")
        if has_substr(colnames[0].lower(), ["date", "time"]):
            # dbug(df[:2])
            # dbug(df.iloc[0][0])
            # dbug(colnames)
            if df.index.name == colnames[0]:
                date_entry = df.first_valid_index()
            else:
                date_entry = str(df.iloc[0][0])
            # dbug(date_entry)
            dtformat = get_dtime_format(date_entry)
            # dbug(dtformat)
            if dtformat != "%Y-%m-%d":
                # df.iloc[:, 0] = pd.to_datetime(pd.Series(df.iloc[:, 0]), format=dtformat, errors='coerce')
                my_df = pd.to_datetime(pd.Series(df.iloc[:, 0]), format=dtformat, errors='coerce')
        # """--== SEP_LINE ==--"""
        pri_min = df[selections_l[0]].min()
        pri_max = df[selections_l[0]].max()
        # """--== SEP_LINE ==--"""
        try:
            pri_max = round(float(pri_max))
            pri_min = round(float(pri_min), 2)
            footer += f"\nMin-Max: {pri_min}-{pri_max}"
        except Exception as Error:
            dbug(Error)
        # """--== SEP_LINE ==--"""
        # this section breaks ????
        grid = (6, 1)  # aka shape
        top_loc = (0, 0)
        bot_loc = (5, 0)
        # """--== SEP_LINE ==--"""
        top_plt = plt.subplot2grid(grid, top_loc, rowspan=5, colspan=1)  # THIS SEEMS PROBLEMATIC, NOT SURE WHY - if chromebook... reboot
        # dbug(selections_l)
        top_plt.plot(df[selections_l], label=selections_l)
        top_plt.legend(loc="upper right")
        top_plt.set_title(title)
        # """--== SEP_LINE ==--"""
        # dbug("Now adding title to plt")
        plt.title(title)
        # """--== SEP_LINE ==--"""
        if box_text != "":
            if isinstance(box_text, list):
                box_text = "\n".join(box_text)
                box_text = parse_codes(box_text, 'escaped')
            # properties
            props = dict(boxstyle='round', facecolor='wheat', alpha=1.0)
            top_plt.text(0.01, 0.97, box_text, transform=top_plt.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
            top_plt.legend(loc='upper right')
        # """--== SEP_LINE ==--"""
        if subplot:
            bot_plt = plt.subplot2grid(grid, bot_loc, rowspan=1, colspan=1)
            bot_plt.fill_between(df.index, df[subplot], label=subplot, color="blue", facecolor='grey')
            bot_plt.legend(loc="upper right")
            # plt.subplots_adjust(hspace=1)  # make no diff???
        # """--== SEP_LINE ==--"""
        if pb_lines:
            # indx_len = len(df.index)
            x_val = df.index[0]
            # """--== correction mrkt ==--"""
            try:
                correction = round(0.9 * float(pri_max), 2)  # 10% pull back
            except Exception as Error:
                correction = 0
                dbug(Error)
            top_plt.axhline(y=correction, color='cyan', linestyle="--")
            if len(box_text) < 10:
                top_plt.text(x_val, correction, "Correction[10%]", va='center', ha='left', backgroundcolor='w')
            # """--== bear mrkt ==--"""
            bear = 0.8 * pri_max  # 20% pull back
            top_plt.axhline(y=bear, color='cyan', linestyle="-.")
            if len(box_text) < 10:
                top_plt.text(x_val, bear, "Bear[20%]", va='center', ha='left', backgroundcolor='w')
            # """--== superbear mrkt ==--"""
            superbear = 0.7 * pri_max  # 30% pull back
            top_plt.axhline(y=superbear, color='cyan', linestyle="-.")
            if len(box_text) < 10:
                top_plt.text(x_val, superbear, "SuperBear[30%]", va='center', ha='left', backgroundcolor='w')
            # """--== ultrabear mrkt ==--"""
            uberbear = 0.6 * pri_max  # 40% pull back
            top_plt.axhline(y=uberbear, color='cyan', linestyle="-.")
            if len(box_text) < 10:
                top_plt.text(x_val, uberbear, "UberBear[40%]", va='center', ha='left', backgroundcolor='w')
        # """--== SEP_LINE ==--"""
        footer = "\n\n" + footer + f" {dbug('here')} "
        plt.figtext(0.5, 0.01, footer, ha='center', fontsize=11)
        plt.gcf().set_size_inches(15, 5)
        if len(subplot) > 0:
            plt.gcf().set_size_inches(15, 6)
        # """--== save plot file ==--"""
        if savefile != "":
            # NOTE!!!! this has to be called BEFORE plt.show !!!! NOTE #
            # dbug(f"Saving file: {savefile}")
            plt.savefig(f"{savefile}")
        # """--== chromebook problem with display of plot ==--"""
        # dbug("Checking for chromebook...")
        if file_exists("/opt/google/cros-containers", type='dir'):
            # dbug("This is a chromebook... so plot_show will fail ... you might try 'sudo apt get python3-tk' ...")
            if askYN(f"This is a chromebook ... Do you want to open the graph file {savefile} with feh", "y", 'centered'):
                cmd = "feh " + savefile
                run_cmd(cmd)
        else:
            # dbug("Running plt.show()")
            plt.show()
    # dbug(f"Returning df: {df} as an lol")
    my_lol = cnvrt(df)
    if ask_b:
        askYN()
    return my_lol
    # ### EOB def quick_plot(data, *args, **kwargs): ### #


# ##################
def do_func_docs():
    # ##############
    """
    purpose: to get function docs
    returns: prints selected function __doc__ boxed and centered
    """
    # """--== SAMPLE TABLE ==--"""
    # gtable(tst_d, 'prnt', 'wrap', title="Simple tst_d no col_limit so default?", footer=dbug('here'))
    # dbug('ask')
    # """--== SAMPLE TABLE 2 ==--"""
    # gtable(tst_d, 'prnt', 'wrap', title='tst_d with list type items no  col_limit', footer=dbug('here'))
    # dbug('ask')
    # """--== SAMPLE TABLE 3 ==--"""
    # gtable(tst_d, 'prnt', 'wrap', title="tst_d no col_limit", footer=dbug('here'))
    # dbug('ask')
    # """--== SEP_LINE ==--"""
    # """--== Get a list of all func except a few... ==--"""
    my_lines = grep_lines(__file__, r"^def .*\(")
    my_funcs_l = [x.replace("def ", "") for x in my_lines]
    funcs_l = [re.sub(r"\((.*)\):.*", "", x) for x in my_funcs_l]
    funcs_l = [x for x in funcs_l if x.strip() not in ("main", 'tst')]
    funcs_l = [x for x in funcs_l if x.strip() if "demo" not in x]
    funcs_l = sorted(funcs_l)
    # """--== user select ==--"""
    # func = gselect(stripped_funcs_l, 'centered', title="Which Function would you like information on:")
    exclude_l = ["main", 'tst', 'do_func_demos']
    funcs_l = chk_substr(funcs_l, exclude_l, action='exclude')
    funcs_l = sorted(funcs_l)
    func = gselect(funcs_l, 'centered', title="Which Function would you like information on:", footer=dbug('here'), width='80%')
    if func not in ("", "q", "Q"):
        doc = globals()[func].__doc__
        doc = doc.split("\n")
        doc = [line.strip() for line in doc if line.strip() != '']
        printit(doc, 'center', 'boxed', title=func+"(...)", footer=dbug('here'))
    return func
    # ### EOB def do_func_docs(): ### #


# #############################################
def has_substr(text_s, chk_l, *args, **kwargs):
    # #########################################
    """
    purpose: determin if any sub-string in chk_l is in text_s
        column_name = "dtime"
        eg is "time" or "date" in column_name... then use has_substr(column_name, ["time", "date"])
    required:
        - text_s: str
        - chk_l: list
    options:
        - ci: bool  # case_insensitive
    returns True | False
    notes:
        used in quick_plot()
    """
    ci_b = arg_val(["ci", "case_insensitive"], args, kwargs, dflt=False)
    if ci_b:
        text_s = text_s.lower()
    has_substr_b = False
    for sstr in chk_l:
        if ci_b:
            sstr = sstr.lower()
        if str(sstr) in str(text_s):
            has_substr_b = True
    return has_substr_b
    # ### EOB def has_substr(text_s, chk_l, *args, **kwargs): ### #


# ###############################################
def chk_substr(chk_l, strgs_l, action='exclude'):
    # ###########################################
    """
    purpose: given a list of strings to check (chk_l) and a list of substrings to compare (strgs_l)
            if any "compare" substring is in any string in check list of strings then
                do action either 'exclude' or 'include'
    required:
        - chk_l: list | str
        - strgs_l: list
    options:
        - action: str  # default is 'exclude'
    return: new_list
    usage:
        # given a list of functions, exclude the ones that may have any of the provided  substrings (list) in the exclude_l list
        funcs_l = chk_substr(funcs_l, exclude_l, action='exclude')
        eg:
            exclude_l = ["main", 'tst', 'do_func_demos']
            funcs_l = chk_substr(funcs_l, exclude_l, action='exclude')
            funcs_l = sorted(funcs_l)
    """
    new_l = []
    for string_s in chk_l:
        if any(sub_s in string_s for sub_s in strgs_l):
            if action == 'include':
                new_l.append(string_s)
        else:
            if action == 'exclude':
                new_l.append(string_s)
    return new_l


# #################################
def gcontains(string_s, pattern_m):
    # #############################
    """
    purpose: determines if any pattern (str|list) is a substring of string (string_s)
    required:
        - string_s: str | list
        - pattern_m: str | list  # list = [pattern1, pattern2, ...]
    options: none
    returns: bool
    """
    if isinstance(string_s, list) and isinstance(pattern_m, list):
        list1 = pattern_m
        list2 = string_s
        # to see if any string from one list is in any elem of second list
        any_match = any(s1 in s2 for s1 in list1 for s2 in list2)
        # dbug(any_match)
        # for s2 in list2:  # this is the long version of above
        #     dbug(f"processing {s2=}")
        #     for s1 in list1:
        #         if s1 in s2:
        #             dbug(f"FOUND {s1=} in {s2=}")
        #         else:
        #             dbug(f"did NOT find {s1=} in {s2=}")
        return any_match
    if not isinstance(pattern_m, list):
        pattern_l = [pattern_m]
    else:
        pattern_l = pattern_m
    for pat in pattern_l:
        if pat in string_s:
            # dbug(f"Found pat: {pat} in string_s: {string_s} returning True")
            return True
    return False
    # ### EOB def gcontains(string_s, pattern_m): ### #


# # ############################################
# def fix_docstring(docstring, *args, **kwargs):
#     # ########################################
#     """
#     purpose: takes a multiline string (docstring) and strips off leading shitespaces, deletes blank first and last lines, and returns a list of lines
#     requires:
#         - docstring: str     # multiline string
#     options: none
#         - length: str        # default=0 (no wrap)
#         - prnt: bool
#         - centered: bool
#         - rtrn_type: str     # can be: "str" as default is to return a list of lines
#     returns: list of "fixed" lines or a string is declared in options
#     notes:
#         - aka should be called fix_msg of lstrip_msg
#     """
#     dbug("Deprecated... use fix_msg()")
#     return 
#     # """--== Config ==--"""
#     prnt_b = arg_val(['prnt', 'print'], args, kwargs, dflt=False)
#     centered_b = arg_val(['center', 'centered'], args, kwargs, dflt=False)
#     boxed_b = arg_val(['box', 'boxed'], args, kwargs, dflt=False)
#     length = kvarg_val(['length', 'width', 'wrap'], kwargs, dflt=0)  # default=0 (no wrap)
#     title = kvarg_val(["title"], kwargs, dflt="")
#     footer = kvarg_val(['footer'], kwargs, dflt="")
#     rtrn_type = arg_val(["rtrn_type","return_type"], args, kwargs, dflt="")
#     # """--== Process ==--"""
#     doc_lines = docstring.split("\n")
#     doc_lines = [line.lstrip() for line in doc_lines]
#     # dbug(doc_lines)
#     pop_elems = [len(doc_lines) - 1, 0]  # if blank, delete last and first line (has to be in this order)
#     for elem in pop_elems:
#         # dbug(f"len(doc_lines): {len(doc_lines)} elem: {elem}")
#         line = doc_lines[elem]
#         # dbug(f"elem: {elem} line: {line}")
#         if len(line) == 0 or line.isspace():
#             doc_lines.pop(elem)
#             # dbug("deleted line ")
#     doc_lines = printit(doc_lines, prnt=prnt_b, boxed=boxed_b, centered=centered_b, length=length, title=title, footer=footer)
#     if rtrn_type in ('str', 'string'):
#         doc_lines = "\n".join(doc_lines)
#     return doc_lines
#     # ### def fix_docstring(docstring, *args, **kwargs): ### #


# ######################################################
def get_mod_docs(mod=__file__, *args, fn="*", **kwargs):
    # ##################################################
    """
    purpose: lists all functions and the docs from a module
    Note: except some functions eg _demo _tst (declared within this function, for now)
    returns cnt
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(kwargs)
    # """--== Imports ==--"""
    # import inspect
    # from inspect import getmembers, isfunction
    # boxed_b = arg_val(["boxed", "box"], args, kwargs, dflt=True)
    # """--== SEP_LINE ==--"""
    funcs = []
    exclude = ["main", "tst", "demo", "qnd"]
    with open(__file__) as f:
        for s in f:
            # dbug(f"testing s: {s}")
            results = re.finditer(r"^def (?P<this_func>[^(]+)", s)
            # dbug(results)
            for result in results:
                funcname = result['this_func']
                if [ele for ele in exclude if(ele in funcname)]:
                    # dbug(f"skipping funcname: {funcname}")
                    continue
                funcs.append(funcname)
    funcs = sorted(funcs)
    selected = None 
    while selected not in ("q", "Q", ""):
        selected = gselect(funcs, cols=4, title="functions", footer=dbug('here'), prnt=True, boxed=True,centered=True)
        if selected in ("q", "Q", ""):
            return
        if selected in ("E"):
            do_edit(__file__)
        # dbug(selected)
        doc = globals()[selected].__doc__
        if doc is not None:
            doc = doc.split("\n")
            doc = [ln.rstrip("\n") for ln in doc[1:] if not ln.isspace()]
            printit(doc, 'boxed', 'centered', title=f" {selected}(...) ", bxclr="yellow! on grey30")
        else:
            dbug(f"No doc found for {selected}")
        if not askYN("Continue? ", 'centered'):
           selected = "q" 
    return
    # ### EOB def get_mod_docs(mod=__file__, fn="*"): ### #


# ##################################
def columned(my_l, *args, **kwargs):
    # ##############################
    """
    purpose: set a list in X columns (this is used by gcolumnize)
    required: my_l: list
    options:
        - cols=0: int               # number of columns
        - order='v': str            # 'vertical', 'vert', 'v'| 'horizontal', 'hor', 'h'
                                    # order directs the order of the choices - proceed vertically through columns or horizontally through columns
        - justify='left: str        # 'left', 'right', 'center'
        - prnt=False: bool          # 'print', 'prnt' ... to invoke printing the lines
            - boxed: bool
            - centered: bool
            - title: str
            - footer: str
        - width=0: int              # cols will be calculated from this - approximated
    returns: lines for printing
    notes: this takes the place of standard module columnize so we are not dependant on that code
        - you probably do not want to use this function directly - use gcolumnize instead.
        - used by: gcolumnize()
    """
    # """--== Debugging ==--"""
    # dbug(f"{funcname()} called_from(): {called_from()}")
    # dbug(my_l)
    # dbug(args)
    # dbug(kwargs)
    # """--== Imports ==--"""
    # from math import ceil
    # """--== Config ==--"""
    cols = kvarg_val(["cols", 'num_cols'], kwargs, dflt=0)
    # dbug(cols)
    prnt = arg_val(['prnt', 'print'], args, kwargs, dflt=False)
    boxed_b = arg_val(["boxed", "box"], args, kwargs, dflt=False)
    centered_b = arg_val(["centered", "center"], args, kwargs, dflt=False)
    color = kvarg_val(["color", "clr"], kwargs, dflt="")
    box_color = kvarg_val(["box_color", "box_clr"], kwargs, dflt="")
    title = kvarg_val("title", kwargs, dflt="")
    footer = kvarg_val("footer", kwargs, dflt="")
    justify = kvarg_val(["just", "justify"], kwargs, dflt='left')
    order = kvarg_val(["order", 'orient', 'orientation'], kwargs, dflt="v")
    # dbug(order)
    pivot_b = arg_val(["pivot", "pivot_b", "invert"], args, kwargs, dflt=False)
    sep = kvarg_val(["sep"], kwargs, dflt=" | ")
    pad = kvarg_val(["pad"], kwargs, dflt=" ")
    blank = kvarg_val("blank", kwargs, dflt="...")
    width = kvarg_val(["width", "w", "length", "len", "l"], kwargs, dflt=0)
    # dbug(width, 'ask')
    # """--== Verify ==--"""
    # if len(my_l) == 0 or my_l is None:
    if isempty(my_l):
        # dbug(f"Nothing to work on... {called_from()}...")
        return None
    # if islol(my_l):
    if data_type(my_l, 'lol'):
        dbug("You should consider using gcolumnize as this is for simple lists only")
        return None
    # """--== Init ==--"""
    scr_cols = get_columns()
    if "%" in str(width):
        width = width.replace("%", "")
        width = int(scr_cols * (int(width)/100))
    col = 0
    if pivot_b:
        if order == "v":
            order = "h"
        if order == "h":
            order = "v"
    avg_maxof = maxof(my_l)
    if cols == 0 and width == 0:
        width = get_columns()
        # dbug(width)
    if int(width) > 0 and int(cols) < 2:
        # cols is given preference over width
        # dbug(width)
        # dbug(avg_maxof)
        max_cols = math.ceil(width / avg_maxof)
        # dbug(f"width: {width}  avg_maxof: {avg_maxof} max_cols: {max_cols}")
        cols = max_cols
        if max_cols < len(my_l):
            # without this section you will end up with too many empty or blank cells and columns
            needed_rows = math.ceil(len(my_l) / max_cols)
            cols = math.ceil(len(my_l) / needed_rows)
            # dbug(f"len(my_l): {len(my_l)} and avg_maxof * len(my_l): {avg_maxof * len(my_l)}")
        # dbug(cols)
        if cols > len(my_l):
            cols = len(my_l)
        if cols == 1:
            order = "v"
        # dbug(f"width: {width} avg_maxof: {avg_maxof} cols: {cols} order: {order}")
    if cols == 0:
        cols = 1
    # dbug(f"width: {width} avg_maxof: {avg_maxof} cols: {cols} order: {order}")
    # """--== Process ==--"""
    rows = math.ceil(len(my_l)/cols)
    # build a matrux for each col (ie rc_arr row_col_array) it gets populated with elems from my_l
    rc_arr = matrix(rows, cols, dflt_val=blank)  # col is normally one but user may want the table split into multiple cols
    for num, i in enumerate(my_l):
        elem = i
        # for row in range(rows):
        if order.lower() in ("v", 'vert', 'vertical'):
            row = num % rows
            col = num // rows
            # dbug(f"order: {order} cols: {cols} i: {i} num: {num} row: {row} col: {col} elem: {elem}")
        else:  # ie ("h", "hor", "horizontal")
            row = num // cols
            col = num % cols
            # dbug(f"order: {order} cols: {cols} i: {i} num: {num} row: {row} col: {col} elem: {elem}")
        rc_arr[row][col] = elem
    # dbug(rc_arr)
    # """--== max_col_lens ==--"""
    max_col_lens = []
    for col in range(cols):
        # dbug(f"col: {col} of cols:{cols}")
        max_col_lens.append(0)
        for row in range(rows):
            rc_arr_row_col_len = parse_codes(rc_arr[row][col], 'nclen')
            # if nclen(rc_arr[row][col]) > max_col_lens[col]:
            if rc_arr_row_col_len > max_col_lens[col]:
                # max_col_lens[col] = nclen(rc_arr[row][col])
                max_col_lens[col] = rc_arr_row_col_len
    # dbug(max_col_lens)
    lines = []
    # for row_num, elem in enumerate(rc_arr):
    for elem in rc_arr:
        new_elems = []
        for col_num, item in enumerate(elem):
            # dbug(item)
            item = str(item)
            item_len = parse_codes(item, 'nclen')
            # item_len = nclen(item)
            max_col_len = max_col_lens[col_num]
            diff = max_col_len - item_len
            fill = pad * diff
            if justify == 'left':
                new_elems.append(item + fill)
            if justify == 'right':
                new_elems.append(fill + item)
            if justify == 'center':
                center_fill = (diff // 2) * pad
                new_elems.append(center_fill + item + center_fill)
        items = [str(i) for i in new_elems]
        elems = ""
        elems = sep.join(items)
        lines.append(elems)
    lines = gblock(lines)  # not needed if you are using blocked or printit with blocked but this makes it hemogenous
    if prnt:
        printit(lines, boxed=boxed_b, centered=centered_b, title=title, footer=footer, color=color, box_color=box_color)
    return lines
    # ### EOB def columned(my_l=["one", "and two", "three", "and four", "five", 6, "my seven", "eight", "9", 10, 11], *args, **kwargs): ### #


def dtree(dir_name="./", *args, **kwargs):
    """
    purpose: print a simple directory tree
    required:
        - dir_name: str         # default = "./" 
    options:
        - files: bool           # default=False
        - prnt: bool            # default=False  should we print out the lines
        - excludes: list | str  # default=[] this is a pattern or list of patterns to skip
        - boxed: bool           # boxes all the lines
        - title: str            # default=f"Directory: {dir_name} Show files: {files_b}"
        - footer: str           # default=f"Excludes: {excludes} " + dbug('here')"
        - centered: bool        # boxes all the lines
        - length: int           # default=3  # size of the "fill"
        - box_clr: str          # color of box if that option is True
    returns: list (lines for printing) unless rtrn='files' (see above)
    """
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(dir_name)
    # dbug(args)
    # dbug(kwargs)
    # dbug(dir_name)
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "print", "show"], args, kwargs, dflt=False)
    # dbug(prnt)
    files_b = arg_val(["files", "f"], args, kwargs, dflt=False)
    boxed_b = arg_val(["boxed", "box"], args, kwargs, dflt=False)
    box_clr = arg_val(['box_clr', 'box_color'], args, kwargs, dflt="white! on black")
    centered_b = arg_val(["centered", "center", "cntr"], args, kwargs, dflt=False)
    excludes = arg_val(["exclude", "excludes", "filer", "filters"], args, kwargs, dflt=[])
    length = arg_val(["length"], args, kwargs, dflt=3)
    title = arg_val("title", args, kwargs, dflt="")
    footer = arg_val(["footer", "ftr"], args, kwargs, dflt="")
    # """--== Init ==--"""
    if title == "":
        title = f"Directory: {dir_name} Show files: {files_b}"
    # if footer == "":
        # footer = f"Excludes: {excludes} " + dbug('here')
    start_str = "|"
    start_mark = "+"
    fill_str = " " * (length)
    mark_str = "-" * length
    lines = []
    if isinstance(excludes, str):
        excludes = [excludes]
    if isinstance(dir_name, list) and len(dir_name) == 1:  # just in case
        dir_name = dir_name[0].replace("//","/")
    # """--== Process ==--"""
    # dbug(dir_name)
    for root, dirs, files in os.walk(dir_name, topdown=True):
        skip = False
        level = root.replace(dir_name, '').count(os.sep)
        # dbug(f"{root=} {dirs=} {files=} {level=}")
        dname = os.path.basename(root)
        # """--== SEP_LINE ==--"""
        for pat in excludes:
            if re.search(pat, root):
                skip = True
        if not skip:
            lines.append((level * (start_str + fill_str)) + start_mark + mark_str + dname + os.sep)
        else:
            continue
        # """--== files ==--"""
        if files_b:
            for num, file in enumerate(files, start=1):
                skip = False
                # """--== SEP_LINE ==--"""
                for pat in excludes:
                    if re.search(pat, file):
                        skip = True
                if not skip:
                    lines.append(((level + 1) * (start_str + fill_str)) + start_mark + mark_str + file)
    lines = printit(lines, title=f"Directory: {dir_name} Show files: {files_b}",
                    prnt=prnt, boxed=boxed_b, centered=centered_b, 
                    box_clr=box_clr,
                    footer=footer)
    # """--== return ==--""" #
    return lines


# this is here for reference - don't take it out yet
# def imports_list():
#     # 
#     import sys
#     modulenames = set(sys.modules) & set(globals())
#     allmodules = [sys.modules[name] for name in modulenames]
#     printit(allmodules)


# ###########################
def isinterect(list1, list2, *args, **kwargs):
    # #######################
    """
    purpose: determine if any element in first list exists in the second list
    required:
        - list1: list,
        - list2: list
    options:
        - lst: bool  # default=False - will return a list of intersecting elems
    returns: bool (True | False)
    notes: used by boxed()
    """
    # """--== Config ==--"""
    lst_b = arg_val(['lst', 'list'], args, kwargs, dflt=False)
    # """--== Process ==--"""
    if lst_b:
        list3 = [value for value in list1 if value in list2]
        return list3
    set1 = set(list1)
    set2 = set(list2)
    if set1.intersection(set2):
        return True
    else:
        return False
    # ### EOB def isinterect(list1, list2, *args, **kwargs): # ###


# ###########################################
def chklst(chk_l, chkd_l=[], *args, **kwargs):
    # #######################################
    """
    purpose: display a list of empty checkboxes|ballot boxes with chkd_l boxes checked and xed_l boxes with and X
    required:
        - my_l: list      # list of check box names
        - chkd_l: list    # list of boxes that have been checked, usually this starts with an empty list []
    options:
        - dflt: str       # default='empty' - alternatives: default= or dflt= 'chk', 'chkd', 'checked', 'all_chkd', 'chk_all , 'xed' 'x_all', 'all_x' ...
        - xed: list       # list of elems to "X"
        - boxed: bool
        - centered: bool
        - prnt: bool=True
        - color|clr: str      # default="" - text color
        - masterbox_clr: str  # default='white! on black' - outside master box color
        - chkmark_clr: str    # default='green!' - check mark color
        - xmark_clr: str      # default='red!' - X mark color
        - chkbox_color: str   # default="" - check boxes color
        - title: str
        - footer: str
        - cols: int           # number of columns
        - indx|nums|indexed|numbered: bool  # whether to number the items
        - prompt: str         # default="Selections: "
        - select: bool        # default=False is select True then a while loop will accumulate chkd response and return that list when "q" or "Q" or "" is entered
        - stats_b: bool       # default=False - whether to display statistics (percent of checked) - only works when select is True
        - cls: bool           # default=False - only useful with option select, if set to True the screen will be cleared between selections
        - timeout: int        # question will timeout after declared seconds with the default as the answer
    returns: list  # printable lines or if option select=True  a list of checked items (chkd_l)
    notes:
    useage:
        chk_l = ["one", "two", "three"]
        chkd_l = []
        chkd_l = chklst(chk_l, chkd_l, 'select', 'centered', 'stats')
        # ### or ### #
        from gtoolz import cls, chklst, cinput
        ans = []
        chk_l = ["one", "two", "three"]
        chkd_l = []
        while ans not in ("q", "Q", ""):
            cls()
            chklst(chk_l, chkd_l, 'prnt', 'centered', 'boxed', title="What has been done", footer=dbug('here'))
            ans =  cinput("Select which one you would like to work on (q)uit: ", timeout=timeout)
            if ans in ("q", "Q", ""):
                break
            chkd_l.append(ans)
        chklst(my_l, chkd_l, 'prnt', title="Completed", footer=dbug('here'))
    """
    # import unicodedata
    # """--== Debugging ==--"""
    # dbug(funcname())
    # dbug(chk_l)
    # dbug(chkd_l)
    # dbug(args)
    # dbug(kwargs)
    # """--== Config ==--"""
    prnt = arg_val(["prnt", "print", "show"], args, kwargs, dflt=False)  # you generally want this false do you can control flashing in a loop
    my_dflt = kvarg_val(["dflt", 'default'], kwargs, dflt='empty')
    xed_l = arg_val(["xed_l", "xd_l", "xd", "xs", "xes", "x_l", "xed", "fail", "failed", "failed_l"], args, kwargs, dflt=[])
    # dbug(f"{xed_l=}")
    # if 'xed_l' in kwargs:
        # dbug(kwargs['xed_l'])
    centered_b = arg_val(["centered", "center"], args, kwargs, dflt=False)
    boxed_b = arg_val(["boxed", "box"], args, kwargs, dflt=False)
    chkbox_clr = kvarg_val(["box_clr", "box_color", 'chkbox_clr', 'checkbox_clr'], kwargs, dflt="")
    master_box_clr = kvarg_val(["master_box_clr", "master_box_color", "mstrbox_clr", "masterbox_clr", 'main_box_clr', 'mainbox_clr', 'box_clr'], kwargs, dflt="white! on black")
    # dbug(master_box_clr)
    clr = kvarg_val(["clr", "color"], kwargs, dflt="")
    chkmark_clr = kvarg_val(["checkmark_clr", 'chkmark_clr', 'checkmark_color', 'chkd_clr'], kwargs, dflt="green!")
    xmark_clr = kvarg_val(["xmark_clr", 'xmark_clr', 'xmark_color', 'xed_clr'], kwargs, dflt="red!")
    style = kvarg_val(["style"], kwargs, dflt="checkbox")
    # ballot_b = arg_val(["ballot"], args, kwargs, dflt=True)
    chkbox_b = arg_val(["check_box", 'chk_box', 'chkbox', 'chkbx', 'simple'], args, kwargs, dflt=False)
    title = kvarg_val("title", kwargs, dflt="")
    footer = kvarg_val("footer", kwargs, dflt="")
    cols = kvarg_val("cols", kwargs, dflt=1)
    indx = arg_val(["numbered", "indx", "indexed", "nums"], args, kwargs, dflt=False)
    select_b = arg_val(["select", 'menu', 'while', 'loop'], args, kwargs, dflt=False)
    stats_b = arg_val(["stats", "score", "statistics"], args, kwargs, dflt=False)
    cls_b = arg_val(["clear", 'cls'], args, kwargs, dflt=False)
    timeout = arg_val(['timeout'], args, kwargs, dflt=0)
    # """--== demo ==--"""
    if chk_l == 'demo':
        # my_chk_l = ["one", "two", "three"]
        # my_chkd_l = []
        # my_chkd_l = chklst(my_chk_l, my_chkd_l) # , 'select', 'centered', 'stats')
        # ### or ### #
        from gtoolz import cls, chklst, cinput
        ans = []
        chk_l = ["one", "two", "three"]
        chkd_l = []
        while True:  # ans not in ("q", "Q", ""):
            cls()
            chklst(chk_l, chkd_l, 'prnt', 'centered', 'boxed', title="What has been done", footer=dbug('here'))
            ans =  cinput("Select which item you would like to work on (q)uit: ", timeout=timeout)
            if ans in ("q", "Q", ""):
                break
            chkd_l.append(ans)
        chklst(chk_l, chkd_l, 'prnt', 'boxed', title="Demo Completed", footer=dbug('here'))
    # """--== Init ==--"""
    lines = []
    # dbug("\u2713")  # check mark
    # dbug("\u2714")  # bold check mark
    # dbug("\u2715")  # X
    # dbug("\u2716")  # bold X
    # dbug("\u2717")  # stylized X
    # dbug("\u2718")  # bold stylized X
    prompt = "Selection: "
    chk_l = [item.strip() for item in chk_l]    # make sure items are stripped
    chkd_l = [str(item).strip() for item in chkd_l]  # make sure items are stripped
    CLR = gclr(clr)
    CHKBOX_CLR = gclr(chkbox_clr)
    CHKMARK_CLR = gclr(chkmark_clr)
    XMARK_CLR = gclr(xmark_clr)
    # note 2716 is bold X 2718 is italisized X
    style_d = {'ballot': [f"{CHKBOX_CLR}{chr(9744)} {RESET}",
                          f"{CHKMARK_CLR}{chr(9745)} {RESET}",
                          f"{XMARK_CLR}{chr(9746)}{RESET}"],
               'checkbox': [f"{CHKBOX_CLR}[_]{RESET}",
                            f"{CHKBOX_CLR}[{CHKMARK_CLR}" + "\u2714" + f"{RESET}{CHKBOX_CLR}]{RESET}",
                            f"{CHKBOX_CLR}[{XMARK_CLR}" + "\u2716" + f"{RESET}{CHKBOX_CLR}]{RESET}",
                            ]
               }
    # dbug(style)
    if style.lower() in ("ballot"):  # or ballot_b:
        style = 'ballot'
    if style.lower() in ('check_box', 'chkbox', 'chk_box', 'chk_bx', 'checkbox', 'simple') or chkbox_b:
        style = 'checkbox'
    # dbug(style)
    style_l = style_d[style]
    # dbug(f"Style: {style_l}")
    # """--== Validate ==--"""
    if isempty(chk_l):
        dbug(f"Supplied list is empty chk_l: {chk_l}... returning...")
        return None
    if not isinstance(chkd_l, list):
        dbug(f"chkd_l must be a list type(chkd_l): {type(chkd_l)} ... returning...")
        return None
    # """--== Process ==--"""
    lines = []
    for item_num, item in enumerate(chk_l, start=1):
        item = str(item).strip()
        # dbug(item)
        # dbug(f"Checking item: [{item}]")
        # box = "[" + "_" + "]"
        if my_dflt.lower() in ("empty", "", 'mpty', 'none'):
            box = style_l[0]
        if my_dflt.lower() in ("checked", 'chkd', 'all_chkd', 'all_chk', 'chk_all', 'chkf_all'):
            box = style_l[1]
        if my_dflt.lower() in ("xed", 'xd', 'x', 'all_x', 'all_xd', 'all_xed', 'all_xes' 'all_xs'):
            box = style_l[2]
        if item in xed_l:
            # box = "[" + "\u2718" + "]"
            box = style_l[2]
        if item in chkd_l or str(item_num) in chkd_l:
            # dbug(f"found item: {item} in chkd_l: {chkd_l}")
            box = style_l[1]
        lines.append(f"{box} {RESET}{CLR}{item}{RESET}")
        lines = gblock(lines)
    if indx:
        lines = [f"{num:>2}. {line}" for num, line in enumerate(lines, start=1)]
    if cols > 1:
        # dbug(f"{lines=}")
        lines = gcolumnize(lines, cols=cols)
        # dbug(f"{lines=}")
        # printit(lines)
        # dbug('ask')
    # dbug(prnt)
    ans = "bogus"
    if select_b:
        prnt = False
        # prnt = True
        # chkd_l = []
        # dbug(chk_l)
        # while True:
        # dbug(f"This may be where we break to... interesting {ans=}")
        while ans not in ("q", "Q", ""):  # True:
            from gtoolz import chklst, cinput
            # dbug(f"{ans=} {chkd_l=} {len(lines)=} {prnt=}")
            lines = chklst(chk_l, chkd_l, 'indx', 'boxed', 'prnt', centered=centered_b, master_box_clr=master_box_clr, box_clr=chkbox_clr, clr=clr, cols=cols, title=title, footer=footer)
            # dbug(f"what {boxed=} {prnt=}")
            if stats_b:
                stats_prcnt = round((int(len(chkd_l)) * 100 / int(len(chk_l))), 2)
                printit(f"Stats: {len(chkd_l)}/{len(chk_l)} {stats_prcnt} %", centered=centered_b)
            if centered_b:
                ans = cinput(prompt, timeout=timeout)
            else:
                ans = cinput(prompt, centered=False, timeout=timeout )
            if isnumber(ans):
                ans_num = int(ans) - 1
                # dbug(ans_num)
                chkd_l.append(chk_l[ans_num])  # add the last ans to chkd_l
            else:
                # dbug(ans)
                if ans in ("q", "Q", ""):
                    # dbug(f"returning  ...{ans=} {chkd_l=} {called_from('v')}")
                    return chkd_l
                    # break
            if cls_b:
                cls()
        # dbug(chkd_l, 'ask')
        return chkd_l
    if not isempty(lines):
        lines = printit(lines, boxed=boxed_b, prnt=prnt, centered=centered_b, title=title, footer=footer, box_clr=master_box_clr, clr=clr)
    else:
        dbug(f"{lines=} {called_from('verbose')} returning...")
        return
    if stats_b:
        stats_prcnt = round((int(len(chkd_l)) * 100 / int(len(chk_l))), 2)
        pbar_b = True
        if pbar_b:
            my_pbar = pbar(stats_prcnt) + f" Finished {len(chkd_l)+len(xed_l)} of {len(chk_l)}"
        line = printit(f"{my_pbar} Stats: {len(chkd_l)}/{len(chk_l)} {stats_prcnt}%", prnt=prnt, centered=centered_b)
        lines.append(line)
    return lines
    # ### EOB def chklst(chk_l, chkd_l=[], xed_l=[], *args, **kwargs): ### #


# #######################################
def do_cli(cmd, args_s, *args, **kwargs):
    # ###################################
    """
    purpose: runs command-line requests with cmd args...
    requires: 
        - cmd: str
        - args: str
    returns: None
    """
    # dbug(args_s)
    if 'help' in args_s:
        cli_help()
        do_close()
    # dbug(cmd)
    # dbug(args_s)
    args_d = get_args(args_s)
    args = args_d['args']
    kwargs = args_d['kwargs']
    # dbug(f"Running cmd: {cmd} with args: {args} kwargs: {kwargs}")
    out = globals()[cmd](*args, **kwargs)
    # dbug(out)
    # dbug("Returning out...")
    return out


@docvars(os.path.basename(__file__))
# ############################
def cli_help(*args, **kwargs):
    # ########################
    """
    purpose: provide basic help with commandline usage
    notes: This is work-in-progress (TODO)
    """
    msg = """
    {0} <function> <argument_string>
        - the function call is without quotes
        - the argument string must be in quotes
            - within the argument string you have the option of quoting or not quoting
    Examples:
        - {0} printit 'Please open the door', 'boxed', 'centered', 'shadowed', box_clr='red! on black
        - {0} printit 'Please open the door!', 'boxed', 'centered', 'shadowed', box_clr='red! on black'
        - {0} boxed "This is my message, box_clr=yellow! on black, prnt=True"
        - {0} boxed "'This is my message', box_clr='yellow on black', prnt=True"
        - {0} gtable "~/data/speedtst.csv, 'hdr', centered"
        - {0} gtable "~/data/speedtst.csv, hdr, centered"
    {0} is under development; a work in progress ... any suggeted improvements are encouraged. Currently this is limited in usefulness.
    """
    printit(msg, 'boxed', 'centered', title=f"{0}", box_clr="yellow! on black", footer=dbug('here'))
    # ### EOB def cli_help(*args, **kwargs): # ###


# #####################################
def data_stats(data, *args, **kwargs):
    # #################################
    """
    purpose: provides a statistics table (ie details) for data (rows of columns)
    requires:
        - data: list of list - first row must be oolumn names
    options:
        - prnt: bool=False
        - centered: bool=False
        - title: str=""
        - footer: str=""
        - excludes: lis=[]                               # list of [colnames] to exclude
        - includes|selected: list=colnames               # all colnames unless declared otherwise
        - neg: bool=False                                # default=True, shows negative values as red and positive values as gree
        - human: bool|list                               # default=True, displays large numbers with ("T","G","B"...) 
        - centered: bool=False                           # default=False
        - stats: list=['count','sum','avg',...           # choose specific stats to calculate
                       ...min, max, median, stdev]       # stdev = standard deviation
        - rtrn_type: str default=""                      # default will return stats_d (all the possible stats) if this is set to 'table' | 'tbl' then it will return the table
        - pivot: bool=False                              # this will allow transposing the columns with the row ie: pivoting the table
    return: dictionary of dictionaries syntax = {colname: {'sum': val, 'avg': val, ...},...}
    notes:
        - this function is limited but useful after running gtable to provide quick statistics on that table data
    """
    # """--== Imports ==--"""
    import statistics
    # """--== Config ==--"""
    prnt = arg_val(['prnt', 'print'], args, kwargs, dflt=False)
    centered_b = arg_val(['cntrd', 'cntr', 'centered', 'center'], args, kwargs, dflt=False)
    title = kvarg_val(['title'], kwargs, dflt="Statistics")
    footer = kvarg_val(['footer'], kwargs, dflt="")
    rnd = kvarg_val(['rnd', 'round'], kwargs, dflt=2)
    neg_b = arg_val(['neg', 'cond'], args, kwargs, dflt=True)
    rnd = arg_val(['rnd'], args, kwargs, dflt=2)
    excludes = kvarg_val(['exclude', 'excludes'], kwargs, dflt=[])
    includes = arg_val(['include', 'includes', 'include_cols', 'selected'], args, kwargs, dflt=[])
    colors = kvarg_val(['colors', 'clrs'], kwargs, dflt=[])
    colnames = kvarg_val(['colnames'], kwargs, dflt=[])
    stats_l = arg_val(['stats'], args, kwargs, dflt=[])
    pivot_b = arg_val(['pivot', 'pivot_b', 'transpose'], args, kwargs, dflt=False)
    pivot_b = not pivot_b  # we want it in reversed order first to strech cols across the top - seems more natural that way
    human = arg_val(["human", "H", "h"], args, kwargs, dfault=False)
    rtrn_type = arg_val(['rtrn_type', 'rtype', 'return_type', 'type'], args,kwargs, dfl="stats")
    # """--== Verify ==--"""
    if not isempty(args) and isinstance(args[0], list):
        dbug(f"Make this args[0]: {args[0]} a kwarg(s) ie:  includes={args[0]}....")
        includes = args[0]  # this is only here because of the other data_stats that I wrote
    dtype = data_type(data)
    if dtype not in ('lol'):
        dbug(f"data_type(data): {dtype} must be a list of lists (rows of columns)... returning...")
        return
    # """--== Init ==--"""
    poss_stats_l = ['count','sum','avg','min','max', 'median', 'stdev']
    if isempty(stats_l):
        stats_l = poss_stats_l
    if colnames == []:
        colnames = data[0]
    if includes == []:
        includes = colnames
    stats_d = {}
    # """--== Process ==--"""
    # for my_stat in stats_l:
    for my_stat in poss_stats_l:
        row = [my_stat.capitalize()]
        # for col in colnames[1:]:
        for col in colnames:
            if col in excludes:
                row.append(["-"*len(col)])
                continue
            if col not in includes:
                continue
            colname_idx = colnames.index(col)
            # values1 = [float(escaped(row[colname_idx])) for row in data if isnumber(row[colname_idx])]
            # dbug(values1)
            values = [cond_num(row[colname_idx], 'uncond') for row in data if isnumber(row[colname_idx])]
            # dbug(values)
            if len(values) < 1:
                # dbug(f"col: {col} had no numbers...")
                continue
            if col not in stats_d:
                stats_d[col] = {}
            if my_stat == 'count' or my_stat == 'cnt':
                count = len(values)
                stats_d[col][my_stat] = count
            if my_stat == 'sum': 
                # dbug(col)
                # dbug(values1)
                # dbug(values)
                my_sum = sum(values)
                # dbug(my_sum)
                my_sum = round(float(my_sum), rnd)
                # dbug(my_sum)
                stats_d[col]['sum'] = my_sum
            if my_stat == 'median':
                my_median = statistics.median(values) 
                my_median = round(my_median, rnd)
                stats_d[col]['median'] = my_median
            if my_stat == 'avg':
                my_avg = statistics.mean(values)
                my_avg = round(float(my_avg), rnd)
                stats_d[col]['avg'] =  my_avg
            if my_stat == 'min':
                my_min = min(values)
                stats_d[col]['min'] = my_min
            if my_stat == 'max':
                my_max = max(values)
                stats_d[col]['max'] = my_max
            if my_stat == 'stdev':
                # dbug(len(values))
                if len(values) > 1:  # you have to have at least two data points
                    my_stdev = statistics.stdev(values)
                    my_stdev = round(float(my_stdev), rnd)
                else:
                    my_stdev = 0
                stats_d[col]['stdev'] =  my_stdev
    # dbug(f"stats_l: {stats_l} colnames: {colnames}")
    # colnames = ['columns'] + stats_l
    # dbug(f"human: {human}, pivot_b: {pivot_b} {prnt=} {centered_b=}")
    my_table = gtable(stats_d, 'hdr', prnt=prnt, title=title, footer=footer, rnd=rnd, 
                      neg=neg_b, human=human, colors=colors, pivot=pivot_b, selected=stats_l,
                      centered=centered_b, colnames=["stat","value"])
    # if prnt:
        # printit(my_table, centered=centered_b)
    # dbug(stats_d,'ask')
    if rtrn_type in ('table', 'tbl'):
        return (my_table)
    else:
        return stats_d
    # ### EOB def data_stats(data, *args, **kwargs): ### #


def html_codes(code=None, *args, **kwargs):
    """
    purpose:
    requires:
        - code: int
    options:
        - prnt: bool
    returns:
        - code_name
    notes:
        - WIP
        - 20251118-1101
    """
    # """--== Config ==--""" #
    prnt = arg_val(['prnt'], args, kwargs, dflt=False)
    code = arg_val(['code'], args, kwargs, dflt=code)
    # """--== Init ==--""" #
    rtrn = None
    # """--== SEP_LINE ==--""" #
    categories = {"Informational responses": [100,199], 
                  "Successful responses": [200,299],
                  "Redirection messages": [300, 399],
                  "Client error responses": [400, 499],
                  "Server error responses": [500, 599],
            }
    client_errors = {
            400: "Bad request",
            402: "Payment required",
            403: "Forbidden",
            404: "Not Found",
            405: "Method not allowed",
            406: "Not acceptable",
            407: "Proxy Authentication Required",
            408: "Request timeout",
            409: "Conflict",
            410: "Gone",
            411: "Length Required",
            412: "Precondition Failed",
            413: "Content too large",
            414: "URL Too Long",
            415: "Unsupported Media Type",
            416: "Range Not Satisfied",
            417: "Expectation Failed",
            418: "I'm a teapot",  # yep... you saw it!
            421: "Misdirected Request",
            422: "Unprocessible Content (Webdav)",
            423: "Locked (Webdav)",
            424: "Failed Dependency (Webdav)",
            425: "Too Early",
            426: "Upgrade Required",
            428: "Precondition Required",
            429: "Too Many Rquests",
            431: "Request Header Fields Too Large",
            451: "Unavailable for Legal Reasons",
            }
    server_errors = {
            500: "Internal Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
            505: "HTTP Version Not Supported",
            506: "Variant Also Negotiates",
            507: "Insufficient Storage",
            508: "Loop Detected",
            510: "Not Extended",
            511: "Network Authentication Required",
            }
    if code:
        code = int(code)
        if code == 200:
            rtrn = "Success"
        if code in client_errors:
            # dbug(f"Found {code=} in {client_errors=}")
            rtrn = client_errors[code]
        if code in server_errors: 
            # dbug(f"Found {code=} in server_errors")
            rtrn = server_errors[code]
        if prnt:
            dbug(f"{code=} {rtrn=}", 'boxed')
    if prnt and isempty(code):
        box1 = gtable(categories, 'noprnt', 'hdr', title='Categories', footer=dbug('here'), pivot=True, colnames=['Key','Start', "End"])
        box2 = gtable(client_errors, 'noprnt', 'hdr', title='Client Errors', footer=dbug('here'), pivot=True, colnames=['Key','Value'])
        box3 = gtable(server_errors, 'noprnt', 'hdr', title='Server Errors', footer=dbug('here'), pivot=True, colnames=['Key','Value'])
        gcolumnize([box1, box2, box3], 'prnt', 'boxed', title='Principle HTML Return Codes', footer=dbug('here'), cols=3)
    # dbug(f"Returning  from {code=} {rtrn=}")
    return rtrn
    # ### EOB def html_codes(*args, **kwargs): ### #


# # ##########################
# def my_doc(*args, **kwargs):
#     # ######################
#     """
#     purpose: my_doc grabs the function's documentation
#     requires:
#     options:
#         - funcname: str=called_from('funcname')
#     returns: funcname doc
#     notes:
#         - WIP
#         - 20260215-1034
#         - this fails.... the problem here is that gtoolz can not "see" the calling script's functions
#     """
#     prnt = arg_val(['prnt', 'print'], args, kwargs, dflt=False)
#     fname = arg_val(["fname", "func", "funcname"], args, kwargs, dflt=called_from('func'))
#     doc_l = [line for line in eval(fname + ".__doc__").split("\n") if line]
#     if prnt:
#         dbug(doc_l, 'boxed')
#     return doc_l
#     # ### EOB def my_doc(*args, **kwargs): ### #


def mydoc(func):
    """
    purpose: mydoc is a wrapper/docorator that grabs the function's documentation
    requires: none (as func is passed)
    options: none
    returns: funcname doc but it also prints dbug(this_doc, 'boxed')
    notes:
        - WIP
        - 20260215-1034
        - this is experimental
        - I would love to make print optional
    A decorator that prints the docstring of the wrapped function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Access and print the docstring of the original function
        # print(f"{wrapper.__doc__=}")
        # this_doc = str(wrapper.__doc__).split("\n")
        this_doc = wrapper.__doc__.split("\n")
        this_doc = [line for line in this_doc if line]
        dbug(this_doc, 'boxed')
        return func(*args, **kwargs, my_doc=this_doc)
    return wrapper


def lazy_load(pkg, *args, **kwargs):
    """
    purpose: use but install of upgrade first
    requires:
    options:
    returns:
    notes:
      - WIP
      - 20260528-1006
    """
    try:
      # Run pip install --upgrade for the package
      # subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
      cmd = f"{sys.executable} -m pip install --upgrade {pkg}"
      # dbug(cmd)
      out,rc = run_cmd(cmd, 'both')
      if rc != 0:
          printit(out, 'prnt', 'boxed', 'noask', title=f"debugging {called_from('v')}i {cmd=}", footer=dbug('here'), box_clr='red!')  # debugging only
      # Import or reload the package into global memory
      globals()[pkg] = __import__(pkg)
    except Exception as Error:
      print(f"Failed to upgrade {pkg}. {Error=} Attempting standard import...")
      globals()[pkg] = __import__(pkg)
    return



# ##### Main Code #######
def main(args=""):  # ######
    # ###################
    """
    purpose: allows user to see some of the fuctionality of this tool set
    """
    # dbug(sys.argv, 'ask')
    # ### Note: {0}-cli <cmd. [<fargs>...] is handles by handeOPTS ### #
    #       ie: {0} <cmd> [<fargs>...]
    # dbug(args, 'ask')
    # """--== SEP_LINE ==--"""
    if args['--arch']:
        arch(__file__, days=60, prnt=True, boxed=True, stats=True, centered=True)
        do_close()
    if not args['-T'] or '-cli' not in sys.argv[0]:
        do_logo("Companionway", box_color="red! on black!")
        printit(handleOPTS.__doc__, 'boxed', 'centered', title='debugging', footer=dbug('here'))
        credits_caveats = """I offer sincere thanks to any and all who have shared or posted code that has helped me produce this file.
        I am sure there are much better ways to achieve the results provided in every function or class etc.
        Please let me know of any problems, issues, improvements or suggestions.     geoff.mcanamara@gmail.com
        """
        credits_caveats = [ln.lstrip() for ln in credits_caveats.split("\n")]
        printit(credits_caveats, 'centered', 'boxed', box_color="blue on black!", txt_center=99)
    else:
        # dbug(args, 'ask')
        do_cli(args)
    # dbug(args)
    # do_cli(args)
    # """--== EOB main() ==--"""


if __name__ == "__main__":
    args = docopt(handleOPTS.__doc__, version=SCRIPT + "\nversion: " + __version__)
    handleOPTS(args)
    main(args)
