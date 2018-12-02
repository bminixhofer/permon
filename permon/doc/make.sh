SOURCEDIR=`dirname "$0"`
TARGETDIR=${SOURCEDIR}/../../docs
# clean the target directory
rm -rf ${TARGETDIR}/*
sphinx-build -b dirhtml ${SOURCEDIR} ${TARGETDIR}