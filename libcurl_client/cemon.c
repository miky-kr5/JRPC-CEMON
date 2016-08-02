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

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <jansson.h>
#include <curl/curl.h>

/* ANSI escape codes for coloring the output.
 */
#define ANSI_BOLD_RED    "\x1b[1;31m"
#define ANSI_BOLD_GREEN  "\x1b[1;32m"
#define ANSI_BOLD_YELLOW "\x1b[1;33m"
#define ANSI_BOLD_BLUE   "\x1b[1;34m"
#define ANSI_RESET_STYLE "\x1b[m"

/* JSON-RPC protocol field constants.
 */
static const char * JSON_RPC_REQ_JRPC   = "jsonrpc";
static const char * JSON_RPC_VERSION    = "2.0";
static const char * JSON_RPC_REQ_METHOD = "method";
static const char * JSON_RPC_REQ_PARAMS = "params";
static const char * JSON_RPC_REQ_ID     = "id";

/* Jansson format string for a JSON-RPC request.
 */
static const char * JANSSON_REQ_FMT_STR = "{sssss[ss]si}";

/* JSON-RPC standard error codes.
 */
typedef enum JRPC_ERRORS { JRPC_PARSE_ERROR      = -32700,
			   JRPC_INVALID_REQ      = -32600,
			   JRPC_INVALID_METHOD   = -32601,
			   JRPC_INVALID_PARAMS   = -32602,
			   JRPC_RPC_ERROR        = -32603,
			   JRPC_SERVER_ERROR_MIN = -32099,
			   JRPC_SERVER_ERROR_M   = -32000
} jrpc_error_t;

/* Cemon specific JSON-RPC request parameters.
 */
static const char * METHOD_NAME = "get_disponibility";
static const int    BASE_ID     = 1;

/* User agent and service urls for cURL.
 */
static const char * USER_AGENT = "libcurl-cemon/1.0";
static char **      services   = NULL;
static int          num_services;

/* cURL connection data return struct.
 */
typedef struct DATA {
  char * memory;
  size_t size;
} data_t;

/* Boolean alias for convenience.
 */
typedef enum BOOL { FALSE = 0,
		    TRUE = 1
} bool_t;

/**
 * cURL uses this function to copy the data returned by a service into a struct
 * we can use.
 */
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

/**
 * Checks if a response obtained from a service is a valid JSON-RPC message.
 */
bool_t validate_response(json_t * root) {
  if(!json_is_object(root))
    return FALSE;
  
  return TRUE;
}

/**
 * Load the service URLs from a file.
 */
bool_t read_conf(const char * file_name) {
  int     i;
  size_t  n;
  ssize_t s;
  bool_t  ret_val = TRUE;
  char *  buffer  = NULL;
  FILE *  f       = fopen(file_name, "r");

  if(f == NULL)
    return FALSE;

  /* Read the number of services. */
  s = getline(&buffer, &n, f);
  if(s == -1) {
    /* If there was no line then fail. */
#ifndef NDEBUG
    perror(ANSI_BOLD_RED "ERROR" ANSI_RESET_STYLE ": failed to read number of services");
#endif
    ret_val = FALSE;
    goto read_conf_exit;
  }

  num_services = atoi(buffer);
  if(num_services == 0) {
    /* If there are no services then fail. */
    ret_val = FALSE;
    goto read_conf_exit;
  }

  /* Allocate memory for the URLs. */
  services = (char **)malloc(sizeof(char*) * num_services);
  memset(services, 0, sizeof(char **) * num_services);

  /* Read all services. */
  for(i = 0; i < num_services; i++) {
    s = getline(&services[i], &n, f);
    if(s == -1) {
      /* If there was no line then fail. */
#ifndef NDEBUG
      perror(ANSI_BOLD_RED "ERROR" ANSI_RESET_STYLE ": failed to read service URL");
#endif
      free(services);
      ret_val = FALSE;
      goto read_conf_exit;
    } else {
      /* Eliminate the line delimiter from the URL. */
      services[i][s - 1] = '\0';
    }
  }

 read_conf_exit:
  if(buffer != NULL)
    free(buffer);
  fclose(f);
  return ret_val;
}

/**
 * The function of the hour.
 */
