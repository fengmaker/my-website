# 仓库协作约定

这是一个 MkDocs 网站。文章放在 `docs/`，导航和站点配置在 `mkdocs.yml`，依赖在 `requirements.txt`。

用户委托修改本仓库时：

1. 完成修改后运行 `python -m mkdocs build --strict` 和 `git diff --check`。若修改与网站构建无关，可省略构建，并在回复中说明。
2. 提交前查看 `git status` 和 diff，只暂存本次任务涉及的文件。保留与本次任务无关的现有改动；用户明确要求一并提交时除外。
3. 在本地创建一个内容明确的 Git commit，然后在回复中给出提交摘要和 commit 哈希。
4. 不执行 `git push`、`mkdocs gh-deploy` 或其他发布操作，除非用户另外明确要求。用户会自行 push。

纯咨询或只读检查无需创建 commit；没有文件改动时也无需创建空 commit。
