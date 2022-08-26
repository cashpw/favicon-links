# Basic Favicon Links

An alternative to [favicon-links](https://github.com/cashweaver/favicon-links) which doesn't need to pull favicons on the fly.

This expects https://github.com/mat/besticon to be running locally at http://localhost:8080.

## Usage

1. `pip install -r requirements.txt`
1. Start the [iconserver](https://github.com/mat/besticon)
1. 
    ```sh
    python3 get_favicons.py \
      --markdown_directory=path/to/dir/with/md/files \
      --icon_directory=path/to/dir/to/save/icons/to \
      --favicon_css_outfile_path=path/to/file/to/write/css/to \
      --your_site_url=www.example.com
    ```
