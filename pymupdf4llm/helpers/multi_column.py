"""
This is an advanced PyMuPDF utility for detecting multi-column pages.
It can be used in a shell script, or its main function can be imported and
invoked as descript below.

Features
---------
- Identify text belonging to (a variable number of) columns on the page.
- Text with different background color is handled separately, allowing for
  easier treatment of side remarks, comment boxes, etc.
- Uses text block detection capability to identify text blocks and
  uses the block bboxes as primary structuring principle.
- Supports ignoring footers via a footer margin parameter.
- Returns re-created text boundary boxes (integer coordinates), sorted ascending
  by the top, then by the left coordinates.

Restrictions
-------------
- Only supporting horizontal, left-to-right text
- Returns a list of text boundary boxes - not the text itself. The caller is
  expected to extract text from within the returned boxes.
- Text written above images is ignored altogether (option).
- This utility works as expected in most cases. The following situation cannot
  be handled correctly:
    * overlapping (non-disjoint) text blocks
    * image captions are not recognized and are handled like normal text

Usage
------
- As a CLI shell command use

  python multi_column.py input.pdf footer_margin header_margin

  Where margins are the height of the bottom / top stripes to ignore on each
  page.
  This code is intended to be modified according to your need.

- Use in a Python script as follows:

  ----------------------------------------------------------------------------------
  from multi_column import column_boxes

  # for each page execute
  bboxes = column_boxes(page, footer_margin=50, no_image_text=True)

  bboxes is a list of fitz.IRect objects, that are sorted ascending by their
  y0, then x0 coordinates. Their text content can be extracted by all PyMuPDF
  get_text() variants, like for instance the following:
  for rect in bboxes:
      print(page.get_text(clip=rect, sort=True))
  ----------------------------------------------------------------------------------

Dependencies
-------------
PyMuPDF v1.24.2 or later

Copyright and License
----------------------
Copyright 2024 Artifex Software, Inc.
License GNU Affero GPL 3.0
"""

