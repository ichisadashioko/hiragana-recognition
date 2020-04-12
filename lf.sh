#!/bin/bash
find . -type f \
    -not -path "./.git/*" \
    -not -path "./.ipynb_checkpoints/*" \
    -not -path "./__pycache__/*" \
    -not -path "./*.h5" \
    -not -path "./*.tfrecord" \
    -not -path "./*.log" \
    -not -path "./*.png" \
    -not -path "./fonts/*.ttf" \
    -not -path "./fonts/*.otf" \
    -print0 | xargs -0 dos2unix