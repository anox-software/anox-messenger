> **Status:** HISTORICAL / SUPERSEDED
> **Architecture Baseline:** Raw1.1
> **Last synchronized:** 2026-08-19
> **Do not use as current implementation specification.**
> **Current direction:** Push is wake-up only; FCM HTTP v1 is the primary V1 transport; UnifiedPush-default is not a current binding promise.
> **Superseded by:** `docs/authority/B025/TRACK_B/B011_PUSH_OFFLINE.md` and `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md`.

# Push Notifications Analysis - anoX Messenger

## Architecture Version
Raw1.1

## Overview
This document provides an architectural analysis of push notification options for anoX Messenger, focusing on privacy, reliability, and complexity while ensuring no message content is included in push payloads.

---

## Core Requirement

### No Message Content in Push Payloads
**Push notifications must not contain message content in plaintext.**

Push notifications should only indicate that a message has been received, without revealing the content of the message.

---

## Push Notification Options

### Option A: Firebase Cloud Messaging (FCM)

#### Description
Google's Firebase Cloud Messaging service for push notifications.

#### Privacy Analysis
- **Google dependency**: Requires Google services and infrastructure
- **Google access**: Google has access to push metadata
- **Google tracking**: Potential for Google tracking through push tokens
- **Server communication**: Communication with Google servers required

#### Reliability Analysis
- **High reliability**: High reliability and mature infrastructure
- **Global coverage**: Global server coverage
- **Scalability**: Excellent scalability
- **Real-time**: Real-time delivery capabilities

#### Complexity Analysis
- **Low implementation complexity**: Well-documented APIs
- **Google dependency**: Dependency on Google services
- **Platform limitations**: Some platform limitations
- **Vendor lock-in**: Vendor lock-in to Google ecosystem

#### Minimal Payload Options
- **New message indicator**: Simple "new message" indicator
- **Sender identifier**: anoX-ID of sender (encrypted if possible)
- **Message count**: Number of unread messages
- **Badge update**: Badge count update only

#### Privacy Limitations
- **Google access**: Google has access to push tokens and metadata
- **No Google-free**: Not Google-free, violates some privacy principles
- **Tracking potential**: Potential for tracking through push tokens
- **Jurisdiction concerns**: Google subject to US jurisdiction

#### Security Rating: ⭐⭐⭐☆☆
#### Privacy Rating: ⭐⭐☆☆☆
#### Reliability Rating: ⭐⭐⭐⭐⭐
#### Complexity Rating: ⭐⭐⭐⭐☆

---

### Option B: UnifiedPush (Google-Free Alternative)

#### Description
Decentralized, Google-free push notification system using user-selected push distributors.

#### Privacy Analysis
- **User choice**: User can select push distributor
- **No Google dependency**: No dependency on Google services
- **Distributed trust**: Distributed trust model
- **Transparency**: More transparent infrastructure

#### Reliability Analysis
- **Variable reliability**: Reliability depends on chosen distributor
- **Limited coverage**: Limited global coverage compared to FCM
- **Scalability**: Variable scalability depending on distributor
- **Real-time**: Generally real-time, but variable

#### Complexity Analysis
- **Higher implementation complexity**: Less standardised APIs
- **User configuration**: Requires user configuration
- **Distributor management**: Need to manage multiple distributors
- **No vendor lock-in**: No vendor lock-in

#### Minimal Payload Options
- **New message indicator**: Simple "new message" indicator
- **Sender identifier**: anoX-ID of sender (encrypted if possible)
- **Message count**: Number of unread messages
- **Badge update**: Badge count update only

#### Privacy Advantages
- **Google-free**: Google-free alternative
- **User control**: User control over push infrastructure
- **Distributed**: Distributed infrastructure reduces single point of failure
- **Federated**: Federated model supports self-hosting

#### Privacy Limitations
- **Distributor access**: Chosen distributor has access to metadata
- **Configuration complexity**: Complex configuration for users
- **Limited ecosystem**: Limited ecosystem compared to FCM
- **Variable quality**: Variable quality of distributors

#### Security Rating: ⭐⭐⭐⭐☆
#### Privacy Rating: ⭐⭐⭐⭐☆
#### Reliability Rating: ⭐⭐⭐☆☆
#### Complexity Rating: ⭐⭐☆☆☆

---

### Option C: WebSockets / Long Polling

#### Description
Direct connection to server using WebSockets or long polling for real-time updates.

#### Privacy Analysis
- **Direct connection**: Direct connection to anoX server
- **No third-party**: No third-party push service dependency
- **Server control**: Full control over push infrastructure
- **Limited metadata**: Limited metadata exposure

