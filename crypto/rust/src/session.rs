// Session module - wraps vodozemac Session functionality
use crate::error::CryptoError;
use crate::serialization::CryptoSerializer;
use vodozemac::olm::{OlmMessage, Session as VodozemacSession, SessionPickle};
use zeroize::Zeroize;

/// Wrapper around vodozemac Session for encrypted communication
pub struct Session {
    session: VodozemacSession,
}

impl Session {
    /// Create a new session from vodozemac Session
    pub fn new(session: VodozemacSession) -> Self {
        Self { session }
    }
    
    /// Encrypt a message
    /// Returns (message_type, ciphertext_bytes) where message_type is:
    /// - 0 for PreKey (session-establishment) messages
    /// - 1 for Normal (established-session) messages
    pub fn encrypt(&mut self, plaintext: &[u8]) -> Result<(u32, Vec<u8>), CryptoError> {
        let message = self
            .session
            .encrypt(plaintext)
            .map_err(|_| CryptoError::CryptoFailure)?;
        
        // Use vodozemac's own to_parts serialization (message_type, bytes)
        let (message_type, message_bytes) = message.to_parts();
        
        Ok((message_type as u32, message_bytes))
    }
    
    /// Decrypt a Normal (established-session) message
    /// For PreKey messages, use Identity::create_inbound_session instead
    pub fn decrypt(&mut self, message_type: u32, ciphertext: &[u8]) -> Result<Vec<u8>, CryptoError> {
        // For established sessions, only Normal messages (type 1) should be decrypted here
        if message_type != 1 {
            return Err(CryptoError::InvalidInput);
        }
        
        // Reconstruct OlmMessage using the actual vodozemac API
        let message = OlmMessage::from_parts(message_type as usize, ciphertext)
            .map_err(|_| CryptoError::InvalidCiphertext)?;
        
        self.session
            .decrypt(&message)
            .map_err(|_| CryptoError::InvalidCiphertext)
    }
    
    /// Get session ID for identification
    pub fn session_id(&self) -> String {
        self.session.session_id()
    }
    
    /// Check if session has received messages
    pub fn has_received_message(&self) -> bool {
        self.session.has_received_message()
    }
    
    /// Serialize session with encryption
    pub fn serialize(&self, key: &[u8]) -> Result<Vec<u8>, CryptoError> {
        if key.len() != 32 {
            return Err(CryptoError::InvalidInput);
        }
        
        let pickle = self.session.pickle();
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

    /// Deserialize session from encrypted data
    pub fn deserialize(data: &[u8], key: &[u8]) -> Result<Self, CryptoError> {
        if key.len() != 32 {
            return Err(CryptoError::InvalidInput);
        }
        
        let serializer = CryptoSerializer::new(key)
            .map_err(|e| CryptoError::DeserializationError(e.to_string()))?;
        let pickle: SessionPickle = serializer
            .deserialize(data)
            .map_err(Self::map_serializer_error)?;
        
        Ok(Self {
            session: pickle.into(),
        })
    }
}

impl Drop for Session {
    fn drop(&mut self) {
        // The Session will be dropped and its memory zeroized by vodozemac
    }
}

// Security: Ensure sensitive data is zeroized when possible
impl Zeroize for Session {
    fn zeroize(&mut self) {
        // vodozemac Session handles its own zeroization
    }
}