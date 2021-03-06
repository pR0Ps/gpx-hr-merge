#!/usr/bin/env python3

import argparse
import contextlib
import csv
from datetime import datetime
import os
import xml.etree.ElementTree as ET


# Formats for parsing datetimes from GPX and CSV files (may be device-specific)
GPX_DATE_FMTS = ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ")
CSV_DATE_FMTS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ")


# XML Namespaces
ns = {
    "gpx": "http://www.topografix.com/GPX/1/1",
    "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
}


def parse_datetime(s, fmts):
    for fmt in fmts:
        with contextlib.suppress(ValueError):
            return datetime.strptime(s, fmt)
    raise ValueError("Timestamp '{}' not in a recognized format ({})", s, " / ".join(fmts))


def load_hr_data(hr_filename):
    """Load HR data from a file into a list of (time, hr) tuples

    Expects a CSV file with (date, hr) pairs
    Expects dates to be formated according to one of CSV_DATE_FMTS
    """
    # TODO: autodetect and support other common formats?
    data = []
    with open(hr_filename, "rt", newline="") as f:
        reader = csv.reader(f)

        # Get the iterator for the reader (yields each line one by one)
        rows = iter(reader)

        # First line is the headers - step the iterator forward to ignore them
        next(rows)

        # Process the data into a time -> hr mapping
        for row in rows:
            data.append((parse_datetime(row[0], CSV_DATE_FMTS), int(row[1])))
    return sorted(data)


def get_time(trkpt):
    """Get the time for the trackpoint

    Expects dates to be formatted according to one of GPX_DATE_FMTS
    """
    time = trkpt.find("gpx:time", ns).text
    return parse_datetime(time, GPX_DATE_FMTS)


def set_hr(trkpt, value):
    """Set the heart rate for the trackpoint

    Adds any required intermediary elements.
    """
    ext = trkpt.find("gpx:extensions", ns)
    if ext is None:
        ext = ET.SubElement(trkpt, "{{{gpx}}}extensions".format(**ns))
    tpe = ext.find("gpxtpx:TrackPointExtension", ns)
    if tpe is None:
        tpe = ET.SubElement(ext, "{{{gpxtpx}}}TrackPointExtension".format(**ns))
    hr = tpe.find("gpxtpx:hr", ns)
    if hr is None:
        hr = ET.SubElement(tpe, "{{{gpxtpx}}}hr".format(**ns))

    hr.text = str(value)


def binary_search_lerp(time, hr_data, max_interpolate=None):
    """Perform a binary search for the time in the HR data

    Use linear interpolation (within the max_interpolate param) to return a
    value if no exact results exist.
    """
    min_, max_, i = 0, len(hr_data) - 1, None
    while min_ <= max_:
        idx = (min_ + max_) // 2
        if hr_data[idx][0] == time:
            # exact match - return it
            return hr_data[idx][1]
        elif hr_data[idx][0] < time:
            min_ = idx + 1
        else:
            max_ = idx - 1

    # No exact match
    # Make sure index is always on the lower bound
    if hr_data[idx][0] > time:
        idx -= 1

    # Don't interpolate missing data
    if not (0 <= idx < len(hr_data) - 1):
        return None

    (time1, hr1), (time2, hr2) = hr_data[idx:idx+2]

    # Only interpolate if it's within range, otherwise return no data
    if max_interpolate is not None and min(time-time1, time2-time).total_seconds() > max_interpolate:
        return None

    return round(hr1 + (hr2-hr1) * ((time-time1) / (time2-time1)))


def merge(gpx_file, hr_file, interpolate):

    print("Merging heart rate date from {} into {}...".format(hr_file, gpx_file))
    # Read in the hr_data
    hr_data = load_hr_data(hr_file)

    if not os.path.exists(gpx_file):
        raise Exception("GPX file {} does not exist".format(gpx_file))

    # Move the original file to filename.orig
    orig_gpx = "{}.orig".format(gpx_file)
    if os.path.exists(orig_gpx):
        raise Exception("Backup of '{}' already exists".format(gpx_file))
    os.rename(gpx_file, orig_gpx)

    # Register namespaces to use when writing the document
    ET.register_namespace("", ns["gpx"])  # "" to use it as the default namespace
    ET.register_namespace("gpxtpx", ns["gpxtpx"])
    try:
        # Read in the document
        gpx = ET.parse(orig_gpx)

        # Iterate over all the trackpoints
        for trkpt in gpx.iterfind("./gpx:trk/gpx:trkseg/gpx:trkpt", ns):
            # Use the point data to look up the HR from the CSV
            # Will interpolate a value if no exact match is found
            point_time = get_time(trkpt)
            hr_at_time = binary_search_lerp(point_time, hr_data, max_interpolate=1 if not interpolate else None)
            if hr_at_time:
                set_hr(trkpt, hr_at_time)

        # Write the document out
        gpx.write(gpx_file, xml_declaration=True, encoding="UTF-8")
    except Exception:
        # Something went wrong, move the backup file back
        os.rename(orig_gpx, gpx_file)
        raise
    print("Merged!")


def main():
    parser = argparse.ArgumentParser(
        description="Merge HR data from a CSV into a GPX file"
    )
    parser.add_argument("--gpx", help="The GPX file to modify", required=True)
    parser.add_argument("--hr", help="The heart rate data file", required=True)
    parser.add_argument("--interpolate", help="Interpolate missing heart rate data?", action="store_true")
    args = parser.parse_args()

    merge(gpx_file=args.gpx, hr_file=args.hr, interpolate=args.interpolate)


if __name__ == "__main__":
    main()
