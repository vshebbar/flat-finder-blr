"""Local OCR with macOS's built-in Vision framework (free, no upload). Returns text boxes with page positions.

Large pages are read in overlapping tiles: Vision shrinks big images internally, which loses the tiny
room-size text floor plans use.
"""
import Quartz
import Vision
from Foundation import NSURL

TILE = 1600


def _read(cg):
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    req.setUsesLanguageCorrection_(False)
    req.setMinimumTextHeight_(0.0)  # floor plans print sizes in tiny type; the default skips them
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg, None)
    handler.performRequests_error_([req], None)
    for o in req.results() or []:
        c = o.topCandidates_(1)[0]
        b = o.boundingBox()
        yield str(c.string()), b.origin.x + b.size.width / 2, 1 - (b.origin.y + b.size.height / 2), b.size.height, float(c.confidence())


def ocr(path):
    """[(text, cx, cy, height, confidence)] with x, y in 0..1 of the whole image, from the top-left."""
    src = Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(str(path)), None)
    img = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    W, H = Quartz.CGImageGetWidth(img), Quartz.CGImageGetHeight(img)
    if W <= TILE * 1.25 and H <= TILE * 1.25:
        return list(_read(img))
    out, step = [], int(TILE * 0.8)
    for y0 in range(0, max(1, H - TILE // 5), step):
        for x0 in range(0, max(1, W - TILE // 5), step):
            w, h = min(TILE, W - x0), min(TILE, H - y0)
            tile = Quartz.CGImageCreateWithImageInRect(img, Quartz.CGRectMake(x0, y0, w, h))
            for t, cx, cy, bh, conf in _read(tile):
                X, Y = (x0 + cx * w) / W, (y0 + cy * h) / H
                # the same words seen in two overlapping tiles: keep one
                if any(o[0] == t and abs(o[1] - X) < 0.01 and abs(o[2] - Y) < 0.01 for o in out):
                    continue
                out.append((t, X, Y, bh * h / H, conf))
    return out


if __name__ == "__main__":
    import sys
    for t in ocr(sys.argv[1]):
        print(f"{t[1]:.3f} {t[2]:.3f} {t[0]}")
