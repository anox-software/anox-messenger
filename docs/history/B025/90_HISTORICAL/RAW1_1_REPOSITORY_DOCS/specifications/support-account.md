> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current binding:** anoX Support chat exists, uses same E2EE principles, no universal decryption bypass. Operational concerns (HA, key backup, ticket integration, virtual devices, special retention) remain OPEN.  
> **Superseded by:** `docs/current/SECURITY_INVARIANTS.md`  

# Support Account Specification - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document specifies the support account system for anoX Messenger, including the "anoX Support" chat that uses end-to-end encryption while maintaining separation from private user chats.

---

## Support Identity

### Support Account Structure
- **Support anoX-ID**: `AX-SUPPORT-00001` (reserved identifier)
- **Display name**: "anoX Support"
- **Account type**: Special system account
- **Visibility**: Automatically added to all user contact lists

### Support Identity Keys
- **Long-term identity key**: Dedicated support identity key pair
- **Signed prekey**: Support signed prekey for initialization
- **Key rotation**: Regular key rotation per security policy
- **Key distribution**: Public key distributed to all users

### Key Management
- **Server-side signing**: Support identity keys signed by server
- **Key verification**: Users can verify support identity keys
- **Key transparency**: Support keys published for transparency
- **Key rotation notification**: Users notified of support key changes

---

## Support Device

### Support Device Architecture
- **Single device model**: Support operates from single device infrastructure
- **Virtual device**: Support device is virtual infrastructure
- **High availability**: Support device designed for high availability
- **Load balancing**: Support device infrastructure supports load balancing

### Support Device Keys
- **Device-specific keys**: Support device has unique device keys
- **Key binding**: Device keys bound to support identity
- **Key rotation**: Regular device key rotation
- **Key backup**: Encrypted backup of support device keys

### Support Device Access
- **Controlled access**: Strict access controls for support device
- **Authentication**: Multi-factor authentication for support staff
- **Authorization**: Role-based access control for support staff
- **Audit logging**: All support device access logged

---

## Support Encryption

### End-to-End Encryption
- **E2EE for support**: Support chats use same E2EE as user chats
- **Same protocol**: Support uses same cryptographic protocol as users
- **No special access**: Support has no special decryption capabilities
- **Zero-knowledge**: Server cannot decrypt support chat content

### Encryption Architecture
- **User-to-support encryption**: Messages encrypted user-to-support
- **Double ratchet**: Support chats use double ratchet for forward secrecy
- **Key exchange**: Standard key exchange protocol with support
- **Message authentication**: Standard message authentication for support chats

### Encryption Differences
- **Identity verification**: Support identity verification handled differently
- **Key distribution**: Support key distribution centralized
- **Trust model**: Different trust model for support vs. user contacts
- **Key rotation**: Support key rotation may be more frequent

---

## Support Key Management

### Support Identity Key Management
- **Centralized generation**: Support identity keys generated centrally
- **Secure storage**: Support keys stored in secure infrastructure
- **Access controls**: Strict access controls for support keys
- **Rotation policy**: Defined rotation policy for support keys

### Support Device Key Management
- **Per-session keys**: Support device uses per-session keys
- **Key isolation**: Support keys isolated from user keys
- **Secure disposal**: Secure disposal of support keys after use
- **Backup policy**: Defined backup policy for support keys

### Support Key Rotation
- **Scheduled rotation**: Regular scheduled key rotation
- **Compromise rotation**: Immediate rotation on compromise
- **User notification**: Users notified of support key changes
- **Verification**: Users can verify new support keys

---

## Admin Rights

### Support Staff Access
- **Limited access**: Support staff have limited access to support device
- **Authentication**: Strong authentication required for support staff
- **Authorization**: Specific authorization for support functions
- **Monitoring**: All support staff activities monitored

### Admin Functions
- **Support messaging**: Ability to send support messages
- **Issue investigation**: Ability to investigate user issues
- **Account assistance**: Ability to assist with account issues
- **Limited escalation**: Limited escalation capabilities for complex issues

### Limitations
- **No private chat access**: Support staff cannot access private user chats
- **No decryption access**: Support staff cannot decrypt user messages
- **No metadata access**: Support staff have limited metadata access
- **No administrative override**: No administrative override of E2EE

---

## Support vs. Private Chat Separation

### Technical Separation
- **Separate encryption**: Support chats encrypted separately from private chats
- **Separate keys**: Support uses separate keys from private chats
- **Separate storage**: Support chats stored separately from private chats
- **Separate access**: Separate access controls for support vs. private

