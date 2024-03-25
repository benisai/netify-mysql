import os
from datetime import datetime
import requests
from CONFIG import * # This will import shared variables from the CONFIG.py file.




# Decision to generate MAC host mapping from prometheus_url
generate_mac_mapping = "yes"  # Change to "no" if you want to skip the mapping generation

# Function to fetch DHCP lease data from the custom page
def fetch_dhcp_data():
    try:
        response = requests.get(dhcp_page_url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx)
        data = response.text

        dhcp_lease_data = {}
        lines = data.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                fields = line.split(" ")
                mac_address = fields[1]
                hostname = fields[3]
                ip_address = fields[2]
                dhcp_lease_data[mac_address] = (hostname, ip_address)

        return dhcp_lease_data

    except requests.RequestException as e:
        print("An error occurred while fetching DHCP data from the {ROUTER_IP}/dhcp.html page:")
        print(e)
        return {}

# Check if MAC host mapping generation is required
if generate_mac_mapping == "yes":
    # Fetch DHCP lease data from the custom page
    dhcp_data = fetch_dhcp_data()

    # Save DHCP lease data to a file
    with open(dhcp_mapping_file, "w") as file:
        for mac_address, (hostname, ip_address) in dhcp_data.items():
            file.write(f"{mac_address} {hostname} {ip_address}\n")

    # Example usage of the fetched DHCP data
    #for mac_address, (hostname, ip_address) in dhcp_data.items():
    #    print(f"MAC: {mac_address}, Hostname: {hostname}, IP: {ip_address}")
elif generate_mac_mapping == "no":
    print("Skipping MAC host mapping generation.")
else:
    print("Skipping MAC host mapping generation.")

