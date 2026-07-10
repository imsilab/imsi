(function () {
  let citeBlobUrl = null;

  function escapeBibValue(value) {
    return String(value || '')
      .replace(/\\/g, '\\\\')
      .replace(/{/g, '\\{')
      .replace(/}/g, '\\}')
      .replace(/\r?\n/g, ' ')
      .trim();
  }

  function buildSimpleBib({ title, authors, year }) {
    return [
      '@article{',
      `  title={${escapeBibValue(title)}},`,
      `  author={${escapeBibValue(authors)}},`,
      `  year={${escapeBibValue(year)}}`,
      '}',
      ''
    ].join('\n');
  }

  function attachCitationModal(citeText) {
    const modal = document.getElementById('modal');
    if (!modal || typeof window.jQuery === 'undefined') return;

    const $ = window.jQuery;
    const $modal = $(modal);
    const $code = $modal.find('.modal-body code');
    const $download = $modal.find('.js-download-cite');
    const $trigger = $('.js-cite-modal');

    $code.text(citeText);

    if (citeBlobUrl) {
      URL.revokeObjectURL(citeBlobUrl);
      citeBlobUrl = null;
    }
    citeBlobUrl = URL.createObjectURL(new Blob([citeText], { type: 'text/plain;charset=utf-8' }));

    $download.attr('href', citeBlobUrl);
    $download.attr('download', 'cite.bib');

    $trigger.off('click').on('click', function (event) {
      event.preventDefault();
      $modal.modal('show');
    });
  }

  function ensureSkeletonStyles() {
    if (document.getElementById('pub-sheet-skeleton-style')) return;
    const style = document.createElement('style');
    style.id = 'pub-sheet-skeleton-style';
    style.textContent = `
      .publication-loading-hidden {
        display: none;
      }
      #pub-sheet-skeleton {
        max-width: 980px;
        margin: 4.25rem auto 2rem;
        padding: 0 1rem;
      }
      #pub-sheet-skeleton .sheet-status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 700;
        font-size: 1rem;
        color: #1f3b77;
        margin-bottom: 0.75rem;
      }
      #pub-sheet-skeleton .sheet-status .status-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: auto;
        height: auto;
        padding: 0;
        gap: 0.22rem;
        color: #2f5fbe;
        font-size: 0.9rem;
        line-height: 1;
      }
      #pub-sheet-skeleton .sheet-board {
        border: 1px solid #d9e2f1;
        border-radius: 10px;
        background: #ffffff;
        padding: 12px;
        box-shadow: 0 8px 26px rgba(16, 35, 86, 0.08);
      }
      #pub-sheet-skeleton .sheet-row {
        display: grid;
        grid-template-columns: 0.55fr 0.8fr 1.55fr 1fr 1.2fr;
        gap: 8px;
        margin-bottom: 8px;
        opacity: 0;
        transform: translateY(5px);
        animation: sheet-row-in 0.4s ease forwards;
      }
      #pub-sheet-skeleton .sheet-row:last-child {
        margin-bottom: 0;
      }
      #pub-sheet-skeleton .sheet-row:nth-child(1) { animation-delay: 0.05s; }
      #pub-sheet-skeleton .sheet-row:nth-child(2) { animation-delay: 0.14s; }
      #pub-sheet-skeleton .sheet-row:nth-child(3) { animation-delay: 0.23s; }
      #pub-sheet-skeleton .sheet-row:nth-child(4) { animation-delay: 0.32s; }
      #pub-sheet-skeleton .sheet-row:nth-child(5) { animation-delay: 0.41s; }
      #pub-sheet-skeleton .sheet-row:nth-child(6) { animation-delay: 0.50s; }
      #pub-sheet-skeleton .sheet-cell {
        height: 14px;
        border-radius: 5px;
        background: linear-gradient(90deg, #e9eef8 20%, #f8fbff 50%, #e9eef8 80%);
        background-size: 200% 100%;
        animation: sheet-shimmer 1.35s linear infinite;
      }
      #pub-sheet-skeleton .sheet-row.is-header .sheet-cell {
        height: 12px;
        background: linear-gradient(90deg, #d3dff3 20%, #ecf3ff 50%, #d3dff3 80%);
        background-size: 200% 100%;
      }
      #pub-sheet-skeleton .sheet-cell.wide {
        grid-column: span 2;
      }
      @keyframes sheet-shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
      }
      @keyframes sheet-row-in {
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      @media (max-width: 768px) {
        #pub-sheet-skeleton {
          margin-top: 3.25rem;
        }
        #pub-sheet-skeleton .sheet-row {
          grid-template-columns: 1fr 1fr;
        }
        #pub-sheet-skeleton .sheet-cell.wide {
          grid-column: span 2;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function showSkeleton(article) {
    if (!article) return null;
    ensureSkeletonStyles();
    article.classList.add('publication-loading-hidden');

    const skeleton = document.createElement('section');
    skeleton.id = 'pub-sheet-skeleton';
    skeleton.innerHTML = `
      <p class="sheet-status"><span class="status-icon" aria-hidden="true">&#10024;</span><span>Synchronizing...</span></p>
      <div class="sheet-board">
        <div class="sheet-row is-header">
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell wide"></div>
          <div class="sheet-cell"></div>
        </div>
        <div class="sheet-row">
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell wide"></div>
          <div class="sheet-cell"></div>
        </div>
        <div class="sheet-row">
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell wide"></div>
        </div>
        <div class="sheet-row">
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell wide"></div>
          <div class="sheet-cell"></div>
        </div>
        <div class="sheet-row">
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell"></div>
          <div class="sheet-cell wide"></div>
        </div>
      </div>
    `;

    article.parentNode.insertBefore(skeleton, article);
    return skeleton;
  }

  function hideSkeleton(article, skeleton) {
    if (skeleton && skeleton.parentNode) {
      skeleton.parentNode.removeChild(skeleton);
    }
    if (article) {
      article.classList.remove('publication-loading-hidden');
    }
  }

  function getValue(row, keys) {
    for (const key of keys) {
      if (row[key] !== undefined && row[key] !== null && String(row[key]).trim() !== '') {
        return String(row[key]).trim();
      }
    }
    return '';
  }

  function normalizePubId(value) {
    return String(value || '')
      .trim()
      .toUpperCase()
      .replace(/[-_]/g, '');
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function getCurrentPublicationId() {
    const parts = window.location.pathname.split('/').filter(Boolean);
    const publicationIndex = parts.findIndex((part) => part.toLowerCase() === 'publication');
    if (publicationIndex < 0 || !parts[publicationIndex + 1]) return '';
    return parts[publicationIndex + 1];
  }

  function setTextById(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  function setHtmlById(id, html) {
    const element = document.getElementById(id);
    if (element) {
      element.innerHTML = html;
    }
  }

  async function renderPublicationDetail() {
    if (typeof getPublications !== 'function') return;
    const article = document.querySelector('article.article-publication');
    const skeleton = showSkeleton(article);

    try {
      const currentPublicationId = getCurrentPublicationId();
      if (!currentPublicationId) return;

      const rows = await getPublications();
      if (!Array.isArray(rows) || rows.length === 0) return;

      const targetKey = normalizePubId(currentPublicationId);
      const row = rows.find((item) => {
        const pubId = getValue(item, ['Pub_ID', 'Pub ID', 'pub_id', 'Column_0']);
        return normalizePubId(pubId) === targetKey;
      });

      if (!row) return;

      const title = getValue(row, ['Title', 'title', 'Column_2']);
      const year = getValue(row, ['Year', 'year', 'Column_1']);
      const authors = getValue(row, ['Authors', 'authors', 'Column_4']);
      const paperLink = getValue(row, ['Paper_Link', 'Paper Link', 'paper_link', 'Column_5']);
      const venueName = getValue(row, ['Venue_Name', 'Venue Name', 'venue_name', 'Column_3']);
      const venueLink = getValue(row, ['Venue_Link', 'Venue Link', 'venue_link', 'Column_6']);
      const notes = getValue(row, ['Notes', 'notes', 'Column_7']);
      const citeText = getValue(row, ['Cite', 'cite', 'Citation', 'citation', 'BibTeX', 'Bibtex', 'bibtex', 'Column_11']);

      if (title) {
        setTextById('pub-title', title);
        document.title = `${title} | IMSI Research Lab`;
      }

      if (authors) {
        setTextById('pub-authors', authors);
      }

      if (year) {
        setTextById('pub-year', year);
      }

      const pdfLinkElement = document.getElementById('pub-pdf-link');
      if (pdfLinkElement && paperLink) {
        pdfLinkElement.setAttribute('href', paperLink);
        pdfLinkElement.setAttribute('target', '_blank');
        pdfLinkElement.setAttribute('rel', 'noopener');
      }

      if (notes) {
        setTextById('pub-abstract', notes);
      }

      if (venueName) {
        if (venueLink) {
          setHtmlById(
            'pub-venue',
            `<em><a href="${escapeHtml(venueLink)}" target="_blank" rel="noopener">${escapeHtml(venueName)}</a></em>`
          );
        } else {
          setHtmlById('pub-venue', `<em>${escapeHtml(venueName)}</em>`);
        }
      }

      attachCitationModal(citeText || buildSimpleBib({ title, authors, year }));
    } finally {
      hideSkeleton(article, skeleton);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    renderPublicationDetail().catch(function (error) {
      console.error('Failed to render publication detail from sheet:', error);
    });
  });
})();
