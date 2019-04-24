import sys

from os import path
from argparse import ArgumentParser
from .builder import WebsiteBuilder


# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('srcdir', default='.')
parser.add_argument('dstdir', default='./public')
parser.add_argument('--silent', action='store_true')
args = parser.parse_args()

# Build website
builder = WebsiteBuilder(path.abspath(args.srcdir), verbose=not args.silent)
builder.build(path.abspath(args.dstdir))
