gpx-hr-merge
============

Merge heart rate data from a Fitbit into a GPX file.

The Fitbit data must be in CSV format like so (header name doesn't matter):
```csv
Datetime,Heart rate
2018-04-15 00:00:10,82
2018-04-15 00:00:20,81
2018-04-15 00:00:35,81
```

Any standard GPX file should work although it has only been tested with the files that
[Strava](https://www.strava.com/) generates when exporting an activity.

Times must match to the second in order for the heart rate data to be added to the GPX point.

A backup of the GPX file is taken (with a `.orig` suffix) before modifying it. After the script runs
it's a good idea to take a `diif` of the two to make sure everything worked properly.

License
=======
Licensed under the [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
