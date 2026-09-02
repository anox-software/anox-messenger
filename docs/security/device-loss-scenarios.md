> **Status:** HISTORICAL / SUPERSEDED
> **Architecture Baseline:** Raw1.1
> **Last synchronized:** 2026-08-19
> **Do not use as current implementation specification.**
> **Current direction:** V1 one active device, no recovery. A new device creates a new V1 cryptographic identity.
> **Superseded by:** `docs/authority/B025/TRACK_B/B013_LIFECYCLE.md` and `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md#B-013` (B-013 v1.3).

# Device Loss Scenarios Analysis - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document analyzes various device loss scenarios and their implications for security and user experience in the anoX Messenger system.

---

## Scenario A: Device Lost, Private Key Not Exportable

### Description
User loses device and the private key was not exportable (most secure scenario).

### Security Implications
- **High security**: Maximum security - private key remains on lost device
- **No key exposure**: No risk of private key exposure
- **Limited impact**: Impact limited to messages already decrypted on device
- **Forward secrecy**: Forward secrecy protects past messages

### User Experience Implications
- **Data loss**: Loss of all locally stored data
- **Account recovery**: Need for account recovery mechanism
- **Device replacement**: Need to set up new device
- **Message history**: Loss of message history unless synced

### Recommended Response
1. **Immediate revocation**: User should immediately revoke lost device
2. **Authentication**: Strong authentication required for revocation
3. **New device setup**: User sets up new device
4. **Key regeneration**: Generate new device keys on new device
5. **Data sync**: Sync available data from server or other devices
6. **Contact notification**: Optionally notify contacts of device change

### Security Rating: ⭐⭐⭐⭐⭐
### User Experience Rating: ⭐⭐☆☆☆

---

## Scenario B: New Device

### Description
User gets a new device and wants to add it to their account.

### Security Implications
- **Moderate security**: Security depends on device addition process
- **Key generation**: New device generates new keys
- **Attack surface**: Increases attack surface with additional device
- **Key synchronization**: Requires secure key synchronization

### User Experience Implications
- **Setup process**: Setup process for new device
- **Data sync**: Message history sync to new device
- **Verification**: May require verification from existing device
- **Gradual setup**: Potential for gradual setup process

### Recommended Response
1. **Device addition**: User initiates device addition from existing device
2. **Authentication**: Strong authentication for device addition
3. **Key generation**: New device generates unique device keys
4. **Key binding**: New device keys bound to user identity
5. **Data sync**: Secure sync of data to new device
6. **Verification**: Verification from existing device

### Security Rating: ⭐⭐⭐⭐☆
### User Experience Rating: ⭐⭐⭐⭐☆

---

## Scenario C: User Wants to Continue Using Old Account

### Description
User loses device but wants to continue using their existing anoX account.

### Security Implications
- **Variable security**: Security depends on recovery mechanism
- **Account continuity**: Maintains account continuity
- **Key rotation**: May require key rotation
- **Authentication**: Strong authentication required for recovery

### User Experience Implications
- **Account preservation**: User maintains their anoX-ID and identity
- **Social continuity**: Maintains existing contacts and relationships
- **Recovery process**: Recovery process may be complex
- **Data continuity**: Potential for data continuity

### Recommended Response
1. **Account recovery**: User initiates account recovery
2. **Authentication**: Strong multi-factor authentication
3. **Identity verification**: Verify user identity through multiple factors
4. **Key management**: Generate new keys or recover existing keys
5. **Device setup**: Set up new device with recovered account
6. **Contact notification**: Notify contacts of recovery (optional)

### Security Rating: ⭐⭐⭐☆☆
### User Experience Rating: ⭐⭐⭐⭐☆

---

## Scenario D: Private Key Compromised

### Description
User's private key is compromised (e.g., through malware or device theft).

### Security Implications
- **Critical security**: Critical security incident
- **Message exposure**: Potential exposure of past and future messages
- **Identity compromise**: Potential identity compromise
- **Forward secrecy**: Forward secrecy may protect some past messages

### User Experience Implications
- **Urgent action**: Requires urgent user action
- **Key rotation**: Requires immediate key rotation
- **Contact notification**: Should notify contacts of compromise
- **Service disruption**: Potential service disruption during recovery

### Recommended Response
1. **Immediate revocation**: Immediately revoke compromised device
2. **Key rotation**: Rotate all compromised keys
3. **Identity rotation**: Consider rotating user identity keys
4. **Contact notification**: Notify all contacts of potential compromise
5. **Security audit**: Conduct security audit of other devices
6. **Monitoring**: Monitor for suspicious activity

### Security Rating: ⭐☆☆☆☆
### User Experience Rating: ⭐☆☆☆☆

---

## Scenario E: Device Should Be Permanently Revoked

### Description
User wants to permanently revoke a device (e.g., selling device, employee leaving).

### Security Implications
- **High security**: Permanent revocation provides good security
- **Key invalidation**: Device keys permanently invalidated
- **Access removal**: Complete removal of device access
- **Data cleanup**: Potential cleanup of device-specific data

### User Experience Implications
- **Clear process**: Clear revocation process
- **Confirmation**: Requires confirmation to prevent accidental revocation
- **Data impact**: Impact on data synced to device
- **Recovery difficulty**: Difficult to recover from accidental revocation

