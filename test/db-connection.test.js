const { db } = require('../server');

test('DB connection', async () => {
  const result = await new Promise((resolve, reject) => {
    db.get('SELECT 1', (err, row) => {
      err ? reject(err) : resolve(row);
    });
  });
  expect(result).toEqual({ '1': 1 });
});