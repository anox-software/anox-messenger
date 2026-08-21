> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current threat model is in `docs/current/THREAT_MODEL.md`.**  
> **Superseded by:** `docs/current/THREAT_MODEL.md`  

# Threat Model - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document analyzes potential attackers against anoX Messenger and defines appropriate countermeasures.

---

## 1. Network Attacker

### Attack Capabilities
- **Man-in-the-Middle (MitM)**: Intercept and modify network traffic
- **Packet sniffing**: Capture unencrypted network data
- **Replay attacks**: Re-send previously captured messages
- **DNS spoofing**: Redirect traffic to malicious servers
- **Traffic analysis**: Infer communication patterns from metadata

### Desired Protection Level
**HIGH** - Network attackers should not be able to read message content or modify messages without detection.

### Technical Countermeasures
- **End-to-end encryption (E2EE)**: Messages encrypted client-side
- **Certificate pinning**: Prevent DNS/spoofing attacks
- **TLS 1.3**: Transport layer encryption for all connections
- **Message authentication codes (MAC)**: Detect message tampering
- **Forward secrecy**: Compromise of long-term keys doesn't expose past communications
- **Random padding**: Obfuscate message sizes to prevent traffic analysis

### Remaining Risks
- **Metadata exposure**: Communication patterns, timing, and participant identities may still be visible
- **Availability attacks**: DoS attacks could disrupt service
- **Endpoint compromise**: If endpoints are compromised, network encryption provides limited protection

---

## 2. Backend Server Attacker

### Attack Capabilities
- **Server code execution**: Execute arbitrary code on backend servers
- **Database access**: Read/write database contents
- **Log access**: Read server logs
- **Memory dumps**: Extract sensitive data from server memory
- **Configuration access**: Read server configuration and secrets

### Desired Protection Level
**CRITICAL** - Backend compromise should not expose message content or private keys.

### Technical Countermeasures
- **Zero-knowledge architecture**: Server only stores encrypted data
- **Client-side encryption**: All message encryption/decryption happens on devices
- **No private key storage**: Private keys never stored on servers
- **Memory encryption**: Sensitive operations use secure memory handling
- **Minimal logging**: No message content or decryption keys in logs
- **Separation of concerns**: Auth, storage, and delivery services separated
- **Regular security audits**: Code reviews and penetration testing

### Remaining Risks
- **Metadata access**: User identities, communication patterns, and timestamps may be accessible
- **Service disruption**: Attacker could deny service or inject malformed data
- **Public key manipulation**: Attacker could replace public keys (requires detection mechanisms)
- **Mass surveillance**: Even without content, metadata enables surveillance

---

## 3. Database Attacker

### Attack Capabilities
- **Direct database access**: Read/write database contents
- **SQL injection**: Execute arbitrary SQL commands
- **Backup access**: Access database backups
- **Schema modification**: Alter database structure
- **Data exfiltration**: Extract entire database contents

### Desired Protection Level
**CRITICAL** - Database compromise should not expose message content or user private keys.

### Technical Countermeasures
- **Encryption at rest**: Database contents encrypted (AES-256)
- **Column-level encryption**: Sensitive columns encrypted separately
- **No plaintext storage**: Message content stored only in encrypted form
- **No private keys**: Private keys never stored in database
- **Database access controls**: Strict role-based access control
- **Regular backups**: Encrypted backups with separate key management
- **Audit logging**: All database access logged and monitored

### Remaining Risks
- **Encrypted data exfiltration**: Attacker could extract encrypted data for offline attacks
- **Metadata exposure**: User identities, relationships, and communication patterns visible
- **Denial of service**: Database could be corrupted or deleted
- **Cryptographic analysis**: Encrypted data could be subject to future cryptanalysis

---

## 4. Compromised User Account

### Attack Capabilities
- **Account takeover**: Access to user's anoX account
- **Identity impersonation**: Send messages as the compromised user
- **Contact list access**: Access to user's contacts
- **Profile modification**: Change user profile information
- **Historical access**: Access to account settings and preferences

### Desired Protection Level
**HIGH** - Account compromise should not expose private keys or historical communications from other devices.

### Technical Countermeasures
- **Multi-factor authentication (MFA)**: Require additional verification for sensitive operations
- **Device-specific authentication**: Each device has separate authentication tokens
- **Account activity monitoring**: Detect and alert on suspicious activity
- **Separation of identity and account**: anoX ID tied to cryptographic identity, not just account
- **Device authorization**: Explicit device addition/removal with verification
- **Rate limiting**: Prevent brute force attacks
- **Secure session management**: Proper session timeout and invalidation

### Remaining Risks
- **Social engineering**: User could be tricked into revealing credentials
- **Credential reuse**: Compromised credentials from other services
- **Active session hijacking**: If user is logged in during compromise
- **Contact list exposure**: Attacker could see user's social graph
- **New message interception**: Attacker could receive and respond to new messages

---

## 5. Device Attacker

### Attack Capabilities
- **Physical access**: Direct access to user's device
- **Malware installation**: Install malicious software
- **Memory extraction**: Extract data from device memory
- **Storage access**: Read encrypted storage if device is unlocked
- **Key logger**: Capture user input including passphrases
- **Network monitoring**: Monitor device network traffic

### Desired Protection Level
**CRITICAL** - Device compromise should not expose other devices' communications or compromise long-term security.

### Technical Countermeasures
- **Hardware security modules (HSM)**: Use secure enclaves for key operations
- **Strong device encryption**: Full disk encryption with strong passphrases
- **Secure key storage**: Keys stored in Android Keystore/Keychain
- **Biometric authentication**: Additional layer of security for key access
- **App sandboxing**: Strict isolation between apps
- **Runtime application self-protection (RASP)**: Detect and prevent tampering
- **Remote wipe**: Ability to remotely revoke compromised devices
- **Forward secrecy**: Compromise of current session keys doesn't expose past communications