int main(int argc, char ** argv) {
  int                 i;                             // Index used in loops.
  int                 curr_id   = BASE_ID;           // Id of the current request.
  int                 responses = 0;                 // Number of services that responded correctly.
  double              disponibility = 1.0;           // Total disponibility of the system.
  CURL   *            curl;                          // cURL handle.
  CURLcode            res;                           // cURL return code.
  data_t              chunk;                         // Data obtained from a service.
  json_t *            json_req = NULL;               // Jansson representation of a JSON-RPC request message.
  char   *            req;                           // JSON-RPC request message as text.
  json_t *            root = NULL;                   // Root element of a JSON-RPC response message.
  json_error_t        error;                         // Jansson return code.
  struct curl_slist * list = NULL;                   // HTTP headers list.

  /* Check command line arguments. */
  if(argc < 4) {
    fprintf(stderr, "Usage: %s FILE START_DATE END_DATE\n", argv[0]);
    return EXIT_FAILURE;
  }

  /* Print welcome header. */
  printf("\nWelcome to the libcurl " ANSI_BOLD_RED "J" ANSI_BOLD_GREEN "RPC" ANSI_RESET_STYLE "-" ANSI_BOLD_BLUE "CEMON" ANSI_RESET_STYLE " client.\n\n");
  printf("Reading service URLs from " ANSI_BOLD_GREEN "%s" ANSI_RESET_STYLE "\n\n", argv[1]);

  /* Try to read the service URLs. */
  if(!read_conf(argv[1])) {
    fprintf(stderr, ANSI_BOLD_RED "ERROR" ANSI_RESET_STYLE ": failed to parse config file.\n\n");
    return EXIT_FAILURE;
  }

  /* Get a cURL handle. */
  curl_global_init(CURL_GLOBAL_ALL);
  curl = curl_easy_init();

  /* Set the only HTTP header we will use. */
  list = curl_slist_append(list, "Content-Type: application/json");

  printf("Contacting services:\n");
  if(curl) {
    /* Contact each service read from the config file. */
    for(i = 0; i < num_services; i++) {
      chunk.memory = malloc(1);
      chunk.size = 0;

      printf("Service: " ANSI_BOLD_BLUE "%-40s" ANSI_RESET_STYLE, services[i]);
      
      /* Create a JSON-RPC request message. */
      json_req = json_pack(JANSSON_REQ_FMT_STR,
			   JSON_RPC_REQ_JRPC,
			   JSON_RPC_VERSION,
			   JSON_RPC_REQ_METHOD,
			   METHOD_NAME,
			   JSON_RPC_REQ_PARAMS,
			   argv[2],
			   argv[3],
			   JSON_RPC_REQ_ID,
			   curr_id++);
      assert(json_req != NULL);
      req = json_dumps(json_req, JSON_INDENT(0));
      assert(req != NULL);
      
      /* Set up the connection parameters. */
      curl_easy_setopt(curl, CURLOPT_URL, services[i]);                   // The connection URL.
      curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback); // The function that will get the return data.
      curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);          // The parameter to pass to the previous callback.
      curl_easy_setopt(curl, CURLOPT_USERAGENT, USER_AGENT);              // The user agent string.
      curl_easy_setopt(curl, CURLOPT_POSTFIELDS, req);                    // The HTTP POST data to send.
      curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)strlen(req));   // The length of the POST data.
      curl_easy_setopt(curl, CURLOPT_HTTPHEADER, list);                   // The "Content-Type" HTTP header field.
 
      /* Perform the connection. */
      res = curl_easy_perform(curl);

      if(res != CURLE_OK) {
	/* If the service failed to respond or wasn't there then print an error message. */
	printf(" [" ANSI_BOLD_RED "FAIL" ANSI_RESET_STYLE "]\n");
	printf("\t" ANSI_BOLD_RED "ERROR" ANSI_RESET_STYLE ": Service did not answer.\n");
#ifndef NDEBUG
	fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
#endif

      } else {
	/* Else process the received response. */
	printf(" [" ANSI_BOLD_GREEN " OK " ANSI_RESET_STYLE "]\n");
#ifndef NDEBUG
	fprintf(stderr, "SERVICE: %s - RESPONSE: %s\n", services[i], chunk.memory);
#endif

	/* Attempt to parse the JSON text received. */
	root = json_loads(chunk.memory, 0, &error);
	if(!root) {
	  printf("\t" ANSI_BOLD_RED "ERROR" ANSI_RESET_STYLE ": failed to parse response from " ANSI_BOLD_BLUE "%-40s" ANSI_RESET_STYLE, services[i]);
	} else {
	  if(validate_response(root)) {
	    printf("\t" ANSI_BOLD_GREEN "Returned" ANSI_RESET_STYLE " {Name: " ANSI_BOLD_YELLOW "%s" ANSI_RESET_STYLE, "COMING SOON");
	    printf(", Disponibility: " ANSI_BOLD_YELLOW "%1.2lf" ANSI_RESET_STYLE "}\n", 1.0);
	    responses++;
	  }

	  json_decref(root);
	}
      }

      /* Calculate the disponibility. */
      disponibility *= 1.0;
      
      /* Clean up. */
      free(chunk.memory);
      json_decref(json_req);
      free(req);
    }

    /* Print how many services responded. */
    if(responses < num_services)
      printf("\n" ANSI_BOLD_RED "%d" ANSI_RESET_STYLE " out of " ANSI_BOLD_GREEN "%d" ANSI_RESET_STYLE " services responded.\n", responses, num_services);
    else
      printf("\n" ANSI_BOLD_GREEN "%d" ANSI_RESET_STYLE " out of " ANSI_BOLD_GREEN "%d" ANSI_RESET_STYLE " services responded.\n", responses, num_services);

    /* Print the disponibility of the system. */
    if(disponibility >= 0.95)
      printf("The disponibility of the service is: " ANSI_BOLD_GREEN "%1.2lf" ANSI_RESET_STYLE "\n\n", disponibility);
    else
      printf("The disponibility of the service is: " ANSI_BOLD_BLUE "%1.2lf" ANSI_RESET_STYLE "\n\n", disponibility);
    
    /* Close cURL. */
    curl_slist_free_all(list);
    curl_easy_cleanup(curl);
    curl_global_cleanup();
  }

  /* Good bye. */
  return EXIT_SUCCESS;
}
