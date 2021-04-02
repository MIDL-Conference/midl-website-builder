import http.server
import sys

from os import path
from argparse import ArgumentParser
from functools import partial

from .builder import WebsiteBuilder


# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('srcdir', default='.')
parser.add_argument('dstdir', default='./output')
parser.add_argument('--silent', action='store_true', help='Do not display any info during compilation.')
parser.add_argument('--verbose', action='store_true', help='Display all compiled pages, not only errors.')
parser.add_argument('--prettify', action='store_true')
parser.add_argument('--no-minify', action='store_true')
parser.add_argument('--serve', action='store_true', help='Start a webserver after building the site')
args = parser.parse_args()
args.minify = not args.no_minify

# Build website
builder = WebsiteBuilder(
    path.abspath(args.srcdir),
    verbose=args.verbose, silent=args.silent,
    minify=args.minify, prettify=args.prettify
)
builder.build(path.abspath(args.dstdir))

# Start webserver?
if args.serve:
    handler_class = partial(http.server.SimpleHTTPRequestHandler, directory=args.dstdir)
    with http.server.ThreadingHTTPServer(('localhost', 8000), handler_class) as httpd:
        host, port = httpd.socket.getsockname()[:2]
        print(f"Serving website on port {port} from {args.dstdir} ...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt")
            sys.exit(0)
