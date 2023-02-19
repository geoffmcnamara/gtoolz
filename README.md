# gtoolz

This repository is for holding python(3+) tools that I frequently need

Simply run nicetools.py to see some of the possible uses.

Tool File:

* gtoolz.py a collection of tools to help produce charts or tables from data
  * debugging tool
  * tools for colorizing text of boxes or tables
  * tools to tabulize data including pandas, list of lists, lists of dictionaries, csv files etc
  * tools to put (colorized) boxes around text or lines of text
  * tools to center output on the screen
  * tools to place shadows around boxes
  * tools for running shell commands with options to manipulate output
  * tools to pull data from files lines of output and build tables, lists of lists, or pandas, etc
  * rudimentary progress bars or percentage bar
  * spinners while others tasks are carried out
  * tools to read html tables and turn it into colorfull ascii table with selected columns and/or filtered data
  * other tools to manipulate text or data

This set of tools offers over 100 functions. 

You can get a sense of some of the functionality by running gtoolz from the command line.

Example of use in code:

```python
import random
from gtoolz import printit, dbug, funcname, docvars, gselect, quick-plot, gtable  # etc

lines = []
with Spinner("Working...", 'elapsed', elapsed_clr="yellow! on black"):
  for n in range(5):
    lines.append([f"This is line {n}", f"col1val")
```

Enjoy

geoff.mcnamara@gmail.com