import string

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def column_boxes(
    page,
    *,
    footer_margin=50,
    header_margin=50,
    no_image_text=True,
    textpage=None,
    paths=None,
    avoid=None,
):
    """Determine bboxes which wrap a column on the page.

    Args:
        footer_margin: ignore text if distance from bottom is less
        header_margin: ignore text if distance from top is less
        no_image_text: ignore text inside image bboxes
        textpage: use this textpage instead of creating one
        paths: use these drawings instead of extracting here
        avoid: ignore text in any of these areas
    """
    WHITE = set(string.whitespace)

    def is_white(text):
        """Check for relevant text."""
        return WHITE.issuperset(text)

    # compute relevant page area
    clip = +page.rect
    clip.y1 -= footer_margin  # Remove footer area
    clip.y0 += header_margin  # Remove header area

    if paths is None:
        paths = page.get_drawings()

    if textpage is None:
        textpage = page.get_textpage(clip=clip, flags=fitz.TEXTFLAGS_TEXT)

    bboxes = []

    # path rectangles
    path_rects = []

    # image bboxes
    img_bboxes = []
    if avoid is not None:
        img_bboxes.extend(avoid)

    # bboxes of non-horizontal text
    # avoid when expanding horizontal text boxes
    vert_bboxes = []

    def in_bbox(bb, bboxes):
        """Return 1-based number if a bbox contains bb, else return 0."""
        for i, bbox in enumerate(bboxes):
            if bb in bbox:
                return i + 1
        return 0

    def intersects_bboxes(bb, bboxes):
        """Return True if a bbox touches bb, else return False."""
        for bbox in bboxes:
            if not (bb & bbox).is_valid:
                return True
        return False

    def can_extend(temp, bb, bboxlist, vert_bboxes):
        """Determines whether rectangle 'temp' can be extended by 'bb'
        without intersecting any of the rectangles contained in 'bboxlist'.

        Items of bboxlist may be None if they have been removed.

        Returns:
            True if 'temp' has no intersections with items of 'bboxlist'.
        """
        for b in bboxlist:
            if not intersects_bboxes(temp, vert_bboxes) and (
                b is None or b == bb or (temp & b).is_empty
            ):
                continue
            return False

        return True

    # def extend_right(bboxes, width, path_bboxes, vert_bboxes, img_bboxes):
    #     """Extend a bbox to the right page border.

    #     Whenever there is no text to the right of a bbox, enlarge it up
    #     to the right page border.

    #     Args:
    #         bboxes: (list[IRect]) bboxes to check
    #         width: (int) page width
    #         path_bboxes: (list[IRect]) bboxes with a background color
    #         vert_bboxes: (list[IRect]) bboxes with vertical text
    #         img_bboxes: (list[IRect]) bboxes of images
    #     Returns:
    #         Potentially modified bboxes.
    #     """
    #     for i, bb in enumerate(bboxes):
    #         # do not extend text with background color
    #         if in_bbox(bb, path_bboxes):
    #             continue

    #         # do not extend text in images
    #         if in_bbox(bb, img_bboxes):
    #             continue

    #         # temp extends bb to the right page border
    #         temp = +bb
    #         temp.x1 = width

    #         # do not cut through colored background or images
    #         if intersects_bboxes(temp, path_bboxes + vert_bboxes + img_bboxes):
    #             continue

    #         # also, do not intersect other text bboxes
    #         check = can_extend(temp, bb, bboxes, vert_bboxes)
    #         if check:
    #             bboxes[i] = temp  # replace with enlarged bbox

    #     return [b for b in bboxes if b != None]

    def join_rects_phase1(bboxes):
        """Postprocess identified text blocks, phase 1.

        Joins any rectangles that "touch" each other. This means that
        their intersection is valid (but may be empty).
        """
        prects = bboxes[:]
        new_rects = []
        while prects:
            prect0 = prects[0]
            repeat = True
            while repeat:
                repeat = False
                for i in range(len(prects) - 1, 0, -1):
                    if (prect0 & prects[i]).is_valid:
                        prect0 |= prects[i]
                        del prects[i]
                        repeat = True
            new_rects.append(prect0)
            del prects[0]
        return new_rects

    def join_rects_phase2(bboxes):
        """Postprocess identified text blocks, phase 2.

        Increase the width of each text block so that small left or right
        border differences are removed. Then try to join even more text
        rectangles.
        """
        prects = bboxes[:]  # copy of argument list
        for i in range(len(prects)):
            b = prects[i]
            # go left and right somewhat
            x0 = min([bb.x0 for bb in prects if abs(bb.x0 - b.x0) <= 3])
            x1 = max([bb.x1 for bb in prects if abs(bb.x1 - b.x1) <= 3])
            b.x0 = x0  # store new left / right border
            b.x1 = x1
            prects[i] = b

        # sort by left, top
        prects.sort(key=lambda b: (b.x0, b.y0))
        new_rects = [prects[0]]  # initialize with first item

        # walk through the rest, top to bottom, thwn left to right
        for r in prects[1:]:
            r0 = new_rects[-1]  # previous bbox

            # join if we have similar borders and are not to far down
            if (
                abs(r.x0 - r0.x0) <= 3
                and abs(r.x1 - r0.x1) <= 3
                and abs(r0.y1 - r.y0) <= 12
            ):
                r0 |= r
                new_rects[-1] = r0
                continue
            # else append this as new text block
            new_rects.append(r)
        return new_rects

    def join_rects_phase3(bboxes):
        prects = bboxes[:]
        prects.sort(key=lambda b: (b.x0, b.y0))
        new_rects = []
        while prects:
            prect0 = prects[0]
            repeat = True
            while repeat:
                repeat = False
                for i in range(len(prects) - 1, 0, -1):
                    prect1 = prects[i]
                    if prect1.x0 > prect0.x1 or prect1.x1 < prect0.x0:
                        continue
                    temp = prect0 | prects[i]
                    test = set(
                        [
                            tuple(b)
                            for b in prects + new_rects
                            if b.intersects(temp)
                        ]
                    )
                    if test == set((tuple(prect0), tuple(prect1))):
                        prect0 |= prect1
                        del prects[i]
                        repeat = True
            new_rects.append(prect0)
            del prects[0]
        new_rects.sort(key=lambda b: (b.y0, b.x0))
        return new_rects

    def clean_nblocks(nblocks):
        """Do some elementary cleaning."""

        # 1. remove any duplicate blocks.
        blen = len(nblocks)
        if blen < 2:
            return nblocks
        start = blen - 1
        for i in range(start, -1, -1):
            bb1 = nblocks[i]
            bb0 = nblocks[i - 1]
            if bb0 == bb1:
                del nblocks[i]

        # 2. repair sequence in special cases:
        # consecutive bboxes with almost same bottom value are sorted ascending
        # by x-coordinate.
        y1 = nblocks[0].y1  # first bottom coordinate
        i0 = 0  # its index
        i1 = -1  # index of last bbox with same bottom

        # Iterate over bboxes, identifying segments with approx. same bottom value.
        # Replace every segment by its sorted version.
        for i in range(1, len(nblocks)):
            b1 = nblocks[i]
            if abs(b1.y1 - y1) > 10:  # different bottom
                if i1 > i0:  # segment length > 1? Sort it!
                    nblocks[i0 : i1 + 1] = sorted(
                        nblocks[i0 : i1 + 1], key=lambda b: b.x0
                    )
                y1 = b1.y1  # store new bottom value
                i0 = i  # store its start index
            i1 = i  # store current index
        if i1 > i0:  # segment waiting to be sorted
            nblocks[i0 : i1 + 1] = sorted(
                nblocks[i0 : i1 + 1], key=lambda b: b.x0
            )
        return nblocks

    # extract vector graphics
    for p in paths:
        path_rects.append(p["rect"].irect)
    path_bboxes = path_rects

    # sort path bboxes by ascending top, then left coordinates
    path_bboxes.sort(key=lambda b: (b.y0, b.x0))

    # bboxes of images on page, no need to sort them
    for item in page.get_images():
        img_bboxes.extend(page.get_image_rects(item[0]))

    # blocks of text on page
    blocks = textpage.extractDICT()["blocks"]

    # Make block rectangles, ignoring non-horizontal text
    for b in blocks:
        bbox = fitz.IRect(b["bbox"])  # bbox of the block

        # ignore text written upon images
        if no_image_text and in_bbox(bbox, img_bboxes):
            continue

        # confirm first line to be horizontal
        try:
            line0 = b["lines"][0]  # get first line
        except IndexError:
            continue

        if line0["dir"] != (1, 0):  # only accept horizontal text
            vert_bboxes.append(bbox)
            continue

        srect = fitz.EMPTY_IRECT()
        for line in b["lines"]:
            lbbox = fitz.IRect(line["bbox"])
            text = "".join([s["text"].strip() for s in line["spans"]])
            if len(text) > 1:
                srect |= lbbox
        bbox = +srect

        if not bbox.is_empty:
            bboxes.append(bbox)

    # Sort text bboxes by ascending background, top, then left coordinates
    bboxes.sort(key=lambda k: (in_bbox(k, path_bboxes), k.y0, k.x0))

    # Extend bboxes to the right where possible
    # bboxes = extend_right(
    #     bboxes, int(page.rect.width), path_bboxes, vert_bboxes, img_bboxes
    # )

    # immediately return of no text found
    if bboxes == []:
        return []

    # --------------------------------------------------------------------
    # Join bboxes to establish some column structure
    # --------------------------------------------------------------------
    # the final block bboxes on page
    nblocks = [bboxes[0]]  # pre-fill with first bbox
    bboxes = bboxes[1:]  # remaining old bboxes

    for i, bb in enumerate(bboxes):  # iterate old bboxes
        check = False  # indicates unwanted joins

        # check if bb can extend one of the new blocks
        for j in range(len(nblocks)):
            nbb = nblocks[j]  # a new block

            # never join across columns
            if bb == None or nbb.x1 < bb.x0 or bb.x1 < nbb.x0:
                continue

            # never join across different background colors
            if in_bbox(nbb, path_bboxes) != in_bbox(bb, path_bboxes):
                continue

            temp = bb | nbb  # temporary extension of new block
            check = can_extend(temp, nbb, nblocks, vert_bboxes)
            if check == True:
                break

        if not check:  # bb cannot be used to extend any of the new bboxes
            nblocks.append(bb)  # so add it to the list
            j = len(nblocks) - 1  # index of it
            temp = nblocks[j]  # new bbox added

        # check if some remaining bbox is contained in temp
        check = can_extend(temp, bb, bboxes, vert_bboxes)
        if check == False:
            nblocks.append(bb)
        else:
            nblocks[j] = temp
        bboxes[i] = None

    # do some elementary cleaning
    nblocks = clean_nblocks(nblocks)
    # final joining of overlapping rectangles
    nblocks = join_rects_phase1(nblocks)
    nblocks = join_rects_phase2(nblocks)
    nblocks = join_rects_phase3(nblocks)

    # return identified text bboxes
    return nblocks


