#!/usr/bin/env python

from __future__ import print_function
import git
import os
import sys
import re
import subprocess


def get_command_output(command):
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    process_output = process.stdout.read()
    process.wait()
    return process_output


def get_commits_between(earlier, later):
    # excludes earlier commit, includes later commit
    raw_commit_list = get_command_output(
        'git rev-list --ancestry-path ' + earlier + '..' + later)
    commit_list = raw_commit_list.rstrip('\n').split('\n')
    commit_list.reverse()
    return commit_list


def get_direct_parent(commit):
    return get_command_output('git rev-parse ' + commit + '^').rstrip('\n')


def cherry_pick_list(commits):
    for commit in commits:
        get_command_output('git cherry-pick ' + commit)


def move_commits(root_commit, commits_to_move_down, end_move_commit):
    commits_to_move_up = get_commits_between(
        commits_to_move_down, end_move_commit)
    commitsToMoveDown = get_commits_between(root_commit, commits_to_move_down)
    commits_to_remain = get_commits_between(end_move_commit, 'HEAD')
    get_command_output('git reset ' + root_commit + ' --hard')
    ordered_commits = commits_to_move_up + commitsToMoveDown + commits_to_remain
    cherry_pick_list(ordered_commits)
    # should check the diff here and then error out if it does not match


def squash_commit(start_squash, end_squash):
    prev_head = get_command_output('git rev-parse HEAD').rstrip('\n')
    get_command_output('git reset ' + end_squash + ' --hard')
    get_command_output('git reset --soft ' + start_squash)
    get_command_output('git commit --amend --no-edit')
    ordered_commits = get_commits_between(end_squash, prev_head)
    cherry_pick_list(ordered_commits)


def delete_commit(commit_to_delete):
    prev_head = get_command_output('git rev-parse HEAD').rstrip('\n')
    get_command_output('git reset ' + commit_to_delete + '^ --hard')
    ordered_commits = get_commits_between(commit_to_delete, prev_head)
    cherry_pick_list(ordered_commits)


reset_color = '\x1b[00m'


def green(text):
    if text == '':
        return ''
    return '\x1b[0;32m' + text + reset_color


def magenta(text):
    if text == '':
        return ''
    return '\x1b[0;35m' + text + reset_color


def red(text):
    if text == '':
        return ''
    return '\x1b[0;31m' + text + reset_color


def is_clean():
    status = get_command_output('git status --long')
    clean_status_pattern = re.compile(
        r'On branch ([^\n])+\nnothing to commit, working tree clean\n')
    return clean_status_pattern.match(status)


def print_log():
    commit_separator = '~*~**~**~**~'
    detail_separator = '~*~<>~<>~<>~'
    raw_log = get_command_output('git --no-pager log --reverse --pretty=format:"%h' + detail_separator +
                                 '%an' + detail_separator + '%s' + detail_separator + '%b' + commit_separator + '" origin/master..HEAD')
    raw_commits = raw_log.split(commit_separator)
    commit_head_offset = len(raw_commits) - 2
    for commit in raw_commits:
        commit_details = commit.split(detail_separator)
        if len(commit_details) < 3:
            continue
        commit_hash = commit_details[0].lstrip('\n')
        full_name = commit_details[1]
        first_name = full_name.split(' ')[0].lstrip(' ')
        commit_title = commit_details[2].rstrip('\n')
        full_commit_message = commit_details[3]
        phab_line_match = re.search(
            r'\nDifferential Revision: [^\n]+\n', full_commit_message)
        phab_line_url = ''
        head_offset = green(str(commit_head_offset))
        if commit_head_offset <= 9:
            head_offset = ' ' + head_offset
        commit_head_offset -= 1
        if phab_line_match:
            phab_line_url = re.sub('\n', '', re.sub(
                r'\nDifferential Revision: ', '', phab_line_match.group(0)))
        print(' '.join(
            filter(None, [head_offset + ' ', magenta(commit_hash), magenta(phab_line_url), red(first_name), commit_title])))


def main():

    argumentLength = len(sys.argv)
    if (argumentLength < 2):
        # https://docs.python.org/3/library/argparse.html
        print_log()
        return

    action = sys.argv[1].rstrip('\n')

    if action == '-m' and argumentLength > 3:
        rebaseCommit = sys.argv[2].rstrip('\n')
        lastCommit = sys.argv[3].rstrip('\n')
        firstCommit = get_direct_parent(lastCommit)
        if argumentLength > 4:
            lastCommit = sys.argv[4].rstrip('\n')
        move_commits(rebaseCommit, firstCommit, lastCommit)

    if action == '-d' and argumentLength == 3:
        commitToDelete = sys.argv[2].rstrip('\n')
        delete_commit(commitToDelete)

    if action == '-s' and argumentLength == 3:
        commitToSquash = sys.argv[2].rstrip('\n')
        squash_commit(commitToSquash + '^', commitToSquash)
    if action == '-s' and argumentLength == 4:
        start = sys.argv[2].rstrip('\n')
        end = sys.argv[3].rstrip('\n')
        squash_commit(start, end)

    if action == '--isClean':
        if is_clean():
            print('status is clean')
        else:
            print('status is not clean')

    # Features to add
    # rename an arbitrary commit to be an append of a different commit


if __name__ == '__main__':
    main()
