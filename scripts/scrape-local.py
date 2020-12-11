#! /usr/bin/env python3
import os
import sys
import csv
import argparse
from warcio.capture_http import capture_http
import requests

def parseCommandLine(parser):
    """Command line parser"""

    parser.add_argument('configFile',
                        action='store',
                        type=str,
                        help='Apache config file with VirtualHost entries for each site')

    # Parse arguments
    arguments = parser.parse_args()
    return arguments

def errorExit(msg):
    """Print error to stderr and exit"""
    msgString = ('ERROR: ' + msg + '\n')
    sys.stderr.write(msgString)
    sys.exit(1)


def readConfig(configFile):
    """Read Apache config file, parse contents and
    return result as list"""

    # Text strings that identify start, end of virtual host entry
    vHostStart = "<VirtualHost *:80>"
    vHostEnd = "</VirtualHost>"

    # List that holds individual site dictionaries
    sites = []

    # Intialise empty siteInfo dictionary
    siteInfo = {}

    with open(configFile) as configIn:
        for line in configIn:
            if line.startswith(vHostEnd):
                # Append previous siteInfo dictionary to list
                try:
                    siteInfo['ServerName'] = ServerName
                    siteInfo['ServerAlias'] = ServerAlias
                    siteInfo['DocumentRoot'] = DocumentRoot
                    sites.append(siteInfo)
                except UnboundLocalError:
                    pass

                # Intialise empty siteInfo dictionary
                siteInfo = {}

            if line.startswith("ServerName"):
                ServerName = line.split()[1].strip()

            if line.startswith("ServerAlias"):
                ServerAlias = line.split()[1].strip()

            if line.startswith("DocumentRoot"):
                DocumentRoot = line.split()[1].strip()

            if line.startswith("ServerAlias"):
                ServerAlias = line.split()[1].strip()

    return sites


def scrapeSite(site):
    """Scrape one site"""

    ServerName = site["ServerName"]
    ServerAlias = site["ServerAlias"]
    DocumentRoot = site["DocumentRoot"]

    rootDir = os.path.abspath(DocumentRoot)

    # Use ServerName as basis for output WARC name
    warcOut = ServerName + ".warc.gz"

    # Remove warcOut if it already exists (otherwise multiple runs will add data
    # to pre-existing version of the file)
    if os.path.isfile(warcOut):
        try:
            os.remove(warcOut)
        except:
            msg = "cannot remove " + warcOut
            errorExit(msg)

    # Open URLs output file
    urlsOut = ServerName + ".urls.csv"

    try:
        fUrls = open(urlsOut, "w", encoding="utf-8")
    except IOError:
        msg = 'could not open file ' + urlsOut
        errorExit(msg)

    # List of URLs to scrape
    urls = []

    # First add domain root
    # TODO: or use www- address (ServerAlias), or both?
    #urls.append("http://" + ServerName)
    urls.append("http://" + ServerAlias)

    # Add remaining files (and rewrite file paths as URLs)
    for root, dirs, files in os.walk(rootDir):
        for filename in files:
            # Full path
            file_path = os.path.join(root, filename)

            # Construct url and add to list
            #url = file_path.replace(rootDir, "http://" + ServerName)
            url = file_path.replace(rootDir, "http://" + ServerAlias)
            urls.append(url)

        for dirname in dirs:
            # Full path
            file_path = os.path.join(root, dirname)

            # Construct url and add to list
            url = file_path.replace(rootDir, "http://" + ServerAlias)
            urls.append(url)

    # Start capturing stuff
    with capture_http(warcOut):
        # Iterate over URL list
        for url in urls:
            try:
                requests.get(url)
            except:
                print(url)
                raise
            try:
                fUrls.write(url + '\n')
            except IOError:
                msg = 'could not write file ' + fUrls
                errorExit(msg)

    fUrls.close()


def main():
    """
    Scrape locally rendered sites to compressed WARCs (one for each site)
    """

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Scrape locally rendered sites to compressed WARC')
    args = parseCommandLine(parser)
    configFile = os.path.abspath(args.configFile)

    # Read config file
    sites = readConfig(configFile)

    # Open output list of all sites
    sitesOut = "sites.csv"

    try:
        fSites = open(sitesOut, "w", encoding="utf-8")
    except IOError:
        msg = 'could not open file ' + sitesOut
        errorExit(msg)

    # Process sites
    for site in sites:
        #print(site["ServerName"])
        scrapeSite(site)
        try:
            fSites.write(site["ServerName"] + '\n')
        except IOError:
            msg = 'could not write file ' + fSites
            errorExit(msg)

    fSites.close()

main()