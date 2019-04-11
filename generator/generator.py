#!/usr/bin/python
"""A basic report generator class.
"""
import re
import pylatex as pl


class Report:
    """Report"""
    def __init__(self, **kargs):
        """Generates a PDF report.

        Args:
            author          The author of the paper.
            title           The title of the paper.
            toc             Display table of contents if True.
            root            The root directory.
            glossary_file   A file containing def/thm/cor/prop/lemma.
            outline_file    A file containing the section outline.
            bib_file        A file containing a bibliography.
            refs            A dictionary of labels and their associated
                            environments.
            packages        Required LaTeX packages.
        """
        self.args = kargs
        self.doc = pl.Document(geometry_options={'margin': '1in'})
        options = ['12pt']
        self.twocolumn = kargs.get('twocolumn')
        if not self.twocolumn:
            self.twocolumn = False
        if self.twocolumn:
            options.append('twocolumn')
        self.doc.documentclass = pl.Command(
            'documentclass',
            options=options,
            arguments=['article'],
        )

        self.args['headers'] = ['lhead', 'chead', 'rhead',
                                'lfoot', 'cfoot', 'rfoot']
        self.args['heads'] = {}
        for pos in self.args['headers']:
            self.args['heads'][pos] = kargs.get(pos)

        if 'bib_file' in self.args:
            self.args['packages'].append('biblatex')
        self.sections = {}
        self.glossary = {}
        self.outline = []
        self.kinds = {}

    def _has_headers(self):
        return any(self.args['heads'].values())

    def _check_fancyhdr(self):
        if 'fancyhdr' not in self.args['packages']:
            self.args['packages'].append('fancyhdr')
        if self.args['count_pos'] in self.args['headers']:
            if 'lastpage' not in self.args['packages']:
                self.args['packages'].append('lastpage')
            msg = r'Page~\thepage\ of~\pageref{LastPage}'
            self.args['heads'][self.args['count_pos']] = pl.NoEscape(msg)

    def _add_headers(self):
        self.doc.preamble.append(pl.Command('pagestyle', 'fancy'))
        self.doc.preamble.append(pl.Command('fancyhf', ' '))
        for pos, val in self.args['heads'].items():
            if val:
                self.doc.preamble.append(pl.Command(pos, val))

    def _load_packages(self):
        """Add packages to preamble."""
        for package in self.args['packages']:
            self.doc.packages.append(pl.Package(package))

    def load_section_from_file(self, title, file):
        """Replace the references in a file and create a section containing
        the result.

        Args:
            title       The name of the new section.
            file        The filename of the file to import.
        """
        with open(file, 'r') as reader:
            data = reader.read()
        content = self._parse_refs(data)
        if title in self.sections:
            self.add_to_section(title, content)
        else:
            self.new_section(title, content)

    def _load_glossary(self):
        """Read the glossary and create a dict indexed by labels."""
        if not self.args['glossary_file']:
            raise Exception("Glossary file not set.")
        location = self.args['root'] + self.args['glossary_file']
        with open(location, 'r') as reader:
            data = reader.read()

        # parse file for entries
        kind_format = r'(' + '|'.join(self.kinds.keys()) + r')'
        entry_format = kind_format + r'\s(.+?)\n(.+?)END'
        entries = re.findall(entry_format, data, re.S)

        # create an object for each entry
        self.glossary = {self.args['refs'].lower() + ':' + label.strip():
                         {'kind': kind, 'body': body.strip()}
                         for (kind, label, body) in entries}

    def _load_bib(self):
        if not self.args['bib_file']:
            raise Exception("Bibliography file not set.")
        arg = [self.args['root'] + self.args['bib_file']]
        self.doc.preamble.append(pl.Command('bibliography', arguments=arg))

    def _load_outline(self):
        """Create new sections from a plaintext outline."""
        if not self.args['outline_file']:
            raise Exception("Outline file not set.")
        location = self.args['root'] + self.args['outline_file']
        with open(location, 'r') as reader:
            data = reader.readlines()
        for line in data:
            self.new_section(line.strip())

    @staticmethod
    def page_break():
        """page_break"""
        return pl.NoEscape(r'\newpage')

    def _gen_toc(self):
        """Add a table of contents to body."""
        self.doc.append(pl.Command('tableofcontents'))

    def _gen_title(self):
        r"""Add metadata to preamble and `\maketitle` to body."""
        date = pl.NoEscape(r'\today')
        self.doc.preamble.append(pl.Command('title', self.args['title']))
        self.doc.preamble.append(pl.Command('author', self.args['author']))
        self.doc.preamble.append(pl.Command('date', date))
        self.doc.append(pl.NoEscape(r'\maketitle'))

    def new_section(self, title, content=''):
        """Create a new section.

        Args:
            title       The header for the new section.
            content     The material to display in the new section.
        """
        if title in self.sections:
            raise Exception("A section with the given title already exists.")
        # By default, append section to outline
        self.sections[title] = content
        self.outline.append(title)

    def add_to_section(self, title, content):
        """Add content to an existing section.

        Args:
            label       The label of the section.
            content     The content to append.
        """
        if title not in self.sections:
            raise KeyError("That section does not exist.")
        section = self.sections[title]
        if section:
            section += content
        else:
            section = content
        self.sections[title] = section

    def move_section(self, currentpos, newpos):
        """Change the position of a section.

        Args:
            currentpos  The current position of the section.
            newpos      The new position of the section.
        """
        """
        [0 1 2 3 4 5 6]
        move 5 to 2
        [0 1 3 4 5 2 6]

        move 2 to 5
        [0 1 5 2 3 4 6]
        """
        ordering = list(range(len(self.outline)))
        if newpos >= len(self.outline):
            ordering.append(ordering.pop(currentpos))
        else:
            ordering.insert(newpos, ordering.pop(currentpos))
        self.reorder_outline(ordering)

    def reorder_outline(self, ordering):
        """Reorder the outline.

        Args:
            ordering    A list of integers representing the new positions.
        """
        self.outline = [self.outline[i] for i in ordering]

    def _insert_sections(self):
        """Add existing sections to the body."""
        for title in self.outline:
            body = self.sections[title]
            with self.doc.create(pl.Section(title)):
                self.doc.append(pl.NoEscape(body))

    def _prep_gloss_item(self, label):
        """Prepare a latex-ready item.

        Args:
            label   The string reference to a glossary item. This must have
                    the appropriate prefix.
        """
        raise NotImplementedError

    def _parse_refs(self, content):
        """Replace references in a string with the correct glossary item.

        Args:
            content     A string containing references.
        """
        raise NotImplementedError

    def initialize(self):
        """initialize"""
        if self._has_headers():
            self._check_fancyhdr()
        self._load_packages()
        if self._has_headers():
            self._add_headers()
        if self.args['toc']:
            self._gen_toc()
        if 'hide_title' not in self.args:
            self._gen_title()
        if 'outline_file' in self.args:
            self._load_outline()

    def prepare(self):
        """prepare"""
        self._insert_sections()

    def generate(self, clean_tex=True):
        """Generate the PDF."""
        self.doc.generate_pdf('%sreports/%s' % (self.args['root'],
                                                self.args['title']),
                              clean_tex=clean_tex)

    def auto_generate(self, clean_tex=True):
        """Run all the steps necessary for pdf generation.

        Args:
            dest    The directory in which to save the pdf.
        """
        self.initialize()
        self.prepare()
        self.generate(clean_tex)
