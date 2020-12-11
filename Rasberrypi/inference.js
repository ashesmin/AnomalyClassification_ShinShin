var express = require('express'),
    http = require('http'),
    path = require('path'),
    fs = require('fs');

var app = express();
var router = require('./routes/main')(app);


var bodyParser = require('body-parser');
var methodOverride = require('method-override');
var logger = require('morgan');
var errorHandler = require('errorhandler');
var multipart = require('connect-multiparty')
var multipartMiddleware = multipart();

var pyshell =  require('python-shell');

// all environments
//app.set('port', process.env.PORT || 8080);
app.set('port', 80);
app.set('views', __dirname + '/views');
app.set('view engine', 'ejs');
app.engine('html', require('ejs').renderFile);
app.use(logger('dev'));
app.use(bodyParser.urlencoded({
    extended: true
}));
app.use(bodyParser.json());
app.use(methodOverride());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/style', express.static(path.join(__dirname, '/views/style')));

// list of users
var sender;
var receiver;
global.sender = sender;
global.receiver = receiver;

var WebSocketServer = require('ws').Server;
var wss = new WebSocketServer( { port: 8100 } );

var options = {
    mode: 'text',
    pythonPath: '',
    scriptPath: ''
}

// check if connection is established
wss.on('connection', function(ws) {
    // console.log(ws);

    ws.on('message', function(message) {
        // console.log('received: %s', message);

        if (message == 'web') {
            pyshell.PythonShell.run('shinshin.py', options, function (err, results){
                if (err) throw err;
            });

            receiver = ws;
        } else if(message == 'python') {
            sender = ws;
        } else {
            receiver.send(message);
            sender.send('ack');
        }
    });

    ws.on('close', function() {
        console.log('closed');
        sender.send('closed');
    });
});

http.createServer(app).listen(app.get('port'), '0.0.0.0', function() {
    console.log('Express server listening on port ' + app.get('port'));
});