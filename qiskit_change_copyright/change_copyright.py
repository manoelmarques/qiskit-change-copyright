# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM Corp. 2017 and later.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
import argparse

_NEW_COPYRIGHT_TEXT = [
    '# This code is part of Qiskit.',
    '#',
    '# (C) Copyright IBM Corp. 2017 and later.',
    '#',
    '# This code is licensed under the Apache License, Version 2.0. You may',
    '# obtain a copy of this license in the LICENSE.txt file in the root directory',
    '# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.',
    '#',
    '# Any modifications or derivative works of this code must retain this',
    '# copyright notice, and modified files need to carry a notice indicating',
    '# that they have been altered from the originals.',
]


def _replace_copyright_text(file_path):
    copyright_replaced = False
    is_copyright = False
    new_contents = ''
    with open(file_path, 'rt', encoding="utf8") as f:
        for line in f:
            if line.startswith('#'):
                if 'copyright' in line.lower() and 'IBM' in line:
                    is_copyright = True
            else:
                if is_copyright:
                    new_contents += '\n'.join(_NEW_COPYRIGHT_TEXT) + '\n'
                    copyright_replaced = True
                    is_copyright = False

            if not is_copyright:
                new_contents += line

    # file finished without replacing copyright
    if is_copyright and not copyright_replaced:
        new_contents += '\n'.join(_NEW_COPYRIGHT_TEXT) + '\n'
        copyright_replaced = True
        is_copyright = False

    file_changed = False
    if copyright_replaced and len(new_contents) > 0:
        with open(file_path, 'w') as f:
            f.write(new_contents)
            print(file_path)
            file_changed = True

    return file_changed


def _change_copyright(dir_path):
    files_changed = 0
    for item in os.listdir(dir_path):
        fullpath = os.path.join(dir_path, item)
        if os.path.isdir(fullpath):
            files_changed += _change_copyright(fullpath)
            continue

        if os.path.isfile(fullpath):
            try:
                if _replace_copyright_text(fullpath):
                    files_changed += 1
            except UnicodeDecodeError:
                pass
            except Exception as e:
                print("{} error: {}".format(fullpath, str(e)))

    return files_changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Qiskit Change Copyright Tool')
    parser.add_argument('path',
                        metavar='path',
                        help='Root path of project to change in place.')

    args = parser.parse_args()

    files_changed = _change_copyright(args.path)
    print("{} files changed.".format(files_changed))
