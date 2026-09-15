plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.anox.messenger"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.anox.messenger"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        ndkVersion = "26.2.11394342"
        ndk {
            // Exactly the frozen ABI set — no accidental extra unreviewed ABI.
            abiFilters.addAll(listOf("arm64-v8a", "x86_64"))
        }

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
        jniLibs {
            // MSC-UNIT-001: the packaged .so must be byte-identical to the
            // artifact produced by the authoritative build path, so AGP must
            // not re-strip at package time (hash binding is verified against
            // build/native/native-manifest.json).
            keepDebugSymbols += "**/*.so"
        }
    }

    lint {
        abortOnError = true
    }

    sourceSets {
        getByName("main") {
            java {
                srcDir("src/main/java")
                srcDir("../crypto/android/src/main/java")
            }
            jniLibs {
                // Authoritative build output only — see tools/security/native_build.py.
                srcDir("$rootDir/build/native/jniLibs")
            }
        }
        getByName("test") {
            java {
                srcDir("src/test/java")
            }
        }
        getByName("androidTest") {
            java {
                srcDir("src/androidTest/java")
                srcDir("../crypto/android/src/androidTest/java")
            }
            jniLibs {
                srcDir("$rootDir/build/native/jniLibs")
            }
        }
    }
}

// MSC-UNIT-001 (REMEDIATION_SESSION_S1): fail-closed gate. The APK may only
// consume the native library produced by the authoritative build path
// (tools/security/native_build.py). Committed or hand-built .so files under
// android/src/main/jniLibs are a prohibited bypass.
val nativeArtifactsDir = rootDir.resolve("build/native/jniLibs")
val committedJniLibsDir = file("src/main/jniLibs")

val verifyNativeArtifacts by tasks.registering {
    description =
        "Fail-closed gate: packaged native artifacts must come from the authoritative build path."
    group = "verification"
    doLast {
        val committed = committedJniLibsDir.walkTopDown()
            .filter { it.isFile && it.extension == "so" }
            .toList()
        if (committed.isNotEmpty()) {
            throw GradleException(
                "Committed native binaries are prohibited (MSC-UNIT-001): " +
                    committed.joinToString(", ") { it.path } +
                    " — build via tools/security/native_build.py instead."
            )
        }
        for (abi in listOf("arm64-v8a", "x86_64")) {
            val so = nativeArtifactsDir.resolve("$abi/libanox_crypto.so")
            if (!so.isFile) {
                throw GradleException(
                    "Missing authoritative native artifact: $so — " +
                        "run: python3 tools/security/native_build.py build"
                )
            }
        }
    }
}

tasks.matching { it.name.startsWith("package") }.configureEach {
    dependsOn(verifyNativeArtifacts)
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.activity:activity-compose:1.8.1")
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    // B-002 Device Authentication: RFC9449 DPoP / JOSE ES256.
    // Pinned. Standards-compliant JWS/JWK implementation; supports non-extractable
    // Android Keystore EC private keys via ECDSASigner(PrivateKey, Curve).
    // Java 7 bytecode, shaded JSON, BouncyCastle/Tink optional -> Android-safe.
    implementation("com.nimbusds:nimbus-jose-jwt:10.9.1")

    testImplementation("junit:junit:4.13.2")
    testImplementation("com.nimbusds:nimbus-jose-jwt:10.9.1")
    androidTestImplementation("androidx.test:runner:1.5.2")
    androidTestImplementation("androidx.test:rules:1.5.0")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2023.10.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}