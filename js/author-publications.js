(function () {
  'use strict';

  const escapeHtml = value => String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

  const value = (row, keys) => {
    for (const key of keys) {
      if (row[key] !== undefined && row[key] !== null && String(row[key]).trim()) {
        return String(row[key]).trim();
      }
    }
    return '';
  };

  const normalizedAuthor = author => String(author || '')
    .replace(/[\s*†‡]+$/g, '')
    .trim()
    .toLowerCase();

  const hasAuthor = (row, authorName) => value(row, ['Authors', 'Column_4'])
    .split(',')
    .some(author => normalizedAuthor(author) === normalizedAuthor(authorName));

  const publicationNumber = row => Number(
    (value(row, ['Pub_ID', 'Column_0']).match(/\d+/g) || [0]).pop()
  );

  function statusBadge(row) {
    const status = value(row, ['Status', 'Column_14']);
    if (!status || /^published$/i.test(status)) return '';
    return `<span class="profile-publication-status">${escapeHtml(status)}</span>`;
  }

  function publicationItem(row) {
    const title = value(row, ['Title', 'Column_2']);
    const paper = value(row, ['Paper_Link', 'Column_5']);
    const venue = value(row, ['Venue_Name', 'Column_3']);
    const year = value(row, ['Year', 'Column_1']);
    const titleHtml = paper && paper !== '-'
      ? `<a href="${escapeHtml(paper)}" target="_blank" rel="noopener"><strong>${escapeHtml(title)}</strong></a>`
      : `<strong>${escapeHtml(title)}</strong>`;
    return `<li>${titleHtml}${statusBadge(row)}
      <small>${escapeHtml([venue, year].filter(Boolean).join(' · '))}</small>
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
          Number(value(b, ['Year', 'Column_1'])) - Number(value(a, ['Year', 'Column_1'])) ||
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
