#! /bin/bash

# function to find the path to this script
function get_dir_of_this_script () {
    # This function sets DIR to the directory in which this script itself is found.
    # Thank you https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself
    SCRIPT_SOURCE="${BASH_SOURCE[0]}"
    while [ -h "$SCRIPT_SOURCE" ]; do # resolve $SCRIPT_SOURCE until the file is no longer a symlink
	DIR="$( cd -P "$( dirname "$SCRIPT_SOURCE" )" >/dev/null 2>&1 && pwd )"
	SCRIPT_SOURCE="$(readlink "$SCRIPT_SOURCE")"
	# if $SCRIPT_SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
	[[ $SCRIPT_SOURCE != /* ]] && SCRIPT_SOURCE="$DIR/$SCRIPT_SOURCE" 
    done
    DIR="$( cd -P "$( dirname "$SCRIPT_SOURCE" )" >/dev/null 2>&1 && pwd )"
    }


sudo docker run -p 5000:5000 -v ${DIR}/../data/mydb.db:/data/mydb.db lordbayes:latest
