import mapzen.whosonfirst.pip.utils
import mapzen.whosonfirst.placetypes
import mapzen.whosonfirst.utils

import os

def append_parent_and_hierarchy(t38_client, feature, **kwargs):

    props = feature['properties']
    placetype = props['wof:placetype']

    lat, lon = mapzen.whosonfirst.pip.utils.reverse_geocoordinates(feature)
    pt = mapzen.whosonfirst.placetypes.placetype(placetype)

    parent_id = -1
    hierarchies = []

    possible = []

    for parent in pt.parents():

        filters = {
            'wof:placetype': str(parent)
        }

        pip_kwargs = {
            'filters': filters,
            'as_feature': True
        }

        rsp = t38_client.point_in_polygon(lat, lon, **pip_kwargs)
        rsp = list(rsp)

        if len(rsp):
            possible = rsp
            break

    if len(possible):

        for ft in possible:

            pr = ft['properties']
            id = pr['wof:id']
            repo = pr['wof:repo']

            # it might make more sense overall to store the hierarchies in T38
            # itself - it sort of depends on whether it makes sense to use T38
            # for doing point-in-poly at all (20161110/thisisaaronland)
            # https://github.com/whosonfirst/go-whosonfirst-tile38/issues/7

            root = os.path.join(kwargs['data_root'], repo)
            data = os.path.join(root, 'data')

            f = mapzen.whosonfirst.utils.load(data, id)            
            hierarchies.extend(f['properties']['wof:hierarchy'])

        if len(possible) == 1:
            parent_id = possible[0]['properties']['wof:id']

    else:
        pass

    props['wof:parent_id'] = parent_id
    props['wof:hierarchy'] = hierarchies



