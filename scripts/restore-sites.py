#! /usr/bin/env python3

"""
Restore sites from xxLINK tape

Author: Johan van der Knijff

Example command line:

sudo python3 ~/kb/xxLINK-resources/scripts/restore-sites.py /home/johan/kb/xxLINK/tapes-DDS/2/file000001/home/local/www /home/johan/kb/xxLINK/siteData-DDS/2/www /home/johan/kb/xxLINK/tapes-DDS/2/file000001/home/local/etc/httpd.conf /home/johan/kb/xxLINK/siteData-DDS/2/etc/sites.conf

NOTE: running as sudo is needed bc of permissions set in source data.

"""

import os
import sys
import csv
import argparse
import subprocess as sub
from shutil import which
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
    wwwOut = os.path.join(dirOut, "www")
    configFile = os.path.join(dirIn, "home/local/etc/httpd.conf")

    # Prefix / suffix used in Map entries (need to be stripped)
    mapPrefix="/htbin/htimage/home/local/www"
    mapSuffix="/*.map"
    execSuffix="/*"

    # List that holds individual site dictionaries
    sites = []

    with open(configFile) as configIn:
        for line in configIn:
            if line.startswith("MultiHost"):
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

                    #print(execPathIn, execPathOut)

                    # Store execPathIn and execPathout pair as dictionary and
                    # add to list
                    execPaths.append({execPathIn:execPathOut})

            if line.startswith("Welcome") and noWelcomes == 0:
                indexPage = line.split()[1].strip()
                noWelcomes += 1
                siteInfo['indexPage'] = indexPage

    return sites


def writeConfig(site, configOut):
    """Write output Apache config records for site"""

    with open(configOut, "a", encoding="utf-8") as fOut:
        fOut.write("<VirtualHost *:80>\n")
        fOut.write("ServerName " + site["serverName"] + "\n")
        fOut.write("ServerAlias " + site["url"] + "\n")
        fOut.write("DocumentRoot " + site["pathOut"] + "\n")
        fOut.write('RedirectMatch ^/$ "/' + site["indexPage"] + '"\n')
        fOut.write("</VirtualHost>" + "\n\n")


def fixSymLinks(folder, dirIn, dirOut):
    for root, _, files in os.walk(folder):
        for f in files:
            thisFile = os.path.join(root, f)
            try:
                os.stat(thisFile)
            except OSError or FileNotFoundError:
                # Read link target
                linkTarget = os.readlink(thisFile)
                print(thisFile, linkTarget, file=sys.stderr)
                
                # Leave relative links unchanged, update absolute links to input 
                # and output paths
                # /home/local/NFIC/docs --> 
                if os.path.isabs(linkTarget):
                    linkTargetIn = os.path.join(dirIn, linkTarget[1:])
                    linkTargetOut = os.path.join(dirOut, linkTarget.replace("/home/", ""))
                    print(linkTargetIn, linkTargetOut, file=sys.stderr)
                else:
                    linkTargetIn = os.path.join(root, linkTarget)

                if os.path.isdir(linkTargetIn):
                    # Copy directory to outDir
                    try:
                        # Note copy_tree by default aborts on broken symlinks, hence preserve_symlinks=1
                        # However this means that these broken  
                        copy_tree(linkTargetIn, linkTargetOut, verbose=1, update=1, preserve_symlinks=1)
                    except:
                        print("ERROR copying " + linkTargetIn, file=sys.stderr)
                        raise
                    
                #print('file %s does not exist or is a broken symlink' % thisFile, file=sys.stderr)

def copyFiles(site, dirIn, dirOut):
    """Copy site's folder structure and apply correct permissions:
    - Dirs to 755
    - Files in source dir to 644
    - Files in exec (cgi-bin) dirs to 755
    """
    sourceDir = os.path.abspath(site["pathIn"])
    destDir = os.path.abspath(site["pathOut"])
    execDirs = site["execPaths"]

    print("======PROCESSING SOURCE DIR " + sourceDir)

    # Source dir tree
    if os.path.exists(sourceDir):

        try:
            # Note copy_tree by default aborts on broken symlinks, hence preserve_symlinks=1
            # However this means that these broken  
            copy_tree(sourceDir, destDir, verbose=1, update=1, preserve_symlinks=1)
        except:
            print("ERROR copying " + sourceDir, file=sys.stderr)
            raise

        # Search destination dir for broken symbolic links, fix them and copy
        # underlying data
        fixSymLinks(destDir, dirIn, dirOut)

        # Update permissions
        for root, dirs, files in os.walk(destDir): 
            for d in dirs:
                try:
                    os.chmod(os.path.join(root, d), 0o755)
                except OSError:
                    print("ERROR updating permissions for directory " + os.path.abspath(d), file=sys.stderr)

            for f in files:
                try:
                    os.chmod(os.path.join(root, f), 0o644)
                except OSError:
                    print("ERROR updating permissions for file " + os.path.abspath(f), file=sys.stderr)
    else:
        print("WARNING: directory " + sourceDir + " does not exist", file=sys.stderr)

    print("======PROCESSING EXEC DIRS====")

    # Executable (cgi-bin) dirs (can be multiple or none at all)
    for d in execDirs:
        for i, o in d.items():
            execSourceDir = os.path.abspath(i)
            execDestDir = os.path.abspath(o)

            if os.path.exists(execSourceDir):
                """
                try:
                    copy_tree(execSourceDir, execDestDir, verbose=1, update=1, preserve_symlinks=1)
                except:
                    print("ERROR copying " + execSourceDir, file=sys.stderr)
                    raise
                """

                # Update permissions
                for root, dirs, files in os.walk(execDestDir):  
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), 0o755)
                        except OSError:
                            print("ERROR updating permissions for file " + os.path.abspath(f), file=sys.stderr)
            else:
                print("WARNING: directory " + execSourceDir + " does not exist", file=sys.stderr)


def main():
    """Main function"""

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Restore sites from xxLINK tape')
    args = parseCommandLine(parser)
    dirIn = os.path.abspath(args.dirIn)
    dirOut = os.path.abspath(args.dirOut)

    httpdConfOut = os.path.join(dirOut, "etc/sites.conf")

    #print(dirIn, dirOut, wwwIn, wwwOut, httpdConfIn, httpdConfOut)

    # Read info on sites from config file
    sites = readApacheConfig(dirIn, dirOut)

    # Create directory for output config
    dirConfOut = os.path.dirname(httpdConfOut)
    if not os.path.exists(dirConfOut):
        os.makedirs(dirConfOut)

    # Remove output config file if it already exists
    if os.path.isfile(httpdConfOut):
        os.remove(httpdConfOut)

    # For each site, write output config, hosts entries
    # and copy data over to destination
    for site in sites:
        writeConfig(site, httpdConfOut)
        # TODO: write entries for hosts file!
        copyFiles(site, dirIn, dirOut)

if __name__ == "__main__":
    main()
