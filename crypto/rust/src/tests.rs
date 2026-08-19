// Comprehensive crypto tests using real vodozemac implementation

#[cfg(test)]
mod tests {
    use crate::identity::Identity;
    use crate::serialization::CryptoSerializer;

    // Test 1: Identity creation and basic operations
    #[test]
    fn test_identity_creation() {
        let identity = Identity::new();
        
        // Check that public keys are generated
        let curve25519_key = identity.curve25519_public_key();
        let ed25519_key = identity.ed25519_public_key();
        
        // Keys should be 32 bytes
        assert_eq!(curve25519_key.len(), 32);
        assert_eq!(ed25519_key.len(), 32);
        
        // Keys should not be all zeros
        assert_ne!(curve25519_key, [0u8; 32]);
        assert_ne!(ed25519_key, [0u8; 32]);
    }

    // Test 2: One-time key generation
    #[test]
    fn test_one_time_key_generation() {
        let mut identity = Identity::new();
        
        // Generate 5 one-time keys
        let result = identity.generate_one_time_keys(5);
        assert!(result.is_ok());
        
        // Check that keys were generated
        let count = identity.one_time_keys_count();
        assert_eq!(count, 5);
    }

    // Test 3: End-to-end Alice → Bob encryption (positive test)
    #[test]
    fn test_alice_bob_full_flow() {
        // Create identities for Alice and Bob
        let alice = Identity::new();
        let mut bob = Identity::new();
        
        // Bob generates one-time keys
        bob.generate_one_time_keys(1).unwrap();
        assert_eq!(bob.one_time_keys_count(), 1);
        
        // Get Bob's one-time key
        let bob_one_time_keys = bob.unpublished_one_time_keys();
        let bob_otk_id = bob_one_time_keys.keys().next().unwrap();
        let bob_otk_bytes = bob.get_one_time_key(*bob_otk_id).unwrap();
        
        // Alice creates outbound session to Bob
        let mut alice_session = alice.create_outbound_session(
            &bob.curve25519_public_key(),
            &bob_otk_bytes,
        ).unwrap();
        
        // Alice encrypts a message - on a new session this is a PreKey message
        let plaintext = b"test message";
        let (message_type, encrypted) = alice_session.encrypt(plaintext).unwrap();
        
        // The message type should be 0 (PreKey) for the first message
        assert_eq!(message_type, 0);
        
        // The encrypted message should be different from plaintext
        assert_ne!(encrypted, plaintext.to_vec());
        
        // Bob marks keys as published
        bob.mark_keys_as_published();
        
        // Bob creates inbound session from Alice's PreKey message and gets plaintext
        let (mut bob_session, bob_plaintext) = bob.create_inbound_session(
            &alice.curve25519_public_key(),
            &encrypted,
        ).unwrap();
        
        // Bob must recover exactly "test message"
        assert_eq!(bob_plaintext, b"test message");
        
        // Bob replies with a Normal message (established session)
        let reply = b"Yes. Take this, it's dangerous out there!";
        let (reply_type, reply_encrypted) = bob_session.encrypt(reply).unwrap();
        
        // The message type should be 1 (Normal) for the second message
        assert_eq!(reply_type, 1);
        
        // Alice decrypts Bob's Normal message
        let alice_reply = alice_session.decrypt(reply_type, &reply_encrypted).unwrap();
        assert_eq!(alice_reply, reply);
    }

    // Test 4: Invalid ciphertext (negative test)
    #[test]
    fn test_invalid_ciphertext() {
        let alice = Identity::new();
        let mut bob = Identity::new();
        
        bob.generate_one_time_keys(1).unwrap();
        let bob_one_time_keys = bob.unpublished_one_time_keys();
        let bob_otk_id = bob_one_time_keys.keys().next().unwrap();
        let bob_otk_bytes = bob.get_one_time_key(*bob_otk_id).unwrap();
        
        let mut alice_session = alice.create_outbound_session(
            &bob.curve25519_public_key(),
            &bob_otk_bytes,
        ).unwrap();
        
        // First message is a PreKey message
        let (msg_type, _first_encrypted) = alice_session.encrypt(b"hello").unwrap();
        
        // After first message, session should be established
        assert_eq!(msg_type, 0);
        
        // Try to decrypt invalid ciphertext as Normal message
        let invalid_ciphertext = vec![0u8; 32];
        let result = alice_session.decrypt(1, &invalid_ciphertext);
        
        // Should fail safely
        assert!(result.is_err());
    }

