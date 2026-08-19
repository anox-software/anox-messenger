// Serialization module - handles encrypted pickling of crypto state with authenticated encryption
use aes_gcm::{
    aead::{Aead, KeyInit, Payload},
    Aes256Gcm, Nonce,
};
use thiserror::Error;
use zeroize::Zeroize;

/// Current protected-state envelope version.
pub const ANOX_STATE_VERSION: u8 = 0x01;

/// Magic bytes at the start of every protected-state envelope.
pub const ANOX_STATE_MAGIC: &[u8; 4] = b"ANOX";

/// CryptoSerializer for encrypting/decrypting pickled state with authenticated encryption
pub struct CryptoSerializer {
    key: [u8; 32],
}

impl CryptoSerializer {
    /// Create a new serializer with the given key (must be 32 bytes)
    pub fn new(key: &[u8]) -> Result<Self, CryptoSerializerError> {
        if key.len() != 32 {
            return Err(CryptoSerializerError::InvalidKeyLength);
        }
        let mut key_array = [0u8; 32];
        key_array.copy_from_slice(key);
        Ok(Self { key: key_array })
    }

    /// Serialize and encrypt data with authenticated encryption.
    /// Envelope format: [4 magic][1 version][12 nonce][ciphertext + 16 tag]
    /// The magic and version are authenticated via GCM AAD.
    pub fn serialize<T: serde::Serialize>(&self, data: &T) -> Result<Vec<u8>, CryptoSerializerError> {
        // First serialize to JSON
        let json = serde_json::to_vec(data)
            .map_err(|e| CryptoSerializerError::SerializationError(e.to_string()))?;

        // Encrypt the JSON data with authenticated encryption
        self.encrypt(&json)
    }

    /// Decrypt and deserialize data with authenticated encryption.
    /// Validates magic, version, and envelope size before attempting decryption.
    pub fn deserialize<T: serde::de::DeserializeOwned>(
        &self,
        data: &[u8],
    ) -> Result<T, CryptoSerializerError> {
        // Decrypt the data with authenticated encryption
        let decrypted = self.decrypt(data)?;

        // Deserialize from JSON (decrypted data is owned, so T must own its data)
        serde_json::from_slice(&decrypted)
            .map_err(|e| CryptoSerializerError::DeserializationError(e.to_string()))
    }

    /// Encrypt data using AES-256-GCM (authenticated encryption)
    fn encrypt(&self, plaintext: &[u8]) -> Result<Vec<u8>, CryptoSerializerError> {
        // Create cipher
        let cipher = Aes256Gcm::new(&self.key.into());

        // Generate random nonce (12 bytes for GCM)
        let mut nonce_bytes = [0u8; 12];
        getrandom::getrandom(&mut nonce_bytes).map_err(|_| CryptoSerializerError::RandomError)?;
        let nonce = Nonce::from_slice(&nonce_bytes);

        // Authenticated associated data: magic + version (binds the header to the ciphertext)
        let aad = [ANOX_STATE_MAGIC.as_slice(), &[ANOX_STATE_VERSION]].concat();

        // Encrypt with authenticated encryption and AAD
        let ciphertext = cipher
            .encrypt(nonce, Payload { msg: plaintext, aad: &aad })
            .map_err(|_| CryptoSerializerError::EncryptionError)?;

        // Prepend magic, version, and nonce to ciphertext
        let mut result = Vec::with_capacity(4 + 1 + 12 + ciphertext.len());
        result.extend_from_slice(ANOX_STATE_MAGIC);
        result.push(ANOX_STATE_VERSION);
        result.extend_from_slice(&nonce_bytes);
        result.extend_from_slice(&ciphertext);

        Ok(result)
    }

    /// Decrypt data using AES-256-GCM (authenticated encryption)
    fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>, CryptoSerializerError> {
        // Minimum: magic(4) + version(1) + nonce(12) + tag(16) = 33
        if ciphertext.len() < 4 + 1 + 12 + 16 {
            return Err(CryptoSerializerError::InvalidCiphertext);
        }

        // Extract magic
        let magic = &ciphertext[0..4];
        if magic != ANOX_STATE_MAGIC {
            return Err(CryptoSerializerError::InvalidEnvelope);
        }

        // Extract and validate version
        let version = ciphertext[4];
        if version != ANOX_STATE_VERSION {
            return Err(CryptoSerializerError::UnsupportedVersion);
        }

        // Extract nonce and actual ciphertext
        let nonce_bytes = &ciphertext[5..17];
        let ciphertext_data = &ciphertext[17..];
        let nonce = Nonce::from_slice(nonce_bytes);

        // AAD used during encryption
        let aad = [ANOX_STATE_MAGIC.as_slice(), &[version]].concat();

        // Create cipher
        let cipher = Aes256Gcm::new(&self.key.into());

        // Decrypt with authenticated encryption (also verifies integrity, AAD, and tag)
        let plaintext = cipher
            .decrypt(nonce, Payload { msg: ciphertext_data, aad: &aad })
            .map_err(|_| CryptoSerializerError::DecryptionError)?;

        Ok(plaintext)
    }
}

impl Drop for CryptoSerializer {
    fn drop(&mut self) {
        self.key.zeroize();
    }
}

#[derive(Error, Debug)]
pub enum CryptoSerializerError {
    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Deserialization error: {0}")]
    DeserializationError(String),

    #[error("Encryption error")]
    EncryptionError,

    #[error("Decryption error (authentication failed or data corrupted)")]
    DecryptionError,

    #[error("Invalid ciphertext (too short or malformed)")]
    InvalidCiphertext,

    #[error("Invalid envelope (magic missing or malformed)")]
    InvalidEnvelope,

    #[error("Random number generation failed")]
    RandomError,

    #[error("Invalid key length (must be 32 bytes)")]
    InvalidKeyLength,

    #[error("Unsupported protected-state version")]
    UnsupportedVersion,
}

// Security: Ensure key material is zeroized
impl Zeroize for CryptoSerializer {
    fn zeroize(&mut self) {
        self.key.zeroize();
    }
}
