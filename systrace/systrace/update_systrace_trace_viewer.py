#!/usr/bin/env python

# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function   # pylint: disable=wrong-import-position

import codecs
import optparse
import os
import re
import subprocess
import sys

_CATAPULT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(os.path.join(_CATAPULT_PATH, 'tracing'))

# this import needs to be after the change to sys.path above
#pylint: disable=wrong-import-position
from tracing_build import vulcanize_trace_viewer


SYSTRACE_TRACE_VIEWER_HTML_FILE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'systrace_trace_viewer.html')
CATAPULT_REV_ = 'CATAPULT_REV'
NO_AUTO_UPDATE_ = 'NO_AUTO_UPDATE'
UNKNOWN_REVISION_ = 'UNKNOWN'


def create_catapult_rev_str_(revision):
  return '<!--' + CATAPULT_REV_ + '=' + str(revision) + '-->'


def get_catapult_rev_in_file_(html_file):
  assert os.path.exists(html_file)
  rev = ''
  with open(html_file, 'r') as f:
    lines = f.readlines()
    for line in lines[::-1]:
      if CATAPULT_REV_ in line:
        tokens = line.split(CATAPULT_REV_)
        rev = re.sub(r'[=\->]', '', tokens[1]).strip()
        break
  return rev


def get_catapult_rev_in_git_():
  try:
    catapult_rev = subprocess.check_output(
        'git rev-parse HEAD',
        shell=True, # Needed by Windows
        cwd=os.path.dirname(os.path.abspath(__file__))).strip()
  except (subprocess.CalledProcessError, OSError):
    return None
  if not catapult_rev:
    return None
  return catapult_rev


def update(no_auto_update=False, no_min=False, force_update=False):
  """Update the systrace trace viewer html file.

  When the html file exists, do not update the file if
  1. the revision is NO_AUTO_UPDATE_;
  2. or the revision is not changed.

  Args:
    no_auto_update: If true, force updating the file with revision
                    NO_AUTO_UPDATE_. Future auto-updates will be skipped.
    no_min:         If true, skip minification when updating the file.
    force_update:   If true, update the systrace trace viewer file no matter
                    what.
  """
  if no_auto_update:
    new_rev = NO_AUTO_UPDATE_
  else:
    new_rev = get_catapult_rev_in_git_()
    if not new_rev:
      # Source tree could be missing git metadata.
      print('Warning: Couldn\'t determine current git revision.',
            file=sys.stderr)
      new_rev = UNKNOWN_REVISION_

  need_update = False
  if force_update:
    need_update = True
  elif no_auto_update:
    need_update = True
  elif not os.path.exists(SYSTRACE_TRACE_VIEWER_HTML_FILE):
    need_update = True
  else:
    old_rev = get_catapult_rev_in_file_(SYSTRACE_TRACE_VIEWER_HTML_FILE)
    if not old_rev or old_rev == UNKNOWN_REVISION_:
      need_update = True
    # If old_rev was set to NO_AUTO_UPDATE_ it should be skipped, since forced
    # update cases have been already handled above.
    if old_rev != new_rev and old_rev != NO_AUTO_UPDATE_:
      need_update = True

  if not need_update:
    print('Update skipped.')
    return

  print('Generating viewer file %s with revision %s.' % (
            SYSTRACE_TRACE_VIEWER_HTML_FILE, new_rev))

  # Generate the vulcanized result.
  with codecs.open(SYSTRACE_TRACE_VIEWER_HTML_FILE,
                   encoding='utf-8', mode='w') as f:
    vulcanize_trace_viewer.WriteTraceViewer(
        f,
        config_name='full',
        minify=(not no_min),
        output_html_head_and_body=False)
    if not force_update:
      f.write(create_catapult_rev_str_(new_rev))

def main():
  parser = optparse.OptionParser()
  parser.add_option('--force-update', dest='force_update',
                    default=False, action='store_true', help='force update the '
                    'systrace trace viewer html file')
  parser.add_option('--no-auto-update', dest='no_auto_update',
                    default=False, action='store_true', help='force update the '
                    'systrace trace viewer html file and disable auto-updates, '
                    'delete \'systrace_trace_viewer.html\' to re-enable '
                    'auto-updates')
  parser.add_option('--no-min', dest='no_min', default=False,
                    action='store_true', help='skip minification')
  # pylint: disable=unused-variable
  options, unused_args = parser.parse_args(sys.argv[1:])

  update(no_auto_update=options.no_auto_update,
         no_min=options.no_min,
         force_update=options.force_update)

if __name__ == '__main__':
  main()
