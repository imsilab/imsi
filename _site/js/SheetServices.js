const sheetId = '1nr8EWtSU3Y50oK7oeKvwIZ1tHBUMmOhiSjtFYYufSYI';
const baseUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:json`;

async function getPeople() {
  return await fetchSheetData('WEB_People');
}

async function fetchSheetData(sheetName) {
  try {
    const url = `${baseUrl}&sheet=${sheetName}`;
    const response = await fetch(url);
    const text = await response.text();
    const json = JSON.parse(text.substring(text.indexOf('{'), text.lastIndexOf('}') + 1));

    const rows = json.table.rows;
    if (!rows || !rows.length) return [];

    // Use row 0 as headers
    const headers = rows[0].c.map(cell => (cell && cell.v !== null) ? cell.v : '');

    // Data from row 1
    return rows.slice(1).map(row => {
      const item = {};
      row.c.forEach((cell, i) => {
        const key = headers[i] || `col_${i}`;
        item[key] = (cell && cell.v !== null) ? cell.v : '';
      });
      return item;
    });
  } catch (err) {
    console.error(`Error fetching sheet [${sheetName}]:`, err);
    return [];
  }
}
