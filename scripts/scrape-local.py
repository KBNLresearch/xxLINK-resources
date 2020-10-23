#! /usr/bin/env python3
import os
import argparse
from warcio.capture_http import capture_http
import requests

def parseCommandLine(parser):
    """Command line parser"""

    parser.add_argument('configFile',
                        action='store',
                        type=str,
                        help='Apache config file with VirtualHost entries for each site')
    parser.add_argument('warcOut',
                        action='store',
                        type=str,
                        help='output compressed WARC file')

    # Parse arguments
    arguments = parser.parse_args()
    return arguments


def readConfig(configFile):
    """Read Apache config file, parse contents and
    return result as list"""

    # Text strings that identify start, end of virtual host entry
    vHostStart = "<VirtualHost *:80>"
    vHostEnd = "</VirtualHost>"

    # List that holds individual site dictionaries
    sites = [] 

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

        # Append final siteInfo dictionary to list
        try:
            siteInfo['ServerName'] = ServerName
            siteInfo['ServerAlias'] = ServerAlias
            siteInfo['DocumentRoot'] = DocumentRoot
            sites.append(siteInfo)
        except UnboundLocalError:
            pass

    return sites


def scapeSite(site, warcOut):
    """Scrape one site"""

    ServerName = site["ServerName"]
    ServerAlias = site["ServerAlias"]
    DocumentRoot = site["DocumentRoot"]

    rootDir = os.path.abspath(DocumentRoot)

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


def main():
    """
    Scrape locally rendered sites to compressed WARC.
    """

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Scrape locally rendered sites to compressed WARC')
    args = parseCommandLine(parser)
    configFile = os.path.abspath(args.configFile)
    warcOut = os.path.abspath(args.warcOut)

    # Read config file
    sites = readConfig(configFile)
    print(sites)

    # Process sites
    for site in sites:
        scapeSite(site, warcOut)
        #print(ServerName, ServerAlias, DocumentRoot)

    """
    url = line.split()[1].strip()
    siteInfo['url'] = url
    siteInfo['serverName'] = url.replace("www.", "")
    """

    #siteName = "ziklies.home.xs4all.nl"
    #scapeSite(siteName, warcOut)

main()