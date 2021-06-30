#!/usr/bin/env bash

container install

apk add -U tzdata
cp /usr/share/zoneinfo/Europe/Prague /etc/localtime