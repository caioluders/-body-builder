# &lt;body&gt;builder

This script will generate a `index.html` file for every directory recursively. The aim it's to create a simple static blog based on `Index Of`. 
The main differences of a simple `Index of` to this are : 
* Timestamp
* Markdown
* Templates
* Configurable
* RSS

![Screenshot](https://imgur.com/5XpqHAZ.png)


## Using

```
$ python3 app.py --help
usage: app.py [-h] [-p PATH] [-c CONFIG]

Create a blog from .txt files

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path of the files.
  -c CONFIG, --config CONFIG
                        Config file.

```

For the default usage simply :

```
$ python3 app.py -p /path/to/site -c /path/to/site/config.json
/path/to/site
/path/to/site/posts
/path/to/site/notes
```

Now on every directory will have a `index.html` file like the above image.

## Optional page scripts and local search

Python 3.9+ is required. Install the pinned dependencies once:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

One invocation generates directory indexes, Markdown pages, optional RSS, and optional search data:

```sh
.venv/bin/python app.py -p /path/to/site -c /path/to/site/config.json
```

These optional config fields apply to any site:

```json
{
    "page_scripts": ["/assets/site.js"],
    "search_index": "assets/search-index.json",
    "timezone": "UTC"
}
```

- `page_scripts`: deferred script URLs inserted before `</body>` in every generated page. Keep the JavaScript in your site; do not also include these scripts in its template. Omit this option for pages without injected scripts.
- `search_index`: output path relative to the site root. Omit it to disable search-data generation. The builder supplies JSON; the site supplies its search UI. Each entry has `title`, `url`, `category`, `date`, and plain-text `content`.
- `timezone`: IANA timezone used for directory dates, search dates, and RSS dates; defaults to `UTC`.

Search automatically includes nonempty `.md` and `.txt` sources throughout the same directory traversal used for page generation, plus configured `link_folders`. It respects `ignore` and hidden paths; `hide_dirs` only hides directory navigation, as before. New folders require no search-code changes. Local result URLs and RSS links preserve nested paths and the path prefix from `url`.

Keep templates and support-asset directories in `ignore` so their contents are not listed or indexed. Markdown articles inherit the configured template's inline styles and receive a title, viewport metadata, footnote, and configured scripts. Their first line becomes an H1, with or without a leading Markdown heading marker. Handwritten HTML files are left untouched, except `index.html`: directory index files are generated output and will be overwritten. Removing a Markdown source removes its navigation/search/RSS entries on the next build; its old HTML file must be removed separately if it should no longer be directly accessible.

Run the generic build regression tests:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Files

For the Timestamp features to work, each file has to have a [Unix Time](https://en.wikipedia.org/wiki/Unix_time) on it. The first line of a file will be interpreted as the Title and the second line as the Unix timestamp.  

## Customizing
If you want to customize the index files you can create a new config file and/or create a new template. 

### Config file
The default config file it's [default_config.json](default_config.json). 

```
{
    "theme": "templates/default.html",
    "title": "A blog",
    "url": "https://example.ple",
    "footnote": "by You",
    "rss": false,
    "ignore" : ["CNAME","index.html"]
}
```

#### Variables

`theme` : (String) File of the template theme

`title` : (String) The title of all index files

`url` : (String) The final URL of the website

`footnote` : (String) A footnote HTML text

`rss`: (Boolean) Set to true if you want to have an `rss.xml` file on every directory

`ignore` : (Array of strings) Filenames / Directories to ignore from the listing

`link_folders` : (Object) Create folders made of hardcoded external links instead of files. Each key is a folder path (relative to the website root) and each value is an array of link objects. The folder is created automatically and listed in its parent `Index of` like any other directory.

```
"link_folders": {
    "projects": [
        {"name": "my-project", "url": "https://github.com/you/my-project", "title": "A cool tool", "date": "1700000000"},
        {"name": "another", "url": "https://github.com/you/another"}
    ]
}
```

Each link object: `name` (the displayed text), `url` (the link target), optional `title` (description column), and optional `date` (Unix timestamp or any string).

`hide_dirs` : (Object) Hide specific subdirectories from a folder's `Index of` listing. Each key is a folder path (relative to the website root) and each value is an array of directory names to omit from that folder's listing. The directories are still generated/recursed — they just don't show up in the parent index.

```
"hide_dirs": {
    "posts": ["images"]
}
```

Note: the `theme` path is resolved relative to the site (`--path`) first, so you can keep the template inside the website repo; if not found there it falls back to the body-builder directory.

## Template theme

This script uses the template string of Python. The default templates are [templates/default.html](templates/default.html) and [templates/dark.html](templates/dark.html) , use those as base.
You can create any HTML file to use as template but it has to have those variables 

`$blog_title` : The title from the config file.

`$latest_entry` : The content of the latest file.

`$posts_table` : The HTML table of the files.
