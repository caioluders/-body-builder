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
from xml.dom import minidom

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
		link.appendChild(root.createTextNode(cfg["url"] + "/" + p[0].replace(path, "")))
		item.appendChild(link)

		description = root.createElement("description")
		description.appendChild(root.createTextNode("A blog post"))
		item.appendChild(description)

		pubDate = root.createElement("pubDate")
		# convert p[2] to epoch time
		pubDate.appendChild(root.createTextNode(datetime.datetime.fromtimestamp(int(p[2])).strftime("%a, %d %b %Y %H:%M:%S %z")))
		item.appendChild(pubDate)

		channel.appendChild(item)

	return root.toprettyxml(indent="  ")

def parse_file(file):
	try:
		f = open(file, "r").read().splitlines()
		# Strip a leading Markdown heading marker ("# Title" -> "Title").
		title = re.sub(r"^#+\s*", "", f[0])
		return {"title": title, "date": f[1]}
	except:
		return {"title": "", "date": ""}

def parse_markdown(file, template, cfg):
	f = open(file, "r").read()

	template_style = re.search("<style>(.*)</style>", template, re.MULTILINE | re.DOTALL).group(1)

	html = """<!DOCTYPE html>
<html>
<style>
%s
</style>
<head>
  <meta charset="UTF-8">
</head>

<body>""" % (template_style)

	html += markdown.markdown(f, extensions=['fenced_code', 'codehilite'])
	html += "</body><hr>%s</html>" % (cfg["footnote"])
	return html

def break_on_slash(text):
	# Strip the scheme for display and insert zero-width break opportunities
	# after slashes so long URLs wrap.
	text = re.sub(r"^https?://", "", text)
	return text.replace("/", "/<wbr>")

def make_link_row(link):
	date = link.get("date", "")
	if str(date).isdigit():
		date = datetime.datetime.fromtimestamp(int(date)).strftime("%d/%m/%Y")
	return """<tr>
	<td><a href="%s">%s</a></td>
	<td>%s</td>
	<td>%s</td>
</tr>
""" % (link["url"], break_on_slash(link["name"]), link.get("title", ""), date)

def make_index(root, dirs, files, cfg, local_path):
	path = os.path.abspath(root)

	template = open(cfg["theme"], "r").read()

	table_html = ""

	print(path)

	table_html += """<tr>
	<td><a href="../">../</a></td>
	<td></td>
	<td></td>
</tr>
"""

	rel_path = path.replace(local_path, "").strip("/")

	hidden_dirs = cfg.get("hide_dirs", {}).get(rel_path, [])

	for d in dirs:
		if d in hidden_dirs:
			continue
		table_html += """<tr>
	<td><a href="%s">%s</a></td>
	<td>%s</td>
	<td>%s</td>
</tr>
""" % (d, d, "Directory", "-")

	# Rows that carry a date (hardcoded links + files), sorted together below.
	dated_rows = []

	for link in cfg.get("link_folders", {}).get(rel_path, []):
		sortkey = int(link["date"]) if str(link.get("date", "")).isdigit() else 0
		dated_rows.append((sortkey, make_link_row(link)))

	files_dated = []

	for f in files:
		metadata = parse_file(os.path.join(path, f))
		if f[-3:] == ".md":
			html_md = parse_markdown(os.path.join(path, f), template, cfg)
			fw = open(os.path.join(path, f[:-3] + ".html"), "w")
			fw.write(html_md)
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
""" % (f[0], f[0], f[1], (datetime.datetime.fromtimestamp(int(
			f[2])).strftime("%d/%m/%Y") if f[2].isdigit() else f[2]))
		dated_rows.append((sortkey, row))

	dated_rows.sort(key=operator.itemgetter(0), reverse=True)
	table_html += "".join(html for _, html in dated_rows)

	html_result = string.Template(template).substitute({
		"posts_table": table_html,
		"blog_title": cfg["title"],
		"footnote": cfg["footnote"]
	})

	index_file = open(os.path.join(path, "index.html"), "w", encoding="utf-8")
	index_file.write(html_result)
	index_file.close()

	return files_dated

def main(args):
	path = os.path.abspath(args.path)

	config = json.loads(open(args.config).read())

	# Prefer a theme that lives inside the site, falling back to the CWD path.
	site_theme = os.path.join(path, config["theme"])
	if os.path.exists(site_theme):
		config["theme"] = site_theme

	# Create folders that only hold hardcoded links so os.walk lists them.
	for folder in config.get("link_folders", {}):
		os.makedirs(os.path.join(path, folder), exist_ok=True)

	all_posts = []

	for root, dirs, files in os.walk(path):
		files = [
			f for f in files if not f[0] == '.' and f not in config["ignore"]
		]
		dirs[:] = [d for d in dirs
				   if not d[0] == '.' and d not in config["ignore"]]  # ignore hidden files/dirs

		posts = make_index(os.path.join(path, root), dirs, files, config, path)
		all_posts.extend(posts)

	if config["rss"]:
		rss_file = open(os.path.join(path, "rss.xml"), "w", encoding="utf-8")
		rss_file.write(make_rss(all_posts, config, path))
		rss_file.close()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Create a blog from .md files")
	parser.add_argument('-p', '--path', help="Path of the files.")
	parser.add_argument('-c', '--config', help='Config file.', default="default_config.json")
	args = parser.parse_args()

	main(args)
