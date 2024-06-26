// This is my mysql-netify.js file

const mysql = require('mysql2');

ROUTER_IP: process.env.ROUTER_IP || '10.0.3.1'

// MySQL config via envVars or static if envvars not found. 
const connectionConfig = {
  host: process.env.MYSQL_HOST || '10.0.5.5',
  port: process.env.MYSQL_PORT || '3306', // Parse port as integer
  user: process.env.MYSQL_USER || 'netify',
  password: process.env.MYSQL_PASSWORD || 'netify',
  database: process.env.MYSQL_DB || 'netifyDB',
};

let connection;

// Connect to the MySQL server
function connectToMySQL() {
  connection = mysql.createConnection(connectionConfig);

  connection.connect((err) => {
    if (err) {
      console.error(`Error connecting to MySQL server at ${connectionConfig.host}:${connectionConfig.port}:`, err);
      setTimeout(connectToMySQL, 1000); // Retry connection every 1 second
      return;
    }
    console.log(`Connected to MySQL server at ${connectionConfig.host}:${connectionConfig.port}`);
  });

  // Handle connection errors
  connection.on('error', (err) => {
    if (err.code === 'PROTOCOL_CONNECTION_LOST') {
      console.error('MySQL connection lost to ${connectionConfig.host}:${connectionConfig.port}. Reconnecting...');
      connectToMySQL();
    }
  });
}

// Handle the netify route request
function handleNetifyRequest(req, res) {
  const timeframeOptions = [
    { label: '1 mins', value: '1m' },    
    { label: '5 mins', value: '5m' },
    { label: '15 mins', value: '15m' },
    { label: '30 mins', value: '30m' },
    { label: '1 hour', value: '60m' },
    { label: '6 hours', value: '360m' },
    { label: '12 hours', value: '720m' },
    { label: '24 hours', value: '1404m' },
  ];

  const queryProtocols = `
    SELECT DISTINCT detected_protocol_name
    FROM netify_flow
    WHERE timeinsert >= NOW() - INTERVAL ? MINUTE
    ORDER BY detected_protocol_name;`;

  const queryResults = `
    SELECT timeinsert, hostname, local_ip, local_port, fqdn, dest_ip, dest_port, dest_type, detected_protocol_name, interface, dest_country, dest_state, dest_city
    FROM netify_flow
    WHERE detected_protocol_name like ? AND timeinsert >= NOW() - INTERVAL ? MINUTE
    ORDER BY timeinsert DESC;`;

  const selectedTimeframe = req.query.timeframe || '1m';
  const selectedHostname = req.query.hostname || '';
  const selectedProtocol = req.query.protocol || '';
  const selectedFqdn = req.query.fqdn || '';

  // Execute the query to fetch available protocols
  connection.query(queryProtocols, [selectedTimeframe], (err, protocolResults) => {
    if (err) {
      console.error('Error executing query:', err);
      res.status(500).send('Internal Server Error, could not connect to MySQL instance');
      return;
    }

    const availableProtocols = protocolResults.map(row => row.detected_protocol_name);

    // Execute the query with the selected timeframe, hostname, and protocol filter
    connection.query(queryResults, [`%${selectedProtocol}%`, selectedTimeframe], (err, results) => {
      if (err) {
        console.error('Error executing query:', err);
        res.status(500).send('Internal Server Error, could not connect to MySQL instance');
        return;
      }

      const filteredResults = results.filter(row =>
        (!selectedHostname || row.hostname === selectedHostname) &&
        (!selectedFqdn || row.fqdn.includes(selectedFqdn))
      );

      const uniqueHostnames = [...new Set(results.map(row => row.hostname))];

      res.render('netify', {
        timeframeOptions: timeframeOptions,
        selectedTimeframe: selectedTimeframe,
        selectedHostname: selectedHostname,
        selectedProtocol: selectedProtocol,
        selectedFqdn: selectedFqdn,
        availableProtocols: availableProtocols,
        uniqueHostnames: uniqueHostnames,
        filteredResults: filteredResults
      });
    });
  });
}

module.exports = {
  handleNetifyRequest,
  connectToMySQL
};
