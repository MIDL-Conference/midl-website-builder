import sys

from os import path
from argparse import ArgumentParser
from .builder import WebsiteBuilder, WebsiteBuildError


# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('srcdir', default='.')
parser.add_argument('dstdir', default='./public')
parser.add_argument('--silent', action='store_true')
args = parser.parse_args()

# Build website
builder = WebsiteBuilder(path.abspath(args.srcdir), verbose=not args.silent)
try:
    builder.build(path.abspath(args.dstdir))
except WebsiteBuildError as error:
    if not args.silent:
        print(error)
    sys.exit(-1)
else:
    sys.exit(0)
