#!/usr/bin/env python

from __future__ import print_function
import git
import os
import sys
import re
import subprocess


def getCommandOutput(command):
    buildProcess = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    buildCommandOutput = buildProcess.stdout.read()
    buildProcess.wait()
    return buildCommandOutput


def getCommitsBetween(earlier, later):
    # excludes earlier commit, includes later commit
    unparsedCommitList = getCommandOutput(
        'git rev-list --ancestry-path ' + earlier + '..' + later)
    commitList = unparsedCommitList.rstrip('\n').split('\n')
    commitList.reverse()
    print(commitList)
    return commitList


def getDirectParent(commit):
    return getCommandOutput('git rev-parse ' + commit + '^').rstrip('\n')


def moveCommits(commitToFollow, startCommitToMove, endCommitToMove):
    commitsToMoveUp = getCommitsBetween(startCommitToMove, endCommitToMove)
    commitsToMoveDown = getCommitsBetween(commitToFollow, startCommitToMove)
    commitsToRemain = getCommitsBetween(endCommitToMove, 'HEAD')
    getCommandOutput('git reset ' + commitToFollow + ' --hard')
    orderedCommits = commitsToMoveUp + commitsToMoveDown + commitsToRemain
    for cherryPickCommit in orderedCommits:
        getCommandOutput('git cherry-pick ' + cherryPickCommit)
    # should check the diff here and then error out if it does not match


def squashCommit(startSquash, endSquash):
    oldHead = getCommandOutput('git rev-parse HEAD').rstrip('\n')
    getCommandOutput('git reset ' + endSquash + ' --hard')
    getCommandOutput('git reset --soft ' + startSquash)
    getCommandOutput('git commit --amend --no-edit')
    orderedCommits = getCommitsBetween(endSquash, oldHead)
    for cherryPickCommit in orderedCommits:
        getCommandOutput('git cherry-pick ' + cherryPickCommit)


def deleteCommit(commitToDelete):
    oldHead = getCommandOutput('git rev-parse HEAD').rstrip('\n')
    getCommandOutput('git reset ' + commitToDelete + '^ --hard')
    orderedCommits = getCommitsBetween(commitToDelete, oldHead)
    for cherryPickCommit in orderedCommits:
        getCommandOutput('git cherry-pick ' + cherryPickCommit)


green = '\x1b[0;32m'
magenta = '\x1b[0;35m'
reset = '\x1b[00m'
red = '\x1b[0;31m'


def isClean():
    status = getCommandOutput('git status --long')
    ss = re.sub(
        r'On branch ([^\n])+\nnothing to commit, working tree clean\n', 'abcd', status)
    return ss == 'abcd'


def getLog():
    commitSeparator = '~*~**~**~**~'
    detailSeparator = '~*~<>~<>~<>~'
    gitlog = getCommandOutput('git --no-pager log --reverse --pretty=format:"%h' + detailSeparator +
                              '%an' + detailSeparator + '%s' + detailSeparator + '%b' + commitSeparator + '" origin/master..HEAD')
    commits = gitlog.split(commitSeparator)
    commitCounter = len(commits) - 2
    for commit in commits:
        v = commit.split(detailSeparator)
        if len(v) < 3:
            continue
        ohash = magenta + v[0].lstrip('\n') + reset
        fullname = v[1]
        firstname = red + fullname.split(' ')[0].lstrip(' ') + reset
        title = v[2].rstrip('\n')
        fullmessage = v[3]
        matchObj = re.search(r'\nDifferential Revision: [^\n]+\n', fullmessage)
        diffUrlLine = ''
        headOffset = green + str(commitCounter) + reset
        if commitCounter <= 9:
            headOffset = ' ' + headOffset
        commitCounter -= 1
        if matchObj:
            diffUrlLine = magenta + \
                re.sub('\n', '', re.sub(r'\nDifferential Revision: ',
                                        '', matchObj.group(0))) + reset
        print(' '.join(
            filter(None, [headOffset + ' ', ohash, diffUrlLine, firstname, title])))


def main():

    argumentLength = len(sys.argv)
    if (argumentLength < 2):
        # https://docs.python.org/3/library/argparse.html
        getLog()
        return

    action = sys.argv[1].rstrip('\n')

    if action == '-m' and argumentLength > 3:
        rebaseCommit = sys.argv[2].rstrip('\n')
        lastCommit = sys.argv[3].rstrip('\n')
        firstCommit = getDirectParent(lastCommit)
        if argumentLength > 4:
            lastCommit = sys.argv[4].rstrip('\n')
        moveCommits(rebaseCommit, firstCommit, lastCommit)

    if action == '-d' and argumentLength == 3:
        commitToDelete = sys.argv[2].rstrip('\n')
        deleteCommit(commitToDelete)

    if action == '-s' and argumentLength == 3:
        commitToSquash = sys.argv[2].rstrip('\n')
        squashCommit(commitToSquash + '^', commitToSquash)
    if action == '-s' and argumentLength == 4:
        start = sys.argv[2].rstrip('\n')
        end = sys.argv[3].rstrip('\n')
        squashCommit(start, end)

    if action == '--isClean':
        if isClean():
            print('status is clean')
        else:
            print('status is not clean')

    # Features to add
    # rename an arbitrary commit to be an append of a different commit


if __name__ == '__main__':
    main()