if __name__ == "__main__":
    """Only for debugging purposes, currently.

    Draw red borders around the returned text bboxes and insert
    the bbox number.
    Then save the file under the name "input-blocks.pdf".
    """
    import sys

    RED = fitz.pdfcolor["red"]
    # get the file name
    filename = sys.argv[1]

    # check if footer margin is given
    if len(sys.argv) > 2:
        footer_margin = int(sys.argv[2])
    else:  # use default vaue
        footer_margin = 50

    # check if header margin is given
    if len(sys.argv) > 3:
        header_margin = int(sys.argv[3])
    else:  # use default vaue
        header_margin = 50

    # open document
    doc = fitz.open(filename)

    # iterate over the pages
    for page in doc:
        # get the text bboxes
        bboxes = column_boxes(
            page, footer_margin=footer_margin, header_margin=header_margin
        )

        # prepare a canvas to draw rectangles and text
        shape = page.new_shape()

        # iterate over the bboxes
        for i, rect in enumerate(bboxes):
            shape.draw_rect(rect)  # draw a border

            # write sequence number
            shape.insert_text(rect.tl + (5, 15), str(i), color=RED)

        # finish drawing / text with color red
        shape.finish(color=RED)
        shape.commit()  # store to the page

    # save document with text bboxes
    doc.ez_save(filename.replace(".pdf", "-blocks.pdf"))
