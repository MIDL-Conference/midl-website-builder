import yaml
import jinja2
import htmlmin
import shutil
import distutils.dir_util as dirutil

from os import path, makedirs
from glob import glob
from collections import OrderedDict
from numbers import Number
from yaml.error import YAMLError

from . import __version__ as mwb_version
from .markdown import Markdown, DivWrapExtension


# Suppress future warning when importing the scss package
import warnings
with warnings.catch_warnings():
    warnings.simplefilter(action='ignore', category=FutureWarning)
    import scss
    import scss.namespace
    import scss.types


def parse_content_file(filename):
    # Read file into buffers
    mode = '?'
    buffer = ''
    header_buffer = ''

    with open(filename, encoding='utf-8') as file_stream:
        for row in file_stream:
            header_delimiter = row.strip().startswith('---')

            if header_delimiter and mode != 'markup':
                if mode == '?':
                    mode = 'header'
                elif mode == 'header':
                    header_buffer = buffer
                    buffer = ''
                    mode = 'markup'
            else:
                buffer += row

    # Did we find a proper header?
    header = {'layout': 'default'}
    try:
        header.update(yaml.safe_load(header_buffer))
    except (YAMLError, TypeError):
        markup = header_buffer + buffer
    else:
        markup = buffer

    return header, markup


def convert_to_scss_variable(var):
    if isinstance(var, str):
        if var.startswith('#'):
            return scss.types.Color.from_hex(var)
        else:
            return scss.types.String(var)
    elif isinstance(var, Number):
        return scss.types.Number(var)
    elif isinstance(var, list):
        return scss.types.List(convert_to_scss_variable(v) for v in var)
    elif isinstance(var, dict):
        return scss.types.Map([(k, convert_to_scss_variable(v)) for k, v in var.items()])
    else:
        return scss.types.Null()


class WebsiteBuildError(Exception):
    pass


