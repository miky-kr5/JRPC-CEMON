#! /usr/bin/env python
# _*_ coding: UTF-8 _*_

"""
Copyright (c) 2016, Miguel Angel Astor Romero
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import random as r
import sys
import json

import web

urls = (
    '/database', 'DBService',
    '/server', 'ServerService',
    '/app', 'AppService',
    '/link', 'LinkService',
    '/router', 'RouterService'
)

class JRPCError(Exception):
    pass

class JRPCInvalidRequestError(JRPCError):
    def __init__(self, jrpc_id):
        self.jrpc_id = jrpc_id

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": -32600, "message": "Invalid request"}})

class JRPCUnknownMethodError(JRPCError):
    def __init__(self, method, jrpc_id):
        self.method  = method
        self.jrpc_id = jrpc_id

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": -32601, "message": "Method '" + self.method + "' not found"}})
    
class JRPCNotificationError(JRPCError):
    def __init__(self):
        pass

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32089, "message": 'JSON-RPC notifications not supported'}})

class BaseService(object):
    name = "BASE SERVICE"

    def get_disponibility(self):
        return r.random()
    
    def validate_request(self, req):
        if not req.has_key("jsonrpc") and not req.has_key("method"):
            raise JRPCInvalidRequestError(None)

        if not req.has_key("id"):
            raise JRPCNotificationError()

        version = req["jsonrpc"]
        _id = req["id"]
        method = req["method"]

        if version != "2.0":
            raise JRPCInvalidRequestError(_id)
        if method not in dir(self):
            raise JRPCUnknownMethodError(method, _id)

        return (version, _id, method)

    def POST(self):
        try:
            _id = None
            req = json.loads(web.data())
            version, _id, method = self.validate_request(req)
            disp = getattr(self, method)()
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "result": disp})
            
        except JRPCError as e:
            response = str(e)

        except ValueError:
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "error": {"code": -32700, "message": "Parse error"}})
            
        except Exception as e:
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "error": {"code": -32099, "message": "Internal server error"}})

        return response

class DBService(BaseService):
    name = "DATABASE"

class ServerService(BaseService):
    name = "SERVER HARDWARE"

class AppService(BaseService):
    name = "APPLICATION"

class LinkService(BaseService):
    name = "INTERNET LINK"

class RouterService(BaseService):
    name = "INTERNET ROUTER"
    
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
