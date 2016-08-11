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

-------------------------------------------------------------------------------

Execute as 'service.py IP:PORT SERVICE_NAME'.

"""

import numpy as np
import sys
import json

import web

##############################################################################
# GLOBAL DEFINITIONS                                                         #
##############################################################################

# Default service name. Should never be used.
CEMON_SERVICE_NAME = "DEFAULT"

# Parameters for the normal random number generator ahead.
SERVICE_MU = 0.95
SERVICE_SIGMA = 0.2

# JSON-RPC standard error codes and extensions.
JRPC_PARSE_ERROR      = -32700
JRPC_INVALID_REQ      = -32600
JRPC_INVALID_METHOD   = -32601
JRPC_INVALID_PARAMS   = -32602
JRPC_RPC_ERROR        = -32603
JRPC_NO_NOTIFY_ERROR  = -32089       
JRPC_NO_BATCH_ERROR   = -32088

# URLs recognized by the service.
urls = (
    '/rpc', 'JRPCService'
)

##############################################################################
# EXCEPTION HANDLING                                                         #
##############################################################################

class JRPCError(Exception):
    """ Base class for JSON-RPC derived errors. """
    pass

class JRPCInvalidRequestError(JRPCError):
    """ Exception to raise when a request message is not valid. """

    def __init__(self, jrpc_id, msg):
        self.jrpc_id = jrpc_id
        self.msg = msg

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": JRPC_INVALID_REQ, "message": "Invalid request: " + self.msg}})

class JRPCUnknownMethodError(JRPCError):
    """ Exception to raise when a request message references and unknown or
    unexported method. """

    def __init__(self, method, jrpc_id):
        self.method  = method
        self.jrpc_id = jrpc_id

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": JRPC_INVALID_METHOD, "message": "Method '" + self.method + "' not found"}})
    
class JRPCNotificationError(JRPCError):
    """ Exception to raise when a notification is received. 
    JSON-RPC 2.0 notifications are not supported at this time. """

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": JRPC_NO_NOTIFY_ERROR, "message": 'JSON-RPC notifications not supported'}})

class JRPCBatchError(JRPCError):
    """ Exception to raise when a batch request message received.
    JSON-RPC 2.0 batch requests are not supported at this time. """

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": JRPC_NO_BATCH_ERROR, "message": 'JSON-RPC batch requests not supported'}})

class JRPCInvalidParamsError(JRPCInvalidRequestError):
    """ Exception to raise when a request message has unrecognized or
    otherwise invalid params for a valid method. """

    def __str__(self):
        return json.dumps({"jsonrpc": "2.0", "id": self.jrpc_id, "error": {"code": JRPC_INVALID_PARAMS, "message": "Invalid parameters: " + self.msg}})

##############################################################################
# WEB.PY URL HANDLER CLASS                                                   #
##############################################################################

class JRPCService(object):
    """ This class handles the POST method for the '/rpc' URL as defined above. """

    # List of methods from this class that can be called with JSON-RPC.
    exported_methods = ['get_disponibility']

    def get_disponibility(self, start_date, end_date):
        """ Returns a normal-distributed random number between 0.0 and 1.0 """
        return min(abs(np.random.normal(SERVICE_MU, SERVICE_SIGMA)), 1.0)

    def _check_params(self, req, method, _id):
        """ Validates the parameters of a JSON-RPC 2.0 request for the 'get_disponibility' method. """
        params = None

        # First check if the request has parameters at all.
        if req.has_key("params"):
            params = req["params"] 

            # Then check the type of the parameters structure.
            if type(params) == list:
                # If it is a list then check if it has anything else than exactly 2 elements.
                if len(params) != 2:
                    raise JRPCInvalidParamsError(_id, "Array params must contain two values")

                else:
                    # If there are 2 elements, then check if they are both unicode strings.
                    if type(params[0]) != unicode or type(params[1]) != unicode:
                        raise JRPCInvalidParamsError(_id, "Array params must be string values")

            elif type(params) == dict:
                # If it is a dictionary, then check if it is missing the two named parameters received by the
                # function.
                if not params.has_key("start_date") or not params.has_key("end_date"):
                    raise JRPCInvalidParamsError(_id, 'Missing key params "start_date" or "end_date"')

                elif type(params["start_date"]) is not unicode or type(params["end_date"]) is not unicode:
                    # If both elements exist, then check that they are unicode strings.
                    raise JRPCInvalidParamsError(_id, "Object params must be string values")                    

            else:
                raise JRPCInvalidParamsError(_id, "Params must an array or object")

        else:
            raise JRPCInvalidParamsError(_id, 'Params are required for "' + method + '"')

        return params

    def _validate_request(self, req):
        """ Checks if a JSON-RPC request is valid. """

        if type(req) == list:
            # If the request is a batch request, then fail.
            raise JRPCBatchError()
        else:
            # Check for the mandatory elements of a request message.
            try:
                # All requests and notifications must contain a version number and method name.
                if not req.has_key("jsonrpc") or not req.has_key("method"):
                    raise JRPCInvalidRequestError(None, "Request is missing mandatory attributes")

                # Notifications (requests without an id) are not supported.
                if not req.has_key("id"):
                    raise JRPCNotificationError()

            except AttributeError as e:
                raise JRPCInvalidRequestError(None, "Request's root is not a JSON object")

            # Get the version number, id and method name, then validate them.
            version = req["jsonrpc"]
            _id = req["id"]
            method = req["method"]

            # JSON-RPC 2.0 mandates that the version number MUST always be 2.0
            if version != "2.0":
                raise JRPCInvalidRequestError(_id, "Invalid version number: " + version)

            # Check if the method is in the list of exported methods.
            if method not in self.exported_methods:
                raise JRPCUnknownMethodError(method, _id)

            # Get the parameters from the request.
            params = self._check_params(req, method, _id)

            return (version, _id, method, params)

    def POST(self):
        """ Handle the post request. """
        global CEMON_SERVICE_NAME

        # Set the service name.
        CEMON_SERVICE_NAME = sys.argv[-1]

        # Try to process the received request message.
        try:
            # Parse the JSON text and validate it as a JSON-RPC 2.0 request.
            _id = None
            req = json.loads(web.data())
            version, _id, method, params = self._validate_request(req)

            # Execute the requested method according to the type of the parameters structure.
            if type(params) == list:
                disp = getattr(self, method)(params[0], params[1])
            elif type(params) == dict:
                disp = getattr(self, method)(params["start_date"], params["end_date"])
            else:
                # This should never happen. Catched as an exception instead of an assert to avoid
                # bringing down the server unnecesarily.
                raise Exception("Mind boggling invalid params!")

            # Prepare the JSON-RPC 2.0 reply.
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "result": {"name": CEMON_SERVICE_NAME, "disponibility": disp}})
        
        # Catch all possible errors and prepare the corresponding response messages.
        except JRPCError as e:
            response = str(e)

        except ValueError:
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "error": {"code": -32700, "message": "Parse error"}})
            
        except Exception as e:
            response = json.dumps({"jsonrpc": "2.0", "id": _id, "error": {"code": -32099, "message": "Internal server error: " + str(e)}})

        # Reply to the client.
        return response

##############################################################################
# SCRIPT ENTRY POINT                                                         #
##############################################################################

if __name__ == "__main__":
    # Check for command line arguments.
    if len(sys.argv) >= 3:
        app = web.application(urls, globals())
        app.run()
    else:
        raise Exception("Usage: " + sys.argv[0] + " NAME")
