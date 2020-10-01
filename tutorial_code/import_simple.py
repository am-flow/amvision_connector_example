import argparse
import sys
import os
import time

import yaml
import slumber


class APIClient(slumber.API):
    def __init__(self, url, token):
        super().__init__(url)
        # add auth header to slumber's default api client
        header = "Token {}".format(token)
        self._store['session'].auth = None
        self._store['session'].headers['Authorization'] = header


def import_files(api, meta_fn):
    print("load metadata and root path")
    with open(meta_fn, 'r') as in_file:
        meta = yaml.load(in_file, Loader=yaml.Loader)
    root = os.path.dirname(meta_fn)

    print("upload material references")
    for reference in meta['material_references']:
        api.material_reference.post({
            'id': reference['id'],
            'material': reference['material']
        })

    print("uploading prints")
    for prnt in meta['prints']:
        # upload stl and get design id
        model_fn = os.path.join(root, prnt['model_fn'])
        with open(model_fn, 'rb') as in_file:
            response = api.design_reference.post(
                {'id': prnt['model_id']}, files={'stl': in_file}
            )
        design_id = response['design']

        # get material id from mapping
        response = api.material_reference(prnt['material_id']).get()
        material_id = response['material']

        # upload design material
        response = api.design_material.post({
            'design': design_id, 
            'material': material_id
        })
        design_material_id = response['id']

        # upload the print
        api.print.post({
            'id': prnt['id'],
            'title': prnt['title'],
            'copies': prnt['copies'],
            'attributes': prnt,
            'design_material': design_material_id,
        })

    print("uploading print attributes")
    for attr in meta['print_attributes']:
        response = api.print_attribute.post({
            'id': attr['id'],
            'datatype': attr['datatype'],
            'field': attr['field'],
            'filtering': attr['filtering'],
            'summary': attr['summary'],
            'detail': attr['detail'],
            'order': attr.get('order'),
        })

    print("uploading queries")
    for query in meta['queries']:
        response = api.query.post({
            'id': query['id'],
            'query': query['query'],
            'sorting': query['sorting'],
        })

    print("uploading views")
    for view in meta['views']:
        api.view.post({'id': view['id'], 'title': view['title']})

    print("uploading batches")
    for batch in meta['batches']:
        api.batch.post({
            'id': batch['id'],
            'title': batch['title'],
            'view': batch['view'],
            'query': batch['query'],
        })


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Print importer')
    parser.add_argument('url', type=str, help='AM-Vision url')
    parser.add_argument('token', type=str, help='AM-Vision token')
    parser.add_argument('meta_fn', type=str, help='path to yaml file with print metadata')
    args = parser.parse_args()

    start = time.time()
    api = APIClient(args.url, args.token)
    import_files(api, args.meta_fn)
    end = time.time()
    print("Imported models in %d seconds" % (end - start))