    // Test 5: Malformed message (negative test)
    #[test]
    fn test_malformed_message() {
        let alice = Identity::new();
        let mut bob = Identity::new();
        
        bob.generate_one_time_keys(1).unwrap();
        let bob_one_time_keys = bob.unpublished_one_time_keys();
        let bob_otk_id = bob_one_time_keys.keys().next().unwrap();
        let bob_otk_bytes = bob.get_one_time_key(*bob_otk_id).unwrap();
        
        // Bob's session does not yet exist
        // Try to create inbound session with malformed message
        let malformed = vec![0xFF; 100];
        let result = bob.create_inbound_session(
            &alice.curve25519_public_key(),
            &malformed,
        );
        
        // Should fail safely
        assert!(result.is_err());
    }

    // Test 6: Wrong key material (negative test)
    #[test]
    fn test_wrong_key_material() {
        let alice = Identity::new();
        let mut bob = Identity::new();
        
        bob.generate_one_time_keys(1).unwrap();
        let bob_one_time_keys = bob.unpublished_one_time_keys();
        let bob_otk_id = bob_one_time_keys.keys().next().unwrap();
        let bob_otk_bytes = bob.get_one_time_key(*bob_otk_id).unwrap();
        
        // Try to create session with wrong identity key size
        let wrong_key = [0u8; 16]; // Wrong size
        let result = alice.create_outbound_session(&wrong_key, &bob_otk_bytes);
        
        // Should fail safely
        assert!(result.is_err());
    }

    // Test 7: Modified ciphertext (negative test)
    #[test]
    fn test_modified_ciphertext() {
        let alice = Identity::new();
        let mut bob = Identity::new();
        
        bob.generate_one_time_keys(1).unwrap();
        let bob_one_time_keys = bob.unpublished_one_time_keys();
        let bob_otk_id = bob_one_time_keys.keys().next().unwrap();
        let bob_otk_bytes = bob.get_one_time_key(*bob_otk_id).unwrap();
        
        let mut alice_session = alice.create_outbound_session(
            &bob.curve25519_public_key(),
            &bob_otk_bytes,
        ).unwrap();
        
        // Alice encrypts a message
        let (_, encrypted) = alice_session.encrypt(b"test message").unwrap();
        
        // Bob marks keys as published
        bob.mark_keys_as_published();
        
        // Modify the ciphertext
        let mut modified = encrypted.clone();
        if !modified.is_empty() {
            modified[5] ^= 0xFF;
        }
        
        // Try to create inbound session with modified PreKey message
        let result = bob.create_inbound_session(
            &alice.curve25519_public_key(),
            &modified,
        );
        
        // Should fail safely
        assert!(result.is_err());
    }

    // Test 8: Corrupted serialized state (negative test)
    #[test]
    fn test_corrupted_serialized_state() {
        let identity = Identity::new();
        let key = [0u8; 32];
        
        // Serialize identity
        let serialized = identity.serialize(&key).unwrap();
        
        // Corrupt the serialized data
        let mut corrupted = serialized.clone();
        corrupted[0] ^= 0xFF;
        
        // Try to deserialize corrupted data
        let result = Identity::deserialize(&corrupted, &key);
        
        // Should fail safely (authentication will fail)
        assert!(result.is_err());
    }

    // Test 9: Serialization/restoration (positive test)
    #[test]
    fn test_serialization_restoration() {
        let identity = Identity::new();
        let original_curve25519 = identity.curve25519_public_key();
        let original_ed25519 = identity.ed25519_public_key();
        
        let key = [0u8; 32];
        
        // Serialize identity
        let serialized = identity.serialize(&key);
        assert!(serialized.is_ok());
        
        // Deserialize identity
        let deserialized = Identity::deserialize(&serialized.unwrap(), &key);
        assert!(deserialized.is_ok());
        
        let restored_identity = deserialized.unwrap();
        
        // Check that keys match
        assert_eq!(restored_identity.curve25519_public_key(), original_curve25519);
        assert_eq!(restored_identity.ed25519_public_key(), original_ed25519);
    }

