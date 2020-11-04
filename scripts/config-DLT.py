#! /usr/bin/env python3

"""
Generate configuration for xxLINK sites, DLT version

Author: Johan van der Knijff

Example command line:

python3 ~/kb/xxLINK-resources/scripts/config-DLT.py /media/johan/xxLINK/xxLINK-DLT/tapes-DLT/1/file000001 /home/johan/kb/xxLINK/siteData-DLT/1

"""

import os
import sys
import csv
import argparse
from shutil import which
from shutil import copyfile
from distutils.dir_util import copy_tree


def parseCommandLine(parser):
    """Command line parser"""

    parser.add_argument('dirIn',
                        action='store',
                        type=str,
                        help='input directory')
    parser.add_argument('dirOut',
                        action='store',
                        type=str,
                        help='output directory')

    # Parse arguments
    arguments = parser.parse_args()
    return arguments


def errorExit(msg):
    """Print error to stderr and exit"""
    msgString = ('ERROR: ' + msg + '\n')
    sys.stderr.write(msgString)
    sys.exit(1)


def readConfigDir(dirIn, dirOut):
    """
    Read config dir, filter site config files and return
    list with dictionary for each site
    """

    configDirIn = os.path.join(dirIn, "apache.intel/conf/configdb")

    # List that holds individual site dictionaries
    sites = []

    if os.path.exists(configDirIn):
        for path in os.listdir(configDirIn):
            thisPath = os.path.join(configDirIn, path)
            if os.path.isfile(thisPath):
                siteInfo = readApacheConfig(thisPath, dirIn, dirOut)
                if siteInfo["isApacheConfig"]:
                    sites.append(siteInfo)
    return sites


def readApacheConfig(configFile, dirIn, dirOut):
    """
    Read Apache config file, extract interesting bits and return
    them in dictionary
    """

    siteInfo = {}
    isApacheConfig = False

    with open(configFile) as configIn:
        # TODO: Include RewriteRule entries?
        for line in configIn:
            if line.startswith("<VirtualHost"):
                isApacheConfig = True
            if line.startswith("DocumentRoot"):
                DocumentRoot = line.split()[1].strip()
                siteInfo["DocumentRoot"] = DocumentRoot
            if line.startswith("ServerName"):
                ServerName = line.split()[1].strip()
                siteInfo["ServerName"] = ServerName
                 if not ServerName.startswith("www."):
                    ServerAlias = "www." + ServerName
                    siteInfo["ServerAlias"] = ServerAlias

    siteInfo["isApacheConfig"] = isApacheConfig

    return siteInfo

def writeConfig(site, configOut, hostsOut):
    """Write output Apache config records for site"""

    with open(configOut, "a", encoding="utf-8") as cOut:
        cOut.write("<VirtualHost *:80>\n")
        cOut.write("ServerName " + site["ServerName"] + "\n")
        try:
            cOut.write("ServerAlias " + site["ServerAlias"] + "\n")
        except KeyError:
            pass
        cOut.write("DocumentRoot " + site["pathOut"] + "\n")
        cOut.write("</VirtualHost>" + "\n\n")

    with open(hostsOut, "a", encoding="utf-8") as hOut:
        hOut.write("127.0.0.1 " + site["ServerName"] + "\n")
        hOut.write("127.0.0.1 " + "http://" + site["ServerName"] + "\n")
        #hOut.write("\n\n")

def main():
    """Main function"""

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Generate config for xxLINK sites (DLT structure)')
    args = parseCommandLine(parser)
    dirIn = os.path.abspath(args.dirIn)
    dirOut = os.path.abspath(args.dirOut)

    # String constants
    DocumentRootPrefix = "/export/home/local/www"
    wwwIn = os.path.join(dirIn, "www")
    wwwOut = os.path.join(dirOut, "www")

    # Dir, files for output config
    dirOutEtc = os.path.join(dirOut, "etc")
    httpdConfOut = os.path.join(dirOutEtc, "sites.conf")
    hostsOut = os.path.join(dirOutEtc, "hosts")

    # Read info on sites from config file
    #sites = readApacheConfig(dirIn, dirOut)
    sites = readConfigDir(dirIn, dirOut)

    # Create output etc directory
    if not os.path.exists(dirOutEtc):
        os.makedirs(dirOutEtc)

    # Remove output config files they already exist
    if os.path.isfile(httpdConfOut):
        os.remove(httpdConfOut)
    if os.path.isfile(hostsOut):
        os.remove(hostsOut)

    ## TODO: in some case either ServerName or DocumentRoot are missing from config
    # file. Mostly happens for .xxLINK domains, but also for www.hospitalitynet.org
    # which imports a value using INCLUDE file. For now ignore these.

    for site in sites:
        hasServerName = True
        hasDocumentRoot = True
        try:
            ServerName = site["ServerName"]
        except KeyError:
            hasServerName = False
        try:
            DocumentRoot = site["DocumentRoot"]
        except KeyError:
            if ServerName == "www.hospitalitynet.org":
                # Fix for missing DocumentRoot hospitalitynet
                DocumentRoot = "/export/home/local/www/hospitorg/root"
            else:
                hasDocumentRoot = False

        if hasServerName and hasDocumentRoot:
            # Construct source and destination paths
            pathIn = DocumentRoot.replace(DocumentRootPrefix, wwwIn)
            pathOut = DocumentRoot.replace(DocumentRootPrefix, wwwOut)
            site["pathIn"] = pathIn
            site["pathOut"] = pathOut
            ## TEST
            #print(ServerName, pathIn, pathOut)
            ## TEST
            # Write config entry
            writeConfig(site, httpdConfOut, hostsOut)

if __name__ == "__main__":
    main()
