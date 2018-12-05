SOURCEDIR=`dirname "$0"`
TARGETDIR=${SOURCEDIR}/../../docs
# clean the target directory
rm -rf ${TARGETDIR}/*
npm --prefix ${SOURCEDIR} run build || { echo 'npm build failed' ; exit 1; }
sphinx-build -b dirhtml ${SOURCEDIR} ${TARGETDIR} || { echo 'sphinx-build failed' ; exit 1; }