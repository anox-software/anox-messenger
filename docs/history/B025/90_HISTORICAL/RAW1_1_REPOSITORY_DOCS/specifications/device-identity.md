> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current direction:** V1 one active device, no multi-device sync, random `device_id`, device auth separate.  
> **Superseded by:** `docs/current/ACCOUNT_DEVICE_LIFECYCLE.md` and `docs/current/SECURITY_INVARIANTS.md`  

# Device Identity Specification - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document specifies the device identity system for anoX Messenger, including the separation between user identity and device identity.

---

## User vs. Device Identity Separation

### Conceptual Model
```
User (anoX-ID: AX-7K4M92QPR3ST)
├── Device A (Device-ID: D1-ABC123)
├── Device B (Device-ID: D2-DEF456)
└── Device C (Device-ID: D3-GHI789)
```

### Key Principles
- **User Identity**: Persistent across devices, tied to anoX-ID
- **Device Identity**: Specific to each device, independently managed
- **Separation**: Compromise of one device should not compromise others
- **Revocation**: Devices can be individually revoked without affecting user identity

---

## Device Identity Structure

### Device-ID Format
```
D1-ABC123XYZ
```

- **Prefix**: "D" followed by sequential number (D1, D2, etc.)
- **Device-specific segment**: 9-character alphanumeric
- **Total length**: 12 characters
- **Entropy**: 9 characters × ~5.85 bits = ~52.6 bits
- **Purpose**: Uniquely identify each device within a user's account

### Device Metadata
- **Device name**: User-assigned name (e.g., "iPhone", "Work Laptop")
- **Device type**: Mobile, desktop, tablet, etc.
- **OS version**: Operating system version
- **App version**: anoX app version
- **Last active**: Timestamp of last activity
- **Registration date**: When device was added to account

---

## Device Addition

### Registration Flow
1. **User initiates**: User selects "Add Device" on existing device
2. **Authentication**: User authenticates with existing device
3. **QR code generation**: Existing device generates QR code with registration token
4. **New device scan**: New device scans QR code
5. **Device registration**: New device contacts server with registration token
6. **Key generation**: New device generates device-specific key pair
7. **Key upload**: New device uploads public key to server
8. **Confirmation**: Existing device confirms new device registration
9. **Sync**: Existing device syncs necessary data to new device

### Security Requirements
- **Multi-factor verification**: At least two factors for device addition
- **User confirmation**: Explicit user confirmation required
- **Time-limited tokens**: Registration tokens expire after short period
- **Rate limiting**: Limit device addition attempts
- **Device limits**: Maximum number of devices per user (configurable)
- **Notification**: Other devices notified of new device addition

### Alternative: Email/Phone Verification
1. **User initiates**: User requests device addition via email/phone
2. **Verification code**: System sends verification code to email/phone
3. **Code entry**: User enters verification code on new device
4. **Device registration**: New device completes registration
5. **Confirmation**: User confirms on existing device

---

## Device Removal

### Revocation Flow
1. **User initiates**: User selects device to remove
2. **Authentication**: User authenticates (MFA recommended)
3. **Confirmation**: User confirms removal
4. **Server notification**: Server notified of device revocation
5. **Key invalidation**: Device's public key marked as invalid
6. **Session termination**: All active sessions terminated
7. **Data cleanup**: Optional cleanup of device-specific data
8. **Notification**: Other devices notified of removal

### Security Requirements
- **Authentication required**: Strong authentication for device removal
- **Immediate effect**: Revocation takes effect immediately
- **Notification**: User and other devices notified
- **Grace period**: Short grace period for accidental removals
- **Audit logging**: All removals logged and audited

### Self-Removal
- **Device-initiated**: Device can remove itself from account
- **Authentication required**: User must authenticate
- **Confirmation**: User confirms removal on other device
- **Immediate effect**: Takes effect immediately after confirmation

---

## Lost Device Handling

### Immediate Actions
1. **User reports**: User reports device as lost
2. **Remote revocation**: User remotely revokes lost device
3. **Authentication**: Strong authentication required
4. **Key invalidation**: Lost device's keys invalidated
5. **Session termination**: All sessions terminated
6. **Notification**: Other devices notified

### Security Considerations
- **No private key exposure**: Lost device's private key remains on device
- **No message decryption**: Lost device cannot decrypt new messages
- **Historical access**: Lost device retains access to already decrypted messages
- **Timeline**: Revocation timeline critical (immediate preferred)

### Recovery Options
- **Add new device**: User can add replacement device
- **Data sync**: Historical messages sync to new device (if available)
- **No automatic recovery**: No automatic recovery of lost device access

---

## Compromised Device Handling

### Detection
- **Anomaly detection**: Unusual device behavior detected
- **User report**: User reports suspected compromise
- **Security audit**: Security audit reveals compromise indicators
- **Automated alerts**: Automated security alerts triggered

