#!/usr/bin/env python3
# encoding=utf-8
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()

    print(args)

    if not os.path.exists(args.infile):
        raise Exception(args.infile + ' does not exist!')

    original_bs = open(args.infile, mode='rb').read()
    content = original_bs.decode('utf-8')
    lines = content.splitlines()
    lines = list(filter(lambda x: len(x) > 0, lines))
    lines.sort()
    modified_content = '\n'.join(lines)
    modified_content = modified_content + '\n'
    modified_bs = modified_content.encode('utf-8')
    if modified_bs == original_bs:
        print('The content is already sorted.')
    else:
        print('The content needs to be sorted!')
        if args.run:
            open(args.infile, mode='wb').write(modified_bs)
            print('Done!')
