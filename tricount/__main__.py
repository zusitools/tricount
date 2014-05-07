#!/usr/bin/env python

# Small helper script to count the number of triangles in a .ls3 file.
# Usage: tricount.py filename
# Requires lxml, libxml2, and libxslt

import sys
import os.path
from lxml import etree
import zusicommon

# absolute path => ([#triangles in subset 1, #triangles in subset 2], [linked file 1, linked file 2, ...])
ls3s = {}

# total number of triangles (including linked files) per file
tricounts = {}

# files whose count has already been printed
printed = set()

# Parses a LS3 file and counts the triangles in it
def parseLs3(filePath):
    if filePath in ls3s:
        return
    tricounts[filePath] = 0

    # The number of triangles in this file and all included files
    triSum = 0

    # Parse the file
    try:
        fp = open(filePath, "rb")
        xml = etree.parse(fp)
    except IOError as e:
        print("Error opening file %s. Error message: %s" % (filePath, e.strerror))
        return

    tricount = 0
    subset_counts = []
    included_files = []
    ls3s[filePath] = (subset_counts, included_files)

    # Get triangle count of subsets embedded in the file
    for subsetno, subset in enumerate(xml.xpath("//SubSet[@MeshI > 0]")):
        # MeshI contains the number of mesh indices, i.e. 3 * the number of triangles
        subset_count = int(subset.get("MeshI")) / 3
        subset_counts.append(subset_count)
        tricount += subset_count

    # Call the function recursively for all included files that do not have the "NurInfo" attribute set
    for includedFileNode in xml.xpath("//Verknuepfte/Datei[@Dateiname != '' and (not(@NurInfo) or @NurInfo != '1')]"):
        includedFilePath = zusicommon.resolve_file_path(includedFileNode.get("Dateiname"),
            os.path.dirname(filePath), zusicommon.get_zusi_data_path())

        # Only count .ls3 files
        if not includedFilePath.lower().endswith(".ls3"):
            continue
        elif not os.path.exists(includedFilePath):
            print("File not found: %s" % includedFilePath)
        else:
            included_files.append(includedFilePath)
            parseLs3(includedFilePath)
            tricount += tricounts[includedFilePath]

    tricounts[filePath] = tricount

def printLs3(filePath, indent = 0):
    print("| " * indent + "+ " + filePath + ": " + str(tricounts[filePath]))

    if filePath in printed:
        return
    printed.add(filePath)

    if filePath not in ls3s:
        return

    for index, subset_count in enumerate(ls3s[filePath][0]):
        print("| " * (indent+1) + "- %" + str(index) + ": " + str(subset_count))
    for linked_file in ls3s[filePath][1]:
        printLs3(linked_file, indent + 1)

if __name__ == "__main__":
    filepath = os.path.realpath(sys.argv[1])
    parseLs3(filepath)

    if filepath in ls3s:
        printLs3(filepath)