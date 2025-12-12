# Semi-purpose-built and semi-customizable script to download and configure favicons.

import argparse
import glob
import markdown
import mimetypes
import os
import pathlib
import re
import requests
import urllib
import sys
import validators

parser = argparse.ArgumentParser()
parser.add_argument(
    "--markdown_directory",
    help="Path to directory with HTML files to scan for links.",
    required=True,
)
parser.add_argument(
    "--icon_directory",
    help="Path to directory to store downloaded icons in.",
    required=True,
)
parser.add_argument(
    "--favicon_css_outfile_path", help="Path to write the CSS to.", required=True
)
parser.add_argument(
    "--your_site_url", help="Your site's url (without HTTP(s)).", required=True
)
parser.add_argument(
    "--iconserver", help="Iconserver url.", default="http://localhost:8080", type=str
)
args = parser.parse_args()


def get_links_from_markdown(md):
    """Return a list with markdown links

    Reference: https://github.com/andrewp-as-is/markdown-link-extractor.py/blob/master/markdown_link_extractor/__init__.py
    """

    html = markdown.markdown(md, output_format="html")
    links = list(set(re.findall(r'href=[\'"]?([^\'" >]+)', html)))
    links = list(filter(lambda link: link[0] != "{", links))

    return links


def get_baselinks_from_markdown(md):
    http_links = [link for link in get_links_from_markdown(md) if "http" in link]
    parsed_links = [urllib.parse.urlparse(link) for link in http_links]

    return [f"{link.scheme}://{link.netloc}" for link in parsed_links]


def get_icon_query_url(link, iconserver_location, size="16..16..100"):
    return f"{iconserver_location}/icon?url={link}&size={size}"


def get_favicon_filename(link, response):
    """Return the filename to use for saving the provided url."""
    netloc = urllib.parse.urlparse(link).netloc
    extension = get_extension(response)

    return f"{netloc}{extension}"


def get_extension(response):
    """Return the file extension (with leading period) for use when saving the favicon at the provided url."""
    extension_from_path = pathlib.Path(urllib.parse.urlparse(response.url).path).suffix
    if extension_from_path:
        return extension_from_path

    content_type = response.headers["content-type"]

    return mimetypes.guess_extension(content_type)


def get_links_from_markdown_files(directory):
    """Return valid links from markdown files in DIRECTORY."""
    os.chdir(args.markdown_directory)
    links = []
    for filename in glob.glob("*.md"):
        with open(filename, "r") as f:
            links += get_baselinks_from_markdown(f.read())

    return [link for link in links if validators.url(link)]


# css += [f"  background-image: url('/favicons/{icon_filename}');"]
def css_for_favicon(link, favicon_path):
    """Return CSS string to display the favicon in :after."""
    return f"""a[href*='{link}']:after {{
      background-image: url('{favicon_path}');
      padding-left: 16px;
      margin-left: 0.5ch;
    }}"""


valid_links = get_links_from_markdown_files(args.markdown_directory)
if not valid_links:
    sys.exit("Failed to find any valid links.")

css = f"""a:not([href*='{args.your_site_url}']):not([href^='#']):not([href^='/']):after {{
  background-position: 0 center;
  background-repeat: no-repeat;
  background-size: 16px 16px !important;
  content: '';
  height: 16px;
  vertical-align: middle;
  width: 16px;
}}
"""
unique_links = set(valid_links)
hosts_with_existing_favicons = sorted(
    [pathlib.Path(filename).stem for filename in os.listdir(args.icon_directory)]
)
links_to_download = sorted(
    [
        link
        for link in unique_links
        if urllib.parse.urlparse(link).netloc not in hosts_with_existing_favicons
    ]
)

print(f"Downloading {len(links_to_download)} missing favicons")
for i, link in enumerate(links_to_download, start=1):
    print(f"({i}/{len(links_to_download)}) Downloading favicon for {link}")
    try:
        response = requests.get(get_icon_query_url(link, args.iconserver), timeout=10)
        icon_filename = get_favicon_filename(link, response)

        with open(f"{args.icon_directory}/{icon_filename}", "wb") as handler:
            handler.write(response.content)
        print(f"({i}/{len(links_to_download)}) Downloaded favicon for {link}")

        css += css_for_favicon(link, f"/favicons/{icon_filename}") + "\n"
    except Exception as e:
        print(f"Failed to fetch {link}: {e}")

with open(f"{args.favicon_css_outfile_path}", "w") as css_file:
    css_file.write(css)
