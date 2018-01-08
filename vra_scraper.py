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
    """ Return a vra URL"""
    return "%s%s%s" %("http://images.northwestern.edu/technical_metadata/", pid, "/VRA")

def parse_pid(pid):
    """ Run pid against list of stuff, lay it out in a list"""
    try: 
        images_xpath = get_list(vra_xpath)  
        url = get_vra_url(pid)
        namespaces = {"vra":"http://www.vraweb.org/vracore4.htm"}
        print 'working on ... %s' %url
        tree = etree.parse(url)
        tree.getroot()
        items = [url]
        for field in images_xpath:
            items.append(tree.xpath(field, namespaces=namespaces))
    except Exception as inst:
        # exception raised, print it to see what went wrong. 
        items = [url, "something wrong with the xml in this pid, or couldn't get through to the server", inst]
        
    return items

def iterate_pids(pids):
    """ Iterate through pidlist return a list of lists"""
    return [parse_pid(pid) for pid in pids]

def save_csv(list_of_data, outputfile):
    """ put headers in and save it"""
    import csv
    output = open(outputfile, 'wb')
    writer = csv.writer(output)
    writer.writerow(["url"]+get_list(next_gen_fields))
    writer.writerow(["url"]+get_list(vra_xpath))
    writer.writerow(["url"]+get_list(next_gen_pred))

    for row in list_of_data:
        writer.writerow(row)

def save_as_mapped_csv(inputfile, outputfile): 
    save_csv(iterate_pids(get_list(inputfile)), outputfile)
    print "saved csv file as: %s"%outputfile

def save_raw_xml(pids, outputdir):
    """Iterate pids and save xml"""
    for pid in get_list(pids):
       print "working on %s" %pid
       filename = pid.replace(":","-")+".xml"
       urllib.URLopener().retrieve(get_vra_url(pid), os.path.join(outputdir, filename)) 

def get_xml_from_file(pid, directory):
    """Takes a pid, and returns the xmlfile"""
    xml_file = "%s.xml" %pid.replace(":", "-")
    data_file = os.path.join(directory, xml_file)
    return data_file

def flatten_item(url, pid):
    """ Takes an item's xml and flattens it"""
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
    """completely flatten the object, and serialize as json"""

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
    parser.add_argument('-j', '--json', action='store_true')


    parser.add_help
    args = parser.parse_args()
    if args.rawxml and args.outputfile and args.inputfile:
        # Save it as raw xml to a directory
        save_raw_xml(args.inputfile, args.outputfile)

    if args.inputfile and args.outputfile and args.json and args.xmldir:
        save_as_flat_json(args.inputfile, args.outputfile, xmldir=args.xmldir)

    elif args.outputfile and args.json and args.inputfile:
        # Save it as a totally flat JSON file
        save_as_flat_json(args.inputfile, args.outputfile)
    
    elif args.outputfile and args.inputfile:
        # Save it as Mapped CSV
        save_as_mapped_csv(args.inputfile, args.outputfile)
    else:
        parser.print_help()

