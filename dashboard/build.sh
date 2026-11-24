#!/usr/bin/env bash
# Publica SOLO el dashboard, estado/publico y diario (nunca código, state.json ni secretos).
set -e
rm -rf public && mkdir -p public/estado
cp dashboard/index.html public/
cp -r estado/publico public/estado/
cp -r diario public/
