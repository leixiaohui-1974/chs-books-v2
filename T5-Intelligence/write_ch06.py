# -*- coding: utf-8 -*-
path = "Z:/research/chs-books-v2/T5-Intelligence/ch06_draft.md"
content = chr(31532)+chr(54)+chr(31456)+chr(10)
with open(path, "wb") as f: f.write(content.encode("utf-8"))
print("done, size:", len(content))
