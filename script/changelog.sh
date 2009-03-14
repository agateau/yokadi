#!/bin/sh
cd $(dirname $0)/..
git --no-pager log > ChangeLog
