import csv
import urllib2
import urllib
from lxml import etree 
import os
from collections import OrderedDict
import json

script_dir = os.path.dirname(__file__) 
vra_xpath = os.path.join(script_dir, 'vra_xpath.txt')
next_gen_pred = os.path.join(script_dir, 'dc_term_map.txt')
next_gen_fields = os.path.join(script_dir, 'next_gen_field.txt')

def get_list(csv_file):
    """turn a list of items into a, well list. Used for PIDs, vra fields, and headers"""

    f = open(csv_file, 'r').read()
    # Note, pop the last one to ensure no errors. 
    # I think I should do a [line for line in lines if line] to scrub
    return [line.strip() for line in f.split('\n') if line]

def get_vra_url(pid):
    """ Return a vra URL. This is hardwired to Images
    
    >>> get_vra_url('123')
    'http://images.northwestern.edu/technical_metadata/123/VRA'
    
    """

    return "%s%s%s" %("http://images.northwestern.edu/technical_metadata/", pid, "/VRA")

def get_xml_from_file(pid, directory):
    """Takes a pid, and returns the xmlfile
    
    >>> get_xml_from_file('123','/home/david/testxml/')
    '/home/david/testxml/123.xml'

    """
    xml_file = "%s.xml" %pid.replace(":", "-")
    file_path = os.path.join(directory, xml_file)
    return file_path

def save_raw_xml(pids, outputdir):
    """Iterate pids and save xml"""

    for pid in get_list(pids):
       print "working on %s" %pid
       filename = pid.replace(":","-")+".xml"
       urllib.URLopener().retrieve(get_vra_url(pid), os.path.join(outputdir, filename)) 

def flatten_item(url, pid):
    """ Takes an item's xml and flattens it. The PID is used in errors. It returns a key, value tuple 
    with the key being in the flattened format of '/vra:vra/vra:image/vra:titleSet/vra:display'

    Get a file (or a URL) and flatten it
    >>> file="samples/test.xml"
    >>> flattened = flatten_item(file, '123')
    >>> len(flattened)==80
    True
    >>> dictionary_of_data=dict(flattened)
    >>> dictionary_of_data['/vra:vra/vra:image@id']
    'inu-dil-258550_w'
    >>> dictionary_of_data['/vra:vra/vra:image/vra:titleSet/vra:display']
    'Look-out post in watch tower as above'
    """

    # Try to parse the URL or XML file.
    try: 
        item = []
        # Parse it and grab the root
        tree = etree.parse(url)
        root = tree.getroot().tag
        # Iterate through the nodes and create a tuple with (xpath, value)
        for node in tree.iter():
            for child in node.getchildren():
                if child.attrib:
                    # Extend the list if there's an attribute with the key, value
                    attributes = [tree.getpath(child)+'@'+key for key in child.attrib.keys()]
                    item.extend(zip(attributes, child.attrib.values()))
                if child.text:
                    item.append((tree.getpath(child), child.text.strip()))
    except Exception as err:
        # Trap exceptions and extend the item
        item.append(("/vra:vra/vra:image@refid", pid))
        item.append(("ERROR", str(err)))
        # Print the error
        print err
    # dict and append to a big old list. This could also be a dict.  
    return item

def save_as_flat_json(pids, output, **kwargs):
    """completely flatten the object, and serialize as json
    
    Takes a list of PIDS, processses them and saves them to a directory.
    
    """

    items = []
    pid_list = get_list(pids)
    print "starting %s pids" %len(pid_list)
    for pid in pid_list:
        if kwargs.get('xmldir'):
            url = get_xml_from_file(pid, kwargs['xmldir'])
        else:
            url = get_vra_url(pid)
        item = flatten_item(url, pid)
        items.append(dict(item))

    with open (output, 'w') as f:
        # write it out to a file based on input
        print "dumping %s json records" %len(items)
        json.dump(items, f, encoding="utf-8")
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile')
    parser.add_argument('-o', '--outputfile')
    parser.add_argument('-x', '--xmldir')
    parser.add_argument('-r', '--rawxml', action='store_true')
    parser.add_help
    args = parser.parse_args()
   
    if args.rawxml and args.outputfile and args.inputfile:
        # Save it as raw xml to a directory
        save_raw_xml(args.inputfile, args.outputfile)

    elif args.inputfile and args.outputfile and args.xmldir:
        save_as_flat_json(args.inputfile, args.outputfile, xmldir=args.xmldir)

    elif args.outputfile and args.json and args.inputfile:
        # Save it as a totally flat JSON file. Get the Data from a URL
        save_as_flat_json(args.inputfile, args.outputfile)
    
    else:
        parser.print_help()

