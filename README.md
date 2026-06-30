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
$ python3 app.py -p ../caioluders.github.io/ 
/home/g3ol4d0/Desktop/caioluders.github.io
/home/g3ol4d0/Desktop/caioluders.github.io/h4ck1ng
/home/g3ol4d0/Desktop/caioluders.github.io/4rt3
/home/g3ol4d0/Desktop/caioluders.github.io/4rt3/Haikais
/home/g3ol4d0/Desktop/caioluders.github.io/4rt3/1337
/home/g3ol4d0/Desktop/caioluders.github.io/4rt3/Concretos
```

Now on every directory will have a `index.html` file like the above image.

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
    "r4nd0m": [
        {"name": "my-project", "url": "https://github.com/you/my-project", "title": "A cool tool", "date": "1700000000"},
        {"name": "another", "url": "https://github.com/you/another"}
    ]
}
```

Each link object: `name` (the displayed text), `url` (the link target), optional `title` (description column), and optional `date` (Unix timestamp or any string).

`hide_dirs` : (Object) Hide specific subdirectories from a folder's `Index of` listing. Each key is a folder path (relative to the website root) and each value is an array of directory names to omit from that folder's listing. The directories are still generated/recursed — they just don't show up in the parent index.

```
"hide_dirs": {
    "h4ck1ng": ["img"]
}
```

Note: the `theme` path is resolved relative to the site (`--path`) first, so you can keep the template inside the website repo; if not found there it falls back to the body-builder directory.

## Template theme

This script uses the template string of Python. The default templates are [templates/default.html](templates/default.html) and [templates/dark.html](templates/dark.html) , use those as base.
You can create any HTML file to use as template but it has to have those variables 

`$blog_title` : The title from the config file.

`$latest_entry` : The content of the latest file.

`$posts_table` : The HTML table of the files.
