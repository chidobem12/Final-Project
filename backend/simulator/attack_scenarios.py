SCENARIOS = {
    "ddos_flood": {
        "name": "DDoS Flood Attack",
        "description": "Volumetric DDoS attack from 500 external IPs targeting port 80",
        "duration_seconds": 30,
        "events_per_second": 50,
        "attack_type": "DDoS",
        "source_count": 500,
        "target_port": 80
    },
    "ransomware_outbreak": {
        "name": "Ransomware Lateral Movement",
        "description": "Internal host compromised, scanning internal network",
        "duration_seconds": 45,
        "events_per_second": 20,
        "attack_type": "Infiltration",
        "source_count": 1,
        "internal": True
    },
    "apt_intrusion": {
        "name": "Advanced Persistent Threat",
        "description": "Slow, low-and-slow APT reconnaissance over 60 seconds",
        "duration_seconds": 60,
        "events_per_second": 2,
        "attack_type": "Infiltration",
        "source_count": 3
    },
    "credential_stuffing": {
        "name": "Credential Stuffing Campaign",
        "description": "Mass authentication attempts from distributed botnet",
        "duration_seconds": 20,
        "events_per_second": 30,
        "attack_type": "Brute Force",
        "source_count": 200
    },
    "insider_exfiltration": {
        "name": "Insider Data Exfiltration",
        "description": "Internal user transferring large data volumes to external IP",
        "duration_seconds": 25,
        "events_per_second": 5,
        "attack_type": "Exfiltration",
        "source_count": 1,
        "internal": True
    }
}