class WebsiteBuilder:
    def __init__(self, srcdir, verbose=False):
        self.srcdir = srcdir
        self.verbose = verbose

        self.config = self.read_global_configuration()

        # Populate scss namespace with variables from global configuration
        namespace = scss.namespace.Namespace()
        for name, value in self.config.items():
            converted_value = convert_to_scss_variable(value)
            namespace.set_variable('${}'.format(name), converted_value)

        self.scss_compiler = scss.compiler.Compiler(
            search_path=list(self.asset_dirs('stylesheets')),
            import_static_css=True,
            output_style='compressed',
            namespace=namespace
        )
        self.html_minifier = htmlmin.Minifier(remove_comments=True, remove_empty_space=True)
        self.markdown_parser = Markdown(
            extensions=['tables', 'attr_list', DivWrapExtension()]
        )

    def print(self, message):
        if self.verbose:
            print(message)

    def build(self, dstdir):
        # Clear output directory
        self.print('Preparing output directory')
        if path.exists(dstdir):
            shutil.rmtree(dstdir)
        makedirs(dstdir, exist_ok=True)

        # Copy static files
        self.print('Copying static files')
        for static_src in (self.theme, self.srcdir):
            static_dir = path.join(static_src, 'static')
            if path.exists(static_dir):
                dirutil.copy_tree(static_dir, dstdir)

        # Compile assets and pages
        self.print('Compiling stylesheets')
        stylesheets = self.compile_stylesheets(dstdir)

        self.print('Compiling pages')
        vars = {
            'mwb': {'version': mwb_version},
            'config': self.config,
            'stylesheets': stylesheets
        }
        self.compile_content(dstdir, vars)

    def read_global_configuration(self):
        for ext in ('yaml', 'yml'):
            cfgfile = path.join(self.srcdir, 'website.' + ext)
            if path.exists(cfgfile):
                with open(cfgfile, encoding='utf-8') as file_stream:
                    return yaml.safe_load(file_stream)

        return dict()

    @property
    def theme(self):
        try:
            theme_name = self.config['theme']
        except KeyError:
            theme_name = 'midl-website-theme'
        return path.join(self.srcdir, 'themes', theme_name)

    def asset_dirs(self, name, theme_assets_first=False):
        if theme_assets_first:
            asset_sources = (self.theme, self.srcdir)
        else:
            asset_sources = (self.srcdir, self.theme)

        for asset_source in asset_sources:
            asset_dir = path.join(asset_source, name)
            if path.exists(asset_dir):
                yield asset_dir

    def find_assets(self, name, ext, keep_ext=False):
        """Searches for files in subfolders with the specified name in both theme and local files"""
        assets = OrderedDict()

        for asset_dir in self.asset_dirs(name, theme_assets_first=True):
            asset_files = glob(path.join(asset_dir, '[!_]*{}'.format(ext)))
            for asset_file in asset_files:
                asset_name = path.basename(asset_file)
                if not keep_ext:
                    asset_name = asset_name[:-len(ext)]
                assets[asset_name] = asset_file

        return assets

    def compile_stylesheets(self, dstdir):
        # Prepare output directory
        css_dir = path.join(dstdir, 'assets', 'css')
        if not path.exists(css_dir):
            makedirs(css_dir)

        # Compile files
        stylesheets = self.find_assets(name='stylesheets', ext='.scss')
        compiled = dict()
        for name, scss_file in stylesheets.items():
            if self.verbose:
                print(' > compiling {}'.format(path.relpath(scss_file, self.srcdir)))

            # Compile from SCSS to CSS
            css = self.scss_compiler.compile(scss_file)
            css_file = path.join(css_dir, '{}.css'.format(name))

            # Write to output directory
            with open(css_file, 'w', encoding='utf-8') as file_stream:
                file_stream.write(css)

            # Populate dictionary with all compiled stylesheet files and their new locations
            compiled[name] = {
                'path': '/' + path.relpath(css_file, dstdir).replace('\\', '/')
            }

        return compiled

    def find_content(self, name, ext):
        """Searches for md and html files in the specified subfolder"""
        contents = dict()

        content_dir = path.join(self.srcdir, name)
        content_files = glob(path.join(content_dir, '**/[!_]*{}'.format(ext)), recursive=True)
        for content_file in content_files:
            content_name = path.relpath(content_file, content_dir)[:-len(ext)]
            contents[content_name] = content_file

        return contents

    def compile_content(self, dstdir, global_vars):
        # Prepare template parsing engine
        tpl_loader = jinja2.FileSystemLoader(list(self.asset_dirs('layouts')))
        tpl_env = jinja2.Environment(loader=tpl_loader)

        # Different location of the content?
        try:
            content_names = self.config['content']
        except KeyError:
            content_names = 'pages'

        # One (string) or multiple (list) content names are possible
        if not isinstance(content_names, list):
            content_names = [content_names]

        for ext in ('.md', '.html'):
            for content_name in content_names:
                pages = self.find_content(name=content_name, ext=ext)
                for page_name, page_file in pages.items():
                    if self.verbose:
                        print(' > compiling {}'.format(path.relpath(page_file, self.srcdir)))

                    # Read header and markup from file
                    header, markup = parse_content_file(page_file)

                    # Determine permalink of this page
                    try:
                        permalink = header['permalink']
                        if not permalink.startswith('/'):
                            permalink = '/' + permalink
                        if not permalink.endswith('.html') and not permalink.endswith('/') and permalink != '/':
                            permalink += '/'
                    except KeyError:
                        permalink = '/' + page_name.replace('\\', '/')
                        if permalink == 'index':
                            permalink = '/'
                        elif permalink.endswith('/index'):
                            permalink = permalink[:-len('index')]
                        else:
                            permalink += '.html'

                    if self.verbose:
                        print('   permalink: {}'.format(permalink))

                    # Render content
                    local_vars = global_vars.copy()
                    local_vars.update(header)
                    local_vars['permalink'] = permalink

                    try:
                        tpl_content = jinja2.Template(markup.strip())
                        markup = tpl_content.render(**local_vars)
                    except jinja2.exceptions.TemplateError as e:
                        if self.verbose:
                            print('Rendering page content failed: {}'.format(e.message))
                        continue

                    if ext == '.md':
                        # Parse markdown
                        markup = self.markdown_parser.convert(markup).strip()

                    local_vars['content'] = markup

                    # Render layout
                    try:
                        template = tpl_env.get_template(header['layout'] + '.html')
                        html = template.render(**local_vars)
                    except jinja2.exceptions.TemplateError as e:
                        if self.verbose:
                            print('Rendering page layout failed: {}'.format(e.message))
                        continue

                    # Clean up HTML
                    html = html.replace('\r\n', '\n').replace('\r', '\n')
                    html = self.html_minifier.minify(html)

                    # Write HTML to output directory
                    filename = permalink[1:]
                    if filename == '' or filename.endswith('/'):
                        filename += 'index.html'

                    html_file = path.join(dstdir, filename)
                    if self.verbose and path.exists(html_file):
                        print('   warning: overwriting existing page with same name!')

                    html_dir = path.dirname(html_file)
                    makedirs(html_dir, exist_ok=True)
                    with open(html_file, 'w', encoding='utf-8') as file_stream:
                        file_stream.write(html)
