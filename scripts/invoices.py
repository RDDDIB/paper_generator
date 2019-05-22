#!/usr/bin/python3
"""An invoice report for the Transplant House of Cleveland."""
from datetime import datetime
from os.path import join
import glob
import re
import dateparser
import pandas as pd
from paper_generator import Report


def prep_dataframe(data):
    """A wrapper for pandas to_latex().

    Args:
        data  A pandas DataFrame.
    """
    return data.to_latex(index=True, escape=False, longtable=True)


def text_bold(text):
    """Add latex wrapper to make the text bold."""
    return r'\textbf{' + str(text) + r'}'


class InvoiceData:
    """A class to collect all the useful data and manipulations."""
    def __init__(self, start_date='last month', end_date='today', abbr=False):
        """init"""
        self.data = None
        self.abbr = abbr
        self.start_date = start_date
        self.end_date = end_date
        self.date_format = r'%m/%d/%y'
        self.date_col = "Invoice Date"
        self.start_date = dateparser.parse(start_date).replace(day=1)
        self.end_date = dateparser.parse(end_date).replace(day=1)
        self.payors = {'Guest Payor': 'P',
                       'Paid by Subsidy from Clev Clinic': 'CC',
                       'Paid by Family Assistance Fund': 'FAF',
                       'Community Member paid for Smith Family': 'SF',
                       'Paid by a Foundation': 'F',
                       'Paid by 3rd Party': '3'}

    def print_range(self):
        """Output date range in a human-readable format."""
        return (self.start_date.strftime('%b %d, %Y'),
                self.end_date.strftime('%b %d, %Y'))

    def load_csv(self, name, file_dir='./'):
        """load_csv

        :param name:
        :param file_dir:
        """
        self.data = pd.read_csv("%s%s.csv" % (file_dir, name))

    def load_csv_dir(self, file_dir='./'):
        """Load a directory of csv files and concatenate them."""
        all_files = glob.glob(join(file_dir, "*.csv"))
        self.data = pd.concat((pd.read_csv(dfile,
                                           usecols=[0, 1, 2, 4, 5, 6, 7])
                               for dfile in all_files))

    def _parse_dates(self):
        """Convert each date to a string then parse."""
        aware = 'RETURN_AS_TIMEZONE_AWARE'
        self.data[self.date_col] = self.data[self.date_col].astype(str)
        self.data[self.date_col] = [dateparser.parse(date,
                                                     settings={aware: False})
                                    for date in self.data[self.date_col]]

    def number_of_entries(self):
        """Return the length of the data table."""
        return len(self.data)

    def _abbreviate_payors(self):
        """Replace payors with abbreviated codes."""
        self.data['Paid By'] = [self.payors[payor]
                                for payor in self.data['Paid By']]

    def _abbreviate_names(self):
        """Try to shorten patient and caregiver names."""
        self.data['Name'] = [re.sub(r'(^|and )(\w)[^ ]+', r'\g<1>\g<2>.',
                                    name)
                             for name in self.data['Name']]

    def _keep_range(self):
        """Drop any entries outside the set date range."""
        if self.start_date:
            self.data = self.data[self.data[self.date_col] >= self.start_date]
        if self.end_date:
            self.data = self.data[self.data[self.date_col] <= self.end_date]

    def prepare_data(self):
        """Perform preliminary cleanup and computations."""
        if self.data is None:
            raise Exception("Load some data first!")
        self.data.dropna(inplace=True)
        self._parse_dates()
        self._keep_range()
        if self.abbr:
            self._abbreviate_payors()
            self._abbreviate_names()


def main():
    """main"""
    pd.options.display.float_format = r'\${:,.2f}'.format

    rootdir = "./"
    indices = ['Name', 'Paid By']
    columns = ['Total Paid', 'Amount Due ']

    print("Your input is rounded down to the month.")
    start_date = input('Start Date (default: last month) ')
    end_date = input('End Date (default: today) ')
    print("Generating report...")

    # Load file containing walk-in data
    print("Loading csv file...", end='')
    invoices = InvoiceData(start_date, end_date, abbr=True)
    invoices.load_csv_dir(file_dir=join(rootdir, "data/"))
    print("DONE")

    print("Hiding entries not between %s and %s..." % (start_date, end_date),
          end='')
    invoices.prepare_data()
    print("DONE")
    print("Abbreviating payors...", end='')
    print("DONE")
    print("Abbreviating names...", end='')
    print("DONE")

    print("Building pivot tables...", end='')
    invoice_report = pd.pivot_table(invoices,
                                    index=indices,
                                    values=columns,
                                    margins=True,
                                    margins_name='Total')

    invoices.data = invoices.data[invoices.data['Paid By'] == 'CC']
    indices = ['Name', 'Invoice Date']

    clvclinic_report = pd.pivot_table(invoices,
                                      index=indices,
                                      values=columns,
                                      margins=True,
                                      margins_name='Total')
    print("DONE")

    print("Writing report...", end='')
    bform = r'%m/%d/%y'
    title = 'Guest Billing Report'
    full_title = '%s %s to %s' % (title, start_date, end_date)
    report = Report(title=full_title,
                    author='Roland Baumann',
                    root=rootdir,
                    show_title=False,
                    lhead='Generated %s' % datetime.today().strftime(bform),
                    rhead=title,
                    cfoot='Transplant House of Cleveland',
                    count_pos='rfoot',
                    toc=False,
                    packages=['booktabs', 'longtable',
                              'underscore', 'graphicx'])

    report.new_section('Payor Key', '')
    msg = r'\begin{description}'
    for full, sym in invoices.payors.items():
        msg += r'\item[' + '%s] %s' % (sym, full)
    msg += r'\end{description}'
    report.add_to_section('Payor Key', msg)
    report.new_section('All Invoices in the Billing Period',
                       prep_dataframe(invoice_report))
    report.add_to_section('All Invoices in the Billing Period',
                          report.page_break())
    report.new_section('Invoices to Cleveland Clinic',
                       prep_dataframe(clvclinic_report))
    print("DONE")
    report.auto_generate(clean_tex=False)
    print("Report saved as %sreports/%s.pdf" % (rootdir, full_title))


if __name__ == "__main__":
    main()
