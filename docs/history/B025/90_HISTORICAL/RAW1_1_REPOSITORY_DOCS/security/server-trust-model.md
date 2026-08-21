> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current direction:** Server is untrusted for content; metadata remains visible; availability not guaranteed. Avoid broad "zero-knowledge" branding.  
> **Superseded by:** `docs/current/SECURITY_INVARIANTS.md` and `docs/current/SYSTEM_ARCHITECTURE.md`  

# Server Trust Model - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document defines what the server may and may not know in the anoX Messenger system, establishing a zero-knowledge architecture where the server is not trusted with message content.

---

## Core Principle

### Zero-Knowledge Architecture
**The server should not be trusted with message content or user private keys.**

The server acts as a transport and storage mechanism for encrypted data, but should never have access to plaintext messages or the means to decrypt them.

---

## What the Server MAY Know

### ALLOWED: User Identity Information
- **anoX-ID**: User's anoX identifier
- **Public keys**: User's public cryptographic keys
- **Device information**: Device metadata (type, OS version, etc.)
- **Registration timestamp**: When user registered
- **Last activity**: Timestamp of last user activity

### ALLOWED: Public Key Infrastructure
- **Public keys**: All user public keys
- **Key mappings**: Mapping between anoX-ID and public keys
- **Key signatures**: Signatures on key mappings
- **Key metadata**: Key creation timestamps, expiration dates
- **Revocation status**: Status of key revocations

### ALLOWED: Encrypted Message Data
- **Encrypted message content**: Message content encrypted with recipient's public key
- **Message metadata**: Sender, recipient, timestamp (encrypted where possible)
- **Message identifiers**: Unique message identifiers
- **Delivery status**: Whether message was delivered
- **Read receipts**: Whether message was read (optional, encrypted)

### ALLOWED: Technical Infrastructure
- **Network routing**: IP addresses for message delivery
- **Connection metadata**: TLS session information
- **Server logs**: Technical server logs (no message content)
- **Performance metrics**: System performance data
- **Error logs**: Technical error information

### ALLOWED: Contact Relationships
- **Contact lists**: Encrypted contact lists
- **Group memberships**: Encrypted group membership information
- **Relationship metadata**: Encrypted relationship information
- **Social graph**: Encrypted social graph data

### ALLOWED: Service Management
- **Account status**: Account active/inactive status
- **Subscription status**: Subscription/payment information
- **Service configuration**: Service configuration data
- **Administrative data**: Administrative account information

---

## What the Server MUST NOT Know

### FORBIDDEN: Message Content
- **Plaintext messages**: Any message content in plaintext
- **Decryption keys**: Any keys that could decrypt message content
- **Message drafts**: Draft messages in plaintext
- **Message subjects**: Subject lines in plaintext
- **Message attachments**: Attachment content in plaintext

### FORBIDDEN: Private Key Material
- **Private keys**: Any user private keys
- **Key derivation secrets**: Any secrets used for key derivation
- **Passphrases**: User passphrases or passwords
- **Recovery secrets**: Recovery codes or backup secrets
- **Biometric data**: Any biometric templates or data

### FORBIDDEN: Decryption Capabilities
- **Decryption algorithms**: No ability to decrypt user data
- **Key escrow**: No key escrow mechanisms
- **Backdoor access**: No backdoor access to encrypted data
- **Master keys**: No master decryption keys
- **Lawful access**: No built-in lawful access capabilities

### FORBIDDEN: User Secrets
- **Authentication secrets**: User authentication secrets beyond minimal
- **Session secrets**: Session keys or tokens that could decrypt data
- **Personal identifiers**: Personal information beyond anoX-ID
- **Location data**: Precise user location data
- **Behavioral data**: Detailed behavioral profiling data

### FORBIDDEN: Contact Details
- **Contact plaintext**: Contact information in plaintext
- **Address books**: User address books in plaintext
- **Communication patterns**: Detailed communication patterns
- **Social graph plaintext**: Social graph relationships in plaintext
- **Contact metadata**: Detailed contact metadata

---

## Technical Implementation

### Client-Side Encryption
- **All encryption client-side**: All message encryption performed on client devices
- **No server decryption**: Server has no capability to decrypt messages
- **End-to-end encryption**: Messages encrypted end-to-end between devices
- **Key management**: All key management client-side

### Server-Side Storage
- **Encrypted storage only**: Only encrypted data stored on server
- **No plaintext storage**: No plaintext data stored on server
- **Encryption at rest**: Server-side encryption for defense in depth
- **Separate key management**: Server-side encryption keys separate from user keys

### Transport Security
- **TLS 1.3**: All connections use TLS 1.3
- **Certificate pinning**: Client-side certificate pinning
- **HSTS**: HTTP Strict Transport Security
- **Perfect forward secrecy**: TLS perfect forward secrecy

### Data Minimization
- **Minimal metadata**: Store only essential metadata
- **Data retention limits**: Automatic deletion of old data
- **Privacy by design**: Privacy considerations in all design decisions
- **Data minimization**: Collect and store minimum necessary data

