# This is my netify.py file
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
from database_setup import * # This will import functions from the database_setup.py file.

#---------- Check if GeoLite2-City.mmdb, dhcp_mapping or netifyDB.db exists ----------#

# Check if the file GeoLite2-City.mmdb exists
if not os.path.exists(GEOIP_DB_FILE):
    print("GeoLite2-City.mmdb file missing. Running get-geolite2-db.py...")
    subprocess.run(['python3', 'get_geolite2_db.py'])
else:
    print("GeoLite2-City.mmdb file found. No need to run get_geolite2_db.py.")

# Check if the file dhcp_mapping exists
if not os.path.exists(mac_host_mapping_file):
    print("dhcp_mapping.txt file missing. Running get_dhcp.py...")
    subprocess.run(['python3', 'get_dhcp.py'])
else:
    print("dhcp_mapping.txt file found. No need to run get-dhcp.py.")

#----------- END Check GeoLite2-City.mmdb, dhcp_mapping or netifyDB.db exists ----------#

# Create database if it doesn't exist
create_database()

# Create table if it doesn't exist
create_table()

# Initialize mac_host_mapping
mac_host_mapping = {}

# Read mac_host_mapping.txt and create mapping dictionary
with open(mac_host_mapping_file, "r") as file:
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line:
            mac, hostname, ip = line.split(" ", 2)
            mac_host_mapping[mac] = (hostname, ip)

# Read GeoIP Database
geoip_reader = geoip2.database.Reader(GEOIP_DB_FILE)

# Function to establish MySQL connection with retry logic

def connect_to_mysql():
    print(f"Connecting to MySQL using: {MYSQL_HOST} {MYSQL_PORT}")
    while True:
        try:
            db = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB
            )
            cursor = db.cursor()
            return db, cursor
        except mysql.connector.Error as err:
            print(f"Failed to connect to MySQL: {err}")
            time.sleep(5)  # Wait for a few seconds before retrying

# Establish MySQL connection with retry logic
db, cursor = connect_to_mysql()

# Function to run netcat command with retry logic
def run_netcat():
    while True:
        try:
            netcat_process = subprocess.Popen(
                ["nc", ROUTER_IP, NETIFY_PORT],
                stdout=subprocess.PIPE,
                universal_newlines=True
            )
            return netcat_process
        except Exception as e:
            print(f"Failed to run netcat: {e}")
            time.sleep(5)  # Wait for a few seconds before retrying

# Run netcat command with retry logic
netcat_process = run_netcat()


