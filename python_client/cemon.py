#! /usr/bin/env python

import sys
import argparse
import jsonrpclib

RED    = "\x1b[1;31m"
GREEN  = "\x1b[1;32m"
YELLOW = "\x1b[1;33m"
BLUE   = "\x1b[1;34m"
RESET  = "\x1b[m"

def main():
    disp = 1.0
    responses = 0

    # Parse command line arguments.
    parser = argparse.ArgumentParser(description = 'CEMON Python based JSON-RPC client.')
    parser.add_argument("FILE", metavar = 'FILE', help = "File with service urls to consume.")
    parser.add_argument("START_DATE", metavar = 'START_DATE', help = "First date to query.")
    parser.add_argument("END_DATE", metavar = 'END_DATE', help = "Last date to query.")
    args = parser.parse_args()

    try:
        with open(args.FILE, 'r') as f:
            print "\nWelcome to the Python " + RED + "J"  + GREEN + "RPC" + RESET + "-" + BLUE + "CEMON" + RESET + " client.\n"
            print "Reading service URLs from " + GREEN + sys.argv[1] + RESET + "\n"
            print "Contacting services:"

            num_services = int(f.readline())
            for s in xrange(num_services):
                url = f.readline().rstrip("\n\t\r ").lstrip("\n\t\r ")
                server = jsonrpclib.Server(url)
                try:
                    resp = server.get_disponibility(args.START_DATE, args.END_DATE)
                    print "Service: " + BLUE + url + "\t [" + GREEN + " OK " + RESET + "]"
                    print "\t" + GREEN + "Returned" + RESET + " {Name: " + YELLOW + resp["name"] + RESET + \
                        ", Disponibility: " + YELLOW + str(resp["disponibility"]) + RESET + "}"

                    responses += 1
                    disp *= resp["disponibility"]
                    
                except Exception as e:
                    print "Service: " + BLUE + url + "\t [" + RED + "FAIL" + RESET + "]"
                    print "\t" + RED + str(e) + RESET

            # Print how many services responded.
            if responses < num_services:
                print "\n" + RED + str(responses) + RESET + " out of " + GREEN + str(num_services) + RESET + " services responded."
            else:
                print "\n" + GREEN + str(responses) + RESET + " out of " + GREEN + str(num_services) + RESET + " services responded."

            # Print the disponibility of the system.
            if responses > 0:
                if disp >= 0.95:
                    print "The disponibility of the service is: " + GREEN + str(disp) + RESET+ "\n"
                else:
                    print "The disponibility of the service is: " + BLUE + str(disp) + RESET + "\n"
            else:
                print RED + "Cannot calculate the disponibility of the service.\n" + RESET

    except Exception as e:
        print str(e)
                    
if __name__ == "__main__":
    main()