    // Test 10: Ensure secrets are not in error messages
    #[test]
    fn test_error_messages_no_secrets() {
        let result = Identity::deserialize(&[0u8; 10], &[0u8; 32]);
        
        if let Err(error) = result {
            let error_string = format!("{:?}", error);
            
            // Check that error message doesn't contain sensitive terms
            assert!(!error_string.contains("key"), "Error message should not contain 'key'");
            assert!(!error_string.contains("secret"), "Error message should not contain 'secret'");
            assert!(!error_string.contains("private"), "Error message should not contain 'private'");
        }
    }

    // Test 11: Authenticated encryption properties
    #[test]
    fn test_authenticated_encryption() {
        let serializer = CryptoSerializer::new(&[0u8; 32]).unwrap();
        
        let data = vec![1u8, 2, 3, 4, 5];
        
        // Encrypt data
        let encrypted = serializer.serialize(&data).unwrap();
        
        // Modify ciphertext (tamper with data)
        let mut tampered = encrypted.clone();
        tampered[15] ^= 0xFF; // Modify some byte
        
        // Try to decrypt tampered data
        let result = serializer.deserialize::<Vec<u8>>(&tampered);
        
        // Should fail due to authentication failure
        assert!(result.is_err());
    }

    // Test 12: Key separation - different identities have different keys
    #[test]
    fn test_key_separation() {
        let identity1 = Identity::new();
        let identity2 = Identity::new();
        
        // Check that different identities have different keys
        assert_ne!(identity1.curve25519_public_key(), identity2.curve25519_public_key());
        assert_ne!(identity1.ed25519_public_key(), identity2.ed25519_public_key());
    }

    // Test 13: No recovery mechanism
    #[test]
    fn test_no_recovery_mechanism() {
        let identity = Identity::new();
        let key = [0u8; 32];
        
        // Serialize identity
        let serialized = identity.serialize(&key).unwrap();
        
        // Without the correct serialization key, the identity is lost
        let wrong_key = [1u8; 32];
        let result = Identity::deserialize(&serialized, &wrong_key);
        
        // Should fail - no recovery mechanism
        assert!(result.is_err());
    }

    // Test: Invalid state key length must not panic
    #[test]
    fn test_invalid_state_key_length() {
        let identity = Identity::new();
        let short_key = [0u8; 16];
        let result = identity.serialize(&short_key);
        assert!(result.is_err(), "Short state key must be rejected");

        let invalid = CryptoSerializer::new(&[0u8; 31]);
        assert!(invalid.is_err(), "31-byte key must be rejected");

        let valid = CryptoSerializer::new(&[0u8; 32]);
        assert!(valid.is_ok(), "32-byte key must be accepted");
    }

    // Test 14: Wrong session (decrypt with wrong message type)
    #[test]
    fn test_wrong_session_message_type() {
        let alice = Identity::new();
        let mut bob = Identity::new();
        
        bob.generate_one_time_keys(1).unwrap();
        let bob_one_time_keys = bob.unpublished_one_time_keys();
        let bob_otk_id = bob_one_time_keys.keys().next().unwrap();
        let bob_otk_bytes = bob.get_one_time_key(*bob_otk_id).unwrap();
        
        let mut alice_session = alice.create_outbound_session(
            &bob.curve25519_public_key(),
            &bob_otk_bytes,
        ).unwrap();
        
        // First message is a PreKey message
        let (msg_type, encrypted) = alice_session.encrypt(b"hello").unwrap();
        assert_eq!(msg_type, 0);
        
        // Try to decrypt PreKey message as a Normal message on a session
        // that hasn't been established - this should fail
        let result = alice_session.decrypt(1, &encrypted);
        assert!(result.is_err());
    }
}