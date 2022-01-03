# Semi-purpose-built and semi-customizable script to download and configure favicons.

import argparse
import glob
import markdown
import os
import pathlib
import re
import requests
import urllib

parser = argparse.ArgumentParser()
parser.add_argument("markdown_directory", help="Path to directory with HTML files to scan for links.")
parser.add_argument("icon_directory", help="Path to directory to store downloaded icons in.")
parser.add_argument("favicon_css_outfile_path", help="Path to write the CSS to.")
parser.add_argument("your_site_url", help="Your site's url (without HTTP(s)).")
args = parser.parse_args()

ICONSERVER_URL="http://localhost:8080"

def get_links(string):
    """return a list with markdown links

    Reference: https://github.com/andrewp-as-is/markdown-link-extractor.py/blob/master/markdown_link_extractor/__init__.py"""
    html = markdown.markdown(string, output_format='html')
    links = list(set(re.findall(r'href=[\'"]?([^\'" >]+)', html)))
    links = list(filter(lambda l: l[0] != "{", links))
    return links

def get_baselinks(string):
    http_links = [link for link in get_links(content) if "http" in link]
    parsed_links = [urllib.parse.urlparse(link) for link in http_links]

    return [f"{link.scheme}://{link.netloc}" for link in parsed_links]

def get_icon_query_url(link, size="16..16..100"):
    return f"{ICONSERVER_URL}/icon?url={link}&size={size}";

os.chdir(args.markdown_directory)
links = []
for filename in glob.glob("*.md"):
    with open(filename, 'r') as f:
        content = f.read()
        baselinks = get_baselinks(content)
        links += baselinks

if links:
    css = []
    css += [f"a:not([href*='{args.your_site_url}']):not([href^='#']):not([href^='/']):after {{"]
    css += ["  background-position: 0 center;"]
    css += ["  background-repeat: no-repeat;"]
    css += ["  background-size: 16px 16px !important;"]
    css += ["  content: '';"]
    css += ["  height: 16px;"]
    css += ["  margin-left: 0.5ch;"]
    css += ["  vertical-align: middle;"]
    css += ["  width: 16px;"]
    css += ["}"]


    unique_links = sorted(list(set(links)))
    for link in unique_links:
        netloc = urllib.parse.urlparse(link).netloc
        icon_data = requests.get(get_icon_query_url(link))
        extension = pathlib.Path(urllib.parse.urlparse(icon_data.url).path).suffix
        icon_filename = f"{netloc}{extension}"
        with open(f"{args.icon_directory}/{icon_filename}", "wb") as handler:
            handler.write(icon_data.content)

        css += [f"a[href*='{link}']:after {{"]
        css += [f"  background-image: url('/favicons/{icon_filename}');"]
        css += ["  padding-left: 16px;"]
        css += ["}"]

    with open(f"{args.favicon_css_outfile_path}", 'w') as css_file:
        css_file.write("\n".join(css))
