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

    def nearby(self, lat, lon, r, **kwargs):

        cursor = kwargs.get('cursor', 0)
        filters = kwargs.get('filters', {})
        possible = ('wof:id', 'wof:placetype_id')

        where = []

        for k in possible:

            v = filters.get(k, None)

            if v:
                where.append("WHERE %s %s %s" % (k, v, v))

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

            for o in rsp['objects']:
                yield o

            cursor = rsp.get('cursor', 0)

            if cursor == 0:
                break

    def intersects(self, swlat, swlon, nelat, nelon, **kwargs):

        cursor = kwargs.get('cursor', 0)
        filters = kwargs.get('filters', {})
        possible = ('wof:id', 'wof:placetype_id')

        where = []

        for k in possible:

            v = filters.get(k, None)

            if v:
                where.append("WHERE %s %s %s" % (k, v, v))

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

            for o in rsp['objects']:
                yield o

            cursor = rsp.get('cursor', 0)

            if cursor == 0:
                break

    def rsp2features(self, rsp, **kwargs):

        fetch_names = kwargs.get('fetch_names', False)

        features = []

        fields = rsp.get('fields', [])
        count_fields = len(fields)

        for row in rsp['objects']:
            
            geom = row['object']
            props = {}

            for i in range(0, count_fields):

                k = fields[i]
                v = row['fields'][i]

                """
                if k == 'wof:placetype_id':

                    pt = mapzen.whosonfirst.placetypes.placetype(v)
                    print pt.name()
                """

                props[k] = v

            if fetch_names:

                key = "%s:name" % props['wof:id']
                cmd = "GET %s %s" % (self.collection, key)

                rsp2 = self.do(cmd)
                props['wof:name'] = rsp2['object']

            features.append({'type': 'Feature', 'geometry': geom, 'properties': props })
        
        return features
