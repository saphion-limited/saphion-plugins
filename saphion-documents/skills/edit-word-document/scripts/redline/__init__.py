"""Faithful edits to a Word file: the parts of a .docx are changed one at a time and every other part is kept byte for byte.

Libraries (licence checked 1 November 2026, S10a): lxml 6.1.3 (BSD-3-Clause) reads and writes the XML parts; python-docx 1.2.0 (MIT) is used
only to check that the result opens and still holds its comments. Both are pinned in the file sandbox image (docker/file-sandbox/requirements.txt).
This package is Saphion's own code, written from the ECMA-376 / ISO 29500 WordprocessingML specification and the libraries' documentation.
"""
