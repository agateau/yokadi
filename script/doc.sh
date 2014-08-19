#!/bin/sh
cd ../"$(dirname "$0")"
epydoc --name="Yokadi" --html --graph=all -o doc yokadi/
