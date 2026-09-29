(function () {
  'use strict';

  const value = (row, keys) => {
    const key = keys.find(candidate => row[candidate] != null && String(row[candidate]).trim());
    return key ? String(row[key]).trim() : '';
  };
  const escapeHtml = text => String(text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const normalizeId = text => String(text || '').trim().replace(/_/g, '-').toUpperCase();

  function inline(text) {
    const pattern = /\[([^\]]+)\]\(((?:https?:\/\/|\/)[^\s)]+)\)/g;
    let output = '';
    let cursor = 0;
    let match;
    while ((match = pattern.exec(String(text || ''))) !== null) {
      output += escapeHtml(String(text).slice(cursor, match.index));
      const download = /(?:export=download|\/export\?format=)/i.test(match[2]);
      output += `<a href="${escapeHtml(match[2])}" target="_blank" rel="noopener"${download ? ' class="news-download"' : ''}>${escapeHtml(match[1])}</a>`;
      cursor = match.index + match[0].length;
    }
    return output + escapeHtml(String(text || '').slice(cursor));
  }

  function formatContent(content) {
    const html = [];
    let list = '';
    const close = () => { if (list) html.push(`</${list}>`); list = ''; };
    String(content || '').trim().split(/\r?\n/).forEach(raw => {
      const line = raw.trim();
      if (!line) { close(); return; }
      const heading = line.match(/^(#{2,3})\s+(.+)$/);
      if (heading) { close(); html.push(`<h${heading[1].length}>${inline(heading[2])}</h${heading[1].length}>`); return; }
      const bullet = line.match(/^[-*]\s+(.+)$/);
      const numbered = line.match(/^\d+\.\s+(.+)$/);
      if (bullet || numbered) {
        const next = bullet ? 'ul' : 'ol';
        if (list !== next) { close(); list = next; html.push(`<${list}>`); }
        html.push(`<li>${inline((bullet || numbered)[1])}</li>`);
        return;
      }
      close();
      html.push(`<p>${inline(line)}</p>`);
    });
    close();
    return html.join('');
  }

  function formatDate(raw) {
    const parsed = new Date(String(raw || '').replace(/\./g, '-').replace(/\//g, '-'));
    return Number.isNaN(parsed.getTime()) ? String(raw || '') : parsed.toLocaleDateString('ko-KR', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
  }

  async function renderNewsDetail() {
    const loading = document.querySelector('[data-news-loading]');
    const article = document.querySelector('[data-news-article]');
    const title = document.querySelector('[data-news-title]');
    const date = document.querySelector('[data-news-date]');
    const content = document.querySelector('[data-news-content]');
    const match = location.pathname.match(/\/news\/([^/]+)/i);
    const currentId = normalizeId(match && decodeURIComponent(match[1]));
    try {
      const rows = typeof getNews === 'function' ? await getNews() : [];
      const row = rows.find(item => normalizeId(value(item, ['News_ID', 'news_id', 'Column_0'])) === currentId);
      if (!row) throw new Error('News item not found');
      const headline = value(row, ['Title', 'title', 'Column_1']);
      title.textContent = headline;
      date.textContent = formatDate(value(row, ['Date', 'date', 'Column_2']));
      content.innerHTML = formatContent(value(row, ['Content', 'content', 'Column_3']));
      document.title = `${headline} | IMSI Lab`;
    } catch (error) {
      title.textContent = 'News';
      content.innerHTML = '<p>Unable to load this news item right now.</p>';
      console.error('Failed to render news detail:', error);
    } finally {
      loading.classList.add('news-hidden');
      article.classList.remove('news-hidden');
    }
  }

  document.addEventListener('DOMContentLoaded', renderNewsDetail);
})();
