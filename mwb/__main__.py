from os import path
from argparse import ArgumentParser
from .builder import WebsiteBuilder


# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('srcdir', default='.')
parser.add_argument('dstdir', default='./public')
parser.add_argument('--silent', action='store_true')
parser.add_argument('--prettify', action='store_true')
parser.add_argument('--no-minify', action='store_true')
args = parser.parse_args()
args.minify = not args.no_minify

# Build website
builder = WebsiteBuilder(path.abspath(args.srcdir), verbose=not args.silent,
                         minify=args.minify, prettify=args.prettify)
builder.build(path.abspath(args.dstdir))
