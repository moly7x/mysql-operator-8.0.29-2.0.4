#!/bin/bash
# Copyright (c) 2022, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
#

set -vx

if [ "$#" -ne 1 ]; then
	echo "usage: <filter>"
	exit 1
fi

FILTER=$1

docker volume prune -f

docker volume ls -q -f name=$FILTER | xargs -r -n 1 docker volume inspect -f '{{.Name}} {{json .CreatedAt}}' \
  | awk -v cut_off_date=\""$(date -d 'yesterday' -Ins)"\" '$2 <= cut_off_date {print $1}' \
  | xargs -r -n 1 docker volume rm
