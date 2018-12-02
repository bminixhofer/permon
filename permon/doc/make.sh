SOURCEDIR=`dirname "$0"`
TARGETDIR=${SOURCEDIR}/../../docs
# clean the target directory
rm -rf ${TARGETDIR}/*
npm --prefix ${SOURCEDIR} run build
sphinx-build -b dirhtml ${SOURCEDIR} ${TARGETDIR}