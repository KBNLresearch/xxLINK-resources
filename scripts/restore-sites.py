#! /usr/bin/env python3

"""
Restore sites from xxLINK tape

Author: Johan van der Knijff
Requirements:

1. Unix/Linux environment with 'rsync' tool installed

Example command line:

python3 ~/kb/xxLINK-resources/scripts/restore-sites.py /home/johan/kb/xxLINK/tapes-DDS/2/file000001/home/local/www /home/johan/kb/xxLINK/siteData-DDS/2/www /home/johan/kb/xxLINK/tapes-DDS/2/file000001/home/local/etc/httpd.conf /home/johan/kb/xxLINK/siteData-DDS/2/etc/sites.conf

"""

import os
import sys
import csv
import argparse
import subprocess as sub
from shutil import which


def parseCommandLine(parser):
    """Command line parser"""

    parser.add_argument('wwwIn',
                        action='store',
                        type=str,
                        help='input www directory')
    parser.add_argument('wwwOut',
                        action='store',
                        type=str,
                        help='output www directory')
    parser.add_argument('httpdConfIn',
                        action='store',
                        type=str,
                        help='input httpd.conf file')
    parser.add_argument('httpdConfOut',
                        action='store',
                        type=str,
                        help='output httpd.conf file')

    # Parse arguments
    arguments = parser.parse_args()
    return arguments


def errorExit(msg):
    """Print error to stderr and exit"""
    msgString = ('ERROR: ' + msg + '\n')
    sys.stderr.write(msgString)
    sys.exit(1)


def launchSubProcess(args):
    """Launch subprocess and return exit code, stdout and stderr"""
    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        output, errors = p.communicate()

        # Decode to UTF8
        outputAsString = output.decode('utf-8')
        errorsAsString = errors.decode('utf-8')

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...

        exitStatus = -99
        outputAsString = ""
        errorsAsString = ""

    return exitStatus, outputAsString, errorsAsString


def main():
    """Main function"""

    # Check if rsync tool is installed
    if which('rsync') is None:
        msg = "'rsync' tool is not installed"
        errorExit(msg)

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Restore sites from xxLINK tape')
    args = parseCommandLine(parser)
    wwwIn = args.wwwIn
    wwwOut = args.wwwOut
    httpdConfIn = args.httpdConfIn
    httpdConfOut = args.httpdConfOut

    # Prefix / suffix used in Map entries (need to be stripped)
    mapPrefix="/htbin/htimage/home/local/www"
    mapSuffix="/*.map"

    # List that holds individual site dictionaries
    sites = []

    newSite = False
    
    with open(httpdConfIn) as configIn:
        for line in configIn:
            if line.startswith("MultiHost"):
                newSite = True
                # Reset record counters
                noMaps = 0
                noExecs = 0
                noWelcomes = 0

                # Append previous siteInfo dictionary to list
                try:
                    sites.append(siteInfo)
                except UnboundLocalError:
                    # siteInfo doesn't exist atv start of first processed site
                    pass

                # Intialise empty siteInfo dictionary
                siteInfo = {}

                url = line.split()[1].strip()
                siteInfo['url'] = url
                siteInfo['serverName'] = url.replace("www.", "")

            if line.startswith("Map") and noMaps == 0:
                # Only read 1st map entry for a site
                mapPath = line.split()[2].strip()

                if mapPath != "/noproxy.htm":
                    # Remove suffix
                    mapPath = mapPath.replace(mapSuffix, "")

                    # Construct source and destination paths
                    pathIn = mapPath.replace(mapPrefix, wwwIn)
                    pathOut = mapPath.replace(mapPrefix, wwwOut)

                    siteInfo['pathIn'] = pathIn
                    siteInfo['pathOut'] = pathOut
                    noMaps += 1

            if line.startswith("Welcome") and noWelcomes == 0:
                indexPage = line.split()[1].strip()
                noWelcomes += 1
                siteInfo['indexPage'] = indexPage

    print(sites)



if __name__ == "__main__":
    main()
