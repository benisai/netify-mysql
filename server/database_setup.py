import mysql.connector
from CONFIG import *

def create_database():
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

    # Close MySQL cursor and connection
    cursor.close()
    db.close()

def create_table():
    # Establish MySQL connection using VARS from config.py
    db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = db.cursor()

    # Create Netify Flow table if it doesn't exist
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {NETIFY_FLOW_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timeinsert TEXT,
        hostname TEXT,
        local_ip TEXT,
        local_mac TEXT,
        local_port INT,
        fqdn TEXT,    
        dest_ip TEXT,
        dest_mac TEXT,
        dest_port INT,
        dest_type TEXT,
        detected_protocol_name TEXT,
        detected_app_name TEXT,
        digest TEXT,
        first_seen_at BIGINT,
        first_update_at BIGINT,
        vlan_id INT,
        interface TEXT,
        internal INT,
        ip_version INT,
        last_seen_at BIGINT,
        type TEXT,
        dest_country TEXT,
        dest_state TEXT,
        dest_city TEXT,
        risk_score TEXT,
        risk_score_client TEXT,
        risk_score_server TEXT
    );
    """
    cursor.execute(create_table_query)
    db.commit()

    # Create Netify purge table if it doesn't exist
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {NETIFY_PURGE_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timeinsert TEXT,
        digest TEXT,
        detection_packets INT,
        last_seen_at INT,
        local_bytes INT,
        local_packets INT,
        other_bytes INT,
        other_packets INT,
        total_bytes INT,
        total_packets INT,
        interface TEXT,
        internal INT,
        reason TEXT,
        type TEXT
    );
    """
    cursor.execute(create_table_query)
    db.commit()

    # Create nlbw_data table if it doesn't exist
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {NETIFY_DATA_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timeinsert text,       
        cpu_cores INT,
        cpu_system DOUBLE,
        cpu_system_prev DOUBLE,
        cpu_user DOUBLE,
        cpu_user_prev DOUBLE,
        dhc_size INT,
        dhc_status TINYINT(1),
        flows INT,
        flows_prev INT,
        maxrss_kb BIGINT,
        maxrss_kb_prev BIGINT,
        sink_queue_max_size_kb INT,
        sink_queue_size_kb INT,
        sink_resp_code INT,
        sink_status TINYINT(1),
        sink_uploads TINYINT(1),
        timestamp BIGINT,
        type VARCHAR(255),
        update_imf INT,
        update_interval INT,
        uptime BIGINT
    );
    """
    cursor.execute(create_table_query)
    db.commit()


    # Create nlbw_data table if it doesn't exist
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {NLBW_DATA_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timeinsert TEXT,
        ip TEXT,
        mac TEXT,
        conns INT,
        rx_bytes INT,
        rx_pkts INT,
        tx_bytes INT,
        tx_pkts INT
    );
    """
    cursor.execute(create_table_query)
    db.commit()


    # Close MySQL cursor and connection
    cursor.close()
    db.close()

if __name__ == "__main__":
    create_database()
    create_table()
