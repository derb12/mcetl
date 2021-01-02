# -*- coding: utf-8 -*-
"""Creates a git log and parses the commits to build a changelog with different sections.

@author  : Donald Erb
Created on 2020-12-29 11:32:26

"""


from pathlib import Path
import subprocess
import sys
import traceback


def create_git_log(start_date=None, log_file='git_log.txt'):
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

    Returns
    -------
    success : bool
        True if the git command ran successfully, otherwise False.

    Notes
    -----
    Runs the following command with subprocess:
        git log development --format="%s%n%b"  --after={start_date} > {log_file}'
    where %s, %n, and %b in the format specify the commit title, new line, and commit
    body text. The command gets the git log from the development branch and includes
    any commits after the specified start date.

    """

    if log_file[0].startswith('"') or log_file[0].startswith("'"): # input was a string
        log_file = log_file[1:-1]

    if start_date is None or start_date.lower() == 'none':
        start_date = input('Input date to begin git log (eg. "2020-11-08", "11-8", or "8"): ')
    try:
        subprocess.run(
            f'git log development --format="%s%n%b"  --after={start_date} > {log_file}',
            capture_output=True, shell=True
        )
        success = True
    except:
        print('git log generation failed')
        print(traceback.format_exc())
        success = False

    return success


def parse_changes(log_file=None, delete_log=False):
    """
    Parses the output of git log and groups the commits.

    Outputs the grouped messages to 'new_changes.rst' in
    the same directory as the log file.

    Parameters
    ----------
    log_file : str or Path, optional
        The file path to the git log file.
    delete_log : bool, optional
        If True, will delete the log file when done if no
        errors are raised.

    """

    if log_file is None:
        log_file = input('Input git log file path: ')
    if log_file[0].startswith('"') or log_file[0].startswith("'"): # input was a string
        log_file = log_file[1:-1]

    if isinstance(delete_log, str):
        replacements = {'false': False, 'true': True}
        if delete_log.lower() in replacements:
            delete_log = replacements[delete_log.lower()]
        else:
            delete_log = False

    log_path = Path(log_file)
    with log_path.open() as fp:
        total_lines = fp.readlines()

    # should be commit message\n long message\n blank line\n
    # but could also be commit message\n blank line\n
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
            next_line = total_lines[i + 1]
        except:
            next_line = ''

        if next_line.strip():
            add_line = False
        else:
            add_line = True

        lines.extend([line.strip(), next_line.strip()])

    unfiled = []
    keys = {
        'FEAT': ([], 'New Features'),
        'FIX': ([], 'Bug Fixes'),
        'OTHER': ([], 'Other Changes'),
        'DOCS': ([], 'Documentation/Examples')
    }
    for line in range(0, len(lines), 2):
        try:
            signature, message = lines[line].split(':')
        except ValueError:
            signature = ''
        if signature.upper() in keys:
            keys[signature][0].append([message.strip(), lines[line + 1]])
        else:
            unfiled.append([lines[line], lines[line + 1]])

    changelog = Path(log_path.parent, 'new_changes.rst')
    with changelog.open('w') as fp:
        for commits, header in keys.values():
            if commits:
                fp.write(f'\n{header}\n{"~" * len(header)}\n\n')
                for line in commits:
                    fp.write(f'* {line[0]}\n  {line[1]}\n')
    print(f'Saved file with new git changes to {str(changelog)}.')

    if unfiled:
        print(f'Unfiled items:\n{unfiled}')

    if delete_log:
        log_path.unlink()

if __name__ == '__main__':

    # quick and dirty parser, but it doesn't need to be robust
    if not sys.argv: # not sure if this will ever be True, but just in case
        kwargs = {}
    else:
        keys = ['start_date', 'log_file', 'delete_log']
        kwargs = {}
        for param in sys.argv[1:]:
            if '=' in param:
                key, value = param.split('=')
                if key.startswith('-'):
                    first_index = 2 if param.startswith('--') else 1
                else:
                    first_index = 0
                key = key.strip()[first_index:].replace('-', '_')
                if key in keys:
                    kwargs[key] = value.strip()
            else:
                # fill in keys from left to right
                for key in keys:
                    if key not in kwargs:
                        kwargs[key] = param
                        break

    kwargs.setdefault('start_date', None)
    kwargs.setdefault('log_file', 'git_log.txt')
    log_created = create_git_log(kwargs['start_date'], kwargs['log_file'])
    if log_created:
        kwargs.setdefault('delete_log', True)
        parse_changes(kwargs['log_file'], kwargs['delete_log'])
