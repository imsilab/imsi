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

const PEOPLE_COLUMNS = [
    'Person_ID', 'Category', 'Name_EN_FULL', 'Org_EN', 'Dept_EN', 'Sub_Org_EN',
    'Email_Paper', 'Education', 'Experience', 'Github', 'Blog', 'Linkedin',
    'Tags', 'PhotoUrl'
];

function normalizePersonName(value) {
    return String(value || '').trim().replace(/\s+/g, ' ').toLowerCase();
}

/**
 * Normalize WEB_People rows from either a canonical header or the current
 * malformed export, where the first person row became the gviz header.
 */
function normalizePeopleRows(rows) {
    if (!Array.isArray(rows) || rows.length === 0) return [];

    const first = rows[0] || {};
    const malformedShape = !Object.prototype.hasOwnProperty.call(first, 'Person_ID') &&
        Object.prototype.hasOwnProperty.call(first, 'P_0001') &&
        Object.prototype.hasOwnProperty.call(first, 'Professor') &&
        Object.prototype.hasOwnProperty.call(first, 'Name_EN_FULL') &&
        Object.prototype.hasOwnProperty.call(first, 'Column_0');

    const idWidth = String(rows.find(row => row?.Column_0)?.Column_0 || '').match(/^P_(\d+)$/i)?.[1]?.length || 4;

    return rows.map((row, rowIndex) => {
        if (malformedShape) {
            const normalized = {};
            PEOPLE_COLUMNS.forEach((field, index) => {
                normalized[field] = String(row?.[`Column_${index}`] ?? '').trim();
            });
            normalized._SheetPerson_ID = normalized.Person_ID;
            // The first roster row was consumed as the malformed header. The
            // relationship sheet still numbers people by physical roster row,
            // including rows whose visible ID cell is blank, so row position is
            // the only stable canonical ID across the offset transition.
            normalized.Person_ID = `P_${String(rowIndex + 1).padStart(idWidth, '0')}`;
            return normalized;
        }

        const normalized = {...row};
        PEOPLE_COLUMNS.forEach(field => {
            normalized[field] = String(normalized[field] ?? '').trim();
        });
        normalized._SheetPerson_ID = String(normalized._SheetPerson_ID || normalized.Person_ID || '').trim();
        return normalized;
    }).filter(person => {
        const isPseudoHeader = person.Name_EN_FULL === 'Name_EN_FULL' &&
            person.Org_EN === 'Org_EN' && person.Dept_EN === 'Dept_EN';
        return !isPseudoHeader && Boolean(person.Name_EN_FULL);
    });
}

function createPeopleLookup(people) {
    const lookup = {
        byId: new Map(),
        byShiftedId: new Map(),
        byName: new Map()
    };

    (people || []).forEach(person => {
        const id = String(person?.Person_ID || '').trim();
        const sheetId = String(person?._SheetPerson_ID || '').trim();
        const name = normalizePersonName(person?.Name_EN_FULL || person?.Name_KR);
        if (id && !lookup.byId.has(id)) lookup.byId.set(id, person);
        if (sheetId && sheetId !== id && !lookup.byShiftedId.has(sheetId)) {
            lookup.byShiftedId.set(sheetId, person);
        }
        if (name && !lookup.byName.has(name)) lookup.byName.set(name, person);
    });
    return lookup;
}

function resolveTeamPerson(membership, lookup) {
    if (!membership || !lookup) return null;
    const id = String(membership.Person_ID || membership.PersonID || '').trim();
    if (id && lookup.byId?.has(id)) return lookup.byId.get(id);
    if (id && lookup.byShiftedId?.has(id)) return lookup.byShiftedId.get(id);
    const name = normalizePersonName(membership.Name_EN_FULL || membership.Name_EN || membership.Name);
    return name && lookup.byName?.has(name) ? lookup.byName.get(name) : null;
}

// Wrapper functions for specific sheets
async function getPeople() {
    return normalizePeopleRows(await fetchSheetData('WEB_People'));
}

let publicationsPromise;
async function getPublications() {
    if (!publicationsPromise) {
        publicationsPromise = fetchSheetData('WEB_Publications');
    }
    return await publicationsPromise;
}

async function getProjects() {
    return await fetchSheetData('WEB_Projects');
}

let newsPromise;
async function getNews() {
    if (!newsPromise) {
        const sheetNewsPromise = fetchSheetData('WEB_NEWS');
        const localNewsPromise = fetch('/imsi/data/news-local.json', {cache: 'no-store'})
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .catch(error => {
                console.error('Local news load failed:', error);
                return [];
            });

        newsPromise = Promise.all([sheetNewsPromise, localNewsPromise])
            .then(([sheetNews, localNews]) => {
                const merged = new Map();
                [...sheetNews, ...localNews].forEach(item => {
                    const id = String(item?.News_ID || item?.Column_0 || '')
                        .trim()
                        .replace(/_/g, '-')
                        .toUpperCase();
                    if (id) merged.set(id, item);
                });
                return Array.from(merged.values());
            });
    }
    return await newsPromise;
}

async function getGallery() {
    return await fetchSheetData('WEB_Gallery');
}

async function getTeams() {
    return await fetchSheetData('DB_Teams');
}

let authorProfilesPromise;
async function getAuthorProfiles() {
    if (!authorProfilesPromise) {
        authorProfilesPromise = fetch('/imsi/data/author-profiles.json')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .catch(error => {
                console.error('Author profile map load failed:', error);
                return {};
            });
    }
    return await authorProfilesPromise;
}

if (typeof globalThis !== 'undefined') {
    globalThis.normalizePeopleRows = normalizePeopleRows;
    globalThis.createPeopleLookup = createPeopleLookup;
    globalThis.resolveTeamPerson = resolveTeamPerson;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        normalizePeopleRows,
        createPeopleLookup,
        resolveTeamPerson
    };
}
