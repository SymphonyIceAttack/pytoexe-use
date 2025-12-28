#!/usr/bin/env python

import argparse
import itertools
import math
import sys
import re
from file_wrapper import FileWrapper, HexByteWrapper

parser = argparse.ArgumentParser(description="Apply a patch to a file")
parser.add_argument('source')
parser.add_argument('-b', '--base', default='0',
    help="Location (in hex) to start patch", metavar="addr")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-p', '--patch', default=argparse.SUPPRESS,
  help="Patch file", metavar="filename")
group.add_argument('-x', '--hexpatch', default=argparse.SUPPRESS,
    help="Patch content in hex", metavar="HEX_NUMBER")
parser.add_argument('-o', '--output', required=True,
  help="Output location", metavar="filename")
parser.add_argument('-k', '--block', default=None, type=int,
    help="Process files in blocks of N kilobytes (useful if patching extremely large files). If this option is used, ensure that the output file will not overwrite any of the input files.")

args = vars(parser.parse_args())

patch_base = int(args['base'], 16)


source = FileWrapper( args['source'], 'r', blocksize=args['block'] )
patch = FileWrapper( args['patch'], 'r', blocksize=args['block'] ) \
    if 'patch' in args else \
    HexByteWrapper( args['hexpatch'] )

if len(source) < patch_base + len(patch):
  print "Base + Patch size is larger than Source file. Aborting."
  sys.exit(1)

# If the user did not specify a block size, the files have been slurped in and
# closed. Open output as normal.
output = open(args['output'], 'w+')

# These two patch styles are different enough to warrant not using abstraction
if args['block'] is None:
  file_data = source.data()
  file_data[patch_base : patch_base + len(patch)] = patch.data()
  output.write("".join(file_data))
else:
  blocksize = args['block']
  written = 0
  for i in range(patch_base / blocksize):
    buf = source.read(blocksize)
    if len(buf) != blocksize:
      print "something horrible has happened"
    output.write("".join(buf))
    written += len(buf)

  buf = source.read(patch_base-written)
  output.write("".join(buf))
  written += len(buf)

  print "Patching at: 0x%x"%(source.tell())
  patch_size = len(patch)
  while patch_size > 0:
    buf = patch.read(min(patch_size, blocksize))
    output.write("".join(buf))
    source.seek(len(buf), 1)
    written += len(buf)
    patch_size -= len(buf)

  while True:
    buf = source.read(blocksize)
    if len(buf) == 0:
      break
    output.write("".join(buf))
    written += len(buf)

