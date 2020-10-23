#! /usr/bin/env python3

"""
Restore sites from xxLINK tape

Author: Johan van der Knijff

Example command line:

sudo python3 ~/kb/xxLINK-resources/scripts/restore-sites.py /home/johan/kb/xxLINK/tapes-DDS/2/file000001 /home/johan/kb/xxLINK/siteData-DDS/2

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


def readApacheConfig(dirIn, dirOut):
    """
    Read Apache config file, extract interesting bits and return
    list with dictionary for each site
    """

    # Construct paths
    wwwIn = os.path.join(dirIn, "home/local/www")
    #wwwIn = os.path.join(dirIn, "local/www") # Only for tape 12!
    wwwOut = os.path.join(dirOut, "www")
    configFile = os.path.join(dirIn, "home/local/etc/httpd.conf")
    #configFile = os.path.join(dirIn, "local/etc/httpd.conf") # Only for tape 12!

    # Prefix / suffix used in Map entries (need to be stripped)
    mapPrefix="/htbin/htimage/home/local/www"
    mapSuffix="/*.map"
    execSuffix="/*"

    # List that holds individual site dictionaries
    sites = []

    with open(configFile) as configIn:
        for line in configIn:
            if line.startswith("MultiHost"):
                # TODO make sure that last entry of httpd.conf gets added to sites as well!
                # Reset record counters
                noMaps = 0
                noExecs = 0
                noWelcomes = 0

                # Append previous siteInfo dictionary to list
                try:
                    # Ignore test entries
                    if not siteInfo['serverName'].startswith("test"):
                        siteInfo['execPaths'] = execPaths
                        sites.append(siteInfo)
                except UnboundLocalError:
                    # siteInfo, execPathsIn and execPathsOut don't
                    # exist at start of first processed site
                    pass

                # Intialise empty siteInfo dictionary and execPath list
                siteInfo = {}
                execPaths = []

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

            if line.startswith("Exec"):
                # Only read 1st map entry for a site
                execPath = line.split()[2].strip()

                if execPath not in ["/home/local/www/cgi-bin/*",
                                    "/home/local/www//cgi-bin/*"]:
                    # Remove suffix
                    execPath = execPath.replace(execSuffix, "")
                    
                    # Construct source and destination paths
                    execPathIn = execPath.replace("/home/local/www", wwwIn)
                    execPathOut = execPath.replace("/home/local/www", wwwOut)

                    # Store execPathIn and execPathout pair as dictionary and
                    # add to list
                    execPaths.append({execPathIn:execPathOut})

            if line.startswith("Welcome") and noWelcomes == 0:
                indexPage = line.split()[1].strip()
                noWelcomes += 1
                siteInfo['indexPage'] = indexPage

    return sites


def writeConfig(site, configOut, hostsOut):
    """Write output Apache config records for site"""

    with open(configOut, "a", encoding="utf-8") as cOut:
        cOut.write("<VirtualHost *:80>\n")
        cOut.write("ServerName " + site["serverName"] + "\n")
        cOut.write("ServerAlias " + site["url"] + "\n")
        cOut.write("DocumentRoot " + site["pathOut"] + "\n")
        cOut.write('RedirectMatch ^/$ "/' + site["indexPage"] + '"\n')
        cOut.write("</VirtualHost>" + "\n\n")

    with open(hostsOut, "a", encoding="utf-8") as hOut:
        hOut.write("127.0.0.1 " + site["serverName"] + "\n")
        hOut.write("127.0.0.1 " + site["url"] + "\n")
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
    parser = argparse.ArgumentParser(description='Restore sites from xxLINK tape')
    args = parseCommandLine(parser)
    dirIn = os.path.abspath(args.dirIn)
    dirOut = os.path.abspath(args.dirOut)

    # Dir, files for output config
    dirOutEtc = os.path.join(dirOut, "etc")
    httpdConfOut = os.path.join(dirOutEtc, "sites.conf")
    hostsOut = os.path.join(dirOutEtc, "hosts")

    # Read info on sites from config file
    sites = readApacheConfig(dirIn, dirOut)

    # Create output etc directory
    if not os.path.exists(dirOutEtc):
        os.makedirs(dirOutEtc)

    # Remove output config files they already exist
    if os.path.isfile(httpdConfOut):
        os.remove(httpdConfOut)
    if os.path.isfile(hostsOut):
        os.remove(hostsOut)

    # For each site, write output config, hosts entries
    # and copy data over to destination
    for site in sites:
        writeConfig(site, httpdConfOut, hostsOut)
        # TODO: write entries for hosts file!
        copyFiles(site, dirIn, dirOut)

if __name__ == "__main__":
    main()
