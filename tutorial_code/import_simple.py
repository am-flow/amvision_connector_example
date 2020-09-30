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

















# """File import functionality."""
# import logging
# import argparse
# import sys
# import yaml
# import os

# from common.config import get_config
# from common.api_client import APIClient

# mat_ids = {
#     ('SLS', None): 'SLS_PLAIN',
#     ('MJF', None): 'MJF_PLAIN',
#     ('SLS', 'GREEN'): 'SLS_GREEN',
#     ('SLS', 'RED'): 'SLS_RED',
#     ('SLS', 'BLACK'): 'SLS_BLACK',
# }
# log = logging.getLogger(__name__)

# class Importer():
#     def __init__(self, amvision_ip, amvision_port, amvision_token):
#         self.api = APIClient(amvision_ip, amvision_port, amvision_token)

#     def get_material(self, prnt):
#         material_map = {
#             ('SLS', None): 'MTR_PRT_SLS_MAT_PA2200',
#             ('MJF', None): 'MTR_PRT_MJF_MAT_PA12',
#             ('SLS', 'GREEN'): 'MTR_PRT_SLS_MAT_PA2200_DYE_green',
#             ('SLS', 'RED'): 'MTR_PRT_SLS_MAT_PA2200_DYE_red',
#             ('SLS', 'BLACK'): 'MTR_PRT_SLS_MAT_PA2200_DYE_black',
#         }
#         material = material_map.get((prnt['print_method'], prnt['dye_color']))
#         if not material:
#             log.warning("Unknown material for print %s", str(prnt))
#             material = material_map[('SLS', None)]
#         return material

#     def one_time_imports(self):
#         # create views for the batches
#         self.api.view.post({'id': 'by_tray', 'title': "View by tray"})
#         self.api.view.post({'id': 'by_method', 'title': "View by method"})
#         # create the necessary print attributes
#         self.api.print_attribute.post({
#             'id': 'tray',
#             'datatype': 'NUMBER',
#             'field': 'tray_id',
#             'filtering': True,
#             'summary': False,
#             'detail': True,
#         })
#         self.api.print_attribute.post({
#             'id': 'method',
#             'datatype': 'STRING',
#             'field': 'print_method',
#             'filtering': True,
#             'summary': True,
#             'detail': True,
#             'order': 10
#         })
#         self.api.print_attribute.post({
#             'id': 'dye',
#             'datatype': 'STRING',
#             'field': 'dye_color',
#             'filtering': True,
#             'summary': True,
#             'detail': True,
#             'order': 11
#         })
#         self.api.print_attribute.post({
#             'id': 'category',
#             'datatype': 'STRING',
#             'field': 'category',
#             'filtering': False,
#             'summary': True,
#             'detail': True,
#             'order': 12
#         })
#         self.api.print_attribute.post({
#                 'id': 'has_dye',
#                 'datatype': 'STRING',
#                 'field': 'dye_color',
#                 'filtering': True,
#                 'summary': True,
#                 'detail': True,
#                 'order': 13
#         })
#         self.api.query.post({
#             'id': 'Green',
#             'query': 'dye=GREEN',
#             'sorting': True,
#         })
#         self.api.query.post({
#             'id': 'Black',
#             'query': 'dye=BLACK',
#             'sorting': True,
#         })
#         self.api.query.post({
#             'id': 'Unpainted_SLS',
#             'query': 'has_dye=False&method=SLS',
#             'sorting': True,
#         })
#         self.api.query.post({
#             'id': 'Unpainted_MJF',
#             'query': 'has_dye=False&method=MJF',
#             'sorting': True,
#         })

#     def import_prints(self, prints_fn):
#         # load print definition
#         with open(prints_fn, 'r') as infile:
#             prints = yaml.load(infile, Loader=yaml.Loader)

#         # keep track of trays and categories to add batches later
#         trays = set()
#         methods = set()

#         for prnt in prints:
#             # determine id and full path to stl
#             stl_id = os.path.splitext(prnt['stl'])[0]
#             # assuming stl filenames are relative to prints_fn location
#             stl_fn = os.path.join(os.path.dirname(prints_fn), prnt['stl'])
#             # add the has_dye key
#             prnt['has_dye'] = prnt.get('dye_color') is not None

#             # now upload the stl file
#             with open(stl_fn, 'rb') as in_file:
#                 response = self.api.design_reference.post({'id': stl_id}, files={'stl': in_file})
#                 design = response['design']

#             # determine material to use
#             material = self.get_material(prnt)

#             # create the design_material combination
#             response = self.api.design_material.post({'design': design, 'material': material})
#             design_material = response['id']

#             # finally create the print
#             response = self.api.print.post({
#                 'id': prnt['id'],
#                 'copies': prnt['copies'],
#                 'title': prnt['title'],
#                 'attributes': prnt,
#                 'design_material': design_material
#             })

#             # store tray id and category
#             trays.add(prnt['tray_id'])
#             methods.add(prnt['print_method'])

#         # create batches for each tray
#         for tray in trays:
#             self.api.batch.post({
#                 'id': tray,
#                 'title': "Tray {}".format(tray),
#                 'view': 'by_tray',
#                 'query': 'tray={}'.format(tray),
#             })

#         # create batches for each method
#         for method in methods:
#             self.api.batch.post({
#                 'id': method,
#                 'title': "Method {}".format(method),
#                 'view': 'by_method',
#                 'query': 'method={}'.format(method),
#             })

#         self.api.batch.post({
#             'id': 'all',
#             'title': 'All prints',
#             'view': 'by_method',
#             'query': 'method={}'.format(','.join(methods)),
#         })

#         # make sure the batches are all up to date
#         self.api.batch.populate_all()


# def _get_parser():
#     """Build argument parser."""
#     parser = argparse.ArgumentParser(
#         description='Print importer')
#     parser.add_argument(
#         '-d', '--debug', action='store_true',
#         help='enable debug logging',
#     )
#     parser.add_argument(
#         '-c', '--config', type=str, default='config.yml',
#         help='config file for connector',
#     )
#     parser.add_argument(
#         'prints', type=str,
#         help='path to yaml file with prints definition',
#     )
#     return parser


# def cli():
#     """Command line zip importer."""
#     parser = _get_parser()
#     args = parser.parse_args()
#     logging.basicConfig(
#         stream=sys.stdout,
#         level=logging.DEBUG if args.debug else logging.INFO,
#         format='[%(asctime)s: %(levelname)s] %(message)s'
#     )
#     conf = get_config(config_fn=args.config, key='amvision_api')
#     log.info("Starting importer")
#     importer = Importer(conf['ip'], conf['port'], conf['token'])
#     importer.one_time_imports()
#     importer.import_prints(args.prints)
#     log.info("Import complete")


# if __name__ == '__main__':
#     cli()
