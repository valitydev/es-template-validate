#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import requests
import os
import sys
import json
import time

TMPL_DIR = 'templates'
SMPL_DIR = 'samples'
ES_HOST = 'localhost'
ES_PORT = '9200'

# Obtaining list of templates
templates = os.listdir(TMPL_DIR)


# Waiting while ES starts
def check_es_ready():
    tries = 0
    while tries < 10:
        try:
            requests.get('http://%s:%s' % (ES_HOST, ES_PORT), timeout=3)
            return
        except requests.exceptions.ConnectionError:
            tries+=1
            print "ES not ready yet. Attempting to reconnect (#%s)" % tries
            time.sleep(3)
    print "ES not ready. Retry limit reached. Aborting script"
    sys.exit(1)


# Main test
def perform_check(item):
    index_name = item.split('.')[0]
    # No need to run if no sample data for template
    if item not in os.listdir(SMPL_DIR):
        print "No sample data for index %s. Aborting" % index_name
        sys.exit(1)

    # Obtaining existing indices from test ES
    try:
        req = requests.get('http://%s:%s/_cat/indices?h=index' % (ES_HOST, ES_PORT))
        if req.status_code == 200:
            indices = req.text.split('\n')
        else:
            print 'Failed to obtain indeces: %s' % req.text
            sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print 'Failed to connect to ES', e
        sys.exit(1)

    # Deleting existing index if exists
    if index_name in indices:
        try:
            req = requests.delete('http://%s:%s/%s' % (ES_HOST, ES_PORT, index_name))
            if req.status_code == 200:
                response = json.loads(req.text)
                print 'Deleting index "%s": %s' % (index_name, response["acknowledged"])
            else:
                print 'Failed to clear index "%s": %s' % (index_name, req.text)
                sys.exit(1)
        except requests.exceptions.ConnectionError as e:
            print 'Failed to connect to ES', e
            sys.exit(1)

    # Creating new template for index
    with open('%s/%s' % (TMPL_DIR, item), 'r') as template:
        try:
            mapping = json.loads((template.read()))
        except ValueError:
            print 'Failed to serialize template for index "%s"' % index_name
            sys.exit(1)

        try:
            req = requests.put('http://%s:%s/_template/%s' % (ES_HOST, ES_PORT, index_name), json=mapping)
            if req.status_code == 200:
                response = json.loads(req.text)
                print 'Creating template for index "%s": %s' % (index_name, response["acknowledged"])
            else:
                print 'Failed to create template for index "%s": %s' % (index_name, req.text)
        except requests.exceptions.ConnectionError as e:
            print 'Failed to connect to ES', e
            sys.exit(1)

    # Posting sample data into index
    with open('%s/%s' % (SMPL_DIR, item), 'r') as sample:
        try:
            data = json.loads(sample.read())
        except ValueError:
            print 'Failed to serialize sample data for index "%s"' % index_name
            sys.exit(1)
        try:
            req = requests.post('http://%s:%s/%s/_doc' % (ES_HOST, ES_PORT, index_name), json=data)
            if req.status_code == 201:
                response = json.loads(req.text)
                print 'Posting sample data to index "%s": %s' % (index_name, response["result"])
            else:
                print 'Failed to post sample data to index "%s": %s' % (index_name, req.text)
        except requests.exceptions.ConnectionError as e:
            print 'Failed to connect to ES', e
            sys.exit(1)

    # Obtaining autocreated mapping for index and comparing it with template
    try:
        req = requests.get('http://%s:%s/%s/_mapping' % (ES_HOST, ES_PORT, index_name), json=mapping)
    except requests.exceptions.ConnectionError as e:
        print 'Failed to connect to ES', e
        sys.exit(1)
    cur_mapping = json.loads(req.text)
    compare_result = cmp(mapping["mappings"], cur_mapping[index_name]["mappings"])
    if compare_result == 1:
        print 'Template for index "%s" sucessfully passed the test\n\n' % index_name
        return
    else:
        print 'Generated template is differ from original template for index "%s"' % index_name


if __name__ == "__main__":
    # Waiting for elasticsearch to start
    check_es_ready()
    # For each template execute series of tests:
    for entry in templates:
        perform_check(entry)
    print 'All tests passed'
    sys.exit(0)
