# https://pythonhosted.org/setuptools/setuptools.html#namespace-packages
__import__('pkg_resources').declare_namespace(__name__)

import logging
import json
import requests

class client:

    def __init__(self, **kwargs):
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 9851)
        self.index = kwargs.get('index', 'whosonfirst')
        
    def do(self, cmd):
            
        logging.debug(cmd)
        
        # because I have no idea how to make the py-redis execute_command
        # method return more than a single result... (20160803/thisisaaronland)
        
        url = "http://%s:%s" % (self.host, self.port)
        rsp = requests.post(url, data=cmd)
        
        try:
            return json.loads(rsp.content)
        except Exception, e:
            logging.debug("failed to parse %s" % rsp.content)
            raise Exception, e
        
    def nearby(self, lat, lon, r):
                
        cmd = "NEARBY %s POINT %0.6f %0.6f %d" % (self.index, lat, lon, r)
        return self.do(cmd)
