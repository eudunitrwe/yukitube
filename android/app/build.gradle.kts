import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// The same version as the desktop app: read from the PKGBUILD's pkgver.
val yukiVersion: String = rootProject.file("../pkgbuild/PKGBUILD").readLines()
    .first { it.startsWith("pkgver=") }.substringAfter("=").trim()
val yukiCode: Int = yukiVersion.split(".").map { it.toInt() }.let { (a, b, c) -> a * 10000 + b * 100 + c }

// Release signing key, kept out of the repo (see android/README.md).
val keyProps = Properties().apply {
    val f = file(System.getenv("YUKITUBE_KEYSTORE_PROPS") ?: "${System.getProperty("user.home")}/.android-keys/yukitube.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

// The page bridge is shared with the desktop app.
val bridgeAssets = layout.buildDirectory.dir("generated/yukiAssets")
val copyBridge by tasks.registering(Copy::class) {
    from(rootProject.file("../remote/browser/agent-core.js"))
    into(bridgeAssets)
}

android {
    namespace = "com.yukitube.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.yukitube.app"
        minSdk = 26
        targetSdk = 35
        versionCode = yukiCode
        versionName = yukiVersion
    }

    signingConfigs {
        if (keyProps.getProperty("storeFile") != null) {
            create("release") {
                storeFile = file(keyProps.getProperty("storeFile"))
                storePassword = keyProps.getProperty("storePassword")
                keyAlias = keyProps.getProperty("keyAlias")
                keyPassword = keyProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.findByName("release")
        }
    }

    sourceSets["main"].assets.srcDir(bridgeAssets)

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    androidResources {
        @Suppress("UnstableApiUsage")
        generateLocaleConfig = true
    }
    packaging {
        resources.excludes += setOf("/META-INF/{AL2.0,LGPL2.1}", "DebugProbesKt.bin", "kotlin-tooling-metadata.json")
    }
}

tasks.named("preBuild") { dependsOn(copyBridge) }

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.webkit:webkit:1.12.1")
    implementation("androidx.media:media:1.7.0")
    implementation("io.coil-kt:coil-compose:2.7.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
}
