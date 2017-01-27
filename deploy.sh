#!/bin/bash

set -ex

tag=$(echo "$2" | sed -e 's/\//-/')
docker tag "$1" "$1:$tag"
docker push "$1:$tag"
docker push "$1:latest"
