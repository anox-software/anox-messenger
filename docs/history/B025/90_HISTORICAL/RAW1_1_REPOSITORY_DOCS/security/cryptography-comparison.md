> **Status:** SUPERSEDED HISTORICAL DECISION INPUT  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current implementation specification.**  
> **Current decision:** vodozemac/Olm. libsignal and OpenPGP are not current implementation choices.  
> **Superseded by:** `docs/current/KEY_AND_SESSION_ARCHITECTURE.md` and `docs/current/SECURITY_INVARIANTS.md`  

# Cryptography Architecture Comparison - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document compares three cryptographic architecture approaches for anoX Messenger: OpenPGP, modern E2EE with ratcheting, and a hybrid approach.

---

## Comparison Criteria

### Security Properties
- **Confidentiality**: Protection against unauthorized access to message content
- **Integrity**: Detection of message tampering
- **Authenticity**: Verification of message sender identity
- **Forward Secrecy**: Protection of past messages if current keys are compromised
- **Post-Compromise Security**: Recovery from key compromise

### Operational Properties
- **Key Rotation**: Ability to rotate keys without disruption
- **Multi-Device**: Support for multiple devices per user
- **Offline Messages**: Support for offline message delivery
- **Device Change**: Support for device changes and recovery

### Implementation Properties
- **Implementation Risk**: Complexity and potential for implementation errors
- **Library Maturity**: Availability of well-tested, mature libraries
- **Maintainability**: Long-term maintenance and update requirements

---

## Option A: OpenPGP

### Description
Traditional OpenPGP-based encryption using public/private key pairs, following the OpenPGP standard (RFC 4880).

### Security Properties

#### Confidentiality: ⭐⭐⭐⭐☆
- **Strong encryption**: Uses proven encryption algorithms (AES, RSA, ECC)
- **Key management**: Established key management practices
- **Algorithm flexibility**: Support for multiple algorithms
- **Risk**: Dependent on proper key management and passphrase strength

#### Integrity: ⭐⭐⭐⭐☆
- **Digital signatures**: Strong message authentication
- **MDC packets**: Modification detection codes
- **Risk**: Implementation vulnerabilities in signature verification

#### Authenticity: ⭐⭐⭐⭐☆
- **Web of Trust**: Decentralized trust model
- **Key signatures**: Users can sign each other's keys
- **Risk**: Web of trust requires user participation and understanding

#### Forward Secrecy: ⭐⭐☆☆☆
- **No forward secrecy**: Compromise of long-term key exposes all past messages
- **Key rotation**: Possible but disruptive
- **Risk**: High - historical messages vulnerable to key compromise

#### Post-Compromise Security: ⭐⭐☆☆☆
- **Limited recovery**: Key compromise affects future and past messages
- **Key rotation**: Manual key rotation required
- **Risk**: Extended impact of key compromise

### Operational Properties

#### Key Rotation: ⭐⭐☆☆☆
- **Manual process**: Key rotation requires manual intervention
- **Disruptive**: Requires redistribution of new keys
- **Contact notification**: Manual notification to contacts required
- **Risk**: Users may not rotate keys regularly

#### Multi-Device: ⭐⭐☆☆☆
- **Key sharing**: Requires sharing private keys across devices
- **Security risk**: Private key exposure increases with device count
- **Synchronization**: Complex synchronization of keys and messages
- **Risk**: Private key compromise on any device affects all devices

#### Offline Messages: ⭐⭐⭐⭐☆
- **Server storage**: Encrypted messages can be stored on server
- **Asynchronous**: Supports offline message delivery
- **Risk**: Server stores encrypted messages (acceptable if properly encrypted)

#### Device Change: ⭐⭐☆☆☆
- **Key export**: Requires export/import of private keys
- **Security risk**: Private key exposure during transfer
- **Complex**: Complex process for non-technical users
- **Risk**: Private key mishandling during device change

### Implementation Properties

#### Implementation Risk: ⭐⭐⭐☆☆
- **Complex standard**: OpenPGP standard is complex
- **Implementation diversity**: Multiple implementations with different behaviors
- **Risk**: Implementation vulnerabilities and interoperability issues

