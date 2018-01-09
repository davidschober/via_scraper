# vra_scraper
A quick and dirty scraper for VRA data --> CSV. Take a list of pids and spit out a CSV file for metadata folks to take a look at. 

## Usage

usage: vra_scraper.py [-h] [-i INPUTFILE] [-o OUTPUTFILE] [-x XMLDIR] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTFILE, --inputfile INPUTFILE
  -o OUTPUTFILE, --outputfile OUTPUTFILE
  -x XMLDIR, --xmldir XMLDIR

## Example
python vra_scraper.py -i /Users/dsc712/Downloads/multiresimage_pids_01_05_18.txt -o /Users/dsc712/Desktop/dil.json -x /Users/dsc712/Downloads/vra 
