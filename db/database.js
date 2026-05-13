const fs = require('fs');
const path = require('path');

let tables = {};

// ── helpers ──────────────────────────────────────────────

function applyParams(sql, params) {
  let i = 0;
  return sql.replace(/\?/g, () => {
    const v = params[i++];
    if (v === null) return 'NULL';
    if (typeof v === 'string') return `'${v.replace(/'/g, "''")}'`;
    return v;
  });
}

function coerce(v) {
  if (v === 'NULL') return null;
  if (v === 'true' || v === '1') return 1;
  if (v === 'false' || v === '0') return 0;
  const n = Number(v);
  return !isNaN(n) ? n : v.replace(/^['"]|['"]$/g, '');
}

function compare(a, op, b) {
  if (op === '=') return String(a ?? '') === String(b ?? '');
  if (op === '!=') return String(a ?? '') !== String(b ?? '');
  return true;
}

function parseWhere(whereClause, row, params = []) {
  if (!whereClause) return true;
  const parts = whereClause.split(/\s+and\s+/i).map(s => s.trim());
  const paramsCopy = [...params]; // Create a copy to avoid modifying original
  return parts.every(part => {
    const m = part.match(/(\w+)\s*([=!=<>]+)\s*(.+?)(?:\s+|$)/);
    if (!m) return true;
    const [, col, op, rawVal] = m;
    let val;
    if (rawVal === '?') {
      val = paramsCopy.shift();
    } else {
      val = coerce(rawVal.replace(/^['"]|['"]$/g, ''));
    }
    const rowVal = row[col];
    return compare(rowVal, op, val);
  });
}

function extractColumns(sql) {
  const colMatch = sql.match(/INSERT\s+INTO\s+\w+\s*\(([^)]+)\)/i);
  if (!colMatch) return [];
  return colMatch[1].split(',').map(s => s.trim());
}

function extractInsertValues(sql) {
  const match = sql.match(/VALUES\s*\((.+)\)/si);
  if (!match) return {};
  return match[1].split(',').map(s => s.trim()).map(v => {
    // Preserve question marks for parameter substitution
    if (v === '?') return '?';
    return coerce(v);
  });
}

// ── exec: CREATE / ALTER ─────────────────────────────────

function exec(sql, cb) {
  const lines = sql
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .split(';')
    .map(s => s.trim())
    .filter(Boolean);

  for (const stmt of lines) {
    const up = stmt.toUpperCase();

    if (up.startsWith('CREATE TABLE')) {
      const nameMatch = stmt.match(/CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)/i);
      if (nameMatch) {
        const name = nameMatch[1];
        const colsBlock = stmt.match(/\(([\s\S]+)\)/);
        if (colsBlock) {
          tables[name] = { columns: [], rows: [], nextId: 1 };

          const colDefs = colsBlock[1].split(',').map(d => d.trim()).filter(Boolean);
          colDefs.forEach(def => {
            const tokens = def.trim().split(/\s+/);
            const colName = tokens[0];
            const type = tokens[1] || 'TEXT';
            if (colName.toUpperCase() === 'FOREIGN' || colName.toUpperCase() === 'PRIMARY' || colName.toUpperCase() === 'UNIQUE' || colName.toUpperCase() === 'CHECK') return;
            tables[name].columns.push({ name: colName, type });
          });
        }
      }
    }
  }

  if (cb) cb(null, { lastID: 0, changes: 0 });
  return { lastID: 0, changes: 0 };
}

// ── run: INSERT / UPDATE / DELETE ────────────────────────

function run(sql, params, cb) {
  if (typeof params === 'function') { cb = params; params = []; }
  try {
    const up = sql.toUpperCase().trim();
    let result = { lastID: 0, changes: 0 };

    if (up.startsWith('INSERT INTO')) {
      const tableMatch = sql.match(/INSERT\s+INTO\s+(\w+)/i);
      const tableName = tableMatch[1];
      const cols = extractColumns(sql);
      let values = extractInsertValues(sql);

      if (!tables[tableName]) throw new Error(`Table ${tableName} does not exist`);

      // Substitute parameters in VALUES clause
      values = values.map(v => v === '?' ? params.shift() : v);

      // Auto-assign ID if not provided
      const hasId = cols.some(c => c.toLowerCase() === 'id');
      if (!hasId) {
        cols.unshift('id');
        values.unshift(tables[tableName].nextId);
        tables[tableName].nextId++;
      }

      const row = {};
      cols.forEach((c, i) => { row[c] = values[i]; });
      tables[tableName].rows.push({ ...row });
      result.lastID = row.id || 0;
      result.changes = 1;
    }
    else if (up.startsWith('UPDATE')) {
      const tableMatch = sql.match(/UPDATE\s+(\w+)/i);
      const tableName = tableMatch[1];
      const setMatch = sql.match(/SET\s+(.+?)(?:\s+WHERE|\s*$)/is);
      const whereMatch = sql.match(/WHERE\s+(.+?)(?:\s*$)/is);

      const setCols = setMatch ? setMatch[1].split(',').map(s => s.trim()).filter(Boolean) : [];
      
      // Separate params: first for SET, then for WHERE
      const setParamCount = setCols.filter(c => c.includes('?')).length;
      const setParams = params.slice(0, setParamCount);
      const whereParams = params.slice(setParamCount);

      let count = 0;
      for (const row of tables[tableName].rows) {
        if (!parseWhere(whereMatch?.[1] || null, row, whereParams)) continue;
        
        let setParamIndex = 0;
        setCols.forEach(expr => {
          const [k, v] = expr.split('=').map(s => s.trim());
          if (v === '?') {
            row[k] = setParams[setParamIndex++];
          } else {
            row[k] = coerce(v.replace(/^['"]|['"]$/g, ''));
          }
        });
        count++;
      }
      result.changes = count;
    }
    else if (up.startsWith('DELETE FROM')) {
      const tableMatch = sql.match(/DELETE\s+FROM\s+(\w+)/i);
      const tableName = tableMatch[1];
      const before = tables[tableName].rows.length;
      tables[tableName].rows = tables[tableName].rows.filter(row =>
        parseWhere(sql.match(/WHERE\s+(.+?)(?:\s*$)/is)?.[1] || null, row, params)
      );
      result.changes = before - tables[tableName].rows.length;
    }

    if (cb) {
      cb.call({ lastID: result.lastID, changes: result.changes }, null, result);
    }
    return result;
  } catch (err) {
    if (cb) cb(err, null);
    else throw err;
  }
}

// ── get / all: SELECT ────────────────────────────────────

function query(sql, params, one) {
  const trimmed = sql.replace(/\s+/g, ' ').trim();
  const upper = trimmed.toUpperCase();

  // Handle SELECT 1, SELECT sqlite_version(), etc. (no FROM clause)
  if (!upper.includes(' FROM ')) {
    const expr = trimmed.replace(/^select\s+/i, '').trim();
    // Simple expressions: "1", "sqlite_version()", "COUNT(1)"
    let result;
    const numMatch = expr.match(/^(\d+)$/);
    if (numMatch) {
      result = { [numMatch[1]]: Number(numMatch[1]) };
    } else {
      // For other expressions, just return a placeholder
      result = { [expr.replace(/[()]/g, '_').toLowerCase()]: null };
    }
    return result;
  }

  const tableMatch = sql.match(/SELECT\s+.+\s+FROM\s+(\w+)/i);
  if (!tableMatch) throw new Error(`Unknown table`);
  const tableName = tableMatch[1];
  const table = tables[tableName];
  if (!table) throw new Error(`Unknown table: ${tableName}`);

  const selectMatch = sql.match(/SELECT\s+(.+?)\s+FROM/si);
  const selected = selectMatch
    ? selectMatch[1].split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
    : ['*'];

  const whereContentMatch = sql.match(/WHERE\s+(.+)$/is);

  // Apply WHERE filtering with parameter substitution
  const rows = (table.rows || []).filter(row => {
    if (!whereContentMatch) return true;
    return parseWhere(whereContentMatch[1], row, params);
  });

  const projectRow = (r) => {
    if (selected.includes('*')) return { ...r };
    const out = {};
    selected.forEach(col => {
      if (col.includes('(')) {
        const aliasMatch = col.match(/(\w+)\s+AS\s+(\w+)/i);
        if (aliasMatch) out[aliasMatch[2]] = r[aliasMatch[1]];
      } else {
        out[col] = r[col];
      }
    });
    return out;
  };

  if (one) return rows.length === 0 ? null : projectRow(rows[0]);
  return rows.map(projectRow);
}

function all(sql, params, cb) {
  // Handle both all(sql, [params], cb) and all(sql, cb) signatures
  if (typeof params === 'function') {
    cb = params;
    params = [];
  } else if (typeof cb === 'function' && !Array.isArray(params)) {
    params = [];
  }
  try {
    // Create a copy of params to avoid modifying the original array
    const paramsCopy = [...params];
    const result = query(sql, paramsCopy, false);
    if (cb) cb(null, result);
    return result;
  } catch (err) {
    if (cb) cb(err, null);
    else throw err;
  }
}

function get(sql, params, cb) {
  // Handle both get(sql, [params], cb) and get(sql, cb) signatures
  if (typeof params === 'function') {
    cb = params;
    params = [];
  } else if (typeof cb === 'function' && !Array.isArray(params)) {
    params = [];
  }
  try {
    // Create a copy of params to avoid modifying the original array
    const paramsCopy = [...params];
    const result = query(sql, paramsCopy, true);
    if (cb) cb(null, result);
    return result;
  } catch (err) {
    if (cb) cb(err, null);
    else throw err;
  }
}

// ── public API ───────────────────────────────────────────

// Initialize DB with schema
function initDB() {
  const schemaPath = path.join(__dirname, 'schema.sql');
  if (fs.existsSync(schemaPath)) {
    const schema = fs.readFileSync(schemaPath, 'utf8');
    exec(schema);
  }
}

initDB();

module.exports = {
  db: { exec, run, get, all },
  _clear: () => {
    tables = {};
    initDB();
  },
};
