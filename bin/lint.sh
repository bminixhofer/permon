#!/bin/sh
# python is linted using flake8 - see setup.cfg for the configuration
# javascript is linted using eslint according to the airbnb config, there are no custom option set - see https://github.com/airbnb/javascript
set -e
PROJECT_ROOT=`dirname "$0"`/../
# lint python
flake8 ${PROJECT_ROOT}
# lint javascript in browser frontend
npm --prefix ${PROJECT_ROOT}/permon/frontend/browser/ run test
# lint javascript in docs
npm --prefix ${PROJECT_ROOT}/permon/doc/ run test