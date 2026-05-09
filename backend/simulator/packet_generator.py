import random
from typing import Dict, Any

def generate_normal_features() -> Dict[str, float]:
    """Generates features for a normal network packet."""
    fwd_pkts = random.randint(1, 10)
    bwd_pkts = random.randint(1, 10)
    duration = random.uniform(100, 30000)
    fwd_len_mean = random.uniform(20.0, 500.0)
    bwd_len_mean = random.uniform(20.0, 1000.0)
    
    total_bytes = (fwd_pkts * fwd_len_mean) + (bwd_pkts * bwd_len_mean)
    bytes_per_s = total_bytes / (duration / 1000.0) if duration > 0 else 0
    iat_mean = duration / (fwd_pkts + bwd_pkts) if (fwd_pkts + bwd_pkts) > 0 else duration

    return {
        "Flow Duration": duration,
        "Total Fwd Packets": float(fwd_pkts),
        "Total Backward Packets": float(bwd_pkts),
        "Flow Bytes/s": bytes_per_s * random.uniform(0.8, 1.2),
        "Fwd Packet Length Mean": fwd_len_mean,
        "Bwd Packet Length Mean": bwd_len_mean,
        "Flow IAT Mean": iat_mean
    }

def generate_attack_features(attack_type: str) -> Dict[str, float]:
    """Generates features for specific attack types."""
    if attack_type in {"DDoS", "DoS Hulk", "DoS GoldenEye"}:
        duration = random.uniform(1, 50)
        fwd_pkts = random.randint(80, 260)
        bwd_pkts = random.randint(0, 2)
        fwd_len_mean = random.uniform(40.0, 60.0)
        bwd_len_mean = random.uniform(0.0, 20.0)
    elif attack_type == "Brute Force":
        duration = random.uniform(100, 500)
        fwd_pkts = random.randint(30, 90)
        bwd_pkts = random.randint(10, 40)
        fwd_len_mean = random.uniform(40.0, 140.0)
        bwd_len_mean = random.uniform(40.0, 260.0)
    elif attack_type == "Port Scan":
        duration = random.uniform(1, 8)
        fwd_pkts = random.randint(25, 80)
        bwd_pkts = random.randint(0, 8)
        fwd_len_mean = 0.0
        bwd_len_mean = 0.0
    elif attack_type in {"Infiltration", "Exfiltration", "Botnet C2"}:
        duration = random.uniform(10000, 60000)
        fwd_pkts = random.randint(100, 1000)
        bwd_pkts = random.randint(100, 1000)
        fwd_len_mean = random.uniform(500.0, 1500.0)
        bwd_len_mean = random.uniform(500.0, 2500.0)
    elif attack_type in {"Web Attack", "SQL Injection", "XSS"}:
        duration = random.uniform(40, 300)
        fwd_pkts = random.randint(18, 70)
        bwd_pkts = random.randint(5, 25)
        fwd_len_mean = random.uniform(200.0, 900.0)
        bwd_len_mean = random.uniform(80.0, 400.0)
    elif attack_type == "Zero-Day":
        duration = random.uniform(200, 12000)
        fwd_pkts = random.randint(8, 60)
        bwd_pkts = random.randint(8, 80)
        fwd_len_mean = random.uniform(30.0, 700.0)
        bwd_len_mean = random.uniform(20.0, 900.0)
    else:
        # Generic attack
        duration = random.uniform(10, 500)
        fwd_pkts = random.randint(10, 100)
        bwd_pkts = random.randint(10, 100)
        fwd_len_mean = random.uniform(100.0, 500.0)
        bwd_len_mean = random.uniform(100.0, 500.0)
        
    total_bytes = (fwd_pkts * fwd_len_mean) + (bwd_pkts * bwd_len_mean)
    bytes_per_s = total_bytes / (duration / 1000.0) if duration > 0 else 0
    iat_mean = duration / (fwd_pkts + bwd_pkts) if (fwd_pkts + bwd_pkts) > 0 else duration

    return {
        "Flow Duration": duration,
        "Total Fwd Packets": float(fwd_pkts),
        "Total Backward Packets": float(bwd_pkts),
        "Flow Bytes/s": bytes_per_s,
        "Fwd Packet Length Mean": fwd_len_mean,
        "Bwd Packet Length Mean": bwd_len_mean,
        "Flow IAT Mean": iat_mean
    }

def generate_event(threat_rate: float, specific_attack: str = None) -> Dict[str, Any]:
    import uuid
    import datetime
    
    is_attack = False
    attack_type = "Normal"
    
    if specific_attack:
        is_attack = True
        attack_type = specific_attack
    elif random.random() < threat_rate:
        is_attack = True
        attacks = [
            "DDoS",
            "DoS Hulk",
            "DoS GoldenEye",
            "Port Scan",
            "Brute Force",
            "Botnet C2",
            "Web Attack",
            "SQL Injection",
            "XSS",
            "Infiltration",
            "Exfiltration",
            "Zero-Day",
        ]
        weights = [0.16, 0.14, 0.1, 0.1, 0.08, 0.08, 0.08, 0.06, 0.04, 0.06, 0.06, 0.04]
        total_w = sum(weights)
        norm_weights = [w/total_w for w in weights]
        rd = random.random()
        cumulative = 0.0
        for i, w in enumerate(norm_weights):
            cumulative += w
            if rd < cumulative:
                attack_type = attacks[i]
                break

    if is_attack:
        features = generate_attack_features(attack_type)
    else:
        features = generate_normal_features()
        
    # Generate random IPs for visual effect
    def random_ip(internal=False):
        if internal:
            return f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}"
        return f"{random.randint(11, 220)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    src_internal = attack_type in ["Infiltration", "Exfiltration"]
    
    # Calculate bytes for event format
    fwd_bytes = features["Total Fwd Packets"] * features["Fwd Packet Length Mean"]
    bwd_bytes = features["Total Backward Packets"] * features["Bwd Packet Length Mean"]
    
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "source_ip": random_ip(src_internal),
        "destination_ip": random_ip(True), # targeting internal
        "destination_port": 80 if attack_type == "DDoS" else random.choice([80, 443, 22, 3306, 53]),
        "protocol": "TCP" if attack_type not in ["Botnet C2"] else "UDP",
        "raw_features": features,
        "bytes_transferred": fwd_bytes + bwd_bytes,
        "flow_duration_ms": features["Flow Duration"],
        "true_label": attack_type
    }