#### Library Maturity: ⭐⭐⭐⭐⭐
- **Mature libraries**: Well-established libraries (GPG, Bouncy Castle, etc.)
- **Extensive testing**: Decades of testing and bug fixes
- **Documentation**: Extensive documentation and community support
- **Risk**: Low - mature, well-tested libraries available

#### Maintainability: ⭐⭐⭐☆☆
- **Standard evolution**: OpenPGP standard continues to evolve
- **Algorithm updates**: Need to update algorithms over time
- **Backward compatibility**: Need to maintain backward compatibility
- **Risk**: Moderate - ongoing maintenance required

### Overall Assessment: ⭐⭐⭐☆☆

**Strengths:**
- Mature, well-tested libraries
- Strong encryption and authentication
- Established trust model (web of trust)
- Good offline message support

**Weaknesses:**
- No forward secrecy
- Poor multi-device support
- Complex key rotation
- Limited post-compromise security

**Use Case:** Suitable for scenarios where forward secrecy is not critical and multi-device support is not required.

---

## Option B: Modern E2EE with Ratcheting

### Description
Modern end-to-end encryption using the Double Ratchet algorithm (Signal Protocol) with forward secrecy and post-compromise security.

### Security Properties

#### Confidentiality: ⭐⭐⭐⭐⭐
- **Strong encryption**: Uses modern encryption algorithms (X25519, AES-256-GCM, ChaCha20-Poly1305)
- **Forward secrecy**: Automatic forward secrecy through ratcheting
- **Post-compromise security**: Automatic recovery from key compromise
- **Key separation**: Clear separation between long-term and ephemeral keys

#### Integrity: ⭐⭐⭐⭐⭐
- **Authentication codes**: Strong message authentication (HMAC, MAC)
- **Key derivation**: Cryptographic key derivation ensures integrity
- **Sequence numbers**: Message sequence verification
- **Risk**: Implementation complexity in ratchet logic

#### Authenticity: ⭐⭐⭐⭐☆
- **Key-based authentication**: Authentication through public keys
- **Signed prekeys**: Initial authentication through signed prekeys
- **Risk**: Requires trusted key distribution mechanism

#### Forward Secrecy: ⭐⭐⭐⭐⭐
- **Automatic ratcheting**: Per-message key rotation provides forward secrecy
- **DH ratchet**: Periodic DH exchanges enhance forward secrecy
- **Ephemeral keys**: Ephemeral keys are regularly discarded
- **Risk**: Implementation complexity in ratchet logic

#### Post-Compromise Security: ⭐⭐⭐⭐⭐
- **Automatic recovery**: DH ratchet provides automatic recovery
- **Key rotation**: Regular key rotation limits compromise impact
- **Healing**: Protocol "heals" from compromise over time
- **Risk**: Depends on proper implementation of ratchet

### Operational Properties

#### Key Rotation: ⭐⭐⭐⭐⭐
- **Automatic rotation**: Automatic per-message key rotation
- **Transparent**: Transparent to users
- **No disruption**: No disruption to ongoing conversations
- **Risk**: Implementation complexity

#### Multi-Device: ⭐⭐⭐⭐☆
- **Device-specific keys**: Each device has unique keys
- **Key synchronization**: Keys synchronized across devices
- **Complex**: More complex than single-device architecture
- **Risk**: Increased complexity for multi-device scenarios

#### Offline Messages: ⭐⭐⭐⭐☆
- **Prekey bundles**: Prekey messages enable offline initialization
- **Server storage**: Encrypted messages stored on server
- **Asynchronous**: Supports offline message delivery
- **Risk**: Requires prekey management infrastructure

#### Device Change: ⭐⭐⭐⭐☆
- **Key regeneration**: Generate new keys for new device
- **No private key transfer**: No need to transfer private keys
- **Simpler**: Simpler than OpenPGP key transfer
- **Risk**: Requires key synchronization infrastructure

### Implementation Properties

#### Implementation Risk: ⭐⭐⭐☆☆
- **Complex protocol**: Double Ratchet algorithm is complex
- **State management**: Complex state management across devices
- **Risk**: Implementation vulnerabilities in ratchet logic

