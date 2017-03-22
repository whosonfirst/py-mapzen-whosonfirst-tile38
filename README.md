# py-mapzen-whosonfirst-tile38

Shared utilities for working with Who's On First documents and Tile38 indices

## Install

```
sudo pip install -r requirements.txt .
```

## Caveats

This library is provided as-is, right now. It lacks proper
documentation which will probably make it hard for you to use unless
you are willing to poke and around and investigate things on your
own.

## Usage

### Simple

```
import mapzen.whosonfirst.tile38

client = mapzen.whosonfirst.tile38.client()
rsp = client.nearby(51.06078, 6.094941, 500)

# or this:
# cmd  = "NEARBY whosonfirst POINT 51.06078 6.094941 500"
# rsp = client.do(cmd)

for row in rsp['objects']:
	print row['id']
```

### Fancy

```
import mapzen.whosonfirst.tile38
import mapzen.whosonfirst.placetypes

if __name__ == '__main__':

    pt = mapzen.whosonfirst.placetypes.placetype('venue')
    filters = { 'wof:placetype_id': pt.id() }

    cl = mapzen.whosonfirst.tile38.whosonfirst_client()

    rsp = cl.nearby(37.775159, -122.413316, 10, filters=filters)
    print cl.rsp2features(rsp, fetch_names=True)

    # prints
    # [{'geometry': {u'type': u'Point', u'coordinates': [-122.413361, 37.775088]}, 'type': 'Feature', 'properties': {'wof:name': u'El Dorado Hotel', u'wof:placetype_id': 102312325, u'wof:id': 286765465}}]

    rsp = cl.nearby_paginated(37.775159, -122.413316, 1000)
    print len(rsp['objects'])

    # prints
    # 5268
```

## See also

* http://tile38.com/
* https://github.com/whosonfirst/go-whosonfirst-tile38