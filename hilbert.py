
import os, sys, math, datetime, time, string
from PIL import Image, ImageDraw


def graycode(x):
    x = int(x)
    return x^(x>>1)

def igraycode(x):
    if x == 0:
        return x
    m = int(math.ceil(math.log(x, 2)))+1
    i, j = x, 1
    while j < m:
        i = i ^ (x>>j)
        j += 1
    return i

def bits(n, width):
    assert n < 2**width
    bin = []
    for i in range(width):
        bin.insert(0, 1 if n&(1<<i) else 0)
    return bin

def bits2int(bits):
    n = 0
    for p, i in enumerate(reversed(bits)):
        n += i*2**p
    return n

def rrot(x, i, width):
    assert x < 2**width
    i = i%width
    x = (x>>i) | (x<<width-i)
    return x&(2**width-1)

def lrot(x, i, width):
    assert x < 2**width
    i = i%width
    x = (x<<i) | (x>>width-i)
    return x&(2**width-1)

def tsb(x, width):
    assert x < 2**width
    i = 0
    while x&1 and i <= width:
        x = x >> 1
        i += 1
    return i

def setbit(x, w, i, b):
    assert b in [1, 0]
    assert i < w
    if b:
        return x | 2**(w-i-1)
    else:
        return x & ~2**(w-i-1)

def bitrange(x, width, start, end):
    return x >> (width-end) & ((2**(end-start))-1)

def entropy(data, blocksize, offset, symbols=256):
    if len(data) < blocksize:
        raise ValueError("Data length must be larger than block size.")
    if offset < blocksize/2:
        start = 0
    elif offset > len(data)-blocksize/2:
        start = len(data)-blocksize/2
    else:
        start = offset-blocksize/2
    hist = {}
    for i in data[start:start+blocksize]:
        hist[i] = hist.get(i, 0) + 1
    base = min(blocksize, symbols)
    entropy = 0
    for i in hist.values():
        p = i/float(blocksize)
        entropy += (p * math.log(p, base))
    return -entropy

def transform(entry, direction, width, x):
    assert x < 2**width
    assert entry < 2**width
    return rrot((x^entry), direction+1, width)

def itransform(entry, direction, width, x):
    assert x < 2**width
    assert entry < 2**width
    return lrot(x, direction+1, width)^entry

def direction(x, n):
    assert x < 2**n
    if x == 0:
        return 0
    elif x%2 == 0:
        return tsb(x-1, n)%n
    else:
        return tsb(x, n)%n

def entry(x):
    if x == 0:
        return 0
    else:
        return graycode(2*((x-1)/2))

def hilbert_point(dimension, order, h):
    hwidth = order*dimension
    e, d = 0, 0
    p = [0]*dimension
    for i in range(order):
        w = bitrange(h, hwidth, i*dimension, i*dimension+dimension)
        l = graycode(w)
        l = itransform(e, d, dimension, l)
        for j in range(dimension):
            b = bitrange(l, dimension, j, j+1)
            p[j] = setbit(p[j], order, i, b)
        e = e ^ lrot(entry(w), d+1, dimension)
        d = (d + direction(w, dimension) + 1)%dimension
    return p

def hilbert_index(dimension, order, p):
    h, e, d = 0, 0, 0
    for i in range(order):
        l = 0
        for x in range(dimension):
            b = bitrange(p[dimension-x-1], order, i, i+1)
            l |= b<<x
        l = transform(e, d, dimension, l)
        w = igraycode(l)
        e = e ^ lrot(entry(w), d+1, dimension)
        d = (d + direction(w, dimension) + 1)%dimension
        h = (h<<dimension)|w
    return h

class Hilbert:
    def __init__(self, dimension, order):
        self.dimension, self.order = dimension, order

    @classmethod
    def fromSize(self, dimension, size):
        x = math.log(size, 2)
        if not float(x)/dimension == int(x)/dimension:
            raise ValueError("Size does not fit Hilbert curve of dimension %s."%dimension)
        return Hilbert(dimension, int(x/dimension))

    def __len__(self):
        return 2**(self.dimension*self.order)

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError
        return self.point(idx)

    def dimensions(self):
        return [int(math.ceil(len(self)**(1/float(self.dimension))))]*self.dimension

    def index(self, p):
        return hilbert_index(self.dimension, self.order, p)

    def point(self, idx):
        return hilbert_point(self.dimension, self.order, idx)


curveMap = {
    # "hcurve": hcurve.Hcurve,
    "hilbert": Hilbert
    # "zigzag": zigzag.ZigZag,
    # "zorder": zorder.ZOrder,
    # "natural": natural.Natural,
    # "gray": graycurve.GrayCurve,
}
curves = curveMap.keys()

