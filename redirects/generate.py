"""Generate Cloudflare Bulk Redirect CSVs; run with --check to verify outputs."""
import csv
import io
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT.parent / 'shenxiangzhuang.github.io/src/content/blog'
HOME = 'https://mathewshen.me/'
BASES = ('datahonor.com', 'www.datahonor.com', 'mathewshen.me/legacyblog')
# Older Hexo link still referenced by the migrated Effect Size article.
ALIASES = {'/2020/05/02/ROC-AUC/': '2020/roc-auc'}

# Explicitly reviewed source documents -> published Astro collection IDs.
MIGRATED = {
    'blog/posts/2019.md': '2019/2019',
    'blog/posts/2024.md': '2024/2024-summary',
    'blog/posts/ai-town.md': '2024/ai-town',
    'blog/posts/ai_golden_age.md': '2025/ai-golden-age',
    'blog/posts/bert.md': '2025/bert',
    'blog/posts/chance.md': '2019/chance',
    'blog/posts/dl_book.md': '2025/books/ai-llm-dl',
    'blog/posts/ds.md': '2024/ds',
    'blog/posts/graduate.md': '2022/graduate',
    'blog/posts/grpo_kl.md': '2025/grpo-kl',
    'blog/posts/lifelong_learning_2023.md': '2024/lifelong-2023',
    'blog/posts/llm_2024.md': '2024/ai-think-2024',
    'blog/posts/llm_kv_cache.md': '2025/llm-kv-cache',
    'blog/posts/llm_sps.md': '2025/llm-sps',
    'blog/posts/newer_scholar.md': '2025/google-scholar-new-features',
    'blog/posts/obscurant.md': '2018/obscurant',
    'blog/posts/oh_numpy_pytorch.md': '2025/oh-numpy-pytorch',
    'blog/posts/open-source.md': '2023/open-source-related',
    'blog/posts/open_source_thought.md': '2025/open-source-feedback',
    'blog/posts/presentia.md': '2025/presentia',
    'blog/posts/redis_lock.md': '2025/redis-lock',
    'blog/posts/rust_and_python.md': '2025/rust-and-python',
    'blog/posts/searching.md': '2019/wushuang',
    'blog/posts/strange-dream.md': '2018/strange-dream',
    'blog/posts/sysu-card.md': '2021/sysu-card',
    'blog/posts/ten.md': '2023/ten-years-old',
    'blog/posts/toynlp.md': '2025/toynlp',
    'blog/posts/toyrl.md': '2025/toyrl',
    'blog/posts/wang_work.md': '2025/wang-work',
    'blog/posts/zhplot.md': '2024/zhplot',
    'datascience/ml/mle-mer.md': '2017/mle-erm',
    'datascience/statistics/effect-size.md': '2021/p-value-effect-size',
    'datascience/statistics/index.md': '2025/books/probability-statistics',
    'datascience/statistics/probability-and-mathematical-statistics-books.md': '2025/books/probability-statistics',
    'datascience/statistics/roc-auc.md': '2020/roc-auc',
    'datascience/statistics/three-doors-and-three-prisoners.md': '2017/three-doors-and-three-prisoners',
    'life/cookbook/boil.md': '2025/cookbook/boil',
    'life/cookbook/saute.md': '2025/cookbook/saute',
    'life/cookbook/stew.md': '2025/cookbook/stew',
    'life/literature/books.md': '2025/books/literature',
    'odyssey/aiops/index.md': '2025/aiops',
    'odyssey/aiops/rca/paper.md': '2025/aiops/rca-paper',
    'odyssey/aiops/tsad/paper.md': '2025/aiops/tsad-paper',
    'odyssey/aiops/tsfcst/paper.md': '2025/aiops/tsfcst-paper',
    'odyssey/chc/index.md': '2025/crowdsourcing',
    'odyssey/chc/paper.md': '2025/crowdsourcing/papers',
    'odyssey/llm/engineering.md': '2025/odyssey-llm/engineering',
    # The old LLM landing page contains book reviews, now in the books series.
    'odyssey/llm/index.md': '2025/books/ai-llm-dl',
    'odyssey/llm/paper.md': '2025/odyssey-llm/paper-reading-list',
}


def old_path(source):
    path = Path(source)
    if source.startswith('blog/posts/'):
        text = (ROOT / 'docs' / source).read_text()
        date = re.search(r'^date: (\d{4})-(\d{2})-(\d{2})\s*$', text, re.M)
        slug = re.search(r'^slug: (.+)$', text, re.M)[1].strip('"\' ')
        return '/blog/' + '/'.join(date.groups()) + '/' + slug + '/'
    relative = path.parent if path.stem == 'index' else path.with_suffix('')
    return '/' + (relative.as_posix().strip('./') + '/' if source != 'index.md' else '')


