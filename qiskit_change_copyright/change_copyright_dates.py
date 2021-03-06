# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" Change copyright date """
import os
import datetime
import argparse
import subprocess
import traceback


class ChangeDate:
    """ Change copyright date """

    def __init__(self, root_dir):
        self._root_dir = root_dir

    @staticmethod
    def _exception_to_string(excp):
        stack = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)
        pretty = traceback.format_list(stack)
        return ''.join(pretty) + '\n  {} {}'.format(excp.__class__, excp)

    @staticmethod
    def _get_year_from_date(date):
        if not date or len(date) < 4:
            return None

        return int(date[:4])

    @staticmethod
    def _format_output(out, err):
        out = out.decode('utf-8').strip()
        err = err.decode('utf-8').strip()
        err = err if err else None
        year = ChangeDate._get_year_from_date(out)
        return year, err

    def _process_file_year(self, file_path, start, follow):
        file = file_path.replace(self._root_dir, '')
        if file.startswith('/'):
            file = file[1:]

        cmd = ['git', 'log']
        if follow:
            cmd.append('--follow')

        cmd.extend(['--format=%aI', '--', file])

        popen_git = subprocess.Popen(cmd,
                                     cwd=self._root_dir,
                                     stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        cmd = ['tail'] if start else ['head']
        cmd.append('-1')
        popen = subprocess.Popen(cmd,
                                 stdin=popen_git.stdout,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        out, err = popen.communicate()

        popen_git.wait()
        popen.wait()

        return ChangeDate._format_output(out, err)

    def _get_file_last_year(self, file_path):
        last_year = None
        errors = []
        try:
            last_year, err = self._process_file_year(file_path, False, True)
            if err:
                errors.append(err)
            elif last_year is None:
                last_year, err = self._process_file_year(file_path, False, False)
                if err:
                    errors.append(err)
        except Exception as ex:  # pylint: disable=broad-except
            errors.append("'{}' Last year: {}".format(file_path, str(ex)))

        if errors:
            raise ValueError(' - '.join(errors))

        return last_year

    def replace_copyright_date(self, file_path):
        """ replace copyright dates if modified for a file """
        now = datetime.datetime.now()
        date_replaced = False
        new_contents = ''
        has_header = False
        try:
            with open(file_path, 'rt', encoding="utf8") as file:
                for line in file:
                    if not line.startswith('# (C) Copyright IBM '):
                        new_contents += line
                        continue

                    has_header = True
                    curr_years = []
                    for word in line.strip().split():
                        for year in word.strip().split(','):
                            if year.startswith('20') and len(year) >= 4:
                                try:
                                    curr_years.append(int(year[0:4]))
                                except ValueError:
                                    pass

                    header_start_year = None
                    header_last_year = None
                    if len(curr_years) > 1:
                        header_start_year = curr_years[0]
                        header_last_year = curr_years[1]
                    elif len(curr_years) == 1:
                        header_start_year = header_last_year = curr_years[0]

                    last_year = self._get_file_last_year(file_path)
                    if last_year and header_last_year != last_year:
                        new_line = '# (C) Copyright IBM '
                        if header_start_year and header_start_year != last_year:
                            new_line += '{}, '.format(header_start_year)

                        new_line += '{}.\n'.format(now.year)
                        print(file_path, line[:-1], new_line[:-1])

                        date_replaced = True
                        new_contents += new_line

        except UnicodeDecodeError:
            return False, False

        if date_replaced and new_contents:
            with open(file_path, 'w') as file:
                file.write(new_contents)
                return True, has_header

        return False, has_header

    def change_dates(self, dir_path):
        """ change copyright dates if changed """
        files_changed = 0
        files_with_header = 0
        for item in os.listdir(dir_path):
            fullpath = os.path.join(dir_path, item)
            if os.path.isdir(fullpath):
                if not item.startswith('.git'):
                    files = self.change_dates(fullpath)
                    files_changed += files[0]
                    files_with_header += files[1]
                continue

            if os.path.isfile(fullpath):
                file_changed, file_has_header = self.replace_copyright_date(fullpath)
                if file_changed:
                    files_changed += 1
                if file_has_header:
                    files_with_header += 1

        return files_changed, files_with_header


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='Qiskit Change Copyright Date Tool')
    PARSER.add_argument('path',
                        metavar='path',
                        help='Root path of project to change in place.')

    ARGS = PARSER.parse_args()

    CHANGED, HAS_HEADER = ChangeDate(ARGS.path).change_dates(ARGS.path)
    print("{} of {} files with copyright header changed.".format(CHANGED, HAS_HEADER))
