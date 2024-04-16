# This is my CONFIG.py file
import os

# Router IP Address
ROUTER_IP = os.getenv('ROUTER_IP', '10.0.3.1')
NETIFY_PORT = os.getenv('NETIFY_PORT', '7150')

# MySQL configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', '10.0.5.5')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306') 
MYSQL_USER = os.getenv('MYSQL_USER', 'netify')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'netify')
MYSQL_DB = os.getenv('MYSQL_DB', 'netifyDB')
MYSQL_TABLE = os.getenv('MYSQL_TABLE', 'netify_flow')

# SQLite database configuration
NETIFY_FLOW_TABLE = "netify_flow"
NETIFY_PURGE_TABLE = "netify_purge"
NETIFY_DATA_TABLE = "netify_data"
NLBW_DATA_TABLE = "nlbw_data"




# URL to fetch NLBW data
nlbw_url = f"http://{ROUTER_IP}/nlbw.txt"

# Custom DHCP page URL -- On the Router, run this command 'ln -s /tmp/dhcp.leases  /www/dhcp.html'
dhcp_page_url = f"http://{ROUTER_IP}/dhcp.html"
dhcp_mapping_file = "./files/dhcp_mapping.txt"
mac_host_mapping_file = "./files/dhcp_mapping.txt"

# GeoIP database section and license
DOWNLOAD_NEW_GEOIP_DB = os.getenv('DOWNLOAD_NEW_GEOIP_DB', 'yes') # Set to "yes" to download the new database, set to "no" to skip DB download
maxmind_license_key = os.getenv('maxmind_license_key', 'NO-KEY-CANT-DOWNLOAD')
GEOIP_DB_FILE = "./files/GeoLite2-City.mmdb"






