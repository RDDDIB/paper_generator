Report Documentation
====================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Using This Module
-----------------

The general usage looks like this:

.. code:: python

    report = Report(title='File Title',
                    author='Your Name',
                    root='./',
                    lhead='Date',
                    chead='Document Title',
                    rhead='Your Organisation',
                    count_pos='cfoot',
                    packages=['required', 'packages'])

    report.new_section('Section Header',
                       'Section Body')
    report.auto_generate(clean_tex=False)


Full Report Class Documentation
-------------------------------

.. autoclass:: paper_generator.Report
   :members:
   :special-members:
