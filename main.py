#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import git
import os
import sys
import re
import subprocess

def getCommandOutput(command):
  # print(command)
  buildProcess = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
  buildCommandOutput = buildProcess.stdout.read()
  buildProcess.wait()
  return buildCommandOutput

# add function that takes a function and executes the instructions in a new branch then either
# returns to original branch with a hard reset or does nothing if there is an error

# add a function to check if there are unstaged changes

# add a function to check if there are staged changes

# excludes earlier commit, includes later commit
def getCommitsBetween(earlier, later):
  unparsedCommitList = getCommandOutput('git rev-list --ancestry-path ' + earlier + '..' + later)
  commitList = unparsedCommitList.rstrip('\n').split('\n')
  commitList.reverse()
  print(commitList)
  return commitList

def getDirectParent(commit):
  return getCommandOutput('git rev-list ' + commit + ' --max-count=1 --skip=1').rstrip('\n')

def moveCommits(commitToFollow, startCommitToMove, endCommitToMove):
  oldHead=getCommandOutput('git rev-parse HEAD').rstrip('\n')
  commitsToMoveUp = getCommitsBetween(startCommitToMove, endCommitToMove)
  commitsToMoveDown = getCommitsBetween(commitToFollow, startCommitToMove)
  commitsToRemain = getCommitsBetween(endCommitToMove, 'HEAD')
  getCommandOutput('git reset ' + commitToFollow + ' --hard')
  orderedCommits = commitsToMoveUp + commitsToMoveDown + commitsToRemain
  for cherryPickCommit in orderedCommits:
    getCommandOutput('git cherry-pick ' + cherryPickCommit)
  # should check the diff here and then error out if it does not match

green = '\x1b[0;32m'
magenta = '\x1b[0;35m'
reset = '\x1b[00m'
red = '\x1b[0;31m'


def getLog():
  commitSeparator = '~*~**~**~**~'
  detailSeparator = '~*~<>~<>~<>~'
  gitlog = getCommandOutput('git --no-pager log --reverse --pretty=format:"%h' + detailSeparator + '%an' + detailSeparator + '%s' + detailSeparator + '%b' + commitSeparator + '" origin/master..HEAD')
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
      diffUrlLine = magenta + re.sub('\n', '', re.sub(r'\nDifferential Revision: ', '', matchObj.group(0))) + reset
    print(' '.join(filter(None, [headOffset + ' ', ohash, diffUrlLine, firstname, title])))


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



  # Features to add
  # move a commit to an arbitrary position
  # rename an arbitrary commit
  # rename an arbitrary commit to be an append of a different commit
  # squash a list of commits
  # print out a list of commits offset from master


  # gitRootPath = getGitRoot()


  # oldCommitName = getCommandOutput('git log -n 1 --pretty=format:%s ' + commitHash)
  # oldHead=getCommandOutput('git rev-parse HEAD').rstrip('\n')
  # getCommandOutput('git commit -m "' + oldCommitName + ' FIXUP"')
  # cherryPickCommit = getCommandOutput('git rev-parse HEAD').rstrip('\n')
  # getCommandOutput('git reset ' + commitHash + ' --hard')
  # getCommandOutput('git cherry-pick ' + cherryPickCommit)
  # resetHead = getCommandOutput('git rev-parse HEAD').rstrip('\n')
  # getCommandOutput('git reset ' + oldHead + ' --hard')
  # getCommandOutput('git rebase ' + resetHead)






if __name__ == '__main__':
  main()