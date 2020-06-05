# MIDL website builder (mwb)

The `mwb` package builds static HTML websites from content written in MarkDown or HTML format, combined
with a theme package that defines the layout and styling. For the MIDL conference series, this setup
ensures that websites can be efficiently hosted and served. The use of a theme ensures that the websites
of the individual editions of the conference share the same look and feel.

Each years edition will have a website maintained mostly by the conference organizers. To make
editing and deploying the website as simple as possible, many components that are usually very
much configurable in static website generators are fixed and the repository structure is hardcoded.

## Installation

Using pipenv:

```
cd midl-website-2018/
pipenv install -e git+https://github.com/MIDL-Conference/midl-website-builder.git@1.0#egg=mwb
```

This installs version 1.0 with all dependencies.

## Usage

Just call the module and specify input and output paths:

```
pipenv run python -m mwb . output/
```

By default, the builder displays information about the build process. This can be disable with
 the `--silent` switch.

The builder produces minified HTML. This can be turned off with the `--no-minify` switch. The
produced HTML can optinally also be prettified with the `--prettify` switch. These are mainly
intended for debugging purposes and not for a production environment.

## Features and expected structure

### Main configuration (`website.yaml`)

Every website is required to have a configuration file named `/website.yaml` at the root of the
project folder. This configures the builder and the theme. All values from this file are also
available in content files as well as theme layout files in the variable `config` (for example,
`{{ config.theme }}` in a content file would print out the name of the active theme).

### Content

Content files can be either MarkDown (`.md`) or HTML (`.html`). The location of content files needs
to be specified in `/website.yaml` as either a string or a list of strings. For example, the entry

```yaml
content: ["pages", "more_pages"]
```

results in all md/html files first from the directory `/pages` and then from `/more_pages` being
parsed, combined with the layout and written to the output folder as html files. Files are processed
recursively, so the file `/pages/sub/hello.md` is converted into the file `/output/sub/hello.html`.
When multipe directories are specified, pages with the same name overwrite pages from previous
directories. In the example above, if there was a page `index.md` in both `/pages` and `/more_pages`,
only the latter would end up in the output directory.

In the default template, the content is in `/pages` and alternative content (a temporary placeholder
website which is used while the actual content is being prepared) is in `/placeholder`. By default,
the placeholder is rendered. Changing the configuration in `/website.yaml` into `content: "pages"`
deactivates the placeholder website.

Each content file can optionally contain a header in YAML format. This header is separated from the
actual content by three dashes, for example:

    ---
    title: "The theme puts this value into the <title> tag"
    layout: "placeholder"
    ---
    
    # Actual content

This metadata can be used to choose a layout ("placeholder" layout in the example above) and to define
variables for that layout. The title defined above would be available in the layout template in the
variable `{{ title }}`.

### Static files

All files and folders in `/static` are recursively copied to the output directory. Images, documents,
etc. should therefore be stored in this folder. These files will be copied after files from the theme
have been copied (from the theme's `static` directory), so that theme files like the logo or favicon can
be replaced.

### Layouts

Layouts are HTML files that define the structure of the website. In a typical setup, these are part of
theme and do not require further configuration, the default layout will work for most pages.

A very basic layout file would be:

```html
<!DOCTYPE html>
<html lang="en-US">
    <head>
        <title>MIDL</title>
    </head>
    <body>
        {{ content }}
    </body>
</html>
```

Layouts are part of themes in the theme's subdirectory `layouts`, but there can also be website
specific layouts in `/layouts`.

### Stylesheets

In most cases, there will be no need for stylesheet files other than those from the theme. SASS (`.scss`)
files in `/themes/{theme-name}/stylesheets` and then `/stylesheets` are automatically compiled into CSS,
unless their filename begins with an underscore. The resulting CSS files are written to `assets/css` in the
output directory.

In content and layout files, the absolute path to all compiled CSS files is available in the variable
`stylesheets`, for example, the CSS file generated from `twitter.scss` can be referenced like this:

```html
<link rel="stylesheet" href="{{ stylesheets.twitter.path }}">
```

### Themes

Themes are stored in `/themes` and the active theme is specified in `/website.yaml` as the name
of the theme folder. The default theme is configured as `theme: midl-website-theme` and loaded
from the directory `/themes/midl-website-theme`.

Themes are ideally (like the default theme) git submodules, i.e., standalone git repositories.
This enables using the same theme across multiple websites. When the MIDL standard theme is
changed, all websites using that theme only need to pull the new version of the submodule to
refresh their layout and styling. 

Just like the actual website, themes can contain:

* Static files in the folder `static/`
* Layouts in the folder `layouts/`
* Stylesheets in the folder `stylesheets/`