def csv_text(rows):
    output = io.StringIO()
    csv.writer(output, lineterminator='\n').writerows(rows)
    return output.getvalue()


def generate():
    documents = sorted(p.relative_to(ROOT / 'docs').as_posix() for p in (ROOT / 'docs').rglob('*.md'))
    assert set(MIGRATED) <= set(documents)
    rows = []
    paths = {old_path(source): post for source, post in MIGRATED.items()} | ALIASES
    for source, post in sorted(MIGRATED.items()):
        targets = list((BLOG / post).glob('index.*'))
        assert len(targets) == 1, post
        assert not re.search(r'^draft:\s*true\s*$', targets[0].read_text(), re.M), post
    for path, post in sorted(paths.items()):
        for base in BASES:
            for variant in (path, path.rstrip('/'), path + 'index.html'):
                # No scheme matches HTTP and HTTPS. Exact paths only; drop old query strings.
                rows.append((base + variant, HOME + 'blog/' + post + '/', 301, 'FALSE', 'FALSE', 'FALSE', 'FALSE'))
    assert len({r[0] for r in rows}) == len(rows)
    fallback = [
        ('datahonor.com/', HOME, 301, 'FALSE', 'FALSE', 'TRUE', 'FALSE'),
        ('www.datahonor.com/', HOME, 301, 'FALSE', 'FALSE', 'TRUE', 'FALSE'),
        ('mathewshen.me/legacyblog/', HOME, 301, 'FALSE', 'FALSE', 'TRUE', 'FALSE'),
        ('mathewshen.me/legacyblog', HOME, 301, 'FALSE', 'FALSE', 'FALSE', 'FALSE'),
    ]
    report = [
        '# 旧站内容对应表', '',
        f'检查 {len(documents)} 个旧站 Markdown 页面：{len(MIGRATED)} 个有新版对应，其余 {len(documents) - len(MIGRATED)} 个跳首页。', '',
        '旧路径同时适用于 `datahonor.com`、`www.datahonor.com` 和 `mathewshen.me/legacyblog`；支持尾斜杠、无尾斜杠、`index.html`。', '',
        'AIOps 和 Crowdsourcing 索引跳对应专题；旧 LLM 索引正文为书评，跳新版 AI 书单。统计学索引的书评已迁移，课程列表未完整迁移。',
        '仅有相似主题或重复引言不算迁移；例如旧 Life 入口、AIOps 会议列表不映射到相关文章。', '',
        '| 旧源文件 | 旧路径 | 新版地址 |', '| --- | --- | --- |',
    ]
    for source in documents:
        destination = HOME + 'blog/' + MIGRATED[source] + '/' if source in MIGRATED else HOME
        path = '/' if source == 'index.md' else old_path(source)
        report.append(f'| `{source}` | `{path}` | {destination} |')
    report += ['', '额外兼容仍被新版正文引用的 Hexo 地址：`/2020/05/02/ROC-AUC/` → `/blog/2020/roc-auc/`。']
    return {
        'articles.csv': csv_text(rows),
        'fallback.csv': csv_text(fallback),
        'coverage.md': '\n'.join(report) + '\n',
    }


if __name__ == '__main__':
    outputs = generate()
    # Regression: renamed slugs, consolidated books, root fallback, exact article matching.
    articles = dict((r[0], r[1]) for r in csv.reader(io.StringIO(outputs['articles.csv'])))
    assert articles['datahonor.com/blog/2024/12/28/2024_summary/'] == HOME + 'blog/2024/2024-summary/'
    assert articles['mathewshen.me/legacyblog/odyssey/llm/index.html'] == HOME + 'blog/2025/books/ai-llm-dl/'
    assert 'mathewshen.me/' not in articles
    assert 'datahonor.com/cs/os/ubuntu-usage/' not in articles
    assert all(row[5:] == ['FALSE', 'FALSE'] for row in csv.reader(io.StringIO(outputs['articles.csv'])))
    assert old_path('blog/posts/llm_kv_cache.md') == '/blog/2025/06/03/llm_kv_cache/'
    for name, content in outputs.items():
        output = Path(__file__).parent / name
        if '--check' in sys.argv:
            assert output.read_text() == content, f'Regenerate {output}'
        else:
            output.write_text(content)
    print(f'OK: {len(MIGRATED)} mappings, {len(articles)} exact redirects, 4 fallback entries')
