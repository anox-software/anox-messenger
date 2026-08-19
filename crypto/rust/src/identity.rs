// Identity module - wraps vodozemac Account functionality
use crate::error::CryptoError;
use crate::serialization::CryptoSerializer;
use std::collections::HashMap;
use vodozemac::olm::{Account, AccountPickle};
use vodozemac::{Curve25519PublicKey, KeyId};
use zeroize::Zeroize;

/// Wrapper around vodozemac Account for identity management
pub struct Identity {
    account: Account,
}

impl Identity {
    /// Create a new identity with fresh cryptographic keys
    pub fn new() -> Self {
        Self {
            account: Account::new(),
        }
    }
    
    /// Get the Curve25519 public key (32 bytes)
    pub fn curve25519_public_key(&self) -> [u8; 32] {
        self.account.curve25519_key().to_bytes()
    }
    
    /// Get the Ed25519 public key (32 bytes)
    pub fn ed25519_public_key(&self) -> [u8; 32] {
        *self.account.ed25519_key().as_bytes()
    }
    
    /// Generate one-time keys for session establishment
    pub fn generate_one_time_keys(&mut self, count: usize) -> Result<(), CryptoError> {
        self.account.generate_one_time_keys(count);
        Ok(())
    }
    
    /// Get the number of stored one-time keys
    pub fn one_time_keys_count(&self) -> usize {
        self.account.stored_one_time_key_count()
    }
    
    /// Get one-time keys that haven't been published yet
    pub fn unpublished_one_time_keys(&self) -> HashMap<KeyId, [u8; 32]> {
        self.account
            .one_time_keys()
            .iter()
            .map(|(id, key)| (*id, key.to_bytes()))
            .collect()
    }
    
    /// Get a specific one-time key by ID
    pub fn get_one_time_key(&self, key_id: KeyId) -> Option<[u8; 32]> {
        self.account
            .one_time_keys()
            .get(&key_id)
            .map(|key| key.to_bytes())
    }
    
    /// Get one-time key by index (for JNI/Android bridge testing)
    pub fn get_one_time_key_by_index(&self, index: usize) -> Option<[u8; 32]> {
        self.account
            .one_time_keys()
            .values()
            .nth(index)
            .map(|key| key.to_bytes())
    }
    
    /// Mark keys as published (should be called after uploading to server)
    pub fn mark_keys_as_published(&mut self) {
        self.account.mark_keys_as_published();
    }
    
    /// Serialize identity with encryption
    pub fn serialize(&self, key: &[u8]) -> Result<Vec<u8>, CryptoError> {
        if key.len() != 32 {
            return Err(CryptoError::InvalidInput);
        }
        
        let pickle = self.account.pickle();
        let serializer = CryptoSerializer::new(key)
            .map_err(|e| CryptoError::SerializationError(e.to_string()))?;
        
        serializer
            .serialize(&pickle)
            .map_err(|e| CryptoError::SerializationError(e.to_string()))
    }
    
    fn map_serializer_error(e: crate::serialization::CryptoSerializerError) -> CryptoError {
        match e {
            crate::serialization::CryptoSerializerError::UnsupportedVersion => CryptoError::UnsupportedVersion,
            _ => CryptoError::DeserializationError(e.to_string()),
        }
    }

    /// Deserialize identity from encrypted data
    pub fn deserialize(data: &[u8], key: &[u8]) -> Result<Self, CryptoError> {
        if key.len() != 32 {
            return Err(CryptoError::InvalidInput);
        }
        
        let serializer = CryptoSerializer::new(key)
            .map_err(|e| CryptoError::DeserializationError(e.to_string()))?;
        let pickle: AccountPickle = serializer
            .deserialize(data)
            .map_err(Self::map_serializer_error)?;
        
        Ok(Self {
            account: pickle.into(),
        })
    }
    
    /// Create outbound session (for initiating communication)
    pub fn create_outbound_session(
        &self,
        their_identity_key: &[u8],
        their_one_time_key: &[u8],
    ) -> Result<super::session::Session, CryptoError> {
        if their_identity_key.len() != 32 || their_one_time_key.len() != 32 {
            return Err(CryptoError::InvalidInput);
        }
        
        let identity_key = Curve25519PublicKey::from_slice(their_identity_key)
            .map_err(|_| CryptoError::KeyError("Invalid identity key".to_string()))?;
        
        let one_time_key = Curve25519PublicKey::from_slice(their_one_time_key)
            .map_err(|_| CryptoError::KeyError("Invalid one-time key".to_string()))?;
        
        self.account
            .create_outbound_session(vodozemac::olm::SessionConfig::version_1(), identity_key, one_time_key)
            .map(|session| super::session::Session::new(session))
            .map_err(|_| CryptoError::CryptoFailure)
    }
    
    /// Create inbound session (for receiving initial PreKey message)
    /// Returns the new session and the decrypted plaintext from the PreKey message
    pub fn create_inbound_session(
        &mut self,
        their_identity_key: &[u8],
        pre_key_message: &[u8],
    ) -> Result<(super::session::Session, Vec<u8>), CryptoError> {
        if their_identity_key.len() != 32 {
            return Err(CryptoError::InvalidInput);
        }
        
        let identity_key = Curve25519PublicKey::from_slice(their_identity_key)
            .map_err(|_| CryptoError::KeyError("Invalid identity key".to_string()))?;
        
        // Parse the pre-key message using the actual vodozemac API
        let pre_key = vodozemac::olm::PreKeyMessage::from_bytes(pre_key_message)
            .map_err(|_| CryptoError::InvalidInput)?;
        
        let result = self.account
            .create_inbound_session(vodozemac::olm::SessionConfig::version_1(), identity_key, &pre_key)
            .map_err(|_| CryptoError::SessionCreationFailed)?;
        
        Ok((super::session::Session::new(result.session), result.plaintext))
    }
}

impl Drop for Identity {
    fn drop(&mut self) {
        // The Account will be dropped and its memory zeroized by vodozemac
    }
}

// Security: Ensure sensitive data is zeroized when possible
impl Zeroize for Identity {
    fn zeroize(&mut self) {
        // vodozemac Account handles its own zeroization
    }
}