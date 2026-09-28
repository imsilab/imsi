(function () {
  'use strict';

  const escapeHtml = value => String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

  const normalizedAuthor = author => String(author || '')
    .replace(/[\s*†‡]+$/g, '')
    .trim()
    .toLowerCase();

  const hasAuthor = (row, authorName) => String(row.authors || '')
    .split(',')
    .some(author => normalizedAuthor(author) === normalizedAuthor(authorName));

  const publicationNumber = row => Number(
    (String(row.id || '').match(/\d+/g) || [0]).pop()
  );

  function publicationItem(row) {
    const title = row.title;
    const venue = row.venue;
    const year = row.year;
    const actions = window.IMSI.Publications.actions(row)
      .filter(action => action.kind !== 'cite')
      .map(action => `<a href="${escapeHtml(action.url)}" target="_blank" rel="noopener">${escapeHtml(action.label)}</a>`)
      .join(' · ');
    return `<li><strong>${escapeHtml(title)}</strong>
      <small>${escapeHtml([venue, year].filter(Boolean).join(' · '))}</small>
      ${actions ? `<small class="profile-publication-actions">${actions}</small>` : ''}
    </li>`;
  }

  async function render(root) {
    const authorName = root.dataset.authorPublications || '';
    try {
      if (typeof getPublications !== 'function') {
        throw new Error('SheetServices is unavailable');
      }
      const rows = (await getPublications())
        .filter(row => hasAuthor(row, authorName))
        .sort((a, b) =>
          Number(b.year) - Number(a.year) ||
          publicationNumber(b) - publicationNumber(a)
        )
        .slice(0, 15);
      const emptyMessage = root.dataset.emptyMessage ||
        'No publications found in WEB_Publications.';
      root.innerHTML = rows.map(publicationItem).join('') ||
        `<li>${escapeHtml(emptyMessage)}</li>`;
    } catch (error) {
      console.error(`${authorName} publication load failed:`, error);
      root.innerHTML = '<li>Publication data is temporarily unavailable.</li>';
    }
  }

  function initialize() {
    if (!document.getElementById('profile-publication-styles')) {
      const style = document.createElement('style');
      style.id = 'profile-publication-styles';
      style.textContent = `
        .profile-publications { list-style: none; padding-left: 0; }
        .profile-publications li {
          border-bottom: 1px solid #e8e8e8;
          padding: .7rem 0;
        }
        .profile-publications li:last-child { border-bottom: 0; }
        .profile-publications small {
          color: #6c757d;
          display: block;
          margin-top: .2rem;
        }
        .profile-publications .profile-publication-actions a {
          font-weight: 600;
        }
        .profile-publication-status {
          background: #f57c00;
          border-radius: 4px;
          color: #fff;
          display: inline-block;
          font-size: .72em;
          font-weight: 700;
          margin-left: .5rem;
          padding: 2px 6px;
          vertical-align: middle;
        }
      `;
      document.head.appendChild(style);
    }
    document.querySelectorAll('[data-author-publications]').forEach(render);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})();