#### Reliability Analysis
- **Variable reliability**: Reliability depends on server infrastructure
- **Connection dependent**: Dependent on persistent connection
- **Battery impact**: Higher battery impact on mobile devices
- **Network dependent**: More dependent on network conditions

#### Complexity Analysis
- **High implementation complexity**: Requires custom infrastructure
- **Connection management**: Complex connection management
- **Scaling challenges**: Scaling challenges for real-time connections
- **No vendor lock-in**: No vendor lock-in

#### Minimal Payload Options
- **New message indicator**: Simple "new message" indicator
- **Message count**: Number of unread messages
- **Badge update**: Badge count update only
- **Encrypted metadata**: Option for encrypted metadata

#### Privacy Advantages
- **No third-party**: No third-party dependency
- **Full control**: Full control over infrastructure
- **Minimal metadata**: Minimal metadata exposure
- **Direct connection**: Direct connection to trusted server

#### Privacy Limitations
- **Infrastructure burden**: Infrastructure burden on anoX
- **Scalability challenges**: Scalability challenges
- **Battery impact**: Higher battery impact
- **Network limitations**: Network limitations

#### Security Rating: ⭐⭐⭐⭐☆
#### Privacy Rating: ⭐⭐⭐⭐⭐
#### Reliability Rating: ⭐⭐⭐☆☆
#### Complexity Rating: ⭐⭐☆☆☆

---

### Option D: Hybrid Approach

#### Description
Combination of approaches, e.g., FCM as default with UnifiedPush as option.

#### Privacy Analysis
- **User choice**: User can choose push method
- **Default compromise**: Default may compromise privacy
- **Flexibility**: Flexibility for different user needs
- **Complex trust model**: Complex trust model

#### Reliability Analysis
- **High reliability**: High reliability through multiple options
- **Fallback options**: Fallback options if one method fails
- **Complex management**: Complex management of multiple methods
- **Optimal routing**: Potential for optimal routing

#### Complexity Analysis
- **Very high complexity**: Very high implementation complexity
- **Multiple integrations**: Multiple integrations required
- **User configuration**: User configuration complexity
- **Maintenance burden**: High maintenance burden

#### Minimal Payload Options
- **Consistent payloads**: Consistent payloads across methods
- **Method-specific options**: Method-specific payload options
- **Fallback handling**: Fallback handling for different methods

#### Privacy Advantages
- **User control**: User control over privacy/reliability trade-off
- **Flexibility**: Flexibility for different requirements
- **Progressive enhancement**: Progressive enhancement approach
- **Future-proof**: Future-proof for new technologies

#### Privacy Limitations
- **Complexity**: High complexity may introduce vulnerabilities
- **Default concerns**: Default choice may compromise privacy
- **User confusion**: User confusion about options
- **Maintenance burden**: High maintenance burden

#### Security Rating: ⭐⭐⭐☆☆
#### Privacy Rating: ⭐⭐⭐☆☆
#### Reliability Rating: ⭐⭐⭐⭐⭐
#### Complexity Rating: ⭐☆☆☆☆

---

## Minimal Push Payload Strategies

### Strategy 1: Badge Count Only
```json
{
  "badge": 3
}
```
- **Maximum privacy**: Only unread count
- **Minimal information**: Minimal information leakage
- **User experience**: Limited user experience

### Strategy 2: New Message Indicator
```json
{
  "type": "new_message",
  "badge": 3
}
```
- **Good privacy**: Indicates new message without content
- **Better UX**: Better user experience
- **Minimal metadata**: Minimal metadata exposure

### Strategy 3: Encrypted Sender ID
```json
{
  "type": "new_message",
  "sender": "encrypted_sender_id",
  "badge": 3
}
```
- **Balanced privacy**: Encrypted sender information
- **Good UX**: Good user experience
- **Decryption required**: Requires client-side decryption

### Strategy 4: Message Count per Contact
```json
{
  "type": "new_messages",
  "counts": {
    "encrypted_contact_1": 2,
    "encrypted_contact_2": 1
  },
  "badge": 3
}
```
- **Moderate privacy**: More detailed metadata
- **Best UX**: Best user experience
- **More metadata**: More metadata exposure

---

## Comparative Analysis

### Privacy vs. Reliability Trade-offs

| Option | Privacy | Reliability | Complexity | Best For |
|--------|---------|-------------|------------|----------|
| FCM | ⭐⭐☆☆☆ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐☆ | Maximum reliability |
| UnifiedPush | ⭐⭐⭐⭐☆ | ⭐⭐⭐☆☆ | ⭐⭐☆☆☆ | Privacy-focused users |
| WebSockets | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ | ⭐⭐☆☆☆ | Maximum privacy |
| Hybrid | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ | ⭐☆☆☆☆ | Flexibility |

