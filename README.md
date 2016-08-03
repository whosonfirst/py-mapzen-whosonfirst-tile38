# py-mapzen-whosonfirst-tile38

Shared utilities for working with Who's On First documents and Tile38 indices

## Caveats

This library is provided as-is, right now. It lacks proper
documentation which will probably make it hard for you to use unless
you are willing to poke and around and investigate things on your
own.

## Installation

The usual Python dance:

```
sudo python setup.py install
```    

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

## See also

* http://tile38.com/
