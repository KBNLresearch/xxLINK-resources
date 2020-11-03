#! /usr/bin/env python3

"""
Restore sites from xxLINK tape, DLT version

Author: Johan van der Knijff

Example command line:

sudo python3 ~/kb/xxLINK-resources/scripts/restore-sites-DLT.py /media/johan/xxLINK/xxLINK-DLT/tapes-DLT/1/file000001 /home/johan/kb/xxLINK/siteData-DLT/1

NOTE: running as sudo is needed bc of permissions set in source data.

"""

import os
import sys
import csv
import argparse
import subprocess as sub
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

    siteInfo["isApacheConfig"] = isApacheConfig

    return siteInfo

def writeConfig(site, configOut, hostsOut):
    """Write output Apache config records for site"""

    with open(configOut, "a", encoding="utf-8") as cOut:
        cOut.write("<VirtualHost *:80>\n")
        cOut.write("ServerName " + site["ServerName"] + "\n")
        cOut.write("DocumentRoot " + site["pathOut"] + "\n")
        cOut.write("</VirtualHost>" + "\n\n")

    with open(hostsOut, "a", encoding="utf-8") as hOut:
        hOut.write("127.0.0.1 " + site["ServerName"] + "\n")
        hOut.write("127.0.0.1 " + "http://" + site["ServerName"] + "\n")
        #hOut.write("\n\n")

def fixSymLinks(folder, dirIn, dirOut):
    for root, _, files in os.walk(folder):
        for f in files:
            thisFile = os.path.join(root, f)
            try:
                os.stat(thisFile)
            except OSError:
                # Read link target
                linkTarget = os.readlink(thisFile)
                #print(thisFile, linkTarget, file=sys.stderr)
                
                # Leave relative links unchanged, update absolute links to input 
                # and output paths
                if os.path.isabs(linkTarget):
                    linkTargetIn = os.path.join(dirIn, linkTarget[1:])                    
                else:
                    linkTargetIn = os.path.join(root, linkTarget)
                    #print("linkTarget: " + linkTarget + "linkTargetIn: " + linkTargetIn, file=sys.stderr)

                linkTargetOut = os.path.join(dirOut, linkTarget.replace("/home/", ""))
                #print("linkTargetOut: " + linkTargetOut, file=sys.stderr)

                if os.path.isdir(linkTargetIn):
                    # Copy directory to outDir
                    try:
                        copy_tree(linkTargetIn, linkTargetOut, verbose=1, update=1, preserve_symlinks=1)
                    except:
                        print("ERROR copying " + linkTargetIn, file=sys.stderr)
                        #raise
                elif os.path.isfile(linkTargetIn):
                    try:
                        copyfile(linkTargetIn, linkTargetOut)
                    except:
                        print("ERROR copying " + linkTargetIn, file=sys.stderr)
                        #raise

                # Update symlink
                try:
                    linkTmp = os.path.join(root, "templink")
                    os.symlink(linkTargetOut, os.path.join(root, linkTmp))
                    os.replace(linkTmp, thisFile)
                except UnboundLocalError:
                    print("ERROR updating symlink %s" % linkTargetIn, file=sys.stderr)


def copyFiles(site, dirIn, dirOut):
    """Copy site's folder structure and apply correct permissions:
    - Dirs to 755
    - Files in source dir to 644
    - Files in exec (cgi-bin) dirs to 755
    """
    sourceDir = os.path.abspath(site["pathIn"])
    destDir = os.path.abspath(site["pathOut"])
    execDirs = site["execPaths"]

    print("====== PROCESSING SOURCE DIR " + sourceDir, file=sys.stderr)

    # Source dir tree
    if os.path.exists(sourceDir):

        try:
            # Note copy_tree by default aborts on broken symlinks, hence preserve_symlinks=1
            # However this means that these broken  
            copy_tree(sourceDir, destDir, verbose=1, update=1, preserve_symlinks=1)
        except:
            print("ERROR copying " + sourceDir, file=sys.stderr)

        # Search destination dir for broken symbolic links, fix them and copy
        # underlying data
        fixSymLinks(destDir, dirIn, dirOut)

        # Update permissions
        for root, dirs, files in os.walk(destDir): 
            for d in dirs:
                thisDir = os.path.join(root, d)
                try:
                    os.chmod(thisDir, 0o755)
                except OSError:
                    print("ERROR updating permissions for directory " + thisDir, file=sys.stderr)

            for f in files:
                thisFile = os.path.join(root, f)
                try:
                    os.chmod(thisFile, 0o644)
                except OSError:
                    print("ERROR updating permissions for file " + thisFile, file=sys.stderr)
    else:
        print("WARNING: directory " + sourceDir + " does not exist", file=sys.stderr)

    # Executable (cgi-bin) dirs (can be multiple or none at all)
    """
    for d in execDirs:
        for i, o in d.items():
            execSourceDir = os.path.abspath(i)
            execDestDir = os.path.abspath(o)
            print("====== PROCESSING EXEC DIR " + execSourceDir, file=sys.stderr)

            if os.path.exists(execSourceDir):
                try:
                    copy_tree(execSourceDir, execDestDir, verbose=1, update=1, preserve_symlinks=1)
                except:
                    print("ERROR copying " + execSourceDir, file=sys.stderr)

                # Search destination dir for broken symbolic links, fix them and copy
                # underlying data
                fixSymLinks(execDestDir, dirIn, dirOut)

                # Update permissions
                for root, dirs, files in os.walk(execDestDir):  
                    for f in files:
                        thisFile = os.path.join(root, f)
                        try:
                            os.chmod(thisFile, 0o755)
                        except OSError:
                            print("ERROR updating permissions for file " + thisFile, file=sys.stderr)
            else:
                print("WARNING: directory " + execSourceDir + " does not exist", file=sys.stderr)
    """


def main():
    """Main function"""

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Restore sites from xxLINK tape (DLT structure)')
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
            print(ServerName, pathIn, pathOut)
            ## TEST
            # Write config entry
            writeConfig(site, httpdConfOut, hostsOut)
            # Copy files
            #copyFiles(site, dirIn, dirOut)

if __name__ == "__main__":
    main()
