# gtoolz

This repository is for holding python(3+) tools that I frequently need

## Install

pip install gtoolz

  or

see: [https://github.com/geoffmcnamara/gtoolz]

Note: In version 0.1.5 I lowered the required Pandas version. As a result you may have to install the latest version specifically:
   eg: pip install gtoolz==0.1.5  # or latest version

## Use

Simply run gtoolz.py (or see ./test/test_gtoolz.py) to see some of the possible uses.

## Features

### gtoolz.py a collection of tools to help produce collect data, produce charts or tables from any type of data

* a useful breakpoint type debugging tool is included (ie dbug(msg or variable... etc))
* tools for colorizing text of boxes or tables
* tools to build colorful tables data including pandas, list of lists, lists of dictionaries, csv files etc
* tools to put (colorized) boxes around text or lines of text
* tools to center output on the screen
* tools to place shadows around boxes
* tools for running shell commands with options to manipulate output
* tools to pull data from files lines of output and build tables, lists of lists, or pandas, etc
* rudimentary progress bars or percentage bar
* spinners while others tasks are carried out
* tools to read HTML tables and turn it into colorful ascii table with selected columns and/or filtered data
* other tools to manipulate text or data
* tools to build ascii dashboards or columns of boxes or blocks

This set of tools offers over 100 functions.

Some examples:

* gtable() accepts a list of lists or a dataframe and will display the data in a table (with lots of options to alter the table)
* gselect() accepts a list or dictionary and displays either keys or numbered listing in a box and returns what you want - it is a type of menu selection
* usr_update() takes a dictionary and presents each (or selected) values to the user for editing and replacing
* printit() accepts a list or a string and prints, options include boxing (with or without a shadow), centering, wraping text, etc 
* kvcols() takes a dictionary of key_value pairs and displays in columnized tables
* gcolumnize() puts lists or lists of lists into columns, also see gblocks which positions blocks within blocks (lines of strings all the same length)
* gclr() will return ansii codes for colorizing text - several differnt ways to colorize including tags, rgb, or simple strings
* progess() bars, do_prcnt_bar() , Spinner()
* boxed() puts text in a box with options for color, centering etc - see also shadowed()
* centered() centers text on a screen
* cinput() input user supplied text in the center of the screen
* askYN() prompts for a response and returns a boolean - several options including centering and defaults
* dbug() quick way to display file:function:lineno and optionally a message or variable or simple stop and ask Continue? or return silently the file:function:lineno
* cond_num() has several uses including setting rounding, colorizing negative or positive numbers, "humanizing" large numbers etc
* isnumber() tests if a string is a number, int, float etc also see has_alpha()
* isempty() tests if pretty much anything is empty or None
* islol() test to see if the supplied data is a list of lists see also islod() <-- is it a list of dictionaries
* remap_keys() allows you to alter a dictionary with new keys, optionally select on some key-value pairs and reorder the dictionary
* addit() will add or replace a line in a file or a list based on the pattern you provide
* from_to() will select lines between two patterns from a file or a list
* comma_split() or comma_join() or get_elems() splits or joins a list or string line by line using commas and will quote some if needed for use as CSV file input
* get_html_tables() grabs all tables in a web page (I do a lot of financial research and this tool is quite handy in that regard)
* gwrap() will text wrap any text to specified max length (was previously called wrapit but I pretty much rewrote the whole thing.
* scr_dims) will return the number of columns available on the terminal screen (and or rows available)
* gline() allows returning a line or specified length with a title, fill characters, corner charaters etc - used in making boxes etc also see gtitle()
* fixlol() will make ever row in a list of list the same length with several options - used with gtable() to "fix" broken data
* cnvrt() will take data in several formats and turn that data into rows of columns (a list of lists) or do the reverse
* chunkit() breaks a list into small chunks
* get_random_line() selects a random line from a file or list (I use this with a file of quotes to give me a random quote)
* run_cmd() a simple routine to run a shell command and return the output (optionally the return code)
* grep_lines() pull matching lines from a file or list
* list_files() list files from a directory (or a list of directorries) and optionally with a matching pattern etc see also select_file()
* escape_ansi() strips off ansii color codes (used to determine real length of printed strings etc)
* nclen() uses escape_ansi to get the no-color length of a string
* do_edit() will bring up the file in an vim editor - I use this to quickly edit code while running the code
* do_logo(), do_close() these just offer a quick way to open an application with a logo box and the close with a message box
* arg_val() this is used in almost every function I write to easily manage boolen options or key_val arguments to functions


Example of use in code:

```python
from gtoolz import Spinner, boxed, printit
sym = "AAPL"
boxes = []
with Spinner("Working...", 'elapsed', elapsed_clr="yellow! on black"):
    url = f"https://finance.yahoo.com/quote/AAPL?p={sym}&.tsrc=fin-srch"
    tables = get_html_tables(url)
    for num, table in enumerate(tables, start=1):
        print()
        box = (gtable(table, 'hdr', 'prnt', title=f"Table {num} sym: {sym}", footer=dbug('here'), cols_limit=5, col_limit=20))
        boxes.append(box)
lines = gcolumnize(boxes, cols=2)
printit(lines, 'boxed', 'centered', title=f"Symbol: {sym} url: {url}", footer=dbug('here'))
```
## The name (gtoolz)
People might think that the name gtoolz starts with "g" because of my first name (Geoff) but the truth is this project evolved from a previous tool I had written call gomenu. So the "g" stands for "go". I couldn't use gtools (with an "s" at the end) because someone already used that name.

--------------------------------------------

Enjoy,

[email: geoff.mcnamara@gmail.com]