#### Library Maturity: ⭐⭐⭐⭐☆
- **Mature libraries**: Well-tested libraries (libsignal, libsignal-protocol-c)
- **Battle-tested**: Used by major messaging apps (Signal, WhatsApp)
- **Documentation**: Good documentation and reference implementations
- **Risk**: Moderate - fewer implementation options than OpenPGP

#### Maintainability: ⭐⭐⭐⭐☆
- **Protocol stability**: Signal Protocol is relatively stable
- **Algorithm updates**: Updates coordinated through library updates
- **Community support**: Active community and commercial support
- **Risk**: Moderate - ongoing maintenance required

### Overall Assessment: ⭐⭐⭐⭐☆

**Strengths:**
- Excellent forward secrecy and post-compromise security
- Automatic key rotation
- Good multi-device support
- Battle-tested in major applications

**Weaknesses:**
- Implementation complexity
- More complex infrastructure requirements
- Fewer library options compared to OpenPGP
- Requires trusted key distribution

**Use Case:** Recommended for modern messaging applications requiring strong forward secrecy and multi-device support.

---

## Option C: Hybrid Approach (OpenPGP + Modern E2EE)

### Description
Combination approach using OpenPGP for long-term identity and modern E2EE for message encryption with ratcheting.

### Security Properties

#### Confidentiality: ⭐⭐⭐⭐⭐
- **Layered encryption**: OpenPGP for identity, E2EE for messages
- **Best of both**: Combines strengths of both approaches
- **Risk**: Increased complexity may introduce vulnerabilities

#### Integrity: ⭐⭐⭐⭐⭐
- **Multiple authentication**: Both OpenPGP signatures and E2EE MACs
- **Redundant verification**: Multiple layers of integrity verification
- **Risk**: Implementation complexity in coordinating both systems

#### Authenticity: ⭐⭐⭐⭐⭐
- **Web of trust**: OpenPGP web of trust for identity verification
- **Key-based**: E2EE key-based authentication for messages
- **Risk**: Complexity in coordinating trust models

#### Forward Secrecy: ⭐⭐⭐⭐⭐
- **E2EE ratcheting**: Forward secrecy through E2EE ratcheting
- **OpenPGP limitations**: OpenPGP layer lacks forward secrecy
- **Risk**: Dependency on proper layering

#### Post-Compromise Security: ⭐⭐⭐⭐☆
- **E2EE recovery**: E2EE provides post-compromise security
- **OpenPGP impact**: OpenPGP key compromise affects identity layer
- **Risk**: Complex compromise scenarios

### Operational Properties

#### Key Rotation: ⭐⭐⭐⭐☆
- **Automatic E2EE**: Automatic rotation in E2EE layer
- **Manual OpenPGP**: Manual rotation in OpenPGP layer
- **Coordination**: Requires coordination between layers
- **Risk**: Increased operational complexity

#### Multi-Device: ⭐⭐⭐☆☆
- **E2EE support**: E2EE supports multi-device
- **OpenPGP issues**: OpenPGP multi-device challenges remain
- **Coordination**: Complex coordination between systems
- **Risk**: High complexity for multi-device scenarios

#### Offline Messages: ⭐⭐⭐⭐☆
- **Both support**: Both systems support offline messages
- **Coordination**: Requires coordination between layers
- **Risk**: Increased complexity in offline scenarios

#### Device Change: ⭐⭐⭐☆☆
- **E2EE simpler**: E2EE simplifies device change
- **OpenPGP complex**: OpenPGP complexity remains
- **Coordination**: Complex coordination required
- **Risk**: High complexity for device changes

### Implementation Properties

#### Implementation Risk: ⭐⭐☆☆☆
- **High complexity**: Highest complexity of all options
- **Integration challenges**: Complex integration of two systems
- **Risk**: High - integration vulnerabilities likely

#### Library Maturity: ⭐⭐⭐⭐☆
- **Both mature**: Both OpenPGP and E2EE libraries are mature
- **Integration**: Integration complexity reduces effective maturity
- **Risk**: Integration challenges reduce maturity benefit

