#!/usr/bin/env python
import argparse
import collections
import math
import re
import xml.etree.ElementTree as ET

# pip python-dateutil
from dateutil.parser import parse

def main():
  p = argparse.ArgumentParser(description='Python utility to help runners log distance and time info stored in .tcx files.')
  # p.add_argument('-v', help='Verbose output.')
  # p.add_argument('-p', help='Output pattern per file.') # TODO: custom patterns
  p.add_argument('files', nargs='*')
  args = p.parse_args()

  for file in args.files:
    parsefile(file)


def parsefile(file):
  # print 'Parsing {}...'.format(file) # TODO: output vs debug messages, etc.

  tcx = ET.parse(file).getroot()
  ns = {'tcx': re.match('\{(.*)\}', tcx.tag).group(1)}

  # Start time
  # FIXME: some files don't have a starttime (no data), these should be skipped
  start = parse(tcx.find('./tcx:Activities/tcx:Activity/tcx:Lap', ns).attrib['StartTime'])

  # For tracking idles
  lasttime = start
  idletime = start - lasttime

  # Metadata about the run
  run = dict() # TODO: initialize more gracefully
  run['dist'] = 0 # initial distance
  run['min'] = 0 # initial minutes
  run['sec'] = 0 # seconds
  run['extdist'] = 0 # extended distance
  run['extmin'] = 0 # extended minutes
  run['extsec'] = 0 # seconds
  run['start'] = start.strftime('%Y-%m-%d') # start time

  # Distance checkpoints to track, in miles (use 999 for the end)
  # TODO: interpolate these more sanely; perhaps non-integer miles can be passed in as an argument
  run['dists'] = collections.deque([3.1, 6.2, 999])

  # Extended distance checkpoints to track, in miles
  run['extdists'] = collections.deque([3.1, 4, 5, 6, 6.2, 7, 8, 9, 10, 11, 12, 13, 13.1, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 26.2, 27, 999])

  run['inout'] = 'O' # Assume all these runs are outdoors

  # TODO: push me out into a function or something
  if start.hour <= 11:
    run['timeofday'] = 'AM'
  elif start.hour >= 14:
    run['timeofday'] = 'PM'
  else:
    run['timeofday'] = 'Noon'

  for tp in tcx.findall('./tcx:Activities/tcx:Activity/tcx:Lap/tcx:Track/tcx:Trackpoint', ns):
    t = parse(tp.find('tcx:Time', ns).text)
    d = float(tp.find('tcx:DistanceMeters', ns).text)

    if d == 0:
      # We're idling at the moment
      idletime += t - lasttime

    else:
      # We're making progress, so check to see if we've hit any distance marks
      runsec = int((t - start - idletime).total_seconds())
      checkmark(d / 1000, runsec, run, '')
      checkmark(d / 1000, runsec, run, 'ext')

    lasttime = t

  print '{start}\t{dist}\t{min}\t{sec}\t{extdist}\t{extmin}\t{extsec}\t{timeofday}\t{file}'.format(start=run['start'], dist=run['dist'], min=run['min'], sec=run['sec'], extdist=run['extdist'], extmin=run['extmin'], extsec=run['extsec'], timeofday=run['timeofday'], file=file)
  # TODO: skip if not even the first checkpoint is reached?

def checkmark(dist, runsec, run, col):

    # Check against dist/extdist marks
    if dist * 0.621371 >= run[col+'dists'][0]:
      # We hit the next distance mark
      # TODO: interpolation if we're not exact?
      m = int(math.floor(runsec / 60))
      s = runsec % 60
      run[col+'min'] = m
      run[col+'sec'] = s
      run[col+'dist'] = run[col+'dists'].popleft()


if __name__ == '__main__':
  main()
