#!/bin/sh
set -e
BROWSER_FRONTEND_DIR=`dirname "$0"`/../permon/frontend/browser/
npm --prefix ${BROWSER_FRONTEND_DIR} run build