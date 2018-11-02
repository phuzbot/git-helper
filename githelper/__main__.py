from __future__ import print_function
import os
import sys
import re
import subprocess


def get_command_output(command):
    """Runs a command and returns the output."""
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    process_output = process.stdout.read()
    process.wait()
    return process_output


def get_head_hash():
    """Returns the hash of the current head."""
    return get_commit_hash('HEAD')


def get_commit_hash(commit):
    """Returns the ref of the commit.

    Used so that relative references do not become incorrect. """
    return get_command_output('git rev-parse ' + commit).rstrip('\n')


def get_commits_between(earlier, later):
    """Returns a list of commits between earlier exclusive and later inclusive."""
    raw_commit_list = get_command_output(
        'git rev-list --ancestry-path ' + earlier + '..' + later)
    commit_list = raw_commit_list.rstrip('\n').split('\n')
    commit_list.reverse()
    return commit_list


def get_direct_parent(commit):
    """Returns the direct parent of a given commit."""
    return get_commit_hash(commit + '^')


def cherry_pick_list(commits):
    """Cherry picks a list of commits onto the current head."""
    for commit in commits:
        get_command_output('git cherry-pick ' + commit)


def move_commits(root_commit, start_move_commit, end_move_commit):
    """Moves the lit of commits defined by start exclusive to end inclusive to directly after the root.

    Note that this action is also identical to swapping the two blocks of commits from root exclusive
    to start inclusive with start exclusive to end inclusive.
    eg. move_commits(g, d, a)
    h             h
    g             g
    f             c
    e             b
    d       ->    a
    c             f
    b             e
    a             d
    HEAD          HEAD
    """
    commits_to_move_up = get_commits_between(
        start_move_commit, end_move_commit)
    commits_to_move_down = get_commits_between(root_commit, start_move_commit)
    commits_to_remain = get_commits_between(end_move_commit, 'HEAD')
    get_command_output('git reset ' + root_commit + ' --hard')
    ordered_commits = commits_to_move_up + commits_to_move_down + commits_to_remain
    cherry_pick_list(ordered_commits)
    # should check the diff here and then error out if it does not match


def squash_commit(start_squash, end_squash):
    """Squashes all the commits between start and end inclusive into start preserving only the
    commit message of start."""
    prev_head = get_head_hash()
    start_squash_hash = get_commit_hash(start_squash)
    end_squash_hash = get_commit_hash(end_squash)
    get_command_output('git reset ' + end_squash_hash + ' --hard')
    get_command_output('git reset --soft ' + start_squash_hash)
    get_command_output('git commit --amend --no-edit')
    ordered_commits = get_commits_between(end_squash_hash, prev_head)
    cherry_pick_list(ordered_commits)


def delete_commit(commit_to_delete):
    """Deletes a commit."""
    commit_to_delete_hash = get_commit_hash(commit_to_delete)
    prev_head = get_head_hash()
    get_command_output('git reset ' + commit_to_delete_hash + '^ --hard')
    ordered_commits = get_commits_between(commit_to_delete_hash, prev_head)
    cherry_pick_list(ordered_commits)


reset_color = '\x1b[00m'


def green(text):
    """Makes text green in the console."""
    if text == '':
        return ''
    return '\x1b[0;32m' + text + reset_color


def magenta(text):
    """Makes text magenta in the console."""
    if text == '':
        return ''
    return '\x1b[0;35m' + text + reset_color


def red(text):
    """Makes text red in the console."""
    if text == '':
        return ''
    return '\x1b[0;31m' + text + reset_color


def _is_clean():
    status = get_command_output('git status --long')
    clean_status_pattern = re.compile(
        r'On branch ([^\n])+\nnothing to commit, working tree clean\n')
    return clean_status_pattern.match(status)


def print_log():
    """Prints a formatted log output."""
    commit_separator = '~*~**~**~**~'
    detail_separator = '~*~<>~<>~<>~'
    # https://git-scm.com/docs/pretty-formats
    abbreviated_commit_hash = '%h'
    author_name = '%an'
    subject = '%s'
    body = '%b'
    raw_log = get_command_output('git --no-pager log --reverse --pretty=format:"' + abbreviated_commit_hash + detail_separator +
                                 author_name + detail_separator + subject + detail_separator + body + commit_separator + '" origin/master..HEAD')
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


def main(args):

    argumentLength = len(args)
    if (argumentLength < 2):
        # https://docs.python.org/3/library/argparse.html
        print_log()
        return

    action = args[1].rstrip('\n')

    if action == '-m' and argumentLength > 3:
        rebaseCommit = args[2].rstrip('\n')
        lastCommit = args[3].rstrip('\n')
        firstCommit = get_direct_parent(lastCommit)
        if argumentLength > 4:
            lastCommit = args[4].rstrip('\n')
        move_commits(rebaseCommit, firstCommit, lastCommit)

    if action == '-d' and argumentLength == 3:
        commitToDelete = args[2].rstrip('\n')
        delete_commit(commitToDelete)

    if action == '-s' and argumentLength == 3:
        commitToSquash = args[2].rstrip('\n')
        squash_commit(commitToSquash + '^', commitToSquash)
    if action == '-s' and argumentLength == 4:
        start = args[2].rstrip('\n')
        end = args[3].rstrip('\n')
        squash_commit(start, end)

    if action == '--isClean':
        if _is_clean():
            print('status is clean')
        else:
            print('status is not clean')

    # Features to add
    # rename an arbitrary commit to be an append of a different commit


if __name__ == '__main__':
    main(sys.argv)
