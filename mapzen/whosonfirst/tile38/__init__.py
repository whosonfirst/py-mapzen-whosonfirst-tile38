import logging
import json
import requests

import mapzen.whosonfirst.placetypes

class client:

    def __init__(self, **kwargs):
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 9851)
        self.collection = kwargs.get('collection', 'whosonfirst')
        
    def do(self, cmd):
            
        logging.debug(cmd)
        
        # because I have no idea how to make the py-redis execute_command
        # method return more than a single result... (20160803/thisisaaronland)
        
        url = "http://%s:%s" % (self.host, self.port)
        rsp = requests.post(url, data=cmd)

        parsed = None
        
        try:
            parsed = json.loads(rsp.content)
        except Exception, e:
            logging.debug("failed to parse %s" % rsp.content)
            raise Exception, e

        # throw an error if parsed['ok'] != True?
        
        return parsed

class whosonfirst_client(client):

    def __init__ (self, **kwargs):

        client.__init__(self, **kwargs)

        self.possible_filters = (
            'wof:id',
            'wof:placetype',		# this gets special-cased in filters_to_where (20161110/thisisaaronland)
            'wof:placetype_id',
            'wof:is_superseded',
            'wof:is_deprecated'
        )

    def point_in_polygon(self, lat, lon, **kwargs):

        return self.intersects_paginated(lat, lon, lat, lon, **kwargs)

    def nearby(self, lat, lon, r, **kwargs):

        cursor = kwargs.get('cursor', 0)
        filters = kwargs.get('filters', {})

        where = self.filters_to_where(filters)

        cmd = [ "NEARBY", self.collection ]

        if cursor != 0:
            cmd.extend(["CURSOR %s" % cursor])

        if len(where):
            cmd.extend(where)

        cmd.extend(["POINT",
                    "%0.6f" % lat,
                    "%0.6f" % lon,
                    r])

        cmd = " ".join(map(str, cmd))
        logging.debug(cmd)

        return self.do(cmd)

    def nearby_paginated(self, lat, lon, r, **kwargs):

        rsp = None
        cursor = 0

        while True:

            kwargs['cursor'] = cursor
            rsp = self.nearby(lat, lon, r, **kwargs)

            if not rsp['ok']:
                logging.error(rsp['err'])
                break

            fields = rsp['fields']

            for row in rsp['objects']:

                if kwargs.get('as_feature', False):
                    row = self.row_to_feature(row, field_names=fields, fetch_meta=True)

                yield row

            cursor = rsp.get('cursor', 0)

            if cursor == 0:
                break

    def intersects(self, swlat, swlon, nelat, nelon, **kwargs):

        cursor = kwargs.get('cursor', 0)
        filters = kwargs.get('filters', {})

        where = self.filters_to_where(filters)

        cmd = [ "INTERSECTS", self.collection ]

        if cursor != 0:
            cmd.extend(["CURSOR %s" % cursor])

        if len(where):
            cmd.extend(where)

        cmd.extend([
            "BOUNDS",
            "%0.6f" % swlat,
            "%0.6f" % swlon,
            "%0.6f" % nelat,
            "%0.6f" % nelon
        ])
        
        cmd = " ".join(map(str, cmd))
        logging.debug(cmd)

        return self.do(cmd)

    def intersects_paginated(self, swlat, swlon, nelat, nelon, **kwargs):

        rsp = None
        cursor = 0

        while True:

            kwargs['cursor'] = cursor
            rsp = self.intersects(swlat, swlon, nelat, nelon, **kwargs)

            if not rsp['ok']:
                logging.error(rsp['err'])
                break

            fields = rsp['fields']

            for row in rsp['objects']:

                if kwargs.get('as_feature', False):
                    row = self.row_to_feature(row, field_names=fields, fetch_meta=True)

                yield row

            cursor = rsp.get('cursor', 0)

            if cursor == 0:
                break

    def rsp_to_features(self, rsp, **kwargs):

        fields = rsp['fields']

        for row in rsp['objects']:
            yield self.row_to_feature(row, field_names=fields, fetch_meta=True)

    def row_to_feature(self, row, **kwargs):

        geom_type = kwargs.get('type', 'object')

        field_names = kwargs.get('field_names', [])
        fetch_meta = kwargs.get('fetch_meta', False)

        if not row.get(geom_type, False):
            logging.error("Invalid geom type")
            return None

        count_fields = len(field_names)

        wofid, repo = row['id'].split("#")

        geom = row[geom_type]

        props = {
            'wof:repo': repo
        }
        
        for i in range(0, count_fields):
            
            k = field_names[i]
            v = row['fields'][i]
            
            props[k] = v
            
        if fetch_meta:
                
            key = "%s#meta" % props['wof:id']
            cmd = "GET %s %s" % (self.collection, key)
            
            rsp2 = self.do(cmd)
            meta = json.loads(rsp2['object'])
            
            for k, v in meta.items():

                if props.get(k, False):
                    continue

                props[k] = v
            
        feature = {
            'id': wofid,
            'type': 'Feature',
            'geometry': geom,
            'properties': props
        }
        
        return feature

    def filters_to_where(self, filters):

        where = []

        for k in self.possible_filters:

            v = filters.get(k, None)

            if not v:
                continue

            if k == 'wof:placetype':

                pt = mapzen.whosonfirst.placetypes.placetype(v)
                
                k = 'wof:placetype_id'
                v = pt.id()

            where.append("WHERE %s %s %s" % (k, v, v))

        return where

    def index_feature(self, feature, **kwargs):

        # see also: the IndexFeature method in https://github.com/whosonfirst/go-whosonfirst-tile38

        geometry = kwargs.get("geometry", "")

        if geometry == "":

            geom = feature["geometry"]

        elif geometry == "bbox":
            raise Exception, "Please implement me"
        
        elif geometry == "centroid":
            # Use mapzen.whosonfirst.pip.utils.reverse_geocoordinates ?
            raise Exception, "Please implement me"

        else:

            raise Exception, "Unknown geometry filter"

        props = feature["properties"]

        wofid = props["wof:id"]

        placetype = props["wof:placetype"]

        pt = mapzen.whosonfirst.placetypes.placetype(placetype)
        placetype_id = pt.id()

        repo = props.get("wof:repo", None)

        if repo == None:
            raise Exception, "Missing wof:repo property"

        parent_id = props.get("wof:parent_id", -1)
        
        key = "#".join(wofid, repo)
