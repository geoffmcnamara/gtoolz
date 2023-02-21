# gtoolz

This repository is for holding python(3+) tools that I frequently need

Simply run gtoolz.py (or see ./test/test_gtoolz.py) to see some of the possible uses.

## gtoolz.py a collection of tools to help produce collect data, produce charts or tables from any type of data

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

You can get a sense of some of the functionality by running gtoolz.py from the command line.

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

Enjoy

geoff.mcnamara@gmail.com