---

## Unavoidable Metadata

### Network-Level Metadata
- **IP addresses**: Server sees client IP addresses
- **Connection timing**: Server sees connection timing
- **Data volume**: Server sees approximate data volumes
- **Connection patterns**: Server sees connection patterns

### Protocol-Level Metadata
- **Message timing**: Server sees when messages are sent/received
- **Message size**: Server sees approximate message sizes
- **Recipient information**: Server sees message routing information
- **Delivery status**: Server sees delivery confirmation

### Account-Level Metadata
- **Account existence**: Server knows which accounts exist
- **Account activity**: Server sees account activity patterns
- **Device information**: Server sees registered device information
- **Service usage**: Server sees service usage patterns

### Mitigation Strategies
- **Padding**: Add random padding to message sizes
- **Dummy traffic**: Generate dummy traffic to obscure patterns
- **Batch processing**: Process messages in batches to obscure timing
- **Onion routing**: Use anonymizing networks where possible
- **Data retention limits**: Automatically delete old metadata

---

## Trust Boundaries

### Trusted Components
- **Client applications**: User devices running the anoX app
- **User authentication**: User authentication mechanisms
- **Cryptographic libraries**: Cryptographic libraries used on client
- **User actions**: User decisions and actions

### Untrusted Components
- **Server infrastructure**: All server infrastructure
- **Network infrastructure**: Network infrastructure between clients and server
- **Third-party services**: Third-party services (push notifications, etc.)
- **Administrative access**: Administrative access to servers

### Semi-Trusted Components
- **Server code**: Server code is audited but not fully trusted
- **Storage systems**: Storage systems with encryption at rest
- **CDN networks**: Content delivery networks for static content
- **Monitoring systems**: Monitoring and logging systems

---

## Security Requirements

### SEC-SERVER-001
The server must never have access to message plaintext.

### SEC-SERVER-002
The server must never have access to user private keys.

### SEC-SERVER-003
The server must never have access to decryption keys for user data.

### SEC-SERVER-004
All message encryption must be performed client-side.

### SEC-SERVER-005
The server must store only encrypted user data.

### SEC-SERVER-006
The server must implement encryption at rest for all stored data.

### SEC-SERVER-007
The server must minimize metadata collection and retention.

### SEC-SERVER-008
The server must implement data retention limits and automatic deletion.

### SEC-SERVER-009
The server must not implement any key escrow mechanisms.

### SEC-SERVER-010
The server must not implement any backdoor access to encrypted data.

---

## Implementation Considerations

### Data Model
```json
{
  "message": {
    "id": "msg-12345",
    "senderId": "AX-7K4M92QPR3ST",
    "recipientId": "AX-ABC123DEF456",
    "encryptedContent": "base64-encoded-encrypted-data",
    "encryptedMetadata": "base64-encoded-metadata",
    "timestamp": "2024-01-15T10:30:00Z",
    "deliveryStatus": "delivered"
  }
}
```

### API Design
- **No plaintext endpoints**: No API endpoints accept or return plaintext
- **Encrypted payloads**: All API payloads encrypted
- **Authenticated requests**: All requests authenticated
- **Rate limiting**: Rate limiting to prevent abuse
- **Input validation**: Strict input validation

### Storage Design
- **Encrypted databases**: All database fields encrypted
- **Separate encryption keys**: Database encryption keys separate from user keys
- **Key rotation**: Regular database encryption key rotation
- **Access controls**: Strict database access controls
- **Audit logging**: All database access logged

---

## Monitoring and Auditing

### Server Monitoring
- **Performance monitoring**: Monitor server performance
- **Security monitoring**: Monitor for security incidents
- **Access monitoring**: Monitor all access to servers
- **Error monitoring**: Monitor and log errors
- **Compliance monitoring**: Monitor for compliance violations

### Audit Logging
- **Access logs**: Log all access to user data
- **Administrative actions**: Log all administrative actions
- **Security events**: Log all security-relevant events
- **Data access**: Log all access to encrypted data
- **Key access**: Log all access to encryption keys

### Transparency
- **Transparency reports**: Publish transparency reports
- **Security audits**: Regular security audits
- **Penetration testing**: Regular penetration testing
- **Bug bounty**: Bug bounty program for security issues
- **Incident response**: Documented incident response procedures

---

## Open Decisions

### OPEN-SERVER-001
What is the acceptable retention period for encrypted message data?

### OPEN-SERVER-002
What metadata is technically unavoidable for message delivery?

### OPEN-SERVER-003
How should the system handle lawful access requests while maintaining zero-knowledge architecture?

### OPEN-SERVER-004
What level of geographic data distribution is required for compliance?

### OPEN-SERVER-005
How should the system handle server compromise scenarios?

### OPEN-SERVER-006
What level of server-side logging is appropriate for security vs. privacy?

### OPEN-SERVER-007
How should the system handle data deletion requests (right to be forgotten)?