#!/usr/bin/python
"""A report generator for the Center for International Affairs."""
from datetime import datetime
from os.path import join
import glob
import dateparser
import numpy as np
import pandas as pd
from paper_generator import Report

"""
* TODO summary by timeslot

    - busiest timeslot
    - most common reason

* TODO focus the sections
* TODO seasonal weight of reason
* TODO show count of reason
"""


def prep_dataframe(data):
    """A wrapper for pandas to_latex().

    Args:
        data  A pandas DataFrame.
    """
    return data.to_latex(index=True, escape=False, longtable=True)


def find_time_slot(date, hours):
    """Categorize a date into the timeslot it belongs to.

    Args:
        date    The date to label.
        hours   A partition of the day.
    """
    hr_range = r'%H'
    slots = [date.replace(hour=i) for i in hours]
    for start, end in zip(slots[:-1], slots[1:]):
        if start <= date < end:
            return '%s - %s' % (start.strftime(hr_range),
                                end.strftime(hr_range))
    return 'Unknown'


def text_bold(text):
    """Add latex wrapper to make the text bold."""
    return r'\textbf{' + str(text) + r'}'


class WalkinData:
    """A class to collect all the useful data and manipulations."""
    def __init__(self):
        """init"""
        self.data = None
        self.date_columns = {'initial': 'Entered',
                             'middle': 'Started',
                             'final': 'Completed'}
        self.date_format = r'%m/%d/%y'

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
        for col in self.date_columns.values():
            self.data[col] = self.data[col].astype(str)
            self.data[col] = [dateparser.parse(date, settings={aware: False})
                              for date in self.data[col]]

    def _assign_timeslots(self):
        """Assign each entry a timeslot."""
        initial = self.date_columns['initial']
        self.data['Timeslot'] = [find_time_slot(date, range(0, 24, 1))
                                 for date in self.data[initial]]

    def _compute_wait(self):
        """Add a column with the wait time in minutes."""
        initial = self.date_columns['initial']
        middle = self.date_columns['middle']
        self.data['Wait'] = self.data[middle] - self.data[initial]
        self.data['Wait'] = [int(date.total_seconds() / 60)
                             for date in self.data['Wait']]

    def _compute_meet(self):
        """Add a column with the meeting duration in minutes."""
        middle = self.date_columns['middle']
        final = self.date_columns['final']
        self.data['Meeting'] = self.data[final] - self.data[middle]
        self.data['Meeting'] = [int(date.total_seconds() / 60)
                                for date in self.data['Meeting']]

    def _delete_nulls(self):
        """Drop null durations."""
        for col in ['Wait', 'Meeting']:
            self.data = self.data[self.data[col] != 0]

    def number_of_entries(self):
        """Return the length of the data table."""
        return len(self.data)

    def compute_range(self):
        """Return the earliest and latest date."""
        return (min(self.data['Entered']).strftime(self.date_format),
                max(self.data['Entered']).strftime(self.date_format))

    def unique_reasons(self):
        """Return a set of unique reasons."""
        return set(self.data['Reason'])

    def most_freq_reason(self):
        """Find the most frequent reason and return all entries with this
            reason.
        """
        mainr = max(self.unique_reasons(),
                    key=lambda r: len(self.data[self.data['Reason'] == r]))
        return mainr, self.data[self.data['Reason'] == mainr]

    def compute_wait_mean(self):
        """Average wait time overall."""
        return int(np.mean(self.data['Wait']))

    def compute_meet_mean(self):
        """Average meeting duration overall."""
        return int(np.mean(self.data['Meeting']))

    def compute_meet_quartiles(self):
        """Calculate the lower, median, and upper quartiles."""
        return [np.percentile(self.data['Meeting'], quart)
                for quart in [25, 50, 75]]

    def _compute_inner_fence(self):
        """Calculate inner fence using interquartile range."""
        lower, _, upper = self.compute_meet_quartiles()
        inter = upper - lower
        edge = inter * 1.5
        return (lower - edge, upper + edge)

    def _compute_outer_fence(self):
        """Calculate outer fence using interquartile range."""
        lower, _, upper = self.compute_meet_quartiles()
        inter = upper - lower
        edge = inter * 3
        return (lower - edge, upper + edge)

    def _is_major_outlier(self, entry):
        """Check that the entry falls beyond the outer fence."""
        lower, upper = self._compute_outer_fence()
        return (entry < lower) or (entry > upper)

    def _is_minor_outlier(self, entry):
        """Check that the entry falls between the inner and outer fences."""
        if self._is_major_outlier(entry):
            return False
        lower, upper = self._compute_inner_fence()
        return (entry < lower) or (entry > upper)

    def _drop_major_outliers(self):
        """Drop any entries with abnormal meeting times."""
        outliers = list(map(self._is_major_outlier, self.data['Meeting']))
        outliers = [not outlier for outlier in outliers]
        self.data = self.data[outliers]

    def prepare_data(self):
        """Perform preliminary cleanup and computations."""
        if self.data is None:
            raise Exception("Load some data first!")
        self.data.dropna(inplace=True)
        self._parse_dates()
        self._compute_wait()
        self._compute_meet()
        self._delete_nulls()
        self._drop_major_outliers()
        self._assign_timeslots()