### Response Actions
1. **Immediate revocation**: Device immediately revoked
2. **Key rotation**: User's long-term keys rotated (if necessary)
3. **Contact notification**: Contacts notified of potential compromise
4. **Message review**: Review messages sent during compromise window
5. **Security audit**: Comprehensive security audit
6. **Forensic analysis**: Analyze extent of compromise

### Security Requirements
- **Immediate action**: Compromised devices revoked immediately
- **Key rotation**: Consider rotating user's cryptographic keys
- **Notification**: Transparent notification to affected parties
- **Audit**: Comprehensive audit of compromise impact

---

## Multi-Device Architecture

### Synchronization Model
- **Message sync**: Messages synchronized across all user devices
- **Key sync**: Public keys synchronized across devices
- **Contact sync**: Contact list synchronized across devices
- **Settings sync**: User settings synchronized across devices

### Consistency Requirements
- **Eventual consistency**: Accept eventual consistency for some data
- **Strong consistency**: Strong consistency for security-critical data
- **Conflict resolution**: Clear conflict resolution policies
- **Ordering**: Message ordering preserved across devices

### Offline Support
- **Offline access**: Devices can operate offline
- **Queueing**: Offline changes queued for sync
- **Conflict detection**: Detect and resolve sync conflicts
- **Background sync**: Background synchronization when online

---

## Device Limits

### Maximum Devices
- **Default limit**: 5 devices per user (configurable)
- **Premium limit**: Higher limits for premium users
- **Enterprise limits**: Custom limits for enterprise users
- **Graceful handling**: Graceful handling when limit reached

### Device Types
- **Mobile devices**: Phones, tablets
- **Desktop devices**: Laptops, desktops
- **Web browsers**: Browser-based access (if supported)
- **Special devices**: IoT devices, wearables (future consideration)

### Active vs. Inactive
- **Active devices**: Recently used devices
- **Inactive devices**: Devices not used for extended period
- **Auto-revocation**: Automatic revocation of long-inactive devices
- **User notification**: Notify before auto-revocation

---

## Device Authentication

### Device-Specific Authentication
- **Device keys**: Each device has unique key pair
- **Device certificates**: Optional device certificates
- **Device tokens**: Short-lived device authentication tokens
- **Biometric authentication**: Biometric authentication on device

### Session Management
- **Session tokens**: Short-lived session tokens
- **Refresh tokens**: Long-lived refresh tokens
- **Token rotation**: Regular token rotation
- **Session invalidation**: Ability to invalidate sessions

### Multi-Factor Authentication
- **Device factor**: Something you have (device)
- **Knowledge factor**: Something you know (password/PIN)
- **Biometric factor**: Something you are (fingerprint, face)
- **Location factor**: Somewhere you are (location-based)

---

## Security Requirements

### SEC-DEV-001
Each device must have a unique device identity separate from user identity.

### SEC-DEV-002
Device addition must require multi-factor authentication.

### SEC-DEV-003
Device revocation must take effect immediately.

### SEC-DEV-004
Compromise of one device must not compromise other devices.

### SEC-DEV-005
Device private keys must never leave the device.

### SEC-DEV-006
Device addition must be confirmed by existing device.

### SEC-DEV-007
Maximum number of devices per user must be enforced.

### SEC-DEV-008
Inactive devices must be automatically revoked after extended period.

### SEC-DEV-009
Device authentication must use short-lived tokens with rotation.

### SEC-DEV-010
All device changes must be logged and audited.

---

## Implementation Considerations

### Data Model
```json
{
  "userId": "AX-7K4M92QPR3ST",
  "devices": [
    {
      "deviceId": "D1-ABC123XYZ",
      "deviceName": "iPhone",
      "deviceType": "mobile",
      "publicKey": "...",
      "lastActive": "2024-01-15T10:30:00Z",
      "registeredAt": "2024-01-01T08:00:00Z",
      "status": "active"
    }
  ]
}
```

### API Endpoints
- `POST /devices/register` - Register new device
- `DELETE /devices/{deviceId}` - Remove device
- `GET /devices` - List user devices
- `PUT /devices/{deviceId}/name` - Update device name
- `POST /devices/{deviceId}/revoke` - Revoke device

### Error Handling
- **Device not found**: Clear error message
- **Device limit reached**: Inform user of limit
- **Authentication failed**: Generic authentication error
- **Device already registered**: Clear error message

---

## Open Decisions

### OPEN-DEV-001
What is the maximum number of devices allowed per user?

### OPEN-DEV-002
What is the inactivity period before automatic device revocation?

### OPEN-DEV-003
Should web browser access be supported as a device type?

### OPEN-DEV-004
What is the device registration token expiration time?

### OPEN-DEV-005
Should device addition require email/phone verification in addition to existing device confirmation?

### OPEN-DEV-006
How should the system handle device synchronization conflicts?

### OPEN-DEV-007
Should there be different device classes with different capabilities?