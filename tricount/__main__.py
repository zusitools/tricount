#!/usr/bin/env python

# Small helper script to count the number of triangles in a .ls3 file.
# Usage: tricount.py filename
# Requires lxml, libxml2, and libxslt

import sys
import os.path
from lxml import etree
import zusicommon

class Ls3File:
    def __init__(self):
        # Full name of the file.
        self.filename = ""

        # Total number of triangles (including linked files)
        self.tricount = 0

        # Subset triangle count
        self.subset_counts = []

        # Subset names
        self.subset_names = []

        # Set of subset indices which are animated
        self.subset_animations = set()

        # List of linked files
        self.linked_files = []

        # Set of linked file indices which are animated
        self.linked_animations = set()

# absolute path => Ls3File object
ls3files = {}

# files whose count has already been printed
printed = set()

datapath = zusicommon.get_zusi_data_path()

# Parses a LS3 file and counts the triangles in it
def parseLs3(filePath):
    if filePath in ls3files:
        return
    ls3file = Ls3File()
    ls3file.filename = filePath
    ls3files[filePath] = ls3file

    # Parse the file
    try:
        fp = open(filePath, "rb")
        xml = etree.parse(fp)
    except IOError as e:
        print("Error opening file %s. Error message: %s" % (filePath, e.strerror))
        return

    # Get triangle count of subsets embedded in the file
    for subset in xml.xpath("//SubSet"):
        # MeshI contains the number of mesh indices, i.e. 3 * the number of triangles
        subset_count = len(subset.xpath("Face"))
        meshi = subset.get("MeshI")
        if meshi is not None:
            subset_count += int(meshi) / 3

        ls3file.subset_counts.append(subset_count)
        ls3file.tricount += subset_count
        ls3file.subset_names.append(subset.get("Name"))

    # Call the function recursively for all linked files that do not have the "NurInfo" attribute set
    for linkedFileNode in xml.xpath("//Verknuepfte/Datei[@Dateiname != '' and (not(@NurInfo) or @NurInfo != '1')]"):
        linkedFilePath = zusicommon.resolve_file_path(linkedFileNode.get("Dateiname"),
            os.path.dirname(filePath), datapath)

        # Only count .ls3 files
        if not linkedFilePath.lower().endswith(".ls3"):
            continue
        elif not os.path.exists(linkedFilePath):
            print("File not found: %s" % linkedFilePath)
        else:
            parseLs3(linkedFilePath)
            ls3file.linked_files.append(ls3files[linkedFilePath])
            ls3file.tricount += ls3files[linkedFilePath].tricount

    # Set animation indices
    for verknAnimationNode in xml.xpath("//VerknAnimation"):
        idx = verknAnimationNode.get("AniIndex")
        idx = 0 if idx is None else int(idx)
        ls3file.linked_animations.add(idx)
    for meshAnimationNode in xml.xpath("//MeshAnimation"):
        idx = meshAnimationNode.get("AniIndex")
        idx = 0 if idx is None else int(idx)
        ls3file.subset_animations.add(idx)

def printLs3(ls3file, indent = 0, is_ani = False):
    filename = ls3file.filename[len(datapath):] if ls3file.filename.startswith(datapath) else ls3file.filename
    print("| " * indent + "+ " + filename + ": " + str(ls3file.tricount)
        + (" (Ani)" if is_ani else ""))

    if ls3file in printed:
        return
    printed.add(ls3file)

    for index, subset_count in enumerate(ls3file.subset_counts):
        subset_name = ls3file.subset_names[index]
        print("| " * (indent+1) + "- %" + str(index)
            + (" (" + subset_name + ")" if subset_name is not None else "")
            + ": " + str(subset_count)
            + (" (Ani)" if index in ls3file.subset_animations else ""))
    for index, linked_file in enumerate(ls3file.linked_files):
        printLs3(linked_file, indent + 1, index in ls3file.linked_animations)

if __name__ == "__main__":
    filepath = os.path.realpath(sys.argv[1])
    parseLs3(filepath)

    if filepath in ls3files:
        printLs3(ls3files[filepath])
