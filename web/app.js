// This is my index.js file //

const express = require('express');
const app = express();
const ejs = require('ejs');
const path = require('path');

// Set EJS as the view engine
app.set('view engine', 'ejs');

// Set the views directory
app.set('views', path.join(__dirname, 'pages'));

// Serve static files from the "public" directory
app.use(express.static(path.join(__dirname, 'public')));

// Require the mysql-netify.js file
const { handleNetifyRequest, connectToMySQL } = require('./js/mysql-netify');

// Define a route to retrieve data
app.get('/netify', handleNetifyRequest);

// Define a route for the dashboard page
app.get('/dashboard', (req, res) => {
  res.render('dashboard');
});

// Define a route for the devices page
app.get('/devices', (req, res) => {
  res.render('devices');
});

// Define a route handler for the root path
app.get('/', (req, res) => {
  res.redirect('/netify'); // Redirect to the dashboard page by default
});

// Start the server
app.listen(3000, () => {
  console.log('Server is running on http://localhost:3000');
});

// Connect to MySQL server
connectToMySQL();
