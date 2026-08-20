> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current direction:** vodozemac/Olm-based key and session architecture in `docs/current/KEY_AND_SESSION_ARCHITECTURE.md`.  
> **Superseded by:** `docs/current/KEY_AND_SESSION_ARCHITECTURE.md`  

# Key Architecture - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document specifies the cryptographic key architecture for anoX Messenger, including key types, generation, storage, rotation, and lifecycle management.

---

## Key Hierarchy

### Key Types
```
User Identity Keys (Long-term)
├── Identity Key Pair (IK)
│   ├── Identity Public Key (IPK)
│   └── Identity Private Key (ISK)
└── Signed Prekey (SPK)
    ├── Signed Prekey Public Key (SPPK)
    └── Signed Prekey Private Key (SPSK)

Device Keys (Long-term per device)
├── Device Key Pair (DK)
│   ├── Device Public Key (DPK)
│   └── Device Private Key (DSK)
└── Device Signed Prekey (DSPK)
    ├── Device Signed Prekey Public Key (DSPPK)
    └── Device Signed Prekey Private Key (DSPSK)

Session Keys (Ephemeral)
├── Root Key (RK)
├── Chain Keys (CK)
│   ├── Sending Chain Key (CKs)
│   └── Receiving Chain Key (CKr)
└── Message Keys (MK)
```

---

## Identity Keys

### Purpose
- **Long-term user identity**: Persistent cryptographic identity
- **Key verification**: Basis for verifying other keys
- **Trust establishment**: Foundation for trust relationships
- **Device binding**: Bind devices to user identity

### Identity Key Pair (IK)
- **Algorithm**: Ed25519 (EdDSA) or X25519 (ECDH)
- **Key size**: 256 bits
- **Lifetime**: Long-term (years)
- **Rotation**: Rare, only in exceptional circumstances
- **Storage**: Secure storage (Android Keystore/Keychain)
- **Backup**: Optional encrypted backup

### Signed Prekey (SPK)
- **Algorithm**: X25519 (ECDH)
- **Key size**: 256 bits
- **Lifetime**: Medium-term (weeks to months)
- **Rotation**: Regular rotation (recommended: monthly)
- **Signature**: Signed by Identity Private Key
- **Purpose**: Enable initial key exchange without online availability

### Key Generation
- **CSPRNG**: Cryptographically secure random number generator
- **Hardware support**: Use hardware security modules when available
- **Entropy**: Sufficient entropy from multiple sources
- **Validation**: Validate generated keys for mathematical correctness

---

## Device Keys

### Purpose
- **Device-specific identity**: Unique cryptographic identity per device
- **Device authentication**: Authenticate device to server
- **Message encryption**: Participate in encrypted messaging
- **Device revocation**: Enable device-specific revocation

### Device Key Pair (DK)
- **Algorithm**: X25519 (ECDH)
- **Key size**: 256 bits
- **Lifetime**: Device lifetime
- **Rotation**: On device compromise or user request
- **Storage**: Secure storage (Android Keystore/Keychain)
- **Backup**: No backup (device-specific)

### Device Signed Prekey (DSPK)
- **Algorithm**: X25519 (ECDH)
- **Key size**: 256 bits
- **Lifetime**: Short-term (days to weeks)
- **Rotation**: Regular rotation (recommended: weekly)
- **Signature**: Signed by Device Private Key
- **Purpose**: Enable device-specific key exchange

### Device Binding
- **User identity signature**: Device keys signed by user identity key
- **Server verification**: Server verifies device-key binding
- **Device authentication**: Devices authenticate using device keys
- **Cross-device sync**: Device keys synced across user's devices

---

## Session Keys

### Purpose
- **Message encryption**: Encrypt individual messages
- **Forward secrecy**: Compromise doesn't expose past messages
- **Post-compromise security**: Recovery from key compromise
- **Efficient encryption**: Fast per-message operations

### Root Key (RK)
- **Algorithm**: HKDF-derived key
- **Key size**: 256 bits
- **Lifetime**: Session lifetime
- **Derivation**: Derived from DH exchange
- **Purpose**: Root of key derivation chain

### Chain Keys (CK)
- **Sending Chain Key (CKs)**: For sending messages
- **Receiving Chain Key (CKr)**: For receiving messages
- **Algorithm**: KDF (Key Derivation Function)
- **Key size**: 256 bits
- **Rotation**: Per message (ratchet)
- **Purpose**: Provide forward secrecy

