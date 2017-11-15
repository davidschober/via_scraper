import csv
import urllib2
import urllib
from lxml import etree 
import os

from pyxml2dict import XML2Dict 

import json

script_dir = os.path.dirname(__file__) 
vra_xpath = os.path.join(script_dir, 'vra_xpath.txt')
next_gen_pred = os.path.join(script_dir, 'dc_term_map.txt')
next_gen_fields = os.path.join(script_dir, 'next_gen_field.txt')

def get_vra_url(pid):
    """ Return a vra URL"""
    return "%s%s%s" %("http://images.northwestern.edu/technical_metadata/", pid, "/VRA")

def parse_pid(pid):
    try: 
        """ parse throught the vra and get the necessary data"""
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

def get_list(csv_file):
    """turn a list of items into a, well list. Used for PIDs, vra fields, and headers"""
    f = open(csv_file, 'r').read()
    # Note, pop the last one to ensure no errors. 
    # I think I should do a [line for line in lines if line] to scrub
    return [line for line in f.split('\n') if line]

def main(inputfile, outputfile): 
    save_csv(iterate_pids(get_list(inputfile)), outputfile)
    print "saved csv file as: %s"%outputfile

def save_raw_xml(pids, outputdir):
    """Iterate pids and save xml"""
    for pid in get_list(pids):
       print "working on %s" %pid
       filename = pid.replace(":","-")+".xml"
       urllib.URLopener().retrieve(get_vra_url(pid), os.path.join(outputdir, filename)) 

def flatten_dict(init_dict):
    """Flatten the heck out of a dictionary and ditch all parents"""

    res_dict = {}
    if type(init_dict) is not dict:
        return res_dict

    for k, v in init_dict.iteritems():
        if type(v) == dict:
            res_dict.update(flatten_dict(v))
        else:
            res_dict[k] = v

    return res_dict

def save_as_json(pids, output):
    """ grab each PID, concact a list, dump to json"""
    collection = []

    for pid in get_list(pids):
        url = get_vra_url(pid)
        print 'working on %s' %url 
        xml2dict = XML2Dict()
        item_dict = xml2dict.fromstring(urllib.urlopen(url).read())
        # flatten it and append it
        collection.append(item_dict)
    
    with open (output, 'w') as f:
        # write it out to a file
        json.dump(collection, f)     


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile')
    parser.add_argument('-o', '--outputfile')
    parser.add_argument('-r', '--rawxml')
    parser.add_argument('-j', '--json')

    parser.add_help
    args = parser.parse_args()
    if args.rawxml and args.outputfile and args.inputfile:
        save_raw_xml(args.inputfile, args.outputfile)
    elif args.outputfile and args.json and args.inputfile:
        save_as_json(args.inputfile, args.outputfile)
    
    elif args.outputfile and args.inputfile:
        main(args.inputfile, args.outputfile)
    else:
        parser.print_help()

# test_pids = get_list('/Users/dsc712/Desktop/casas.csv')
# save_csv('test.csv', iterate_pids(test_pids))
