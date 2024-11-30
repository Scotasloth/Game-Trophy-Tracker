[app]
title = Trophy King
package.name = TrophyKing
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,sqlite3,os,sys,pillow,functools,time,re,requests
orientation = portrait

[osx]
osx.python_version = 3
osx.kivy_version = 1.9.1

[android]
fullscreen = 0
android.api = 31
android.minapi = 21
android.sdk = 31
java.sdk_path = C:/Program Files/Android/jdk/jdk-8.0.302.8-hotspot/jdk8u302-b08
android.ndk_path = C:/Users/Ross/AppData/Local/Android/Sdk/ndk/28.0.12674087
android.sdk_path = C:/Users/Ross/AppData/Local/Android/Sdk
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer