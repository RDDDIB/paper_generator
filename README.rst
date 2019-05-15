.. highlight:: rst

Paper Generator
===============

This is a wrapper for the PyLatex python module that generates elegant reports
on provided data and is easy to customize.

Full documentation will be up soon.

Requirements
------------

* `Python <python.org>`_

  + (This will also install `pip`.)

* `TeX Live <http://www.tug.org/texlive/>`_ (This may take a while to
  install...)

Installation
------------

* If you have downloaded a `zip` archive of this repository, be sure to unzip it
  somewhere in your home directory.
* Enter the root of this directory.
* Open a terminal in the directory (from the `File` tab in Windows Explorer) and
  run ::

    py -m pip install .[pandas, date, numpy]

The command above ensures that the extra packages needed for the specialized
scripts are installed and/or upgraded.

Usage
-----

* Make a new directory somewhere in your home directory to house your data and
  reports.
* Copy the appropriate script from the `scripts` folder to the new directory.
* Create two folders named `data` and `reports`.

  + `data` will contain any `csv` files needed for data analysis.
  + `reports` will contain the generated `PDF` reports.

* Fill `data` with all the necessary files.
* Run the script and follow any instructions that appear.

If you find any bugs or unexpected behavior, please open an issue and I will
check it out as soon as I can.
