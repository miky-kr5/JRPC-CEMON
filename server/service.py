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

CEMON_SERVICE_NAME = "DEFAULT"

JRPC_PARSE_ERROR      = -32700
JRPC_INVALID_REQ      = -32600
JRPC_INVALID_METHOD   = -32601
JRPC_INVALID_PARAMS   = -32602
JRPC_RPC_ERROR        = -32603
JRPC_NO_NOTIFY_ERROR  = -32089       
JRPC_NO_BATCH_ERROR   = -32088

urls = (
    '/rpc', 'JRPCService'
)

class JRPCError(Exception):
    pass

class JRPCInvalidRequestError(JRPCError):
    def __init__(self, jrpc_id, msg):
        self.jrpc_id = jrpc_id
        self.msg = msg

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": JRPC_INVALID_REQ, "message": "Invalid request: " + self.msg}})

class JRPCUnknownMethodError(JRPCError):
    def __init__(self, method, jrpc_id):
        self.method  = method
        self.jrpc_id = jrpc_id

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": JRPC_INVALID_METHOD, "message": "Method '" + self.method + "' not found"}})
    
class JRPCNotificationError(JRPCError):
    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": JRPC_NO_NOTIFY_ERROR, "message": 'JSON-RPC notifications not supported'}})

class JRPCBatchError(JRPCError):
    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": JRPC_NO_BATCH_ERROR, "message": 'JSON-RPC batch requests not supported'}})

class JRPCInvalidParamsError(JRPCInvalidRequestError):
    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": JRPC_INVALID_PARAMS, "message": "Invalid parameters: " + self.msg}})

class JRPCService(object):
    exported_methods = ['get_disponibility']

    def get_disponibility(self, start_date, end_date):
        return r.random()

    def _check_params(self, req, method, _id):
        params = None

        if req.has_key("params"):
            params = req["params"] 

            if type(params) == list:
                if len(params) != 2:
                    raise JRPCInvalidParamsError(_id, "Array params must contain two values")
                else:
                    if type(params[0]) != unicode or type(params[1]) != unicode:
                        raise JRPCInvalidParamsError(_id, "Array params must be string values")

            elif type(params) == dict:
                if not params.has_key("start_date") or not params.has_key("end_date"):
                    raise JRPCInvalidParamsError(_id, 'Missing key params "start_date" or "end_date"')
            else:
                raise JRPCInvalidParamsError(_id, "Params must an array or object")

        else:
            raise JRPCInvalidParamsError(_id, 'Params are required for "' + method + '"')

        return params

    def _validate_request(self, req):
        if type(req) == list:
            raise JRPCBatchError()
        else:
            try:
                if not req.has_key("jsonrpc") or not req.has_key("method"):
                    raise JRPCInvalidRequestError(None, "Request is missing mandatory attributes")

                if not req.has_key("id"):
                    raise JRPCNotificationError()

            except AttributeError as e:
                raise JRPCInvalidRequestError(None, "Request's root is not a JSON object")

            version = req["jsonrpc"]
            _id = req["id"]
            method = req["method"]

            if version != "2.0":
                raise JRPCInvalidRequestError(_id, "Invalid version number: " + version)

            if method not in self.exported_methods:
                raise JRPCUnknownMethodError(method, _id)

            params = self._check_params(req, method, _id)

            return (version, _id, method, params)

    def POST(self):
        global CEMON_SERVICE_NAME
        CEMON_SERVICE_NAME = sys.argv[-1]

        try:
            _id = None
            req = json.loads(web.data())
            version, _id, method, params = self._validate_request(req)
            if type(params) == list:
                disp = getattr(self, method)(params[0], params[1])
            elif type(params) == dict:
                disp = getattr(self, method)(params["start_date"], params["end_date"])
            else:
                raise Exception("Mind boggling invalid params!")
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "result": {"name": CEMON_SERVICE_NAME, "disponibility": disp}})
            
        except JRPCError as e:
            response = str(e)

        except ValueError:
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "error": {"code": -32700, "message": "Parse error"}})
            
        except Exception as e:
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "error": {"code": -32099, "message": "Internal server error: " + str(e)}})

        return response

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        app = web.application(urls, globals())
        app.run()
    else:
        raise Exception("Usage: " + sys.argv[0] + " NAME")
