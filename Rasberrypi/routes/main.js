
/*
 * GET home page.
 */

module.exports = function(app){
  app.get('/', function(req, res) {
  	res.render('index.html');
  });
  app.get('/error', function(req, res) {
  	res.render('error.html');
  });
  app.get('/index', function(req, res) {
  	res.render('index.html');
  });
};