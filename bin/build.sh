#!/bin/sh
set -e
HERE=`dirname "$0"`
${HERE}/build-docs.sh
${HERE}/build-browser.sh