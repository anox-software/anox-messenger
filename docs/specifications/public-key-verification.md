> **Status:** HISTORICAL / SUPERSEDED
> **Architecture Baseline:** Raw1.1
> **Last synchronized:** 2026-08-19
> **Do not use as current implementation specification.**
> **Current direction:** SAS/QR with local trust states; no custom safety-number protocol; canonical trust states in B-010 v1.3.
> **Superseded by:** `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md#B-010` (B-010 v1.3) and `docs/authority/B025/TRACK_B/B010_CONTACTS_VERIFICATION.md`.

# Public-Key Verification Specification - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document specifies how users can verify that a public key belongs to the intended person, ensuring trust establishment in the anoX Messenger system.

---

## Verification Methods

### 1. Key Fingerprints

### Description
Cryptographic hash of the public key that can be compared out-of-band.

### Implementation
- **Algorithm**: SHA-256
- **Format**: Hexadecimal string
- **Length**: 64 characters (256 bits)
- **Display**: Truncated display (first 8 and last 8 characters) for usability
- **Full access**: Option to view full fingerprint

### User Experience
```
Contact: John Doe
anoX-ID: AX-7K4M92QPR3ST
Key Fingerprint: A3F7B2C1...D8E9F4A6
[View Full Fingerprint]
```

### Security Properties
- **Out-of-band verification**: Users can compare fingerprints via separate channel
- **Manual process**: Requires manual comparison and verification
- **User burden**: High cognitive load for users
- **Risk**: Users may not perform verification correctly

### Advantages
- **Simple to implement**: Straightforward technical implementation
- **Flexible**: Can be used via any communication channel
- **No additional infrastructure**: Requires no additional infrastructure
- **Standard approach**: Well-understood approach in security community

### Disadvantages
- **User error prone**: Users may make mistakes in comparison
- **Channel security**: Requires secure out-of-band channel
- **Inconvenient**: Requires manual effort for each verification
- **Not scalable**: Difficult to scale for many contacts

---

### 2. QR Code Verification

### Description
QR codes containing public key information that can be scanned for verification.

### Implementation
- **Content**: Public key fingerprint + anoX-ID + timestamp
- **Format**: Standard QR code (version 4, error correction level M)
- **Size**: Approximately 100x100 pixels
- **Scanning**: Built-in QR code scanner in app

### User Experience
```
Verification Method:
[Show QR Code] [Scan QR Code]

1. Both users open verification screen
2. User A selects "Show QR Code"
3. User B selects "Scan QR Code"
4. User B scans User A's QR code
5. App verifies key match
6. Both users confirm verification
```

### Security Properties
- **In-person verification**: Designed for in-person verification
- **Automated comparison**: App performs automated comparison
- **Reduced user error**: Less prone to user error than manual comparison
- **Physical proximity**: Requires physical proximity (can be feature or limitation)

### Advantages
- **User-friendly**: Easier for users than manual fingerprint comparison
- **Automated**: App performs verification automatically
- **Reduced errors**: Less prone to user error
- **Standard**: Users familiar with QR codes

### Disadvantages
- **Physical proximity**: Requires physical proximity
- **Not remote**: Not suitable for remote verification
- **QR security**: QR codes can be copied or photographed
- **Device compatibility**: Requires camera and QR scanning capability

---

### 3. Safety Numbers

### Description
Short numeric codes derived from public key fingerprints, similar to Signal's safety numbers.

### Implementation
- **Algorithm**: Phonetic encoding of fingerprint
- **Format**: 5 groups of 5 digits (25 digits total)
- **Phonetic mapping**: Map digits to words for easier verification
- **Comparison**: Users compare safety numbers digit by digit

### User Experience
```
Contact: John Doe
anoX-ID: AX-7K4M92QPR3ST
Safety Number:
24 51 89 33 76
12 45 78 90 23
56 89 12 34 67
[Compare Safety Numbers]
```

### Phonetic Version (Alternative)
```
Contact: John Doe
anoX-ID: AX-7K4M92QPR3ST
Safety Number:
blue-frog-tree-sun-book
apple-star-moon-cat-dog
[Compare Safety Numbers]
```

### Security Properties
- **Human-readable**: Designed for human readability and comparison
- **Out-of-band**: Can be compared via any channel
- **Memorable**: Phonetic version easier to remember
- **Partial verification**: Users can verify partially (first few groups)

### Advantages
- **User-friendly**: Easier for users than hexadecimal fingerprints
- **Flexible**: Can be used via any communication channel
- **Memorable**: Phonetic version easier to remember
- **Partial verification**: Supports partial verification

### Disadvantages
- **Manual process**: Still requires manual comparison
- **Channel security**: Requires secure out-of-band channel
- **Reduced entropy**: Fewer bits than full fingerprint
- **User burden**: Still requires user effort

---

### 4. Key Change Notifications

### Description
Automatic warnings when a contact's public key changes.

### Implementation
- **Detection**: Automatic detection of public key changes
- **Notification**: In-app notification of key change
- **Verification prompt**: Prompt user to verify new key
- **Grace period**: Grace period for key verification
- **Historical records**: Maintain historical key records

### User Experience
```
⚠️ Key Change Detected

John Doe's public key has changed.
Old key: A3F7B2C1...D8E9F4A6
New key: F5E8D2C9...B7A4E3F1

Possible reasons:
- John got a new device
- John's key was compromised
- This is not actually John

[Verify New Key] [Mark as Trusted] [Report Suspicious]
```

