
"""
  Copyright 2011 Jeff Garzik

  AuthServiceProxy has the following improvements over python-jsonrpc's
  ServiceProxy class:

  - HTTP connections persist for the life of the AuthServiceProxy object
    (if server supports HTTP/1.1)
  - sends protocol 'version', per JSON-RPC 1.1
  - sends proper, incrementing 'id'
  - sends Basic HTTP authentication headers
  - parses all JSON numbers that look like floats as Decimal
  - uses standard Python json lib

  Previous copyright, from python-jsonrpc/jsonrpc/proxy.py:

  Copyright (c) 2007 Jan-Klaas Kollhof

  This file is part of jsonrpc.

  jsonrpc is free software; you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation; either version 2.1 of the License, or
  (at your option) any later version.

  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this software; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import decimal
import json
import logging
import requests

USER_AGENT = "AuthServiceProxy/0.1"

HTTP_TIMEOUT = 30

log = logging.getLogger("BitcoinRPC")

class JSONRPCException(Exception):
    def __init__(self, rpc_error):
        parent_args = []
        try:
            parent_args.append(rpc_error['message'])
        except:
            pass
        Exception.__init__(self, *parent_args)
        self.error = rpc_error
        self.code = rpc_error['code'] if 'code' in rpc_error else None
        self.message = rpc_error['message'] if 'message' in rpc_error else None

    def __str__(self):
        return '%d: %s' % (self.code, self.message)

    def __repr__(self):
        return '<%s \'%s\'>' % (self.__class__.__name__, self)


class DecimalEncoder(float):
    def __init__(self, o):
        self.o = o
    def __repr__(self):
        return str(self.o)

class JSONEncoderWithDecimalCls(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return DecimalEncoder(o)
        return json.JSONEncoder.default(self, o)

JSONEncoderWithDecimal = JSONEncoderWithDecimalCls()

def jsondumps(o):
    return ''.join(JSONEncoderWithDecimal.iterencode(o))

class AuthServiceProxy(object):
    __id_count = 0

    def __init__(self, service_url, service_name=None, timeout=HTTP_TIMEOUT, 
                 connection=None, ssl_context=None):
        self.__service_url = service_url
        self.__service_name = service_name
        self.__timeout = timeout

        if connection:
            # Callables re-use the connection of the original proxy
            self.__conn = connection
        else:
            self.__conn = requests.Session()

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            # Python internal stuff
            raise AttributeError
        if self.__service_name is not None:
            name = "%s.%s" % (self.__service_name, name)
        return AuthServiceProxy(self.__service_url, name, self.__timeout, self.__conn)

    def __call__(self, *args):
        AuthServiceProxy.__id_count += 1

        log.debug("-%s-> %s %s"%(AuthServiceProxy.__id_count, self.__service_name,
                                 jsondumps(args)))                        
        response = self.__conn.post(url=self.__service_url,
        headers={
            'User-Agent': USER_AGENT,
            'Content-type': 'application/json',
            'Accept-encoding': 'br,gzip'
        },
        json={
            'version': '1.1',
            'method': self.__service_name,
            'params': args,
            'id': AuthServiceProxy.__id_count
        })                    
        if response.status_code != 200:
            raise JSONRPCException(response.text)
        j = response.json()    
        result = j.get('result', None)
        if result is None:
            raise JSONRPCException({
                'code': -343, 'message': 'missing JSON-RPC result'})
        
        return result

    def batch_(self, rpc_calls):
        """Batch RPC call.
           Pass array of arrays: [ [ "method", params... ], ... ]
           Returns array of results.
        """
        batch_data = []
        for rpc_call in rpc_calls:
            AuthServiceProxy.__id_count += 1
            m = rpc_call.pop(0)
            batch_data.append({"jsonrpc":"2.0", "method":m, "params":rpc_call, "id":AuthServiceProxy.__id_count})

        postdata = jsondumps(batch_data)
        log.debug("--> "+postdata)
        responses = self.__conn.post(url=self.__service_url,
        headers={
            'User-Agent': USER_AGENT,
            'Content-type': 'application/json',
            'Accept-encoding': 'br,gzip'
        },
        json=batch_data)
        results = []
        if responses.status_code != 200:
            raise JSONRPCException(responses.text)
        res = responses.json() 
        if isinstance(res, (dict,)):
            error = res.get('error', None)
            if error is not None:
                raise JSONRPCException(error)
            raise JSONRPCException({
                'code': -32700, 'message': 'Parse error'})
        for r in res:
            error = r.get('error', None)
            if error is not None:
                print(error)
                raise JSONRPCException(error)
            elif r.get('result', None) is None:
                raise JSONRPCException({
                    'code': -343, 'message': 'missing JSON-RPC result'})
            else:
                results.append(r.get('result'))
        return results
