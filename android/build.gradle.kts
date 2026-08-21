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
    }
    
    sourceSets {
        getByName("main") {
            java {
                srcDir("src/main/java")
                srcDir("../crypto/android/src/main/java")
            }
            jniLibs {
                srcDir("src/main/jniLibs")
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
                srcDir("src/main/jniLibs")
            }
        }
    }
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