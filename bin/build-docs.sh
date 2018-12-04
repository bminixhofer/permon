#!/bin/sh
set -e
PROJECT_ROOT=`dirname "$0"`/../
SOURCEDIR=${PROJECT_ROOT}/permon/doc/
TARGETDIR=${PROJECT_ROOT}/docs/
# clean the target directory
rm -rf ${TARGETDIR}/*
npm --prefix ${SOURCEDIR} run build
sphinx-build -b dirhtml ${SOURCEDIR} ${TARGETDIR}