package com.anox.crypto

/**
 * Sealed class representing the result of a cryptographic operation
 * Either Success with a value or Failure with a CryptoError
 */
sealed class CryptoResult<out T> {
    data class Success<out T>(val value: T) : CryptoResult<T>()
    data class Failure(val error: CryptoError) : CryptoResult<Nothing>()
    
    fun <R> map(transform: (T) -> R): CryptoResult<R> {
        return when (this) {
            is Success -> Success(transform(value))
            is Failure -> this as CryptoResult<R>
        }
    }
    
    fun <R> flatMap(transform: (T) -> CryptoResult<R>): CryptoResult<R> {
        return when (this) {
            is Success -> transform(value)
            is Failure -> this as CryptoResult<R>
        }
    }
    
    fun getOrNull(): T? {
        return when (this) {
            is Success -> value
            is Failure -> null
        }
    }
    
    fun getOrThrow(): T {
        return when (this) {
            is Success -> value
            is Failure -> throw error
        }
    }
    
    companion object {
        fun <T> success(value: T): CryptoResult<T> = Success(value)
        fun <T> failure(error: CryptoError): CryptoResult<T> = Failure(error)
    }
}