# Process the data stream for Netify_Flow
for line in netcat_process.stdout:
#-------------------------------------------------------------------------------------------------------------------------------NETIFY_FLOW_TABLE#    
    # Check if the line contains both "established" or "flow" and "local_ip"
    if "established" in line or ("flow" in line and "local_ip" in line):
        # Parse JSON data
        data = json.loads(line)
        flow_data = data.get("flow", {})
        
        # The values
        detected_protocol_name = flow_data.get("detected_protocol_name", "Unknown")
        first_seen_at = flow_data.get("first_seen_at", 0)
        first_update_at = flow_data.get("first_update_at", 0)
        ip_version = flow_data.get("ip_version", 0)
        last_seen_at = flow_data.get("last_seen_at", 0)
        local_ip = flow_data.get("local_ip", "Unknown")
        local_mac = flow_data.get("local_mac", "Unknown")
        local_port = flow_data.get("local_port", 0)
        dest_ip = flow_data.get("other_ip", "Unknown")
        dest_mac = flow_data.get("other_mac", "Unknown")
        dest_port = flow_data.get("other_port", 0)
        dest_type = flow_data.get("other_type", "Unknown")
        vlan_id = flow_data.get("vlan_id", 0)
        interface = data.get("interface", "Unknown")
        internal = int(data.get("internal", 0))  # Convert to int for MySQL
        type = data.get("type", "Unknown")
        detected_app_name = flow_data.get("detected_application_name", "Unknown")
        digest = flow_data.get("digest", "Unknown")

        # Check the structure of 'risks_data'
        risks_data = flow_data.get("risks", {})

        # Extract risk scores values
        risk_score = risks_data.get("ndpi_risk_score", 0)
        risk_score_client = risks_data.get("ndpi_risk_score_client", 0)
        risk_score_server = risks_data.get("ndpi_risk_score_server", 0)

        # Check if 'host_server_name' exists in the data
        fqdn = flow_data.get("host_server_name", local_ip)

        ssl_data = flow_data.get("ssl", {})
        client_sni = ssl_data.get("client_sni", "no_ssl")
        # Check if SSL field exists and has the 'client_sni' attribute, set the FQDN to the SNI
        if "client_sni" in ssl_data:
            fqdn = ssl_data["client_sni"]
            client_sni = ssl_data["client_sni"]

        # Check if local_mac exists in mac_host_mapping
        hostname, _ = mac_host_mapping.get(local_mac, (local_ip, ""))

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

        insert_query = f"""
            INSERT INTO {NETIFY_FLOW_TABLE} (
                timeinsert, hostname, local_ip, local_mac, local_port, fqdn, dest_ip, dest_mac, dest_port, dest_type,
                detected_protocol_name, detected_app_name, digest, first_seen_at, first_update_at, vlan_id, interface, internal, ip_version,
                last_seen_at, type, dest_country, dest_state, dest_city, risk_score, risk_score_client, risk_score_server
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        # Execute the SQL query
        cursor.execute(insert_query, (
            time_insert, hostname, local_ip, local_mac, local_port, fqdn, dest_ip, dest_mac, dest_port, dest_type,
            detected_protocol_name, detected_app_name, digest, first_seen_at, first_update_at, vlan_id, interface, internal, ip_version,
            last_seen_at, type, dest_country, dest_state, dest_city, risk_score, risk_score_client, risk_score_server
        ))
        db.commit()
#------------------------------------------------------------------------------------------------------------------------------NETIFY_PURGE_TABLE#
    # Check if the line contains both "digest" and "flow_purge"
    if "digest" in line and "flow_purge" in line:
        data = json.loads(line)
        flow_data = data.get("flow", {})  # Extract the flow data

        detection_packets = flow_data.get("detection_packets", 0)
        last_seen_at = flow_data.get("last_seen_at", 0)
        local_bytes = flow_data.get("local_bytes", 0)
        local_packets = flow_data.get("local_packets", 0)
        other_bytes = flow_data.get("other_bytes", 0)
        other_packets = flow_data.get("other_packets", 0)
        total_bytes = flow_data.get("total_bytes", 0)
        total_packets = flow_data.get("total_packets", 0)
        interface = data.get("interface", "Unknown")
        internal = int(data.get("internal", 0))  # Convert to int for MySQL
        reason = data.get("reason", "Unknown")
        detected_app_name = flow_data.get("detected_application_name", "Unknown")
        digest = flow_data.get("digest", "Unknown")
        type = data.get("type", "Unknown")

        # Get current timestamp
        time_insert = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # SQL query to insert data into the table
        insert_query = f"""
        INSERT INTO {NETIFY_PURGE_TABLE} (
            timeinsert, detection_packets, digest, last_seen_at, local_bytes, local_packets,
            other_bytes, other_packets, total_bytes, total_packets, interface, internal, reason, type
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        # Prepare the data for insertion
        insert_data = (
            time_insert, detection_packets, digest, last_seen_at, local_bytes, local_packets,
            other_bytes, other_packets, total_bytes, total_packets,
            interface, internal, reason, type
        )

        # Execute the SQL query
        cursor.execute(insert_query, insert_data)
        db.commit()
#------------------------------------------------------------------------------------------------------------------------------------netify_data#
    # Check if the line contains "cpu_cores"
    if "cpu_cores" in line:
        data = json.loads(line.strip())

        # Get current timestamp
        time_insert = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Extract relevant data
        cpu_cores = data.get("cpu_cores", 0)
        cpu_system = data.get("cpu_system", 0)
        cpu_system_prev = data.get("cpu_system_prev", 0)
        cpu_user = data.get("cpu_user", 0)
        cpu_user_prev = data.get("cpu_user_prev", 0)
        dhc_size = data.get("dhc_size", 0)
        dhc_status = int(data.get("dhc_status", 0))  # Convert to int for MySQL
        flows = data.get("flows", 0)
        flows_prev = data.get("flows_prev", 0)
        maxrss_kb = data.get("maxrss_kb", 0)
        maxrss_kb_prev = data.get("maxrss_kb_prev", 0)
        sink_queue_max_size_kb = data.get("sink_queue_max_size_kb", 0)
        sink_queue_size_kb = data.get("sink_queue_size_kb", 0)
        sink_resp_code = data.get("sink_resp_code", 0)
        sink_status = int(data.get("sink_status", 0))  # Convert to int for MySQL
        sink_uploads = int(data.get("sink_uploads", 0))  # Convert to int for MySQL
        timestamp = data.get("timestamp", 0)
        type = data.get("type", "Unknown")
        update_imf = data.get("update_imf", 0)
        update_interval = data.get("update_interval", 0)
        uptime = data.get("uptime", 0)


        # Insert the data into the MySQL database
        insert_query = f"""
        INSERT INTO netify_data (
            timeinsert, cpu_cores, cpu_system, cpu_system_prev, cpu_user, cpu_user_prev,
            dhc_size, dhc_status, flows, flows_prev, maxrss_kb,
            maxrss_kb_prev, sink_queue_max_size_kb, sink_queue_size_kb,
            sink_resp_code, sink_status, sink_uploads, timestamp,
            type, update_imf, update_interval, uptime
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        # Prepare the data for insertion
        insert_data = (
            time_insert, cpu_cores, cpu_system, cpu_system_prev,
            cpu_user, cpu_user_prev, dhc_size,
            dhc_status, flows, flows_prev,
            maxrss_kb, maxrss_kb_prev,
            sink_queue_max_size_kb, sink_queue_size_kb,
            sink_resp_code, sink_status,
            sink_uploads, timestamp, type,
            update_imf, update_interval, uptime
        )

        # Execute the SQL query
        cursor.execute(insert_query, insert_data)
        db.commit()


# Close the GeoIP database reader
geoip_reader.close()

# Close MySQL cursor and connection
cursor.close()
db.close()

