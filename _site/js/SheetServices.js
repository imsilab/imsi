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

        const rows = json.table.rows;
        if (!rows || rows.length === 0) return [];

        // Use the first row as headers (Labels)
        const headers = rows[0].c.map(cell => cell?.v || '');

        // Process data from the second row onwards
        return rows.slice(1).map(row => {
            const item = {};
            row.c.forEach((cell, index) => {
                const label = headers[index] || `Column_${index}`;
                item[label] = cell?.v || '';
            });
            return item;
        });
    } catch (e) {
        console.error(`${sheetName} 데이터 로드 실패:`, e);
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