/************************************************************************************
 * Copyright (c) 2016, Miguel Angel Astor Romero                                    *
 * All rights reserved.                                                             *
 *                                                                                  *
 * Redistribution and use in source and binary forms, with or without               *
 * modification, are permitted provided that the following conditions are met:      *
 *                                                                                  *
 * * Redistributions of source code must retain the above copyright notice, this    *
 *   list of conditions and the following disclaimer.                               *
 *                                                                                  * 
 * * Redistributions in binary form must reproduce the above copyright notice,      *
 *   this list of conditions and the following disclaimer in the documentation      *
 *   and/or other materials provided with the distribution.                         *
 *                                                                                  *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"      *
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE        *
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE   *
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE     *
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL       *
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR       *
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER       *
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,    *
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE    *
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.             *
 ************************************************************************************/
/* Uses the "WriteMemoryCallback" function and associated data structure from the
 * cURL tutorials. WriteMemoryCallback is copyright (C) 1998, 2016 of Daniel Stenberg.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <jansson.h>
#include <curl/curl.h>

#define NUM_SERVICES 5

static const char * JSON_RPC_REQ_JRPC   = "jsonrpc";
static const char * JSON_RPC_VERSION    = "2.0";
static const char * JSON_RPC_REQ_METHOD = "method";
static const char * JSON_RPC_REQ_ID     = "id";
static const char * JANSSON_REQ_FMT_STR = "{sssssi}";

typedef enum JRPC_ERRORS { JRPC_PARSE_ERROR        = -32700,
			   JRPC_INVALID_REQ        = -32600,
			   JRPC_INVALID_METHOD     = -32601,
			   JRPC_INVALID_PARAMS     = -32602,
			   JRPC_RPC_ERROR          = -32603,
			   JRPC_SERVER_ERROR_MIN   = -32099,
			   JRPC_SERVER_ERROR_M     = -32000
} jrpc_error_t;

static const char * METHOD_NAME         = "get_disponibility";
static const int    BASE_ID             = 1;

static const char * USER_AGENT = "libcurl-cemon/1.0";
static const char * SERVICES[NUM_SERVICES] = { "http://localhost:8080/database",
					       "http://localhost:8080/server",
					       "http://localhost:8080/app",
					       "http://localhost:8080/link",
					       "http://localhost:8081/router"};

typedef struct DATA {
  char *memory;
  size_t size;
} data_t;

typedef enum BOOL {FALSE = 0, TRUE = 1} bool_t;

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
  size_t   realsize = size * nmemb;
  data_t * mem      = (data_t *)userp;
 
  mem->memory = realloc(mem->memory, mem->size + realsize + 1);
  if(mem->memory == NULL) {
    printf("not enough memory (realloc returned NULL)\n");
    return 0;
  }
 
  memcpy(&(mem->memory[mem->size]), contents, realsize);
  mem->size += realsize;
  mem->memory[mem->size] = 0;
 
  return realsize;
}

bool_t validate_response(json_t * root) {
  if(!json_is_object(root))
    return FALSE;
  
  return TRUE;
}

int main(void) {
  int          i;
  int          curr_id   = BASE_ID;
  int          responses = 0;
  double       disponibilities[NUM_SERVICES];
  double       total_disp = 1.0;
  CURL   *     curl;
  CURLcode     res;
  data_t       chunk;
  json_t *     json_req;
  char   *     req;
  json_t *     root = NULL;
  json_error_t error;

  memset(disponibilities, 0, NUM_SERVICES * sizeof(double));

  curl_global_init(CURL_GLOBAL_ALL);
  curl = curl_easy_init();

  if(curl) {
    for(i = 0; i < NUM_SERVICES; i++) {
      chunk.memory = malloc(1);
      chunk.size = 0;

      printf("SERVICE: \x1b[1;34m%-40s\x1b[m", SERVICES[i]);
      
      json_req = json_pack(JANSSON_REQ_FMT_STR,
			   JSON_RPC_REQ_JRPC,
			   JSON_RPC_VERSION,
			   JSON_RPC_REQ_METHOD,
			   METHOD_NAME,
			   JSON_RPC_REQ_ID,
			   curr_id++);
      req = json_dumps(json_req, JSON_INDENT(0));
      
      curl_easy_setopt(curl, CURLOPT_URL, SERVICES[i]);
      curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
      curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
      curl_easy_setopt(curl, CURLOPT_USERAGENT, USER_AGENT);
      curl_easy_setopt(curl, CURLOPT_POSTFIELDS, req);
      curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)strlen(req));
 
      res = curl_easy_perform(curl);

      if(res != CURLE_OK) {
	printf(" [\x1b[1;31mFAIL\x1b[m]\n");
#ifndef NDEBUG
	fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
#endif

      } else {
	printf(" [\x1b[1;32m OK \x1b[m] DISP: \x1b[1;34m%1.2lf\x1b[m\n", 1.0);
#ifndef NDEBUG
	fprintf(stderr, "SERVICE: %s - RESPONSE: %s\n", SERVICES[i], chunk.memory);
#endif

	root = json_loads(chunk.memory, 0, &error);
	if(!root) {
	  printf("\x1b[1;31mERROR\x1b[m: failed to parse response from \x1b[1;34m%-40s\x1b[m", SERVICES[i]);
	} else {
	  if(validate_response(root))
	    responses++;

	  free(root);
	}
      }

      total_disp *= 1.0;
      
      free(chunk.memory);
      free(json_req);
      free(req);
    }

    if(responses == 1)
      printf("\n\x1b[1;31m1\x1b[m service of %d responded.\n", NUM_SERVICES);
    else if(responses < NUM_SERVICES)
      printf("\n\x1b[1;31m%d\x1b[m services of %d responded.\n", responses, NUM_SERVICES);
    else
      printf("\n\x1b[1;32m%d\x1b[m services of %d responded.\n", responses, NUM_SERVICES);

    printf("The disponibility of the service is: \x1b[1;32m%1.2lf\x1b[m\n\n", total_disp);
    
    curl_easy_cleanup(curl);
    curl_global_cleanup();
  }

  return 0;
}
