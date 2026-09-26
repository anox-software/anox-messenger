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
                // Authoritative build output ONLY — see tools/security/native_build.py.
                // setSrcDirs REPLACES the AGP default (src/main/jniLibs) so a
                // committed/stale library can never be silently merged in.
                setSrcDirs(listOf("$rootDir/build/native/jniLibs"))
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
                setSrcDirs(listOf("$rootDir/build/native/jniLibs"))
            }
        }
    }
}

// MSC-UNIT-001 (S1 clean rebuild): fail-closed packaging boundary.
//
// The APK may only consume the native library produced by the authoritative
// build path (tools/security/native_build.py). Before ANY task that merges,
// strips or packages native libraries runs, the canonical verifier must
// succeed against the authoritative manifest + binaries. The security logic is
// NOT duplicated here: Gradle invokes `native_build.py verify`, which fails on
// a missing manifest, missing/unexpected ABI, missing binary, non-ELF
// placeholder, hash/size mismatch, wrong ELF architecture, JNI parity mismatch
// against the ACTUAL binary export surface, absent provenance fields, absent
// reproducibility attestation, dirty tree and any uncontrolled alternative JNI
// library source (committed .so / .aar / .jar under android/ or crypto/android/).
val nativeArtifactsDir = rootDir.resolve("build/native/jniLibs")
val nativeManifestFile = rootDir.resolve("build/native/native-manifest.json")
val nativeVerifier = rootDir.resolve("tools/security/native_build.py")
val requiredNativeAbis = listOf("arm64-v8a", "x86_64")
// Every native input source AGP could otherwise consume for this module.
val alternativeNativeInputDirs = listOf(
    file("src/main/jniLibs"),
    file("src/debug/jniLibs"),
    file("src/release/jniLibs"),
    file("src/androidTest/jniLibs"),
    file("libs"),
    rootDir.resolve("crypto/android/src"),
)

val verifyNativeArtifacts by tasks.registering(Exec::class) {
    description =
        "Fail-closed gate: packaged native artifacts must pass the canonical provenance verifier."
    group = "verification"
    // Provenance is re-established on every packaging run — never cached.
    outputs.upToDateWhen { false }
    workingDir = rootDir
    isIgnoreExitValue = false
    commandLine(
        "python3", nativeVerifier.path, "verify",
        "--repo-root", rootDir.path,
        "--out-dir", nativeArtifactsDir.path,
        "--manifest", nativeManifestFile.path,
    )
    doFirst {
        if (!nativeVerifier.isFile) {
            throw GradleException("Canonical native verifier missing: $nativeVerifier (MSC-UNIT-001)")
        }
        if (!nativeManifestFile.isFile) {
            throw GradleException(
                "Missing authoritative native provenance manifest: $nativeManifestFile — " +
                    "run: python3 tools/security/native_build.py build && rebuild-compare && verify"
            )
        }
        for (abi in requiredNativeAbis) {
            val so = nativeArtifactsDir.resolve("$abi/libanox_crypto.so")
            if (!so.isFile) {
                throw GradleException(
                    "Missing authoritative native artifact: $so — " +
                        "run: python3 tools/security/native_build.py build"
                )
            }
        }
        val alternative = alternativeNativeInputDirs
            .filter { it.isDirectory }
            .flatMap { dir ->
                dir.walkTopDown().filter { f ->
                    f.isFile && (f.extension == "so" || f.extension == "aar" || f.extension == "jar" ||
                        f.path.contains("${File.separator}jniLibs${File.separator}"))
                }.toList()
            }
        if (alternative.isNotEmpty()) {
            throw GradleException(
                "Uncontrolled alternative native input is prohibited (MSC-UNIT-001): " +
                    alternative.joinToString(", ") { it.path } +
                    " — only build/native/jniLibs produced by tools/security/native_build.py may be packaged."
            )
        }
    }
}

// Every task that merges, strips, packages or bundles native libraries depends
// on the fail-closed verifier: no APK/AAB can be produced from unverified input.
tasks.matching {
    Regex("^(merge.*JniLibFolders|merge.*NativeLibs|strip.*Symbols|extract.*NativeSymbolTables|package.*|bundle.*)$")
        .matches(it.name)
}.configureEach {
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