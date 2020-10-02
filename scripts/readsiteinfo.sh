#!/bin/bash
#
# Generate CSV of url and root dir pairs from httpd.conf config file
#
confFile="/home/johan/ownCloud/xxLINK/httpd-cleaned.conf"

#foundurl=false
#founddirectory=false
prefix="/htbin/htimage"
suffix="\/*.map"
wwwSource="/home/local/www"
wwwDest="/var/www"

#echo "domain","serverName","rootDir","indexPage"

while IFS= read -r line
    do

    if [[ $line == "ServerRoot"* ]]; then
        serverrroot="$(awk -F '[[:blank:]]+' '{print $2}' <<< $line )"
        #echo $serverrroot
    fi

    if [[ $line == "MultiHost"* ]]; then
        # Indicates start of new site definition
        foundurl=true
        url="$(awk -F '[[:blank:]]+' '{print $2}' <<< $line )"
        serverName=${url#"www."}
        #echo $url
    fi

    if [[ $line == "Map"* ]]; then
        mapPath="$(awk -F '[[:blank:]]+' '{print $3}' <<< $line )"
        if [[ $mapPath != "/noproxy.htm" ]]; then
            directory=$mapPath
            # Remove prefix, suffix
            directory=${mapPath#$prefix}
            directory=${directory%$suffix}
            # Replace source www directory with destination directory
            directoryDest="${directory/$wwwSource/$wwwDest}"

            #founddirectory=true
            #foundurl=false
            #founddirectory=false
            #echo $directory
        fi
    fi

    if [[ $line == "Welcome"* ]]; then
        indexPage="$(awk -F '[[:blank:]]+' '{print $2}' <<< $line )"
        #echo $url,$serverName,$directoryDest,$indexPage
        # Output Apache Virtual Host config items 
        echo "<VirtualHost *:80>"
        echo "ServerName" $serverName
        echo "ServerAlias" $url
        echo "DocumentRoot" $directoryDest
        echo "RedirectMatch ^/$" '"/'$indexPage'"'
        echo "</VirtualHost>"
        echo
    fi

done < "$confFile"

