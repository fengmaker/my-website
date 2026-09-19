# cjs 的学习笔记

这是使用 MkDocs Material 构建的个人学习网站，内容放在 `docs/`，导航和站点信息在 `mkdocs.yml`。

## 本地预览

```powershell
python -m pip install -r requirements.txt
python -m mkdocs serve
```

打开终端显示的本地地址查看页面。提交前运行：

```powershell
python -m mkdocs build --strict
```

`site/` 是生成目录，已被 Git 忽略。编辑文章时，优先检查页面链接、公式、代码块和导航是否正确。

## 发布

推送到 `main` 后，[GitHub Actions](.github/workflows/update.yml)会先执行严格构建，再将站点发布到 `gh-pages` 分支。GitHub Pages 的发布源需要指向该分支。

按仓库默认的 GitHub Pages 项目地址发布时，站点地址应为 <https://fengmaker.github.io/my-website/>；若使用自定义域名，需要同步更新 `mkdocs.yml` 的 `site_url`。
