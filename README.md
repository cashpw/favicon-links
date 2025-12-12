# Favicon links

An alternative to [dynamic-favicon-links](https://github.com/cashpw/dynamic-favicon-links) which doesn't need to pull favicons on the fly.

## Usage

1. `pip install -r requirements.txt`
1. Start the [iconserver](https://github.com/mat/besticon)
1. 
    ```sh
    python3 get_favicons.py \
      --markdown_directory=path/to/dir/with/md/files \
      --icon_directory=path/to/dir/to/save/icons/to \
      --favicon_css_outfile_path=path/to/file/to/write/css/to \
      --iconserver=http://localhost:8080 \
      --your_site_url=www.example.com
    ```
