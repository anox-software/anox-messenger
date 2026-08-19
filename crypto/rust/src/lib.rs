// anoX Crypto Library - Rust Layer
// This module provides cryptographic operations using vodozemac
// It exposes a narrow JNI interface for Android integration

pub mod error;
pub mod identity;
pub mod session;
pub mod serialization;

#[cfg(test)]
mod tests;

pub use error::CryptoError;
pub use identity::Identity;
pub use session::Session;

/// Current version of the crypto library
pub const CRYPTO_VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(target_os = "android")]
mod jni_bridge {
    use super::{Identity, Session};
    use jni::objects::{JByteArray, JClass, JIntArray, JLongArray};
    use jni::sys::{jboolean, jint, jlong};
    use jni::JNIEnv;
    use std::collections::HashSet;
    use std::sync::{LazyLock, Mutex};

    /// Tracks live `Identity` handles. Kept separate from `ACTIVE_SESSIONS` to
    /// prevent type confusion at the JNI boundary.
    static ACTIVE_IDENTITIES: LazyLock<Mutex<HashSet<usize>>> =
        LazyLock::new(|| Mutex::new(HashSet::new()));

    /// Tracks live `Session` handles. Kept separate from `ACTIVE_IDENTITIES`.
    static ACTIVE_SESSIONS: LazyLock<Mutex<HashSet<usize>>> =
        LazyLock::new(|| Mutex::new(HashSet::new()));

    fn register_identity(ptr: *mut Identity) {
        if !ptr.is_null() {
            let _ = ACTIVE_IDENTITIES.lock().unwrap().insert(ptr as usize);
        }
    }

    fn is_identity_active(handle: jlong) -> bool {
        if handle == 0 {
            return false;
        }
        ACTIVE_IDENTITIES.lock().unwrap().contains(&(handle as usize))
    }

    fn release_identity(handle: jlong) -> Option<*mut Identity> {
        if handle == 0 {
            return None;
        }
        let removed = ACTIVE_IDENTITIES.lock().unwrap().remove(&(handle as usize));
        if removed {
            Some(handle as *mut Identity)
        } else {
            None
        }
    }

    fn register_session(ptr: *mut Session) {
        if !ptr.is_null() {
            let _ = ACTIVE_SESSIONS.lock().unwrap().insert(ptr as usize);
        }
    }

    fn is_session_active(handle: jlong) -> bool {
        if handle == 0 {
            return false;
        }
        ACTIVE_SESSIONS.lock().unwrap().contains(&(handle as usize))
    }

    fn release_session(handle: jlong) -> Option<*mut Session> {
        if handle == 0 {
            return None;
        }
        let removed = ACTIVE_SESSIONS.lock().unwrap().remove(&(handle as usize));
        if removed {
            Some(handle as *mut Session)
        } else {
            None
        }
    }

    fn to_i8_vec(bytes: &[u8]) -> Vec<i8> {
        bytes.iter().map(|b| *b as i8).collect()
    }

    fn from_i8_slice(buf: &[i8]) -> Vec<u8> {
        buf.iter().map(|b| *b as u8).collect()
    }

    fn read_byte_array(env: &mut JNIEnv, array: &JByteArray) -> Option<Vec<u8>> {
        let len = env.get_array_length(array).ok()? as usize;
        let mut buf = vec![0i8; len];
        env.get_byte_array_region(array, 0, &mut buf).ok()?;
        Some(from_i8_slice(&buf))
    }