### Metadata Exposure Analysis

| Option | Push Provider Access | Message Content | Sender Identity | Timing Information |
|--------|---------------------|-----------------|-----------------|-------------------|
| FCM | Google | No | Possible | Yes |
| UnifiedPush | Distributor | No | Possible | Yes |
| WebSockets | None | No | Optional | Yes |
| Hybrid | Variable | No | Variable | Yes |

### Implementation Complexity

| Option | Development Time | Maintenance | User Configuration | Dependencies |
|--------|------------------|-------------|-------------------|--------------|
| FCM | Low | Low | None | Google |
| UnifiedPush | Medium | Medium | Required | Various |
| WebSockets | High | High | None | None |
| Hybrid | Very High | Very High | Required | Multiple |

---

## Recommended Approach

### Primary Recommendation: UnifiedPush with FCM Fallback

**Primary: UnifiedPush**
- **Privacy-first**: Privacy-first approach aligned with anoX principles
- **User control**: User control over push infrastructure
- **Google-free**: Google-free alternative
- **Federated**: Supports self-hosting and decentralization

**Fallback: FCM**
- **Reliability fallback**: FCM as reliability fallback
- **User choice**: User can choose FCM if UnifiedPush unavailable
- **Gradual transition**: Gradual transition from FCM to UnifiedPush
- **Default configuration**: Default to UnifiedPush with FCM as opt-in

**Future: WebSockets**
- **Long-term consideration**: WebSockets as long-term consideration
- **Infrastructure investment**: Requires infrastructure investment
- **Battery optimization**: Battery optimization research needed
- **Progressive enhancement**: Progressive enhancement approach

### Minimal Payload Strategy
**Recommended: Strategy 2 (New Message Indicator)**
- **Balance**: Good balance between privacy and user experience
- **Implementation**: Simple to implement
- **Privacy**: Protects message content and sender identity
- **User experience**: Adequate user experience for notifications

---

## Security Requirements

### SEC-PUSH-001
Push notification payloads must not contain message content in plaintext.

### SEC-PUSH-002
Push notification payloads must not contain sender identity in plaintext.

### SEC-PUSH-003
Push notification payloads must be minimized to essential information only.

### SEC-PUSH-004
Push notification metadata must be minimized where technically feasible.

### SEC-PUSH-005
The system must support Google-free push notification options.

### SEC-PUSH-006
The system must allow user control over push notification infrastructure.

### SEC-PUSH-007
Push notification providers must not have access to message decryption keys.

### SEC-PUSH-008
Push notification configuration must be transparent to users.

### SEC-PUSH-009
The system must implement fallback mechanisms for push notification failures.

### SEC-PUSH-010
Push notification architecture must maintain zero-knowledge principles.

---

## Implementation Considerations

### Push Payload Structure
```kotlin
data class PushPayload(
    val type: PushType,
    val badge: Int,
    val encryptedSender: String? = null,
    val timestamp: Long
)

enum class PushType {
    NEW_MESSAGE,
    BADGE_UPDATE,
    SYNC_REQUIRED
}
```

### UnifiedPush Integration
```kotlin
class UnifiedPushManager {
    fun registerPushEndpoint(endpoint: String) {
        // Register with chosen UnifiedPush distributor
    }

    fun sendPushNotification(userId: String, payload: PushPayload) {
        // Send via UnifiedPush distributor
    }
}
```

### FCM Fallback
```kotlin
class PushNotificationManager {
    private val unifiedPush = UnifiedPushManager()
    private val fcm = FCMManager()

    suspend fun sendNotification(userId: String, payload: PushPayload) {
        try {
            unifiedPush.sendPushNotification(userId, payload)
        } catch (e: Exception) {
            fcm.sendPushNotification(userId, payload)
        }
    }
}
```

---

## Open Decisions

### OPEN-PUSH-001
Should UnifiedPush be the default or optional for users?

### OPEN-PUSH-002
What is the appropriate fallback strategy when UnifiedPush is unavailable?

### OPEN-PUSH-003
How should the system handle push notification distributor selection?

### OPEN-PUSH-004
What level of sender identity information should be included in push payloads?

### OPEN-PUSH-005
Should the system implement WebSockets as a long-term push notification strategy?

### OPEN-PUSH-006
How should the system handle push notification for users who disable push entirely?

### OPEN-PUSH-007
What is the appropriate strategy for push notification rate limiting?