### Recommended Response
1. **Revocation request**: User requests permanent device revocation
2. **Authentication**: Strong authentication for revocation
3. **Confirmation**: Clear confirmation of revocation intent
4. **Key invalidation**: Invalidate device keys
5. **Session termination**: Terminate all device sessions
6. **Data cleanup**: Optional cleanup of device-specific data
7. **Notification**: Notify user and other devices of revocation

### Security Rating: ⭐⭐⭐⭐⭐
### User Experience Rating: ⭐⭐⭐☆☆

---

## Comparative Analysis

### Security vs. User Experience Trade-offs

| Scenario | Security | User Experience | Best For |
|----------|----------|------------------|----------|
| A: Lost Device, No Export | ⭐⭐⭐⭐⭐ | ⭐⭐☆☆☆ | Maximum security requirements |
| B: New Device | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐☆ | Normal device addition |
| C: Continue Old Account | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐☆ | Account continuity |
| D: Key Compromised | ⭐☆☆☆☆ | ⭐☆☆☆☆ | Emergency response |
| E: Permanent Revocation | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ | Device lifecycle management |

### Recovery Complexity

| Scenario | Recovery Complexity | Time to Recovery | User Effort |
|----------|---------------------|------------------|-------------|
| A: Lost Device, No Export | High | Medium-High | High |
| B: New Device | Low | Low | Low |
| C: Continue Old Account | Medium | Medium | Medium |
| D: Key Compromised | Very High | High | Very High |
| E: Permanent Revocation | Low | Low | Low |

### Data Loss Risk

| Scenario | Data Loss Risk | Recoverable Data | Permanent Loss |
|----------|----------------|------------------|----------------|
| A: Lost Device, No Export | High | Server-synced data | Local data only |
| B: New Device | Low | Most data | Minimal |
| C: Continue Old Account | Medium | Server-synced data | Some local data |
| D: Key Compromised | High | Server-synced data | Potentially high |
| E: Permanent Revocation | Low | Server-synced data | Device-specific data |

---

## Prevention Strategies

### Before Device Loss
- **Regular backups**: Encourage regular encrypted backups
- **Multi-device**: Encourage multi-device setup for redundancy
- **Key export**: Optional secure key export for advanced users
- **Education**: User education on security best practices

### During Device Use
- **Strong authentication**: Strong device authentication
- **Auto-lock**: Automatic device locking
- **Secure storage**: Secure storage of sensitive data
- **Monitoring**: Monitor for suspicious activity

### After Device Loss
- **Quick response**: Quick response to device loss
- **Remote revocation**: Remote device revocation capability
- **Clear guidance**: Clear guidance for users
- **Support access**: Easy access to support

---

## Security Requirements

### SEC-LOSS-001
Users must be able to remotely revoke lost or compromised devices.

### SEC-LOSS-002
Device revocation must take effect immediately.

### SEC-LOSS-003
Device addition must require strong authentication from existing device.

### SEC-LOSS-004
Account recovery must require multi-factor authentication.

### SEC-LOSS-005
Key compromise must trigger immediate key rotation and contact notification.

### SEC-LOSS-006
Permanent device revocation must require explicit user confirmation.

### SEC-LOSS-007
The system must support account continuity after device loss.

### SEC-LOSS-008
The system must minimize data loss after device loss where possible.

### SEC-LOSS-009
All device loss events must be logged and audited.

### SEC-LOSS-010
The system must provide clear guidance for device loss scenarios.

---

## Implementation Considerations

### Device Revocation API
```kotlin
suspend fun revokeDevice(deviceId: String, context: RevocationContext) {
    // Authenticate user
    authenticateUser(context)

    // Revoke device
    invalidateDeviceKeys(deviceId)

    // Terminate sessions
    terminateDeviceSessions(deviceId)

    // Notify user
    notifyUserOfRevocation(deviceId)

    // Notify other devices
    notifyOtherDevices(deviceId)

    // Log event
    logDeviceRevocation(deviceId, context)
}
```

### Account Recovery API
```kotlin
suspend fun recoverAccount(recoveryContext: RecoveryContext) {
    // Multi-factor authentication
    authenticateMFA(recoveryContext)

    // Verify identity
    verifyUserIdentity(recoveryContext)

    // Generate new keys or recover existing
    val keys = generateOrRecoverKeys(recoveryContext)

    // Set up new device
    setupNewDevice(keys)

    // Sync data
    syncUserData()

    // Notify contacts (optional)
    notifyContactsOfRecovery()
}
```

---

## Open Decisions

### OPEN-LOSS-001
Should private key export be an optional feature for advanced users?

### OPEN-LOSS-002
What is the appropriate recovery mechanism for account recovery?

### OPEN-LOSS-003
How should the system handle key rotation during account recovery?

### OPEN-LOSS-004
Should contacts be automatically notified of device loss or key compromise?

### OPEN-LOSS-005
What is the appropriate grace period for accidental device revocation?

### OPEN-LOSS-006
How should the system balance security vs. user experience in recovery scenarios?

### OPEN-LOSS-007
Should there be different recovery mechanisms for different user types?