def fromSize(curve, dimension, size):
    return curveMap[curve].fromSize(dimension, size)

def fromOrder(curve, dimension, order):
    return curveMap[curve](dimension, order)

class Inplace:
    def __init__(self, title="", stream=sys.stderr):
        self.stream, self.title = stream, title
        self.last = 0

    def tick(self, s):
        if not self.stream:
            return
        w = "\r%s%s"%(self.title, s)
        self.last = len(w)
        self.stream.write(w)
        self.stream.flush()

    def inject(self, txt):
        self.stream.write("\n")
        self.clear()
        self.stream.write("%s\n"%txt)
        self.stream.flush()

    def clear(self):
        if not self.stream:
            return
        spaces = " "*self.last
        self.stream.write("\r%s\r"%spaces)

def entropy(data, blocksize, offset, symbols=256):
    if len(data) < blocksize:
        raise ValueError("Data length must be larger than block size.")
    if offset < blocksize/2:
        start = 0
    elif offset > len(data)-blocksize/2:
        start = len(data)-blocksize/2
    else:
        start = offset-blocksize/2
    hist = {}
    for i in data[start:start+blocksize]:
        hist[i] = hist.get(i, 0) + 1
    base = min(blocksize, symbols)
    entropy = 0
    for i in hist.values():
        p = i/float(blocksize)
        entropy += (p * math.log(p, base))
    return -entropy

class Progress(Inplace):
    bookend = "|"
    done = "-"
    current = ">"
    todo = " "
    def __init__(self, target, title="", width=40, stream=sys.stderr):
        Inplace.__init__(self, title, stream=stream)
        self.width, self.target = width, target
        self.prev = -1
        self.startTime = None
        self.window = None

    def tick(self, val):
        if not self.stream:
            return
        if not self.startTime:
            self.startTime = datetime.datetime.now()
        pp = val/float(self.target)
        progress = int(pp * self.width)
        t = datetime.datetime.now() - self.startTime
        runsecs = t.days*86400 + t.seconds + t.microseconds/1000000.0
        if pp == 0:
            eta = "?:??:??"
        else:
            togo = runsecs * (1 - pp)/pp
            eta = datetime.timedelta(seconds = int(togo))
        if pp > self.prev:
            self.prev = pp
            l = self.done * progress
            r = self.todo * (self.width - progress)
            now = time.time()
            s = "%s%s%s%s%s %s" % (
                self.bookend, l,
                self.current,
                r, self.bookend, eta
            )
            Inplace.tick(self, s)

    def set_target(self, t):
        self.target = t

    def restoreTerm(self):
        if self.window:
            #begin nocover
            curses.echo()
            curses.nocbreak()
            curses.endwin()
            self.window = None
            #end nocover

    def clear(self):
        Inplace.clear(self)
        self.restoreTerm()

    def __del__(self):
        self.restoreTerm()

    def full(self):
        self.tick(self.target)


class Dummy:
    def __init__(self, *args, **kwargs): pass
    def tick(self, *args, **kwargs): pass
    def restoreTerm(self, *args, **kwargs): pass
    def clear(self, *args, **kwargs): pass
    def full(self, *args, **kwargs): pass
    def set_target(self, *args, **kwargs): pass

def parseColor(c):
    if len(c) == 6:
        r = int(c[0:2], 16)/255.0
        g = int(c[2:4], 16)/255.0
        b = int(c[4:6], 16)/255.0
        return [r, g, b]
    elif len(c) == 3:
        return c

class _Color:
    def __init__(self, data, block):
        self.data, self.block = data, block
        s = list(set(data))
        s.sort()
        self.symbol_map = {v : i for (i, v) in enumerate(s)}

    def __len__(self):
        return len(self.data)

    def point(self, x):
        if self.block and (self.block[0]<=x<self.block[1]):
            return self.block[2]
        else:
            return self.getPoint(x)

class ColorGradient(_Color):
    def getPoint(self, x):
        c = ord(self.data[x])/255.0
        return [
            int(255*c),
            int(255*c),
            int(255*c)
        ]

class ColorHilbert(_Color):
    def __init__(self, data, block):
        _Color.__init__(self, data, block)
        self.csource = fromSize("hilbert", 3, 256**3)
        self.step = len(self.csource)/float(len(self.symbol_map))

    def getPoint(self, x):
        c = self.symbol_map[self.data[x]]
        return self.csource.point(int(c*self.step))


class ColorClass(_Color):
    def getPoint(self, x):
        c = ord(self.data[x])
        if c == 0:
            return [0, 0, 0]
        elif c == 255:
            return [255, 255, 255]
        elif chr(c) in string.printable:
            return [55, 126, 184]
        return [228, 26, 28]

