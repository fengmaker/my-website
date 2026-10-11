# cjs 的学习笔记

这是使用 MkDocs Material 构建的个人学习网站，内容放在 `docs/`，导航和站点信息在 `mkdocs.yml`。

## 本地预览

```powershell
python -m pip install -r requirements.txt
python -m mkdocs serve
```

打开终端显示的本地地址查看页面。本轮进度、完成证据与后续事项见[重构进度](重构进度.md)。提交前运行：

```powershell
python -B -m unittest discover -s tests -p "test_*.py"
python -B scripts/check_docs.py --report
python -m mkdocs build --strict
git diff --check
```

离线检查覆盖导航、标签元数据、本地图片和完全重复文章提示。运筹优化内容页及学习地图必须使用 `config/tags.yml` 中的统一标签，索引与许可工具页除外。中文术语词典在 `config/search/jieba-user.dict`，添加条目时沿用现有格式。

`site/` 是生成目录，已被 Git 忽略。编辑文章时，优先检查页面链接、公式、代码块和导航是否正确。

## 外链与性能维护

```powershell
python -X utf8 -B scripts/check_external_links.py --timeout 8 --retries 1 --workers 4 --max-seconds 600 --output reports/maintenance/external-links.json --report reports/maintenance/external-links.md
python -X utf8 -B scripts/measure_site.py --measure-network --samples 5 --network-label "实际网络名称" --output reports/maintenance/performance-current.json --report reports/maintenance/performance-current.md
```

外链脚本默认只报告；`--inventory-only` 不联网，`--strict` 仅对 GET 复核后的 404/410 返回失败。受限、限流、TLS、网络超时和其他 HTTP 错误分别记录，预算外地址标为未检查。它扫描 `docs/` 中的常见 Markdown / HTML 链接，忽略代码块，不检查片段锚点。每周一 UTC 02:17 的[独立巡检流程](.github/workflows/check-external-links.yml)上传报告，不发布网站，也不阻断发布流程；推送后生效，可手动运行。

性能脚本先读取本地严格构建后的 `site/`，仅指定 `--measure-network` 或 `--url URL` 时联网。HTTP 采样不执行 JavaScript，不能代表浏览器首屏或公式渲染时间。首次结果、复测步骤与限制见[维护记录](reports/maintenance/README.md)。

## 个人项目与实验记录

[作品集](docs/运筹优化/项目与实验复现/index.md)已收录 GMRP-ALNS 与 VRPTW Solver，含固定版本、归档实测、限制、下载表格与复现入口。本轮材料核查见 [project-evidence](reports/project-evidence/README.md)，来源和文件哈希见 `docs/assets/projects/provenance.json`。两张汇总图可用 `python -B scripts/plot_project_results.py` 重画，仅需可选 Matplotlib 依赖，不会执行求解器。

## 发布

推送到 `main` 后，[GitHub Actions](.github/workflows/update.yml)会先执行严格构建，再将站点发布到 `gh-pages` 分支。GitHub Pages 的发布源需要指向该分支。

按仓库默认的 GitHub Pages 项目地址发布时，站点地址应为 <https://fengmaker.github.io/my-website/>；若使用自定义域名，需要同步更新 `mkdocs.yml` 的 `site_url`。