### Policy Separation
- **Different retention**: Different retention policies for support vs. private
- **Different access**: Different access policies for support vs. private
- **Different logging**: Different logging policies for support vs. private
- **Different compliance**: Different compliance requirements for support vs. private

### User Interface Separation
- **Visual distinction**: Clear visual distinction between support and private chats
- **Separate chat list**: Support chat in separate section or visually distinct
- **Different features**: Different features available in support vs. private chats
- **Clear labeling**: Clear labeling of support chat identity

---

## Support Chat Features

### Basic Features
- **Text messaging**: Standard text messaging
- **File sharing**: Limited file sharing for support purposes
- **Message history**: Support chat message history
- **Search**: Search within support chat

### Support-Specific Features
- **Issue categorization**: Ability to categorize support issues
- **Ticket system**: Integration with support ticket system
- **Automated responses**: Automated responses for common issues
- **Escalation**: Escalation to human support when needed

### Limitations
- **No group support**: Support chat is 1:1 only
- **No voice/video**: No voice or video in support chat
- **Limited attachments**: Limited attachment types and sizes
- **No encryption verification**: Different key verification process

---

## Support Staff Training

### Security Training
- **E2EE understanding**: Training on E2EE principles and limitations
- **Data handling**: Training on proper data handling procedures
- **Incident response**: Training on security incident response
- **Privacy awareness**: Training on privacy principles and requirements

### Operational Training
- **Support procedures**: Training on support procedures and policies
- **Tool usage**: Training on support tools and systems
- **Communication**: Training on effective user communication
- **Escalation**: Training on issue escalation procedures

### Compliance Training
- **Legal requirements**: Training on legal and compliance requirements
- **Data protection**: Training on data protection regulations
- **Reporting requirements**: Training on reporting requirements
- **Audit procedures**: Training on audit procedures

---

## Security Requirements

### SEC-SUPPORT-001
Support chats must use the same E2EE protocol as user chats.

### SEC-SUPPORT-002
Support staff must not have access to private user chat content.

### SEC-SUPPORT-003
Support staff must not have access to user private keys.

### SEC-SUPPORT-004
Support identity keys must be regularly rotated.

### SEC-SUPPORT-005
Support device access must require multi-factor authentication.

### SEC-SUPPORT-006
Support staff activities must be logged and audited.

### SEC-SUPPORT-007
Support chats must be clearly distinguished from private chats in the UI.

### SEC-SUPPORT-008
Support keys must be distributed transparently to users.

### SEC-SUPPORT-009
Support staff must have limited, role-based access.

### SEC-SUPPORT-010
Support infrastructure must maintain zero-knowledge architecture.

---

## Implementation Considerations

### Support Account Setup
```json
{
  "supportAccount": {
    "anoXId": "AX-SUPPORT-00001",
    "displayName": "anoX Support",
    "accountType": "system",
    "identityKey": {
      "publicKey": "...",
      "signature": "..."
    },
    "deviceKeys": [
      {
        "deviceId": "SUPPORT-DEVICE-001",
        "publicKey": "..."
      }
    ]
  }
}
```

### Support Chat Initialization
```kotlin
fun initializeSupportChat(userId: String) {
    // Get support public keys
    val supportKeys = getSupportPublicKeys()
    
    // Initialize E2EE session with support
    val session = initializeE2EESession(supportKeys)
    
    // Create support chat entry
    createSupportChatEntry(userId, session)
}
```

### Support Key Rotation
```kotlin
fun rotateSupportKeys() {
    // Generate new support keys
    val newKeys = generateSupportKeys()
    
    // Sign new keys
    val signedKeys = signSupportKeys(newKeys)
    
    // Distribute new keys to users
    distributeSupportKeys(signedKeys)
    
    // Notify users of key change
    notifyUsersOfKeyChange()
}
```

---

## Open Decisions

### OPEN-SUPPORT-001
What is the appropriate rotation period for support identity keys?

### OPEN-SUPPORT-002
How should support key verification be presented to users?

### OPEN-SUPPORT-003
What level of file sharing should be supported in support chats?

### OPEN-SUPPORT-004
How should support staff access be monitored and audited?

### OPEN-SUPPORT-005
What is the appropriate retention period for support chat history?

### OPEN-SUPPORT-006
How should the system handle support staff turnover and key management?

### OPEN-SUPPORT-007
Should support chats have different message limits than private chats?