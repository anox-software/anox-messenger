package com.anox.messenger.security.deviceauth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** RFC9449 `htu` normalisation tests. */
class DpopHtuTest {

    @Test
    fun `query and fragment are stripped`() {
        assertEquals(
            "https://api.example.test/v1/resource",
            DpopHtu.normalize("https://api.example.test/v1/resource?a=1&b=2#frag")
        )
    }

    @Test
    fun `plain uri is unchanged`() {
        assertEquals(
            "https://api.example.test/v1/resource",
            DpopHtu.normalize("https://api.example.test/v1/resource")
        )
    }

    @Test
    fun `scheme and host are lowercased but path is preserved`() {
        assertEquals(
            "https://api.example.test/v1/Resource",
            DpopHtu.normalize("HTTPS://API.Example.TEST/v1/Resource")
        )
    }

    @Test
    fun `root path is preserved`() {
        assertEquals("https://api.example.test/", DpopHtu.normalize("https://api.example.test/"))
    }

    @Test
    fun `port is part of the authority`() {
        assertEquals(
            "https://api.example.test:8443/v1/resource",
            DpopHtu.normalize("https://api.example.test:8443/v1/resource?x=1")
        )
    }

    @Test
    fun `relative uri is rejected`() {
        assertThrows(IllegalArgumentException::class.java) {
            DpopHtu.normalize("/v1/resource")
        }
    }

    @Test
    fun `garbage uri is rejected`() {
        assertThrows(IllegalArgumentException::class.java) {
            DpopHtu.normalize("http://  bad uri")
        }
    }
}
