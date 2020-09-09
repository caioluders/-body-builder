# &lt;body&gt;builder

This script will generate a `index.html` file for every directory recursively. The aim it's to create a simple static blog based on `Index Of`. 
The main differences of a simple `Index of` to this are : 
* Last entry feature
* Timestamp
* Templates
* Configurable

![Screenshot](https://i.imgur.com/T53JRxK.png)


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

Now on every directory will be a `index.html` file like the above image.

## Files

For the Latest Entry and the Timestamp features to work, each file has to have a [Unix Time](https://en.wikipedia.org/wiki/Unix_time) on it. The first line of a file will be interpreted as the Title and the second line as the Unix timestamp.  

## Customizing
If you want to customize the index files you can create a new config file and/or create a new template. 

### Config file
The default config file it's [default_config.json](default_config.json). 

```
{
    "theme": "templates/default.html",
    "title": "lude.rs",
    "ignore" : ["CNAME","index.html"]
}
```

#### Variables

`theme` : (String) File of the template theme

`title` : (String) The title of all index files

`ignore` : (Array of strings) Filenames to ignore from the listing

## Template theme

This script uses the template string of Python. The default templates are [templates/default.html](templates/default.html) and [templates/dark.html](templates/dark.html) , use those as base.
You can create any HTML file to use as template but it has to have those variables 

`$blog_title` : The title from the config file.

`$latest_entry` : The content of the latest file.

`$posts_table` : The HTML table of the files.