### Security Properties
- **Automatic detection**: Automatic detection of key changes
- **User awareness**: Raises user awareness of potential attacks
- **Verification opportunity**: Provides opportunity for verification
- **Risk of habituation**: Users may become habituated to warnings

### Advantages
- **Automatic**: No user action required for detection
- **Security-focused**: Addresses key substitution attacks
- **User control**: User decides how to respond
- **Historical context**: Provides historical context

### Disadvantages
- **False positives**: May generate false positives (legitimate key changes)
- **User fatigue**: Users may become fatigued by warnings
- **Habituation**: Users may habitually dismiss warnings
- **Complexity**: Adds complexity to key management

---

## Verification Workflow

### Initial Contact Verification
1. **Contact discovery**: User discovers contact (via anoX-ID or other method)
2. **Key exchange**: Public keys exchanged via server
3. **Verification prompt**: App prompts user to verify contact
4. **Verification method**: User selects verification method
5. **Verification process**: User performs verification
6. **Trust establishment**: Contact marked as verified
7. **Future communication**: Future communications use verified keys

### Ongoing Verification
1. **Key change detection**: Automatic detection of key changes
2. **Change notification**: User notified of key change
3. **Verification prompt**: Prompt user to verify new key
4. **Verification process**: User performs verification
5. **Trust update**: Trust status updated based on verification
6. **Historical record**: Historical record maintained

### Re-verification
1. **User initiation**: User can initiate re-verification at any time
2. **Verification method**: User selects verification method
3. **Verification process**: User performs verification
4. **Trust confirmation**: Trust status confirmed or updated

---

## Trust Levels

### Unverified
- **Definition**: Contact not verified
- **Behavior**: App warns about unverified status
- **Limitations**: May limit functionality for unverified contacts
- **Visual indicator**: Clear visual indicator of unverified status

### Verified
- **Definition**: Contact verified through one or more methods
- **Behavior**: Normal functionality
- **Visual indicator**: Visual indicator of verified status
- **Verification method**: Record of verification method used

### Trusted
- **Definition**: Contact verified and marked as trusted
- **Behavior**: Enhanced functionality (if applicable)
- **Visual indicator**: Distinct visual indicator of trusted status
- **User control**: User explicitly marks as trusted

### Compromised
- **Definition**: Contact marked as compromised
- **Behavior**: Limited or blocked functionality
- **Visual indicator**: Clear warning indicator
- **User action**: User action required to restore

---

## User Interface Considerations

### Verification Prompts
- **Clear language**: Use clear, non-technical language
- **Actionable**: Provide clear, actionable options
- **Educational**: Include educational content about importance
- **Context**: Provide context for why verification is important

### Visual Indicators
- **Consistent**: Consistent visual indicators across app
- **Color-coded**: Use color coding for trust levels
- **Accessible**: Ensure accessibility for all users
- **Prominent**: Make trust status prominent in UI

### Progressive Disclosure
- **Initial simplicity**: Simple initial interface
- **Progressive detail**: Progressive disclosure of details
- **Advanced options**: Advanced options for power users
- **Contextual help**: Contextual help and explanations

---

## Security Requirements

### SEC-VERIFY-001
The system must provide multiple methods for public key verification.

### SEC-VERIFY-002
The system must automatically detect and notify users of public key changes.

### SEC-VERIFY-003
The system must use cryptographically secure fingerprints for verification.

### SEC-VERIFY-004
The system must maintain historical records of public key changes.

### SEC-VERIFY-005
The system must clearly indicate verification status in the user interface.

### SEC-VERIFY-006
The system must not allow unverified keys to be used without user awareness.

### SEC-VERIFY-007
The system must provide clear, actionable prompts for key verification.

### SEC-VERIFY-008
The system must support out-of-band verification methods.

### SEC-VERIFY-009
The system must maintain the security of verification processes.

### SEC-VERIFY-010
The system must educate users about the importance of key verification.

---

## Implementation Considerations

### Fingerprint Generation
```kotlin
fun generateFingerprint(publicKey: ByteArray): String {
    val digest = MessageDigest.getInstance("SHA-256")
    val hash = digest.digest(publicKey)
    return hash.joinToString("") { "%02x".format(it) }
}
```

### Safety Number Generation
```kotlin
fun generateSafetyNumber(fingerprint: String): String {
    // Map fingerprint to safety number format
    // Phonetic encoding for user-friendly display
}
```

### QR Code Generation
```kotlin
fun generateVerificationQRCode(publicKey: ByteArray, anoXId: String): Bitmap {
    val data = mapOf(
        "fingerprint" to generateFingerprint(publicKey),
        "anoXId" to anoXId,
        "timestamp" to System.currentTimeMillis()
    )
    // Generate QR code from data
}
```

---

## Open Decisions

### OPEN-VERIFY-001
Which verification methods should be implemented as primary vs. secondary?

### OPEN-VERIFY-002
Should the system implement a trust-on-first-use (TOFU) model?

### OPEN-VERIFY-003
How should the system handle verification for group conversations?

### OPEN-VERIFY-004
What is the appropriate frequency for re-verification prompts?

### OPEN-VERIFY-005
Should the system implement social verification (friends verifying friends)?

### OPEN-VERIFY-006
How should the system handle verification for business/organizational accounts?

### OPEN-VERIFY-007
Should the system implement automated verification through trusted third parties?
