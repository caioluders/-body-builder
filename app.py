#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import argparse
import functools
import datetime
import string
import operator
import json
import re
import markdown
from html import escape
from email.utils import format_datetime
from urllib.parse import quote, urljoin
from zoneinfo import ZoneInfo
from pathlib import Path
from xml.dom import minidom
from search_index import write_search_index

def finish_page(document, cfg):
	"""Attach site-owned scripts to every generated page, including articles."""
	scripts = '\n'.join('<script defer src="%s"></script>' % escape(src, quote=True)
		for src in cfg.get('page_scripts', []))
	if scripts:
		document = document.replace('</body>', scripts + '\n</body>', 1)
	return document

def make_rss(posts, cfg, path) :
	root = minidom.Document()

	rss = root.createElement("rss")
	rss.setAttribute("version","2.0")
	root.appendChild(rss)

	channel = root.createElement("channel")
	rss.appendChild(channel)

	title = root.createElement("title")
	title.appendChild(root.createTextNode(cfg["title"]))
	channel.appendChild(title)

	link = root.createElement("link")   
	link.appendChild(root.createTextNode(cfg["url"]))
	channel.appendChild(link)
	
	description = root.createElement("description") 
	description.appendChild(root.createTextNode(cfg["footnote"]))
	channel.appendChild(description)
	

	for p in [tp for tp in posts if len(tp) == 3]:
		# check if p[2] is epoch time
		if not p[2].isdigit():
			continue

		item = root.createElement("item")
				
		title = root.createElement("title")
		title.appendChild(root.createTextNode(p[1]))
		item.appendChild(title)

		link = root.createElement("link")
		print(p[0])
		relative = os.path.relpath(p[0], path).replace(os.sep, '/')
		link.appendChild(root.createTextNode(urljoin(cfg["url"].rstrip('/') + '/', quote(relative))))
		item.appendChild(link)

		description = root.createElement("description")
		description.appendChild(root.createTextNode("A blog post"))
		item.appendChild(description)

		pubDate = root.createElement("pubDate")
		# convert p[2] to epoch time
		published = datetime.datetime.fromtimestamp(int(p[2]), ZoneInfo(cfg.get('timezone', 'UTC')))
		pubDate.appendChild(root.createTextNode(format_datetime(published)))
		item.appendChild(pubDate)

		channel.appendChild(item)

	return root.toprettyxml(indent="  ")

def parse_file(file):
	try:
		f = Path(file).read_text(encoding='utf-8').splitlines()
		# Strip a leading Markdown heading marker ("# Title" -> "Title").
		title = re.sub(r"^#+\s*", "", f[0])
		return {"title": title, "date": f[1]}
	except:
		return {"title": "", "date": ""}

def parse_markdown(file, template, cfg):
	f = Path(file).read_text(encoding='utf-8')
	metadata = parse_file(file)
	# A plain first-line title is also supported by the source format.
	if f.strip():
		first, separator, rest = f.partition('\n')
		f = '# ' + re.sub(r'^#+\s*', '', first) + separator + rest

	template_style = re.search("<style>(.*)</style>", template, re.MULTILINE | re.DOTALL).group(1)

	html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%s</title>
<style>
%s
</style>
</head>

<body>""" % (escape(metadata['title']), template_style)

	html += markdown.markdown(f, extensions=['fenced_code', 'codehilite'])
	html += '<hr><footer class="site-byline">%s</footer></body></html>' % (cfg["footnote"])
	return finish_page(html, cfg)

def break_on_slash(text):
	# Strip the scheme for display and insert zero-width break opportunities
	# after slashes so long URLs wrap.
	text = re.sub(r"^https?://", "", text)
	return text.replace("/", "/<wbr>")

def make_link_row(link, cfg):
	date = link.get("date", "")
	if str(date).isdigit():
		date = datetime.datetime.fromtimestamp(int(date), ZoneInfo(cfg.get('timezone', 'UTC'))).strftime("%d/%m/%Y")
	return """<tr>
	<td><a href="%s">%s</a></td>
	<td>%s</td>
	<td>%s</td>
</tr>
""" % (escape(link["url"], quote=True), break_on_slash(escape(link["name"])), escape(link.get("title", "")), escape(str(date)))

def make_index(root, dirs, files, cfg, local_path):
	path = os.path.abspath(root)

	template = Path(cfg["theme"]).read_text(encoding='utf-8')

	table_html = ""

	print(path)

	if path != os.path.abspath(local_path):
		table_html += """<tr>
	<td><a href="../">../</a></td>
	<td></td>
	<td></td>
