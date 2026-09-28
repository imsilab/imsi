(function (root) {
  'use strict';

  const text = value => String(value == null ? '' : value).trim();

  function normalize(row) {
    const source = row || {};
    return {
      id: text(source.Pub_ID),
      year: text(source.Year),
      title: text(source.Title),
      venue: text(source.Venue_Name),
      authors: text(source.Authors),
      spacer: text(source.Spacer),
      projectUrl: text(source.Project_Link),
      gdriveUrl: text(source.GDrive_Link),
      arxivUrl: text(source.arXiv_Link),
      paperUrl: text(source.Paper_Link),
      venueUrl: text(source.Venue_Link),
      codeUrl: text(source.Code),
      modelUrl: text(source.Model),
      posterUrl: text(source.Poster_Link),
      slidesUrl: text(source.Slides_link),
      cite: text(source.Cite),
      inGoogleScholar: text(source['In Google Scholar']),
      citedAtLeastOnce: text(source['Cited at Least Once']),
      notes: text(source.Notes),
      remarks: text(source.Remarks),
      raw: source
    };
  }

  function actions(publication) {
    const item = publication || {};
    return [
      {kind: 'project', label: 'Project', url: text(item.projectUrl)},
      {kind: 'gdrive', label: 'GDrive', url: text(item.gdriveUrl)},
      {kind: 'arxiv', label: 'arXiv', url: text(item.arxivUrl)},
      {kind: 'paper', label: 'Paper', url: text(item.paperUrl)},
      {kind: 'venue', label: 'Venue', url: text(item.venueUrl)},
      {kind: 'code', label: 'Code', url: text(item.codeUrl)},
      {kind: 'model', label: 'Model', url: text(item.modelUrl)},
      {kind: 'poster', label: 'Poster', url: text(item.posterUrl)},
      {kind: 'slides', label: 'Slides', url: text(item.slidesUrl)},
      {kind: 'cite', label: 'Cite', url: text(item.cite)}
    ].filter(action => action.url);
  }

  function isLabPublication(publication) {
    return !/\bPERSONAL\b/i.test(text(publication && publication.remarks));
  }

  const api = {normalize, actions, isLabPublication};
  root.IMSI = root.IMSI || {};
  root.IMSI.Publications = api;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : window);
