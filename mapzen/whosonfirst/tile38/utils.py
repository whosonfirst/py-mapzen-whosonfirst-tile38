import mapzen.whosonfirst.pip.utils
import mapzen.whosonfirst.placetypes
import mapzen.whosonfirst.utils

import os

# everything in here is early days and wrapped up in a big sweater of experimental
# (20161110/thisisaaronland)

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

            # see below - this hasn't been rolled in to production yet
            # hierarchies.extend(pr['wof:hierarchy'])

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

def whereami(t38_client, feature, **kwargs):

    props = feature['properties']
    placetype = props['wof:placetype']

    lat, lon = mapzen.whosonfirst.pip.utils.reverse_geocoordinates(feature)

    return whereami_by_coord(t38_client, lat, lon, placetype, **kwargs)

def whereami_by_coord(t38_client, lat, lon, placetype, **kwargs):

    pt = mapzen.whosonfirst.placetypes.placetype(placetype)

    hierarchy = {}
    match = None

    roles = kwargs.get('roles', ['common'])

    for a in pt.ancestors(roles):

        filters = {
            'wof:placetype': str(a)
        }

        pip_kwargs = {
            'filters': filters,
            'as_feature': True
        }

        rsp = t38_client.point_in_polygon(lat, lon, **pip_kwargs)
        rsp = list(rsp)
        
        if len(rsp) != 1:
            hierarchy[ str(a) ] = -1
            continue

        match = rsp[0]
        break

    if match:

        # see notes above inre storing the hierarchy in T38 itself
        # (20161110/thisisaaronland)

        pr = match['properties']
        id = pr['wof:id']
        repo = pr['wof:repo']

        root = os.path.join(kwargs['data_root'], repo)
        data = os.path.join(root, 'data')

        f = mapzen.whosonfirst.utils.load(data, id)            

        # see this - we are just ignoring instances where there are
        # 0 or > 1 hierarchies - we should do something about that...
        # (20161110/thisisaaronland)

        for k, v in f['properties']['wof:hierarchy'][0].items():

            if hierarchy.get(k):
                continue
            
            hierarchy[k] = v

    return hierarchy