#### Maintainability: ⭐⭐☆☆☆
- **Double maintenance**: Maintenance of both systems required
- **Coordination**: Coordination between systems adds complexity
- **Risk**: High - long-term maintenance burden

### Overall Assessment: ⭐⭐⭐☆☆

**Strengths:**
- Combines strengths of both approaches
- Strong security properties across all dimensions
- Flexible trust model

**Weaknesses:**
- Highest implementation complexity
- Integration challenges
- Increased maintenance burden
- Risk of integration vulnerabilities

**Use Case:** Only recommended if specific requirements necessitate both OpenPGP and modern E2EE features.

---

## Critical Analysis: Double Encryption

### Common Misconception
**"Double encryption is automatically more secure"**

### Reality
- **Security plateau**: Encryption security plateaus; additional layers provide diminishing returns
- **Complexity risk**: Increased complexity often decreases overall security
- **Implementation bugs**: More code = more potential vulnerabilities
- **Performance impact**: Additional computational overhead
- **Interoperability**: Reduced interoperability with other systems

### When Double Encryption Makes Sense
- **Algorithm diversity**: Protection against algorithm-specific attacks
- **Key separation**: Protection against key compromise in one layer
- **Regulatory requirements**: Specific regulatory or compliance requirements
- **Defense in depth**: Multiple independent security layers

### When Double Encryption Does Not Make Sense
- **Same algorithm**: Double encryption with same algorithm provides minimal benefit
- **Implementation complexity**: When complexity outweighs security benefits
- **Performance constraints**: When performance impact is unacceptable
- **Interoperability needs**: When interoperability is important

---

## Recommendation

### Recommended Architecture: Option B (Modern E2EE with Ratcheting)

### Rationale
1. **Strong security properties**: Excellent forward secrecy and post-compromise security
2. **Modern requirements**: Meets modern security expectations for messaging apps
3. **Battle-tested**: Proven in major applications (Signal, WhatsApp)
4. **Multi-device support**: Good support for multi-device scenarios
5. **Automatic key rotation**: Reduces user burden and operational complexity
6. **Future-proof**: Designed for modern security requirements

### Implementation Considerations
- **Library selection**: Use mature, well-tested libraries (libsignal, libsignal-protocol-c)
- **Implementation care**: Careful implementation of ratchet logic
- **Testing**: Extensive testing of ratchet behavior
- **Infrastructure**: Investment in key management infrastructure
- **Fallback mechanisms**: Appropriate fallback mechanisms for edge cases

### Alternatives Considered
- **OpenPGP**: Rejected due to lack of forward secrecy and poor multi-device support
- **Hybrid**: Rejected due to excessive complexity and integration risks

---

## Security Requirements

### SEC-CRYPTO-001
The system must implement forward secrecy through automatic key rotation.

### SEC-CRYPTO-002
The system must provide post-compromise security through key ratcheting.

### SEC-CRYPTO-003
Message encryption must use modern, well-vetted cryptographic algorithms.

### SEC-CRYPTO-004
The system must support multi-device scenarios without compromising security.

### SEC-CRYPTO-005
Key rotation must be automatic and transparent to users.

### SEC-CRYPTO-006
The system must use battle-tested cryptographic libraries.

### SEC-CRYPTO-007
Cryptographic implementation must be extensively tested and audited.

### SEC-CRYPTO-008
The system must avoid unnecessary double encryption layers.

### SEC-CRYPTO-009
Key management must be designed to minimize complexity.

### SEC-CRYPTO-010
The architecture must be maintainable and updatable over time.

---

## Open Decisions

### OPEN-CRYPTO-001
Which specific E2EE library should be used (libsignal, libsignal-protocol-c, or alternative)?

### OPEN-CRYPTO-002
Should the system support prekey message bundles for offline initialization?

### OPEN-CRYPTO-003
What is the recommended DH ratchet frequency for optimal security/performance balance?

### OPEN-CRYPTO-004
How should the system handle edge cases in ratchet implementation (out-of-order messages, skipped messages)?

### OPEN-CRYPTO-005
Should the system implement any fallback mechanisms for devices with limited computational resources?

### OPEN-CRYPTO-006
How should the system handle algorithm updates and cryptographic agility?