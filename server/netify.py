from datetime import datetime
import subprocess
import json
import mysql.connector
import requests
import geoip2.database
import tarfile
import os
import time

from CONFIG import * # This will import shared variables from the CONFIG.py file.

# MySQL configuration
MYSQL_HOST = "10.0.5.213"
MYSQL_USER = "netify"
MYSQL_PASSWORD = "netify"
MYSQL_DB = "netifyDB"
MYSQL_TABLE = "netify"

#---------- Check if GeoLite2-City.mmdb, dhcp_mapping or netifyDB.db exists ----------#

# Check if the file GeoLite2-City.mmdb exists
if not os.path.exists(GEOIP_DB_FILE):
    print("GeoLite2-City.mmdb file missing. Running get-geolite2-db.py...")
    subprocess.run(['python3', 'get-geolite2-db.py'])
else:
    print("GeoLite2-City.mmdb file found. No need to run get-geolite2-db.py.")

# Check if the file dhcp_mapping exists
if not os.path.exists(mac_host_mapping_file):
    print("dhcp_mapping.txt file missing. Running get-dhcp.py...")
    subprocess.run(['python3', 'get-dhcp.py'])
else:
    print("dhcp_mapping.txt file found. No need to run get-dhcp.py.")


#----------- END Check GeoLite2-City.mmdb, dhcp_mapping or netifyDB.db exists ----------#
    

# Initialize mac_host_mapping
mac_host_mapping = {}

# Read mac_host_mapping.txt and create mapping dictionary
mac_host_mapping = {}
with open(mac_host_mapping_file, "r") as file:
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line:
            mac, hostname, ip = line.split(" ", 2)
            mac_host_mapping[mac] = (hostname, ip)


# Read GeoIP Database
geoip_reader = geoip2.database.Reader(GEOIP_DB_FILE)


# Establish MySQL connection
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD
)
cursor = db.cursor()

# Create database if it doesn't exist
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
db.commit()

# Switch to the specified database
cursor.execute(f"USE {MYSQL_DB}")                

# Create table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS netify (
    timeinsert VARCHAR(255),
    hostname VARCHAR(255),
    local_ip VARCHAR(255),
    local_mac VARCHAR(255),
    local_port INT,
    fqdn VARCHAR(255),
    dest_ip VARCHAR(255),
    dest_mac VARCHAR(255),
    dest_port INT,
    dest_type VARCHAR(255),
    detected_protocol_name VARCHAR(255),
    first_seen_at BIGINT,
    first_update_at BIGINT,
    vlan_id INT,
    interface VARCHAR(255),
    internal BOOL,
    ip_version INT,
    last_seen_at BIGINT,
    type VARCHAR(255),
    dest_country VARCHAR(255),
    dest_state VARCHAR(255),
    dest_city VARCHAR(255)
);
"""
cursor.execute(create_table_query)
db.commit()

# Netcat command
netcat_process = subprocess.Popen(
    ["nc", ROUTER_IP, "7150"],
    stdout=subprocess.PIPE,
    universal_newlines=True
)

# Process the data stream
for line in netcat_process.stdout:
    # Filter lines containing "established"
    if "established" in line:
        # Remove unwanted text
        line = line.replace('"established":false,', '')
        line = line.replace('"flow":{', '')
        line = line.replace('0}', '0')

        # Parse JSON
        data = json.loads(line)

        # Extract relevant variables
        detected_protocol_name = data["detected_protocol_name"]
        first_seen_at = data["first_seen_at"]
        first_update_at = data["first_update_at"]
        ip_version = data["ip_version"]
        last_seen_at = data["last_seen_at"]
        local_ip = data["local_ip"]
        local_mac = data["local_mac"]
        local_port = data["local_port"]
        dest_ip = data["other_ip"]
        dest_mac = data["other_mac"]
        dest_port = data["other_port"]
        dest_type = data["other_type"]
        vlan_id = data["vlan_id"]
        interface = data["interface"]
        internal = data["internal"]
        type = data["type"]

        # Check if 'host_server_name' exists in the data
        if "host_server_name" in data:
            fqdn = data["host_server_name"]
        else:
            fqdn = data["other_ip"]
        # Check if local_mac exists in mac_host_mapping
        if local_mac in mac_host_mapping:
            hostname, _ = mac_host_mapping[local_mac]
        else:
            hostname = "Unknown"

        # Retrieve location information using GeoIP
        try:
            response = geoip_reader.city(dest_ip)
            dest_country = response.country.name
            dest_state = response.subdivisions.most_specific.name
            dest_city = response.city.name
        except geoip2.errors.AddressNotFoundError:
            dest_country = "Unknown"
            dest_state = "Unknown"
            dest_city = "Unknown"

        # Get current timestamp
        time_insert = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # SQL query to insert data into the table
        insert_query = f"""
        INSERT INTO {MYSQL_TABLE} (
            timeinsert, hostname, local_ip, local_mac, local_port, fqdn, dest_ip, dest_mac, dest_port, dest_type,
            detected_protocol_name, first_seen_at, first_update_at, vlan_id, interface, internal, ip_version,
            last_seen_at, type, dest_country, dest_state, dest_city
        ) VALUES (
            '{time_insert}', '{hostname}', '{local_ip}', '{local_mac}', {local_port}, '{fqdn}', '{dest_ip}',
            '{dest_mac}', {dest_port}, '{dest_type}', '{detected_protocol_name}', {first_seen_at}, {first_update_at},
            {vlan_id}, '{interface}', {internal}, {ip_version}, {last_seen_at}, '{type}', '{dest_country}',
            '{dest_state}', '{dest_city}'
        );
        """

        # Execute the SQL query
        cursor.execute(insert_query)
        db.commit()

# Close the GeoIP database reader
geoip_reader.close()

# Close MySQL cursor and connection
cursor.close()
db.close()