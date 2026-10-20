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

  function isTrustedRichContentUrl(url) {
    return /^\/imsi\/data\/news-assets\/[a-z0-9][a-z0-9._/-]*\.html$/i.test(url)
      && !url.includes('..');
  }

  function isSafeRichContentUrl(rawUrl, allowFragment) {
    const candidate = String(rawUrl || '').trim();
    if (allowFragment && /^#[A-Za-z][\w:.-]*$/.test(candidate)) return true;
    try {
      const parsed = new URL(candidate, location.origin);
      return ['http:', 'https:', 'mailto:'].includes(parsed.protocol);
    } catch (_error) {
      return false;
    }
  }

  function sanitizeRichContent(root) {
    const allowedTags = new Set([
      'a', 'b', 'blockquote', 'br', 'code', 'details', 'div', 'em', 'h1', 'h2', 'h3',
      'hr', 'li', 'ol', 'p', 'pre', 'strong', 'summary', 'table', 'tbody', 'td', 'th',
      'thead', 'tr', 'ul'
    ]);
    const allowedAttributes = new Set(['class', 'data-guide', 'href', 'id', 'rel', 'style', 'target']);
    const allowedStyles = new Set([
      '-webkit-overflow-scrolling', 'background', 'border', 'border-bottom', 'border-collapse',
      'border-left', 'border-radius', 'border-top', 'box-sizing', 'color', 'cursor', 'display',
      'font-family', 'font-size', 'font-style', 'font-weight', 'gap', 'grid-template-columns',
      'letter-spacing', 'line-height', 'list-style', 'margin', 'margin-bottom', 'max-width',
      'min-width', 'overflow-wrap', 'overflow-x', 'overflow-y', 'padding', 'padding-left',
      'tab-size', 'text-align', 'text-decoration', 'text-underline-offset', 'vertical-align',
      'white-space', 'width', 'word-break'
    ]);
    const blocked = 'script, iframe, object, embed, style, link, meta, base, svg, math, form, input, button, select, textarea';
    root.querySelectorAll(blocked).forEach(node => node.remove());
    [root, ...root.querySelectorAll('*')].forEach(node => {
      if (!allowedTags.has(node.tagName.toLowerCase())) {
        node.replaceWith(...node.childNodes);
        return;
      }
      [...node.attributes].forEach(attribute => {
        const name = attribute.name.toLowerCase();
        if (!allowedAttributes.has(name)) {
          node.removeAttribute(attribute.name);
          return;
        }
        if (name === 'href' && !isSafeRichContentUrl(attribute.value, true)) {
          node.removeAttribute(attribute.name);
          return;
        }
        if (name === 'style') {
          const properties = Array.from({length: node.style.length}, (_unused, index) => node.style.item(index));
          properties.forEach(property => {
            const styleValue = node.style.getPropertyValue(property);
            const unsafeValue = /(?:url|image-set|cross-fade|element|paint|expression)\s*\(|@import|-moz-binding|behavior\s*:/i.test(styleValue);
            if (!allowedStyles.has(property) || unsafeValue) node.style.removeProperty(property);
          });
          if (!node.style.cssText.trim()) node.removeAttribute('style');
        }
      });
    });
    return root;
  }

  async function appendRichContent(container, url) {
    if (!url) return;
    if (!isTrustedRichContentUrl(url)) throw new Error('Untrusted news content URL');

    const response = await fetch(url, {cache: 'no-store'});
    if (!response.ok) throw new Error(`Rich news content HTTP ${response.status}`);
    const documentFragment = new DOMParser().parseFromString(await response.text(), 'text/html');
    const guide = documentFragment.querySelector('[data-guide="alphagpu-2026"]');
    if (!guide) throw new Error('Rich news guide root was not found');
    sanitizeRichContent(guide);
    guide.querySelector('h1')?.remove();
    guide.classList.add('news-rich-guide');
    guide.querySelectorAll('a[target="_blank"]').forEach(link => {
      link.setAttribute('rel', 'noopener noreferrer');
    });
    container.appendChild(document.importNode(guide, true));
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
      const richContentUrl = value(row, ['Content_HTML_URL', 'content_html_url']);
      if (richContentUrl) {
        try {
          await appendRichContent(content, richContentUrl);
        } catch (richContentError) {
          console.error('Failed to load rich news content:', richContentError);
          content.insertAdjacentHTML('beforeend', '<p class="news-rich-error">상세 가이드를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</p>');
        }
      }
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

  globalThis.IMSI = globalThis.IMSI || {};
  globalThis.IMSI.NewsDetail = Object.freeze({sanitizeRichContent});
  document.addEventListener('DOMContentLoaded', renderNewsDetail);
})();
