import re, glob

for f in sorted(glob.glob("ch*_draft.md")):
    with open(f, "r", encoding="utf-8") as fh:
        c = fh.read()
    o = c
    c = re.sub(r"(?<!\\)(?<!f)rac\{", r"\\frac{", c)
    c = re.sub(r"(?<!\\)eft\(", r"\\left(", c)
    c = re.sub(r"(?<!\\)eft\[", r"\\left[", c)
    c = re.sub(r"(?<!\\)ight\)", r"\\right)", c)
    c = re.sub(r"(?<!\\)ight\]", r"\\right]", c)
    c = re.sub(r"(?<!\\)egin\{", r"\\begin{", c)
    # tab+ext → \text
    c = c.replace("\text{", "\\text{")
    if c != o:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(c)
        print(f + ": fixed")
    else:
        print(f + ": ok")