### Message Keys (MK)
- **Algorithm**: AES-256-GCM or ChaCha20-Poly1305
- **Key size**: 256 bits
- **Lifetime**: Single message
- **Derivation**: Derived from chain keys
- **Purpose**: Encrypt individual messages

### Double Ratchet
- **Sending ratchet**: Advance sending chain key per message
- **Receiving ratchet**: Advance receiving chain key per message
- **DH ratchet**: Perform new DH exchange periodically
- **Skip ratchet**: Handle out-of-order messages

---

## Key Generation

### Cryptographically Secure Generation
- **CSPRNG**: Use cryptographically secure random number generator
- **Hardware entropy**: Prefer hardware RNG when available
- **Entropy accumulation**: Accumulate entropy from multiple sources
- **Quality testing**: Test generated keys for randomness

### Key Validation
- **Mathematical validation**: Validate key mathematical properties
- **Range checking**: Ensure keys are in valid range
- **Uniqueness**: Ensure key uniqueness within context
- **Strength verification**: Verify key strength meets requirements

### Generation Timing
- **On-demand**: Generate keys when needed
- **Pre-generation**: Pre-generate keys for performance
- **Batch generation**: Generate key batches when appropriate
- **Rotation scheduling**: Schedule key rotations in advance

---

## Key Storage

### Storage Requirements
- **Secure storage**: Use platform secure storage (Android Keystore, iOS Keychain)
- **Hardware protection**: Use hardware security modules when available
- **Access control**: Strict access controls for key access
- **Encryption at rest**: Keys encrypted when stored
- **Memory protection**: Protect keys in memory

### Private Key Storage
- **Never leave device**: Private keys never transmitted off-device
- **Secure enclave**: Use secure enclave when available
- **Biometric protection**: Require biometric authentication for access
- **Memory zeroing**: Zero memory after key use
- **No logging**: Never log private keys or derivatives

### Public Key Storage
- **Server storage**: Public keys stored on server
- **Distribution**: Public keys distributed to contacts
- **Caching**: Cache public keys for performance
- **Validation**: Validate public key signatures
- **Revocation**: Support public key revocation

### Key Backup
- **Optional backup**: Optional encrypted backup for identity keys
- **User-controlled**: User controls backup creation and deletion
- **Strong encryption**: Backup encrypted with user-selected passphrase
- **Separate storage**: Backup stored separately from device
- **Recovery mechanism**: Secure recovery mechanism for backup

---

## Key Rotation

### Rotation Triggers
- **Time-based**: Regular scheduled rotation
- **Compromise**: Immediate rotation on compromise
- **User request**: User-initiated rotation
- **Security policy**: Policy-driven rotation
- **Key age**: Rotation based on key age

### Rotation Strategies
- **Gradual rotation**: Gradual rollout of new keys
- **Immediate rotation**: Immediate switch to new keys
- **Dual operation**: Operate with old and new keys during transition
- **Contact notification**: Notify contacts of key changes
- **Grace period**: Grace period for transition

### Identity Key Rotation
- **Rare event**: Identity key rotation should be rare
- **Strong authentication**: Require strong authentication
- **Contact notification**: Notify all contacts
- **Key continuity**: Maintain continuity with old keys
- **Verification**: Encourage out-of-band verification

### Session Key Rotation
- **Per message**: Automatic per-message rotation (ratchet)
- **DH ratchet**: Periodic DH ratchet (recommended: per conversation)
- **Time-based**: Time-based rotation as fallback
- **Message count**: Rotation after N messages

---

## Key Revocation

### Revocation Triggers
- **Device compromise**: Immediate revocation on device compromise
- **User request**: User-initiated revocation
- **Security policy**: Policy-driven revocation
- **Inactivity**: Revocation after extended inactivity
- **Security audit**: Audit-driven revocation

### Revocation Process
- **Immediate effect**: Revocation takes effect immediately
- **Server notification**: Server notified of revocation
- **Contact notification**: Contacts notified of revocation
- **Key invalidation**: Invalidated keys marked as such
- **Session termination**: Active sessions terminated

### Revocation Verification
- **Revocation lists**: Maintain revocation lists
- **Online verification**: Verify revocation status online
- **Offline verification**: Support offline revocation verification
- **Caching**: Cache revocation status for performance
- **TTL**: Time-to-live for cached revocation status

