#!/bin/bash
find . -type f \
    -not -path "./.git/*" \
    -not -path "./__pycache__/*" \
    -not -path "./*.h5" \
    -not -path "./*.tfrecord" \
    -not -path "./*.log" \
    -not -path "./fonts/*.ttf" \
    -not -path "./fonts/*.otf" \
    -print0 | xargs -0 dos2unix