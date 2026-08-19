// Error types for the crypto library
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CryptoError {
    #[error("Invalid input parameters")]
    InvalidInput,
    
    #[error("Invalid ciphertext")]
    InvalidCiphertext,
    
    #[error("Invalid session")]
    InvalidSession,
    
    #[error("Session creation failed")]
    SessionCreationFailed,
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
    
    #[error("Deserialization error: {0}")]
    DeserializationError(String),
    
    #[error("State corrupted")]
    StateCorrupted,
    
    #[error("Cryptographic operation failed")]
    CryptoFailure,
    
    #[error("Unsupported version")]
    UnsupportedVersion,
    
    #[error("Key error: {0}")]
    KeyError(String),
}

impl From<CryptoError> for i32 {
    fn from(error: CryptoError) -> Self {
        match error {
            CryptoError::InvalidInput => -1,
            CryptoError::InvalidCiphertext => -2,
            CryptoError::InvalidSession => -3,
            CryptoError::SessionCreationFailed => -4,
            CryptoError::SerializationError(_) => -5,
            CryptoError::DeserializationError(_) => -6,
            CryptoError::StateCorrupted => -7,
            CryptoError::CryptoFailure => -8,
            CryptoError::UnsupportedVersion => -9,
            CryptoError::KeyError(_) => -10,
        }
    }
}