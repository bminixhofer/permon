#!/bin/sh
set -e
PROJECT_ROOT=`dirname "$0"`/../
npm --prefix ${PROJECT_ROOT}/permon/doc/ install
npm --prefix ${PROJECT_ROOT}/permon/frontend/browser/ install
git config core.hooksPath .githooks