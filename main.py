#!/usr/bin/env python
import git
import os
import sys
import subprocess

def getCommandOutput(command):
  print command
  buildProcess = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
  buildCommandOutput = buildProcess.stdout.read()
  buildProcess.wait()
  return buildCommandOutput


def main():
  currentWorkingDirectory = os.getcwd()
  gitRepo = git.Repo(currentWorkingDirectory, search_parent_directories=True)
  gitRoot = gitRepo.git.rev_parse("--show-toplevel")

  argumentLength = len(sys.argv)
  if (argumentLength < 2):
    # printHelpInfo()
    return


  # gitRootPath = getGitRoot()

  commitHash = sys.argv[1].rstrip('\n')

  oldCommitName = getCommandOutput('git log -n 1 --pretty=format:%s ' + commitHash)
  oldHead=getCommandOutput('git rev-parse HEAD').rstrip('\n')
  getCommandOutput('git commit -m "' + oldCommitName + ' FIXUP"')
  cherryPickCommit = getCommandOutput('git rev-parse HEAD').rstrip('\n')
  getCommandOutput('git reset ' + commitHash + ' --hard')
  getCommandOutput('git cherry-pick ' + cherryPickCommit)
  resetHead = getCommandOutput('git rev-parse HEAD').rstrip('\n')
  getCommandOutput('git reset ' + oldHead + ' --hard')
  getCommandOutput('git rebase ' + resetHead)








  print gitRoot

if __name__ == '__main__':
  main()