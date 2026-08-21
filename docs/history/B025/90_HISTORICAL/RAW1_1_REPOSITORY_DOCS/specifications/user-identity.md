> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current direction:** random `account_id`, username/QR public identifier, no phone/email, no global directory.  
> **Superseded by:** `docs/current/ACCOUNT_LICENSE_REGISTRATION.md`  

# User Identity Specification - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document specifies the user identity system for anoX Messenger, including the anoX-ID format and its relationship to cryptographic identity.

---

## anoX-ID Format

### Proposed Format
```
AX-7K4M-92QP
```

### Structure Analysis
- **Prefix**: "AX" (anoX identifier)
- **Segments**: Two 4-character alphanumeric segments
- **Total length**: 11 characters (including hyphens)
- **Character set**: Alphanumeric (A-Z, 0-9) - case-insensitive
- **Entropy**: 8 characters × ~5.85 bits = ~47 bits of entropy

### Alternative Format Consideration
For better security and collision resistance:
```
AX-7K4M92QPR3ST
```
- **Single segment**: 10-character alphanumeric
- **Total length**: 13 characters (including prefix and hyphen)
- **Entropy**: 10 characters × ~5.85 bits = ~58.5 bits of entropy

---

## Generation Analysis

### Random Generation Requirements
- **Cryptographically secure random number generator (CSPRNG)**
- **Sufficient entropy source** (hardware RNG, system entropy)
- **Collision resistance**: Acceptable collision probability < 10^-9
- **Uniqueness guarantee**: Server-side uniqueness verification

### Collision Probability Analysis

#### Format 1 (8 characters): ~47 bits entropy
- **Total possible IDs**: 36^8 ≈ 2.8 × 10^12
- **Birthday paradox at 1M users**: ~0.02% collision probability
- **Birthday paradox at 10M users**: ~1.7% collision probability
- **Assessment**: Insufficient for large-scale deployment

#### Format 2 (10 characters): ~58.5 bits entropy
- **Total possible IDs**: 36^10 ≈ 3.6 × 10^15
- **Birthday paradox at 1M users**: ~0.00014% collision probability
- **Birthday paradox at 10M users**: ~0.014% collision probability
- **Birthday paradox at 100M users**: ~1.4% collision probability
- **Assessment**: Acceptable for moderate scale, may need extension for massive scale

### Recommendation
Use 10-character format (58.5 bits entropy) with server-side uniqueness verification.

---

## Enumeration Protection

### Risks
- **User discovery**: Sequential or predictable IDs allow user enumeration
- **Privacy violation**: Attackers can discover registered users
- **Targeted attacks**: Enables focused attacks on specific users

### Protection Measures
- **Random generation**: No sequential or predictable patterns
- **High entropy**: Sufficient randomness to prevent brute force
- **Rate limiting**: Limit ID lookup/verification attempts
- **No user search**: Do not provide user directory or search functionality
- **Contact discovery via mutual contacts**: Only discover users through mutual contacts
- **Delayed verification**: Do not confirm ID existence immediately

### Implementation Considerations
- **No existence confirmation**: API should not confirm if an ID exists
- **Constant-time responses**: Response time should not indicate existence
- **Error message uniformity**: Same error messages for existing and non-existing IDs
- **Contact sync limits**: Limit contact synchronization to prevent bulk enumeration

---

## Immutability

### Design Principle
**anoX-ID should be immutable** - once assigned, it should not change.

### Rationale
- **Stable identity**: Users can be reliably identified over time
- **Trust establishment**: Long-term trust relationships depend on stable IDs
- **Simplified implementation**: Immutability simplifies key management
- **User expectations**: Users expect stable identifiers

### Exceptions
- **Security incidents**: In case of fundamental security compromise
- **User request**: In exceptional circumstances with proper verification
- **Migration**: During major system migrations (transparent to users)

### Change Mechanism (if absolutely necessary)
- **Explicit user action**: User must explicitly request change
- **Multi-factor verification**: Strong authentication required
- **Notification**: Contacts notified of ID change
- **Key continuity**: Cryptographic identity should remain linked
- **Transition period**: Support old ID during transition period