### Remaining Risks
- **Active session access**: If device is unlocked during compromise
- **Screen recording/screen capture**: Malware could capture displayed content
- **Clipboard access**: Malware could access copied sensitive data
- **Microphone/camera access**: Malware could access audio/video
- **Network traffic**: While encrypted, traffic patterns may be analyzed
- **Zero-day exploits**: Unknown vulnerabilities could bypass protections

---

## 6. Compromised Support/Admin Account

### Attack Capabilities
- **User account access**: Access to any user account
- **Service disruption**: Modify or delete service configurations
- **Data modification**: Modify stored data
- **Log access**: Access comprehensive service logs
- **Key material access**: Potential access to server-side secrets
- **Mass surveillance**: Monitor all user activities

### Desired Protection Level
**CRITICAL** - Support/admin compromise should not enable decryption of user communications.

### Technical Countermeasures
- **Principle of least privilege**: Admin accounts have minimal necessary access
- **Zero-knowledge architecture**: Even admins cannot access message content
- **Separation of duties**: Different admin roles for different functions
- **Audit logging**: All admin actions logged and reviewed
- **Multi-factor authentication**: Strong MFA for admin access
- **Just-in-time access**: Temporary access grants with expiration
- **No private key access**: Admin accounts cannot access user private keys
- **Emergency procedures**: Documented compromise response procedures

### Remaining Risks
- **Metadata access**: Admins could access comprehensive metadata
- **Service disruption**: Could deny service or corrupt data
- **Identity manipulation**: Could modify user identities or public keys
- **Mass account takeover**: Could compromise user accounts
- **Configuration changes**: Could weaken security configurations

---

## 7. Metadata Analyzer

### Attack Capabilities
- **Traffic analysis**: Analyze communication patterns
- **Social graph mapping**: Map relationships between users
- **Behavioral profiling**: Infer user behavior from metadata
- **Timing analysis**: Infer communication timing patterns
- **Location inference**: Infer user locations from metadata
- **Contact discovery**: Discover user contacts and relationships

### Desired Protection Level
**MEDIUM-HIGH** - Minimize metadata exposure while maintaining functionality.

### Technical Countermeasures
- **Constant traffic**: Generate dummy traffic to obscure patterns
- **Batch delivery**: Delay message delivery to obscure timing
- **Padding**: Add random padding to message sizes
- **Onion routing**: Use anonymizing networks where possible
- **Minimal metadata**: Store only essential metadata
- **Data retention limits**: Automatically delete old metadata
- **Metadata encryption**: Encrypt metadata where possible
- **Dummy contacts**: Add fake contacts to obscure real relationships

### Remaining Risks
- **Fundamental trade-off**: Some metadata is unavoidable for functionality
- **Timing correlation**: Even with padding, timing patterns may be inferable
- **Network-level metadata**: ISPs and network providers see IP addresses and timing
- **Push notification metadata**: Push services may reveal message receipt
- **User behavior**: User behavior patterns may reveal information regardless of technical measures

---

## 8. Message Manipulation/Replay Attacker

### Attack Capabilities
- **Message modification**: Alter message content in transit
- **Message replay**: Re-send previously captured messages
- **Message deletion**: Remove messages from transit
- **Message injection**: Inject fake messages
- **Man-in-the-middle**: Intercept and modify all communications
- **Sequence manipulation**: Alter message order or timing

### Desired Protection Level
**CRITICAL** - Message manipulation must be detectable and preventable.

### Technical Countermeasures
- **Message authentication codes (MAC)**: Cryptographically verify message integrity
- **Digital signatures**: Sign messages with sender's private key
- **Sequence numbers**: Include sequence numbers to detect replay attacks
- **Timestamps**: Include timestamps to detect delayed replay
- **Hash chains**: Use hash chains to verify message sequence
- **Double ratchet**: Ensure forward secrecy and message authentication
- **Key rotation**: Regular key rotation prevents long-term key compromise
- **Acknowledgment protocols**: Verify message delivery and integrity

### Remaining Risks
- **Implementation bugs**: Flaws in cryptographic implementation could be exploited
- **Side-channel attacks**: Timing or other side channels could leak information
- **Quantum computing**: Future quantum computers could break current cryptography
- **Key compromise**: If private keys are compromised, message authentication fails
- **Complexity**: Complex protocols increase implementation risk

---

## Summary of Protection Levels

| Attacker Type | Protection Level | Primary Risk |
|---------------|------------------|--------------|
| Network Attacker | HIGH | Metadata exposure |
| Backend Server Attacker | CRITICAL | Metadata access, service disruption |
| Database Attacker | CRITICAL | Encrypted data exfiltration, metadata |
| Compromised User Account | HIGH | Contact list, new message interception |
| Device Attacker | CRITICAL | Active session access, screen capture |
| Compromised Support/Admin | CRITICAL | Metadata access, service disruption |
| Metadata Analyzer | MEDIUM-HIGH | Fundamental trade-offs with functionality |
| Message Manipulation Attacker | CRITICAL | Implementation bugs, key compromise |

## Key Principles

1. **Zero-knowledge architecture**: Server should never have access to message content
2. **Defense in depth**: Multiple layers of security controls
3. **Forward secrecy**: Compromise of long-term keys shouldn't expose past communications
4. **Minimize trust**: Minimize what needs to be trusted (server, admin, etc.)
5. **Secure by default**: Security should be the default, not an option
6. **Transparency**: Security architecture should be auditable and verifiable