const sheetId = '1nr8EWtSU3Y50oK7oeKvwIZ1tHBUMmOhiSjtFYYufSYI';
const baseUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:json`;

async function getPeople() {
    try {
        const response = await fetch(`${baseUrl}&sheet=WEB_People`);
        const text = await response.text();
        const json = JSON.parse(text.substring(text.indexOf('{'), text.lastIndexOf('}') + 1));

        const rows = json.table.rows;
        if (!rows || rows.length === 0) return [];

        // 첫 번째 행을 헤더(Labels)로 사용
        const headers = rows[0].c.map(cell => cell?.v || '');

        // 두 번째 행부터 데이터로 처리
        return rows.slice(1).map(row => {
            const item = {};
            row.c.forEach((cell, index) => {
                const label = headers[index] || `Column_${index}`;
                item[label] = cell?.v || '';
            });
            return item;
        });
    } catch (e) {
        console.error("데이터 로드 실패:", e);
        return [];
    }
}
