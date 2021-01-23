# Disk Image File Recovery

CONTENTS OF THIS FILE
---------------------

 * Introduction
 * Installation

INTRODUCTION
------------
A python project to recover files from a disk image. The supported recoverable files are [MPG, PDF, BMP, GIF, ZIP, JPG, DOCX, AVI, and PNG].
In addition to recovering the files, the project also finds the SHA-256 value for each of the recovered files. The recovery process is done by looking for the signatures (headers and footers) for each of the available file types that are supported.


INSTALLATION
------------

```sh
$ python main.py mystery.dd
```



