const sheetId = '1nr8EWtSU3Y50oK7oeKvwIZ1tHBUMmOhiSjtFYYufSYI';
const baseUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:json`;

async function getPeople() {
    try {
        const response = await fetch(`${baseUrl}&sheet=WEB_People`);
        const text = await response.text();
        const json = JSON.parse(text.substring(text.indexOf('{'), text.lastIndexOf('}') + 1));

        return json.table.rows.slice(1).map(row => ({
            id: row.c[0]?.v || '',
            category: row.c[1]?.v || '',
            name: row.c[2]?.v || '',
            dept: row.c[4]?.v || '',
            email: row.c[6]?.v || '',
            github: row.c[9]?.v || '',
            photoUrl: row.c[13]?.v || ''
        }));
    } catch (e) {
        console.error("데이터 로드 실패:", e);
        return [];
    }
}