---

## Persistence

### Long-term Identity
- **Permanent assignment**: anoX-ID assigned for user lifetime
- **Account persistence**: ID persists across device changes
- **Service continuity**: ID persists across service migrations
- **Historical records**: ID maintains historical message associations

### Deletion Considerations
- **Account deletion**: User can delete account, but ID may be reserved
- **ID recycling**: Do not recycle deleted IDs (prevents confusion)
- **Privacy vs. persistence**: Balance privacy with identity stability
- **Grace period**: Extended grace period before potential ID reuse

---

## Relationship to Cryptographic Identity

### Key Principle
**anoX-ID ≠ Cryptographic Identity**

The anoX-ID is a human-readable identifier, while cryptographic identity is based on public/private key pairs.

### Separation of Concerns
- **anoX-ID**: Human-readable, user-facing identifier
- **Cryptographic identity**: Technical security foundation
- **Mapping**: Server maintains mapping between anoX-ID and public keys
- **Verification**: Users verify cryptographic identity, not just anoX-ID

### Binding Mechanism
- **anoX-ID → Public Key Mapping**: Server maintains authenticated mapping
- **Signed mappings**: Server signs mappings to prevent tampering
- **Key changes**: Users can change keys while keeping same anoX-ID
- **Key continuity**: Historical keys preserved for message verification

### Security Implications
- **Trust establishment**: Users must verify public keys, not just anoX-IDs
- **Key compromise**: If private key compromised, user can generate new key
- **Server trust**: Server mapping must be authentic (signed by server)
- **Key verification**: Out-of-band verification of public keys recommended

---

## Security Requirements

### SEC-ID-001
anoX-IDs must be generated using cryptographically secure random number generators.

### SEC-ID-002
anoX-IDs must have sufficient entropy (≥58 bits) to prevent collisions.

### SEC-ID-003
Server must verify uniqueness of anoX-IDs before assignment.

### SEC-ID-004
anoX-IDs must be immutable under normal circumstances.

### SEC-ID-005
System must not enable user enumeration through anoX-ID guessing.

### SEC-ID-006
anoX-ID must not be the sole identifier for security-critical operations.

### SEC-ID-007
Cryptographic identity (public/private keys) must be separate from anoX-ID.

### SEC-ID-008
Server must maintain authenticated mapping between anoX-ID and public keys.

### SEC-ID-009
Users must be able to verify public keys independently of anoX-ID.

### SEC-ID-010
anoX-ID changes (if ever allowed) must require strong authentication and notify contacts.

---

## Implementation Considerations

### Registration Flow
1. User selects username/identifier (optional)
2. System generates random anoX-ID
3. System generates cryptographic key pair
4. System creates mapping: anoX-ID → public key
5. Server signs mapping
6. User stores private key securely

### Key Change Flow
1. User generates new key pair
2. User uploads new public key to server
3. Server updates mapping with authentication
4. Server signs new mapping
5. Contacts notified of key change
6. Users verify new key (out-of-band recommended)

### Discovery Flow
1. User shares anoX-ID with contact
2. Contact requests anoX-ID from server
3. Server returns public key mapping
4. Contact verifies server signature
5. Contact optionally verifies key out-of-band
6. Contact establishes encrypted communication

---

## Open Decisions

### OPEN-ID-001
Should anoX-ID include any user-selectable component (like username) or be entirely random?

### OPEN-ID-002
What is the maximum acceptable collision probability for anoX-IDs?

### OPEN-ID-003
Should the system support anoX-ID changes in exceptional circumstances?

### OPEN-ID-004
What is the policy for anoX-ID reuse after account deletion?

### OPEN-ID-005
How should the system handle anoX-ID conflicts during migration?

### OPEN-ID-006
Should there be a mechanism for users to reserve preferred anoX-IDs?

### OPEN-ID-007
How should the system handle anoX-ID verification in offline scenarios?