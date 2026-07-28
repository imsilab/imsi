(function () {
  'use strict';

  const sheetUrl =
    'https://docs.google.com/spreadsheets/d/1nr8EWtSU3Y50oK7oeKvwIZ1tHBUMmOhiSjtFYYufSYI/gviz/tq';

  const validUrl = value => {
    const url = String(value || '').trim();
    return /^https?:\/\//i.test(url) ? url : '';
  };

  function parseGoogleVisualization(text) {
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start < 0 || end < start) throw new Error('Invalid Google Sheets response');
    const payload = JSON.parse(text.slice(start, end + 1));
    if (payload.status && payload.status !== 'ok') {
      throw new Error('Google Sheets query failed');
    }
    const table = payload.table || {};
    const headers = (table.cols || []).map((column, index) =>
      String(column.label || `Column_${index}`).trim()
    );
    return (table.rows || []).map(row => {
      const result = {};
      const cells = row.c || [];
      headers.forEach((header, index) => {
        const cell = cells[index];
        result[header] = cell && cell.v != null ? cell.v : '';
      });
      return result;
    });
  }

  function socialItem(url, label, iconClass) {
    const item = document.createElement('li');
    const anchor = document.createElement('a');
    const icon = document.createElement('i');
    anchor.href = url;
    anchor.target = '_blank';
    anchor.rel = 'noopener';
    anchor.setAttribute('aria-label', label);
    icon.className = `${iconClass} big-icon`;
    anchor.appendChild(icon);
    item.appendChild(anchor);
    return item;
  }

  function updateSocialLinks(person) {
    const profile = document.getElementById('profile');
    if (!profile) return;

    let list = profile.querySelector('.network-icon');
    if (!list) {
      list = document.createElement('ul');
      list.className = 'network-icon';
      list.setAttribute('aria-hidden', 'false');
      profile.appendChild(list);
    }

    list.querySelectorAll('li').forEach(item => {
      if (item.querySelector('.fa-github, .fa-globe')) item.remove();
    });

    const github = validUrl(person && person.Github);
    const homepage = validUrl(person && person.Homepage);
    if (github) {
      list.appendChild(socialItem(github, 'GitHub', 'fab fa-github'));
    }
    if (homepage) {
      list.appendChild(socialItem(homepage, 'Personal homepage', 'fas fa-globe'));
    }
    if (!list.children.length) list.remove();
  }

  async function initialize() {
    const name = document.querySelector('#profile .portrait-title h2');
    if (!name) return;
    try {
      const query = new URLSearchParams({
        tqx: `out:json;reqId:${Date.now()}`,
        sheet: 'DB_People',
        headers: '1'
      });
      const response = await fetch(`${sheetUrl}?${query}`, {cache: 'no-store'});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const rows = parseGoogleVisualization(await response.text());
      const profileName = name.textContent.trim().toLowerCase();
      const person = rows.find(row =>
        String(row.Name_EN_FULL || '').trim().toLowerCase() === profileName
      );
      updateSocialLinks(person || null);
    } catch (error) {
      console.error('Profile social links could not be refreshed:', error);
    }
  }

  initialize();
})();
