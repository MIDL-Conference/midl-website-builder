import re

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


"""
Extension for div wrappers with the syntax [% .class #id "css: value;" %] and [% / %]
"""
DIV_WRAPPER_RE = re.compile(r'\[%(?P<attr>[^%]*)%\]')
DIV_ATTR_RE = re.compile(r'"(?P<style>[^"]+)"|\.(?P<class>[^\s]+)|#(?P<id>[^\s]+)')


class DivWrapExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(DivWrapPreprocessor(md), 'divwrap', 19)  # return after HTML preprocessor


class DivWrapPreprocessor(Preprocessor):
    def run(self, lines):
        new_text = []
        for line in lines:
            m = DIV_WRAPPER_RE.match(line)
            if not m:
                new_text.append(line)
                continue

            attributes = m.group('attr').strip()
            if attributes == '/':
                tag = '</div>'
            else:
                id = None
                classes = []
                styles = []

                for m in DIV_ATTR_RE.finditer(attributes):
                    attr = m.groupdict()
                    id = attr['id']
                    if attr['class']:
                        classes.append(attr['class'])
                    if attr['style']:
                        styles.append(attr['style'])

                tag = '<div'
                if id is not None:
                    tag += ' id="{}"'.format(id)
                if len(classes) > 0:
                    tag += ' class="{}"'.format(' '.join(classes))
                if len(styles) > 0:
                    tag += ' style="{};"'.format('; '.join(s.strip(';') for s in styles))
                tag += '>'

            new_text.append('')
            new_text.append(tag)
            new_text.append('')

        return new_text