    fn write_byte_array(env: &mut JNIEnv, out: &JByteArray, data: &[u8]) -> Result<(), i32> {
        let out_len = match env.get_array_length(out) {
            Ok(l) => l as usize,
            Err(_) => return Err(-10),
        };
        if data.len() > out_len {
            return Err(-11);
        }
        let i8_data = to_i8_vec(data);
        match env.set_byte_array_region(out, 0, &i8_data) {
            Ok(_) => Ok(()),
            Err(_) => Err(-12),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoInit<'local>(
        _env: JNIEnv<'local>,
        _class: JClass<'local>,
    ) -> jboolean {
        1
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoCreateIdentity<'local>(
        _env: JNIEnv<'local>,
        _class: JClass<'local>,
    ) -> jlong {
        let ptr = Box::into_raw(Box::new(Identity::new()));
        register_identity(ptr);
        ptr as jlong
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoDestroyIdentity<'local>(
        _env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
    ) {
        if let Some(ptr) = release_identity(identity) {
            unsafe {
                let _ = Box::from_raw(ptr);
            }
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoGetCurve25519PublicKey<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        out: JByteArray<'local>,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) {
            return -1;
        }
        let out_len = match env.get_array_length(&out) {
            Ok(l) => l as usize,
            Err(_) => return -3,
        };
        if out_len < 32 {
            return -2;
        }
        let id_ref = unsafe { &*(identity as *const Identity) };
        let key = id_ref.curve25519_public_key();
        match write_byte_array(&mut env, &out, &key) {
            Ok(_) => 0,
            Err(e) => e,
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoGetEd25519PublicKey<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        out: JByteArray<'local>,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) {
            return -1;
        }
        let out_len = match env.get_array_length(&out) {
            Ok(l) => l as usize,
            Err(_) => return -3,
        };
        if out_len < 32 {
            return -2;
        }
        let id_ref = unsafe { &*(identity as *const Identity) };
        let key = id_ref.ed25519_public_key();
        match write_byte_array(&mut env, &out, &key) {
            Ok(_) => 0,
            Err(e) => e,
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoGenerateOneTimeKeys<'local>(
        _env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        count: jint,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) || count < 0 {
            return -1;
        }
        let id_ref = unsafe { &mut *(identity as *mut Identity) };
        match id_ref.generate_one_time_keys(count as usize) {
            Ok(_) => 0,
            Err(e) => e.into(),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoOneTimeKeysCount<'local>(
        _env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) {
            return -1;
        }
        let id_ref = unsafe { &*(identity as *const Identity) };
        id_ref.one_time_keys_count() as jint
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoGetOneTimeKey<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        index: jint,
        out: JByteArray<'local>,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) || index < 0 {
            return -1;
        }
        let out_len = match env.get_array_length(&out) {
            Ok(l) => l as usize,
            Err(_) => return -3,
        };
        if out_len < 32 {
            return -2;
        }
        let id_ref = unsafe { &*(identity as *const Identity) };
        match id_ref.get_one_time_key_by_index(index as usize) {
            Some(key) => match write_byte_array(&mut env, &out, &key) {
                Ok(_) => 0,
                Err(e) => e,
            },
            None => -3,
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoSerializeIdentity<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        key: JByteArray<'local>,
        out: JByteArray<'local>,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) {
            return -1;
        }
        let key_bytes = match read_byte_array(&mut env, &key) {
            Some(v) if v.len() == 32 => v,
            _ => return -1,
        };
        let id_ref = unsafe { &*(identity as *const Identity) };
        match id_ref.serialize(&key_bytes) {
            Ok(data) => {
                let out_len = match env.get_array_length(&out) {
                    Ok(l) => l as usize,
                    Err(_) => return -3,
                };
                if data.len() > out_len {
                    return -2;
                }
                match write_byte_array(&mut env, &out, &data) {
                    Ok(_) => data.len() as jint,
                    Err(e) => e,
                }
            }
            Err(e) => e.into(),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoDeserializeIdentity<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        data: JByteArray<'local>,
        key: JByteArray<'local>,
    ) -> jlong {
        let data_bytes = match read_byte_array(&mut env, &data) {
            Some(v) => v,
            None => return 0,
        };
        let key_bytes = match read_byte_array(&mut env, &key) {
            Some(v) if v.len() == 32 => v,
            _ => return 0,
        };
        match Identity::deserialize(&data_bytes, &key_bytes) {
            Ok(id) => {
                let ptr = Box::into_raw(Box::new(id));
                register_identity(ptr);
                ptr as jlong
            }
            Err(_) => 0,
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoCreateOutboundSession<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        their_identity_key: JByteArray<'local>,
        their_one_time_key: JByteArray<'local>,
    ) -> jlong {
        if identity == 0 || !is_identity_active(identity) {
            return 0;
        }
        let id_ref = unsafe { &*(identity as *const Identity) };
        let identity_key = match read_byte_array(&mut env, &their_identity_key) {
            Some(v) if v.len() == 32 => v,
            _ => return 0,
        };
        let one_time_key = match read_byte_array(&mut env, &their_one_time_key) {
            Some(v) if v.len() == 32 => v,
            _ => return 0,
        };
        match id_ref.create_outbound_session(&identity_key, &one_time_key) {
            Ok(sess) => {
                let ptr = Box::into_raw(Box::new(sess));
                register_session(ptr);
                ptr as jlong
            }
            Err(_) => 0,
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoCreateInboundSession<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        identity: jlong,
        their_identity_key: JByteArray<'local>,
        pre_key_message: JByteArray<'local>,
        out_plaintext: JByteArray<'local>,
        out_session: JLongArray<'local>,
    ) -> jint {
        if identity == 0 || !is_identity_active(identity) {
            return -1;
        }
        let id_ref = unsafe { &mut *(identity as *mut Identity) };
        let identity_key = match read_byte_array(&mut env, &their_identity_key) {
            Some(v) if v.len() == 32 => v,
            _ => return -1,
        };
        let pre_key = match read_byte_array(&mut env, &pre_key_message) {
            Some(v) => v,
            None => return -1,
        };
        match id_ref.create_inbound_session(&identity_key, &pre_key) {
            Ok((sess, plaintext)) => {
                let out_len = match env.get_array_length(&out_plaintext) {
                    Ok(l) => l as usize,
                    Err(_) => return -3,
                };
                if plaintext.len() > out_len {
                    return -2;
                }
                match write_byte_array(&mut env, &out_plaintext, &plaintext) {
                    Ok(_) => {}
                    Err(e) => return e,
                }
                // Do not register the handle until the Java output array has
                // accepted the pointer. Otherwise a JNI write failure would
                // leak the native Session.
                let ptr = Box::into_raw(Box::new(sess));
                let session_ptr = ptr as jlong;
                if env.set_long_array_region(&out_session, 0, &[session_ptr]).is_err() {
                    unsafe {
                        let _ = Box::from_raw(ptr);
                    }
                    return -3;
                }
                register_session(ptr);
                plaintext.len() as jint
            }
            Err(e) => e.into(),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoEncrypt<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        session: jlong,
        plaintext: JByteArray<'local>,
        out: JByteArray<'local>,
        out_len: JIntArray<'local>,
    ) -> jint {
        if session == 0 || !is_session_active(session) {
            return -1;
        }
        let sess_ref = unsafe { &mut *(session as *mut Session) };
        let pt = match read_byte_array(&mut env, &plaintext) {
            Some(v) => v,
            None => return -1,
        };
        match sess_ref.encrypt(&pt) {
            Ok((message_type, encrypted)) => {
                let out_capacity = match env.get_array_length(&out) {
                    Ok(l) => l as usize,
                    Err(_) => return -3,
                };
                if encrypted.len() > out_capacity {
                    return -2;
                }
                match write_byte_array(&mut env, &out, &encrypted) {
                    Ok(_) => {}
                    Err(e) => return e,
                }
                if env.set_int_array_region(&out_len, 0, &[encrypted.len() as i32]).is_err() {
                    return -3;
                }
                message_type as jint
            }
            Err(e) => e.into(),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoDecrypt<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        session: jlong,
        message_type: jint,
        ciphertext: JByteArray<'local>,
        out: JByteArray<'local>,
    ) -> jint {
        if session == 0 || !is_session_active(session) || (message_type != 0 && message_type != 1) {
            return -1;
        }
        let sess_ref = unsafe { &mut *(session as *mut Session) };
        let cipher = match read_byte_array(&mut env, &ciphertext) {
            Some(v) => v,
            None => return -1,
        };
        match sess_ref.decrypt(message_type as u32, &cipher) {
            Ok(plaintext) => {
                let out_len = match env.get_array_length(&out) {
                    Ok(l) => l as usize,
                    Err(_) => return -3,
                };
                if plaintext.len() > out_len {
                    return -2;
                }
                match write_byte_array(&mut env, &out, &plaintext) {
                    Ok(_) => {}
                    Err(e) => return e,
                }
                plaintext.len() as jint
            }
            Err(e) => e.into(),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoDestroySession<'local>(
        _env: JNIEnv<'local>,
        _class: JClass<'local>,
        session: jlong,
    ) {
        if let Some(ptr) = release_session(session) {
            unsafe {
                let _ = Box::from_raw(ptr);
            }
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoSerializeSession<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        session: jlong,
        key: JByteArray<'local>,
        out: JByteArray<'local>,
    ) -> jint {
        if session == 0 || !is_session_active(session) {
            return -1;
        }
        let key_bytes = match read_byte_array(&mut env, &key) {
            Some(v) if v.len() == 32 => v,
            _ => return -1,
        };
        let sess_ref = unsafe { &*(session as *const Session) };
        match sess_ref.serialize(&key_bytes) {
            Ok(data) => {
                let out_len = match env.get_array_length(&out) {
                    Ok(l) => l as usize,
                    Err(_) => return -3,
                };
                if data.len() > out_len {
                    return -2;
                }
                match write_byte_array(&mut env, &out, &data) {
                    Ok(_) => data.len() as jint,
                    Err(e) => e,
                }
            }
            Err(e) => e.into(),
        }
    }

    #[no_mangle]
    pub extern "system" fn Java_com_anox_crypto_CryptoNative_cryptoDeserializeSession<'local>(
        mut env: JNIEnv<'local>,
        _class: JClass<'local>,
        data: JByteArray<'local>,
        key: JByteArray<'local>,
    ) -> jlong {
        let data_bytes = match read_byte_array(&mut env, &data) {
            Some(v) => v,
            None => return 0,
        };
        let key_bytes = match read_byte_array(&mut env, &key) {
            Some(v) if v.len() == 32 => v,
            _ => return 0,
        };
        match Session::deserialize(&data_bytes, &key_bytes) {
            Ok(sess) => {
                let ptr = Box::into_raw(Box::new(sess));
                register_session(ptr);
                ptr as jlong
            }
            Err(_) => 0,
        }
    }
}
