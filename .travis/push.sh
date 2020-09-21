#!/bin/sh

echo Currently on branch `git branch`

bumpversion patch --no-tag --allow-dirty --no-commit --list > .temp
CURRENT_VERSION=`cat .temp | grep current_version | sed s,"^.*=",,`
NEW_VERSION=`cat .temp | grep new_version | sed s,"^.*=",,`

git add .bumpversion.cfg
git add custom_components.json
#git add midea.py
git add setup.py
git add msmart/*.py

git commit -m "Version Changed from ${CURRENT_VERSION} -> ${NEW_VERSION}"
git tag "v${NEW_VERSION}"
