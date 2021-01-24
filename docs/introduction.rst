============
Introduction
============

Purpose
~~~~~~~

The aim of mcetl is to ease the repeated processing of data files. Contrary to its name, mcetl
can process any tabulated files (txt, csv, tsv, xlsx, etc.), and does not require that the files originate
from materials characterization. However, the focus on materials characterization was selected because:

* Most data files from materials characterization are relatively small in size (a few kB or MB).
* Materials characterization files are typically cleanly tabulated and do not require handling
  messy or missing data.
* It was the author's area of usage and naming things is hard...

mcetl requires only a very basic understanding of Python to use, and allows a single person to
create a tool that their entire group can use to process data and produce Excel files with a
consistent style. mcetl can create new Excel files when processing data or saving peak fitting
results, or it can append to an existing Excel file to easily work with already created files.

Limitations
~~~~~~~~~~~

* Data from files is fully loaded into memory for processing, so mcetl is not
  suited for processing files whose total memory size is large (e.g. cannot
  load a 10 GB file on a computer with only 8 GB of RAM).
* mcetl does not provide any resources for processing data files directly from
  characterization equipment (such as .XRDML, .PAR, etc.). Other libraries such
  as `xylib <https://github.com/wojdyr/xylib>`_ already exist and are capable of
  converting many such files to a format mcetl can use (txt, csv, etc.).
* The peak fitting and plotting modules in mcetl are not as feature-complete as
  other alternatives such as `Origin <https://originlab.com>`_,
  `fityk <https://fityk.nieto.pl>`_, `SciDAVis <https://sourceforge.net/projects/scidavis/>`_,
  etc. The modules are included in mcetl in case those better alternatives are not
  available, and the author highly recommends using those alternatives over mcetl if available.
