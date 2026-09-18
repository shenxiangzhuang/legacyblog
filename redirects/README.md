# Cloudflare 旧站跳转

内容核对日期：2026-09-18。两个站点继续使用 GitHub Pages，仅在 Cloudflare 配置 HTTP 301，不需要修改 Astro 或部署 Worker。

- [coverage.md](coverage.md)：109 个旧页面的去向；49 个有新版对应（30 篇旧博客正文及 19 个笔记/专题页面），60 个回首页。
- [articles.csv](articles.csv)：450 条精确映射。包含两个入口及现有 www.datahonor.com 别名、尾斜杠/无尾斜杠/index.html，以及旧 Hexo ROC-AUC 链接。
- [fallback.csv](fallback.csv)：首页和未匹配旧路径回 `https://mathewshen.me/`。

## 配置

1. 确认两个域名的相应 DNS 记录开启 Cloudflare Proxy（橙云）。`mathewshen.me` 源站为 GitHub Pages；保留现有 Full 加密模式，已确认 Universal 边缘证书 Active。
2. 在账号级 Delivery & performance → Bulk redirects 创建 `legacyblog_articles`，导入 `articles.csv`，创建并启用关联规则。
3. 创建 `legacyblog_fallback`，导入 `fallback.csv`，创建并启用关联规则。**文章规则必须排在兜底规则之前**。
4. 停用与之冲突的旧域名跳转规则。Single Redirects 先于 Bulk Redirects 执行，因此旧 Single Redirect 必须停用，否则会抢先跳到 `/legacyblog/`。先保留旧规则内容，以便回滚。
5. 验证 `datahonor.com`、`mathewshen.me/legacyblog` 和 `/legacyblog/` 一跳到首页；文章一跳到对应新版；未知路径一跳到首页；新版首页和 `/blog/` 不跳转。

CSV 无表头，顺序为 source,target,status,preserve_query,include_subdomains,subpath_matching,preserve_path_suffix。源地址不写协议，因此同时匹配 HTTP/HTTPS。文章只精确匹配；兜底允许子路径，但不保留路径后缀。两类规则都丢弃查询参数；旧 MkDocs 的 `?h=` 搜索高亮参数在新版无意义。URL fragment 不发给服务器，浏览器可能继承旧锚点；本配置保证到达对应文章，不保证旧章节锚点仍有效。

仅匹配 `datahonor.com`、`www.datahonor.com` 和 `mathewshen.me/legacyblog`；不会覆盖 `mathewshen.me` 的其他页面或未列出的其他子域。

## 生成与检查

在旧站仓库运行（新站仓库位于同级目录）：

```sh
python3 redirects/generate.py
python3 redirects/generate.py --check
```

显式映射保存在 `generate.py` 中。生成器校验旧源文件、新版目标文件、draft 状态及 URL 唯一性。已对照线上两个 sitemap 验证全部 49 个旧地址，并确认 47 个不同新版目标均为 HTTP 200、无额外跳转。

## 回滚

停用新建的两个 Bulk Redirect Rules，再恢复旧跳转规则。若本次开启了主域名 Proxy，需要恢复此前 DNS only 状态。浏览器已经缓存的 301 可能继续生效，验证时使用无缓存请求。

## 官方文档

- [Bulk Redirect CSV 格式](https://developers.cloudflare.com/rules/url-forwarding/bulk-redirects/reference/csv-file-format/)
- [执行顺序与 Proxy 要求](https://developers.cloudflare.com/rules/url-forwarding/)
- [匹配方式](https://developers.cloudflare.com/rules/url-forwarding/bulk-redirects/how-it-works/)

## 变更前状态

- `mathewshen.me` 根域名的 4 条 A 和 4 条 AAAA 均为 DNS only。源站地址为 GitHub Pages 的 `185.199.108–111.153` / `2606:50c0:8000–8003::153`。
- 主域名 SSL/TLS 为 Full，Universal 边缘证书 Active；不需要更改加密模式。
- `datahonor.com` 现有 Single Redirect：`datahonor.com all to mathewshen.me`（ID `79ad16abf7644c128fb6da8e174722bf`），匹配根域名及 `www.datahonor.com`，301 到 `concat("https://mathewshen.me/legacyblog", http.request.uri.path)`。

## 已部署（2026-09-18）

- Bulk Redirect Rule 1：`Legacy blog articles`（`1345f25730704d1288dee08eabea679a`），关联 450 条精确映射，Enabled。
- Bulk Redirect Rule 2：`Legacy blog fallback`（`89607968aaaf41b6a3ebc6a745051386`），关联 4 条首页兜底，Enabled。
- 旧 Single Redirect 已 Disabled，保留配置可回滚。
- 主域名 8 条 A/AAAA 已开启 Proxied，IP、SSL/TLS 模式及其他 DNS 记录保持原值。
- 兜底的 Preserve path suffix 已显式关闭并保存；实际请求验证未匹配路径直接跳首页。配置传播期间短暂观察到保留后缀，不能只凭控制台勾选状态判断生效。
- 最终批量验证：537 个 HTTP 请求全部通过，包括全部 450 条 HTTPS 精确映射、HTTP/HTTPS 首页及未知路径兜底、查询参数、子路径误匹配检查，以及全部 47 个新版文章目标和主站首页/博客列表的 HTTP 200 检查。