</tr>
"""

	rel_path = os.path.relpath(path, local_path).replace(os.sep, '/')
	if rel_path == '.':
		rel_path = ''

	hidden_dirs = cfg.get("hide_dirs", {}).get(rel_path, [])

	for d in dirs:
		if d in hidden_dirs:
			continue
		table_html += """<tr>
	<td><a href="%s">%s</a></td>
	<td>%s</td>
	<td>%s</td>
</tr>
""" % (quote(d) + "/", escape(d) + "/", "Directory", "-")

	# Rows that carry a date (hardcoded links + files), sorted together below.
	dated_rows = []

	for link in cfg.get("link_folders", {}).get(rel_path, []):
		sortkey = int(link["date"]) if str(link.get("date", "")).isdigit() else 0
		dated_rows.append((sortkey, make_link_row(link, cfg)))

	files_dated = []

	for f in files:
		metadata = {"title": "RSS feed", "date": ""} if f == 'rss.xml' and path == local_path and cfg.get('rss') else parse_file(os.path.join(path, f))
		if f[-3:] == ".md":
			html_md = parse_markdown(os.path.join(path, f), template, cfg)
			Path(path, f[:-3] + '.html').write_text(html_md, encoding='utf-8')
			try:
				files_dated.remove([f[:-3] + ".html", "<!DOCTYPE html>", "<html>"])
			except:
				pass
			files_dated.append([f[:-3] + ".html", metadata["title"], metadata["date"]])
			continue
		elif f[-5:] == ".html":
			continue
		_file_metadata = [os.path.join(path, f), metadata["title"], metadata["date"]]
		if not any(_file_metadata[0] in fff for fff in files_dated):
			files_dated.append(_file_metadata)

	for f in files_dated:
		f = [f[0].replace(local_path, "").split("/")[-1] , f[1], f[2]]
		sortkey = int(f[2]) if f[2].isdigit() else 0
		row = """<tr>
	<td><a href="%s">%s</a></td>
	<td>%s</td>
	<td>%s</td>
</tr>
""" % (quote(f[0]), escape(f[0]), escape(f[1]), (datetime.datetime.fromtimestamp(int(
			f[2]), ZoneInfo(cfg.get('timezone', 'UTC'))).strftime("%d/%m/%Y") if f[2].isdigit() else escape(f[2])))
		dated_rows.append((sortkey, row))

	dated_rows.sort(key=operator.itemgetter(0), reverse=True)
	table_html += "".join(html for _, html in dated_rows)

	html_result = string.Template(template).substitute({
		"posts_table": table_html,
		"blog_title": cfg["title"],
		"footnote": cfg["footnote"]
	})

	Path(path, 'index.html').write_text(finish_page(html_result, cfg), encoding='utf-8')

	return [[os.path.join(path, f[0]), f[1], f[2]] for f in files_dated]

def main(args):
	path = os.path.abspath(args.path)

	config = json.loads(Path(args.config).read_text(encoding='utf-8'))

	# Prefer a theme that lives inside the site, falling back to the CWD path.
	site_theme = os.path.join(path, config["theme"])
	if os.path.exists(site_theme):
		config["theme"] = site_theme

	# Create folders that only hold hardcoded links so os.walk lists them.
	for folder in config.get("link_folders", {}):
		os.makedirs(os.path.join(path, folder), exist_ok=True)

	all_posts = []
	search_sources = []

	for root, dirs, files in os.walk(path):
		if root == path and config.get('rss') and 'rss.xml' not in files:
			files.append('rss.xml')
		files = sorted([
			f for f in files if not f[0] == '.' and f not in config["ignore"]
		])
		dirs[:] = sorted(d for d in dirs
				   if not d[0] == '.' and d not in config["ignore"])  # ignore hidden files/dirs
		search_sources.extend(os.path.join(root, f) for f in files if f.endswith(('.md', '.txt')))

		posts = make_index(os.path.join(path, root), dirs, files, config, path)
		all_posts.extend(posts)
	if config.get('search_index'):
		write_search_index(search_sources, config, path)

	if config["rss"]:
		Path(path, 'rss.xml').write_text(make_rss(all_posts, config, path), encoding='utf-8')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Create a blog from .md files")
	parser.add_argument('-p', '--path', help="Path of the files.")
	parser.add_argument('-c', '--config', help='Config file.', default="default_config.json")
	args = parser.parse_args()

	main(args)
