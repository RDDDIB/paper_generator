#!/usr/bin/python3
import sys
import re
import dateparser
import pandas as pd
from paper_generator import Report  # noqa: E402
import pandacsv as tools  # noqa: E402


def main():
    pd.options.display.float_format = r'\${:,.2f}'.format

    rootdir = "/home/di/projects/report_generator/reportR/"
    packages = ['booktabs', 'longtable', 'underscore', 'graphicx', 'lastpage']
    indices = ['Name', 'Paid By']
    columns = ['Total Paid', 'Amount Due ']

    payors = {'Guest Payor': 'P',
              'Paid by Subsidy from Clev Clinic': 'CC',
              'Paid by Family Assistance Fund': 'FAF',
              'Community Member paid for Smith Family': 'SF',
              'Paid by a Foundation': 'F',
              'Paid by 3rd Party': '3'}

    print("Your input is rounded to the month before.")
    start_date = input('Start Date (default: last month) ')
    end_date = input('End Date (default: today) ')
    abbr = input('Abbreviate Firstnames? ').lower()
    if not start_date:
        start_date = 'last month'
    if not end_date:
        end_date = 'today'
    literal_start_date = dateparser.parse(start_date).replace(day=1)
    literal_end_date = dateparser.parse(end_date).replace(day=1)
    start_date = literal_start_date.strftime('%b %d, %Y')
    end_date = literal_end_date.strftime('%b %d, %Y')
    print("Generating report...")

    # Load file containing walk-in data
    print("Loading csv file...", end='')
    invoices = tools.load_csv(dir=rootdir + "data/",
                              name="ExceedGuestInvoiceList")
    print("DONE")

    print("Hiding entries not between %s and %s..." % (start_date, end_date),
          end='')
    invoices = tools.parse_dates(invoices, 'Invoice Date')
    invoices = invoices[invoices['Invoice Date'] >= literal_start_date]
    invoices = invoices[invoices['Invoice Date'] < literal_end_date]
    print("DONE")

    print("Abbreviating firstnames...", end='')
    if abbr and abbr in 'yes':
        invoices['Name'] = [re.sub(r'(^|and )(\w)[^ ]+', r'\g<1>\g<2>.', name)
                            for name in invoices['Name']]
    print("DONE")

    print("Abbreviating payors...", end='')
    invoices['Paid By'] = [payors[payor] for payor in invoices['Paid By']]
    print("DONE")

    print("Building pivot tables...", end='')
    invoice_report = pd.pivot_table(invoices,
                                    index=indices,
                                    values=columns,
                                    margins=True,
                                    margins_name='Total')

    invoices = invoices[invoices['Paid By'] == 'CC']
    indices = ['Name', 'Invoice Date']

    clvclinic_report = pd.pivot_table(invoices,
                                      index=indices,
                                      values=columns,
                                      margins=True,
                                      margins_name='Total')
    print("DONE")

    print("Writing report...", end='')
    title = 'Guest Billing Report'
    edit_date = dateparser.parse('today').strftime('%m/%d/%Y')
    full_title = '%s %s to %s' % (title, start_date, end_date)
    report = Report(title=full_title,
                    author='Roland Baumann',
                    root=rootdir,
                    show_title=False,
                    lhead='Generated %s' % edit_date,
                    chead=title,
                    rhead='Transplant House of Cleveland',
                    count_pos='cfoot',
                    toc=False,
                    packages=packages)

    report.new_section('Payor Key', '')
    msg = r'\begin{description}'
    for full, sym in payors.items():
        msg += r'\item[' + '%s] %s' % (sym, full)
    msg += r'\end{description}'
    report.add_to_section('Payor Key', msg)
    report.new_section('All Invoices in the Billing Period',
                       tools.prep_dataframe(invoice_report))
    report.add_to_section('All Invoices in the Billing Period',
                          report.page_break())
    report.new_section('Invoices to Cleveland Clinic',
                       tools.prep_dataframe(clvclinic_report))
    print("DONE")
    report.auto_generate(clean_tex=False)
    print("Report saved as %sreports/%s.pdf" % (rootdir, full_title))


if __name__ == "__main__":
    main()
