# USGS Minerals Data (Africa)

## Preface
Check the [robots.txt](https://minerals.usgs.gov/robots.txt) and *Policies and Notices* (currently a broken link) first.
At the time of writing (2018-02-25) none of the following knowingly violates the law.

## Steps

Preparing the data

1. `download-html.py` 
    - downloads the [Minerals Yearbook Volume III: Area Reports-International-Africa and the Middle East](https://www.usgs.gov/centers/nmic/africa-and-middle-east) 
      page from USGS to be fixed locally before processing further
    - HTML is invalid in many parts, fixes need to be applied by hand
        - keep an eye on the indentation of the rendered HTML to find faults
        - removing comments (such as contact info) never hurts
2. `extract-data-urls.py [-f]`
    - extracts lists of CSV files per country
3. `download-recent-data.py`
    - download these CSV files
    - store in a structured way
4. `convert-xls-csv.py`
    - converts downloaded XLS to CSV
    - one CSV per sheet in XLS
    - deletes "cover sheet" (contains no information) where applicable
5. `filter-by-minerals.py`
    - scans through CSV files
    - writes a list of mentioned minerals to sources and (much less reliably) to countries in the database
6. `flatpak run org.libreoffice.LibreOffice --headless --convert-to pdf data/xls/* --outdir /data/pdf`
    - generate PDF files from the XLS files for faster access
    
and then you can start semi-automatically transfering it to the DB:

`input-per-source.py`

Ultimately there are minimal export tools in `reporting/`

## Unusual dependencies
- `ssconvert` (found in `gnumeric`)
