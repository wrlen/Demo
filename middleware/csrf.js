/**
 * CSRF Protection Middleware
 */

const csrf = require('csurf');

module.exports = function csrfMiddleware(req, res, next) {
  if (process.env.NODE_ENV === 'test') {
    return next();
  }
  return csrf({ cookie: true })(req, res, next);
};
