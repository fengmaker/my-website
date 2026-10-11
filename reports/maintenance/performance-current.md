# MkDocs site measurement

Network label: **当前执行环境网络；未切换网络；2026-10-11**

Static file sizes describe the built files. HTTP values describe streamed transfers for explicitly selected URLs.
`time_to_headers_ms` includes DNS, connection, TLS, request, and response-header time; it is not a pure server TTFB.
HTTP byte counts cover response bodies and exclude headers and protocol framing.
This tool does not run a browser: FCP, LCP, and actual MathJax formula-render time were not measured.

Generated at (UTC): 2026-10-11T09:32:13Z

## Static site

Files: 377

Total: 46466871 bytes

Large-file threshold: 262144 bytes

| Category | Files | Bytes |
|---|---:|---:|
| css | 3 | 152731 |
| html | 154 | 12302634 |
| images | 175 | 26942677 |
| javascript | 37 | 1061404 |
| other | 7 | 1359213 |
| search_index | 1 | 4648212 |

External MathJax URLs in `mkdocs.yml`:
- `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js`

Largest HTML pages

| Path | Bytes |
|---|---:|
| `运筹优化/面试题库/路径规划算法岗面试题库_参考答案/index.html` | 235707 |
| `算法笔记/二叉树/自底向上/index.html` | 172712 |
| `算法笔记/数据结构/枚举技巧/index.html` | 168003 |
| `运筹优化/运筹学基础/Chapter7_2/index.html` | 159552 |
| `运筹优化/面试题库/运筹优化算法岗面试题库_参考答案/index.html` | 152964 |
| `算法笔记/二分/二分查找/index.html` | 152283 |
| `算法笔记/二叉树/自顶向下/index.html` | 139316 |
| `运筹优化/解谜/CPSAT_2/index.html` | 133504 |
| `运筹优化/资料库与面试/标签索引/index.html` | 130285 |
| `运筹优化/离散优化/Ch_07/index.html` | 129750 |

Largest non-HTML resources

| Path | Bytes |
|---|---:|
| `search/search_index.json` | 4648212 |
| `运筹优化/images/202411252008954.png` | 1487656 |
| `运筹优化/images/202507150148475.png` | 1125857 |
| `运筹优化/images/20260421180401534.png` | 1074064 |
| `assets/javascripts/bundle.79ae519e.min.js.map` | 1026989 |
| `运筹优化/images/202310251200191.png` | 946146 |
| `运筹优化/images/20260504210451635.png` | 911138 |
| `运筹优化/images/20260504192513076.png` | 871297 |
| `运筹优化/images/202310251200190.png` | 708673 |
| `assets/javascripts/lunr/wordcut.js` | 677463 |

## HTTP measurements

| URL | Successes | Median headers (ms) | Median body (ms) | Median total (ms) | Median bytes | Failures |
|---|---:|---:|---:|---:|---:|---|
| `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` | 5/5 | 569.22 | 378.501 | 944.672 | 1173007 | None |
| `https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js` | 4/5 | 1386.542 | 404.634 | 1767.267 | 1173007.0 | http_status: 1 |
| `https://fengmaker.github.io/my-website/` | 5/5 | 737.136 | 0.452 | 737.435 | 25060 | None |

Samples for `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js`:

- #1: HTTP 200; 1173007 bytes; total 1019.406 ms
- #2: HTTP 200; 1173007 bytes; total 971.091 ms
- #3: HTTP 200; 1173007 bytes; total 941.216 ms
- #4: HTTP 200; 1173007 bytes; total 907.345 ms
- #5: HTTP 200; 1173007 bytes; total 944.672 ms

Samples for `https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js`:

- #1: HTTP 200; 1173007 bytes; total 2067.772 ms
- #2: HTTP 200; 1173007 bytes; total 1597.784 ms
- #3: HTTP 200; 1173007 bytes; total 1537.925 ms
- #4: HTTP 200; 1173007 bytes; total 1936.751 ms
- #5: HTTP 302; 50 bytes; total 701.766 ms (HTTP 302)

Samples for `https://fengmaker.github.io/my-website/`:

- #1: HTTP 200; 25060 bytes; total 976.931 ms
- #2: HTTP 200; 25060 bytes; total 657.07 ms
- #3: HTTP 200; 25060 bytes; total 623.453 ms
- #4: HTTP 200; 25060 bytes; total 737.435 ms
- #5: HTTP 200; 25060 bytes; total 790.979 ms

Static sizes refreshed after the DOI correction. Network samples retained from 2026-10-11T09:25:17Z.
