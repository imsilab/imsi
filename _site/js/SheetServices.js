const sheetId = '1nr8EWtSU3Y50oK7oeKvwIZ1tHBUMmOhiSjtFYYufSYI';
const baseUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:json`;

/**
 * Generic function to fetch and parse Google Sheet data
 * @param {string} sheetName - The name of the tab in the spreadsheet
 */
async function fetchSheetData(sheetName) {
    try {
        const response = await fetch(`${baseUrl}&sheet=${sheetName}`);
        const text = await response.text();
        const json = JSON.parse(text.substring(text.indexOf('{'), text.lastIndexOf('}') + 1));

        const table = json.table || {};
        const cols = table.cols || [];
        const rows = table.rows || [];
        if (rows.length === 0) return [];

        // Prefer gviz column labels. Fallback to first-row headers only when labels are absent.
        let headers = cols.map((col, index) => {
            const label = String(col?.label || '').trim();
            return label || `Column_${index}`;
        });
        let dataRows = rows;

        const hasNamedHeaders = headers.some(h => !/^Column_\d+$/.test(h));
        if (!hasNamedHeaders) {
            const firstRowCells = rows[0]?.c || [];
            headers = firstRowCells.map((cell, index) => {
                const label = String(cell?.v || '').trim();
                return label || `Column_${index}`;
            });
            dataRows = rows.slice(1);
        }

        return dataRows.map(row => {
            const item = {};
            const cells = row?.c || [];
            const maxLen = Math.max(headers.length, cells.length);

            for (let index = 0; index < maxLen; index += 1) {
                const label = headers[index] || `Column_${index}`;
                const value = cells[index]?.v || '';
                item[label] = value;
                item[`Column_${index}`] = value;
            }
            return item;
        });
    } catch (e) {
        console.error(`${sheetName} data load failed:`, e);
        return [];
    }
}

// Wrapper functions for specific sheets
async function getPeople() {
    return await fetchSheetData('WEB_People');
}

async function getPublications() {
    return await fetchSheetData('WEB_Publications');
}

async function getProjects() {
    return await fetchSheetData('WEB_Projects');
}

async function getNews() {
    return await fetchSheetData('WEB_NEWS');
}
