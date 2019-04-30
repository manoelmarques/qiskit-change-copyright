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
import subprocess
import traceback


class ChangeDate(object):

    def __init__(self, root_dir):
        self._root_dir = root_dir

    @staticmethod
    def exception_to_string(excp):
        stack = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)
        pretty = traceback.format_list(stack)
        return ''.join(pretty) + '\n  {} {}'.format(excp.__class__, excp)

    def get_file_year(self, file_path):
        try:
            file = file_path.replace(self._root_dir, '')
            if file.startswith('/'):
                file = file[1:]

            cmd1 = ['git',
                    'log',
                    '--follow',
                    '--format=%aI',
                    '--',
                    file]
            popen1 = subprocess.Popen(cmd1,
                                      cwd=self._root_dir,
                                      stdin=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
            cmd2 = ['tail',
                    '-1']
            popen2 = subprocess.Popen(cmd2,
                                      stdin=popen1.stdout,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

            cmd3 = ['head',
                    '-1']
            popen3 = subprocess.Popen(cmd3,
                                      stdin=popen1.stdout,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

            out, err = popen2.communicate()
            err_msg = err.decode('utf-8').strip()
            if len(err_msg) > 0:
                print("'{}' Error: '{}'".format(file_path, err_msg))
                return None

            start_date = out.decode('utf-8').strip()
            if len(start_date) == 0 or len(start_date) < 4:
                print(file)
                print("'{}' Error: 'No Start Date returned'".format(file_path))
                return None

            start_date = start_date[:4]

            out, err = popen3.communicate()
            err_msg = err.decode('utf-8').strip()
            if len(err_msg) > 0:
                print("'{}' Error: '{}'".format(file_path, err_msg))
                return None

            end_date = out.decode('utf-8').strip()
            if len(end_date) == 0 or len(end_date) < 4:
                end_date = None
            else:
                end_date = end_date[:4]

            if start_date == end_date:
                end_date = None

            popen1.wait()
            popen2.wait()
            popen3.wait()
            return (start_date, end_date)
        except Exception as e:
            print('Process has failed: {}'.format(ChangeDate.exception_to_string(e)))

        return None

    def _replace_copyright_date(self, file_path):
        date_replaced = False
        new_contents = ''
        with open(file_path, 'rt', encoding="utf8") as f:
            for line in f:
                if line.startswith('# (C) Copyright IBM Corp. '):
                    start_year, end_year = self.get_file_year(file_path)
                    if start_year is not None:
                        if end_year is not None:
                            new_line = "# (C) Copyright IBM {}, {}.\n".format(start_year, end_year)
                        else:
                            new_line = "# (C) Copyright IBM {}.\n".format(start_year)

                        date_replaced = True
                        new_contents += new_line
                else:
                    new_contents += line

        file_changed = False
        if date_replaced and len(new_contents) > 0:
            with open(file_path, 'w') as f:
                f.write(new_contents)
                print(file_path)
                file_changed = True

        return file_changed

    def change_date(self, dir_path):
        files_changed = 0
        for item in os.listdir(dir_path):
            fullpath = os.path.join(dir_path, item)
            if os.path.isdir(fullpath):
                if not item.startswith('.git'):
                    files_changed += self.change_date(fullpath)
                continue

            if os.path.isfile(fullpath):
                try:
                    if self._replace_copyright_date(fullpath):
                        files_changed += 1
                except UnicodeDecodeError:
                    pass
                except Exception as e:
                    print("{} error: {}".format(fullpath, str(e)))

        return files_changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Qiskit Change Copyright Date Tool')
    parser.add_argument('path',
                        metavar='path',
                        help='Root path of project to change in place.')

    args = parser.parse_args()

    change_date = ChangeDate(args.path)
    files_changed = change_date.change_date(args.path)
    print("{} files changed.".format(files_changed))