def main():
    """main"""
    # Set default float format
    pd.options.display.float_format = '{:,.0f}'.format

    # Set root directory
    rootdir = "./"

    # Load the data
    walkins = WalkinData()
    walkins.load_csv_dir(file_dir=join(rootdir, "data/"))
    walkins.prepare_data()

    # Aggregate functions to use in the pivot tables
    funcs = [np.min, np.max, np.mean]

    pivots = {}
    # Generate a pivot table
    #                     Wait - Meeting
    # Timeslot - Reason -
    pivots['time_reason'] = pd.pivot_table(walkins.data,
                                           index=['Timeslot', 'Reason'],
                                           values=['Wait', 'Meeting'],
                                           aggfunc={'Wait': funcs,
                                                    'Meeting': funcs},
                                           dropna=True)

    # Generate a pivot table
    #                          Wait - Meeting
    # Timeslot - CIA Adviser -
    pivots['time_advisor'] = pd.pivot_table(walkins.data,
                                            index=['Timeslot', 'CIA Adviser'],
                                            values=['Wait', 'Meeting'],
                                            aggfunc={'Wait': funcs,
                                                     'Meeting': funcs},
                                            dropna=True)

    # Generate a pivot table
    #          Wait - Meeting
    # Reason -
    pivots['reason'] = pd.pivot_table(walkins.data,
                                      index=['Reason'],
                                      values=['Wait', 'Meeting'],
                                      aggfunc={'Wait': funcs,
                                               'Meeting': funcs},
                                      dropna=True)

    # Default date format
    bform = r'%m/%d/%y'
    # Save file title
    full_title = 'Walk_In_Report'
    # Make notes bold
    main_reason_name, main_reason = walkins.most_freq_reason()
    disclaimer = (
        'This report has been automatically generated from our '
        'Walk-In records. Please keep in mind that any conclusions drawn '
        'from the following analysis may not be indicative of actual '
        'behavior and activity due to glitches in the recording macro, '
        'human error, or parsing issues. '
    )
    msg = (
        'This report is generated to provide some basic analysis of '
        'our records '
        'of students who make use of our Walk-In hours at the Center for '
        'International Affairs. '
        'The analysis is performed on %s entries.\n\n'
        'Overall wait time averages '
        '%s minutes while the average length of an advisory meeting is '
        '%s minutes. The most frequent reason is %s with an average meeting '
        'time of %s minutes, a minimum recorded meeting time of %s minutes, '
        'and a maximum recorded meeting time of %s minutes.'
    ) % (text_bold(walkins.number_of_entries()),
         text_bold(walkins.compute_wait_mean()),
         text_bold(walkins.compute_meet_mean()),
         text_bold(main_reason_name),
         text_bold(int(np.mean(main_reason['Meeting']))),
         text_bold(int(np.min(main_reason['Meeting']))),
         text_bold(int(np.max(main_reason['Meeting']))))

    report = Report(title=full_title,
                    author='Roland Baumann',
                    root=rootdir,
                    show_title=False,
                    lhead='Generated %s' % datetime.today().strftime(bform),
                    rhead='Walk In Report (%s - %s)' % walkins.compute_range(),
                    cfoot='International Student Services',
                    count_pos='rfoot',
                    toc=True,
                    packages=['booktabs', 'longtable',
                              'underscore', 'graphicx'])

    sections = {
        'Disclaimer': disclaimer,
        'General Statistics and Some Explanation': msg,
        'Reason Summary': prep_dataframe(pivots['reason']),
        'Walk Ins By Reason': prep_dataframe(pivots['time_reason']),
        'Walk Ins By Advisor': prep_dataframe(pivots['time_advisor'])
    }

    report.sections_from_dict(sections)
    for title in sections:
        report.add_to_section(title, report.page_break())
    report.auto_generate(clean_tex=True)
    print("Report saved as %sreports/%s.pdf" % (rootdir, full_title))


if __name__ == '__main__':
    main()
