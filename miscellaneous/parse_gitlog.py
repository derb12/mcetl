# -*- coding: utf-8 -*-
"""Creates a git log and parses the commits to build a changelog with different sections.

@author  : Donald Erb
Created on 2020-12-29 11:32:26

"""


import argparse
from pathlib import Path
import subprocess
import traceback


def create_git_log(start_date=None, log_file='git_log.txt', branch='development'):
    """
    Creates a log containing the messages of all commits after a given date.

    Parameters
    ----------
    start_date : str, optional
        The start date to begin counting commits. Can be in the following
        formats: "YYYY-MM-DD"", "MM-DD", or "DD", although month and days
        do not have to be double digits (eg. both "08" and "8" are acceptable).
        If year is not given, then git assumes the current year; likewise, if
        month is not given, the current month is assumed.
    log_file : str, optional
        The name of the file to output the git log to.
    branch : str, optional
        The git branch to log. Default is 'development'.

    Returns
    -------
    success : bool
        True if the git command ran successfully, otherwise False.

    Notes
    -----
    Runs the following command with subprocess:
        git log {branch} --format="%s%n%b"  --after={start_date} > {log_file}'
    where %s, %n, and %b in the format specify the commit title, new line, and commit
    body text. The command gets the git log from the main branch and includes
    any commits after the specified start date.

    """

    if log_file[0].startswith('"') or log_file[0].startswith("'"): # input was a nested string
        log_file = log_file[1:-1]

    if start_date is None or start_date.lower() == 'none':
        start_date = input('Input date to begin git log (eg. "2020-11-08", "11-8", or "8"): ')
    try:
        result = subprocess.run(
            f'git log {branch} --format="%s%n%b"  --after={start_date} > {log_file}',
            capture_output=True, shell=True
        )
        if result.stderr:
            raise subprocess.SubprocessError(result.stderr.decode())
        elif result.stdout:
            print('The git command gave output:', result.stdout.decode())
        success = True
    except:
        print('git log generation failed')
        print(traceback.format_exc())
        success = False

    return success


def parse_changes(log_file=None, keep_log=False):
    """
    Parses the output of git log and groups the commits.

    Outputs the grouped messages to 'new_changes.rst' in
    the same directory as the log file.

    Parameters
    ----------
    log_file : str or Path, optional
        The file path to the git log file.
    keep_log : bool, optional
        If False (default), will delete the log file when done if no
        errors are raised.

    """

    if log_file is None:
        log_file = input('Input git log file path: ')
    if log_file[0].startswith('"') or log_file[0].startswith("'"): # input was a nested string
        log_file = log_file[1:-1]

    if isinstance(keep_log, str):
        replacements = {'false': False, 'true': True}
        if keep_log.lower() in replacements:
            keep_log = replacements[keep_log.lower()]
        else:
            keep_log = False

    log_path = Path(log_file)
    with log_path.open() as fp:
        total_lines = fp.readlines()

    # should be commit message\n long message\n blank line\n
    # but could also be commit message\n blank line\n if there was no commit description
    # or commit message/n long message\n commit message\n long message\n blank line\n
    # for pull requests.
    # add_line becomes False once a header and the commit body are added, and remains
    # False until a blank line separating commits is encountered.
    add_line = True
    lines = []
    for i, line in enumerate(total_lines):
        if not line.strip(): # a blank line
            add_line = True
            continue
        elif not add_line:
            continue

        try:
            second_line = total_lines[i + 1]
        except IndexError:
            second_line = ''
            third_line = ''
            fourth_line = ''
        else:
            try:
                third_line = total_lines[i + 2]
            except IndexError:
                third_line = ''
                fourth_line = ''
            else:
                try:
                    fourth_line = total_lines[i + 3]
                except IndexError:
                    fourth_line = ''

        if second_line.strip():
            add_line = False
        else:
            add_line = True

        lines.extend([line.strip(), second_line.strip()])
        # there was no empty line separating the entries; happens for pull requests.
        if second_line.strip() and third_line.strip():
            lines.extend([third_line.strip(), fourth_line.strip()])

    unfiled = []
    keys = {
        ('FEAT', 'ENH'): ([], 'New Features'),
        ('FIX', 'BUG'): ([], 'Bug Fixes'),
        ('OTH'): ([], 'Other Changes'),
        ('DEP', 'BRK', 'BREAK'): ([], 'Deprecations/Breaking Changes'),
        ('DOC', 'EXA'): ([], 'Documentation/Examples'),
        ('MAINT'): ([], 'Maintenance') # MAINT will be removed, only for internal usage
    }
    for line in range(0, len(lines), 2):
        try:
            signature, message = lines[line].split(':')
        except ValueError:
            signature = ''

        for key in keys.keys():
            if signature.upper().startswith(key):
                keys[key][0].append([message.strip(), lines[line + 1]])
                break
        else: # no break
            unfiled.append([lines[line], lines[line + 1]])

    # remove the maintenance items, since they are not needed in the changelog
    keys.pop(('MAINT'))
    changelog = Path(log_path.parent, 'new_changes.rst')
    with changelog.open('w') as fp:
        for commits, header in keys.values():
            if commits:
                fp.write(f'\n{header}\n{"~" * len(header)}\n\n')
                for line in commits:
                    fp.write(f'* {line[0]}\n  {line[1]}\n')
        if unfiled:
            fp.write(
                f'\nUnfiled Items (Need to Fix!)\n{"~" * len("Unfiled Items (Need to Fix!)")}\n\n'
            )
            for line in unfiled:
                fp.write(f'* {line[0]}\n  {line[1]}\n')
    print(f'\nSaved file with new git changes to {str(changelog)}.')

    if unfiled:
        print('\nUnfiled items:')
        for line in unfiled:
            print(line)

    if not keep_log:
        log_path.unlink()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=('Creates a log of all commits to the specified git branch after '
                     'the specified start data, collects them into sections, and '
                     'formats a new entry for the changelog, output as new_changes.rst.')
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='If specified, will print out all input arguments.'
    )
    parser.add_argument(
        '--start-date', '-S', default=None,
        help=('The start date to begin counting commits. Can be in the following '
              'formats: "YYYY-MM-DD"", "MM-DD", or "DD", although month and days '
              'do not have to be double digits (eg. both "08" and "8" are acceptable).'
              ' If year is not given, then git assumes the current year; likewise, if '
              'month is not given, the current month is assumed.')
    )
    parser.add_argument(
        '--log-file', '-L', default='git_log.txt',
        help='The file to output the git log. Default is "git_log.txt".'
    )
    parser.add_argument(
        '--branch', '-B', default='development',
        help='The branch to use. Default is "development".'
    )
    parser.add_argument(
        '--keep-log', '-K', action='store_true',
        help='If specified, will keep the git log file after parsing it, rather than deleting it.'
    )

    args = parser.parse_args()
    if args.log_file.startswith('F='): # input was a copied file path
        if args.verbose:
            print(f'Corrected log file input from "{args.log_file}" to "{args.log_file[2:]}"')
        args.log_file = args.log_file[2:]

    if args.verbose:
        print(f'The input arguments were: {args}')

    if create_git_log(args.start_date, args.log_file, args.branch):
        parse_changes(args.log_file, args.keep_log)
