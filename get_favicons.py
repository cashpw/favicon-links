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
import validators

parser = argparse.ArgumentParser()
parser.add_argument("--markdown_directory", help="Path to directory with HTML files to scan for links.", required=True)
parser.add_argument("--icon_directory", help="Path to directory to store downloaded icons in.", required=True)
parser.add_argument("--favicon_css_outfile_path", help="Path to write the CSS to.", required=True)
parser.add_argument("--your_site_url", help="Your site's url (without HTTP(s)).", required=True)
parser.add_argument("--iconserver_location", help="Iconserver url.", default="http://localhost:8080", type=str)
args = parser.parse_args()

def yes_or_no(prompt):
    """Prompt the user to enter Y/N. Return True for yes, False for no.

    https://gist.github.com/garrettdreyfus/8153571"""

    reply = str(input(prompt+' (y/n): ')).lower().strip()
    if len(reply) == 0:
        return yes_or_no(prompt)

    if reply[0] == 'y':
        return True

    if reply[0] == 'n':
        return False

    return yes_or_no(prompt)

def get_links(string):
    """Return a list with markdown links

    Reference: https://github.com/andrewp-as-is/markdown-link-extractor.py/blob/master/markdown_link_extractor/__init__.py"""
    html = markdown.markdown(string, output_format='html')
    links = list(set(re.findall(r'href=[\'"]?([^\'" >]+)', html)))
    links = list(filter(lambda l: l[0] != "{", links))
    return links

def get_baselinks(string):
    http_links = [link for link in get_links(string) if "http" in link]
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

    content_type = response.headers['content-type']
    return mimetypes.guess_extension(content_type)


os.chdir(args.markdown_directory)
links = []
markdown_files = glob.glob("*.md")
for filename in markdown_files:
    with open(filename, 'r') as f:
        content = f.read()
        baselinks = get_baselinks(content)
        links += baselinks
valid_links = [link for link in links if validators.url(link)]

if valid_links:
    css = []

    if os.path.exists(args.favicon_css_outfile_path):
        print(f"Found {args.favicon_css_outfile_path}. Additional CSS will be appended to the existing file.")
    else:
        css += [f"a:not([href*='{args.your_site_url}']):not([href^='#']):not([href^='/']):after {{"]
        css += ["  background-position: 0 center;"]
        css += ["  background-repeat: no-repeat;"]
        css += ["  background-size: 16px 16px !important;"]
        css += ["  content: '';"]
        css += ["  height: 16px;"]
        css += ["  vertical-align: middle;"]
        css += ["  width: 16px;"]
        css += ["}"]

    unique_links = set(valid_links)
    unique_links = [link for link in unique_links if "cashweaver" not in link]
    hosts_with_existing_favicons=sorted([pathlib.Path(filename).stem for filename in os.listdir(args.icon_directory)])
    links_to_download = sorted([link for link in unique_links if not urllib.parse.urlparse(link).netloc in hosts_with_existing_favicons])

    """
    if len(hosts_with_existing_favicons) != len(unique_links):
        print(f"Skipping download for favicons already present in {args.icon_directory}")
    """

    if yes_or_no(f"Download {len(links_to_download)} favicons?"):

        for i, link in enumerate(links_to_download, start=1):
            print(f"({i}/{len(links_to_download)}) {link}")
            try:
                response = requests.get(get_icon_query_url(link, args.iconserver_location), timeout=10)
                icon_filename = get_favicon_filename(link, response)

                print(f"↓ {icon_filename}")
                with open(f"{args.icon_directory}/{icon_filename}", "wb") as handler:
                    handler.write(response.content)

                css += [f"a[href*='{link}']:after {{"]
                css += [f"  background-image: url('/favicons/{icon_filename}');"]
                css += ["  padding-left: 16px;"]
                css += ["  margin-left: 0.5ch;"]
                css += ["}"]
            except Exception as e:
                print(f"Failed to fetch {link}: {e}")

        with open(f"{args.favicon_css_outfile_path}", 'w') as css_file:
            css_file.write("\n".join(css))