---

## Key Backup

### Backup Types
- **Identity key backup**: Backup of long-term identity keys
- **Device key backup**: No backup for device keys (device-specific)
- **Session key backup**: No backup for session keys (ephemeral)
- **Settings backup**: Backup of user settings and preferences

### Backup Security
- **User-controlled**: User controls backup creation
- **Strong encryption**: Backup encrypted with user passphrase
- **Separate storage**: Backup stored separately from device
- **Access control**: Strict access controls for backup
- **Secure deletion**: Secure deletion of backup when requested

### Backup Recovery
- **Authentication**: Strong authentication for recovery
- **Verification**: Verify backup integrity before recovery
- **Key validation**: Validate recovered keys
- **Contact notification**: Notify contacts of recovery
- **Audit logging**: Log all recovery operations

---

## Key Recovery

### Recovery Scenarios
- **Device loss**: Recovery after device loss
- **Device compromise**: Recovery after device compromise
- **User error**: Recovery after user error
- **System failure**: Recovery after system failure

### Recovery Methods
- **Backup recovery**: Recovery from backup
- **Multi-device recovery**: Recovery from other devices
- **Recovery codes**: Recovery using recovery codes
- **Social recovery**: Recovery through trusted contacts
- **No recovery**: No recovery mechanism (most secure)

### Recovery Security
- **Strong authentication**: Strong authentication for recovery
- **Multi-factor**: Multi-factor authentication recommended
- **Rate limiting**: Limit recovery attempts
- **Audit logging**: Log all recovery attempts
- **Notification**: Notify user of recovery attempts

---

## Device Change

### Device Addition
- **Key generation**: Generate new device keys
- **Key binding**: Bind device keys to user identity
- **Key sync**: Sync necessary keys to new device
- **Contact notification**: Notify contacts of new device
- **Authentication**: Strong authentication for device addition

### Device Removal
- **Key revocation**: Revoke device keys
- **Session termination**: Terminate device sessions
- **Contact notification**: Notify contacts of device removal
- **Data cleanup**: Optional cleanup of device data
- **Audit logging**: Log device removal

### Device Replacement
- **Add then remove**: Add new device, then remove old device
- **Key continuity**: Maintain key continuity where possible
- **Data migration**: Migrate data to new device
- **Contact notification**: Notify contacts of device change
- **Authentication**: Strong authentication for device replacement

---

## Security Requirements

### SEC-KEY-001
Private keys must never leave the device they were generated on.

### SEC-KEY-002
All key generation must use cryptographically secure random number generators.

### SEC-KEY-003
Identity keys must be stored in platform secure storage (Android Keystore/Keychain).

### SEC-KEY-004
Session keys must provide forward secrecy through regular rotation.

### SEC-KEY-005
Key compromise must trigger immediate key rotation.

### SEC-KEY-006
Device keys must be unique per device and not shared across devices.

### SEC-KEY-007
Key backup must be optional and user-controlled.

### SEC-KEY-008
Key revocation must take effect immediately.

### SEC-KEY-009
Key changes must be cryptographically signed by appropriate authority.

### SEC-KEY-010
All key operations must be logged and audited.

---

## Implementation Considerations

### Key Storage APIs
- **Android**: Android Keystore, KeyStore API
- **iOS**: Keychain Services, CryptoKit
- **Cross-platform**: Platform-specific secure storage

### Key Generation Libraries
- **Ed25519**: libsodium, TweetNaCl
- **X25519**: libsodium, TweetNaCl
- **HKDF**: Crypto++ libsodium
- **AES**: Crypto++, libsodium

### Key Management
- **Key lifecycle**: Comprehensive key lifecycle management
- **Key rotation**: Automated key rotation where possible
- **Key backup**: User-controlled key backup
- **Key recovery**: Secure key recovery mechanisms

---

## Open Decisions

### OPEN-KEY-001
Should identity key backup be mandatory or optional?

### OPEN-KEY-002
What is the recommended rotation period for signed prekeys?

### OPEN-KEY-003
Should there be a recovery mechanism for lost identity keys?

### OPEN-KEY-004
What is the maximum number of devices per user for key management?

### OPEN-KEY-005
Should session keys use AES-256-GCM or ChaCha20-Poly1305?

### OPEN-KEY-006
How should the system handle key rotation during active conversations?

### OPEN-KEY-007
Should there be a social recovery mechanism for key recovery?