class ColorEntropy(_Color):
    def getPoint(self, x):
        e = entropy(self.data, 32, x, len(self.symbol_map))
        # http://www.wolframalpha.com/input/?i=plot+%284%28x-0.5%29-4%28x-0.5%29**2%29**4+from+0.5+to+1
        def curve(v):
            f = (4*v - 4*v**2)**4
            f = max(f, 0)
            return f
        r = curve(e-0.5) if e > 0.5 else 0
        b = e**2
        return [
            int(255*r),
            0,
            int(255*b)
        ]

def drawmap_unrolled(map, size, csource, name, prog):
    prog.set_target((size**2)*4)
    map = fromSize(map, 2, size**2)
    c = Image.new("RGB", (size, size*4))
    cd = ImageDraw.Draw(c)
    step = len(csource)/float(len(map)*4)

    sofar = 0
    for quad in range(4):
        for i, p in enumerate(map):
            off = (i + (quad * size**2))
            color = csource.point(
                        int(off * step)
                    )
            x, y = tuple(p)
            cd.point(
                (x, y + (size * quad)),
                fill=tuple(color)
            )
            if not sofar%100:
                prog.tick(sofar)
            sofar += 1
    c.save(name)


def drawmap_square(map, size, csource, name, prog):
    prog.set_target((size**2))
    map = fromSize(map, 2, size**2)
    c = Image.new("RGB", map.dimensions())
    cd = ImageDraw.Draw(c)
    step = len(csource)/float(len(map))
    for i, p in enumerate(map):
        color = csource.point(int(i*step))
        cd.point(tuple(p), fill=tuple(color))
        if not i%100:
            prog.tick(i)
    c.save(name)

def main():
    from optparse import OptionParser, OptionGroup
    parser = OptionParser(
                usage = "%prog [options] infile [output]",
                version="%prog 0.1",
            )
    parser.add_option(
        "-b", "--block", action="store",
        dest="block", default=None,
        help="Mark a block of data with a specified color. Format: hexstartaddr:hexendaddr[:hexcolor]"
    )
    parser.add_option(
        "-c", "--color", action="store",
        type="choice", dest="color", default="class",
        choices=["class", "hilbert", "entropy", "gradient"],
        help="Color map."
    )
    parser.add_option(
        "-m", "--map", action="store",
        type="choice", dest="map", default="hilbert",
        choices=sorted(curveMap.keys()),
        help="Pixel layout map. Can be any supported curve."
    )
    parser.add_option(
        "-n", "--namesuffix", action="store",
        type="str", dest="suffix", default="",
        help="Suffix for generated file names. Ignored if destination is specified."
    )
    parser.add_option(
        "-p", "--progress", action="store_true", default=False,
        dest="progress",
        help="Don't show progress bar - print the destination file name."
    )
    parser.add_option(
        "-s", "--size", action="store",
        type="int", dest="size", default=256,
        help="Image width in pixels."
    )
    parser.add_option(
        "-t", "--type", type="choice",
        dest="type", default="unrolled",
        choices=["unrolled", "square"],
        help="Image aspect ratio - square (1x1) or unrolled (1x4)"
    )
    parser.add_option(
        "-q", "--quiet", action="store_true",
        dest="quiet", default=False
    )
    options, args = parser.parse_args()
    if len(args) not in [1, 2]:
        parser.error("Please specify input and output file.")

    d = open(args[0]).read()
    if len(args) == 2:
        dst = args[1]
    else:
        base = os.path.basename(args[0])
        if "." in base:
            base, _ = base.rsplit(".", 1)
        dst = base + options.suffix + ".png"

    if os.path.exists(dst) and len(args) < 2:
        print >> sys.stderr, "Refusing to over-write '%s'. Specify explicitly if you really want to do this."%dst
        sys.exit(1)

    block = None
    if options.block:
        parts = options.block.split(":")
        if len(parts) not in [2, 3]:
            raise ValueError("Invalid block specification.")
        s, e = int(parts[0], 16), int(parts[1], 16)
        if len(parts) == 3:
            c = parseColor(parts[2])
        else:
            c = [255, 0, 0]
        block = (s, e, c)

    if options.color == "class":
        csource = ColorClass(d, block)
    elif options.color == "hilbert":
        csource = ColorHilbert(d, block)
    elif options.color == "gradient":
        csource = ColorGradient(d, block)
    else:
        csource = ColorEntropy(d, block)


    if options.progress:
        print(dst)

    if options.quiet or options.progress:
        prog = Dummy()
    else:
        prog = Progress(None)


    if options.type == "unrolled":
        drawmap_unrolled(options.map, options.size, csource, dst, prog)
    elif options.type == "square":
        drawmap_square(options.map, options.size, csource, dst, prog)
    prog.clear()


main()
