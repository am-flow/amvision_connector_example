import argparse
import sys
import os
import logging
import time

import yaml
import slumber

from .api_client import APIClient


log = logging.getLogger(__name__)


class Importer():
    def __init__(self, api):
        self.api = api

    def load_meta_file(self, meta_fn):
        with open(meta_fn, 'r') as in_file:
            meta = yaml.load(in_file, Loader=yaml.Loader)
        meta['root'] = os.path.dirname(meta_fn)
        return meta

    def one_time_imports(self, meta_fn):
        log.info("Running one-time imports")
        meta = self.load_meta_file(meta_fn)
        self.api.material_reference.put(meta['material_references'])
        self.api.view.put(meta['views'])
        self.api.print_attribute.put(meta['print_attributes'])
        self.api.query.put(meta['queries'])

    def import_all(self, meta_fn):
        meta = self.load_meta_file(meta_fn)

        log.info("Uploading designs")
        # first check which designs have been uploaded already
        ids = set(p['model_id'] for p in meta['prints'])
        resp = self.api.design_reference.search.post(
            data={'id':','.join(ids)}, page_size=len(ids)
        )
        prnt_to_design = {ref['id']:ref['design'] for ref in resp['results']}
        # now upload the remaining stls one-by-one
        for prnt in meta['prints']:
            if prnt['model_id'] in prnt_to_design:
                # already have this one!
                continue
            # if not existing, upload it
            with open(os.path.join(meta['root'], prnt['model_fn']), 'rb') as in_file:
                response = self.api.design_reference.post(
                    {'id': prnt['model_id']}, files={'stl': in_file}
                )
                prnt_to_design[prnt['model_id']] = response['design']

        log.info("Find materials")
        # get the AM-Vision material ids from the material references
        ids = set(p['material_id'] for p in meta['prints'])
        resp = self.api.material_reference.search.post(
            data={'id':','.join(ids)}, page_size=len(ids)
        )
        prnt_to_material = {ref['id']:ref['material'] for ref in resp['results']}

        log.info("Uploading design materials")
        dms = []
        for prnt in meta['prints']:
            dms.append({
                'design': prnt_to_design[prnt['model_id']],
                'material': prnt_to_material[prnt['material_id']]
            })
        # create the design_material combinations with a bulk PUT
        resp = self.api.design_material.put(dms)
        prnt_to_dm = {(dm['design'], dm['material']):dm['id'] for dm in resp}

        log.info("Uploading prints")
        # now create the prints in bulk
        print_data = []
        for prnt in meta['prints']:
            # create the prints in bulk
            dm = prnt_to_dm[(
                prnt_to_design[prnt['model_id']],
                prnt_to_material[prnt['material_id']]
            )]
            print_data.append({
                'id': prnt['id'],
                'copies': prnt['copies'],
                'title': prnt['title'],
                'attributes': prnt,
                'design_material': dm
            })
        # create the prints with a bulk PUT
        self.api.print.put(print_data)

        log.info("Uploading batches")
        # create the batches with a bulk PUT
        self.api.batch.put(meta['batches'])
        # make sure the batches are all up to date
        self.api.batch.populate_all()


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Print importer')
    parser.add_argument('url', type=str, help='AM-Vision url')
    parser.add_argument('token', type=str, help='AM-Vision token')
    parser.add_argument('meta_fn', type=str, help='path to yaml file with print metadata')
    args = parser.parse_args()
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO,
        format='[%(asctime)s: %(levelname)s] %(message)s'
    )

    start = time.time()
    api = APIClient(args.url, args.token)
    importer = Importer(api)
    importer.one_time_imports(args.meta_fn)
    importer.import_all(args.meta_fn)
    end = time.time()
    print("Imported models in %d seconds" % (end - start))




